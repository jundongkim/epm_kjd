import pandas as pd
import numpy as np
from .data_utils import get_sensor_type
import streamlit as st

def process_dataframe(df):
    """데이터프레임 기본 처리 및 통계 계산"""
    if df is None or len(df) == 0:
        return None, {}
        
    # 데이터프레임을 timestamp 기준으로 정렬
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Get sensor column name
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 결측값(null, None) 처리 - 세션 상태 확인하여 사용자 설정에 따라 처리
    null_count = df[sensor_col].isna().sum()
    stats = {
        "null_count": null_count,  # 결측값 개수 통계 추가
        "total_count": len(df)
    }
    
    # 결측값 처리 방법 세션 상태 확인
    if "null_handling_method" not in st.session_state:
        # 기본값 설정 (처음 실행 시)
        st.session_state.null_handling_method = "remove"
    
    # 결측값 처리
    df_cleaned = df.copy()
    if null_count > 0:
        if st.session_state.null_handling_method == "remove":
            # 결측값이 있는 행 제거
            df_cleaned = df.dropna(subset=[sensor_col])
            print(f"'{sensor_col}' 컬럼에서 {null_count}개의 결측값이 있는 행이 제거되었습니다.")
        elif st.session_state.null_handling_method == "fill_mean":
            # 평균값으로 대체
            mean_value = df[sensor_col].mean()
            df_cleaned[sensor_col] = df[sensor_col].fillna(mean_value)
            print(f"'{sensor_col}' 컬럼의 {null_count}개 결측값을 평균값({mean_value:.2f})으로 대체했습니다.")
        elif st.session_state.null_handling_method == "fill_median":
            # 중앙값으로 대체
            median_value = df[sensor_col].median()
            df_cleaned[sensor_col] = df[sensor_col].fillna(median_value)
            print(f"'{sensor_col}' 컬럼의 {null_count}개 결측값을 중앙값({median_value:.2f})으로 대체했습니다.")
        elif st.session_state.null_handling_method == "fill_zero":
            # 0으로 대체
            df_cleaned[sensor_col] = df[sensor_col].fillna(0)
            print(f"'{sensor_col}' 컬럼의 {null_count}개 결측값을 0으로 대체했습니다.")
        elif st.session_state.null_handling_method == "fill_previous":
            # 이전 값으로 대체 (forward fill)
            df_cleaned[sensor_col] = df[sensor_col].fillna(method='ffill')
            # 첫 행이 NaN인 경우 다음 값으로 대체 (backward fill)
            df_cleaned[sensor_col] = df_cleaned[sensor_col].fillna(method='bfill')
            # 여전히 NaN이 있는 경우 0으로 대체
            remaining_nulls = df_cleaned[sensor_col].isna().sum()
            if remaining_nulls > 0:
                df_cleaned[sensor_col] = df_cleaned[sensor_col].fillna(0)
            print(f"'{sensor_col}' 컬럼의 {null_count}개 결측값을 인접한 값으로 대체했습니다.")
        elif st.session_state.null_handling_method == "interpolation":
            # 선형 보간법으로 대체
            df_cleaned[sensor_col] = df[sensor_col].interpolate(method='linear')
            # 양 끝에 남아있는 NaN 처리 (bfill, ffill로 처리)
            df_cleaned[sensor_col] = df_cleaned[sensor_col].fillna(method='ffill').fillna(method='bfill')
            print(f"'{sensor_col}' 컬럼의 {null_count}개 결측값을 선형 보간법으로 대체했습니다.")
    
    # 기본 통계 계산 (결측값 처리 후)
    stats.update({
        "count": len(df_cleaned),
        "mean": df_cleaned[sensor_col].mean(),
        "median": df_cleaned[sensor_col].median(),
        "std": df_cleaned[sensor_col].std(),
        "min": df_cleaned[sensor_col].min(),
        "max": df_cleaned[sensor_col].max(),
        "cv": df_cleaned[sensor_col].std() / df_cleaned[sensor_col].mean() if df_cleaned[sensor_col].mean() != 0 else 0
    })
    
    # 시간 관련 변수 추가
    df_processed = df_cleaned.copy()
    
    # NaN 값 처리를 위한 안전 변환
    if 'timestamp' in df_processed.columns:
        # timestamp 열에 NaN이 있는지 확인
        timestamp_na_count = df_processed['timestamp'].isna().sum()
        if timestamp_na_count > 0:
            print(f"경고: timestamp 열에 {timestamp_na_count}개의 NaN 값이 있습니다. 이 행들은 시간 관련 계산에서 제외됩니다.")
            # NaN 값이 있는 행 제외
            df_processed = df_processed.dropna(subset=['timestamp'])
        
        # 안전하게 시간 관련 변수 추가
        try:
            df_processed['hour'] = df_processed['timestamp'].dt.hour
            df_processed['day_of_week'] = df_processed['timestamp'].dt.dayofweek
            df_processed['month'] = df_processed['timestamp'].dt.month
            df_processed['quarter'] = df_processed['timestamp'].dt.quarter
            
            # 시간대 분류
            time_bins = [0, 6, 12, 18, 24]
            time_labels = ['새벽(0-6시)', '오전(6-12시)', '오후(12-18시)', '저녁(18-24시)']
            df_processed['time_of_day'] = pd.cut(df_processed['hour'], bins=time_bins, labels=time_labels, right=False)
            
            # 주말/평일 분류 - 안전하게 정수로 변환
            df_processed['is_weekend'] = df_processed['day_of_week'].apply(
                lambda x: '주말' if (isinstance(x, (int, float)) and not np.isnan(x) and int(x) >= 5) else '평일'
            )
            
            # 요일 이름 추가 - 안전하게 정수로 변환 후 인덱싱
            day_names = ['월', '화', '수', '목', '금', '토', '일']
            df_processed['day_name'] = df_processed['day_of_week'].apply(
                lambda x: day_names[int(x)] if (isinstance(x, (int, float)) and not np.isnan(x) and 0 <= int(x) < 7) else '알 수 없음'
            )
        except Exception as e:
            print(f"시간 관련 변수 추가 중 오류 발생: {str(e)}")
            # 기본 시간 변수 추가 (오류 발생 시)
            if 'hour' not in df_processed.columns: df_processed['hour'] = 0
            if 'day_of_week' not in df_processed.columns: df_processed['day_of_week'] = 0
            if 'month' not in df_processed.columns: df_processed['month'] = 1
            if 'quarter' not in df_processed.columns: df_processed['quarter'] = 1
            if 'time_of_day' not in df_processed.columns: df_processed['time_of_day'] = '알 수 없음'
            if 'is_weekend' not in df_processed.columns: df_processed['is_weekend'] = '알 수 없음' 
            if 'day_name' not in df_processed.columns: df_processed['day_name'] = '알 수 없음'
    else:
        # timestamp 열이 없는 경우 기본값 설정
        df_processed['hour'] = 0
        df_processed['day_of_week'] = 0
        df_processed['month'] = 1
        df_processed['quarter'] = 1
        df_processed['time_of_day'] = '알 수 없음'
        df_processed['is_weekend'] = '알 수 없음'
        df_processed['day_name'] = '알 수 없음'
    
    return df_processed, stats

def create_sample_dataframe(df, max_points=10000):
    """시각화를 위한 샘플 데이터프레임을 생성합니다."""
    if len(df) > max_points:
        step = len(df) // max_points
        return df.iloc[::step].copy()
    return df.copy()

def calculate_rolling_average(df, window_size):
    """이동 평균을 계산합니다."""
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    return df[sensor_col].rolling(window=window_size).mean() 