import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import random

# 시작 날짜를 고정된 값으로 설정 (2022년 12월 19일)
start_date = datetime(2022, 1, 1)
# 종료 날짜 설정 (예: 시작일로부터 30일 후)
end_date = start_date + timedelta(days=365)

# Lot ID 생성 함수
def generate_lot_id(date, seq):
    """
    날짜와 순번으로 Lot ID 생성
    
    Args:
        date (datetime): 날짜
        seq (int): 순번
    
    Returns:
        str: Lot ID (예: 2212190)
    """
    return f"{date.strftime('%y%m%d')}{seq:02d}"

# 1차 공정 데이터 생성 함수 - 첨부 그림 참조 구현
def generate_process_1_data():
    """
    1차 공정 데이터 생성 - 설비 공유 제약 및 종료 날짜 고려
    그림과 같이 각 lot이 순차적으로 공정 처리
    """
    # 공정 단계와 요청된 소요 시간 설정 (분)
    stages = ['mixer', 'hopper', 'auger', 'rhk_input', 'rhk_output', 'roc']
    durations = {
        'mixer': 10,      # 10분 내외 간격
        'hopper': 100,    # 100분 내외 간격
        'auger': 60,      # 60분 내외 간격
        'rhk_input': 30,  # 30분 내외 간격
        'rhk_output': 30, # 30분 내외 간격
        'roc': 40         # 40분 내외 간격
    }
    
    # 설비별 마지막 사용 완료 시간 추적 (설비 공유 제약 구현)
    equipment_end_times = {stage: start_date for stage in stages}
    
    data = []
    
    # Lot 간 시작 시간 간격 - 가장 긴 설비 시간(hopper의 100분)을 기준으로 설정
    lot_interval = max(durations.values()) # 가장 긴 설비 시간으로 인터벌 설정
    
    # 총 10개의 lot 생성 -> 종료 날짜까지 생성하도록 변경
    i = 1 # Lot 순번 초기화
    while True:
        # 현재 날짜
        current_date = start_date # 각 Lot의 시작 날짜는 start_date를 기준으로 함

        # 공정 시작 시간 설정 - 각 lot은 이전 lot보다 lot_interval분 후에 시작
        base_time = current_date.replace(hour=9, minute=0, second=0)
        process_base_time = base_time + timedelta(minutes=lot_interval * (i-1))

        # 공정 단계별 시작/종료 시간 계산 (임시)
        temp_process_times = {}
        current_time = process_base_time
        final_end_time = None # 마지막 공정 종료 시간 추적

        for stage in stages:
            # 이 설비가 이전에 사용 중이었다면, 그 완료 시간 이후로 조정
            if current_time < equipment_end_times[stage]:
                current_time = equipment_end_times[stage]

            # 고정된 소요 시간 적용
            duration = durations[stage]

            # 약간의 랜덤성 추가 (±5% 변동)
            actual_duration = int(duration * random.uniform(0.95, 1.05))

            start_time = current_time
            end_time = current_time + timedelta(minutes=actual_duration)

            temp_process_times[f"{stage}_start"] = start_time
            temp_process_times[f"{stage}_end"] = end_time

            # 이 설비의 완료 시간 업데이트 (임시)
            # equipment_end_times[stage] = end_time # 실제 추가 시점에 업데이트

            # 다음 단계로 즉시 이동 (대기 시간 없음)
            current_time = end_time
            final_end_time = end_time # 마지막 단계의 종료 시간 저장

        # 마지막 공정 종료 시간이 end_date를 초과하면 루프 중단
        if final_end_time > end_date:
            break

        # Lot ID 생성 - 번호를 3자리로 설정 (001, 002, ...)
        lot_id = f"{process_base_time.strftime('%y%m%d')}{i:03d}" # Lot ID는 실제 공정 시작 시간 기준으로 생성

        # 최종 공정 시간 계산 및 설비 종료 시간 업데이트
        process_times = {}
        current_time = process_base_time # 시간 재설정
        for stage in stages:
             # 이 설비가 이전에 사용 중이었다면, 그 완료 시간 이후로 조정
            if current_time < equipment_end_times[stage]:
                current_time = equipment_end_times[stage]

            # 고정된 소요 시간 적용
            duration = durations[stage]

            # 약간의 랜덤성 추가 (±5% 변동)
            actual_duration = int(duration * random.uniform(0.95, 1.05))

            start_time = current_time
            end_time = current_time + timedelta(minutes=actual_duration)

            process_times[f"{stage}_start"] = start_time.strftime('%Y-%m-%d %H:%M:%S')
            process_times[f"{stage}_end"] = end_time.strftime('%Y-%m-%d %H:%M:%S')

            # 이 설비의 완료 시간 업데이트 (최종)
            equipment_end_times[stage] = end_time

            # 다음 단계로 즉시 이동 (대기 시간 없음)
            current_time = end_time


        # Target ICP 값 생성 (정규 분포 사용)
        # 평균 0.5, 표준편차 0.15, 값을 0.1 ~ 0.9 사이로 제한
        target_icp = round(np.clip(np.random.normal(loc=0.5, scale=0.15), 0.1, 0.9), 4)
        
        # Outlier 생성 (확률 조정: 예: 1%)
        if random.random() < 0.005:
            # 0.0 ~ 0.05 또는 0.95 ~ 1.0 사이의 값으로 대체
            if random.random() < 0.5:
                target_icp = round(random.uniform(0.0, 0.05), 4)
            else:
                target_icp = round(random.uniform(0.95, 1.0), 4)
        
        # 데이터 행 생성
        row = {
            'date': process_base_time.strftime('%Y-%m-%d'), # 각 lot의 시작 날짜
            'lot_id': lot_id,
            **process_times,
            'target_icp1': target_icp
        }
        
        data.append(row)
        i += 1 # 다음 Lot 번호
    
    return pd.DataFrame(data)

