"""
Extractor agent for extracting information from documents.
"""
import logging
from typing import Literal
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from models.agent_state import AgentState
from document_processing.extraction import extract_documents, load_cached_extraction_data

logger = logging.getLogger(__name__)

def extractor_node(state: AgentState) -> Command[Literal["validator", "supervisor"]]:
    """
    Extractor node that extracts information from documents.
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Command: Next step in the workflow
    """
    try:
        # Check if cached extraction data is available
        if state["cached_extraction_data_file_path"] != "":
            extracted_data = load_cached_extraction_data()
            if extracted_data:
                logger.info(f"--- Workflow Transition: Extractor to Validator ---")
                return Command(
                    update={
                        "messages": [
                            HumanMessage(
                                content="Extraction completed.",
                                name="extractor"
                            )
                        ],
                        "extracted_data": extracted_data
                    },
                    goto="validator",
                )
        
        # Extract information from documents
        result_str = extract_documents(state["extraction_filepath_dict"])
        
        # Proceed to validation
        logger.info(f"--- Workflow Transition: Extractor to Validator ---")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Extraction completed.",
                        name="extractor"
                    )
                ],
                "extracted_data": result_str
            },
            goto="validator",
        )
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Extraction Component Failed.",
                        name="extractor"
                    )
                ],
                "extracted_data": {}
            },
            goto="supervisor",
        )