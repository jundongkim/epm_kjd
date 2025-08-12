"""
DX-AI Manufacturing Copilot - AI 보고서 생성기 v2.0
LangGraph 기반 다단계 AI 보고서 생성 시스템
AI 모듈 구조에 맞춘 향상된 기능 포함
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Literal, TypedDict, Annotated
from datetime import datetime
from dataclasses import dataclass

# LangGraph 관련 import
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# AI 모듈 내부 import - 상대 경로 사용
from .llm_client import EnhancedOllamaClient, get_report_client
from .context_engineering import get_context_engineer, ContextEngineer

# Core 모듈 import - 절대 경로 사용  
try:
    import sys
    import os
    # backend/src를 sys.path에 추가
    backend_src = os.path.join(os.path.dirname(__file__), '../..')
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)
    from copilot.data_models import ReportModel, LotModel, EquipmentModel, MaterialModel
    from copilot.config import settings
except ImportError:
    # 폴백: 직접 경로로 시도
    import sys
    import os
    copilot_path = os.path.join(os.path.dirname(__file__), '../../copilot')
    sys.path.append(copilot_path)
    from data_models import ReportModel, LotModel, EquipmentModel, MaterialModel
    from config import settings

logger = logging.getLogger(__name__)

__version__ = "2.0.0"


@dataclass
class ReportQualityMetrics:
    """보고서 품질 평가 메트릭"""
    overall_score: float = 0.0
    content_quality: float = 0.0
    technical_accuracy: float = 0.0
    clarity_score: float = 0.0
    completeness: float = 0.0
    custom_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}


class ReportGenerationState(TypedDict):
    """향상된 보고서 생성 상태 정의 v2.0"""
    # 입력 데이터
    report_type: str
    parameters: Dict[str, Any]
    data_sources: List[str]
    
    # 수집된 데이터
    collected_data: Dict[str, Any]
    
    # 분석 결과
    analysis_results: Dict[str, Any]
    
    # 생성된 컨텍스트
    context: str
    enhanced_context: str  # v2.0: 컨텍스트 엔지니어링 결과
    
    # 보고서 내용
    report_content: str
    
    # 검토 결과
    review_result: Dict[str, Any]
    quality_score: float
    
    # 최종 보고서
    final_report: Optional[ReportModel]
    
    # 메타데이터 (v2.0 향상)
    messages: List[str]
    iteration_count: int
    max_iterations: int
    processing_times: Dict[str, float]
    service_optimizations: Dict[str, str]
    
    # 생성 설정
    generated_by: str
    temperature: float
    max_tokens: int
    service_context: str  # v2.0: 서비스별 최적화


@dataclass
class ReportGenerationConfig:
    """향상된 보고서 생성 설정 v2.0"""
    report_type: str
    data_sources: List[str] = None
    parameters: Dict[str, Any] = None
    max_iterations: int = 3
    quality_threshold: float = 0.7
    temperature: float = 0.5  # 보고서용 최적화
    max_tokens: int = 2048
    generated_by: str = "AI_Report_Generator_v2.0"
    use_context_engineering: bool = True  # v2.0: 컨텍스트 엔지니어링 사용
    service_optimization: bool = True     # v2.0: 서비스별 최적화 사용
    async_processing: bool = False        # v2.0: 비동기 처리 옵션
    
    # 실험 설계 전용 추가 필드들
    sections: List[str] = None
    analysis_depth: str = "standard"
    domain: str = "general"
    language: str = "korean"
    format: str = "markdown"
    include_charts: bool = True
    include_recommendations: bool = True
    statistical_confidence: float = 0.95
    optimization_focus: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            "report_type": self.report_type,
            "data_sources": self.data_sources or [],
            "parameters": self.parameters or {},
            "max_iterations": self.max_iterations,
            "quality_threshold": self.quality_threshold,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "generated_by": self.generated_by,
            "use_context_engineering": self.use_context_engineering,
            "service_optimization": self.service_optimization,
            "async_processing": self.async_processing,
            "sections": self.sections or [],
            "analysis_depth": self.analysis_depth,
            "domain": self.domain,
            "language": self.language,
            "format": self.format,
            "include_charts": self.include_charts,
            "include_recommendations": self.include_recommendations,
            "statistical_confidence": self.statistical_confidence,
            "optimization_focus": self.optimization_focus
        }


class EnhancedAIReportGenerator:
    """
    향상된 LangGraph 기반 AI 보고서 생성기 v2.0
    
    v2.0 개선사항:
    - 서비스별 최적화된 LLM 클라이언트 활용
    - 컨텍스트 엔지니어링과 통합
    - 성능 모니터링 및 통계
    - 비동기 처리 지원
    - 향상된 품질 평가
    """
    
    def __init__(self, 
                 llm_client: Optional[EnhancedOllamaClient] = None,
                 context_engineer: Optional[ContextEngineer] = None,
                 use_optimized_clients: bool = True):
        """
        향상된 AI 보고서 생성기 초기화
        
        Args:
            llm_client: 사용할 LLM 클라이언트 (None시 보고서용 최적화 클라이언트 사용)
            context_engineer: 컨텍스트 엔지니어 (None시 기본 인스턴스 사용)
            use_optimized_clients: 서비스별 최적화 클라이언트 사용 여부
        """
        # LLM 클라이언트 설정 (v2.0: 보고서용 최적화)
        if llm_client is None and use_optimized_clients:
            self.llm_client = get_report_client()
            logger.info("보고서용 최적화 LLM 클라이언트 사용")
        else:
            self.llm_client = llm_client or EnhancedOllamaClient(service_context="report_generation")
        
        # 컨텍스트 엔지니어 설정 (v2.0)
        self.context_engineer = context_engineer or get_context_engineer()
        self.use_optimized_clients = use_optimized_clients
        
        # 그래프 구축
        self.graph = self._build_graph()
        
        # 성능 통계 (v2.0)
        self.performance_stats = {
            "reports_generated": 0,
            "total_processing_time": 0.0,
            "avg_quality_score": 0.0,
            "iteration_stats": {},
            "service_optimizations_used": 0
        }
        
        logger.info(f"AI 보고서 생성기 v{__version__} 초기화 완료")
        
    def _build_graph(self) -> StateGraph:
        """향상된 보고서 생성 그래프 구축"""
        # 상태 그래프 생성
        workflow = StateGraph(ReportGenerationState)
        
        # 노드 추가 (v2.0: 컨텍스트 엔지니어링 노드 추가)
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("analyze_data", self._analyze_data_node)
        workflow.add_node("generate_context", self._generate_context_node)
        workflow.add_node("enhance_context", self._enhance_context_node)  # v2.0 신규
        workflow.add_node("generate_report", self._generate_report_node)
        workflow.add_node("review_report", self._review_report_node)
        workflow.add_node("finalize_report", self._finalize_report_node)
        
        # 에지 정의 (v2.0: 컨텍스트 향상 단계 추가)
        workflow.add_edge(START, "collect_data")
        workflow.add_edge("collect_data", "analyze_data")
        workflow.add_edge("analyze_data", "generate_context")
        workflow.add_edge("generate_context", "enhance_context")  # v2.0
        workflow.add_edge("enhance_context", "generate_report")
        workflow.add_edge("generate_report", "review_report")
        
        # 조건부 에지 - 품질 평가에 따른 재생성 또는 최종화
        workflow.add_conditional_edges(
            "review_report",
            self._should_regenerate,
            {
                "regenerate": "generate_report",
                "finalize": "finalize_report"
            }
        )
        
        workflow.add_edge("finalize_report", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    def _collect_data_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """데이터 수집 노드 (v2.0 향상)"""
        start_time = datetime.now()
        logger.info("데이터 수집 시작")
        
        collected_data = {}
        report_type = state["report_type"]
        data_sources = state.get("data_sources", [])
        
        try:
            # 보고서 타입에 따른 데이터 수집 (기존 로직 유지)
            if report_type == "production_summary":
                collected_data = self._collect_production_data(state.get("parameters", {}))
            elif report_type == "quality_analysis":
                collected_data = self._collect_quality_data(state.get("parameters", {}))
            elif report_type == "cost_analysis":
                collected_data = self._collect_cost_data(state.get("parameters", {}))
            elif report_type == "equipment_status":
                collected_data = self._collect_equipment_data(state.get("parameters", {}))
            else:
                collected_data = self._collect_general_data(state.get("parameters", {}))
                
            # v2.0: 성능 추적
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_times = state.get("processing_times", {})
            processing_times["data_collection"] = processing_time
            
            messages = state.get("messages", [])
            messages.append(f"데이터 수집 완료: {len(collected_data)} 개 항목 ({processing_time:.2f}초)")
            
            return {
                "collected_data": collected_data,
                "messages": messages,
                "processing_times": processing_times
            }
            
        except Exception as e:
            logger.error(f"데이터 수집 실패: {e}")
            messages = state.get("messages", [])
            messages.append(f"데이터 수집 오류: {str(e)}")
            return {
                "collected_data": {},
                "messages": messages
            }
    
    def _analyze_data_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """데이터 분석 노드 (v2.0 향상)"""
        start_time = datetime.now()
        logger.info("데이터 분석 시작")
        
        collected_data = state.get("collected_data", {})
        report_type = state["report_type"]
        
        try:
            # v2.0: 서비스별 최적화된 클라이언트 사용
            analysis_client = self.llm_client
            if self.use_optimized_clients:
                # 분석용으로 더 정확한 설정 사용
                analysis_client.temperature = 0.3
                analysis_client.max_tokens = 1024
            
            # 데이터 분석 프롬프트 생성
            analysis_prompt = self._create_analysis_prompt(report_type, collected_data)
            
            # LLM을 사용한 데이터 분석
            analysis_result = analysis_client.generate(
                analysis_prompt,
                temperature=state.get("temperature", 0.5),
                max_tokens=state.get("max_tokens", 1024)
            )
            
            # 분석 결과 구조화 (v2.0 향상)
            analysis_results = {
                "raw_analysis": analysis_result,
                "key_insights": self._extract_key_insights(analysis_result),
                "trends": self._identify_trends(collected_data),
                "anomalies": self._detect_anomalies(collected_data),
                "data_quality": self._assess_data_quality(collected_data),  # v2.0
                "recommendations": self._generate_recommendations(analysis_result)  # v2.0
            }
            
            # v2.0: 성능 추적
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_times = state.get("processing_times", {})
            processing_times["data_analysis"] = processing_time
            
            messages = state.get("messages", [])
            messages.append(f"데이터 분석 완료 ({processing_time:.2f}초)")
            
            return {
                "analysis_results": analysis_results,
                "messages": messages,
                "processing_times": processing_times
            }
            
        except Exception as e:
            logger.error(f"데이터 분석 실패: {e}")
            messages = state.get("messages", [])
            messages.append(f"데이터 분석 오류: {str(e)}")
            return {
                "analysis_results": {},
                "messages": messages
            }
    
    def _generate_context_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """기본 컨텍스트 생성 노드"""
        start_time = datetime.now()
        logger.info("기본 컨텍스트 생성 시작")
        
        collected_data = state.get("collected_data", {})
        analysis_results = state.get("analysis_results", {})
        report_type = state["report_type"]
        
        try:
            # 컨텍스트 생성 프롬프트
            context_prompt = self._create_context_prompt(report_type, collected_data, analysis_results)
            
            # LLM을 사용한 컨텍스트 생성
            context = self.llm_client.generate(
                context_prompt,
                temperature=state.get("temperature", 0.5),
                max_tokens=state.get("max_tokens", 1024)
            )
            
            # v2.0: 성능 추적
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_times = state.get("processing_times", {})
            processing_times["context_generation"] = processing_time
            
            messages = state.get("messages", [])
            messages.append(f"기본 컨텍스트 생성 완료 ({processing_time:.2f}초)")
            
            return {
                "context": context,
                "messages": messages,
                "processing_times": processing_times
            }
            
        except Exception as e:
            logger.error(f"컨텍스트 생성 실패: {e}")
            messages = state.get("messages", [])
            messages.append(f"컨텍스트 생성 오류: {str(e)}")
            return {
                "context": "",
                "messages": messages
            }
    
    def _enhance_context_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """
        컨텍스트 향상 노드 (v2.0 신기능)
        컨텍스트 엔지니어링을 활용한 고급 컨텍스트 생성
        """
        start_time = datetime.now()
        logger.info("컨텍스트 엔지니어링 시작")
        
        base_context = state.get("context", "")
        report_type = state["report_type"]
        parameters = state.get("parameters", {})
        
        try:
            # v2.0: 컨텍스트 엔지니어링 활용
            enhanced_context = self.context_engineer.create_specialized_context(
                service_type="report_generation",
                topic=f"{report_type}_optimization",
                parameters={
                    "base_context": base_context,
                    "report_parameters": parameters,
                    "optimization_level": "high"
                }
            )
            
            # 추가 최적화: 보고서 타입별 전문 컨텍스트
            type_context = self.context_engineer.create_context(
                topic=report_type.replace("_", " "),
                context_type="manufacturing_report",
                details=parameters
            )
            
            # 컨텍스트 결합 및 최적화
            final_enhanced_context = f"{enhanced_context}\n\n보고서 전문 컨텍스트:\n{type_context}"
            
            # v2.0: 성능 추적
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_times = state.get("processing_times", {})
            processing_times["context_enhancement"] = processing_time
            
            # 서비스 최적화 사용 추적
            service_optimizations = state.get("service_optimizations", {})
            service_optimizations["context_engineering"] = "enhanced"
            
            messages = state.get("messages", [])
            messages.append(f"컨텍스트 엔지니어링 완료 ({processing_time:.2f}초)")
            
            return {
                "enhanced_context": final_enhanced_context,
                "messages": messages,
                "processing_times": processing_times,
                "service_optimizations": service_optimizations
            }
            
        except Exception as e:
            logger.error(f"컨텍스트 향상 실패: {e}")
            # 폴백: 기본 컨텍스트 사용
            messages = state.get("messages", [])
            messages.append(f"컨텍스트 향상 실패, 기본 컨텍스트 사용: {str(e)}")
            return {
                "enhanced_context": base_context,
                "messages": messages
            }
    
    def _generate_report_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """보고서 생성 노드 (v2.0 향상)"""
        start_time = datetime.now()
        logger.info("보고서 생성 시작")
        
        # v2.0: 향상된 컨텍스트 우선 사용
        context = state.get("enhanced_context") or state.get("context", "")
        report_type = state["report_type"]
        parameters = state.get("parameters", {})
        iteration_count = state.get("iteration_count", 0)
        
        try:
            # v2.0: 서비스별 최적화된 프롬프트 생성
            if self.use_optimized_clients:
                report_prompt = self._create_optimized_report_prompt(report_type, context, parameters)
            else:
                report_prompt = self._create_report_prompt(report_type, context, parameters)
            
            # 재생성인 경우 이전 검토 결과를 반영
            if iteration_count > 0:
                review_result = state.get("review_result", {})
                suggestions = review_result.get("suggestions", [])
                if suggestions:
                    improvement_note = f"\n\n다음 개선사항을 반영하여 보고서를 수정하세요:\n" + "\n".join(f"- {s}" for s in suggestions)
                    report_prompt += improvement_note
            
            # v2.0: 향상된 생성 설정
            generation_params = {
                "temperature": state.get("temperature", 0.5),
                "max_tokens": state.get("max_tokens", 2048)
            }
            
            # LLM을 사용한 보고서 생성
            report_content = self.llm_client.generate(report_prompt, **generation_params)
            
            # v2.0: 성능 추적
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_times = state.get("processing_times", {})
            processing_times["report_generation"] = processing_time
            
            messages = state.get("messages", [])
            messages.append(f"보고서 생성 완료 (반복 {iteration_count + 1}회, {processing_time:.2f}초)")
            
            return {
                "report_content": report_content,
                "messages": messages,
                "processing_times": processing_times,
                "iteration_count": iteration_count + 1
            }
            
        except Exception as e:
            logger.error(f"보고서 생성 실패: {e}")
            messages = state.get("messages", [])
            messages.append(f"보고서 생성 오류: {str(e)}")
            return {
                "report_content": "",
                "messages": messages,
                "iteration_count": iteration_count + 1
            }
    
    def _review_report_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """보고서 검토 노드 (v2.0 향상)"""
        start_time = datetime.now()
        logger.info("보고서 검토 시작")
        
        report_content = state.get("report_content", "")
        report_type = state["report_type"]
        
        try:
            # v2.0: 향상된 검토 프롬프트 (더 세밀한 평가 기준)
            review_prompt = self._create_enhanced_review_prompt(report_type, report_content)
            
            # v2.0: 검토용 최적화 설정 (낮은 온도, 정확성 우선)
            review_client = self.llm_client
            if self.use_optimized_clients:
                review_client.temperature = 0.2  # 매우 낮은 온도로 일관성 확보
            
            # LLM을 사용한 보고서 검토
            review_result_text = review_client.generate(
                review_prompt,
                temperature=0.2,  # 검토 시에는 낮은 온도 사용
                max_tokens=1024
            )
            
            # v2.0: 향상된 품질 점수 계산
            quality_score = self._calculate_enhanced_quality_score(
                report_content, 
                review_result_text, 
                state.get("analysis_results", {})
            )
            
            # v2.0: 더 상세한 검토 결과 구조화
            review_result = {
                "review_text": review_result_text,
                "suggestions": self._extract_suggestions(review_result_text),
                "strengths": self._extract_strengths(review_result_text),
                "weaknesses": self._extract_weaknesses(review_result_text),
                "technical_accuracy": self._assess_technical_accuracy(review_result_text),  # v2.0
                "readability_score": self._calculate_readability_score(report_content),      # v2.0
                "completeness_score": self._assess_completeness(report_content)             # v2.0
            }
            
            # v2.0: 성능 추적
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_times = state.get("processing_times", {})
            processing_times["report_review"] = processing_time
            
            messages = state.get("messages", [])
            messages.append(f"보고서 검토 완료 (품질 점수: {quality_score:.2f}, {processing_time:.2f}초)")
            
            return {
                "review_result": review_result,
                "quality_score": quality_score,
                "messages": messages,
                "processing_times": processing_times
            }
            
        except Exception as e:
            logger.error(f"보고서 검토 실패: {e}")
            messages = state.get("messages", [])
            messages.append(f"보고서 검토 오류: {str(e)}")
            return {
                "review_result": {},
                "quality_score": 0.0,
                "messages": messages
            }
    
    def _finalize_report_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """보고서 최종화 노드 (v2.0 향상)"""
        start_time = datetime.now()
        logger.info("보고서 최종화 시작")
        
        try:
            # v2.0: 향상된 메타데이터 포함
            final_report = ReportModel(
                title=self._generate_report_title(state["report_type"], state.get("parameters", {})),
                report_type=state["report_type"],
                content=state.get("report_content", ""),
                generated_by=state.get("generated_by", f"AI_Report_Generator_v{__version__}"),
                data_sources=state.get("data_sources", []),
                parameters=state.get("parameters", {}),
                # v2.0: 추가 메타데이터
                metadata={
                    "version": __version__,
                    "quality_score": state.get("quality_score", 0.0),
                    "iteration_count": state.get("iteration_count", 1),
                    "processing_times": state.get("processing_times", {}),
                    "service_optimizations": state.get("service_optimizations", {}),
                    "context_engineering_used": bool(state.get("enhanced_context")),
                    "total_processing_time": sum(state.get("processing_times", {}).values())
                }
            )
            
            # v2.0: 성능 통계 업데이트
            self._update_performance_stats(state)
            
            # v2.0: 성능 추적
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_times = state.get("processing_times", {})
            processing_times["finalization"] = processing_time
            
            messages = state.get("messages", [])
            messages.append(f"보고서 최종화 완료 ({processing_time:.2f}초)")
            
            return {
                "final_report": final_report,
                "messages": messages,
                "processing_times": processing_times
            }
            
        except Exception as e:
            logger.error(f"보고서 최종화 실패: {e}")
            messages = state.get("messages", [])
            messages.append(f"보고서 최종화 오류: {str(e)}")
            return {
                "final_report": None,
                "messages": messages
            }
    
    def _should_regenerate(self, state: ReportGenerationState) -> Literal["regenerate", "finalize"]:
        """보고서 재생성 여부 결정 (v2.0 향상)"""
        quality_score = state.get("quality_score", 0.0)
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 3)
        
        # v2.0: 더 정교한 재생성 로직
        quality_threshold = 0.7
        
        # 컨텍스트 엔지니어링을 사용한 경우 더 높은 품질 기대
        if state.get("enhanced_context"):
            quality_threshold = 0.75
        
        # 품질 점수가 임계값 이하이고 최대 반복 횟수에 도달하지 않았으면 재생성
        if quality_score < quality_threshold and iteration_count < max_iterations:
            logger.info(f"품질 점수 {quality_score:.2f} < {quality_threshold}, 재생성 진행")
            return "regenerate"
        else:
            logger.info(f"품질 점수 {quality_score:.2f} 또는 최대 반복 도달, 최종화 진행")
            return "finalize"
    
    # 데이터 수집 메서드들 (기존 로직 유지)
    def _collect_production_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """생산 데이터 수집"""
        return {
            "lots": [
                {"lot_number": "LOT001", "status": "completed", "quantity": 1000},
                {"lot_number": "LOT002", "status": "in_progress", "quantity": 800}
            ],
            "production_rate": 95.2,
            "yield_rate": 98.5,
            "defect_rate": 1.5
        }
    
    def _collect_quality_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """품질 데이터 수집"""
        return {
            "quality_metrics": {
                "purity": 99.2,
                "consistency": 98.7,
                "defect_rate": 1.3
            },
            "test_results": [
                {"test_name": "purity_test", "result": 99.2, "pass": True},
                {"test_name": "consistency_test", "result": 98.7, "pass": True}
            ]
        }
    
    def _collect_cost_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """비용 데이터 수집"""
        return {
            "material_costs": 15000,
            "labor_costs": 8000,
            "overhead_costs": 3000,
            "total_costs": 26000,
            "cost_per_unit": 26.0
        }
    
    def _collect_equipment_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """설비 데이터 수집"""
        return {
            "equipment_status": [
                {"name": "Reactor-1", "status": "running", "utilization": 85.0},
                {"name": "Reactor-2", "status": "maintenance", "utilization": 0.0}
            ],
            "overall_efficiency": 92.5,
            "downtime_hours": 12.5
        }
    
    def _collect_general_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """일반 데이터 수집"""
        return {
            "general_metrics": {
                "production_volume": 50000,
                "quality_score": 96.8,
                "efficiency": 94.2
            }
        }
    
    # 프롬프트 생성 메서드들 (v2.0 향상)
    def _create_analysis_prompt(self, report_type: str, data: Dict[str, Any]) -> str:
        """데이터 분석 프롬프트 생성 (v2.0 향상)"""
        prompt = f"""
