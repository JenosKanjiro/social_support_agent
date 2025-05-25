"""
Main entry point for the Social Support Application Processing System.
"""
import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from database.db_operations import initialize_database, save_applicant, save_application
from workflow.graph import create_workflow_graph, print_workflow_graph
from config import EXTRACTION_CACHE_PATH, STORAGE_DIR


logger = logging.getLogger(__name__)


def get_saved_states(app, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get the history of checkpoints
    history = []
    for checkpoint in app.get_state_history(config):
        history.append(checkpoint)
    
    return history

# Get current state
def get_current_state(app, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    current_state = app.get_state(config)
    return current_state



def process_query(query: str, app) -> Optional[Dict[str, Any]]:
    """
    Process a user query.
    
    Args:
        query: User query
    
    Returns:
        Dict: Query processing results
    """
    try:
        logger.info(f"Processing user query: {query}")

        state_history = get_saved_states(app, "social_support_agent")
        logger.info(f"Found {len(state_history)} checkpoints in history")
        
        # Prepare initial state

        if len(state_history) > 0:
            initial_state = get_current_state(app, "social_support_agent")[0]
            templist = initial_state["messages"].copy()
            templist.append(("user", query))
            initial_state["messages"] = templist
            try:
                logger.info("Chatbot History: {}".format(str(initial_state["chatbot_conversation"])))
            except:
                initial_state["chatbot_conversation"] = []
        else:
            initial_state = {
                "extraction_filepath_dict": {},
                "application_data": {},
                "cached_extraction_data_file_path": "",
                "extracted_data": {},
                "validation_result": {},
                "decision": {},
                "chatbot_conversation": [],
                "recommendations": "",
                "messages": [
                    ("user", query)
                ]
            }
        logger.info("Current state:{}".format(str(initial_state)))
            
        config = {"configurable":{"thread_id":"social_support_agent"}}
        # Invoke workflow
        results = app.invoke(initial_state, config = config)
        
        return results
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return None


def process_application(
    emirates_id_path: str,
    bank_statement_path: str,
    credit_report_path: str,
    resume_path: str,
    assets_liabilities_path: str,
    application_data: Dict[str, Any],
    app,
    emirates_id_file, bank_statement_file, credit_report_file, 
                resume_file, assets_liabilities_file,
    use_cached_extraction: bool = False,
) -> Dict[str, Any]:
    """
    Process a social support application.
    
    Args:
        emirates_id_path: Path to Emirates ID document
        bank_statement_path: Path to bank statement document
        credit_report_path: Path to credit report document
        resume_path: Path to resume document
        assets_liabilities_path: Path to assets/liabilities spreadsheet
        application_data: Application data
        use_cached_extraction: Whether to use cached extraction data
    
    Returns:
        Dict: Processing results
    """
    try:
        logger.info("Starting application processing")
        
        # Prepare initial state
        state_history = get_saved_states(app, "social_support_agent")
        logger.info(f"Found {len(state_history)} checkpoints in history")
        
        # Prepare initial state
        cacheFile = ""

        if  ((emirates_id_file.split("\\")[-1] == "eida.png") and (bank_statement_file.split("\\")[-1] == "BankStatement.pdf") and (credit_report_file.split("\\")[-1] == "credit-report.png") and (resume_file.split("\\")[-1] == "Resume.pdf") and (assets_liabilities_file.split("\\")[-1] == "Assets-Liabilities.xlsx")):
            cacheFile = str(EXTRACTION_CACHE_PATH)


        if len(state_history) > 0:
            initial_state = get_current_state(app, "social_support_agent")[0]
            templist = initial_state["messages"].copy()
            templist.append(("user", "CODE-STARTAPPLICATION"))
            initial_state["messages"] = templist
            initial_state['extraction_filepath_dict'] =  {
                    "emirates_id_file_path": emirates_id_path,
                    "bank_statements_file_path": bank_statement_path,
                    "credit_report_file_path": credit_report_path,
                    "resume_file_path": resume_path,
                    "assets_liabilities_file_path": assets_liabilities_path
                }
            initial_state["application_data"] = application_data
            initial_state["cached_extraction_data_file_path"] = cacheFile

        else:
            initial_state = {
                "extraction_filepath_dict": {
                    "emirates_id_file_path": emirates_id_path,
                    "bank_statements_file_path": bank_statement_path,
                    "credit_report_file_path": credit_report_path,
                    "resume_file_path": resume_path,
                    "assets_liabilities_file_path": assets_liabilities_path
                },
                "application_data": application_data,
                "cached_extraction_data_file_path": cacheFile,
                "messages": [
                    ("user", "CODE-STARTAPPLICATION")
                ]
            }
        logger.info("Current state:{}".format(str(initial_state)))

        config = {"configurable":{"thread_id":"social_support_agent"}}
        # Invoke workflow
        results = app.invoke(initial_state, config = config)
        
        # Process results
        current_time = datetime.now().isoformat()
        
        # Save applicant data
        applicant_data = {
            "applicant_id": application_data.get("applicant_id", ""),
            "created_at": current_time,
            "updated_at": current_time,
            "first_name": application_data.get("first_name", ""),
            "last_name": application_data.get("last_name", ""),
            "date_of_birth": application_data.get("date_of_birth", ""),
            "gender": application_data.get("gender", ""),
            "nationality": application_data.get("nationality", ""),
            "emirates_id": application_data.get("emirates_id", ""),
            "address": application_data.get("address", "")
        }
        save_applicant(applicant_data)
        
        # Save application data
        application_data = {
            "applicant_id": application_data.get("applicant_id", ""),
            "created_at": current_time,
            "support_type": results.get("decision", {}).get("decision", ""),
            "status": "Completed",
            "processing_completed_at": datetime.now().isoformat(),
            "decision": results.get("decision", {}).get("decision", ""),
            "decision_reason": results.get("decision", {}).get("reason", ""),
            "decision_explanation": "",
            "decision_date": current_time,
            "enablement_recommendations": results.get("recommendations", ""),
            "documents": str(initial_state["extraction_filepath_dict"]),
            "validation_results": str(results.get("validation_result", {}))
        }
        save_application(application_data)
        
        return results
    except Exception as e:
        logger.error(f"Error processing application: {str(e)}")
        return {"error": str(e)}


def queryChatbot(queryText: str) -> str:
    query_results = process_query(queryText)
    
    if query_results and 'chatbot_conversation' in query_results:
        for message in query_results['chatbot_conversation']:
            print(message)
    return message


def main():
    """
    Main function for the Social Support Application Processing System.
    """
    # Initialize database
    #initialize_database()
    
    # Print workflow graph
    print_workflow_graph()
    
    # Example application data
    application_data = {
        'monthly_income': 3500,
        'assets': 15000,
        'liabilities': 45000,
        'household_size': 5,
        'age': 42,
        'education_level': 'high school',
        'marital_status': 'Single',
        'first_name': 'Mohamed',
        'last_name': 'Yunus Ali Khan Samiullah',
        'full_name': 'Mohamed Yunus Ali Khan Samiullah',
        'date_of_birth': '01/12/1995',
        'gender': 'MALE',
        'nationality': 'INDIA',
        'emirates_id': '784.1995-5406984-1',
        'address': '102 DOUBLE TREE HILTON 9639 ABU DHABI UNITED ARAB EMIRATES'
    }
    
    # Example application processing
    """
    results = process_application(
        emirates_id_path= STORAGE_DIR / "eida.png",
        bank_statement_path= STORAGE_DIR / "BankStatement.pdf",
        credit_report_path= STORAGE_DIR / "credit-report.png",
        resume_path= STORAGE_DIR / "Resume.pdf",
        assets_liabilities_path= STORAGE_DIR / "Assets-Liabilities.xlsx",
        application_data=application_data
    )
    """
    
    chatbotResult = queryChatbot("What is the Emirates ID number?")

    logger.info(f"Application processing complete: {chatbotResult}")

if __name__ == "__main__":
    main()