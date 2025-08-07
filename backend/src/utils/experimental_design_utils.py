"""
DX-AI Manufacturing Copilot - 실험 설계 유틸리티

실험 설계 관련 공통 유틸리티 함수들을 제공합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Union
import time


class ExperimentDesignAnalyzer:
    """실험 설계 분석 유틸리티"""
    
    @staticmethod
    def analyze_experiment_plan(experiment_plan: pd.DataFrame, factors: List[str]) -> Dict[str, Any]:
        """실험 계획 분석"""
        if experiment_plan.empty:
            return {"error": "실험 계획이 비어있습니다."}
        
        analysis = {
            "total_runs": len(experiment_plan),
            "factors_analyzed": len(factors),
            "factor_names": factors,
            "design_summary": {},
            "statistical_properties": {},
            "recommendations": []
        }
        
        # 각 인자별 분석
        for factor in factors:
            factor_columns = [col for col in experiment_plan.columns if factor in col]
            if factor_columns:
                factor_col = factor_columns[0]
                values = experiment_plan[factor_col].values
                
                analysis["design_summary"][factor] = {
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "unique_levels": len(np.unique(values))
                }
        
        # 통계적 특성 분석
        analysis["statistical_properties"] = {
            "runs_per_factor": analysis["total_runs"] / max(1, analysis["factors_analyzed"]),
            "design_resolution": ExperimentDesignAnalyzer._estimate_resolution(analysis["total_runs"], analysis["factors_analyzed"]),
            "power_estimate": ExperimentDesignAnalyzer._estimate_power(analysis["total_runs"], analysis["factors_analyzed"])
        }
        
        # 권장사항 생성
        analysis["recommendations"] = ExperimentDesignAnalyzer._generate_recommendations(analysis)
        
        return analysis
    
    @staticmethod
    def _estimate_resolution(num_runs: int, num_factors: int) -> str:
        """설계 해상도 추정"""
        if num_runs >= 2**num_factors:
            return "Full Resolution"
        elif num_runs >= 2**(num_factors-1):
            return "Resolution V"
        elif num_runs >= 2**(num_factors-2):
            return "Resolution IV"
        else:
            return "Resolution III"
    
    @staticmethod
    def _estimate_power(num_runs: int, num_factors: int) -> float:
        """검정력 추정"""
        # 간단한 검정력 추정 공식
        base_power = 0.5
        factor_effect = min(0.4, num_runs / (num_factors * 10))
        estimated_power = min(0.95, base_power + factor_effect)
        return round(estimated_power, 3)
    
    @staticmethod
    def _generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        total_runs = analysis["total_runs"]
        num_factors = analysis["factors_analyzed"]
        
        if total_runs < 8:
            recommendations.append("실험 횟수가 적습니다. 최소 8회 이상을 권장합니다.")
        
        if total_runs > 100:
            recommendations.append("실험 횟수가 많습니다. 효율성을 위해 스크리닝 실험을 고려해보세요.")
        
        if num_factors > 5:
            recommendations.append("인자 수가 많습니다. 주요 인자 선별 후 단계적 접근을 권장합니다.")
        
        runs_per_factor = total_runs / max(1, num_factors)
        if runs_per_factor < 3:
            recommendations.append("인자당 실험 횟수가 부족합니다. 통계적 유의성을 위해 더 많은 실험이 필요합니다.")
        
        return recommendations


class CorrelationAnalyzer:
    """상관관계 분석 유틸리티"""
    
    @staticmethod
    def get_correlation_strength(correlation_value: float) -> str:
        """상관계수 절댓값에 따른 강도 분류"""
        abs_corr = abs(correlation_value)
        if abs_corr >= 0.9:
            return "매우 강함"
        elif abs_corr >= 0.7:
            return "강함"
        elif abs_corr >= 0.5:
            return "보통"
        elif abs_corr >= 0.3:
            return "약함"
        else:
            return "매우 약함"
    
    @staticmethod
    def analyze_factor_correlations(experiment_plan: pd.DataFrame, factors: List[str]) -> Dict[str, Any]:
        """인자 간 상관관계 분석"""
        if experiment_plan.empty or len(factors) < 2:
            return {"error": "분석을 위한 데이터가 부족합니다."}
        
        # 인자 컬럼 찾기
        factor_columns = []
        for factor in factors:
            factor_cols = [col for col in experiment_plan.columns if factor in col and "예상" not in col]
            if factor_cols:
                factor_columns.append(factor_cols[0])
        
        if len(factor_columns) < 2:
            return {"error": "분석 가능한 인자가 부족합니다."}
        
        # 상관관계 계산
        correlation_data = experiment_plan[factor_columns].corr()
        
        # 결과 정리
        correlations = {}
        for i, factor1 in enumerate(factor_columns):
            for j, factor2 in enumerate(factor_columns):
                if i < j:  # 중복 제거
                    corr_value = correlation_data.loc[factor1, factor2]
                    correlations[f"{factor1} vs {factor2}"] = {
                        "correlation": round(corr_value, 3),
                        "strength": CorrelationAnalyzer.get_correlation_strength(corr_value),
                        "interpretation": CorrelationAnalyzer._interpret_correlation(corr_value)
                    }
        
        return {
            "correlation_matrix": correlation_data.to_dict(),
            "pairwise_correlations": correlations,
            "summary": CorrelationAnalyzer._summarize_correlations(correlations)
        }
    
    @staticmethod
    def _interpret_correlation(correlation_value: float) -> str:
        """상관관계 해석"""
        abs_corr = abs(correlation_value)
        
        if abs_corr >= 0.7:
            if correlation_value > 0:
                return "강한 양의 상관관계 - 한 변수가 증가하면 다른 변수도 크게 증가"
            else:
                return "강한 음의 상관관계 - 한 변수가 증가하면 다른 변수는 크게 감소"
        elif abs_corr >= 0.3:
            if correlation_value > 0:
                return "보통 양의 상관관계 - 한 변수가 증가하면 다른 변수도 어느 정도 증가"
            else:
                return "보통 음의 상관관계 - 한 변수가 증가하면 다른 변수는 어느 정도 감소"
        else:
            return "약한 상관관계 - 두 변수 간 선형 관계가 미약함"
    
    @staticmethod
    def _summarize_correlations(correlations: Dict[str, Dict]) -> Dict[str, Any]:
        """상관관계 요약"""
        if not correlations:
            return {"message": "분석 가능한 상관관계가 없습니다."}
        
        strong_correlations = [k for k, v in correlations.items() if abs(v["correlation"]) >= 0.7]
        moderate_correlations = [k for k, v in correlations.items() if 0.3 <= abs(v["correlation"]) < 0.7]
        weak_correlations = [k for k, v in correlations.items() if abs(v["correlation"]) < 0.3]
        
        return {
            "total_pairs": len(correlations),
            "strong_correlations": len(strong_correlations),
            "moderate_correlations": len(moderate_correlations),
            "weak_correlations": len(weak_correlations),
            "strong_pairs": strong_correlations,
            "concern_level": "높음" if len(strong_correlations) > 0 else "낮음" if len(moderate_correlations) == 0 else "보통"
        }


class OptimizationResultAnalyzer:
    """최적화 결과 분석 유틸리티"""
    
    @staticmethod
    def analyze_optimization_result(optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """최적화 결과 분석"""
        if not optimization_result:
            return {"error": "최적화 결과가 없습니다."}
        
        analysis = {
            "optimization_summary": {},
            "parameter_analysis": {},
            "performance_analysis": {},
            "confidence_analysis": {},
            "recommendations": []
        }
        
        # 최적화 요약
        analysis["optimization_summary"] = {
            "improvement_rate": optimization_result.get("improvement_rate", 0),
            "convergence_achieved": optimization_result.get("convergence_info", {}).get("convergence_rate", 0) > 80,
            "iterations_used": optimization_result.get("convergence_info", {}).get("iterations_used", 0),
            "final_score": optimization_result.get("convergence_info", {}).get("best_score", 0)
        }
        
        # 파라미터 분석
        optimal_params = optimization_result.get("optimal_parameters", {})
        if optimal_params:
            analysis["parameter_analysis"] = OptimizationResultAnalyzer._analyze_parameters(optimal_params)
        
        # 성능 분석
        performance = optimization_result.get("predicted_performance", {})
        if performance:
            analysis["performance_analysis"] = OptimizationResultAnalyzer._analyze_performance(performance)
        
        # 신뢰도 분석
        confidence = optimization_result.get("confidence_levels", {})
        if confidence:
            analysis["confidence_analysis"] = OptimizationResultAnalyzer._analyze_confidence(confidence)
        
        # 권장사항 생성
        analysis["recommendations"] = OptimizationResultAnalyzer._generate_optimization_recommendations(analysis)
        
        return analysis
    
    @staticmethod
    def _analyze_parameters(optimal_params: Dict[str, float]) -> Dict[str, Any]:
        """파라미터 분석"""
        analysis = {
            "parameter_count": len(optimal_params),
            "parameter_ranges": {},
            "critical_parameters": []
        }
        
        # 파라미터별 분석
        for param, value in optimal_params.items():
            if isinstance(value, (int, float)):
                analysis["parameter_ranges"][param] = {
                    "optimal_value": value,
                    "criticality": "높음" if param in ["온도", "압력", "pH"] else "보통"
                }
                
                if param in ["온도", "압력", "pH"]:
                    analysis["critical_parameters"].append(param)
        
        return analysis
    
    @staticmethod
    def _analyze_performance(performance: Dict[str, str]) -> Dict[str, Any]:
        """성능 분석"""
        analysis = {
            "metrics_count": len(performance),
            "performance_levels": {},
            "overall_grade": "B"
        }
        
        # 성능 지표 분석
        for metric, value in performance.items():
            if "순도" in metric:
                # 값이 이미 숫자인 경우와 문자열인 경우 모두 처리
                if isinstance(value, str):
                    purity_val = float(value.replace('%', ''))
                else:
                    purity_val = float(value)
                analysis["performance_levels"]["purity"] = {
                    "value": purity_val,
                    "grade": "A" if purity_val >= 98 else "B" if purity_val >= 95 else "C"
                }
            elif "수율" in metric:
                # 값이 이미 숫자인 경우와 문자열인 경우 모두 처리
                if isinstance(value, str):
                    yield_val = float(value.replace('%', ''))
                else:
                    yield_val = float(value)
                analysis["performance_levels"]["yield"] = {
                    "value": yield_val,
                    "grade": "A" if yield_val >= 94 else "B" if yield_val >= 90 else "C"
                }
        
        # 전체 등급 결정
        grades = [info["grade"] for info in analysis["performance_levels"].values()]
        if all(grade == "A" for grade in grades):
            analysis["overall_grade"] = "A"
        elif any(grade == "C" for grade in grades):
            analysis["overall_grade"] = "C"
        else:
            analysis["overall_grade"] = "B"
        
        return analysis
    
    @staticmethod
    def _analyze_confidence(confidence: Dict[str, float]) -> Dict[str, Any]:
        """신뢰도 분석"""
        confidence_values = list(confidence.values())
        
        analysis = {
            "average_confidence": round(np.mean(confidence_values), 1),
            "min_confidence": round(np.min(confidence_values), 1),
            "max_confidence": round(np.max(confidence_values), 1),
            "confidence_level": "높음" if np.mean(confidence_values) >= 90 else "보통" if np.mean(confidence_values) >= 80 else "낮음",
            "low_confidence_parameters": [param for param, conf in confidence.items() if conf < 85]
        }
        
        return analysis
    
    @staticmethod
    def _generate_optimization_recommendations(analysis: Dict[str, Any]) -> List[str]:
        """최적화 권장사항 생성"""
        recommendations = []
        
        # 수렴 분석
        if not analysis["optimization_summary"].get("convergence_achieved", False):
            recommendations.append("최적화가 완전히 수렴되지 않았습니다. 더 많은 반복 또는 다른 알고리즘을 시도해보세요.")
        
        # 성능 분석
        performance_grade = analysis.get("performance_analysis", {}).get("overall_grade", "B")
        if performance_grade == "C":
            recommendations.append("예측 성능이 목표에 미달합니다. 실험 설계를 재검토하거나 추가 최적화가 필요합니다.")
        
        # 신뢰도 분석
        conf_analysis = analysis.get("confidence_analysis", {})
        if conf_analysis.get("confidence_level") == "낮음":
            recommendations.append("파라미터 추정의 신뢰도가 낮습니다. 더 많은 데이터나 다른 모델을 고려해보세요.")
        
        if conf_analysis.get("low_confidence_parameters"):
            low_conf_params = conf_analysis["low_confidence_parameters"]
            recommendations.append(f"다음 파라미터들의 신뢰도가 낮습니다: {', '.join(low_conf_params)}")
        
        # 개선율 분석
        improvement_rate = analysis["optimization_summary"].get("improvement_rate", 0)
        if improvement_rate < 5:
            recommendations.append("개선율이 낮습니다. 더 넓은 탐색 공간이나 다른 접근법을 고려해보세요.")
        
        return recommendations


class ReportUtilities:
    """보고서 관련 유틸리티"""
    
    @staticmethod
    def estimate_reading_time(text: str) -> Dict[str, int]:
        """읽기 시간 추정"""
        word_count = len(text.split())
        
        return {
            "word_count": word_count,
            "estimated_minutes": max(1, word_count // 200),  # 분당 200단어 기준
            "page_count": max(1, word_count // 250)  # 페이지당 250단어 기준
        }
    
    @staticmethod
    def format_report_metadata(metadata: Dict[str, Any]) -> str:
        """보고서 메타데이터 포맷팅"""
        formatted = []
        
        formatted.append(f"**보고서 유형**: {metadata.get('report_type', 'N/A')}")
        formatted.append(f"**생성 시간**: {metadata.get('generation_time', 'N/A')}")
        formatted.append(f"**단어 수**: {metadata.get('word_count', 0):,}개")
        
        if metadata.get('sections_included'):
            sections = ', '.join(metadata['sections_included'])
            formatted.append(f"**포함 섹션**: {sections}")
        
        return '\n'.join(formatted)
    
    @staticmethod
    def generate_executive_summary(experiment_data: Dict[str, Any], 
                                 optimization_data: Dict[str, Any] = None) -> str:
        """경영진 요약 생성"""
        summary = []
        
        summary.append("## 📊 경영진 요약")
        summary.append("")
        
        if experiment_data:
            exp_type = experiment_data.get('experiment_type', 'N/A')
            factors = experiment_data.get('factors', [])
            num_runs = experiment_data.get('num_runs', 0)
            
            summary.append(f"**실험 개요**: {exp_type} 방법으로 {len(factors)}개 인자에 대해 {num_runs}회 실험 계획")
            
            if experiment_data.get('target_purity') and experiment_data.get('target_yield'):
                summary.append(f"**목표 성능**: 순도 {experiment_data['target_purity']}%, 수율 {experiment_data['target_yield']}%")
        
        if optimization_data:
            improvement_rate = optimization_data.get('improvement_rate', 0)
            summary.append(f"**최적화 결과**: {improvement_rate}% 성능 개선 예상")
            
            if optimization_data.get('predicted_performance'):
                perf = optimization_data['predicted_performance']
                summary.append(f"**예측 성능**: 순도 {perf.get('예측 순도', 'N/A')}, 수율 {perf.get('예측 수율', 'N/A')}")
        
        summary.append("")
        summary.append("**권장사항**: 제안된 최적 조건으로 파일럿 실험 진행")
        
        return '\n'.join(summary)
    
    @staticmethod
    def create_progress_summary(progress_data: Dict[str, Any]) -> str:
        """진행 상황 요약 생성"""
        progress = []
        
        progress.append("## 🚀 진행 상황")
        progress.append("")
        
        if progress_data.get('experiment_completed'):
            progress.append("✅ 실험 계획 완료")
        else:
            progress.append("⏳ 실험 계획 진행 중")
        
        if progress_data.get('optimization_completed'):
            progress.append("✅ 최적화 완료")
        else:
            progress.append("⏳ 최적화 진행 중")
        
        if progress_data.get('report_generated'):
            progress.append("✅ 보고서 생성 완료")
        else:
            progress.append("⏳ 보고서 생성 대기")
        
        return '\n'.join(progress)


class ValidationUtilities:
    """검증 관련 유틸리티"""
    
    @staticmethod
    def validate_experiment_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
        """실험 파라미터 검증"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # 필수 파라미터 확인
        required_params = ['experiment_type', 'factors', 'num_runs']
        for param in required_params:
            if param not in parameters or not parameters[param]:
                validation["errors"].append(f"필수 파라미터 '{param}'이 누락되었습니다.")
                validation["is_valid"] = False
        
        # 인자 수 검증
        if parameters.get('factors'):
            factor_count = len(parameters['factors'])
            if factor_count < 2:
                validation["errors"].append("최소 2개 이상의 인자가 필요합니다.")
                validation["is_valid"] = False
            elif factor_count > 6:
                validation["warnings"].append("6개 이상의 인자는 실험 복잡도를 높입니다.")
                validation["recommendations"].append("주요 인자부터 단계적으로 접근하세요.")
        
        # 실험 횟수 검증
        if parameters.get('num_runs'):
            num_runs = parameters['num_runs']
            if num_runs < 8:
                validation["warnings"].append("실험 횟수가 적어 통계적 유의성이 낮을 수 있습니다.")
            elif num_runs > 100:
                validation["warnings"].append("실험 횟수가 많아 비용과 시간이 증가합니다.")
        
        return validation
    
    @staticmethod
    def validate_optimization_constraints(constraints: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """최적화 제약 조건 검증"""
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        for param, constraint in constraints.items():
            if isinstance(constraint, dict) and 'min' in constraint and 'max' in constraint:
                min_val = constraint['min']
                max_val = constraint['max']
                
                if min_val >= max_val:
                    validation["errors"].append(f"{param}의 최솟값이 최댓값보다 크거나 같습니다.")
                    validation["is_valid"] = False
                
                # 범위 검증
                if param == 'temperature' and (min_val < 50 or max_val > 500):
                    validation["warnings"].append(f"{param}의 범위가 일반적인 공정 범위를 벗어납니다.")
                elif param == 'pressure' and (min_val < 0.1 or max_val > 10):
                    validation["warnings"].append(f"{param}의 범위가 일반적인 공정 범위를 벗어납니다.")
        
        return validation


# 편의 함수들
def analyze_experiment_efficiency(experiment_plan: pd.DataFrame, factors: List[str]) -> Dict[str, Any]:
    """실험 효율성 분석 (편의 함수)"""
    return ExperimentDesignAnalyzer.analyze_experiment_plan(experiment_plan, factors)


def get_correlation_analysis(experiment_plan: pd.DataFrame, factors: List[str]) -> Dict[str, Any]:
    """상관관계 분석 (편의 함수)"""
    return CorrelationAnalyzer.analyze_factor_correlations(experiment_plan, factors)


def analyze_optimization_results(optimization_result: Dict[str, Any]) -> Dict[str, Any]:
    """최적화 결과 분석 (편의 함수)"""
    return OptimizationResultAnalyzer.analyze_optimization_result(optimization_result)


def estimate_report_specs(text: str) -> Dict[str, int]:
    """보고서 규격 추정 (편의 함수)"""
    return ReportUtilities.estimate_reading_time(text)


def validate_experiment_setup(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """실험 설정 검증 (편의 함수)"""
    return ValidationUtilities.validate_experiment_parameters(parameters)


def create_experiment_summary(experiment_data: Dict[str, Any], 
                            optimization_data: Dict[str, Any] = None) -> str:
    """실험 요약 생성 (편의 함수)"""
    return ReportUtilities.generate_executive_summary(experiment_data, optimization_data) 