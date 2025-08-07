import os
import time
import pandas as pd
import sys
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import concurrent.futures
import plotly.io as pio

# Add parent directory to path to import from iot package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from iot_prism.utils import (
    DATA_DIR,
    parallel_process_file,
    optimize_dtypes
)

# 참고: 스타일 및 폰트 적용은 iot/utils/style.py의 load_iot_font_css(), get_font_path()를 참조하세요.
# Plotly 그래프의 폰트도 동일한 Paperlogy.ttf를 사용합니다.

# 커스텀 폰트 경로
FONT_PATH = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'Paperlogy.ttf')
FONT_FAMILY = 'Paperlogy'

# Plotly에 커스텀 폰트 등록 (로컬 폰트 사용)
pio.templates.default = "plotly_white"

# 실용적인 데이터 샘플 크기 설정
SAMPLE_SIZE = 30000000  # 50만 레코드 (실행 시간 단축을 위해)

def create_test_data(total_records=SAMPLE_SIZE, file_path=None):
    """IoT Prism의 일반적인 데이터와 유사한 테스트 데이터를 생성합니다"""
    print(f"총 {total_records:,}개의 레코드를 생성합니다...")
    
    # 날짜 범위 생성 (1개월)
    start_date = datetime.strptime("2023-01-01", "%Y-%m-%d")
    end_date = datetime.strptime("2023-01-31", "%Y-%m-%d")
    date_range = pd.date_range(start=start_date, end=end_date, periods=total_records)
    
    # 다양한 센서 데이터 시뮬레이션
    # IoT Prism의 일반적인 센서 데이터와 유사하게 구성
    np.random.seed(42)  # 재현성을 위한 시드 설정
    
    # 장비 ID 목록 생성
    equipment_ids = [f'EQUIP_{i:03d}' for i in range(1, 21)]  # 20개 장비
    
    # 실제와 유사한 센서 데이터 생성
    df = pd.DataFrame({
        'timestamp': date_range,
        'equipment_id': np.random.choice(equipment_ids, size=total_records),
        'temperature': np.random.normal(25, 3, total_records),  # 온도 (°C)
        'humidity': np.random.normal(60, 10, total_records),    # 습도 (%)
        'pressure': np.random.normal(1013, 5, total_records),   # 기압 (hPa)
        'vibration': np.random.exponential(0.5, total_records), # 진동
        'voltage': np.random.normal(220, 5, total_records),     # 전압 (V)
        'current': np.random.normal(5, 0.5, total_records)      # 전류 (A)
    })
    
    # 비정상 패턴 추가 (이상치)
    anomaly_indices = np.random.choice(total_records, size=int(total_records * 0.01), replace=False)
    df.loc[anomaly_indices, 'temperature'] *= 1.5
    df.loc[anomaly_indices, 'vibration'] *= 3
    
    # 결측값 추가
    for col in ['temperature', 'humidity', 'pressure', 'voltage']:
        missing_indices = np.random.choice(total_records, size=int(total_records * 0.005), replace=False)
        df.loc[missing_indices, col] = np.nan
    
    # 파생 변수 계산
    df['power'] = df['voltage'] * df['current']  # 전력 (W)
    
    # 파일로 저장
    if file_path is None:
        # 디렉토리 확인 및 생성
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # 파일 경로 생성
        file_path = os.path.join(DATA_DIR, f'iot_sensor_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    
    # CSV로 저장
    print(f"데이터프레임을 CSV 파일로 저장 중: {file_path}")
    df.to_csv(file_path, index=False)
    print(f"파일 크기: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
    
    return df, file_path

# IoT Prism의 일반적인 분석 작업을 시뮬레이션하는 함수
def process_iot_data(df):
    """IoT 데이터 처리 및 분석 함수"""
    # 1. 데이터 정제
    print("데이터 정제 중...")
    # 결측값 처리
    df = df.fillna(method='ffill').fillna(method='bfill')
    
    # 2. 시간 기반 특성 추출
    print("시간 기반 특성 추출 중...")
    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.day
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # 3. 집계 통계 계산 (그룹별)
    print("집계 통계 계산 중...")
    agg_stats = df.groupby('equipment_id').agg({
        'temperature': ['mean', 'min', 'max', 'std'],
        'humidity': ['mean', 'min', 'max', 'std'],
        'pressure': ['mean', 'min', 'max'],
        'vibration': ['mean', 'max'],
        'power': ['mean', 'max', 'min']
    })
    
    # 4. 시간대별 집계
    hourly_stats = df.groupby(['equipment_id', 'hour']).agg({
        'temperature': 'mean',
        'humidity': 'mean',
        'power': 'mean'
    }).reset_index()
    
    # 5. 이상치 탐지
    print("이상치 탐지 중...")
    # Z-점수 기반 이상치 탐지
    for col in ['temperature', 'humidity', 'vibration', 'power']:
        mean = df[col].mean()
        std = df[col].std()
        df[f'{col}_zscore'] = (df[col] - mean) / std
        df[f'{col}_is_anomaly'] = abs(df[f'{col}_zscore']) > 3
    
    # 6. 이동 평균 계산
    print("이동 평균 계산 중...")
    for col in ['temperature', 'humidity', 'pressure', 'power']:
        df[f'{col}_ma_10'] = df[col].rolling(window=10, min_periods=1).mean()
    
    # 7. 장비별 요약 정보
    equipment_summary = df.groupby('equipment_id').apply(lambda x: pd.Series({
        'record_count': len(x),
        'temp_anomalies': x['temperature_is_anomaly'].sum(),
        'vibration_anomalies': x['vibration_is_anomaly'].sum(),
        'avg_power': x['power'].mean(),
        'max_temp': x['temperature'].max(),
        'min_temp': x['temperature'].min()
    }))
    
    return {
        'processed_data': df,
        'agg_stats': agg_stats,
        'hourly_stats': hourly_stats,
        'equipment_summary': equipment_summary
    }

# 청크 단위로 처리하는 함수 (병렬 처리용)
def process_chunk(chunk):
    """데이터 청크 처리 함수"""
    # 타입이 문자열인 경우 날짜로 변환
    if 'timestamp' in chunk.columns and pd.api.types.is_string_dtype(chunk['timestamp']):
        chunk['timestamp'] = pd.to_datetime(chunk['timestamp'])
    
    # 데이터 타입 최적화
    chunk = optimize_dtypes(chunk)
    
    # 결측값 처리 (전진 채우기, 후진 채우기)
    chunk = chunk.fillna(method='ffill').fillna(method='bfill')
    
    # 파생 변수 계산 (필요한 경우)
    if 'power' not in chunk.columns and 'voltage' in chunk.columns and 'current' in chunk.columns:
        chunk['power'] = chunk['voltage'] * chunk['current']
    
    # 시간 기반 특성 추출
    if 'timestamp' in chunk.columns:
        chunk['hour'] = chunk['timestamp'].dt.hour
        chunk['day'] = chunk['timestamp'].dt.day
        chunk['day_of_week'] = chunk['timestamp'].dt.dayofweek
    
    # 통계 계산
    for col in ['temperature', 'humidity', 'pressure', 'vibration', 'power']:
        if col in chunk.columns:
            # 이동 평균
            chunk[f'{col}_ma_10'] = chunk[col].rolling(window=10, min_periods=1).mean()
            
            # Z-점수 계산
            mean = chunk[col].mean()
            std = chunk[col].std()
            if std > 0:  # 0으로 나누기 방지
                chunk[f'{col}_zscore'] = (chunk[col] - mean) / std
                chunk[f'{col}_is_anomaly'] = abs(chunk[f'{col}_zscore']) > 3
            else:
                chunk[f'{col}_zscore'] = 0
                chunk[f'{col}_is_anomaly'] = False
    
    return chunk

# 병렬 처리 함수
def parallel_process_iot_data(file_path, num_workers):
    """CSV 파일을 청크 단위로 병렬 처리"""
    # CSV 파일 크기 확인
    file_size = os.path.getsize(file_path)
    
    # 샘플링하여 레코드 수 예측
    sample = pd.read_csv(file_path, nrows=1000)
    sample_size_bytes = sample.memory_usage(deep=True).sum()
    avg_row_size = file_size / len(sample) if len(sample) > 0 else 1000
    estimated_rows = int(file_size / avg_row_size)
    
    # 청크 크기 계산
    chunk_size = max(1000, estimated_rows // num_workers)
    print(f"예상 레코드 수: {estimated_rows:,}, 청크 크기: {chunk_size:,}, 워커 수: {num_workers}")
    
    # 청크 단위로 데이터 읽기 및 처리
    chunks = pd.read_csv(file_path, chunksize=chunk_size, parse_dates=['timestamp'])
    
    # 병렬 처리
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_chunk, chunks))
    
    # 결과 합치기
    processed_df = pd.concat(results)
    
    # 집계 통계 계산
    equipment_columns = {
        'temperature': ['mean', 'min', 'max', 'std'],
        'humidity': ['mean', 'min', 'max', 'std'],
        'pressure': ['mean', 'min', 'max']
    }
    
    # 사용 가능한 컬럼만 선택
    agg_columns = {col: funcs for col, funcs in equipment_columns.items() 
                  if col in processed_df.columns}
    
    # 전력, 진동 컬럼이 있는 경우 추가
    if 'power' in processed_df.columns:
        agg_columns['power'] = ['mean', 'max', 'min']
    if 'vibration' in processed_df.columns:
        agg_columns['vibration'] = ['mean', 'max']
    
    # 집계 통계 계산
    agg_stats = processed_df.groupby('equipment_id').agg(agg_columns)
    
    # 장비별 요약 정보
    summary_data = {}
    
    for eq_id, group in processed_df.groupby('equipment_id'):
        row_data = {
            'record_count': len(group)
        }
        
        # 이상치 통계 (있는 경우만)
        for col in ['temperature', 'vibration', 'power']:
            anomaly_col = f'{col}_is_anomaly'
            if anomaly_col in group.columns:
                row_data[f'{col}_anomalies'] = group[anomaly_col].sum()
        
        # 평균값 통계
        for col in ['temperature', 'humidity', 'pressure', 'power']:
            if col in group.columns:
                row_data[f'avg_{col}'] = group[col].mean()
                
                # 최대/최소 온도는 특별히 중요
                if col == 'temperature':
                    row_data[f'max_{col}'] = group[col].max()
                    row_data[f'min_{col}'] = group[col].min()
        
        summary_data[eq_id] = row_data
    
    equipment_summary = pd.DataFrame.from_dict(summary_data, orient='index')
    
    return {
        'processed_data': processed_df,
        'agg_stats': agg_stats,
        'equipment_summary': equipment_summary
    }

# 시각화 함수
def create_visualization(data, file_path):
    """데이터 시각화 함수"""
    print("시각화 생성 중...")
    
    # 장비별 요약 정보 시각화
    equipment_summary = data['equipment_summary']
    
    # 대시보드 생성
    dashboard = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '장비별 이상치 발생 횟수', 
            '장비별 평균 온도',
            '장비별 평균 전력 소비',
            '장비별 레코드 수'
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )
    
    # 상위 10개 장비만 표시
    top_equipment = equipment_summary.sort_values('record_count', ascending=False).head(10).index
    
    # 1. 이상치 차트 추가
    if 'temperature_anomalies' in equipment_summary.columns:
        temp_anomalies = equipment_summary.loc[top_equipment, 'temperature_anomalies']
        dashboard.add_trace(
            go.Bar(
                x=temp_anomalies.index,
                y=temp_anomalies.values,
                name='온도 이상치',
                marker_color='red'
            ),
            row=1, col=1
        )
    
    if 'vibration_anomalies' in equipment_summary.columns:
        vib_anomalies = equipment_summary.loc[top_equipment, 'vibration_anomalies']
        dashboard.add_trace(
            go.Bar(
                x=vib_anomalies.index,
                y=vib_anomalies.values,
                name='진동 이상치',
                marker_color='orange'
            ),
            row=1, col=1
        )
    
    # 2. 평균 온도 차트 추가
    if 'avg_temperature' in equipment_summary.columns:
        avg_temp = equipment_summary.loc[top_equipment, 'avg_temperature']
        dashboard.add_trace(
            go.Bar(
                x=avg_temp.index,
                y=avg_temp.values,
                name='평균 온도',
                marker_color='blue',
                text=avg_temp.round(1).values,
                textposition='auto'
            ),
            row=1, col=2
        )
    
    # 3. 평균 전력 소비 추가
    if 'avg_power' in equipment_summary.columns:
        avg_power = equipment_summary.loc[top_equipment, 'avg_power']
        dashboard.add_trace(
            go.Bar(
                x=avg_power.index,
                y=avg_power.values,
                name='평균 전력',
                marker_color='green',
                text=avg_power.round(1).values,
                textposition='auto'
            ),
            row=2, col=1
        )
    
    # 4. 레코드 수 추가
    records = equipment_summary.loc[top_equipment, 'record_count']
    dashboard.add_trace(
        go.Bar(
            x=records.index,
            y=records.values,
            name='레코드 수',
            marker_color='purple',
            text=records.values,
            textposition='auto'
        ),
        row=2, col=2
    )
    
    # 레이아웃 업데이트
    dashboard.update_layout(
        title_text='IoT 센서 데이터 분석 대시보드',
        height=800,
        width=1000,
        showlegend=False,
        font=dict(family=FONT_FAMILY)
    )
    
    # PNG로 저장
    dashboard_path = os.path.join(os.path.dirname(file_path), 'iot_dashboard.png')
    dashboard.write_image(dashboard_path)
    print(f"대시보드가 저장되었습니다: {dashboard_path}")
    
    return dashboard

