"""
DX-AI Manufacturing Copilot - 원가 최적화 엔진

생산 이력 학습, 품질 예측, 민감도 분석 및 최적화를 통합하는 핵심 엔진
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# 최적화 라이브러리
from scipy.optimize import minimize, differential_evolution
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 내부 모듈
from .data_models import (
    MaterialUsageModel, CostItemModel, OptimizationResultModel,
    PredictionModel, LotModel, EquipmentReadingModel
)
from src.ml_models.model_manager import ModelManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationConstraint:
    """최적화 제약 조건"""
    parameter: str
    constraint_type: str  # 'ge' (>=), 'le' (<=), 'eq' (=)
    value: float
    weight: float = 1.0


@dataclass
class QualityTarget:
    """품질 목표"""
    metric: str
    target_value: float
    constraint_type: str = "ge"  # 'ge' (>=), 'le' (<=), 'eq' (=)
    tolerance: float = 0.0
    weight: float = 1.0


class ProductionHistoryLearner:
    """생산 이력 학습 시스템"""
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        # ModelManager 인스턴스 공유
        self.model_manager = model_manager if model_manager is not None else ModelManager()
        self.production_data = None
        self.material_usage_history = None
        self.quality_history = None
        
    def load_production_history(self, data_path: str = None) -> Dict[str, Any]:
        """생산 이력 데이터 로드"""
        if data_path:
            # 실제 파일에서 데이터 로드
            try:
                self.production_data = pd.read_csv(data_path)
                logger.info(f"생산 이력 데이터 로드 완료: {len(self.production_data)} 레코드")
            except Exception as e:
                logger.error(f"데이터 로드 실패: {e}")
                return {"success": False, "error": str(e)}
        else:
            # 시뮬레이션 데이터 생성
            self.production_data = self._generate_simulation_data()
            logger.info("시뮬레이션 데이터 생성 완료")
        
        return {"success": True, "data_shape": self.production_data.shape}
    
    def _generate_simulation_data(self) -> pd.DataFrame:
        """시뮬레이션 생산 이력 데이터 생성"""
        np.random.seed(42)
        n_samples = 1000
        
        # 투입량 변수
        material_a = np.random.normal(100, 10, n_samples)  # 원료 A (kg/h)
        material_b = np.random.normal(50, 5, n_samples)    # 원료 B (kg/h)
        catalyst = np.random.normal(5, 0.5, n_samples)    # 촉매 (kg/h)
        
        # 운전 조건
        temperature = np.random.normal(175, 5, n_samples)  # 온도 (°C)
        pressure = np.random.normal(2.5, 0.2, n_samples)  # 압력 (bar)
        flow_rate = np.random.normal(200, 15, n_samples)   # 유량 (L/h)
        
        # 유틸리티 사용량
        steam = np.random.normal(150, 10, n_samples)       # 스팀 (kg/h)
        electricity = np.random.normal(80, 8, n_samples)   # 전력 (kWh)
        cooling_water = np.random.normal(500, 30, n_samples)  # 냉각수 (L/h)
        
        # 품질 지표 (투입량과 운전조건의 복합 함수)
        purity = (
            85 + 
            0.1 * material_a + 
            0.05 * material_b + 
            0.5 * catalyst + 
            0.02 * temperature + 
            0.5 * pressure +
            np.random.normal(0, 1, n_samples)
        )
        purity = np.clip(purity, 80, 99)  # 물리적 제약
        
        yield_rate = (
            75 + 
            0.08 * material_a + 
            0.12 * material_b + 
            0.3 * catalyst + 
            0.01 * temperature + 
            0.2 * pressure +
            np.random.normal(0, 1.5, n_samples)
        )
        yield_rate = np.clip(yield_rate, 70, 95)  # 물리적 제약
        
        # 비용 계산
        material_cost = (
            material_a * 450 +  # 원료 A 단가
            material_b * 720 +  # 원료 B 단가
            catalyst * 18000    # 촉매 단가
        )
        
        utility_cost = (
            steam * 50 +        # 스팀 단가
            electricity * 120 + # 전력 단가
            cooling_water * 5   # 냉각수 단가
        )
        
        total_cost = material_cost + utility_cost
        
        # 데이터프레임 생성
        data = pd.DataFrame({
            'lot_number': [f'LOT_{i+1:04d}' for i in range(n_samples)],
            'timestamp': pd.date_range(start='2023-01-01', periods=n_samples, freq='H'),
            'material_a': material_a,
            'material_b': material_b,
            'catalyst': catalyst,
            'temperature': temperature,
            'pressure': pressure,
            'flow_rate': flow_rate,
            'steam': steam,
            'electricity': electricity,
            'cooling_water': cooling_water,
            'purity': purity,
            'yield': yield_rate,
            'material_cost': material_cost,
            'utility_cost': utility_cost,
            'total_cost': total_cost,
            'production_rate': np.random.normal(95, 5, n_samples)  # 생산율
        })
        
        return data
    
    def prepare_ml_training_data(self) -> Tuple[pd.DataFrame, List[str]]:
        """ML 모델 훈련용 데이터 준비"""
        if self.production_data is None:
            raise ValueError("생산 이력 데이터가 로드되지 않았습니다.")
        
        # 특성 컬럼 정의
        feature_columns = [
            'material_a', 'material_b', 'catalyst',
            'temperature', 'pressure', 'flow_rate',
            'steam', 'electricity', 'cooling_water'
        ]
        
        # 목표 변수 정의
        target_columns = ['purity', 'yield', 'total_cost']
        
        # 컬럼명 매핑 (다양한 형태의 컬럼명 지원)
        column_mapping = {
            # 원료 관련
            'material_a': ['material_a', 'Material_A', '원료_A', '원료A', 'raw_material_a'],
            'material_b': ['material_b', 'Material_B', '원료_B', '원료B', 'raw_material_b'],
            'catalyst': ['catalyst', 'Catalyst', '촉매', 'cat'],
            # 운전 조건
            'temperature': ['temperature', 'Temperature', 'temp', 'Temperature_C', '온도'],
            'pressure': ['pressure', 'Pressure', 'press', 'Pressure_bar', '압력'],
            'flow_rate': ['flow_rate', 'Flow_Rate', 'flowrate', 'flow', '유량'],
            # 유틸리티
            'steam': ['steam', 'Steam', '스팀', 'steam_usage'],
            'electricity': ['electricity', 'Electricity', 'electric', 'power', '전력'],
            'cooling_water': ['cooling_water', 'Cooling_Water', 'coolant', '냉각수'],
            # 품질 지표
            'purity': ['purity', 'Purity', 'Purity_%', 'purity_percent', '순도'],
            'yield': ['yield', 'Yield', 'Yield_%', 'yield_rate', '수율'],
            'total_cost': ['total_cost', 'Total_Cost', 'cost', '총비용', '총원가']
        }
        
        # 실제 데이터의 컬럼명 확인 및 매핑
        available_columns = self.production_data.columns.tolist()
        mapped_columns = {}
        
        for standard_name, possible_names in column_mapping.items():
            for possible_name in possible_names:
                if possible_name in available_columns:
                    mapped_columns[standard_name] = possible_name
                    break
        
        # 누락된 필수 컬럼 확인
        missing_features = [col for col in feature_columns if col not in mapped_columns]
        missing_targets = [col for col in target_columns if col not in mapped_columns]
        
        if missing_features:
            logger.warning(f"누락된 특성 컬럼: {missing_features}")
        if missing_targets:
            logger.warning(f"누락된 목표 컬럼: {missing_targets}")
        
        # 사용 가능한 컬럼만으로 데이터 구성
        available_features = [col for col in feature_columns if col in mapped_columns]
        available_targets = [col for col in target_columns if col in mapped_columns]
        
        # 데이터 추출 및 정규화
        X = self.production_data[[mapped_columns[col] for col in available_features]].copy()
        X.columns = available_features  # 표준 컬럼명으로 변경
        
        y = self.production_data[[mapped_columns[col] for col in available_targets]].copy()
        y.columns = available_targets  # 표준 컬럼명으로 변경
        
        # 간단한 정규화 (StandardScaler 대신)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = pd.DataFrame(
            scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
        
        # 스케일러 정보 저장 (예측 시 사용)
        self.feature_scaler = scaler
        self.feature_columns = available_features
        
        # 전체 데이터 결합
        training_data = pd.concat([X_scaled, y], axis=1)
        
        return training_data, available_features
    
    def train_quality_prediction_models(self) -> Dict[str, Any]:
        """품질 예측 모델 훈련 - 순환 종속성 해결"""
        training_data, feature_columns = self.prepare_ml_training_data()
        
        # 순환 종속성 방지를 위한 독립적인 피처 정의
        independent_features = [
            'material_a', 'material_b', 'catalyst',
            'temperature', 'pressure', 'flow_rate',
            'steam', 'electricity', 'cooling_water'
        ]
        
        # 독립 피처만 사용하는 훈련 데이터
        independent_data = training_data[independent_features + ['purity', 'yield', 'total_cost']].copy()
        
        results = {}
        
        try:
            # 순도 예측 모델 (독립 피처만 사용)
            purity_model_name = "purity_predictor"
            if self.model_manager.create_model("random_forest", purity_model_name, "regression"):
                purity_result = self.model_manager.train_model(
                    purity_model_name, 
                    independent_data[independent_features + ['purity']], 
                    'purity',
                    show_progress=False
                )
                results['purity'] = purity_result
                logger.info(f"순도 예측 모델 훈련 완료: {purity_model_name}")
            
            # 수율 예측 모델 (독립 피처만 사용)
            yield_model_name = "yield_predictor"
            if self.model_manager.create_model("random_forest", yield_model_name, "regression"):
                yield_result = self.model_manager.train_model(
                    yield_model_name, 
                    independent_data[independent_features + ['yield']], 
                    'yield',
                    show_progress=False
                )
                results['yield'] = yield_result
                logger.info(f"수율 예측 모델 훈련 완료: {yield_model_name}")
            
            # 총 비용 예측 모델 (독립 피처만 사용)
            cost_model_name = "cost_predictor"
            if self.model_manager.create_model("random_forest", cost_model_name, "regression"):
                cost_result = self.model_manager.train_model(
                    cost_model_name, 
                    independent_data[independent_features + ['total_cost']], 
                    'total_cost',
                    show_progress=False
                )
                results['total_cost'] = cost_result
                logger.info(f"비용 예측 모델 훈련 완료: {cost_model_name}")
            
            # 사용된 피처 정보 저장 (예측 시 참조용)
            self.feature_columns = independent_features
            
            logger.info("전체 품질 예측 모델 훈련 완료 (순도/수율/비용 모델 3개)")
            
        except Exception as e:
            logger.error(f"모델 훈련 실패: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_context_engineering_data(self) -> Dict[str, Any]:
        """Context Engineering용 데이터 생성"""
        if self.production_data is None:
            return {}
        
        # 최근 데이터 통계
        recent_data = self.production_data.tail(100)
        
        context_data = {
            "production_history": [],
            "material_usage": [],
            "quality_metrics": {},
            "cost_breakdown": [],
            "optimization_potential": {},
            "model_performance": {}
        }
        
        # 생산 이력 요약
        for _, row in recent_data.head(10).iterrows():
            context_data["production_history"].append({
                "lot_number": row['lot_number'],
                "quantity": row['production_rate'],
                "purity": row['purity'],
                "yield": row['yield']
            })
        
        # 원료 사용량 통계
        material_stats = {
            "material_a": {
                "name": "원료 A",
                "quantity": recent_data['material_a'].mean(),
                "unit": "kg/h",
                "unit_cost": 450
            },
            "material_b": {
                "name": "원료 B", 
                "quantity": recent_data['material_b'].mean(),
                "unit": "kg/h",
                "unit_cost": 720
            },
            "catalyst": {
                "name": "촉매",
                "quantity": recent_data['catalyst'].mean(),
                "unit": "kg/h",
                "unit_cost": 18000
            }
        }
        
        for material in material_stats.values():
            context_data["material_usage"].append(material)
        
        # 품질 지표 통계
        context_data["quality_metrics"] = {
            "평균 순도": f"{recent_data['purity'].mean():.2f}%",
            "평균 수율": f"{recent_data['yield'].mean():.2f}%",
            "품질 변동계수": f"{recent_data['purity'].std() / recent_data['purity'].mean():.3f}"
        }
        
        # 원가 구조
        avg_material_cost = recent_data['material_cost'].mean()
        avg_utility_cost = recent_data['utility_cost'].mean()
        total_avg_cost = avg_material_cost + avg_utility_cost
        
        context_data["cost_breakdown"] = [
            {
                "항목": "원료비",
                "금액(만원)": avg_material_cost / 10000,
                "비율(%)": (avg_material_cost / total_avg_cost) * 100
            },
            {
                "항목": "유틸리티",
                "금액(만원)": avg_utility_cost / 10000,
                "비율(%)": (avg_utility_cost / total_avg_cost) * 100
            }
        ]
        
        return context_data


class CostOptimizationEngine:
    """원가 최적화 엔진"""
    
    def __init__(self):
        # 공유 ModelManager 인스턴스 생성
        self.model_manager = ModelManager()
        self.history_learner = ProductionHistoryLearner(self.model_manager)  # 같은 인스턴스 공유
        self.optimization_results = None
        
    def initialize(self, data_path: str = None) -> Dict[str, Any]:
        """초기화 및 데이터 로드"""
        # 생산 이력 데이터 로드
        load_result = self.history_learner.load_production_history(data_path)
        if not load_result["success"]:
            return load_result
        
        # ML 모델 훈련
        training_result = self.history_learner.train_quality_prediction_models()
        
        return {
            "success": True,
            "data_loaded": load_result,
            "models_trained": training_result
        }
    
    def predict_quality(self, input_conditions: Dict[str, float]) -> Dict[str, float]:
        """품질 예측 - 독립 피처만 사용"""
        # 순환 종속성 방지를 위한 독립적인 피처만 사용
        required_features = [
            'material_a', 'material_b', 'catalyst',
            'temperature', 'pressure', 'flow_rate',
            'steam', 'electricity', 'cooling_water'
        ]
        
        # 기본값 설정 (누락된 컬럼 대응)
        default_values = {
            'material_a': 100.0,
            'material_b': 50.0,
            'catalyst': 5.0,
            'temperature': 175.0,
            'pressure': 2.5,
            'flow_rate': 200.0,
            'steam': 150.0,
            'electricity': 80.0,
            'cooling_water': 500.0
        }
        
        # 입력 조건 보완
        complete_conditions = default_values.copy()
        complete_conditions.update(input_conditions)
        
        # 데이터프레임 생성 (정확한 컬럼 순서 보장)
        try:
            # 필요한 컬럼만 추출하고 올바른 순서로 정렬
            input_data = []
            for feature in required_features:
                input_data.append(complete_conditions.get(feature, default_values.get(feature, 0.0)))
            
            input_df = pd.DataFrame([input_data], columns=required_features)
            
            # 훈련 시 사용한 스케일러가 있다면 적용
            if hasattr(self.history_learner, 'feature_scaler') and self.history_learner.feature_scaler is not None:
                try:
                    input_df_scaled = pd.DataFrame(
                        self.history_learner.feature_scaler.transform(input_df),
                        columns=required_features
                    )
                except Exception as scale_error:
                    logger.warning(f"스케일링 실패, 원본 데이터 사용: {scale_error}")
                    input_df_scaled = input_df
            else:
                input_df_scaled = input_df
                logger.warning("특성 스케일러가 없습니다. 원본 데이터를 사용합니다.")
            
        except Exception as e:
            logger.error(f"입력 데이터 처리 실패: {e}")
            return {"error": f"입력 데이터 처리 실패: {e}"}
        
        # 예측 수행
        predictions = {}
        
        try:
            # 모델 존재 여부 확인
            available_models = [model['name'] for model in self.model_manager.list_models()]
            
            # 각 모델별로 안전하게 예측 수행
            model_predictions = {}
            
            for model_name, target_name in [
                ("purity_predictor", "purity"),
                ("yield_predictor", "yield"), 
                ("cost_predictor", "total_cost")
            ]:
                if model_name in available_models:
                    try:
                        # 모델 정보 확인
                        model_info = self.model_manager.get_model_info(model_name)
                        if model_info.get('manager_info', {}).get('trained', False):
                            # 더 안전한 예측 수행
                            try:
                                # 입력 데이터 형태 확인
                                logger.debug(f"{model_name} 예측 시작 - 입력 데이터 형태: {input_df_scaled.shape}, 컬럼: {input_df_scaled.columns.tolist()}")
                                
                                # 모델에 예측 요청
                                pred_result = self.model_manager.predict(model_name, input_df_scaled)
                                
                                if pred_result is not None and len(pred_result) > 0:
                                    model_predictions[target_name] = float(pred_result[0])
                                    logger.debug(f"{model_name} 예측 성공: {model_predictions[target_name]}")
                                else:
                                    logger.warning(f"{model_name} 예측 결과가 비어있습니다.")
                                    model_predictions[target_name] = 0.0
                                    
                            except Exception as prediction_error:
                                error_msg = str(prediction_error)
                                logger.error(f"{model_name} 모델 예측 중 오류: {error_msg}")
                                
                                # 특정 오류 타입별 처리
                                if "not in index" in error_msg:
                                    logger.error(f"컬럼 인덱스 오류 - 필요한 컬럼: {required_features}")
                                    logger.error(f"입력 데이터 컬럼: {input_df_scaled.columns.tolist()}")
                                
                                model_predictions[target_name] = 0.0
                        else:
                            logger.warning(f"{model_name} 모델이 훈련되지 않았습니다.")
                            model_predictions[target_name] = 0.0
                    except Exception as model_error:
                        logger.error(f"{model_name} 모델 정보 확인 오류: {model_error}")
                        model_predictions[target_name] = 0.0
                else:
                    logger.warning(f"{model_name} 모델을 찾을 수 없습니다.")
                    model_predictions[target_name] = 0.0
            
            # 예측 결과 검증 및 기본값 적용
            predictions['purity'] = model_predictions.get('purity', 95.0)
            predictions['yield'] = model_predictions.get('yield', 85.0)  
            predictions['total_cost'] = model_predictions.get('total_cost', 100000.0)
            
            # 예측값이 모두 0이거나 비현실적인 경우 기본값으로 대체
            if predictions['purity'] <= 0:
                predictions['purity'] = 95.0
            if predictions['yield'] <= 0:
                predictions['yield'] = 85.0
            if predictions['total_cost'] <= 0:
                predictions['total_cost'] = 100000.0
            
            # 예측이 모두 실패한 경우 사용자에게 알림
            if all(v == 0.0 for v in model_predictions.values()):
                predictions["warning"] = "모든 모델 예측이 실패했습니다. 기본값을 사용합니다."
                logger.warning("모든 모델 예측이 실패했습니다. 기본값을 사용합니다.")
            
        except Exception as e:
            logger.error(f"전체 예측 실패: {e}")
            # 기본값으로 fallback
            predictions = {
                "purity": 95.0,
                "yield": 85.0,
                "total_cost": 100000.0,
                "error": f"예측 실패: {str(e)}"
            }
        
        return predictions
    
    def sensitivity_analysis(self, base_conditions: Dict[str, float],
                           variables: List[str], 
                           variation_range: float = 0.1) -> Dict[str, Dict[str, float]]:
        """민감도 분석"""
        sensitivities = {}
        
        # 기준 조건에서의 예측값
        base_predictions = self.predict_quality(base_conditions)
        
        # 예측 실패한 경우 빈 결과 반환
        if "error" in base_predictions:
            logger.error(f"기준 조건 예측 실패: {base_predictions['error']}")
            return {}
        
        for var in variables:
            if var not in base_conditions:
                # 기본값으로 변수 추가
                default_values = {
                    'material_a': 100.0, 'material_b': 50.0, 'catalyst': 5.0,
                    'temperature': 175.0, 'pressure': 2.5, 'flow_rate': 200.0,
                    'steam': 150.0, 'electricity': 80.0, 'cooling_water': 500.0
                }
                base_conditions[var] = default_values.get(var, 100.0)
            
            var_sensitivities = {}
            base_value = base_conditions[var]
            
            # 변동 범위 계산
            delta = base_value * variation_range
            
            # 상한 예측
            upper_conditions = base_conditions.copy()
            upper_conditions[var] = base_value + delta
            upper_predictions = self.predict_quality(upper_conditions)
            
            # 하한 예측
            lower_conditions = base_conditions.copy()
            lower_conditions[var] = base_value - delta
            lower_predictions = self.predict_quality(lower_conditions)
            
            # 민감도 계산
            for metric in ['purity', 'yield', 'total_cost']:
                if metric in base_predictions:
                    sensitivity = (
                        (upper_predictions[metric] - lower_predictions[metric]) / 
                        (2 * delta)
                    ) * base_value / base_predictions[metric]
                    var_sensitivities[metric] = sensitivity
            
            sensitivities[var] = var_sensitivities
        
        return sensitivities
    
    def optimize_inputs(self, 
                       quality_targets: List[QualityTarget],
                       constraints: List[OptimizationConstraint],
                       bounds: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """투입량 최적화"""
        
        # 최적화 변수 정의
        variables = list(bounds.keys())
        bounds_list = [bounds[var] for var in variables]
        
        def objective_function(x):
            """목적 함수 (비용 최소화)"""
            input_conditions = dict(zip(variables, x))
            
            # 누락된 변수에 대한 기본값 설정
            default_values = {
                'material_a': 100, 'material_b': 50, 'catalyst': 5,
                'temperature': 175, 'pressure': 2.5, 'flow_rate': 200,
                'steam': 150, 'electricity': 80, 'cooling_water': 500
            }
            
            for var, default_val in default_values.items():
                if var not in input_conditions:
                    input_conditions[var] = default_val
            
            predictions = self.predict_quality(input_conditions)
            
            if "error" in predictions:
                return 1e6  # 오류 시 큰 값 반환
            
            # 비용 최소화
            cost = predictions.get('total_cost', 1e6)
            
            # 품질 제약 조건 페널티
            penalty = 0
            for target in quality_targets:
                metric_value = predictions.get(target.metric, 0)
                if target.constraint_type == 'ge':
                    if metric_value < target.target_value:
                        penalty += target.weight * (target.target_value - metric_value) ** 2
                elif target.constraint_type == 'le':
                    if metric_value > target.target_value:
                        penalty += target.weight * (metric_value - target.target_value) ** 2
            
            return cost + penalty * 1000  # 페널티 가중치
        
        # 최적화 실행
        try:
            result = differential_evolution(
                objective_function,
                bounds_list,
                seed=42,
                maxiter=100,
                popsize=15
            )
            
            if result.success:
                # 최적 조건
                optimal_inputs = dict(zip(variables, result.x))
                
                # 최적 조건에서의 예측값
                optimal_predictions = self.predict_quality(optimal_inputs)
                
                # 결과 포맷팅
                optimization_result = {
                    "success": True,
                    "optimal_inputs": optimal_inputs,
                    "expected_quality": optimal_predictions,
                    "objective_value": result.fun,
                    "optimization_info": {
                        "iterations": result.nit,
                        "function_evaluations": result.nfev
                    }
                }
                
                self.optimization_results = optimization_result
                return optimization_result
            
            else:
                return {
                    "success": False,
                    "error": "최적화 실패",
                    "message": result.message
                }
        
        except Exception as e:
            logger.error(f"최적화 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_context_data(self) -> Dict[str, Any]:
        """Context Engineering용 데이터 반환"""
        return self.history_learner.get_context_engineering_data()
    
    def calculate_cost_savings(self, 
                              baseline_inputs: Dict[str, float],
                              optimized_inputs: Dict[str, float]) -> Dict[str, float]:
        """비용 절감 효과 계산"""
        baseline_pred = self.predict_quality(baseline_inputs)
        optimized_pred = self.predict_quality(optimized_inputs)
        
        if "error" in baseline_pred or "error" in optimized_pred:
            return {"error": "예측 실패"}
        
        baseline_cost = baseline_pred['total_cost']
        optimized_cost = optimized_pred['total_cost']
        
        savings = {
            "baseline_cost": baseline_cost,
            "optimized_cost": optimized_cost,
            "absolute_savings": baseline_cost - optimized_cost,
            "percentage_savings": ((baseline_cost - optimized_cost) / baseline_cost) * 100,
            "monthly_savings": (baseline_cost - optimized_cost) * 24 * 30 / 10000,  # 만원 단위
            "annual_savings": (baseline_cost - optimized_cost) * 24 * 365 / 10000   # 만원 단위
        }
        
        return savings 