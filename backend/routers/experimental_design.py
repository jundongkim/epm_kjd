"""
DX-AI Manufacturing Copilot - 실험 설계 API 라우터

실험 설계 관련 API 엔드포인트들을 정의합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import io
from datetime import datetime

from src.copilot.experimental_design_engine import (
    DOEDesignEngine,
    BayesianOptimizationEngine,
    ReportGenerationEngine,
    ExperimentType,
    OptimizationGoal
)
from src.utils.experimental_design_utils import (
    analyze_experiment_efficiency,
    get_correlation_analysis,
    analyze_optimization_results,
    create_experiment_summary,
    validate_experiment_setup
)

router = APIRouter(prefix="/experimental-design", tags=["experimental-design"])

# Request/Response Models
class ExperimentPlanRequest(BaseModel):
    experiment_type: str
    factors: List[str]
    num_runs: int
    replications: int = 1
    target_purity: float = 97.5
    target_yield: float = 92.0
    optimization_goal: str = "순도 최대화"

class ExperimentPlanResponse(BaseModel):
    experiment_plan: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    validation: Dict[str, Any]

class OptimizationRequest(BaseModel):
    objectives: List[str]
    constraints: Dict[str, Dict[str, float]]
    optimizer: str = "Gaussian Process"
    max_iterations: int = 50
    acquisition_function: str = "Expected Improvement"

class OptimizationResponse(BaseModel):
    optimal_parameters: Dict[str, float]
    predicted_performance: Dict[str, float]
    confidence_levels: Dict[str, float]
    improvement_rate: float
    convergence_info: Dict[str, Any]
    analysis: Dict[str, Any]

class ReportRequest(BaseModel):
    report_type: str
    include_sections: List[str]
    report_length: str
    experiment_data: Optional[Dict[str, Any]] = None
    optimization_data: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    content: str
    metadata: Dict[str, Any]


@router.post("/experiment-plan", response_model=ExperimentPlanResponse)
async def generate_experiment_plan(request: ExperimentPlanRequest):
    """실험 계획 생성 API"""
    try:
        # 파라미터 검증
        validation = validate_experiment_setup(request.dict())
        
        if not validation['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"실험 설정 오류: {', '.join(validation['errors'])}"
            )
        
        # DoE 엔진 초기화
        doe_engine = DOEDesignEngine()
        
        # 실험 계획 생성
        experiment_plan, metadata = doe_engine.generate_experiment_plan(
            experiment_type=request.experiment_type,
            factors=request.factors,
            num_runs=request.num_runs,
            replications=request.replications,
            target_purity=request.target_purity,
            target_yield=request.target_yield
        )
        
        # 분석 수행
        analysis = analyze_experiment_efficiency(experiment_plan, request.factors)
        
        # 상관관계 분석
        correlation_analysis = get_correlation_analysis(experiment_plan, request.factors)
        analysis.update(correlation_analysis)
        
        return ExperimentPlanResponse(
            experiment_plan=experiment_plan.to_dict(orient='records'),
            metadata=metadata,
            analysis=analysis,
            validation=validation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실험 계획 생성 중 오류: {str(e)}")


@router.post("/optimization", response_model=OptimizationResponse)
async def run_optimization(request: OptimizationRequest):
    """베이지안 최적화 실행 API"""
    try:
        # 베이지안 최적화 엔진 초기화
        optimization_engine = BayesianOptimizationEngine()
        
        # 최적화 실행
        result = optimization_engine.run_optimization(
            objectives=request.objectives,
            constraints=request.constraints,
            optimizer=request.optimizer,
            max_iterations=request.max_iterations,
            acquisition_function=request.acquisition_function
        )
        
        # 최적화 결과 분석
        analysis = analyze_optimization_results(result.__dict__)
        
        return OptimizationResponse(
            optimal_parameters=result.optimal_parameters,
            predicted_performance=result.predicted_performance,
            confidence_levels=result.confidence_levels,
            improvement_rate=result.improvement_rate,
            convergence_info=result.convergence_info,
            analysis=analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최적화 실행 중 오류: {str(e)}")


@router.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """AI 보고서 생성 API"""
    try:
        # 보고서 생성 엔진 초기화
        report_engine = ReportGenerationEngine()
        
        # 보고서 생성
        report = report_engine.generate_report(
            report_type=request.report_type,
            include_sections=request.include_sections,
            report_length=request.report_length,
            experiment_data=request.experiment_data or {},
            optimization_data=request.optimization_data
        )
        
        # 기본 메타데이터 가져오기
        content = report.get('content', '')
        word_count = len(content.split()) if content else 0
        
        # 기존 메타데이터와 계산된 메타데이터 병합
        existing_metadata = report.get('metadata', {})
        
        # API 응답용 메타데이터 생성
        metadata = {
            'word_count': word_count,
            'estimated_read_time': max(1, word_count // 200),  # 분 단위, 최소 1분
            'estimated_pages': max(1, word_count // 250),      # 페이지 단위, 최소 1페이지
            'report_type': request.report_type,
            'sections_included': request.include_sections,
            'report_length': request.report_length,
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_experiment_data': bool(request.experiment_data),
            'has_optimization_data': bool(request.optimization_data),
            # 기존 AI 메타데이터 포함
            'ai_metadata': existing_metadata
        }
        
        return ReportResponse(
            content=content,
            metadata=metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류: {str(e)}")


@router.get("/parameters")
async def get_available_parameters():
    """사용 가능한 실험 파라미터 정보 조회"""
    try:
        engine = DOEDesignEngine()
        parameters = engine.get_all_parameters()
        
        return {
            "parameters": {
                name: {
                    "name": param.name,
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "levels": param.levels,
                    "unit": param.unit
                }
                for name, param in parameters.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파라미터 조회 중 오류: {str(e)}")


@router.get("/experiment-types")
async def get_experiment_types():
    """실험 유형 목록 조회"""
    return {
        "experiment_types": [
            {
                "id": exp_type.value,
                "name": exp_type.value,
                "description": _get_experiment_type_description(exp_type)
            }
            for exp_type in ExperimentType
        ]
    }


@router.get("/optimization-goals")
async def get_optimization_goals():
    """최적화 목표 목록 조회"""
    return {
        "optimization_goals": [
            {
                "id": goal.value,
                "name": goal.value,
                "description": _get_optimization_goal_description(goal)
            }
            for goal in OptimizationGoal
        ]
    }


@router.post("/validate-setup")
async def validate_experiment_setup_endpoint(request: ExperimentPlanRequest):
    """실험 설정 검증 API"""
    try:
        validation = validate_experiment_setup(request.dict())
        return validation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검증 중 오류: {str(e)}")


@router.get("/report/download/{report_type}")
async def download_report(report_type: str, content: str):
    """보고서 다운로드 API"""
    try:
        # 파일 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"실험설계_보고서_{report_type}_{timestamp}.md"
        
        # 스트리밍 응답 생성
        def generate():
            yield content.encode('utf-8')
        
        return StreamingResponse(
            generate(),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 중 오류: {str(e)}")


def _get_experiment_type_description(exp_type: ExperimentType) -> str:
    """실험 유형 설명 반환"""
    descriptions = {
        ExperimentType.FULL_FACTORIAL: "모든 인자 조합을 다 실험하는 완전요인설계",
        ExperimentType.FRACTIONAL_FACTORIAL: "실험 횟수를 줄인 효율적인 부분요인설계",
        ExperimentType.CENTRAL_COMPOSITE: "2차 곡선 모델링이 가능한 중심합성설계",
        ExperimentType.BOX_BEHNKEN: "안전한 3수준 Box-Behnken 설계"
    }
    return descriptions.get(exp_type, "")


def _get_optimization_goal_description(goal: OptimizationGoal) -> str:
    """최적화 목표 설명 반환"""
    descriptions = {
        OptimizationGoal.MAXIMIZE_PURITY: "제품 순도를 최대화",
        OptimizationGoal.MAXIMIZE_YIELD: "제품 수율을 최대화",
        OptimizationGoal.MINIMIZE_COST: "생산 비용을 최소화",
        OptimizationGoal.MINIMIZE_TIME: "생산 시간을 최소화"
    }
    return descriptions.get(goal, "") 