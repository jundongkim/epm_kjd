import os
import time
import pandas as pd
import polars as pl
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
    DATA_DIR
)

# 참고: 스타일 및 폰트 적용은 iot/utils/style.py의 load_iot_font_css(), get_font_path()를 참조하세요.
# Plotly 그래프의 폰트도 동일한 Paperlogy.ttf를 사용합니다.

# 커스텀 폰트 경로
FONT_PATH = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'Paperlogy.ttf')
FONT_FAMILY = 'Paperlogy'

# Plotly에 커스텀 폰트 등록 (로컬 폰트 사용)
pio.templates.default = "plotly_white"

# 실용적인 데이터 샘플 크기 설정
SAMPLE_SIZE = 30000000  # 3000만 레코드 (실행 시간 단축을 위해)

def optimize_dtypes_polars(df):
    """Polars 데이터프레임의 데이터 타입을 최적화하여 메모리 사용량을 줄입니다."""
    # 정수형 컬럼 최적화
    integer_dtypes = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64]
    float_dtypes = [pl.Float32, pl.Float64]
    
    # 각 컬럼의 데이터 타입을 확인하고 최적화
    for col in df.columns:
        col_dtype = df.schema[col]
        
        # 정수형 컬럼 최적화
        if col_dtype in integer_dtypes:
            c_min = df[col].min()
            c_max = df[col].max()
            
            # 부호가 없는 정수로 변환 가능한 경우
            if c_min >= 0:
                if c_max < 255:
                    df = df.with_columns(pl.col(col).cast(pl.UInt8))
                elif c_max < 65535:
                    df = df.with_columns(pl.col(col).cast(pl.UInt16))
                elif c_max < 4294967295:
                    df = df.with_columns(pl.col(col).cast(pl.UInt32))
                else:
                    df = df.with_columns(pl.col(col).cast(pl.UInt64))
            # 부호가 있는 정수로 변환
            else:
                if c_min > -128 and c_max < 127:
                    df = df.with_columns(pl.col(col).cast(pl.Int8))
                elif c_min > -32768 and c_max < 32767:
                    df = df.with_columns(pl.col(col).cast(pl.Int16))
                elif c_min > -2147483648 and c_max < 2147483647:
                    df = df.with_columns(pl.col(col).cast(pl.Int32))
                else:
                    df = df.with_columns(pl.col(col).cast(pl.Int64))
        
        # 부동 소수점 컬럼 최적화
        elif col_dtype in float_dtypes:
            if df[col].min() > np.finfo(np.float32).min and df[col].max() < np.finfo(np.float32).max:
                df = df.with_columns(pl.col(col).cast(pl.Float32))
            else:
                df = df.with_columns(pl.col(col).cast(pl.Float64))
    
    # 범주형 데이터 최적화 (고유 값이 전체 데이터의 50% 미만인 경우)
    for col in df.columns:
        if df.schema[col] == pl.Utf8:
            # 결측값이 아닌 값 중 고유 값 수
            num_unique = df[col].n_unique()
            # 결측값이 아닌 값의 개수
            num_total = df.filter(~pl.col(col).is_null()).height
            # 고유 값 비율
            if num_total > 0 and num_unique / num_total < 0.5:
                df = df.with_columns(pl.col(col).cast(pl.Categorical))
    
    return df

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

