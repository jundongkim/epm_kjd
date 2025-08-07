import streamlit as st
import os
import glob
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)
import json

def show_visualization_gallery(plot_dir: str, model_type: str):
    """시각화 갤러리 탭 표시 (카테고리 구분)"""
    # 세션 상태 초기화
    init_session_state(key_prefix="visualization_gallery")

    # 선택된 데이터셋 확인
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값

    st.header(f"{model_type} 모델 및 데이터 시각화 갤러리 (데이터셋: {selected_dataset})")

    # 데이터 생성 시각화 경로 정의 - 데이터셋별 디렉토리로 변경
    data_vis_dir = f"FWHM/visualization_{selected_dataset}"
    
    # 데이터셋별 디렉토리가 없는 경우 기본 디렉토리 사용
    if not os.path.exists(data_vis_dir):
        data_vis_dir = "FWHM/visualization"
        st.info(f"데이터셋별 시각화 디렉토리({data_vis_dir})가 없어 기본 디렉토리를 사용합니다.")

    # 파일 경로를 저장할 딕셔너리 (카테고리별 분리)
    model_vis_files = {}
    data_vis_files = {}

    # 1. 모델 결과 시각화 파일 검색
    if os.path.exists(plot_dir):
        model_html_files = glob.glob(os.path.join(plot_dir, "*.html"))
        for f_path in model_html_files:
            model_vis_files[os.path.basename(f_path)] = f_path
    else:
        st.warning(f"{model_type} 모델 시각화 파일 폴더({plot_dir})가 없습니다.")

    # 2. 데이터 생성 시각화 파일 검색
    if os.path.exists(data_vis_dir):
        data_html_files = glob.glob(os.path.join(data_vis_dir, "*.html"))
        for f_path in data_html_files:
            data_vis_files[os.path.basename(f_path)] = f_path
    else:
        st.warning(f"데이터 생성 시각화 파일 폴더({data_vis_dir})가 없습니다.")

    # 카테고리 선택 UI
    selected_category = st.radio(
        "시각화 카테고리 선택",
        ("모델 시각화", "데이터 시각화"),
        horizontal=True
    )

    # 선택된 카테고리에 따라 파일 목록 필터링
    files_to_show = {}
    file_origin_label = ""
    if selected_category == "모델 시각화":
        files_to_show = model_vis_files
        file_origin_label = "모델 결과 분석"
        if not files_to_show:
            st.info(f"{model_type} 모델 관련 시각화 파일이 없습니다. ({plot_dir})")
            return
    elif selected_category == "데이터 시각화":
        files_to_show = data_vis_files
        file_origin_label = "데이터 생성 분석"
        if not files_to_show:
            st.info(f"데이터 생성 관련 시각화 파일이 없습니다. ({data_vis_dir})")
            return

    # 파일 이름 정렬
    file_names = sorted(list(files_to_show.keys()))

    # 파일 선택
    selected_file = st.selectbox(
        f"{selected_category} 파일 선택",
        file_names
    )

    # 선택된 파일 표시
    if selected_file:
        selected_path = files_to_show[selected_file]
        
        st.subheader(f"시각화: {selected_file} ({file_origin_label})")

        try:
            with open(selected_path, 'r', encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=800)
        except Exception as e:
            st.error(f"파일 로드 오류: {selected_path} - {e}")
            return

        # AI 분석 요약
        st.subheader("🤖 iDSB AI 시각화 분석 요약")

        # 분석 정보 수집
        analysis_info = {
            "모델_유형": model_type, # 현재 선택된 모델 (참고용)
            "파일_출처": file_origin_label,
            "선택된_파일": selected_file,
            "파일_경로": selected_path
        }

        # 프롬프트 생성
        prompt = f"""
        아래 시각화 정보를 바탕으로 전문적인 분석 리포트를 작성해주세요.

        ## 시각화 정보
        - 분석 대상: {file_origin_label}
        {json.dumps(analysis_info, indent=2, ensure_ascii=False)}

        ## 시각화 컨텍스트
        - {selected_file} 파일은 '{file_origin_label}' 과정에서 생성된 시각화 자료입니다.

        다음 구조로 분석 리포트를 작성해주세요:

        1. 시각화 개요 (시각화의 목적과 보여주는 데이터/결과 유형)
        2. 주요 패턴 분석 (시각화에서 관찰되는 주요 패턴과 트렌드)
        3. 데이터/결과 인사이트 (시각화에서 도출할 수 있는 주요 인사이트)
        4. 활용 방안 (이 시각화를 통해 얻은 정보를 어떻게 활용할 수 있는지)
        5. 추가 분석 제안 (추가로 살펴볼 만한 관점이나 시각화 방법)

        각 섹션은 ### 헤더로 구분하고, 중요한 수치나 인사이트는 **볼드체**로 강조해주세요.
        """

        try:
            # 분석 UI 표시 및 처리
            is_running = display_analysis_ui(
                prompt=prompt,
                button_label="시각화 분석 시작",
                key_prefix="visualization_gallery",
                info_message="AI 시각화 분석을 실행하려면 '시각화 분석 시작' 버튼을 클릭하세요."
            )

            # 분석 실행 중인 경우
            if is_running:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    metadata_placeholder = st.empty()

                    with st.spinner("AI가 시각화를 분석하고 있습니다..."):
                        # AI 분석 실행
                        generate_ai_analysis(
                            prompt=prompt,
                            key_prefix="visualization_gallery",
                            message_placeholder=message_placeholder,
                            metadata_placeholder=metadata_placeholder
                        )

        except Exception as e:
            st.error(f"AI 시각화 분석 생성 중 오류가 발생했습니다: {str(e)}")