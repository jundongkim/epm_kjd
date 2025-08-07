import streamlit as st
import pandas as pd
import os
import glob
from catboost import CatBoostRegressor

@st.cache_data
def load_data():
    """데이터 로드 함수"""
    # 선택된 데이터셋 확인 (세션 상태에서)
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값
    
    # 선택된 데이터셋에 따른 파일 경로
    data_path = f"FWHM/normalized_data_{selected_dataset}.csv"
    
    if os.path.exists(data_path):
        return pd.read_csv(data_path)
    else:
        # 기본 경로 시도 (이전 버전 호환성)
        default_path = "FWHM/normalized_data.csv"
        if os.path.exists(default_path):
            st.warning(f"선택한 데이터셋({selected_dataset}) 파일을 찾을 수 없어 기본 데이터를 사용합니다.")
            return pd.read_csv(default_path)
        else:
            st.error(f"데이터 파일을 찾을 수 없습니다: {data_path} 또는 {default_path}")
            return None

@st.cache_data
def load_visualization_files():
    """시각화 HTML 파일 로드 함수"""
    # 선택된 데이터셋 확인
    if 'selected_fwhm_dataset' in st.session_state:
        selected_dataset = st.session_state.selected_fwhm_dataset
    else:
        selected_dataset = "F28"  # 기본값
    
    # 데이터셋별 디렉토리 경로
    vis_dir = f"FWHM/visualization_{selected_dataset}"
    plot_dir = f"FWHM/plots_cbm_{selected_dataset}"
    
    # 데이터셋별 디렉토리가 없으면 기본 디렉토리 사용
    if not os.path.exists(vis_dir):
        vis_dir = "FWHM/visualization"
        
    if not os.path.exists(plot_dir):
        plot_dir = "FWHM/plots_cbm"

    vis_files = {}
    if os.path.exists(vis_dir):
        vis_files["데이터 생성"] = {
            "html": sorted(glob.glob(f"{vis_dir}/*.html")),
            "type": "visualization"
        }

    if os.path.exists(plot_dir):
        vis_files["모델 학습"] = {
            "html": sorted(glob.glob(f"{plot_dir}/*.html")),
            "type": "plots"
        }

    return vis_files