"""
CMMS 분석 보고서 평가 모듈
"""

import re
import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

def evaluate_report_quality(report_content, analysis_type):
    """마크다운 보고서 내용을 분석하여 품질을 평가

    Args:
        report_content (str): 평가할 마크다운 보고서 내용
        analysis_type (str): 분석 유형 ("WORK_PATTERN", "RISK_ASSESSMENT", "PREDICTIVE_MAINTENANCE")

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

    # 분석 유형별 필수 섹션 및 키워드 정의 (유연한 매칭을 위해 단순화)
    required_sections = {
        'WORK_PATTERN': {
            '문제점': ['문제', '이상', '고장', '사례'],
            '원인': ['원인', '이슈', '반복', '근본'],
            '유지보수': ['유지', '보수', '예방', '개선', '제안'],
            '효율성개선': ['효율', '개선', '향상', '인사이트']
        },
        'RISK_ASSESSMENT': {
            '위험도': ['위험', '점수', '등급', '평가'],
            '위험요소': ['위험', '요소', '심각성', '빈도'],
            '조치사항': ['권장', '개선', '대응', '조치사항'],
            '감소전략': ['감소', '전략', '대책', '방지']
        },
        'PREDICTIVE_MAINTENANCE': {
            '정비주기': ['정비', '주기', '최적', '예방'],
            '이상감지': ['비정상', '이상', '식별', '차이'],
            '모니터링': ['모니터링', '포인트', '측정', '센서'],
            '통계적접근': ['데이터 분석', '통계', '추세', '패턴']
        }
    }

    # 구조 완전성 평가 (필수 섹션 포함 여부) - 유연한 패턴으로 수정
    evaluation['debug_info']['found_sections'] = []  # 디버깅: 찾은 섹션 저장

    # 모든 마크다운 헤더 파싱 (디버깅용)
    all_headers = re.findall(r'(#{1,6}\s+.+)', report_content)
    evaluation['debug_info']['all_headers'] = all_headers

    for section, keywords in required_sections[analysis_type].items():
        # 헤더 섹션 검색
        section_exists = check_section_exists(section, keywords, report_content, all_headers)

        evaluation['structure'][section] = section_exists

        # 디버깅 정보 저장
        if section_exists:
            evaluation['debug_info']['found_sections'].append(section)
            # 매치된 헤더 정보 저장 시도
            matched_header = find_matching_header(section, keywords, all_headers)
            evaluation['debug_info'][f'match_{section}'] = matched_header if matched_header else "다중 키워드 매칭됨"

        if not section_exists:
            evaluation['warnings'].append(f"'{section}' 관련 내용이 보고서에 없거나 부족합니다.")

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
    # 구조 점수 (40점 만점)
    structure_score = sum(evaluation['structure'].values()) / len(evaluation['structure']) * 40

    # 볼드체 점수 (10점 만점)
    bold_score = min(evaluation['format']['bold_count'] * 2, 10)

    # 전문성 점수 (최대 20점)
    expertise_score = evaluation['expertise']['score']

    # 명확성 점수 (최대 15점)
    clarity_score = evaluation['clarity']['score']

    # 분석 근거 점수 (최대 15점)
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

def check_section_exists(section_name, keywords, report_content, all_headers):
    """더 유연한 섹션 매칭을 위한 헬퍼 함수

    Args:
        section_name (str): 찾을 섹션 이름
        keywords (list): 해당 섹션 관련 키워드 목록
        report_content (str): 보고서 전체 내용
        all_headers (list): 모든 헤더 목록

    Returns:
        bool: 섹션 존재 여부
    """
    # 방법 1: 정확한 섹션명 매칭 (이전 방식)
    section_pattern = r'#{1,6}\s+.*' + re.escape(section_name) + r'.*'
    if re.search(section_pattern, report_content):
        return True

    # 방법 2: 헤더 내에 키워드 매칭 확인
    keyword_match_count = 0
    for header in all_headers:
        for keyword in keywords:
            if keyword in header.lower():
                keyword_match_count += 1
                break  # 한 헤더에서 하나의 키워드만 카운트

    # 방법 3: 텍스트 내에서 키워드 검색
    content_match_count = 0
    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', report_content.lower()):
            content_match_count += 1

    # 판단 기준: 헤더에서 하나 이상 키워드 매칭되거나, 내용에서 키워드의 50% 이상 매칭
    return (keyword_match_count > 0) or (content_match_count >= len(keywords) * 0.5)

def find_matching_header(section_name, keywords, all_headers):
    """일치하는 헤더를 찾는 함수

    Args:
        section_name (str): 찾을 섹션 이름
        keywords (list): 해당 섹션 관련 키워드 목록
        all_headers (list): 모든 헤더 목록

    Returns:
        str: 일치하는 헤더 또는 None
    """
    # 정확한 섹션명이 포함된 헤더 찾기
    for header in all_headers:
        if section_name in header.lower():
            return header

    # 키워드가 포함된 헤더 찾기
    for header in all_headers:
        for keyword in keywords:
            if keyword in header.lower():
                return header

    return None

def evaluate_with_llm(report_content, analysis_type):
    """LLM을 사용하여 보고서의 전문성, 명확성, 분석 근거를 평가

    Args:
        report_content (str): 평가할 마크다운 보고서 내용
        analysis_type (str): 분석 유형 ("WORK_PATTERN", "RISK_ASSESSMENT", "PREDICTIVE_MAINTENANCE")

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
        'WORK_PATTERN': "작업 패턴, 유지보수 주기, 고장 모드, 예방정비, 수리 효율성, 작업시간, 공구 활용도, 작업자 생산성",
        'RISK_ASSESSMENT': "위험도 점수, 고장 확률, 영향도 평가, 위험 매트릭스, 중대고장, 설비 신뢰성, 안전 카테고리, 심각도 레벨",
        'PREDICTIVE_MAINTENANCE': "예지 보전, 상태 모니터링, 고장 예측 모델, 이상 감지, 센서 데이터, 진동 분석, 열화 패턴, 잔여 수명, 최적 교체 시점, 성능 저하율"
    }

    # 평가 프롬프트
    system_prompt = """당신은 CMMS 분석 보고서를 평가하는 전문가입니다.
아래 보고서를 전문성, 명확성, 분석 근거 측면에서 평가하고 정확한 JSON 형식으로 점수와 피드백을 제공해주세요.

평가 기준:
1. 전문성 (0-20점)
- 분석 분야에 적합한 전문 용어를 필요한 곳에 정확히 사용했는가?
- {analysis_type} 분석에 적합한 전문 용어 예시: {technical_terms}

2. 명확성 (0-15점)
- 내용이 명확하게 정리되었는가?
- 논리적 흐름이 적절한가?
- 용어와 개념이 일관되게 사용되었는가?

3. 분석 근거 (0-15점)
- 분석 근거가 타당한가?
- 주장과 결론이 데이터와 관찰에 근거하는가?
- 논리적 추론이 명확한가?

다음 JSON 형식으로 응답해주세요:
```json
{{
  "expertise": {{
    "score": 0-20 사이의 정수,
    "feedback": "전문성에 대한 3~4문장의 피드백"
  }},
  "clarity": {{
    "score": 0-15 사이의 정수,
    "feedback": "명확성에 대한 3~4문장의 피드백"
  }},
  "evidence": {{
    "score": 0-15 사이의 정수,
    "feedback": "분석 근거에 대한 3~4문장의 피드백"
  }},
  "warnings": ["개선이 필요한 사항 1", "개선이 필요한 사항 2"]
}}
```
"""

    user_prompt = """다음 {analysis_type} 분석 보고서를 평가해주세요:

{report_content}

위 보고서에 대한 전문성, 명확성, 분석 근거 측면의 평가를 JSON 형식으로 제공해주세요.
"""

    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ]).invoke({
        "analysis_type": analysis_type,
        "technical_terms": technical_terms[analysis_type],
        "report_content": report_content
    })

    # 응답 생성
    try:
        with st.spinner(f"LLM으로 {analysis_type} 분석 보고서 평가 중..."):
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
        analysis_type (str): 분석 유형 ("WORK_PATTERN", "RISK_ASSESSMENT", "PREDICTIVE_MAINTENANCE")
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

