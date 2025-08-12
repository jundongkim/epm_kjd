"""
AI Advisor - Dify 클라이언트 통합 모듈

기존 AI Advisor의 벡터 검색 결과를 Dify 에이전트로 전달하여 
더 정교한 응답을 생성하는 하이브리드 시스템
"""

import os
import json
import asyncio
import httpx
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

from .utils import AIAdvisorConfig, get_config, AIAdvisorException

logger = logging.getLogger(__name__)


class DifyAIAdvisorClient:
    """AI Advisor용 Dify 클라이언트"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
        
        # Dify API 설정
        self.dify_api_url = os.getenv("DIFY_API_URL", "http://localhost/console/api")
        self.dify_api_key = os.getenv("DIFY_API_KEY", "")
        self.console_api_key = os.getenv("DIFY_CONSOLE_API_KEY", "")
        
        # AI Advisor 전용 에이전트 ID (없으면 자동 생성)
        self.advisor_agent_id = os.getenv("DIFY_ADVISOR_AGENT_ID", "")
        
        # HTTP 클라이언트
        self.http_client = None
        self.initialized = False
        
        logger.info("Dify AI Advisor 클라이언트 초기화")
    
    async def _ensure_http_client(self):
        """HTTP 클라이언트 초기화"""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def _get_headers(self, use_console_api: bool = False) -> Dict[str, str]:
        """API 헤더 생성"""
        api_key = self.console_api_key if use_console_api else self.dify_api_key
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize(self) -> bool:
        """Dify 클라이언트 초기화 및 AI Advisor 전용 에이전트 설정"""
        try:
            await self._ensure_http_client()
            
            # API 연결 테스트
            if not await self._test_connection():
                logger.error("Dify API 연결 실패")
                return False
            
            # AI Advisor 전용 에이전트 확인/생성
            if not self.advisor_agent_id:
                agent_id = await self._create_advisor_agent()
                if agent_id:
                    self.advisor_agent_id = agent_id
                    logger.info(f"AI Advisor 전용 에이전트 생성: {agent_id}")
                else:
                    logger.error("AI Advisor 에이전트 생성 실패")
                    return False
            
            self.initialized = True
            logger.info("✅ Dify AI Advisor 클라이언트 초기화 성공")
            return True
            
        except Exception as e:
            logger.error(f"❌ Dify 클라이언트 초기화 실패: {str(e)}")
            return False
    
    async def _test_connection(self) -> bool:
        """Dify API 연결 테스트"""
        try:
            headers = await self._get_headers(use_console_api=True)
            response = await self.http_client.get(
                f"{self.dify_api_url}/apps",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Dify API 연결 성공")
                return True
            else:
                logger.error(f"Dify API 연결 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Dify API 연결 테스트 오류: {str(e)}")
            return False
    
    async def _create_advisor_agent(self) -> Optional[str]:
        """AI Advisor 전용 Dify 에이전트 생성"""
        try:
            headers = await self._get_headers(use_console_api=True)
            
            # AI Advisor 전용 에이전트 설정
            agent_config = {
                "name": "DX-AI Manufacturing Advisor",
                "description": "제조업 전문 AI 어드바이저 - 문서 기반 기술 상담 및 문제 해결",
                "mode": "agent-chat",  # 에이전트 모드
                "model_config": {
                    "provider": "ollama",
                    "model": "gemma3:4b-it-qat",
                    "parameters": {
                        "temperature": 0.2,
                        "max_tokens": 2000
                    }
                },
                "user_input_form": [],
                "pre_prompt": self._get_advisor_system_prompt(),
                "agent_mode": {
                    "enabled": True,
                    "tools": [
                        {
                            "tool_name": "document_search",
                            "enabled": True,
                            "description": "문서 검색 도구"
                        }
                    ]
                },
                "opening_statement": "안녕하세요! 저는 제조업 전문 AI 어드바이저입니다. 업로드된 문서를 바탕으로 기술적 문제 해결과 공정 개선에 도움을 드립니다. 궁금한 점을 자유롭게 물어보세요.",
                "suggested_questions": [
                    "현재 공정에서 발생하는 품질 문제의 원인은 무엇인가요?",
                    "장비 성능을 개선할 수 있는 방법이 있나요?",
                    "안전 관련 주의사항을 확인하고 싶습니다.",
                    "유사한 사례의 해결 방법을 찾아주세요."
                ],
                "speech_to_text": {"enabled": False},
                "text_to_speech": {"enabled": False},
                "retrieval_model": {
                    "search_method": "semantic_search",
                    "reranking_enable": True,
                    "reranking_model": {
                        "reranking_provider_name": "",
                        "reranking_model_name": ""
                    },
                    "top_k": 5,
                    "score_threshold_enabled": True,
                    "score_threshold": 0.5
                }
            }
            
            response = await self.http_client.post(
                f"{self.dify_api_url}/apps",
                headers=headers,
                json=agent_config
            )
            
            if response.status_code == 201:
                result = response.json()
                agent_id = result.get("id")
                logger.info(f"AI Advisor 에이전트 생성 성공: {agent_id}")
                return agent_id
            else:
                logger.error(f"에이전트 생성 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"에이전트 생성 오류: {str(e)}")
            return None
    
    def _get_advisor_system_prompt(self) -> str:
        """AI Advisor 전용 시스템 프롬프트"""
        return """당신은 제조업 전문 AI 어드바이저입니다. 다음 역할을 수행합니다:

