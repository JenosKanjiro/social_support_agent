"""
Workflow graph construction for the Social Support Application Processing System.
"""
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from models.agent_state import AgentState
from agents.supervisor import supervisor_node
from agents.extractor import extractor_node
from agents.validator import validator_node
from agents.decision_maker import decision_maker_node
from agents.recommender import recommender_node
from agents.chatbot import chatbot_node

logger = logging.getLogger(__name__)

def create_workflow_graph():
    """
    Create the workflow graph for the Social Support Application Processing System.
    
    Returns:
        StateGraph: Compiled workflow graph
    """
    # Create state graph
    graph = StateGraph(AgentState)
    
    # Add nodes to graph
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("validator", validator_node)
    graph.add_node("decision_maker", decision_maker_node)
    graph.add_node("recommender", recommender_node)
    graph.add_node("chatbot", chatbot_node)
    
    # Add edges to graph
    graph.add_edge(START, "supervisor")
    
    memory = InMemorySaver()
    # Compile graph
    app = graph.compile(checkpointer=memory)
    
    return app

def print_workflow_graph():
    """
    Print a text representation of the workflow graph.
    """
    graph = create_workflow_graph()
    graph.get_graph().print_ascii()