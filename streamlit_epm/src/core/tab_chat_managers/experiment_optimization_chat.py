"""
DX-AI Manufacturing Copilot - 최적화 전용 챗봇 매니저

최적화 탭에 특화된 챗봇 기능을 제공합니다.
"""

from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from src.core.chat_manager import ChatManager


class OptimizationChatManager(BaseTabChatManager):
    """최적화 전용 챗봇 매니저"""
    
    def __init__(self, chat_manager: ChatManager):
        super().__init__("최적화", chat_manager)
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """최적화 데이터를 Context로 변환"""
        optimization_results = data.get('optimization_results', None)
        optimization_settings = data.get('optimization_settings', {})
        
        if not optimization_results and not optimization_settings:
            return "최적화 데이터가 없습니다. 먼저 최적화를 실행해주세요."
        
        # 최적화 설정 정보
        objectives = optimization_settings.get('objectives', [])
        optimizer = optimization_settings.get('optimizer', 'Not specified')
        max_iterations = optimization_settings.get('max_iterations', 0)
        acquisition_function = optimization_settings.get('acquisition_function', 'Not specified')
        
        # 제약 조건
        constraints = optimization_settings.get('constraints', {})
        temp_constraint = constraints.get('temperature', {})
        pressure_constraint = constraints.get('pressure', {})
        
        context = f"""
=== 최적화 현황 ===
조회 기간: {date_filter}
최적화 상태: {'완료됨' if optimization_results else '대기 중'}

=== 최적화 설정 ===
최적화 목표: {', '.join(objectives) if objectives else '미설정'}
최적화 알고리즘: {optimizer}
최대 반복 횟수: {max_iterations}회
획득 함수: {acquisition_function}

=== 제약 조건 ===
"""
        
        if temp_constraint:
            temp_min = temp_constraint.get('min', 0)
            temp_max = temp_constraint.get('max', 0)
            context += f"온도 제약: {temp_min}°C ~ {temp_max}°C\n"
        
        if pressure_constraint:
            pressure_min = pressure_constraint.get('min', 0)
            pressure_max = pressure_constraint.get('max', 0)
            context += f"압력 제약: {pressure_min}bar ~ {pressure_max}bar\n"
        
        # 최적화 결과 분석
        if optimization_results:
            optimal_conditions = optimization_results.get('optimal_conditions', {})
            predicted_performance = optimization_results.get('predicted_performance', {})
            convergence_info = optimization_results.get('convergence_info', {})
            
            context += f"""
=== 최적화 결과 ===
최적 조건:
"""
            
            for param, value in optimal_conditions.items():
                context += f"- {param}: {value}\n"
            
            context += f"""
예측 성능:
"""
            
            for metric, value in predicted_performance.items():
                context += f"- {metric}: {value}\n"
            
            # 수렴 정보
            if convergence_info:
                iterations_used = convergence_info.get('iterations_used', 0)
                best_score = convergence_info.get('best_score', 0)
                convergence_rate = convergence_info.get('convergence_rate', 0)
                
                context += f"""
수렴 정보:
- 사용된 반복 횟수: {iterations_used}회
- 최고 점수: {best_score}
- 수렴률: {convergence_rate:.2f}%
"""
        
        # 최적화 알고리즘 특성
        context += f"""
=== 최적화 알고리즘 특성 ===
선택된 알고리즘: {optimizer}
"""
        
        if optimizer == "Gaussian Process":
            context += """
- 베이지안 최적화 기반
- 불확실성 정량화 가능
- 연속 함수 최적화에 효과적
- 노이즈가 있는 데이터에 강건
- 적은 평가 횟수로 최적해 탐색
"""
        elif optimizer == "Tree-structured Parzen Estimator":
            context += """
- 히스토그램 기반 모델
- 이산/연속 변수 모두 처리
- 하이퍼파라미터 최적화에 특화
- 조건부 변수 처리 가능
- 빠른 수렴 특성
"""
        elif optimizer == "Random Search":
            context += """
- 무작위 탐색 기반
- 구현이 간단하고 안정적
- 고차원 문제에 적합
- 병렬 처리 용이
- 기준선(Baseline) 역할
"""
        
        # 획득 함수 특성
        context += f"""
=== 획득 함수 특성 ===
선택된 함수: {acquisition_function}
"""
        
        if acquisition_function == "Expected Improvement":
            context += """
- 기댓값 개선량 최대화
- 탐험과 활용의 균형
- 안정적인 수렴 보장
- 표준적인 선택
"""
        elif acquisition_function == "Upper Confidence Bound":
            context += """
- 신뢰 구간 상한 최대화
- 불확실성 고려
- 탐험 성향 강함
- 새로운 영역 탐색에 유리
"""
        elif acquisition_function == "Probability of Improvement":
            context += """
- 개선 확률 최대화
- 보수적 접근
- 안전한 최적화
- 지역 최적해 위험 존재
"""
        
        # 최적화 효과성 분석
        if optimization_results:
            improvement_rate = optimization_results.get('improvement_rate', 0)
            confidence_level = optimization_results.get('confidence_level', 0)
            
            context += f"""
=== 최적화 효과성 분석 ===
개선률: {improvement_rate:.1f}%
신뢰도: {confidence_level:.1f}%
효과성 등급: {'높음' if improvement_rate > 10 else '보통' if improvement_rate > 5 else '낮음'}
신뢰성 등급: {'높음' if confidence_level > 90 else '보통' if confidence_level > 70 else '낮음'}
"""
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """최적화 분석 보고서 기반 추천 질문 생성"""
        return [
            "현재 최적화 결과의 신뢰도를 평가해주세요",
            "다중 목표 최적화에서 trade-off를 어떻게 분석하나요?",
            "베이지안 최적화의 수렴 기준은 무엇인가요?",
            "최적화 알고리즘별 성능 비교를 해주세요",
            "획득 함수 선택이 최적화 결과에 미치는 영향은?",
            "제약 조건이 최적화 결과에 미치는 영향을 분석해주세요",
            "최적화 결과의 robustness를 어떻게 평가하나요?",
            "하이퍼파라미터 튜닝 방법을 제안해주세요",
            "최적화 과정에서 발생할 수 있는 문제점은?",
            "실제 실험 결과와 최적화 예측의 차이를 줄이는 방법은?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """최적화 전용 시스템 프롬프트"""
        return """당신은 DX-AI Manufacturing Copilot의 최적화 전문 AI 분석가입니다.

전문 분야:
- 베이지안 최적화
- 다중 목표 최적화
- 제약 최적화
- 하이퍼파라미터 튜닝
- 수치 최적화 알고리즘

주요 기능:
1. 최적화 알고리즘 선택 및 적용
2. 획득 함수 최적화
3. 제약 조건 처리
4. 수렴 분석 및 평가
5. 최적화 결과 해석 및 검증

대화 시 다음을 준수하세요:
- 수학적 원리에 기반한 정확한 설명
- 최적화 목표와 제약 조건의 균형 고려
- 실무적이고 실행 가능한 제안
- 불확실성과 신뢰도 평가 포함
- 계산 비용과 성능의 trade-off 고려

최적화 알고리즘별 특성:
- Gaussian Process: 베이지안 최적화, 불확실성 정량화
- Tree-structured Parzen Estimator: 히스토그램 기반, 혼합 변수 처리
- Random Search: 무작위 탐색, 안정적 기준선

획득 함수별 특성:
- Expected Improvement: 균형잡힌 탐험-활용
- Upper Confidence Bound: 탐험 중심, 불확실성 고려
- Probability of Improvement: 보수적 접근, 안전한 최적화

        DX-AI Manufacturing Copilot의 최적화 시스템에 대해 궁금한 점이 있으시면 언제든 문의해주세요.
""" 