def display_evaluation_results(evaluation, st_container=None):
    """평가 결과를 시각화하여 표시

    Args:
        evaluation (dict): evaluate_report_quality의 결과
        st_container (streamlit.container, optional): 결과를 표시할 Streamlit 컨테이너
    """
    # Streamlit 컨테이너가 제공되지 않은 경우 기본값 사용
    container = st if st_container is None else st_container

    # 평가 결과 표시
    container.markdown("### 📊 보고서 품질 평가 결과")

    # 종합 점수
    container.metric("종합 점수", f"{evaluation['overall_score']} / 100점")

    # 세부 평가 결과를 카테고리별로 표시
    cols = container.columns(5)

    # 1. 구조 완전성
    with cols[0]:
        container.markdown("**구조 완전성**")
        structure_ok = sum(evaluation['structure'].values())
        structure_total = len(evaluation['structure'])
        container.markdown(f"{structure_ok} / {structure_total} 섹션")
        structure_score = (structure_ok / structure_total) * 40
        container.progress(structure_score / 40)

    # 2. 형식 준수
    with cols[1]:
        container.markdown("**형식 준수**")
        container.markdown(f"볼드체: {evaluation['format']['bold_count']}회")
        bold_score = min(evaluation['format']['bold_count'] * 2, 10)
        container.progress(bold_score / 10)

    # 3. 전문성 점수
    with cols[2]:
        container.markdown("**전문성**")
        container.markdown(f"{evaluation['expertise']['score']} / 20점")
        container.progress(evaluation['expertise']['score'] / 20)

    # 4. 명확성 점수
    with cols[3]:
        container.markdown("**명확성**")
        container.markdown(f"{evaluation['clarity']['score']} / 15점")
        container.progress(evaluation['clarity']['score'] / 15)

    # 5. 분석 근거 점수
    with cols[4]:
        container.markdown("**분석 근거**")
        container.markdown(f"{evaluation['evidence']['score']} / 15점")
        container.progress(evaluation['evidence']['score'] / 15)

    # 개선 필요 사항
    if evaluation['warnings']:
        container.markdown("### ⚠️ 개선 필요 사항")
        for warning in evaluation['warnings']:
            container.warning(warning)
    else:
        container.success("모든 평가 기준을 충족했습니다! 👍")

    # 상세 분석 정보
    container.markdown("### 📑 상세 분석 정보")

    # 섹션 인식 상태
    container.markdown("#### 섹션 인식 결과")
    for section, exists in evaluation['structure'].items():
        if exists:
            match_key = f'match_{section}'
            matched_text = evaluation['debug_info'].get(match_key, "매치 정보 없음")
            container.success(f"✓ **{section}** 섹션 인식됨")
            container.markdown(f"   매치된 헤더: `{matched_text}`")
        else:
            container.error(f"✗ **{section}** 섹션 인식 실패")

    # 피드백 정보
    container.markdown("#### 피드백 정보")
    container.markdown(f"**전문성**: {evaluation['expertise']['feedback']}")
    container.markdown(f"**명확성**: {evaluation['clarity']['feedback']}")
    container.markdown(f"**분석 근거**: {evaluation['evidence']['feedback']}")