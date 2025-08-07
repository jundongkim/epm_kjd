import os
import pandas as pd
import numpy as np
import concurrent.futures
import tempfile

def optimize_dtypes(df):
    """데이터프레임의 데이터 타입을 최적화하여 메모리 사용량을 줄입니다."""
    # 정수형 컬럼 최적화
    for col in df.select_dtypes(include=['int']).columns:
        # 최소값과 최대값 확인
        c_min = df[col].min()
        c_max = df[col].max()
        
        # 부호가 없는 정수로 변환 가능한 경우
        if c_min >= 0:
            if c_max < 255:
                df[col] = df[col].astype(np.uint8)
            elif c_max < 65535:
                df[col] = df[col].astype(np.uint16)
            elif c_max < 4294967295:
                df[col] = df[col].astype(np.uint32)
            else:
                df[col] = df[col].astype(np.uint64)
        # 부호가 있는 정수로 변환
        else:
            if c_min > -128 and c_max < 127:
                df[col] = df[col].astype(np.int8)
            elif c_min > -32768 and c_max < 32767:
                df[col] = df[col].astype(np.int16)
            elif c_min > -2147483648 and c_max < 2147483647:
                df[col] = df[col].astype(np.int32)
            else:
                df[col] = df[col].astype(np.int64)
    
    # 부동 소수점 컬럼 최적화
    for col in df.select_dtypes(include=['float']).columns:
        # 값의 범위를 확인하여 필요한 정밀도 결정
        if df[col].min() > np.finfo(np.float32).min and df[col].max() < np.finfo(np.float32).max:
            df[col] = df[col].astype(np.float32)
        else:
            df[col] = df[col].astype(np.float64)
    
    # 범주형 데이터 최적화 (고유 값이 전체 데이터의 50% 미만인 경우)
    for col in df.select_dtypes(include=['object']).columns:
        # 결측값이 아닌 값 중 고유 값 수
        num_unique = df[col].nunique()
        # 결측값이 아닌 값의 개수
        num_total = df[col].count()
        # 고유 값 비율
        if num_total > 0 and num_unique / num_total < 0.5:
            df[col] = df[col].astype('category')
    
    return df

def process_chunk(chunk):
    """청크 처리 함수"""
    # 데이터 타입 최적화
    return optimize_dtypes(chunk)

def parallel_process_file(file_path, num_workers=None):
    """파일을 Pandas 청크로 나누어 병렬 처리"""
    if num_workers is None:
        # 자동 CPU 코어 수 감지
        num_workers = os.cpu_count()
    
    # 파일 크기 확인
    file_size = os.path.getsize(file_path)
    
    # 전체 행 수 추정 (첫 1000행 샘플로 평균 행 크기 계산)
    sample = pd.read_csv(file_path, nrows=1000)
    avg_row_size = len(sample) / sample.memory_usage(deep=True).sum()
    estimated_rows = int(file_size * avg_row_size)
    
    # 청크 크기 계산 (전체 행 수를 워커 수로 나눔)
    chunk_size = max(1000, estimated_rows // num_workers)
    
    print(f"예상 행 수: {estimated_rows:,}, 청크 크기: {chunk_size:,}")
    
    # 청크별로 CSV 파일 읽기
    chunks = pd.read_csv(file_path, chunksize=chunk_size)
    
    # ThreadPoolExecutor 사용 (I/O 작업이 많은 경우 더 효율적)
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # 각 청크를 병렬로 처리
        results = list(executor.map(process_chunk, chunks))
    
    # 결과 합치기
    if not results:
        return pd.DataFrame()
    
    return pd.concat(results) 