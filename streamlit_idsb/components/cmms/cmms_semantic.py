"""
CMMS 의미론적 분석 컴포넌트
작업 패턴 심층 분석, 설비별 위험도 평가, 예지 보전 분석을 포함
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

def stream_llm_response(llm, prompt, placeholder, session_key=None, save_report=False, analysis_type=None):
    """LLM 응답을 실시간으로 스트리밍하여 표시하고 선택적으로 저장합니다."""
    try:
        response_text = ""
        message_placeholder = placeholder.empty()

        # 세션에 저장된 결과가 있으면 바로 표시
        if session_key and session_key in st.session_state:
            message_placeholder.markdown(st.session_state[session_key])
            response_text = st.session_state[session_key]

            # 저장 옵션이 켜져 있으면 리포트 저장
            if save_report and analysis_type:
                save_markdown_report(response_text, analysis_type)

            return response_text

        # 스트리밍 효과를 위한 표시 문자
        cursor = "▌"

        # 스트리밍 응답 처리
        for chunk in llm.stream(prompt):
            # 청크에서 텍스트 추출
            if hasattr(chunk, "content"):
                chunk_text = chunk.content
            elif isinstance(chunk, str):
                chunk_text = chunk
            elif isinstance(chunk, dict) and "content" in chunk:
                chunk_text = chunk["content"]
            else:
                # 기타 형식 처리 - 튜플 등
                try:
                    if isinstance(chunk, tuple) and len(chunk) > 0 and chunk[0] == 'content':
                        chunk_text = chunk[1]
                    else:
                        chunk_text = str(chunk)
                except:
                    chunk_text = str(chunk)

            # 응답 텍스트에 추가
            response_text += chunk_text

            # 플레이스홀더 업데이트 - 커서 포함
            message_placeholder.markdown(response_text + cursor)

        # 최종 응답 표시 (커서 제거)
        message_placeholder.markdown(response_text)

        # 세션 상태에 저장
        if session_key:
            st.session_state[session_key] = response_text

        # 저장 옵션이 켜져 있으면 리포트 저장
        if save_report and analysis_type:
            report_path = save_markdown_report(response_text, analysis_type)
            if report_path:
                st.success(f"리포트가 저장되었습니다: {report_path}")

        return response_text
    except Exception as e:
        error_msg = f"LLM 응답 스트리밍 오류: {str(e)}"
        placeholder.error(error_msg)

        # 오류 메시지도 세션에 저장
        if session_key:
            st.session_state[session_key] = error_msg

        return None

def save_markdown_report(markdown_content, analysis_type):
    """마크다운 리포트를 파일로 저장합니다.

    Args:
        markdown_content (str): 저장할 마크다운 텍스트
        analysis_type (str): 분석 유형 ("work_pattern", "risk_assessment", "predictive_maintenance")

    Returns:
        str: 저장된 파일 경로 또는 None (저장 실패 시)
    """
    try:
        # 작업 디렉토리와 저장 경로 설정
        workspace_root = os.getcwd()
        save_dir = os.path.join(workspace_root, "CMMS", "reports")
        os.makedirs(save_dir, exist_ok=True)

        # 현재 타임스탬프
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 파일명 설정
        report_filename = f"{analysis_type.lower()}_report_{timestamp}.md"
        report_path = os.path.join(save_dir, report_filename)

        # 리포트 헤더 추가
        report_header = f"""# {analysis_type.replace('_', ' ').title()} 리포트
생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
        report_content = report_header + markdown_content

        # 파일 저장
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"Report successfully saved to: {report_path}")
        return report_path

    except IOError as e:
        st.error(f"리포트 파일 저장 중 오류 발생: {e}")
        print(f"Error saving report: {e}")
        return None
    except Exception as e:
        st.error(f"리포트 저장 중 예상치 못한 오류 발생: {e}")
        print(f"Unexpected error during report saving: {e}")
        return None

