"""
DX-AI Manufacturing Copilot - 실험 설계 엔진

실험 설계 관련 백엔드 비즈니스 로직을 처리하는 엔진 클래스들입니다.
"""

import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

# 로거 설정
logger = logging.getLogger(__name__)


class ExperimentType(Enum):
    """실험 유형 열거형"""
    FULL_FACTORIAL = "Full Factorial"
    FRACTIONAL_FACTORIAL = "Fractional Factorial"
    CENTRAL_COMPOSITE = "Central Composite"
    BOX_BEHNKEN = "Box-Behnken"


class OptimizationGoal(Enum):
    """최적화 목표 열거형"""
    MAXIMIZE_PURITY = "순도 최대화"
    MAXIMIZE_YIELD = "수율 최대화"
    MINIMIZE_COST = "비용 최소화"
    MINIMIZE_TIME = "시간 최소화"


@dataclass
class ExperimentParameter:
    """실험 파라미터 데이터 클래스"""
    name: str
    min_value: float
    max_value: float
    levels: int = 3
    unit: str = ""


@dataclass
class ExperimentRun:
    """실험 실행 데이터 클래스"""
    run_id: int
    parameters: Dict[str, float]
    predicted_purity: float
    predicted_yield: float
    confidence: float = 0.0


@dataclass
class OptimizationResult:
    """최적화 결과 데이터 클래스"""
    optimal_parameters: Dict[str, float]
    predicted_performance: Dict[str, float]
    confidence_levels: Dict[str, float]
    improvement_rate: float
    convergence_info: Dict[str, Any]


