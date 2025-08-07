# Import required libraries
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import IsolationForest
from scipy import stats
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json
import warnings
warnings.filterwarnings('ignore')

def calculate_fixed_thresholds(df, sensor_col, percentiles=[0.001, 0.01, 0.05, 0.95, 0.99, 0.999]):
    """
    고정 임계값을 계산하는 함수
    
    Args:
        df: 센서 데이터가 포함된 데이터프레임
        sensor_col: 센서 값이 저장된 열 이름
        percentiles: 계산할 백분위수 목록
        
    Returns:
        임계값 사전 (백분위수 -> 값)
    """
    thresholds = {}
    for p in percentiles:
        thresholds[p] = np.percentile(df[sensor_col], p * 100)
        thresholds[1-p] = np.percentile(df[sensor_col], (1-p) * 100)
    
    # 추가 통계 계산
    mean = df[sensor_col].mean()
    std = df[sensor_col].std()
    
    thresholds['mean'] = mean
    thresholds['mean-1std'] = mean - std
    thresholds['mean-2std'] = mean - 2*std
    thresholds['mean-3std'] = mean - 3*std
    thresholds['mean+1std'] = mean + std
    thresholds['mean+2std'] = mean + 2*std
    thresholds['mean+3std'] = mean + 3*std
    
    return thresholds

def calculate_dynamic_thresholds(df, sensor_col, window=24, n_std=3):
    """
    동적 임계값을 계산하는 함수 (이동 평균 기반)
    
    Args:
        df: 센서 데이터가 포함된 데이터프레임
        sensor_col: 센서 값이 저장된 열 이름
        window: 이동 평균 윈도우 크기
        n_std: 표준편차 배수
        
    Returns:
        동적 임계값이 추가된 데이터프레임
    """
    df_copy = df.copy()
    
    # 이동 평균 및 표준편차 계산
    df_copy['moving_avg'] = df_copy[sensor_col].rolling(window=window, min_periods=1).mean()
    df_copy['moving_std'] = df_copy[sensor_col].rolling(window=window, min_periods=1).std()
    
    # 상하한 임계값 계산
    df_copy['upper_threshold'] = df_copy['moving_avg'] + n_std * df_copy['moving_std']
    df_copy['lower_threshold'] = df_copy['moving_avg'] - n_std * df_copy['moving_std']
    
    return df_copy

def detect_anomalies(df, sensor_col, method='zscore', **kwargs):
    """
    이상치 탐지 기반 임계값 계산 함수
    
    Args:
        df: 센서 데이터가 포함된 데이터프레임
        sensor_col: 센서 값이 저장된 열 이름
        method: 이상치 탐지 방법 ('zscore', 'iqr', 'lof', 'isolation_forest')
        kwargs: 이상치 탐지 방법에 따른 추가 매개변수
        
    Returns:
        이상치 플래그가 추가된 데이터프레임
    """
    df_copy = df.copy()
    values = df_copy[sensor_col].values.reshape(-1, 1)
    
    if method == 'zscore':
        # Z-점수 기반 이상치 탐지
        threshold = kwargs.get('threshold', 3)
        z_scores = np.abs(stats.zscore(df_copy[sensor_col]))
        df_copy['anomaly'] = z_scores > threshold
        df_copy['anomaly_score'] = z_scores
        
    elif method == 'iqr':
        # IQR 기반 이상치 탐지
        q1 = df_copy[sensor_col].quantile(0.25)
        q3 = df_copy[sensor_col].quantile(0.75)
        iqr = q3 - q1
        factor = kwargs.get('factor', 1.5)
        lower_bound = q1 - factor * iqr
        upper_bound = q3 + factor * iqr
        
        df_copy['anomaly'] = (df_copy[sensor_col] < lower_bound) | (df_copy[sensor_col] > upper_bound)
        # 이상치 점수 계산 (얼마나 경계를 벗어났는지)
        df_copy['anomaly_score'] = np.maximum(
            np.abs(df_copy[sensor_col] - lower_bound) / iqr if lower_bound != q1 else 0,
            np.abs(df_copy[sensor_col] - upper_bound) / iqr if upper_bound != q3 else 0
        )
        
    elif method == 'lof':
        # 지역 이상치 인자(LOF) 기반 이상치 탐지
        n_neighbors = kwargs.get('n_neighbors', 20)
        contamination = kwargs.get('contamination', 0.01)
        
        lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
        pred = lof.fit_predict(values)
        df_copy['anomaly'] = pred == -1
        # 음수 이웃 이상치 인자를 양수로 변환하여 점수로 사용
        df_copy['anomaly_score'] = -lof.negative_outlier_factor_
        
    elif method == 'isolation_forest':
        # Isolation Forest 기반 이상치 탐지
        contamination = kwargs.get('contamination', 0.01)
        
        model = IsolationForest(contamination=contamination, random_state=42)
        pred = model.fit_predict(values)
        df_copy['anomaly'] = pred == -1
        # 이상치 결정 점수를 절대값으로 변환하여 사용
        df_copy['anomaly_score'] = np.abs(model.decision_function(values))
    
    return df_copy

