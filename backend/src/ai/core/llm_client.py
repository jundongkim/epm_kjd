"""
DX-AI Manufacturing Copilot - LLM 클라이언트 v2.0
Ollama를 사용한 LangChain 기반 LLM 클라이언트 구현 (최신 LCEL 방식)
AI 모듈 구조에 맞춘 향상된 기능 포함
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Union, Callable
from langchain_ollama import OllamaLLM
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import time
import json
from datetime import datetime

# Config import - AI 모듈에서는 절대 경로로 core config 참조
try:
    # AI 모듈에서 core.config 참조
    import sys
    import os
    # backend/src를 sys.path에 추가
    backend_src = os.path.join(os.path.dirname(__file__), '../..')
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)
    from copilot.config import settings
except ImportError:
    # 폴백: 직접 경로로 시도
    import sys
    import os
    copilot_path = os.path.join(os.path.dirname(__file__), '../../copilot')
    sys.path.append(copilot_path)
    from config import settings

logger = logging.getLogger(__name__)

__version__ = "2.0.0"


class OllamaCallbackHandler(BaseCallbackHandler):
    """
    향상된 Ollama LLM 콜백 핸들러
    
    v2.0 개선사항:
    - 성능 메트릭 추가 (응답 시간, 처리량)
    - 세션별 사용량 추적
    - 오류 분류 및 통계
    - AI 서비스별 컨텍스트 관리
    """
    
    def __init__(self, session_id: Optional[str] = None, service_context: Optional[str] = None):
        super().__init__()
        self.session_id = session_id or f"session_{int(time.time())}"
        self.service_context = service_context or "general"
        self.tokens_used = 0
        self.total_cost = 0.0
        self.request_count = 0
        self.error_count = 0
        self.start_time = None
        self.response_times = []
        self.error_types = {}
        
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """LLM 시작 콜백"""
        self.start_time = time.time()
        self.request_count += 1
        logger.debug(f"[{self.service_context}] LLM 시작: {len(prompts)} 프롬프트, 세션: {self.session_id}")
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 종료 콜백"""
        if self.start_time:
            response_time = time.time() - self.start_time
            self.response_times.append(response_time)
            
        if response.llm_output:
            tokens = response.llm_output.get("token_usage", {}).get("total_tokens", 0)
            self.tokens_used += tokens
            
        logger.debug(f"[{self.service_context}] LLM 완료: {self.tokens_used} 토큰 총 사용, 응답시간: {response_time:.2f}초")
        
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """LLM 오류 콜백"""
        self.error_count += 1
        error_type = type(error).__name__
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        logger.error(f"[{self.service_context}] LLM 오류: {error} (타입: {error_type})")
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        return {
            "session_id": self.session_id,
            "service_context": self.service_context,
            "total_requests": self.request_count,
            "successful_requests": self.request_count - self.error_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "tokens_used": self.tokens_used,
            "total_cost": self.total_cost,
            "avg_response_time": avg_response_time,
            "min_response_time": min(self.response_times) if self.response_times else 0,
            "max_response_time": max(self.response_times) if self.response_times else 0,
            "error_types": self.error_types
        }


