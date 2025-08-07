"""
DX-AI Manufacturing Copilot - 원가 관리 엔진

원가 최적화, 품질 예측, 시나리오 분석 등의 핵심 비즈니스 로직을 담당합니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

from src.copilot.cost_optimization_engine import CostOptimizationEngine, QualityTarget
from src.copilot.advanced_optimization import AdvancedOptimizationEngine


class CostManagementEngine:
    """원가 관리 핵심 엔진"""
    
    def __init__(self):
        self.cost_optimization_engine: Optional[CostOptimizationEngine] = None
        self.advanced_optimization_engine: Optional[AdvancedOptimizationEngine] = None
        self.is_initialized = False
    
    def initialize(self, data_path: Optional[str] = None) -> Dict[str, Any]:
        """엔진 초기화"""
        try:
            # 기본 최적화 엔진 초기화
            self.cost_optimization_engine = CostOptimizationEngine()
            
            # 데이터 경로 설정
            if data_path is None and "cost_data_filepath" in st.session_state:
                data_path = st.session_state.cost_data_filepath
            
            # 엔진 초기화
            init_result = self.cost_optimization_engine.initialize(data_path)
            
            if not init_result["success"]:
                return init_result
            
            # 고급 최적화 엔진 초기화
            self.advanced_optimization_engine = AdvancedOptimizationEngine(
                self.cost_optimization_engine
            )
            

            
            self.is_initialized = True
            return {"success": True, "message": "엔진 초기화 완료"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_optimization(
        self, 
        method: str,
        quality_targets: List[QualityTarget],
        optimization_bounds: Dict[str, tuple]
    ) -> Dict[str, Any]:
        """최적화 실행"""
        if not self.is_initialized:
            return {"success": False, "error": "엔진이 초기화되지 않았습니다"}
        
        try:
            if method == "Differential Evolution":
                result = self.cost_optimization_engine.optimize_inputs(
                    quality_targets, [], optimization_bounds
                )
            elif method == "Bayesian Optimization":
                result = self.advanced_optimization_engine.bayesian_optimization(
                    quality_targets, optimization_bounds, n_calls=30
                )
            elif method == "Robust Optimization":
                result = self.advanced_optimization_engine.robust_optimization(
                    quality_targets, optimization_bounds
                )
            elif method == "Multi-Objective":
                result = self.advanced_optimization_engine.multi_objective_optimization(
                    ["minimize_cost", "maximize_purity", "maximize_yield"], 
                    optimization_bounds,
                    weights=[0.5, 0.3, 0.2]
                )
            elif method == "Method Comparison":
                result = self.advanced_optimization_engine.optimization_comparison(
                    quality_targets, [], optimization_bounds
                )
            else:
                return {"success": False, "error": f"지원하지 않는 최적화 방법: {method}"}
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_sensitivity_analysis(
        self,
        analysis_type: str,
        base_conditions: Dict[str, float],
        sensitivity_vars: List[str],
        variation_range: float
    ) -> Dict[str, Any]:
        """민감도 분석 실행"""
        if not self.is_initialized:
            return {"success": False, "error": "엔진이 초기화되지 않았습니다"}
        
        try:
            if analysis_type == "기본 민감도 분석":
                result = self.cost_optimization_engine.sensitivity_analysis(
                    base_conditions, sensitivity_vars, variation_range
                )
                return {"success": True, "result": result, "type": "basic"}
                
            elif analysis_type in ["고급 민감도 분석", "교호작용 분석"]:
                var_ranges = {var: variation_range for var in sensitivity_vars}
                result = self.advanced_optimization_engine.sensitivity_analysis_advanced(
                    base_conditions, sensitivity_vars, var_ranges
                )
                return {"success": True, "result": result, "type": "advanced"}
            
            else:
                return {"success": False, "error": f"지원하지 않는 분석 유형: {analysis_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def predict_quality(self, inputs: Dict[str, float]) -> Dict[str, Any]:
        """품질 예측"""
        if not self.is_initialized:
            return {"error": "엔진이 초기화되지 않았습니다"}
        
        try:
            return self.cost_optimization_engine.predict_quality(inputs)
        except Exception as e:
            return {"error": str(e)}
    
    def run_scenario_analysis(
        self, 
        base_inputs: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """시나리오 분석 실행"""
        if not self.is_initialized:
            return []
        
        try:
            scenarios = [
                {"name": "현재 조건", "multiplier": 1.0},
                {"name": "절약 모드", "multiplier": 0.9},
                {"name": "품질 우선", "multiplier": 1.1},
                {"name": "균형 모드", "multiplier": 1.05}
            ]
            
            scenario_results = []
            
            for scenario in scenarios:
                scenario_inputs = base_inputs.copy()
                mult = scenario["multiplier"]
                
                # 일부 변수에 승수 적용
                scenario_inputs["material_a"] *= mult
                scenario_inputs["material_b"] *= mult
                scenario_inputs["catalyst"] *= mult
                
                pred = self.predict_quality(scenario_inputs)
                
                if "error" not in pred:
                    scenario_results.append({
                        "시나리오": scenario["name"],
                        "순도 (%)": pred.get('purity', 0),
                        "수율 (%)": pred.get('yield', 0),
                        "총 비용 (원/h)": pred.get('total_cost', 0)
                    })
            
            return scenario_results
            
        except Exception as e:
            print(f"시나리오 분석 오류: {e}")
            return []
    
    def calculate_cost_savings(
        self,
        baseline_inputs: Dict[str, float],
        optimal_inputs: Dict[str, float]
    ) -> Dict[str, Any]:
        """비용 절감 효과 계산"""
        if not self.is_initialized:
            return {"error": "엔진이 초기화되지 않았습니다"}
        
        try:
            return self.cost_optimization_engine.calculate_cost_savings(
                baseline_inputs, optimal_inputs
            )
        except Exception as e:
            return {"error": str(e)}
    
    def get_context_data(self) -> Dict[str, Any]:
        """컨텍스트 데이터 조회"""
        if not self.is_initialized:
            return {}
        
        try:
            return self.cost_optimization_engine.get_context_data()
        except Exception as e:
            print(f"컨텍스트 데이터 조회 오류: {e}")
            return {}
    
    def generate_analysis_report(self) -> Dict[str, Any]:
        """AI 분석 보고서 생성"""
        if not self.is_initialized:
            return {"error": "엔진이 초기화되지 않았습니다"}
        
        try:
            context_data = self.get_context_data()
            
            if not context_data:
                return {"error": "분석할 데이터가 없습니다"}
            
            report = {
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "cost_analysis": {},
                "production_analysis": {},
                "recommendations": []
            }
            
            # 원가 현황 분석
            cost_breakdown = context_data.get("cost_breakdown", [])
            if cost_breakdown:
                total_cost = sum(item["금액(만원)"] for item in cost_breakdown)
                material_cost = next((item["금액(만원)"] for item in cost_breakdown if item["항목"] == "원료비"), 0)
                material_ratio = (material_cost / total_cost) * 100 if total_cost > 0 else 0
                
                report["cost_analysis"] = {
                    "total_cost": total_cost,
                    "material_ratio": material_ratio,
                    "cost_structure": "원료비 중심" if material_ratio > 70 else "균형형"
                }
            
            # 생산 이력 분석
            production_history = context_data.get("production_history", [])
            if production_history:
                avg_purity = np.mean([lot['purity'] for lot in production_history])
                avg_yield = np.mean([lot['yield'] for lot in production_history])
                
                report["production_analysis"] = {
                    "avg_purity": avg_purity,
                    "avg_yield": avg_yield,
                    "purity_status": "우수" if avg_purity >= 95 else "보통" if avg_purity >= 90 else "개선 필요",
                    "yield_status": "우수" if avg_yield >= 85 else "보통" if avg_yield >= 80 else "개선 필요"
                }
            
            # 최적화 제안
            recommendations = []
            material_ratio = report["cost_analysis"].get("material_ratio", 0)
            avg_purity = report["production_analysis"].get("avg_purity", 100)
            avg_yield = report["production_analysis"].get("avg_yield", 100)
            
            if material_ratio > 80:
                recommendations.append("원료비 절감을 위한 투입량 최적화 검토")
            
            if avg_purity < 95:
                recommendations.append("순도 개선을 위한 반응 조건 최적화")
            
            if avg_yield < 85:
                recommendations.append("수율 향상을 위한 촉매 효율 개선")
            
            if not recommendations:
                recommendations.append("현재 운전 조건 유지 및 지속적 모니터링")
            
            report["recommendations"] = recommendations
            
            return report
            
        except Exception as e:
            return {"error": str(e)}
    
    def reset(self):
        """엔진 리셋"""
        self.cost_optimization_engine = None
        self.advanced_optimization_engine = None
        self.is_initialized = False 