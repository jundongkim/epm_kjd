import streamlit as st
import os
import base64
import logging
import matplotlib.pyplot as plt
import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px

# 로깅 설정
logger = logging.getLogger(__name__)

# DX-AI IoT Prism 로고 색상 기반 팔레트
PRISM_COLORS = {
    'light_blue': '#26A9E0',  # 밝은 파란색
    'dark_blue': '#164193',   # 진한 파란색
    'orange': '#F15A29',      # 주황색
    'light_gray': '#f0f5f9',  # 연한 회색
    'text': '#333333',        # 텍스트 색상
    # 확장 팔레트
    'blue_light': '#61c6ea',  # 밝은 파란색 파생
    'blue_dark_light': '#3a5eab',  # 진한 파란색 파생
    'orange_light': '#f7876a', # 주황색 파생
    'green': '#00a28a',       # 보조 색상
    'red': '#e53935',         # 보조 색상
    'yellow': '#ffb300',      # 보조 색상
    'purple': '#8e24aa',      # 보조 색상
}

# 시퀀셜 색상 팔레트 (그래프에서 데이터 시리즈를 위한 색상)
PRISM_SEQUENTIAL = [
    PRISM_COLORS['dark_blue'],
    PRISM_COLORS['light_blue'],
    PRISM_COLORS['orange'],
    PRISM_COLORS['blue_dark_light'],
    PRISM_COLORS['blue_light'],
    PRISM_COLORS['orange_light'],
    PRISM_COLORS['green'],
    PRISM_COLORS['red'],
    PRISM_COLORS['yellow'],
    PRISM_COLORS['purple'],
]

def configure_matplotlib_theme():
    """Matplotlib 테마 설정"""
    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=PRISM_SEQUENTIAL)
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['text.color'] = PRISM_COLORS['text']
    plt.rcParams['axes.labelcolor'] = PRISM_COLORS['dark_blue']
    plt.rcParams['xtick.color'] = PRISM_COLORS['text']
    plt.rcParams['ytick.color'] = PRISM_COLORS['text']
    plt.rcParams['grid.color'] = PRISM_COLORS['light_gray']
    plt.rcParams['font.family'] = 'Noto Sans KR'

def configure_plotly_theme():
    """Plotly 테마 설정"""
    # 커스텀 템플릿 생성
    prism_template = go.layout.Template()

    # 기본 색상 설정
    prism_template.layout.colorway = PRISM_SEQUENTIAL

    # 레이아웃 설정
    prism_template.layout.plot_bgcolor = 'white'
    prism_template.layout.paper_bgcolor = 'white'
    prism_template.layout.font = dict(color=PRISM_COLORS['text'], family='Noto Sans KR')
    prism_template.layout.title = dict(font=dict(color=PRISM_COLORS['dark_blue'], size=20))

    # X축, Y축 설정
    axis_template = dict(
        gridcolor=PRISM_COLORS['light_gray'],
        linecolor=PRISM_COLORS['text'],
        linewidth=1,
        title=dict(font=dict(color=PRISM_COLORS['dark_blue']))
    )
    prism_template.layout.xaxis = axis_template
    prism_template.layout.yaxis = axis_template

    # 템플릿 등록
    pio.templates['prism'] = prism_template
    pio.templates.default = 'prism'

    # Plotly Express 기본 색상 설정
    px.defaults.color_discrete_sequence = PRISM_SEQUENTIAL
    px.defaults.color_continuous_scale = [
        [0, PRISM_COLORS['light_blue']],
        [0.5, PRISM_COLORS['blue_dark_light']],
        [1, PRISM_COLORS['dark_blue']]
    ]

def apply_graph_themes():
    """모든 그래프 라이브러리에 테마 적용"""
    configure_matplotlib_theme()
    configure_plotly_theme()

