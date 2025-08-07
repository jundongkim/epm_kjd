"""
DX-AI Manufacturing Copilot - AI 보고서 생성 시스템
LangGraph를 활용한 AI 기반 보고서 생성 워크플로우
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal, TypedDict
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from .llm_client import OllamaClient
from .data_models import ReportModel, LotModel, EquipmentModel, MaterialModel
from .config import settings

logger = logging.getLogger(__name__)


class ReportGenerationState(TypedDict):
    """보고서 생성 상태 정의"""
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
    
    # 보고서 내용
    report_content: str
    
    # 검토 결과
    review_result: Dict[str, Any]
    quality_score: float
    
    # 최종 보고서
    final_report: Optional[ReportModel]
    
    # 메타데이터
    messages: List[str]
    iteration_count: int
    max_iterations: int
    
    # 생성 설정
    generated_by: str
    temperature: float
    max_tokens: int


@dataclass
class ReportGenerationConfig:
    """보고서 생성 설정"""
    report_type: str
    data_sources: List[str] = None
    parameters: Dict[str, Any] = None
    max_iterations: int = 3
    quality_threshold: float = 0.7
    temperature: float = 0.7
    max_tokens: int = 2048
    generated_by: str = "AI_Report_Generator"


class AIReportGenerator:
    """LangGraph 기반 AI 보고서 생성기"""
    
    def __init__(self, llm_client: Optional[OllamaClient] = None):
        """
        AI 보고서 생성기 초기화
        
        Args:
            llm_client: Ollama LLM 클라이언트 (선택사항)
        """
        self.llm_client = llm_client or OllamaClient()
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """보고서 생성 그래프 구축"""
        # 상태 그래프 생성
        workflow = StateGraph(ReportGenerationState)
        
        # 노드 추가
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("analyze_data", self._analyze_data_node)
        workflow.add_node("generate_context", self._generate_context_node)
        workflow.add_node("generate_report", self._generate_report_node)
        workflow.add_node("review_report", self._review_report_node)
        workflow.add_node("finalize_report", self._finalize_report_node)
        
        # 에지 정의
        workflow.add_edge(START, "collect_data")
        workflow.add_edge("collect_data", "analyze_data")
        workflow.add_edge("analyze_data", "generate_context")
        workflow.add_edge("generate_context", "generate_report")
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
        """데이터 수집 노드"""
        logger.info("데이터 수집 시작")
        
        collected_data = {}
        report_type = state["report_type"]
        data_sources = state.get("data_sources", [])
        
        try:
            # 보고서 타입에 따른 데이터 수집
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
                
            messages = state.get("messages", [])
            messages.append(f"데이터 수집 완료: {len(collected_data)} 개 항목")
            
            return {
                "collected_data": collected_data,
                "messages": messages
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
        """데이터 분석 노드"""
        logger.info("데이터 분석 시작")
        
        collected_data = state.get("collected_data", {})
        report_type = state["report_type"]
        
        try:
            # 데이터 분석 프롬프트 생성
            analysis_prompt = self._create_analysis_prompt(report_type, collected_data)
            
            # LLM을 사용한 데이터 분석
            analysis_result = self.llm_client.generate(
                analysis_prompt,
                temperature=state.get("temperature", 0.7),
                max_tokens=state.get("max_tokens", 1024)
            )
            
            # 분석 결과 구조화
            analysis_results = {
                "raw_analysis": analysis_result,
                "key_insights": self._extract_key_insights(analysis_result),
                "trends": self._identify_trends(collected_data),
                "anomalies": self._detect_anomalies(collected_data)
            }
            
            messages = state.get("messages", [])
            messages.append("데이터 분석 완료")
            
            return {
                "analysis_results": analysis_results,
                "messages": messages
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
        """컨텍스트 생성 노드"""
        logger.info("컨텍스트 생성 시작")
        
        collected_data = state.get("collected_data", {})
        analysis_results = state.get("analysis_results", {})
        report_type = state["report_type"]
        
        try:
            # 컨텍스트 생성 프롬프트
            context_prompt = self._create_context_prompt(report_type, collected_data, analysis_results)
            
            # LLM을 사용한 컨텍스트 생성
            context = self.llm_client.generate(
                context_prompt,
                temperature=state.get("temperature", 0.7),
                max_tokens=state.get("max_tokens", 1024)
            )
            
            messages = state.get("messages", [])
            messages.append("컨텍스트 생성 완료")
            
            return {
                "context": context,
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"컨텍스트 생성 실패: {e}")
            messages = state.get("messages", [])
            messages.append(f"컨텍스트 생성 오류: {str(e)}")
            return {
                "context": "",
                "messages": messages
            }
    
    def _generate_report_node(self, state: ReportGenerationState) -> Dict[str, Any]:
        """보고서 생성 노드"""
        logger.info("보고서 생성 시작")
        
        context = state.get("context", "")
        report_type = state["report_type"]
        parameters = state.get("parameters", {})
        iteration_count = state.get("iteration_count", 0)
        
        try:
            # 보고서 생성 프롬프트
            report_prompt = self._create_report_prompt(report_type, context, parameters)
            
            # 재생성인 경우 이전 검토 결과를 반영
            if iteration_count > 0:
                review_result = state.get("review_result", {})
                suggestions = review_result.get("suggestions", [])
                if suggestions:
                    improvement_note = f"\n\n다음 개선사항을 반영하여 보고서를 수정하세요:\n" + "\n".join(f"- {s}" for s in suggestions)
                    report_prompt += improvement_note
            
            # LLM을 사용한 보고서 생성
            report_content = self.llm_client.generate(
                report_prompt,
                temperature=state.get("temperature", 0.7),
                max_tokens=state.get("max_tokens", 2048)
            )
            
            messages = state.get("messages", [])
            messages.append(f"보고서 생성 완료 (반복 {iteration_count + 1}회)")
            
            return {
                "report_content": report_content,
                "messages": messages,
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
        """보고서 검토 노드"""
        logger.info("보고서 검토 시작")
        
        report_content = state.get("report_content", "")
        report_type = state["report_type"]
        
        try:
            # 보고서 검토 프롬프트
            review_prompt = self._create_review_prompt(report_type, report_content)
            
            # LLM을 사용한 보고서 검토
            review_result_text = self.llm_client.generate(
                review_prompt,
                temperature=0.3,  # 검토 시에는 낮은 온도 사용
                max_tokens=1024
            )
            
            # 품질 점수 계산 (간단한 휴리스틱)
            quality_score = self._calculate_quality_score(report_content, review_result_text)
            
            review_result = {
                "review_text": review_result_text,
                "suggestions": self._extract_suggestions(review_result_text),
                "strengths": self._extract_strengths(review_result_text),
                "weaknesses": self._extract_weaknesses(review_result_text)
            }
            
            messages = state.get("messages", [])
            messages.append(f"보고서 검토 완료 (품질 점수: {quality_score:.2f})")
            
            return {
                "review_result": review_result,
                "quality_score": quality_score,
                "messages": messages
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
        """보고서 최종화 노드"""
        logger.info("보고서 최종화 시작")
        
        try:
            # 최종 보고서 모델 생성
            final_report = ReportModel(
                title=self._generate_report_title(state["report_type"], state.get("parameters", {})),
                report_type=state["report_type"],
                content=state.get("report_content", ""),
                generated_by=state.get("generated_by", "AI_Report_Generator"),
                data_sources=state.get("data_sources", []),
                parameters=state.get("parameters", {})
            )
            
            messages = state.get("messages", [])
            messages.append("보고서 최종화 완료")
            
            return {
                "final_report": final_report,
                "messages": messages
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
        """보고서 재생성 여부 결정"""
        quality_score = state.get("quality_score", 0.0)
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 3)
        
        # 반복 횟수 업데이트
        updated_state = state.copy()
        updated_state["iteration_count"] = iteration_count + 1
        
        # 품질 점수가 임계값 이하이고 최대 반복 횟수에 도달하지 않았으면 재생성
        if quality_score < 0.7 and iteration_count < max_iterations:
            return "regenerate"
        else:
            return "finalize"
    
    def _collect_production_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """생산 데이터 수집"""
        # 실제 구현에서는 데이터베이스나 API에서 데이터 수집
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
    
    def _create_analysis_prompt(self, report_type: str, data: Dict[str, Any]) -> str:
        """데이터 분석 프롬프트 생성"""
        prompt = f"""
