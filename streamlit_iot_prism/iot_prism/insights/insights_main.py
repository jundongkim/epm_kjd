import streamlit as st
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style, apply_graph_themes
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
from .insights_ui import render_insights_generation_tab, render_visualization_history_tab, render_questions_answers_tab
from .insights_plotly_style import apply_insights_plotly_style


def render_insights_ui(df):
    """IoT 데이터에 대한 종합 인사이트를 생성하고 표시하는 기능"""
    # 스타일 적용
    load_iot_font_css()
    apply_custom_style()
    apply_graph_themes()
    
    # 세션 상태 초기화 (AI 분석용) - 먼저 AI 설정 초기화
    init_ai_settings()
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    st.title("📊 종합 인사이트 리포트")
    st.markdown("현재 데이터와 세션 정보를 기반으로 종합 분석 및 인사이트를 생성합니다.")
    
    # 세션 상태 초기화
    if "insights_analysis_cache" not in st.session_state:
        st.session_state.insights_analysis_cache = {}
    if "insights_analysis_running" not in st.session_state:
        st.session_state.insights_analysis_running = False
    if "insights_analysis_history" not in st.session_state:
        st.session_state.insights_analysis_history = []
    if "insights_report_generated" not in st.session_state:
        st.session_state.insights_report_generated = False
    if "insights_questions" not in st.session_state:
        st.session_state.insights_questions = []
    if "insights_answers" not in st.session_state:
        st.session_state.insights_answers = []
    
    # 장비 및 센서 정보
    equipment_type = get_equipment_type()
    sensor_type = get_sensor_type()
    
    # 기본 데이터 검증 및 정보 표시
    if df is None or len(df) == 0:
        st.error("분석할 데이터가 없습니다. 먼저 데이터를 생성하거나 로드해주세요.")
        return
    
    # 데이터 기본 정보 표시
    show_basic_data_info(df, equipment_type, sensor_type)
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["인사이트 생성", "시각화 기록", "질문 및 답변"])
    
    with tab1:
        render_insights_generation_tab(df, equipment_type, sensor_type)
    
    with tab2:
        render_visualization_history_tab()
    
    with tab3:
        render_questions_answers_tab(df, equipment_type, sensor_type)


def show_basic_data_info(df, equipment_type, sensor_type):
    """데이터 기본 정보를 표시하는 함수"""
    import plotly.graph_objects as go
    import numpy as np
    
    st.subheader("데이터 기본 정보")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("데이터 크기", f"{len(df):,}행")
    with col2:
        st.metric("설비 유형", equipment_type)
    with col3:
        st.metric("센서 유형", sensor_type)
    with col4:
        time_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
        time_range_str = f"{time_range / 86400:.1f}일"
        st.metric("시간 범위", time_range_str)
        
    # 데이터 개요 그래프 추가 (샘플 데이터 사용)
    with st.expander("데이터 개요 시각화", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # 시계열 미리보기 생성
            # 샘플링된 데이터 사용 (최대 1000개 포인트)
            if len(df) > 1000:
                step = len(df) // 1000
                df_sample = df.iloc[::step].copy()
            else:
                df_sample = df.copy()
            
            # 인사이트용 선 차트 생성
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df_sample['timestamp'],
                    y=df_sample[sensor_type],
                    mode='lines',
                    name=sensor_type
                )
            )
            
            # 레이아웃 설정
            fig.update_layout(
                title=f"{equipment_type} {sensor_type} 시계열 데이터 미리보기",
                xaxis_title="시간",
                yaxis_title=sensor_type,
                height=300
            )
            
            # 스타일 적용
            apply_insights_plotly_style(fig)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 히스토그램 미리보기 생성
            fig = go.Figure()
            fig.add_trace(
                go.Histogram(
                    x=df_sample[sensor_type],
                    nbinsx=30,
                    name=sensor_type,
                    marker_color='rgba(25, 118, 210, 0.6)'
                )
            )
            
            # 레이아웃 설정
            fig.update_layout(
                title=f"{sensor_type} 분포 히스토그램",
                xaxis_title=sensor_type,
                yaxis_title="빈도",
                height=300
            )
            
            # 스타일 적용
            apply_insights_plotly_style(fig)
            st.plotly_chart(fig, use_container_width=True) 