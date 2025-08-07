"""
DX-AI Manufacturing Copilot - 원가 관리 유틸리티

원가 관리 페이지에서 사용되는 파일 관리, 데이터 처리 등의 유틸리티 함수들
"""

import streamlit as st
import pandas as pd
import os
import glob
import time
from typing import Dict, Any, List, Optional
from datetime import datetime


def get_current_data_info() -> Dict[str, Any]:
    """현재 데이터 정보 반환"""
    info = {
        "has_custom_data": False,
        "filepath": None,
        "record_count": 0,
        "avg_purity": 0,
        "avg_yield": 0,
        "avg_cost": 0
    }
    
    if "cost_data_filepath" in st.session_state and st.session_state.cost_data_filepath:
        info["has_custom_data"] = True
        info["filepath"] = st.session_state.cost_data_filepath
        
        if "generated_cost_data" in st.session_state:
            df = st.session_state.generated_cost_data
            info["record_count"] = len(df)
            if 'purity' in df.columns:
                info["avg_purity"] = df['purity'].mean()
            if 'yield' in df.columns:
                info["avg_yield"] = df['yield'].mean()
            if 'total_cost' in df.columns:
                info["avg_cost"] = df['total_cost'].mean()
    
    return info


def get_available_cost_files() -> List[str]:
    """사용 가능한 원가 데이터 파일 목록 반환"""
    # 원가 데이터 폴더 경로들
    search_paths = [
        "data/generated/cost_production/*.csv",
        "data/generated/*.csv"
    ]
    
    files = []
    for pattern in search_paths:
        files.extend(glob.glob(pattern))
    
    # 파일명에 'cost' 또는 'production'이 포함된 파일만 필터링
    cost_files = [f for f in files if 'cost' in os.path.basename(f).lower() or 'production' in os.path.basename(f).lower()]
    
    # 최신 파일 순으로 정렬
    cost_files.sort(key=os.path.getmtime, reverse=True)
    
    return cost_files


def get_file_info(filepath: str) -> str:
    """파일 기본 정보 반환"""
    try:
        stat = os.stat(filepath)
        size_mb = stat.st_size / 1024 / 1024
        created_date = datetime.fromtimestamp(stat.st_mtime).strftime('%m/%d %H:%M')
        return f"{size_mb:.1f}MB, {created_date}"
    except:
        return "정보 없음"


def get_detailed_file_info(filepath: str) -> Dict[str, Any]:
    """파일 상세 정보 반환"""
    info = {
        "size_mb": 0,
        "created_date": "알 수 없음",
        "record_count": 0,
        "date_range": "알 수 없음",
        "avg_cost": 0
    }
    
    try:
        # 파일 기본 정보
        stat = os.stat(filepath)
        info["size_mb"] = stat.st_size / 1024 / 1024
        info["created_date"] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # CSV 데이터 정보
        df = pd.read_csv(filepath, nrows=1000)  # 처음 1000개 행만 읽어서 빠르게 처리
        info["record_count"] = len(pd.read_csv(filepath))  # 전체 행 수
        
        if 'timestamp' in df.columns:
            info["date_range"] = f"{df['timestamp'].min()[:10]} ~ {df['timestamp'].max()[:10]}"
        
        if 'total_cost' in df.columns:
            info["avg_cost"] = df['total_cost'].mean()
        
    except Exception as e:
        print(f"파일 정보 읽기 오류: {e}")
    
    return info


def load_selected_file(filepath: str) -> None:
    """선택된 파일 로드"""
    try:
        # 파일 읽기
        df = pd.read_csv(filepath)
        
        # 세션 상태에 저장
        st.session_state.cost_data_filepath = filepath
        st.session_state.generated_cost_data = df
        
        # 기존 엔진 삭제 (재초기화를 위해)
        reset_cost_engines()
        
        st.success(f"✅ 데이터 파일 로드 완료: {len(df):,}개 레코드")
        st.success("🔄 원가관리 시스템이 새로운 데이터로 재초기화됩니다.")
        
        # 페이지 새로고침
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 파일 로드 실패: {e}")