def show_cmms_semantic_analysis():
    """CMMS 의미론적 분석 컴포넌트"""
    st.title("🧠 CMMS 의미론적 분석")

    # 데이터 확인
    if "cmms_data" not in st.session_state:
        st.error("일일업무일지 데이터가 로드되지 않았습니다.")
        st.info("상단 메뉴에서 다른 CMMS 메뉴를 클릭한 후 다시 시도해주세요.")
        return

    # 데이터 가져오기
    cmms_data = st.session_state.cmms_data

    # 데이터프레임 변환 (리스트인 경우 DataFrame으로 변환)
    if isinstance(cmms_data, list):
        df = pd.DataFrame(cmms_data)
    else:
        df = cmms_data

    # 작업 일자 변환 (문자열 -> datetime)
    if '작업 일자' in df.columns:
        df['작업 일자'] = pd.to_datetime(df['작업 일자'].str.split('\n').str[0], errors='coerce')
    else:  # 작업 일자 컬럼이 없는 경우 샘플 데이터 생성
        st.warning("작업 일자 정보가 없습니다. 샘플 데이터를 사용합니다.")
        # 샘플 데이터 생성 - 현재로부터 최근 90일 동안의 임의 날짜
        now = datetime.now()
        df['작업 일자'] = [now - timedelta(days=i) for i in range(min(len(df), 90))]

    # LLM 초기화
    try:
        from langchain_ollama import ChatOllama

        # Ollama API 서버 URL 설정
        OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Ollama 모델 초기화 (세션 상태에서 모델 이름 가져오기)
        llm = ChatOllama(
            model=st.session_state.get("selected_model", "gemma3:4b"),
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            streaming=True,  # 스트리밍 응답 활성화
        )
    except ImportError:
        st.error("LangChain 라이브러리가 필요합니다. `pip install langchain langchain_ollama` 명령으로 설치해주세요.")
        return
    except Exception as e:
        st.error(f"LLM 초기화 오류: {str(e)}")
        st.warning("LLM을 사용할 수 없어 일부 분석이 제한됩니다.")
        llm = None

    # 분석 섹션 선택
    analysis_section = st.radio(
        "분석 유형 선택:",
        ["📊 작업 패턴 심층 분석", "⚠️ 설비별 위험도 평가", "🔮 예지 보전 분석"],
        horizontal=True,
        key="cmms_semantic_analysis_section"
    )

    if llm is None:
        st.warning("LLM 서비스를 사용할 수 없어 분석이 제한됩니다.")

    # 세션 상태에 분석 결과 저장을 위한 초기화
    if "cmms_semantic_results" not in st.session_state:
        st.session_state.cmms_semantic_results = {
            "work_pattern": None,
            "risk_assessment": {},
            "predictive_maintenance": None
        }

    if analysis_section == "📊 작업 패턴 심층 분석":
        show_work_pattern_analysis(df, llm)
    elif analysis_section == "⚠️ 설비별 위험도 평가":
        show_risk_assessment(df, llm)
    elif analysis_section == "🔮 예지 보전 분석":
        show_predictive_maintenance(df, llm)

