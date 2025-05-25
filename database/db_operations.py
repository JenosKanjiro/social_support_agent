"""
Database operations for the Social Support Application Processing System.
"""
import logging
import psycopg2
from typing import Dict, Any, Optional
from config import DB_CONFIG

logger = logging.getLogger(__name__)

def get_connection():
    """
    Create and return a database connection.
    
    Returns:
        psycopg2.connection: Database connection object
    
    Raises:
        Exception: If connection fails
    """
    try:
        conn = psycopg2.connect(
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            host=DB_CONFIG["host"],
            password=DB_CONFIG["password"]
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def initialize_database():
    """
    Initialize the database by creating necessary tables if they don't exist.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create applicant table
        cursor.execute('''CREATE TABLE IF NOT EXISTS applicant
                 (
                    id SERIAL PRIMARY KEY,
                    applicant_id TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    date_of_birth TEXT,
                    gender TEXT,
                    nationality TEXT,
                    emirates_id TEXT,
                    address TEXT)''')
        
        # Create application table
        cursor.execute('''CREATE TABLE IF NOT EXISTS application
                 (
                    id SERIAL PRIMARY KEY,
                    applicant_id TEXT,
                    created_at TEXT,
                    support_type TEXT,
                    status TEXT,
                    processing_completed_at TEXT,
                    decision TEXT,
                    decision_reason TEXT,
                    decision_explanation TEXT,
                    decision_date TEXT,
                    enablement_recommendations TEXT,
                    documents TEXT,
                    validation_results TEXT)''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False

def save_applicant(applicant_data: Dict[str, Any]) -> Optional[str]:
    """
    Save applicant data to the database.
    
    Args:
        applicant_data: Dictionary containing applicant information
    
    Returns:
        str: Applicant ID if successful, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insert applicant data
        cursor.execute(
            """
            INSERT INTO applicant 
            (applicant_id, created_at, updated_at, first_name, last_name, 
            date_of_birth, gender, nationality, emirates_id, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING applicant_id
            """,
            (
                applicant_data.get("applicant_id"),
                applicant_data.get("created_at"),
                applicant_data.get("updated_at"),
                applicant_data.get("first_name"),
                applicant_data.get("last_name"),
                applicant_data.get("date_of_birth"),
                applicant_data.get("gender"),
                applicant_data.get("nationality"),
                applicant_data.get("emirates_id"),
                applicant_data.get("address")
            )
        )
        
        applicant_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return applicant_id
    except Exception as e:
        logger.error(f"Error saving applicant: {str(e)}")
        return None

def save_application(application_data: Dict[str, Any]) -> Optional[int]:
    """
    Save application data to the database.
    
    Args:
        application_data: Dictionary containing application information
    
    Returns:
        int: Application ID if successful, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insert application data
        cursor.execute(
            """
            INSERT INTO application 
            (applicant_id, created_at, support_type, status, processing_completed_at,
            decision, decision_reason, decision_explanation, decision_date,
            enablement_recommendations, documents, validation_results)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                application_data.get("applicant_id"),
                application_data.get("created_at"),
                application_data.get("support_type"),
                application_data.get("status"),
                application_data.get("processing_completed_at"),
                application_data.get("decision"),
                application_data.get("decision_reason"),
                application_data.get("decision_explanation"),
                application_data.get("decision_date"),
                application_data.get("enablement_recommendations"),
                application_data.get("documents"),
                application_data.get("validation_results")
            )
        )
        
        application_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return application_id
    except Exception as e:
        logger.error(f"Error saving application: {str(e)}")
        return None

def get_applicant(applicant_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve applicant data from the database.
    
    Args:
        applicant_id: ID of the applicant to retrieve
    
    Returns:
        Dict: Applicant data if found, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM applicant WHERE applicant_id = %s",
            (applicant_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        # Convert to dictionary
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result))
    except Exception as e:
        logger.error(f"Error retrieving applicant: {str(e)}")
        return None

def get_application(application_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve application data from the database.
    
    Args:
        application_id: ID of the application to retrieve
    
    Returns:
        Dict: Application data if found, None otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM application WHERE id = %s",
            (application_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        # Convert to dictionary
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result))
    except Exception as e:
        logger.error(f"Error retrieving application: {str(e)}")
        return None