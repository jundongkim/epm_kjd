"""
DX-AI Manufacturing Copilot - 원가 분석 탭 채팅 관리자

원가 구조 분석, 원가 트렌드 분석 및 원가 성과 지표 전용 채팅 관리자
"""

import streamlit as st
from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from datetime import datetime
import pandas as pd


class CostAnalysisChatManager(BaseTabChatManager):
    """원가 분석 탭 채팅 관리자"""
    
    def __init__(self, chat_manager):
        super().__init__("원가 분석", chat_manager)
        
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """원가 분석 데이터를 Context로 변환"""
        context = f"""
=== 원가 분석 데이터 ({date_filter}) ===

"""
        
        # 원가 구조 정보
        if "cost_breakdown" in data:
            context += "📊 원가 구조 분석:\n"
            total_cost = sum(item["금액(만원)"] for item in data["cost_breakdown"])
            context += f"- 총 원가: {total_cost}만원\n"
            for item in data["cost_breakdown"]:
                context += f"- {item['항목']}: {item['금액(만원)']}만원 ({item['비율(%)']}%)\n"
            context += "\n"
        
        # 원료비 상세 분석
        if "material_costs" in data:
            context += "📦 원료비 상세:\n"
            for material in data["material_costs"]:
                context += f"- {material['name']}: {material['cost']}만원 ({material['usage']}kg × {material['unit_price']}원/kg)\n"
            context += "\n"
        
        # 유틸리티 비용 분석
        if "utility_costs" in data:
            context += "⚡ 유틸리티 비용:\n"
            for utility in data["utility_costs"]:
                context += f"- {utility['type']}: {utility['cost']}만원 ({utility['usage']}{utility['unit']})\n"
            context += "\n"
        
        # 생산량 대비 원가 효율성
        if "production_efficiency" in data:
            context += "📈 생산 효율성:\n"
            eff = data["production_efficiency"]
            context += f"- 단위당 원가: {eff['cost_per_unit']}원/kg\n"
            context += f"- 생산량: {eff['production_volume']}kg\n"
            context += f"- 가동률: {eff['utilization_rate']}%\n"
            context += "\n"
        
        # 원가 트렌드 분석
        if "cost_trends" in data:
            context += "📊 원가 트렌드:\n"
            trends = data["cost_trends"]
            context += f"- 전월 대비 증감: {trends['monthly_change']}%\n"
            context += f"- 전년 대비 증감: {trends['yearly_change']}%\n"
            context += f"- 주요 변동 요인: {trends['main_factors']}\n"
            context += "\n"
        
        # 원가 성과 지표
        if "cost_performance" in data:
            context += "🎯 원가 성과 지표:\n"
            for metric, value in data["cost_performance"].items():
                context += f"- {metric}: {value}\n"
            context += "\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """원가 분석 기반 추천 질문 생성"""
        questions = [
            "현재 원가 구조에서 가장 큰 비중을 차지하는 항목은?",
            "원료비 절감을 위한 구체적인 방안은?",
            "유틸리티 비용 최적화 방법은?",
            "생산량 증가 시 단위당 원가 변화는?",
            "원가 트렌드 분석 결과와 주요 요인은?",
            "경쟁사 대비 우리 원가 경쟁력은?",
            "원가 절감 목표 달성을 위한 액션 플랜은?",
            "원가 변동성이 높은 항목과 리스크는?",
            "품질 유지하면서 원가 절감하는 방법은?",
            "원가 성과 지표 개선 방안은?"
        ]
        return questions
    
    def get_tab_specific_system_prompt(self) -> str:
        """원가 분석 탭 특화 시스템 프롬프트"""
        return """
당신은 제조업 원가 분석 전문가입니다. 다음 영역에 특화된 분석과 조언을 제공해야 합니다:

## 핵심 전문 영역:
1. **원가 구조 분석**: 원료비, 유틸리티, 기타 비용 항목별 상세 분석
2. **원가 트렌드 분석**: 시간에 따른 원가 변동 패턴 및 요인 분석
3. **원가 성과 지표**: 단위당 원가, 생산 효율성, 원가 경쟁력 분석
4. **원가 절감 기회**: 비용 절감 잠재 영역 식별 및 개선 방안
5. **원가 벤치마킹**: 업계 표준 대비 원가 경쟁력 평가

## 분석 접근 방법:
- 원가 구조의 정량적 분석 및 시각화
- 원가 동인(Cost Driver) 분석
- 가치사슬 관점의 원가 분석
- 원가-품질-납기 트레이드오프 분석
- 원가 절감 ROI 계산

## 답변 특징:
- 구체적인 수치와 비율 제시
- 원가 항목별 상세 분석 제공
- 실행 가능한 원가 절감 방안 제시
- 원가 변동의 근본 원인 분석
- 지속가능한 원가 관리 전략 제공

제조업 현장의 실제 원가 구조와 운영 환경을 고려하여 실용적인 원가 분석을 제공하세요.
"""
    
    def get_cost_structure_insights(self, cost_breakdown: List[Dict[str, Any]]) -> str:
        """원가 구조 인사이트 생성"""
        insights = []
        
        total_cost = sum(item["금액(만원)"] for item in cost_breakdown)
        max_cost_item = max(cost_breakdown, key=lambda x: x['금액(만원)'])
        
        insights.append(f"💰 총 원가: {total_cost}만원")
        insights.append(f"📊 최대 원가 항목: {max_cost_item['항목']} ({max_cost_item['비율(%)']}%)")
        
        # 원료비 비중 분석
        material_items = [item for item in cost_breakdown if '원료' in item['항목']]
        if material_items:
            material_ratio = sum(item['비율(%)'] for item in material_items)
            insights.append(f"📦 원료비 총 비중: {material_ratio}%")
        
        # 유틸리티 비중 분석
        utility_items = [item for item in cost_breakdown if '유틸리티' in item['항목']]
        if utility_items:
            utility_ratio = sum(item['비율(%)'] for item in utility_items)
            insights.append(f"⚡ 유틸리티 비중: {utility_ratio}%")
        
        return "\n".join(insights)
    
    def format_cost_analysis_report(self, analysis_data: Dict[str, Any]) -> str:
        """원가 분석 보고서 포맷팅"""
        report = "## 📊 원가 분석 보고서\n\n"
        
        # 원가 구조 분석
        if "cost_breakdown" in analysis_data:
            report += "### 💰 원가 구조 분석\n"
            cost_breakdown = analysis_data["cost_breakdown"]
            total_cost = sum(item["금액(만원)"] for item in cost_breakdown)
            report += f"- **총 원가**: {total_cost}만원\n"
            
            for item in cost_breakdown:
                report += f"- **{item['항목']}**: {item['금액(만원)']}만원 ({item['비율(%)']}%)\n"
            report += "\n"
        
        # 원가 효율성 분석
        if "efficiency_metrics" in analysis_data:
            report += "### 📈 원가 효율성 지표\n"
            metrics = analysis_data["efficiency_metrics"]
            for metric, value in metrics.items():
                report += f"- **{metric}**: {value}\n"
            report += "\n"
        
        # 개선 권장사항
        if "improvement_recommendations" in analysis_data:
            report += "### 💡 개선 권장사항\n"
            for i, rec in enumerate(analysis_data["improvement_recommendations"], 1):
                report += f"{i}. {rec}\n"
        
        return report 