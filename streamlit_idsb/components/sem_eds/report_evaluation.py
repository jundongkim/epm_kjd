"""
SEM-EDS 분석 보고서 평가 모듈
"""

import re
import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

def evaluate_report_quality(report_content, analysis_type):
    """마크다운 보고서 내용을 분석하여 품질을 평가

    Args:
        report_content (str): 평가할 마크다운 보고서 내용
        analysis_type (str): 분석 유형 ("SEM", "EDS", "OPERATION", "EQUIPMENT")

    Returns:
        dict: 평가 결과 (구조, 내용, 형식 등)
    """
    # 평가 결과 초기화
    evaluation = {
        'structure': {},         # 필수 섹션 포함 여부
        'content': {},           # 콘텐츠 세부 정보 포함 여부
        'format': {              # 형식 준수 여부
            'bold_count': 0      # 볼드체 사용 횟수
        },
        'expertise': {           # 전문성 평가
            'score': 0,          # 전문성 점수
            'feedback': ""       # 전문성 피드백
        },
        'clarity': {             # 명확성 평가
            'score': 0,          # 명확성 점수
            'feedback': ""       # 명확성 피드백
        },
        'evidence': {            # 분석 근거 평가
            'score': 0,          # 분석 근거 점수
            'feedback': ""       # 분석 근거 피드백
        },
        'warnings': [],          # 개선 필요 사항
        'overall_score': 0,      # 종합 점수
        'debug_info': {}         # 디버깅 정보 추가
    }

    # 분석 유형별 필수 섹션 및 키워드 정의
    required_sections = {
        'SEM': {
            '크기 분석 결과': ['스케일', '크기', '분포'],
            '형태 분석 결과': ['형태', '표면', '상태'],
            '종합 평가': ['발견', '권장', '분석']
        },
        'EDS': {
            '원소 조성 분석': ['원소', '함량', '조성'],
            '산화 상태 분석': ['산소', '산화', '원인'],
            '강종 추정': ['강종', '물질', '판단'],
            '종합 평가': ['발견', '권장', '분석']
        },
        'OPERATION': {
            '입자 특성 요약': ['SEM', 'EDS', '형태', '조성'],
            '작동 모드 추정': ['모드', '판단', '근거', '신뢰도'],
            '결론 및 제안': ['발견', '관리', '저감']
        }
    }

    # 구조 완전성 평가 (필수 섹션 포함 여부) - 유연한 패턴으로 수정
    evaluation['debug_info']['found_sections'] = []  # 디버깅: 찾은 섹션 저장

    # 모든 마크다운 헤더 파싱 (디버깅용)
    all_headers = re.findall(r'(#{1,6}\s+.+)', report_content)
    evaluation['debug_info']['all_headers'] = all_headers

    for section, keywords in required_sections[analysis_type].items():
        # 더 유연한 섹션 헤더 패턴 (여러 가지 변형 감지)
        # 패턴 1: #로 시작하는 헤더에서 섹션명을 포함하는 경우
        section_pattern1 = r'#{1,6}\s+.*' + re.escape(section) + r'.*'

        # 패턴 2: 번호 형식으로 시작하는 헤더에서 섹션명을 포함하는 경우
        section_pattern2 = r'#{1,6}\s+\d+\.?\s+.*' + re.escape(section) + r'.*'

        match1 = re.search(section_pattern1, report_content)
        match2 = re.search(section_pattern2, report_content)

        # 어떤 패턴이든 일치하면 섹션 존재로 판단
        section_exists = bool(match1) or bool(match2)

        # 대체 방법: 일반 텍스트 내에서 섹션명에 대한 포괄적인 검색
        if not section_exists:
            # 보다 느슨한 패턴으로 검색 시도 (볼드체 또는 이탤릭체로 강조된 섹션명)
            alt_pattern = r'\*\*.*' + re.escape(section) + r'.*\*\*|\*.*' + re.escape(section) + r'.*\*'
            section_exists = bool(re.search(alt_pattern, report_content))

        evaluation['structure'][section] = section_exists

        # 디버깅 정보 저장
        if section_exists:
            evaluation['debug_info']['found_sections'].append(section)
            found_match = match1.group(0) if match1 else (match2.group(0) if match2 else "Alt pattern matched")
            evaluation['debug_info'][f'match_{section}'] = found_match

        if not section_exists:
            evaluation['warnings'].append(f"'{section}' 섹션이 보고서에 없습니다.")

    # 형식 준수 평가 (볼드체 사용)
    bold_matches = re.findall(r'\*\*([^*]+)\*\*', report_content)
    evaluation['format']['bold_count'] = len(bold_matches)

    if evaluation['format']['bold_count'] < 3:
        evaluation['warnings'].append("중요한 수치나 인사이트를 **볼드체**로 강조하는 것이 권장됩니다.")

    # LLM을 이용한 추가 평가
    try:
        llm_evaluation = evaluate_with_llm(report_content, analysis_type)

        # LLM 평가 결과 반영
        if llm_evaluation:
            evaluation['expertise'] = llm_evaluation.get('expertise', evaluation['expertise'])
            evaluation['clarity'] = llm_evaluation.get('clarity', evaluation['clarity'])
            evaluation['evidence'] = llm_evaluation.get('evidence', evaluation['evidence'])

            # 경고 사항 추가
            if 'warnings' in llm_evaluation and llm_evaluation['warnings']:
                evaluation['warnings'].extend(llm_evaluation['warnings'])
    except Exception as e:
        st.warning(f"LLM 평가 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본값 설정
        evaluation['expertise'] = {'score': 0, 'feedback': "LLM 평가 중 오류 발생"}
        evaluation['clarity'] = {'score': 0, 'feedback': "LLM 평가 중 오류 발생"}
        evaluation['evidence'] = {'score': 0, 'feedback': "LLM 평가 중 오류 발생"}
        evaluation['warnings'] = ["LLM 평가 중 오류가 발생했습니다 (evaluate_report_quality)"]

    # 종합 점수 계산
    # 구조 점수 (20점 만점)
    structure_score = sum(evaluation['structure'].values()) / len(evaluation['structure']) * 20

    # 볼드체 점수 (10점 만점)
    bold_score = min(evaluation['format']['bold_count'] * 2, 10)

    # 전문성 점수 (최대 20점)
    expertise_score = evaluation['expertise']['score']

    # 명확성 점수 (최대 20점)
    clarity_score = evaluation['clarity']['score']

    # 분석 근거 점수 (최대 30점)
    evidence_score = evaluation['evidence']['score']

    # 종합 점수 계산 및 반올림
    evaluation['overall_score'] = round(
        structure_score +
        bold_score +
        expertise_score +
        clarity_score +
        evidence_score
    )

    return evaluation

def evaluate_with_llm(report_content, analysis_type):
    """LLM을 사용하여 보고서의 전문성, 명확성, 분석 근거를 평가

    Args:
        report_content (str): 평가할 마크다운 보고서 내용
        analysis_type (str): 분석 유형 ("SEM", "EDS", "OPERATION", "EQUIPMENT")

    Returns:
        dict: LLM 평가 결과
    """

    # 세션 상태에서 설정된 모델 가져오기
    model_name = st.session_state.get("selected_model", "gemma3:4b")

    # Chat Ollama 초기화
    llm = ChatOllama(
        model=model_name,
        temperature=0  # 일관된 평가를 위해 낮은 temperature 사용
    )

    # 분석 유형별 전문 용어 예시
    technical_terms = {
        'SEM': "마이크로미터, 스케일바, 표면형상, 형태학, 응집, 균열, 기공, 표면거칠기",
        'EDS': "원소조성, 중량백분율, wt%, 피크강도, 특성 X선, 산화층, K-알파, L-알파, 검출한계, 정량분석",
        'OPERATION': "작동 모드, 마찰, 접촉, 피로, 마모, 산화, 부식, 회전, 연삭, 충돌, 열 스프레이, 분사, 캐비테이션, 진동 마멸"
    }

    # 평가 프롬프트
    system_prompt = """당신은 SEM-EDS 분석 보고서를 평가하는 전문가입니다.
아래 보고서를 전문성, 명확성, 분석 근거 측면에서 평가하고 정확한 JSON 형식으로 점수와 피드백을 제공해주세요.

평가 기준:
1. 전문성 (0-20점)
- 분석 분야에 적합한 전문 용어를 필요한 곳에 정확히 사용했는가?
- {analysis_type} 분석에 적합한 전문 용어 예시: {technical_terms}

2. 명확성 (0-20점)
- 내용이 명확하게 정리되었는가?
- 논리적 흐름이 적절한가?
- 용어와 개념이 일관되게 사용되었는가?

3. 분석 근거 (0-30점)
- 분석 근거가 타당한가?
- 주장과 결론이 데이터와 관찰에 근거하는가?
- 논리적 추론이 명확한가?

다음 JSON 형식으로 응답해주세요:
```json
{{
  "expertise": {{
    "score": 0-20 사이의 정수,
    "feedback": "전문성에 대한 1-2문장의 피드백"
  }},
  "clarity": {{
    "score": 0-20 사이의 정수,
    "feedback": "명확성에 대한 1-2문장의 피드백"
  }},
  "evidence": {{
    "score": 0-30 사이의 정수,
    "feedback": "분석 근거에 대한 1-2문장의 피드백"
  }},
  "warnings": ["개선이 필요한 사항 1", "개선이 필요한 사항 2"]
}}
```
"""

    user_prompt = """다음 {analysis_type} 분석 보고서를 평가해주세요:

{report_content}

위 보고서에 대한 전문성, 명확성, 분석 근거 측면의 평가를 JSON 형식으로 제공해주세요.
"""

    # 분석 유형 단어 변환
    if analysis_type == "OPERATION":
        analysis_type_word = "공정 조건"
    elif analysis_type == "EQUIPMENT":
        analysis_type_word = "설비/부품 추정"
    else:
        analysis_type_word = analysis_type

    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ]).invoke({
        "analysis_type": analysis_type_word,
        "technical_terms": technical_terms[analysis_type],
        "report_content": report_content
    })

    # 응답 생성
    try:
        with st.spinner(f"LLM으로 {analysis_type_word} 분석 보고서 평가 중..."):
            response = llm.invoke(prompt)

            # JSON 응답 추출
            response_text = response.content

            # JSON 부분 추출 (마크다운 코드 블록이 있는 경우)
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].strip()
            else:
                json_text = response_text.strip()

            import json
            evaluation_result = json.loads(json_text)

            return evaluation_result
    except Exception as e:
        st.error(f"LLM 평가 중 오류: {str(e)}")
        return {
            "expertise": {"score": 0, "feedback": "평가 오류 발생"},
            "clarity": {"score": 0, "feedback": "평가 오류 발생"},
            "evidence": {"score": 0, "feedback": "평가 오류 발생"},
            "warnings": ["LLM 평가 중 오류가 발생했습니다 (evaluate_with_llm)"]
        }

