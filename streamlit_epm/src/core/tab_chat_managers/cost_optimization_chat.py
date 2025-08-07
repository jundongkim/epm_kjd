"""
DX-AI Manufacturing Copilot - 원가 최적화 탭 채팅 관리자

투입량 최적화, 최적화 알고리즘 분석 및 최적화 결과 해석 전용 채팅 관리자
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from datetime import datetime
import pandas as pd


class CostOptimizationChatManager(BaseTabChatManager):
    """원가 최적화 탭 채팅 관리자"""
    
    def __init__(self, chat_manager):
        super().__init__("원가 최적화", chat_manager)
        
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """원가 최적화 데이터를 Context로 변환"""
        context = f"""
=== 원가 최적화 데이터 ({date_filter}) ===

"""
        
        # 최적화 설정 정보
        if "optimization_settings" in data:
            context += "⚙️ 최적화 설정:\n"
            settings = data["optimization_settings"]
            context += f"- 목표 순도: {settings.get('target_purity', 'N/A')}%\n"
            context += f"- 목표 수율: {settings.get('target_yield', 'N/A')}%\n"
            context += f"- 최적화 방법: {settings.get('optimization_method', 'N/A')}\n"
            context += "\n"
        
        # 최적화 결과 정보
        if "optimization_results" in data:
            context += "🎯 최적화 결과:\n"
            results = data["optimization_results"]
            if "optimal_inputs" in results:
                context += "최적 투입량:\n"
                for param, value in results["optimal_inputs"].items():
                    context += f"- {param}: {value:.2f}kg/h\n"
            
            if "expected_quality" in results:
                context += "예상 품질:\n"
                for metric, value in results["expected_quality"].items():
                    unit = "%" if metric in ["purity", "yield"] else "원"
                    context += f"- {metric}: {value:.2f}{unit}\n"
            
            if "cost_savings" in results:
                savings = results["cost_savings"]
                context += f"비용 절감: {savings.get('percentage', 0)}% ({savings.get('monthly', 0)}만원/월)\n"
            context += "\n"
        
        # 최적화 알고리즘 성능
        if "algorithm_performance" in data:
            context += "📊 알고리즘 성능:\n"
            for method, performance in data["algorithm_performance"].items():
                context += f"- {method}: 목적함수 값 {performance.get('objective_value', 'N/A')}\n"
            context += "\n"
        
        # 제약 조건 분석
        if "constraint_analysis" in data:
            context += "🔒 제약 조건 분석:\n"
            constraints = data["constraint_analysis"]
            for constraint in constraints:
                status = "만족" if constraint["satisfied"] else "위반"
                context += f"- {constraint['parameter']}: {constraint['value']:.2f} ({status})\n"
            context += "\n"
        
        # 최적화 히스토리
        if "optimization_history" in data:
            context += "📈 최적화 히스토리:\n"
            history = data["optimization_history"]
            context += f"- 총 실행 횟수: {len(history)}회\n"
            if history:
                latest = history[-1]
                context += f"- 최근 결과: {latest.get('objective_value', 'N/A')}\n"
                context += f"- 수렴 여부: {'예' if latest.get('converged', False) else '아니오'}\n"
            context += "\n"
        
        # 파레토 최적해 분석
        if "pareto_analysis" in data:
            context += "⚖️ 파레토 최적해 분석:\n"
            pareto = data["pareto_analysis"]
            context += f"- 최적해 개수: {pareto.get('solution_count', 0)}개\n"
            context += f"- 최적 트레이드오프 포인트: {pareto.get('best_tradeoff', 'N/A')}\n"
            context += "\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """원가 최적화 기반 추천 질문 생성"""
        questions = [
            "현재 최적화 결과의 신뢰성과 실현 가능성은?",
            "최적화 알고리즘별 성능 비교 결과는?",
            "제약 조건 변경 시 최적화 결과 변화는?",
            "목표 품질 기준 조정이 원가에 미치는 영향은?",
            "최적 투입량 대비 현재 운전 조건의 차이는?",
            "파레토 최적해에서 최적 트레이드오프 포인트는?",
            "최적화 결과 구현 시 예상되는 리스크는?",
            "다목적 최적화에서 목표 간 상충 관계는?",
            "로버스트 최적화 적용 시 안정성 향상 정도는?",
            "최적화 결과를 현장에 적용하는 단계별 계획은?"
        ]
        return questions
    
    def get_tab_specific_system_prompt(self) -> str:
        """원가 최적화 탭 특화 시스템 프롬프트"""
        return """
