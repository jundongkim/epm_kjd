import streamlit as st
import pandas as pd
import plotly.express as px
from components.ai_utils import (
    init_session_state,
    display_analysis_ui,
    generate_ai_analysis
)
from utils.style import ECOPRO_COLORS
import json

def show_data_overview(df):
    """데이터 개요 탭 표시"""
    # 세션 상태 초기화
    init_session_state(key_prefix="analysis")

    # 선택된 데이터셋 확인
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값

    st.header(f"데이터 개요 (데이터셋: {selected_dataset})")

    # 데이터 기본 정보
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("데이터 크기", f"{df.shape[0]:,} 행 × {df.shape[1]:,} 열")
    with col2:
        feature_types = {
            "Li 특성": len([col for col in df.columns if col.startswith('Li')]),
            "Pre_L 특성": len([col for col in df.columns if col.startswith('Pre_L')]),
            "Pre_S 특성": len([col for col in df.columns if col.startswith('Pre_S')]),
            "Qcp 특성": len([col for col in df.columns if col.startswith('Qcp')])
        }
        st.metric("특성 수", f"{df.shape[1]-2:,} 개")
        st.markdown(f"""
        <div style="font-size: 0.9rem; margin-top: -15px;">
            타겟 변수: <span style="color: {ECOPRO_COLORS['dark_blue']}; font-weight: bold;">Target_F</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.metric("메모리 사용량", f"{df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")

    # 데이터 미리보기
    st.subheader("데이터 미리보기")
    st.dataframe(df.head(10), use_container_width=True)

    # 기본 통계 정보
    st.subheader("기본 통계 정보")
    stats_df = df.describe()
    st.dataframe(stats_df, use_container_width=True)

    # 결측치 확인
    st.subheader("결측치 정보")
    missing_data = pd.DataFrame({
        '결측치 수': df.isnull().sum(),
        '결측 비율 (%)': (df.isnull().sum() / len(df) * 100).round(2)
    })
    if missing_data['결측치 수'].sum() > 0:
        st.dataframe(
            missing_data[missing_data['결측치 수'] > 0],
            use_container_width=True,
            column_config={
                "결측치 수": st.column_config.NumberColumn(
                    "결측치 수",
                    help="컬럼별 결측치 개수",
                    format="%d",
                    # color_continuous_scale=[
                    #     (0, ECOPRO_COLORS['light_blue']),
                    #     (0.5, ECOPRO_COLORS['dark_blue']),
                    #     (1, ECOPRO_COLORS['orange'])
                    # ]
                ),
                "결측 비율 (%)": st.column_config.NumberColumn(
                    "결측 비율 (%)",
                    help="전체 데이터 대비 결측치 비율",
                    format="%.2f%%",
                    # color_continuous_scale=[
                    #     (0, ECOPRO_COLORS['light_blue']),
                    #     (0.5, ECOPRO_COLORS['dark_blue']),
                    #     (1, ECOPRO_COLORS['orange'])
                    # ]
                )
            }
        )
    else:
        st.success("데이터에 결측치가 없습니다! 👍", icon="✅")

    # 히스토그램 (Target_F)
    st.subheader("타겟 변수 분포")
    fig = px.histogram(
        df, x="Target_F",
        nbins=50,
        marginal="box",
        title="Target_F 분포",
        color_discrete_sequence=[ECOPRO_COLORS['dark_blue']]
    )
    fig.update_layout(
        xaxis_title="Target_F 값",
        yaxis_title="빈도",
        template="plotly_white"
    )

    # 박스 플롯 색상 변경
    fig.update_traces(
        marker_color=ECOPRO_COLORS['dark_blue'],
        selector=dict(type='histogram')
    )
    fig.update_traces(
        marker_color=ECOPRO_COLORS['light_blue'],
        fillcolor=ECOPRO_COLORS['light_blue'],
        line=dict(color=ECOPRO_COLORS['dark_blue']),
        selector=dict(type='box')
    )

    st.plotly_chart(fig, use_container_width=True)

    # AI 분석 요약
    st.subheader("🤖 iDSB AI 분석 요약")

    # 분석 정보 수집
    analysis_info = {
        "데이터셋 크기": f"{df.shape[0]:,} 행 × {df.shape[1]:,} 열",
        "특성 유형별 수": feature_types,
        "기본 통계": stats_df.to_dict(),
        "결측치 현황": "없음" if missing_data['결측치 수'].sum() == 0 else missing_data[missing_data['결측치 수'] > 0].to_dict(),
        "Target_F 범위": f"{df['Target_F'].min():.2f} ~ {df['Target_F'].max():.2f}",
        "Target_F 평균": f"{df['Target_F'].mean():.2f}",
        "Target_F 표준편차": f"{df['Target_F'].std():.2f}"
    }

    # 프롬프트 생성
    prompt = f"""
    아래 데이터셋의 주요 분석 정보를 바탕으로 전문적인 분석 리포트를 작성해주세요.
    리포트는 마크다운 형식으로 작성하며, 각 섹션을 명확히 구분해주세요.

    ## 데이터셋 기본 정보
    - 크기: {analysis_info['데이터셋 크기']}
    - 특성 구성:
      * Li 특성: {analysis_info['특성 유형별 수']['Li 특성']}개
      * Pre_L 특성: {analysis_info['특성 유형별 수']['Pre_L 특성']}개
      * Pre_S 특성: {analysis_info['특성 유형별 수']['Pre_S 특성']}개
      * Qcp 특성: {analysis_info['특성 유형별 수']['Qcp 특성']}개

    ## Target_F 변수 통계
    - 범위: {analysis_info['Target_F 범위']}
    - 평균: {analysis_info['Target_F 평균']}
    - 표준편차: {analysis_info['Target_F 표준편차']}

    ## 데이터 품질
    - 결측치 현황: {analysis_info['결측치 현황']}

    다음 구조로 분석 리포트를 작성해주세요:

    1. 데이터셋 개요 (데이터의 규모와 구조)
    2. 특성 구성 분석 (Li, Pre_L, Pre_S, Qcp 특성의 분포와 의미)
    3. Target_F 분포 특성 (범위, 평균, 표준편차의 의미와 해석)
    4. 데이터 품질 평가 (결측치, 이상치 등)
    5. 종합 평가 및 시사점

    각 섹션은 ### 헤더로 구분하고, 중요한 수치나 인사이트는 **볼드체**로 강조해주세요.

    ## 통계학을 전혀 몰라도 이해 가능하도록 쉬운 용어와 예를 들어 설명해주세요
    ## 2차 전지 양극제 제조업 관점에서 업무에 도움이 되는 쉬운 용어를 사용해주세요
    ## Target_F 는 양극제 품질을 결정하는 반가폭 지표
    ## Li, Pre_L, Pre_S 변수는 양극재 생산을 위한 전도체의 성분
    ## Qcp 변수는 양극재 생산 설비의 IoT 센서 데이터
    """

    try:
        # 분석 UI 표시 및 처리
        is_running = display_analysis_ui(
            prompt=prompt,
            button_label="데이터 분석 시작",
            key_prefix="analysis",
            info_message="AI 분석을 실행하려면 '데이터 분석 시작' 버튼을 클릭하세요."
        )

        # 분석 실행 중인 경우
        if is_running:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                metadata_placeholder = st.empty()

                with st.spinner("AI가 데이터를 분석하고 있습니다..."):
                    # AI 분석 실행
                    generate_ai_analysis(
                        prompt=prompt,
                        key_prefix="analysis",
                        message_placeholder=message_placeholder,
                        metadata_placeholder=metadata_placeholder
                    )

    except Exception as e:
        st.error(f"AI 분석 요약 생성 중 오류가 발생했습니다: {str(e)}")