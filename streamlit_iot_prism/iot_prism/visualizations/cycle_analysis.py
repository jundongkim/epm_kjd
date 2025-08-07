import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json
import time
import concurrent.futures
import multiprocessing

# 성능 최적화를 위한 CPU 코어 수 확인
NUM_CORES = multiprocessing.cpu_count()

def detect_cycles(df, sensor_col, threshold=None, smooth_window=5, show_progress=True):
    """
    운전/정지 주기를 감지하는 함수
    
    Args:
        df (DataFrame): 분석할 데이터프레임
        sensor_col (str): 센서 값 열 이름
        threshold (float, optional): 운전/정지 구분 임계값. None인 경우 자동 계산
        smooth_window (int): 이동 평균 윈도우 크기
        show_progress (bool): 진행 상태 표시 여부
        
    Returns:
        tuple: (주기 정보 데이터프레임, 임계값)
    """
    # 데이터 복사
    data = df.copy()
    
    # 진행 상태 표시를 위한 전체 단계 설정
    total_steps = 7
    current_step = 0
    
    if show_progress:
        progress_bar = st.progress(0, "주기 분석 진행 중...")
        status_text = st.empty()
        
        status_text.text(f"단계 {current_step+1}/{total_steps}: 데이터 전처리 중...")
    
    # 시간순으로 정렬
    if 'timestamp' in data.columns:
        data = data.sort_values('timestamp')
    
    current_step += 1
    if show_progress:
        progress_bar.progress(current_step/total_steps, f"주기 분석 진행 중... ({int(current_step/total_steps*100)}%)")
        status_text.text(f"단계 {current_step+1}/{total_steps}: 이동 평균 계산 중...")
    
    # 이동 평균으로 노이즈 감소
    if smooth_window > 1:
        data[f'{sensor_col}_smooth'] = data[sensor_col].rolling(window=smooth_window, center=True).mean()
        data[f'{sensor_col}_smooth'].fillna(data[sensor_col], inplace=True)
    else:
        data[f'{sensor_col}_smooth'] = data[sensor_col]
    
    current_step += 1
    if show_progress:
        progress_bar.progress(current_step/total_steps, f"주기 분석 진행 중... ({int(current_step/total_steps*100)}%)")
        status_text.text(f"단계 {current_step+1}/{total_steps}: 임계값 계산 중...")
    
    # 임계값 자동 계산 (값 분포의 중앙값 사용)
    if threshold is None:
        # 값 분포 분석 - 벡터화된 연산 사용
        q1 = data[sensor_col].quantile(0.25)
        q3 = data[sensor_col].quantile(0.75)
        data_range = data[sensor_col].max() - data[sensor_col].min()
        
        # 값 분포가 양봉 형태이면 (운전/정지가 명확하게 구분되면)
        if (q3 - q1) > (data_range * 0.4):
            threshold = (data[sensor_col].max() + data[sensor_col].min()) / 2
        else:
            # 분포가 양봉 형태가 아니면 중앙값 근처를 임계값으로 사용
            threshold = data[sensor_col].median()
    
    current_step += 1
    if show_progress:
        progress_bar.progress(current_step/total_steps, f"주기 분석 진행 중... ({int(current_step/total_steps*100)}%)")
        status_text.text(f"단계 {current_step+1}/{total_steps}: 운전/정지 상태 계산 중...")
    
    # 운전/정지 상태 결정 (1: 운전, 0: 정지)
    data['state'] = (data[f'{sensor_col}_smooth'] > threshold).astype(int)
    
    # 상태 변화 감지
    data['state_change'] = data['state'].diff().fillna(0)
    
    current_step += 1
    if show_progress:
        progress_bar.progress(current_step/total_steps, f"주기 분석 진행 중... ({int(current_step/total_steps*100)}%)")
        status_text.text(f"단계 {current_step+1}/{total_steps}: 주기 시작/종료 시점 감지 중...")
    
    # 주기 시작/종료 인덱스 찾기
    start_indices = data[data['state_change'] == 1].index.tolist()
    end_indices = data[data['state_change'] == -1].index.tolist()
    
    # 데이터가 운전 상태로 시작하면 첫 번째 시작 인덱스 추가
    if data['state'].iloc[0] == 1 and (not start_indices or start_indices[0] > 0):
        start_indices.insert(0, 0)
    
    # 데이터가 운전 상태로 끝나면 마지막 종료 인덱스 추가
    if data['state'].iloc[-1] == 1 and (not end_indices or end_indices[-1] < len(data) - 1):
        end_indices.append(len(data) - 1)
    
    current_step += 1
    if show_progress:
        progress_bar.progress(current_step/total_steps, f"주기 분석 진행 중... ({int(current_step/total_steps*100)}%)")
        status_text.text(f"단계 {current_step+1}/{total_steps}: 운전 주기 분석 중...")
    
    # 주기 정보 수집
    cycles = []
    
    # 주기 처리 함수
    def process_cycle(i):
        if i >= min(len(start_indices), len(end_indices)):
            return None
            
        start_idx = start_indices[i]
        end_idx = end_indices[i]
        
        # 주기 시작/종료 시간
        if 'timestamp' in data.columns:
            start_time = data.loc[start_idx, 'timestamp']
            end_time = data.loc[end_idx, 'timestamp']
            duration = (end_time - start_time).total_seconds() / 60  # 분 단위
        else:
            start_time = start_idx
            end_time = end_idx
            duration = end_idx - start_idx  # 데이터 포인트 수
        
        # 주기 동안의 센서 값 통계 - 시작점은 포함하고 끝점은 제외
        if start_idx == end_idx:  # 같은 인덱스인 경우 (매우 짧은 주기)
            cycle_data = data.loc[[start_idx], sensor_col]
        else:
            # 상태 전환점(end_idx)은 제외하고 그 이전까지만 포함
            cycle_data = data.loc[start_idx:end_idx-1, sensor_col]
            
        avg_value = cycle_data.mean()
        max_value = cycle_data.max()
        min_value = cycle_data.min()
        
        return {
            'cycle_id': i + 1,
            'start_time': start_time,
            'end_time': end_time,
            'duration_min': duration,
            'avg_value': avg_value,
            'max_value': max_value,
            'min_value': min_value
        }
    
    # 병렬 처리 실행 (코어 수 기반)
    if min(len(start_indices), len(end_indices)) > 10:  # 충분한 수의 주기가 있을 때만 병렬 처리
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CORES) as executor:
            results = list(executor.map(process_cycle, range(min(len(start_indices), len(end_indices)))))
            cycles = [r for r in results if r is not None]
    else:
        # 주기가 적을 경우 일반 반복문으로 처리
        for i in range(min(len(start_indices), len(end_indices))):
            cycle = process_cycle(i)
            if cycle:
                cycles.append(cycle)
    
    current_step += 1
    if show_progress:
        progress_bar.progress(current_step/total_steps, f"주기 분석 진행 중... ({int(current_step/total_steps*100)}%)")
        status_text.text(f"단계 {current_step+1}/{total_steps}: 정지 주기 분석 중...")
    
    # 정지 주기 분석 (운전 주기 사이의 시간)
    stop_cycles = []
    
    # 정지 주기 처리 함수
    def process_stop_cycle(i):
        if i >= min(len(end_indices), len(start_indices) - 1):
            return None
            
        stop_start_idx = end_indices[i]
        stop_end_idx = start_indices[i + 1]
        
        # 정지 시작/종료 시간
        if 'timestamp' in data.columns:
            stop_start_time = data.loc[stop_start_idx, 'timestamp']
            stop_end_time = data.loc[stop_end_idx, 'timestamp']
            stop_duration = (stop_end_time - stop_start_time).total_seconds() / 60  # 분 단위
        else:
            stop_start_time = stop_start_idx
            stop_end_time = stop_end_idx
            stop_duration = stop_end_idx - stop_start_idx  # 데이터 포인트 수
        
        # 주기 동안의 센서 값 통계 - 정지 상태(state=0)인 데이터만 포함
        if stop_start_idx == stop_end_idx:  # 같은 인덱스인 경우 (매우 짧은 주기)
            # 동일 인덱스는 정지 주기로 간주하지 않음
            return None
        else:
            # 시작점과 끝점을 제외한 인덱스 범위에서
            idx_range = range(stop_start_idx+1, stop_end_idx)
            if not idx_range:  # 범위가 비어있으면 건너뛰기
                return None
                
            # 경계에 추가 안전 마진 적용 (범위가 충분히 넓은 경우)
            margin = 1  # 기본 마진
            if len(idx_range) > 4:  # 충분히 넓은 경우 마진 증가
                margin = 2
                
            # 마진 적용 (단, 범위가 너무 좁아지지 않도록)
            filtered_range = range(stop_start_idx+1+margin, stop_end_idx-margin) if len(idx_range) > 2*margin else idx_range
            if not filtered_range:  # 마진 적용 후 비어있으면 원래 범위 사용
                filtered_range = idx_range
                
            # state=0인 데이터만 필터링
            valid_indices = [idx for idx in filtered_range if data.loc[idx, 'state'] == 0]
            
            if not valid_indices:  # 유효한 인덱스가 없으면 건너뛰기
                return None
                
            stop_cycle_data = data.loc[valid_indices, sensor_col]
        
        # 데이터가 비어있으면 건너뛰기
        if stop_cycle_data.empty:
            return None
        
        stop_avg_value = stop_cycle_data.mean()
        stop_max_value = stop_cycle_data.max()
        stop_min_value = stop_cycle_data.min()
        
        return {
            'cycle_id': i + 1,
            'start_time': stop_start_time,
            'end_time': stop_end_time,
            'duration_min': stop_duration,
            'avg_value': stop_avg_value,
            'max_value': stop_max_value,
            'min_value': stop_min_value
        }
    
    if len(end_indices) > 0 and len(start_indices) > 1:
        # 병렬 처리 실행
        if min(len(end_indices), len(start_indices) - 1) > 10:  # 충분한 수의 주기가 있을 때만 병렬 처리
            with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CORES) as executor:
                results = list(executor.map(process_stop_cycle, range(min(len(end_indices), len(start_indices) - 1))))
                stop_cycles = [r for r in results if r is not None]
        else:
            # 주기가 적을 경우 일반 반복문으로 처리
            for i in range(min(len(end_indices), len(start_indices) - 1)):
                stop_cycle = process_stop_cycle(i)
                if stop_cycle:
                    stop_cycles.append(stop_cycle)
    
    # 데이터프레임으로 변환
    cycles_df = pd.DataFrame(cycles) if cycles else pd.DataFrame()
    stop_cycles_df = pd.DataFrame(stop_cycles) if stop_cycles else pd.DataFrame()
    
    # 프로그레스 바 완료 표시
    if show_progress:
        progress_bar.progress(1.0, "주기 분석 완료!")
        time.sleep(0.5)  # 완료 메시지를 잠시 표시
        progress_bar.empty()
        status_text.empty()
    
    return cycles_df, stop_cycles_df, threshold, data

