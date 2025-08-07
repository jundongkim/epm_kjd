"""
DX-AI Manufacturing Copilot - 설비 모니터링 전용 챗봇 매니저

설비 모니터링 탭에 특화된 챗봇 기능을 제공합니다.
"""

from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from src.core.chat_manager import ChatManager


class EquipmentMonitoringChatManager(BaseTabChatManager):
    """설비 모니터링 전용 챗봇 매니저"""
    
    def __init__(self, chat_manager: ChatManager):
        super().__init__("설비 모니터링", chat_manager)
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """설비 모니터링 데이터를 Context로 변환"""
        equipment_status = data.get('equipment_status', [])
        equipment_stats = data.get('equipment_stats', {})
        
        if not equipment_status:
            return "설비 모니터링 데이터가 없습니다."
        
        # 설비 상태별 통계
        status_counts = {}
        utilization_rates = []
        for eq in equipment_status:
            status = eq["상태"]
            status_counts[status] = status_counts.get(status, 0) + 1
            utilization_rates.append(eq["가동률"])
        
        avg_utilization = sum(utilization_rates) / len(utilization_rates) if utilization_rates else 0
        max_utilization = max(utilization_rates) if utilization_rates else 0
        min_utilization = min(utilization_rates) if utilization_rates else 0
        
        # 성능 지표 계산
        performance_summary = {}
        if equipment_stats:
            for eq_id, stats in equipment_stats.items():
                performance_summary[eq_id] = {
                    'avg_purity': stats.get('avg_purity', 0),
                    'avg_yield': stats.get('avg_yield', 0),
                    'completion_rate': stats.get('completion_rate', 0),
                    'total_lots': stats.get('total_lots', 0)
                }
        
        # 가동률 분포
        utilization_distribution = {
            'high': len([u for u in utilization_rates if u >= 80]),
            'medium': len([u for u in utilization_rates if 50 <= u < 80]),
            'low': len([u for u in utilization_rates if u < 50])
        }
        
        # Context 텍스트 생성
        context = f"""
=== 설비 모니터링 현황 분석 (조회 기간: {date_filter}) ===

🏭 **설비 상태 요약**
- 전체 설비 수: {len(equipment_status)}개
- 평균 가동률: {avg_utilization:.1f}%
- 최고 가동률: {max_utilization:.1f}%
- 최저 가동률: {min_utilization:.1f}%

📊 **설비 상태별 분포**
"""
        
        for status, count in status_counts.items():
            percentage = count / len(equipment_status) * 100
            context += f"- {status}: {count}개 ({percentage:.1f}%)\n"
        
        context += f"""
🎯 **가동률 분포**
- 고가동률 (80% 이상): {utilization_distribution['high']}개
- 중가동률 (50-80%): {utilization_distribution['medium']}개
- 저가동률 (50% 미만): {utilization_distribution['low']}개

📈 **설비별 상세 현황**
"""
        
        for eq in equipment_status:
            context += f"- {eq['ID']}: {eq['상태']}, 가동률 {eq['가동률']}%, 마지막 점검 {eq['마지막 점검']}, 총 Lot {eq['총 Lot']}개\n"
        
        # 성능 지표
        if performance_summary:
            context += f"\n🔧 **설비별 성능 지표**\n"
            for eq_id, perf in performance_summary.items():
                context += f"- {eq_id}: 평균 순도 {perf['avg_purity']:.1f}%, 평균 수율 {perf['avg_yield']:.1f}%, 완료율 {perf['completion_rate']:.1f}%, 총 Lot {perf['total_lots']}개\n"
        
        # 주요 이슈 식별
        context += f"\n⚠️ **주요 이슈 식별**\n"
        
        # 저가동률 설비
        low_utilization_equipment = [eq for eq in equipment_status if eq["가동률"] < 50]
        if low_utilization_equipment:
            context += f"- 저가동률 설비: {', '.join([eq['ID'] for eq in low_utilization_equipment])}\n"
        
        # 점검 필요 설비
        maintenance_needed = [eq for eq in equipment_status if eq["상태"] == "점검 필요"]
        if maintenance_needed:
            context += f"- 점검 필요 설비: {', '.join([eq['ID'] for eq in maintenance_needed])}\n"
        
        # 고성능 설비
        high_performance_equipment = [eq for eq in equipment_status if eq["가동률"] >= 90]
        if high_performance_equipment:
            context += f"\n✅ **고성능 설비**\n"
            for eq in high_performance_equipment:
                context += f"- {eq['ID']}: 가동률 {eq['가동률']}%, 상태 {eq['상태']}\n"
        
        # 설비 효율성 랭킹
        sorted_equipment = sorted(equipment_status, key=lambda x: x["가동률"], reverse=True)
        context += f"\n🏆 **설비 효율성 랭킹** (상위 5개)\n"
        for i, eq in enumerate(sorted_equipment[:5]):
            context += f"{i+1}. {eq['ID']}: 가동률 {eq['가동률']}%, 상태 {eq['상태']}\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """설비 모니터링 분석 보고서 기반 추천 질문 생성"""
        return [
            "가동률이 낮은 설비들의 공통 문제는 무엇인가요?",
            "설비별 성능 차이의 근본 원인을 분석해주세요",
            "예방 정비 계획을 어떻게 수립해야 하나요?",
            "설비 효율성을 높이는 구체적인 방안을 제안해주세요",
            "점검이 필요한 설비의 우선순위를 정해주세요",
            "고성능 설비의 성공 요인을 다른 설비에 적용할 수 있나요?",
            "설비 가동률 목표 설정 기준을 제안해주세요",
            "설비 교체 시기를 판단하는 기준은 무엇인가요?",
            "전체 설비 운영 효율성을 개선하는 방법은?",
            "설비 모니터링 지표를 개선할 방안은 무엇인가요?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """설비 모니터링 전용 시스템 프롬프트"""
        return """당신은 DX-AI Manufacturing Copilot의 설비 모니터링 전문 AI 분석가입니다.

전문 분야:
- 설비 성능 모니터링
- 가동률 및 효율성 분석
- 예방 정비 계획
- 설비 최적화
- 에너지 효율성 관리

주요 기능:
1. 실시간 설비 상태 모니터링
2. 가동률 및 OEE(Overall Equipment Effectiveness) 분석
3. 설비 성능 트렌드 분석
4. 예방 정비 스케줄링
5. 설비 최적화 제안

대화 시 다음을 준수하세요:
- 설비 성능 데이터의 정확한 해석
- 가동률과 효율성 지표 분석
- 예방 정비의 경제적 효과 고려
- 설비 수명 연장 방안 제시
- 에너지 절약 및 환경 영향 고려

        DX-AI Manufacturing Copilot의 설비 모니터링 시스템에 대해 궁금한 점이 있으시면 언제든 문의해주세요.
""" 