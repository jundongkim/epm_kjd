"""
PRD(생산이슈리포트) 의미론적 분석 컴포넌트
생산 패턴 심층 분석, 라인/설비별 위험도 평가, 예측 분석을 포함
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

# LLM 응답 스트리밍 및 저장 함수
def stream_llm_response_prd(llm, prompt, placeholder, session_key=None, save_report=False, analysis_type=None):
    """LLM 응답을 실시간으로 스트리밍하여 표시하고 선택적으로 PRD 리포트를 저장합니다."""
    try:
        response_text = ""
        message_placeholder = placeholder.empty()

        # 세션에 저장된 결과가 있으면 바로 표시
        if session_key and session_key in st.session_state:
            message_placeholder.markdown(st.session_state[session_key])
            response_text = st.session_state[session_key]

            # 저장 옵션이 켜져 있으면 리포트 저장
            if save_report and analysis_type:
                save_markdown_report_prd(response_text, analysis_type)

            return response_text

        # 스트리밍 효과를 위한 표시 문자
        cursor = "▌"

        # 스트리밍 응답 처리
        for chunk in llm.stream(prompt):
            # 청크에서 텍스트 추출 (기존 로직과 동일)
            if hasattr(chunk, "content"):
                chunk_text = chunk.content
            elif isinstance(chunk, str):
                chunk_text = chunk
            elif isinstance(chunk, dict) and "content" in chunk:
                chunk_text = chunk["content"]
            else:
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
            report_path = save_markdown_report_prd(response_text, analysis_type)
            if report_path:
                st.success(f"PRD 리포트가 저장되었습니다: {report_path}")

        return response_text
    except Exception as e:
        error_msg = f"LLM 응답 스트리밍 오류 (PRD): {str(e)}"
        placeholder.error(error_msg)

        # 오류 메시지도 세션에 저장
        if session_key:
            st.session_state[session_key] = error_msg

        return None

# 마크다운 리포트 저장 함수
def save_markdown_report_prd(markdown_content, analysis_type):
    """PRD 마크다운 리포트를 파일로 저장합니다.

    Args:
        markdown_content (str): 저장할 마크다운 텍스트
        analysis_type (str): 분석 유형 (예: "prd_production_pattern", "prd_line_risk_assessment_5Line")

    Returns:
        str: 저장된 파일 경로 또는 None (저장 실패 시)
    """
    try:
        # 작업 디렉토리와 저장 경로 설정 (PRD용으로 변경)
        workspace_root = os.getcwd()
        save_dir = os.path.join(workspace_root, "PRD", "reports")
        os.makedirs(save_dir, exist_ok=True)

        # 현재 타임스탬프
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 파일명 설정
        report_filename = f"{analysis_type.lower()}_report_{timestamp}.md"
        report_path = os.path.join(save_dir, report_filename)

        # 리포트 헤더 추가
        report_header = f"""# {analysis_type.replace('prd_', '').replace('_', ' ').title()} 리포트 (PRD)
생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
        report_content = report_header + markdown_content

        # 파일 저장
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"PRD Report successfully saved to: {report_path}")
        return report_path

    except IOError as e:
        st.error(f"PRD 리포트 파일 저장 중 오류 발생: {e}")
        print(f"Error saving PRD report: {e}")
        return None
    except Exception as e:
        st.error(f"PRD 리포트 저장 중 예상치 못한 오류 발생: {e}")
        print(f"Unexpected error during PRD report saving: {e}")
        return None

def get_prd_df() -> pd.DataFrame:
    # 데이터 가져오기 (PRD용으로 변경)
    prd_data = st.session_state.prd_data

    # 데이터 전처리
    # 임시로 Cartesian product 방식으로 데이터 변환
    prd_row_list = []
    for entry in prd_data:
        date = entry.get('date', None)
        summary = entry.get('summary', {}).get('full_text', None)
        lines = entry.get('lines', [])
        equipments = entry.get('equipments', [])
        issues = entry.get('issues', [])
        for line in lines:
            for equipment in equipments:
                for issue in issues:
                    prd_row_list.append({
                        'date': date,
                        'summary': summary,
                        'line': line,
                        'equipment': equipment,
                        'issue': issue
                    })

    # 데이터프레임으로 변환
    prd_df = pd.DataFrame(prd_row_list)
    return prd_df

