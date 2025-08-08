"""
DX-AI Manufacturing Copilot - AI 모듈
통합 AI 서비스 인터페이스 제공
"""

from .chatbot import ChatbotService, get_chatbot_service
from .classification import ClassificationService, get_classification_service
from .core import (
    BaseAIService, 
    ContextEngineer, 
    get_context_engineer,
    EnhancedOllamaClient,
    OllamaClient,
    OllamaCallbackHandler,
    get_ollama_client,
    create_ollama_client,
    get_chatbot_client,
    get_classification_client,
    get_report_client,
    get_context_client
)

__version__ = "2.0.0"

__all__ = [
    # Services
    "ChatbotService",
    "get_chatbot_service", 
    "ClassificationService",
    "get_classification_service",
    
    # Core AI components
    "BaseAIService",
    "ContextEngineer",
    "get_context_engineer",
    
    # LLM Client components
    "EnhancedOllamaClient",
    "OllamaClient",
    "OllamaCallbackHandler",
    "get_ollama_client", 
    "create_ollama_client",
    "get_chatbot_client",
    "get_classification_client",
    "get_report_client", 
    "get_context_client",
    
    # AI Report Generator components - 제거됨
    
    # Version
    "__version__"
]


def get_ai_module_info():
    """AI 모듈 정보 반환"""
    return {
        "version": __version__,
        "services": ["chatbot", "classification"],
        "llm_providers": ["ollama"],
        "features": [
            "context_engineering",
            "service_optimization", 
            "batch_processing",
            "async_support",
            "performance_monitoring"
        ]
    } 