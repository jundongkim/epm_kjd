"""
DX-AI Manufacturing Copilot - 스타일링 모듈

CSS 스타일링과 UI 관련 함수들을 관리합니다.
"""

import streamlit as st
from src.utils.font_utils import apply_paperlogy_font


def get_page_config():
    """Streamlit 페이지 설정 반환"""
    return {
        "page_title": "DX-AI Manufacturing Copilot",
        "page_icon": "🤖",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
        "menu_items": {
            'Get Help': None,
            'Report a bug': None,
            'About': """
            # DX-AI Manufacturing Copilot
            
            스마트 제조 공정 관리를 위한 AI 솔루션
            
            **주요 기능:**
            - 🔢 가상 데이터 생성
            - ⚙️ 프로세스 관리 
            - 🧪 제품 개발
            - 💰 원가 관리
            
            **기술 스택:**
            - Frontend: Streamlit
            - AI/ML: LangChain, LangGraph
            - Backend: FastAPI
            - 의존성: Poetry
            """
        }
    }


def load_custom_css():
    """커스텀 CSS 스타일 로드 및 Paperlogy 폰트 적용"""
    # Paperlogy 폰트 적용
    apply_paperlogy_font()
    
    # 나머지 CSS 스타일 적용
    css = """
    <style>
    
    /* 메인 컨테이너 스타일링 */
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #4a90e2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* 네비게이션 스타일 */
    .nav-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    
    /* 카드 스타일 */
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .feature-card h3 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
        font-size: 1.3rem;
    }
    
    /* 메트릭 스타일 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        background-color: #f0f2f6;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(90deg, #1f77b4 0%, #4a90e2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* 데이터프레임 스타일 */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 알림 박스 */
    .alert-info {
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
        border-radius: 4px;
        padding: 1rem;
        margin: 1rem 0;
        color: #1565c0;
    }
    
    .alert-success {
        background-color: #e8f5e8;
        border: 1px solid #c8e6c9;
        border-radius: 4px;
        padding: 1rem;
        margin: 1rem 0;
        color: #2e7d32;
    }
    
    .alert-warning {
        background-color: #fff3e0;
        border: 1px solid #ffcc02;
        border-radius: 4px;
        padding: 1rem;
        margin: 1rem 0;
        color: #ef6c00;
    }
    
    /* 로딩 애니메이션 */
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #1f77b4;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 레스폰시브 디자인 */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }
        
        .feature-card {
            padding: 1rem;
        }
    }
    
    /* 차트 컨테이너 */
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* 상태 표시기 */
    .status-online {
        color: #4caf50;
        font-weight: bold;
    }
    
    .status-offline {
        color: #f44336;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def create_main_header():
    """메인 헤더 생성"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 DX-AI Manufacturing Copilot</h1>
        <p>스마트 제조 공정 관리를 위한 AI 솔루션</p>
    </div>
    """, unsafe_allow_html=True) 