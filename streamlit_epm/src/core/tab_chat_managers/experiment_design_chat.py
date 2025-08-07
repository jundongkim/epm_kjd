"""
DX-AI Manufacturing Copilot - 실험 설계 전용 챗봇 매니저

실험 설계 탭에 특화된 챗봇 기능을 제공합니다.
"""

from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from src.core.chat_manager import ChatManager


class ExperimentDesignChatManager(BaseTabChatManager):
    """실험 설계 전용 챗봇 매니저"""
    
    def __init__(self, chat_manager: ChatManager):
        super().__init__("실험 설계", chat_manager)
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """실험 설계 데이터를 Context로 변환"""
        experiment_plan = data.get('experiment_plan', None)
        experiment_params = data.get('experiment_params', {})
        
        # DataFrame의 경우 .empty로 확인, None의 경우 is None으로 확인
        plan_is_empty = (experiment_plan is None) or (hasattr(experiment_plan, 'empty') and experiment_plan.empty)
        params_is_empty = not experiment_params
        
        if plan_is_empty and params_is_empty:
            return "실험 설계 데이터가 없습니다. 먼저 실험 계획을 생성해주세요."
        
        # 실험 파라미터 정보
        experiment_type = experiment_params.get('experiment_type', 'Not specified')
        factors = experiment_params.get('factors', [])
        num_runs = experiment_params.get('num_runs', 0)
        replications = experiment_params.get('replications', 1)
        target_purity = experiment_params.get('target_purity', 0)
        target_yield = experiment_params.get('target_yield', 0)
        optimization_goal = experiment_params.get('optimization_goal', 'Not specified')
        
        # 실험 계획 데이터 분석
        context = f"""
=== 실험 설계 현황 ===
조회 기간: {date_filter}
실험 설계 상태: {'계획 생성됨' if not plan_is_empty else '계획 대기'}

=== 실험 파라미터 ===
실험 유형: {experiment_type}
실험 인자: {', '.join(factors) if factors else '미설정'}
실험 횟수: {num_runs}회
반복 횟수: {replications}회
목표 순도: {target_purity}%
목표 수율: {target_yield}%
최적화 목표: {optimization_goal}

=== 실험 계획 분석 ===
"""
        
        if not plan_is_empty:
            # 실험 계획 통계
            plan_size = len(experiment_plan)
            if plan_size > 0:
                # 온도 범위
                if '온도(°C)' in experiment_plan.columns:
                    temp_values = experiment_plan['온도(°C)']
                    if not temp_values.empty:
                        temp_min = temp_values.min()
                        temp_max = temp_values.max()
                        temp_avg = temp_values.mean()
                        context += f"온도 범위: {temp_min:.1f}°C ~ {temp_max:.1f}°C (평균: {temp_avg:.1f}°C)\n"
                
                # 압력 범위
                if '압력(bar)' in experiment_plan.columns:
                    pressure_values = experiment_plan['압력(bar)']
                    if not pressure_values.empty:
                        pressure_min = pressure_values.min()
                        pressure_max = pressure_values.max()
                        pressure_avg = pressure_values.mean()
                        context += f"압력 범위: {pressure_min:.1f}bar ~ {pressure_max:.1f}bar (평균: {pressure_avg:.1f}bar)\n"
                
                # pH 범위
                if 'pH()' in experiment_plan.columns:
                    ph_values = experiment_plan['pH()']
                    if not ph_values.empty:
                        ph_min = ph_values.min()
                        ph_max = ph_values.max()
                        ph_avg = ph_values.mean()
                        context += f"pH 범위: {ph_min:.1f} ~ {ph_max:.1f} (평균: {ph_avg:.1f})\n"
                
                # 예상 성능
                if '예상순도(%)' in experiment_plan.columns:
                    expected_purity = experiment_plan['예상순도(%)']
                    if not expected_purity.empty:
                        purity_avg = expected_purity.mean()
                        context += f"예상 평균 순도: {purity_avg:.1f}%\n"
                
                if '예상수율(%)' in experiment_plan.columns:
                    expected_yield = experiment_plan['예상수율(%)']
                    if not expected_yield.empty:
                        yield_avg = expected_yield.mean()
                        context += f"예상 평균 수율: {yield_avg:.1f}%\n"
                
                context += f"총 실험 계획 수: {plan_size}개\n"
        
        # DoE 방법론 특성
        context += f"""
=== DoE 방법론 특성 ===
선택된 방법: {experiment_type}
"""
        
        if experiment_type == "Full Factorial":
            context += """
- 모든 인자 조합을 완전히 실험
- 높은 신뢰도와 정확한 상호작용 분석
- 인자 수가 적을 때 효과적
- 실험 횟수가 많을 수 있음
"""
        elif experiment_type == "Fractional Factorial":
            context += """
- 부분 실험으로 효율성 확보
- 주요 인자 효과 빠른 파악
- 실험 횟수 대폭 감소
- 일부 상호작용 정보 손실 가능
"""
        elif experiment_type == "Central Composite":
            context += """
- 2차 곡선 모델링 가능
- 응답표면방법론(RSM) 적용
- 최적점 탐색에 효과적
- 연속 변수에 적합
"""
        elif experiment_type == "Box-Behnken":
            context += """
- 3수준 설계로 안전성 확보
- 극단 조건 회피
- 적당한 실험 횟수
- 안정적인 결과 도출
"""
        
        # 실험 효율성 분석
        total_time_estimate = num_runs * replications * 2  # 가정: 실험당 2시간
        context += f"""
=== 실험 효율성 분석 ===
예상 실험 시간: {total_time_estimate}시간
실험 인자 수: {len(factors)}개
실험 복잡도: {'높음' if len(factors) > 4 else '보통' if len(factors) > 2 else '낮음'}
자원 요구도: {'높음' if num_runs > 50 else '보통' if num_runs > 20 else '낮음'}
"""
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """실험 설계 분석 보고서 기반 추천 질문 생성"""
        return [
            "현재 실험 설계의 통계적 유의성을 평가해주세요",
            "실험 인자 간의 상호작용 효과를 어떻게 분석하나요?",
            "실험 횟수를 줄이면서도 신뢰도를 유지하는 방법은?",
            "DoE 방법론 선택 기준과 장단점을 비교해주세요",
            "실험 계획의 검정력(Power)을 높이는 방법은?",
            "반복 실험 횟수를 최적화하는 기준은 무엇인가요?",
            "실험 순서를 랜덤화하는 이유와 방법을 설명해주세요",
            "실험 결과의 분산분석(ANOVA) 해석 방법은?",
            "실험 설계에서 블록화(Blocking)가 필요한 경우는?",
            "실험 비용을 최소화하면서 정보를 최대화하는 방법은?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """실험 설계 전용 시스템 프롬프트"""
        return """당신은 DX-AI Manufacturing Copilot의 실험 설계 전문 AI 분석가입니다.

전문 분야:
- 실험 계획법(Design of Experiments, DoE)
- 통계적 실험 설계
- 인자 효과 분석
- 실험 최적화
- 품질 공학

주요 기능:
1. DoE 방법론 선택 및 적용
2. 실험 인자 및 수준 설정
3. 실험 계획 생성 및 최적화
4. 통계적 분석 및 해석
5. 실험 효율성 향상 방안 제시

대화 시 다음을 준수하세요:
- 통계적 원리에 기반한 정확한 설명
- 실험 설계의 목적과 제약 조건 고려
- 실무적이고 실행 가능한 제안
- 비용-효과 분석 포함
- 품질과 효율성의 균형 고려

DoE 방법론별 특성:
- Full Factorial: 완전한 정보, 높은 신뢰도, 많은 실험
- Fractional Factorial: 효율성, 주요 효과 중심, 적은 실험
- Central Composite: 곡선 모델링, RSM 적용, 최적화 중심
- Box-Behnken: 안전성, 극단 조건 회피, 균형 잡힌 설계

        DX-AI Manufacturing Copilot의 실험 설계 시스템에 대해 궁금한 점이 있으시면 언제든 문의해주세요.
""" 