def evaluate_threshold_performance(df, sensor_col, threshold_type, threshold_value=None, **kwargs):
    """
    임계값 성능 평가 함수
    
    Args:
        df: 센서 데이터가 포함된 데이터프레임
        sensor_col: 센서 값이 저장된 열 이름
        threshold_type: 임계값 유형 ('fixed', 'dynamic', 'anomaly')
        threshold_value: 고정 임계값인 경우 임계값
        kwargs: 동적 임계값 또는 이상치 탐지 방법에 따른 추가 매개변수
        
    Returns:
        알람 발생 횟수, 거짓 경보 추정 횟수, 알람 지속 시간 등의 성능 지표
    """
    df_copy = df.copy()
    
    # 임계값 유형에 따른 알람 플래그 계산
    if threshold_type == 'fixed':
        upper_threshold = kwargs.get('upper_threshold', float('inf'))
        lower_threshold = kwargs.get('lower_threshold', float('-inf'))
        
        if threshold_value is not None:
            # 단일 임계값이 주어진 경우 (상한 또는 하한)
            direction = kwargs.get('direction', 'upper')
            if direction == 'upper':
                df_copy['alarm'] = df_copy[sensor_col] > threshold_value
            else:
                df_copy['alarm'] = df_copy[sensor_col] < threshold_value
        else:
            # 상한과 하한이 모두 주어진 경우
            df_copy['alarm'] = (df_copy[sensor_col] > upper_threshold) | (df_copy[sensor_col] < lower_threshold)
    
    elif threshold_type == 'dynamic':
        window = kwargs.get('window', 24)
        n_std = kwargs.get('n_std', 3)
        
        # 동적 임계값 계산
        df_temp = calculate_dynamic_thresholds(df_copy, sensor_col, window, n_std)
        df_copy['alarm'] = (df_copy[sensor_col] > df_temp['upper_threshold']) | (df_copy[sensor_col] < df_temp['lower_threshold'])
        # 동적 임계값 저장
        df_copy['upper_threshold'] = df_temp['upper_threshold']
        df_copy['lower_threshold'] = df_temp['lower_threshold']
    
    elif threshold_type == 'anomaly':
        method = kwargs.get('method', 'zscore')
        
        # 이상치 탐지를 위해 kwargs 복사
        kwargs_copy = kwargs.copy()
        if 'method' in kwargs_copy:
            del kwargs_copy['method']
        
        # detect_anomalies 함수 호출로 이상치 탐지
        df_temp = detect_anomalies(df_copy, sensor_col, method=method, **kwargs_copy)
        df_copy['alarm'] = df_temp['anomaly']
        df_copy['anomaly_score'] = df_temp['anomaly_score']
    
    # 알람 발생 횟수 계산
    total_alarms = df_copy['alarm'].sum()
    
    # 연속 알람 탐지 (알람 이벤트로 그룹화)
    df_copy['alarm_event'] = (df_copy['alarm'] != df_copy['alarm'].shift(1)).cumsum()
    alarm_events = df_copy[df_copy['alarm']].groupby('alarm_event').size()
    
    # 알람 이벤트 수
    alarm_event_count = len(alarm_events)
    
    # 알람 지속 시간 (평균, 최대)
    avg_alarm_duration = alarm_events.mean() if not alarm_events.empty else 0
    max_alarm_duration = alarm_events.max() if not alarm_events.empty else 0
    
    # 예상 거짓 경보율 (간단한 추정)
    # 실제로는 라벨이 있는 데이터가 필요하지만, 여기서는 단기 알람을 거짓 경보로 간주
    short_alarm_threshold = kwargs.get('short_alarm_threshold', 3)  # 3개 미만의 포인트를 가진 알람은 거짓 경보로 간주
    false_alarms = sum(1 for duration in alarm_events if duration < short_alarm_threshold)
    false_alarm_ratio = false_alarms / alarm_event_count if alarm_event_count > 0 else 0
    
    # 결과 사전 반환
    result = {
        'total_alarms': total_alarms,
        'alarm_events': alarm_event_count,
        'avg_duration': avg_alarm_duration,
        'max_duration': max_alarm_duration,
        'false_alarms': false_alarms,
        'false_alarm_ratio': false_alarm_ratio,
        'df_with_alarms': df_copy
    }
    
    return result

