"""
데이터 분석 워크플로우 API 라우터
5단계 데이터 분석 프로세스를 지원하는 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime
import asyncio
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# ============================
# 데이터 모델 정의
# ============================

class AnalysisConfig(BaseModel):
    """분석 설정 모델"""
    selectedData: List[str] = Field(..., description="선택된 데이터 파일 경로 목록")
    engineConfig: Dict[str, Any] = Field(..., description="엔진 설정")
    stepConfig: Dict[str, Any] = Field(default={}, description="단계별 설정")

class ObjectiveDefinition(BaseModel):
    """목표 정의 모델"""
    objectives: List[str] = Field(..., description="분석 목표 목록")
    hypotheses: str = Field(..., description="검증할 가설")
    analysisTheme: str = Field(..., description="분석 테마")

class PreprocessingConfig(BaseModel):
    """전처리 설정 모델"""
    enabled: bool = Field(True, description="전처리 활성화 여부")
    cleaningRules: List[str] = Field(default=[], description="정제 규칙")
    featureEngineering: List[str] = Field(default=[], description="피처 엔지니어링 방법")
    metadataTagging: bool = Field(True, description="메타데이터 태깅 여부")

class EDAConfig(BaseModel):
    """EDA 설정 모델"""
    enabled: bool = Field(True, description="EDA 활성화 여부")
    autoReports: bool = Field(True, description="자동 리포트 생성 여부")
    pandasProfiling: bool = Field(True, description="Pandas Profiling 사용 여부")
    sweetviz: bool = Field(True, description="Sweetviz 사용 여부")
    customCharts: List[str] = Field(default=[], description="커스텀 차트 목록")

class HypothesisConfig(BaseModel):
    """가설 검정 설정 모델"""
    enabled: bool = Field(True, description="가설 검정 활성화 여부")
    statisticalTests: List[str] = Field(default=[], description="통계적 검정 방법")
    alertRules: List[str] = Field(default=[], description="알림 규칙")
    notifications: bool = Field(True, description="알림 시스템 사용 여부")

class EngineConfigModel(BaseModel):
    """엔진 설정 전체 모델"""
    preprocessing: PreprocessingConfig
    eda: EDAConfig
    hypothesis: HypothesisConfig

class DataFile(BaseModel):
    """데이터 파일 모델"""
    filepath: str = Field(..., description="파일 경로")
    dataType: str = Field(..., description="데이터 타입")
    filename: str = Field(..., description="파일명")
    createTime: datetime = Field(..., description="생성 시간")
    fileSizeKb: float = Field(..., description="파일 크기 (KB)")
    rowCount: Optional[int] = Field(None, description="행 수")
    colCount: Optional[int] = Field(None, description="열 수")
    previewData: Optional[List[Dict[str, Any]]] = Field(None, description="미리보기 데이터")

class AnalysisResult(BaseModel):
    """분석 결과 모델"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="결과 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="결과 데이터")
    artifacts: Optional[Dict[str, List[str]]] = Field(None, description="생성된 파일들")
    duration: Optional[float] = Field(None, description="실행 시간 (초)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")

# ============================
# 헬퍼 함수
# ============================

def get_data_directory():
    """데이터 디렉토리 경로 반환"""
    return Path(__file__).parent.parent / "data"

