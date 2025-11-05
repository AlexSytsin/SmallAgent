from langgraph.graph import StateGraph, END
from .state import MarketAnalysisState
from .nodes import searcher_node, summarizer_node, reasoner_node

def create_analyst_graph():
    workflow = StateGraph(MarketAnalysisState)

    workflow.add_node("searcher", searcher_node)
    workflow.add_node("summarizer", summarizer_node)
    workflow.add_node("reasoner", reasoner_node)

    workflow.set_entry_point("searcher")
    workflow.add_edge("searcher", "summarizer")
    workflow.add_edge("summarizer", "reasoner")
    workflow.add_edge("reasoner", END)

    return workflow.compile()

analyst_graph_app = create_analyst_graph()
