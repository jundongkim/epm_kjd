"""
PRD(생산이슈리포트) 통계 분석 모듈
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar
import re
from collections import Counter

from components.prd.prd_data_loader import load_prd_data, find_image_file

def extract_date(date_str):
    """날짜 문자열에서 날짜 객체 추출"""
    if not date_str:
        return None

    try:
        # 날짜 형식 변환
        date_str = date_str.split()[0]  # 공백으로 분리된 경우 첫 부분만 사용
        return pd.to_datetime(date_str)
    except:
        return None

def extract_keywords(text, min_length=2):
    """텍스트에서 키워드 추출"""
    if not text or pd.isna(text):
        return []

    # 한글, 영문, 숫자만 남기고 제거
    text = re.sub(r'[^\w\s가-힣]', ' ', str(text))
    # 연속된 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()

    # 단어 분리
    words = text.split()

    # 불용어 목록 (한국어)
    stopwords = [
        '이', '있', '하', '것', '들', '그', '되', '수', '이', '보', '않', '없', '나', '사람', '주', '아니', '등', '같', '우리', '때', '년', '가', '한', '지', '대하', '오', '말', '일',
        '그렇', '위하', '때문', '그것', '두', '말하', '알', '그러나', '받', '못하', '일', '그런', '또', '문제', '더', '사회', '많', '그리고', '좋', '크', '따르', '중', '나오', '가지',
        '씨', '시키', '만들', '지금', '생각하', '그러', '속', '하나', '집', '살', '모르', '적', '월', '데', '자신', '안', '원', '력', '것', '인', '어떤', '경우'
    ]

    # 불용어 제거 및 길이 필터링
    filtered_words = [word for word in words if word not in stopwords and len(word) >= min_length]

    return filtered_words

def show_prd_statistics():
    """생산이슈리포트 통계 분석 화면을 표시합니다."""
    st.title("생산이슈리포트 통계 분석")

    # 데이터 로드
    if "prd_data" not in st.session_state:
        with st.spinner("생산이슈리포트 데이터 로딩 중..."):
            st.session_state.prd_data = load_prd_data()

    if not st.session_state.prd_data:
        st.warning("생산이슈리포트 데이터를 불러올 수 없습니다.")
        return

    prd_data = st.session_state.prd_data

    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📊 기본 통계", "📅 시간별 분석", "🔄 상관관계 분석", "📝 텍스트 분석"])

    with tab1:
        st.subheader("기본 통계")

        # 기본 통계 정보
        total_entries = len(prd_data)
        st.info(f"총 {total_entries}개의 생산이슈리포트 데이터가 있습니다.")

        # 분석 항목
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

        # 차트 표시
        col1, col2 = st.columns(2)

        with col1:
            # 라인별 차트
            if line_counts:
                df_line = pd.DataFrame({
                    "라인": list(line_counts.keys()),
                    "건수": list(line_counts.values())
                })
                df_line = df_line.sort_values("건수", ascending=False)

                fig = px.bar(
                    df_line,
                    x="라인",
                    y="건수",
                    title="라인별 이슈 분포",
                    color="라인"
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # 설비별 차트
            if equipment_counts:
                df_equipment = pd.DataFrame({
                    "설비": list(equipment_counts.keys()),
                    "건수": list(equipment_counts.values())
                })
                df_equipment = df_equipment.sort_values("건수", ascending=False)

                fig = px.bar(
                    df_equipment,
                    x="설비",
                    y="건수",
                    title="설비별 이슈 분포",
                    color="제품"
                )
                st.plotly_chart(fig, use_container_width=True)

        # 이슈별 차트 (전체 너비)
        if issue_counts:
            df_issue = pd.DataFrame({
                "이슈": list(issue_counts.keys()),
                "건수": list(issue_counts.values())
            })
            df_issue = df_issue.sort_values("건수", ascending=False)

            fig = px.bar(
                df_issue,
                x="이슈",
                y="건수",
                title="이슈별 분포",
                color="이슈"
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("시간별 분석")

        # 날짜 정보 추출
        dates = []
        for entry in prd_data:
            date_str = entry.get("date", "1000-01-01")
            date_obj = extract_date(date_str)
            if date_obj:
                dates.append(date_obj)

        if dates:
            # 날짜별 빈도 계산
            date_counts = pd.Series(dates).value_counts().sort_index()

            # 월별 집계
            monthly_counts = date_counts.resample('M').sum()

            # 월별 추이 그래프
            fig = px.line(
                x=monthly_counts.index,
                y=monthly_counts.values,
                title="월별 이슈 발생 추이",
                labels={"x": "날짜", "y": "이슈 건수"}
            )
            fig.update_layout(xaxis_title="날짜", yaxis_title="이슈 건수")
            st.plotly_chart(fig, use_container_width=True)

            # 요일별 분석
            weekday_counts = pd.Series(dates).dt.dayofweek.value_counts().sort_index()
            weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
            weekday_counts.index = [weekday_names[i] for i in weekday_counts.index]

            fig = px.bar(
                x=weekday_counts.index,
                y=weekday_counts.values,
                title="요일별 이슈 발생 빈도",
                labels={"x": "요일", "y": "이슈 건수"},
                color=weekday_counts.index
            )
            st.plotly_chart(fig, use_container_width=True)

            # 월별 분석
            month_counts = pd.Series(dates).dt.month.value_counts().sort_index()
            month_names = [calendar.month_name[i] for i in month_counts.index]

            fig = px.bar(
                x=month_names,
                y=month_counts.values,
                title="월별 이슈 발생 빈도",
                labels={"x": "월", "y": "이슈 건수"},
                color=month_names
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("날짜 정보가 없어 시간별 분석을 수행할 수 없습니다.")

    with tab3:
        st.subheader("상관관계 분석")

        # 라인-이슈 상관관계
        line_issue_counts = {}
        for entry in prd_data:
            lines = entry.get("lines", ["대상 라인 정보 없음"])
            issues = entry.get("issues", ["발생 이슈 정보 없음"])
            for line in lines:
                for issue in issues:
                    key = (line, issue)
                    line_issue_counts[key] = line_issue_counts.get(key, 0) + 1

        if line_issue_counts:
            # 히트맵 데이터 준비
            lines = sorted(list(set([k[0] for k in line_issue_counts.keys()])))
            issues = sorted(list(set([k[1] for k in line_issue_counts.keys()])))

            heatmap_data = np.zeros((len(lines), len(issues)))
            for i, line in enumerate(lines):
                for j, issue in enumerate(issues):
                    heatmap_data[i, j] = line_issue_counts.get((line, issue), 0)

            # 히트맵 그리기
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=issues,
                y=lines,
                colorscale='Blues',
                hoverongaps=False
            ))
            fig.update_layout(
                title="라인-이슈 상관관계",
                xaxis_title="이슈",
                yaxis_title="라인",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

        # 설비-이슈 상관관계
        equipment_issue_counts = {}
        for entry in prd_data:
            equipments = entry.get("equipments", ["대상 설비 정보 없음"])
            issues = entry.get("issues", ["발생 이슈 정보 없음"])
            for equipment in equipments:
                for issue in issues:
                    key = (equipment, issue)
                    equipment_issue_counts[key] = equipment_issue_counts.get(key, 0) + 1

        if equipment_issue_counts:
            # 히트맵 데이터 준비
            equipments = sorted(list(set([k[0] for k in equipment_issue_counts.keys()])))
            issues = sorted(list(set([k[1] for k in equipment_issue_counts.keys()])))

            heatmap_data = np.zeros((len(equipments), len(issues)))
            for i, equipment in enumerate(equipments):
                for j, issue in enumerate(issues):
                    heatmap_data[i, j] = equipment_issue_counts.get((equipment, issue), 0)

            # 히트맵 그리기
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=issues,
                y=equipments,
                colorscale='Viridis',
                hoverongaps=False
            ))
            fig.update_layout(
                title="설비-이슈 상관관계",
                xaxis_title="이슈",
                yaxis_title="설비",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("텍스트 분석")

        # 텍스트 데이터 추출
        text_data = []
        for entry in prd_data:
            for page in entry.get("pages", []):
                text_data.append(page.get("content", ""))

        if text_data:
            # 키워드 추출
            all_keywords = []
            for text in text_data:
                keywords = extract_keywords(text)
                all_keywords.extend(keywords)

            # 키워드 빈도 계산
            keyword_counts = Counter(all_keywords)
            top_keywords = keyword_counts.most_common(20)

            # 키워드 빈도 차트
            df_keywords = pd.DataFrame(top_keywords, columns=["키워드", "빈도"])

            fig = px.bar(
                df_keywords,
                x="키워드",
                y="빈도",
                title="상위 20개 키워드 빈도",
                color="빈도",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 텍스트 길이 분석
            text_lengths = [len(text) for text in text_data]

            fig = px.histogram(
                x=text_lengths,
                nbins=30,
                title="텍스트 길이 분포",
                labels={"x": "텍스트 길이", "y": "빈도"}
            )
            st.plotly_chart(fig, use_container_width=True)

            # 통계 정보
            avg_length = np.mean(text_lengths)
            median_length = np.median(text_lengths)
            max_length = np.max(text_lengths)
            min_length = np.min(text_lengths)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("평균 텍스트 길이", f"{avg_length:.1f}")
            col2.metric("중앙값 텍스트 길이", f"{median_length:.1f}")
            col3.metric("최대 텍스트 길이", max_length)
            col4.metric("최소 텍스트 길이", min_length)
        else:
            st.warning("텍스트 데이터가 없어 분석을 수행할 수 없습니다.")

if __name__ == "__main__":
    st.set_page_config(page_title="생산이슈리포트 통계 분석", layout="wide")
    show_prd_statistics()