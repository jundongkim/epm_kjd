import streamlit as st
import os
import pandas as pd
from PIL import Image
import numpy as np
from components.cmms.cmms_data_loader import find_image_file

def get_all_image_paths(cmms_data):
    """모든 이미지 경로와 관련 정보를 가져옵니다."""
    all_images = []
    for entry in cmms_data:
        if "작업사진" in entry and entry["작업사진"]:
            image_descriptions = entry.get("이미지설명", {})
            for img_filename in entry["작업사진"]:
                image_path = find_image_file(img_filename)
                if image_path and os.path.exists(image_path):
                    all_images.append({
                        "path": image_path,
                        "filename": img_filename,
                        "description": image_descriptions.get(img_filename, ""),
                        "line": entry.get("라인", ""),
                        "equipment_no": entry.get("설비번호", "").split('\n')[0] if entry.get("설비번호") else "",
                        "work_date": entry.get("작업 일자", "").split('\n')[0] if entry.get("작업 일자") else "",
                        "work_details": entry.get("작업 상세내용", ""),
                        "equipment_name": entry.get("설비명", ""),
                        "work_type": entry.get("작업 종류", "")
                    })
    return all_images

@st.fragment
def show_cmms_images():
    """CMMS 작업 이미지 갤러리 컴포넌트"""
    st.title("📸 작업 이미지 갤러리")

    # 일일업무일지 데이터 확인
    if "cmms_data" not in st.session_state:
        st.error("일일업무일지 데이터가 로드되지 않았습니다.")
        return

    # 데이터 가져오기
    cmms_data = st.session_state.cmms_data

    # 모든 이미지 경로 가져오기
    all_images = get_all_image_paths(cmms_data)

    if not all_images:
        st.warning("작업 이미지가 없습니다.")
        return

    # 필터링 옵션 UI
    st.subheader("이미지 필터링 옵션")

    col1, col2 = st.columns(2)

    with col1:
        # 라인별 필터링
        filter_options = ["전체"]
        lines = sorted(list(set([img["line"] for img in all_images if img["line"]])))
        filter_options.extend(lines)
        selected_line = st.selectbox("라인별 필터링", filter_options)

    with col2:
        # 설비 유형별 필터링
        equipment_options = ["전체"]
        equipment_types = sorted(list(set([img["equipment_name"] for img in all_images if img["equipment_name"]])))
        equipment_options.extend(equipment_types)
        selected_equipment = st.selectbox("설비별 필터링", equipment_options)

    # 작업 종류별 필터링
    work_type_options = ["전체"]
    work_types = sorted(list(set([img["work_type"] for img in all_images if img["work_type"]])))
    work_type_options.extend(work_types)
    selected_work_type = st.selectbox("작업 종류별 필터링", work_type_options)

    # 이미지 검색 기능
    search_query = st.text_input("이미지 설명 또는 작업 내용 검색:", "")

    # 필터링된 이미지
    filtered_images = all_images

    # 라인별 필터링
    if selected_line != "전체":
        filtered_images = [img for img in filtered_images if img["line"] == selected_line]

    # 설비별 필터링
    if selected_equipment != "전체":
        filtered_images = [img for img in filtered_images if img["equipment_name"] == selected_equipment]

    # 작업 종류별 필터링
    if selected_work_type != "전체":
        filtered_images = [img for img in filtered_images if img["work_type"] == selected_work_type]

    # 검색어 필터링
    if search_query:
        search_query = search_query.lower()
        filtered_images = [
            img for img in filtered_images if
            search_query in img["description"].lower() or
            search_query in img["work_details"].lower()
        ]

    # 필터링 결과 표시
    st.markdown(f"### 검색 결과: {len(filtered_images)}개 이미지")

    if not filtered_images:
        st.warning("선택한 필터에 맞는 이미지가 없습니다.")
        return

    # 이미지 갤러리 표시
    st.subheader("이미지 갤러리")

    # 이미지 표시 방식 선택
    display_mode = st.radio(
        "표시 방식 선택:",
        ["그리드 뷰", "상세 뷰"],
        horizontal=True
    )

    if display_mode == "그리드 뷰":
        # 그리드 형식으로 이미지 표시
        columns = st.columns(3)

        for i, img in enumerate(filtered_images):
            with columns[i % 3]:
                st.image(img["path"],
                         caption=f"{img['equipment_no']} - {img['work_date']}",
                         use_container_width=True)
                st.markdown(f"**라인**: {img['line']}")
                st.markdown(f"**설비**: {img['equipment_name']}")

                # 이미지 상세보기 버튼
                if st.button(f"상세보기 #{i+1}", key=f"detail_btn_{i}"):
                    st.session_state.selected_image = img
                    # st.rerun()

        # 선택된 이미지 상세 보기 (팝업 효과)
        if hasattr(st.session_state, 'selected_image') and st.session_state.selected_image:
            img = st.session_state.selected_image

            with st.container():
                st.markdown("## 이미지 상세 정보")
                col1, col2 = st.columns([3, 2])

                with col1:
                    st.image(img["path"], use_container_width=True)

                with col2:
                    markdown_content = f"""### 기본 정보
    - **라인**: {img['line']}
    - **설비번호**: {img['equipment_no']}
    - **설비명**: {img['equipment_name']}
    - **작업일자**: {img['work_date']}
    - **작업종류**: {img['work_type']}

    ### 이미지 설명
    {img['description']}

    ### 작업 상세내용
    {img['work_details']}"""
                    st.markdown(markdown_content)

                    if st.button("닫기"):
                        st.session_state.selected_image = None
                        st.rerun(scope="fragment")

    else:
        # 상세 뷰 형식으로 이미지 표시
        for i, img in enumerate(filtered_images):
            with st.expander(f"{img['equipment_no']} - {img['work_date']} ({img['line']})", expanded=i==0):
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.image(img["path"], use_container_width=True, caption=img["filename"])

                with col2:
                    st.markdown("### 이미지 정보")
                    st.markdown(f"""
                    **라인**: {img['line']}
                    **설비번호**: {img['equipment_no']}
                    **설비명**: {img['equipment_name']}
                    **작업일자**: {img['work_date']}
                    **작업종류**: {img['work_type']}
                    """)

                    if img["description"]:
                        st.markdown("### 이미지 설명")
                        st.markdown(img["description"])

                st.markdown("### 작업 상세내용")
                st.markdown(img["work_details"])

                st.markdown("---")