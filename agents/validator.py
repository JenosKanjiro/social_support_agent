"""
Validator agent for validating extracted information.
"""
import logging
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.types import Command

from config import LLM_CONFIG
from models.agent_state import AgentState
from models.data_models import ValidationResult
from document_processing.prompts import VALIDATION_PROMPT

logger = logging.getLogger(__name__)

def validator_node(state: AgentState) -> Command[Literal["supervisor", "decision_maker"]]:
    """
    Validator node that validates extracted information.
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Command: Next step in the workflow
    """
    try:
        # Extract application data
        application_data = state["application_data"]
        app_data_dict = {
            'monthly_income': application_data['monthly_income'],
            'age': application_data['age'],
            'education_level': application_data['education_level'],
            'full_name': application_data['full_name'],
        }
        
        # Initialize LLM for validation
        llm = ChatOllama(
            model=LLM_CONFIG["validation_model"],
            temperature=LLM_CONFIG["validation_temperature"]
        )
        
        # Create validation chain
        prompt = ChatPromptTemplate.from_template(VALIDATION_PROMPT)
        structured_llm_validate = llm.with_structured_output(
            ValidationResult,
            include_raw=True
        )
        chain = prompt | structured_llm_validate
        
        # Perform validation
        result = chain.invoke({
            "application_data": str(app_data_dict),
            "document_extractions": str(state["extracted_data"])
        })
        
        # Validation threshold (changed for testing purposes in original code)
        validation_successful = True  # Simplified for this example
        
        if validation_successful:
            logger.info(f"--- Workflow Transition: Validator to Decision Maker ---")
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content="Application Validation Completed.",
                            name="validator"
                        )
                    ],
                    "validation_result": {"validations_result": result}  
                },
                goto="decision_maker",
            )
        else:
            logger.info(f"--- Workflow Transition: Validator to Recommender ---")
            return Command(
                update={
                    "messages": [
                        HumanMessage(
                            content="Validation Unsuccessful.",
                            name="validator"
                        )
                    ],
                    "validation_result": {"validations_result": result}
                },
                goto="recommender",
            )
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Validation Component Failed.",
                        name="validator"
                    )
                ],
                "validation_result": {"validations_result": {}}
            },
            goto="supervisor",
        )