당신은 제조업 원가 최적화 전문가입니다. 다음 영역에 특화된 분석과 조언을 제공해야 합니다:

## 핵심 전문 영역:
1. **투입량 최적화**: 원료, 촉매, 유틸리티 투입량의 최적 조합 도출
2. **최적화 알고리즘**: Differential Evolution, Bayesian Optimization, Robust Optimization 등
3. **제약 조건 관리**: 품질 기준, 안전 한계, 설비 제약 등
4. **다목적 최적화**: 비용-품질-생산성 간 트레이드오프 분석
5. **최적화 결과 해석**: 민감도 분석, 신뢰도 평가, 구현 가능성 검토

## 분석 접근 방법:
- 수학적 최적화 기법 활용
- 머신러닝 기반 목적함수 모델링
- 불확실성을 고려한 로버스트 최적화
- 파레토 최적해 기반 의사결정 지원
- 실시간 최적화 및 적응적 제어

## 답변 특징:
- 최적화 결과의 수학적 근거 제시
- 알고리즘별 성능 비교 분석
- 제약 조건 위반 시 대안 제시
- 최적화 신뢰도와 민감도 분석
- 현장 적용 가능한 구현 방안 제공

제조업 현장의 실제 제약 조건과 운영 환경을 고려하여 실용적인 최적화 솔루션을 제공하세요.
"""
    
    def get_optimization_insights(self, optimization_results: Dict[str, Any]) -> str:
        """최적화 결과 인사이트 생성"""
        insights = []
        
        if "optimal_inputs" in optimization_results:
            optimal_inputs = optimization_results["optimal_inputs"]
            # 기준 투입량 대비 변화율 계산
            baseline = {"material_a": 100, "material_b": 50, "catalyst": 5}
            
            for param, optimal_value in optimal_inputs.items():
                if param in baseline:
                    change_rate = ((optimal_value - baseline[param]) / baseline[param]) * 100
                    direction = "증가" if change_rate > 0 else "감소"
                    insights.append(f"📊 {param}: {abs(change_rate):.1f}% {direction} 권장")
        
        if "expected_quality" in optimization_results:
            quality = optimization_results["expected_quality"]
            insights.append(f"🎯 예상 순도: {quality.get('purity', 0):.1f}%")
            insights.append(f"🎯 예상 수율: {quality.get('yield', 0):.1f}%")
        
        if "cost_savings" in optimization_results:
            savings = optimization_results["cost_savings"]
            insights.append(f"💰 예상 절감: {savings.get('percentage', 0):.1f}% ({savings.get('monthly', 0)}만원/월)")
        
        return "\n".join(insights)
    
    def format_optimization_report(self, results: Dict[str, Any]) -> str:
        """최적화 결과 보고서 포맷팅"""
        report = "## 🎯 원가 최적화 결과 보고서\n\n"
        
        # 최적 투입량
        if "optimal_inputs" in results:
            report += "### 📊 최적 투입량\n"
            for param, value in results["optimal_inputs"].items():
                report += f"- **{param}**: {value:.2f}kg/h\n"
            report += "\n"
        
        # 예상 품질 지표
        if "expected_quality" in results:
            report += "### 🏆 예상 품질 지표\n"
            for metric, value in results["expected_quality"].items():
                unit = "%" if metric in ["purity", "yield"] else "원"
                report += f"- **{metric}**: {value:.2f}{unit}\n"
            report += "\n"
        
        # 비용 절감 효과
        if "cost_savings" in results:
            report += "### 💰 비용 절감 효과\n"
            savings = results["cost_savings"]
            report += f"- **절감율**: {savings.get('percentage', 0):.1f}%\n"
            report += f"- **월간 절감**: {savings.get('monthly', 0)}만원\n"
            report += f"- **연간 절감**: {savings.get('annual', 0)}만원\n"
            report += "\n"
        
        # 최적화 알고리즘 성능
        if "algorithm_performance" in results:
            report += "### 🤖 알고리즘 성능\n"
            for method, performance in results["algorithm_performance"].items():
                report += f"- **{method}**: 목적함수 값 {performance.get('objective_value', 'N/A')}\n"
            report += "\n"
        
        # 구현 권장사항
        report += "### 💡 구현 권장사항\n"
        report += "1. 최적 투입량을 단계적으로 적용\n"
        report += "2. 품질 모니터링 강화\n"
        report += "3. 정기적인 최적화 재수행\n"
        report += "4. 설비 제약 조건 지속 확인\n"
        
        return report 