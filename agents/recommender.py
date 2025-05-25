"""
Recommender agent for providing recommendations based on application decision.
"""
import logging
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.types import Command

from config import LLM_CONFIG
from models.agent_state import AgentState
from document_processing.prompts import (
    RECOMMENDATION_AGENT_PROMPT,
    VALIDATION_FAILURE_RECOMMENDATION_PROMPT
)

logger = logging.getLogger(__name__)

def recommender_node(state: AgentState) -> Command[Literal["supervisor"]]:
    """
    Recommender node that provides recommendations based on application decision.
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Command: Next step in the workflow
    """
    try:
        # Initialize LLM
        llm = ChatOllama(
            model=LLM_CONFIG["validation_model"],
            temperature=LLM_CONFIG["validation_temperature"]
        )
        
        # Handle validation failure case
        if (isinstance(state["messages"][-1], HumanMessage) and 
            state["messages"][-1].name == "validator" and 
            state["messages"][-1].content == "Validation Unsuccessful."):
            
            # Create validation failure recommendation chain
            prompt = ChatPromptTemplate.from_template(VALIDATION_FAILURE_RECOMMENDATION_PROMPT)
            chain = prompt | llm
            
            # Generate recommendations
            result = chain.invoke({
                'data_collected_from_emirates_id': state['extracted_data']['EID_Extract_In_Text'],
                'data_collected_from_bank_statements': state['extracted_data']['BankS_Extract_In_Text'],
                'data_collected_from_resume': state['extracted_data']['Resume_Extract_In_Text']
            })
            
            logger.info(" --- Transitioning to supervisor ---")
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content="Process Complete (Extraction - Validation - Recommendation)",
                            name="recommender"
                        )
                    ],
                    "recommendations": result.content.split("</think>")[-1],
                },
                goto="supervisor",
            )
        
        # Handle normal recommendation case
        application_data = state["application_data"]
        
        # Create recommendation chain
        prompt = ChatPromptTemplate.from_template(RECOMMENDATION_AGENT_PROMPT)
        chain = prompt | llm
        
        # Generate recommendations
        result = chain.invoke({
            'decision': state["decision"]["decision"],
            'reason': state["decision"]["reason"],
            'monthly_income': application_data['monthly_income'],
            'assets': application_data['assets'],
            'liabilities': application_data['liabilities'],
            'household_size': application_data['household_size'],
            'age': application_data['age'],
            'education_level': application_data['education_level'],
            'marital_status': application_data['marital_status'],
        })
        
        logger.info(f"--- Workflow Transition: Recommender to Supervisor ---")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Process Complete (Extraction - Validation - Decision - Recommendation)",
                        name="recommender"
                    )
                ],
                "recommendations": result.content.split("</think>")[-1]
            },
            goto="supervisor",
        )
    except Exception as e:
        logger.error(f"Recommendation error: {str(e)}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Recommender Component Failed.",
                        name="recommender"
                    )
                ],
                "recommendations": ""
            },
            goto="supervisor",
        )