def analyze_cycles(cycles_df, stop_cycles_df):
    """
    운전/정지 주기를 분석하여 통계 정보를 반환하는 함수
    
    Args:
        cycles_df (DataFrame): 운전 주기 정보 데이터프레임
        stop_cycles_df (DataFrame): 정지 주기 정보 데이터프레임
        
    Returns:
        dict: 주기 분석 결과
    """
    result = {}
    
    # 운전 주기 통계
    if not cycles_df.empty:
        result['operation_count'] = len(cycles_df)
        result['operation_avg_duration'] = cycles_df['duration_min'].mean()
        result['operation_std_duration'] = cycles_df['duration_min'].std()
        result['operation_min_duration'] = cycles_df['duration_min'].min()
        result['operation_max_duration'] = cycles_df['duration_min'].max()
        result['operation_avg_value'] = cycles_df['avg_value'].mean()
        
        # 이상 주기 분석 (지속 시간 기준)
        duration_mean = cycles_df['duration_min'].mean()
        duration_std = cycles_df['duration_min'].std()
        duration_threshold = 2.0  # Z-score 임계값
        
        # Z-score 계산
        cycles_df['duration_zscore'] = (cycles_df['duration_min'] - duration_mean) / duration_std if duration_std > 0 else 0
        
        # 센서값 기준 Z-score 계산 추가
        for value_col in ['avg_value', 'max_value', 'min_value']:
            if value_col in cycles_df.columns:
                value_mean = cycles_df[value_col].mean()
                value_std = cycles_df[value_col].std()
                cycles_df[f'{value_col}_zscore'] = (cycles_df[value_col] - value_mean) / value_std if value_std > 0 else 0
        
        # 이상 주기 식별 (지속 시간)
        anomalous_cycles = cycles_df[abs(cycles_df['duration_zscore']) > duration_threshold]
        result['operation_anomalous_cycles'] = anomalous_cycles.to_dict('records') if not anomalous_cycles.empty else []
        result['operation_anomalous_count'] = len(anomalous_cycles)
        
        # 이상 주기 식별 (센서값 기준)
        sensor_anomalous_cycles = cycles_df[
            (abs(cycles_df['avg_value_zscore']) > duration_threshold) | 
            (abs(cycles_df['max_value_zscore']) > duration_threshold) | 
            (abs(cycles_df['min_value_zscore']) > duration_threshold)
        ]
        result['operation_sensor_anomalous_cycles'] = sensor_anomalous_cycles.to_dict('records') if not sensor_anomalous_cycles.empty else []
        result['operation_sensor_anomalous_count'] = len(sensor_anomalous_cycles)
    else:
        result['operation_count'] = 0
        result['operation_anomalous_count'] = 0
        result['operation_sensor_anomalous_count'] = 0
    
    # 정지 주기 통계
    if not stop_cycles_df.empty:
        result['stop_count'] = len(stop_cycles_df)
        result['stop_avg_duration'] = stop_cycles_df['duration_min'].mean()
        result['stop_std_duration'] = stop_cycles_df['duration_min'].std()
        result['stop_min_duration'] = stop_cycles_df['duration_min'].min()
        result['stop_max_duration'] = stop_cycles_df['duration_min'].max()
        result['stop_avg_value'] = stop_cycles_df['avg_value'].mean()
        
        # 이상 주기 분석 (지속 시간 기준)
        stop_duration_mean = stop_cycles_df['duration_min'].mean()
        stop_duration_std = stop_cycles_df['duration_min'].std()
        stop_duration_threshold = 2.0  # Z-score 임계값
        
        # Z-score 계산
        stop_cycles_df['duration_zscore'] = (stop_cycles_df['duration_min'] - stop_duration_mean) / stop_duration_std if stop_duration_std > 0 else 0
        
        # 센서값 기준 Z-score 계산 추가
        for value_col in ['avg_value', 'max_value', 'min_value']:
            if value_col in stop_cycles_df.columns:
                value_mean = stop_cycles_df[value_col].mean()
                value_std = stop_cycles_df[value_col].std()
                stop_cycles_df[f'{value_col}_zscore'] = (stop_cycles_df[value_col] - value_mean) / value_std if value_std > 0 else 0
        
        # 이상 주기 식별
        stop_anomalous_cycles = stop_cycles_df[abs(stop_cycles_df['duration_zscore']) > stop_duration_threshold]
        result['stop_anomalous_cycles'] = stop_anomalous_cycles.to_dict('records') if not stop_anomalous_cycles.empty else []
        result['stop_anomalous_count'] = len(stop_anomalous_cycles)
        
        # 이상 주기 식별 (센서값 기준)
        stop_sensor_anomalous_cycles = stop_cycles_df[
            (abs(stop_cycles_df['avg_value_zscore']) > stop_duration_threshold) | 
            (abs(stop_cycles_df['max_value_zscore']) > stop_duration_threshold) | 
            (abs(stop_cycles_df['min_value_zscore']) > stop_duration_threshold)
        ]
        result['stop_sensor_anomalous_cycles'] = stop_sensor_anomalous_cycles.to_dict('records') if not stop_sensor_anomalous_cycles.empty else []
        result['stop_sensor_anomalous_count'] = len(stop_sensor_anomalous_cycles)
    else:
        result['stop_count'] = 0
        result['stop_anomalous_count'] = 0
        result['stop_sensor_anomalous_count'] = 0
    
    return result