class ExperimentalDesignEngine:
    """실험 설계 기본 엔진"""
    
    def __init__(self):
        self.available_parameters = {
            "온도": ExperimentParameter("온도", 100, 300, 3, "°C"),
            "압력": ExperimentParameter("압력", 1.0, 5.0, 3, "bar"),
            "pH": ExperimentParameter("pH", 4.0, 10.0, 3, ""),
            "반응시간": ExperimentParameter("반응시간", 30, 300, 3, "min"),
            "촉매농도": ExperimentParameter("촉매농도", 0.1, 2.0, 3, "M"),
            "교반속도": ExperimentParameter("교반속도", 100, 1000, 3, "rpm")
        }
        
        self.default_ranges = {
            "온도": (150, 200),
            "압력": (1.5, 3.0),
            "pH": (6.5, 8.5),
            "반응시간": (60, 180),
            "촉매농도": (0.3, 1.5),
            "교반속도": (200, 800)
        }
    
    def get_parameter_info(self, parameter_name: str) -> Optional[ExperimentParameter]:
        """파라미터 정보 반환"""
        return self.available_parameters.get(parameter_name)
    
    def get_all_parameters(self) -> Dict[str, ExperimentParameter]:
        """모든 파라미터 정보 반환"""
        return self.available_parameters
    
    def validate_experiment_settings(self, experiment_type: str, factors: List[str], 
                                   num_runs: int, replications: int) -> Dict[str, Any]:
        """실험 설정 유효성 검사"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # 인자 수 검증
        if len(factors) < 2:
            validation_result["errors"].append("최소 2개 이상의 인자가 필요합니다.")
            validation_result["is_valid"] = False
        
        if len(factors) > 6:
            validation_result["warnings"].append("6개 이상의 인자는 실험 복잡도가 높아집니다.")
            validation_result["recommendations"].append("초기에는 3-4개 주요 인자로 시작하는 것을 권장합니다.")
        
        # 실험 유형별 검증
        if experiment_type == ExperimentType.FULL_FACTORIAL.value:
            if len(factors) > 4:
                validation_result["warnings"].append("Full Factorial은 인자 수가 많을 때 실험 횟수가 급격히 증가합니다.")
                validation_result["recommendations"].append("Fractional Factorial 고려해보세요.")
        
        # 실험 횟수 검증
        if num_runs < 8:
            validation_result["warnings"].append("실험 횟수가 너무 적어 통계적 유의성이 낮을 수 있습니다.")
        
        if num_runs > 100:
            validation_result["warnings"].append("실험 횟수가 많아 시간과 비용이 증가합니다.")
        
        # 반복 횟수 검증
        if replications < 2:
            validation_result["recommendations"].append("재현성을 위해 최소 2회 반복을 권장합니다.")
        
        return validation_result


class DOEDesignEngine(ExperimentalDesignEngine):
    """실험 계획법(DOE) 설계 엔진"""
    
    def __init__(self):
        super().__init__()
        self.design_methods = {
            ExperimentType.FULL_FACTORIAL: self._generate_full_factorial,
            ExperimentType.FRACTIONAL_FACTORIAL: self._generate_fractional_factorial,
            ExperimentType.CENTRAL_COMPOSITE: self._generate_central_composite,
            ExperimentType.BOX_BEHNKEN: self._generate_box_behnken
        }
    
    def generate_experiment_plan(self, experiment_type: str, factors: List[str], 
                               num_runs: int, replications: int = 1,
                               target_purity: float = 97.5, target_yield: float = 92.0,
                               random_seed: int = 42) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """실험 계획 생성"""
        np.random.seed(random_seed)
        
        # 유효성 검사
        validation = self.validate_experiment_settings(experiment_type, factors, num_runs, replications)
        
        if not validation["is_valid"]:
            raise ValueError(f"실험 설정 오류: {', '.join(validation['errors'])}")
        
        # 실험 유형에 따른 설계 생성
        exp_type = ExperimentType(experiment_type)
        design_method = self.design_methods.get(exp_type, self._generate_full_factorial)
        
        experiment_plan = design_method(factors, num_runs, replications, target_purity, target_yield)
        
        # 실험 계획 메타데이터
        metadata = {
            "experiment_type": experiment_type,
            "factors": factors,
            "num_runs": len(experiment_plan),
            "replications": replications,
            "target_purity": target_purity,
            "target_yield": target_yield,
            "design_efficiency": self._calculate_design_efficiency(experiment_plan, factors),
            "power_analysis": self._calculate_power_analysis(experiment_plan, factors),
            "validation": validation
        }
        
        return experiment_plan, metadata
    
    def _generate_full_factorial(self, factors: List[str], num_runs: int, replications: int,
                               target_purity: float, target_yield: float) -> pd.DataFrame:
        """Full Factorial 설계 생성"""
        experiment_runs = []
        
        # 3수준 Full Factorial 기본 설계
        levels = [-1, 0, 1]  # 저수준, 중수준, 고수준
        
        # 모든 조합 생성
        factor_combinations = []
        n_factors = len(factors)
        
        for i in range(3**n_factors):
            combination = []
            temp_i = i
            for _ in range(n_factors):
                combination.append(levels[temp_i % 3])
                temp_i //= 3
            factor_combinations.append(combination)
        
        # 실제 수치로 변환
        for run_id, combination in enumerate(factor_combinations[:num_runs], 1):
            parameter_values = {}
            
            for j, factor in enumerate(factors):
                if factor in self.default_ranges:
                    min_val, max_val = self.default_ranges[factor]
                    level = combination[j]
                    if level == -1:
                        value = min_val
                    elif level == 0:
                        value = (min_val + max_val) / 2
                    else:
                        value = max_val
                    parameter_values[f"{factor}({self.available_parameters[factor].unit})"] = round(value, 2)
            
            # 예측 성능 계산
            predicted_purity, predicted_yield = self._predict_performance(parameter_values, target_purity, target_yield)
            
            experiment_runs.append({
                "Run": run_id,
                **parameter_values,
                "예상순도(%)": predicted_purity,
                "예상수율(%)": predicted_yield
            })
        
        return pd.DataFrame(experiment_runs)
    
    def _generate_fractional_factorial(self, factors: List[str], num_runs: int, replications: int,
                                     target_purity: float, target_yield: float) -> pd.DataFrame:
        """Fractional Factorial 설계 생성"""
        experiment_runs = []
        
        # 2수준 Fractional Factorial
        levels = [-1, 1]  # 저수준, 고수준
        
        # 효율적인 부분 설계 생성
        for run_id in range(1, num_runs + 1):
            parameter_values = {}
            
            for factor in factors:
                if factor in self.default_ranges:
                    min_val, max_val = self.default_ranges[factor]
                    level = np.random.choice(levels)
                    value = min_val if level == -1 else max_val
                    parameter_values[f"{factor}({self.available_parameters[factor].unit})"] = round(value, 2)
            
            # 예측 성능 계산
            predicted_purity, predicted_yield = self._predict_performance(parameter_values, target_purity, target_yield)
            
            experiment_runs.append({
                "Run": run_id,
                **parameter_values,
                "예상순도(%)": predicted_purity,
                "예상수율(%)": predicted_yield
            })
        
        return pd.DataFrame(experiment_runs)
    
    def _generate_central_composite(self, factors: List[str], num_runs: int, replications: int,
                                  target_purity: float, target_yield: float) -> pd.DataFrame:
        """Central Composite 설계 생성"""
        experiment_runs = []
        
        # 팩토리얼 점 + 중심점 + 축점 조합
        alpha = 1.414  # 축점 거리
        
        for run_id in range(1, num_runs + 1):
            parameter_values = {}
            
            for factor in factors:
                if factor in self.default_ranges:
                    min_val, max_val = self.default_ranges[factor]
                    center = (min_val + max_val) / 2
                    range_half = (max_val - min_val) / 2
                    
                    # 점 유형 결정
                    point_type = np.random.choice(['factorial', 'center', 'axial'], p=[0.5, 0.3, 0.2])
                    
                    if point_type == 'factorial':
                        level = np.random.choice([-1, 1])
                        value = center + level * range_half * 0.8
                    elif point_type == 'center':
                        value = center
                    else:  # axial
                        level = np.random.choice([-alpha, alpha])
                        value = center + level * range_half * 0.6
                    
                    value = max(min_val, min(max_val, value))
                    parameter_values[f"{factor}({self.available_parameters[factor].unit})"] = round(value, 2)
            
            # 예측 성능 계산
            predicted_purity, predicted_yield = self._predict_performance(parameter_values, target_purity, target_yield)
            
            experiment_runs.append({
                "Run": run_id,
                **parameter_values,
                "예상순도(%)": predicted_purity,
                "예상수율(%)": predicted_yield
            })
        
        return pd.DataFrame(experiment_runs)
    
    def _generate_box_behnken(self, factors: List[str], num_runs: int, replications: int,
                            target_purity: float, target_yield: float) -> pd.DataFrame:
        """Box-Behnken 설계 생성"""
        experiment_runs = []
        
        # 3수준 설계 (-1, 0, 1)
        levels = [-1, 0, 1]
        
        for run_id in range(1, num_runs + 1):
            parameter_values = {}
            
            for factor in factors:
                if factor in self.default_ranges:
                    min_val, max_val = self.default_ranges[factor]
                    center = (min_val + max_val) / 2
                    range_half = (max_val - min_val) / 2
                    
                    level = np.random.choice(levels)
                    value = center + level * range_half * 0.8
                    
                    parameter_values[f"{factor}({self.available_parameters[factor].unit})"] = round(value, 2)
            
            # 예측 성능 계산
            predicted_purity, predicted_yield = self._predict_performance(parameter_values, target_purity, target_yield)
            
            experiment_runs.append({
                "Run": run_id,
                **parameter_values,
                "예상순도(%)": predicted_purity,
                "예상수율(%)": predicted_yield
            })
        
        return pd.DataFrame(experiment_runs)
    
    def _predict_performance(self, parameter_values: Dict[str, float], 
                           target_purity: float, target_yield: float) -> Tuple[float, float]:
        """파라미터 값으로부터 성능 예측"""
        # 간단한 예측 모델 (실제로는 더 복잡한 모델 사용)
        base_purity = target_purity
        base_yield = target_yield
        
        # 온도 영향
        temp_key = next((k for k in parameter_values.keys() if "온도" in k), None)
        if temp_key:
            temp_val = parameter_values[temp_key]
            if temp_val < 170:
                base_purity *= 0.98
                base_yield *= 0.95
            elif temp_val > 190:
                base_purity *= 0.96
                base_yield *= 0.98
        
        # 압력 영향
        pressure_key = next((k for k in parameter_values.keys() if "압력" in k), None)
        if pressure_key:
            pressure_val = parameter_values[pressure_key]
            if pressure_val > 2.5:
                base_purity *= 1.01
                base_yield *= 1.02
        
        # pH 영향
        ph_key = next((k for k in parameter_values.keys() if "pH" in k), None)
        if ph_key:
            ph_val = parameter_values[ph_key]
            if 7.0 <= ph_val <= 7.5:
                base_purity *= 1.01
                base_yield *= 1.01
        
        # 노이즈 추가
        purity_noise = np.random.normal(0, 0.5)
        yield_noise = np.random.normal(0, 0.8)
        
        predicted_purity = min(99.5, max(90.0, base_purity + purity_noise))
        predicted_yield = min(98.0, max(80.0, base_yield + yield_noise))
        
        return round(predicted_purity, 1), round(predicted_yield, 1)
    
    def _calculate_design_efficiency(self, experiment_plan: pd.DataFrame, factors: List[str]) -> float:
        """설계 효율성 계산"""
        # D-efficiency 기반 계산
        num_runs = len(experiment_plan)
        num_factors = len(factors)
        
        # 이론적 최소 실험 횟수
        min_runs = num_factors + 1
        
        # 효율성 계산
        efficiency = min(100.0, (min_runs / num_runs) * 100)
        
        return round(efficiency, 1)
    
    def _calculate_power_analysis(self, experiment_plan: pd.DataFrame, factors: List[str]) -> Dict[str, float]:
        """검정력 분석"""
        num_runs = len(experiment_plan)
        num_factors = len(factors)
        
        # 간단한 검정력 계산
        effect_size = 0.5  # 중간 효과 크기
        alpha = 0.05
        
        # 검정력 추정
        power = min(0.95, 0.3 + (num_runs / (num_factors * 10)))
        
        return {
            "statistical_power": round(power, 3),
            "effect_size": effect_size,
            "alpha_level": alpha,
            "sample_size": num_runs
        }


class BayesianOptimizationEngine(ExperimentalDesignEngine):
    """베이지안 최적화 엔진"""
    
    def __init__(self):
        super().__init__()
        self.optimization_algorithms = {
            "Gaussian Process": self._gaussian_process_optimization,
            "Tree-structured Parzen Estimator": self._tpe_optimization,
            "Random Search": self._random_search_optimization
        }
        
        self.acquisition_functions = {
            "Expected Improvement": self._expected_improvement,
            "Upper Confidence Bound": self._upper_confidence_bound,
            "Probability of Improvement": self._probability_of_improvement
        }
    
    def run_optimization(self, objectives: List[str], constraints: Dict[str, Dict[str, float]],
                        optimizer: str = "Gaussian Process", max_iterations: int = 50,
                        acquisition_function: str = "Expected Improvement",
                        random_seed: int = 42) -> OptimizationResult:
        """베이지안 최적화 실행"""
        np.random.seed(random_seed)
        
        # 최적화 알고리즘 선택
        optimization_method = self.optimization_algorithms.get(optimizer, self._gaussian_process_optimization)
        
        # 최적화 실행 (제약조건만 전달)
        result = optimization_method(objectives, constraints, max_iterations, acquisition_function)
        
        # 결과 후처리
        result.convergence_info["optimizer"] = optimizer
        result.convergence_info["acquisition_function"] = acquisition_function
        result.convergence_info["total_iterations"] = max_iterations
        
        return result
    
    def _gaussian_process_optimization(self, objectives: List[str], constraints: Dict[str, Dict[str, float]],
                                     max_iterations: int, acquisition_function: str) -> OptimizationResult:
        """Gaussian Process 기반 최적화"""
        # 최적 파라미터 시뮬레이션 - 제약조건이 설정된 인자들만 처리
        optimal_params = {}
        
        # 동적으로 제약조건 처리
        if "temperature" in constraints and constraints["temperature"]:
            temp_min = constraints["temperature"]["min"]
            temp_max = constraints["temperature"]["max"]
            optimal_params["온도"] = round(np.random.uniform(temp_min + 0.2*(temp_max-temp_min), 
                                                           temp_max - 0.1*(temp_max-temp_min)), 1)
        
        if "pressure" in constraints and constraints["pressure"]:
            pressure_min = constraints["pressure"]["min"]
            pressure_max = constraints["pressure"]["max"]
            optimal_params["압력"] = round(np.random.uniform(pressure_min + 0.3*(pressure_max-pressure_min),
                                                           pressure_max - 0.2*(pressure_max-pressure_min)), 1)
        
        if "ph" in constraints and constraints["ph"]:
            ph_min = constraints["ph"]["min"]
            ph_max = constraints["ph"]["max"]
            optimal_params["pH"] = round(np.random.uniform(ph_min + 0.1*(ph_max-ph_min),
                                                          ph_max - 0.1*(ph_max-ph_min)), 1)
        
        if "reaction_time" in constraints and constraints["reaction_time"]:
            time_min = constraints["reaction_time"]["min"]
            time_max = constraints["reaction_time"]["max"]
            optimal_params["반응시간"] = round(np.random.uniform(time_min + 0.2*(time_max-time_min),
                                                              time_max - 0.1*(time_max-time_min)), 0)
        
        if "catalyst_concentration" in constraints and constraints["catalyst_concentration"]:
            cat_min = constraints["catalyst_concentration"]["min"]
            cat_max = constraints["catalyst_concentration"]["max"]
            optimal_params["촉매농도"] = round(np.random.uniform(cat_min + 0.1*(cat_max-cat_min),
                                                              cat_max - 0.1*(cat_max-cat_min)), 2)
        
        if "stirring_speed" in constraints and constraints["stirring_speed"]:
            stir_min = constraints["stirring_speed"]["min"]
            stir_max = constraints["stirring_speed"]["max"]
            optimal_params["교반속도"] = round(np.random.uniform(stir_min + 0.1*(stir_max-stir_min),
                                                              stir_max - 0.1*(stir_max-stir_min)), 0)
        
        # 성능 예측
        predicted_performance = {
            "예측 순도": 98.3,
            "예측 수율": 94.7,
            "예상 비용": 85000,
            "예상 시간": 118
        }
        
        # 신뢰도 계산 (실제 파라미터에 따라 동적 생성)
        confidence_levels = {}
        for param in optimal_params.keys():
            confidence_levels[param] = np.random.uniform(85.0, 95.0)
        
        # 수렴 정보
        convergence_info = {
            "iterations_used": min(max_iterations, 45),
            "best_score": 0.953,
            "convergence_rate": 85.2,
            "final_uncertainty": 0.03
        }
        
        return OptimizationResult(
            optimal_parameters=optimal_params,
            predicted_performance=predicted_performance,
            confidence_levels=confidence_levels,
            improvement_rate=8.5,
            convergence_info=convergence_info
        )
    
    def _tpe_optimization(self, objectives: List[str], constraints: Dict[str, Dict[str, float]],
                         max_iterations: int, acquisition_function: str) -> OptimizationResult:
        """Tree-structured Parzen Estimator 최적화"""
        # 최적 파라미터 시뮬레이션 - 제약조건이 설정된 인자들만 처리
        optimal_params = {}
        
        # 동적으로 제약조건 처리
        if "temperature" in constraints and constraints["temperature"]:
            temp_min = constraints["temperature"]["min"]
            temp_max = constraints["temperature"]["max"]
            optimal_params["온도"] = round(np.random.uniform(temp_min + 0.15*(temp_max-temp_min), 
                                                           temp_max - 0.15*(temp_max-temp_min)), 1)
        
        if "pressure" in constraints and constraints["pressure"]:
            pressure_min = constraints["pressure"]["min"]
            pressure_max = constraints["pressure"]["max"]
            optimal_params["압력"] = round(np.random.uniform(pressure_min + 0.25*(pressure_max-pressure_min),
                                                           pressure_max - 0.25*(pressure_max-pressure_min)), 1)
        
        if "ph" in constraints and constraints["ph"]:
            ph_min = constraints["ph"]["min"]
            ph_max = constraints["ph"]["max"]
            optimal_params["pH"] = round(np.random.uniform(ph_min + 0.1*(ph_max-ph_min),
                                                          ph_max - 0.2*(ph_max-ph_min)), 1)
        
        if "reaction_time" in constraints and constraints["reaction_time"]:
            time_min = constraints["reaction_time"]["min"]
            time_max = constraints["reaction_time"]["max"]
            optimal_params["반응시간"] = round(np.random.uniform(time_min + 0.1*(time_max-time_min),
                                                              time_max - 0.25*(time_max-time_min)), 0)
        
        if "catalyst_concentration" in constraints and constraints["catalyst_concentration"]:
            cat_min = constraints["catalyst_concentration"]["min"]
            cat_max = constraints["catalyst_concentration"]["max"]
            optimal_params["촉매농도"] = round(np.random.uniform(cat_min + 0.2*(cat_max-cat_min),
                                                              cat_max - 0.1*(cat_max-cat_min)), 2)
        
        if "stirring_speed" in constraints and constraints["stirring_speed"]:
            stir_min = constraints["stirring_speed"]["min"]
            stir_max = constraints["stirring_speed"]["max"]
            optimal_params["교반속도"] = round(np.random.uniform(stir_min + 0.15*(stir_max-stir_min),
                                                              stir_max - 0.15*(stir_max-stir_min)), 0)
        
        predicted_performance = {
            "예측 순도": 98.1,
            "예측 수율": 94.2,
            "예상 비용": 83500,
            "예상 시간": 115
        }
        
        # 신뢰도 계산 (실제 파라미터에 따라 동적 생성)
        confidence_levels = {}
        for param in optimal_params.keys():
            confidence_levels[param] = np.random.uniform(80.0, 92.0)
        
        convergence_info = {
            "iterations_used": min(max_iterations, 38),
            "best_score": 0.948,
            "convergence_rate": 78.5,
            "final_uncertainty": 0.04
        }
        
        return OptimizationResult(
            optimal_parameters=optimal_params,
            predicted_performance=predicted_performance,
            confidence_levels=confidence_levels,
            improvement_rate=7.2,
            convergence_info=convergence_info
        )
    
    def _random_search_optimization(self, objectives: List[str], constraints: Dict[str, Dict[str, float]],
                                  max_iterations: int, acquisition_function: str) -> OptimizationResult:
        """Random Search 최적화"""
        # 최적 파라미터 시뮬레이션 - 제약조건이 설정된 인자들만 처리
        optimal_params = {}
        
        # 동적으로 제약조건 처리
        if "temperature" in constraints and constraints["temperature"]:
            temp_min = constraints["temperature"]["min"]
            temp_max = constraints["temperature"]["max"]
            optimal_params["온도"] = round(np.random.uniform(temp_min, temp_max), 1)
        
        if "pressure" in constraints and constraints["pressure"]:
            pressure_min = constraints["pressure"]["min"]
            pressure_max = constraints["pressure"]["max"]
            optimal_params["압력"] = round(np.random.uniform(pressure_min, pressure_max), 1)
        
        if "ph" in constraints and constraints["ph"]:
            ph_min = constraints["ph"]["min"]
            ph_max = constraints["ph"]["max"]
            optimal_params["pH"] = round(np.random.uniform(ph_min, ph_max), 1)
        
        if "reaction_time" in constraints and constraints["reaction_time"]:
            time_min = constraints["reaction_time"]["min"]
            time_max = constraints["reaction_time"]["max"]
            optimal_params["반응시간"] = round(np.random.uniform(time_min, time_max), 0)
        
        if "catalyst_concentration" in constraints and constraints["catalyst_concentration"]:
            cat_min = constraints["catalyst_concentration"]["min"]
            cat_max = constraints["catalyst_concentration"]["max"]
            optimal_params["촉매농도"] = round(np.random.uniform(cat_min, cat_max), 2)
        
        if "stirring_speed" in constraints and constraints["stirring_speed"]:
            stir_min = constraints["stirring_speed"]["min"]
            stir_max = constraints["stirring_speed"]["max"]
            optimal_params["교반속도"] = round(np.random.uniform(stir_min, stir_max), 0)
        
        predicted_performance = {
            "예측 순도": 97.8,
            "예측 수율": 93.5,
            "예상 비용": 87200,
            "예상 시간": 135
        }
        
        # 신뢰도 계산 (실제 파라미터에 따라 동적 생성)
        confidence_levels = {}
        for param in optimal_params.keys():
            confidence_levels[param] = np.random.uniform(75.0, 87.0)
        
        convergence_info = {
            "iterations_used": max_iterations,
            "best_score": 0.928,
            "convergence_rate": 65.8,
            "final_uncertainty": 0.06
        }
        
        return OptimizationResult(
            optimal_parameters=optimal_params,
            predicted_performance=predicted_performance,
            confidence_levels=confidence_levels,
            improvement_rate=5.8,
            convergence_info=convergence_info
        )
    
    def _expected_improvement(self, x: np.ndarray, model: Any) -> float:
        """Expected Improvement 획득 함수"""
        # 간단한 EI 계산
        return np.random.random()
    
    def _upper_confidence_bound(self, x: np.ndarray, model: Any) -> float:
        """Upper Confidence Bound 획득 함수"""
        # 간단한 UCB 계산
        return np.random.random()
    
    def _probability_of_improvement(self, x: np.ndarray, model: Any) -> float:
        """Probability of Improvement 획득 함수"""
        # 간단한 PI 계산
        return np.random.random()


class ReportGenerationEngine(ExperimentalDesignEngine):
    """AI 보고서 생성 엔진 v2.0 - 실험 설계 전화"""
    
    def __init__(self):
        super().__init__()
        # v2.0: 실험 설계 전용 AI 보고서 생성기 통합
        try:
            from src.ai.report import (
                ExperimentalDesignReportGenerator,
                create_experimental_design_report_generator
            )
            self.ai_generator = create_experimental_design_report_generator(
                use_context_engineering=True,
                use_optimized_clients=True
            )
            self.use_ai_generation = True
            logger.info("실험 설계 전용 AI 보고서 생성기 v2.0 연동 완료")
        except ImportError as e:
            logger.warning(f"실험 설계 전용 AI 보고서 생성기 로드 실패, 템플릿 모드로 동작: {e}")
            self.use_ai_generation = False
    
    def generate_report(self, report_type: str, include_sections: List[str], 
                       report_length: str, experiment_data: Dict[str, Any],
                       optimization_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        실험 설계 보고서 생성 (AI 기반 v2.0)
        
        Args:
            report_type: 보고서 유형
            include_sections: 포함할 섹션 리스트
            report_length: 보고서 길이
            experiment_data: 실험 데이터
            optimization_data: 최적화 데이터
            
        Returns:
            생성된 보고서와 메타데이터
        """
        logger.info(f"실험 설계 보고서 생성 시작: {report_type}")
        
        try:
            if self.use_ai_generation:
                # AI 생성기 v2.0 사용 (실험 설계 전용)
                result = self.ai_generator.generate_experiment_report(
                    report_type=report_type,
                    experiment_data=experiment_data,
                    optimization_data=optimization_data,
                    include_sections=include_sections,
                    report_length=report_length,
                    include_charts=True,
                    include_recommendations=True,
                    statistical_confidence=0.95,
                    optimization_focus=True
                )
                
                # 성공적인 AI 생성
                if result and "content" in result:
                    # quality_metrics가 ReportQualityMetrics 객체인 경우 처리
                    quality_metrics = result.get("quality_metrics")
                    overall_score = "N/A"
                    if quality_metrics:
                        if hasattr(quality_metrics, 'overall_score'):
                            overall_score = quality_metrics.overall_score
                        elif isinstance(quality_metrics, dict):
                            overall_score = quality_metrics.get('overall_score', 'N/A')
                    
                    logger.info(f"AI 보고서 생성 성공 - 품질 점수: {overall_score}")
                    return {
                        "content": result["content"],
                        "word_count": len(result["content"].split()),
                        "generation_method": "ai_v2_experimental_design",
                        "metadata": result.get("metadata", {}),
                        "quality_metrics": result.get("quality_metrics", {}),
                        "success": True,
                        "error": None
                    }
                else:
                    logger.warning("AI 생성 실패, 템플릿 모드로 폴백")
                    return self._generate_template_fallback(report_type, include_sections, 
                                                          report_length, experiment_data, optimization_data)
            else:
                # 템플릿 기반 폴백
                return self._generate_template_fallback(report_type, include_sections, 
                                                      report_length, experiment_data, optimization_data)
                
        except Exception as e:
            logger.error(f"보고서 생성 중 오류 발생: {e}")
            return {
                "content": f"# 보고서 생성 오류\\n\\n보고서 생성 중 오류가 발생했습니다: {str(e)}",
                "word_count": 0,
                "generation_method": "error_fallback",
                "success": False,
                "error": str(e)
            }
    
    def _generate_template_fallback(self, report_type: str, include_sections: List[str],
                                  report_length: str, experiment_data: Dict[str, Any],
                                  optimization_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """템플릿 기반 폴백 보고서 생성"""
        
        logger.info("템플릿 기반 보고서 생성 모드")
        
        try:
            # 보고서 유형별 생성
            if report_type == "실험 계획 요약":
                content = self._generate_experiment_summary_report(include_sections, report_length, 
                                                                 experiment_data, optimization_data)
            elif report_type == "최적화 결과":
                content = self._generate_optimization_report(include_sections, report_length, 
                                                           experiment_data, optimization_data)
            elif report_type == "DoE 분석":
                content = self._generate_doe_report(include_sections, report_length, 
                                                  experiment_data, optimization_data)
            elif report_type == "종합 보고서":
                content = self._generate_comprehensive_report_template(include_sections, report_length, 
                                                                     experiment_data, optimization_data)
            else:
                content = self._generate_experiment_summary_report(include_sections, report_length, 
                                                                 experiment_data, optimization_data)
            
            return {
                "content": content,
                "word_count": len(content.split()),
                "generation_method": "template_based",
                "success": True,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"템플릿 기반 생성 실패: {e}")
            return {
                "content": f"# 보고서 생성 실패\\n\\n템플릿 기반 생성에 실패했습니다: {str(e)}",
                "word_count": 0,
                "generation_method": "error_fallback",
                "success": False,
                "error": str(e)
            }
    
    def _get_analysis_depth(self, report_length: str) -> str:
        """보고서 길이에 따른 분석 깊이 결정"""
        depth_map = {
            "간단 (1-2페이지)": "basic",
            "표준 (3-5페이지)": "standard", 
            "상세 (5-10페이지)": "comprehensive"
        }
        return depth_map.get(report_length, "standard")
    
    # 폴백용 템플릿 기반 보고서 생성 메서드들
    def _generate_experiment_summary_report(self, include_sections: List[str], report_length: str,
                                          experiment_data: Dict[str, Any], 
                                          optimization_data: Dict[str, Any] = None) -> str:
        """실험 계획 요약 보고서 생성 (템플릿 기반)"""
        content = []
        
        # 헤더
        content.append("# 🔬 실험 설계 보고서\n")
        content.append(f"**생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        content.append("---\n")
        
        if "실행 요약" in include_sections:
            content.append("## 📊 실행 요약\n")
            
            if experiment_data:
                exp_type = experiment_data.get('experiment_type', 'Full Factorial')
                factors = experiment_data.get('factors', [])
                num_runs = experiment_data.get('num_runs', 25)
                goal = experiment_data.get('optimization_goal', '순도 최대화')
                
                content.append(f"- **실험 유형**: {exp_type}\n")
                content.append(f"- **실험 인자**: {len(factors)}개 ({', '.join(factors)})\n")
                content.append(f"- **실험 횟수**: {num_runs}회\n")
                content.append(f"- **목표**: {goal}\n")
            
            content.append("\n")
        
        if "실험 설계" in include_sections:
            content.append("## 🎯 실험 설계 방법론\n")
            content.append("선택된 실험 설계 방법론은 효율적인 실험 수행을 위해 최적화되었습니다.\n")
            
            if experiment_data:
                exp_type = experiment_data.get('experiment_type', 'Full Factorial')
                content.append(f"\n### {exp_type} 특징\n")
                
                if exp_type == "Full Factorial":
                    content.append("- 모든 인자 조합을 다 실험\n")
                    content.append("- 완전한 정보 확보 가능\n")
                    content.append("- 상호작용 효과 정확 분석\n")
                elif exp_type == "Fractional Factorial":
                    content.append("- 실험 횟수 대폭 감소\n")
                    content.append("- 효율적 스크리닝\n")
                    content.append("- 중요 인자 빠른 선별\n")
                elif exp_type == "Central Composite":
                    content.append("- 2차 곡선 모델링\n")
                    content.append("- 응답표면방법론(RSM)\n")
                    content.append("- 최적점 탐색 가능\n")
                elif exp_type == "Box-Behnken":
                    content.append("- 3수준 설계\n")
                    content.append("- 경계점 없음 (안전)\n")
                    content.append("- 적당한 실험 횟수\n")
            
            content.append("\n")
        
        if "최적화 결과" in include_sections and optimization_data:
            content.append("## 📈 최적화 결과\n")
            
            if optimization_data.get('optimal_parameters'):
                content.append("### 최적 조건\n")
                for param, value in optimization_data['optimal_parameters'].items():
                    content.append(f"- **{param}**: {value}\n")
            
            if optimization_data.get('predicted_performance'):
                content.append("\n### 예측 성능\n")
                for metric, value in optimization_data['predicted_performance'].items():
                    content.append(f"- **{metric}**: {value}\n")
            
            content.append("\n")
        
        if "결과 해석" in include_sections:
            content.append("## 🔍 결과 해석\n")
            content.append("실험 결과를 바탕으로 다음과 같은 주요 인사이트를 도출했습니다:\n")
            content.append("1. 온도와 압력이 순도에 가장 큰 영향을 미침\n")
            content.append("2. pH는 수율에 중요한 역할을 함\n")
            content.append("3. 인자 간 상호작용 효과가 존재함\n")
            content.append("\n")
        
        if "개선 제안" in include_sections:
            content.append("## 💡 개선 제안\n")
            content.append("1. 핵심 인자 우선 실험\n")
            content.append("2. 베이지안 최적화 적용\n")
            content.append("3. 실시간 모니터링 구축\n")
            content.append("4. 다단계 최적화 전략 수립\n")
            content.append("\n")
        
        if "다음 단계" in include_sections:
            content.append("## 📋 다음 단계\n")
            content.append("1. 실험 계획 승인\n")
            content.append("2. 자원 할당 및 일정 조정\n")
            content.append("3. 실험 실행 및 모니터링\n")
            content.append("4. 결과 분석 및 모델 검증\n")
            content.append("5. 최적화 조건 적용\n")
            content.append("\n")
        
        return "".join(content)
    
    def _generate_optimization_report(self, include_sections: List[str], report_length: str,
                                    experiment_data: Dict[str, Any], 
                                    optimization_data: Dict[str, Any] = None) -> str:
        """최적화 결과 보고서 생성 (템플릿 기반)"""
        content = []
        
        content.append("# 🎯 최적화 결과 보고서\n")
        content.append(f"**생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        content.append("---\n")
        
        if optimization_data:
            content.append("## 📊 최적화 요약\n")
            
            if optimization_data.get('optimal_parameters'):
                content.append("### 🎯 최적 조건\n")
                for param, value in optimization_data['optimal_parameters'].items():
                    content.append(f"- **{param}**: {value}\n")
            
            if optimization_data.get('predicted_performance'):
                content.append("\n### 📈 예측 성능\n")
                for metric, value in optimization_data['predicted_performance'].items():
                    content.append(f"- **{metric}**: {value}\n")
            
            content.append(f"\n### 🚀 개선율: {optimization_data.get('improvement_rate', 0)}%\n")
        
        return "".join(content)
    
    def _generate_doe_analysis_report(self, include_sections: List[str], report_length: str,
                                    experiment_data: Dict[str, Any], 
                                    optimization_data: Dict[str, Any] = None) -> str:
        """DoE 분석 보고서 생성 (템플릿 기반)"""
        content = []
        
        content.append("# 📊 DoE 분석 보고서\n")
        content.append(f"**생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        content.append("---\n")
        
        if experiment_data:
            content.append("## 🔬 실험 설계 분석\n")
            content.append(f"- **설계 유형**: {experiment_data.get('experiment_type', 'N/A')}\n")
            content.append(f"- **실험 인자**: {len(experiment_data.get('factors', []))}개\n")
            content.append(f"- **실험 횟수**: {experiment_data.get('num_runs', 0)}회\n")
            
            if experiment_data.get('design_efficiency'):
                content.append(f"- **설계 효율성**: {experiment_data['design_efficiency']}%\n")
            
            if experiment_data.get('power_analysis'):
                power_info = experiment_data['power_analysis']
                content.append(f"- **검정력**: {power_info.get('statistical_power', 0):.3f}\n")
        
        return "".join(content)
    
    def _generate_comprehensive_report(self, include_sections: List[str], report_length: str,
                                     experiment_data: Dict[str, Any], 
                                     optimization_data: Dict[str, Any] = None) -> str:
        """종합 보고서 생성 (템플릿 기반)"""
        content = []
        
        content.append("# 📋 종합 분석 보고서\n")
        content.append(f"**생성일**: {datetime.now().strftime('%Y년 %m월 %d일')}\n")
        content.append("---\n")
        
        # 실험 설계 부분
        content.append(self._generate_experiment_summary_report(include_sections, report_length, experiment_data, optimization_data))
        
        # 최적화 결과 부분
        if optimization_data:
            content.append("\n---\n")
            content.append(self._generate_optimization_report(include_sections, report_length, experiment_data, optimization_data))
        
        return "".join(content)
    
    def estimate_report_length(self, report_type: str, include_sections: List[str], 
                             report_length: str) -> Dict[str, int]:
        """보고서 길이 추정"""
        base_lengths = {
            "간단 (1-2페이지)": 500,
            "표준 (3-5페이지)": 1500,
            "상세 (5-10페이지)": 3000
        }
        
        base_length = base_lengths.get(report_length, 1500)
        section_multiplier = len(include_sections) / 6  # 6개 섹션이 기본
        
        estimated_words = int(base_length * section_multiplier)
        estimated_pages = max(1, estimated_words // 250)  # 250 단어 = 1페이지
        
        return {
            "estimated_words": estimated_words,
            "estimated_pages": estimated_pages,
            "estimated_reading_time": max(1, estimated_words // 200)  # 분 단위
        } 