def load_data_file(filepath: str) -> pd.DataFrame:
    """데이터 파일 로드"""
    try:
        if filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        elif filepath.endswith('.json'):
            return pd.read_json(filepath)
        elif filepath.endswith('.xlsx'):
            return pd.read_excel(filepath)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {filepath}")
    except Exception as e:
        logger.error(f"데이터 파일 로드 실패: {filepath}, 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=f"데이터 파일 로드 실패: {str(e)}")

def save_analysis_result(step: str, result: Dict[str, Any]) -> str:
    """분석 결과 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{step}_{timestamp}.json"
    filepath = get_data_directory() / "analysis_results" / filename
    
    # 디렉토리 생성
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    return str(filepath)

# ============================
# API 엔드포인트
# ============================

@router.get("/data/available")
async def get_available_data():
    """사용 가능한 데이터 파일 목록 조회"""
    try:
        data_dir = get_data_directory()
        files = []
        
        # Mock 데이터 반환 (실제 구현에서는 실제 파일 시스템 스캔)
        mock_files = [
            {
                "filepath": "/data/production/manufacturing_data.csv",
                "dataType": "production",
                "filename": "manufacturing_data.csv",
                "createTime": datetime.now(),
                "fileSizeKb": 125.4,
                "rowCount": 1000,
                "colCount": 15
            },
            {
                "filepath": "/data/sensors/sensor_readings.csv",
                "dataType": "sensor",
                "filename": "sensor_readings.csv",
                "createTime": datetime.now(),
                "fileSizeKb": 87.2,
                "rowCount": 5000,
                "colCount": 8
            },
            {
                "filepath": "/data/quality/quality_metrics.csv",
                "dataType": "quality",
                "filename": "quality_metrics.csv",
                "createTime": datetime.now(),
                "fileSizeKb": 43.8,
                "rowCount": 500,
                "colCount": 12
            }
        ]
        
        return {"files": mock_files}
        
    except Exception as e:
        logger.error(f"데이터 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터 목록 조회 실패: {str(e)}")

@router.post("/workflow/define_objectives_&_hypotheses")
async def run_objectives_definition(config: AnalysisConfig):
    """1단계: 분석 목표 및 가설 정의"""
    try:
        logger.info("분석 목표 및 가설 정의 단계 시작")
        
        # 분석 목표와 가설 처리
        objectives = config.stepConfig.get('objectives', [])
        hypotheses = config.stepConfig.get('hypotheses', '')
        analysis_theme = config.stepConfig.get('analysisTheme', 'manufacturing_quality')
        
        # 분석 결과 생성
        result = {
            "objectives": objectives,
            "hypotheses": hypotheses,
            "analysis_theme": analysis_theme,
            "defined_metrics": [
                "품질 지표 (순도, 수율)",
                "공정 파라미터 (온도, 압력, 유량)",
                "설비 성능 지표",
                "비용 효율성 지표"
            ],
            "analysis_scope": {
                "time_range": "최근 3개월",
                "data_sources": config.selectedData,
                "target_variables": ["purity", "yield", "temperature", "pressure"]
            }
        }
        
        # 결과 저장
        result_file = save_analysis_result("objectives_definition", result)
        
        return AnalysisResult(
            success=True,
            message="분석 목표 및 가설이 성공적으로 정의되었습니다.",
            data=result,
            artifacts={"reports": [result_file]},
            metadata={"step": 1, "analysis_theme": analysis_theme}
        )
        
    except Exception as e:
        logger.error(f"목표 정의 단계 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"목표 정의 단계 실행 실패: {str(e)}")

@router.post("/workflow/data_acquisition_&_ingestion")
async def run_data_acquisition(config: AnalysisConfig):
    """2단계: 데이터 수집 및 수집"""
    try:
        logger.info("데이터 수집 및 수집 단계 시작")
        
        acquired_data = []
        
        for filepath in config.selectedData:
            # Mock 데이터 정보 생성
            data_info = {
                "filepath": filepath,
                "status": "acquired",
                "row_count": np.random.randint(100, 5000),
                "column_count": np.random.randint(5, 20),
                "data_quality": {
                    "missing_values": np.random.randint(0, 10),
                    "duplicates": np.random.randint(0, 5),
                    "outliers": np.random.randint(0, 20)
                },
                "data_types": {
                    "numeric": np.random.randint(3, 15),
                    "categorical": np.random.randint(1, 5),
                    "datetime": np.random.randint(1, 3)
                }
            }
            acquired_data.append(data_info)
        
        result = {
            "acquired_datasets": acquired_data,
            "total_records": sum(data["row_count"] for data in acquired_data),
            "data_sources": {
                "production_data": len([d for d in acquired_data if "production" in d["filepath"]]),
                "sensor_data": len([d for d in acquired_data if "sensor" in d["filepath"]]),
                "quality_data": len([d for d in acquired_data if "quality" in d["filepath"]])
            },
            "ingestion_summary": {
                "successful": len(acquired_data),
                "failed": 0,
                "total_size_mb": round(sum(data["row_count"] * data["column_count"] * 0.001 for data in acquired_data), 2)
            }
        }
        
        # 결과 저장
        result_file = save_analysis_result("data_acquisition", result)
        
        return AnalysisResult(
            success=True,
            message=f"{len(acquired_data)}개 데이터 소스가 성공적으로 수집되었습니다.",
            data=result,
            artifacts={"reports": [result_file]},
            metadata={"step": 2, "datasets_count": len(acquired_data)}
        )
        
    except Exception as e:
        logger.error(f"데이터 수집 단계 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터 수집 단계 실행 실패: {str(e)}")

@router.post("/workflow/data_cleaning_&_feature_engineering")
async def run_data_cleaning(config: AnalysisConfig):
    """3단계: 데이터 정제 및 피처 엔지니어링"""
    try:
        logger.info("데이터 정제 및 피처 엔지니어링 단계 시작")
        
        preprocessing_config = config.engineConfig.get('preprocessing', {})
        
        # Mock 정제 결과
        cleaning_results = {
            "before_cleaning": {
                "total_records": np.random.randint(1000, 10000),
                "missing_values": np.random.randint(50, 200),
                "duplicates": np.random.randint(10, 50),
                "outliers": np.random.randint(20, 100)
            },
            "cleaning_operations": {
                "removed_duplicates": np.random.randint(10, 50),
                "filled_missing_values": np.random.randint(50, 200),
                "treated_outliers": np.random.randint(20, 100),
                "standardized_formats": np.random.randint(5, 20)
            },
            "after_cleaning": {
                "total_records": np.random.randint(900, 9500),
                "data_quality_score": round(np.random.uniform(0.85, 0.98), 3),
                "completeness": round(np.random.uniform(0.95, 1.0), 3)
            }
        }
        
        # Mock 피처 엔지니어링 결과
        feature_engineering_results = {
            "original_features": np.random.randint(10, 20),
            "engineered_features": {
                "interaction_features": np.random.randint(5, 15),
                "polynomial_features": np.random.randint(3, 10),
                "temporal_features": np.random.randint(2, 8),
                "aggregate_features": np.random.randint(4, 12)
            },
            "final_feature_count": np.random.randint(25, 50),
            "feature_importance": {
                "temperature": 0.23,
                "pressure": 0.18,
                "flow_rate": 0.15,
                "catalyst_concentration": 0.12,
                "residence_time": 0.10
            }
        }
        
        result = {
            "cleaning_results": cleaning_results,
            "feature_engineering_results": feature_engineering_results,
            "preprocessing_config": preprocessing_config,
            "metadata_tags": {
                "data_version": "v1.0_cleaned",
                "processing_date": datetime.now().isoformat(),
                "quality_flags": ["cleaned", "normalized", "feature_enhanced"]
            }
        }
        
        # 결과 저장
        result_file = save_analysis_result("data_cleaning", result)
        
        return AnalysisResult(
            success=True,
            message="데이터 정제 및 피처 엔지니어링이 성공적으로 완료되었습니다.",
            data=result,
            artifacts={"reports": [result_file], "files": ["cleaned_data.csv", "feature_map.json"]},
            metadata={"step": 3, "final_features": result["feature_engineering_results"]["final_feature_count"]}
        )
        
    except Exception as e:
        logger.error(f"데이터 정제 단계 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터 정제 단계 실행 실패: {str(e)}")

@router.post("/workflow/exploratory_data_analysis_(eda)")
async def run_eda(config: AnalysisConfig):
    """4단계: 탐색적 데이터 분석 (EDA)"""
    try:
        logger.info("EDA 단계 시작")
        
        eda_config = config.engineConfig.get('eda', {})
        
        # Mock EDA 결과
        eda_results = {
            "summary_statistics": {
                "temperature": {"mean": 285.2, "std": 12.4, "min": 260.0, "max": 310.0},
                "pressure": {"mean": 15.3, "std": 2.1, "min": 12.0, "max": 18.5},
                "purity": {"mean": 95.8, "std": 2.3, "min": 90.1, "max": 99.2},
                "yield": {"mean": 88.5, "std": 4.2, "min": 78.3, "max": 95.1}
            },
            "correlation_analysis": {
                "strong_correlations": [
                    {"variables": ["temperature", "purity"], "correlation": 0.78},
                    {"variables": ["pressure", "yield"], "correlation": 0.65},
                    {"variables": ["temperature", "pressure"], "correlation": -0.43}
                ]
            },
            "distribution_analysis": {
                "normal_distributions": ["temperature", "pressure"],
                "skewed_distributions": ["purity", "yield"],
                "outlier_detection": {
                    "temperature": 12,
                    "pressure": 8,
                    "purity": 15,
                    "yield": 10
                }
            },
            "temporal_patterns": {
                "seasonal_trends": True,
                "cyclical_patterns": True,
                "trend_direction": "slightly_increasing"
            }
        }
        
        # 생성된 리포트 및 차트
        artifacts = {
            "reports": ["pandas_profiling_report.html", "sweetviz_report.html"],
            "charts": [
                "correlation_matrix.png",
                "distribution_plots.png",
                "box_plots.png",
                "time_series_analysis.png"
            ]
        }
        
        result = {
            "eda_results": eda_results,
            "insights": [
                "온도와 순도 간에 강한 양의 상관관계 발견",
                "압력이 수율에 중간 정도의 영향을 미침",
                "계절적 패턴이 공정 성능에 영향을 줄 가능성",
                "일부 변수에서 이상값 패턴 발견"
            ],
            "recommendations": [
                "온도 제어 최적화를 통한 순도 향상 검토",
                "압력 설정값 조정을 통한 수율 개선 가능성 검토",
                "이상값에 대한 근본 원인 분석 필요"
            ]
        }
        
        # 결과 저장
        result_file = save_analysis_result("eda", result)
        
        return AnalysisResult(
            success=True,
            message="EDA가 성공적으로 완료되었습니다. 주요 인사이트가 발견되었습니다.",
            data=result,
            artifacts=artifacts,
            metadata={"step": 4, "insights_count": len(result["insights"])}
        )
        
    except Exception as e:
        logger.error(f"EDA 단계 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"EDA 단계 실행 실패: {str(e)}")

@router.post("/workflow/hypothesis_testing_&_alerting")
async def run_hypothesis_testing(config: AnalysisConfig):
    """5단계: 가설 검정 및 알림"""
    try:
        logger.info("가설 검정 및 알림 단계 시작")
        
        hypothesis_config = config.engineConfig.get('hypothesis', {})
        
        # Mock 가설 검정 결과
        hypothesis_tests = [
            {
                "hypothesis": "온도와 순도 간에 유의미한 상관관계가 있다",
                "test_type": "correlation_test",
                "p_value": 0.001,
                "significance_level": 0.05,
                "result": "rejected_null",
                "conclusion": "온도와 순도 간 유의미한 양의 상관관계 확인"
            },
            {
                "hypothesis": "압력 변화가 수율에 영향을 미친다",
                "test_type": "regression_analysis",
                "p_value": 0.023,
                "significance_level": 0.05,
                "result": "rejected_null",
                "conclusion": "압력이 수율에 유의미한 영향을 미침"
            },
            {
                "hypothesis": "공정 변수들이 정상 분포를 따른다",
                "test_type": "shapiro_wilk_test",
                "p_value": 0.156,
                "significance_level": 0.05,
                "result": "failed_to_reject_null",
                "conclusion": "대부분의 변수가 정상 분포를 따름"
            }
        ]
        
        # 알림 규칙 설정
        alert_rules = [
            {
                "rule_name": "temperature_outlier",
                "condition": "temperature > 300 OR temperature < 270",
                "severity": "high",
                "action": "immediate_notification"
            },
            {
                "rule_name": "purity_drop",
                "condition": "purity < 93",
                "severity": "medium",
                "action": "quality_team_alert"
            },
            {
                "rule_name": "yield_trend",
                "condition": "yield_7day_avg < 85",
                "severity": "low",
                "action": "trend_monitoring"
            }
        ]
        
        result = {
            "hypothesis_tests": hypothesis_tests,
            "statistical_summary": {
                "total_tests": len(hypothesis_tests),
                "significant_results": len([t for t in hypothesis_tests if t["p_value"] < 0.05]),
                "confidence_level": 0.95
            },
            "alert_system": {
                "rules_configured": len(alert_rules),
                "active_alerts": np.random.randint(0, 5),
                "notification_channels": ["email", "dashboard", "mobile"]
            },
            "alert_rules": alert_rules,
            "recommendations": [
                "온도 모니터링 시스템 강화 필요",
                "압력 제어 로직 최적화 검토",
                "실시간 품질 모니터링 대시보드 구축",
                "예측 모델 개발을 통한 선제적 대응 시스템 구축"
            ]
        }
        
        # 결과 저장
        result_file = save_analysis_result("hypothesis_testing", result)
        
        return AnalysisResult(
            success=True,
            message="가설 검정 및 알림 시스템이 성공적으로 구성되었습니다.",
            data=result,
            artifacts={
                "reports": [result_file, "statistical_tests_summary.pdf"],
                "files": ["alert_rules_config.json", "monitoring_dashboard.html"]
            },
            metadata={"step": 5, "significant_tests": len([t for t in hypothesis_tests if t["p_value"] < 0.05])}
        )
        
    except Exception as e:
        logger.error(f"가설 검정 단계 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"가설 검정 단계 실행 실패: {str(e)}")

# ============================
# 엔진 설정 관리 API
# ============================

@router.get("/engines/{engine_type}/config")
async def get_engine_config(engine_type: str):
    """엔진 설정 조회"""
    try:
        config_file = get_data_directory() / "engine_configs" / f"{engine_type}_config.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            # 기본 설정 반환
            default_configs = {
                "preprocessing": {
                    "enabled": True,
                    "cleaningRules": ["remove_duplicates", "handle_missing_values"],
                    "featureEngineering": ["normalize", "feature_selection"],
                    "metadataTagging": True
                },
                "eda": {
                    "enabled": True,
                    "autoReports": True,
                    "pandasProfiling": True,
                    "sweetviz": True,
                    "customCharts": ["correlation_matrix", "distribution_plots"]
                },
                "hypothesis": {
                    "enabled": True,
                    "statisticalTests": ["t_test", "chi_square", "anova"],
                    "alertRules": ["outlier_detection", "trend_analysis"],
                    "notifications": True
                }
            }
            return default_configs.get(engine_type, {})
            
    except Exception as e:
        logger.error(f"엔진 설정 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"엔진 설정 조회 실패: {str(e)}")

@router.post("/engines/{engine_type}/config")
async def save_engine_config(engine_type: str, config: Dict[str, Any]):
    """엔진 설정 저장"""
    try:
        config_dir = get_data_directory() / "engine_configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / f"{engine_type}_config.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return {"message": f"{engine_type} 엔진 설정이 저장되었습니다.", "config": config}
        
    except Exception as e:
        logger.error(f"엔진 설정 저장 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"엔진 설정 저장 실패: {str(e)}")

# ============================
# 유틸리티 API
# ============================

@router.get("/workflow/status")
async def get_workflow_status():
    """워크플로우 상태 조회"""
    try:
        return {
            "engines": {
                "preprocessing": {"status": "active", "version": "1.0.0"},
                "eda": {"status": "active", "version": "1.0.0"},
                "hypothesis": {"status": "active", "version": "1.0.0"}
            },
            "meta_store": {
                "status": "connected",
                "last_update": datetime.now().isoformat()
            },
            "system_health": "healthy"
        }
    except Exception as e:
        logger.error(f"워크플로우 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워크플로우 상태 조회 실패: {str(e)}")

@router.get("/results")
async def get_analysis_results(limit: int = Query(10, ge=1, le=100)):
    """분석 결과 목록 조회"""
    try:
        results_dir = get_data_directory() / "analysis_results"
        
        if not results_dir.exists():
            return {"results": []}
        
        # Mock 결과 목록
        mock_results = [
            {
                "id": f"analysis_{i}",
                "step": i % 5 + 1,
                "timestamp": datetime.now(),
                "status": "completed",
                "message": f"단계 {i % 5 + 1} 분석 완료"
            }
            for i in range(min(limit, 10))
        ]
        
        return {"results": mock_results}
        
    except Exception as e:
        logger.error(f"분석 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 결과 조회 실패: {str(e)}")