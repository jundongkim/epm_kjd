import streamlit as st
# 페이지 설정 - 반드시 첫 번째 Streamlit 명령어로 실행
st.set_page_config(
    page_title="DX-AI iDSB (InteractiveDashboard)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",  # 사이드바를 기본적으로 확장
)

import os
import base64
from pathlib import Path
import pandas as pd

# 유틸리티 모듈 임포트
from utils.data_loader import load_data, load_visualization_files
from utils.style import load_font_css, apply_custom_style, apply_graph_themes, ECOPRO_COLORS
from models.model_loader import load_catboost_model, load_xgboost_booster

# 컴포넌트 모듈 임포트
from components.fwhm.fwhm_data_overview import show_data_overview
from components.fwhm.fwhm_feature_analysis import show_feature_analysis
from components.fwhm.fwhm_model_results import show_model_results
from components.fwhm.fwhm_visualization_gallery import show_visualization_gallery
from components.fwhm.fwhm_simulation import show_simulation
from components.fwhm.fwhm_xai_visualization import show_fwhm_xai_visualization
from components.sem_eds import show_sem_analysis, show_eds_analysis, show_operation_inference, show_equipment_inference
# ICP 관련 컴포넌트 임포트 (세분화된 파일)
from components.icp import show_icp_lot_analysis, show_icp_lot_visualization_gallery, show_icp_qcp_visualization_gallery, show_icp_model_results, show_icp_xai_visualization, show_icp_simulation
from components.chat_widget import configure_sidebar_chat
# CMMS 컴포넌트 임포트
from components.cmms import (
    show_cmms_maintenance, show_cmms_risk_assessment,
    show_cmms_chat, show_cmms_images, find_image_file,
    show_cmms_similar_search, show_cmms_statistics,
    show_cmms_semantic_analysis,
    # 데이터 로더 함수들
    load_cmms_data, load_or_create_vector_db as load_or_create_cmms_vector_db
)
# 랜딩 페이지 컴포넌트 임포트
from components.landing_page import show_landing_page
# 공정관리이력 컴포넌트 임포트
from components.process import (
    show_process_chat,
    show_process_similar_search,
    load_process_data,
    load_or_create_vector_db as load_or_create_process_vector_db,
    show_process_reports
)
# 생산이슈리포트 컴포넌트 임포트
from components.prd import (
    show_prd_maintenance,
    show_prd_chat,
    show_prd_images,
    find_image_file as find_prd_image_file,
    show_prd_similar_search,
    show_prd_semantic_analysis,
    # 데이터 로더 함수들
    load_prd_data,
    load_or_create_vector_db as load_or_create_prd_vector_db
)

# Ollama 설정 정보 로그
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
print(f"Ollama API 서버 URL: {OLLAMA_BASE_URL}")

