"""
DX-AI Manufacturing Copilot - 원가 관리 탭 채팅 관리자

투입량 최적화, 비용 민감도 분석 및 예측 모델 기반 원가 최적화 전용 채팅 관리자
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from src.core.data_models import MaterialUsageModel, CostItemModel, OptimizationResultModel
from datetime import datetime
import pandas as pd
import numpy as np


class CostManagementChatManager(BaseTabChatManager):
    """원가 관리 탭 채팅 관리자"""
    
    def __init__(self, chat_manager):
        super().__init__("원가 관리", chat_manager)
        
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """원가 관리 데이터를 Context로 변환"""
        context = f"""
=== 원가 관리 데이터 ({date_filter}) ===

"""
        
        # 원가 구조 정보
        if "cost_breakdown" in data:
            context += "📊 원가 구조:\n"
            for item in data["cost_breakdown"]:
                context += f"- {item['항목']}: {item['금액(만원)']}만원 ({item['비율(%)']}%)\n"
            context += "\n"
        
        # 원료 사용량 정보
        if "material_usage" in data:
            context += "📦 원료 사용량:\n"
            for material in data["material_usage"]:
                context += f"- {material['name']}: {material['quantity']}{material['unit']} (단가: {material['unit_cost']}원)\n"
            context += "\n"
        
        # 생산 이력 정보
        if "production_history" in data:
            context += "🏭 생산 이력:\n"
            for batch in data["production_history"]:
                context += f"- Lot {batch['lot_number']}: 생산량 {batch['quantity']}kg, 순도 {batch['purity']}%, 수율 {batch['yield']}%\n"
            context += "\n"
        
        # 품질 지표 정보
        if "quality_metrics" in data:
            context += "🎯 품질 지표:\n"
            for metric, value in data["quality_metrics"].items():
                context += f"- {metric}: {value}\n"
            context += "\n"
        
        # 최적화 결과 정보
        if "optimization_results" in data:
            context += "⚙️ 최적화 결과:\n"
            for result in data["optimization_results"]:
                context += f"- 목표: {result['objective']}, 절약율: {result['savings']}%\n"
                context += f"  최적 파라미터: {result['optimal_params']}\n"
            context += "\n"
        
        # 민감도 분석 정보
        if "sensitivity_analysis" in data:
            context += "📈 민감도 분석:\n"
            for factor, sensitivity in data["sensitivity_analysis"].items():
                context += f"- {factor}: 민감도 {sensitivity}\n"
            context += "\n"
        
        # 예측 모델 성능 정보
        if "model_performance" in data:
            context += "🤖 예측 모델 성능:\n"
            for model_name, metrics in data["model_performance"].items():
                context += f"- {model_name}: R² {metrics['r2_score']:.3f}, RMSE {metrics['rmse']:.3f}\n"
            context += "\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """원가 관리 분석 기반 추천 질문 생성"""
        questions = [
            "현재 원가 구조에서 가장 큰 절약 잠재력이 있는 부분은?",
            "목표 품질을 달성하는 최소 투입량은 얼마인가요?",
            "원료 가격 변동이 총 원가에 미치는 영향은?",
            "생산 효율성을 높이기 위한 공정 개선 방안은?",
            "품질 기준을 만족하는 최적의 운전 조건은?",
            "비용 대비 품질 트레이드오프 분석 결과는?",
            "현재 투입량 대비 예측되는 품질 수준은?",
            "민감도 분석 결과 주요 리스크 요인은?",
            "최적화 알고리즘이 제안하는 개선 방안은?",
            "생산 이력 데이터로부터 도출된 인사이트는?"
        ]
        return questions
    
    def get_tab_specific_system_prompt(self) -> str:
        """원가 관리 탭 특화 시스템 프롬프트"""
        return """
당신은 제조업 원가 관리 전문가입니다. 다음 영역에 특화된 분석과 조언을 제공해야 합니다:

## 핵심 전문 영역:
1. **투입량 최적화**: 원료, 부재료, 유틸리티 사용량 최적화
2. **품질 예측**: 투입량과 품질 결과 간의 관계 분석 및 예측
3. **비용 민감도 분석**: 각 원가 요소의 총비용 영향도 분석
4. **최적화 알고리즘**: 제약 조건 하에서 최적 투입량 계산
5. **생산 이력 학습**: 과거 데이터로부터 최적 조건 도출