def load_iot_font_css():
    """iot 패키지 전용 폰트 CSS 적용 (iot/fonts/Paperlogy.ttf 사용)"""
    # iot 디렉토리 내의 폰트 경로
    font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "Paperlogy.ttf")
    
    if not os.path.exists(font_path):
        logger.warning(f"폰트 파일을 찾을 수 없습니다: {font_path}")
        # 폰트 파일이 없는 경우 웹 폰트 사용
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

        * {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        /* 모든 텍스트 요소에 강제 적용 */
        p, h1, h2, h3, h4, h5, h6, div, span, button, a, input, textarea, select, label, code {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        </style>
        """, unsafe_allow_html=True)
        return

    try:
        # 폰트 파일을 base64로 인코딩
        with open(font_path, "rb") as font_file:
            encoded_font = base64.b64encode(font_file.read()).decode()
        
        # CSS에 폰트 적용
        custom_css = f"""
        @font-face {{
            font-family: 'Paperlogy';
            src: url(data:font/ttf;base64,{encoded_font});
            font-weight: normal;
            font-style: normal;
        }}

        * {{
            font-family: 'Paperlogy', sans-serif !important;
        }}

        /* 모든 텍스트 요소에 강제 적용 */
        p, h1, h2, h3, h4, h5, h6, div, span, button, a, input, textarea, select, label, code {{
            font-family: 'Paperlogy', sans-serif !important;
        }}

        """
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
        logger.info("Paperlogy 폰트가 성공적으로 적용되었습니다.")
    except Exception as e:
        logger.error(f"폰트 적용 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본 웹 폰트 사용
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

        * {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        /* 모든 텍스트 요소에 강제 적용 */
        p, h1, h2, h3, h4, h5, h6, div, span, button, a, input, textarea, select, label, code {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        </style>
        """, unsafe_allow_html=True)

def get_font_path():
    """iot 패키지의 폰트 경로를 반환합니다."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "Paperlogy.ttf")

def apply_custom_style():
    """대시보드에 적용할 커스텀 스타일 CSS"""
    st.markdown("""
    <style>
    /* DX-AI IoT Prism 로고 기반 색상 변수 */
    :root {
        --prism-light-blue: #26A9E0;  /* 밝은 파란색 */
        --prism-dark-blue: #164193;   /* 진한 파란색 */
        --prism-dark-blue-light: #2752A4;   /* 진한 파란색 - 조금 더 밝게 */
        --prism-orange: #F15A29;      /* 주황색 */
        --prism-background: #fafcfe;  /* 배경색 */
        --prism-light-gray: #f0f5f9;  /* 연한 회색 */
        --prism-text: #333333;        /* 텍스트 색상 */
    }

    /* 전체 배경 및 레이아웃 스타일 */
    .main {
        background-color: var(--prism-background);
    }

    .main .block-container {
        padding-top: 0;
        max-width: 100%;
    }

    /* 상단 고정 헤더 스타일 */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        z-index: 999;
        padding: 0.5rem 2rem;
        border-bottom: 1px solid var(--prism-light-blue);
    }

    /* 헤더 내부 컨텐츠 스타일 */
    .header-content {
        display: flex;
        align-items: center;
    }

    .header-content img {
        max-height: 60px;
        margin-right: 20px;
    }

    /* 하단 고정 푸터 스타일 */
    .fixed-footer {
        text-align: center;
        margin-top: 2rem;
        padding: 1rem 0;
        border-top: 1px solid var(--prism-light-blue);
        color: var(--prism-dark-blue);
        font-size: 0.8rem;
    }

    /* 데이터 테이블 스타일 */
    .dataframe {
        width: 100%;
        border-collapse: collapse;
        background-color: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(5px);
    }

    .dataframe th {
        background-color: var(--prism-dark-blue);
        color: white;
        font-weight: 600;
        text-align: left;
        padding: 0.75rem;
        border-bottom: 1px solid #e5e7eb;
    }

    .dataframe td {
        padding: 0.75rem;
        border-bottom: 1px solid #e5e7eb;
    }

    .dataframe tr:hover {
        background-color: var(--prism-light-gray);
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(230, 242, 245, 0.7);
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--prism-dark-blue);
        color: white;
    }

    /* 카드 스타일 */
    .card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(5px);
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 3px solid var(--prism-light-blue);
    }

    /* 메트릭 스타일 */
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        background: rgba(249, 250, 251, 0.7);
        backdrop-filter: blur(5px);
        border-radius: 8px;
        padding: 1rem;
        flex: 1;
        min-width: 180px;
        border-bottom: 3px solid var(--prism-orange);
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--prism-dark-blue);
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--prism-text);
        margin-top: 0.25rem;
    }

    /* 위젯 스타일 */
    div[data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(5px);
        border-radius: 8px;
    }

    /* 스트림릿 버튼 스타일 */
    .stButton > button {
        background-color: var(--prism-light-blue);
        color: white;
        border: none;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        background-color: var(--prism-dark-blue);
        color: white;
    }

    /* 중요 버튼 스타일 */
    .stButton > button[kind="primary"] {
        background-color: var(--prism-dark-blue);
        color: white;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: var(--prism-dark-blue-light);
        color: white;
    }

    /* 슬라이더 스타일 */
    .stSlider div[data-baseweb="slider"] > div {
        background-color: var(--prism-light-gray);
    }

    .stSlider div[data-baseweb="slider"] > div > div > div {
        background-color: var(--prism-dark-blue);
    }

    /* 반응형 조정 - 사이드바 토글 시 */
    @media (max-width: 992px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True) 