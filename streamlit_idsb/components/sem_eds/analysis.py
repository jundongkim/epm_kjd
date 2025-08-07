"""
SEM-EDS 분석 및 보고서 생성 기능 모듈
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from textwrap import dedent

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from components.sem_eds.server import check_ollama_server
# from components.ai_utils import generate_ai_analysis
from components.sem_eds.ai_utils import generate_ai_analysis
from components.sem_eds.report_evaluation import evaluate_report_quality
from components.sem_eds.image_utils import encode_image_to_base64

def extract_image_info(image_data, image_type):
    """이미지로부터 정보 추출

    Args:
        image_data (dict): 처리된 이미지 데이터
        image_type (str): 이미지 타입 ("SEM" 또는 "EDS")

    Returns:
        dict: 추출된 이미지 분석 정보
    """
    try:
        if not check_ollama_server():
            st.error("Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # LLM 초기화
        llm = ChatOllama(
            model=st.session_state.selected_model,
            temperature=st.session_state.temperature
        )

        # 이미지 타입에 따른 시스템 프롬프트
        if image_type == "SEM":
            system_prompt = """당신은 대한민국의 배터리 양극재 생산 기업 'EcoPro BM'에서 SEM-EDS 분석을 진행하는 전문 엔지니어입니다. 당신의 업무는 양극재 생산 공정에서 검출된 금속 이물질에 대한 SEM(주사전자현미경) 분석입니다.
            당신이 분석한 내용은 이물질이 발생한 설비를 추정하는 데에 사용됩니다. 금속 이물질은 생산 설비 내부 표면이나 부품에서 발생할 수 있습니다.
            주어진 SEM 이미지 상의 이물질 입자에 대해 아래 기준에 맞추어 분석을 수행하세요.

            다음 JSON 형식으로만 정확히 응답하세요:
            {{
                "이물질_정보": {{
                    "대상_입자": "분석 대상으로 선택한 입자 하나의 이미지 상 위치",
                    "형태_묘사": "분석 대상 입자의 형태 묘사"
                }},
                "크기_분석": {{
                    "스케일바_크기": "스케일바의 길이 μm, 스케일바는 길이 단위 주변의 눈에 잘 띄는 막대",
                    "입자_크기": "스케일바 기준 입자의 크기 μm, 가로 μm x 세로 μm",
                    "종횡비": "입자의 가로 길이 대 세로 길이 비율, 가로(μm)/세로(μm) 계산값을 소수점 첫째자리까지 표기"
                }},
                "형태_분석": {{
                    "입자_형태": "spherical(구형)/angular(각형)/flake(판상형)/fiber(섬유형)/cohesive(응집형) 등",
                    "표면_질감": "smooth(매끄러움)/striated(연삭 홈)/cracked(균열)/melt_pool(용융 흔적)/rough(거칢) 등"
                }}
            }}"""
        else:  # EDS
            system_prompt = """당신은 대한민국의 배터리 양극재 생산 기업 'EcoPro BM'에서 SEM-EDS 분석을 진행하는 전문 엔지니어입니다. 주어진 EDS 스펙트럼 분석 이미지 상의 원소 조성 비율 테이블을 주로 참고하여 정보를 정리해주세요.
            다른 설명이나 마크다운 코드 블록 등은 포함하지 말고, 정확한 JSON 형식으로만 응답해주세요.

            다음 JSON 형식으로만 정확히 응답하세요:
            {{
                "원소_조성": {{
                    "원소": ["검출된 모든 원소기호 목록 (누락없이)"],
                    "함량_비율": {{"원소기호": "함량 (wt% 혹은 weight%)"}},
                    "피크_강도": {{"원소기호": "스펙트럼 그래프 이미지 상 피크 기준 높음/중간/낮음"}}
                }},
                "산화_상태": {{
                    "산소_함량": "산소(O) 함량 (wt%), 없으면 '0'",
                    "산화_여부": "'산소_함량' 30 이상이면 '부식', '산소_함량' 20 이상이면 '고온 산화', 그외 '산화되지 않음'"
                }}
            }}"""

        # 이미지 메타데이터 준비
        metadata = image_data["metadata"]

        # 이미지 base64 인코딩
        base64_image = encode_image_to_base64(image_data["image"])

        # ChatPromptTemplate 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", [
                # {
                #     "type": "text",
                #     "text": f"이미지 정보:\n- 크기: {metadata['size']}\n- 형식: {metadata['format']}\n- 해상도: {metadata['dimensions']}"
                # },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ])
        ])

        # 디버그 정보를 세션 상태에 저장
        if image_type == "SEM":
            st.session_state["sem_metadata"] = metadata
        else:
            st.session_state["eds_metadata"] = metadata

        with st.expander("디버그 정보", expanded=False):
            st.write("입력 메타데이터:")
            st.json(metadata)

        # 프롬프트 실행
        chain = prompt | llm
        result = chain.invoke({})

        # 결과 문자열 정리 및 디버깅
        result_text = str(result.content).strip()

        # JSON 부분만 추출
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1]
        result_text = result_text.strip()

        # JSON 파싱 시도
        try:
            info = json.loads(result_text)
        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {str(e)}")
            st.error("정제된 응답:")
            st.code(result_text)
            # JSON 형식 검증을 위한 디버깅 정보
            st.error("문자열 길이: " + str(len(result_text)))
            st.error("처음 50자: " + result_text[:50])
            st.error("마지막 50자: " + result_text[-50:])
            return None

        # EDS인 경우 스테인리스 강종 분류 결과 추가
        if image_type == "EDS":
            from components.sem_eds.classification import classify_stainless_steel
            info["강종_판단"] = classify_stainless_steel(info["원소_조성"]["함량_비율"])

        # AI 모델 원본 응답을 세션 상태에 저장
        result_text = json.dumps(info, ensure_ascii=False, indent=4)
        if image_type == "SEM":
            st.session_state["sem_raw_response"] = result_text
        else:
            st.session_state["eds_raw_response"] = result_text

        with st.expander("AI 모델 원본 응답", expanded=False):
            st.code(result_text)

        # EDS인 경우 스테인리스 강종 표준 조성 비율 데이터 -> 테이블 출력
        if image_type == "EDS":
            from components.sem_eds.classification import get_stainless_standard_composition_df
            with st.expander("스테인리스 강종 표준 조성 비율", expanded=False):
                df = get_stainless_standard_composition_df()
                st.dataframe(df)

        # 필수 키 검증
        if image_type == "SEM":
            required_keys = ["이물질_정보", "크기_분석", "형태_분석"]
        else:  # EDS
            required_keys = ["원소_조성", "강종_판단", "산화_상태"]

        missing_keys = [key for key in required_keys if key not in info]
        if missing_keys:
            st.error(f"필수 정보 누락: {', '.join(missing_keys)}")
            st.json(info)  # 현재 파싱된 데이터 표시
            return None

        # 분석 결과에 메타데이터 추가
        # info["메타데이터"] = metadata

        # JSON 파일로 저장
        json_path = Path("SEM_EDS") / "json" / f"{image_type.lower()}_analysis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        return info

    except Exception as e:
        st.error(f"이미지 정보 추출 중 오류가 발생했습니다: {str(e)}")
        st.error("상세 오류:")
        st.code(str(e))
        return None

def generate_analysis_report(analysis_type, analysis_info, sem_image_path=None, eds_image_path=None):
    """분석 리포트 생성

    Args:
        analysis_type (str): 분석 유형 ("SEM", "EDS", "OPERATION", "EQUIPMENT")
        analysis_info (dict): 분석 정보
        sem_image_path (str, optional): SEM 이미지 경로
        eds_image_path (str, optional): EDS 이미지 경로

    Returns:
        tuple: (마크다운 컨텐츠, 저장된 파일 경로)
    """
    try:
        # 리포트 생성을 위한 프롬프트 준비
        if analysis_type == "SEM":
            prompt = f"""당신은 대한민국의 배터리 양극재 생산 기업 'EcoPro BM'에서 SEM-EDS 분석 전문 엔지니어입니다.
            검출된 이물질 입자에 대한 아래 SEM 분석 정보를 바탕으로 전문적인 SEM 분석 리포트를 작성해주세요.

            ### SEM 분석 정보 ###
            {json.dumps(analysis_info, ensure_ascii=False, indent=2)}

            ### 리포트 구조 ###
            1. 크기 분석 결과
               - 스케일바 기준 크기: 스케일바의 길이 μm
               - 이물 크기: 입자의 크기, 가로 μm x 세로 μm
               - 종횡비: 종횡비가 **3 이상이면** 입자의 형태는 판상형 혹은 섬유형으로 추정

            2. 형태 분석 결과
               - 이물의 형태적 특징
               - 표면 상태 분석
               - 형태 관련 특이사항

            3. 종합 평가
               - 주요 발견사항
               - 추가 분석 필요사항

            ### 주의사항 ###
            - 각 섹션은 ### 헤더로 구분하고, 중요한 수치나 인사이트는 **볼드체**로 강조해주세요.
            - 분석 내용은 양극재가 아니라, 이물질 입자에 대한 분석 결과입니다.
            """
        elif analysis_type == "EDS":
            prompt = f"""당신은 대한민국의 배터리 양극재 생산 기업 'EcoPro BM'에서 SEM-EDS 분석을 진행하는 전문 엔지니어입니다.
            검출된 이물질 입자에 대한 EDS 분석 정보를 바탕으로 전문적인 EDS 분석 리포트를 작성해주세요.

            ### 리포트 구조 ###
            ```
            <report_structure>
            1. 원소 조성 분석
               - 주요 원소 함량
               - 원소별 피크 강도

            2. 산화 상태 분석
               - 산소 함량 분석
               - 산화 정도 평가
               - 이물질 발생 위치 추정

            3. 강종 추정
               - 추정 강종
               - 판단 근거
               - 신뢰도 평가
               - 추정 강종 후보: **유사도 기준으로 여러 강종들이 제시된 경우**, 강종 후보들의 정보를 상세하게 나열해주세요.

            4. 종합 평가
               - 주요 발견사항
               - 추가 분석 필요사항
            </report_structure>
            ```

            ### 리포트 작성 지침 ###
            <report_writing_instructions>
            - 위 구조에 따라 마크다운 형식의 리포트를 작성해 주세요.
            - 원소 함량의 단위는 wt%로 표시해주세요.
            - '산화 정도 평가'는 '산소 함량 분석' 결과와 아래 내용을 참고하여 작성해주세요.
                - 산소 함량 30 이상이면 '부식'
                - 산소 함량 20 이상이면 '고온 산화'
                - 그외 산화되지 않음
            - '이물질 발생 위치 추정'은 '산화 정도 평가' 결과와 아래 내용을 참고하여 작성해주세요.
                - 산화 여부가 '부식'인 경우(= 산소 함량이 30 이상인 경우), 공정 내 습기 유입으로 인해 발생한 이물질로 판단
                - 산화 여부가 '고온 산화'인 경우(= 산소 함량이 20 이상인 경우), 소성로 공정 이전에 발생한 이물질로 판단
                - 산화 여부가 '산화되지 않음'인 경우(= 산소 함량이 20 미만인 경우), 소성로 공정 이후에 발생한 이물질로 판단
            - '강종 추정' 내용은 강종의 grade 뿐만 아니라 계열까지 상세하게 추정해주세요.
            </report_writing_instructions>

            ### 주의사항 ###
            ```
            <attention>
            - 각 섹션은 ### 헤더로 구분하고, 중요한 수치나 인사이트는 **볼드체**로 강조해주세요.
            - 분석 내용은 양극재가 아니라, 이물질 입자에 대한 분석 결과입니다.
            </attention>
            ```

            ---

            ### EDS 분석 정보 ###
            {json.dumps(analysis_info, ensure_ascii=False, indent=2)}
            """
        elif analysis_type == "OPERATION":
            prompt = dedent(f"""당신은 대한민국의 배터리 양극재 생산 기업 'EcoPro BM'의 SEM-EDS 분석 전문 엔지니어입니다.
            주어진 SEM-EDS 분석 데이터를 바탕으로 이물질 입자가 발생한 설비의 작동 모드를 추정하는 리포트를 작성해 주세요.

            ### 작업 목표 ###
            이물질 입자의 SEM 및 EDS 분석 데이터로부터 설비의 작동 모드를 추정하여 이물질 발생 원인을 파악합니다.

            ### 작동 모드 판단 기준 ###
            ```
            <mode_determination_criteria>
            다음 작동 모드 중 하나를 선택하고, 그 판단 근거를 명확히 설명해야 합니다:

            1. ROTATE_SLIDE (회전 접촉 피로)
               - 판단 기준: "표면_질감"=cracked(균열) ∧ "입자_형태"=angular(각진형) ∧ "강종_판단"=Bearing_52100(베어링강)
               - 특징: 균열 표면, 각진 형태, 베어링강 성분을 가진 이물의 경우 베어링이나 롤러와 같은 회전 접촉 부위에서 발생한 피로 파괴로 추정

            2. GRIND_IMPACT (연삭/충돌 마모)
               - 판단 기준: "표면_질감"=striated(연삭 흔적) ∧ "입자_형태"=angular(각진형)
               - 특징: 연삭 흔적이 있는 표면과 각진 형태의 입자는 연삭이나 충돌에 의한 마모 환경에서 발생

            3. HEAT_SPRAY (열 스프레이/분사)
               - 판단 기준: "입자_형태"=sphere(구형) ∧ "산소_함량">20(wt%)
               - 특징: 구형 형태와 높은 산소 함량(20wt% 이상)은 고온에서의 열 스프레이 또는 열 분사 공정 환경을 시사

            4. WET_CORROSIVE (습식 부식)
               - 판단 기준: "입자_형태"=flake(판상형) ∧ "산소_함량">30(wt%)
               - 특징: 판상형 형태와 매우 높은 산소 함량(30wt% 이상)은 습식 세정(CIP) 또는 부식성 환경에서 발생

            5. CAVITATION (공동 현상)
               - 판단 기준: "입자_형태"=spherical/angular mix(구형/각진형 혼합) ∧ "표면_질감"=pitted(움푹 패인)
               - 특징: 구형과 각진형이 혼합된 형태와 움푹 패인 표면은 공동 현상(캐비테이션) 환경에서 발생

            6. VIBRATION_FRETTING (진동 마멸)
               - 판단 기준: "표면_질감"=cracked(균열) ∧ "산소_함량">20(wt%) ∧ "입자_형태"=flake(판상형)
               - 특징: 균열 표면, 높은 산소 함량, 판상형 형태는 진동에 의한 마멸(Fretting Corrosion) 환경에서 발생
            </mode_determination_criteria>
            ```

            ### 리포트 작성 지침 ###
            ```
            <report_writing_instructions>
            다음 구조로 마크다운 형식의 리포트를 작성해 주세요:

            ### 1. 입자 특성 요약
            - **SEM 분석 요약**: 입자의 형태, 크기, 표면 특성 등 SEM 분석 결과의 핵심 정보
            - **EDS 분석 요약**: 주요 원소 구성, 산소 함량, 강종 판단 등 EDS 분석 결과의 핵심 정보
            - **핵심 지표**: 작동 모드 판단에 중요한 입자 형태, 표면 질감, 산소 함량, 강종 판단 등을 명확히 나열

            ### 2. 작동 모드 추정
            - **추정 작동 모드**: 위 6가지 중 가장 적합한 하나의 작동 모드를 명확히 선택하고 굵은 글씨로 표시
            - **판단 근거**: 선택한 작동 모드의 판단 기준과 분석 데이터가 어떻게 일치하는지 상세히 설명
            - **대안 모드**: 차선으로 고려할 수 있는 다른 작동 모드와 선택하지 않은 이유
            - **신뢰도**: 추정의 신뢰도(상/중/하)와 그 근거 설명

            ### 3. 결론 및 제안
            - **핵심 발견**: 작동 모드 추정 결과와 그 의미에 대한 요약
            - **설비 관리 제안**: 해당 작동 모드에 따른 설비 관리 방안 제시
            - **이물질 저감 방안**: 해당 작동 모드에서 이물질 발생을 줄이기 위한 구체적 제안
            </report_writing_instructions>
            ```

            ### 주의사항 ###
            <attention>
            - 각 섹션과 하위 항목을 명확한 마크다운 형식으로 구분하세요
            - 중요한 정보와 결론은 **굵은 글씨**로 강조하세요
            - 불필요한 배경 설명이나 반복은 피하고 정보 중심으로 간결하게 작성하세요
            - 작동 모드는 6가지 중 하나를 명확히 선택하고, 그에 맞는 물리 조건을 상세히 추정해주세요.
            - 모든 추정과 제안은 제공된 SEM-EDS 분석 데이터에 근거해야 합니다.
            </attention>

            ---

            ### 분석 데이터 ###
            {json.dumps(analysis_info, ensure_ascii=False, indent=2)}
            """)
        elif analysis_type == "EQUIPMENT":
            prompt = f"""당신은 대한민국의 배터리 양극재 생산 기업 'EcoPro BM'에서 SEM-EDS 분석을 진행하는 전문 엔지니어입니다.
            검출된 이물질 입자에 대한 아래 SEM-EDS 종합 분석 정보를 바탕으로 전문적인 분석 리포트를 작성해주세요:

            ### 종합 분석 정보 ###
            {json.dumps(analysis_info, ensure_ascii=False, indent=2)}

            ### 리포트 구조 ###
            1. 분석 개요
               - 분석 목적
               - 분석 방법
               - 분석 환경

            2. SEM 분석 주요 결과
               - 크기 분석
               - 형태 분석
               - 설비 영향

            3. EDS 분석 주요 결과
               - 원소 조성
               - 물질 특성
               - 산화 상태

            4. 크기-조성 연관성 분석
               - 크기와 조성의 관계
               - 특이사항
               - 시사점

            5. 원인 설비 평가
               - 예상되는 원인 설비
               - 추정 근거와 설명
               - 관련 부품 예상

            6. 종합 평가 및 권장사항
               - 주요 발견사항
               - 개선 권장사항
               - 추가 분석 필요사항

            ### 주의사항 ###
            - 각 섹션은 ### 헤더로 구분하고, 중요한 수치나 인사이트는 **볼드체**로 강조해주세요.
            - 분석 내용은 양극재가 아니라, 이물질 입자에 대한 분석 결과입니다.
            """

        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            # 분석 유형별 메시지 변환
            if analysis_type == "OPERATION":
                analysis_message = "AI가 SEM-EDS 데이터를 바탕으로 공정 조건을 분석하고 있습니다..."
            elif analysis_type == "EQUIPMENT":
                analysis_message = "AI가 SEM-EDS 데이터와 공정 조건 분석 정보를 바탕으로 이물 발생 설비/부품을 추정하고 있습니다..."
            else:
                analysis_message = f"AI가 {analysis_type} 데이터를 분석하고 있습니다..."

            with st.spinner(analysis_message):
                # AI 분석 실행
                result = generate_ai_analysis(
                    prompt=prompt,
                    key_prefix=f"{analysis_type.lower()}_analysis",
                    message_placeholder=message_placeholder
                )

                # 결과 처리
                if result is None:
                    st.error("AI 분석 결과가 없습니다.")
                    return None, None

                # 결과에서 리포트 내용(마크다운 문자열) 추출 - 다양한 반환 타입 처리
                markdown_content = None

                # 1. 튜플 형태 확인 (가장 먼저)
                if isinstance(result, tuple) and len(result) > 0:
                    first_element = result[0]
                    if isinstance(first_element, dict) and 'answer' in first_element:
                        markdown_content = first_element['answer']
                    elif isinstance(first_element, str):
                        markdown_content = first_element
                    # 튜플의 첫 요소가 예상 타입이 아니면 아래 로직에서 처리 시도

                # 2. 딕셔너리 형태 확인 (튜플이 아니거나 튜플에서 추출 실패 시)
                elif isinstance(result, dict) and 'answer' in result:
                    markdown_content = result['answer']

                # 3. 문자열 형태 확인 (튜플, 딕셔너리가 아닐 경우)
                elif isinstance(result, str):
                    markdown_content = result

                # 4. 위에서 처리되지 않은 경우 (경고 후 문자열 변환 시도 - 이전 로직 유지)
                if markdown_content is None:
                    st.warning(f"AI 분석 결과 형식이 예상과 다릅니다 (type: {type(result)}). 문자열 변환을 시도합니다.")
                    try:
                        potential_content = str(result)
                        if potential_content.startswith(("{", "[")) and potential_content.endswith(("}", "]")):
                             st.error(f"AI 분석 결과에서 마크다운 텍스트를 추출할 수 없습니다. 원본 결과: {potential_content}")
                             return None, None
                        markdown_content = potential_content
                    except Exception as str_e:
                         st.error(f"AI 분석 결과를 문자열로 변환하는 중 오류 발생: {str_e}")
                         return None, None

                # 추출된 내용이 실제 문자열인지, 비어있지 않은지 최종 확인
                if not isinstance(markdown_content, str) or not markdown_content.strip():
                    st.error(f"추출된 리포트 내용이 유효한 텍스트가 아니거나 비어있습니다. 추출된 내용: {markdown_content}")
                    return None, None

                # --- 이미지 링크 추가 로직 ---
                image_markdown = "" # 리포트 마크다운 저장용
                if analysis_type == "SEM" and sem_image_path:
                    image_markdown += f"![SEM Image](/{sem_image_path})\n\n"
                elif analysis_type == "EDS" and eds_image_path:
                    image_markdown += f"![EDS Image](/{eds_image_path})\n\n"
                elif analysis_type == "OPERATION":
                    if sem_image_path:
                        image_markdown += f"![SEM Image](/{sem_image_path})\n\n"
                    if eds_image_path:
                        image_markdown += f"![EDS Image](/{eds_image_path})\n\n"
                elif analysis_type == "EQUIPMENT":
                    if sem_image_path:
                        image_markdown += f"![SEM Image](/{sem_image_path})\n\n"
                    if eds_image_path:
                        image_markdown += f"![EDS Image](/{eds_image_path})\n\n"

                # 최종 마크다운 내용 조합
                report_markdown = image_markdown + markdown_content
                # ------------------------------

                # 리포트 저장 경로 설정 및 파일 쓰기
                try:
                    workspace_root = os.getcwd()
                    save_dir = os.path.join(workspace_root, "SEM_EDS", "reports")
                    os.makedirs(save_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_filename = f"{analysis_type.lower()}_report_{timestamp}.md"
                    report_path = os.path.join(save_dir, report_filename)

                    with open(report_path, "w", encoding="utf-8") as f:
                        f.write(report_markdown) # 이미지 링크가 추가된 내용 저장
                    print(f"Report successfully saved to: {report_path}")

                    # 성공 시 수정된 내용과 경로 반환
                    return markdown_content, str(report_path)

                except IOError as e:
                    st.error(f"리포트 파일 저장 중 오류 발생: {report_path}. 오류: {e}")
                    print(f"Error saving report to {report_path}: {e}")
                    return markdown_content, None # 저장 실패해도 내용은 반환
                except Exception as e:
                    st.error(f"리포트 저장 중 예상치 못한 오류 발생: {e}")
                    print(f"Unexpected error during report saving: {e}")
                    return markdown_content, None # 저장 실패해도 내용은 반환

    except Exception as e:
        st.error(f"리포트 생성 중 오류가 발생했습니다: {str(e)}")
        st.error("상세 오류:")
        st.code(str(e))
        return None, None
