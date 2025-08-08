"""
DX-AI Advisor - 고급 제조업 특화 AI 어드바이저 에이전트 모듈

다중 모델 지원과 고급 분석 기능을 제공하는 제조업 특화 AI 어드바이저 시스템
온톨로지 기반 지식 그래프와 벡터 검색을 통합한 고성능 분석 기능
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
from .source_tracker import StreamingSourceTracker
from ..ai.core.llm_client import get_ollama_client, create_ollama_client
from ..ai.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)


class AdvancedManufacturingAdvisorAgent:
    """고급 제조업 특화 AI 어드바이저 에이전트 - 다중 모델 지원"""
    
    def __init__(self, 
                 config: Optional[AIAdvisorConfig] = None,
                 embedding_manager: Optional[EmbeddingManager] = None,
                 ontology_manager: Optional[OntologyManager] = None,
                 model_name: str = None,
                 streaming: bool = True,
                 analysis_mode: str = "standard"):
        
        # config가 코루틴인 경우 처리
        if config is not None and hasattr(config, '__await__'):
            # 코루틴인 경우 기본 설정 사용
            self.config = get_config()
        else:
            self.config = config or get_config()
            
        self.model_name = model_name or self.config.default_llm_model
        self.streaming = streaming
        self.analysis_mode = analysis_mode  # "standard", "advanced", "expert"
        
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
        
        # 분석 모드별 설정
        self.analysis_configs = {
            "standard": {"search_k": 5, "context_limit": 3, "depth": "basic"},
            "advanced": {"search_k": 10, "context_limit": 5, "depth": "detailed"},
            "expert": {"search_k": 15, "context_limit": 8, "depth": "comprehensive"}
        }
        
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
            
            logger.info(f"고급 제조업 특화 AI 어드바이저 에이전트 초기화 완료 - 모델: {self.model_name} (모드: {self.analysis_mode})")
            
        except Exception as e:
            logger.error(f"고급 어드바이저 에이전트 초기화 오류: {str(e)}")
            raise AIAdvisorException(f"고급 어드바이저 에이전트 초기화 실패: {str(e)}")
    
    async def _analyze_manufacturing_context_advanced(self, user_query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """고급 제조업 컨텍스트 분석"""
        try:
            context_analysis = {
                "domain": "general",
                "keywords": [],
                "process_related": False,
                "quality_related": False,
                "safety_related": False,
                "efficiency_related": False,
                "complexity_level": "basic",
                "technical_terms": [],
                "recommended_approach": "standard"
            }
            
            # 검색 결과에서 도메인 정보 추출
            if search_results:
                domains = []
                technical_terms = []
                
                for result in search_results:
                    metadata = result.get("metadata", {})
                    domain = metadata.get("manufacturing_domain", "general")
                    if domain != "general":
                        domains.append(domain)
                    
                    # 기술 용어 추출
                    content = result.get("content", "")
                    extracted_terms = metadata.get("quality_keywords", []) + metadata.get("process_keywords", [])
                    technical_terms.extend(extracted_terms)
                
                if domains:
                    # 가장 빈번한 도메인 선택
                    from collections import Counter
                    domain_counts = Counter(domains)
                    context_analysis["domain"] = domain_counts.most_common(1)[0][0]
                
                # 기술 용어 정리
                context_analysis["technical_terms"] = list(set(technical_terms))
            
            # 질문 복잡도 분석
            query_lower = user_query.lower()
            complexity_indicators = {
                "basic": ["무엇", "어떻게", "언제", "어디서"],
                "intermediate": ["왜", "어떤", "어떻게 하면", "방법"],
                "advanced": ["근본원인", "최적화", "분석", "전략", "시스템"]
            }
            
            for level, indicators in complexity_indicators.items():
                if any(indicator in query_lower for indicator in indicators):
                    context_analysis["complexity_level"] = level
                    break
            
            # 제조업 키워드 분석
            manufacturing_keywords = {
                "process": ["공정", "프로세스", "제조", "생산", "조업", "가공", "설비", "라인"],
                "quality": ["품질", "검사", "테스트", "불량", "결함", "스펙", "표준", "인증"],
                "safety": ["안전", "사고", "위험", "보호", "환경", "폐기물", "규정", "법규"],
                "efficiency": ["효율", "생산성", "원가", "비용", "최적화", "개선", "KPI", "성과"]
            }
            
            for category, keywords in manufacturing_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    context_analysis[f"{category}_related"] = True
                    context_analysis["keywords"].extend(keywords)
            
            # 권장 접근 방식 결정
            if context_analysis["complexity_level"] == "advanced" or len(context_analysis["technical_terms"]) > 5:
                context_analysis["recommended_approach"] = "expert"
            elif context_analysis["complexity_level"] == "intermediate" or len(context_analysis["technical_terms"]) > 2:
                context_analysis["recommended_approach"] = "advanced"
            else:
                context_analysis["recommended_approach"] = "standard"
            
            return context_analysis
            
        except Exception as e:
            logger.warning(f"고급 컨텍스트 분석 중 오류: {str(e)}")
            return {"domain": "general", "keywords": [], "process_related": False, 
                   "quality_related": False, "safety_related": False, "efficiency_related": False,
                   "complexity_level": "basic", "technical_terms": [], "recommended_approach": "standard"}
    
    async def _generate_advanced_manufacturing_response(self, user_query: str, context_analysis: Dict[str, Any], 
                                                       search_results: List[Dict[str, Any]]) -> str:
        """고급 제조업 특화 응답 생성"""
        try:
            # 분석 모드별 설정 가져오기
            analysis_config = self.analysis_configs.get(self.analysis_mode, self.analysis_configs["standard"])
            
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
            
            # 복잡도별 접근 방식
            complexity_approaches = {
                "basic": "기본적인 설명과 실용적인 조언을 제공하세요.",
                "intermediate": "상세한 분석과 구체적인 해결 방안을 제시하세요.",
                "advanced": "전문적인 분석, 근본원인 분석, 그리고 종합적인 전략을 제공하세요."
            }
            
            approach_guidance = complexity_approaches.get(context_analysis["complexity_level"], complexity_approaches["basic"])
            
            # 컨텍스트 구성
            context_parts = []
            if search_results:
                context_parts.append("관련 문서 정보:")
                for i, result in enumerate(search_results[:analysis_config["context_limit"]], 1):
                    filename = result["metadata"].get("filename", f"문서{i}")
                    content_preview = result["content"][:400] + "..." if len(result["content"]) > 400 else result["content"]
                    context_parts.append(f"[{filename}] {content_preview}")
            
            context = "\n".join(context_parts) if context_parts else "현재 업로드된 문서가 없습니다. 일반적인 제조업 지식을 바탕으로 답변드리겠습니다."
            
            # 기술 용어 정보
            technical_terms_info = ""
            if context_analysis["technical_terms"]:
                technical_terms_info = f"\n관련 기술 용어: {', '.join(context_analysis['technical_terms'][:10])}"
            
            # 고급 응답 프롬프트
            response_prompt = f"""
            {domain_expert} 다음 질문에 대해 전문적이고 실용적인 답변을 제공해주세요.
            
            질문: {user_query}
            
            참고 정보:
            {context}{technical_terms_info}
            
            분석 요구사항:
            - 복잡도: {context_analysis['complexity_level']}
            - 접근 방식: {approach_guidance}
            
            답변 지침:
            1. 검색된 정보의 출처를 명시하세요 (예: "[문서명]에 따르면...")
            2. 제조업 전문가 관점에서 기술적으로 정확한 정보를 제공하세요
            3. 근본원인 분석과 구체적인 해결 방안을 제시하세요
            4. 실현 가능한 실행 계획과 권장사항을 포함하세요
            5. 관련된 위험 요소나 고려사항을 언급하세요
            6. 전문 용어는 쉽게 설명하여 이해하기 쉽게 하세요
            7. 제조업 표준과 규정을 고려한 답변을 제공하세요
            8. 데이터 기반의 객관적인 분석을 포함하세요
            9. ROI와 비용 효율성을 고려한 권장사항을 제공하세요
            10. 지속가능성과 환경 영향을 고려하세요
            
            전문적이면서도 이해하기 쉬운 답변을 제공해주세요.
            """
            
            response = await self.llm_client.llm.ainvoke(response_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            return response_text
            
        except Exception as e:
            logger.error(f"고급 응답 생성 중 오류: {str(e)}")
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    # 메인 실행 메서드들
    async def query(self, user_query: str, conversation_id: str = None) -> Dict[str, Any]:
        """사용자 질의 처리 (고급 제조업 특화)"""
        try:
            # 분석 모드별 설정 가져오기
            analysis_config = self.analysis_configs.get(self.analysis_mode, self.analysis_configs["standard"])
            
            # 관련 문서 검색 (강화된 처리)
            search_results = []
            try:
                await self.embedding_manager.ensure_initialized()
                search_results = await self.embedding_manager.search_similar_documents(user_query, k=analysis_config["search_k"])
                logger.info(f"고급 문서 검색 결과: {len(search_results)}개 (모드: {self.analysis_mode})")
            except Exception as search_error:
                logger.warning(f"문서 검색 중 오류 (무시하고 계속): {str(search_error)}")
                search_results = []
            
            # 고급 제조업 컨텍스트 분석
            context_analysis = await self._analyze_manufacturing_context_advanced(user_query, search_results)
            
            # 응답 생성
            response_text = await self._generate_advanced_manufacturing_response(user_query, context_analysis, search_results)
            
            return {
                "query": user_query,
                "response": response_text,
                "mode": f"advanced_manufacturing_{self.analysis_mode}",
                "domain": context_analysis["domain"],
                "complexity_level": context_analysis["complexity_level"],
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
        """스트리밍 응답 생성 (고급 제조업 특화)"""
        try:
            # 분석 모드별 설정 가져오기
            analysis_config = self.analysis_configs.get(self.analysis_mode, self.analysis_configs["standard"])
            
            # 컨텍스트 수집
            search_results = []
            try:
                await self.embedding_manager.ensure_initialized()
                search_results = await self.embedding_manager.search_similar_documents(user_query, k=analysis_config["search_k"])
                logger.info(f"고급 스트리밍 - 문서 검색 결과: {len(search_results)}개")
            except Exception as search_error:
                logger.warning(f"스트리밍 - 문서 검색 중 오류 (무시하고 계속): {str(search_error)}")
                search_results = []
            
            # 출처 추적기 초기화
            source_tracker = StreamingSourceTracker()
            source_tracker.add_search_results(search_results)
            
            # 고급 제조업 컨텍스트 분석
            context_analysis = await self._analyze_manufacturing_context_advanced(user_query, search_results)
            
            # 컨텍스트 구성
            context_parts = []
            if search_results:
                context_parts.append("관련 문서 정보:")
                for i, result in enumerate(search_results[:analysis_config["context_limit"]], 1):
                    filename = result["metadata"].get("filename", f"문서{i}")
                    content_preview = result["content"][:400] + "..." if len(result["content"]) > 400 else result["content"]
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
            
            분석 모드: {self.analysis_mode}
            복잡도: {context_analysis['complexity_level']}
            
            전문적이고 실용적인 답변을 제공해주세요.
            """
            
            # 스트리밍 응답 생성
            async for chunk in self.streaming_llm_client.generate_stream(streaming_prompt):
                source_tracker.add_response_chunk(chunk)
                yield chunk
            
            # 출처 정보 추가
            sources_text = source_tracker.tracker.get_formatted_sources()
            if sources_text:
                yield sources_text
                    
        except Exception as e:
            yield f"스트리밍 응답 생성 중 오류 발생: {str(e)}"
    
    async def switch_analysis_mode(self, mode: str) -> bool:
        """분석 모드 전환"""
        try:
            if mode in self.analysis_configs:
                self.analysis_mode = mode
                logger.info(f"✅ 분석 모드 전환 성공: {mode}")
                return True
            else:
                logger.error(f"❌ 지원하지 않는 분석 모드: {mode}")
                return False
                
        except Exception as e:
            logger.error(f"분석 모드 전환 오류: {str(e)}")
            return False
    
    def get_current_config(self) -> Dict[str, Any]:
        """현재 설정 정보 반환"""
        return {
            "model_name": self.model_name,
            "analysis_mode": self.analysis_mode,
            "streaming": self.streaming,
            "analysis_config": self.analysis_configs.get(self.analysis_mode, {}),
            "manufacturing_domains": self.manufacturing_domains
        }
    

    
    async def close(self):
        """리소스 정리"""
        try:
            logger.info("고급 제조업 어드바이저 에이전트 리소스 정리 완료")
        except Exception as e:
            logger.error(f"리소스 정리 오류: {str(e)}")


