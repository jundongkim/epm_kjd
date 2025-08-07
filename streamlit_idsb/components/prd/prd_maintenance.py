"""
PRD(생산이슈리포트) 유지보수 관련 정보를 표시하는 모듈
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from components.prd.prd_data_loader import load_prd_data, find_image_file

def show_prd_maintenance():
    """생산이슈리포트 유지보수 정보를 표시합니다."""
    st.title("생산이슈리포트 정보")

    # 데이터 로드
    if "prd_data" not in st.session_state:
        with st.spinner("생산이슈리포트 데이터 로딩 중..."):
            st.session_state.prd_data = load_prd_data()

    if not st.session_state.prd_data:
        st.warning("생산이슈리포트 데이터를 불러올 수 없습니다.")
        return

    prd_data = st.session_state.prd_data

    # 데이터 분석 및 표시
    st.subheader("생산이슈리포트 개요")

    # 1. 기본 통계
    total_entries = len(prd_data)
    st.info(f"총 {total_entries}개의 생산이슈리포트 데이터가 있습니다.")

    # 2. 라인별 이슈 분포
    line_counts = {}
    equipment_counts = {}
    issue_counts = {}
    work_type_counts = {}
    date_counts = {}

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

        # 날짜 정보
        date = entry.get("date", "1000-01-01")
        if date:
            try:
                # 날짜 형식 변환
                date_obj = datetime.strptime(date.split()[0], "%Y-%m-%d")
                date_str = date_obj.strftime("%Y-%m")  # 년-월 형식으로 변환
                date_counts[date_str] = date_counts.get(date_str, 0) + 1
            except:
                pass

    # 탭 구성
    tab1, tab2 = st.tabs(["라인/설비별 분석", "이슈/시간별 분석"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            # 라인별 차트
            if line_counts:
                df_lines = pd.DataFrame({
                    "라인": list(line_counts.keys()),
                    "건수": list(line_counts.values())
                })
                df_lines = df_lines.sort_values("건수", ascending=False)

                fig = px.bar(
                    df_lines,
                    x="라인",
                    y="건수",
                    title="라인별 이슈 분포",
                    color="라인"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("라인 정보가 없습니다.")

        with col2:
            # 설비별 차트
            if equipment_counts:
                df_equipments = pd.DataFrame({
                    "설비": list(equipment_counts.keys()),
                    "건수": list(equipment_counts.values())
                })
                df_equipments = df_equipments.sort_values("건수", ascending=False)

                fig = px.bar(
                    df_equipments,
                    x="설비",
                    y="건수",
                    title="설비별 이슈 분포",
                    color="설비"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("제품 정보가 없습니다.")

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            # 이슈별 차트
            if issue_counts:
                df_issues = pd.DataFrame({
                    "이슈": list(issue_counts.keys()),
                    "건수": list(issue_counts.values())
                })
                df_issues = df_issues.sort_values("건수", ascending=False)

                fig = px.bar(
                    df_issues,
                    x="이슈",
                    y="건수",
                    title="이슈별 분포",
                    color="이슈"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("이슈 정보가 없습니다.")

        with col2:
            # 시간별 차트
            if date_counts:
                df_date = pd.DataFrame({
                    "년월": list(date_counts.keys()),
                    "건수": list(date_counts.values())
                })
                df_date = df_date.sort_values("년월")

                fig = px.line(
                    df_date,
                    x="년월",
                    y="건수",
                    title="월별 이슈 발생 추이",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("날짜 정보가 없습니다.")

    # 3. 상세 데이터 표시
    st.subheader("생산이슈리포트 상세 데이터")

    # 필터링 옵션
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_line = st.selectbox(
            "라인 선택",
            ["전체"] + sorted(list(line_counts.keys())),
            key="prd_maintenance_line_filter"
        )

    with col2:
        selected_equipment = st.selectbox(
            "설비 선택",
            ["전체"] + sorted(list(equipment_counts.keys())),
            key="prd_maintenance_equipment_filter"
        )

    with col3:
        selected_issue = st.selectbox(
            "이슈 선택",
            ["전체"] + sorted(list(issue_counts.keys())),
            key="prd_maintenance_issue_filter"
        )

    # 데이터 필터링
    filtered_data = prd_data.copy()

    filtered_data = [
        entry for entry in prd_data
        if (selected_line == "전체" or selected_line in entry.get("lines", [])) and
           (selected_equipment == "전체" or selected_equipment in entry.get("equipments", [])) and
           (selected_issue == "전체" or selected_issue in entry.get("issues", []))
    ]

    # 필터링된 데이터 표시
    if filtered_data:
        st.info(f"필터링된 데이터: {len(filtered_data)}건")

        # 테이블 형태로 데이터 표시
        table_data = []
        for entry in filtered_data:
            table_data.append({
                "파일명": entry.get("file_name", ""),
                "제목": entry.get("title", ""),
                "날짜": entry.get("date", ""),
                "라인": str(entry.get("lines", "")),
                "설비": str(entry.get("equipments", "")),
                "이슈": str(entry.get("issues", ""))
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

        # 선택한 데이터 상세 보기
        st.subheader("상세 정보")
        selected_index = st.selectbox("상세 정보 보기", range(len(filtered_data)),
                                     format_func=lambda i: filtered_data[i].get("file_name", f"항목 {i+1}"),
                                     key="prd_maintenance_detail_selector")

        selected_entry = filtered_data[selected_index]

        # 상세 정보 표시
        st.markdown(f"## {selected_entry.get('file_name', '파일명 없음')}")
        st.markdown(f"**제목:** {selected_entry.get('title', '제목 없음')}")
        st.markdown(f"**날짜:** {selected_entry.get('date', '날짜 정보 없음')}")
        st.markdown(f"**라인:** {', '.join(selected_entry.get('lines', ['대상 라인 정보 없음']))}")
        st.markdown(f"**설비:** {', '.join(selected_entry.get('equipments', ['대상 설비 정보 없음']))}")
        st.markdown(f"**이슈:** {', '.join(selected_entry.get('issues', ['발생 이슈 정보 없음']))}")

        # 요약
        if "summary" in selected_entry and selected_entry["summary"]:
            st.markdown("### 요약")
            st.markdown(selected_entry.get("summary", {}).get("full_text", "요약 없음"))

        for page in selected_entry["pages"]:
            col1, col2 = st.columns([2, 3])
            with col1:
                st.image(page["image_path"], use_container_width=True)
            with col2:
                st.markdown(f"#### 제목\n{page.get('title', '제목 없음')}")
                st.markdown(f"#### 요약\n{page.get('summary', '요약 없음')}")
            st.markdown("---")
    else:
        st.warning("필터링 조건에 맞는 데이터가 없습니다.")

if __name__ == "__main__":
    st.set_page_config(page_title="생산이슈리포트 정보", layout="wide")
    show_prd_maintenance()