# IoT Prism의 일반적인 분석 작업을 시뮬레이션하는 함수 (Polars 버전)
def process_iot_data_polars(df_pl):
    """IoT 데이터 처리 및 분석 함수 (Polars 버전)"""
    # 1. 데이터 정제
    print("데이터 정제 중...")
    # 결측값 처리 - Polars에서의 forward fill과 backward fill
    df_pl = df_pl.fill_null(strategy="forward").fill_null(strategy="backward")
    
    # 2. 시간 기반 특성 추출
    print("시간 기반 특성 추출 중...")
    df_pl = df_pl.with_columns([
        pl.col("timestamp").dt.hour().alias("hour"),
        pl.col("timestamp").dt.day().alias("day"),
        pl.col("timestamp").dt.weekday().alias("day_of_week")
    ])
    
    # 3. 집계 통계 계산 (그룹별)
    print("집계 통계 계산 중...")
    agg_stats = df_pl.group_by("equipment_id").agg([
        pl.col("temperature").mean().alias("temperature_mean"),
        pl.col("temperature").min().alias("temperature_min"),
        pl.col("temperature").max().alias("temperature_max"),
        pl.col("temperature").std().alias("temperature_std"),
        pl.col("humidity").mean().alias("humidity_mean"),
        pl.col("humidity").min().alias("humidity_min"),
        pl.col("humidity").max().alias("humidity_max"),
        pl.col("humidity").std().alias("humidity_std"),
        pl.col("pressure").mean().alias("pressure_mean"),
        pl.col("pressure").min().alias("pressure_min"),
        pl.col("pressure").max().alias("pressure_max"),
        pl.col("vibration").mean().alias("vibration_mean"),
        pl.col("vibration").max().alias("vibration_max"),
        pl.col("power").mean().alias("power_mean"),
        pl.col("power").max().alias("power_max"),
        pl.col("power").min().alias("power_min")
    ])
    
    # 4. 시간대별 집계
    hourly_stats = df_pl.group_by(["equipment_id", "hour"]).agg([
        pl.col("temperature").mean().alias("temperature_mean"),
        pl.col("humidity").mean().alias("humidity_mean"),
        pl.col("power").mean().alias("power_mean")
    ])
    
    # 5. 이상치 탐지
    print("이상치 탐지 중...")
    # Z-점수 기반 이상치 탐지
    for col in ["temperature", "humidity", "vibration", "power"]:
        mean_val = df_pl[col].mean()
        std_val = df_pl[col].std()
        df_pl = df_pl.with_columns([
            ((pl.col(col) - mean_val) / std_val).alias(f"{col}_zscore"),
            (((pl.col(col) - mean_val) / std_val).abs() > 3).alias(f"{col}_is_anomaly")
        ])
    
    # 6. 이동 평균 계산
    print("이동 평균 계산 중...")
    for col in ["temperature", "humidity", "pressure", "power"]:
        df_pl = df_pl.with_columns([
            pl.col(col).rolling_mean(window_size=10, min_periods=1).alias(f"{col}_ma_10")
        ])
    
    # 7. 장비별 요약 정보
    equipment_summary = df_pl.group_by("equipment_id").agg([
        pl.count().alias("record_count"),
        pl.col("temperature_is_anomaly").sum().alias("temp_anomalies"),
        pl.col("vibration_is_anomaly").sum().alias("vibration_anomalies"),
        pl.col("power").mean().alias("avg_power"),
        pl.col("temperature").max().alias("max_temp"),
        pl.col("temperature").min().alias("min_temp")
    ])
    
    return {
        'processed_data': df_pl,
        'agg_stats': agg_stats,
        'hourly_stats': hourly_stats,
        'equipment_summary': equipment_summary
    }

# 청크 단위로 처리하는 함수 (병렬 처리용, Polars 버전)
def process_chunk_polars(chunk_data):
    """데이터 청크 처리 함수 (Polars 버전)"""
    # Pandas 청크를 Polars 데이터프레임으로 변환
    chunk = pl.from_pandas(chunk_data)
    
    # 타입이 문자열인 경우 날짜로 변환
    if 'timestamp' in chunk.columns and chunk.schema['timestamp'] == pl.Utf8:
        chunk = chunk.with_columns(pl.col('timestamp').str.strptime(pl.Datetime, format=None))
    
    # 데이터 타입 최적화
    chunk = optimize_dtypes_polars(chunk)
    
    # 결측값 처리 (전진 채우기, 후진 채우기)
    chunk = chunk.fill_null(strategy="forward").fill_null(strategy="backward")
    
    # 파생 변수 계산 (필요한 경우)
    if 'power' not in chunk.columns and 'voltage' in chunk.columns and 'current' in chunk.columns:
        chunk = chunk.with_columns((pl.col('voltage') * pl.col('current')).alias('power'))
    
    # 시간 기반 특성 추출
    if 'timestamp' in chunk.columns:
        chunk = chunk.with_columns([
            pl.col('timestamp').dt.hour().alias('hour'),
            pl.col('timestamp').dt.day().alias('day'),
            pl.col('timestamp').dt.weekday().alias('day_of_week')
        ])
    
    # 통계 계산
    for col in ['temperature', 'humidity', 'pressure', 'vibration', 'power']:
        if col in chunk.columns:
            # 이동 평균
            chunk = chunk.with_columns([
                pl.col(col).rolling_mean(window_size=10, min_periods=1).alias(f'{col}_ma_10')
            ])
            
            # Z-점수 계산
            mean = chunk[col].mean()
            std = chunk[col].std()
            if std > 0:  # 0으로 나누기 방지
                chunk = chunk.with_columns([
                    ((pl.col(col) - mean) / std).alias(f'{col}_zscore'),
                    (((pl.col(col) - mean) / std).abs() > 3).alias(f'{col}_is_anomaly')
                ])
            else:
                chunk = chunk.with_columns([
                    pl.lit(0).alias(f'{col}_zscore'),
                    pl.lit(False).alias(f'{col}_is_anomaly')
                ])
    
    # 처리된 Polars 데이터프레임을 Pandas로 변환하여 반환 (호환성을 위해)
    return chunk.to_pandas()