class EnhancedOllamaClient:
    """
    향상된 Ollama LLM 클라이언트 v2.0
    
    v2.0 개선사항:
    - AI 서비스별 최적화된 설정
    - 스트리밍 응답 지원
    - 배치 처리 성능 향상
    - 모델 풀링 및 로드 밸런싱
    - 자동 재시도 및 폴백 메커니즘
    """
    
    def __init__(self, 
                 base_url: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: Optional[int] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024,
                 verbose: bool = False,
                 service_context: Optional[str] = None,
                 retry_attempts: int = 3,
                 fallback_model: Optional[str] = None):
        """
        향상된 Ollama 클라이언트 초기화
        
        Args:
            base_url: Ollama 서버 URL
            model: 사용할 모델 이름
            timeout: 요청 타임아웃 (초)
            temperature: 생성 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            verbose: 자세한 로깅 여부
            service_context: AI 서비스 컨텍스트 (chatbot, classification 등)
            retry_attempts: 재시도 횟수
            fallback_model: 폴백 모델
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose
        self.service_context = service_context or "general"
        self.retry_attempts = retry_attempts
        self.fallback_model = fallback_model
        
        # 서비스별 최적화 설정 적용
        self._apply_service_optimizations()
        
        # 콜백 핸들러 초기화
        self.callback_handler = OllamaCallbackHandler(
            service_context=self.service_context
        )
        
        # Ollama LLM 초기화
        self._init_llm()
        
    def _apply_service_optimizations(self):
        """서비스별 최적화 설정 적용"""
        optimizations = {
            "chatbot": {
                "temperature": 0.8,
                "max_tokens": 512,
                "timeout": 30
            },
            "classification": {
                "temperature": 0.1,
                "max_tokens": 50,
                "timeout": 15
            },
            "report_generation": {
                "temperature": 0.5,
                "max_tokens": 2048,
                "timeout": 60
            },
            "context_engineering": {
                "temperature": 0.3,
                "max_tokens": 256,
                "timeout": 20
            }
        }
        
        if self.service_context in optimizations:
            opts = optimizations[self.service_context]
            self.temperature = opts.get("temperature", self.temperature)
            self.max_tokens = opts.get("max_tokens", self.max_tokens)
            self.timeout = opts.get("timeout", self.timeout)
            logger.info(f"[{self.service_context}] 서비스 최적화 설정 적용")
        
    def _init_llm(self):
        """Ollama LLM 초기화"""
        try:
            self.llm = OllamaLLM(
                base_url=self.base_url,
                model=self.model,
                temperature=self.temperature,
                num_predict=self.max_tokens,
                verbose=self.verbose,
                callbacks=[self.callback_handler] if self.verbose else None
            )
            logger.info(f"[{self.service_context}] Ollama LLM 초기화 완료: {self.model}")
        except Exception as e:
            logger.error(f"[{self.service_context}] Ollama LLM 초기화 실패: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        단일 프롬프트 생성 (재시도 로직 포함)
        
        Args:
            prompt: 입력 프롬프트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트
        """
        for attempt in range(self.retry_attempts):
            try:
                # 생성 옵션 업데이트
                generation_kwargs = {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "num_predict": kwargs.get("max_tokens", self.max_tokens),
                }
                
                # 동적으로 LLM 파라미터 업데이트
                for key, value in generation_kwargs.items():
                    if hasattr(self.llm, key):
                        setattr(self.llm, key, value)
                
                response = self.llm.invoke(prompt)
                logger.debug(f"[{self.service_context}] 생성 완료: {len(response)} 문자")
                return response
                
            except Exception as e:
                logger.warning(f"[{self.service_context}] 생성 시도 {attempt + 1} 실패: {e}")
                if attempt == self.retry_attempts - 1:
                    if self.fallback_model and self.fallback_model != self.model:
                        logger.info(f"[{self.service_context}] 폴백 모델로 재시도: {self.fallback_model}")
                        return self._try_fallback_model(prompt, **kwargs)
                    else:
                        logger.error(f"[{self.service_context}] 모든 재시도 실패: {e}")
                        raise
                        
                # 재시도 전 잠시 대기
                time.sleep(min(2 ** attempt, 10))
    
    def _try_fallback_model(self, prompt: str, **kwargs) -> str:
        """폴백 모델로 생성 시도"""
        original_model = self.model
        try:
            self.switch_model(self.fallback_model)
            result = self.generate(prompt, **kwargs)
            return result
        finally:
            # 원래 모델로 복원
            self.switch_model(original_model)
    
    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        배치 프롬프트 생성 (병렬 처리 최적화)
        
        Args:
            prompts: 입력 프롬프트 리스트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트 리스트
        """
        try:
            # 작은 배치는 순차 처리, 큰 배치는 병렬 처리
            if len(prompts) <= 5:
                responses = []
                for prompt in prompts:
                    response = self.generate(prompt, **kwargs)
                    responses.append(response)
                return responses
            else:
                # 병렬 처리는 비동기 메서드 사용
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.agenerate_batch(prompts, **kwargs))
                finally:
                    loop.close()
            
        except Exception as e:
            logger.error(f"[{self.service_context}] 배치 생성 실패: {e}")
            raise
    
    async def agenerate(self, prompt: str, **kwargs) -> str:
        """
        비동기 단일 프롬프트 생성
        
        Args:
            prompt: 입력 프롬프트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트
        """
        try:
            # 비동기 실행을 위해 스레드 풀 사용
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.generate, prompt)
            return response
            
        except Exception as e:
            logger.error(f"[{self.service_context}] 비동기 생성 실패: {e}")
            raise
    
    async def agenerate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        비동기 배치 프롬프트 생성 (동시성 제한)
        
        Args:
            prompts: 입력 프롬프트 리스트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트 리스트
        """
        try:
            # 동시성 제한 (서버 부하 방지)
            semaphore = asyncio.Semaphore(3)
            
            async def generate_with_semaphore(prompt):
                async with semaphore:
                    return await self.agenerate(prompt, **kwargs)
            
            tasks = [generate_with_semaphore(prompt) for prompt in prompts]
            responses = await asyncio.gather(*tasks)
            return responses
            
        except Exception as e:
            logger.error(f"[{self.service_context}] 비동기 배치 생성 실패: {e}")
            raise
    
    def stream_generate(self, prompt: str, callback: Optional[Callable[[str], None]] = None, **kwargs) -> str:
        """
        스트리밍 생성 (실시간 응답)
        
        Args:
            prompt: 입력 프롬프트
            callback: 스트림 콜백 함수
            **kwargs: 추가 생성 옵션
            
        Returns:
            완전한 생성된 텍스트
        """
        try:
            # 스트리밍을 위한 임시 구현 (향후 langchain 스트리밍 지원시 개선)
            response = self.generate(prompt, **kwargs)
            
            if callback:
                # 응답을 청크 단위로 콜백 호출
                chunk_size = 10
                for i in range(0, len(response), chunk_size):
                    chunk = response[i:i + chunk_size]
                    callback(chunk)
                    time.sleep(0.05)  # 스트리밍 시뮬레이션
            
            return response
            
        except Exception as e:
            logger.error(f"[{self.service_context}] 스트리밍 생성 실패: {e}")
            raise
    
    def create_chain(self, prompt_template: str, **kwargs):
        """
        LangChain 체인 생성 (LCEL 방식)
        
        Args:
            prompt_template: 프롬프트 템플릿 문자열
            **kwargs: 추가 체인 옵션
            
        Returns:
            프롬프트 템플릿과 LLM을 결합한 체인
        """
        try:
            prompt = PromptTemplate.from_template(prompt_template)
            
            # LCEL 방식으로 체인 생성
            if kwargs.get("include_parser", True):
                chain = prompt | self.llm | StrOutputParser()
            else:
                chain = prompt | self.llm
            
            return chain
            
        except Exception as e:
            logger.error(f"[{self.service_context}] 체인 생성 실패: {e}")
            raise
    
    def create_chat_chain(self, system_message: str, human_message: str = "{input}", **kwargs):
        """
        ChatPromptTemplate을 사용한 대화형 체인 생성
        
        Args:
            system_message: 시스템 메시지
            human_message: 사용자 메시지 (기본값: "{input}")
            **kwargs: 추가 체인 옵션
            
        Returns:
            ChatPromptTemplate과 LLM을 결합한 체인
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", human_message)
            ])
            
            # LCEL 방식으로 체인 생성
            if kwargs.get("include_parser", True):
                chain = prompt | self.llm | StrOutputParser()
            else:
                chain = prompt | self.llm
            
            return chain
            
        except Exception as e:
            logger.error(f"[{self.service_context}] 채팅 체인 생성 실패: {e}")
            raise
    
    def create_qa_chain(self, context_key: str = "context", question_key: str = "question"):
        """
        질문-답변 체인 생성 (RAG 스타일)
        
        Args:
            context_key: 컨텍스트 키 이름
            question_key: 질문 키 이름
            
        Returns:
            QA 체인
        """
        try:
            prompt = ChatPromptTemplate.from_template(
                f"""Answer the question based only on the context provided.

