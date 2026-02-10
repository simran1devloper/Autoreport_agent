from typing import Annotated, TypedDict, List, Dict, Any, Optional
import operator

def merge_report_sections(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Reducer to perform a shallow merge of report sections.
    Handles None checks to prevent crashes during the initial node run.
    """
    # Initialize as dict if left is None
    new_state = dict(left) if left else {}
    if right:
        new_state.update(right)
    return new_state

class AnalysisPlan(TypedDict, total=False):
    """
    Structured definition for the strategic plan.
    total=False allows the planner to return a partial plan without crashing.
    """
    kpi_goal: str
    stats_goal: str
    viz_goal: str

class AgentState(TypedDict):
    """
    The global state object for the Analyst Workflow.
    """
    csv_path: str
    data_summary: str
    plan: AnalysisPlan
    
    # Annotated with operator.add: 
    # New image paths will be appended: ['chart1.png'] + ['chart2.png']
    artifacts: Annotated[List[str], operator.add]
    
    # Annotated with custom reducer:
    # Merges dicts: {'kpis': '...'} updated with {'stats': '...'}
    report_sections: Annotated[Dict[str, Any], merge_report_sections]
    
    supervisor_review: Optional[str]
    iteration: int