def evaluate_technical_accuracy(report_content, analysis_type, reference_data=None):
    """보고서의 기술적 정확성을 평가

    Args:
        report_content (str): 평가할 마크다운 보고서 내용
        analysis_type (str): 분석 유형 ("SEM", "EDS", "OPERATION", "EQUIPMENT")
        reference_data (dict, optional): 비교를 위한 참조 데이터

    Returns:
        dict: 정확성 평가 결과
    """
    # 나중에 구현할 정확성 평가 기능을 위한 준비
    accuracy = {
        'numerical_accuracy': 0.0,  # 수치 정확도
        'interpretation': 0.0,      # 해석 정확도
        'conclusion': 0.0,          # 결론 타당성
        'overall_accuracy': 0.0     # 종합 정확도
    }

    # 향후 구현 예정
    return accuracy

def evaluate_educational_value(report_content):
    """보고서의 교육적 가치를 평가

    Args:
        report_content (str): 평가할 마크다운 보고서 내용

    Returns:
        dict: 교육적 가치 평가 결과
    """
    # 향후 구현 예정 - 교육적 가치 평가 기능
    educational = {
        'explanatory_clarity': 0.0,  # 설명 명확성
        'knowledge_depth': 0.0,      # 지식 깊이
        'learning_value': 0.0        # 학습 가치
    }

    return educational
