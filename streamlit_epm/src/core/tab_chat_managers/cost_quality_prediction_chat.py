"""
DX-AI Manufacturing Copilot - 원가 품질 예측 탭 채팅 관리자

품질 예측, 시나리오 분석 및 ML 모델 성능 분석 전용 채팅 관리자
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from datetime import datetime
import pandas as pd


class CostQualityPredictionChatManager(BaseTabChatManager):
    """원가 품질 예측 탭 채팅 관리자"""
    
    def __init__(self, chat_manager):
        super().__init__("원가 품질 예측", chat_manager)
        
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """원가 품질 예측 데이터를 Context로 변환"""
        context = f"""
=== 원가 품질 예측 데이터 ({date_filter}) ===

"""
        
        # 예측 입력 조건
        if "prediction_inputs" in data:
            context += "📊 예측 입력 조건:\n"
            inputs = data["prediction_inputs"]
            for param, value in inputs.items():
                unit = "kg/h" if param in ["material_a", "material_b", "catalyst"] else "°C" if param == "temperature" else "bar" if param == "pressure" else "kWh" if param == "electricity" else "L/h" if param == "cooling_water" else "kg/h"
                context += f"- {param}: {value} {unit}\n"
            context += "\n"
        
        # 품질 예측 결과
        if "quality_predictions" in data:
            context += "🎯 품질 예측 결과:\n"
            predictions = data["quality_predictions"]
            for metric, value in predictions.items():
                if metric in ["purity", "yield"]:
                    context += f"- {metric}: {value:.2f}%\n"
                elif metric == "total_cost":
                    context += f"- 총 비용: {value:.0f}원/h\n"
                else:
                    context += f"- {metric}: {value}\n"
            context += "\n"
        
        # 품질 기준 만족도
        if "quality_compliance" in data:
            context += "✅ 품질 기준 만족도:\n"
            compliance = data["quality_compliance"]
            for criterion, status in compliance.items():
                status_icon = "✅" if status["satisfied"] else "❌"
                context += f"- {criterion}: {status_icon} {status['value']:.2f}% (기준: {status['target']:.2f}%)\n"
            context += "\n"
        
        # ML 모델 성능 지표
        if "model_performance" in data:
            context += "🤖 ML 모델 성능:\n"
            for model_name, metrics in data["model_performance"].items():
                context += f"- {model_name}:\n"
                context += f"  * R² Score: {metrics.get('r2_score', 'N/A'):.3f}\n"
                context += f"  * RMSE: {metrics.get('rmse', 'N/A'):.3f}\n"
                context += f"  * MAE: {metrics.get('mae', 'N/A'):.3f}\n"
            context += "\n"
        
        # 시나리오 분석 결과
        if "scenario_results" in data:
            context += "🎭 시나리오 분석:\n"
            scenarios = data["scenario_results"]
            for scenario in scenarios:
                context += f"- {scenario['시나리오']}: 순도 {scenario['순도 (%)']}%, 수율 {scenario['수율 (%)']}%, 비용 {scenario['총 비용 (원/h)']}원/h\n"
            context += "\n"
        
        # 예측 신뢰도
        if "prediction_confidence" in data:
            context += "📈 예측 신뢰도:\n"
            confidence = data["prediction_confidence"]
            for metric, conf_data in confidence.items():
                context += f"- {metric}: {conf_data['confidence']:.1f}% (불확실성: ±{conf_data['uncertainty']:.2f})\n"
            context += "\n"
        
        # 품질 개선 제안
        if "improvement_suggestions" in data:
            context += "💡 품질 개선 제안:\n"
            suggestions = data["improvement_suggestions"]
            for i, suggestion in enumerate(suggestions, 1):
                context += f"{i}. {suggestion}\n"
            context += "\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """원가 품질 예측 기반 추천 질문 생성"""
        questions = [
            "현재 예측 모델의 정확도와 신뢰성은?",
            "품질 기준 미달 시 개선 방안은?",
            "투입량 변화가 품질에 미치는 영향은?",
            "비용 최소화와 품질 목표 달성의 균형점은?",
            "예측 불확실성을 줄이는 방법은?",
            "시나리오별 품질 변화 패턴은?",
            "ML 모델 성능 개선을 위한 방안은?",
            "품질 예측 결과의 현장 적용 가능성은?",
            "예측 모델의 일반화 성능은?",
            "품질 안정성 확보를 위한 운영 전략은?"
        ]
        return questions
    
    def get_tab_specific_system_prompt(self) -> str:
        """원가 품질 예측 탭 특화 시스템 프롬프트"""
        return """
당신은 제조업 품질 예측 전문가입니다. 다음 영역에 특화된 분석과 조언을 제공해야 합니다:

