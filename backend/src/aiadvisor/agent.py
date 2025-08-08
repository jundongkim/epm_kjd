"""
DX-AI Advisor - AI 어드바이저 에이전트 모듈

LangChain과 LangGraph를 활용한 지능형 어드바이저 에이전트 시스템
온톨로지 기반 지식 그래프와 벡터 검색을 통합한 하이브리드 검색 및 분석 기능
제조업 특화 AI 어드바이저 시스템
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


class ManufacturingAdvisorAgent:
    """제조업 특화 AI 어드바이저 에이전트 - 고성능 지능형 분석 시스템"""
    
    def __init__(self, 
                 config: Optional[AIAdvisorConfig] = None,
                 embedding_manager: Optional[EmbeddingManager] = None,
                 ontology_manager: Optional[OntologyManager] = None,
                 model_name: str = None,
                 streaming: bool = True):
        
        # config가 코루틴인 경우 처리
        if config is not None and hasattr(config, '__await__'):
            # 코루틴인 경우 기본 설정 사용
            self.config = get_config()
        else:
            self.config = config or get_config()
            
        self.model_name = model_name or self.config.default_llm_model
        self.streaming = streaming
        
        # 컴포넌트 초기화
        self.embedding_manager = embedding_manager or EmbeddingManager(config)
        self.ontology_manager = ontology_manager or OntologyManager(config)
        self.search_engine = VectorSearchEngine(self.embedding_manager)
        
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
        
        # 제조업 특화 설정
        self.manufacturing_domains = [
            'chemical', 'electronics', 'automotive', 'machinery', 
            'textile', 'food', 'pharmaceutical', 'general'
        ]
        
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
            
            logger.info(f"제조업 특화 AI 어드바이저 에이전트 초기화 완료 - 모델: {self.model_name}")
            
        except Exception as e:
            logger.error(f"어드바이저 에이전트 초기화 오류: {str(e)}")
            raise AIAdvisorException(f"어드바이저 에이전트 초기화 실패: {str(e)}")
    
    async def _analyze_manufacturing_context(self, user_query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """제조업 컨텍스트 분석"""
        try:
            context_analysis = {
                "domain": "general",
                "keywords": [],
                "process_related": False,
                "quality_related": False,
                "safety_related": False,
                "efficiency_related": False
            }
            
            # 검색 결과에서 도메인 정보 추출
            if search_results:
                domains = []
                for result in search_results:
                    domain = result.get("metadata", {}).get("manufacturing_domain", "general")
                    if domain != "general":
                        domains.append(domain)
                
                if domains:
                    # 가장 빈번한 도메인 선택
                    from collections import Counter
                    domain_counts = Counter(domains)
                    context_analysis["domain"] = domain_counts.most_common(1)[0][0]
            
            # 질문 키워드 분석
            query_lower = user_query.lower()
            manufacturing_keywords = {
                "process": ["공정", "프로세스", "제조", "생산", "조업", "가공"],
                "quality": ["품질", "검사", "테스트", "불량", "결함", "스펙"],
                "safety": ["안전", "사고", "위험", "보호", "환경", "폐기물"],
                "efficiency": ["효율", "생산성", "원가", "비용", "최적화", "개선"]
            }
            
            for category, keywords in manufacturing_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    context_analysis[f"{category}_related"] = True
                    context_analysis["keywords"].extend(keywords)
            
            return context_analysis
            
        except Exception as e:
            logger.warning(f"컨텍스트 분석 중 오류: {str(e)}")
            return {"domain": "general", "keywords": [], "process_related": False, 
                   "quality_related": False, "safety_related": False, "efficiency_related": False}
    
    async def _generate_manufacturing_response(self, user_query: str, context_analysis: Dict[str, Any], 
                                             search_results: List[Dict[str, Any]]) -> str:
        """제조업 특화 응답 생성"""
        try:
            # 도메인별 전문 프롬프트 구성
            domain_prompts = {
                "chemical": "화학공정 전문가로서",
                "electronics": "전자제품 제조 전문가로서",
                "automotive": "자동차 제조 전문가로서",
                "machinery": "기계제조 전문가로서",
                "textile": "섬유제조 전문가로서",
                "food": "식품제조 전문가로서",
                "pharmaceutical": "제약제조 전문가로서",
                "general": "제조업 전문가로서"
            }
            
            domain_expert = domain_prompts.get(context_analysis["domain"], "제조업 전문가로서")
            
            # 컨텍스트 구성
            context_parts = []
            if search_results:
                context_parts.append("관련 문서 정보:")
                for i, result in enumerate(search_results[:3], 1):
                    filename = result["metadata"].get("filename", f"문서{i}")
                    content_preview = result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"]
                    context_parts.append(f"[{filename}] {content_preview}")
            
            context = "\n".join(context_parts) if context_parts else "현재 업로드된 문서가 없습니다. 일반적인 제조업 지식을 바탕으로 답변드리겠습니다."
            
            # 전문 응답 프롬프트
            response_prompt = f"""
            {domain_expert} 다음 질문에 대해 전문적이고 실용적인 답변을 제공해주세요.
            
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
            7. 제조업 표준과 규정을 고려한 답변을 제공하세요
            8. 데이터 기반의 객관적인 분석을 포함하세요
            
            전문적이면서도 이해하기 쉬운 답변을 제공해주세요.
            """
            
            response = await self.llm_client.llm.ainvoke(response_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            return response_text
            
        except Exception as e:
            logger.error(f"응답 생성 중 오류: {str(e)}")
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    # 메인 실행 메서드들
    async def query(self, user_query: str, conversation_id: str = None) -> Dict[str, Any]:
        """사용자 질의 처리 (제조업 특화)"""
        try:
            # 관련 문서 검색 (강화된 처리)
            search_results = []
            try:
                await self.embedding_manager.ensure_initialized()
                search_results = await self.embedding_manager.search_similar_documents(user_query, k=5)
                logger.info(f"문서 검색 결과: {len(search_results)}개")
            except Exception as search_error:
                logger.warning(f"문서 검색 중 오류 (무시하고 계속): {str(search_error)}")
                search_results = []
            
            # 제조업 컨텍스트 분석
            context_analysis = await self._analyze_manufacturing_context(user_query, search_results)
            
            # 응답 생성
            response_text = await self._generate_manufacturing_response(user_query, context_analysis, search_results)
            
            return {
                "query": user_query,
                "response": response_text,
                "mode": "manufacturing_advisor",
                "domain": context_analysis["domain"],
                "context_analysis": context_analysis,
                "search_results": search_results,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"질의 처리 오류: {str(e)}")
            return {
                "query": user_query,
                "response": f"질의 처리 중 오류가 발생했습니다: {str(e)}",
                "mode": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def stream_response(self, user_query: str, conversation_id: str = None) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성 (제조업 특화)"""
        try:
            # 컨텍스트 수집
            search_results = []
            try:
                await self.embedding_manager.ensure_initialized()
                search_results = await self.embedding_manager.search_similar_documents(user_query, k=5)
                logger.info(f"스트리밍 - 문서 검색 결과: {len(search_results)}개")
            except Exception as search_error:
                logger.warning(f"스트리밍 - 문서 검색 중 오류 (무시하고 계속): {str(search_error)}")
                search_results = []
            
            # 제조업 컨텍스트 분석
            context_analysis = await self._analyze_manufacturing_context(user_query, search_results)
            
            # 컨텍스트 구성
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
            
            # 도메인별 전문 프롬프트
            domain_prompts = {
                "chemical": "화학공정 전문가로서",
                "electronics": "전자제품 제조 전문가로서",
                "automotive": "자동차 제조 전문가로서",
                "machinery": "기계제조 전문가로서",
                "textile": "섬유제조 전문가로서",
                "food": "식품제조 전문가로서",
                "pharmaceutical": "제약제조 전문가로서",
                "general": "제조업 전문가로서"
            }
            
            domain_expert = domain_prompts.get(context_analysis["domain"], "제조업 전문가로서")
            
            # 스트리밍 프롬프트
            streaming_prompt = f"""
            {domain_expert} 다음 질문에 답변해주세요.
            
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
    



class ManufacturingAdvisorAgentManager:
    """제조업 특화 어드바이저 에이전트 관리자"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
        self.agents = {}
        self.default_agent_id = "default"
    
    async def create_agent(self, 
                          agent_id: str, 
                          model_name: str = None, 
                          streaming: bool = True,
                          **kwargs) -> ManufacturingAdvisorAgent:
        """새로운 에이전트 인스턴스 생성"""
        try:
            agent = ManufacturingAdvisorAgent(
                config=self.config,
                model_name=model_name,
                streaming=streaming,
                **kwargs
            )
            
            # 비동기 초기화 대기
            await agent._initialize_async_components()
            
            self.agents[agent_id] = agent
            logger.info(f"제조업 특화 에이전트 생성됨: {agent_id}")
            
            return agent
            
        except Exception as e:
            logger.error(f"에이전트 생성 오류 - {agent_id}: {str(e)}")
            raise AIAdvisorException(f"에이전트 생성 실패: {str(e)}")
    
    async def get_agent(self, agent_id: str = None) -> Optional[ManufacturingAdvisorAgent]:
        """에이전트 인스턴스 조회"""
        agent_id = agent_id or self.default_agent_id
        
        if agent_id not in self.agents:
            # 기본 에이전트 자동 생성
            if agent_id == self.default_agent_id:
                return await self.create_agent(agent_id)
            else:
                return None
        
        return self.agents[agent_id]

    async def get_default_agent(self) -> ManufacturingAdvisorAgent:
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
                         agent_id: str = None) -> Dict[str, Any]:
        """특정 에이전트에게 질의"""
        agent = await self.get_agent(agent_id)
        
        if not agent:
            raise AIAdvisorException(f"에이전트를 찾을 수 없습니다: {agent_id}")
        
        return await agent.query(user_query)
    



# 하위 호환성을 위한 별칭
AdvisorAgent = ManufacturingAdvisorAgent
AdvisorAgentManager = ManufacturingAdvisorAgentManager