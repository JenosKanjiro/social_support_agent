"""
OCR functionality for the Social Support Application Processing System.
"""
import logging
from pypdf import PdfReader
import easyocr
from typing import Optional

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        str: Extracted text
    
    Raises:
        Exception: If extraction fails
    """
    try:
        extracted_text = ""
        with open(file_path, 'rb') as pdf_file:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted_text += page.extract_text() + " "
        return extracted_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        raise

def extract_text_from_image(file_path: str) -> str:
    """
    Extract text from an image file using OCR.
    
    Args:
        file_path: Path to the image file
    
    Returns:
        str: Extracted text
    
    Raises:
        Exception: If extraction fails
    """
    try:
        reader = easyocr.Reader(['en'])
        result = reader.readtext(file_path)
        text_extract = ""
        
        for detection in result:
            text_extract += detection[1]
            text_extract += ", "
            
        return text_extract
    except Exception as e:
        logger.error(f"Error extracting text from image {file_path}: {str(e)}")
        raise

def extract_text(file_path: str) -> Optional[str]:
    """
    Extract text from a file based on its type.
    
    Args:
        file_path: Path to the file
    
    Returns:
        str: Extracted text or None if extraction fails
    """
    try:
        if file_path.endswith('.pdf'):
            return extract_text_from_pdf(file_path)
        elif file_path.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            return extract_text_from_image(file_path)
        else:
            logger.error(f"Unsupported file format: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return None