# 2차 공정 데이터 생성 함수
def generate_process_2_data():
    """
    2차 공정 데이터 생성 - 설비 공유 제약 및 종료 날짜 고려
    이미지에 맞게 순차적으로 처리되도록 수정
    """
    # 공정 단계와 요청된 소요 시간 설정 (분)
    stages = ['mixer', 'hopper', 'auger', 'rhk_input', 'rhk_output', 'roc']
    durations = {
        'mixer': 10,      # 10분 내외 간격
        'hopper': 100,    # 100분 내외 간격
        'auger': 60,      # 60분 내외 간격
        'rhk_input': 30,  # 30분 내외 간격
        'rhk_output': 30, # 30분 내외 간격
        'roc': 40         # 40분 내외 간격
    }
    
    # 설비별 마지막 사용 완료 시간 추적 (설비 공유 제약 구현)
    equipment_end_times = {stage: start_date for stage in stages}
    
    data = []
    
    # 날짜 설정 (2차 공정은 12월 20일에 시작)
    process_start_day_offset = 1 # 시작일로부터 1일 뒤 시작
    process_initial_date = start_date + timedelta(days=process_start_day_offset)

    # Lot 간 시작 시간 간격 - 가장 긴 설비 시간(hopper의 100분)을 기준으로 설정
    lot_interval = max(durations.values()) # 가장 긴 설비 시간으로 인터벌 설정
    
    # 총 8개의 lot 생성 -> 종료 날짜까지 생성하도록 변경
    i = 1 # Lot 순번 초기화
    while True:
        # 기본 시작 시간 설정
        # 1차 공정과 동일하게 timedelta를 사용하여 계산
        base_time = process_initial_date.replace(hour=10, minute=0, second=0) # 2차 공정 시작 시간 기준
        process_start = base_time + timedelta(minutes=lot_interval * (i-1))

        # 각 단계별 시작/종료 시간 계산 (임시)
        temp_process_times = {}
        current_time = process_start
        final_end_time = None

        for stage in stages:
            # 이 설비가 이전에 사용 중이었다면, 그 완료 시간 이후로 조정
            if current_time < equipment_end_times[stage]:
                current_time = equipment_end_times[stage]

            # 고정된 소요 시간 적용
            duration = durations[stage]

            # 약간의 랜덤성 추가 (±5% 변동)
            actual_duration = int(duration * random.uniform(0.95, 1.05))

            start_time = current_time
            end_time = current_time + timedelta(minutes=actual_duration)

            temp_process_times[f"{stage}_start"] = start_time
            temp_process_times[f"{stage}_end"] = end_time

            # 다음 단계로 이동 (단계 간 전환 시간 없음)
            current_time = end_time
            final_end_time = end_time

        # 마지막 공정 종료 시간이 end_date를 초과하면 루프 중단
        if final_end_time > end_date:
            break

        # Lot ID 생성
        lot_id = f"{process_start.strftime('%y%m%d')}{i:03d}"

        # 최종 공정 시간 계산 및 설비 종료 시간 업데이트
        process_times = {}
        current_time = process_start # 시간 재설정
        for stage in stages:
            # 이 설비가 이전에 사용 중이었다면, 그 완료 시간 이후로 조정 (1차 공정과 동일한 로직)
            if current_time < equipment_end_times[stage]:
                current_time = equipment_end_times[stage]

            # 고정된 소요 시간 적용
            duration = durations[stage]

            # 약간의 랜덤성 추가 (±5% 변동)
            actual_duration = int(duration * random.uniform(0.95, 1.05))

            start_time = current_time
            end_time = current_time + timedelta(minutes=actual_duration)

            # 시간 기록
            process_times[f"{stage}_start"] = start_time.strftime('%Y-%m-%d %H:%M:%S')
            process_times[f"{stage}_end"] = end_time.strftime('%Y-%m-%d %H:%M:%S')

            # 이 설비의 완료 시간 업데이트
            equipment_end_times[stage] = end_time

            # 다음 단계로 이동 (단계 간 전환 시간 없음)
            current_time = end_time

        # Target ICP 값 생성 (정규 분포 사용)
        # 평균 0.5, 표준편차 0.15, 값을 0.1 ~ 0.9 사이로 제한
        target_icp = round(np.clip(np.random.normal(loc=0.5, scale=0.15), 0.1, 0.9), 4)
        
        # Outlier 생성 (확률 조정: 예: 1%)
        if random.random() < 0.01:
            # 0.0 ~ 0.05 또는 0.95 ~ 1.0 사이의 값으로 대체
            if random.random() < 0.5:
                target_icp = round(random.uniform(0.0, 0.05), 4)
            else:
                target_icp = round(random.uniform(0.95, 1.0), 4)
        
        # 데이터 행 생성
        row = {
            'date': process_start.strftime('%Y-%m-%d'),
            'lot_id': lot_id,
            **process_times,
            'target_icp2': target_icp
        }
        
        data.append(row)
        i += 1 # 다음 Lot 번호
    
    return pd.DataFrame(data)

