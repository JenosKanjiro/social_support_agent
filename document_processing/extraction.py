"""
Document extraction functionality for the Social Support Application Processing System.
"""
import logging
import pickle
import pandas as pd
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from config import LLM_CONFIG, EXTRACTION_CACHE_PATH
from document_processing.ocr import extract_text
from document_processing.prompts import (
    EXTRACT_EID, EXTRACT_BANK_STATEMENT, EXTRACT_CREDIT_REPORT,
    EXTRACT_RESUME, EXTRACT_ASSET_LIABILITY
)
from models.data_models import (
    EmiratesIDData, BankStatement, CreditReport,
    ResumeInfo, AssetLiabilityExtraction
)
from vector_store.operations import add_to_vector_store

logger = logging.getLogger(__name__)

def load_cached_extraction_data() -> Optional[Dict[str, Any]]:
    """
    Load cached extraction data if available.
    
    Returns:
        Dict or None: Cached extraction data if available, None otherwise
    """
    try:
        with open(str(EXTRACTION_CACHE_PATH), 'rb') as f:
            return pickle.load(f)
    except (FileNotFoundError, pickle.PickleError) as e:
        logger.info(f"No valid cached extraction data found: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error loading cached extraction data: {str(e)}")
        return None

def save_cached_extraction_data(data: Dict[str, Any]) -> bool:
    """
    Save extraction data to cache.
    
    Args:
        data: Extraction data to cache
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(str(EXTRACTION_CACHE_PATH), 'wb') as file:
            pickle.dump(data, file)
        return True
    except Exception as e:
        logger.error(f"Error saving cached extraction data: {str(e)}")
        return False

def extract_documents(filepaths: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract information from all document types.
    
    Args:
        filepaths: Dictionary mapping document types to file paths
    
    Returns:
        Dict: Extracted information from all documents
    
    Raises:
        Exception: If extraction fails
    """
    try:

        # Extract text from documents
        extracts = {}
        for i, filename in enumerate([
            filepaths["emirates_id_file_path"],
            filepaths["credit_report_file_path"],
            filepaths["bank_statements_file_path"],
            filepaths["resume_file_path"]
        ]):
            extracts[str(i)] = extract_text(filename)
        
        # Extract data from assets/liabilities spreadsheet
        df = pd.read_excel(filepaths["assets_liabilities_file_path"], index_col=None)
        asset_liability_string = ""
        for r in range(df.shape[0]):
            asset_liability_string += str({
                "type": df.iloc[r]['Type'],
                "asset_or_liability": df.iloc[r]['Asset_or_Liability'],
                "amount_or_value": df.iloc[r]['Value_or_Cost']
            })
        
        # Initialize LLM
        llm = ChatOllama(
            model=LLM_CONFIG["extraction_model"],
            temperature=LLM_CONFIG["extraction_temperature"]
        )
        
        # Prepare prompt templates
        prompt_eid = ChatPromptTemplate.from_template(EXTRACT_EID)
        prompt_cr = ChatPromptTemplate.from_template(EXTRACT_CREDIT_REPORT)
        prompt_bs = ChatPromptTemplate.from_template(EXTRACT_BANK_STATEMENT)
        prompt_r = ChatPromptTemplate.from_template(EXTRACT_RESUME)
        prompt_al = ChatPromptTemplate.from_template(EXTRACT_ASSET_LIABILITY)
        
        # Prepare structured output models
        structured_llm_eid = llm.with_structured_output(EmiratesIDData, include_raw=True)
        structured_llm_cr = llm.with_structured_output(CreditReport, include_raw=True)
        structured_llm_bs = llm.with_structured_output(BankStatement, include_raw=True)
        structured_llm_r = llm.with_structured_output(ResumeInfo, include_raw=True)
        structured_llm_al = llm.with_structured_output(AssetLiabilityExtraction, include_raw=True)
        
        # Create extraction chains
        chain_eid = prompt_eid | structured_llm_eid
        chain_cr = prompt_cr | structured_llm_cr
        chain_bs = prompt_bs | structured_llm_bs
        chain_r = prompt_r | structured_llm_r
        chain_al = prompt_al | structured_llm_al
        
        # Extract information from each document
        logger.info("Extracting from Emirates ID")
        result_eid = chain_eid.invoke({"text": extracts['0']})
        
        logger.info("Extracting from Credit Report")
        result_cr = chain_cr.invoke({"text": extracts['1']})
        
        logger.info("Extracting from Bank Statement")
        result_bs = chain_bs.invoke({"text": extracts['2']})
        
        logger.info("Extracting from Resume")
        result_r = chain_r.invoke({"text": extracts['3']})
        
        logger.info("Extracting from Assets/Liabilities")
        result_al = chain_al.invoke({"data": asset_liability_string})
        
        # Combine results
        result_str = {
            "EmiratedID_Extract": result_eid,
            "CreditReport_Extract": result_cr,
            "BankStatement_Extract": result_bs,
            "Resume_Extract": result_r,
            "Assets_Liabilities_Extract": result_al
        }
        
        # Convert structured extracts to text format for vector storage
        emirates_id_extract = ""
        for key in result_str['EmiratedID_Extract']['parsed'].__dict__.keys():
            string_to_add = f"{key}: {result_str['EmiratedID_Extract']['parsed'].__dict__[key]}\n"
            emirates_id_extract += string_to_add
        result_str['EID_Extract_In_Text'] = emirates_id_extract
        
        bank_s_extract = ""
        for key in result_str['BankStatement_Extract']['parsed'].__dict__.keys():
            if str(type(result_str['BankStatement_Extract']['parsed'].__dict__[key])).startswith("<class '__main__"):
                string_to_add = f"\n{key}: \n"
                bank_s_extract += string_to_add
                for skey in result_str['BankStatement_Extract']['parsed'].__dict__[key].__dict__.keys():
                    string_to_add = f"{skey}: {result_str['BankStatement_Extract']['parsed'].__dict__[key].__dict__[skey]}\n"
                    bank_s_extract += string_to_add
            else:
                string_to_add = f"\n{key}: \n"
                bank_s_extract += string_to_add
                for item_list in result_str['BankStatement_Extract']['parsed'].__dict__[key]:
                    string_to_add = f"{item_list}\n"
                    bank_s_extract += string_to_add
        result_str['BankS_Extract_In_Text'] = bank_s_extract
        
        resume_extract = ""
        for key in result_str['Resume_Extract']['parsed'].__dict__.keys():
            if str(type(result_str['Resume_Extract']['parsed'].__dict__[key])).startswith("<class '__main__"):
                string_to_add = f"\n{key}: \n"
                resume_extract += string_to_add
                for skey in result_str['Resume_Extract']['parsed'].__dict__[key].__dict__.keys():
                    string_to_add = f"{skey}: {result_str['Resume_Extract']['parsed'].__dict__[key].__dict__[skey]}\n"
                    resume_extract += string_to_add
            else:
                string_to_add = f"\n{key}: \n"
                resume_extract += string_to_add
                for item_list in result_str['Resume_Extract']['parsed'].__dict__[key]:
                    string_to_add = f"{item_list}\n"
                    resume_extract += string_to_add
        result_str['Resume_Extract_In_Text'] = resume_extract
        
        # Add extracted information to vector store
        for tx in [
            emirates_id_extract,
            bank_s_extract,
            resume_extract,
            str(result_str['CreditReport_Extract']['parsed'].__dict__),
            str(result_str['Assets_Liabilities_Extract']['parsed'].__dict__)
        ]:
            add_to_vector_store(tx)
        
        # Cache results
        save_cached_extraction_data(result_str)
        
        return result_str
    except Exception as e:
        logger.error(f"Error during document extraction: {str(e)}")
        raise