# 메인 컴포넌트 함수
def show_prd_semantic_analysis():
    """생산이슈리포트 의미론적 분석 컴포넌트"""
    st.title("🧠 생산이슈리포트 의미론적 분석")

    # 데이터 확인 (PRD용으로 변경)
    if "prd_data" not in st.session_state:
        st.error("생산이슈리포트 데이터가 로드되지 않았습니다.")
        st.info("상단 메뉴에서 다른 생산이슈리포트 메뉴를 클릭한 후 다시 시도해주세요.")
        return

    # 데이터 가져오기 (PRD용으로 변경)
    prd_data = get_prd_df()

    # 데이터프레임 변환
    if isinstance(prd_data, list):
        df = pd.DataFrame(prd_data)
    elif isinstance(prd_data, pd.DataFrame):
        df = prd_data # 이미 DataFrame인 경우 그대로 사용
    else:
        st.error("지원하지 않는 데이터 형식입니다. 리스트 또는 DataFrame이 필요합니다.")
        return

    # 날짜 변환 (문자열 -> datetime)
    if 'date' in df.columns:
        # NaT이 아닌 값만 필터링하여 변환 시도
        date_series = pd.to_datetime(df['date'].astype(str).str.split('\n').str[0], errors='coerce')
        df['date'] = date_series
    else:
        st.warning("날짜 정보가 없습니다. 일부 시간 기반 분석이 제한될 수 있습니다.")
        # 날짜가 없으면 임의로 생성하거나 시간 기반 분석을 비활성화해야 할 수 있음

    # LLM 초기화
    try:
        from langchain_ollama import ChatOllama

        # Ollama API 서버 URL 설정
        OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Ollama 모델 초기화 (세션 상태에서 모델 이름 가져오기 - prd 접두사 사용)
        llm = ChatOllama(
            model=st.session_state.get("selected_model", "gemma3:4b"),
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            streaming=True,
        )
    except ImportError:
        st.error("LangChain 라이브러리가 필요합니다. `pip install langchain langchain_ollama` 명령으로 설치해주세요.")
        return
    except Exception as e:
        st.error(f"LLM 초기화 오류: {str(e)}")
        st.warning("LLM을 사용할 수 없어 일부 분석이 제한됩니다.")
        llm = None

    # 분석 섹션 선택 (PRD용으로 수정)
    analysis_section = st.radio(
        "분석 유형 선택:",
        ["📊 생산 패턴 분석", "⚠️ 라인/설비별 위험도 평가", "📈 예측 분석"], # PRD 컨텍스트에 맞게 수정
        horizontal=True,
        key="prd_semantic_analysis_section" # PRD용 키 사용
    )

    if llm is None:
        st.warning("LLM 서비스를 사용할 수 없어 분석이 제한됩니다.")

    # 세션 상태에 분석 결과 저장을 위한 초기화 (PRD용으로 수정)
    if "prd_semantic_results" not in st.session_state:
        st.session_state.prd_semantic_results = {
            "production_pattern": None,
            "line_product_risk": {}, # 라인/설비별 위험도
            "predictive_analysis": None
        }

    if analysis_section == "📊 생산 패턴 분석":
        show_production_pattern_analysis_prd(df, llm)
    elif analysis_section == "⚠️ 라인/설비별 위험도 평가":
        show_line_equipment_risk_assessment_prd(df, llm)
    elif analysis_section == "📈 예측 분석":
        show_predictive_analysis_prd(df, llm)