당신은 {report_type} 보고서를 위한 데이터 분석 전문가입니다.
다음 데이터를 분석하여 주요 인사이트, 트렌드, 이상치를 식별하세요.

데이터:
{data}

분석 결과를 다음 형식으로 제공해주세요:
1. 주요 인사이트
2. 관찰된 트렌드
3. 발견된 이상치
4. 개선 권장사항

분석:
"""
        return prompt
    
    def _create_context_prompt(self, report_type: str, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """컨텍스트 생성 프롬프트"""
        prompt = f"""
{report_type} 보고서를 위한 컨텍스트를 생성하세요.
수집된 데이터와 분석 결과를 바탕으로 보고서의 배경과 맥락을 설정하세요.

데이터: {data}
분석 결과: {analysis}

컨텍스트는 다음을 포함해야 합니다:
- 보고서의 목적과 범위
- 데이터의 출처와 기간
- 분석 방법론
- 주요 발견사항 요약

컨텍스트:
"""
        return prompt
    
    def _create_report_prompt(self, report_type: str, context: str, parameters: Dict[str, Any]) -> str:
        """보고서 생성 프롬프트"""
        prompt = f"""
다음 컨텍스트를 바탕으로 {report_type} 보고서를 작성하세요.
보고서는 전문적이고 체계적이며 실행 가능한 내용을 포함해야 합니다.