# 병렬 처리 함수 (Polars 버전)
def parallel_process_iot_data_polars(file_path, num_workers):
    """CSV 파일을 청크 단위로 병렬 처리 (Polars 버전)"""
    # CSV 파일 크기 확인
    file_size = os.path.getsize(file_path)
    
    # 레코드 수 예측을 위한 샘플링 (Pandas 사용)
    sample = pd.read_csv(file_path, nrows=1000)
    avg_row_size = file_size / len(sample) if len(sample) > 0 else 1000
    estimated_rows = int(file_size / avg_row_size)
    
    # 청크 크기 계산
    chunk_size = max(1000, estimated_rows // num_workers)
    print(f"예상 레코드 수: {estimated_rows:,}, 청크 크기: {chunk_size:,}, 워커 수: {num_workers}")
    
    # 청크 단위로 데이터 읽기 및 처리 (Pandas를 사용하여 청크 읽기)
    chunks = pd.read_csv(file_path, chunksize=chunk_size, parse_dates=['timestamp'])
    
    # 병렬 처리
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_chunk_polars, chunks))
    
    # 결과 합치기 (Pandas 데이터프레임)
    processed_df_pd = pd.concat(results)
    
    # Polars로 변환
    processed_df = pl.from_pandas(processed_df_pd)
    
    # 집계 통계 계산
    # 사용 가능한 컬럼 확인
    col_stats = {
        'temperature': ['mean', 'min', 'max', 'std'],
        'humidity': ['mean', 'min', 'max', 'std'],
        'pressure': ['mean', 'min', 'max']
    }
    
    # 집계 계산을 위한 표현식
    agg_expressions = []
    for col, funcs in col_stats.items():
        if col in processed_df.columns:
            for func in funcs:
                if func == 'mean':
                    agg_expressions.append(pl.col(col).mean().alias(f"{col}_mean"))
                elif func == 'min':
                    agg_expressions.append(pl.col(col).min().alias(f"{col}_min"))
                elif func == 'max':
                    agg_expressions.append(pl.col(col).max().alias(f"{col}_max"))
                elif func == 'std':
                    agg_expressions.append(pl.col(col).std().alias(f"{col}_std"))
    
    # 전력, 진동 컬럼이 있는 경우 추가
    if 'power' in processed_df.columns:
        agg_expressions.extend([
            pl.col('power').mean().alias("power_mean"),
            pl.col('power').max().alias("power_max"),
            pl.col('power').min().alias("power_min")
        ])
    if 'vibration' in processed_df.columns:
        agg_expressions.extend([
            pl.col('vibration').mean().alias("vibration_mean"),
            pl.col('vibration').max().alias("vibration_max")
        ])
    
    # 집계 통계 계산
    agg_stats = processed_df.group_by('equipment_id').agg(agg_expressions)
    
    # 장비별 요약 정보 계산
    summary_expressions = [pl.count().alias("record_count")]
    
    # 이상치 통계 (있는 경우만)
    for col in ['temperature', 'vibration', 'power']:
        anomaly_col = f'{col}_is_anomaly'
        if anomaly_col in processed_df.columns:
            summary_expressions.append(pl.col(anomaly_col).sum().alias(f"{col}_anomalies"))
    
    # 평균값 통계
    for col in ['temperature', 'humidity', 'pressure', 'power']:
        if col in processed_df.columns:
            summary_expressions.append(pl.col(col).mean().alias(f"avg_{col}"))
            
            # 최대/최소 온도는 특별히 중요
            if col == 'temperature':
                summary_expressions.append(pl.col(col).max().alias(f"max_{col}"))
                summary_expressions.append(pl.col(col).min().alias(f"min_{col}"))
    
    equipment_summary = processed_df.group_by('equipment_id').agg(summary_expressions)
    
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
    
    # Polars DataFrame을 Pandas로 변환 (plotly와의 호환성을 위해)
    if isinstance(equipment_summary, pl.DataFrame):
        equipment_summary = equipment_summary.to_pandas()
    
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
    dashboard_path = os.path.join(os.path.dirname(file_path), 'iot_dashboard_polars.png')
    dashboard.write_image(dashboard_path)
    print(f"대시보드가 저장되었습니다: {dashboard_path}")
    
    return dashboard

