import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ..utils.style import load_iot_font_css, apply_custom_style, apply_graph_themes
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings  # AI 설정 관련 기능 추가

# 분리된 모듈 import
from .guide_data import ANALYSIS_RECOMMENDATIONS, analyze_data_characteristics
from .guide_ui import render_recommendation_card, render_analysis_flow_chart, apply_custom_font
from .guide_ai import render_ai_analysis

def render_visualization_guide_ui(df_processed):
    """시각화 가이드 UI를 랜더링합니다"""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 설정 초기화 및 메뉴 표시
    init_ai_settings()
    render_ai_settings_ui()
    
    st.header("IoT 데이터 분석 가이드")
    
    # 안내 메시지
    st.markdown("""
    이 가이드는 IoT 센서 데이터를 효과적으로 분석하기 위한 추천 시각화 방법과 순서를 제공합니다.
    데이터의 특성을 자동으로 분석하여 최적의 분석 경로를 제안합니다.
    """)
    
    # 데이터 특성 분석
    with st.spinner("데이터 특성 분석 중..."):
        recommendations, df_info = analyze_data_characteristics(df_processed)
    
    # 기본 데이터 정보 표시
    st.subheader("데이터 특성 요약")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("데이터 크기", f"{df_info.get('data_size', 'N/A'):,} 포인트")
        st.metric("평균값", f"{df_info.get('mean', 'N/A'):.2f}")
    with col2:
        st.metric("최소값", f"{df_info.get('min', 'N/A'):.2f}")
        st.metric("최대값", f"{df_info.get('max', 'N/A'):.2f}")
    with col3:
        st.metric("표준편차", f"{df_info.get('std', 'N/A'):.2f}")
        st.metric("변동계수(CV)", f"{df_info.get('cv', 'N/A'):.2f}")
    
    additional_info = [
        f"시계열 데이터: {'예' if df_info.get('is_time_series', False) else '아니오'}",
        f"정규분포 여부: {'예' if df_info.get('is_normal', False) else '아니오'}",
        f"이상치 비율: {df_info.get('outliers_ratio', 0)*100:.2f}%",
        f"주기성 감지: {'감지됨' if df_info.get('has_periodicity', False) else '감지되지 않음'}"
    ]
    
    st.markdown("**추가 특성:**\n- " + "\n- ".join(additional_info))
    
    # 탭으로 내용 구성
    tab1, tab2, tab3 = st.tabs(["추천 분석 순서", "분석 흐름도", "AI 분석 추천"])
    
    with tab1:
        st.subheader("자동 추천 분석 순서")
        
        if recommendations:
            # 시각화 타입과 메뉴 매핑
            visualization_menu_mapping = {
                "시계열 차트": "시계열 차트",
                "시계열 플롯": "시계열 차트",
                "이동 평균선": "시계열 차트",
                "히스토그램": "히스토그램",
                "확률 분포": "히스토그램",
                "정규분포 비교": "히스토그램",
                "박스 플롯": "박스 플롯",
                "박스 다이어그램": "박스 플롯",
                "히트맵": "히트맵",
                "주파수 분석": "주파수 분석(FFT)",
                "FFT": "주파수 분석(FFT)",
                "시간-주파수 분석": "시간-주파수 분석",
                "웨이블릿 분석": "시간-주파수 분석",
                "클러스터링": "패턴 클러스터링",
                "패턴 클러스터링": "패턴 클러스터링",
                "상관관계": "상관관계 분석",
                "상관 분석": "상관관계 분석",
                "분포 비교": "분포 비교",
                "이상치": "이상치 분석",
                "이상치 분석": "이상치 분석",
                "3D 시각화": "3D 데이터 시각화",
                "3D 플롯": "3D 데이터 시각화",
                "경보": "경보 및 임계값 설정",
                "임계값": "경보 및 임계값 설정",
                "QQ플롯": "분포 비교",
                "바이올린 플롯": "분포 비교",
                "산점도": "상관관계 분석",
                "일별 패턴": "일별/시간별 패턴",
                "시간별 패턴": "일별/시간별 패턴",
                "추세 분석": "트렌드 분석",
                "트렌드 분석": "트렌드 분석"
            }
            
            # 파스텔 톤 컬러 팔레트
            rainbow_pastel_colors = [
                "#FFB3BA",  # Pastel Red
                "#FFDFBA",  # Pastel Orange
                "#FDFD96",  # Pastel Yellow
                "#B5EAD7",  # Pastel Green
                "#A7C7E7",  # Pastel Blue
                "#DDBAFF",  # Pastel Indigo/Purple
                "#E0BAFF"   # Pastel Violet
            ]
            
            # 각 추천 항목마다 렌더링
            for i, rec in enumerate(recommendations):
                card_color = rainbow_pastel_colors[i % len(rainbow_pastel_colors)]
                
                # 카드 스타일의 컨테이너
                with st.container():
                    # 카드 헤더
                    st.markdown(
                        f"""
                        <div style="background-color: {card_color}; padding: 10px; border-radius: 5px 5px 0 0; 
                                 display: flex; align-items: center;">
                            <div style="background: rgba(255,255,255,0.5); width: 30px; height: 30px; border-radius: 50%; 
                                     display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                                <span style="font-weight: bold; font-size: 18px;">{i+1}</span>
                            </div>
                            <span style="font-weight: bold; font-size: 18px;">{rec['목적']}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    # 추천 이유와 분석 인사이트 통합
                    insight_text = ""
                    if "추가 설명" in rec:
                        insight_text = f"<br><br><strong>분석 인사이트:</strong><br>{rec['추가 설명']}"
                    
                    st.markdown(
                        f"""
                        <div style="background-color: #f9f9f9; padding: 10px; border-left: 5px solid {card_color}; margin-bottom: 10px;">
                            <strong>추천 이유:</strong> {rec['추천 이유']}{insight_text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # 각 시각화 항목을 버튼으로 표시
                    for viz_type in rec['추천 시각화']:
                        # 시각화 메뉴와 매핑 확인
                        menu_value = None
                        for key, value in visualization_menu_mapping.items():
                            if key in viz_type:
                                menu_value = value
                                break
                        
                        # 기본값이 없는 경우
                        if menu_value is None:
                            menu_value = "시각화 가이드"  # 기본값
                        
                        # 시각화 유형에 따른 아이콘 결정
                        if "시계열" in viz_type:
                            icon = "📈"
                        elif "히스토그램" in viz_type:
                            icon = "📊"
                        elif "박스" in viz_type:
                            icon = "📦"
                        elif "히트맵" in viz_type:
                            icon = "🎨"
                        elif "주파수" in viz_type or "FFT" in viz_type:
                            icon = "〰️"
                        elif "클러스터링" in viz_type:
                            icon = "🔄"
                        elif "상관관계" in viz_type:
                            icon = "🔗"
                        elif "분포" in viz_type:
                            icon = "📉"
                        elif "이상치" in viz_type:
                            icon = "⚠️"
                        elif "3D" in viz_type:
                            icon = "🧊"
                        elif "경보" in viz_type or "임계값" in viz_type:
                            icon = "🔔"
                        elif "QQ" in viz_type:
                            icon = "📏"
                        elif "바이올린" in viz_type:
                            icon = "🎻"
                        elif "산점도" in viz_type:
                            icon = "🔹"
                        else:
                            icon = "📊"  # 기본 아이콘
                        
                        # 시각화 항목을 버튼으로 표시
                        viz_details = next((item for item in ANALYSIS_RECOMMENDATIONS.get(rec['목적'], []) 
                                          if item['type'] == viz_type), None)
                        
                        # 버튼 컬러
                        button_color = card_color
                        
                        # 저장 키 생성 (고유한 키 필요)
                        button_key = f"viz_button_{i}_{viz_type.replace(' ', '_')}"
                        
                        # 설명 텍스트 설정
                        description = viz_details['description'] if viz_details and 'description' in viz_details else "데이터 특성을 시각적으로 분석"
                        
                        # 버튼 생성
                        col1, col2 = st.columns([2, 3])
                        with col1:
                            if st.button(f"{icon} {viz_type}", key=button_key, help=description, use_container_width=True):
                                # 버튼 클릭 시 세션 상태 업데이트
                                st.session_state.selected_viz_from_button = menu_value
                                st.rerun()
                        with col2:
                            st.markdown(f"<small>{description}</small>", unsafe_allow_html=True)
                    
                    # 카드 간 구분선
                    st.markdown("---")
        else:
            st.warning("분석 추천을 생성할 수 없습니다. 데이터를 확인해주세요.")
    
    with tab2:
        st.subheader("분석 흐름도")
        
        if recommendations:
            flow_chart_html = render_analysis_flow_chart(recommendations)
            if flow_chart_html:
                st.components.v1.html(flow_chart_html, height=550)
            else:
                st.warning("분석 흐름도를 생성할 수 없습니다.")
        else:
            st.warning("분석 추천이 없어 흐름도를 생성할 수 없습니다.")
    
    with tab3:
        # AI 분석 섹션
        render_ai_analysis(df_processed, recommendations, df_info) 