컨텍스트:
{context}

보고서 요구사항:
- 명확한 제목과 요약
- 주요 발견사항
- 데이터 분석 결과
- 결론 및 권장사항
- 적절한 구조와 형식

보고서:
"""
        return prompt
    
    def _create_review_prompt(self, report_type: str, content: str) -> str:
        """보고서 검토 프롬프트"""
        prompt = f"""
다음 {report_type} 보고서를 검토하고 품질을 평가하세요.

보고서 내용:
{content}

검토 기준:
1. 내용의 정확성과 완전성
2. 구조와 논리적 흐름
3. 데이터 분석의 적절성
4. 결론과 권장사항의 타당성
5. 전반적인 가독성

검토 결과:
- 강점: 
- 약점:
- 개선사항:
- 전체 평가:
"""
        return prompt
    
    def _extract_key_insights(self, analysis: str) -> List[str]:
        """주요 인사이트 추출"""
        # 실제 구현에서는 더 정교한 파싱 로직 사용
        return ["주요 인사이트 1", "주요 인사이트 2", "주요 인사이트 3"]
    
    def _identify_trends(self, data: Dict[str, Any]) -> List[str]:
        """트렌드 식별"""
        return ["트렌드 1", "트렌드 2"]
    
    def _detect_anomalies(self, data: Dict[str, Any]) -> List[str]:
        """이상치 탐지"""
        return ["이상치 1", "이상치 2"]
    
    def _calculate_quality_score(self, content: str, review: str) -> float:
        """품질 점수 계산"""
        # 간단한 휴리스틱으로 품질 점수 계산
        # 실제 구현에서는 더 정교한 평가 로직 사용
        content_length = len(content)
        if content_length < 500:
            return 0.3
        elif content_length < 1000:
            return 0.6
        else:
            return 0.8
    
    def _extract_suggestions(self, review: str) -> List[str]:
        """개선 제안 추출"""
        return ["제안 1", "제안 2"]
    
    def _extract_strengths(self, review: str) -> List[str]:
        """강점 추출"""
        return ["강점 1", "강점 2"]
    
    def _extract_weaknesses(self, review: str) -> List[str]:
        """약점 추출"""
        return ["약점 1", "약점 2"]
    
    def _generate_report_title(self, report_type: str, parameters: Dict[str, Any]) -> str:
        """보고서 제목 생성"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        type_map = {
            "production_summary": "생산 현황 보고서",
            "quality_analysis": "품질 분석 보고서",
            "cost_analysis": "비용 분석 보고서",
            "equipment_status": "설비 현황 보고서"
        }
        title = type_map.get(report_type, "종합 보고서")
        return f"{title} - {current_date}"
    
    async def generate_report_async(self, config: ReportGenerationConfig) -> ReportModel:
        """비동기 보고서 생성"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.generate_report, config
        )
    
    def generate_report(self, config: ReportGenerationConfig) -> ReportModel:
        """보고서 생성 실행"""
        logger.info(f"보고서 생성 시작: {config.report_type}")
        
        # 초기 상태 설정
        initial_state = ReportGenerationState(
            report_type=config.report_type,
            parameters=config.parameters or {},
            data_sources=config.data_sources or [],
            collected_data={},
            analysis_results={},
            context="",
            report_content="",
            review_result={},
            quality_score=0.0,
            final_report=None,
            messages=[],
            iteration_count=0,
            max_iterations=config.max_iterations,
            generated_by=config.generated_by,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        try:
            # 그래프 실행
            result = self.graph.invoke(initial_state)
            
            # 최종 보고서 반환
            final_report = result.get("final_report")
            if final_report:
                logger.info(f"보고서 생성 완료: {final_report.title}")
                return final_report
            else:
                logger.error("최종 보고서 생성 실패")
                raise Exception("최종 보고서 생성 실패")
                
        except Exception as e:
            logger.error(f"보고서 생성 오류: {e}")
            raise
    
    def get_graph_visualization(self) -> str:
        """그래프 시각화 정보 반환"""
        try:
            # Mermaid 다이어그램 생성 (실제 구현에서는 이미지 생성)
            return """
