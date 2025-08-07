"""
SEM-EDS 분석 UI 모듈
"""
import os
import streamlit as st
from datetime import datetime
from components.ai_utils import init_session_state
from components.sem_eds.file_utils import create_sem_eds_folders, save_uploaded_file, get_image_files_in_directory
from components.sem_eds.image_utils import process_uploaded_image, load_image_from_directory
from components.sem_eds.analysis import extract_image_info, generate_analysis_report
from components.sem_eds.report_evaluation import evaluate_report_quality

def show_sem_analysis():
    """SEM 이미지 분석 기능"""
    # 세션 상태 초기화 - 모든 함수에서 동일한 키 프리픽스 사용
    init_session_state(key_prefix="sem_eds")

    # 이미지 데이터 및 분석 결과 관련 세션 상태 초기화
    if "sem_image_data" not in st.session_state:
        st.session_state["sem_image_data"] = None
    if "sem_info" not in st.session_state:
        st.session_state["sem_info"] = None
    if "sem_report" not in st.session_state:
        st.session_state["sem_report"] = None
    if "sem_report_path" not in st.session_state:
        st.session_state["sem_report_path"] = None
    if "sem_metadata" not in st.session_state:
        st.session_state["sem_metadata"] = None
    if "sem_raw_response" not in st.session_state:
        st.session_state["sem_raw_response"] = None

    # 사이드바에서 설정된 모델과 온도 가져오기
    selected_model = st.session_state.get("selected_model", "gemma3:4b")
    temperature = st.session_state.get("temperature", 0.7)

    st.header("SEM 이미지 분석")

    # 폴더 구조 생성
    base_dir = create_sem_eds_folders()

    # 탭 인터페이스 생성
    select_tab, upload_tab = st.tabs(["디렉토리에서 선택", "이미지 업로드"])

    # 탭 1: 디렉토리에서 이미지 선택
    with select_tab:
        st.subheader("SEM 이미지 선택")

        # 이미지 목록 새로고침 버튼
        col1, col2 = st.columns([1, 9])
        with col1:
            refresh_button = st.button("🔄", key="sem_refresh")
        with col2:
            st.text("이미지 목록 새로고침")

        # 이미지 파일 목록 가져오기
        sem_image_files = get_image_files_in_directory(folder="images")

        if not sem_image_files:
            st.warning("이미지 폴더(SEM_EDS/images)에 이미지 파일이 없습니다. 이미지 파일을 추가한 후 새로고침 버튼을 눌러주세요.")

        # 이미지 선택 박스
        selected_sem_file = st.selectbox(
            "분석할 SEM 이미지 선택",
            options=[""] + sem_image_files,
            index=0,
            key="sem_file_select"
        )

        if selected_sem_file:
            # 이미지 로드
            sem_data = load_image_from_directory(selected_sem_file)

            if sem_data:
                image_cols = st.columns([2, 6, 2])
                with image_cols[1]:
                    st.image(sem_data["image"], caption="SEM 이미지")

                # 이미지 경로 저장
                sem_path = sem_data["path"]
                st.session_state["sem_image_path"] = sem_path
                st.session_state["sem_image_data"] = sem_data

                # 이미지가 변경되면 이전 분석 결과 초기화
                if "sem_image_hash" not in st.session_state or st.session_state["sem_image_hash"] != selected_sem_file:
                    st.session_state["sem_info"] = None
                    st.session_state["sem_report"] = None
                    st.session_state["sem_report_path"] = None
                    st.session_state["sem_image_hash"] = selected_sem_file
                    st.session_state["sem_metadata"] = None
                    st.session_state["sem_raw_response"] = None
                    # 종합 분석 결과도 초기화
                    st.session_state["combined_report"] = None
                    st.session_state["combined_report_path"] = None
                    # 각 탭 버튼 클릭 상태 초기화
                    st.session_state["sem_analysis_run"] = False
                    st.session_state["combined_analysis_run"] = False

    # 탭 2: 이미지 업로드
    with upload_tab:
        st.subheader("SEM 이미지 업로드")
        sem_file = st.file_uploader("SEM 이미지 업로드", type=['png', 'jpg', 'jpeg'], key="sem_file")
        if sem_file:
            # 이미지 처리
            sem_data = process_uploaded_image(sem_file)
            if sem_data:
                image_cols = st.columns([2, 6, 2])
                with image_cols[1]:
                    st.image(sem_data["image"], caption="SEM 이미지")
                sem_path = save_uploaded_file(sem_file, "images")
                st.session_state["sem_image_path"] = sem_path
                st.session_state["sem_image_data"] = sem_data
                # 이미지가 변경되면 이전 분석 결과 초기화
                if "sem_image_hash" not in st.session_state or st.session_state["sem_image_hash"] != sem_file.name:
                    st.session_state["sem_info"] = None
                    st.session_state["sem_report"] = None
                    st.session_state["sem_report_path"] = None
                    st.session_state["sem_image_hash"] = sem_file.name
                    st.session_state["sem_metadata"] = None
                    st.session_state["sem_raw_response"] = None
                    # 종합 분석 결과도 초기화
                    st.session_state["combined_report"] = None
                    st.session_state["combined_report_path"] = None
                    # 각 탭 버튼 클릭 상태 초기화
                    st.session_state["sem_analysis_run"] = False
                    st.session_state["combined_analysis_run"] = False

    has_sem_image = st.session_state.get("sem_image_data") is not None
    if has_sem_image:
        try:
            # SEM 이미지 분석
            st.subheader("🤖 SEM 이미지 분석")

            # 이미 완료된 분석 결과가 있는지 확인
            if st.session_state["sem_report"] is not None:
                _display_completed_analysis_report(
                    report=st.session_state["sem_report"],
                    report_path=st.session_state["sem_report_path"],
                    image_links=[st.session_state["sem_image_path"]],
                    metadata=st.session_state.get("sem_metadata"),
                    raw_response=st.session_state.get("sem_raw_response"),
                    analysis_type="SEM"
                )
            else:
                # SEM 이미지 정보 추출
                if st.session_state["sem_info"] is None and st.session_state["sem_image_data"] is not None:
                    with st.spinner("SEM 이미지 분석 중..."):
                        st.session_state["sem_info"] = extract_image_info(st.session_state["sem_image_data"], "SEM")

                if st.session_state["sem_info"]:
                    # SEM 분석 버튼 및 리포트 생성
                    sem_analysis_run = st.button("SEM 분석 시작", key="sem_analysis_button")
                    # 버튼 클릭 상태 저장
                    if sem_analysis_run:
                        st.session_state["sem_analysis_run"] = True
                    # 버튼 클릭 시 실행
                    if st.session_state["sem_analysis_run"] and st.session_state["sem_report"] is None:
                        with st.spinner("SEM 분석 리포트 생성 중..."):
                            result = generate_analysis_report(
                                analysis_type="SEM",
                                analysis_info=st.session_state["sem_info"],
                                sem_image_path=st.session_state.get("sem_image_path")
                            )
                            if result is not None:
                                report_content, report_path = result
                                # 분석 결과 캐싱 (반환된 final_markdown_content 사용)
                                st.session_state["sem_report"] = report_content
                                st.session_state["sem_report_path"] = report_path

                                # 성공 메시지 후 새로고침 - 중요: 페이지 다시 로드하여 결과와 평가 UI 표시
                                st.success("SEM 분석 리포트가 생성되었습니다. 페이지를 새로고침합니다...")
                                st.rerun()
                            else:
                                st.error("SEM 분석 리포트 생성에 실패했습니다.")
                else:
                    st.error("SEM 이미지 분석에 실패했습니다. 다시 시도해주세요.")

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("SEM 이미지를 선택하거나 업로드하여 분석을 시작하세요.")

