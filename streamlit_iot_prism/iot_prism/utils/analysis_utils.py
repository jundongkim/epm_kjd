import numpy as np
from scipy import fft
from .data_utils import get_sensor_type

def calculate_fft(signal_values, sampling_rate=1.0):
    """FFT 계산."""
    n = len(signal_values)
    fft_values = fft.fft(signal_values)
    freqs = fft.fftfreq(n, d=1/sampling_rate)
    
    # 양의 주파수만 선택
    pos_mask = freqs > 0
    freqs = freqs[pos_mask]
    fft_values = fft_values[pos_mask]
    
    # 스펙트럼 계산 (절대값)
    spectrum = np.abs(fft_values) / n
    
    return freqs, spectrum

def get_correlation_data(df):
    """상관관계 데이터를 계산."""
    df_corr = df.copy()
    
    # Get sensor column name
    sensor_col = get_sensor_type()
    if sensor_col not in df_corr.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 시간 관련 변수 추가
    df_corr['hour'] = df_corr['timestamp'].dt.hour
    df_corr['day_of_week'] = df_corr['timestamp'].dt.dayofweek
    df_corr['day_of_month'] = df_corr['timestamp'].dt.day
    df_corr['month'] = df_corr['timestamp'].dt.month
    df_corr['quarter'] = df_corr['timestamp'].dt.quarter
    
    # 상관관계 변수 선택
    corr_vars = [sensor_col, 'hour', 'day_of_week', 'day_of_month', 'month', 'quarter']
    
    # 상관관계 계산
    corr_matrix = df_corr[corr_vars].corr()
    
    return corr_matrix 