# 생산 패턴 분석 함수
def show_production_pattern_analysis_prd(df, llm):
    """생산 패턴 심층 분석 표시 (PRD)"""
    st.markdown("#### 📊 생산 패턴 심층 분석")

    if llm is None:
        st.info("LLM 서비스를 사용할 수 없어 패턴 분석이 제한됩니다.")
        return

    # 세션 키 정의 (PRD용)
    session_key = "prd_semantic_production_pattern"
    eval_session_key = f"{session_key}_eval" # 평가 세션 키도 PRD용으로

    # 분석/평가 선택 탭
    tabs = st.tabs(["📝 분석 결과", "📊 품질 평가"])

    with tabs[0]:  # 분석 결과 탭
        # 재분석 버튼과 저장 버튼
        if session_key in st.session_state:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("🔄 재분석하기", key="prd_reanalyze_production_pattern"):
                    if session_key in st.session_state: del st.session_state[session_key]
                    if eval_session_key in st.session_state: del st.session_state[eval_session_key]
            with col3:
                if st.button("💾 리포트 저장", key="prd_save_production_pattern_report"):
                    report_path = save_markdown_report_prd(st.session_state[session_key], "prd_production_pattern")
                    if report_path:
                        st.success(f"PRD 리포트가 저장되었습니다: {report_path}")

        # 최근 10개 생산 이력 내용 추출 (PRD 필드 사용)
        if 'date' in df.columns and not df['date'].isnull().all():
            recent_works = df.sort_values('date', ascending=False).head(10)
        else:
            recent_works = df.head(10) # 날짜 없으면 그냥 상위 10개

        # PRD 필드 확인 및 선택
        prd_fields = ['line', 'equipment', 'issue', 'summary']
        available_fields = [f for f in prd_fields if f in recent_works.columns]

        if not available_fields:
             st.warning("분석에 필요한 PRD 필드(라인, 설비, 이슈, 요약)가 충분하지 않습니다.")
             return

        work_analysis_prompt = f"""
        다음은 최근 10개의 생산이슈리포트입니다. 이를 분석하여 주요 패턴과 인사이트를 도출해주세요:

        {recent_works[available_fields].to_string()}

        다음 관점에서 분석해주세요 (생산 관리 이력 맥락에서):
        1. 주요 발생 이슈 및 해결 패턴
        2. 반복되는 문제점과 가능한 근본 원인 (라인, 설비 연관성 포함)
        3. 생산 안정성 및 품질 개선을 위한 제안
        4. 공정 효율성 및 관리 개선을 위한 인사이트
        """

        # 저장 옵션
        save_checkbox = st.checkbox("분석 완료 후 자동으로 리포트 저장", key="prd_auto_save_production_pattern")

        # 스트리밍 표시를 위한 플레이스홀더 생성
        pattern_placeholder = st.empty()

        # 세션에 결과가 없을 때만 LLM 호출
        if session_key not in st.session_state:
            with st.spinner("생산 패턴 분석 중..."):
                response = stream_llm_response_prd(
                    llm,
                    work_analysis_prompt,
                    pattern_placeholder,
                    session_key=session_key,
                    save_report=save_checkbox,
                    analysis_type="prd_production_pattern"
                )
        else:
            # 저장된 결과 표시
            pattern_placeholder.markdown(st.session_state[session_key])


    with tabs[1]:  # 품질 평가 탭
        if session_key in st.session_state:
            col1, col2 = st.columns([3, 1])
            with col2:
                show_evaluation = st.button("🔍 평가하기", key="prd_evaluate_production_pattern") or eval_session_key in st.session_state

            if show_evaluation:
                try:
                    # TODO: PRD용 보고서 평가 모듈/함수 구현 또는 CMMS 모듈 재사용 결정 필요
                    # from components.prd.prd_report_evaluation import evaluate_report_quality_prd, display_evaluation_results_prd
                    # 여기서는 임시로 CMMS 평가 함수를 호출하는 것으로 가정 (추후 수정 필요)
                    from components.cmms.cmms_report_evaluation import evaluate_report_quality, display_evaluation_results

                    if eval_session_key not in st.session_state:
                        with st.spinner("PRD 보고서 품질을 평가하는 중..."):
                            # 평가 유형: 생산 패턴 분석 -> WORK_PATTERN
                            evaluation = evaluate_report_quality(st.session_state[session_key], "WORK_PATTERN")
                            st.session_state[eval_session_key] = evaluation

                    display_evaluation_results(st.session_state[eval_session_key]) # 결과 표시 함수도 PRD용으로 수정 필요할 수 있음
                except ImportError:
                     st.warning("CMMS 보고서 평가 기능 모듈을 찾을 수 없습니다. (PRD 평가 기능 구현 필요)")
                except Exception as e:
                    st.error(f"PRD 보고서 평가 중 오류가 발생했습니다: {str(e)}")

            elif eval_session_key not in st.session_state:
                st.info("👆 '평가하기' 버튼을 클릭하여 PRD 보고서 품질을 평가하세요.")
        else:
            st.warning("분석을 먼저 실행하세요. 분석 결과가 있어야 평가할 수 있습니다.")

