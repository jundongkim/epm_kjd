import streamlit as st
import os
import glob
import json
ICP_DIR = "ICP"
VIS_DIR = os.path.join(ICP_DIR, "icp_visualization")
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)

def show_icp_qcp_visualization_gallery():
    """ICP QCP 데이터 시각화 갤러리 탭 표시"""
    init_session_state(key_prefix="icp_qcp_visualization_gallery")

    st.header("ICP QCP 시각화 갤러리")
    st.markdown("--- ")

    st.subheader("시각화 결과 갤러리")
    st.write(f"생성된 시각화 파일 (`{VIS_DIR}` 폴더):")

    if not os.path.exists(VIS_DIR):
        st.warning(f"`{VIS_DIR}` 폴더를 찾을 수 없습니다. 데이터 생성 및 시각화 프로세스가 올바르게 완료되었는지 확인하세요.")
        return

    # 시각화 HTML 파일 목록 가져오기
    vis_html_files = glob.glob(os.path.join(VIS_DIR, "*.html"))

    if not vis_html_files:
        st.info(f"표시할 시각화 파일(*.html)이 없습니다. (`{VIS_DIR}` 폴더 확인)")
        return

    # 파일 이름만 추출하여 정렬 (선택적)
    vis_filenames = sorted([os.path.basename(f) for f in vis_html_files])

    # 시각화 유형별 분류
    vis_categories = {
        "상관관계": [f for f in vis_filenames if "correlation" in f],
        "박스플롯": [f for f in vis_filenames if "boxplot" in f],
        "PCA 분석": [f for f in vis_filenames if "pca" in f],
        "그룹 비교": [f for f in vis_filenames if "comparison" in f],
        "기타": [f for f in vis_filenames if not any(x in f for x in ["correlation", "boxplot", "pca", "comparison"])]
    }
    
    # 메인 페이지 상단에 설정 섹션 추가
    st.markdown("## 시각화 설정")
    
    # 설정을 위한 열 생성
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 카테고리 선택
        selected_category = st.radio(
            "시각화 카테고리:",
            options=list(vis_categories.keys()),
            key="select_vis_category_qcp",
            horizontal=True
        )
    
    # 해당 카테고리의 파일 목록
    category_files = vis_categories[selected_category]
    
    if not category_files:
        st.info(f"'{selected_category}' 카테고리에 표시할 시각화 파일이 없습니다.")
        return
    
    # 시각화 표시
    st.markdown("---")
    st.subheader(f"{selected_category} 시각화")
    
    # 파일 선택과 시각화 높이 조절을 위한 열 생성
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 파일 선택 드롭다운
        selected_vis_filename = st.selectbox(
            "시각화 선택:",
            category_files,
            key="select_vis_html_qcp_gallery"
        )
    
    # 카테고리별 추천 높이 설정
    recommended_heights = {
        "상관관계": 700,
        "박스플롯": 600,
        "PCA 분석": 800,
        "그룹 비교": 700,
        "기타": 600
    }
    
    # 파일 유형별 추천 높이 미세 조정
    file_type_heights = {
        "correlation_heatmap": 750,
        "correlations_bar": 750,
        "pca_scatter_3d": 850,
        "pca_scatter_2d": 700,
        "boxplot": 550,
        "group_comparison": 700
    }
    
    # 기본 높이 설정 (카테고리 기반)
    default_height = recommended_heights.get(selected_category, 600)
    
    # 파일 이름 기반으로 높이 미세 조정
    for file_type, height in file_type_heights.items():
        if file_type in selected_vis_filename:
            default_height = height
            break
    
    with col2:
        # 높이 조절 슬라이더
        vis_height = st.slider(
            "시각화 높이:",
            min_value=400,
            max_value=1200,
            value=default_height,
            step=50,
            key=f"vis_height_{selected_category}"
        )

    # 선택된 파일 표시 및 AI 분석
    if selected_vis_filename:
        vis_path = os.path.join(VIS_DIR, selected_vis_filename)
        try:
            # HTML 파일 내용 읽기
            with open(vis_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 컨테이너로 감싸기
            vis_container = st.container()
            with vis_container:
                st.caption(f"파일: {selected_vis_filename} (높이: {vis_height}px)")
                # Streamlit 컴포넌트로 HTML 렌더링
                st.components.v1.html(html_content, height=vis_height, scrolling=True)

            st.markdown("--- ")
            st.subheader("🤖 iDSB AI 시각화 분석 요약")

            # 분석 정보 수집 (파일 유형 명시적으로 html)
            analysis_info = {
                "선택된_파일": selected_vis_filename,
                "파일_경로": vis_path,
                "시각화_유형": "Plotly HTML Chart",
                "카테고리": selected_category
            }
            
            # AI 분석 프롬프트 생성
            prompt = f"""
            다음 QCP 데이터 시각화 파일을 분석해주세요:
            
            파일명: {selected_vis_filename}
            카테고리: {selected_category}
            
            이 시각화를 면밀히 분석하고 다음 구조로 마크다운 형식의 분석 리포트를 작성해주세요:
            
            ### 1. 시각화 개요
            - 이 시각화는 어떤 데이터를 보여주고 있으며, 어떤 유형의 차트인가요?
            - 이 시각화의 주요 목적은 무엇인가요?
            
            ### 2. 주요 관찰 사항
            - 데이터에서 어떤 주요 패턴, 이상점, 또는 관계가 보이나요?
            - 특별히 주목할 만한 인사이트가 있나요?
            
            ### 3. 품질 관리 관점의 해석
            - 이 시각화 결과가 생산 공정의 품질 관리에 어떤 의미를 가지나요?
            - 어떤 품질 향상 또는 결함 예방 조치를 제안할 수 있나요?
            
            ### 4. 후속 분석 제안
            - 이 데이터를 바탕으로 어떤 추가 분석이 유용할까요?
            - 더 깊은 인사이트를 얻기 위해 어떤 접근 방식을 취할 수 있을까요?
            
            리포트는 명확하고 간결하게 작성하고, 중요한 발견이나 인사이트는 **볼드체**로 강조해주세요.
            """
            
            # AI 분석 UI 표시
            try:
                is_running = display_analysis_ui(
                    prompt=prompt,
                    button_label="AI 시각화 분석 실행",
                    key_prefix="icp_qcp_visualization_gallery",
                    info_message="AI 분석을 실행하려면 버튼을 클릭하세요."
                )
                
                if is_running:
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        metadata_placeholder = st.empty()
                        with st.spinner("AI가 시각화를 분석하고 있습니다..."):
                            generate_ai_analysis(
                                prompt=prompt,
                                key_prefix="icp_qcp_visualization_gallery",
                                message_placeholder=message_placeholder,
                                metadata_placeholder=metadata_placeholder
                            )
            except Exception as e:
                st.error(f"AI 시각화 분석 생성 중 오류가 발생했습니다: {str(e)}")
                
        except Exception as e:
            st.error(f"HTML 파일 로드 오류: {e}")
            st.error(f"파일 경로: {vis_path}")

if __name__ == "__main__":
    show_icp_qcp_visualization_gallery() 