graph TD
    A[START] --> B[데이터 수집]
    B --> C[데이터 분석]
    C --> D[컨텍스트 생성]
    D --> E[보고서 생성]
    E --> F[보고서 검토]
    F --> G{품질 평가}
    G -->|품질 미달| E
    G -->|품질 통과| H[보고서 최종화]
    H --> I[END]
"""
        except Exception as e:
            logger.error(f"그래프 시각화 생성 실패: {e}")
            return "그래프 시각화를 생성할 수 없습니다."


# 편의 함수들
def create_report_generator(llm_client: Optional[OllamaClient] = None) -> AIReportGenerator:
    """보고서 생성기 생성"""
    return AIReportGenerator(llm_client)


def generate_production_report(parameters: Dict[str, Any] = None) -> ReportModel:
    """생산 보고서 생성"""
    generator = create_report_generator()
    config = ReportGenerationConfig(
        report_type="production_summary",
        parameters=parameters or {}
    )
    return generator.generate_report(config)


def generate_quality_report(parameters: Dict[str, Any] = None) -> ReportModel:
    """품질 보고서 생성"""
    generator = create_report_generator()
    config = ReportGenerationConfig(
        report_type="quality_analysis",
        parameters=parameters or {}
    )
    return generator.generate_report(config)


def generate_cost_report(parameters: Dict[str, Any] = None) -> ReportModel:
    """비용 보고서 생성"""
    generator = create_report_generator()
    config = ReportGenerationConfig(
        report_type="cost_analysis",
        parameters=parameters or {}
    )
    return generator.generate_report(config)


def generate_equipment_report(parameters: Dict[str, Any] = None) -> ReportModel:
    """설비 보고서 생성"""
    generator = create_report_generator()
    config = ReportGenerationConfig(
        report_type="equipment_status",
        parameters=parameters or {}
    )
    return generator.generate_report(config) 