def demo_parallel_processing():
    """IoT Prism 워크로드를 시뮬레이션한 병렬 처리 데모"""
    print("=" * 60)
    print("IoT Prism 병렬 처리 데모를 시작합니다.")
    print("=" * 60)
    print("이 데모는 IoT Prism의 실제 워크로드를 시뮬레이션합니다:")
    print("- 센서 데이터 로드 (온도, 습도, 압력, 진동, 전압, 전류)")
    print("- 데이터 정제 및 통계 계산")
    print("- 이상치 탐지")
    print("- Plotly를 이용한 데이터 시각화")
    
    try:
        # 1. 테스트 데이터 생성
        print("\n1. 테스트 데이터 생성")
        print("-" * 40)
        df, file_path = create_test_data()
        print(f"테스트 데이터가 생성되었습니다: {file_path}")
        print(f"데이터프레임 형태: {df.shape}")
        
        # 2. 다양한 워커 수로 성능 테스트
        print("\n2. 병렬 처리 성능 테스트")
        print("-" * 40)
        
        # 사용 가능한 CPU 코어 수 확인
        cpu_cores = os.cpu_count()
        print(f"시스템에서 감지된 CPU 코어 수: {cpu_cores}")
        
        # 테스트할 워커 수
        worker_counts = list(range(1, cpu_cores + 1))
        
        results = []
        processing_times = []
        
        for workers in worker_counts:
            print(f"\n워커 {workers}개로 처리 중...")
            start_time = time.time()
            
            try:
                # 병렬 처리 실행
                result = parallel_process_iot_data(file_path, num_workers=workers)
                
                # 결과 저장
                results.append(result)
                elapsed_time = time.time() - start_time
                processing_times.append(elapsed_time)
                
                print(f"처리 완료: {elapsed_time:.2f}초")
                
                # 처리된 데이터 정보 출력
                print(f"처리된 레코드 수: {len(result['processed_data']):,}")
                print(f"생성된 통계: {len(result['agg_stats']):,}개 장비")
                
                # 이상치 통계가 있는 경우 출력
                if 'temperature_is_anomaly' in result['processed_data'].columns:
                    temp_anomalies = result['processed_data']['temperature_is_anomaly'].sum()
                    print(f"이상치 감지: {temp_anomalies:,}개 온도 이상치")
            
            except Exception as e:
                print(f"오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                processing_times.append(None)
        
        # 3. 결과 시각화
        if processing_times and any(t is not None for t in processing_times):
            print("\n3. 성능 결과 시각화")
            print("-" * 40)
            
            # 성능 차트 생성
            fig = go.Figure()
            
            valid_times = []
            valid_labels = []
            
            for i, time_val in enumerate(processing_times):
                if time_val is not None:
                    valid_times.append(time_val)
                    valid_labels.append(f"{worker_counts[i]}개 워커")
            
            fig.add_trace(go.Bar(
                x=valid_labels,
                y=valid_times,
                text=[f"{t:.2f}초" for t in valid_times],
                textposition='outside',
                marker_color='darkblue'
            ))
            
            # 속도 향상 계산 (1개 워커 대비)
            if valid_times and valid_times[0] > 0:
                speedups = [valid_times[0] / t for t in valid_times]
                
                fig.add_trace(go.Scatter(
                    x=valid_labels,
                    y=speedups,
                    mode='lines+markers+text',
                    text=[f"{s:.2f}x" for s in speedups],
                    textposition='top center',
                    yaxis='y2',
                    line=dict(color='red', width=3),
                    marker=dict(size=10),
                    name='속도 향상'
                ))
            
            fig.update_layout(
                title='워커 수에 따른 처리 시간',
                xaxis_title='워커 수',
                yaxis_title='처리 시간 (초)',
                yaxis2=dict(
                    title='속도 향상 (배)',
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                height=600,
                width=800,
                font=dict(family=FONT_FAMILY)
            )
            
            # PNG로 저장
            perf_path = os.path.join(os.path.dirname(file_path), 'performance_comparison.png')
            fig.write_image(perf_path)
            print(f"성능 비교 차트가 저장되었습니다: {perf_path}")
        
        # 4. 데이터 시각화 (가장 빠른 결과로)
        if results:
            print("\n4. 처리된 데이터 시각화")
            print("-" * 40)
            
            # 가장 빠른 결과 선택
            fastest_idx = processing_times.index(min(t for t in processing_times if t is not None))
            fastest_result = results[fastest_idx]
            
            # 데이터 시각화
            dashboard = create_visualization(fastest_result, file_path)
        
        print("\n데모가 완료되었습니다!")
        
    except Exception as e:
        print(f"\n데모 실행 중 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_parallel_processing() 