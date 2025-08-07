import os
import pandas as pd
import streamlit as st
from datetime import datetime

# DATA_DIR setup
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iot_data")

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_equipment_type(df=None):
    """데이터프레임, 세션 상태 또는 파일 이름에서 equipment_type 값을 가져옵니다."""
    # 세션 상태에서 확인
    if 'equipment_type' in st.session_state:
        return st.session_state.equipment_type
    
    # 현재 사용 중인 데이터에서 파일 이름 확인
    if 'current_filename' in st.session_state and st.session_state.current_filename:
        filename = st.session_state.current_filename
        # iot_장비유형_날짜.csv 형식에서 장비 유형 추출
        try:
            parts = os.path.basename(filename).split('_')
            if len(parts) >= 2 and parts[0] == 'iot':
                return parts[1]
        except:
            pass
    
    # 기본값 반환
    return "장비"

def get_sensor_type():
    """세션 상태에서 sensor_type 값을 가져옵니다."""
    # 세션 상태에서 확인
    if 'sensor_type' in st.session_state:
        return st.session_state.sensor_type
    
    # 기본값 반환
    return "value"

def save_df_to_file(df, equipment_type=None):
    if equipment_type is None:
        equipment_type = get_equipment_type(df)
    
    # iot_data 폴더에 저장
    filename = f'iot_{equipment_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    filepath = os.path.join(DATA_DIR, filename)
    
    try:
        df.to_csv(filepath, index=False)
        return True, filepath
    except Exception as e:
        return False, str(e)

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8') 