## 핵심 전문 영역:
1. **품질 예측 모델링**: 투입량-품질 관계 모델링 및 예측
2. **ML 모델 성능 평가**: 예측 정확도, 신뢰도, 일반화 성능 분석
3. **시나리오 분석**: 다양한 운영 조건하에서 품질 변화 예측
4. **품질 최적화**: 목표 품질 달성을 위한 최적 조건 도출
5. **예측 불확실성 관리**: 예측 구간, 신뢰도 평가 및 리스크 관리

## 분석 접근 방법:
- 머신러닝 기반 품질 예측 모델 활용
- 교차 검증을 통한 모델 성능 평가
- 피처 중요도 분석을 통한 핵심 변수 도출
- 예측 구간 추정을 통한 불확실성 정량화
- 시나리오 기반 품질 변화 시뮬레이션

## 답변 특징:
- 예측 정확도와 신뢰도 정량화
- 품질 개선을 위한 구체적 방안 제시
- 모델 한계와 적용 범위 명시
- 현장 적용 가능한 실용적 조언
- 품질 안정성 확보 전략 제공

제조업 현장의 실제 품질 기준과 운영 환경을 고려하여 실용적인 품질 예측 및 개선 방안을 제공하세요.
"""
    
    def get_prediction_insights(self, prediction_data: Dict[str, Any]) -> str:
        """품질 예측 인사이트 생성"""
        insights = []
        
        if "quality_predictions" in prediction_data:
            predictions = prediction_data["quality_predictions"]
            purity = predictions.get("purity", 0)
            yield_rate = predictions.get("yield", 0)
            total_cost = predictions.get("total_cost", 0)
            
            insights.append(f"🎯 예측 순도: {purity:.2f}%")
            insights.append(f"🎯 예측 수율: {yield_rate:.2f}%")
            insights.append(f"💰 예측 비용: {total_cost:.0f}원/h")
        
        if "model_performance" in prediction_data:
            performance = prediction_data["model_performance"]
            best_model = max(performance.items(), key=lambda x: x[1].get('r2_score', 0))
            insights.append(f"🤖 최고 성능 모델: {best_model[0]} (R²: {best_model[1].get('r2_score', 0):.3f})")
        
        if "quality_compliance" in prediction_data:
            compliance = prediction_data["quality_compliance"]
            satisfied_count = sum(1 for status in compliance.values() if status["satisfied"])
            total_count = len(compliance)
            insights.append(f"✅ 품질 기준 만족: {satisfied_count}/{total_count}")
        
        return "\n".join(insights)
    
    def format_prediction_report(self, results: Dict[str, Any]) -> str:
        """품질 예측 보고서 포맷팅"""
        report = "## 🔮 품질 예측 분석 보고서\n\n"
        
        # 예측 결과
        if "quality_predictions" in results:
            report += "### 🎯 품질 예측 결과\n"
            predictions = results["quality_predictions"]
            for metric, value in predictions.items():
                if metric in ["purity", "yield"]:
                    report += f"- **{metric}**: {value:.2f}%\n"
                elif metric == "total_cost":
                    report += f"- **총 비용**: {value:.0f}원/h\n"
            report += "\n"
        
        # 품질 기준 만족도
        if "quality_compliance" in results:
            report += "### ✅ 품질 기준 만족도\n"
            compliance = results["quality_compliance"]
            for criterion, status in compliance.items():
                status_icon = "✅" if status["satisfied"] else "❌"
                report += f"- **{criterion}**: {status_icon} {status['value']:.2f}% (기준: {status['target']:.2f}%)\n"
            report += "\n"
        
        # 모델 성능 평가
        if "model_performance" in results:
            report += "### 🤖 ML 모델 성능\n"
            for model_name, metrics in results["model_performance"].items():
                report += f"- **{model_name}**:\n"
                report += f"  * R² Score: {metrics.get('r2_score', 'N/A'):.3f}\n"
                report += f"  * RMSE: {metrics.get('rmse', 'N/A'):.3f}\n"
            report += "\n"
        
        # 시나리오 분석
        if "scenario_results" in results:
            report += "### 🎭 시나리오 분석\n"
            scenarios = results["scenario_results"]
            for scenario in scenarios:
                report += f"- **{scenario['시나리오']}**: 순도 {scenario['순도 (%)']}%, 수율 {scenario['수율 (%)']}%\n"
            report += "\n"
        
        # 개선 권장사항
        if "improvement_suggestions" in results:
            report += "### 💡 개선 권장사항\n"
            for i, suggestion in enumerate(results["improvement_suggestions"], 1):
                report += f"{i}. {suggestion}\n"
        
        return report 