def optimize_threshold(df, sensor_col, threshold_type, optimization_metric='false_alarm_ratio', **kwargs):
    """
    최적의 임계값을 찾는 함수
    
    Args:
        df: 센서 데이터가 포함된 데이터프레임
        sensor_col: 센서 값이 저장된 열 이름
        threshold_type: 임계값 유형 ('fixed', 'dynamic', 'anomaly')
        optimization_metric: 최적화할 지표 ('false_alarm_ratio', 'total_alarms', 'alarm_events')
        kwargs: 임계값 계산 방법에 따른 추가 매개변수
        
    Returns:
        최적 임계값 및 성능 지표
    """
    # 최적화 범위 설정
    if threshold_type == 'fixed':
        # 고정 임계값 최적화
        direction = kwargs.get('direction', 'both')
        percentiles = np.linspace(0.001, 0.2, 20)  # 0.1% ~ 20% 범위에서 20개 포인트
        
        best_score = float('inf') if optimization_metric != 'total_alarms' else 0
        best_params = None
        results = []
        
        # kwargs에서 direction 파라미터 제거 (함수 내에서 직접 설정)
        kwargs_without_direction = {k: v for k, v in kwargs.items() if k != 'direction'}
        
        for p in percentiles:
            if direction == 'upper' or direction == 'both':
                # 상한 임계값 테스트
                upper_threshold = np.percentile(df[sensor_col], 100 - p * 100)
                perf = evaluate_threshold_performance(
                    df, sensor_col, 'fixed', upper_threshold, 
                    direction='upper', **kwargs_without_direction
                )
                
                score = perf[optimization_metric]
                if (optimization_metric == 'false_alarm_ratio' and score < best_score) or \
                   (optimization_metric == 'total_alarms' and score > best_score):
                    best_score = score
                    best_params = {'percentile': 1-p, 'threshold': upper_threshold, 'direction': 'upper'}
                
                results.append({
                    'percentile': 1-p, 
                    'threshold': upper_threshold, 
                    'direction': 'upper',
                    **{k: v for k, v in perf.items() if k != 'df_with_alarms'}
                })
            
            if direction == 'lower' or direction == 'both':
                # 하한 임계값 테스트
                lower_threshold = np.percentile(df[sensor_col], p * 100)
                perf = evaluate_threshold_performance(
                    df, sensor_col, 'fixed', lower_threshold, 
                    direction='lower', **kwargs_without_direction
                )
                
                score = perf[optimization_metric]
                if (optimization_metric == 'false_alarm_ratio' and score < best_score) or \
                   (optimization_metric == 'total_alarms' and score > best_score):
                    best_score = score
                    best_params = {'percentile': p, 'threshold': lower_threshold, 'direction': 'lower'}
                
                results.append({
                    'percentile': p, 
                    'threshold': lower_threshold, 
                    'direction': 'lower',
                    **{k: v for k, v in perf.items() if k != 'df_with_alarms'}
                })
    
    elif threshold_type == 'dynamic':
        # 동적 임계값 최적화 (윈도우 크기 및 표준편차 배수)
        windows = kwargs.get('windows', [6, 12, 24, 48, 72])
        n_stds = kwargs.get('n_stds', [2.0, 2.5, 3.0, 3.5, 4.0])
        
        best_score = float('inf') if optimization_metric != 'total_alarms' else 0
        best_params = None
        results = []
        
        for window in windows:
            for n_std in n_stds:
                perf = evaluate_threshold_performance(
                    df, sensor_col, 'dynamic', 
                    window=window, n_std=n_std, **kwargs
                )
                
                score = perf[optimization_metric]
                if (optimization_metric == 'false_alarm_ratio' and score < best_score) or \
                   (optimization_metric == 'total_alarms' and score > best_score):
                    best_score = score
                    best_params = {'window': window, 'n_std': n_std}
                
                results.append({
                    'window': window, 
                    'n_std': n_std,
                    **{k: v for k, v in perf.items() if k != 'df_with_alarms'}
                })
    
    elif threshold_type == 'anomaly':
        # 이상치 탐지 방법 최적화
        method = kwargs.get('method', 'zscore')
        
        if method == 'zscore':
            # Z-점수 임계값 최적화
            thresholds = kwargs.get('thresholds', [2.0, 2.5, 3.0, 3.5, 4.0])
            
            best_score = float('inf') if optimization_metric != 'total_alarms' else 0
            best_params = None
            results = []
            
            for threshold in thresholds:
                # kwargs에서 method 키워드 충돌 방지
                kwargs_copy = kwargs.copy()
                if 'method' in kwargs_copy:
                    del kwargs_copy['method']
                
                perf = evaluate_threshold_performance(
                    df, sensor_col, 'anomaly', method=method,
                    threshold=threshold, **kwargs_copy
                )
                
                score = perf[optimization_metric]
                if (optimization_metric == 'false_alarm_ratio' and score < best_score) or \
                   (optimization_metric == 'total_alarms' and score > best_score):
                    best_score = score
                    best_params = {'method': method, 'threshold': threshold}
                
                results.append({
                    'method': method, 
                    'threshold': threshold,
                    **{k: v for k, v in perf.items() if k != 'df_with_alarms'}
                })
        
        elif method == 'iqr':
            # IQR 배수 최적화
            factors = kwargs.get('factor', [1.0, 1.5, 2.0, 2.5, 3.0])  # factors를 factor로 변경
            
            best_score = float('inf') if optimization_metric != 'total_alarms' else 0
            best_params = None
            results = []
            
            for factor in factors:
                # kwargs에서 method 키워드 충돌 방지
                kwargs_copy = kwargs.copy()
                if 'method' in kwargs_copy:
                    del kwargs_copy['method']
                
                perf = evaluate_threshold_performance(
                    df, sensor_col, 'anomaly', method=method,
                    factor=factor, **kwargs_copy
                )
                
                score = perf[optimization_metric]
                if (optimization_metric == 'false_alarm_ratio' and score < best_score) or \
                   (optimization_metric == 'total_alarms' and score > best_score):
                    best_score = score
                    best_params = {'method': method, 'factor': factor}
                
                results.append({
                    'method': method, 
                    'factor': factor,
                    **{k: v for k, v in perf.items() if k != 'df_with_alarms'}
                })
        
        elif method in ['lof', 'isolation_forest']:
            # LOF 또는 IsolationForest 오염도 최적화
            contaminations = kwargs.get('contaminations', [0.01, 0.02, 0.05, 0.1])
            
            best_score = float('inf') if optimization_metric != 'total_alarms' else 0
            best_params = None
            results = []
            
            for contamination in contaminations:
                # method는 이미 kwargs에 포함될 수 있으므로 삭제
                kwargs_copy = kwargs.copy()
                if 'method' in kwargs_copy:
                    del kwargs_copy['method']
                
                perf = evaluate_threshold_performance(
                    df, sensor_col, 'anomaly',
                    method=method,
                    contamination=contamination, 
                    **kwargs_copy
                )
                
                score = perf[optimization_metric]
                if (optimization_metric == 'false_alarm_ratio' and score < best_score) or \
                   (optimization_metric == 'total_alarms' and score > best_score):
                    best_score = score
                    best_params = {'method': method, 'contamination': contamination}
                
                results.append({
                    'method': method, 
                    'contamination': contamination,
                    **{k: v for k, v in perf.items() if k != 'df_with_alarms'}
                })
    
    return best_params, results 