# 3차 공정 데이터 생성 함수
def generate_process_3_data():
    """
    3차 공정 데이터 생성 - 설비 공유 제약 및 종료 날짜 고려
    """
    # 공정 단계와 요청된 소요 시간 설정 (분)
    stages = ['washing', 'filter_press', 'dry', 'cooler', 'shifter', 'ems', 'packing']
    durations = {
        'washing': 240,       # 240분 내외 간격 (4시간)
        'filter_press': 240,  # 240분 내외 간격 (4시간)
        'dry': 1440,          # 24시간(1440분) 내외 간격
        'cooler': 240,        # 240분 내외 간격 (4시간)
        'shifter': 240,       # 240분 내외 간격 (4시간)
        'ems': 240,           # 240분 내외 간격 (4시간)
        'packing': 240        # 240분 내외 간격 (4시간)
    }
    
    # 설비별 마지막 사용 완료 시간 추적 (설비 공유 제약 구현)
    equipment_end_times = {stage: start_date for stage in stages}
    
    data = []
    
    # Lot 간 시작 시간 간격 - 가장 긴 설비 시간(dry의 1440분)을 기준으로 설정
    lot_interval = max(durations.values()) # 가장 긴 설비 시간으로 인터벌 설정
    
    # 3차 공정 시작일 설정
    process_start_day_offset = 2 # 시작일로부터 2일 뒤 시작
    process_initial_date = start_date + timedelta(days=process_start_day_offset)

    # 3차 공정은 총 7개의 lot 생성 -> 종료 날짜까지 생성하도록 변경
    i = 1 # Lot 순번 초기화
    while True:
        # 공정 시작 시간 설정 - 1, 2차 공정과 동일하게 timedelta 사용
        # 3차 공정 첫 lot의 기준 시작 시간 (시작일 + 2일, 오전 8시)
        base_time = process_initial_date.replace(hour=8, minute=0, second=0)
        process_base_time = base_time + timedelta(minutes=lot_interval * (i-1))

        # 공정 단계별 시작/종료 시간 계산 (임시)
        temp_process_times = {}
        current_time = process_base_time
        final_end_time = None

        for stage in stages:
            # 이 설비가 이전에 사용 중이었다면, 그 완료 시간 이후로 조정
            if current_time < equipment_end_times[stage]:
                current_time = equipment_end_times[stage]

            # 고정된 소요 시간 적용
            duration = durations[stage]

            # 약간의 랜덤성 추가 (±5% 변동, dry는 ±2%로 줄임)
            if stage == 'dry':
                actual_duration = int(duration * random.uniform(0.98, 1.02))
            else:
                actual_duration = int(duration * random.uniform(0.95, 1.05))

            start_time = current_time
            end_time = current_time + timedelta(minutes=actual_duration)

            temp_process_times[f"{stage}_start"] = start_time
            temp_process_times[f"{stage}_end"] = end_time

            # 이 설비의 완료 시간 업데이트 (임시)
            # equipment_end_times[stage] = end_time

            # 다음 단계로 이동 (dry 단계 후에는 2시간 대기 - 실제 공정 반영)
            if stage == 'dry':
                current_time = end_time + timedelta(hours=2)
            else:
                current_time = end_time
            final_end_time = end_time # packing 단계의 종료 시간 저장

        # 마지막 공정(packing) 종료 시간이 end_date를 초과하면 루프 중단
        if final_end_time > end_date:
            break

        # Lot ID 생성 - 번호를 3자리로 설정
        lot_id = f"{process_base_time.strftime('%y%m%d')}{i:03d}"

        # 최종 공정 시간 계산 및 설비 종료 시간 업데이트
        process_times = {}
        current_time = process_base_time # 시간 재설정
        for stage in stages:
            # 이 설비가 이전에 사용 중이었다면, 그 완료 시간 이후로 조정
            if current_time < equipment_end_times[stage]:
                current_time = equipment_end_times[stage]

            # 고정된 소요 시간 적용
            duration = durations[stage]

            # 약간의 랜덤성 추가 (±5% 변동, dry는 ±2%로 줄임)
            if stage == 'dry':
                actual_duration = int(duration * random.uniform(0.98, 1.02))
            else:
                actual_duration = int(duration * random.uniform(0.95, 1.05))

            start_time = current_time
            end_time = current_time + timedelta(minutes=actual_duration)

            process_times[f"{stage}_start"] = start_time.strftime('%Y-%m-%d %H:%M:%S')
            process_times[f"{stage}_end"] = end_time.strftime('%Y-%m-%d %H:%M:%S')

            # 이 설비의 완료 시간 업데이트
            equipment_end_times[stage] = end_time

            # 다음 단계로 이동 (dry 단계 후에는 2시간 대기 - 실제 공정 반영)
            if stage == 'dry':
                current_time = end_time + timedelta(hours=2)
            else:
                current_time = end_time

        # Target ICP 값 생성 (정규 분포 사용)
        # 평균 0.5, 표준편차 0.15, 값을 0.1 ~ 0.9 사이로 제한
        target_icp = round(np.clip(np.random.normal(loc=0.5, scale=0.15), 0.1, 0.9), 4)
        
        # Outlier 생성 (확률 조정: 예: 1%)
        if random.random() < 0.01:
            # 0.0 ~ 0.05 또는 0.95 ~ 1.0 사이의 값으로 대체
            if random.random() < 0.5:
                target_icp = round(random.uniform(0.0, 0.05), 4)
            else:
                target_icp = round(random.uniform(0.95, 1.0), 4)
        
        # 데이터 행 생성
        row = {
            'date': process_base_time.strftime('%Y-%m-%d'), # 각 lot의 시작 날짜로 변경
            'lot_id': lot_id,
            **process_times,
            'target_icp3': target_icp
        }
        
        data.append(row)
        i += 1 # 다음 Lot 번호

    return pd.DataFrame(data)

# # 디렉토리 생성 (주석 처리 또는 삭제 - 각 분석/시각화 스크립트에서 생성)
# os.makedirs('visualization', exist_ok=True)
# os.makedirs('analysis', exist_ok=True)

# 데이터 생성
df_process1 = generate_process_1_data()
df_process2 = generate_process_2_data()
df_process3 = generate_process_3_data()

# CSV 파일로 저장
df_process1.to_csv('lot_normalized_data_1.csv', index=False)
df_process2.to_csv('lot_normalized_data_2.csv', index=False)
df_process3.to_csv('lot_normalized_data_3.csv', index=False)

print(f"데이터 생성 완료: 시작일 {start_date.strftime('%Y-%m-%d')}부터 종료일 {end_date.strftime('%Y-%m-%d')}까지 설비 공유 제약 반영")
print(f"1차 공정: {len(df_process1)}개 Lot")
print(f"2차 공정: {len(df_process2)}개 Lot")
print(f"3차 공정: {len(df_process3)}개 Lot") 