def show_eds_analysis():
    """EDS 스펙트럼 분석 기능"""
    # 세션 상태 초기화 - 모든 함수에서 동일한 키 프리픽스 사용
    init_session_state(key_prefix="sem_eds")

    # 이미지 데이터 및 분석 결과 관련 세션 상태 초기화
    if "eds_image_data" not in st.session_state:
        st.session_state["eds_image_data"] = None
    if "eds_info" not in st.session_state:
        st.session_state["eds_info"] = None
    if "eds_report" not in st.session_state:
        st.session_state["eds_report"] = None
    if "eds_report_path" not in st.session_state:
        st.session_state["eds_report_path"] = None
    if "eds_metadata" not in st.session_state:
        st.session_state["eds_metadata"] = None
    if "eds_raw_response" not in st.session_state:
        st.session_state["eds_raw_response"] = None

    # 사이드바에서 설정된 모델과 온도 가져오기
    selected_model = st.session_state.get("selected_model", "llama2")
    temperature = st.session_state.get("temperature", 0.7)

    st.header("EDS 스펙트럼 분석")

    # 폴더 구조 생성
    base_dir = create_sem_eds_folders()

    # 탭 인터페이스 생성
    select_tab, upload_tab = st.tabs(["디렉토리에서 선택", "이미지 업로드"])

    # 탭 1: 디렉토리에서 이미지 선택
    with select_tab:
        st.subheader("EDS 스펙트럼 이미지 선택")

        # 이미지 목록 새로고침 버튼
        col1, col2 = st.columns([1, 9])
        with col1:
            refresh_button = st.button("🔄", key="eds_refresh")
        with col2:
            st.text("이미지 목록 새로고침")

        # 이미지 파일 목록 가져오기
        eds_image_files = get_image_files_in_directory(folder="images")

        if not eds_image_files:
            st.warning("이미지 폴더(SEM_EDS/images)에 이미지 파일이 없습니다. 이미지 파일을 추가한 후 새로고침 버튼을 눌러주세요.")

        # 이미지 선택 박스
        selected_eds_file = st.selectbox(
            "분석할 EDS 스펙트럼 이미지 선택",
            options=[""] + eds_image_files,
            index=0,
            key="eds_file_select"
        )

        if selected_eds_file:
            # 이미지 로드
            eds_data = load_image_from_directory(selected_eds_file)

            if eds_data:
                image_cols = st.columns([2, 6, 2])
                with image_cols[1]:
                    st.image(eds_data["image"], caption="EDS 스펙트럼")

                # 이미지 경로 저장
                eds_path = eds_data["path"]
                st.session_state["eds_image_path"] = eds_path
                st.session_state["eds_image_data"] = eds_data

                # 이미지가 변경되면 이전 분석 결과 초기화
                if "eds_image_hash" not in st.session_state or st.session_state["eds_image_hash"] != selected_eds_file:
                    st.session_state["eds_info"] = None
                    st.session_state["eds_report"] = None
                    st.session_state["eds_report_path"] = None
                    st.session_state["eds_image_hash"] = selected_eds_file
                    st.session_state["eds_metadata"] = None
                    st.session_state["eds_raw_response"] = None
                    # 종합 분석 결과도 초기화
                    st.session_state["combined_report"] = None
                    st.session_state["combined_report_path"] = None
                    # 각 탭 버튼 클릭 상태 초기화
                    st.session_state["eds_analysis_run"] = False
                    st.session_state["combined_analysis_run"] = False

    # 탭 2: 이미지 업로드
    with upload_tab:
        st.subheader("EDS 스펙트럼 이미지 업로드")
        eds_file = st.file_uploader("EDS 스펙트럼 이미지 업로드", type=['png', 'jpg', 'jpeg'], key="eds_file")
        if eds_file:
            # 이미지 처리
            eds_data = process_uploaded_image(eds_file)
            if eds_data:
                image_cols = st.columns([2, 6, 2])
                with image_cols[1]:
                    st.image(eds_data["image"], caption="EDS 스펙트럼")
                eds_path = save_uploaded_file(eds_file, "images")
                st.session_state["eds_image_path"] = eds_path
                st.session_state["eds_image_data"] = eds_data
                # 이미지가 변경되면 이전 분석 결과 초기화
                if "eds_image_hash" not in st.session_state or st.session_state["eds_image_hash"] != eds_file.name:
                    st.session_state["eds_info"] = None
                    st.session_state["eds_report"] = None
                    st.session_state["eds_report_path"] = None
                    st.session_state["eds_image_hash"] = eds_file.name
                    st.session_state["eds_metadata"] = None
                    st.session_state["eds_raw_response"] = None
                    # 종합 분석 결과도 초기화
                    st.session_state["combined_report"] = None
                    st.session_state["combined_report_path"] = None
                    # 각 탭 버튼 클릭 상태 초기화
                    st.session_state["eds_analysis_run"] = False
                    st.session_state["combined_analysis_run"] = False

    has_eds_image = st.session_state.get("eds_image_data") is not None
    if has_eds_image:
        try:
            # EDS 스펙트럼 분석
            st.subheader("🤖 EDS 스펙트럼 분석")

            # 이미 완료된 분석 결과가 있는지 확인
            if st.session_state["eds_report"] is not None:
                _display_completed_analysis_report(
                    report=st.session_state["eds_report"],
                    report_path=st.session_state["eds_report_path"],
                    image_links=[st.session_state["eds_image_path"]],
                    metadata=st.session_state.get("eds_metadata"),
                    raw_response=st.session_state.get("eds_raw_response"),
                    analysis_type="EDS"
                )
            else:
                # EDS 이미지 정보 추출
                if st.session_state["eds_info"] is None and st.session_state["eds_image_data"] is not None:
                    with st.spinner("EDS 스펙트럼 분석 중..."):
                        st.session_state["eds_info"] = extract_image_info(st.session_state["eds_image_data"], "EDS")

                if st.session_state["eds_info"]:
                    # EDS 분석 버튼 및 리포트 생성
                    eds_analysis_run = st.button("EDS 분석 시작", key="eds_analysis_button")
                    # 버튼 클릭 상태 저장
                    if eds_analysis_run:
                        st.session_state["eds_analysis_run"] = True
                    # 버튼 클릭 시 실행
                    if st.session_state["eds_analysis_run"] and st.session_state["eds_report"] is None:
                        with st.spinner("EDS 분석 리포트 생성 중..."):
                            result = generate_analysis_report(
                                analysis_type="EDS",
                                analysis_info=st.session_state["eds_info"],
                                eds_image_path=st.session_state.get("eds_image_path")
                            )
                            if result is not None:
                                report_content, report_path = result
                                # 분석 결과 캐싱 (반환된 final_markdown_content 사용)
                                st.session_state["eds_report"] = report_content
                                st.session_state["eds_report_path"] = report_path

                                # 성공 메시지 후 새로고침 - 중요: 페이지 다시 로드하여 결과와 평가 UI 표시
                                st.success("EDS 분석 리포트가 생성되었습니다. 페이지를 새로고침합니다...")
                                st.rerun()
                            else:
                                st.error("EDS 분석 리포트 생성에 실패했습니다.")
                else:
                    st.error("EDS 스펙트럼 분석에 실패했습니다. 다시 시도해주세요.")

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("EDS 스펙트럼 이미지를 선택하거나 업로드하여 분석을 시작하세요.")

