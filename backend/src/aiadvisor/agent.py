"""
DX-AI Advisor - AI 어드바이저 에이전트 모듈

LangChain과 LangGraph를 활용한 지능형 어드바이저 에이전트 시스템
온톨로지 기반 지식 그래프와 벡터 검색을 통합한 하이브리드 검색 및 분석 기능
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from datetime import datetime
import logging

# LangChain & LangGraph imports
from langchain.agents import Tool, AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough

# Graph state management
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Internal imports
from .utils import AIAdvisorConfig, get_config, AIAdvisorException
from .document_processor import DocumentProcessor
from .ontology import OntologyManager
from .embedding import EmbeddingManager, VectorSearchEngine
from .dify_client import DifyAIAdvisorClient
from ..ai.core.llm_client import get_ollama_client, create_ollama_client
from ..ai.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)


class AdvisorState(TypedDict):
    """어드바이저 에이전트 상태"""
    messages: List[Union[HumanMessage, AIMessage]]
    query: str
    search_results: List[Dict[str, Any]]
    ontology_context: Dict[str, Any]
    analysis_context: str
    response: str
    metadata: Dict[str, Any]


class AdvisorAgent:
    """AI 어드바이저 에이전트 - 하이브리드 지능형 분석 시스템 (Ollama + Dify 지원)"""
    
    def __init__(self, 
                 config: Optional[AIAdvisorConfig] = None,
                 embedding_manager: Optional[EmbeddingManager] = None,
                 ontology_manager: Optional[OntologyManager] = None,
                 model_name: str = None,
                 streaming: bool = True,
                 use_dify: bool = False):
        
        # config가 코루틴인 경우 처리
        if config is not None and hasattr(config, '__await__'):
            # 코루틴인 경우 기본 설정 사용
            self.config = get_config()
        else:
            self.config = config or get_config()
            
        self.model_name = model_name or self.config.default_llm_model
        self.streaming = streaming
        self.use_dify = use_dify
        
        # 컴포넌트 초기화
        self.embedding_manager = embedding_manager or EmbeddingManager(config)
        self.ontology_manager = ontology_manager or OntologyManager(config)
        self.search_engine = VectorSearchEngine(self.embedding_manager)
        
        # Dify 클라이언트 초기화 (use_dify가 True인 경우)
        self.dify_client = DifyAIAdvisorClient(config) if use_dify else None
        
        # LLM 클라이언트 초기화
        self.llm_client = None
        self.streaming_llm_client = None
        
        # 메모리 및 도구 초기화
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # 에이전트 초기화
        self.agent_executor = None
        self.workflow_graph = None
        
        # 초기화
        asyncio.create_task(self._initialize_async_components())
    
    async def _initialize_async_components(self):
        """비동기 컴포넌트 초기화"""
        try:
            # LLM 클라이언트 초기화
            self.llm_client = create_ollama_client(
                model=self.model_name,
                temperature=self.config.llm_temperature
            )
            
            if self.streaming:
                # 스트리밍을 위해 OllamaProvider 사용
                self.streaming_llm_client = OllamaProvider(
                    model=self.model_name,
                    temperature=self.config.llm_temperature
                )
            
            # Dify 클라이언트 초기화
            if self.dify_client:
                dify_initialized = await self.dify_client.initialize()
                if dify_initialized:
                    logger.info("✅ Dify 클라이언트 초기화 성공")
                else:
                    logger.warning("⚠️ Dify 클라이언트 초기화 실패 - Ollama 모드로 대체")
                    self.use_dify = False
            
            mode_info = "Dify 하이브리드" if self.use_dify else "Ollama 단독"
            logger.info(f"AI 어드바이저 에이전트 초기화 완료 - 모델: {self.model_name} ({mode_info})")
            
        except Exception as e:
            logger.error(f"어드바이저 에이전트 초기화 오류: {str(e)}")
            raise AIAdvisorException(f"어드바이저 에이전트 초기화 실패: {str(e)}")
    
    # 메인 실행 메서드들
    async def query(self, user_query: str, conversation_id: str = None) -> Dict[str, Any]:
        """사용자 질의 처리 (하이브리드 모드)"""
        try:
            # 공통: 관련 문서 검색 (강화된 처리)
            search_results = []
            try:
                # 임베딩 매니저 초기화 확인
                await self.embedding_manager.ensure_initialized()
                search_results = await self.embedding_manager.search_similar_documents(user_query, k=5)
                logger.info(f"문서 검색 결과: {len(search_results)}개")
            except Exception as search_error:
                logger.warning(f"문서 검색 중 오류 (무시하고 계속): {str(search_error)}")
                search_results = []
            
            # Dify 모드 vs Ollama 모드 분기
            if self.use_dify and self.dify_client:
                logger.info("🤖 Dify 하이브리드 모드로 응답 생성")
                return await self.dify_client.generate_response(
                    user_query=user_query,
                    search_results=search_results,
                    conversation_id=conversation_id
                )
            
            # 기존 Ollama 모드
            elif self.llm_client:
                logger.info("🤖 Ollama 단독 모드로 응답 생성")
                
                # 컨텍스트 구성
                context_parts = []
                if search_results:
                    context_parts.append("관련 문서 정보:")
                    for i, result in enumerate(search_results[:3], 1):
                        filename = result["metadata"].get("filename", f"문서{i}")
                        content_preview = result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"]
                        context_parts.append(f"[{filename}] {content_preview}")
                    logger.info(f"문서 컨텍스트 포함: {len(search_results)}개 문서")
                else:
                    logger.info("사용 가능한 문서가 없어 일반 답변 모드로 진행")
                    context_parts.append("현재 업로드된 문서가 없거나 검색할 수 없습니다. 일반적인 제조업 지식을 바탕으로 답변드리겠습니다.")
                
                context = "\n".join(context_parts)
                
                # 응답 생성 프롬프트
                response_prompt = f"""
                당신은 제조업 전문 AI 어드바이저입니다. 다음 질문에 대해 전문적이고 실용적인 답변을 제공해주세요.
                
                질문: {user_query}
                
                참고 정보:
                {context}
                
                답변 지침:
                1. 검색된 정보의 출처를 명시하세요 (예: "[문서명]에 따르면...")
                2. 제조업 전문가 관점에서 기술적으로 정확한 정보를 제공하세요
                3. 근본원인 분석과 구체적인 해결 방안을 제시하세요
                4. 실현 가능한 실행 계획과 권장사항을 포함하세요
                5. 관련된 위험 요소나 고려사항을 언급하세요
                6. 전문 용어는 쉽게 설명하여 이해하기 쉽게 하세요
                
                전문적이면서도 이해하기 쉬운 답변을 제공해주세요.
                """
                
                response = await self.llm_client.llm.ainvoke(response_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                return {
                    "query": user_query,
                    "response": response_text,
                    "mode": "direct_llm",
                    "search_results": search_results,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise AIAdvisorException("LLM 클라이언트가 초기화되지 않았습니다.")
                
        except Exception as e:
            logger.error(f"질의 처리 오류: {str(e)}")
            return {
                "query": user_query,
                "response": f"질의 처리 중 오류가 발생했습니다: {str(e)}",
                "mode": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def stream_response(self, user_query: str, conversation_id: str = None) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성 (하이브리드 모드)"""
        try:
            
            # 컨텍스트 수집 (강화된 처리)
            search_results = []
            try:
                await self.embedding_manager.ensure_initialized()
                search_results = await self.embedding_manager.search_similar_documents(user_query, k=5)
                logger.info(f"스트리밍 - 문서 검색 결과: {len(search_results)}개")
            except Exception as search_error:
                logger.warning(f"스트리밍 - 문서 검색 중 오류 (무시하고 계속): {str(search_error)}")
                search_results = []
            
            context_parts = []
            if search_results:
                context_parts.append("관련 문서 정보:")
                for i, result in enumerate(search_results[:3], 1):
                    filename = result["metadata"].get("filename", f"문서{i}")
                    content_preview = result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"]
                    context_parts.append(f"[{filename}] {content_preview}")
            else:
                context_parts.append("현재 업로드된 문서가 없거나 검색할 수 없습니다. 일반적인 제조업 지식을 바탕으로 답변드리겠습니다.")
            
            context = "\n".join(context_parts)
            
            # 스트리밍 프롬프트
            streaming_prompt = f"""
            제조업 전문 AI 어드바이저로서 다음 질문에 답변해주세요.
            
            질문: {user_query}
            
            참고 정보:
            {context}
            
            전문적이고 실용적인 답변을 제공해주세요.
            """
            
            # 스트리밍 응답 생성
            async for chunk in self.streaming_llm_client.generate_stream(streaming_prompt):
                yield chunk
                    
        except Exception as e:
            yield f"스트리밍 응답 생성 중 오류 발생: {str(e)}"


