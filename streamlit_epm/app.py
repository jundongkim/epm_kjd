"""
DX-AI Manufacturing Copilot - 메인 애플리케이션

스마트 제조 공정 관리를 위한 AI 솔루션 메인 진입점
"""

import streamlit as st

# 패키지 모듈 import
from src.ui import load_custom_css, get_page_config, create_main_header
from src.pages import (
    main_home,
    data_generation_page,
    process_management_page,
    product_data_analysis_page,
    product_modeling_page,
    experimental_design_page,
    cost_management_page,
    show_ai_report_page
)


def main():
    """메인 애플리케이션 함수"""
    
    # 페이지 설정
    page_config = get_page_config()
    st.set_page_config(**page_config)
    
    # 커스텀 CSS 로드
    load_custom_css()
    
    # 사이드바 네비게이션
    st.sidebar.title("📋 메뉴")
    
    # 페이지 선택
    page_selection = st.sidebar.selectbox(
        "페이지 선택",
        [
            "🏠 홈",
            "📊 데이터 생성", 
            "🔬 실험 설계",
            "🧪 제품 개발 - 📊 데이터 분석",
            "🧪 제품 개발 - 🤖 예측 모델링",
            "⚙️ 프로세스 관리",
            "💰 원가 관리",
            "🤖 AI 보고서 생성"
        ]
    )
    
    # 홈페이지가 아닐 때만 공통 헤더 표시
    if page_selection != "🏠 홈":
        create_main_header()
    
    # 페이지 라우팅
    if page_selection == "🏠 홈":
        main_home()
    elif page_selection == "📊 데이터 생성":
        data_generation_page()
    elif page_selection == "🔬 실험 설계":
        experimental_design_page()
    elif page_selection == "🧪 제품 개발 - 📊 데이터 분석":
        product_data_analysis_page()
    elif page_selection == "🧪 제품 개발 - 🤖 예측 모델링":
        product_modeling_page()
    elif page_selection == "⚙️ 프로세스 관리":
        process_management_page()
    elif page_selection == "💰 원가 관리":
        cost_management_page()
    elif page_selection == "🤖 AI 보고서 생성":
        show_ai_report_page()
    
    # 사이드바 정보
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 시스템 정보")
    st.sidebar.markdown("**버전**: v1.0.0")
    st.sidebar.markdown("**환경**: 프로토타입")
    st.sidebar.markdown("**상태**: 🟢 정상 운영")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📞 지원")
    st.sidebar.markdown("**📧 이메일**: support@manufacturing-copilot.com")
    st.sidebar.markdown("**📚 문서**: [Wiki](https://docs.manufacturing-copilot.com)")


if __name__ == "__main__":
    main() 