# 라인/설비별 위험도 평가 함수
def show_line_equipment_risk_assessment_prd(df, llm):
    """라인/설비별 위험도 평가 표시 (PRD)"""
    st.markdown("#### ⚠️ 라인/설비별 위험도 평가")

    if llm is None:
        st.info("LLM 서비스를 사용할 수 없어 위험도 평가가 제한됩니다.")
        return

    # 위험도 평가 기준 선택
    assessment_target = st.radio(
        "위험도 평가 기준:",
        ["라인", "설비"],
        horizontal=True,
        key="prd_risk_assessment_target"
    )

    target_column = "line" if assessment_target == "라인" else "equipment" # 'line' 또는 'equipment'

    # 평가 기준별 최근 내용 집계 (PRD 필드 사용)
    if target_column not in df.columns:
        st.warning(f"'{target_column}' 컬럼이 데이터에 없어 위험도 평가를 수행할 수 없습니다.")
        return

    summary_fields = ['summary', 'issue', 'date'] # 필요한 필드 정의
    available_summary_fields = [f for f in summary_fields if f in df.columns]

    # 집계 함수 정의
    def aggregate_recent_info(x):
        # Series와 DataFrame을 모두 처리할 수 있도록 수정
        if isinstance(x, pd.Series):
            # Series인 경우는 그 자체가 하나의 열이므로 직접 반환
            return x.astype(str).head(5).to_string()

        # DataFrame인 경우
        if isinstance(x, pd.DataFrame):
            # 날짜가 있고 유효한 값이 있으면 최근 5개, 없으면 그냥 5개
            if 'date' in x.columns and not x['date'].isnull().all():
                x_sorted = x.sort_values('date', ascending=False)
            else:
                x_sorted = x
            recent_entries = x_sorted[available_summary_fields].head(5)
            return recent_entries.to_string() # 문자열로 반환

        return "정보 없음"

    # 요약 집계 시 오류 처리 추가
    def aggregate_details(x):
        # Series 객체와 DataFrame 객체 모두 처리할 수 있도록 수정
        if isinstance(x, pd.DataFrame) and 'summary' in x.columns:
            details = x['summary'].astype(str).dropna().tolist()[-5:]
            return '\n\n'.join(details)
        elif isinstance(x, pd.Series):
            # Series인 경우는 그 자체가 하나의 열이므로 직접 처리
            details = x.astype(str).dropna().tolist()[-5:]
            return '\n\n'.join(details)
        return "상세 내용 없음"

    # '이슈' 컬럼이 있는지 확인하고, 없으면 'count' 사용
    agg_dict = {
        'summary': aggregate_details
    }
    # 날짜 또는 다른 컬럼을 이용해 count 계산
    count_col = 'date' if 'date' in df.columns else df.columns[0] # 첫번째 컬럼이라도 사용
    agg_dict[count_col] = 'count'


    if 'issue' in df.columns:
        agg_dict['issue'] = lambda x: x.dropna().value_counts().head(3).to_dict() # 상위 3개 이슈

    # NaN 값 처리 후 집계
    df_filled = df.fillna({target_column: "미분류"})
    target_summary = df_filled.groupby(target_column).agg(agg_dict).reset_index()

    # 총 항목 수 기준으로 정렬 (count_col 사용)
    target_summary = target_summary.sort_values(count_col, ascending=False)

    # 상위 5개 항목만 평가
    top_targets = target_summary.head(5)

    if top_targets.empty:
        st.warning(f"'{target_column}' 기준으로 집계할 데이터가 없습니다.")
        return

    # 전체 재분석 버튼 및 모든 보고서 저장 버튼
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button(f"🔄 모든 {assessment_target} 재분석", key="prd_reanalyze_all_risk"):
            for target_val in top_targets[target_column]:
                session_key = f"prd_semantic_risk_{target_column}_{target_val}"
                eval_session_key = f"{session_key}_eval"
                if session_key in st.session_state: del st.session_state[session_key]
                if eval_session_key in st.session_state: del st.session_state[eval_session_key]
    with col3:
        if st.button(f"💾 모든 {assessment_target} 리포트 저장", key="prd_save_all_risk_reports"):
            saved_reports = []
            for target_val in top_targets[target_column]:
                session_key = f"prd_semantic_risk_{target_column}_{target_val}"
                if session_key in st.session_state:
                    report_path = save_markdown_report_prd(
                        st.session_state[session_key],
                        f"prd_{target_column}_risk_{target_val}"
                    )
                    if report_path:
                        saved_reports.append(report_path)
            if saved_reports:
                st.success(f"{len(saved_reports)}개 리포트가 저장되었습니다.")

    # 자동 저장 옵션
    auto_save = st.checkbox("분석 완료 후 자동으로 리포트 저장", key="prd_auto_save_risk")

    for _, row in top_targets.iterrows():
        target_value = row[target_column]
        session_key = f"prd_semantic_risk_{target_column}_{target_value}"
        eval_session_key = f"{session_key}_eval"

        st.markdown(f"### {assessment_target} '{target_value}' 위험도 평가")

        # 분석/평가 선택 탭
        tabs = st.tabs(["📝 분석 결과", "📊 품질 평가"])

        with tabs[0]:  # 분석 결과 탭
            if session_key in st.session_state:
                col1_btn, col2_btn, col3_btn = st.columns([2, 1, 1])
                with col2_btn:
                    if st.button("🔄 재분석", key=f"prd_reanalyze_{target_column}_{target_value}"):
                        if session_key in st.session_state: del st.session_state[session_key]
                        if eval_session_key in st.session_state: del st.session_state[eval_session_key]
                with col3_btn:
                    if st.button("💾 저장", key=f"prd_save_{target_column}_{target_value}"):
                        report_path = save_markdown_report_prd(
                            st.session_state[session_key],
                            f"prd_{target_column}_risk_{target_value}"
                        )
                        if report_path:
                            st.success(f"리포트가 저장되었습니다: {report_path}")

            # 프롬프트 생성 (PRD 컨텍스트 반영)
            issue_info = f"주요 이슈: {row.get('issue', '정보 없음')}"
            total_count = row.get(count_col, 0)
            risk_prompt = f"""
            다음 생산 {assessment_target}의 관리 이력을 분석하여 위험도를 평가해주세요:

            {assessment_target}: {target_value}
            총 기록 건수: {total_count} ({issue_info})
            최근 상세 내용: {row.get('summary', '정보 없음')}

            다음 형식으로 답변해주세요 (생산 안정성 및 품질 관점에서):
            1. 위험도 점수 (1-10, 높을수록 위험)
            2. 주요 위험 요소 (품질 문제, 공정 불안정성, 반복 이슈 등)
            3. 권장 조치사항 (모니터링 강화, 공정 개선, 원인 분석 등)
            4. 위험도 감소 및 생산성 향상 전략
            """

            # 스트리밍 표시를 위한 플레이스홀더 생성
            risk_placeholder = st.empty()

            # 세션에 결과가 없을 때만 LLM 호출
            if session_key not in st.session_state:
                with st.spinner(f"{assessment_target} '{target_value}' 위험도 분석 중..."):
                    response = stream_llm_response_prd(
                        llm,
                        risk_prompt,
                        risk_placeholder,
                        session_key=session_key,
                        save_report=auto_save,
                        analysis_type=f"prd_{target_column}_risk_{target_value}"
                    )
            else:
                # 저장된 결과 표시
                risk_placeholder.markdown(st.session_state[session_key])

        with tabs[1]:  # 품질 평가 탭
            if session_key in st.session_state:
                col1_eval, col2_eval = st.columns([3, 1])
                with col2_eval:
                    show_evaluation = st.button("🔍 평가하기", key=f"prd_evaluate_{target_column}_{target_value}") or eval_session_key in st.session_state

                if show_evaluation:
                    try:
                        # TODO: PRD용 보고서 평가 모듈/함수 구현 또는 CMMS 모듈 재사용 결정 필요
                        from components.cmms.cmms_report_evaluation import evaluate_report_quality, display_evaluation_results

                        if eval_session_key not in st.session_state:
                            with st.spinner("PRD 보고서 품질을 평가하는 중..."):
                                # 평가 유형: 위험도 평가 -> RISK_ASSESSMENT
                                evaluation = evaluate_report_quality(st.session_state[session_key], "RISK_ASSESSMENT")
                                st.session_state[eval_session_key] = evaluation

                        display_evaluation_results(st.session_state[eval_session_key]) # 결과 표시 함수 수정 필요할 수 있음
                    except ImportError:
                         st.warning("CMMS 보고서 평가 기능 모듈을 찾을 수 없습니다. (PRD 평가 기능 구현 필요)")
                    except Exception as e:
                        st.error(f"PRD 보고서 평가 중 오류가 발생했습니다: {str(e)}")

                elif eval_session_key not in st.session_state:
                    st.info("👆 '평가하기' 버튼을 클릭하여 PRD 보고서 품질을 평가하세요.")
            else:
                st.warning("분석을 먼저 실행하세요. 분석 결과가 있어야 평가할 수 있습니다.")

        st.markdown("---")

