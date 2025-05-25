"""
Machine learning model inference for the Social Support Application Processing System.
"""
import os
import logging
import pickle
import pandas as pd
from pandas import Index
import xgboost as xgb
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from typing import Dict, Any, Tuple

from config import MODEL_PATH, LABEL_ENCODER_PATH, LLM_CONFIG
from document_processing.prompts import ELIGIBILITY_AGENT_PROMPT

logger = logging.getLogger(__name__)

def load_model_and_encoder():
    """
    Load the XGBoost model and label encoder.
    
    Returns:
        Tuple: (model, label_encoder)
    
    Raises:
        Exception: If loading fails
    """
    try:
        # Load model
        model = xgb.XGBClassifier()
        model.load_model(MODEL_PATH)
        
        # Load label encoder
        with open(str(LABEL_ENCODER_PATH), 'rb') as f:
            label_encoder = pickle.load(f)
            
        return model, label_encoder
    except Exception as e:
        logger.error(f"Error loading model or encoder: {str(e)}")
        raise

def predict_eligibility(
    application_data: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Predict eligibility for social support based on application data.
    
    Args:
        application_data: Dictionary containing application information
        
    Returns:
        Tuple: (decision, reason)
        
    Raises:
        Exception: If prediction fails
    """
    try:
        # Load model and encoder
        model, label_encoder = load_model_and_encoder()
        
        # Prepare feature columns
        X_columns = Index([
            'monthly_income', 'assets', 'liabilities', 'household_size', 'age',
            'education_level_bachelor\'s', 'education_level_high school',
            'education_level_master\'s', 'education_level_uneducated',
            'marital_status_Married', 'marital_status_Single'
        ])
        
        # Create input data dictionary
        input_data = {
            'monthly_income': application_data['monthly_income'],
            'assets': application_data['assets'],
            'liabilities': application_data['liabilities'],
            'household_size': application_data['household_size'],
            'age': application_data['age']
        }
        
        # Create one-hot encoded columns for education_level
        for level in ['bachelor\'s', 'high school', 'master\'s', 'uneducated']:
            input_data[f'education_level_{level}'] = 1 if application_data['education_level'] == level else 0
        
        # Create one-hot encoded columns for marital_status
        for status in ['Married', 'Single']:
            input_data[f'marital_status_{status}'] = 1 if application_data['marital_status'] == status else 0
        
        # Create DataFrame with the input data
        input_df = pd.DataFrame([input_data])
        
        # Ensure columns match the training data
        missing_cols = set(X_columns) - set(input_df.columns)
        for col in missing_cols:
            input_df[col] = 0
        
        # Ensure column order matches the training data
        input_df = input_df[X_columns]
        
        # Make prediction
        prediction = model.predict(input_df)[0]
        
        # Convert prediction back to original label
        decision = label_encoder.inverse_transform([prediction])[0]
        
        # Get reasoning for decision using LLM
        llm = ChatOllama(
            model=LLM_CONFIG["validation_model"],
            temperature=LLM_CONFIG["validation_temperature"]
        )
        
        prompt = ChatPromptTemplate.from_template(ELIGIBILITY_AGENT_PROMPT)
        chain = prompt | llm
        
        result = chain.invoke({
            'monthly_income': application_data['monthly_income'],
            'assets': application_data['assets'],
            'liabilities': application_data['liabilities'],
            'household_size': application_data['household_size'],
            'age': application_data['age'],
            'education_level': application_data['education_level'],
            'marital_status': application_data['marital_status'],
            'decision': decision
        })
        
        # Extract reason from result (assuming result.content has the reason)
        reason = result.content.split("</think>")[-1].strip()
        
        return decision, reason
    except Exception as e:
        logger.error(f"Error predicting eligibility: {str(e)}")
        raise