🎯 **주요 역할**:
1. **기술 문제 진단**: 제조 공정, 품질, 장비 관련 문제의 근본 원인 분석
2. **해결책 제시**: 실현 가능하고 구체적인 개선 방안 제시
3. **문서 기반 답변**: 업로드된 문서의 정보를 우선적으로 활용
4. **안전 고려**: 모든 제안에서 안전성을 최우선으로 고려

📋 **답변 가이드라인**:
1. **출처 명시**: 문서에서 인용한 내용은 반드시 출처 표기
2. **단계별 설명**: 복잡한 해결책은 단계별로 명확히 설명
3. **리스크 언급**: 제안하는 방법의 위험 요소나 주의사항 포함
4. **대안 제시**: 가능한 경우 여러 옵션 제시
5. **후속 조치**: 추가 확인이 필요한 사항 안내

💡 **답변 구조**:
- 문제 상황 파악 및 요약
- 관련 문서 정보 (있는 경우)
- 근본 원인 분석
- 구체적 해결 방안
- 주의사항 및 위험 요소
- 권장 후속 조치

전문적이면서도 이해하기 쉬운 답변을 제공하되, 안전성과 실현 가능성을 항상 고려하세요."""

    async def generate_response(self, 
                              user_query: str, 
                              search_results: List[Dict[str, Any]] = None,
                              conversation_id: str = None) -> Dict[str, Any]:
        """벡터 검색 결과를 활용한 Dify 응답 생성"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                raise AIAdvisorException("Dify 클라이언트가 초기화되지 않았습니다")
            
            # 컨텍스트 구성
            context_message = self._build_context_message(user_query, search_results)
            
            # Dify 에이전트에게 메시지 전송
            headers = await self._get_headers()
            
            chat_payload = {
                "inputs": {},
                "query": context_message,
                "response_mode": "blocking",
                "conversation_id": conversation_id or "",
                "user": "ai-advisor-user"
            }
            
            response = await self.http_client.post(
                f"{self.dify_api_url}/chat-messages",
                headers=headers,
                json=chat_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "query": user_query,
                    "response": result.get("answer", "응답을 생성할 수 없습니다."),
                    "mode": "dify_hybrid",
                    "conversation_id": result.get("conversation_id"),
                    "search_results": search_results or [],
                    "metadata": {
                        "dify_agent_id": self.advisor_agent_id,
                        "message_id": result.get("id"),
                        "created_at": result.get("created_at")
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Dify 응답 생성 실패: {response.status_code} - {response.text}")
                raise AIAdvisorException(f"Dify 응답 생성 실패: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Dify 응답 생성 오류: {str(e)}")
            # 폴백: 기본 응답 반환
            return {
                "query": user_query,
                "response": f"Dify를 통한 응답 생성 중 오류가 발생했습니다: {str(e)}",
                "mode": "dify_error",
                "search_results": search_results or [],
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_streaming_response(self, 
                                        user_query: str, 
                                        search_results: List[Dict[str, Any]] = None,
                                        conversation_id: str = None) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성"""
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.initialized:
                yield "Dify 클라이언트 초기화 실패"
                return
            
            context_message = self._build_context_message(user_query, search_results)
            headers = await self._get_headers()
            
            chat_payload = {
                "inputs": {},
                "query": context_message,
                "response_mode": "streaming",
                "conversation_id": conversation_id or "",
                "user": "ai-advisor-user"
            }
            
            async with self.http_client.stream(
                "POST",
                f"{self.dify_api_url}/chat-messages",
                headers=headers,
                json=chat_payload
            ) as response:
                
                if response.status_code != 200:
                    yield f"Dify 스트리밍 응답 실패: {response.status_code}"
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # "data: " 제거
                            
                            if data.get("event") == "message":
                                answer = data.get("answer", "")
                                if answer:
                                    yield answer
                            elif data.get("event") == "message_end":
                                # 스트리밍 완료
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield f"Dify 스트리밍 오류: {str(e)}"
    
    def _build_context_message(self, user_query: str, search_results: List[Dict[str, Any]] = None) -> str:
        """사용자 질의와 검색 결과를 조합한 컨텍스트 메시지 생성"""
        message_parts = [f"사용자 질문: {user_query}"]
        
        if search_results and len(search_results) > 0:
            message_parts.append("\n📄 관련 문서 정보:")
            
            for i, result in enumerate(search_results[:3], 1):
                filename = result.get("metadata", {}).get("filename", f"문서{i}")
                content = result.get("content", "")
                
                # 내용이 너무 길면 요약
                if len(content) > 500:
                    content = content[:500] + "..."
                
                message_parts.append(f"\n[문서 {i}: {filename}]")
                message_parts.append(content)
        else:
            message_parts.append("\n📄 현재 업로드된 관련 문서가 없습니다. 일반적인 제조업 지식을 바탕으로 답변해주세요.")
        
        return "\n".join(message_parts)
    
    async def close(self):
        """클라이언트 종료"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        logger.info("Dify AI Advisor 클라이언트 종료")