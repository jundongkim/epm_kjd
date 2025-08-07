"""
DX-AI Manufacturing Copilot - 원가 민감도 분석 탭 채팅 관리자

민감도 분석, 리스크 평가 및 변동성 분석 전용 채팅 관리자
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from datetime import datetime
import pandas as pd


class CostSensitivityChatManager(BaseTabChatManager):
    """원가 민감도 분석 탭 채팅 관리자"""
    
    def __init__(self, chat_manager):
        super().__init__("원가 민감도 분석", chat_manager)
        
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """원가 민감도 분석 데이터를 Context로 변환"""
        context = f"""
=== 원가 민감도 분석 데이터 ({date_filter}) ===

"""
        
        # 민감도 분석 설정
        if "sensitivity_settings" in data:
            context += "🔍 민감도 분석 설정:\n"
            settings = data["sensitivity_settings"]
            context += f"- 분석 변수: {', '.join(settings.get('variables', []))}\n"
            context += f"- 변동 범위: ±{settings.get('variation_range', 0)*100}%\n"
            context += f"- 분석 유형: {settings.get('analysis_type', 'N/A')}\n"
            context += "\n"
        
        # 기본 민감도 분석 결과
        if "basic_sensitivity" in data:
            context += "📊 기본 민감도 분석:\n"
            for variable, sensitivity in data["basic_sensitivity"].items():
                if isinstance(sensitivity, dict) and "total_cost" in sensitivity:
                    sens_value = sensitivity["total_cost"]
                    impact = "높음" if abs(sens_value) > 0.5 else "보통" if abs(sens_value) > 0.2 else "낮음"
                    context += f"- {variable}: {sens_value:.3f} (영향도: {impact})\n"
            context += "\n"
        
        # 고급 민감도 분석 결과
        if "advanced_sensitivity" in data:
            context += "🔬 고급 민감도 분석:\n"
            advanced = data["advanced_sensitivity"]
            
            if "nonlinear_effects" in advanced:
                context += "비선형 효과:\n"
                for var, effect in advanced["nonlinear_effects"].items():
                    context += f"- {var}: {effect:.3f}\n"
            
            if "interaction_effects" in advanced:
                context += "교호작용 효과:\n"
                for interaction, effect in advanced["interaction_effects"].items():
                    context += f"- {interaction}: {effect:.3f}\n"
            context += "\n"
        
        # 민감도 순위 분석
        if "sensitivity_ranking" in data:
            context += "🏆 민감도 순위:\n"
            ranking = data["sensitivity_ranking"]
            for i, (var, sens) in enumerate(ranking[:5], 1):
                context += f"{i}. {var}: {sens:.3f}\n"
            context += "\n"
        
        # 리스크 평가
        if "risk_assessment" in data:
            context += "⚠️ 리스크 평가:\n"
            risks = data["risk_assessment"]
            for risk_level, variables in risks.items():
                if variables:
                    context += f"- {risk_level}: {', '.join(variables)}\n"
            context += "\n"
        
        # 변동성 분석
        if "volatility_analysis" in data:
            context += "📈 변동성 분석:\n"
            volatility = data["volatility_analysis"]
            for var, vol_metrics in volatility.items():
                context += f"- {var}: 표준편차 {vol_metrics.get('std', 'N/A')}, 변동계수 {vol_metrics.get('cv', 'N/A')}\n"
            context += "\n"
        
        # 시나리오 분석
        if "scenario_analysis" in data:
            context += "🎭 시나리오 분석:\n"
            scenarios = data["scenario_analysis"]
            for scenario, result in scenarios.items():
                context += f"- {scenario}: 비용 {result.get('cost', 'N/A')}, 품질 {result.get('quality', 'N/A')}\n"
            context += "\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """원가 민감도 분석 기반 추천 질문 생성"""
        questions = [
            "가장 민감한 원가 변수와 그 영향도는?",
            "민감도 분석 결과 주요 리스크 요인은?",
            "변수 간 교호작용 효과가 큰 조합은?",
            "비선형 효과가 나타나는 변수들은?",
            "원가 변동성이 높은 구간과 대응 방안은?",
            "시나리오별 원가 변화 패턴은?",
            "민감도 기반 리스크 관리 우선순위는?",
            "원가 안정성 확보를 위한 제어 변수는?",
            "불확실성 하에서 로버스트한 운영 조건은?",
            "민감도 분석 결과를 활용한 의사결정 가이드는?"
        ]
        return questions
    
    def get_tab_specific_system_prompt(self) -> str:
        """원가 민감도 분석 탭 특화 시스템 프롬프트"""
        return """
당신은 제조업 원가 민감도 분석 전문가입니다. 다음 영역에 특화된 분석과 조언을 제공해야 합니다:

