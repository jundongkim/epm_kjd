"""
DX-AI Manufacturing Copilot - 원가 AI 분석 탭 채팅 관리자

종합 AI 분석, 통합 보고서 생성 및 전략적 인사이트 제공 전용 채팅 관리자
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from datetime import datetime
import pandas as pd


class CostAIAnalysisChatManager(BaseTabChatManager):
    """원가 AI 분석 탭 채팅 관리자"""
    
    def __init__(self, chat_manager):
        super().__init__("원가 AI 분석", chat_manager)
        
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """원가 AI 분석 데이터를 Context로 변환"""
        context = f"""
=== 원가 AI 분석 종합 데이터 ({date_filter}) ===

"""
        
        # 전체 원가 현황
        if "cost_overview" in data:
            context += "💰 원가 현황 요약:\n"
            overview = data["cost_overview"]
            context += f"- 총 원가: {overview.get('total_cost', 'N/A')}만원\n"
            context += f"- 원료비 비중: {overview.get('material_ratio', 'N/A')}%\n"
            context += f"- 유틸리티 비중: {overview.get('utility_ratio', 'N/A')}%\n"
            context += f"- 단위당 원가: {overview.get('cost_per_unit', 'N/A')}원/kg\n"
            context += "\n"
        
        # 최적화 성과
        if "optimization_performance" in data:
            context += "⚙️ 최적화 성과:\n"
            perf = data["optimization_performance"]
            context += f"- 최적화 실행 횟수: {perf.get('optimization_runs', 0)}회\n"
            context += f"- 평균 절감률: {perf.get('avg_savings', 0)}%\n"
            context += f"- 최적 알고리즘: {perf.get('best_algorithm', 'N/A')}\n"
            context += f"- 품질 기준 만족률: {perf.get('quality_compliance_rate', 0)}%\n"
            context += "\n"
        
        # 민감도 분석 요약
        if "sensitivity_summary" in data:
            context += "📊 민감도 분석 요약:\n"
            sensitivity = data["sensitivity_summary"]
            context += f"- 가장 민감한 변수: {sensitivity.get('most_sensitive_var', 'N/A')}\n"
            context += f"- 고위험 변수 수: {sensitivity.get('high_risk_count', 0)}개\n"
            context += f"- 주요 교호작용: {sensitivity.get('key_interactions', 'N/A')}\n"
            context += "\n"
        
        # 품질 예측 성과
        if "prediction_performance" in data:
            context += "🎯 품질 예측 성과:\n"
            pred = data["prediction_performance"]
            context += f"- 예측 정확도: {pred.get('accuracy', 'N/A')}%\n"
            context += f"- 최고 성능 모델: {pred.get('best_model', 'N/A')}\n"
            context += f"- 평균 예측 오차: {pred.get('avg_error', 'N/A')}\n"
            context += f"- 품질 기준 달성 예상: {pred.get('quality_achievement_rate', 'N/A')}%\n"
            context += "\n"
        
        # 생산 성과 지표
        if "production_metrics" in data:
            context += "🏭 생산 성과 지표:\n"
            metrics = data["production_metrics"]
            context += f"- 평균 순도: {metrics.get('avg_purity', 'N/A')}%\n"
            context += f"- 평균 수율: {metrics.get('avg_yield', 'N/A')}%\n"
            context += f"- 생산량: {metrics.get('production_volume', 'N/A')}kg\n"
            context += f"- 품질 안정성: {metrics.get('quality_stability', 'N/A')}\n"
            context += "\n"
        
        # 비용 효율성 분석
        if "cost_efficiency" in data:
            context += "💡 비용 효율성 분석:\n"
            efficiency = data["cost_efficiency"]
            context += f"- 원가 대비 품질 지수: {efficiency.get('cost_quality_index', 'N/A')}\n"
            context += f"- 에너지 효율성: {efficiency.get('energy_efficiency', 'N/A')}%\n"
            context += f"- 원료 활용률: {efficiency.get('material_utilization', 'N/A')}%\n"
            context += f"- 전체 효율성 점수: {efficiency.get('overall_efficiency_score', 'N/A')}\n"
            context += "\n"
        
        # 리스크 및 기회 분석
        if "risk_opportunity" in data:
            context += "⚠️ 리스크 및 기회 분석:\n"
            risk_opp = data["risk_opportunity"]
            context += f"- 주요 리스크: {', '.join(risk_opp.get('major_risks', []))}\n"
            context += f"- 개선 기회: {', '.join(risk_opp.get('opportunities', []))}\n"
            context += f"- 예상 절감 잠재력: {risk_opp.get('savings_potential', 'N/A')}만원/월\n"
            context += "\n"
        
        # KPI 대시보드
        if "kpi_dashboard" in data:
            context += "📈 핵심 KPI:\n"
            kpis = data["kpi_dashboard"]
            for kpi_name, kpi_value in kpis.items():
                context += f"- {kpi_name}: {kpi_value}\n"
            context += "\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """원가 AI 분석 기반 추천 질문 생성"""
        questions = [
            "전체 원가 관리 시스템의 성과 평가는?",
            "최적화와 예측 모델의 통합 효과는?",
            "원가 절감 목표 대비 실제 성과는?",
            "AI 시스템 도입 후 ROI 분석 결과는?",
            "향후 6개월 원가 관리 전략은?",
            "경쟁사 대비 우리 원가 경쟁력은?",
            "원가 관리 시스템의 개선 우선순위는?",
            "지속가능한 원가 절감 방안은?",
            "품질과 원가의 최적 균형점은?",
            "원가 관리 성과의 경영진 보고서는?"
        ]
        return questions
    
    def get_tab_specific_system_prompt(self) -> str:
        """원가 AI 분석 탭 특화 시스템 프롬프트"""
        return """