class AdvancedManufacturingAdvisorAgentManager:
    """고급 제조업 특화 어드바이저 에이전트 관리자"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
        self.agents = {}
        self.default_agent_id = "default"
    
    async def create_agent(self, 
                          agent_id: str, 
                          model_name: str = None, 
                          streaming: bool = True,
                          analysis_mode: str = "standard",
                          **kwargs) -> AdvancedManufacturingAdvisorAgent:
        """새로운 고급 에이전트 인스턴스 생성"""
        try:
            agent = AdvancedManufacturingAdvisorAgent(
                config=self.config,
                model_name=model_name,
                streaming=streaming,
                analysis_mode=analysis_mode,
                **kwargs
            )
            
            # 비동기 초기화 대기
            await agent._initialize_async_components()
            
            self.agents[agent_id] = agent
            logger.info(f"고급 제조업 특화 에이전트 생성됨: {agent_id} (분석 모드: {analysis_mode})")
            
            return agent
            
        except Exception as e:
            logger.error(f"고급 에이전트 생성 오류 - {agent_id}: {str(e)}")
            raise AIAdvisorException(f"고급 에이전트 생성 실패: {str(e)}")
    
    async def get_agent(self, agent_id: str = None) -> Optional[AdvancedManufacturingAdvisorAgent]:
        """에이전트 인스턴스 조회"""
        agent_id = agent_id or self.default_agent_id
        
        if agent_id not in self.agents:
            # 기본 에이전트 자동 생성
            if agent_id == self.default_agent_id:
                return await self.create_agent(agent_id)
            else:
                return None
        
        return self.agents[agent_id]

    async def get_default_agent(self) -> AdvancedManufacturingAdvisorAgent:
        """기본 에이전트 인스턴스 조회"""
        return await self.get_agent(self.default_agent_id)
    
    async def switch_agent_analysis_mode(self, agent_id: str, mode: str) -> bool:
        """특정 에이전트의 분석 모드 전환"""
        agent = await self.get_agent(agent_id)
        if agent:
            return await agent.switch_analysis_mode(mode)
        return False
    
    async def remove_agent(self, agent_id: str) -> bool:
        """에이전트 인스턴스 제거"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await agent.close()
            del self.agents[agent_id]
            logger.info(f"고급 에이전트 제거됨: {agent_id}")
            return True
        return False
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """에이전트 목록 조회"""
        return [
            {
                "agent_id": agent_id,
                "config": agent.get_current_config(),
                "status": "active"
            }
            for agent_id, agent in self.agents.items()
        ]
    
    async def query_agent(self, 
                         user_query: str, 
                         agent_id: str = None, 
                         conversation_id: str = None) -> Dict[str, Any]:
        """특정 에이전트에게 질의"""
        agent = await self.get_agent(agent_id)
        
        if not agent:
            raise AIAdvisorException(f"에이전트를 찾을 수 없습니다: {agent_id}")
        
        return await agent.query(user_query, conversation_id)
    



# 하위 호환성을 위한 별칭
HybridAdvisorAgent = AdvancedManufacturingAdvisorAgent
HybridAdvisorAgentManager = AdvancedManufacturingAdvisorAgentManager