def render_alarm_threshold_ui(df_processed):
    """경보 및 임계값 설정 인터페이스 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    st.subheader("경보 및 임계값 설정 분석")
    
    # Get equipment type
    equipment_type = get_equipment_type(df_processed)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df_processed.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 임계값 설정 옵션
    threshold_options = st.columns([1, 1])
    
    with threshold_options[0]:
        threshold_method = st.selectbox(
            "임계값 설정 방법",
            ["고정 임계값", "동적 임계값", "이상치 기반 임계값"],
            help="고정 임계값: 백분위수 또는 표준편차 기반 고정 값\n동적 임계값: 이동 평균 및 표준편차 기반 동적 값\n이상치 기반: 이상치 탐지 알고리즘 기반 동적 임계값"
        )
    
    with threshold_options[1]:
        optimization_metric = st.selectbox(
            "최적화 기준",
            ["거짓 경보 최소화", "경보 발생 횟수 최적화", "경보 이벤트 최적화"],
            help="거짓 경보 최소화: 짧은 지속 시간의 경보 최소화\n경보 발생 횟수 최적화: 적절한 수의 경보 발생\n경보 이벤트 최적화: 경보 이벤트 수 최적화"
        )
    
    # 선택된 방법에 따른 추가 옵션
    if threshold_method == "고정 임계값":
        direction_col, percentile_col = st.columns(2)
        
        with direction_col:
            direction = st.radio(
                "임계값 방향",
                ["상한", "하한", "양방향"],
                help="상한: 값이 임계값보다 크면 경보\n하한: 값이 임계값보다 작으면 경보\n양방향: 값이 상한보다 크거나 하한보다 작으면 경보"
            )
        
        with percentile_col:
            if direction == "양방향":
                upper_percentile = st.slider("상한 백분위수", 80.0, 99.9, 95.0, 0.1, 
                                           help="상한 임계값으로 사용할 백분위수 (높을수록 경보가 적게 발생)")
                lower_percentile = st.slider("하한 백분위수", 0.1, 20.0, 5.0, 0.1,
                                           help="하한 임계값으로 사용할 백분위수 (낮을수록 경보가 적게 발생)")
            elif direction == "상한":
                upper_percentile = st.slider("상한 백분위수", 80.0, 99.9, 95.0, 0.1)
                lower_percentile = 0
            else:  # 하한
                upper_percentile = 100
                lower_percentile = st.slider("하한 백분위수", 0.1, 20.0, 5.0, 0.1)
    
    elif threshold_method == "동적 임계값":
        window_col, std_col = st.columns(2)
        
        with window_col:
            window = st.slider("윈도우 크기", 6, 72, 24, 6, 
                             help="이동 평균 및 표준편차 계산에 사용할 데이터 포인트 수")
        
        with std_col:
            n_std = st.slider("표준편차 배수", 1.0, 5.0, 3.0, 0.5,
                            help="임계값 = 이동 평균 ± (표준편차 × 배수)")
    
    elif threshold_method == "이상치 기반 임계값":
        method_col, param_col = st.columns(2)
        
        with method_col:
            anomaly_method = st.selectbox(
                "이상치 탐지 방법",
                ["Z-점수", "IQR", "Local Outlier Factor", "Isolation Forest"],
                help="Z-점수: 표준화된 값의 절대값이 임계값보다 크면 이상치\nIQR: 사분위 범위를 벗어나면 이상치\nLOF: 밀도 기반 이상치 탐지\nIsolation Forest: 트리 기반 이상치 탐지"
            )
        
        with param_col:
            if anomaly_method == "Z-점수":
                zscore_threshold = st.slider("Z-점수 임계값", 2.0, 5.0, 3.0, 0.5,
                                           help="표준화된 값의 절대값이 이 값보다 크면 이상치로 판단")
            elif anomaly_method == "IQR":
                iqr_factor = st.slider("IQR 배수", 1.0, 3.0, 1.5, 0.5,
                                     help="임계값 = Q1/Q3 ± (IQR × 배수)")
            else:  # LOF 또는 Isolation Forest
                contamination = st.slider("오염도", 0.01, 0.1, 0.01, 0.01,
                                        help="데이터셋에서 이상치로 간주될 것으로 예상되는 비율")
    
    # 최적화 기준에 따른 매핑
    if optimization_metric == "거짓 경보 최소화":
        opt_metric = "false_alarm_ratio"
    elif optimization_metric == "경보 발생 횟수 최적화":
        opt_metric = "total_alarms"
    else:  # 경보 이벤트 최적화
        opt_metric = "alarm_events"
    
    # 거짓 경보 정의 설정
    false_alarm_threshold = st.slider(
        "거짓 경보 판단 기준 (연속 데이터 포인트)", 
        1, 10, 3, 1,
        help="이 값보다 짧은 지속 시간의 경보는 거짓 경보로 간주"
    ) 

    # 임계값 계산 및 시각화 버튼
    if st.button("임계값 분석 및 시각화", use_container_width=True):
        with st.spinner("임계값 분석 중..."):
            try:
                # 임계값 방법에 따른 매개변수 설정
                if threshold_method == "고정 임계값":
                    if direction == "양방향":
                        # 양방향 임계값
                        upper_threshold = np.percentile(df_processed[sensor_col], upper_percentile)
                        lower_threshold = np.percentile(df_processed[sensor_col], lower_percentile)
                        best_params, results = optimize_threshold(
                            df_processed, sensor_col, 'fixed',
                            optimization_metric=opt_metric,
                            direction='both',
                            short_alarm_threshold=false_alarm_threshold
                        )
                        # 현재 선택된 매개변수로 성능 평가
                        current_perf = evaluate_threshold_performance(
                            df_processed, sensor_col, 'fixed',
                            upper_threshold=upper_threshold,
                            lower_threshold=lower_threshold,
                            short_alarm_threshold=false_alarm_threshold
                        )
                    elif direction == "상한":
                        # 상한 임계값만
                        threshold_value = np.percentile(df_processed[sensor_col], upper_percentile)
                        best_params, results = optimize_threshold(
                            df_processed, sensor_col, 'fixed',
                            optimization_metric=opt_metric,
                            direction='upper',
                            short_alarm_threshold=false_alarm_threshold
                        )
                        # 현재 선택된 매개변수로 성능 평가
                        current_perf = evaluate_threshold_performance(
                            df_processed, sensor_col, 'fixed',
                            threshold_value=threshold_value,
                            direction='upper',
                            short_alarm_threshold=false_alarm_threshold
                        )
                    else:  # 하한
                        # 하한 임계값만
                        threshold_value = np.percentile(df_processed[sensor_col], lower_percentile)
                        best_params, results = optimize_threshold(
                            df_processed, sensor_col, 'fixed',
                            optimization_metric=opt_metric,
                            direction='lower',
                            short_alarm_threshold=false_alarm_threshold
                        )
                        # 현재 선택된 매개변수로 성능 평가
                        current_perf = evaluate_threshold_performance(
                            df_processed, sensor_col, 'fixed',
                            threshold_value=threshold_value,
                            direction='lower',
                            short_alarm_threshold=false_alarm_threshold
                        )
                
                elif threshold_method == "동적 임계값":
                    best_params, results = optimize_threshold(
                        df_processed, sensor_col, 'dynamic',
                        optimization_metric=opt_metric,
                        windows=[6, 12, 24, 48, 72],
                        n_stds=[2.0, 2.5, 3.0, 3.5, 4.0],
                        short_alarm_threshold=false_alarm_threshold
                    )
                    # 현재 선택된 매개변수로 성능 평가
                    current_perf = evaluate_threshold_performance(
                        df_processed, sensor_col, 'dynamic',
                        window=window,
                        n_std=n_std,
                        short_alarm_threshold=false_alarm_threshold
                    )
                
                elif threshold_method == "이상치 기반 임계값":
                    if anomaly_method == "Z-점수":
                        method = 'zscore'
                        best_params, results = optimize_threshold(
                            df_processed, sensor_col, 'anomaly',
                            optimization_metric=opt_metric,
                            method=method,
                            thresholds=[2.0, 2.5, 3.0, 3.5, 4.0],
                            short_alarm_threshold=false_alarm_threshold
                        )
                        # 현재 선택된 매개변수로 성능 평가
                        current_perf = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': method, 'threshold': zscore_threshold,
                            'short_alarm_threshold': false_alarm_threshold}
                        )
                    
                    elif anomaly_method == "IQR":
                        method = 'iqr'
                        best_params, results = optimize_threshold(
                            df_processed, sensor_col, 'anomaly',
                            optimization_metric=opt_metric,
                            method=method,
                            factor=[1.0, 1.5, 2.0, 2.5, 3.0],  # factors를 factor로 변경
                            short_alarm_threshold=false_alarm_threshold
                        )
                        # 현재 선택된 매개변수로 성능 평가
                        current_perf = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': method, 'factor': iqr_factor,
                            'short_alarm_threshold': false_alarm_threshold}
                        )
                    
                    elif anomaly_method == "Local Outlier Factor":
                        method = 'lof'
                        best_params, results = optimize_threshold(
                            df_processed, sensor_col, 'anomaly',
                            optimization_metric=opt_metric,
                            method=method,
                            contaminations=[0.01, 0.02, 0.05, 0.1],
                            short_alarm_threshold=false_alarm_threshold
                        )
                        # 현재 선택된 매개변수로 성능 평가
                        current_perf = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': method, 'contamination': contamination,
                            'short_alarm_threshold': false_alarm_threshold}
                        )
                    
                    else:  # Isolation Forest
                        method = 'isolation_forest'
                        best_params, results = optimize_threshold(
                            df_processed, sensor_col, 'anomaly',
                            optimization_metric=opt_metric,
                            method=method,
                            contaminations=[0.01, 0.02, 0.05, 0.1],
                            short_alarm_threshold=false_alarm_threshold
                        )
                        # 현재 선택된 매개변수로 성능 평가
                        current_perf = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': method, 'contamination': contamination,
                            'short_alarm_threshold': false_alarm_threshold}
                        )
                
                # 결과 시각화
                st.subheader("임계값 분석 결과")
                
                # 현재 설정과 최적 설정 비교
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**현재 설정 성능**")
                    st.metric("경보 발생 수", f"{current_perf['total_alarms']:,}")
                    st.metric("경보 이벤트 수", f"{current_perf['alarm_events']:,}")
                    st.metric("평균 경보 지속 시간", f"{current_perf['avg_duration']:.2f}")
                    st.metric("거짓 경보 비율", f"{current_perf['false_alarm_ratio']:.2%}")
                
                with col2:
                    st.write("**최적화된 설정 추천**")
                    
                    if threshold_method == "고정 임계값":
                        if 'percentile' in best_params:
                            percentile = best_params['percentile']
                            direction_text = "상한" if best_params['direction'] == 'upper' else "하한"
                            threshold_value = best_params['threshold']
                            st.metric("최적 백분위수", f"{percentile:.1%} ({direction_text})")
                            st.metric("최적 임계값", f"{threshold_value:.2f}")
                    
                    elif threshold_method == "동적 임계값":
                        if 'window' in best_params and 'n_std' in best_params:
                            st.metric("최적 윈도우 크기", f"{best_params['window']}")
                            st.metric("최적 표준편차 배수", f"{best_params['n_std']:.1f}")
                    
                    elif threshold_method == "이상치 기반 임계값":
                        if anomaly_method == "Z-점수" and 'threshold' in best_params:
                            st.metric("최적 Z-점수 임계값", f"{best_params['threshold']:.1f}")
                        elif anomaly_method == "IQR" and 'factor' in best_params:
                            st.metric("최적 IQR 배수", f"{best_params['factor']:.1f}")
                        elif 'contamination' in best_params:
                            st.metric("최적 오염도", f"{best_params['contamination']:.2%}")
                
                # 최적화 결과 시각화
                st.subheader("임계값 최적화 결과")
                
                # 데이터프레임으로 변환
                results_df = pd.DataFrame(results)
                
                # 결과 테이블 표시
                st.dataframe(results_df, use_container_width=True, column_config={
                    col: st.column_config.Column(width="auto") for col in results_df.columns
                })
                
                # 성능 지표 시각화
                if len(results_df) > 0:
                    metric_options = ["false_alarm_ratio", "total_alarms", "alarm_events"]
                    metrics_labels = ["거짓 경보 비율", "경보 발생 수", "경보 이벤트 수"]
                    
                    fig = make_subplots(rows=1, cols=len(metric_options),
                                       subplot_titles=metrics_labels)
                    
                    for i, (metric, label) in enumerate(zip(metric_options, metrics_labels)):
                        if metric in results_df.columns:
                            if threshold_method == "고정 임계값" and 'percentile' in results_df.columns:
                                # 고정 임계값의 경우 백분위수에 따른 지표 변화
                                for direction in results_df['direction'].unique():
                                    dir_df = results_df[results_df['direction'] == direction]
                                    fig.add_trace(
                                        go.Scatter(
                                            x=dir_df['percentile'],
                                            y=dir_df[metric],
                                            mode='lines+markers',
                                            name=f"{direction} ({label})"
                                        ),
                                        row=1, col=i+1
                                    )
                                fig.update_xaxes(title="백분위수", row=1, col=i+1)
                            
                            elif threshold_method == "동적 임계값" and 'window' in results_df.columns and 'n_std' in results_df.columns:
                                # 동적 임계값의 경우 윈도우와 표준편차에 따른 지표
                                for window in results_df['window'].unique():
                                    win_df = results_df[results_df['window'] == window]
                                    fig.add_trace(
                                        go.Scatter(
                                            x=win_df['n_std'],
                                            y=win_df[metric],
                                            mode='lines+markers',
                                            name=f"윈도우 {window} ({label})"
                                        ),
                                        row=1, col=i+1
                                    )
                                fig.update_xaxes(title="표준편차 배수", row=1, col=i+1)
                            
                            elif threshold_method == "이상치 기반 임계값":
                                if anomaly_method == "Z-점수" and 'threshold' in results_df.columns:
                                    # Z-점수 임계값에 따른 지표
                                    fig.add_trace(
                                        go.Scatter(
                                            x=results_df['threshold'],
                                            y=results_df[metric],
                                            mode='lines+markers',
                                            name=label
                                        ),
                                        row=1, col=i+1
                                    )
                                    fig.update_xaxes(title="Z-점수 임계값", row=1, col=i+1)
                                
                                elif 'contamination' in results_df.columns:
                                    # 오염도에 따른 지표
                                    fig.add_trace(
                                        go.Scatter(
                                            x=results_df['contamination'],
                                            y=results_df[metric],
                                            mode='lines+markers',
                                            name=label
                                        ),
                                        row=1, col=i+1
                                    )
                                    fig.update_xaxes(title="오염도", row=1, col=i+1)
                    
                    fig.update_layout(height=400, showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
                
                # 실제 데이터에 임계값 적용 시각화
                st.subheader("임계값 적용 시각화")
                
                # 기본 시계열 차트
                fig_ts = go.Figure()
                
                # 시간 범위 제한 (가시성을 위해)
                display_points = min(2000, len(df_processed))
                display_df = df_processed.sort_values('timestamp').tail(display_points).copy()
                
                # 시계열 데이터 추가
                fig_ts.add_trace(
                    go.Scatter(
                        x=display_df['timestamp'],
                        y=display_df[sensor_col],
                        mode='lines',
                        name=sensor_type_display,
                        line=dict(color='royalblue')
                    )
                )
                
                # 임계값 유형에 따라 다른 시각화
                if threshold_method == "고정 임계값":
                    if direction == "양방향":
                        # 상한 임계값 계산
                        upper_threshold = np.percentile(df_processed[sensor_col], upper_percentile)
                        # 하한 임계값 계산
                        lower_threshold = np.percentile(df_processed[sensor_col], lower_percentile)
                        
                        # 상한 임계값 선 추가
                        fig_ts.add_trace(
                            go.Scatter(
                                x=display_df['timestamp'],
                                y=[upper_threshold] * len(display_df),
                                mode='lines',
                                name=f"상한 ({upper_percentile:.1f}%)",
                                line=dict(color='red', dash='dash')
                            )
                        )
                        # 하한 임계값 선 추가
                        fig_ts.add_trace(
                            go.Scatter(
                                x=display_df['timestamp'],
                                y=[lower_threshold] * len(display_df),
                                mode='lines',
                                name=f"하한 ({lower_percentile:.1f}%)",
                                line=dict(color='orange', dash='dash')
                            )
                        )
                    elif direction == "상한":
                        # 상한 임계값 계산
                        threshold_value = np.percentile(df_processed[sensor_col], upper_percentile)
                        # 상한 임계값 선 추가
                        fig_ts.add_trace(
                            go.Scatter(
                                x=display_df['timestamp'],
                                y=[threshold_value] * len(display_df),
                                mode='lines',
                                name=f"상한 ({upper_percentile:.1f}%)",
                                line=dict(color='red', dash='dash')
                            )
                        )
                    else:  # 하한
                        # 하한 임계값 계산
                        threshold_value = np.percentile(df_processed[sensor_col], lower_percentile)
                        # 하한 임계값 선 추가
                        fig_ts.add_trace(
                            go.Scatter(
                                x=display_df['timestamp'],
                                y=[threshold_value] * len(display_df),
                                mode='lines',
                                name=f"하한 ({lower_percentile:.1f}%)",
                                line=dict(color='orange', dash='dash')
                            )
                        )
                
                elif threshold_method == "동적 임계값":
                    # 동적 임계값 계산
                    dyn_df = calculate_dynamic_thresholds(display_df, sensor_col, window, n_std)
                    
                    # 상한 임계값
                    fig_ts.add_trace(
                        go.Scatter(
                            x=dyn_df['timestamp'],
                            y=dyn_df['upper_threshold'],
                            mode='lines',
                            name=f"상한 (이동평균 + {n_std}σ)",
                            line=dict(color='red', dash='dash')
                        )
                    )
                    
                    # 하한 임계값
                    fig_ts.add_trace(
                        go.Scatter(
                            x=dyn_df['timestamp'],
                            y=dyn_df['lower_threshold'],
                            mode='lines',
                            name=f"하한 (이동평균 - {n_std}σ)",
                            line=dict(color='orange', dash='dash')
                        )
                    )
                    
                    # 이동 평균선
                    fig_ts.add_trace(
                        go.Scatter(
                            x=dyn_df['timestamp'],
                            y=dyn_df['moving_avg'],
                            mode='lines',
                            name=f"이동 평균 (윈도우: {window})",
                            line=dict(color='green', dash='dot')
                        )
                    )
                
                elif threshold_method == "이상치 기반 임계값":
                    # 이상치 탐지 - 명시적 파라미터 전달 방식 사용
                    if anomaly_method == "Z-점수":
                        anomaly_df = detect_anomalies(display_df, sensor_col, method='zscore', threshold=zscore_threshold)
                    elif anomaly_method == "IQR":
                        anomaly_df = detect_anomalies(display_df, sensor_col, method='iqr', factor=iqr_factor)
                    elif anomaly_method == "Local Outlier Factor":
                        anomaly_df = detect_anomalies(display_df, sensor_col, method='lof', contamination=contamination)
                    else:  # Isolation Forest
                        anomaly_df = detect_anomalies(display_df, sensor_col, method='isolation_forest', contamination=contamination)
                    
                    # 이상치 포인트 추가
                    anomaly_points = anomaly_df[anomaly_df['anomaly']]
                    fig_ts.add_trace(
                        go.Scatter(
                            x=anomaly_points['timestamp'],
                            y=anomaly_points[sensor_col],
                            mode='markers',
                            name='이상치',
                            marker=dict(color='red', size=8, symbol='x')
                        )
                    )
                
                fig_ts.update_layout(
                    title=f"{equipment_type} {sensor_type_display} 값과 경보 임계값",
                    xaxis_title="시간",
                    yaxis_title=sensor_type_display,
                    height=500,
                    # 인터랙티브 옵션 강화
                    hovermode='closest',
                    dragmode='pan',  # 기본적으로 패닝 모드 활성화
                    # 차트 상호작용 설정 추가
                    xaxis=dict(
                        rangeslider=dict(visible=True),  # 범위 슬라이더 추가
                        type='date',
                        autorange=True,
                    ),
                    modebar=dict(
                        orientation='v',
                        remove=['autoScale2d', 'lasso2d', 'select2d']  # 불필요한 도구 제거
                    ),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                # 확대/축소 버튼 표시 옵션 추가
                config = {'displayModeBar': True, 'scrollZoom': True}
                st.plotly_chart(fig_ts, use_container_width=True, config=config)
                
                # 경보 발생 횟수 분포 시각화
                st.subheader("시간대별 경보 발생 분포")
                
                # 현재 설정으로 경보 적용
                if threshold_method == "고정 임계값":
                    if direction == "양방향":
                        alarm_df = evaluate_threshold_performance(
                            df_processed, sensor_col, 'fixed',
                            upper_threshold=upper_threshold,
                            lower_threshold=lower_threshold
                        )['df_with_alarms']
                    elif direction == "상한":
                        threshold_value = np.percentile(df_processed[sensor_col], upper_percentile)
                        alarm_df = evaluate_threshold_performance(
                            df_processed, sensor_col, 'fixed',
                            threshold_value=threshold_value,
                            direction='upper'
                        )['df_with_alarms']
                    else:  # 하한
                        threshold_value = np.percentile(df_processed[sensor_col], lower_percentile)
                        alarm_df = evaluate_threshold_performance(
                            df_processed, sensor_col, 'fixed',
                            threshold_value=threshold_value,
                            direction='lower'
                        )['df_with_alarms']
                elif threshold_method == "동적 임계값":
                    alarm_df = evaluate_threshold_performance(
                        df_processed, sensor_col, 'dynamic',
                        window=window,
                        n_std=n_std
                    )['df_with_alarms']
                else:  # 이상치 기반
                    if anomaly_method == "Z-점수":
                        alarm_df = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': 'zscore', 'threshold': zscore_threshold}
                        )['df_with_alarms']
                    elif anomaly_method == "IQR":
                        alarm_df = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': 'iqr', 'factor': iqr_factor}
                        )['df_with_alarms']
                    elif anomaly_method == "Local Outlier Factor":
                        alarm_df = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': 'lof', 'contamination': contamination}
                        )['df_with_alarms']
                    else:  # Isolation Forest
                        alarm_df = evaluate_threshold_performance(
                            df_processed, sensor_col, 'anomaly',
                            **{'method': 'isolation_forest', 'contamination': contamination}
                        )['df_with_alarms']
                
                # 시간대별 경보 분포 계산
                alarm_df['hour'] = alarm_df['timestamp'].dt.hour
                alarm_df['weekday'] = alarm_df['timestamp'].dt.dayofweek
                
                # 요일별, 시간별 경보 발생 횟수
                hour_alarm_count = alarm_df[alarm_df['alarm']].groupby('hour').size()
                weekday_alarm_count = alarm_df[alarm_df['alarm']].groupby('weekday').size()
                
                # 히트맵 데이터 준비
                heatmap_df = alarm_df[alarm_df['alarm']].groupby(['weekday', 'hour']).size().reset_index(name='count')
                
                # 모든 요일(0-6)과 시간(0-23)의 조합 생성
                all_weekdays = pd.DataFrame({'weekday': range(7)})
                all_hours = pd.DataFrame({'hour': range(24)})
                all_combinations = all_weekdays.assign(key=1).merge(all_hours.assign(key=1), on='key').drop('key', axis=1)
                
                # 실제 데이터와 모든 조합 병합 (데이터가 없는 경우 0으로 채움)
                complete_heatmap_df = pd.merge(all_combinations, heatmap_df, on=['weekday', 'hour'], how='left').fillna(0)
                
                # 피벗 테이블 생성
                heatmap_pivot = complete_heatmap_df.pivot_table(index='weekday', columns='hour', values='count', fill_value=0)
                
                # 요일 및 시간 레이블
                weekday_labels = ['월', '화', '수', '목', '금', '토', '일']
                hour_labels = [f"{h}시" for h in range(24)]
                
                # 히트맵 그리기
                fig_heatmap = px.imshow(
                    heatmap_pivot,
                    labels=dict(x="시간", y="요일", color="경보 수"),
                    x=list(range(24)),
                    y=weekday_labels,
                    color_continuous_scale='Reds'
                )
                
                fig_heatmap.update_xaxes(
                    title="시간",
                    tickvals=list(range(24)),
                    ticktext=hour_labels
                )
                
                fig_heatmap.update_layout(
                    title="요일 및 시간대별 경보 발생 분포",
                    height=400
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # 경보 지속시간 분포
                st.subheader("경보 지속시간 분포")
                
                # 연속된 경보 이벤트 추출
                alarm_events = alarm_df[alarm_df['alarm']].groupby('alarm_event').size().reset_index(name='duration')
                
                # 지속시간 히스토그램
                if not alarm_events.empty:
                    fig_duration = px.histogram(
                        alarm_events,
                        x='duration',
                        nbins=20,
                        labels={'duration': '경보 지속시간 (데이터 포인트)', 'count': '발생 횟수'},
                        title="경보 지속시간 분포"
                    )
                    
                    fig_duration.update_layout(height=400)
                    st.plotly_chart(fig_duration, use_container_width=True)
                    
                    # 거짓 경보와 실제 경보 비율 파이 차트
                    false_alarms = sum(1 for d in alarm_events['duration'] if d < false_alarm_threshold)
                    true_alarms = len(alarm_events) - false_alarms
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['거짓 경보', '실제 경보'],
                        values=[false_alarms, true_alarms],
                        hole=.3,
                        marker_colors=['#FF6B6B', '#4CAF50']
                    )])
                    
                    fig_pie.update_layout(
                        title="거짓 경보 vs 실제 경보 비율",
                        height=400
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("선택한 임계값으로 발생한 경보가 없습니다.")
            
            except Exception as e:
                st.error(f"임계값 분석 중 오류가 발생했습니다: {str(e)}")
    
    # AI 분석 부분 호출
    render_ai_analysis(
        df=df_processed,
        equipment_type=equipment_type,
        sensor_type_display=sensor_type_display,
        threshold_method=threshold_method
    ) 

def render_ai_analysis(df, equipment_type, sensor_type_display, threshold_method):
    """경보 및 임계값 설정을 위한 AI 분석 부분을 구현합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 알람 임계값 분석 전용 키 접두사 사용
    key_prefix = "alarm_threshold_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 임계값 설정을 세션 상태에 저장
    current_config_key = f"{key_prefix}_current_config"
    
    # 임계값 설정이 변경되었는지 확인
    config_changed = False
    if current_config_key in st.session_state:
        current_config = st.session_state[current_config_key]
        if current_config["threshold_method"] != threshold_method:
            config_changed = True
    else:
        # 최초 실행 시
        config_changed = True
    
    # 현재 임계값 설정 업데이트
    st.session_state[current_config_key] = {
        "threshold_method": threshold_method
    }
    
    # AI 분석 프롬프트 키
    threshold_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 임계값 설정이 변경되었거나 프롬프트가 없으면 새로 생성
    if config_changed or threshold_prompt_key not in st.session_state:
        # 임계값 방법에 대한 설명 추가
        method_description = ""
        method_context = ""
        
        if threshold_method == "고정 임계값":
            method_description = "고정 임계값은 백분위수나 표준편차를 기반으로 한 정적 임계값입니다."
            method_context = "고정 임계값은 설정이 간단하고 이해하기 쉽지만, 시간에 따른 데이터 패턴 변화를 고려하지 못합니다."
        elif threshold_method == "동적 임계값":
            method_description = "동적 임계값은 이동 평균과 표준편차를 기반으로 시간에 따라 변화하는 임계값입니다."
            method_context = "동적 임계값은 시간에 따른 데이터 패턴 변화를 고려하여 더 민감한 알람을 제공하지만, 윈도우 크기와 표준편차 배수 설정이 중요합니다."
        else:  # "이상치 기반 임계값"
            method_description = "이상치 기반 임계값은 Z-점수, IQR, LOF, Isolation Forest 등의 이상치 탐지 알고리즘을 사용합니다."
            method_context = "이상치 기반 임계값은 데이터의 전체적인 분포를 고려하여 이상치를 탐지하지만, 복잡한 설정이 필요하고 계산 비용이 높을 수 있습니다."
        
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 경보 및 임계값 설정에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {threshold_method} 방법을 사용하여 경보 임계값을 설정했습니다.
이 임계값 설정 방법은 {method_description}

