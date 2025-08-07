"""
DX-AI Manufacturing Copilot - LLM 클라이언트
Ollama를 사용한 LangChain 기반 LLM 클라이언트 구현 (최신 LCEL 방식)
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from langchain_ollama import OllamaLLM
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from .config import settings

logger = logging.getLogger(__name__)


class OllamaCallbackHandler(BaseCallbackHandler):
    """Ollama LLM 콜백 핸들러"""
    
    def __init__(self):
        super().__init__()
        self.tokens_used = 0
        self.total_cost = 0.0
        
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """LLM 시작 콜백"""
        logger.debug(f"LLM 시작: {len(prompts)} 프롬프트")
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 종료 콜백"""
        if response.llm_output:
            self.tokens_used += response.llm_output.get("token_usage", {}).get("total_tokens", 0)
        logger.debug(f"LLM 완료: {self.tokens_used} 토큰 사용")
        
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """LLM 오류 콜백"""
        logger.error(f"LLM 오류: {error}")


class OllamaClient:
    """Ollama LLM 클라이언트"""
    
    def __init__(self, 
                 base_url: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: Optional[int] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024,
                 verbose: bool = False):
        """
        Ollama 클라이언트 초기화
        
        Args:
            base_url: Ollama 서버 URL
            model: 사용할 모델 이름
            timeout: 요청 타임아웃 (초)
            temperature: 생성 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            verbose: 자세한 로깅 여부
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose
        
        # 콜백 핸들러 초기화
        self.callback_handler = OllamaCallbackHandler()
        
        # Ollama LLM 초기화
        self._init_llm()
        
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
            logger.info(f"Ollama LLM 초기화 완료: {self.model}")
        except Exception as e:
            logger.error(f"Ollama LLM 초기화 실패: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        단일 프롬프트 생성
        
        Args:
            prompt: 입력 프롬프트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트
        """
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
            logger.debug(f"생성 완료: {len(response)} 문자")
            return response
            
        except Exception as e:
            logger.error(f"생성 실패: {e}")
            raise
    
    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        배치 프롬프트 생성
        
        Args:
            prompts: 입력 프롬프트 리스트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트 리스트
        """
        try:
            responses = []
            for prompt in prompts:
                response = self.generate(prompt, **kwargs)
                responses.append(response)
            return responses
            
        except Exception as e:
            logger.error(f"배치 생성 실패: {e}")
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
            response = await loop.run_in_executor(None, self.generate, prompt, **kwargs)
            return response
            
        except Exception as e:
            logger.error(f"비동기 생성 실패: {e}")
            raise
    
    async def agenerate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        비동기 배치 프롬프트 생성
        
        Args:
            prompts: 입력 프롬프트 리스트
            **kwargs: 추가 생성 옵션
            
        Returns:
            생성된 텍스트 리스트
        """
        try:
            tasks = [self.agenerate(prompt, **kwargs) for prompt in prompts]
            responses = await asyncio.gather(*tasks)
            return responses
            
        except Exception as e:
            logger.error(f"비동기 배치 생성 실패: {e}")
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
            logger.error(f"체인 생성 실패: {e}")
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
            logger.error(f"채팅 체인 생성 실패: {e}")
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
            logger.error(f"QA 체인 생성 실패: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 반환
        
        Returns:
            모델 정보 딕셔너리
        """
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
            "tokens_used": self.callback_handler.tokens_used,
            "total_cost": self.callback_handler.total_cost,
            "available_models": settings.available_llm_models
        }
    
    def reset_usage_stats(self):
        """사용량 통계 초기화"""
        self.callback_handler.tokens_used = 0
        self.callback_handler.total_cost = 0.0
        logger.info("사용량 통계 초기화 완료")
    
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
            logger.warning(f"Ollama 서버 연결 실패: {e}")
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
            
            logger.info(f"모델 전환 완료: {old_model} → {new_model}")
            return True
            
        except Exception as e:
            logger.error(f"모델 전환 실패: {e}")
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


# 전역 Ollama 클라이언트 인스턴스
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    """전역 Ollama 클라이언트 인스턴스 반환"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient(
            verbose=settings.langchain_verbose
        )
    return _ollama_client


def create_ollama_client(**kwargs) -> OllamaClient:
    """새로운 Ollama 클라이언트 인스턴스 생성"""
    return OllamaClient(**kwargs) 