def save_uploaded_file(uploaded_file, df: pd.DataFrame) -> None:
    """업로드된 파일 저장"""
    try:
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = uploaded_file.name.replace('.csv', '')
        filename = f"uploaded_{original_name}_{timestamp}.csv"
        filepath = os.path.join("data", "generated", "cost_production", filename)
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 파일 저장
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        # 세션 상태에 저장
        st.session_state.cost_data_filepath = filepath
        st.session_state.generated_cost_data = df
        
        # 기존 엔진 삭제
        reset_cost_engines()
        
        st.success(f"✅ 파일 저장 완료: `{filepath}`")
        st.success(f"📊 {len(df):,}개 레코드가 로드되었습니다.")
        
        # 페이지 새로고침
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 파일 저장 실패: {e}")


def reset_cost_engines() -> None:
    """원가 관리 엔진들 리셋"""
    engine_keys = [
        "cost_optimization_engine",
        "advanced_optimization_engine", 
        "cost_chat_manager",
        "cost_management_engine"
    ]
    
    for key in engine_keys:
        if key in st.session_state:
            del st.session_state[key]


def use_default_simulation_data() -> None:
    """기본 시뮬레이션 데이터 사용"""
    # 사용자 데이터 세션 상태 삭제
    data_keys = ["cost_data_filepath", "generated_cost_data"]
    for key in data_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # 엔진 재초기화
    reset_cost_engines()
    
    st.success("✅ 기본 시뮬레이션 데이터로 전환되었습니다!")
    st.rerun()


def validate_csv_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """CSV 파일의 필수 컬럼 검증"""
    required_columns = [
        'material_a', 'material_b', 'catalyst',
        'temperature', 'pressure', 'flow_rate',
        'steam', 'electricity', 'cooling_water',
        'purity', 'yield', 'total_cost'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    return {
        "is_valid": len(missing_columns) == 0,
        "missing_columns": missing_columns,
        "available_columns": df.columns.tolist(),
        "column_status": [
            {"name": col, "present": col in df.columns}
            for col in required_columns
        ]
    }


def get_default_data_info() -> Dict[str, Any]:
    """기본 시뮬레이션 데이터 정보 반환"""
    return {
        "record_count": 1000,
        "features": [
            {"name": "material_a", "description": "원료 A 투입량 (kg/h)", "range": "80-120"},
            {"name": "material_b", "description": "원료 B 투입량 (kg/h)", "range": "40-60"},
            {"name": "catalyst", "description": "촉매 투입량 (kg/h)", "range": "4-6"},
            {"name": "temperature", "description": "온도 (°C)", "range": "160-190"},
            {"name": "pressure", "description": "압력 (bar)", "range": "2.0-3.0"},
            {"name": "flow_rate", "description": "유량 (L/h)", "range": "180-220"},
            {"name": "steam", "description": "스팀 사용량 (kg/h)", "range": "120-180"},
            {"name": "electricity", "description": "전력 사용량 (kWh)", "range": "60-100"},
            {"name": "cooling_water", "description": "냉각수 사용량 (L/h)", "range": "400-600"},
            {"name": "purity", "description": "순도 (%)", "range": "80-99"},
            {"name": "yield", "description": "수율 (%)", "range": "70-95"},
            {"name": "total_cost", "description": "총 비용 (원)", "range": "가변"}
        ]
    }


def create_sample_data_preview() -> pd.DataFrame:
    """샘플 데이터 미리보기용 DataFrame 생성"""
    import numpy as np
    
    np.random.seed(42)  # 일관된 샘플 데이터를 위해
    
    sample_data = {
        'material_a': np.random.uniform(80, 120, 5),
        'material_b': np.random.uniform(40, 60, 5),
        'catalyst': np.random.uniform(4, 6, 5),
        'temperature': np.random.uniform(160, 190, 5),
        'pressure': np.random.uniform(2.0, 3.0, 5),
        'flow_rate': np.random.uniform(180, 220, 5),
        'steam': np.random.uniform(120, 180, 5),
        'electricity': np.random.uniform(60, 100, 5),
        'cooling_water': np.random.uniform(400, 600, 5),
        'purity': np.random.uniform(80, 99, 5),
        'yield': np.random.uniform(70, 95, 5),
        'total_cost': np.random.uniform(50000, 150000, 5)
    }
    
    df = pd.DataFrame(sample_data)
    return df.round(2) 