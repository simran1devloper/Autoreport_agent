import logging
from typing import Dict, Annotated, Any
from operator import add

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from agents import (
    StrategicPlanner, 
    VisualizationAgent, 
    ReportingAgent, 
    WriterAgent
)
from state import AgentState

logger = logging.getLogger("GraphFactory")

class WorkflowManager:
    """Orchestrates the construction and compilation of the LangGraph workflow."""

    def __init__(self, model_mapping: Dict[str, str]):
        self.models = model_mapping
        
        self.planner = StrategicPlanner(self.models.get("planner", "gemma3"))
        self.viz_agent = VisualizationAgent(self.models.get("viz", "gemma3"))
        self.reporter = ReportingAgent(self.models.get("reporter", "gemma3"))
        self.writer = WriterAgent(self.models.get("writer", "gemma3"))

    def supervisor_qc(self, state: AgentState) -> Dict[str, Any]:
        """Quality Control node to validate report completeness."""
        iteration = state.get('iteration', 0)
        sections = state.get('report_sections', {})
        
        
        required_keys = ['kpis', 'stats', 'narrative']
        is_complete = all(key in sections for key in required_keys)
        
        if is_complete or iteration >= 2:
            logger.info(f"QC Passed at iteration {iteration}")
            return {"supervisor_review": "approve"}
            
        logger.warning(f"QC Failed. Retrying iteration {iteration + 1}")
        return {
            "supervisor_review": "retry", 
            "iteration": iteration + 1
        }
    def build(self, checkpointer: BaseCheckpointSaver):
        workflow = StateGraph(AgentState)

     
        workflow.add_node("planner", lambda state: self.planner.run(state['csv_path']))
        workflow.add_node("kpi", lambda state: { "report_sections": {"kpis": self.reporter.generate_section("kpi", state.get('data_summary', ""), state['plan'].get('kpi_goal', ""))} })
        workflow.add_node("stats", lambda state: { "report_sections": {"stats": self.reporter.generate_section("stats", state.get('data_summary', ""), state['plan'].get('stats_goal', ""))} })
        workflow.add_node("charts", lambda state: { "artifacts": self.viz_agent.run(state['csv_path'], state['plan'].get('viz_goal', "")) })
        
        
        workflow.add_node("writer", lambda state: {
            "report_sections": {"narrative": self.writer.run(kpis=state['report_sections'].get('kpis', ""), stats=state['report_sections'].get('stats', ""))}
        })
        
        workflow.add_node("supervisor", self.supervisor_qc)

        
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "kpi")
        workflow.add_edge("planner", "stats")
        workflow.add_edge("planner", "charts")
        
        workflow.add_edge("kpi", "writer")
        workflow.add_edge("stats", "writer")
        workflow.add_edge("charts", "writer")
        
       
        workflow.add_edge("writer", "supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            lambda x: x["supervisor_review"],
            {"approve": END, "retry": "planner"}
        )

        return workflow.compile(checkpointer=checkpointer)

def create_app(memory: BaseCheckpointSaver):
    """Factory function to maintain backward compatibility with your main.py."""
    model_config = {
        "planner": "gemma3",
        "viz": "gemma3",
        "reporter": "gemma3",
        "writer": "gemma3"
    }
    manager = WorkflowManager(model_config)
    return manager.build(memory)
