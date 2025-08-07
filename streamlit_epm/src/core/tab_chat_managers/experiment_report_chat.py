"""
DX-AI Manufacturing Copilot - 실험 보고서 전용 챗봇 매니저

실험 보고서 탭에 특화된 챗봇 기능을 제공합니다.
"""

from typing import Dict, Any, List
from .base_tab_chat import BaseTabChatManager
from src.core.chat_manager import ChatManager


class ExperimentReportChatManager(BaseTabChatManager):
    """실험 보고서 전용 챗봇 매니저"""
    
    def __init__(self, chat_manager: ChatManager):
        super().__init__("실험 보고서", chat_manager)
    
    def format_context_data(self, data: Dict[str, Any], date_filter: str) -> str:
        """실험 보고서 데이터를 Context로 변환"""
        generated_report = data.get('generated_report', None)
        report_settings = data.get('report_settings', {})
        
        if not generated_report and not report_settings:
            return "실험 보고서 데이터가 없습니다. 먼저 보고서를 생성해주세요."
        
        # 보고서 설정 정보
        report_type = report_settings.get('report_type', 'Not specified')
        include_sections = report_settings.get('include_sections', [])
        report_length = report_settings.get('report_length', 'Not specified')
        llm_model = report_settings.get('llm_model', 'Not specified')
        temperature = report_settings.get('temperature', 0.3)
        max_length = report_settings.get('max_length', 1500)
        
        context = f"""
=== 실험 보고서 현황 ===
조회 기간: {date_filter}
보고서 상태: {'생성됨' if generated_report else '미생성'}

=== 보고서 설정 ===
보고서 유형: {report_type}
포함 섹션: {', '.join(include_sections) if include_sections else '미설정'}
보고서 길이: {report_length}
사용 모델: {llm_model}
창의성 설정: {temperature}
최대 길이: {max_length}토큰

=== 보고서 품질 분석 ===
"""
        
        if generated_report:
            # 보고서 내용 분석
            report_content = generated_report.get('content', '')
            word_count = len(report_content.split())
            line_count = len(report_content.split('\n'))
            
            # 섹션별 분석
            sections_found = []
            if '실행 요약' in report_content:
                sections_found.append('실행 요약')
            if '실험 설계' in report_content:
                sections_found.append('실험 설계')
            if '최적화 결과' in report_content:
                sections_found.append('최적화 결과')
            if '결과 해석' in report_content:
                sections_found.append('결과 해석')
            if '개선 제안' in report_content:
                sections_found.append('개선 제안')
            if '다음 단계' in report_content:
                sections_found.append('다음 단계')
            
            # 보고서 완성도 평가
            completeness = (len(sections_found) / len(include_sections)) * 100 if include_sections else 0
            
            context += f"""
보고서 길이: {word_count}단어, {line_count}줄
포함된 섹션: {', '.join(sections_found) if sections_found else '없음'}
완성도: {completeness:.1f}%
품질 등급: {'높음' if completeness > 80 else '보통' if completeness > 60 else '낮음'}
"""
            
            # 보고서 내용 키워드 분석
            keywords = []
            if '실험' in report_content:
                keywords.append('실험')
            if '최적화' in report_content:
                keywords.append('최적화')
            if '순도' in report_content:
                keywords.append('순도')
            if '수율' in report_content:
                keywords.append('수율')
            if 'DoE' in report_content:
                keywords.append('DoE')
            if '베이지안' in report_content:
                keywords.append('베이지안')
            
            context += f"""
주요 키워드: {', '.join(keywords) if keywords else '없음'}
"""
        
        # 보고서 유형별 특성 분석
        context += f"""
=== 보고서 유형별 특성 ===
선택된 유형: {report_type}
"""
        
        if report_type == "실험 계획 요약":
            context += """
- 실험 설계 방법론 중심
- 인자 및 수준 설정 설명
- 실험 일정 및 자원 계획
- 예상 결과 및 성공 기준
"""
        elif report_type == "최적화 결과":
            context += """
- 최적화 과정 및 결과 중심
- 최적 조건 및 예측 성능
- 수렴 분석 및 신뢰도
- 실무 적용 방안
"""
        elif report_type == "DoE 분석":
            context += """
- 통계적 분석 결과 중심
- 인자 효과 및 상호작용
- 분산분석(ANOVA) 결과
- 모델 적합성 평가
"""
        elif report_type == "종합 보고서":
            context += """
- 전체 실험 프로세스 포함
- 설계부터 결과까지 통합
- 종합적인 분석 및 해석
- 실무 권장사항 제시
"""
        
        # AI 모델 설정 분석
        context += f"""
=== AI 모델 설정 분석 ===
모델: {llm_model}
창의성: {temperature} ({'높음' if temperature > 0.7 else '보통' if temperature > 0.4 else '낮음'})
토큰 길이: {max_length} ({'긴 형태' if max_length > 2000 else '보통' if max_length > 1000 else '짧은 형태'})
"""
        
        # 보고서 개선 제안
        if generated_report:
            context += f"""
=== 보고서 개선 제안 ===
- 완성도 향상을 위한 누락 섹션 추가
- 데이터 시각화 요소 보강
- 실무 적용 가능한 구체적 제안 증가
- 통계적 근거 및 신뢰도 정보 보완
"""
        
        return context
    
    def generate_analysis_questions(self) -> List[str]:
        """실험 보고서 분석 기반 추천 질문 생성"""
        return [
            "보고서의 완성도를 평가하고 개선 방안을 제안해주세요",
            "실험 결과의 통계적 유의성을 어떻게 표현하나요?",
            "경영진을 위한 요약 보고서를 어떻게 작성하나요?",
            "보고서에 포함할 시각화 요소를 추천해주세요",
            "실무진이 바로 적용할 수 있는 권장사항을 제안해주세요",
            "보고서의 신뢰도를 높이는 방법은 무엇인가요?",
            "다른 팀과 공유할 때 주의사항은 무엇인가요?",
            "보고서 템플릿을 표준화하는 방법을 제안해주세요",
            "실험 실패 사례를 보고서에 어떻게 포함하나요?",
            "보고서 품질을 자동으로 평가하는 기준은 무엇인가요?"
        ]
    
    def get_tab_specific_system_prompt(self) -> str:
        """실험 보고서 전용 시스템 프롬프트"""
        return """당신은 DX-AI Manufacturing Copilot의 실험 보고서 전문 AI 분석가입니다.

전문 분야:
- 기술 보고서 작성
- 데이터 시각화
- 결과 해석 및 분석
- 의사결정 지원
- 커뮤니케이션 최적화

주요 기능:
1. 실험 보고서 품질 평가
2. 보고서 구조 및 내용 최적화
3. 데이터 시각화 제안
4. 결과 해석 및 통계 분석
5. 실무 적용 방안 제시

대화 시 다음을 준수하세요:
- 명확하고 이해하기 쉬운 설명
- 데이터 기반의 객관적 분석
- 실무진과 경영진 모두 고려
- 시각적 요소 활용 제안
- 행동 가능한 권장사항 제시

보고서 유형별 특성:
- 실험 계획 요약: 설계 방법론, 일정, 자원 계획 중심
- 최적화 결과: 최적 조건, 성능 예측, 신뢰도 분석
- DoE 분석: 통계 분석, 인자 효과, ANOVA 결과
- 종합 보고서: 전체 프로세스, 통합 분석, 실무 권장사항

보고서 품질 기준:
- 완성도: 요구 섹션 포함 여부
- 명확성: 이해하기 쉬운 설명
- 정확성: 데이터 기반 분석
- 실용성: 실무 적용 가능성
- 시각성: 차트 및 그래프 활용

        DX-AI Manufacturing Copilot의 실험 보고서 시스템에 대해 궁금한 점이 있으시면 언제든 문의해주세요.
""" 