import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import time
import os
from .data_utils import DATA_DIR, get_equipment_type, get_sensor_type, save_df_to_file

def generate_iot_data(total_records, start_date, end_date, equipment_type, 
                      min_value, max_value, pattern_type, noise_level,
                      simulate_failures=False, failure_count=5, failure_duration=6,
                      operation_minutes=60, shutdown_minutes=30, sensor_type="value"):
    """IoT 센서 데이터를 생성합니다.
    
    Args:
        total_records (int): 생성할 총 레코드 수
        start_date (datetime): 시작 날짜
        end_date (datetime): 종료 날짜
        equipment_type (str): 장비 유형
        min_value (float): 최소값
        max_value (float): 최대값
        pattern_type (str): 패턴 유형 (일정, 계절성, 증가, 감소, 증가+계절성, 감소+계절성, 운전/정지 주기)
        noise_level (float): 노이즈 수준 (0.0~1.0)
        simulate_failures (bool): 고장 시뮬레이션 여부
        failure_count (int): 고장 횟수
        failure_duration (int): 고장 평균 지속 시간(시간)
        operation_minutes (int): 운전 시간 (분)
        shutdown_minutes (int): 정지 시간 (분)
        sensor_type (str): 센서 유형 (기본값: "value")
        
    Returns:
        pandas.DataFrame: 생성된 IoT 데이터
    """
    # 날짜 범위 생성
    date_range = pd.date_range(start=start_date, end=end_date, periods=total_records)
    
    # 기본 값 범위 설정
    value_range = max_value - min_value
    baseline = min_value + value_range * 0.5  # 중간값 기준
    
    # 패턴에 따른 기본 값 생성
    if pattern_type == "일정" or pattern_type == "정상":
        base_values = np.ones(len(date_range)) * baseline
    elif pattern_type == "계절성" or pattern_type == "주기적 변동":
        # 사인 곡선을 사용한 계절성 패턴
        t = np.linspace(0, 4*np.pi, len(date_range))  # 2 사이클
        base_values = baseline + np.sin(t) * (value_range * 0.4)
    elif pattern_type == "증가" or pattern_type == "점진적 증가":
        # 선형 증가 패턴
        t = np.linspace(0, 1, len(date_range))
        base_values = min_value + t * value_range * 0.8
    elif pattern_type == "감소" or pattern_type == "점진적 감소":
        # 선형 감소 패턴
        t = np.linspace(0, 1, len(date_range))
        base_values = max_value - t * value_range * 0.8
    elif pattern_type == "증가+계절성":
        # 증가 추세와 계절성 결합
        t1 = np.linspace(0, 1, len(date_range))
        t2 = np.linspace(0, 4*np.pi, len(date_range))
        trend = min_value + t1 * value_range * 0.6
        seasonal = np.sin(t2) * (value_range * 0.2)
        base_values = trend + seasonal
    elif pattern_type == "감소+계절성":
        # 감소 추세와 계절성 결합
        t1 = np.linspace(0, 1, len(date_range))
        t2 = np.linspace(0, 4*np.pi, len(date_range))
        trend = max_value - t1 * value_range * 0.6
        seasonal = np.sin(t2) * (value_range * 0.2)
        base_values = trend + seasonal
    elif pattern_type == "랜덤 스파이크":
        # 기본값에 랜덤 스파이크 추가
        base_values = np.ones(len(date_range)) * baseline
        # 랜덤 스파이크 생성 (약 1%)
        spike_indices = np.random.choice(len(date_range), size=int(len(date_range) * 0.01), replace=False)
        spike_magnitudes = np.random.normal(0, value_range * 0.6, size=len(spike_indices))
        for idx, mag in zip(spike_indices, spike_magnitudes):
            base_values[idx] += mag
    elif pattern_type == "계절적 변동":
        # 계절성과 일별 패턴 결합
        days = np.linspace(0, 365, len(date_range)) % 365  # 일년 내 일수로 변환
        hours = np.array([(t.hour + t.minute/60) for t in date_range.to_pydatetime()])  # 시간
        
        # 계절성 (1년 주기) + 일별 패턴 (24시간 주기)
        seasonal_comp = np.sin(days * 2 * np.pi / 365) * value_range * 0.3
        daily_comp = np.sin(hours * 2 * np.pi / 24) * value_range * 0.1
        base_values = baseline + seasonal_comp + daily_comp
    elif pattern_type == "운전/정지 주기":
        # 운전/정지 주기 생성
        base_values = np.ones(len(date_range)) * baseline
        
        # 타임스탬프 간격 계산
        if len(date_range) > 1:
            time_interval = (date_range[1] - date_range[0]).total_seconds() / 60  # 분 단위
        else:
            time_interval = 1  # 기본값 1분
        
        # 전체 주기 시간 (분)
        cycle_duration = operation_minutes + shutdown_minutes
        
        # 각 데이터 포인트에 대한 주기 내 위치 계산
        cycle_positions = np.array([(t - date_range[0]).total_seconds() / 60 % cycle_duration 
                                  for t in date_range])
        
        # 운전 상태인지 판별 (True: 운전, False: 정지)
        is_operating = cycle_positions < operation_minutes
        
        # 운전 시 정상값, 정지 시 최소값에 가까운 값 설정 - 더 명확한 차이 설정
        operating_level = max_value * 0.8  # 운전 시 값 (최대값의 약 80%)
        shutdown_level = min_value + value_range * 0.05  # 정지 시 값 (최소값에 매우 가깝게)
        
        # 상태별 미세 변동 범위 정의 (운전 상태는 더 큰 변동폭으로 설정)
        operating_variation = value_range * 0.12  # 운전 상태 내 변동 폭 (12%)
        shutdown_variation = value_range * 0.01  # 정지 상태 내 변동 폭 (1% - 더 감소)
        
        # 운전/정지 상태 구분용 레이블 배열 (시각화용, 1: 운전, 0: 정지)
        operation_state = np.zeros(len(date_range))
        
        # 운전/정지 상태에 따라 값 설정
        for i in range(len(base_values)):
            if is_operating[i]:
                # 운전 상태: 기준 레벨 + 랜덤 노이즈
                operation_state[i] = 1  # 운전 상태 레이블
                
                # 운전 중 값이 매우 안정적으로 유지되도록 설정
                if i > 0 and is_operating[i-1]:
                    # 이전 값과 동일한 값을 유지할 확률 (95%)
                    if np.random.random() < 0.98:
                        base_values[i] = base_values[i-1]
                    else:
                        # 새로운 랜덤 값 생성 (이전 값과 매우 근접하게)
                        new_value = base_values[i-1] + np.random.uniform(-operating_variation/5, operating_variation/5)
                        base_values[i] = np.clip(new_value, operating_level - operating_variation/2, operating_level + operating_variation/2)
                else:
                    # 주기 시작 시 새로운 랜덤 값 시작 (변동폭 감소)
                    base_values[i] = operating_level + np.random.uniform(-operating_variation/4, operating_variation/4)
            else:
                # 정지 상태: 낮은 레벨 + 매우 작은 변동
                operation_state[i] = 0  # 정지 상태 레이블
                # 정지 상태는 매우 일정한 값 유지
                base_values[i] = shutdown_level + np.random.uniform(-shutdown_variation, shutdown_variation)
        
        # 상태 전환 시 즉각적인 변화 적용 (스위치처럼)
        for i in range(1, len(base_values)):
            # 운전→정지 전환 감지
            if i > 0 and is_operating[i-1] and not is_operating[i]:
                # 즉시 정지 레벨로 전환
                base_values[i] = shutdown_level
            
            # 정지→운전 전환 감지
            elif i > 0 and not is_operating[i-1] and is_operating[i]:
                # 즉시 운전 레벨로 전환
                base_values[i] = operating_level
    else:
        # 기본적으로 일정한 값
        base_values = np.ones(len(date_range)) * baseline
    
    # 노이즈 추가
    noise = np.random.normal(0, noise_level * value_range * 0.2, len(date_range))
    values = base_values + noise
    
    # 가능한 장비 고장 시뮬레이션
    if simulate_failures and failure_count > 0:
        # 고장 시작 시간 랜덤 선택
        failure_starts = np.random.choice(
            range(len(date_range) - int(failure_duration * 3600 / (date_range[1] - date_range[0]).seconds)), 
            size=failure_count, 
            replace=False
        )
        
        for start_idx in failure_starts:
            # 고장 지속 시간 (평균 failure_duration 시간, 표준편차 1시간)
            duration_hours = max(1, int(np.random.normal(failure_duration, 1)))
            
            # 고장 패턴 선택 (급격한 증가, 급격한 감소, 또는 불규칙한 값)
            failure_type = np.random.choice(["급증", "급감", "불규칙"])
            
            # 고장 기간 동안의 값 계산
            duration_points = int(duration_hours * 3600 / (date_range[1] - date_range[0]).seconds)
            end_idx = min(start_idx + duration_points, len(values) - 1)
            
            if failure_type == "급증":
                # 급격한 증가 후 서서히 정상화
                peak = max_value * (1.1 + np.random.random() * 0.3)  # 최대값보다 10-40% 증가
                values[start_idx:end_idx] = np.linspace(values[start_idx], peak, end_idx - start_idx)
                # 정상화 구간
                normal_idx = min(end_idx + duration_points // 2, len(values) - 1)
                if end_idx < normal_idx:
                    values[end_idx:normal_idx] = np.linspace(peak, base_values[normal_idx], normal_idx - end_idx)
            
            elif failure_type == "급감":
                # 급격한 감소 후 서서히 정상화
                bottom = min_value * (0.7 - np.random.random() * 0.4)  # 최소값보다 30-70% 감소
                values[start_idx:end_idx] = np.linspace(values[start_idx], bottom, end_idx - start_idx)
                # 정상화 구간
                normal_idx = min(end_idx + duration_points // 2, len(values) - 1)
                if end_idx < normal_idx:
                    values[end_idx:normal_idx] = np.linspace(bottom, base_values[normal_idx], normal_idx - end_idx)
            
            else:  # 불규칙
                # 불규칙한 값 (높은 표준편차)
                irregular_noise = np.random.normal(0, value_range * 0.5, end_idx - start_idx)
                values[start_idx:end_idx] = base_values[start_idx:end_idx] + irregular_noise
    
    # 값을 min_value와 max_value 사이로 자르기
    values = np.clip(values, min_value, max_value)
    
    # 데이터프레임 생성
    df = pd.DataFrame({
        'id': range(1, len(date_range) + 1),
        'timestamp': date_range,
        sensor_type: values
    })
    
    # equipment_type 정보 세션에 저장
    st.session_state.equipment_type = equipment_type
    # sensor_type 정보 세션에 저장
    st.session_state.sensor_type = sensor_type
    
    return df 