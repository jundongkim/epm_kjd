"""
ML 모델링을 위한 공통 유틸리티 함수들
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import json
from datetime import datetime
from typing import Dict, Tuple, Any, Optional
import warnings


def is_date_like(series: pd.Series) -> bool:
    """
    시리즈가 날짜 형식인지 확인
    
    Args:
        series: 확인할 시리즈
        
    Returns:
        날짜 형식 여부
    """
    # 모든 타입에 대해 날짜 형식 확인
    sample_size = min(10, len(series))
    sample_values = series.dropna().head(sample_size)
    
    if len(sample_values) == 0:
        return False
    
    date_count = 0
    for value in sample_values:
        # 문자열 타입이거나 object 타입인 경우
        if isinstance(value, (str, object)):
            try:
                # 일반적인 날짜 형식 확인
                pd.to_datetime(str(value), errors='raise')
                date_count += 1
            except (ValueError, TypeError):
                # 날짜가 아닌 경우, 숫자로 변환 가능한지 확인
                try:
                    float(str(value))
                except (ValueError, TypeError):
                    # 숫자도 날짜도 아닌 경우
                    continue
    
    # 30% 이상이 날짜 형식이면 날짜 컬럼으로 판단 (더 엄격하게)
    return date_count / len(sample_values) >= 0.3 if len(sample_values) > 0 else False


def can_convert_to_numeric(series: pd.Series) -> bool:
    """
    시리즈의 모든 값이 숫자로 변환 가능한지 확인
    
    Args:
        series: 확인할 시리즈
        
    Returns:
        숫자 변환 가능 여부
    """
    try:
        # 결측치 제거
        non_null_values = series.dropna()
        
        if len(non_null_values) == 0:
            return False
        
        # 모든 값을 숫자로 변환 시도
        for value in non_null_values:
            if pd.isna(value):
                continue
            try:
                float(str(value))
            except (ValueError, TypeError):
                return False
        
        return True
    except:
        return False


def preprocess_data(df: pd.DataFrame, target_col: str, test_size: float = 0.2, 
                   random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    데이터 전처리 및 train/test 분할
    
    Args:
        df: 입력 데이터프레임
        target_col: 타겟 변수 컬럼명
        test_size: 테스트 데이터 비율
        random_state: 랜덤 시드
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    # 입력 데이터 복사
    df_copy = df.copy()
    
    # Streamlit 사용 시 정보 출력
    try:
        import streamlit as st
        st.write(f"📊 원본 데이터 형태: {df_copy.shape}")
        st.write(f"📊 컬럼 타입: {df_copy.dtypes.to_dict()}")
        use_streamlit = True
    except:
        print(f"📊 원본 데이터 형태: {df_copy.shape}")
        print(f"📊 컬럼 타입: {df_copy.dtypes.to_dict()}")
        use_streamlit = False
    
    # 타겟 변수 분리
    if target_col not in df_copy.columns:
        raise ValueError(f"타겟 변수 '{target_col}'이 데이터에 없습니다.")
    
    y = df_copy[target_col]
    X = df_copy.drop(columns=[target_col])
    
    # 타겟 변수가 날짜 형식인지 확인
    if is_date_like(y):
        raise ValueError(f"타겟 변수 '{target_col}'이 날짜 형식입니다. 수치형 타겟 변수를 선택해주세요.")
    
    # 타겟 변수가 숫자로 변환 가능한지 확인
    if not can_convert_to_numeric(y):
        raise ValueError(f"타겟 변수 '{target_col}'을 숫자로 변환할 수 없습니다.")
    
    # 모든 컬럼에 대해 엄격한 필터링 수행
    removed_columns = []
    valid_columns = []
    
    for col in X.columns:
        # 1. 날짜 형식 확인
        if is_date_like(X[col]):
            removed_columns.append(f"{col} (날짜 형식)")
            continue
        
        # 2. 숫자 변환 가능성 확인
        if not can_convert_to_numeric(X[col]):
            removed_columns.append(f"{col} (숫자 변환 불가)")
            continue
        
        # 3. 실제 숫자 변환 테스트
        try:
            pd.to_numeric(X[col], errors='raise')
            valid_columns.append(col)
        except (ValueError, TypeError) as e:
            removed_columns.append(f"{col} (변환 오류: {str(e)[:50]})")
            continue
    
    if removed_columns:
        if use_streamlit:
            st.warning(f"❌ 제거된 컬럼들: {removed_columns}")
        else:
            print(f"❌ 제거된 컬럼들: {removed_columns}")
    
    if len(valid_columns) == 0:
        error_msg = "수치형 피처가 없습니다. 데이터를 확인해주세요."
        if use_streamlit:
            st.error(error_msg)
        raise ValueError(error_msg)
    
    # 유효한 컬럼만 선택
    X = X[valid_columns]
    
    if use_streamlit:
        st.success(f"✅ 유효한 피처 컬럼: {valid_columns}")
    else:
        print(f"✅ 유효한 피처 컬럼: {valid_columns}")
    
    # 강제 숫자 변환 (안전장치)
    for col in X.columns:
        try:
            X[col] = pd.to_numeric(X[col], errors='coerce')
        except:
            pass
    
    # 결측치 처리
    X = X.fillna(X.mean())
    
    # 최종 검증
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            raise ValueError(f"컬럼 '{col}'이 여전히 숫자형이 아닙니다.")
    
    if use_streamlit:
        st.info(f"📊 최종 데이터 형태: X={X.shape}, y={y.shape}")
    else:
        print(f"📊 최종 데이터 형태: X={X.shape}, y={y.shape}")
    
    # Train/Test 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    return X_train, X_test, y_train, y_test


def scale_features(X_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Any]:
    """
    피처 스케일링 (표준화)
    
    Args:
        X_train: 훈련 데이터
        X_test: 테스트 데이터
        
    Returns:
        X_train_scaled, X_test_scaled, scaler
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, scaler