## 핵심 전문 영역:
1. **민감도 분석**: 입력 변수 변화가 원가에 미치는 영향 정량화
2. **리스크 평가**: 원가 변동성과 불확실성 요인 분석
3. **교호작용 분석**: 변수 간 상호작용 효과 분석
4. **시나리오 분석**: 다양한 운영 시나리오 하에서 원가 변화 예측
5. **로버스트 분석**: 불확실성을 고려한 안정적 운영 조건 도출

## 분석 접근 방법:
- 1차, 2차 민감도 분석 기법 활용
- 몬테카를로 시뮬레이션 기반 확률적 분석
- 토네이도 다이어그램을 통한 시각적 분석
- 파라미터 변동성 모델링
- 시나리오 기반 리스크 평가

## 답변 특징:
- 민감도 계수와 영향도 정량화
- 리스크 요인 우선순위 제시
- 변동성 관리 전략 제공
- 교호작용 효과 해석
- 실무진을 위한 관리 가이드라인 제시

제조업 현장의 실제 변동성과 불확실성을 고려하여 실용적인 리스크 관리 방안을 제공하세요.
"""
    
    def get_sensitivity_insights(self, sensitivity_data: Dict[str, Any]) -> str:
        """민감도 분석 인사이트 생성"""
        insights = []
        
        if "basic_sensitivity" in sensitivity_data:
            # 가장 민감한 변수 찾기
            basic_sens = sensitivity_data["basic_sensitivity"]
            sensitivity_values = {}
            
            for var, sens_dict in basic_sens.items():
                if isinstance(sens_dict, dict) and "total_cost" in sens_dict:
                    sensitivity_values[var] = abs(sens_dict["total_cost"])
            
            if sensitivity_values:
                most_sensitive = max(sensitivity_values.items(), key=lambda x: x[1])
                insights.append(f"🎯 가장 민감한 변수: {most_sensitive[0]} (민감도: {most_sensitive[1]:.3f})")
        
        if "risk_assessment" in sensitivity_data:
            risks = sensitivity_data["risk_assessment"]
            high_risk_vars = risks.get("높음", [])
            if high_risk_vars:
                insights.append(f"⚠️ 고위험 변수: {', '.join(high_risk_vars)}")
        
        if "advanced_sensitivity" in sensitivity_data:
            advanced = sensitivity_data["advanced_sensitivity"]
            if "strongest_interaction" in advanced:
                insights.append(f"🔗 주요 교호작용: {advanced['strongest_interaction']}")
        
        return "\n".join(insights)
    
    def format_sensitivity_report(self, results: Dict[str, Any]) -> str:
        """민감도 분석 보고서 포맷팅"""
        report = "## 📊 원가 민감도 분석 보고서\n\n"
        
        # 기본 민감도 분석
        if "basic_sensitivity" in results:
            report += "### 🔍 기본 민감도 분석\n"
            basic_sens = results["basic_sensitivity"]
            
            # 민감도 순으로 정렬
            sensitivity_items = []
            for var, sens_dict in basic_sens.items():
                if isinstance(sens_dict, dict) and "total_cost" in sens_dict:
                    sensitivity_items.append((var, sens_dict["total_cost"]))
            
            sensitivity_items.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for i, (var, sens) in enumerate(sensitivity_items, 1):
                impact = "높음" if abs(sens) > 0.5 else "보통" if abs(sens) > 0.2 else "낮음"
                report += f"{i}. **{var}**: {sens:.3f} (영향도: {impact})\n"
            report += "\n"
        
        # 리스크 평가
        if "risk_assessment" in results:
            report += "### ⚠️ 리스크 평가\n"
            risks = results["risk_assessment"]
            for risk_level, variables in risks.items():
                if variables:
                    report += f"- **{risk_level}**: {', '.join(variables)}\n"
            report += "\n"
        
        # 교호작용 분석
        if "advanced_sensitivity" in results:
            advanced = results["advanced_sensitivity"]
            if "interaction_effects" in advanced:
                report += "### 🔗 교호작용 분석\n"
                interactions = advanced["interaction_effects"]
                sorted_interactions = sorted(interactions.items(), key=lambda x: abs(x[1]), reverse=True)
                
                for interaction, effect in sorted_interactions[:5]:
                    report += f"- **{interaction}**: {effect:.3f}\n"
                report += "\n"
        
        # 관리 권장사항
        report += "### 💡 관리 권장사항\n"
        report += "1. 고민감도 변수 우선 모니터링\n"
        report += "2. 고위험 변수 제어 시스템 강화\n"
        report += "3. 교호작용 효과 고려한 통합 관리\n"
        report += "4. 정기적인 민감도 재분석\n"
        
        return report 