class AdvisorAgentManager:
    """어드바이저 에이전트 관리자 - 여러 에이전트 인스턴스 관리"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
        self.agents = {}
        self.default_agent_id = "default"
    
    async def create_agent(self, 
                          agent_id: str, 
                          model_name: str = None, 
                          streaming: bool = True,
                          **kwargs) -> AdvisorAgent:
        """새로운 에이전트 인스턴스 생성"""
        try:
            agent = AdvisorAgent(
                config=self.config,
                model_name=model_name,
                streaming=streaming,
                **kwargs
            )
            
            # 비동기 초기화 대기
            await agent._initialize_async_components()
            
            self.agents[agent_id] = agent
            logger.info(f"에이전트 생성됨: {agent_id}")
            
            return agent
            
        except Exception as e:
            logger.error(f"에이전트 생성 오류 - {agent_id}: {str(e)}")
            raise AIAdvisorException(f"에이전트 생성 실패: {str(e)}")
    
    async def get_agent(self, agent_id: str = None) -> Optional[AdvisorAgent]:
        """에이전트 인스턴스 조회"""
        agent_id = agent_id or self.default_agent_id
        
        if agent_id not in self.agents:
            # 기본 에이전트 자동 생성
            if agent_id == self.default_agent_id:
                return await self.create_agent(agent_id)
            else:
                return None
        
        return self.agents[agent_id]

    async def get_default_agent(self) -> AdvisorAgent:
        """기본 에이전트 인스턴스 조회"""
        return await self.get_agent(self.default_agent_id)
    
    async def remove_agent(self, agent_id: str) -> bool:
        """에이전트 인스턴스 제거"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"에이전트 제거됨: {agent_id}")
            return True
        return False
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """에이전트 목록 조회"""
        return [
            {
                "agent_id": agent_id,
                "model_name": agent.model_name,
                "streaming": agent.streaming,
                "status": "active"
            }
            for agent_id, agent in self.agents.items()
        ]
    
    async def query_agent(self, 
                         user_query: str, 
                         agent_id: str = None, 
                         use_workflow: bool = False) -> Dict[str, Any]:
        """특정 에이전트에게 질의"""
        agent = await self.get_agent(agent_id)
        
        if not agent:
            raise AIAdvisorException(f"에이전트를 찾을 수 없습니다: {agent_id}")
        
        return await agent.query(user_query)