당신은 제조업 원가 관리 전략 컨설턴트입니다. 다음 영역에 특화된 분석과 조언을 제공해야 합니다:

## 핵심 전문 영역:
1. **통합 원가 관리**: 분석-최적화-예측의 통합적 접근
2. **전략적 인사이트**: 데이터 기반 의사결정 지원
3. **성과 평가**: KPI 기반 원가 관리 성과 측정
4. **경쟁력 분석**: 업계 벤치마킹 및 경쟁 우위 요소 분석
5. **미래 전략**: 중장기 원가 관리 로드맵 수립

## 분석 접근 방법:
- 종합적 데이터 분석 및 패턴 인식
- 다차원 성과 지표 통합 평가
- 리스크-기회 매트릭스 분석
- 시나리오 기반 전략 시뮬레이션
- 지속가능성 관점의 원가 관리

## 답변 특징:
- 경영진 관점의 전략적 인사이트 제공
- 실무진을 위한 실행 가능한 액션 플랜
- 정량적 성과 지표와 정성적 평가 결합
- 단기/중기/장기 관점의 균형잡힌 조언
- 리스크 관리와 기회 창출의 통합 접근

제조업 현장의 실제 제약과 경영 환경을 고려하여 전략적이고 실용적인 원가 관리 방향을 제시하세요.
"""
    
    def get_comprehensive_insights(self, data: Dict[str, Any]) -> str:
        """종합적 AI 분석 인사이트 생성"""
        insights = []
        
        # 전체 성과 요약
        if "cost_overview" in data:
            overview = data["cost_overview"]
            total_cost = overview.get("total_cost", 0)
            insights.append(f"💰 총 원가: {total_cost}만원")
        
        # 최적화 성과
        if "optimization_performance" in data:
            perf = data["optimization_performance"]
            avg_savings = perf.get("avg_savings", 0)
            insights.append(f"📈 평균 절감률: {avg_savings}%")
        
        # 품질 성과
        if "production_metrics" in data:
            metrics = data["production_metrics"]
            avg_purity = metrics.get("avg_purity", 0)
            avg_yield = metrics.get("avg_yield", 0)
            insights.append(f"🎯 평균 순도: {avg_purity}%, 평균 수율: {avg_yield}%")
        
        # 효율성 평가
        if "cost_efficiency" in data:
            efficiency = data["cost_efficiency"]
            overall_score = efficiency.get("overall_efficiency_score", 0)
            insights.append(f"⚡ 전체 효율성: {overall_score}점")
        
        # 개선 기회
        if "risk_opportunity" in data:
            risk_opp = data["risk_opportunity"]
            savings_potential = risk_opp.get("savings_potential", 0)
            insights.append(f"💡 절감 잠재력: {savings_potential}만원/월")
        
        return "\n".join(insights)
    
    def format_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """종합 AI 분석 보고서 포맷팅"""
        report = "## 🤖 원가 관리 AI 종합 분석 보고서\n\n"
        
        # 전체 성과 요약
        if "cost_overview" in results:
            report += "### 💰 전체 원가 현황\n"
            overview = results["cost_overview"]
            report += f"- **총 원가**: {overview.get('total_cost', 'N/A')}만원\n"
            report += f"- **원료비 비중**: {overview.get('material_ratio', 'N/A')}%\n"
            report += f"- **단위당 원가**: {overview.get('cost_per_unit', 'N/A')}원/kg\n"
            report += "\n"
        
        # AI 시스템 성과
        if "optimization_performance" in results:
            report += "### 🎯 AI 최적화 성과\n"
            perf = results["optimization_performance"]
            report += f"- **최적화 실행**: {perf.get('optimization_runs', 0)}회\n"
            report += f"- **평균 절감률**: {perf.get('avg_savings', 0)}%\n"
            report += f"- **품질 기준 만족**: {perf.get('quality_compliance_rate', 0)}%\n"
            report += "\n"
        
        # 핵심 성과 지표
        if "kpi_dashboard" in results:
            report += "### 📊 핵심 KPI\n"
            kpis = results["kpi_dashboard"]
            for kpi_name, kpi_value in kpis.items():
                report += f"- **{kpi_name}**: {kpi_value}\n"
            report += "\n"
        
        # 리스크 및 기회
        if "risk_opportunity" in results:
            report += "### ⚠️ 리스크 및 기회\n"
            risk_opp = results["risk_opportunity"]
            report += f"- **주요 리스크**: {', '.join(risk_opp.get('major_risks', []))}\n"
            report += f"- **개선 기회**: {', '.join(risk_opp.get('opportunities', []))}\n"
            report += f"- **절감 잠재력**: {risk_opp.get('savings_potential', 'N/A')}만원/월\n"
            report += "\n"
        
        # 전략적 권장사항
        report += "### 💡 전략적 권장사항\n"
        report += "1. **단기 (1-3개월)**: 고민감도 변수 집중 관리\n"
        report += "2. **중기 (3-6개월)**: 최적화 알고리즘 고도화\n"
        report += "3. **장기 (6개월+)**: 통합 원가 관리 시스템 구축\n"
        report += "4. **지속적**: 품질-원가 균형점 모니터링\n"
        
        return report 