def show_operation_inference():
    """SEM-EDS 분석 내용을 바탕으로 설비의 작동 물리 조건을 추론하는 기능"""
    # 세션 상태 초기화 - 모든 함수에서 동일한 키 프리픽스 사용
    init_session_state(key_prefix="sem_eds")

    # 공정 조건 분석 결과 캐싱 관련 세션 상태 초기화
    if "operation_inference_report" not in st.session_state:
        st.session_state["operation_inference_report"] = None
    if "operation_inference_report_path" not in st.session_state:
        st.session_state["operation_inference_report_path"] = None
    if "operation_inference_run" not in st.session_state:
        st.session_state["operation_inference_run"] = False

    st.header("공정 조건 분석")

    # SEM 및 EDS 데이터가 존재하는지 확인
    has_sem_data = "sem_image_data" in st.session_state and st.session_state["sem_image_data"] is not None
    has_eds_data = "eds_image_data" in st.session_state and st.session_state["eds_image_data"] is not None

    if not has_sem_data:
        st.warning("먼저 'SEM 분석' 탭에서 SEM 이미지를 업로드하고 분석해주세요.")

    if not has_eds_data:
        st.warning("먼저 'EDS 분석' 탭에서 EDS 스펙트럼 이미지를 업로드하고 분석해주세요.")

    if has_sem_data and has_eds_data:
        # 이미지 표시
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("SEM 이미지")
            st.image(st.session_state["sem_image_data"]["image"], caption="SEM 이미지")

            # SEM 분석의 디버그 정보와 AI 모델 원본 응답 표시
            if st.session_state.get("sem_metadata") is not None:
                with st.expander("SEM 디버그 정보", expanded=False):
                    st.write("입력 메타데이터:")
                    st.json(st.session_state["sem_metadata"])

            if st.session_state.get("sem_raw_response") is not None:
                with st.expander("SEM AI 모델 원본 응답", expanded=False):
                    st.code(st.session_state["sem_raw_response"])

        with col2:
            st.subheader("EDS 스펙트럼")
            st.image(st.session_state["eds_image_data"]["image"], caption="EDS 스펙트럼")

            # EDS 분석의 디버그 정보와 AI 모델 원본 응답 표시
            if st.session_state.get("eds_metadata") is not None:
                with st.expander("EDS 디버그 정보", expanded=False):
                    st.write("입력 메타데이터:")
                    st.json(st.session_state["eds_metadata"])

            if st.session_state.get("eds_raw_response") is not None:
                with st.expander("EDS AI 모델 원본 응답", expanded=False):
                    st.code(st.session_state["eds_raw_response"])

        # SEM 및 EDS 분석 정보 확인
        has_sem_info = "sem_info" in st.session_state and st.session_state["sem_info"] is not None
        has_eds_info = "eds_info" in st.session_state and st.session_state["eds_info"] is not None

        if not has_sem_info:
            st.warning("'SEM 분석' 탭에서 SEM 이미지 분석을 완료해주세요.")

        if not has_eds_info:
            st.warning("'EDS 분석' 탭에서 EDS 스펙트럼 분석을 완료해주세요.")

        if has_sem_info and has_eds_info:
            # 분석 정보 표시
            st.subheader("⚡ 공정 조건 분석")

            # 이미 완료된 공정 조건 분석 결과가 있는지 확인
            if st.session_state["operation_inference_report"] is not None:
                _display_completed_analysis_report(
                    report=st.session_state["operation_inference_report"],
                    report_path=st.session_state["operation_inference_report_path"],
                    image_links=[st.session_state["sem_image_path"], st.session_state["eds_image_path"]],
                    metadata=None,
                    raw_response=None,
                    analysis_type="OPERATION"
                )
            else:
                # 공정 조건 분석 정보
                combined_info = {
                    "SEM_분석_결과": st.session_state["sem_info"],
                    "EDS_분석_결과": st.session_state["eds_info"],
                    # "메타데이터": {
                    #     "분석_시간": datetime.now().isoformat(),
                    #     "사용_모델": st.session_state.get("selected_model", "gemma3:4b"),
                    #     "온도": st.session_state.get("temperature", 0.2)
                    # }
                }

                # 공정 조건 분석 버튼 및 리포트 생성
                combined_analysis_run = st.button("공정 조건 분석 시작", key="operation_inference_button")
                # 버튼 클릭 상태 저장
                if combined_analysis_run:
                    st.session_state["operation_inference_run"] = True
                # 버튼 클릭 시 실행
                if st.session_state["operation_inference_run"] and st.session_state["operation_inference_report"] is None:
                    with st.spinner("공정 조건 분석 리포트 생성 중..."):
                        result = generate_analysis_report(
                            analysis_type="OPERATION",
                            analysis_info=combined_info,
                            sem_image_path=st.session_state.get("sem_image_path"),
                            eds_image_path=st.session_state.get("eds_image_path")
                        )
                        if result is not None:
                            report_content, report_path = result
                            # 결과 캐싱 (반환된 final_markdown_content 사용)
                            st.session_state["operation_inference_report"] = report_content
                            st.session_state["operation_inference_report_path"] = report_path

                            # 성공 메시지 후 새로고침 - 중요: 페이지 다시 로드하여 결과와 평가 UI 표시
                            st.success("공정 조건 분석 리포트가 생성되었습니다. 페이지를 새로고침합니다...")
                            st.rerun()
                        else:
                            st.error("공정 조건 분석 리포트 생성에 실패했습니다.")
    else:
        st.info("SEM 이미지와 EDS 스펙트럼 이미지를 모두 선택하거나 업로드하고 분석한 후에 공정 조건 분석을 시작하세요.")