def demo_parallel_processing_polars():
    """IoT Prism 워크로드를 시뮬레이션한 병렬 처리 데모 (Polars 버전)"""
    print("=" * 60)
    print("IoT Prism 병렬 처리 데모를 시작합니다 (Polars 버전).")
    print("=" * 60)
    print("이 데모는 IoT Prism의 실제 워크로드를 시뮬레이션합니다:")
    print("- 센서 데이터 로드 (온도, 습도, 압력, 진동, 전압, 전류)")
    print("- Polars를 이용한 데이터 정제 및 통계 계산")
    print("- 이상치 탐지")
    print("- Plotly를 이용한 데이터 시각화")
    print("- Pandas와 Polars의 성능 비교")
    
    try:
        # 1. 테스트 데이터 생성
        print("\n1. 테스트 데이터 생성")
        print("-" * 40)
        df, file_path = create_test_data()
        print(f"테스트 데이터가 생성되었습니다: {file_path}")
        print(f"데이터프레임 형태: {df.shape}")
        
        # 2. Pandas와 Polars의 성능 비교
        print("\n2. Pandas vs. Polars 성능 테스트")
        print("-" * 40)
        
        # 사용 가능한 CPU 코어 수 확인
        cpu_cores = os.cpu_count()
        print(f"시스템에서 감지된 CPU 코어 수: {cpu_cores}")
        
        # 테스트할 워커 수
        worker_counts = list(range(1, cpu_cores + 1, max(1, cpu_cores // 4)))
        # 마지막 코어 수 추가
        if worker_counts[-1] != cpu_cores:
            worker_counts.append(cpu_cores)
        
        pandas_results = []
        polars_results = []
        pandas_times = []
        polars_times = []
        
        # Pandas 테스트
        print("\n[Pandas 테스트]")
        for workers in worker_counts:
            print(f"\nPandas: 워커 {workers}개로 처리 중...")
            
            # Pandas 함수 임포트 (원래 파일에서)
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from parallel_processing_example import parallel_process_iot_data
            
            start_time = time.time()
            
            try:
                # Pandas 병렬 처리 실행
                result = parallel_process_iot_data(file_path, num_workers=workers)
                
                # 결과 저장
                pandas_results.append(result)
                elapsed_time = time.time() - start_time
                pandas_times.append(elapsed_time)
                
                print(f"Pandas 처리 완료: {elapsed_time:.2f}초")
                print(f"처리된 레코드 수: {len(result['processed_data']):,}")
            
            except Exception as e:
                print(f"Pandas 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                pandas_times.append(None)
        
        # Polars 테스트
        print("\n[Polars 테스트]")
        for workers in worker_counts:
            print(f"\nPolars: 워커 {workers}개로 처리 중...")
            start_time = time.time()
            
            try:
                # Polars 병렬 처리 실행
                result = parallel_process_iot_data_polars(file_path, num_workers=workers)
                
                # 결과 저장
                polars_results.append(result)
                elapsed_time = time.time() - start_time
                polars_times.append(elapsed_time)
                
                print(f"Polars 처리 완료: {elapsed_time:.2f}초")
                
                # 처리된 데이터 정보 출력
                print(f"처리된 레코드 수: {result['processed_data'].height:,}")
                print(f"생성된 통계: {result['agg_stats'].height:,}개 장비")
                
                # 이상치 통계가 있는 경우 출력
                if 'temperature_is_anomaly' in result['processed_data'].columns:
                    temp_anomalies = result['processed_data'].select(pl.col('temperature_is_anomaly').sum())[0, 0]
                    print(f"이상치 감지: {temp_anomalies:,}개 온도 이상치")
            
            except Exception as e:
                print(f"Polars 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                polars_times.append(None)
        
        # 3. 결과 시각화
        if pandas_times and polars_times:
            print("\n3. 성능 비교 시각화")
            print("-" * 40)
            
            # 유효한 결과만 가져오기
            valid_worker_counts = []
            valid_pandas_times = []
            valid_polars_times = []
            
            for i in range(len(worker_counts)):
                if pandas_times[i] is not None and polars_times[i] is not None:
                    valid_worker_counts.append(worker_counts[i])
                    valid_pandas_times.append(pandas_times[i])
                    valid_polars_times.append(polars_times[i])
            
            # 성능 비교 차트 생성
            fig = go.Figure()
            
            # Pandas 처리 시간
            fig.add_trace(go.Bar(
                x=[f"{w}개 워커" for w in valid_worker_counts],
                y=valid_pandas_times,
                name='Pandas',
                text=[f"{t:.2f}초" for t in valid_pandas_times],
                textposition='outside',
                marker_color='blue'
            ))
            
            # Polars 처리 시간
            fig.add_trace(go.Bar(
                x=[f"{w}개 워커" for w in valid_worker_counts],
                y=valid_polars_times,
                name='Polars',
                text=[f"{t:.2f}초" for t in valid_polars_times],
                textposition='outside',
                marker_color='green'
            ))
            
            # 속도 향상 비율 계산 (Pandas 대비 Polars)
            speedup_ratios = [pandas_times[i] / polars_times[i] for i in range(len(valid_worker_counts))]
            
            fig.add_trace(go.Scatter(
                x=[f"{w}개 워커" for w in valid_worker_counts],
                y=speedup_ratios,
                mode='lines+markers+text',
                text=[f"{s:.2f}x" for s in speedup_ratios],
                textposition='top center',
                yaxis='y2',
                line=dict(color='red', width=3),
                marker=dict(size=10),
                name='Polars 속도 향상'
            ))
            
            fig.update_layout(
                title='Pandas vs. Polars: 워커 수에 따른 처리 시간 비교',
                xaxis_title='워커 수',
                yaxis_title='처리 시간 (초)',
                yaxis2=dict(
                    title='속도 향상 (배)',
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                height=600,
                width=1000,
                legend=dict(x=0.01, y=0.99),
                barmode='group',
                font=dict(family=FONT_FAMILY)
            )
            
            # PNG로 저장
            comparison_path = os.path.join(os.path.dirname(file_path), 'pandas_vs_polars_comparison.png')
            fig.write_image(comparison_path)
            print(f"성능 비교 차트가 저장되었습니다: {comparison_path}")
            
            # 성능 비교 요약
            if valid_polars_times and valid_pandas_times:
                pandas_avg = sum(valid_pandas_times) / len(valid_pandas_times)
                polars_avg = sum(valid_polars_times) / len(valid_polars_times)
                avg_speedup = pandas_avg / polars_avg
                
                max_speedup_idx = speedup_ratios.index(max(speedup_ratios))
                max_speedup = speedup_ratios[max_speedup_idx]
                max_speedup_workers = valid_worker_counts[max_speedup_idx]
                
                print(f"\n성능 비교 요약:")
                print(f"- Pandas 평균 처리 시간: {pandas_avg:.2f}초")
                print(f"- Polars 평균 처리 시간: {polars_avg:.2f}초")
                print(f"- 평균 속도 향상: {avg_speedup:.2f}x")
                print(f"- 최대 속도 향상: {max_speedup:.2f}x ({max_speedup_workers}개 워커)")
        
        # 4. 데이터 시각화 (가장 빠른 Polars 결과로)
        if polars_results:
            print("\n4. 처리된 데이터 시각화")
            print("-" * 40)
            
            # 가장 빠른 결과 선택
            if any(t is not None for t in polars_times):
                fastest_idx = [i for i, t in enumerate(polars_times) if t is not None].index(
                    min([i for i, t in enumerate(polars_times) if t is not None], 
                        key=lambda i: polars_times[i])
                )
                fastest_result = polars_results[fastest_idx]
                
                # 데이터 시각화
                dashboard = create_visualization(fastest_result, file_path)
        
        print("\n데모가 완료되었습니다!")
        
    except Exception as e:
        print(f"\n데모 실행 중 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_parallel_processing_polars() 