# 예측 분석 함수
def show_predictive_analysis_prd(df, llm):
    """예측 분석 표시 (PRD)"""
    st.markdown("#### 📈 예측 분석")

    if llm is None:
        st.info("LLM 서비스를 사용할 수 없어 예측 분석이 제한됩니다.")
        return

    # 세션 키 정의 (PRD용)
    session_key = "prd_semantic_predictive"
    eval_session_key = f"{session_key}_eval"

    # 분석 기준 선택 (예: 라인별 이슈 발생 주기 또는 설비별)
    prediction_target = st.radio(
        "예측 분석 기준:",
        ["라인", "설비"],
        horizontal=True,
        key="prd_prediction_target"
    )
    target_column = "line" if prediction_target == "라인" else "equipment" # 'line' 또는 'equipment'

    if target_column not in df.columns or 'date' not in df.columns or df['date'].isnull().all():
        st.warning(f"'{target_column}' 또는 'date' 컬럼이 유효하지 않아 예측 분석을 위한 주기 계산이 어렵습니다.")
        return

    # 기준별 이슈 발생 주기 분석 (예시: 평균 발생 간격)
    df_filtered = df.dropna(subset=['date', target_column])
    if df_filtered.empty:
        st.warning(f"'{target_column}' 또는 'date'에 유효한 데이터가 없어 주기 계산이 불가합니다.")
        return

    df_sorted = df_filtered.sort_values(['date'])

    # 집계 함수 정의 (오류 처리 강화)
    def calculate_mean_interval(dates):
        if len(dates) < 2:
            return None
        try:
            diffs = dates.diff().dt.days
            mean_diff = diffs.mean()
            return mean_diff if pd.notna(mean_diff) else None
        except Exception:
            return None

    issue_cycles = df_sorted.groupby(target_column).agg(
        평균_발생_간격_일=(('date', calculate_mean_interval)),
        최근_이슈_일자=(('date', 'max')),
        총_이슈_건수=(('date', 'count'))
    ).reset_index()

    # NaN 값 제거 및 데이터 필터링 (예: 최소 2건 이상 발생한 경우만)
    issue_cycles = issue_cycles.dropna(subset=['평균_발생_간격_일'])
    issue_cycles = issue_cycles[issue_cycles['총_이슈_건수'] >= 2]

    if not issue_cycles.empty:
        # 분석/평가 선택 탭
        tabs = st.tabs(["📝 분석 결과", "📊 품질 평가"])

        with tabs[0]:  # 분석 결과 탭
            if session_key in st.session_state:
                col1_btn, col2_btn, col3_btn = st.columns([2, 1, 1])
                with col2_btn:
                    if st.button("🔄 재분석하기", key="prd_reanalyze_predictive"):
                         if session_key in st.session_state: del st.session_state[session_key]
                         if eval_session_key in st.session_state: del st.session_state[eval_session_key]
                with col3_btn:
                    if st.button("💾 리포트 저장", key="prd_save_predictive_report"):
                        report_path = save_markdown_report_prd(
                            st.session_state[session_key],
                            f"prd_predictive_analysis_{target_column}"
                        )
                        if report_path:
                            st.success(f"PRD 리포트가 저장되었습니다: {report_path}")

            # 프롬프트 생성 (PRD 컨텍스트 반영)
            predictive_prompt = f"""
            다음은 생산 {prediction_target}별 평균 이슈 발생 간격 데이터입니다:

            {issue_cycles.to_string(index=False)}

            이 데이터를 바탕으로 생산 관리 관점에서 분석해주세요:
            1. 향후 발생 가능성이 높은 이슈 예측 ({prediction_target}별)
            2. 이슈 발생 주기가 짧거나 불규칙한 {prediction_target} 식별 및 원인 추정
            3. 선제적 품질 관리 및 공정 개선을 위한 제안
            4. 데이터 기반 생산 계획 및 관리 방안
            """

            # 자동 저장 옵션
            save_checkbox = st.checkbox("분석 완료 후 자동으로 리포트 저장", key="prd_auto_save_predictive")

            # 스트리밍 표시를 위한 플레이스홀더 생성
            predictive_placeholder = st.empty()

            # 세션에 결과가 없을 때만 LLM 호출
            if session_key not in st.session_state:
                with st.spinner(f"{prediction_target} 기반 예측 분석 중..."):
                    response = stream_llm_response_prd(
                        llm,
                        predictive_prompt,
                        predictive_placeholder,
                        session_key=session_key,
                        save_report=save_checkbox,
                        analysis_type=f"prd_predictive_analysis_{target_column}"
                    )
            else:
                 # 저장된 결과 표시
                 predictive_placeholder.markdown(st.session_state[session_key])

        with tabs[1]:  # 품질 평가 탭
            if session_key in st.session_state:
                col1_eval, col2_eval = st.columns([3, 1])
                with col2_eval:
                    show_evaluation = st.button("🔍 평가하기", key="prd_evaluate_predictive") or eval_session_key in st.session_state

                if show_evaluation:
                    try:
                        # TODO: PRD용 보고서 평가 모듈/함수 구현 또는 CMMS 모듈 재사용 결정 필요
                        from components.cmms.cmms_report_evaluation import evaluate_report_quality, display_evaluation_results

                        if eval_session_key not in st.session_state:
                            with st.spinner("PRD 보고서 품질을 평가하는 중..."):
                                # 평가 유형: 예측 분석 -> PREDICTIVE_MAINTENANCE
                                evaluation = evaluate_report_quality(st.session_state[session_key], "PREDICTIVE_MAINTENANCE")
                                st.session_state[eval_session_key] = evaluation

                        display_evaluation_results(st.session_state[eval_session_key]) # 결과 표시 함수 수정 필요할 수 있음
                    except ImportError:
                         st.warning("CMMS 보고서 평가 기능 모듈을 찾을 수 없습니다. (PRD 평가 기능 구현 필요)")
                    except Exception as e:
                        st.error(f"PRD 보고서 평가 중 오류가 발생했습니다: {str(e)}")

                elif eval_session_key not in st.session_state:
                    st.info("👆 '평가하기' 버튼을 클릭하여 PRD 보고서 품질을 평가하세요.")
            else:
                st.warning("분석을 먼저 실행하세요. 분석 결과가 있어야 평가할 수 있습니다.")
    else:
        st.warning(f"{prediction_target}별 이슈 발생 주기를 계산할 충분한 데이터가 없습니다 (최소 2건 이상 필요).")

