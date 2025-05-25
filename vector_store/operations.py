"""
Vector store operations for the Social Support Application Processing System.
"""
import os
import logging
from typing import List
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.schema import Document

from config import VECTOR_STORE_DIR, EMBEDDING_MODEL, EMBEDDING_BASE_URL

logger = logging.getLogger(__name__)

def setup_embedding_model():
    """
    Set up the embedding model for vector operations.
    """
    ollama_embedding = OllamaEmbedding(
        model_name=EMBEDDING_MODEL,
        base_url=EMBEDDING_BASE_URL,
        ollama_additional_kwargs={"mirostat": 0},
    )
    Settings.embed_model = ollama_embedding

def add_to_vector_store(text: str) -> bool:
    """
    Add text to the vector store.
    
    Args:
        text: Text to add to the vector store
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set up embedding model
        setup_embedding_model()
        
        # Add document to vector store
        if os.path.exists(VECTOR_STORE_DIR):
            logger.info("Loading existing index...")
            storage_context = StorageContext.from_defaults(persist_dir=VECTOR_STORE_DIR)
            index = load_index_from_storage(storage_context)
            index.insert(Document(text=text))
            index.storage_context.persist(persist_dir=VECTOR_STORE_DIR)
        else:
            logger.info("Creating new index...")
            documents = [Document(text=text)]
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(VECTOR_STORE_DIR)
            
        return True
    except Exception as e:
        logger.error(f"Error adding to vector store: {str(e)}")
        return False

def query_vector_db(query: str) -> List[str]:
    """
    Query the vector database for relevant text.
    
    Args:
        query: Query string
    
    Returns:
        List[str]: List of retrieved text chunks
    
    Raises:
        Exception: If query fails
    """
    try:
        # Set up embedding model
        setup_embedding_model()
        
        # Load persistent index
        if not os.path.exists(VECTOR_STORE_DIR):
            logger.warning("Vector store directory does not exist.")
            return []
            
        storage_context = StorageContext.from_defaults(persist_dir=VECTOR_STORE_DIR)
        index = load_index_from_storage(storage_context)
        
        # Get retriever
        retriever = index.as_retriever()
        
        # Retrieve top matching nodes
        retrieved_nodes = retriever.retrieve(query)
        
        # Extract content from nodes
        list_texts = []
        logger.info("\nTop Retrieved Passages:\n")
        for i, node in enumerate(retrieved_nodes, 1):
            content = node.get_content()
            list_texts.append(content)
            logger.info(f"[{i}] {content}\n")
            
        return list_texts
    except Exception as e:
        logger.error(f"Error querying vector database: {str(e)}")
        raise