def render_cycle_analysis_ui(df):
    """주기 분석 UI를 렌더링하는 함수"""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # 세션 상태 초기화 (AI 분석용) - 먼저 AI 설정 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    st.title("주기 분석")
    
    # 데이터프레임이 없는 경우 처리
    if df is None or df.empty:
        st.warning("분석할 데이터가 없습니다.")
        return
    
    # Get equipment type using the helper function
    equipment_type = get_equipment_type()
    
    # 센서 유형 선택
    sensor_type = get_sensor_type()

    if sensor_type not in df.columns:
        sensor_type = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시
    st.info(f"분석 대상 센서: {sensor_type}")

    # 세션 상태 키
    RESULTS_KEY = "cycle_analysis_results"
    ANALYZED_KEY = "cycle_analysis_analyzed"
    
    # 세션 상태 초기화
    if ANALYZED_KEY not in st.session_state:
        st.session_state[ANALYZED_KEY] = False
    
    # 주기 분석 설정
    st.markdown("## 주기 분석 설정")
    
    with st.expander("주기 감지 설정", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 임계값 설정 모드
            threshold_mode = st.selectbox(
                "임계값 설정 방식",
                ["자동 계산", "수동 설정"],
                key="cycle_threshold_mode"
            )
            
            # 임계값 (수동 설정 시)
            if threshold_mode == "수동 설정":
                min_val, max_val = df[sensor_type].min(), df[sensor_type].max()
                threshold = st.slider(
                    "운전/정지 구분 임계값",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val + max_val) / 2,
                    step=(max_val - min_val) / 100,
                    key="cycle_threshold"
                )
            else:
                threshold = None  # 자동 계산
        
        with col2:
            # 스무딩 윈도우 설정
            smooth_window = st.slider(
                "노이즈 감소를 위한 이동 평균 윈도우 크기",
                min_value=1,
                max_value=30,
                value=5,
                step=1,
                help="값이 클수록 노이즈가 줄어들지만, 급격한 변화가 뭉개질 수 있습니다.",
                key="cycle_smooth_window"
            )
            
            # 이상 주기 감지 민감도
            anomaly_sensitivity = st.slider(
                "이상 주기 감지 민감도 (표준편차 배수)",
                min_value=1.0,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help="값이 작을수록 더 많은 주기가 이상으로 감지됩니다.",
                key="cycle_anomaly_sensitivity"
            )
            
            # 진행 상태 표시 여부
            show_progress = st.checkbox(
                "분석 진행 상태 표시",
                value=True,
                key="cycle_show_progress"
            )
    
    # 세션 상태의 설정값과 현재 설정값 비교
    def check_settings_changed():
        """설정이 변경되었는지 확인하는 함수"""
        if RESULTS_KEY not in st.session_state:
            return True
        
        saved_settings = st.session_state[RESULTS_KEY].get('settings', {})
        
        # 임계값 모드 변경 확인
        if saved_settings.get('threshold_mode') != threshold_mode:
            return True
        
        # 임계값 변경 확인 (수동 설정인 경우)
        if threshold_mode == "수동 설정" and abs(saved_settings.get('threshold', 0) - threshold) > 0.01:
            return True
        
        # 스무딩 윈도우 변경 확인
        if saved_settings.get('smooth_window') != smooth_window:
            return True
        
        # 이상 감지 민감도 변경 확인
        if abs(saved_settings.get('anomaly_sensitivity', 0) - anomaly_sensitivity) > 0.01:
            return True
        
        return False
    
    # 분석 실행 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state[ANALYZED_KEY]:
            st.info("주기 분석이 완료되었습니다. 설정을 변경하고 '주기 분석 다시 실행'을 클릭하여 새로 분석할 수 있습니다.")
    with col2:
        if st.session_state[ANALYZED_KEY]:
            run_analysis = st.button("주기 분석 다시 실행", key="run_again", use_container_width=True)
        else:
            run_analysis = st.button("주기 분석 실행", key="run_analysis", use_container_width=True)
    
    # processed_data 변수를 함수 전체에서 사용할 수 있도록 초기화
    processed_data = None
    
    # 이전 분석 결과 표시 또는 새 분석 실행
    if run_analysis or (st.session_state[ANALYZED_KEY] and not check_settings_changed()):
        # 새 분석 실행 필요 여부 확인
        if run_analysis or RESULTS_KEY not in st.session_state:
            # 분석 시작 시간 기록
            start_time = time.time()
            
            # 캐싱 키 생성
            cache_key = f"cycle_analysis_{len(df)}_{threshold}_{smooth_window}"
            
            # 캐시 사용 여부 확인
            if cache_key in st.session_state and not run_analysis:
                # 캐시된 결과 사용
                st.info("캐시된 분석 결과를 사용합니다.")
                cycles_df, stop_cycles_df, auto_threshold, processed_data = st.session_state[cache_key]
                threshold = auto_threshold
            else:
                # 주기 감지 및 분석
                with st.spinner("주기 감지 중..."):
                    cycles_df, stop_cycles_df, auto_threshold, processed_data = detect_cycles(
                        df, sensor_type, threshold, smooth_window, show_progress=show_progress
                    )
                    
                    # 결과 캐싱
                    st.session_state[cache_key] = (cycles_df, stop_cycles_df, auto_threshold, processed_data)
                
                if threshold is None:
                    st.info(f"자동 계산된 임계값: {auto_threshold:.2f}")
                    threshold = auto_threshold
            
            # 분석 소요 시간 계산 및 표시
            end_time = time.time()
            analysis_time = end_time - start_time
            st.success(f"주기 분석 완료! (소요 시간: {analysis_time:.2f}초)")
            
            # 감지된 주기가 없는 경우
            if cycles_df.empty and stop_cycles_df.empty:
                st.warning("운전/정지 주기를 감지할 수 없습니다. 임계값을 조정해보세요.")
                st.session_state[ANALYZED_KEY] = False
                return
            
            # 분석 결과 계산
            analysis_result = analyze_cycles(cycles_df, stop_cycles_df)
            
            # 세션 상태에 결과 저장
            st.session_state[RESULTS_KEY] = {
                'cycles_df': cycles_df.to_dict('records') if not cycles_df.empty else [],
                'stop_cycles_df': stop_cycles_df.to_dict('records') if not stop_cycles_df.empty else [],
                'threshold': threshold,
                'analysis_result': analysis_result,
                'analysis_time': analysis_time,
                'settings': {
                    'threshold_mode': threshold_mode,
                    'threshold': threshold if threshold_mode == "수동 설정" else None,
                    'smooth_window': smooth_window,
                    'anomaly_sensitivity': anomaly_sensitivity
                }
            }
            # processed_data도 세션 상태에 저장
            st.session_state[f"{RESULTS_KEY}_processed_data"] = processed_data
            st.session_state[ANALYZED_KEY] = True
            
        else:
            # 세션에서 저장된 결과 로드
            saved_results = st.session_state[RESULTS_KEY]
            cycles_df = pd.DataFrame(saved_results['cycles_df']) if saved_results['cycles_df'] else pd.DataFrame()
            stop_cycles_df = pd.DataFrame(saved_results['stop_cycles_df']) if saved_results['stop_cycles_df'] else pd.DataFrame()
            threshold = saved_results['threshold']
            analysis_result = saved_results['analysis_result']
            analysis_time = saved_results.get('analysis_time', 0)
            
            # processed_data도 세션 상태에서 로드 (없으면 None)
            processed_data = st.session_state.get(f"{RESULTS_KEY}_processed_data", None)
            
            # 세션에서 불러온 결과임을 표시
            st.info(f"저장된 분석 결과를 표시합니다. (이전 분석 소요 시간: {analysis_time:.2f}초)")
        
        # 분석 결과 요약
        st.markdown("## 분석 결과 요약")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("감지된 운전 주기 수", analysis_result['operation_count'])
            if analysis_result['operation_count'] > 0:
                st.metric("평균 운전 시간 (분)", f"{analysis_result['operation_avg_duration']:.1f}")
                st.metric("지속시간 이상 주기 수", analysis_result['operation_anomalous_count'])
                if 'operation_sensor_anomalous_count' in analysis_result:
                    st.metric("센서값 이상 주기 수", analysis_result['operation_sensor_anomalous_count'])
        
        with col2:
            st.metric("감지된 정지 주기 수", analysis_result['stop_count'])
            if analysis_result['stop_count'] > 0:
                st.metric("평균 정지 시간 (분)", f"{analysis_result['stop_avg_duration']:.1f}")
                st.metric("지속시간 이상 주기 수", analysis_result['stop_anomalous_count'])
                if 'stop_sensor_anomalous_count' in analysis_result:
                    st.metric("센서값 이상 주기 수", analysis_result['stop_sensor_anomalous_count'])
        
        # 주기 타임라인 시각화
        st.markdown("### 주기 타임라인")
        
        # 데이터 샘플링 적용 - 대용량 데이터 처리 속도 개선
        if len(df) > 50000:
            sample_size = 30000  # 샘플링 크기 대폭 증가
            sample_step = max(1, len(df) // sample_size)
            sampled_df = df.iloc[::sample_step].copy()
            st.caption(f"데이터 크기가 큰 관계로 샘플링된 데이터({len(sampled_df):,}개 포인트)로 시각화합니다. 원본 데이터 크기: {len(df):,}개 포인트")
        else:
            sampled_df = df.copy()
        
        # 원본 데이터와 임계값 차트
        fig = go.Figure()

        # 원본 데이터 (샘플링 적용)
        fig.add_trace(go.Scatter(
            x=sampled_df['timestamp'] if 'timestamp' in sampled_df.columns else sampled_df.index,
            y=sampled_df[sensor_type],
            mode='lines',
            name=f'{sensor_type} 원본값',
            line=dict(color='rgba(0, 150, 255, 0.5)', width=1)
        ))

        # 스무딩된 데이터 (세션에서 불러온 경우 스무딩 데이터는 다시 계산)
        if processed_data is not None:
            # 스무딩 데이터도 샘플링 적용
            if len(processed_data) > 50000:
                smooth_step = max(1, len(processed_data) // 30000)  # 샘플링 크기 대폭 증가
                smoothed_data = processed_data[f'{sensor_type}_smooth'].iloc[::smooth_step]
                smoothed_x = processed_data['timestamp'].iloc[::smooth_step] if 'timestamp' in processed_data.columns else processed_data.index[::smooth_step]
            else:
                smoothed_data = processed_data[f'{sensor_type}_smooth']
                smoothed_x = processed_data['timestamp'] if 'timestamp' in processed_data.columns else processed_data.index
        else:
            # 스무딩 데이터 다시 계산 (샘플링된 데이터로)
            temp_data = sampled_df.copy()
            if smooth_window > 1:
                temp_data[f'{sensor_type}_smooth'] = temp_data[sensor_type].rolling(window=min(smooth_window, len(temp_data) // 10), center=True).mean()
                temp_data[f'{sensor_type}_smooth'].fillna(temp_data[sensor_type], inplace=True)
            else:
                temp_data[f'{sensor_type}_smooth'] = temp_data[sensor_type]
            
            smoothed_data = temp_data[f'{sensor_type}_smooth']
            smoothed_x = temp_data['timestamp'] if 'timestamp' in temp_data.columns else temp_data.index
        
        fig.add_trace(go.Scatter(
            x=smoothed_x,
            y=smoothed_data,
            mode='lines',
            name=f'{sensor_type} 스무딩',
            line=dict(color='blue', width=2)
        ))

        # 임계값 선
        fig.add_trace(go.Scatter(
            x=[sampled_df['timestamp'].min() if 'timestamp' in sampled_df.columns else 0, 
               sampled_df['timestamp'].max() if 'timestamp' in sampled_df.columns else len(sampled_df)],
            y=[threshold, threshold],
            mode='lines',
            name='임계값',
            line=dict(color='red', width=2, dash='dash')
        ))

        # 운전 주기 하이라이트 - 모든 주기 표시
        if not cycles_df.empty:
            # 모든 운전 주기 하이라이트 표시
            for _, row in cycles_df.iterrows():
                fig.add_shape(
                    type="rect",
                    x0=row['start_time'],
                    x1=row['end_time'],
                    y0=sampled_df[sensor_type].min(),
                    y1=sampled_df[sensor_type].max(),
                    fillcolor="rgba(0, 255, 0, 0.2)",
                    line=dict(width=0),
                    layer="below"
                )

        # 차트 레이아웃 설정
        fig.update_layout(
            title=f"{equipment_type} 운전/정지 주기 감지",
            xaxis_title="시간",
            yaxis_title=sensor_type,
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='closest'
        )

        # 플롯 표시 설정
        config = {
            'responsive': True,
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{equipment_type}_cycle_analysis',
                'height': 800,
                'width': 1200,
                'scale': 2
            }
        }

        st.plotly_chart(fig, use_container_width=True, config=config)
        
        # 주기 통계 섹션
        st.markdown("### 주기 통계")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 운전 주기")
            if not cycles_df.empty:
                st.metric("감지된 운전 주기 수", analysis_result['operation_count'])
                st.metric("평균 운전 시간 (분)", f"{analysis_result['operation_avg_duration']:.1f}")
                st.metric("표준 편차 (분)", f"{analysis_result['operation_std_duration']:.1f}")
                st.metric("최소 운전 시간 (분)", f"{analysis_result['operation_min_duration']:.1f}")
                st.metric("최대 운전 시간 (분)", f"{analysis_result['operation_max_duration']:.1f}")
            else:
                st.info("운전 주기가 감지되지 않았습니다.")
        
        with col2:
            st.markdown("#### 정지 주기")
            if not stop_cycles_df.empty:
                st.metric("감지된 정지 주기 수", analysis_result['stop_count'])
                st.metric("평균 정지 시간 (분)", f"{analysis_result['stop_avg_duration']:.1f}")
                st.metric("표준 편차 (분)", f"{analysis_result['stop_std_duration']:.1f}")
                st.metric("최소 정지 시간 (분)", f"{analysis_result['stop_min_duration']:.1f}")
                st.metric("최대 정지 시간 (분)", f"{analysis_result['stop_max_duration']:.1f}")
            else:
                st.info("정지 주기가 감지되지 않았습니다.")
        
        # 주기 분포 시각화
        st.markdown("### 주기 분포")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 운전 시간 분포")
            if not cycles_df.empty:
                fig = px.histogram(
                    cycles_df, 
                    x="duration_min", 
                    nbins=20,
                    title="운전 시간 분포 (분)",
                    labels={"duration_min": "운전 시간 (분)"},
                    color_discrete_sequence=["blue"]
                )
                fig.update_layout(
                    xaxis_title="운전 시간 (분)",
                    yaxis_title="빈도",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("운전 주기가 감지되지 않았습니다.")
        
        with col2:
            st.markdown("#### 정지 시간 분포")
            if not stop_cycles_df.empty:
                fig = px.histogram(
                    stop_cycles_df, 
                    x="duration_min", 
                    nbins=20,
                    title="정지 시간 분포 (분)",
                    labels={"duration_min": "정지 시간 (분)"},
                    color_discrete_sequence=["red"]
                )
                fig.update_layout(
                    xaxis_title="정지 시간 (분)",
                    yaxis_title="빈도",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("정지 주기가 감지되지 않았습니다.")
        
        # 이상 주기 섹션
        st.markdown("### 이상 주기 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 이상 운전 주기")
            if not cycles_df.empty and analysis_result['operation_count'] > 0:
                st.metric("이상 운전 주기 수", analysis_result['operation_anomalous_count'])
                
                # 전체 신뢰 구간 시각화 추가 (Box plot)
                st.subheader("운전 시간 분포 및 신뢰 구간")
                
                # 평균 및 신뢰 구간 계산
                mean_duration = cycles_df['duration_min'].mean()
                std_duration = cycles_df['duration_min'].std()
                ci_lower = mean_duration - anomaly_sensitivity * std_duration
                ci_upper = mean_duration + anomaly_sensitivity * std_duration
                
                # 신뢰 구간 표시
                ci_fig = go.Figure()
                
                # 전체 데이터 포인트
                ci_fig.add_trace(go.Box(
                    y=cycles_df['duration_min'],
                    name="운전 시간",
                    boxmean=True,  # 평균 표시
                    marker_color='blue',
                    boxpoints='all',  # 모든 포인트 표시
                    jitter=0.3,  # 포인트 겹침 방지
                    pointpos=-1.8  # 포인트 위치 조정
                ))
                
                # 신뢰 구간 표시
                ci_fig.add_shape(
                    type="rect",
                    x0=0,
                    x1=1, 
                    y0=ci_lower,
                    y1=ci_upper,
                    fillcolor="rgba(0, 255, 0, 0.2)",
                    line=dict(color="green", width=2, dash="dash"),
                    layer="below"
                )
                
                # 평균선 추가
                ci_fig.add_shape(
                    type="line",
                    x0=0,
                    x1=1,
                    y0=mean_duration,
                    y1=mean_duration,
                    line=dict(color="green", width=2)
                )
                
                # 이상 주기 강조 표시
                if analysis_result['operation_anomalous_count'] > 0:
                    anomalous_cycles = pd.DataFrame(analysis_result['operation_anomalous_cycles'])
                    ci_fig.add_trace(go.Scatter(
                        y=anomalous_cycles['duration_min'],
                        x=np.ones(len(anomalous_cycles)) * 0.5,
                        mode="markers",
                        marker=dict(
                            symbol="circle",
                            color="red",
                            size=12,
                            line=dict(color="red", width=2)
                        ),
                        name="이상 주기",
                        hovertemplate="주기 ID: %{text}<br>지속 시간: %{y:.2f}분<br>Z-점수: %{customdata:.2f}",
                        text=anomalous_cycles['cycle_id'],
                        customdata=anomalous_cycles['duration_zscore']
                    ))
                
                ci_fig.update_layout(
                    title="운전 시간 분포 및 신뢰 구간",
                    showlegend=True,
                    xaxis_title="",
                    yaxis_title="운전 시간 (분)",
                    xaxis=dict(
                        showticklabels=False,
                        showgrid=False,
                        zeroline=False
                    ),
                    annotations=[
                        dict(
                            x=0.5,
                            y=mean_duration,
                            xref="x",
                            yref="y",
                            text=f"평균: {mean_duration:.2f}분",
                            showarrow=True,
                            arrowhead=2,
                            ax=70,
                            ay=-30
                        ),
                        dict(
                            x=0.5,
                            y=ci_upper,
                            xref="x",
                            yref="y",
                            text=f"상한: {ci_upper:.2f}분",
                            showarrow=True,
                            arrowhead=2,
                            ax=70,
                            ay=-20
                        ),
                        dict(
                            x=0.5,
                            y=ci_lower,
                            xref="x",
                            yref="y",
                            text=f"하한: {ci_lower:.2f}분",
                            showarrow=True,
                            arrowhead=2,
                            ax=70,
                            ay=20
                        )
                    ],
                    height=450
                )
                
                st.plotly_chart(ci_fig, use_container_width=True)
                
                # 이상 운전 주기 테이블
                if analysis_result['operation_anomalous_count'] > 0:
                    st.subheader("이상 운전 주기 목록 (지속시간 기준)")
                    anomalous_op_df = pd.DataFrame(analysis_result['operation_anomalous_cycles'])
                    anomalous_op_df = anomalous_op_df[['cycle_id', 'start_time', 'end_time', 'duration_min', 'duration_zscore', 'avg_value']]
                    anomalous_op_df.columns = ['주기 ID', '시작 시간', '종료 시간', '지속 시간 (분)', 'Z-점수', '평균 값']
                    anomalous_op_df = anomalous_op_df.sort_values(by='Z-점수', ascending=False)
                    st.dataframe(anomalous_op_df, hide_index=True)
                
                # 센서값 이상 운전 주기 테이블 추가
                if 'operation_sensor_anomalous_count' in analysis_result and analysis_result['operation_sensor_anomalous_count'] > 0:
                    st.subheader("이상 운전 주기 목록 (센서값 기준)")
                    sensor_anomalous_op_df = pd.DataFrame(analysis_result['operation_sensor_anomalous_cycles'])
                    
                    # 필요한 컬럼만 선택
                    display_cols = ['cycle_id', 'start_time', 'end_time', 'avg_value', 'max_value', 'min_value']
                    zscore_cols = ['avg_value_zscore', 'max_value_zscore', 'min_value_zscore']
                    
                    # Z-score 컬럼이 있는지 확인하고 추가
                    for col in zscore_cols:
                        if col in sensor_anomalous_op_df.columns:
                            display_cols.append(col)
                    
                    # 테이블 표시
                    display_df = sensor_anomalous_op_df[display_cols].copy()
                    
                    # 컬럼명 변경
                    rename_dict = {
                        'cycle_id': '주기 ID',
                        'start_time': '시작 시간',
                        'end_time': '종료 시간',
                        'avg_value': '평균값',
                        'max_value': '최대값',
                        'min_value': '최소값',
                        'avg_value_zscore': '평균값 Z-점수',
                        'max_value_zscore': '최대값 Z-점수',
                        'min_value_zscore': '최소값 Z-점수'
                    }
                    display_df.rename(columns=rename_dict, inplace=True)
                    
                    # 가장 큰 절대값 Z-score 순으로 정렬
                    if all(col in display_df.columns for col in ['평균값 Z-점수', '최대값 Z-점수', '최소값 Z-점수']):
                        display_df['최대이상도'] = display_df[['평균값 Z-점수', '최대값 Z-점수', '최소값 Z-점수']].abs().max(axis=1)
                        display_df = display_df.sort_values(by='최대이상도', ascending=False)
                        display_df.drop(columns=['최대이상도'], inplace=True)
                    
                    st.dataframe(display_df, hide_index=True)
                
                # 운전 주기 시각화 (지속 시간 vs Z-score)
                st.subheader("운전 주기 이상치 분석")
                scatter_fig = px.scatter(
                    cycles_df,
                    x='duration_min',
                    y='duration_zscore',
                    hover_data=['cycle_id', 'avg_value', 'start_time', 'end_time'],
                    color='duration_zscore',
                    color_continuous_scale='RdBu_r',
                )
                
                # 정상/이상 영역 구분
                scatter_fig.add_shape(
                    type="rect",
                    x0=cycles_df['duration_min'].min(),
                    x1=cycles_df['duration_min'].max(),
                    y0=-anomaly_sensitivity,
                    y1=anomaly_sensitivity,
                    fillcolor="rgba(0, 255, 0, 0.1)",
                    line=dict(color="green", width=1),
                    layer="below"
                )
                
                # 임계선 추가
                scatter_fig.add_shape(
                    type="line",
                    x0=cycles_df['duration_min'].min(),
                    x1=cycles_df['duration_min'].max(),
                    y0=anomaly_sensitivity,
                    y1=anomaly_sensitivity,
                    line=dict(color="red", width=2, dash="dash"),
                )
                scatter_fig.add_shape(
                    type="line",
                    x0=cycles_df['duration_min'].min(),
                    x1=cycles_df['duration_min'].max(),
                    y0=-anomaly_sensitivity,
                    y1=-anomaly_sensitivity,
                    line=dict(color="red", width=2, dash="dash"),
                )
                
                # 이상 주기만 강조 표시 추가
                if analysis_result['operation_anomalous_count'] > 0:
                    for _, row in anomalous_op_df.iterrows():
                        scatter_fig.add_trace(go.Scatter(
                            x=[row['지속 시간 (분)']],
                            y=[row['Z-점수']],
                            mode="markers",
                            marker=dict(
                                symbol="circle-open",
                                color="black",
                                size=18,
                                line=dict(color="black", width=3)
                            ),
                            name=f"이상 주기 ID: {row['주기 ID']}",
                            showlegend=False,
                            hoverinfo="skip"
                        ))
                
                scatter_fig.update_layout(
                    xaxis_title="운전 지속 시간 (분)",
                    yaxis_title="Z-점수",
                    height=400,
                    coloraxis_colorbar=dict(title="Z-점수"),
                    annotations=[
                        dict(
                            x=cycles_df['duration_min'].max() * 0.9,
                            y=0,
                            text="정상 영역",
                            showarrow=False,
                            font=dict(color="green", size=14)
                        ),
                        dict(
                            x=cycles_df['duration_min'].max() * 0.9,
                            y=anomaly_sensitivity * 1.2,
                            text="이상 영역 (과다)",
                            showarrow=False,
                            font=dict(color="red", size=14)
                        ),
                        dict(
                            x=cycles_df['duration_min'].max() * 0.9,
                            y=-anomaly_sensitivity * 1.2,
                            text="이상 영역 (과소)",
                            showarrow=False,
                            font=dict(color="red", size=14)
                        )
                    ]
                )
                
                st.plotly_chart(scatter_fig, use_container_width=True)
            else:
                st.info("이상 운전 주기가 감지되지 않았습니다.")
        
        with col2:
            st.markdown("#### 이상 정지 주기")
            if not stop_cycles_df.empty and analysis_result['stop_count'] > 0:
                st.metric("이상 정지 주기 수", analysis_result['stop_anomalous_count'])
                
                # 전체 신뢰 구간 시각화 추가 (Box plot)
                st.subheader("정지 시간 분포 및 신뢰 구간")
                
                # 평균 및 신뢰 구간 계산
                mean_duration = stop_cycles_df['duration_min'].mean()
                std_duration = stop_cycles_df['duration_min'].std()
                ci_lower = mean_duration - anomaly_sensitivity * std_duration
                ci_upper = mean_duration + anomaly_sensitivity * std_duration
                
                # 신뢰 구간 표시
                ci_fig = go.Figure()
                
                # 전체 데이터 포인트
                ci_fig.add_trace(go.Box(
                    y=stop_cycles_df['duration_min'],
                    name="정지 시간",
                    boxmean=True,  # 평균 표시
                    marker_color='red',
                    boxpoints='all',  # 모든 포인트 표시
                    jitter=0.3,  # 포인트 겹침 방지
                    pointpos=-1.8  # 포인트 위치 조정
                ))
                
                # 신뢰 구간 표시
                ci_fig.add_shape(
                    type="rect",
                    x0=0,
                    x1=1, 
                    y0=ci_lower,
                    y1=ci_upper,
                    fillcolor="rgba(0, 255, 0, 0.2)",
                    line=dict(color="green", width=2, dash="dash"),
                    layer="below"
                )
                
                # 평균선 추가
                ci_fig.add_shape(
                    type="line",
                    x0=0,
                    x1=1,
                    y0=mean_duration,
                    y1=mean_duration,
                    line=dict(color="green", width=2)
                )
                
                # 이상 주기 강조 표시
                if analysis_result['stop_anomalous_count'] > 0:
                    anomalous_cycles = pd.DataFrame(analysis_result['stop_anomalous_cycles'])
                    ci_fig.add_trace(go.Scatter(
                        y=anomalous_cycles['duration_min'],
                        x=np.ones(len(anomalous_cycles)) * 0.5,
                        mode="markers",
                        marker=dict(
                            symbol="circle",
                            color="red",
                            size=12,
                            line=dict(color="red", width=2)
                        ),
                        name="이상 주기",
                        hovertemplate="주기 ID: %{text}<br>지속 시간: %{y:.2f}분<br>Z-점수: %{customdata:.2f}",
                        text=anomalous_cycles['cycle_id'],
                        customdata=anomalous_cycles['duration_zscore']
                    ))
                
                ci_fig.update_layout(
                    title="정지 시간 분포 및 신뢰 구간",
                    showlegend=True,
                    xaxis_title="",
                    yaxis_title="정지 시간 (분)",
                    xaxis=dict(
                        showticklabels=False,
                        showgrid=False,
                        zeroline=False
                    ),
                    annotations=[
                        dict(
                            x=0.5,
                            y=mean_duration,
                            xref="x",
                            yref="y",
                            text=f"평균: {mean_duration:.2f}분",
                            showarrow=True,
                            arrowhead=2,
                            ax=70,
                            ay=-30
                        ),
                        dict(
                            x=0.5,
                            y=ci_upper,
                            xref="x",
                            yref="y",
                            text=f"상한: {ci_upper:.2f}분",
                            showarrow=True,
                            arrowhead=2,
                            ax=70,
                            ay=-20
                        ),
                        dict(
                            x=0.5,
                            y=ci_lower,
                            xref="x",
                            yref="y",
                            text=f"하한: {ci_lower:.2f}분",
                            showarrow=True,
                            arrowhead=2,
                            ax=70,
                            ay=20
                        )
                    ],
                    height=450
                )
                
                st.plotly_chart(ci_fig, use_container_width=True)
                
                # 이상 정지 주기 테이블
                if analysis_result['stop_anomalous_count'] > 0:
                    st.subheader("이상 정지 주기 목록 (지속시간 기준)")
                    anomalous_stop_df = pd.DataFrame(analysis_result['stop_anomalous_cycles'])
                    anomalous_stop_df = anomalous_stop_df[['cycle_id', 'start_time', 'end_time', 'duration_min', 'duration_zscore', 'avg_value']]
                    anomalous_stop_df.columns = ['주기 ID', '시작 시간', '종료 시간', '지속 시간 (분)', 'Z-점수', '평균 값']
                    anomalous_stop_df = anomalous_stop_df.sort_values(by='Z-점수', ascending=False)
                    st.dataframe(anomalous_stop_df, hide_index=True)
                
                # 센서값 이상 정지 주기 테이블 추가
                if 'stop_sensor_anomalous_count' in analysis_result and analysis_result['stop_sensor_anomalous_count'] > 0:
                    st.subheader("이상 정지 주기 목록 (센서값 기준)")
                    sensor_anomalous_stop_df = pd.DataFrame(analysis_result['stop_sensor_anomalous_cycles'])
                    
                    # 필요한 컬럼만 선택
                    display_cols = ['cycle_id', 'start_time', 'end_time', 'avg_value', 'max_value', 'min_value']
                    zscore_cols = ['avg_value_zscore', 'max_value_zscore', 'min_value_zscore']
                    
                    # Z-score 컬럼이 있는지 확인하고 추가
                    for col in zscore_cols:
                        if col in sensor_anomalous_stop_df.columns:
                            display_cols.append(col)
                    
                    # 테이블 표시
                    display_df = sensor_anomalous_stop_df[display_cols].copy()
                    
                    # 컬럼명 변경
                    rename_dict = {
                        'cycle_id': '주기 ID',
                        'start_time': '시작 시간',
                        'end_time': '종료 시간',
                        'avg_value': '평균값',
                        'max_value': '최대값',
                        'min_value': '최소값',
                        'avg_value_zscore': '평균값 Z-점수',
                        'max_value_zscore': '최대값 Z-점수',
                        'min_value_zscore': '최소값 Z-점수'
                    }
                    display_df.rename(columns=rename_dict, inplace=True)
                    
                    # 가장 큰 절대값 Z-score 순으로 정렬
                    if all(col in display_df.columns for col in ['평균값 Z-점수', '최대값 Z-점수', '최소값 Z-점수']):
                        display_df['최대이상도'] = display_df[['평균값 Z-점수', '최대값 Z-점수', '최소값 Z-점수']].abs().max(axis=1)
                        display_df = display_df.sort_values(by='최대이상도', ascending=False)
                        display_df.drop(columns=['최대이상도'], inplace=True)
                    
                    st.dataframe(display_df, hide_index=True)
                
                # 정지 주기 시각화 (지속 시간 vs Z-score)
                st.subheader("정지 주기 이상치 분석")
                scatter_fig = px.scatter(
                    stop_cycles_df,
                    x='duration_min',
                    y='duration_zscore',
                    hover_data=['cycle_id', 'avg_value', 'start_time', 'end_time'],
                    color='duration_zscore',
                    color_continuous_scale='RdBu_r',
                )
                
                # 정상/이상 영역 구분
                scatter_fig.add_shape(
                    type="rect",
                    x0=stop_cycles_df['duration_min'].min(),
                    x1=stop_cycles_df['duration_min'].max(),
                    y0=-anomaly_sensitivity,
                    y1=anomaly_sensitivity,
                    fillcolor="rgba(0, 255, 0, 0.1)",
                    line=dict(color="green", width=1),
                    layer="below"
                )
                
                # 임계선 추가
                scatter_fig.add_shape(
                    type="line",
                    x0=stop_cycles_df['duration_min'].min(),
                    x1=stop_cycles_df['duration_min'].max(),
                    y0=anomaly_sensitivity,
                    y1=anomaly_sensitivity,
                    line=dict(color="red", width=2, dash="dash"),
                )
                scatter_fig.add_shape(
                    type="line",
                    x0=stop_cycles_df['duration_min'].min(),
                    x1=stop_cycles_df['duration_min'].max(),
                    y0=-anomaly_sensitivity,
                    y1=-anomaly_sensitivity,
                    line=dict(color="red", width=2, dash="dash"),
                )
                
                # 이상 주기만 강조 표시 추가
                if analysis_result['stop_anomalous_count'] > 0:
                    for _, row in anomalous_stop_df.iterrows():
                        scatter_fig.add_trace(go.Scatter(
                            x=[row['지속 시간 (분)']],
                            y=[row['Z-점수']],
                            mode="markers",
                            marker=dict(
                                symbol="circle-open",
                                color="black",
                                size=18,
                                line=dict(color="black", width=3)
                            ),
                            name=f"이상 주기 ID: {row['주기 ID']}",
                            showlegend=False,
                            hoverinfo="skip"
                        ))
                
                scatter_fig.update_layout(
                    xaxis_title="정지 지속 시간 (분)",
                    yaxis_title="Z-점수",
                    height=400,
                    coloraxis_colorbar=dict(title="Z-점수"),
                    annotations=[
                        dict(
                            x=stop_cycles_df['duration_min'].max() * 0.9,
                            y=0,
                            text="정상 영역",
                            showarrow=False,
                            font=dict(color="green", size=14)
                        ),
                        dict(
                            x=stop_cycles_df['duration_min'].max() * 0.9,
                            y=anomaly_sensitivity * 1.2,
                            text="이상 영역 (과다)",
                            showarrow=False,
                            font=dict(color="red", size=14)
                        ),
                        dict(
                            x=stop_cycles_df['duration_min'].max() * 0.9,
                            y=-anomaly_sensitivity * 1.2,
                            text="이상 영역 (과소)",
                            showarrow=False,
                            font=dict(color="red", size=14)
                        )
                    ]
                )
                
                st.plotly_chart(scatter_fig, use_container_width=True)
            else:
                st.info("이상 정지 주기가 감지되지 않았습니다.")
        
        # 주기 상세 정보 섹션
        st.markdown("### 주기 상세 정보")
        
        tab1, tab2 = st.tabs(["운전 주기", "정지 주기"])
        
        with tab1:
            if not cycles_df.empty:
                st.dataframe(cycles_df, hide_index=True)
                
                # 주기별 데이터 값 분포 시각화 추가
                st.markdown("#### 운전 주기별 데이터 값 분포 비교")
                
                # 주기별 평균/최대/최소 값 비교 차트
                fig = go.Figure()
                
                # 주기 ID 목록 (정렬)
                cycle_ids = sorted(cycles_df['cycle_id'].unique())
                
                # 주기별 평균값 
                fig.add_trace(go.Scatter(
                    x=cycle_ids,
                    y=cycles_df.set_index('cycle_id').loc[cycle_ids, 'avg_value'],
                    mode='lines+markers',
                    name='평균값',
                    line=dict(color='blue', width=2),
                    marker=dict(size=8)
                ))
                
                # 주기별 최대값
                fig.add_trace(go.Scatter(
                    x=cycle_ids,
                    y=cycles_df.set_index('cycle_id').loc[cycle_ids, 'max_value'],
                    mode='lines+markers',
                    name='최대값',
                    line=dict(color='red', width=2),
                    marker=dict(size=8)
                ))
                
                # 주기별 최소값
                fig.add_trace(go.Scatter(
                    x=cycle_ids,
                    y=cycles_df.set_index('cycle_id').loc[cycle_ids, 'min_value'],
                    mode='lines+markers',
                    name='최소값',
                    line=dict(color='green', width=2),
                    marker=dict(size=8)
                ))
                
                # 이상 주기 강조 표시 (지속시간 기준)
                if 'duration_zscore' in cycles_df.columns and analysis_result['operation_anomalous_count'] > 0:
                    anomalous_cycles = cycles_df[abs(cycles_df['duration_zscore']) > 2.0]
                    for _, row in anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['avg_value']],
                            mode='markers',
                            marker=dict(
                                symbol='circle-open',
                                size=15,
                                color='rgba(255, 0, 0, 0.8)',
                                line=dict(width=2)
                            ),
                            name=f'지속시간 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 센서값 이상 주기 강조 표시 (평균값)
                if 'avg_value_zscore' in cycles_df.columns and analysis_result.get('operation_sensor_anomalous_count', 0) > 0:
                    avg_anomalous_cycles = cycles_df[abs(cycles_df['avg_value_zscore']) > 2.0]
                    for _, row in avg_anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['avg_value']],
                            mode='markers',
                            marker=dict(
                                symbol='diamond',
                                size=16,
                                color='rgba(255, 165, 0, 0.9)', # 주황색
                                line=dict(width=2)
                            ),
                            name=f'평균값 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 센서값 이상 주기 강조 표시 (최대값)
                if 'max_value_zscore' in cycles_df.columns and analysis_result.get('operation_sensor_anomalous_count', 0) > 0:
                    max_anomalous_cycles = cycles_df[abs(cycles_df['max_value_zscore']) > 2.0]
                    for _, row in max_anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['max_value']],
                            mode='markers',
                            marker=dict(
                                symbol='triangle-up',
                                size=16,
                                color='rgba(255, 0, 255, 0.9)', # 마젠타
                                line=dict(width=2)
                            ),
                            name=f'최대값 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 센서값 이상 주기 강조 표시 (최소값)
                if 'min_value_zscore' in cycles_df.columns and analysis_result.get('operation_sensor_anomalous_count', 0) > 0:
                    min_anomalous_cycles = cycles_df[abs(cycles_df['min_value_zscore']) > 2.0]
                    for _, row in min_anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['min_value']],
                            mode='markers',
                            marker=dict(
                                symbol='triangle-down',
                                size=16,
                                color='rgba(0, 200, 200, 0.9)', # 청록색
                                line=dict(width=2)
                            ),
                            name=f'최소값 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 범례 추가
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='circle-open', size=15, color='rgba(255, 0, 0, 0.8)', line=dict(width=2)),
                    name='지속시간 이상'
                ))
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='diamond', size=16, color='rgba(255, 165, 0, 0.9)', line=dict(width=2)),
                    name='평균값 이상'
                ))
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=16, color='rgba(255, 0, 255, 0.9)', line=dict(width=2)),
                    name='최대값 이상'
                ))
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=16, color='rgba(0, 200, 200, 0.9)', line=dict(width=2)),
                    name='최소값 이상'
                ))
                
                # 레이아웃 설정
                fig.update_layout(
                    title='운전 주기별 센서 값 추이',
                    xaxis_title='주기 ID',
                    yaxis_title='센서 값',
                    height=450,
                    hovermode='closest',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 주기별 분포를 박스플롯으로 시각화
                if len(cycles_df) > 5:  # 일정 개수 이상의 주기가 있을 때만 표시
                    st.markdown("#### 주요 운전 주기별 값 분포 비교 (박스플롯)")
                    
                    # 원본 데이터 및 주기 정보 사용하여 박스플롯 데이터 준비
                    boxplot_data = []
                    
                    # 표시할 주기 수 제한 (너무 많으면 가독성 저하)
                    max_cycles_to_show = 15
                    cycles_to_show = cycle_ids[:max_cycles_to_show] if len(cycle_ids) > max_cycles_to_show else cycle_ids
                    
                    if 'timestamp' in df.columns and processed_data is not None:
                        for cycle_id in cycles_to_show:
                            cycle_row = cycles_df[cycles_df['cycle_id'] == cycle_id].iloc[0]
                            start_time = cycle_row['start_time']
                            end_time = cycle_row['end_time']
                            
                            # 해당 주기 기간 동안의 데이터 필터링
                            cycle_data = processed_data[(processed_data['timestamp'] >= start_time) & 
                                                       (processed_data['timestamp'] <= end_time)]
                            
                            if not cycle_data.empty:
                                boxplot_data.append(go.Box(
                                    y=cycle_data[sensor_type],
                                    name=f'주기 {int(cycle_id)}',
                                    boxmean=True,  # 평균 표시
                                ))
                    
                    if boxplot_data:
                        # 박스플롯 생성
                        box_fig = go.Figure(data=boxplot_data)
                        
                        # 이상 주기 식별을 위한 배경색 설정
                        if 'duration_zscore' in cycles_df.columns:
                            for i, cycle_id in enumerate(cycles_to_show):
                                cycle_row = cycles_df[cycles_df['cycle_id'] == cycle_id]
                                if not cycle_row.empty and abs(cycle_row['duration_zscore'].iloc[0]) > 2.0:
                                    box_fig.add_shape(
                                        type="rect",
                                        x0=i-0.4, x1=i+0.4,
                                        y0=cycles_df['min_value'].min(),
                                        y1=cycles_df['max_value'].max(),
                                        fillcolor="rgba(255, 0, 0, 0.1)",
                                        line=dict(width=0),
                                        layer="below"
                                    )
                        
                        # 레이아웃 설정
                        box_fig.update_layout(
                            title=f"운전 주기별 {sensor_type} 값 분포",
                            xaxis_title="주기 ID",
                            yaxis_title=f"{sensor_type} 값",
                            height=500,
                            showlegend=False
                        )
                        
                        st.plotly_chart(box_fig, use_container_width=True)
                        
                        if len(cycle_ids) > max_cycles_to_show:
                            st.caption(f"주기가 많아 처음 {max_cycles_to_show}개의 주기만 표시합니다.")
                
                # 주기별 통계치 히트맵 시각화
                st.markdown("#### 운전 주기별 특성 히트맵")
                
                # 히트맵용 데이터 준비
                heatmap_df = cycles_df.copy()
                
                # 표시할 주기 수 제한
                max_cycles_for_heatmap = 20
                if len(cycle_ids) > max_cycles_for_heatmap:
                    # 이상 주기와 일부 정상 주기를 포함
                    anomalous_ids = heatmap_df[abs(heatmap_df['duration_zscore']) > 2.0]['cycle_id'].tolist()
                    normal_ids = heatmap_df[abs(heatmap_df['duration_zscore']) <= 2.0]['cycle_id'].tolist()
                    
                    # 표시할 정상 주기 수 계산
                    normal_to_include = max_cycles_for_heatmap - len(anomalous_ids)
                    if normal_to_include > 0:
                        # 처음, 중간, 마지막 정상 주기 포함
                        if len(normal_ids) <= normal_to_include:
                            selected_normal = normal_ids
                        else:
                            step = max(1, len(normal_ids) // normal_to_include)
                            selected_normal = normal_ids[::step][:normal_to_include]
                        
                        selected_cycles = sorted(anomalous_ids + selected_normal)
                    else:
                        selected_cycles = sorted(anomalous_ids[:max_cycles_for_heatmap])
                else:
                    selected_cycles = cycle_ids
                
                # 선택된 주기만 필터링
                heatmap_df = heatmap_df[heatmap_df['cycle_id'].isin(selected_cycles)]
                
                # 특성 선택 및 정규화
                features = ['duration_min', 'avg_value', 'max_value', 'min_value']
                
                # 데이터 정규화 함수
                def normalize(series):
                    min_val = series.min()
                    max_val = series.max()
                    return (series - min_val) / (max_val - min_val) if max_val > min_val else series
                
                # 특성별 정규화
                for feature in features:
                    if feature in heatmap_df.columns:
                        heatmap_df[f'{feature}_norm'] = normalize(heatmap_df[feature])
                
                # 히트맵 데이터 준비
                heatmap_data = []
                feature_labels = {
                    'duration_min_norm': '운전 시간',
                    'avg_value_norm': '평균 값',
                    'max_value_norm': '최대 값',
                    'min_value_norm': '최소 값'
                }
                
                # 주기 ID 문자열 변환 및 정렬
                heatmap_df = heatmap_df.sort_values(by='cycle_id')
                cycle_id_str = [f'{int(cid)}' for cid in heatmap_df['cycle_id']]
                
                # 히트맵 생성
                heatmap_fig = go.Figure(data=go.Heatmap(
                    z=[[row[f'{f}_norm'] for f in features] for _, row in heatmap_df.iterrows()],
                    x=list(feature_labels.values()),
                    y=cycle_id_str,
                    colorscale='Viridis',
                    colorbar=dict(title='정규화 값'),
                    hoverongaps=False,
                    hovertemplate='주기 ID: %{y}<br>특성: %{x}<br>정규화 값: %{z:.2f}<extra></extra>'
                ))
                
                # 레이아웃 설정
                heatmap_fig.update_layout(
                    title='운전 주기별 특성 비교 (정규화)',
                    xaxis_title='특성',
                    yaxis_title='주기 ID',
                    height=max(350, min(600, len(selected_cycles) * 20)),
                    yaxis=dict(autorange="reversed")  # 위에서 아래로 주기 ID 정렬
                )
                
                st.plotly_chart(heatmap_fig, use_container_width=True)
                
                if len(cycle_ids) > max_cycles_for_heatmap:
                    st.caption(f"주기가 많아 이상 주기와 일부 정상 주기만 표시합니다. (총 {len(selected_cycles)}개 / {len(cycle_ids)}개)")
            else:
                st.info("운전 주기가 감지되지 않았습니다.")
        
        with tab2:
            if not stop_cycles_df.empty:
                st.dataframe(stop_cycles_df, hide_index=True)
                
                # 정지 주기별 데이터 값 분포 시각화 추가
                st.markdown("#### 정지 주기별 데이터 값 분포 비교")
                
                # 주기별 평균/최대/최소 값 비교 차트
                fig = go.Figure()
                
                # 주기 ID 목록 (정렬)
                stop_cycle_ids = sorted(stop_cycles_df['cycle_id'].unique())
                
                # 주기별 평균값 
                fig.add_trace(go.Scatter(
                    x=stop_cycle_ids,
                    y=stop_cycles_df.set_index('cycle_id').loc[stop_cycle_ids, 'avg_value'],
                    mode='lines+markers',
                    name='평균값',
                    line=dict(color='blue', width=2),
                    marker=dict(size=8)
                ))
                
                # 주기별 최대값
                fig.add_trace(go.Scatter(
                    x=stop_cycle_ids,
                    y=stop_cycles_df.set_index('cycle_id').loc[stop_cycle_ids, 'max_value'],
                    mode='lines+markers',
                    name='최대값',
                    line=dict(color='red', width=2),
                    marker=dict(size=8)
                ))
                
                # 주기별 최소값
                fig.add_trace(go.Scatter(
                    x=stop_cycle_ids,
                    y=stop_cycles_df.set_index('cycle_id').loc[stop_cycle_ids, 'min_value'],
                    mode='lines+markers',
                    name='최소값',
                    line=dict(color='green', width=2),
                    marker=dict(size=8)
                ))
                
                # 이상 주기 강조 표시 (지속시간 기준)
                if 'duration_zscore' in stop_cycles_df.columns and analysis_result['stop_anomalous_count'] > 0:
                    anomalous_cycles = stop_cycles_df[abs(stop_cycles_df['duration_zscore']) > 2.0]
                    for _, row in anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['avg_value']],
                            mode='markers',
                            marker=dict(
                                symbol='circle-open',
                                size=15,
                                color='rgba(255, 0, 0, 0.8)',
                                line=dict(width=2)
                            ),
                            name=f'지속시간 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 센서값 이상 주기 강조 표시 (평균값)
                if 'avg_value_zscore' in stop_cycles_df.columns and analysis_result.get('stop_sensor_anomalous_count', 0) > 0:
                    avg_anomalous_cycles = stop_cycles_df[abs(stop_cycles_df['avg_value_zscore']) > 2.0]
                    for _, row in avg_anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['avg_value']],
                            mode='markers',
                            marker=dict(
                                symbol='diamond',
                                size=16,
                                color='rgba(255, 165, 0, 0.9)', # 주황색
                                line=dict(width=2)
                            ),
                            name=f'평균값 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 센서값 이상 주기 강조 표시 (최대값)
                if 'max_value_zscore' in stop_cycles_df.columns and analysis_result.get('stop_sensor_anomalous_count', 0) > 0:
                    max_anomalous_cycles = stop_cycles_df[abs(stop_cycles_df['max_value_zscore']) > 2.0]
                    for _, row in max_anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['max_value']],
                            mode='markers',
                            marker=dict(
                                symbol='triangle-up',
                                size=16,
                                color='rgba(255, 0, 255, 0.9)', # 마젠타
                                line=dict(width=2)
                            ),
                            name=f'최대값 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 센서값 이상 주기 강조 표시 (최소값)
                if 'min_value_zscore' in stop_cycles_df.columns and analysis_result.get('stop_sensor_anomalous_count', 0) > 0:
                    min_anomalous_cycles = stop_cycles_df[abs(stop_cycles_df['min_value_zscore']) > 2.0]
                    for _, row in min_anomalous_cycles.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['cycle_id']],
                            y=[row['min_value']],
                            mode='markers',
                            marker=dict(
                                symbol='triangle-down',
                                size=16,
                                color='rgba(0, 200, 200, 0.9)', # 청록색
                                line=dict(width=2)
                            ),
                            name=f'최소값 이상 주기 {int(row["cycle_id"])}',
                            showlegend=False
                        ))
                
                # 범례 추가
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='circle-open', size=15, color='rgba(255, 0, 0, 0.8)', line=dict(width=2)),
                    name='지속시간 이상'
                ))
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='diamond', size=16, color='rgba(255, 165, 0, 0.9)', line=dict(width=2)),
                    name='평균값 이상'
                ))
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=16, color='rgba(255, 0, 255, 0.9)', line=dict(width=2)),
                    name='최대값 이상'
                ))
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=16, color='rgba(0, 200, 200, 0.9)', line=dict(width=2)),
                    name='최소값 이상'
                ))
                
                # 레이아웃 설정
                fig.update_layout(
                    title='정지 주기별 센서 값 추이',
                    xaxis_title='주기 ID',
                    yaxis_title='센서 값',
                    height=450,
                    hovermode='closest',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("정지 주기가 감지되지 않았습니다.")
                
        # AI 분석 추가
        if not cycles_df.empty or not stop_cycles_df.empty:
            render_ai_analysis(df, cycles_df, stop_cycles_df, analysis_result)
    else:
        # 분석 전 안내 메시지
        st.info("주기 분석을 실행하려면 위의 '주기 분석 실행' 버튼을 클릭하세요. 분석이 완료되면 결과가 여기에 표시됩니다.")

def render_ai_analysis(df, cycles_df, stop_cycles_df, analysis_result):
    """
    운전/정지 주기 AI 분석 UI를 렌더링하는 함수
    
    Args:
        df (DataFrame): 원본 데이터프레임
        cycles_df (DataFrame): 운전 주기 정보 데이터프레임
        stop_cycles_df (DataFrame): 정지 주기 정보 데이터프레임
        analysis_result (dict): 주기 분석 결과
    """
    # 세션 상태 초기화 (AI 분석용)
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 주기 분석 전용 키 접두사 사용
    key_prefix = "cycle_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 장비 및 센서 유형 가져오기
    equipment_type = get_equipment_type()
    sensor_type = get_sensor_type()
    
    if sensor_type not in df.columns:
        sensor_type = "value"  # 기본값으로 fallback
    
    # 분석 설정이 변경되었는지 확인하기 위한 키
    current_analysis_key = f"{key_prefix}_current_analysis"
    
    # 현재 분석 설정
    current_analysis = {
        "operation_count": analysis_result.get('operation_count', 0),
        "operation_avg_duration": analysis_result.get('operation_avg_duration', 0),
        "operation_std_duration": analysis_result.get('operation_std_duration', 0),
        "operation_anomalous_count": analysis_result.get('operation_anomalous_count', 0),
        "stop_count": analysis_result.get('stop_count', 0),
        "stop_avg_duration": analysis_result.get('stop_avg_duration', 0),
        "stop_std_duration": analysis_result.get('stop_std_duration', 0),
        "stop_anomalous_count": analysis_result.get('stop_anomalous_count', 0)
    }
    
    # 분석 설정이 변경되었는지 확인
    analysis_changed = False
    if current_analysis_key in st.session_state:
        stored_analysis = st.session_state[current_analysis_key]
        # 주요 지표 값의 변화 확인
        for key, value in current_analysis.items():
            if key not in stored_analysis or abs(stored_analysis[key] - value) > 0.01:
                analysis_changed = True
                break
    else:
        # 최초 실행 시
        analysis_changed = True
    
    # 현재 분석 설정 업데이트
    st.session_state[current_analysis_key] = current_analysis
    
    # AI 분석 프롬프트 키
    cycle_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 분석 설정이 변경되었거나 프롬프트가 없으면 새로 생성
    if analysis_changed or cycle_prompt_key not in st.session_state:
        # 운전 주기 분석 정보
        operation_analysis = ""
        if cycles_df is not None and not cycles_df.empty:
            operation_analysis = f"""
## 운전 주기 분석
- 감지된 운전 주기 수: {analysis_result['operation_count']}개
- 평균 운전 시간: {analysis_result['operation_avg_duration']:.2f}분 (표준편차: {analysis_result['operation_std_duration']:.2f}분)
- 최소 운전 시간: {analysis_result['operation_min_duration']:.2f}분
- 최대 운전 시간: {analysis_result['operation_max_duration']:.2f}분
- 이상 운전 주기 수: {analysis_result['operation_anomalous_count']}개
"""
        
        # 정지 주기 분석 정보
        stop_analysis = ""
        if stop_cycles_df is not None and not stop_cycles_df.empty:
            stop_analysis = f"""
## 정지 주기 분석
- 감지된 정지 주기 수: {analysis_result['stop_count']}개
- 평균 정지 시간: {analysis_result['stop_avg_duration']:.2f}분 (표준편차: {analysis_result['stop_std_duration']:.2f}분)
- 최소 정지 시간: {analysis_result['stop_min_duration']:.2f}분
- 최대 정지 시간: {analysis_result['stop_max_duration']:.2f}분
- 이상 정지 주기 수: {analysis_result['stop_anomalous_count']}개
"""
        
        # 운전/정지 비율 분석
        ratio_analysis = ""
        if (cycles_df is not None and not cycles_df.empty) and (stop_cycles_df is not None and not stop_cycles_df.empty):
            total_operation_time = cycles_df['duration_min'].sum()
            total_stop_time = stop_cycles_df['duration_min'].sum()
            total_time = total_operation_time + total_stop_time
            
            if total_time > 0:
                operation_ratio = total_operation_time / total_time * 100
                stop_ratio = total_stop_time / total_time * 100
                ratio_analysis = f"""
## 운전/정지 비율 분석
- 전체 운전 시간: {total_operation_time:.2f}분
- 전체 정지 시간: {total_stop_time:.2f}분
- 운전 비율: {operation_ratio:.2f}%
- 정지 비율: {stop_ratio:.2f}%
"""
        
        # 이상 주기 상세 정보
        anomaly_details = ""
        if analysis_result['operation_anomalous_count'] > 0 or analysis_result['stop_anomalous_count'] > 0:
            anomaly_details = "## 이상 주기 상세 정보\n"
            
            # 운전 이상 주기
            if analysis_result['operation_anomalous_count'] > 0:
                anomaly_details += "### 이상 운전 주기\n"
                for i, cycle in enumerate(analysis_result['operation_anomalous_cycles'][:3]):  # 최대 3개까지만 표시
                    anomaly_details += f"- 주기 ID {cycle['cycle_id']}: 지속 시간 {cycle['duration_min']:.2f}분 (Z-score: {cycle['duration_zscore']:.2f})\n"
                if len(analysis_result['operation_anomalous_cycles']) > 3:
                    anomaly_details += f"- 그 외 {len(analysis_result['operation_anomalous_cycles']) - 3}개 추가 이상 주기\n"
            
            # 정지 이상 주기
            if analysis_result['stop_anomalous_count'] > 0:
                anomaly_details += "### 이상 정지 주기\n"
                for i, cycle in enumerate(analysis_result['stop_anomalous_cycles'][:3]):  # 최대 3개까지만 표시
                    anomaly_details += f"- 주기 ID {cycle['cycle_id']}: 지속 시간 {cycle['duration_min']:.2f}분 (Z-score: {cycle['duration_zscore']:.2f})\n"
                if len(analysis_result['stop_anomalous_cycles']) > 3:
                    anomaly_details += f"- 그 외 {len(analysis_result['stop_anomalous_cycles']) - 3}개 추가 이상 주기\n"

        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 제조 설비의 IoT 센서 데이터에서 운전/정지 주기를 분석하는 전문가입니다. 운전/정지 주기의 패턴과 이상 징후를 분석하여 실용적인 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type} 값으로, 임계값을 기준으로 운전 상태와 정지 상태를 구분하여 주기를 감지했습니다.
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 {equipment_type}의 운전/정지 주기 분석 결과입니다.