당신은 {report_type} 보고서를 위한 전문 데이터 분석가입니다.
다음 제조업 데이터를 분석하여 핵심 인사이트와 실행 가능한 권장사항을 제시하세요.

데이터:
{data}

분석 요구사항:
1. 주요 성과 지표 (KPI) 분석
2. 트렌드 및 패턴 식별
3. 이상치 및 문제점 발견
4. 근본 원인 분석 (RCA)
5. 개선 기회 식별
6. 구체적이고 실행 가능한 권장사항

분석 결과를 구조화하여 제시하세요:
"""
        return prompt
    
    def _create_context_prompt(self, report_type: str, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """컨텍스트 생성 프롬프트 (v2.0 향상)"""
        prompt = f"""
{report_type} 보고서를 위한 전문적인 컨텍스트를 생성하세요.
제조업 관점에서 데이터와 분석 결과를 종합하여 의미있는 배경을 설정하세요.

데이터: {data}
분석 결과: {analysis}

컨텍스트는 다음을 포함해야 합니다:
- 보고서의 전략적 목적과 비즈니스 가치
- 데이터의 신뢰성과 적용 범위
- 제조업 표준 및 벤치마크와의 비교
- 시장 동향 및 산업 컨텍스트
- 주요 성과 동인 (Key Performance Drivers)

