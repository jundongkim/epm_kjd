"""
DX-AI Manufacturing Copilot - 제품 예측 모델링 엔진

머신러닝 모델 훈련, 예측, 평가 및 AI 보고서 생성을 위한 핵심 엔진 클래스들
"""

import pandas as pd
import numpy as np
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# AI 모듈 import - 보고서 생성기 제거됨
# from ..ai.core.ai_report_generator import (
#     create_report_generator, 
#     ReportGenerationConfig
# )

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """지원되는 모델 타입"""
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    CATBOOST = "catboost"
    NEURAL_NETWORK = "neural_network"
    SVR = "svr"


class TaskType(Enum):
    """머신러닝 태스크 타입"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"


@dataclass
class ModelConfiguration:
    """모델 설정"""
    model_type: ModelType
    model_name: str
    task_type: TaskType
    target_variable: str
    hyperparameters: Dict[str, Any]
    test_size: float = 0.2
    random_state: int = 42


@dataclass
class TrainingResult:
    """훈련 결과"""
    model_name: str
    model_type: str
    target_variable: str
    feature_names: List[str]
    metrics: Dict[str, float]
    feature_importance: Optional[pd.DataFrame]
    predictions: Dict[str, np.ndarray]
    training_history: Optional[Dict[str, Any]]
    model_path: Optional[str]
    training_time: float
    data_shape: Tuple[int, int]


@dataclass
class PredictionRequest:
    """예측 요청"""
    model_name: str
    input_data: Dict[str, float]
    confidence_interval: bool = True


@dataclass
class PredictionResult:
    """예측 결과"""
    prediction: float
    confidence_interval: Optional[Tuple[float, float]]
    model_name: str
    timestamp: str


@dataclass
class ReportRequest:
    """AI 보고서 생성 요청"""
    report_type: str
    include_sections: List[str]
    report_length: str
    model_results: Optional[TrainingResult]
    additional_data: Dict[str, Any] = None


class ProductModelingEngine:
    """제품 예측 모델링 엔진"""
    
    def __init__(self):
        """엔진 초기화"""
        # ML 모델 매니저 import (여기서 import하여 순환 종속성 방지)
        try:
            from ..ml_models import ModelManager
            self.model_manager = ModelManager()
        except ImportError:
            logger.error("ModelManager를 import할 수 없습니다.")
            self.model_manager = None
        
        # AI 보고서 생성기 - 제거됨
        # self.report_generator = create_report_generator()
        
        # 상태 관리
        self.training_results = {}
        self.active_model = None
        
        # 데이터 저장
        self.training_data = None
        self.preprocessing_info = None
        
        logger.info("제품 예측 모델링 엔진 초기화 완료")
    
    def set_training_data(self, 
                         data: pd.DataFrame, 
                         preprocessing_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        훈련 데이터 설정
        
        Args:
            data: 훈련 데이터
            preprocessing_info: 전처리 정보
            
        Returns:
            설정 결과
        """
        try:
            self.training_data = data.copy()
            self.preprocessing_info = preprocessing_info
            
            # 데이터 기본 정보 분석
            numeric_columns = self._get_numeric_columns(data)
            categorical_columns = self._get_categorical_columns(data)
            
            return {
                "success": True,
                "data_shape": data.shape,
                "numeric_columns": numeric_columns,
                "categorical_columns": categorical_columns,
                "preprocessing_applied": preprocessing_info is not None,
                "message": "훈련 데이터가 성공적으로 설정되었습니다."
            }
            
        except Exception as e:
            logger.error(f"훈련 데이터 설정 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "훈련 데이터 설정에 실패했습니다."
            }
    
    def get_sample_data(self) -> pd.DataFrame:
        """예시 데이터 생성"""
        np.random.seed(42)
        n_samples = 100
        
        # 독립 변수들
        temperature = np.random.uniform(150, 200, n_samples)
        pressure = np.random.uniform(1.5, 3.0, n_samples) 
        flowRate = np.random.uniform(80, 120, n_samples)
        humidity = np.random.uniform(40, 60, n_samples)
        phLevel = np.random.uniform(6.5, 8.5, n_samples)
        viscosity = np.random.uniform(0.8, 1.2, n_samples)
        
        # 종속 변수 (quality_score) - 독립 변수들의 복합 함수
        quality_score = (
            85 + 
            0.02 * temperature + 
            0.5 * pressure + 
            0.01 * flowRate +
            0.1 * phLevel +
            np.random.normal(0, 2, n_samples)  # 노이즈 추가
        )
        quality_score = np.clip(quality_score, 80, 100)  # 물리적 제약
        
        sample_data = pd.DataFrame({
            "temperature": temperature,
            "pressure": pressure,
            "flowRate": flowRate,
            "humidity": humidity,
            "phLevel": phLevel,
            "viscosity": viscosity,
            "quality_score": quality_score
        })
        return sample_data
    
    def create_model(self, config: ModelConfiguration) -> Dict[str, Any]:
        """
        모델 생성
        
        Args:
            config: 모델 설정
            
        Returns:
            생성 결과
        """
        if self.model_manager is None:
            return {
                "success": False,
                "error": "ModelManager가 초기화되지 않았습니다.",
                "message": "모델 매니저를 사용할 수 없습니다."
            }
        
        try:
            success = self.model_manager.create_model(
                config.model_type.value,
                config.model_name,
                config.task_type.value
            )
            
            if success:
                return {
                    "success": True,
                    "model_name": config.model_name,
                    "model_type": config.model_type.value,
                    "message": f"모델 '{config.model_name}'이 성공적으로 생성되었습니다."
                }
            else:
                return {
                    "success": False,
                    "error": "모델 생성 실패",
                    "message": "모델 생성에 실패했습니다."
                }
                
        except Exception as e:
            logger.error(f"모델 생성 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"모델 생성 중 오류가 발생했습니다: {str(e)}"
            }
    
    def _safe_to_list(self, data: Any) -> List[Any]:
        """안전하게 데이터를 리스트로 변환"""
        if data is None:
            return []
        elif isinstance(data, list):
            return data
        elif hasattr(data, 'tolist'):
            try:
                return data.tolist()
            except (AttributeError, TypeError):
                return list(data) if hasattr(data, '__iter__') else [data]
        elif hasattr(data, '__iter__') and not isinstance(data, (str, bytes)):
            return list(data)
        else:
            return [data]

    def train_model(self, config: ModelConfiguration) -> Dict[str, Any]:
        """
        모델 훈련
        
        Args:
            config: 모델 설정
            
        Returns:
            훈련 결과
        """
        if self.model_manager is None:
            return {
                "success": False,
                "error": "ModelManager가 초기화되지 않았습니다."
            }
        
        if self.training_data is None:
            return {
                "success": False,
                "error": "훈련 데이터가 설정되지 않았습니다."
            }
        
        try:
            start_time = time.time()
            
            # 데이터 정리
            clean_data = self._clean_training_data(
                self.training_data, config.target_variable
            )
            
            # 모델 훈련
            result = self.model_manager.train_model(
                config.model_name,
                clean_data,
                config.target_variable,
                show_progress=False,
                **config.hyperparameters
            )
            
            logger.info(f"모델 훈련 결과 키: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            
            training_time = time.time() - start_time
            
            # 예측 결과 안전하게 처리
            test_actual_raw = result.get('test_actual', [])
            test_predictions_raw = result.get('test_predictions', [])
            
            logger.info(f"test_actual 타입: {type(test_actual_raw)}, 길이: {len(test_actual_raw) if hasattr(test_actual_raw, '__len__') else 'N/A'}")
            logger.info(f"test_predictions 타입: {type(test_predictions_raw)}, 길이: {len(test_predictions_raw) if hasattr(test_predictions_raw, '__len__') else 'N/A'}")
            
            test_actual = self._safe_to_list(test_actual_raw)
            test_predictions = self._safe_to_list(test_predictions_raw)
            
            logger.info(f"변환 후 - test_actual: {len(test_actual)} 항목, test_predictions: {len(test_predictions)} 항목")
            
            # 훈련 결과 구성
            training_result = TrainingResult(
                model_name=config.model_name,
                model_type=config.model_type.value,
                target_variable=config.target_variable,
                feature_names=result.get('feature_names', []),
                metrics=result.get('metrics', {}),
                feature_importance=result.get('feature_importance'),
                predictions={
                    'test_actual': test_actual,
                    'test_predictions': test_predictions
                },
                training_history=result.get('training_history'),
                model_path=None,  # 저장 후 업데이트
                training_time=training_time,
                data_shape=clean_data.shape
            )
            
            # 모델 저장
            try:
                saved_path = self.model_manager.save_model(config.model_name)
                training_result.model_path = saved_path
            except Exception as e:
                logger.warning(f"모델 저장 실패: {e}")
            
            # 결과 저장
            self.training_results[config.model_name] = training_result
            self.active_model = config.model_name
            
            return {
                "success": True,
                "training_result": training_result,
                "message": "모델 훈련이 성공적으로 완료되었습니다."
            }
            
        except Exception as e:
            logger.error(f"모델 훈련 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"모델 훈련 중 오류가 발생했습니다: {str(e)}"
            }
    
    def predict(self, request: PredictionRequest) -> Dict[str, Any]:
        """
        예측 수행
        
        Args:
            request: 예측 요청
            
        Returns:
            예측 결과
        """
        if self.model_manager is None:
            return {
                "success": False,
                "error": "ModelManager가 초기화되지 않았습니다."
            }

        try:
            # 훈련된 모델의 특성 정보 가져오기
            if request.model_name in self.training_results:
                training_result = self.training_results[request.model_name]
                expected_features = training_result.feature_names
            else:
                expected_features = list(request.input_data.keys())
            
            # 모든 예상 특성에 대해 기본값 설정
            complete_input_data = {}
            default_values = {
                'temperature': 175.0,
                'pressure': 2.5,
                'flowRate': 100.0,
                'humidity': 50.0,
                'phLevel': 7.0,
                'viscosity': 1.0
            }
            
            # 예상 특성에 대해 입력값 또는 기본값 사용
            for feature in expected_features:
                if feature in request.input_data:
                    complete_input_data[feature] = request.input_data[feature]
                elif feature in default_values:
                    complete_input_data[feature] = default_values[feature]
                else:
                    # 알 수 없는 특성에 대해서는 중간값 사용
                    complete_input_data[feature] = 1.0
            
            # 입력 데이터를 DataFrame으로 변환 (특성 순서 보장)
            input_df = pd.DataFrame([complete_input_data], columns=expected_features)
            
            # 예측 수행
            prediction = self.model_manager.predict(request.model_name, input_df)
            
            # 신뢰구간 계산
            confidence_interval = None
            if request.confidence_interval and request.model_name in self.training_results:
                training_result = self.training_results[request.model_name]
                rmse = training_result.metrics.get('rmse', 0)
                if rmse > 0:
                    margin = 1.96 * rmse  # 95% 신뢰구간
                    confidence_interval = (
                        float(prediction[0] - margin),
                        float(prediction[0] + margin)
                    )
            
            # 결과 구성
            result = PredictionResult(
                prediction=float(prediction[0]),
                confidence_interval=confidence_interval,
                model_name=request.model_name,
                timestamp=datetime.now().isoformat()
            )
            
            return {
                "success": True,
                "prediction_result": result,
                "message": "예측이 성공적으로 완료되었습니다."
            }
            
        except Exception as e:
            logger.error(f"예측 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"예측 중 오류가 발생했습니다: {str(e)}"
            }
    
    def generate_ai_report(self, request: ReportRequest) -> Dict[str, Any]:
        """
        AI 보고서 생성 - 보고서 생성기 제거됨
        
        Args:
            request: 보고서 생성 요청
            
        Returns:
            생성된 보고서
        """
        try:
            # 폴백: 기본 보고서 생성
            fallback_report = self._generate_fallback_report(request)
            
            return {
                "success": True,
                "report_content": fallback_report,
                "report_metadata": {
                    "generator": "fallback",
                    "timestamp": datetime.now().isoformat()
                },
                "message": "기본 템플릿으로 보고서가 생성되었습니다."
            }
            
        except Exception as e:
            logger.error(f"AI 보고서 생성 실패: {e}")
            
            return {
                "success": False,
                "report_content": "보고서 생성에 실패했습니다.",
                "report_metadata": {
                    "generator": "error",
                    "timestamp": datetime.now().isoformat()
                },
                "message": f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
            }
    
    def get_model_recommendations(self, data: pd.DataFrame, target_col: str) -> List[Dict[str, Any]]:
        """
        데이터에 적합한 모델 추천
        
        Args:
            data: 데이터프레임
            target_col: 타겟 변수
            
        Returns:
            추천 모델 리스트
        """
        if self.model_manager is None:
            return []
        
        try:
            return self.model_manager.get_model_recommendations(data, target_col)
        except Exception as e:
            logger.error(f"모델 추천 실패: {e}")
            return []
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """등록된 모델 목록 반환"""
        if self.model_manager is None:
            return []
        
        try:
            return self.model_manager.list_models()
        except Exception as e:
            logger.error(f"모델 목록 조회 실패: {e}")
            return []
    
    def get_training_result(self, model_name: str) -> Optional[TrainingResult]:
        """훈련 결과 조회"""
        return self.training_results.get(model_name)
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """모델 정보 조회"""
        if self.model_manager is None:
            return {}
        
        try:
            return self.model_manager.get_model_info(model_name)
        except Exception as e:
            logger.error(f"모델 정보 조회 실패: {e}")
            return {}
    
    def _get_numeric_columns(self, df: pd.DataFrame) -> List[str]:
        """수치형 컬럼 필터링"""
        numeric_cols = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]) and not self._is_date_like(df[col]):
                try:
                    pd.to_numeric(df[col], errors='raise')
                    numeric_cols.append(col)
                except (ValueError, TypeError):
                    continue
        return numeric_cols
    
    def _get_categorical_columns(self, df: pd.DataFrame) -> List[str]:
        """범주형 컬럼 필터링"""
        categorical_cols = []
        for col in df.columns:
            if df[col].dtype == 'object' and not self._is_date_like(df[col]):
                categorical_cols.append(col)
        return categorical_cols
    
    def _is_date_like(self, series: pd.Series) -> bool:
        """시리즈가 날짜 형식인지 확인"""
        if series.dtype == 'object':
            sample_size = min(10, len(series))
            sample_values = series.dropna().head(sample_size)
            
            date_count = 0
            for value in sample_values:
                if isinstance(value, str):
                    try:
                        pd.to_datetime(value, errors='raise')
                        date_count += 1
                    except (ValueError, TypeError):
                        continue
            
            return date_count / len(sample_values) >= 0.5 if len(sample_values) > 0 else False
        return False
    
    def _clean_training_data(self, data: pd.DataFrame, target_variable: str) -> pd.DataFrame:
        """훈련 데이터 정리"""
        clean_data = data.copy()
        
        # 데이터 유효성 검증
        validation_errors = []
        
        # 1. 타겟 변수 존재 확인
        if target_variable not in clean_data.columns:
            validation_errors.append(f"필수 컬럼 누락: ['{target_variable}']")
        
        # 2. 수치형 컬럼 확인
        numeric_columns = self._get_numeric_columns(clean_data)
        if target_variable in clean_data.columns and target_variable not in numeric_columns:
            validation_errors.append(f"타겟 변수 '{target_variable}'가 수치형이 아닙니다")
        
        # 유효성 검증 실패 시 예외 발생
        if validation_errors:
            error_msg = f"데이터 유효성 검증 실패: {validation_errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 문제가 있는 컬럼 제거 (타겟 변수는 제외)
        cols_to_remove = []
        for col in clean_data.columns:
            if col != target_variable and clean_data[col].dtype == 'object':
                if self._is_date_like(clean_data[col]):
                    cols_to_remove.append(col)
                elif not self._is_convertible_to_numeric(clean_data[col]):
                    cols_to_remove.append(col)
        
        if cols_to_remove:
            clean_data = clean_data.drop(columns=cols_to_remove)
            logger.info(f"문제가 있는 컬럼 제거: {cols_to_remove}")
        
        # 최종 검증: 타겟 변수가 여전히 존재하는지 확인
        if target_variable not in clean_data.columns:
            error_msg = f"데이터 정리 후 타겟 변수 '{target_variable}'가 누락되었습니다"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return clean_data
    
    def _is_convertible_to_numeric(self, series: pd.Series) -> bool:
        """시리즈가 숫자로 변환 가능한지 확인"""
        sample_val = series.dropna().iloc[0] if not series.dropna().empty else None
        if sample_val is not None:
            try:
                float(str(sample_val))
                return True
            except (ValueError, TypeError):
                return False
        return False
    
    def _get_prediction_range(self, predictions: Dict[str, Any]) -> Dict[str, float]:
        """예측 범위 계산"""
        if 'test_predictions' not in predictions:
            return {}
            
        preds = predictions['test_predictions']
        
        # 안전한 리스트 변환
        preds_list = self._safe_to_list(preds)
        
        # 빈 배열이나 잘못된 데이터 처리
        if not preds_list:
            return {}
            
        try:
            # 숫자가 아닌 값들 필터링
            numeric_preds = []
            for pred in preds_list:
                try:
                    numeric_preds.append(float(pred))
                except (ValueError, TypeError):
                    continue
            
            if not numeric_preds:
                return {}
                
            preds_array = np.array(numeric_preds)
            
            return {
                "min": float(np.min(preds_array)),
                "max": float(np.max(preds_array)),
                "mean": float(np.mean(preds_array)),
                "std": float(np.std(preds_array))
            }
        except (ValueError, TypeError) as e:
            logger.warning(f"예측 범위 계산 실패: {e}")
            return {}
        except Exception as e:
            logger.error(f"예측 범위 계산 중 예상치 못한 오류: {e}")
            return {}
    
    def _generate_fallback_report(self, request: ReportRequest) -> str:
        """폴백 보고서 생성"""
        report_content = f"""# {request.report_type}

## 개요
제품 예측 모델링 결과에 대한 {request.report_type} 보고서입니다.

"""
        
        if request.model_results:
            report_content += f"""## 모델 정보
- **모델명**: {request.model_results.model_name}
- **모델 타입**: {request.model_results.model_type}
- **목표 변수**: {request.model_results.target_variable}
- **훈련 시간**: {request.model_results.training_time:.2f}초
- **데이터 크기**: {request.model_results.data_shape[0]} × {request.model_results.data_shape[1]}

## 성능 지표
"""
            for metric, value in request.model_results.metrics.items():
                report_content += f"- **{metric.upper()}**: {value:.4f}\n"
            
            if request.model_results.feature_importance is not None:
                report_content += """
## 피처 중요도
모델 훈련을 통해 각 입력 변수의 중요도가 분석되었습니다.

"""
        
        report_content += f"""
## 결론
모델링 작업이 완료되었으며, 향후 예측 작업에 활용할 수 있습니다.

---
*보고서 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report_content


# 편의 함수들
def create_model_configuration(
    model_type: str,
    model_name: str,
    target_variable: str,
    hyperparameters: Dict[str, Any],
    task_type: str = "regression"
) -> ModelConfiguration:
    """모델 설정 생성 편의 함수"""
    return ModelConfiguration(
        model_type=ModelType(model_type),
        model_name=model_name,
        task_type=TaskType(task_type),
        target_variable=target_variable,
        hyperparameters=hyperparameters
    )


def create_prediction_request(
    model_name: str,
    input_data: Dict[str, float],
    confidence_interval: bool = True
) -> PredictionRequest:
    """예측 요청 생성 편의 함수"""
    return PredictionRequest(
        model_name=model_name,
        input_data=input_data,
        confidence_interval=confidence_interval
    )


def create_report_request(
    report_type: str,
    include_sections: List[str],
    report_length: str = "표준 (3-5페이지)",
    model_results: Optional[TrainingResult] = None,
    additional_data: Dict[str, Any] = None
) -> ReportRequest:
    """보고서 요청 생성 편의 함수"""
    return ReportRequest(
        report_type=report_type,
        include_sections=include_sections,
        report_length=report_length,
        model_results=model_results,
        additional_data=additional_data or {}
    ) 