임계값 설정 컨텍스트: {method_context}

주요 분석 포인트:
1. 선택한 임계값 설정 방법의 장단점
2. 거짓 경보 최소화를 위한 최적화 방안
3. 각 임계값 설정 방법별 적합한 사용 시나리오
4. 효과적인 알람 시스템 구축을 위한 전략
5. 임계값 설정이 설비 모니터링에 미치는 영향
"""
        
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 경보 및 임계값 설정에 대한 분석입니다.

## 경보 및 임계값 설정 정보
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 임계값 설정 방법: {threshold_method}

## 임계값 설정 방법별 특성
### 고정 임계값
- 특징: 백분위수나 표준편차를 기반으로 한 정적 임계값
- 장점: 설정이 간단하고 이해하기 쉬움, 계산 비용이 낮음
- 단점: 시간에 따른 데이터 패턴 변화를 고려하지 못함
- 적합한 시나리오: 데이터 패턴이 안정적인 경우, 명확한 안전 한계가 있는 경우

### 동적 임계값
- 특징: 이동 평균과 표준편차를 기반으로 시간에 따라 변화하는 임계값
- 장점: 시간에 따른 패턴 변화를 고려하여 더 민감한 알람 제공
- 단점: 윈도우 크기와 표준편차 배수 설정이 중요, 급격한 변화에 대한 대응이 느릴 수 있음
- 적합한 시나리오: 일간/주간 패턴이 있는 데이터, 점진적인 변화가 있는 시스템

### 이상치 기반 임계값
- 특징: Z-점수, IQR, LOF, Isolation Forest 등의 이상치 탐지 알고리즘 사용
- 장점: 데이터의 전체적인 분포를 고려, 복잡한 패턴에서도 이상치 탐지 가능
- 단점: 복잡한 설정 필요, 계산 비용이 높을 수 있음
- 적합한 시나리오: 복잡한 다변량 데이터, 이상치가 명확하지 않은 시스템

## 거짓 경보 최소화 전략
1. 적절한 임계값 설정: 너무 엄격한 임계값은 거짓 경보를 증가시킴
2. 지속 시간 필터링: 짧은 지속 시간의 경보는 거짓 경보일 가능성이 높음
3. 다중 조건 알람: 여러 조건이 동시에 충족될 때만 경보 발생
4. 알람 딜레이: 임계값 초과 후 일정 시간 동안 지속되는 경우에만 경보 발생

## 분석 과제
위 정보를 바탕으로 {equipment_type}의 {sensor_type_display} 데이터에 대한 경보 및 임계값 설정 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {threshold_method}의 장단점 및 이 방법이 {equipment_type}의 {sensor_type_display} 모니터링에 적합한 이유
2. 거짓 경보를 최소화하면서 중요한 이벤트를 놓치지 않기 위한 최적의 임계값 설정 전략
3. 경보 시스템의 효율성을 평가하는 주요 지표와 이를 개선하는 방법
4. 다양한 임계값 설정 방법의 비교 및 사용 시나리오별 추천 방법
5. {equipment_type}의 효과적인 모니터링을 위한 경보 시스템 구축 방안

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요.
"""
        
        # 임계값 전용 프롬프트로 저장
        st.session_state[threshold_prompt_key] = analysis_prompt
        
        # 설정이 변경되면 캐시도 초기화
        if config_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"임계값 설정이 변경되어 캐시 초기화: {threshold_method}")
        
        # 디버깅용 로깅
        print(f"임계값 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
    else:
        # 캐시된 임계값 전용 프롬프트 사용
        analysis_prompt = st.session_state[threshold_prompt_key]
        print(f"캐시된 임계값 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 경보 및 임계값 설정 분석")

    # 세션 상태 키 정의 - 모두 임계값 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 임계값 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 임계값 분석 전용
    def on_threshold_analyze_click():
        # 캐시 초기화
        if cache_state_key in st.session_state:
            # 캐시 키 생성
            from ..utils.ai_utils import generate_cache_key
            cache_key = generate_cache_key(
                prompt=analysis_prompt,
                model=st.session_state.selected_model,
                temperature=st.session_state.temperature
            )
            st.session_state[cache_state_key].pop(cache_key, None)
        # 대화 기록 초기화
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
        # 실행 상태 설정
        st.session_state[running_key] = True
        
        # 디버깅용 로깅
        print(f"임계값 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 임계값 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 경보 임계값 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_threshold_analyze_click,
            use_container_width=True
        )
    
    # 이전 분석 결과가 있는 경우 (캐시에 있는 경우)
    if cache_state_key in st.session_state and len(st.session_state[cache_state_key]) > 0:
        # 캐시 키 생성
        from ..utils.ai_utils import generate_cache_key
        cache_key = generate_cache_key(
            prompt=analysis_prompt,
            model=st.session_state.selected_model,
            temperature=st.session_state.temperature
        )
        
        if cache_key in st.session_state[cache_state_key]:
            cached_response = st.session_state[cache_state_key][cache_key]
            with st.chat_message("assistant"):
                st.markdown(cached_response["response"])
                if cached_response.get("metadata"):
                    metadata_text = "\n\n---\n**처리 정보**\n```json\n"
                    metadata_text += json.dumps(cached_response["metadata"], indent=2, ensure_ascii=False)
                    metadata_text += "\n```"
                    st.markdown(metadata_text)
            # 실행 상태 업데이트
            st.session_state[running_key] = False
            print(f"임계값 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"임계값 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 경보 및 임계값 설정을 분석하고 있습니다..."):
                print(f"임계값 분석: generate_ai_response 함수 호출 전")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"임계값 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 경보 임계값 분석 실행' 버튼을 클릭하세요. 임계값 설정 방법에 대한 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 경보 및 임계값 설정에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"임계값: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 경보 및 임계값 설정에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 