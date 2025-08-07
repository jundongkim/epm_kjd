"""
DX-AI Manufacturing Copilot - 고급 최적화 시스템

Scipy Optimize, Pyomo, scikit-optimize를 활용한 고급 최적화 알고리즘
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional, Callable
import warnings
warnings.filterwarnings('ignore')

# 최적화 라이브러리
from scipy.optimize import minimize, differential_evolution, dual_annealing
from scipy.stats import norm
from skopt import gp_minimize, forest_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args

# Pyomo 최적화 (조건부 import)
try:
    import pyomo.environ as pyo
    from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
    PYOMO_AVAILABLE = True
except ImportError:
    PYOMO_AVAILABLE = False
    print("Warning: Pyomo not available. Some optimization features will be limited.")

# 프로젝트 내부 모듈
from .cost_optimization_engine import CostOptimizationEngine, QualityTarget, OptimizationConstraint
import logging

logger = logging.getLogger(__name__)


class AdvancedOptimizationEngine:
    """고급 최적화 엔진"""
    
    def __init__(self, cost_engine: CostOptimizationEngine):
        self.cost_engine = cost_engine
        self.optimization_history = []
        self.pareto_front = []
        
    def bayesian_optimization(self, 
                            quality_targets: List[QualityTarget],
                            bounds: Dict[str, Tuple[float, float]],
                            n_calls: int = 50,
                            acquisition_function: str = 'EI') -> Dict[str, Any]:
        """베이지안 최적화"""
        
        # 탐색 공간 정의
        dimensions = []
        var_names = []
        for var_name, (low, high) in bounds.items():
            dimensions.append(Real(low, high, name=var_name))
            var_names.append(var_name)
        
        # 목적 함수 정의
        @use_named_args(dimensions)
        def objective(**kwargs):
            # 입력 조건 설정
            input_conditions = {}
            for var_name in var_names:
                input_conditions[var_name] = kwargs[var_name]
            
            # 기본값 설정
            default_values = {
                'material_a': 100, 'material_b': 50, 'catalyst': 5,
                'temperature': 175, 'pressure': 2.5, 'flow_rate': 200,
                'steam': 150, 'electricity': 80, 'cooling_water': 500
            }
            
            for var, default_val in default_values.items():
                if var not in input_conditions:
                    input_conditions[var] = default_val
            
            # 품질 예측
            predictions = self.cost_engine.predict_quality(input_conditions)
            
            if "error" in predictions:
                return 1e6
            
            # 목적 함수 계산 (비용 최소화 + 품질 제약 페널티)
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
            
            return cost + penalty * 1000
        
        # 베이지안 최적화 실행
        try:
            # 사용자 친화적 이름을 scikit-optimize 이름으로 매핑
            acq_func_mapping = {
                'Expected Improvement': 'EI',
                'Upper Confidence Bound': 'LCB', 
                'Probability of Improvement': 'PI',
                'EI': 'EI',
                'PI': 'PI', 
                'LCB': 'LCB',
                'gp_hedge': 'gp_hedge',
                'MES': 'MES',
                'PVRS': 'PVRS',
                'EIps': 'EIps',
                'PIps': 'PIps'
            }
            
            # acquisition function 이름 변환
            mapped_acq_func = acq_func_mapping.get(acquisition_function, 'EI')
            
            if acquisition_function not in acq_func_mapping:
                logger.warning(f"알 수 없는 acquisition function '{acquisition_function}'. 기본값 'EI' 사용.")
                mapped_acq_func = 'EI'
            
            logger.info(f"베이지안 최적화 시작 - 획득 함수: {acquisition_function} → {mapped_acq_func}")
            
            result = gp_minimize(
                func=objective,
                dimensions=dimensions,
                n_calls=n_calls,
                n_initial_points=10,
                acq_func=mapped_acq_func,
                random_state=42
            )
            
            # 최적 조건 추출
            optimal_inputs = {}
            for i, var_name in enumerate(var_names):
                optimal_inputs[var_name] = result.x[i]
            
            # 최적 조건에서의 예측값
            optimal_predictions = self.cost_engine.predict_quality(optimal_inputs)
            
            return {
                "success": True,
                "method": "Bayesian Optimization",
                "optimal_inputs": optimal_inputs,
                "expected_quality": optimal_predictions,
                "objective_value": result.fun,
                "optimization_info": {
                    "n_calls": n_calls,
                    "func_vals": result.func_vals,
                    "convergence": result.func_vals[-10:] if len(result.func_vals) >= 10 else result.func_vals
                }
            }
            
        except Exception as e:
            logger.error(f"베이지안 최적화 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def multi_objective_optimization(self, 
                                   objectives: List[str],
                                   bounds: Dict[str, Tuple[float, float]],
                                   weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """다목적 최적화 (가중합 방법)"""
        
        if weights is None:
            weights = [1.0] * len(objectives)
        
        if len(weights) != len(objectives):
            raise ValueError("목적 함수와 가중치의 개수가 일치하지 않습니다.")
        
        # 목적 함수 정의
        def multi_objective_func(x):
            variables = list(bounds.keys())
            input_conditions = dict(zip(variables, x))
            
            # 기본값 설정
            default_values = {
                'material_a': 100, 'material_b': 50, 'catalyst': 5,
                'temperature': 175, 'pressure': 2.5, 'flow_rate': 200,
                'steam': 150, 'electricity': 80, 'cooling_water': 500
            }
            
            for var, default_val in default_values.items():
                if var not in input_conditions:
                    input_conditions[var] = default_val
            
            predictions = self.cost_engine.predict_quality(input_conditions)
            
            if "error" in predictions:
                return 1e6
            
            # 다목적 함수 계산
            total_objective = 0
            for i, obj in enumerate(objectives):
                if obj == 'minimize_cost':
                    total_objective += weights[i] * predictions['total_cost']
                elif obj == 'maximize_purity':
                    total_objective -= weights[i] * predictions['purity']  # 최대화를 위해 음수
                elif obj == 'maximize_yield':
                    total_objective -= weights[i] * predictions['yield']   # 최대화를 위해 음수
            
            return total_objective
        
        # 최적화 실행
        bounds_list = [bounds[var] for var in bounds.keys()]
        
        try:
            result = differential_evolution(
                multi_objective_func,
                bounds_list,
                seed=42,
                maxiter=200,
                popsize=20
            )
            
            if result.success:
                optimal_inputs = dict(zip(bounds.keys(), result.x))
                optimal_predictions = self.cost_engine.predict_quality(optimal_inputs)
                
                return {
                    "success": True,
                    "method": "Multi-Objective Optimization",
                    "optimal_inputs": optimal_inputs,
                    "expected_quality": optimal_predictions,
                    "objective_value": result.fun,
                    "objectives": objectives,
                    "weights": weights
                }
            else:
                return {"success": False, "error": result.message}
                
        except Exception as e:
            logger.error(f"다목적 최적화 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def robust_optimization(self, 
                          quality_targets: List[QualityTarget],
                          bounds: Dict[str, Tuple[float, float]],
                          uncertainty_level: float = 0.05) -> Dict[str, Any]:
        """로버스트 최적화 (불확실성 고려)"""
        
        def robust_objective(x):
            variables = list(bounds.keys())
            base_conditions = dict(zip(variables, x))
            
            # 기본값 설정
            default_values = {
                'material_a': 100, 'material_b': 50, 'catalyst': 5,
                'temperature': 175, 'pressure': 2.5, 'flow_rate': 200,
                'steam': 150, 'electricity': 80, 'cooling_water': 500
            }
            
            for var, default_val in default_values.items():
                if var not in base_conditions:
                    base_conditions[var] = default_val
            
            # 몬테카를로 시뮬레이션으로 불확실성 고려
            n_samples = 50
            outcomes = []
            
            for _ in range(n_samples):
                # 불확실성 추가
                uncertain_conditions = {}
                for var, value in base_conditions.items():
                    if var in variables:  # 최적화 변수만 불확실성 적용
                        noise = np.random.normal(0, uncertainty_level * value)
                        uncertain_conditions[var] = value + noise
                    else:
                        uncertain_conditions[var] = value
                
                predictions = self.cost_engine.predict_quality(uncertain_conditions)
                
                if "error" not in predictions:
                    outcomes.append(predictions)
            
            if not outcomes:
                return 1e6
            
            # 평균 비용 + 비용 변동성 페널티
            costs = [pred['total_cost'] for pred in outcomes]
            mean_cost = np.mean(costs)
            cost_std = np.std(costs)
            
            # 품질 제약 위반 페널티
            penalty = 0
            for target in quality_targets:
                violations = 0
                for pred in outcomes:
                    metric_value = pred.get(target.metric, 0)
                    if target.constraint_type == 'ge' and metric_value < target.target_value:
                        violations += 1
                    elif target.constraint_type == 'le' and metric_value > target.target_value:
                        violations += 1
                
                violation_rate = violations / len(outcomes)
                penalty += target.weight * violation_rate * 1000
            
            return mean_cost + 0.5 * cost_std + penalty
        
        # 로버스트 최적화 실행
        bounds_list = [bounds[var] for var in bounds.keys()]
        
        try:
            result = dual_annealing(
                robust_objective,
                bounds_list,
                seed=42,
                maxiter=300
            )
            
            if result.success:
                optimal_inputs = dict(zip(bounds.keys(), result.x))
                optimal_predictions = self.cost_engine.predict_quality(optimal_inputs)
                
                return {
                    "success": True,
                    "method": "Robust Optimization",
                    "optimal_inputs": optimal_inputs,
                    "expected_quality": optimal_predictions,
                    "objective_value": result.fun,
                    "uncertainty_level": uncertainty_level
                }
            else:
                return {"success": False, "error": result.message}
                
        except Exception as e:
            logger.error(f"로버스트 최적화 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def constraint_optimization_pyomo(self, 
                                    quality_targets: List[QualityTarget],
                                    constraints: List[OptimizationConstraint],
                                    bounds: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """Pyomo를 활용한 제약 최적화"""
        
        if not PYOMO_AVAILABLE:
            return {"success": False, "error": "Pyomo 라이브러리가 설치되지 않았습니다."}
        
        try:
            # 모델 생성
            model = pyo.ConcreteModel()
            
            # 변수 정의
            variables = list(bounds.keys())
            for var in variables:
                low, high = bounds[var]
                setattr(model, var, pyo.Var(bounds=(low, high), initialize=(low + high) / 2))
            
            # 목적 함수 정의 (비용 최소화 근사)
            def objective_rule(model):
                # 선형 근사 계수 (실제로는 ML 모델을 통해 계산해야 함)
                cost_coeffs = {
                    'material_a': 450,
                    'material_b': 720,
                    'catalyst': 18000,
                    'temperature': 10,
                    'pressure': 50,
                    'flow_rate': 5,
                    'steam': 50,
                    'electricity': 120,
                    'cooling_water': 5
                }
                
                total_cost = 0
                for var in variables:
                    if var in cost_coeffs:
                        total_cost += cost_coeffs[var] * getattr(model, var)
                
                return total_cost
            
            model.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
            
            # 제약 조건 정의
            def purity_constraint_rule(model):
                # 순도 제약 (선형 근사)
                purity_approx = (85 + 
                               0.1 * model.material_a + 
                               0.05 * model.material_b + 
                               0.5 * model.catalyst + 
                               0.02 * model.temperature + 
                               0.5 * model.pressure)
                return purity_approx >= 95.0
            
            model.purity_constraint = pyo.Constraint(rule=purity_constraint_rule)
            
            def yield_constraint_rule(model):
                # 수율 제약 (선형 근사)
                yield_approx = (75 + 
                              0.08 * model.material_a + 
                              0.12 * model.material_b + 
                              0.3 * model.catalyst + 
                              0.01 * model.temperature + 
                              0.2 * model.pressure)
                return yield_approx >= 85.0
            
            model.yield_constraint = pyo.Constraint(rule=yield_constraint_rule)
            
            # 솔버 실행
            solver = SolverFactory('ipopt')  # 기본 솔버
            if not solver.available():
                # 대체 솔버 시도
                solver = SolverFactory('glpk')
            
            if solver.available():
                result = solver.solve(model)
                
                if result.solver.status == SolverStatus.ok:
                    # 최적 해 추출
                    optimal_inputs = {}
                    for var in variables:
                        optimal_inputs[var] = pyo.value(getattr(model, var))
                    
                    # 실제 ML 모델로 예측
                    optimal_predictions = self.cost_engine.predict_quality(optimal_inputs)
                    
                    return {
                        "success": True,
                        "method": "Pyomo Constraint Optimization",
                        "optimal_inputs": optimal_inputs,
                        "expected_quality": optimal_predictions,
                        "solver_status": str(result.solver.status),
                        "termination_condition": str(result.solver.termination_condition)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"솔버 실패: {result.solver.status}"
                    }
            else:
                return {
                    "success": False,
                    "error": "사용 가능한 솔버가 없습니다."
                }
                
        except Exception as e:
            logger.error(f"Pyomo 최적화 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def sensitivity_analysis_advanced(self, 
                                    base_conditions: Dict[str, float],
                                    variables: List[str],
                                    variation_ranges: Dict[str, float] = None) -> Dict[str, Any]:
        """고급 민감도 분석"""
        
        if variation_ranges is None:
            variation_ranges = {var: 0.1 for var in variables}
        
        # 기본 민감도 분석
        basic_sensitivity = self.cost_engine.sensitivity_analysis(
            base_conditions, variables, variation_ranges.get('default', 0.1)
        )
        
        # 교호작용 효과 분석
        interaction_effects = {}
        for i, var1 in enumerate(variables):
            for j, var2 in enumerate(variables):
                if i < j:  # 중복 방지
                    interaction_key = f"{var1}_x_{var2}"
                    
                    # 기본 조건
                    base_pred = self.cost_engine.predict_quality(base_conditions)
                    
                    # 두 변수 모두 증가
                    both_up = base_conditions.copy()
                    both_up[var1] += base_conditions[var1] * variation_ranges.get(var1, 0.1)
                    both_up[var2] += base_conditions[var2] * variation_ranges.get(var2, 0.1)
                    both_up_pred = self.cost_engine.predict_quality(both_up)
                    
                    # 첫 번째 변수만 증가
                    var1_up = base_conditions.copy()
                    var1_up[var1] += base_conditions[var1] * variation_ranges.get(var1, 0.1)
                    var1_up_pred = self.cost_engine.predict_quality(var1_up)
                    
                    # 두 번째 변수만 증가
                    var2_up = base_conditions.copy()
                    var2_up[var2] += base_conditions[var2] * variation_ranges.get(var2, 0.1)
                    var2_up_pred = self.cost_engine.predict_quality(var2_up)
                    
                    # 교호작용 효과 계산
                    if ("error" not in base_pred and "error" not in both_up_pred and 
                        "error" not in var1_up_pred and "error" not in var2_up_pred):
                        
                        interaction_effect = (
                            both_up_pred['total_cost'] - base_pred['total_cost'] -
                            (var1_up_pred['total_cost'] - base_pred['total_cost']) -
                            (var2_up_pred['total_cost'] - base_pred['total_cost'])
                        )
                        
                        interaction_effects[interaction_key] = interaction_effect
        
        # 비선형 효과 분석
        nonlinear_effects = {}
        for var in variables:
            var_range = variation_ranges.get(var, 0.1)
            base_value = base_conditions[var]
            
            # 다양한 변화량에서 효과 측정
            deltas = [0.05, 0.1, 0.2, 0.3]
            effects = []
            
            for delta in deltas:
                up_condition = base_conditions.copy()
                up_condition[var] = base_value * (1 + delta)
                up_pred = self.cost_engine.predict_quality(up_condition)
                
                down_condition = base_conditions.copy()
                down_condition[var] = base_value * (1 - delta)
                down_pred = self.cost_engine.predict_quality(down_condition)
                
                base_pred = self.cost_engine.predict_quality(base_conditions)
                
                if ("error" not in up_pred and "error" not in down_pred and 
                    "error" not in base_pred):
                    effect = (up_pred['total_cost'] - down_pred['total_cost']) / (2 * delta * base_value)
                    effects.append(effect)
            
            # 비선형성 측정 (효과의 변화율)
            if len(effects) > 1:
                nonlinearity = np.std(effects) / np.mean(np.abs(effects)) if np.mean(np.abs(effects)) > 0 else 0
                nonlinear_effects[var] = {
                    "nonlinearity_index": nonlinearity,
                    "effects_by_delta": dict(zip(deltas, effects))
                }
        
        return {
            "basic_sensitivity": basic_sensitivity,
            "interaction_effects": interaction_effects,
            "nonlinear_effects": nonlinear_effects,
            "analysis_summary": {
                "most_sensitive_variable": max(basic_sensitivity.keys(), 
                                             key=lambda x: abs(basic_sensitivity[x].get('total_cost', 0))),
                "strongest_interaction": max(interaction_effects.keys(), 
                                           key=lambda x: abs(interaction_effects[x])) if interaction_effects else None,
                "most_nonlinear_variable": max(nonlinear_effects.keys(), 
                                             key=lambda x: nonlinear_effects[x]['nonlinearity_index']) if nonlinear_effects else None
            }
        }
    
    def optimization_comparison(self, 
                              quality_targets: List[QualityTarget],
                              constraints: List[OptimizationConstraint],
                              bounds: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """다양한 최적화 방법 비교"""
        
        results = {}
        
        # 1. 기본 최적화 (Differential Evolution)
        try:
            basic_result = self.cost_engine.optimize_inputs(quality_targets, constraints, bounds)
            results["differential_evolution"] = basic_result
        except Exception as e:
            results["differential_evolution"] = {"success": False, "error": str(e)}
        
        # 2. 베이지안 최적화
        try:
            bayes_result = self.bayesian_optimization(quality_targets, bounds, n_calls=30)
            results["bayesian_optimization"] = bayes_result
        except Exception as e:
            results["bayesian_optimization"] = {"success": False, "error": str(e)}
        
        # 3. 로버스트 최적화
        try:
            robust_result = self.robust_optimization(quality_targets, bounds)
            results["robust_optimization"] = robust_result
        except Exception as e:
            results["robust_optimization"] = {"success": False, "error": str(e)}
        
        # 4. Pyomo 제약 최적화
        try:
            pyomo_result = self.constraint_optimization_pyomo(quality_targets, constraints, bounds)
            results["pyomo_optimization"] = pyomo_result
        except Exception as e:
            results["pyomo_optimization"] = {"success": False, "error": str(e)}
        
        # 결과 비교 분석
        successful_methods = {k: v for k, v in results.items() if v.get("success", False)}
        
        if successful_methods:
            comparison = {
                "method_count": len(successful_methods),
                "best_method": min(successful_methods.items(), 
                                 key=lambda x: x[1].get("objective_value", float('inf')))[0],
                "objective_values": {k: v.get("objective_value", float('inf')) 
                                   for k, v in successful_methods.items()},
                "average_objective": np.mean([v.get("objective_value", float('inf')) 
                                            for v in successful_methods.values()])
            }
            results["comparison"] = comparison
        
        return results 