def show_equipment_inference():
    """SEM-EDS 분석 내용 및 공정 조건 분석 내용을 바탕으로 이물질 발생 설비/부품을 추정하는 기능"""
    # 세션 상태 초기화 - 모든 함수에서 동일한 키 프리픽스 사용
    init_session_state(key_prefix="sem_eds")

    # 설비/부품 추론 결과 캐싱 관련 세션 상태 초기화
    if "equipment_inference_report" not in st.session_state:
        st.session_state["equipment_inference_report"] = None
    if "equipment_inference_report_path" not in st.session_state:
        st.session_state["equipment_inference_report_path"] = None

    st.header("설비/부품 추정")

    # SEM 및 EDS 데이터가 존재하는지 확인
    has_sem_data = "sem_image_data" in st.session_state and st.session_state["sem_image_data"] is not None
    has_eds_data = "eds_image_data" in st.session_state and st.session_state["eds_image_data"] is not None

    if not has_sem_data:
        st.warning("먼저 'SEM 분석' 탭에서 SEM 이미지를 업로드하고 분석해주세요.")

    if not has_eds_data:
        st.warning("먼저 'EDS 분석' 탭에서 EDS 스펙트럼 이미지를 업로드하고 분석해주세요.")

    if has_sem_data and has_eds_data:
        # 이미지 표시
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("SEM 이미지")
            st.image(st.session_state["sem_image_data"]["image"], caption="SEM 이미지")

            # SEM 분석의 디버그 정보와 AI 모델 원본 응답 표시
            if st.session_state.get("sem_metadata") is not None:
                with st.expander("SEM 디버그 정보", expanded=False):
                    st.write("입력 메타데이터:")
                    st.json(st.session_state["sem_metadata"])

            if st.session_state.get("sem_raw_response") is not None:
                with st.expander("SEM AI 모델 원본 응답", expanded=False):
                    st.code(st.session_state["sem_raw_response"])

        with col2:
            st.subheader("EDS 스펙트럼")
            st.image(st.session_state["eds_image_data"]["image"], caption="EDS 스펙트럼")

            # EDS 분석의 디버그 정보와 AI 모델 원본 응답 표시
            if st.session_state.get("eds_metadata") is not None:
                with st.expander("EDS 디버그 정보", expanded=False):
                    st.write("입력 메타데이터:")
                    st.json(st.session_state["eds_metadata"])

            if st.session_state.get("eds_raw_response") is not None:
                with st.expander("EDS AI 모델 원본 응답", expanded=False):
                    st.code(st.session_state["eds_raw_response"])

        # SEM 및 EDS 분석 정보 확인
        has_sem_info = "sem_info" in st.session_state and st.session_state["sem_info"] is not None
        has_eds_info = "eds_info" in st.session_state and st.session_state["eds_info"] is not None

        if not has_sem_info:
            st.warning("'SEM 분석' 탭에서 SEM 이미지 분석을 완료해주세요.")

        if not has_eds_info:
            st.warning("'EDS 분석' 탭에서 EDS 스펙트럼 분석을 완료해주세요.")

        if has_sem_info and has_eds_info:
            # 분석 정보 표시
            st.subheader("🔍 설비/부품 추정")
            st.info("설비/부품 추정 기능은 개발 중입니다.", icon="ℹ️")
    else:
        st.info("SEM 이미지와 EDS 스펙트럼 이미지를 모두 선택하거나 업로드하고 분석한 후에 설비/부품 추정을 시작하세요.")