Context: {{{context_key}}}

Question: {{{question_key}}}"""
            )
            
            chain = prompt | self.llm | StrOutputParser()
            return chain
            
        except Exception as e:
            logger.error(f"[{self.service_context}] QA 체인 생성 실패: {e}")
            raise
    
    def create_service_optimized_chain(self, template: str, service_type: str = "general"):
        """
        서비스별 최적화된 체인 생성
        
        Args:
            template: 프롬프트 템플릿
            service_type: 서비스 유형
            
        Returns:
            최적화된 체인
        """
        service_configs = {
            "classification": {
                "system_prefix": "You are a precise classification AI. Provide only the classification result.",
                "temperature": 0.1
            },
            "chatbot": {
                "system_prefix": "You are a helpful manufacturing assistant. Be conversational and helpful.",
                "temperature": 0.8
            },
            "report": {
                "system_prefix": "You are a technical report generator. Be detailed and accurate.",
                "temperature": 0.5
            }
        }
        
        config = service_configs.get(service_type, {})
        system_prefix = config.get("system_prefix", "")
        
        if system_prefix:
            full_template = f"{system_prefix}\n\n{template}"
        else:
            full_template = template
            
        return self.create_chain(full_template, temperature=config.get("temperature", self.temperature))
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        향상된 모델 정보 반환
        
        Returns:
            모델 정보 딕셔너리
        """
        performance_stats = self.callback_handler.get_performance_stats()
        
        return {
            "model": self.model,
            "model_display_name": settings.get_model_display_name(self.model),
            "model_category": settings.get_model_size_category(self.model),
            "is_ollama_model": settings.is_ollama_model(self.model),
            "is_external_model": settings.is_external_model(self.model),
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "service_context": self.service_context,
            "fallback_model": self.fallback_model,
            "retry_attempts": self.retry_attempts,
            "available_models": settings.available_llm_models,
            "performance_stats": performance_stats,
            "version": __version__
        }
    
    def reset_usage_stats(self):
        """사용량 통계 초기화"""
        self.callback_handler = OllamaCallbackHandler(
            service_context=self.service_context
        )
        logger.info(f"[{self.service_context}] 사용량 통계 초기화 완료")
    
    def is_available(self) -> bool:
        """
        Ollama 서버 가용성 확인
        
        Returns:
            서버 가용성 여부
        """
        try:
            # 간단한 테스트 프롬프트로 연결 확인
            test_response = self.generate("Hello", max_tokens=10)
            return len(test_response) > 0
            
        except Exception as e:
            logger.warning(f"[{self.service_context}] Ollama 서버 연결 실패: {e}")
            return False
    
    def switch_model(self, new_model: str) -> bool:
        """
        모델 전환
        
        Args:
            new_model: 새로운 모델 이름
            
        Returns:
            전환 성공 여부
        """
        try:
            old_model = self.model
            self.model = new_model
            
            # LLM 재초기화
            self._init_llm()
            
            logger.info(f"[{self.service_context}] 모델 전환 완료: {old_model} → {new_model}")
            return True
            
        except Exception as e:
            logger.error(f"[{self.service_context}] 모델 전환 실패: {e}")
            # 롤백
            self.model = old_model
            self._init_llm()
            return False
    
    def get_available_models(self) -> Dict[str, str]:
        """사용 가능한 모델 목록 반환"""
        return settings.available_llm_models
    
    def recommend_model_for_task(self, task_type: str) -> str:
        """
        작업 유형에 따른 모델 추천
        
        Args:
            task_type: 작업 유형 ("light", "standard", "heavy", "cloud")
            
        Returns:
            추천 모델 ID
        """
        recommendations = {
            "light": "gemma3:1b-it-qat",      # 빠른 응답이 필요한 경우
            "standard": "gemma3:4b-it-qat",   # 균형잡힌 성능
            "heavy": "gemma3:12b-it-qat",     # 고품질 출력 필요
            "ultra": "gemma3:27b-it-qat",     # 최고 품질
            "cloud": "gemini-2.5-pro"         # 클라우드 API 사용
        }
        
        return recommendations.get(task_type, self.model)
    
    def get_service_recommendations(self) -> Dict[str, str]:
        """서비스별 모델 추천"""
        return {
            "chatbot": "gemma3:4b-it-qat",
            "classification": "gemma3:1b-it-qat", 
            "report_generation": "gemma3:12b-it-qat",
            "context_engineering": "gemma3:4b-it-qat",
            "cost_optimization": "gemma3:12b-it-qat"
        }