# 메인 함수 (테스트용) - 실제 앱에서는 app.py에서 호출됨
if __name__ == '__main__':
    # Streamlit 앱 설정을 위해 실제 app.py에서 사용하는 방식을 따름
    # 예시: 데이터 로드 및 세션 상태 초기화
    if 'prd_data' not in st.session_state:
        try:
            # 실제 데이터 로더 사용 시도
            from components.prd.prd_data_loader import load_prd_data
            loaded_data = load_prd_data()
            if loaded_data:
                 st.session_state.prd_data = pd.DataFrame(loaded_data)
                 print("실제 PRD 데이터 로드 성공")
            else:
                 raise ValueError("로드된 데이터가 비어 있습니다.")
        except Exception as e:
             print(f"실제 PRD 데이터 로드 실패: {e}. 샘플 데이터 사용.")
             # 임시 샘플 데이터 사용
             st.session_state.prd_data = pd.DataFrame({
                 'line': [f'{i % 2 + 5}Line' for i in range(25)],
                 'equipment': [f'Equipment_{chr(65 + i % 3)}' for i in range(25)],
                 'issue': [f'IssueType_{i % 4}' for i in range(25)],
                 'summary': [f'Detail for entry {i}. 라인 점검 중 특이사항 발견.' for i in range(25)],
                 'date': pd.to_datetime([datetime.now() - timedelta(days=i*2) for i in range(25)])
             })

    # 컴포넌트 실행
    show_prd_semantic_analysis()