def show_work_pattern_analysis(df, llm):
    """작업 패턴 심층 분석 표시"""
    st.markdown("#### 📊 작업 패턴 심층 분석")

    if llm is None:
        st.info("LLM 서비스를 사용할 수 없어 패턴 분석이 제한됩니다.")
        return

    # 이미 분석 결과가 세션에 있는지 확인
    session_key = "cmms_semantic_work_pattern"
    eval_session_key = f"{session_key}_eval"

    # 분석/평가 선택 탭
    tabs = st.tabs(["📝 분석 결과", "📊 품질 평가"])

    with tabs[0]:  # 분석 결과 탭
        # 재분석 버튼과 저장 버튼
        if session_key in st.session_state:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("🔄 재분석하기", key="reanalyze_work_pattern"):
                    del st.session_state[session_key]
                    if eval_session_key in st.session_state:
                        del st.session_state[eval_session_key]
            with col3:
                if st.button("💾 리포트 저장", key="save_work_pattern_report"):
                    report_path = save_markdown_report(st.session_state[session_key], "work_pattern")
                    if report_path:
                        st.success(f"리포트가 저장되었습니다: {report_path}")

        # 최근 10개 작업 내용 추출
        recent_works = df.sort_values('작업 일자', ascending=False).head(10)
        work_analysis_prompt = f"""
        다음은 최근 10개의 설비 유지보수 작업 내용입니다. 이를 분석하여 주요 패턴과 인사이트를 도출해주세요:

        {recent_works[['설비번호', '작업 종류', '작업 상세내용']].to_string()}

        다음 관점에서 분석해주세요:
        1. 주요 문제점과 해결 패턴
        2. 반복되는 이슈와 근본 원인
        3. 예방적 유지보수를 위한 제안
        4. 작업 효율성 개선을 위한 인사이트
        """

        # 저장 옵션
        save_checkbox = st.checkbox("분석 완료 후 자동으로 리포트 저장", key="auto_save_work_pattern")

        # 스트리밍 표시를 위한 플레이스홀더 생성
        pattern_placeholder = st.empty()
        # 스트리밍 헬퍼 함수 호출 (저장 옵션 전달)
        response = stream_llm_response(
            llm,
            work_analysis_prompt,
            pattern_placeholder,
            session_key=session_key,
            save_report=save_checkbox,
            analysis_type="work_pattern"
        )

    with tabs[1]:  # 품질 평가 탭
        if session_key in st.session_state:
            # 평가 버튼 - 오른쪽에 배치
            col1, col2 = st.columns([3, 1])
            with col2:
                show_evaluation = st.button("🔍 평가하기", key="evaluate_work_pattern") or eval_session_key in st.session_state

            if show_evaluation:
                try:
                    from components.cmms.cmms_report_evaluation import evaluate_report_quality, display_evaluation_results

                    # 평가 결과가 저장되어 있지 않거나 재평가 버튼을 누른 경우에만 평가 수행
                    if eval_session_key not in st.session_state:
                        with st.spinner("보고서 품질을 평가하는 중..."):
                            # 평가 수행
                            evaluation = evaluate_report_quality(st.session_state[session_key], "WORK_PATTERN")
                            # 평가 결과 저장
                            st.session_state[eval_session_key] = evaluation

                    # 저장된 평가 결과 표시 - 전체 너비 사용
                    display_evaluation_results(st.session_state[eval_session_key])
                except Exception as e:
                    st.error(f"보고서 평가 중 오류가 발생했습니다: {str(e)}")

            elif eval_session_key not in st.session_state:
                st.info("👆 '평가하기' 버튼을 클릭하여 보고서 품질을 평가하세요.")
        else:
            st.warning("분석을 먼저 실행하세요. 분석 결과가 있어야 평가할 수 있습니다.")

