"""
PRD(생산관리이력) 유사 검색 기능을 제공하는 모듈
"""

import streamlit as st
import pandas as pd
from components.prd.prd_data_loader import load_prd_data, load_or_create_vector_db, find_image_file
import os

def show_prd_similar_search():
    """생산관리이력 유사 검색 기능을 제공합니다."""
    st.title("생산관리이력 유사 검색")

    # 데이터 로드
    if "prd_data" not in st.session_state or not st.session_state.prd_data:
        with st.spinner("생산이슈리포트 데이터를 로드 중입니다..."):
            st.session_state.prd_data = load_prd_data()
            if not st.session_state.prd_data:
                st.error("생산이슈리포트 데이터를 로드할 수 없습니다.")
                return
            else:
                st.success("생산이슈리포트 데이터가 성공적으로 로드되었습니다.")
    prd_data = st.session_state.prd_data

    if not prd_data:
        st.warning("생산관리이력 데이터를 불러올 수 없습니다.")
        return

    # 벡터 저장소 로드
    if "prd_vector_store" not in st.session_state or not st.session_state.prd_vector_store:
        with st.spinner("벡터 데이터베이스를 초기화하는 중입니다..."):
            st.session_state.prd_vector_store = load_or_create_vector_db(
                st.session_state.prd_data,
                vector_dir="PRD/vector_db"
            )
            if not st.session_state.prd_vector_store:
                st.error("벡터 저장소를 초기화할 수 없습니다.")
                return
            else:
                st.success("벡터 저장소가 성공적으로 초기화되었습니다.")
    vector_store = st.session_state.prd_vector_store

    if not vector_store:
        st.error("벡터 저장소가 초기화되지 않았습니다.")
        return

    # 검색 옵션
    st.subheader("검색 옵션")

    # 검색어 입력
    query = st.text_input("검색어 입력", placeholder="예: 금속이물 원인 분석")

    # 검색 결과 수 설정
    k_results = st.slider("검색 결과 수", min_value=1, max_value=20, value=5)

    # 필터링 옵션
    with st.expander("필터링 옵션"):
        # 라인 정보 추출
        all_lines = sorted(list(set([line for entry in prd_data for line in entry.get("lines", ["대상 라인 정보 없음"])])))
        all_equipments = sorted(list(set([equipment for entry in prd_data for equipment in entry.get("equipments", ["대상 설비 정보 없음"])])))
        all_issues = sorted(list(set([issue for entry in prd_data for issue in entry.get("issues", ["발생 이슈 정보 없음"])])))

        # 필터링 UI
        col1, col2 = st.columns(2)

        with col1:
            selected_line = st.multiselect(
                "라인 필터링",
                all_lines
            )

        with col2:
            selected_equipment = st.multiselect(
                "설비 필터링",
                all_equipments
            )

        selected_issue = st.multiselect(
            "이슈 필터링",
            all_issues
        )

    # 검색 실행
    if query:
        with st.spinner("검색 중..."):
            # 메타데이터 필터 구성
            filter_dict = {}

            # if selected_line:
            #     filter_dict["lines"] = {"$in": selected_line}

            # if selected_equipment:
            #     filter_dict["equipments"] = {"$in": selected_equipment}

            # if selected_issue:
            #     filter_dict["issues"] = {"$in": selected_issue}
            if selected_line:
                filter_dict["line"] = selected_line

            if selected_equipment:
                filter_dict["equipment"] = selected_equipment

            if selected_issue:
                filter_dict["issue"] = selected_issue

            # 필터 적용 여부에 따라 검색
            if filter_dict:
                # 필터링 함수
                def filter_func(x):
                    is_file = x.get("is_file", False)
                    # 라인 필터링
                    if "line" in filter_dict:
                        if is_file:
                            lines = x.get("lines", [])
                        else:
                            # 페이지이면 parent_file에서 라인 정보 추출
                            lines = x.get("parent_file", {}).get("lines", [])

                        # 두 리스트 사이에 중복되는 라인이 없으면 False
                        if set(filter_dict["line"]).isdisjoint(lines):
                            return False
                    # 설비 필터링
                    if "equipment" in filter_dict:
                        if is_file:
                            equipments = x.get("equipments", [])
                        else:
                            # 페이지이면 parent_file에서 설비 정보 추출
                            equipments = x.get("parent_file", {}).get("equipments", [])

                        # 두 리스트 사이에 중복되는 설비가 없으면 False
                        if set(filter_dict["equipment"]).isdisjoint(equipments):
                            return False
                    # 이슈 필터링
                    if "issue" in filter_dict:
                        if is_file:
                            issues = x.get("issues", [])
                        else:
                            # 페이지이면 parent_file에서 이슈 정보 추출
                            issues = x.get("parent_file", {}).get("issues", [])

                        # 두 리스트 사이에 중복되는 이슈가 없으면 False
                        if set(filter_dict["issue"]).isdisjoint(issues):
                            return False
                    return True

                # 필터링 함수 적용하여 검색
                results = vector_store.similarity_search_with_score(
                    query,
                    k=k_results,
                    filter=filter_func
                )
            else:
                # 필터링 없이 검색
                results = vector_store.similarity_search_with_score(
                    query,
                    k=k_results
                )

            # 결과 표시
            if results:
                st.success(f"{len(results)}개의 검색 결과를 찾았습니다.")

                for i, (doc, score) in enumerate(results):
                    metadata = doc.metadata
                    is_file = metadata.get('is_file', False)

                    if is_file:
                        # 파일인 경우
                        with st.container(border=True):
                            # 유사도 점수 계산 (0~100%)
                            similarity = (1 - score) * 100

                            # 보고서 정보 표시
                            st.markdown(f"## {metadata.get('file_name', '제목 없음')}")
                            st.markdown(f"### (**유사도:** {similarity:.1f}%)")

                            # 메타데이터 표시
                            st.markdown(f"- **날짜:** {metadata.get('date', '날짜 정보 없음')}")
                            st.markdown(f"- **라인:** {', '.join(metadata.get('lines', ['대상 라인 정보 없음']))}")
                            st.markdown(f"- **설비:** {', '.join(metadata.get('equipments', ['대상 설비 정보 없음']))}")
                            st.markdown(f"- **이슈:** {', '.join(metadata.get('issues', ['발생 이슈 정보 없음']))}")
                            st.markdown("")
                            st.markdown(f"#### 요약\n{metadata.get('summary', {}).get('full_text', '요약 없음')}")

                            # 보고서 내용 표시
                            with st.expander("내용 보기", expanded=False):
                                for page in metadata.get("pages", []):
                                    col1, col2 = st.columns([2, 3])
                                    with col1:
                                        st.image(page["image_path"], use_container_width=True)
                                    with col2:
                                        st.markdown(f"#### 제목\n{page.get('title', '제목 없음')}")
                                        st.markdown(f"#### 요약\n{page.get('summary', '요약 없음')}")
                                    st.markdown("---")

                    else:
                        # 페이지인 경우
                        with st.container(border=True):
                            # 유사도 점수 계산 (0~100%)
                            similarity = (1 - score) * 100

                            # 페이지 정보 표시
                            col1, col2 = st.columns([2, 3])
                            with col1:
                                st.image(metadata["image_path"], use_container_width=True)
                            with col2:
                                title = f"## {metadata.get('parent_file', {}).get('file_name', '제목 없음')} - {metadata.get('page_number', '페이지 정보 없음')} 페이지"
                                subtitle = f"### {metadata.get('title', '페이지 제목 없음')}"
                                score = f"### (**유사도:** {similarity:.1f}%)"
                                summary = f"#### 요약\n{metadata.get('summary', '요약 없음')}"
                                st.markdown(title)
                                st.markdown(subtitle)
                                st.markdown(score)
                                st.markdown(summary)

                    st.markdown("---")
            else:
                st.warning("검색 결과가 없습니다.")
    else:
        st.info("검색어를 입력하세요.")

    # 데이터 통계
    with st.expander("데이터 통계"):
        st.info(f"총 {len(prd_data)}개의 생산관리이력 데이터가 있습니다.")

        # 라인별 통계
        line_counts = {}
        equipment_counts = {}
        issue_counts = {}

        for entry in prd_data:
            # 라인 정보
            lines = entry.get("lines", ["대상 라인 정보 없음"])
            for line in lines:
                line_counts[line] = line_counts.get(line, 0) + 1

            # 설비 정보
            equipments = entry.get("equipments", ["대상 설비 정보 없음"])
            for equipment in equipments:
                equipment_counts[equipment] = equipment_counts.get(equipment, 0) + 1

            # 이슈 정보
            issues = entry.get("issues", ["발생 이슈 정보 없음"])
            for issue in issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        # 데이터프레임 생성
        df_line = pd.DataFrame({
            "라인": list(line_counts.keys()),
            "건수": list(line_counts.values())
        }).sort_values("건수", ascending=False)

        df_equipment = pd.DataFrame({
            "설비": list(equipment_counts.keys()),
            "건수": list(equipment_counts.values())
        }).sort_values("건수", ascending=False)

        df_issue = pd.DataFrame({
            "이슈": list(issue_counts.keys()),
            "건수": list(issue_counts.values())
        }).sort_values("건수", ascending=False)

        # 통계 표시
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("라인별 통계")
            st.dataframe(df_line)

        with col2:
            st.subheader("설비별 통계")
            st.dataframe(df_equipment)

        with col3:
            st.subheader("이슈별 통계")
            st.dataframe(df_issue)

if __name__ == "__main__":
    st.set_page_config(page_title="생산관리이력 유사 검색", layout="wide")
    show_prd_similar_search()