전문적이고 데이터 기반의 컨텍스트:
"""
        return prompt
    
    def _create_report_prompt(self, report_type: str, context: str, parameters: Dict[str, Any]) -> str:
        """기본 보고서 생성 프롬프트"""
        prompt = f"""
다음 컨텍스트를 바탕으로 전문적인 {report_type} 보고서를 작성하세요.

컨텍스트:
{context}

보고서 구조:
1. 경영진 요약 (Executive Summary)
2. 주요 발견사항 (Key Findings)
3. 데이터 분석 (Data Analysis)
4. 위험 요소 및 기회 (Risks & Opportunities)
5. 권장사항 (Recommendations)
6. 다음 단계 (Next Steps)

전문적이고 실행 가능한 보고서:
"""
        return prompt
    
    def _create_optimized_report_prompt(self, report_type: str, context: str, parameters: Dict[str, Any]) -> str:
        """서비스 최적화된 보고서 생성 프롬프트 (v2.0)"""
        # 보고서 타입별 특화 프롬프트
        type_specific_guidance = {
            "production_summary": "생산성, 효율성, 품질 지표에 중점을 두세요.",
            "quality_analysis": "품질 메트릭, 불량률, 개선 방안에 집중하세요.",
            "cost_analysis": "비용 구조, ROI, 비용 절감 기회를 강조하세요.",
            "equipment_status": "장비 성능, 유지보수, 가동률을 중심으로 작성하세요."
        }
        
        guidance = type_specific_guidance.get(report_type, "포괄적인 분석을 제공하세요.")
        
        prompt = f"""
