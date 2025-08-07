"""
PRD(생산관리이력) 이미지 관련 기능을 제공하는 모듈
"""

import os
import streamlit as st
import pandas as pd
from PIL import Image
from components.prd.prd_data_loader import load_prd_data, find_image_file

def show_prd_images():
    """생산이슈리포트 보고서를 표시하는 기능"""
    st.title("생산이슈리포트 갤러리")

    # 데이터 로드
    prd_data = load_prd_data()

    if not prd_data:
        st.warning("생산이슈리포트 데이터를 불러올 수 없습니다.")
        return

    # # 이미지 정보 추출
    # all_files = []

    # for file_entry in prd_data:
    #     for page_entry in file_entry["pages"]:
    #         if "작업사진" in page_entry and page_entry["작업사진"]:
    #             # 기본 정보
    #             title = page_entry.get("title", "무제")
    #             content = page_entry.get("content", "내용 없음")
    #             summary = page_entry.get("summary", "요약 없음")
    #             date = file_entry.get("date", "날짜 정보 없음")
    #             line = file_entry.get("line", "대상 라인 정보 없음")
    #             equipment = file_entry.get("equipment", "대상 설비 정보 없음")
    #             issue = file_entry.get("issue", "발생 이슈 정보 없음")
    #             # line = file_entry.get("라인", "미분류")
    #             # product = file_entry.get("제품", "미분류")
    #             # work_date = file_entry.get("작업 일자", "날짜 없음")
    #             # issue = file_entry.get("이슈", "")

    #             # 이미지 설명 정보
    #             # image_descriptions = page_entry.get("이미지설명", {})

    #             # 각 이미지에 대한 정보 추가
    #             image_path = page_entry.get("image_path", None)
    #             if image_path and os.path.exists(image_path):
    #                 image_info = {
    #                     "filename": os.path.basename(image_path),
    #                     "path": image_path,
    #                     "title": title,
    #                     "content": content,
    #                     "summary": summary,
    #                     "date": date,
    #                     "line": line,
    #                     "equipment": equipment,
    #                     "issue": issue,
    #                     # "line": line,
    #                     # "product": product,
    #                     # "issue": issue,
    #                     # "work_date": work_date,
    #                     # "title": page_entry.get("제목", ""),
    #                     # "description": image_descriptions.get(img_filename, "")
    #                 }
    #                 all_images.append(image_info)

    # 이미지 필터링 옵션
    st.subheader("보고서 필터링")

    # # 라인 정보 추출
    # all_lines = sorted(list(set([img["line"] for img in all_images])))
    # all_products = sorted(list(set([img["product"] for img in all_images])))
    # all_issues = sorted(list(set([img["issue"] for img in all_images if img["issue"]])))
    # 메타데이터 추출
    all_lines = []
    all_equipments = []
    all_issues = []
    for file in prd_data:
        all_lines.extend(file.get("lines", ["대상 라인 정보 없음"]))
        all_equipments.extend(file.get("equipments", ["대상 설비 정보 없음"]))
        all_issues.extend(file.get("issues", ["발생 이슈 정보 없음"]))
    all_lines = sorted(list(set(all_lines)))
    all_equipments = sorted(list(set(all_equipments)))
    all_issues = sorted(list(set(all_issues)))

    # 필터링 UI
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_line = st.selectbox(
            "라인 선택",
            ["전체"] + all_lines
        )

    # with col2:
    #     selected_product = st.selectbox(
    #         "제품 선택",
    #         ["전체"] + all_products
    #     )
    with col2:
        selected_equipment = st.selectbox(
            "설비 선택",
            ["전체"] + all_equipments
        )

    with col3:
        selected_issue = st.selectbox(
            "이슈 선택",
            ["전체"] + all_issues
        )

    # 검색어 필터
    search_query = st.text_input("검색어 (보고서 파일명 또는 제목)", "")

    # 이미지 필터링
    filtered_reports = prd_data.copy()

    # 기존 필터링 로직
    # if selected_line != "전체":
    #     filtered_reports = [file for file in filtered_reports if file["line"] == selected_line]

    # if selected_equipment != "전체":
    #     filtered_reports = [file for file in filtered_reports if file["equipment"] == selected_equipment]

    # if selected_issue != "전체":
    #     filtered_reports = [file for file in filtered_reports if file["issue"] == selected_issue]

    # if search_query:
    #     search_query = search_query.lower()
    #     filtered_reports = [
    #         file for file in filtered_reports
    #         if search_query in file.get("file_name", "").lower() or
    #            search_query in file.get("title", "").lower() or
    #            search_query in file.get("summary", {}).get("full_text", "").lower()
    #     ]

    # 최적화된 필터링 로직
    def combined_filter(x):
        try:
            if selected_line != "전체" and selected_line not in x["lines"]:
                return False
            if selected_equipment != "전체" and selected_equipment not in x["equipments"]:
                return False
            if selected_issue != "전체" and selected_issue not in x["issues"]:
                return False
            if search_query:
                search_query_lower = search_query.lower()
                if not (search_query_lower in x.get("file_name", "").lower() or
                    search_query_lower in x.get("title", "").lower() or
                    search_query_lower in x.get("summary", {}).get("full_text", "").lower()):
                    return False
            return True
        except Exception as e:
            print(f"필터링 오류: {str(e)}")
            return False

    filtered_reports = list(filter(combined_filter, filtered_reports))

    # 결과 표시
    st.subheader("보고서 갤러리")
    st.info(f"총 {len(filtered_reports)}개의 보고서가 있습니다.")

    if not filtered_reports:
        st.warning("필터링 조건에 맞는 보고서가 없습니다.")
        return

    # 갤러리 표시 옵션
    display_option = st.radio("표시 방식", ["그리드", "상세"])

    # 그리드 표시
    if display_option == "그리드":
        columns = st.columns(3)

        for i, file in enumerate(filtered_reports):
            col_idx = i % 3

            with columns[col_idx]:
                try:
                    # 각 파일의 첫 페이지를 썸네일로 사용
                    st.image(file["pages"][0]["image_path"])
                except Exception as e:
                    st.error(f"이미지  로드 오류: {str(e)}")

                markdown_content = f"""### {file.get('file_name', '파일명 없음')}
- **제목**: {file.get('title', '제목 없음')}
- **날짜**: {file.get('date', '날짜 정보 없음')}
- **라인**: {', '.join(file.get('lines', ['대상 라인 정보 없음']))}
- **설비**: {', '.join(file.get('equipments', ['대상 설비 정보 없음']))}
- **이슈**: {', '.join(file.get('issues', ['발생 이슈 정보 없음']))}
"""
                st.markdown(markdown_content)
                # 이미지 상세보기 버튼
                if st.button(f"상세보기 #{i+1}", key=f"detail_btn_{i}"):
                    st.session_state["prd_selected_file"] = file

    # 상세 표시
    elif display_option == "상세":
        # for i, img_info in enumerate(filtered_reports):
            # st.markdown(f"### 이미지 {i+1}: {img_info['filename']}")

            # col1, col2 = st.columns([3, 2])

            # with col1:
            #     try:
            #         st.image(img_info["path"])
            #     except Exception as e:
            #         st.error(f"이미지 로드 오류: {str(e)}")

            # with col2:
            #     # 이미지 메타데이터 표시
            #     st.markdown(f"**제목:** {img_info['title']}")
            #     st.markdown(f"**라인:** {img_info['line']}")
            #     st.markdown(f"**제품:** {img_info['product']}")
            #     if img_info['issue']:
            #         st.markdown(f"**이슈:** {img_info['issue']}")
            #     st.markdown(f"**날짜:** {img_info['work_date']}")

            #     # 이미지 설명 표시
            #     if img_info["description"]:
            #         st.markdown("**이미지 설명:**")
            #         st.write(img_info["description"])

        for i, file in enumerate(filtered_reports):
            col1, col2 = st.columns([2, 3])

            with col1:
                # 각 파일의 첫 페이지를 썸네일로 사용
                try:
                    st.image(file["pages"][0]["image_path"])
                except Exception as e:
                    st.error(f"이미지 로드 오류: {str(e)}")

            with col2:
                # 보고서 정보 표시
                markdown_content = f"""## {file['file_name']}
### 기본 정보
- **제목**: {file.get('title', '제목 없음')}
- **날짜**: {file.get('date', '날짜 정보 없음')}
- **라인**: {', '.join(file.get('lines', ['대상 라인 정보 없음']))}
- **설비**: {', '.join(file.get('equipments', ['대상 설비 정보 없음']))}
- **이슈**: {', '.join(file.get('issues', ['발생 이슈 정보 없음']))}

### 요약
{file.get('summary', {}).get('full_text', '요약 없음')}"""
                st.markdown(markdown_content)

            with st.expander("내용 보기", expanded=False):
                for page in file["pages"]:
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        st.image(page["image_path"], use_container_width=True)
                    with col2:
                        st.markdown(f"#### 제목\n{page.get('title', '제목 없음')}")
                        st.markdown(f"#### 요약\n{page.get('summary', '요약 없음')}")
                    st.markdown("---")

            st.markdown("---")

    # # 이미지 정보 테이블
    # with st.expander("이미지 정보 테이블"):
    #     # 표시할 데이터 준비
    #     table_data = []
    #     for img in filtered_reports:
    #         table_data.append({
    #             "파일명": img["filename"],
    #             "라인": img["line"],
    #             "제품": img["product"],
    #             "이슈": img["issue"],
    #             "작업일자": img["work_date"],
    #             "설명여부": "있음" if img["description"] else "없음"
    #         })

    #     # 데이터프레임 표시
    #     df = pd.DataFrame(table_data)
    #     st.dataframe(df, use_container_width=True)

    # 그리드 뷰 - 선택된 보고서 상세 보기
    if hasattr(st.session_state, 'prd_selected_file') and st.session_state.prd_selected_file:
        file = st.session_state.prd_selected_file

        with st.container():
            st.markdown("---")
            st.markdown("## 보고서 상세 정보")
            markdown_content = f"""### {file['file_name']}
- **제목**: {file.get('title', '제목 없음')}
- **날짜**: {file.get('date', '날짜 정보 없음')}
- **라인**: {', '.join(file.get('lines', ['대상 라인 정보 없음']))}
- **설비**: {', '.join(file.get('equipments', ['대상 설비 정보 없음']))}
- **이슈**: {', '.join(file.get('issues', ['발생 이슈 정보 없음']))}

### 요약
{file.get('summary', {}).get('full_text', '요약 없음')}"""
            st.markdown(markdown_content)

            for page in file["pages"]:
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.image(page["image_path"], use_container_width=True)
                with col2:
                    st.markdown(f"#### 제목\n{page.get('title', '제목 없음')}")
                    st.markdown(f"#### 요약\n{page.get('summary', '요약 없음')}")
                st.markdown("---")

            if st.button("닫기"):
                st.session_state.prd_selected_file = None
                st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="생산이슈리포트 보고서 갤러리", layout="wide")
    show_prd_images()