def show_risk_assessment(df, llm):
    """설비별 위험도 평가 표시"""
    st.markdown("#### ⚠️ 설비별 위험도 평가")

    if llm is None:
        st.info("LLM 서비스를 사용할 수 없어 위험도 평가가 제한됩니다.")
        return

    # 설비별 최근 작업 내용 집계
    equipment_summary = df.groupby('설비번호').agg({
        '작업 상세내용': lambda x: '\n\n'.join(x.astype(str).tolist()[-5:]),  # 최근 5개 작업
        '작업 종류': 'count'
    }).sort_values('작업 종류', ascending=False).reset_index()

    # 상위 5개 설비만 평가
    top_equipment = equipment_summary.head(5)

    # 전체 재분석 버튼 및 모든 보고서 저장 버튼
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 모든 설비 재분석", key="reanalyze_all_risk"):
            # 모든 설비의 위험도 평가 결과 삭제
            for equip in top_equipment['설비번호']:
                session_key = f"cmms_semantic_risk_{equip}"
                eval_session_key = f"{session_key}_eval"
                if session_key in st.session_state:
                    del st.session_state[session_key]
                if eval_session_key in st.session_state:
                    del st.session_state[eval_session_key]
    with col3:
        if st.button("💾 모든 리포트 저장", key="save_all_risk_reports"):
            # 모든 설비 리포트 저장
            saved_reports = []
            for equip in top_equipment['설비번호']:
                session_key = f"cmms_semantic_risk_{equip}"
                if session_key in st.session_state:
                    report_path = save_markdown_report(
                        st.session_state[session_key],
                        f"risk_assessment_{equip}"
                    )
                    if report_path:
                        saved_reports.append(report_path)

            if saved_reports:
                st.success(f"{len(saved_reports)}개 리포트가 저장되었습니다.")

    # 자동 저장 옵션
    auto_save = st.checkbox("분석 완료 후 자동으로 리포트 저장", key="auto_save_risk")

    for _, row in top_equipment.iterrows():
        equip_no = row['설비번호']
        session_key = f"cmms_semantic_risk_{equip_no}"
        eval_session_key = f"{session_key}_eval"

        st.markdown(f"### 설비 {equip_no} 위험도 평가")

        # 분석/평가 선택 탭
        tabs = st.tabs(["📝 분석 결과", "📊 품질 평가"])

        with tabs[0]:  # 분석 결과 탭
            # 개별 설비 재분석 버튼 및 저장 버튼
            if session_key in st.session_state:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col2:
                    if st.button("🔄 재분석", key=f"reanalyze_{equip_no}"):
                        del st.session_state[session_key]
                        if eval_session_key in st.session_state:
                            del st.session_state[eval_session_key]
                with col3:
                    if st.button("💾 저장", key=f"save_{equip_no}"):
                        report_path = save_markdown_report(
                            st.session_state[session_key],
                            f"risk_assessment_{equip_no}"
                        )
                        if report_path:
                            st.success(f"리포트가 저장되었습니다: {report_path}")

            risk_prompt = f"""
            다음 설비의 작업 이력을 분석하여 위험도를 평가해주세요:

            설비번호: {equip_no}
            총 작업 건수: {row['작업 종류']}
            최근 작업 내용: {row['작업 상세내용']}

            다음 형식으로 답변해주세요:
            1. 위험도 점수 (1-10)
            2. 주요 위험 요소
            3. 권장 조치사항
            4. 위험도 감소 전략
            """

            # 스트리밍 표시를 위한 플레이스홀더 생성
            risk_placeholder = st.empty()
            # 스트리밍 헬퍼 함수 호출 (자동 저장 옵션 포함)
            response = stream_llm_response(
                llm,
                risk_prompt,
                risk_placeholder,
                session_key=session_key,
                save_report=auto_save,
                analysis_type=f"risk_assessment_{equip_no}"
            )

        with tabs[1]:  # 품질 평가 탭
            if session_key in st.session_state:
                # 평가 버튼 - 오른쪽에 배치
                col1, col2 = st.columns([3, 1])
                with col2:
                    show_evaluation = st.button("🔍 평가하기", key=f"evaluate_{equip_no}") or eval_session_key in st.session_state

                if show_evaluation:
                    try:
                        from components.cmms.cmms_report_evaluation import evaluate_report_quality, display_evaluation_results

                        # 평가 결과가 저장되어 있지 않거나 재평가 버튼을 누른 경우에만 평가 수행
                        if eval_session_key not in st.session_state:
                            with st.spinner("보고서 품질을 평가하는 중..."):
                                # 평가 수행
                                evaluation = evaluate_report_quality(st.session_state[session_key], "RISK_ASSESSMENT")
                                # 평가 결과 저장
                                st.session_state[eval_session_key] = evaluation

                        # 저장된 평가 결과 표시 - 전체 너비 사용
                        display_evaluation_results(st.session_state[eval_session_key])
                    except Exception as e:
                        st.error(f"보고서 평가 중 오류가 발생했습니다: {str(e)}")

                elif eval_session_key not in st.session_state:
                    st.info("👆 '평가하기' 버튼을 클릭하여 보고서 품질을 평가하세요.")
            else:
                st.warning("분석을 먼저 실행하세요. 분석 결과가 있어야 평가할 수 있습니다.")

        st.markdown("---")  # 구분선 추가

