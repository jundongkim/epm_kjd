"""
DX-AI Manufacturing Copilot - AI 핵심 모듈
"""

from .base import BaseAIService
from .context_engineering import ContextEngineer, get_context_engineer
from .llm_client import (
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
# 보고서 생성기 제거됨
# from .ai_report_generator import (
#     EnhancedAIReportGenerator,
#     AIReportGenerator,
#     ReportGenerationConfig,
#     ReportGenerationState,
#     create_report_generator,
#     generate_production_report,
#     generate_quality_report,
#     generate_cost_report,
#     generate_equipment_report,
#     generate_report_async
# )

__all__ = [
    "BaseAIService",
    "ContextEngineer", 
    "get_context_engineer",
    "EnhancedOllamaClient",
    "OllamaClient",
    "OllamaCallbackHandler", 
    "get_ollama_client",
    "create_ollama_client",
    "get_chatbot_client",
    "get_classification_client", 
    "get_report_client",
    "get_context_client",
    # 보고서 생성기 관련 항목들 제거됨
] 