{operation_analysis}
{stop_analysis}
{ratio_analysis}
{anomaly_details}

## 분석 과제
위 운전/정지 주기 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. 운전/정지 주기 패턴의 전반적인 특성과 의미
   - 주기의 규칙성 또는 불규칙성이 의미하는 바
   - 평균 운전/정지 시간이 설비 성능에 주는 의미

2. 이상 주기의 의미와 가능한 원인
   - 비정상적으로 길거나 짧은 주기가 나타나는 이유
   - 이상 주기가 설비 상태에 미치는 영향

3. 운전/정지 비율 분석과 최적화 방안
   - 현재 운전/정지 비율이 적절한지 여부
   - 효율성 향상을 위한 주기 최적화 방안

4. 설비 모니터링 및 유지보수 전략 제안
   - 주기 분석을 기반으로 한 예측 정비 방안
   - 이상 주기 감지를 위한 모니터링 전략

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요.
"""
        # 주기 분석 전용 프롬프트로 저장
        st.session_state[cycle_prompt_key] = analysis_prompt
        
        # 분석 설정이 변경되면 캐시도 초기화
        if analysis_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"분석 설정이 변경되어 캐시 초기화")
    else:
        # 캐시된 주기 분석 전용 프롬프트 사용
        analysis_prompt = st.session_state[cycle_prompt_key]
    
    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 주기 분석")

    # 세션 상태 키 정의 - 모두 주기 분석 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 분석 실행 여부 확인 - 주기 분석 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 주기 분석 전용
    def on_cycle_analyze_click():
        st.session_state[running_key] = True
        
        # 캐시 초기화
        if cache_state_key not in st.session_state:
            st.session_state[cache_state_key] = {}
            
        if chat_history_key not in st.session_state:
            st.session_state[chat_history_key] = []
    
    # 분석 버튼 추가
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 주기 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_cycle_analyze_click,
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
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 주기 분석 데이터를 분석하고 있습니다..."):
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 주기 분석 실행' 버튼을 클릭하세요. 운전/정지 주기 데이터의 패턴과 이상 징후를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 주기 데이터에 대해 질문하기")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 주기 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 