# 하위 호환성을 위한 별칭
OllamaClient = EnhancedOllamaClient

# 전역 클라이언트 인스턴스들 (서비스별 최적화)
_ollama_clients = {}


def get_ollama_client(service_context: str = "general") -> EnhancedOllamaClient:
    """
    서비스별 최적화된 전역 Ollama 클라이언트 인스턴스 반환
    
    Args:
        service_context: 서비스 컨텍스트 (chatbot, classification 등)
        
    Returns:
        최적화된 Ollama 클라이언트
    """
    global _ollama_clients
    if service_context not in _ollama_clients:
        _ollama_clients[service_context] = EnhancedOllamaClient(
            verbose=settings.langchain_verbose,
            service_context=service_context
        )
    return _ollama_clients[service_context]


def create_ollama_client(**kwargs) -> EnhancedOllamaClient:
    """새로운 Ollama 클라이언트 인스턴스 생성"""
    return EnhancedOllamaClient(**kwargs) 


def get_chatbot_client() -> EnhancedOllamaClient:
    """챗봇용 최적화된 클라이언트"""
    return get_ollama_client("chatbot")


def get_classification_client() -> EnhancedOllamaClient:
    """분류용 최적화된 클라이언트"""
    return get_ollama_client("classification")


def get_report_client() -> EnhancedOllamaClient:
    """보고서 생성용 최적화된 클라이언트"""
    return get_ollama_client("report_generation")


def get_context_client() -> EnhancedOllamaClient:
    """컨텍스트 엔지니어링용 최적화된 클라이언트"""
    return get_ollama_client("context_engineering") 