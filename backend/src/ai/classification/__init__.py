"""
DX-AI Manufacturing Copilot - 텍스트 분류 서비스
AI 기반 텍스트 분류 및 라벨링 기능
"""

from .service import ClassificationService, get_classification_service
from .models import ClassificationRequest, ClassificationResponse, Category

__all__ = [
    "ClassificationService",
    "get_classification_service",
    "ClassificationRequest",
    "ClassificationResponse", 
    "Category",
] 