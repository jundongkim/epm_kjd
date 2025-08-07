import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from wordcloud import WordCloud
from konlpy.tag import Okt
import matplotlib.pyplot as plt
import os
import logging

def create_wordcloud(text_data):
    """텍스트 데이터로부터 워드클라우드를 생성합니다."""
    try:
        # 텍스트 전처리
        combined_text = ' '.join([str(text) for text in text_data if isinstance(text, str)])

        # 불용어 정의 (필요에 따라 추가)
        stopwords = set(['및', '등', '를', '이', '가', '의', '도', '를', '으로', '에', '에서', '했다', '했음', '함', '할', '하는', '하다'])

        # 워드클라우드 생성
        wordcloud = WordCloud(
            font_path='fonts/Freesentation.ttf',  # 한글 폰트 사용
            width=1200,
            height=800,
            background_color='white',
            max_words=200,
            stopwords=stopwords,
            min_font_size=10,
            max_font_size=200,
            random_state=42
        )

        # 워드클라우드 생성
        wordcloud_image = wordcloud.generate(combined_text)

        return wordcloud_image

    except Exception as e:
        st.error(f"워드클라우드 생성 중 오류 발생: {str(e)}")
        return None

def show_cmms_statistics():
    """CMMS 통계 분석 컴포넌트"""
    st.title("📊 통계 분석")

    # 일일업무일지 데이터 확인
    if "cmms_data" not in st.session_state:
        st.error("일일업무일지 데이터가 로드되지 않았습니다.")
        return

    # 데이터 가져오기
    cmms_data = st.session_state.cmms_data

    # 데이터프레임 생성
    df = pd.DataFrame(cmms_data)

    # 전체 업무 기록 수 표시
    st.write(f"### 📋 전체 업무 기록: {len(df):,}건")

    # 통계 섹션 선택
    stats_section = st.radio(
        "분석 항목 선택",
        ["시계열 분석", "설비 분석", "작업 유형 분석", "라인별 분석", "키워드 분석"],
        horizontal=True
    )

    # 시계열 분석
    if stats_section == "시계열 분석":
        st.markdown("### 📅 시계열 분석")

        # 작업 일자 전처리
        df['작업 일자'] = pd.to_datetime(df['작업 일자'].str.split('\n').str[0], format='%Y-%m-%d', errors='coerce')
        df['년월'] = df['작업 일자'].dt.strftime('%Y-%m')

        # 1. 월별 추이
        monthly_stats = df.groupby('년월').agg({
            '라인': 'count',
            '설비명': 'nunique'
        }).reset_index()
        monthly_stats.columns = ['년월', '총 작업건수', '설비 수']

        fig_monthly = go.Figure()
        fig_monthly.add_trace(go.Bar(
            x=monthly_stats['년월'],
            y=monthly_stats['총 작업건수'],
            name='총 작업건수'
        ))
        fig_monthly.add_trace(go.Scatter(
            x=monthly_stats['년월'],
            y=monthly_stats['설비 수'],
            name='설비 수',
            yaxis='y2'
        ))
        fig_monthly.update_layout(
            title='월별 작업 통계',
            yaxis=dict(title='총 작업건수'),
            yaxis2=dict(title='설비 수', overlaying='y', side='right'),
            showlegend=True,
            hovermode='x unified'
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

        # 2. 일별 작업 건수 히트맵
        df['요일'] = df['작업 일자'].dt.day_name()
        df['시간'] = pd.to_datetime(df['작업 시작'], format='%H:%M', errors='coerce').dt.hour

        daily_heatmap = pd.crosstab(df['요일'], df['시간'])
        fig_heatmap = px.imshow(
            daily_heatmap,
            title='요일/시간대별 작업 분포',
            labels=dict(x="시간", y="요일", color="작업건수"),
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # 설비 분석
    elif stats_section == "설비 분석":
        st.markdown("### 🔧 설비 분석")

        # 1. 상위 설비 작업 빈도
        equipment_counts = df['설비번호'].value_counts().head(10)
        fig_equipment = px.bar(
            x=equipment_counts.index,
            y=equipment_counts.values,
            title='상위 10개 설비 작업 빈도',
            labels={'x': '설비번호', 'y': '작업건수'},
            color=equipment_counts.values,
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_equipment, use_container_width=True)

        # 2. 설비별 작업 종류 분포
        top_equipment = equipment_counts.index[:5]
        work_type_dist = pd.crosstab(df['설비번호'], df['작업 종류'])
        work_type_dist = work_type_dist.loc[top_equipment]

        fig_work_types = px.bar(
            work_type_dist,
            title='주요 설비별 작업 종류 분포',
            barmode='stack'
        )
        st.plotly_chart(fig_work_types, use_container_width=True)

    # 작업 유형 분석
    elif stats_section == "작업 유형 분석":
        st.markdown("### 🛠️ 작업 유형 분석")

        # 작업 일자 전처리
        df['작업 일자'] = pd.to_datetime(df['작업 일자'].str.split('\n').str[0], format='%Y-%m-%d', errors='coerce')
        df['년월'] = df['작업 일자'].dt.strftime('%Y-%m')

        # 1. 작업 종류별 분포
        work_types = df['작업 종류'].value_counts()
        fig_work_dist = px.pie(
            values=work_types.values,
            names=work_types.index,
            title='작업 종류별 분포',
            hole=0.4
        )
        st.plotly_chart(fig_work_dist, use_container_width=True)

        # 2. 작업 종류별 월간 추이
        monthly_work_types = pd.crosstab(df['년월'], df['작업 종류'])

        fig_monthly_types = px.line(
            monthly_work_types,
            title='작업 종류별 월간 추이',
            labels={'value': '작업건수', 'variable': '작업 종류'},
        )
        st.plotly_chart(fig_monthly_types, use_container_width=True)

    # 라인별 분석
    elif stats_section == "라인별 분석":
        st.markdown("### 🏭 라인별 분석")

        # 작업 일자 전처리
        df['작업 일자'] = pd.to_datetime(df['작업 일자'].str.split('\n').str[0], format='%Y-%m-%d', errors='coerce')
        df['년월'] = df['작업 일자'].dt.strftime('%Y-%m')

        # 1. 라인별 작업 건수
        line_counts = df['라인'].value_counts()
        fig_lines = px.bar(
            x=line_counts.index,
            y=line_counts.values,
            title='라인별 작업 건수',
            labels={'x': '라인', 'y': '작업건수'},
            color=line_counts.values,
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_lines, use_container_width=True)

        # 2. 라인별 작업 종류 분포
        line_work_types = pd.crosstab(df['라인'], df['작업 종류'])
        fig_line_types = px.bar(
            line_work_types,
            title='라인별 작업 종류 분포',
            barmode='stack'
        )
        st.plotly_chart(fig_line_types, use_container_width=True)

        # 3. 라인별 월간 작업 추이
        line_monthly = pd.crosstab(df['년월'], df['라인'])

        fig_line_monthly = px.line(
            line_monthly,
            title='라인별 월간 작업 추이',
            labels={'value': '작업건수', 'variable': '라인'}
        )
        st.plotly_chart(fig_line_monthly, use_container_width=True)

    # 키워드 분석
    elif stats_section == "키워드 분석":
        st.markdown("### 🔤 키워드 분석")

        # 작업 상세내용에서 워드클라우드 생성
        work_details = df['작업 상세내용'].dropna().tolist()

        with st.spinner("워드클라우드 생성 중..."):
            try:
                wordcloud_image = create_wordcloud(work_details)

                if wordcloud_image is not None:
                    # matplotlib figure 생성
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wordcloud_image, interpolation='bilinear')
                    plt.axis('off')

                    # Streamlit에 표시
                    st.pyplot(plt)

                    st.info("워드클라우드는 작업 상세내용에서 추출한 주요 키워드를 시각화한 것입니다.")
                else:
                    st.warning("워드클라우드를 생성할 수 없습니다. 데이터를 확인해주세요.")
            except Exception as e:
                st.error(f"워드클라우드 표시 중 오류 발생: {str(e)}")
                st.error("상세 오류 정보:")
                st.exception(e)

        # 가장 빈번한 키워드 추출 및 표시
        try:
            # 단어 추출
            all_text = ' '.join(work_details)

            # 간단한 정규식으로 단어 추출
            words = re.findall(r'\w+', all_text)
            word_counts = {}

            # 불용어 필터링
            stopwords = set(['및', '등', '를', '이', '가', '의', '도', '를', '으로', '에', '에서'])

            for word in words:
                if len(word) > 1 and word not in stopwords:  # 한 글자 단어 및 불용어 제외
                    if word in word_counts:
                        word_counts[word] += 1
                    else:
                        word_counts[word] = 1

            # 빈도순 정렬
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            top_words = sorted_words[:30]

            # 표 형식으로 표시
            st.subheader("주요 키워드 빈도")

            # 데이터프레임 생성
            word_df = pd.DataFrame(top_words, columns=['키워드', '빈도'])

            # 막대 그래프로 표시
            fig = px.bar(
                word_df.head(15),
                x='키워드',
                y='빈도',
                title="상위 15개 키워드 빈도",
                color='빈도',
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 테이블로 모든 키워드 표시
            st.dataframe(word_df, use_container_width=True)

        except Exception as e:
            st.error(f"키워드 분석 중 오류 발생: {str(e)}")