# 메뉴 구조 정의 (Level 1 메뉴 및 서브 탭)
LEVEL1_MENUS = {
    "홈": {
        "tabs": ["대시보드"],
        "components": [show_landing_page],
        "tab_indices": [15],  # 기본 탭
        "icon": "🏠",  # 집 아이콘
        "key": "home"
    },
    "공정관리": {
        "tabs": ["💬 채팅 인터페이스", "🔍 유사 케이스 검색", "📑 보고서 생성"],
        "components": [show_process_chat, show_process_similar_search, show_process_reports],
        "tab_indices": [19, 20, 21],  # 새로운 고유 인덱스 추가
        "icon": "🏭",  # 공장 아이콘
        "key": "process"
    },
    "생산관리": {
        "tabs": ["💬 채팅 인터페이스", "📸 보고서 갤러리", "🔍 유사 케이스 검색", "📊 유지보수", "🧠 의미론적 분석"],
        "components": [show_prd_chat, show_prd_images, show_prd_similar_search, show_prd_maintenance, show_prd_semantic_analysis],
        "tab_indices": [24, 25, 26, 27, 28],  # 새로운 고유 인덱스 추가
        "icon": "🏗️",  # 건설 아이콘
        "key": "prd"
    },
    "설비관리": {
        "tabs": ["💬 채팅 인터페이스", "📸 작업 이미지", "🔍 유사 케이스 검색", "📊 통계", "🧠 의미론적 분석"],
        "components": [show_cmms_chat, show_cmms_images, show_cmms_similar_search, show_cmms_statistics, show_cmms_semantic_analysis],
        "tab_indices": [14, 15, 16, 17, 18],
        "icon": "🛠️",  # 도구 아이콘
        "key": "cmms"
    },
    "SEM-EDS": {
        "tabs": ["🔬 SEM 분석", "🔍 EDS 분석", "⚡ 공정 조건 분석", "⚙️ 설비/부품 추정"],
        "components": [show_sem_analysis, show_eds_analysis, show_operation_inference, show_equipment_inference],
        "tab_indices": [11, 12, 13, 23],
        "icon": "🔬",  # 현미경 아이콘
        "key": "sem_eds"
    },
    "불량예측": {
        "tabs": ["🖼️ Lot 시각화 갤러리", "📈 Lot 데이터 분석", "🔍 QCP 시각화 갤러리", "📊 모델 결과", "🧠 XAI 분석", "🚀 시뮬레이션"],
        # "tabs": ["🖼️ Lot 시각화 갤러리", "📈 Lot 데이터 분석", "🔍 QCP 시각화 갤러리", "📊 모델 결과"],
        "components": [show_icp_lot_visualization_gallery, show_icp_lot_analysis, show_icp_qcp_visualization_gallery, show_icp_model_results, show_icp_xai_visualization, show_icp_simulation],
        # "components": [show_icp_lot_visualization_gallery, show_icp_lot_analysis, show_icp_qcp_visualization_gallery, show_icp_model_results],

        "tab_indices": [5, 6, 7, 8, 9, 10],
        "icon": "🧪",  # 화학 실험 아이콘
        "key": "icp"
    },
    "품질예측": {
        "tabs": ["📊 데이터 개요", "🔍 특성 분석", "📈 모델 결과", "🖼️ 시각화 갤러리", "🧠 XAI 분석", "🚀 시뮬레이션"],
        "components": [show_data_overview, show_feature_analysis, show_model_results,
                      show_visualization_gallery, show_fwhm_xai_visualization, show_simulation],
        "tab_indices": [0, 1, 2, 3, 22, 4],
        "icon": "📈",  # 차트 아이콘
        "key": "fwhm"
    }

}

# 현재 활성화된 Level-1 메뉴를 추적하기 위한 세션 상태 초기화
if "active_level1" not in st.session_state:
    st.session_state.active_level1 = "홈"

# 현재 활성화된 탭을 추적하기 위한 세션 상태 초기화
if "active_tab" not in st.session_state:
    # URL 매개변수 확인: tab 파라미터가 있으면 해당 값으로 초기화
    if 'tab' in st.query_params:
        try:
            tab_index = int(st.query_params['tab'])
            st.session_state.active_tab = tab_index

            # tab_index에 따라 active_level1 설정
            for level1, menu_data in LEVEL1_MENUS.items():
                if tab_index in menu_data["tab_indices"]:
                    st.session_state.active_level1 = level1
                    break
        except ValueError:
            st.session_state.active_tab = 15  # 홈페이지 탭 인덱스
            st.session_state.active_level1 = "홈"
    else:
        st.session_state.active_tab = 15  # 홈페이지 탭 인덱스
        st.session_state.active_level1 = "홈"

# Level-1 메뉴 변경 함수
def change_level1_menu(level1_menu):
    if st.session_state.active_level1 != level1_menu:
        st.session_state.active_level1 = level1_menu
        # 해당 Level-1 메뉴의 첫 번째 탭으로 활성 탭 설정
        st.session_state.active_tab = LEVEL1_MENUS[level1_menu]["tab_indices"][0]
        # URL 매개변수 업데이트
        st.query_params['tab'] = st.session_state.active_tab

