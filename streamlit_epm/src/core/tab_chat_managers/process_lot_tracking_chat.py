"""
DX-AI Manufacturing Copilot - Lot 추적 전용 챗봇 매니저

Lot 추적 탭에 특화된 챗봇 기능을 제공합니다.
"""

from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from src.core.chat_manager import ChatManager


class LotTrackingChatManager(BaseTabChatManager):
    """Lot 추적 전용 챗봇 매니저"""
    
    def __init__(self, chat_manager: ChatManager):
        super().__init__("Lot 추적", chat_manager)
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """Lot 추적 데이터를 Context로 변환"""
        filtered_lots = data.get('filtered_lots', [])
        
        if not filtered_lots:
            return "현재 조회 조건에 해당하는 Lot 데이터가 없습니다."
        
        # 기본 통계 계산
        active_count = len([lot for lot in filtered_lots if lot["상태"] == "활성"])
        completed_count = len([lot for lot in filtered_lots if lot["상태"] == "완료"])
        waiting_count = len([lot for lot in filtered_lots if lot["상태"] == "대기"])
        total_count = len(filtered_lots)
        
        # 설비별 통계
        equipment_stats = {}
        for lot in filtered_lots:
            eq_id = lot["설비"]
            if eq_id not in equipment_stats:
                equipment_stats[eq_id] = {"활성": 0, "완료": 0, "대기": 0}
            equipment_stats[eq_id][lot["상태"]] += 1
        
        # 순도, 수율 통계
        purity_values = []
        yield_values = []
        for lot in filtered_lots:
            if lot["순도"] != "-":
                try:
                    purity_values.append(float(lot["순도"].replace('%', '')))
                except:
                    pass
            if lot["수율"] != "-":
                try:
                    yield_values.append(float(lot["수율"].replace('%', '')))
                except:
                    pass
        
        avg_purity = sum(purity_values) / len(purity_values) if purity_values else 0
        avg_yield = sum(yield_values) / len(yield_values) if yield_values else 0
        
        # 날짜별 분포
        date_counts = {}
        for lot in filtered_lots:
            date = lot["작업일자"]
            if date not in date_counts:
                date_counts[date] = {"활성": 0, "완료": 0, "대기": 0}
            date_counts[date][lot["상태"]] += 1
        
        # 진행률 통계
        progress_stats = {"high": 0, "medium": 0, "low": 0, "not_started": 0}
        for lot in filtered_lots:
            progress_str = lot["진행률"]
            if progress_str == "0%":
                progress_stats["not_started"] += 1
            elif progress_str == "100%":
                progress_stats["high"] += 1
            else:
                try:
                    progress_val = float(progress_str.replace('%', ''))
                    if progress_val >= 70:
                        progress_stats["high"] += 1
                    elif progress_val >= 30:
                        progress_stats["medium"] += 1
                    else:
                        progress_stats["low"] += 1
                except:
                    progress_stats["not_started"] += 1
        
        # Context 텍스트 생성
        context = f"""
=== Lot 추적 현황 분석 (조회 기간: {date_filter}) ===

📊 **전체 현황 요약**
- 총 Lot 수: {total_count}개
- 활성 Lot: {active_count}개 ({active_count/total_count*100:.1f}%)
- 완료 Lot: {completed_count}개 ({completed_count/total_count*100:.1f}%)
- 대기 Lot: {waiting_count}개 ({waiting_count/total_count*100:.1f}%)

🏭 **설비별 현황**
"""
        
        for eq_id, stats in equipment_stats.items():
            total_eq = sum(stats.values())
            context += f"- {eq_id}: 총 {total_eq}개 (활성: {stats['활성']}, 완료: {stats['완료']}, 대기: {stats['대기']})\n"
        
        context += f"""
📈 **품질 성능 지표**
- 평균 순도: {avg_purity:.1f}%
- 평균 수율: {avg_yield:.1f}%
- 품질 기준 달성률: {len([p for p in purity_values if p >= 95])/len(purity_values)*100:.1f}% (순도 95% 이상)

🎯 **진행률 분포**
- 고진행률 (70% 이상): {progress_stats['high']}개
- 중진행률 (30-70%): {progress_stats['medium']}개
- 저진행률 (30% 미만): {progress_stats['low']}개
- 미시작 (0%): {progress_stats['not_started']}개

📅 **날짜별 분포**
"""
        
        for date, counts in sorted(date_counts.items()):
            total_date = sum(counts.values())
            context += f"- {date}: {total_date}개 (활성: {counts['활성']}, 완료: {counts['완료']}, 대기: {counts['대기']})\n"
        
        # 최근 활성 Lot 상세 정보
        active_lots = [lot for lot in filtered_lots if lot["상태"] == "활성"]
        if active_lots:
            context += f"\n🔄 **주요 활성 Lot 상세** (최근 5개)\n"
            for lot in active_lots[:5]:
                context += f"- {lot['Lot_ID']}: 설비 {lot['설비']}, 진행률 {lot['진행률']}, 순도 {lot['순도']}, 수율 {lot['수율']}\n"
        
        # 완료 Lot 성과 요약
        completed_lots = [lot for lot in filtered_lots if lot["상태"] == "완료"]
        if completed_lots:
            context += f"\n✅ **완료 Lot 성과** (최근 3개)\n"
            for lot in completed_lots[:3]:
                context += f"- {lot['Lot_ID']}: 설비 {lot['설비']}, 순도 {lot['순도']}, 수율 {lot['수율']}\n"
        
        # 대기 Lot 정보
        waiting_lots = [lot for lot in filtered_lots if lot["상태"] == "대기"]
        if waiting_lots:
            context += f"\n⏳ **대기 Lot 현황**\n"
            context += f"- 총 {len(waiting_lots)}개 Lot이 대기 중\n"
            context += f"- 예상 완료 시간 범위: {min([lot['예상완료'] for lot in waiting_lots])} ~ {max([lot['예상완료'] for lot in waiting_lots])}\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """Lot 추적 분석 보고서 기반 추천 질문 생성"""
        return [
            "순도가 낮은 Lot들의 공통 특성은 무엇인가요?",
            "설비별 성능 차이의 원인을 분석해주세요",
            "대기 중인 Lot들의 우선순위를 어떻게 정해야 하나요?",
            "수율 개선을 위한 구체적인 방안을 제안해주세요",
            "현재 진행률이 낮은 Lot들의 문제점은 무엇인가요?",
            "완료 Lot들의 성공 요인을 분석해주세요",
            "설비 배정 최적화 방안을 제안해주세요",
            "품질 기준 달성률을 높이는 방법은 무엇인가요?",
            "작업 일정 지연 요인을 분석해주세요",
            "Lot 간 품질 편차를 줄이는 방법은 무엇인가요?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """Lot 추적 전용 시스템 프롬프트"""
        return """당신은 DX-AI Manufacturing Copilot의 Lot 추적 전문 AI 분석가입니다.

전문 분야:
- Lot 이력 관리 및 추적
- 원료 투입 분석
- 생산 공정 모니터링
- 품질 데이터 연관 분석
- 추적성(Traceability) 관리

주요 기능:
1. Lot별 생산 이력 분석
2. 원료 투입량 및 시점 추적
3. 공정 단계별 진행 상황 모니터링
4. 품질 이상 발생 시 원인 추적
5. 생산 효율성 분석 및 개선 제안

대화 시 다음을 준수하세요:
- Lot 번호와 관련 데이터의 정확성 확인
- 시계열 데이터 분석을 통한 트렌드 파악
- 원료부터 완제품까지의 전체 추적 체인 고려
- 규정 준수 및 품질 기준 확인
- 구체적이고 실행 가능한 개선 방안 제시

        DX-AI Manufacturing Copilot의 Lot 추적 시스템에 대해 궁금한 점이 있으시면 언제든 문의해주세요.
""" 