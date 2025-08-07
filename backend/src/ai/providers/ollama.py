"""
DX-AI Manufacturing Copilot - Ollama AI 제공자
Ollama 서비스와의 통신을 담당하는 제공자 클래스
"""

import logging
from typing import Dict, Any, Optional, AsyncGenerator
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage

from ..core.base import AIProviderInterface
from ...copilot.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(AIProviderInterface):
    """Ollama AI 제공자"""
    
    def __init__(
        self,
        model: str = "gemma2:2b",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        base_url: Optional[str] = None
    ):
        """
        Ollama 제공자 초기화
        
        Args:
            model: 사용할 모델 이름
            temperature: 생성 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            base_url: Ollama 서버 URL
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url or settings.ollama_base_url
        
        # ChatOllama 인스턴스 초기화
        self._client = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
            num_predict=self.max_tokens,
        )
        
        logger.info(f"Ollama 제공자 초기화 완료: {self.model} @ {self.base_url}")
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """단일 응답 생성"""
        try:
            # 메시지 생성
            if context:
                full_prompt = f"{context}\n\n사용자 질문: {prompt}"
            else:
                full_prompt = prompt
            
            # 응답 생성
            response = await self._client.ainvoke(full_prompt)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"Ollama 응답 생성 실패: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성 (최적화된 속도)"""
        try:
            # 메시지 생성
            if context:
                full_prompt = f"{context}\n\n사용자 질문: {prompt}"
            else:
                full_prompt = prompt
            
            # 청크 버퍼링을 위한 변수 (더 빠른 전송을 위해 조정)
            buffer = ""
            char_count = 0
            
            # 스트리밍 응답 생성
            async for chunk in self._client.astream(full_prompt):
                if hasattr(chunk, 'content') and chunk.content:
                    buffer += chunk.content
                    char_count += len(chunk.content)
                    
                    # 더 빠른 전송을 위해 조건 완화
                    should_send = (
                        # 문장 종료 구두점에서 즉시 전송
                        chunk.content in ['.', '!', '?', '\n'] or
                        # 쉼표나 공백에서도 자주 전송 (1-2단어마다)
                        (chunk.content in [',', ' ', ';', ':'] and len(buffer.split()) >= 1) or
                        # 문자 수 기준으로도 더 자주 전송 (15자마다)
                        char_count >= 15 or
                        # 한국어 문장 구분자
                        chunk.content in ['다', '요', '니다', '습니다']
                    )
                    
                    if should_send and buffer.strip():
                        yield buffer
                        buffer = ""
                        char_count = 0
                    
                    # 버퍼가 너무 길어지면 강제로 전송 (임계값 감소)
                    elif len(buffer) >= 25:
                        if buffer.strip():
                            yield buffer
                            buffer = ""
                            char_count = 0
            
            # 남은 버퍼 내용 전송
            if buffer.strip():
                yield buffer
                    
        except Exception as e:
            logger.error(f"Ollama 스트리밍 생성 실패: {e}")
            yield f"오류가 발생했습니다: {str(e)}"
    
    async def generate_from_messages_stream(
        self,
        messages: list[BaseMessage]
    ) -> AsyncGenerator[str, None]:
        """메시지 리스트로부터 스트리밍 응답 생성"""
        try:
            # 청크 버퍼링을 위한 변수
            buffer = ""
            word_count = 0
            
            async for chunk in self._client.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    buffer += chunk.content
                    
                    # 공백이나 구두점으로 단어 경계 확인
                    if chunk.content in [' ', '\n', '.', ',', '!', '?', ';', ':'] or len(buffer) >= 10:
                        word_count += len(buffer.split())
                        
                        # 3-5개 단어마다 또는 문장 끝에서 전송
                        if word_count >= 3 or chunk.content in ['.', '!', '?', '\n']:
                            if buffer.strip():
                                yield buffer
                                buffer = ""
                                word_count = 0
                    
                    # 버퍼가 너무 길어지면 강제로 전송
                    elif len(buffer) >= 50:
                        if buffer.strip():
                            yield buffer
                            buffer = ""
                            word_count = 0
            
            # 남은 버퍼 내용 전송
            if buffer.strip():
                yield buffer
                    
        except Exception as e:
            logger.error(f"Ollama 스트리밍 생성 실패: {e}")
            yield f"오류가 발생했습니다: {str(e)}"
    
    async def generate_from_messages(
        self,
        messages: list[BaseMessage]
    ) -> str:
        """메시지 리스트로부터 단일 응답 생성"""
        try:
            response = await self._client.ainvoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
                
        except Exception as e:
            logger.error(f"Ollama 메시지 응답 생성 실패: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        return {
            "provider": "ollama",
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "base_url": self.base_url,
            "capabilities": {
                "streaming": True,
                "async": True,
                "context_aware": True
            }
        }
    
    def update_config(self, **kwargs) -> None:
        """설정 업데이트"""
        updated = False
        
        if "temperature" in kwargs:
            self.temperature = kwargs["temperature"]
            self._client.temperature = self.temperature
            updated = True
        
        if "max_tokens" in kwargs:
            self.max_tokens = kwargs["max_tokens"]
            self._client.num_predict = self.max_tokens
            updated = True
        
        if "model" in kwargs and kwargs["model"] != self.model:
            # 모델이 변경된 경우 새 클라이언트 생성
            self.model = kwargs["model"]
            self._client = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature,
                num_predict=self.max_tokens,
            )
            updated = True
        
        if updated:
            logger.info(f"Ollama 제공자 설정 업데이트 완료: {kwargs}")
    
    def test_connection(self) -> Dict[str, Any]:
        """연결 테스트"""
        try:
            # 간단한 테스트 메시지로 연결 확인
            response = self._client.invoke("안녕하세요")
            return {
                "success": True,
                "model": self.model,
                "base_url": self.base_url,
                "test_response_length": len(response.content) if hasattr(response, 'content') else 0
            }
        except Exception as e:
            logger.error(f"Ollama 연결 테스트 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": self.model,
                "base_url": self.base_url
            }
    
    @property
    def client(self) -> ChatOllama:
        """내부 ChatOllama 클라이언트 접근"""
        return self._client


# 인스턴스 캐시
_ollama_instances: Dict[str, OllamaProvider] = {}


def get_ollama_provider(
    model: Optional[str] = None,
    **kwargs
) -> OllamaProvider:
    """Ollama 제공자 인스턴스 반환 (싱글톤)"""
    model_key = model or settings.ollama_model
    cache_key = f"{model_key}_{hash(frozenset(kwargs.items()))}"
    
    if cache_key not in _ollama_instances:
        _ollama_instances[cache_key] = OllamaProvider(
            model=model_key,
            **kwargs
        )
    
    return _ollama_instances[cache_key]


def clear_ollama_instances():
    """Ollama 인스턴스 캐시 초기화"""
    global _ollama_instances
    _ollama_instances.clear()
    logger.info("Ollama 인스턴스 캐시 초기화 완료") 