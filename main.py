import os, sys, uuid
from langgraph.checkpoint.memory import MemorySaver
from graph import create_app
from logger import agent_logger, LogColors
from agents import WriterAgent, VisualizationAgent, final_pdf

def run_analytics_session(csv_path: str, session_id: str = "session_001"):
    agent_logger.log_event(f"Initializing Session: {session_id}", level="INFO")
    
    try:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Source file not found: {csv_path}")

        memory = MemorySaver()
        app = create_app(memory)
        config = {"configurable": {"thread_id": session_id}}
        
        initial_state = {
            "csv_path": csv_path, 
            "artifacts": [], 
            "iteration": 0, 
            "report_sections": {}
        }

        # 1. Run the Graph
        for event in app.stream(initial_state, config=config):
            node_name = list(event.keys())[0]
            agent_logger.log_event(f"Node Complete: {node_name}", level="INFO")

        # 2. Extract State
        final_snapshot = app.get_state(config)
        state_values = final_snapshot.values
        
        # 3. Handle Charts (Fallback if graph node failed)
        charts = state_values.get('artifacts', [])
        if not charts:
            agent_logger.log_event("Generating charts via fallback...", level="WARNING")
            plan = state_values.get('plan', {})
            viz_goal = plan.get('viz_goal', "Data distribution plot")
            
            viz_agent = VisualizationAgent("CHARTS_ENGINE")
            charts = viz_agent.run(csv_path=csv_path, viz_goal=viz_goal)

        # 4. Final Narrative Synthesis
        writer = WriterAgent("WRITER_AGENT")
        report_sections = state_values.get('report_sections', {})
        report_meta = writer.run(
            kpis=report_sections.get('kpis', ""), 
            stats=report_sections.get('stats', "")
        ) 

        kpis = report_sections.get('kpis', "No KPI data generated.")
        stats = report_sections.get('stats', "No Statistical data generated.")
        # 5. Generate PDF
      # Updated Section 6 in main.py
        # Updated Section 6 in main.py
        pdf_state = {
            "report_sections": {
                "narrative": {
                    "title": "Initial Sales Performance Report - Q1 2025",
                    "content": report_meta  # The string from WriterAgent.run()
                }, 
                "kpis": kpis,
                "stats": stats
            },
            "artifacts": charts 
        }
        pdf_path = final_pdf(pdf_state)
        
        print(f"\n{LogColors.SUCCESS}>>> Report Ready: {pdf_path}{LogColors.RESET}")

    except Exception as e:
        agent_logger.log_event(f"System Error: {str(e)}", level="ERROR")
        raise

if __name__ == "__main__":
    run_analytics_session(os.getenv("DATA_SOURCE", "data.csv"))