# 탭 변경 함수 정의
def handle_tab_change(tab_index):
    if st.session_state.active_tab != tab_index:
        st.session_state.active_tab = tab_index
        # URL 매개변수 업데이트
        st.query_params['tab'] = tab_index

        # tab_index에 따라 active_level1 업데이트
        for level1, menu_data in LEVEL1_MENUS.items():
            if tab_index in menu_data["tab_indices"]:
                st.session_state.active_level1 = level1
                break

# 이미지를 base64로 인코딩하는 함수
def get_image_as_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# 스타일 적용
load_font_css()
apply_custom_style()
apply_graph_themes()  # 그래프 테마 적용

# 로고 파일 경로
logo_path = "logo/logo.png"
logo_base64 = get_image_as_base64(logo_path)

# 고정 헤더 추가 (로고 포함)
st.markdown(f"""
<style>
/* 헤더 고정 및 z-index 높게 설정 */
.fixed-header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background-color: rgba(255, 255, 255, 0.4);  /* 반투명 배경 */
    backdrop-filter: blur(12px);  /* 블러 효과 */
    -webkit-backdrop-filter: blur(12px);  /* Safari 지원 */
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 10px 20px;
    z-index: 1000;  /* 높은 z-index 값으로 사이드바 위에 오도록 함 */
}}

/* 사이드바를 헤더 아래로 위치시키기 위한 스타일 */
[data-testid="stSidebar"] {{
    z-index: 100;  /* 헤더보다 낮은 z-index */
    padding-top: 80px;  /* 헤더 높이만큼 패딩 추가 */
}}

/* 메인 컨텐츠 영역도 헤더 아래로 위치시키기 */
.main .block-container {{
    padding-top: 80px;
}}
</style>

<div class="fixed-header">
    <div class="header-content" style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{logo_base64}" alt="EcoPro BM Logo" style="height: 60px; margin-right: 20px;">
        <div>
            <h2 style="margin: 0; color: #164193; padding-top: 10px; padding-bottom: 5px;">DX-AI iDSB (Interactive Dashboard)</h2>
            <p style="margin: 0; color: #26A9E0; font-weight: 600; padding-bottom: 10px;">인터렉티브 제조업 데이터 분석 및 예측 시스템</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 헤더와 컨텐츠가 겹치지 않도록 빈 공간 추가는 더 이상 필요하지 않음
# 이미 CSS에서 padding-top으로 처리함

# 데이터 로드
df = load_data()
# vis_files = load_visualization_files()

# 모델 로딩 개선: 세션 상태의 데이터셋 선택을 먼저 확인
if 'selected_fwhm_dataset' not in st.session_state:
    st.session_state.selected_fwhm_dataset = 'F28'  # 초기값 설정

selected_dataset = st.session_state.selected_fwhm_dataset
model_dir = f"FWHM/models_cbm_{selected_dataset}"

# 데이터셋별 모델 로드 시도
model = load_catboost_model(model_dir)

# 초기 모델 로드 상태 메시지는 저장만 하고 표시하지 않음
model_load_status = ""
if model is None:
    # 기본 디렉토리 구조 시도
    legacy_model_dir = "FWHM/models_cbm"
    model = load_catboost_model(legacy_model_dir)

    if model is None:
        model_load_status = f"⚠️ 모델을 로드할 수 없습니다. 다음 경로를 확인: {model_dir} 또는 {legacy_model_dir}"
    else:
        model_load_status = f"ℹ️ 기본 디렉토리에서 CatBoost 모델 로드: {legacy_model_dir}"
else:
    model_load_status = f"✅ {selected_dataset} 데이터셋의 CatBoost 모델 로드 완료"

# 사이드바 메뉴 정의 (Level-1 메뉴)
with st.sidebar:
    st.markdown("""
    <style>
    /* 사이드바 메뉴 스타일 */
    .st-key-sidebar-menu {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    /* Streamlit 버튼 스타일 재정의 */
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
        font-size: 16px;
        padding: 12px 10px;
        transition: all 0.3s ease-in-out;
        border: none !important;
    }

    /* 비활성 메뉴 스타일 */
    .stButton > button[data-baseweb="button"][kind="secondary"] {
        background-color: rgba(22, 65, 147, 0.7) !important;
        color: white !important;
        border: none !important;
    }

    /* 활성 메뉴 스타일 */
    .stButton > button[data-baseweb="button"][kind="primary"] {
        background-color: #26A9E0 !important;
        color: white !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25) !important;
        border: none !important;
        filter: brightness(1.2) !important;
        transform: translateY(-2px) !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }

    /* 스트림릿이 추가하는 추가 래퍼에 대한 스타일 재정의 */
    div[data-testid="stVerticalBlock"] .stButton > button[data-baseweb="button"][kind="primary"] {
        background-color: #26A9E0 !important;
        color: white !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25) !important;
        filter: brightness(1.2) !important;
        transform: translateY(-2px) !important;
    }

    /* 호버 효과 */
    .stButton > button:hover {
        filter: brightness(1.25) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3) !important;
    }

    /* 프라이머리 버튼 호버 시 특별 효과 */
    .stButton > button[data-baseweb="button"][kind="primary"]:hover {
        background-color: #3DB5E6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Level-1 메뉴 생성
    with st.container(key="sidebar-menu", border=False):
        # 각 Level-1 메뉴 버튼 생성
        for menu_name in LEVEL1_MENUS.keys():
            is_active = menu_name == st.session_state.active_level1
            menu_icon = LEVEL1_MENUS[menu_name]["icon"]
            menu_key = LEVEL1_MENUS[menu_name]["key"]

            if st.button(f"{menu_icon} {menu_name}", key=f"sidebar-menu-{menu_key}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary"):
                change_level1_menu(menu_name)
                st.rerun()

    # --- FWHM 메뉴 선택 시 모델 선택 UI 추가 ---
    if st.session_state.active_level1 == "품질예측":
        st.markdown("<hr style='margin: 15px 0; opacity: 0.3;'>", unsafe_allow_html=True)

        # --- 데이터 셋 선택 옵션 추가 ---
        st.markdown("##### FWHM 대상 데이터 선택")
        # 데이터셋 선택을 위한 세션 상태 초기화
        if 'selected_fwhm_dataset' not in st.session_state:
            st.session_state.selected_fwhm_dataset = 'F28'  # 초기값

        # 폴더 내 가용한 데이터셋 파일 확인 (외부에서 변경될 수 있으므로 매번 확인)
        available_datasets = []
        for file in os.listdir("FWHM"):
            if file.startswith("normalized_data_F") and file.endswith(".csv"):
                # normalized_data_F28.csv에서 F28 부분만 추출
                dataset_name = file.replace("normalized_data_", "").replace(".csv", "")
                available_datasets.append(dataset_name)

        # 데이터셋이 없는 경우 기본 옵션 제공
        if not available_datasets:
            available_datasets = ['F28', 'F29', 'F30', 'F31']

        # 정렬하여 일관된 순서 유지
        available_datasets.sort()

        selected_fwhm_dataset_radio = st.radio(
            "분석/시뮬레이션에 사용할 데이터 셋 선택:",
            available_datasets,
            key='fwhm_dataset_radio',
            index=available_datasets.index(st.session_state.selected_fwhm_dataset) if st.session_state.selected_fwhm_dataset in available_datasets else 0,
            horizontal=True,
            label_visibility="collapsed"  # 라벨 숨김
        )

        # 라디오 버튼 값 변경 시 세션 상태 업데이트
        if selected_fwhm_dataset_radio != st.session_state.selected_fwhm_dataset:
            st.session_state.selected_fwhm_dataset = selected_fwhm_dataset_radio
            st.rerun()  # 데이터 다시 로드하기 위해 페이지 새로고침

        # 선택된 데이터셋에 따라 데이터 로드
        selected_fwhm_dataset = st.session_state.selected_fwhm_dataset
        data_path = f"FWHM/normalized_data_{selected_fwhm_dataset}.csv"

        # 데이터 로드 상태 표시
        if os.path.exists(data_path):
            st.sidebar.success(f"{selected_fwhm_dataset} 데이터셋 로드 완료.")
        else:
            st.sidebar.warning(f"{selected_fwhm_dataset} 데이터셋 파일을 찾을 수 없습니다.")

        st.markdown("<hr style='margin: 15px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        st.markdown("##### FWHM 모델 선택")
        # 세션 상태에 모델 선택 저장 및 변경 감지
        if 'selected_fwhm_model' not in st.session_state:
            st.session_state.selected_fwhm_model = 'CatBoost' # 초기값

        selected_fwhm_model_radio = st.radio(
            "분석/시뮬레이션에 사용할 모델 선택:",
            ('CatBoost', 'XGBoost'),
            key='fwhm_model_radio', # 위젯 식별 키
            index=0 if st.session_state.selected_fwhm_model == 'CatBoost' else 1, # 세션 상태 반영
            horizontal=True,
            label_visibility="collapsed" # 라벨 숨김
        )
        # 라디오 버튼 값 변경 시 세션 상태 업데이트
        if selected_fwhm_model_radio != st.session_state.selected_fwhm_model:
            st.session_state.selected_fwhm_model = selected_fwhm_model_radio
            st.rerun() # 모델 다시 로드하기 위해 페이지 새로고침

        # 선택된 모델과 데이터셋에 따라 경로 및 모델 로드
        selected_fwhm_model = st.session_state.selected_fwhm_model # 세션 값 사용
        selected_fwhm_dataset = st.session_state.selected_fwhm_dataset  # 데이터셋 값 사용

        if selected_fwhm_model == 'CatBoost':
            fwhm_model_dir = f"FWHM/models_cbm_{selected_fwhm_dataset}"
            fwhm_plot_dir = f"FWHM/plots_cbm_{selected_fwhm_dataset}"
            fwhm_model = load_catboost_model(fwhm_model_dir) # 디렉토리 경로만 전달
        elif selected_fwhm_model == 'XGBoost':
            fwhm_model_dir = f"FWHM/models_xgb_{selected_fwhm_dataset}"
            fwhm_plot_dir = f"FWHM/plots_xgb_{selected_fwhm_dataset}"
            fwhm_model = load_xgboost_booster(fwhm_model_dir) # XGBoost 모델 로드 라인 추가

        if fwhm_model is None:
            st.sidebar.warning(f"{selected_fwhm_dataset} {selected_fwhm_model} 모델 로드 실패. 해당 모델 파일이 있는지 확인하세요.")
        else:
            st.sidebar.success(f"{selected_fwhm_dataset} {selected_fwhm_model} 모델 로드 완료.")

    # 구분선 추가
    st.markdown("<hr style='margin: 30px 0 0; opacity: 0.3;'>", unsafe_allow_html=True)

    # 채팅창 높이 기본값을 600px로 설정 (원하는 값으로 변경 가능)
    configure_sidebar_chat(st.session_state.active_tab, chat_height=300)

# 현재 활성화된 Level-1 메뉴에 해당하는 탭만 표시
current_menu = LEVEL1_MENUS[st.session_state.active_level1]
current_tabs = current_menu["tabs"]
current_components = current_menu["components"]
current_tab_indices = current_menu["tab_indices"]

# FWHM 메뉴가 선택된 경우 선택된 데이터셋 로드
if st.session_state.active_level1 == "품질예측" and 'selected_fwhm_dataset' in st.session_state:
    # 선택된 데이터셋에 따라 데이터 로드
    data_path = f"FWHM/normalized_data_{st.session_state.selected_fwhm_dataset}.csv"
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        st.error(f"선택한 데이터셋 파일({data_path})을 찾을 수 없습니다.")

# CMMS 메뉴가 선택된 경우에만 CMMS 데이터 및 벡터 저장소 로드
if st.session_state.active_level1 == "설비관리":
    # CMMS 데이터 로드
    if "cmms_data" not in st.session_state:
        st.info("CMMS 데이터 로딩 중...")
        st.session_state.cmms_data = load_cmms_data()

    # 벡터 저장소 로드 또는 생성
    if "vector_store" not in st.session_state and st.session_state.cmms_data:
        with st.spinner("CMMS 벡터 DB 로딩 중... (처음 실행 시 시간이 다소 소요될 수 있습니다)"):
            st.session_state.vector_store = load_or_create_cmms_vector_db(st.session_state.cmms_data, vector_dir="CMMS/vector_db")
            if st.session_state.vector_store:
                st.success("CMMS 벡터 DB 로딩 완료!")
            else:
                st.error("CMMS 벡터 DB 로딩 실패. 데이터를 확인해주세요.")

# 공정관리이력 메뉴가 선택된 경우에만 공정관리이력 데이터 및 벡터 저장소 로드
elif st.session_state.active_level1 == "공정관리":
    # 공정관리이력 데이터 로드
    if "process_data" not in st.session_state:
        st.info("공정관리이력 데이터 로딩 중...")
        st.session_state.process_data = load_process_data()

    # 공정관리이력 데이터가 제대로 로드되었는지 확인
    if "process_data" in st.session_state and st.session_state.process_data:
        # 벡터 저장소 로드 또는 생성
        if "process_vector_store" not in st.session_state or st.session_state.process_vector_store is None:
            with st.spinner("공정관리이력 벡터 DB 로딩 중... (처음 실행 시 시간이 다소 소요될 수 있습니다)"):
                try:
                    st.session_state.process_vector_store = load_or_create_process_vector_db(st.session_state.process_data, vector_dir="PROCESS/vector_db")
                    if st.session_state.process_vector_store:
                        st.success("공정관리이력 벡터 DB 로딩 완료!")
                    else:
                        st.error("공정관리이력 벡터 DB 로딩 실패. 데이터를 확인해주세요.")
                except Exception as e:
                    st.error(f"벡터 DB 초기화 중 오류: {str(e)}")

        # 사이드바에 벡터 DB 상태 및 재설정 버튼 추가
        with st.sidebar.expander("공정관리이력 벡터 DB 상태", expanded=False):
            st.info(f"공정관리이력 데이터: {len(st.session_state.process_data)}건 로드됨")
            if "process_vector_store" in st.session_state and st.session_state.process_vector_store:
                st.success("벡터 DB가 준비되었습니다.")
            else:
                st.warning("벡터 DB가 초기화되지 않았습니다.")

            # 벡터 DB 재설정 버튼
            if st.button("벡터 DB 재설정", key="app_process_vector_db_reset_btn"):
                if "process_vector_store" in st.session_state:
                    del st.session_state.process_vector_store
                try:
                    with st.spinner("공정관리이력 벡터 DB 재생성 중..."):
                        vector_store = load_or_create_process_vector_db(st.session_state.process_data)
                        if vector_store:
                            st.session_state.process_vector_store = vector_store
                            st.success("벡터 DB 재설정 완료")
                        else:
                            st.error("벡터 DB 생성 실패")
                except Exception as e:
                    st.error(f"벡터 DB 재설정 중 오류: {str(e)}")
    else:
        st.error("공정관리이력 데이터를 로드할 수 없습니다. 데이터 파일이 있는지 확인해주세요.")

# 생산이슈리포트 메뉴가 선택된 경우에만 생산이슈리포트 데이터 및 벡터 저장소 로드
elif st.session_state.active_level1 == "생산관리":
    # 생산이슈리포트 데이터 로드
    if "prd_data" not in st.session_state:
        st.info("생산이슈리포트 데이터 로딩 중...")
        st.session_state.prd_data = load_prd_data()

    # 생산이슈리포트 데이터가 제대로 로드되었는지 확인
    if "prd_data" in st.session_state and st.session_state.prd_data:
        # 벡터 저장소 로드 또는 생성
        if "prd_vector_store" not in st.session_state or st.session_state.prd_vector_store is None:
            with st.spinner("생산이슈리포트 벡터 DB 로딩 중... (처음 실행 시 시간이 다소 소요될 수 있습니다)"):
                try:
                    st.session_state.prd_vector_store = load_or_create_prd_vector_db(st.session_state.prd_data, vector_dir="PRD/vector_db")
                    if st.session_state.prd_vector_store:
                        st.success("생산이슈리포트 벡터 DB 로딩 완료!")
                    else:
                        st.error("생산이슈리포트 벡터 DB 로딩 실패. 데이터를 확인해주세요.")
                except Exception as e:
                    st.error(f"벡터 DB 초기화 중 오류: {str(e)}")

        # 사이드바에 벡터 DB 상태 및 재설정 버튼 추가
        with st.sidebar.expander("생산이슈리포트 벡터 DB 상태", expanded=False):
            st.info(f"생산이슈리포트 데이터: {len(st.session_state.prd_data)}건 로드됨")
            if "prd_vector_store" in st.session_state and st.session_state.prd_vector_store:
                st.success("벡터 DB가 준비되었습니다.")
            else:
                st.warning("벡터 DB가 초기화되지 않았습니다.")

            # 벡터 DB 재설정 버튼
            if st.button("벡터 DB 재설정", key="app_prd_vector_db_reset_btn"):
                if "prd_vector_store" in st.session_state:
                    del st.session_state.prd_vector_store
                try:
                    with st.spinner("생산이슈리포트 벡터 DB 재생성 중..."):
                        vector_store = load_or_create_prd_vector_db(st.session_state.prd_data)
                        if vector_store:
                            st.session_state.prd_vector_store = vector_store
                            st.success("벡터 DB 재설정 완료")
                        else:
                            st.error("벡터 DB 생성 실패")
                except Exception as e:
                    st.error(f"벡터 DB 재설정 중 오류: {str(e)}")
    else:
        st.error("생산이슈리포트 데이터를 로드할 수 없습니다. 데이터 파일이 있는지 확인해주세요.")

# 탭 스타일 개선
st.markdown("""
<style>
/* 탭 컨테이너 스타일 */
.stTabs {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

/* 탭 버튼 스타일 */
button[role="tab"] {
    font-size: 15px !important;
    font-weight: 500 !important;
    padding: 5px 15px !important;
}

/* 선택된 탭 스타일 */
button[role="tab"][aria-selected="true"] {
    color: #26A9E0 !important;
    font-weight: 600 !important;
    box-shadow: 0 -2px 0 #26A9E0 inset !important;
}

/* 탭 컨텐츠 스타일 */
[role="tabpanel"] {
    padding: 15px 5px !important;
}
</style>
""", unsafe_allow_html=True)

# 현재 메뉴에 대한 탭 제목 표시
menu_icon = LEVEL1_MENUS[st.session_state.active_level1]["icon"]
st.markdown(f"<h2 style='margin-bottom: 20px; color: #164193;'>{menu_icon} {st.session_state.active_level1}</h2>", unsafe_allow_html=True)

# 탭 생성
tabs = st.tabs(current_tabs)

# 현재 Level-1 메뉴에 해당하는 탭들만 표시
for i, (tab, component, tab_index) in enumerate(zip(tabs, current_components, current_tab_indices)):
    with tab:
        handle_tab_change(tab_index)

        # 컴포넌트 실행
        if tab_index <= 4:  # 반가폭 탭
            if df is not None:
                if tab_index == 4: # 시뮬레이션 탭
                    if st.session_state.active_level1 == "품질예측" and 'fwhm_model' in locals():
                        component(df, fwhm_model) # 로드된 모델 전달
                    else:
                        component(df, model) # 기본 모델 사용
                elif tab_index == 2:  # 모델 결과 탭
                     # show_model_results 함수가 모델 경로 등을 인자로 받도록 수정 필요
                    if st.session_state.active_level1 == "품질예측" and 'fwhm_model_dir' in locals() and 'fwhm_plot_dir' in locals() and 'selected_fwhm_model' in locals():
                        component(model_dir=fwhm_model_dir, plot_dir=fwhm_plot_dir, model_type=selected_fwhm_model)
                    else:
                        # 데이터셋 기본값 설정
                        dataset_suffix = '_F28'
                        if 'selected_fwhm_dataset' in st.session_state:
                            dataset_suffix = f"_{st.session_state.selected_fwhm_dataset}"
                        component(model_dir=f"FWHM/models_cbm{dataset_suffix}", plot_dir=f"FWHM/plots_cbm{dataset_suffix}", model_type="CatBoost")
                elif tab_index == 3:  # 시각화 갤러리 탭
                    # show_visualization_gallery 함수가 플롯 경로를 인자로 받도록 수정 필요
                    if st.session_state.active_level1 == "품질예측" and 'fwhm_plot_dir' in locals() and 'selected_fwhm_model' in locals():
                        component(plot_dir=fwhm_plot_dir, model_type=selected_fwhm_model)
                    else:
                        # 데이터셋 기본값 설정
                        dataset_suffix = '_F28'
                        if 'selected_fwhm_dataset' in st.session_state:
                            dataset_suffix = f"_{st.session_state.selected_fwhm_dataset}"
                        component(plot_dir=f"FWHM/plots_cbm{dataset_suffix}", model_type="CatBoost")
                else:  # 데이터 개요, 특성 분석 탭
                    component(df)
            else:
                st.warning("데이터를 로드할 수 없습니다. 품질예측 데이터가 없습니다.")
        elif tab_index in [11, 12, 13, 23]:  # SEM-EDS 탭
            component()
        elif tab_index in [5, 6, 7, 8, 9, 10]: # ICP 탭
             component()
        elif tab_index in [14, 15, 16, 17, 18]: # CMMS 탭
             component()
        elif tab_index in [19, 20, 21]: # 공정관리이력 채팅 및 검색 탭
             component()
        elif tab_index in [24, 25, 26, 27, 28]: # 생산이슈리포트 탭
             component()
        else:  # 홈 탭 등
            component() # 인자 없는 컴포넌트 실행 (홈 탭 등)

# Footer
st.markdown("""<div class="fixed-footer">
    <div class="footer-content">
        <h5 style="color: #164193;">DX-AI Interactive Dashboard</h5>
        <span style="color: #26A9E0;">이 대시보드는 제조업 데이터 분석 및 모델링 결과를 시각화합니다.</span>
        <br/>
        <span style="color: #666;">© 2025 DX-AI All rights reserved.</span>
    </div>
</div>""", unsafe_allow_html=True)

# ===== html lang="en" -> lang="ko" : 브라우저 언어 설정에 따른 자동 번역에 대응 =====
# st.markdown("""<script>
#     // 문서의 기본 언어 "ko"로 설정
#     document.documentElement.lang = "ko";

#     // st-key-sidebar-menu-로 시작하는 요소들에 no-translate 클래스 추가
#     document.querySelectorAll('.st-key-sidebar-menu p').forEach(element => {
#         element.classList.add("notranslate");
#     });
# </script>""", unsafe_allow_html=True)
from streamlit.components.v1 import html

# 매우 작은 높이로 iframe만 띄운 뒤, 부모 문서의 lang 속성을 변경
html("""<script>
    // 부모 문서(<html>)에 접근
    const pd = window.parent.document;
    // lang 속성 변경
    pd.documentElement.lang = 'ko';
    // <html>에 "notranslate" 클래스 추가
    pd.documentElement.classList.add('notranslate');
    // 사이드바 메뉴 버튼에 "notranslate" 클래스 추가
    const sidebarMenu = pd.querySelectorAll('.st-key-sidebar-menu p');
    sidebarMenu.forEach(el => {
        el.classList.add('notranslate');
    });
</script>""", height=0, width=0, scrolling=False)
