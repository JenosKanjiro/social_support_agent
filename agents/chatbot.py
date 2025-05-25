"""
Chatbot agent for interacting with users.
"""
import logging
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.types import Command

from config import LLM_CONFIG
from models.agent_state import AgentState
from vector_store.operations import query_vector_db
from document_processing.prompts import CONVERSATION_PROMPT

logger = logging.getLogger(__name__)


def chatbot_node(state: AgentState) -> Command[Literal["supervisor"]]:
    """
    Chatbot node that interacts with users.
    
    Args:
        state: Current state of the workflow
    
    Returns:
        Command: Next step in the workflow
    """
    try:
        # Record user message
        message_list = state["chatbot_conversation"]
        message_list.append("User: " + state["messages"][-1].content)
        print(message_list)
        logger.info("User message: {}".format(str(state["messages"][-1].content)))
        logger.info("Chatbot Conversation: {}".format(str(message_list)))
        
        # Query vector DB for context
        context_text = query_vector_db("\n".join(message_list))[0] if query_vector_db("\n".join(message_list)) else ""
        
        # Initialize LLM
        llm = ChatOllama(
            model=LLM_CONFIG["validation_model"],
            temperature=LLM_CONFIG["validation_temperature"]
        )
        
        # Create conversation chain
        prompt = ChatPromptTemplate.from_template(CONVERSATION_PROMPT)
        chain = prompt | llm
        
        # Generate response
        result = chain.invoke({
            "contextText": context_text,
            "userQuestion": state["messages"][-1].content,
            "chatHistory": "\n".join(message_list)
        })
        
        # Record system response
        system_response = result.content.split("</think")[-1].strip()
        message_list.append("System: " + system_response)
        
        logger.info(f"--- Workflow Transition: Chatbot to Supervisor ---")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Successfully constructed a reply for the user.",
                        name="chatbot"
                    )
                ],
                "chatbot_conversation": message_list
            },
            goto="supervisor",
        )
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content="Error generating response for the user.",
                        name="chatbot"
                    )
                ],
                "chatbot_conversation": ["User: " + state["messages"][-1].content, 
                                        "System: I apologize, but I encountered an error while processing your request. Please try again."]
            },
            goto="supervisor",
        )