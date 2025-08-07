"""
DX-AI Manufacturing Copilot - 텍스트 분류 데이터 모델
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Category(BaseModel):
    """분류 카테고리 모델"""
    id: str = Field(..., description="카테고리 ID")
    name: str = Field(..., description="카테고리 이름")
    description: Optional[str] = Field(None, description="카테고리 설명")
    examples: Optional[List[str]] = Field(None, description="예시 텍스트")


class ClassificationRequest(BaseModel):
    """텍스트 분류 요청 모델"""
    text: str = Field(..., description="분류할 텍스트")
    categories: List[Category] = Field(..., description="가능한 카테고리 목록")
    confidence_threshold: Optional[float] = Field(0.7, description="신뢰도 임계값")
    model: Optional[str] = Field(None, description="사용할 모델")


class ClassificationResult(BaseModel):
    """분류 결과 모델"""
    category_id: str = Field(..., description="선택된 카테고리 ID")
    category_name: str = Field(..., description="선택된 카테고리 이름")
    confidence: float = Field(..., description="신뢰도 (0.0-1.0)")
    reasoning: Optional[str] = Field(None, description="분류 근거")


class ClassificationResponse(BaseModel):
    """텍스트 분류 응답 모델"""
    text: str = Field(..., description="입력 텍스트")
    result: ClassificationResult = Field(..., description="분류 결과")
    alternatives: Optional[List[ClassificationResult]] = Field(None, description="대안 분류 결과")
    processing_time: float = Field(..., description="처리 시간 (초)")
    model_used: str = Field(..., description="사용된 모델")
    timestamp: str = Field(..., description="처리 시간") 