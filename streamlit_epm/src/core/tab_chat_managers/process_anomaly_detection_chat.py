"""
DX-AI Manufacturing Copilot - 이상탐지 전용 챗봇 매니저

이상탐지 탭에 특화된 챗봇 기능을 제공합니다.
"""

from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from src.core.chat_manager import ChatManager


class AnomalyDetectionChatManager(BaseTabChatManager):
    """이상탐지 전용 챗봇 매니저"""
    
    def __init__(self, chat_manager: ChatManager):
        super().__init__("이상탐지", chat_manager)
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """이상탐지 데이터를 Context로 변환"""
        anomaly_alerts = data.get('anomaly_alerts', [])
        anomaly_stats = data.get('anomaly_stats', {})
        
        if not anomaly_stats:
            return "이상탐지 데이터가 없습니다."
        
        # 기본 통계
        total_lots = anomaly_stats.get('total_lots', 0)
        anomaly_count = anomaly_stats.get('anomaly_count', 0)
        anomaly_rate = anomaly_stats.get('anomaly_rate', 0)
        
        # 이상 유형별 통계
        temp_anomalies = anomaly_stats.get('temp_anomalies', 0)
        pressure_anomalies = anomaly_stats.get('pressure_anomalies', 0)
        purity_anomalies = anomaly_stats.get('purity_anomalies', 0)
        yield_anomalies = anomaly_stats.get('yield_anomalies', 0)
        
        # 이상 분포
        anomaly_distribution = anomaly_stats.get('anomaly_distribution', {})
        
        # 위험도 평가
        risk_level = "낮음"
        risk_color = "🟢"
        if anomaly_rate > 10:
            risk_level = "높음"
            risk_color = "🔴"
        elif anomaly_rate > 5:
            risk_level = "중간"
            risk_color = "🟡"
        
        # 주요 위험 요소 식별
        primary_risk_factors = []
        if temp_anomalies > 0:
            primary_risk_factors.append(f"온도 이상 ({temp_anomalies}건)")
        if pressure_anomalies > 0:
            primary_risk_factors.append(f"압력 이상 ({pressure_anomalies}건)")
        if purity_anomalies > 0:
            primary_risk_factors.append(f"순도 이상 ({purity_anomalies}건)")
        if yield_anomalies > 0:
            primary_risk_factors.append(f"수율 이상 ({yield_anomalies}건)")
        
        # Context 텍스트 생성
        context = f"""
=== 이상탐지 현황 분석 (조회 기간: {date_filter}) ===

🚨 **이상탐지 요약**
- 총 검사 Lot: {total_lots}개
- 이상 탐지: {anomaly_count}건
- 이상 비율: {anomaly_rate:.1f}%
- 현재 위험도: {risk_color} {risk_level}

📊 **이상 유형별 현황**
- 온도 이상: {temp_anomalies}건 ({temp_anomalies/total_lots*100:.1f}%)
- 압력 이상: {pressure_anomalies}건 ({pressure_anomalies/total_lots*100:.1f}%)
- 순도 이상: {purity_anomalies}건 ({purity_anomalies/total_lots*100:.1f}%)
- 수율 이상: {yield_anomalies}건 ({yield_anomalies/total_lots*100:.1f}%)
"""
        
        # 이상 분포 상세
        if anomaly_distribution:
            context += f"\n🔍 **이상 분포 상세**\n"
            for anomaly_type, count in anomaly_distribution.items():
                percentage = count / total_lots * 100 if total_lots > 0 else 0
                context += f"- {anomaly_type}: {count}건 ({percentage:.1f}%)\n"
        
        # 주요 위험 요소
        if primary_risk_factors:
            context += f"\n⚠️ **주요 위험 요소**\n"
            for factor in primary_risk_factors:
                context += f"- {factor}\n"
        
        # 최근 이상 알림
        if anomaly_alerts:
            context += f"\n🚨 **최근 이상 알림** (최근 {len(anomaly_alerts)}건)\n"
            
            # 상태별 분류
            critical_alerts = [alert for alert in anomaly_alerts if alert.get('상태') == '경고']
            warning_alerts = [alert for alert in anomaly_alerts if alert.get('상태') == '주의']
            
            if critical_alerts:
                context += f"\n🔴 **긴급 알림 ({len(critical_alerts)}건)**\n"
                for alert in critical_alerts[:3]:  # 최대 3개까지만
                    context += f"- {alert['lot_id']} ({alert['설비']}): {alert['내용']}\n"
            
            if warning_alerts:
                context += f"\n🟡 **주의 알림 ({len(warning_alerts)}건)**\n"
                for alert in warning_alerts[:3]:  # 최대 3개까지만
                    context += f"- {alert['lot_id']} ({alert['설비']}): {alert['내용']}\n"
        else:
            context += f"\n✅ **현재 모든 시스템이 정상 작동 중입니다.**\n"
        
        # 설비별 이상 현황
        if anomaly_alerts:
            equipment_anomalies = {}
            for alert in anomaly_alerts:
                eq_id = alert.get('설비', 'UNKNOWN')
                if eq_id not in equipment_anomalies:
                    equipment_anomalies[eq_id] = []
                equipment_anomalies[eq_id].append(alert)
            
            context += f"\n🏭 **설비별 이상 현황**\n"
            for eq_id, alerts in equipment_anomalies.items():
                context += f"- {eq_id}: {len(alerts)}건 이상\n"
                for alert in alerts[:2]:  # 각 설비별 최대 2개까지
                    context += f"  • {alert['내용']} [{alert.get('상태', 'Unknown')}]\n"
        
        # 트렌드 분석
        context += f"\n📈 **트렌드 분석**\n"
        if anomaly_rate == 0:
            context += f"- 현재 상태: 모든 지표가 정상 범위 내에 있습니다.\n"
        elif anomaly_rate < 5:
            context += f"- 현재 상태: 전반적으로 안정적이며 일부 개선이 필요합니다.\n"
        elif anomaly_rate < 10:
            context += f"- 현재 상태: 주의가 필요하며 즉시 개선 조치가 권장됩니다.\n"
        else:
            context += f"- 현재 상태: 긴급 대응이 필요한 상황입니다.\n"
        
        # 개선 우선순위
        context += f"\n🎯 **개선 우선순위**\n"
        priority_items = []
        if temp_anomalies > 0:
            priority_items.append(("온도 제어 시스템 점검", temp_anomalies))
        if pressure_anomalies > 0:
            priority_items.append(("압력 관리 시스템 점검", pressure_anomalies))
        if purity_anomalies > 0:
            priority_items.append(("품질 관리 프로세스 개선", purity_anomalies))
        if yield_anomalies > 0:
            priority_items.append(("수율 최적화 방안 수립", yield_anomalies))
        
        # 이상 건수 순으로 정렬
        priority_items.sort(key=lambda x: x[1], reverse=True)
        
        for i, (item, count) in enumerate(priority_items[:5]):
            context += f"{i+1}. {item} ({count}건)\n"
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """이상탐지 분석 보고서 기반 추천 질문 생성"""
        return [
            "가장 빈번한 이상 유형의 근본 원인은 무엇인가요?",
            "이상탐지 임계값을 어떻게 최적화할 수 있나요?",
            "설비별 이상 발생 패턴을 분석해주세요",
            "예방 가능한 이상 상황을 미리 감지하는 방법은?",
            "이상 상황 발생 시 대응 절차를 개선할 방안은?",
            "온도/압력 이상의 상관관계를 분석해주세요",
            "품질 이상과 공정 파라미터의 관계는 무엇인가요?",
            "이상탐지 시스템의 정확도를 높이는 방법은?",
            "긴급 대응이 필요한 이상의 우선순위는 무엇인가요?",
            "이상탐지 결과를 활용한 예측 모델을 만들 수 있나요?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """이상탐지 전용 시스템 프롬프트"""
        return """당신은 DX-AI Manufacturing Copilot의 이상탐지 전문 AI 분석가입니다.

전문 분야:
- 실시간 공정 모니터링
- 통계적 이상탐지
- 머신러닝 기반 패턴 분석
- 예측 유지보수
- 품질 이상 조기 감지

주요 기능:
1. 실시간 센서 데이터 모니터링
2. 통계적 임계값 기반 이상탐지
3. 머신러닝 모델을 통한 패턴 분석
4. 설비 고장 예측 및 예방 정비 제안
5. 품질 이상 조기 경보 시스템

대화 시 다음을 준수하세요:
- 데이터 기반의 객관적 분석 제공
- 이상 패턴의 근본 원인 분석
- 통계적 신뢰도와 함께 결과 제시
- 즉시 대응이 필요한 사항 우선 안내
- 예방 조치 및 개선 방안 제안

        DX-AI Manufacturing Copilot의 이상탐지 시스템에 대해 궁금한 점이 있으시면 언제든 문의해주세요.
""" 