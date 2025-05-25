"""
Supervisor agent for coordinating workflow in the Social Support Application Processing System.
"""
import logging
from typing import List, Literal
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.types import Command
from langgraph.graph import END
from config import LLM_CONFIG
from models.agent_state import AgentState
from models.data_models import Supervisor

logger = logging.getLogger(__name__)

def supervisor_node(state: AgentState) -> Command[Literal["extractor", "chatbot", "__end__"]]:
    """
    Supervisor node that coordinates workflow and routes to the appropriate specialist.
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Command: Next step in the workflow
    """
    # If the message is a user query that isn't starting an application, route to chatbot
    if isinstance(state["messages"][-1], tuple) and state["messages"][-1][-1] != "CODE-STARTAPPLICATION":
        logger.info("--- Workflow Transition: Supervisor to chatbot ---")
        return Command(
            update={
                "messages": [
                    HumanMessage(content=state["messages"][-1][-1], name="supervisor")
                ]
            },
            goto="chatbot",
        )
    else:
        # Handle agent response messages
        goto = ""
        reason = ""
        if isinstance(state["messages"][-1], HumanMessage):
            if (state["messages"][-1].name == "validator" and state["messages"][-1].content == "Validation Unsuccessful."):
                goto == "FINISH"
                reason = "Document Validation Failed."
                
            
            elif (state["messages"][-1].name == "validator" and state["messages"][-1].content ==  "Validation Component Failed."):
                goto == "FINISH"
                reason = "Validation Component Failed."

            elif (state["messages"][-1].name == "extractor" and state["messages"][-1].content == "Extraction Unsuccessful."):
                goto == "FINISH"
                reason = "Information Extraction from Documents Failed."

                
            elif (state["messages"][-1].name == "extractor" and state["messages"][-1].content == "Extraction Component Failed."):
                goto == "FINISH"
                reason = "Information Extraction component failed."

            elif state["messages"][-1].name == "decision_maker" and state["messages"][-1].content == "Decision made: only Financial Support Approved.":
                goto == "FINISH"
                reason = "Since, only Financial Support was approved, there is no need to generate recommendations for Economic Enablement, and only next steps in the process needs to be communicated to the applicant."

            elif state["messages"][-1].name == "decision_maker" and state["messages"][-1].content == "Decision Making Component Failed.":  
                goto == "FINISH"
                reason = "Decision Making Component Failed."

            elif state["messages"][-1].name == "recommender" and state["messages"][-1].content == "Process Complete (Extraction - Validation - Decision - Recommendation)":
                goto == "FINISH"
                reason = "Decision and Recommendation generation complete."

            elif state["messages"][-1].name == "recommender" and state["messages"][-1].content == "Process Complete (Extraction - Validation - Recommendation)":
                goto == "FINISH"
                reason = "No Decision needed, Recommendation generation complete."

            elif state["messages"][-1].name == "recommender" and state["messages"][-1].content == "Recommender Component Failed.":
                goto == "FINISH"
                reason = "Recommender Component Failed."

            elif state["messages"][-1].name == "chatbot":
                goto == "FINISH"
                reason = "Chatbot Job finished."

            elif state["messages"][-1].name == "chatbot":
                goto == "FINISH"
                reason = "Error generating response for the user."

            print(" --- Transitioning to END ---")  
            return Command(
                update={
                    "messages": [
                        HumanMessage(content=reason, name="supervisor")
                    ]
                },
                goto=END,  
                )
        
        # For other situations, use LLM to determine next step
        system_prompt = '''
            **Team Members**:
            1. **Extractor** - Always prefer this first. Extracts details to be used by subsequent workers.

            **Your Responsibilities**:
            1. Analyze each user request and agent response for completeness, accuracy, and relevance.
            2. Route the task to the most appropriate agent at each decision point.
            3. Maintain workflow momentum by avoiding redundant agent assignments.
            4. Continue the process until the user's request is fully and satisfactorily resolved.
            Return output as JSON as follows:
            - goto: name of the worker node, like extractor, etc.
            - reason: reason for choosing.
        '''
        
        llm = ChatOllama(
            model=LLM_CONFIG["validation_model"],
            temperature=LLM_CONFIG["validation_temperature"]
        )
        
        # Convert state messages to format expected by LLM
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"] + [{"role": "user", "content": "Get the details about the applicant from all the submitted documents"},]
        # Get next step from LLM
        response = llm.with_structured_output(Supervisor).invoke(messages)
        goto = response.next
        reason = response.reason
        
        # Handle "FINISH" as a synonym for "__end__"
        if goto == "FINISH" or goto == "__end__":
            goto = "__end__"
            logger.info(" --- Transitioning to END ---")
        else:
            logger.info(f"--- Workflow Transition: Supervisor to EXTRACTOR ---")
        return Command(
            update={
                "messages": [
                    HumanMessage(content=reason, name="supervisor")
                ]
            },
            goto=goto.lower(),
        )