def show_predictive_maintenance(df, llm):
    """예지 보전 분석 표시"""
    st.markdown("#### 🔮 예지 보전 분석")

    if llm is None:
        st.info("LLM 서비스를 사용할 수 없어 예지 보전 분석이 제한됩니다.")
        return

    # 이미 분석 결과가 세션에 있는지 확인
    session_key = "cmms_semantic_predictive"
    eval_session_key = f"{session_key}_eval"

    # 설비별 작업 주기 분석
    maintenance_cycles = df.groupby('설비번호').agg({
        '작업 일자': lambda x: x.diff().mean().days if len(x) > 1 else None
    }).reset_index()

    # NaN 값 제거
    maintenance_cycles = maintenance_cycles.dropna()

    if not maintenance_cycles.empty:
        # 분석/평가 선택 탭
        tabs = st.tabs(["📝 분석 결과", "📊 품질 평가"])

        with tabs[0]:  # 분석 결과 탭
            # 재분석 버튼과 저장 버튼
            if session_key in st.session_state:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col2:
                    if st.button("🔄 재분석하기", key="reanalyze_predictive"):
                        del st.session_state[session_key]
                        if eval_session_key in st.session_state:
                            del st.session_state[eval_session_key]
                with col3:
                    if st.button("💾 리포트 저장", key="save_predictive_report"):
                        report_path = save_markdown_report(
                            st.session_state[session_key],
                            "predictive_maintenance"
                        )
                        if report_path:
                            st.success(f"리포트가 저장되었습니다: {report_path}")

            predictive_prompt = f"""
            다음은 설비별 평균 작업 주기 데이터입니다:

            {maintenance_cycles.to_string()}

            이 데이터를 바탕으로:
            1. 최적의 예방 정비 주기 제안
            2. 작업 주기가 비정상적인 설비 식별
            3. 예지 보전을 위한 모니터링 포인트 제안

            위 세 가지 관점에서 분석해주세요.
            """

            # 자동 저장 옵션
            save_checkbox = st.checkbox("분석 완료 후 자동으로 리포트 저장", key="auto_save_predictive")

            # 스트리밍 표시를 위한 플레이스홀더 생성
            predictive_placeholder = st.empty()
            # 스트리밍 헬퍼 함수 호출 (저장 옵션 포함)
            response = stream_llm_response(
                llm,
                predictive_prompt,
                predictive_placeholder,
                session_key=session_key,
                save_report=save_checkbox,
                analysis_type="predictive_maintenance"
            )

        with tabs[1]:  # 품질 평가 탭
            if session_key in st.session_state:
                # 평가 버튼 - 오른쪽에 배치
                col1, col2 = st.columns([3, 1])
                with col2:
                    show_evaluation = st.button("🔍 평가하기", key="evaluate_predictive") or eval_session_key in st.session_state

                if show_evaluation:
                    try:
                        from components.cmms.cmms_report_evaluation import evaluate_report_quality, display_evaluation_results

                        # 평가 결과가 저장되어 있지 않거나 재평가 버튼을 누른 경우에만 평가 수행
                        if eval_session_key not in st.session_state:
                            with st.spinner("보고서 품질을 평가하는 중..."):
                                # 평가 수행
                                evaluation = evaluate_report_quality(st.session_state[session_key], "PREDICTIVE_MAINTENANCE")
                                # 평가 결과 저장
                                st.session_state[eval_session_key] = evaluation

                        # 저장된 평가 결과 표시 - 전체 너비 사용
                        display_evaluation_results(st.session_state[eval_session_key])
                    except Exception as e:
                        st.error(f"보고서 평가 중 오류가 발생했습니다: {str(e)}")

                elif eval_session_key not in st.session_state:
                    st.info("👆 '평가하기' 버튼을 클릭하여 보고서 품질을 평가하세요.")
            else:
                st.warning("분석을 먼저 실행하세요. 분석 결과가 있어야 평가할 수 있습니다.")
    else:
        st.warning("작업 주기를 계산할 충분한 데이터가 없습니다.")