def _display_completed_analysis_report(report, report_path, image_links, metadata, raw_response, analysis_type):
    """완료된 분석 보고서 표시 (내부 헬퍼 함수)

    Args:
        report (str): 마크다운 형식의 보고서 내용
        report_path (str): 저장된 보고서 파일 경로
        image_links (list, optional): 이미지 링크 목록
        metadata (dict, optional): 이미지 메타데이터
        raw_response (str, optional): AI 모델 원본 응답
        analysis_type (str): 분석 유형 ("SEM", "EDS", "COMBINED")
    """
    # 분석 유형 단어 변환
    if analysis_type == "OPERATION":
        analysis_type_word = "공정 조건"
    elif analysis_type == "EQUIPMENT":
        analysis_type_word = "설비/부품 추정"
    else:
        analysis_type_word = analysis_type

    st.markdown(f"## 📄 {analysis_type_word} 분석 보고서")
    if image_links:
        image_cols = st.columns(2)
        for col, path in zip(image_cols, image_links):
            with col:
                st.image(os.path.abspath(path))
    st.markdown(report)
    st.success(f"{analysis_type_word} 분석 리포트가 저장되었습니다: {report_path}")

    # 분석 후에도 디버그 정보와 원본 응답 표시
    if metadata is not None:
        with st.expander("디버그 정보", expanded=False):
            st.write("입력 메타데이터:")
            st.json(metadata)

    if raw_response is not None:
        with st.expander("AI 모델 원본 응답", expanded=False):
            st.code(raw_response)

    if analysis_type == "EDS":
        with st.expander("스테인리스 강종 표준 조성 비율", expanded=False):
            from components.sem_eds.classification import get_stainless_standard_composition_df
            df = get_stainless_standard_composition_df()
            st.dataframe(df)

    # 보고서 평가 UI 추가 - 더 눈에 띄게 변경
    st.markdown("---")
    st.markdown("## 📊 보고서 품질 평가")
    st.info(f"{analysis_type_word} 분석 보고서의 품질을 평가하려면 아래 버튼을 클릭하세요.")

    if st.button(f"{analysis_type_word} 분석 보고서 평가하기", key=f"eval_{analysis_type.lower()}_btn", type="primary"):
        _display_report_evaluation(report, analysis_type)

