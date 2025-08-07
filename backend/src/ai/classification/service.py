"""
DX-AI Manufacturing Copilot - 텍스트 분류 서비스
AI 기반 텍스트 분류 및 라벨링 기능
"""

import json
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.base import BaseAIService
from ..core.context_engineering import get_context_engineer
from ..providers.ollama import get_ollama_provider
from .models import (
    ClassificationRequest, 
    ClassificationResponse, 
    ClassificationResult,
    Category
)

logger = logging.getLogger(__name__)


class ClassificationService(BaseAIService):
    """AI 기반 텍스트 분류 서비스"""
    
    def __init__(self, model: Optional[str] = None):
        """
        분류 서비스 초기화
        
        Args:
            model: 사용할 모델 이름
        """
        provider = get_ollama_provider(model or settings.ollama_model)
        super().__init__("ClassificationService", provider)
        
        # 컨텍스트 엔지니어 추가
        self.context_engineer = get_context_engineer()
        
        logger.info(f"텍스트 분류 서비스 초기화 완료: {provider.model}")
    
    async def process_request(self, request: ClassificationRequest) -> ClassificationResponse:
        """분류 요청 처리"""
        start_time = time.time()
        
        try:
            # 분류 수행
            result = await self.classify_text(
                text=request.text,
                categories=request.categories,
                confidence_threshold=request.confidence_threshold
            )
            
            processing_time = time.time() - start_time
            
            return ClassificationResponse(
                text=request.text,
                result=result,
                processing_time=processing_time,
                model_used=self.provider.model,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"분류 처리 중 오류: {e}")
            raise
    
    async def classify_text(
        self, 
        text: str, 
        categories: List[Category],
        confidence_threshold: float = 0.7
    ) -> ClassificationResult:
        """텍스트 분류 수행"""
        try:
            # 컨텍스트 엔지니어를 활용한 분류 컨텍스트 생성
            classification_context = self.context_engineer.create_specialized_context(
                service_type="classification",
                task_type="text_classification",
                domain_data={
                    "categories_count": len(categories),
                    "confidence_threshold": confidence_threshold
                }
            )
            
            # 분류를 위한 프롬프트 생성
            prompt = self._create_classification_prompt(text, categories)
            
            # AI 응답 생성 (컨텍스트 포함)
            response = await self.provider.generate_response(
                prompt, 
                context=classification_context
            )
            
            # 응답 파싱
            result = self._parse_classification_response(response, categories)
            
            # 신뢰도 체크
            if result.confidence < confidence_threshold:
                logger.warning(f"분류 신뢰도가 임계값보다 낮음: {result.confidence} < {confidence_threshold}")
            
            return result
            
        except Exception as e:
            logger.error(f"텍스트 분류 중 오류: {e}")
            # 기본 결과 반환
            return ClassificationResult(
                category_id="unknown",
                category_name="알 수 없음",
                confidence=0.0,
                reasoning=f"분류 중 오류 발생: {str(e)}"
            )
    
    def _create_classification_prompt(self, text: str, categories: List[Category]) -> str:
        """분류를 위한 프롬프트 생성"""
        categories_info = []
        for cat in categories:
            cat_info = f"- ID: {cat.id}\n  이름: {cat.name}"
            if cat.description:
                cat_info += f"\n  설명: {cat.description}"
            if cat.examples:
                cat_info += f"\n  예시: {', '.join(cat.examples[:3])}"
            categories_info.append(cat_info)
        
        prompt = f"""다음 텍스트를 주어진 카테고리 중 하나로 분류해주세요.

분류할 텍스트:
{text}

가능한 카테고리:
{chr(10).join(categories_info)}

응답 형식 (JSON):
{{
    "category_id": "선택된 카테고리 ID",
    "category_name": "선택된 카테고리 이름",
    "confidence": 0.85,
    "reasoning": "분류 근거 설명"
}}

신뢰도는 0.0에서 1.0 사이의 값으로 표현하고, 분류 근거를 간단히 설명해주세요."""
        
        return prompt
    
    def _parse_classification_response(
        self, 
        response: str, 
        categories: List[Category]
    ) -> ClassificationResult:
        """AI 응답을 파싱하여 분류 결과 생성"""
        try:
            # JSON 응답 파싱 시도
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("JSON 형식을 찾을 수 없음")
            
            parsed = json.loads(json_str)
            
            # 카테고리 ID 검증
            category_ids = [cat.id for cat in categories]
            if parsed.get("category_id") not in category_ids:
                # 첫 번째 카테고리를 기본값으로 사용
                parsed["category_id"] = categories[0].id
                parsed["category_name"] = categories[0].name
                parsed["confidence"] = 0.5
                parsed["reasoning"] = "유효하지 않은 카테고리 ID로 인한 기본값 사용"
            
            return ClassificationResult(
                category_id=parsed.get("category_id", categories[0].id),
                category_name=parsed.get("category_name", categories[0].name),
                confidence=max(0.0, min(1.0, float(parsed.get("confidence", 0.5)))),
                reasoning=parsed.get("reasoning", "근거 정보 없음")
            )
            
        except Exception as e:
            logger.error(f"응답 파싱 실패: {e}")
            # 기본값 반환
            return ClassificationResult(
                category_id=categories[0].id,
                category_name=categories[0].name,
                confidence=0.3,
                reasoning=f"응답 파싱 실패로 인한 기본값 사용: {str(e)}"
            )
    
    async def classify_manufacturing_issue(self, text: str) -> ClassificationResult:
        """제조업 이슈 분류 (사전 정의된 카테고리 사용)"""
        manufacturing_categories = [
            Category(
                id="quality",
                name="품질 문제",
                description="제품 품질, 불량률, 검사 관련 이슈",
                examples=["불량률 증가", "품질 기준 미달", "검사 실패"]
            ),
            Category(
                id="equipment",
                name="장비 문제", 
                description="생산 장비, 기계 고장, 유지보수 관련",
                examples=["기계 고장", "장비 정지", "유지보수 필요"]
            ),
            Category(
                id="process",
                name="공정 문제",
                description="생산 공정, 효율성, 작업 순서 관련",
                examples=["공정 지연", "효율성 저하", "작업 순서 문제"]
            ),
            Category(
                id="material",
                name="원자재 문제",
                description="원자재 공급, 재고, 품질 관련",
                examples=["재료 부족", "원자재 품질 저하", "공급 지연"]
            ),
            Category(
                id="safety",
                name="안전 문제",
                description="작업 안전, 사고 예방, 규정 준수 관련",
                examples=["안전사고", "규정 위반", "위험 요소 발견"]
            )
        ]
        
        # 제조업 이슈 전용 컨텍스트 생성
        manufacturing_context = self.context_engineer.create_specialized_context(
            service_type="classification",
            task_type="manufacturing_issue_classification",
            domain_data={
                "industry": "manufacturing",
                "focus": "issue_classification"
            }
        )
        
        # 컨텍스트를 포함한 분류 수행
        prompt = self._create_classification_prompt(text, manufacturing_categories)
        response = await self.provider.generate_response(
            prompt, 
            context=manufacturing_context
        )
        
        return self._parse_classification_response(response, manufacturing_categories)


# 싱글톤 인스턴스 관리
_classification_instances = {}


def get_classification_service(model: Optional[str] = None) -> ClassificationService:
    """분류 서비스 인스턴스 반환 (싱글톤)"""
    model_key = model or settings.ollama_model
    
    if model_key not in _classification_instances:
        _classification_instances[model_key] = ClassificationService(model_key)
    
    return _classification_instances[model_key]


def clear_classification_instances():
    """분류 인스턴스 캐시 초기화"""
    global _classification_instances
    _classification_instances.clear()
    logger.info("분류 인스턴스 캐시 초기화 완료") 