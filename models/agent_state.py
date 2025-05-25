"""
Definition of the agent state used in the workflow.
"""
from typing import Annotated, List, Dict, Any
from typing_extensions import TypedDict
import operator
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    """
    State object for workflow agents.
    
    Attributes:
        cached_extraction_data_file_path: Path to cached extraction data
        extraction_filepath_dict: Dictionary mapping document types to file paths
        application_data: Application data from the applicant
        extracted_data: Data extracted from documents
        validation_result: Results of validation
        decision: Decision made by the model
        chatbot_conversation: List of conversation messages
        recommendations: Recommendations for the applicant
        messages: Messages passed between agents
    """
    cached_extraction_data_file_path: str
    extraction_filepath_dict: Dict[str, str]
    application_data: Dict[str, Any]
    extracted_data: Dict[str, Any]
    validation_result: Dict[str, Any]
    decision: Dict[str, Any]
    chatbot_conversation: List[str]
    recommendations: str
    messages: Annotated[List[AnyMessage], operator.add]