def _display_report_evaluation(report, analysis_type):
    """보고서 평가 결과 표시 (내부 헬퍼 함수)

    Args:
        report (str): 마크다운 형식의 보고서 내용
        analysis_type (str): 분석 유형 ("SEM", "EDS", "COMBINED")
    """
    with st.spinner("보고서 평가 중..."):
        evaluation = evaluate_report_quality(report, analysis_type)

        # 평가 결과 표시
        st.markdown("#### 평가 결과")

        # 종합 점수
        st.metric("종합 점수", f"{evaluation['overall_score']} / 100")

        # 세부 평가 결과
        cols = st.columns(5)

        # 구조 완전성
        with cols[0]:
            st.markdown("**구조 완전성**")
            structure_ok = sum(evaluation['structure'].values())
            structure_total = len(evaluation['structure'])
            st.markdown(f"{structure_ok} / {structure_total} 섹션")
            # 구조 점수 표시 (20점 만점)
            structure_score = (structure_ok / structure_total) * 20
            st.markdown(f"**점수**: {round(structure_score)}/20")

        # 형식 준수 (볼드체)
        with cols[1]:
            st.markdown("**형식 (볼드체)**")
            st.markdown(f"{evaluation['format']['bold_count']} 회 사용")
            # 볼드체 점수 표시 (10점 만점)
            bold_score = min(evaluation['format']['bold_count'] * 2, 10)
            st.markdown(f"**점수**: {bold_score}/10")

        # 전문성
        with cols[2]:
            st.markdown("**전문성**")
            if 'expertise' in evaluation and 'score' in evaluation['expertise']:
                st.markdown(f"**점수**: {evaluation['expertise']['score']}/20")
                if evaluation['expertise']['feedback']:
                    st.info(evaluation['expertise']['feedback'])

        # 명확성
        with cols[3]:
            st.markdown("**명확성**")
            if 'clarity' in evaluation and 'score' in evaluation['clarity']:
                st.markdown(f"**점수**: {evaluation['clarity']['score']}/20")
                if evaluation['clarity']['feedback']:
                    st.info(evaluation['clarity']['feedback'])

        # 분석 근거
        with cols[4]:
            st.markdown("**분석 근거**")
            if 'evidence' in evaluation and 'score' in evaluation['evidence']:
                st.markdown(f"**점수**: {evaluation['evidence']['score']}/30")
                if evaluation['evidence']['feedback']:
                    st.info(evaluation['evidence']['feedback'])

        # 개선 필요 사항
        if evaluation['warnings']:
            with st.expander("⚠️ 개선 필요 사항", expanded=True):
                for warning in evaluation['warnings']:
                    st.warning(warning)
        else:
            st.success("모든 평가 기준을 충족했습니다! 👍")

        # 섹션 검출 상세 결과 - 개선된 UI
        with st.expander("📑 섹션 검출 상세 결과", expanded=False):
            st.markdown("#### 보고서 섹션 인식 결과")
            st.markdown("각 섹션의 인식 여부와 매치된 헤더 텍스트를 확인합니다.")

            for section, exists in evaluation['structure'].items():
                if exists:
                    # 매치된 패턴 정보 표시
                    match_key = f'match_{section}'
                    matched_text = evaluation['debug_info'].get(match_key, "매치 정보 없음")

                    st.success(f"✓ **{section}** 섹션 인식됨")
                    st.markdown(f"   매치된 헤더: `{matched_text}`")
                else:
                    st.error(f"✗ **{section}** 섹션 인식 실패")

            st.markdown("---")
            st.markdown("##### 문서에서 발견된 모든 헤더:")
            if 'all_headers' in evaluation['debug_info'] and evaluation['debug_info']['all_headers']:
                for i, header in enumerate(evaluation['debug_info']['all_headers']):
                    st.markdown(f"{i+1}. `{header}`")
            else:
                st.info("문서에서 헤더 형식(#으로 시작하는)의 텍스트를 찾을 수 없습니다.")