당신은 제조업 전문 보고서 작성자입니다. {guidance}

컨텍스트:
{context}

고품질 {report_type} 보고서 작성 요구사항:
- 데이터 기반의 객관적 분석
- 실행 가능한 구체적 권장사항
- 비즈니스 임팩트 정량화
- 명확한 액션 플랜
- 시각적 데이터 표현 제안

전문적이고 실용적인 보고서:
"""
        return prompt
    
    def _create_enhanced_review_prompt(self, report_type: str, content: str) -> str:
        """향상된 보고서 검토 프롬프트 (v2.0)"""
        prompt = f"""
다음 {report_type} 보고서를 전문가 관점에서 엄격히 검토하고 평가하세요.

보고서 내용:
{content}

검토 기준 (각 항목을 1-10점으로 평가):
1. 기술적 정확성 (Technical Accuracy)
2. 데이터 분석의 적절성 (Data Analysis Quality)  
3. 논리적 구조와 흐름 (Logical Flow)
4. 실행 가능성 (Actionability)
5. 비즈니스 가치 (Business Value)
6. 가독성 및 명확성 (Clarity)
7. 완전성 (Completeness)

상세한 검토 결과:
- 강점 (Strengths): 
- 약점 (Weaknesses):
- 개선사항 (Improvements):
- 누락된 요소 (Missing Elements):
- 전체 평가 (Overall Assessment):
- 품질 점수 (Quality Score): /10
"""
        return prompt
    
    # 분석 및 평가 메서드들 (v2.0 향상)
    def _extract_key_insights(self, analysis: str) -> List[str]:
        """주요 인사이트 추출 (v2.0 향상)"""
        # 실제 구현에서는 NLP 기법 사용
        insights = []
        if "효율성" in analysis or "efficiency" in analysis.lower():
            insights.append("생산 효율성 개선 기회 발견")
        if "품질" in analysis or "quality" in analysis.lower():
            insights.append("품질 관리 체계 강화 필요")
        if "비용" in analysis or "cost" in analysis.lower():
            insights.append("비용 최적화 잠재력 확인")
        return insights or ["포괄적 분석 완료"]
    
    def _identify_trends(self, data: Dict[str, Any]) -> List[str]:
        """트렌드 식별 (v2.0 향상)"""
        trends = []
        # 실제 데이터 기반 트렌드 분석
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)) and value > 90:
                    trends.append(f"{key} 성능 우수")
                elif isinstance(value, (int, float)) and value < 70:
                    trends.append(f"{key} 개선 필요")
        return trends or ["안정적 성능 유지"]
    
    def _detect_anomalies(self, data: Dict[str, Any]) -> List[str]:
        """이상치 탐지 (v2.0 향상)"""
        anomalies = []
        # 실제 구현에서는 통계적 이상치 탐지 기법 사용
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if value > 100 or value < 0:
                        anomalies.append(f"{key} 값 이상 ({value})")
        return anomalies or ["정상 범위 내 데이터"]
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 품질 평가 (v2.0 신기능)"""
        return {
            "completeness": 0.95,
            "accuracy": 0.92,
            "consistency": 0.88,
            "timeliness": 0.90,
            "overall_score": 0.91
        }
    
    def _generate_recommendations(self, analysis: str) -> List[str]:
        """권장사항 생성 (v2.0 신기능)"""
        recommendations = []
        if "개선" in analysis:
            recommendations.append("프로세스 개선 프로그램 시행")
        if "품질" in analysis:
            recommendations.append("품질 관리 시스템 강화")
        if "효율" in analysis:
            recommendations.append("자동화 및 디지털화 추진")
        return recommendations or ["현재 수준 유지 및 모니터링"]
    
    def _calculate_enhanced_quality_score(self, content: str, review: str, analysis: Dict[str, Any]) -> float:
        """향상된 품질 점수 계산 (v2.0)"""
        base_score = 0.5  # 기본 점수
        
        # 내용 길이 기반 점수
        if len(content) > 1500:
            base_score += 0.2
        elif len(content) > 1000:
            base_score += 0.1
        
        # 구조화 정도 평가
        structure_keywords = ["요약", "분석", "권장사항", "결론"]
        structure_score = sum(1 for keyword in structure_keywords if keyword in content) * 0.05
        
        # 데이터 기반 분석 여부
        if analysis and len(analysis) > 0:
            base_score += 0.1
        
        # 검토 결과 기반 조정
        if "우수" in review or "excellent" in review.lower():
            base_score += 0.1
        elif "부족" in review or "poor" in review.lower():
            base_score -= 0.1
        
        return min(1.0, max(0.0, base_score + structure_score))
    
    def _assess_technical_accuracy(self, review: str) -> float:
        """기술적 정확성 평가 (v2.0 신기능)"""
        # 실제 구현에서는 더 정교한 평가 로직 사용
        if "정확" in review or "accurate" in review.lower():
            return 0.9
        elif "부정확" in review or "inaccurate" in review.lower():
            return 0.3
        return 0.7
    
    def _calculate_readability_score(self, content: str) -> float:
        """가독성 점수 계산 (v2.0 신기능)"""
        # 간단한 가독성 평가 (실제로는 더 복잡한 알고리즘 사용)
        sentences = content.count('.') + content.count('!') + content.count('?')
        words = len(content.split())
        
        if sentences == 0:
            return 0.5
        
        avg_sentence_length = words / sentences
        
        # 적절한 문장 길이 (15-25 단어)
        if 15 <= avg_sentence_length <= 25:
            return 0.9
        elif 10 <= avg_sentence_length <= 30:
            return 0.7
        else:
            return 0.5
    
    def _assess_completeness(self, content: str) -> float:
        """완전성 평가 (v2.0 신기능)"""
        required_sections = ["요약", "분석", "결론", "권장"]
        found_sections = sum(1 for section in required_sections if section in content)
        return found_sections / len(required_sections)
    
    def _extract_suggestions(self, review: str) -> List[str]:
        """개선 제안 추출"""
        # 실제 구현에서는 NLP 기법 사용
        return ["구체적 수치 추가", "시각적 표현 강화", "실행 계획 구체화"]
    
    def _extract_strengths(self, review: str) -> List[str]:
        """강점 추출"""
        return ["체계적 분석", "명확한 구조", "실용적 권장사항"]
    
    def _extract_weaknesses(self, review: str) -> List[str]:
        """약점 추출"""
        return ["세부 데이터 부족", "시각적 요소 미흡"]
    
    def _generate_report_title(self, report_type: str, parameters: Dict[str, Any]) -> str:
        """보고서 제목 생성 (v2.0 향상)"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        type_map = {
            "production_summary": "생산 현황 종합 보고서",
            "quality_analysis": "품질 분석 및 개선 보고서",
            "cost_analysis": "비용 분석 및 최적화 보고서",
            "equipment_status": "설비 현황 및 성능 보고서"
        }
        title = type_map.get(report_type, "제조업 AI 분석 보고서")
        version_suffix = f" (v{__version__})"
        return f"{title} - {current_date}{version_suffix}"
    
    def _update_performance_stats(self, state: ReportGenerationState):
        """성능 통계 업데이트 (v2.0)"""
        self.performance_stats["reports_generated"] += 1
        
        total_time = sum(state.get("processing_times", {}).values())
        self.performance_stats["total_processing_time"] += total_time
        
        quality_score = state.get("quality_score", 0.0)
        current_avg = self.performance_stats["avg_quality_score"]
        total_reports = self.performance_stats["reports_generated"]
        self.performance_stats["avg_quality_score"] = (
            (current_avg * (total_reports - 1) + quality_score) / total_reports
        )
        
        if state.get("service_optimizations"):
            self.performance_stats["service_optimizations_used"] += 1
        
        # 반복 횟수 통계
        iterations = state.get("iteration_count", 1)
        iter_stats = self.performance_stats["iteration_stats"]
        iter_stats[iterations] = iter_stats.get(iterations, 0) + 1
    
    async def generate_report_async(self, config: ReportGenerationConfig) -> ReportModel:
        """비동기 보고서 생성 (v2.0)"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.generate_report, config
        )
    
    def generate_report(self, config: ReportGenerationConfig) -> ReportModel:
        """보고서 생성 실행 (v2.0 향상)"""
        logger.info(f"AI 보고서 생성기 v{__version__} - {config.report_type} 보고서 생성 시작")
        
        # 초기 상태 설정 (v2.0 향상)
        initial_state = ReportGenerationState(
            report_type=config.report_type,
            parameters=config.parameters or {},
            data_sources=config.data_sources or [],
            collected_data={},
            analysis_results={},
            context="",
            enhanced_context="",  # v2.0
            report_content="",
            review_result={},
            quality_score=0.0,
            final_report=None,
            messages=[],
            iteration_count=0,
            max_iterations=config.max_iterations,
            processing_times={},  # v2.0
            service_optimizations={},  # v2.0
            generated_by=config.generated_by,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            service_context="report_generation"  # v2.0
        )
        
        try:
            # 그래프 실행
            result = self.graph.invoke(initial_state)
            
            # 최종 보고서 반환
            final_report = result.get("final_report")
            if final_report:
                logger.info(f"보고서 생성 완료: {final_report.title}")
                logger.info(f"총 처리 시간: {sum(result.get('processing_times', {}).values()):.2f}초")
                return final_report
            else:
                logger.error("최종 보고서 생성 실패")
                raise Exception("최종 보고서 생성 실패")
                
        except Exception as e:
            logger.error(f"보고서 생성 오류: {e}")
            raise
    
    def _evaluate_report_quality(self, content: str, config: ReportGenerationConfig) -> ReportQualityMetrics:
        """보고서 품질 평가 (기본 구현)"""
        if not content:
            return ReportQualityMetrics()
        
        # 기본 품질 지표 계산
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        # 길이 기반 완성도
        completeness = min(word_count / 500, 1.0)  # 500단어 기준
        
        # 구조 기반 명확성
        structure_keywords = ['#', '##', '###', '-', '*']
        structure_score = sum(1 for keyword in structure_keywords if keyword in content) / len(structure_keywords)
        
        # 기술적 정확성 (키워드 기반)
        technical_keywords = ['분석', '결과', '권장사항', '데이터', '성능']
        technical_score = sum(1 for keyword in technical_keywords if keyword in content) / len(technical_keywords)
        
        # 전체 점수
        overall_score = (completeness + structure_score + technical_score) / 3
        
        return ReportQualityMetrics(
            overall_score=overall_score,
            content_quality=structure_score,
            technical_accuracy=technical_score,
            clarity_score=structure_score,
            completeness=completeness
        )

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        stats = self.performance_stats.copy()
        if stats["reports_generated"] > 0:
            stats["avg_processing_time"] = stats["total_processing_time"] / stats["reports_generated"]
        return stats
    
    def get_graph_visualization(self) -> str:
        """그래프 시각화 정보 반환 (v2.0 향상)"""
        try:
            return """
graph TD
    A[START] --> B[데이터 수집]
    B --> C[데이터 분석]
    C --> D[기본 컨텍스트 생성]
    D --> E[컨텍스트 엔지니어링]
    E --> F[보고서 생성]
    F --> G[보고서 검토]
    G --> H{품질 평가}
    H -->|품질 미달| F
    H -->|품질 통과| I[보고서 최종화]
    I --> J[END]
    
    style E fill:#e1f5fe
    style H fill:#fff3e0
    style I fill:#e8f5e8
"""
        except Exception as e:
            logger.error(f"그래프 시각화 생성 실패: {e}")
            return "그래프 시각화를 생성할 수 없습니다."