def calculate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    회귀 모델 성능 지표 계산
    
    Args:
        y_true: 실제값
        y_pred: 예측값
        
    Returns:
        성능 지표 딕셔너리
    """
    return {
        'r2_score': r2_score(y_true, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
        'mae': mean_absolute_error(y_true, y_pred),
        'mse': mean_squared_error(y_true, y_pred)
    }


def calculate_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """
    분류 모델 성능 지표 계산
    
    Args:
        y_true: 실제값
        y_pred: 예측값
        
    Returns:
        성능 지표 딕셔너리
    """
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'classification_report': classification_report(y_true, y_pred, output_dict=True),
        'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
    }


def save_model(model: Any, model_name: str, model_type: str, 
               metrics: Dict[str, float], feature_names: list = None) -> str:
    """
    모델 저장
    
    Args:
        model: 훈련된 모델
        model_name: 모델명
        model_type: 모델 타입
        metrics: 성능 지표
        feature_names: 피처명 리스트
        
    Returns:
        저장된 모델 파일 경로
    """
    # 모델 저장 디렉토리 생성
    model_dir = os.path.join("data", "models", model_type)
    os.makedirs(model_dir, exist_ok=True)
    
    # 타임스탬프 추가
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_filename = f"{model_name}_{timestamp}.pkl"
    model_path = os.path.join(model_dir, model_filename)
    
    # 모델 저장
    joblib.dump(model, model_path)
    
    # 메타데이터 저장
    metadata = {
        'model_name': model_name,
        'model_type': model_type,
        'timestamp': timestamp,
        'metrics': metrics,
        'feature_names': feature_names,
        'model_file': model_filename
    }
    
    metadata_path = os.path.join(model_dir, f"{model_name}_{timestamp}_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return model_path


def load_model(model_path: str) -> Any:
    """
    모델 로드
    
    Args:
        model_path: 모델 파일 경로
        
    Returns:
        로드된 모델
    """
    return joblib.load(model_path)


def load_model_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    모델 메타데이터 로드
    
    Args:
        metadata_path: 메타데이터 파일 경로
        
    Returns:
        메타데이터 딕셔너리
    """
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_available_models(model_type: str = None) -> list:
    """
    사용 가능한 모델 목록 반환
    
    Args:
        model_type: 모델 타입 (옵션)
        
    Returns:
        모델 정보 리스트
    """
    models_dir = os.path.join("data", "models")
    available_models = []
    
    if not os.path.exists(models_dir):
        return available_models
    
    # 모델 타입별 검색
    if model_type:
        search_dirs = [os.path.join(models_dir, model_type)]
    else:
        search_dirs = [os.path.join(models_dir, d) for d in os.listdir(models_dir) 
                      if os.path.isdir(os.path.join(models_dir, d))]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for file in os.listdir(search_dir):
                if file.endswith('_metadata.json'):
                    metadata_path = os.path.join(search_dir, file)
                    try:
                        metadata = load_model_metadata(metadata_path)
                        model_path = os.path.join(search_dir, metadata['model_file'])
                        if os.path.exists(model_path):
                            available_models.append({
                                'model_path': model_path,
                                'metadata_path': metadata_path,
                                'metadata': metadata
                            })
                    except Exception as e:
                        print(f"Error loading metadata from {metadata_path}: {e}")
    
    # 타임스탬프 기준 정렬 (최신 순)
    available_models.sort(key=lambda x: x['metadata']['timestamp'], reverse=True)
    
    return available_models


def validate_data(df: pd.DataFrame, required_columns: list) -> Dict[str, Any]:
    """
    데이터 유효성 검증
    
    Args:
        df: 검증할 데이터프레임
        required_columns: 필수 컬럼 리스트
        
    Returns:
        검증 결과 딕셔너리
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }
    
    # 필수 컬럼 확인
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"필수 컬럼 누락: {missing_columns}")
    
    # 데이터 타입 확인
    for col in df.columns:
        if col in required_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                validation_result['warnings'].append(f"비수치형 컬럼: {col}")
    
    # 결측치 확인
    missing_data = df.isnull().sum()
    if missing_data.sum() > 0:
        validation_result['warnings'].append(f"결측치 발견: {missing_data.sum()}개")
    
    # 데이터 크기 확인
    if len(df) < 10:
        validation_result['is_valid'] = False
        validation_result['errors'].append("데이터가 너무 적습니다 (최소 10개 행 필요)")
    
    return validation_result 


def get_model_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    모델 메타데이터 가져오기 (load_model_metadata의 별명)
    
    Args:
        metadata_path: 메타데이터 파일 경로
        
    Returns:
        메타데이터 딕셔너리
    """
    return load_model_metadata(metadata_path) 