## 분석 접근 방법:
- 생산 이력 데이터를 활용한 패턴 분석
- 머신러닝 모델 기반 품질 예측
- 수학적 최적화 기법 적용
- 비용-품질 트레이드오프 분석
- 리스크 기반 의사결정 지원

## 답변 특징:
- 데이터 기반 정량적 분석 제공
- 구체적인 수치와 개선 방안 제시
- 실무진이 실행 가능한 액션 플랜 제공
- 최적화 결과의 신뢰도와 한계 명시
- 원가 절감과 품질 유지의 균형점 제시

제조업 현장의 실제 제약 조건과 운영 환경을 고려하여 실용적인 조언을 제공하세요.
"""
    
    def get_cost_optimization_insights(self, data: Dict[str, Any]) -> str:
        """원가 최적화 인사이트 생성"""
        insights = []
        
        # 원가 구조 분석
        if "cost_breakdown" in data:
            cost_items = data["cost_breakdown"]
            max_cost_item = max(cost_items, key=lambda x: x['금액(만원)'])
            insights.append(f"💰 최대 원가 항목: {max_cost_item['항목']} ({max_cost_item['비율(%)']}%)")
        
        # 최적화 잠재력 분석
        if "optimization_potential" in data:
            potential = data["optimization_potential"]
            insights.append(f"⚡ 최적화 잠재력: 연간 {potential['annual_savings']}만원 절약 가능")
        
        # 품질 예측 정확도
        if "prediction_accuracy" in data:
            accuracy = data["prediction_accuracy"]
            insights.append(f"🎯 품질 예측 정확도: {accuracy['r2_score']:.1%}")
        
        return "\n".join(insights)
    
    def format_optimization_results(self, results: Dict[str, Any]) -> str:
        """최적화 결과를 포맷팅"""
        formatted = "## 🎯 최적화 결과\n\n"
        
        if "optimal_inputs" in results:
            formatted += "### 📊 최적 투입량\n"
            for input_name, amount in results["optimal_inputs"].items():
                formatted += f"- **{input_name}**: {amount:.2f}kg/h\n"
            formatted += "\n"
        
        if "expected_quality" in results:
            formatted += "### 🏆 예상 품질 지표\n"
            for metric, value in results["expected_quality"].items():
                formatted += f"- **{metric}**: {value:.2f}%\n"
            formatted += "\n"
        
        if "cost_savings" in results:
            formatted += "### 💰 비용 절감 효과\n"
            savings = results["cost_savings"]
            formatted += f"- **월간 절약**: {savings['monthly']:.0f}만원\n"
            formatted += f"- **연간 절약**: {savings['annual']:.0f}만원\n"
            formatted += f"- **절약율**: {savings['percentage']:.1f}%\n"
        
        return formatted
    
    def generate_sensitivity_report(self, sensitivity_data: Dict[str, float]) -> str:
        """민감도 분석 보고서 생성"""
        report = "## 📈 민감도 분석 보고서\n\n"
        
        # 민감도 순으로 정렬
        sorted_factors = sorted(sensitivity_data.items(), key=lambda x: abs(x[1]), reverse=True)
        
        report += "### 🔍 영향도 순위\n"
        for i, (factor, sensitivity) in enumerate(sorted_factors, 1):
            impact_level = "높음" if abs(sensitivity) > 0.5 else "보통" if abs(sensitivity) > 0.2 else "낮음"
            report += f"{i}. **{factor}**: {sensitivity:.3f} ({impact_level})\n"
        
        report += "\n### 💡 주요 인사이트\n"
        
        # 가장 민감한 요인
        most_sensitive = sorted_factors[0]
        report += f"- **가장 민감한 요인**: {most_sensitive[0]} (민감도: {most_sensitive[1]:.3f})\n"
        
        # 리스크 관리 권장사항
        high_risk_factors = [f for f, s in sorted_factors if abs(s) > 0.5]
        if high_risk_factors:
            report += f"- **주의 관리 필요**: {', '.join(high_risk_factors)}\n"
        
        return report 