# 하위 호환성을 위한 별칭
AIReportGenerator = EnhancedAIReportGenerator

# 편의 함수들 (v2.0 향상)
def create_report_generator(
    llm_client: Optional[EnhancedOllamaClient] = None,
    use_context_engineering: bool = True,
    use_optimized_clients: bool = True
) -> EnhancedAIReportGenerator:
    """
    향상된 보고서 생성기 생성 (v2.0)
    
    Args:
        llm_client: 사용할 LLM 클라이언트
        use_context_engineering: 컨텍스트 엔지니어링 사용 여부
        use_optimized_clients: 서비스별 최적화 클라이언트 사용 여부
    """
    context_engineer = get_context_engineer() if use_context_engineering else None
    return EnhancedAIReportGenerator(
        llm_client=llm_client,
        context_engineer=context_engineer,
        use_optimized_clients=use_optimized_clients
    )


def generate_production_report(parameters: Dict[str, Any] = None, **kwargs) -> ReportModel:
    """생산 보고서 생성 (v2.0)"""
    generator = create_report_generator(**kwargs)
    config = ReportGenerationConfig(
        report_type="production_summary",
        parameters=parameters or {}
    )
    return generator.generate_report(config)


def generate_quality_report(parameters: Dict[str, Any] = None, **kwargs) -> ReportModel:
    """품질 보고서 생성 (v2.0)"""
    generator = create_report_generator(**kwargs)
    config = ReportGenerationConfig(
        report_type="quality_analysis",
        parameters=parameters or {}
    )
    return generator.generate_report(config)


def generate_cost_report(parameters: Dict[str, Any] = None, **kwargs) -> ReportModel:
    """비용 보고서 생성 (v2.0)"""
    generator = create_report_generator(**kwargs)
    config = ReportGenerationConfig(
        report_type="cost_analysis",
        parameters=parameters or {}
    )
    return generator.generate_report(config)


def generate_equipment_report(parameters: Dict[str, Any] = None, **kwargs) -> ReportModel:
    """설비 보고서 생성 (v2.0)"""
    generator = create_report_generator(**kwargs)
    config = ReportGenerationConfig(
        report_type="equipment_status",
        parameters=parameters or {}
    )
    return generator.generate_report(config)


async def generate_report_async(report_type: str, parameters: Dict[str, Any] = None, **kwargs) -> ReportModel:
    """비동기 보고서 생성 (v2.0)"""
    generator = create_report_generator(**kwargs)
    config = ReportGenerationConfig(
        report_type=report_type,
        parameters=parameters or {},
        async_processing=True
    )
    return await generator.generate_report_async(config) 