"""
Decision maker agent for making decisions on social support applications.
"""
import logging
from typing import Literal
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from models.agent_state import AgentState
from inference.decision_model import predict_eligibility

logger = logging.getLogger(__name__)

def decision_maker_node(state: AgentState) -> Command[Literal["supervisor", "recommender"]]:
    """
    Decision maker node that makes decisions on social support applications.
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Command: Next step in the workflow
    """
    try:
        # Get application data
        application_data = state["application_data"]
        
        # Make prediction
        decision, reason = predict_eligibility(application_data)
        
        # Determine next step based on decision
        if decision == "Financial Support Approved":
            logger.info(f"--- Workflow Transition: Decision Maker to Supervisor ---")
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content="Decision made: only Financial Support Approved.",
                            name="decision_maker"
                        )
                    ],
                    "decision": {
                        "decision": decision,
                        "reason": reason
                    }
                },
                goto="supervisor",
            )
        else:
            logger.info(f"--- Workflow Transition: Decision Maker to Recommender ---")
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content="Decision made.",
                            name="decision_maker"
                        )
                    ],
                    "decision": {
                        "decision": decision,
                        "reason": reason
                    }
                },
                goto="recommender",
            )
    except Exception as e:
        logger.error(f"Decision making error: {str(e)}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Decision Making Component Failed.",
                        name="decision_maker"
                    )
                ],
                "decision": {}
            },
            goto="supervisor",
        )