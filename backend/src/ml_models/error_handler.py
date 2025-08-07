"""
ML 라이브러리 Import 에러 핸들러

이 모듈은 XGBoost, CatBoost 등 ML 라이브러리의 import 오류를 
우아하게 처리하고 대안을 제공합니다.
"""

import logging
import warnings
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

# ML 라이브러리 가용성 상태
ML_LIBRARIES_STATUS = {
    'xgboost': False,
    'catboost': False,
    'lightgbm': False,
    'tensorflow': False,
    'torch': False,
    'statsmodels': False
}

# 대체 모델 매핑
FALLBACK_MODELS = {
    'xgboost': 'random_forest',
    'catboost': 'random_forest', 
    'lightgbm': 'random_forest',
    'neural_network': 'svr'
}

def check_ml_library_availability():
    """ML 라이브러리 가용성 확인"""
    global ML_LIBRARIES_STATUS
    
    # XGBoost 확인
    try:
        import xgboost
        ML_LIBRARIES_STATUS['xgboost'] = True
        logger.info("✅ XGBoost 라이브러리 사용 가능")
    except ImportError as e:
        ML_LIBRARIES_STATUS['xgboost'] = False
        logger.warning(f"⚠️ XGBoost 라이브러리를 사용할 수 없습니다: {e}")
    
    # CatBoost 확인
    try:
        import catboost
        ML_LIBRARIES_STATUS['catboost'] = True
        logger.info("✅ CatBoost 라이브러리 사용 가능")
    except ImportError as e:
        ML_LIBRARIES_STATUS['catboost'] = False
        logger.warning(f"⚠️ CatBoost 라이브러리를 사용할 수 없습니다: {e}")
    
    # LightGBM 확인
    try:
        import lightgbm
        ML_LIBRARIES_STATUS['lightgbm'] = True
        logger.info("✅ LightGBM 라이브러리 사용 가능")
    except ImportError as e:
        ML_LIBRARIES_STATUS['lightgbm'] = False
        logger.warning(f"⚠️ LightGBM 라이브러리를 사용할 수 없습니다: {e}")
    
    # TensorFlow 확인
    try:
        import tensorflow
        ML_LIBRARIES_STATUS['tensorflow'] = True
        logger.info("✅ TensorFlow 라이브러리 사용 가능")
    except ImportError as e:
        ML_LIBRARIES_STATUS['tensorflow'] = False
        logger.warning(f"⚠️ TensorFlow 라이브러리를 사용할 수 없습니다: {e}")
    
    # PyTorch 확인
    try:
        import torch
        ML_LIBRARIES_STATUS['torch'] = True
        logger.info("✅ PyTorch 라이브러리 사용 가능")
    except ImportError as e:
        ML_LIBRARIES_STATUS['torch'] = False
        logger.warning(f"⚠️ PyTorch 라이브러리를 사용할 수 없습니다: {e}")
    
    # statsmodels 확인
    try:
        import statsmodels
        ML_LIBRARIES_STATUS['statsmodels'] = True
        logger.info("✅ statsmodels 라이브러리 사용 가능")
    except ImportError as e:
        ML_LIBRARIES_STATUS['statsmodels'] = False
        logger.warning(f"⚠️ statsmodels 라이브러리를 사용할 수 없습니다: {e}")

def safe_import(library_name: str, fallback_message: str = None):
    """안전한 라이브러리 import 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not ML_LIBRARIES_STATUS.get(library_name, False):
                error_msg = fallback_message or f"{library_name} 라이브러리가 사용 불가능합니다."
                logger.error(error_msg)
                
                # 대체 모델 제안
                if library_name in FALLBACK_MODELS:
                    fallback_model = FALLBACK_MODELS[library_name]
                    suggestion = f"대신 {fallback_model} 모델을 사용해보세요."
                    logger.info(suggestion)
                    
                    raise ImportError(f"{error_msg} {suggestion}")
                else:
                    raise ImportError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_available_models() -> Dict[str, bool]:
    """사용 가능한 ML 모델 목록 반환"""
    available_models = {
        'random_forest': True,  # sklearn 기본 모델
        'svr': True,           # sklearn 기본 모델
        'linear_regression': True,  # sklearn 기본 모델
        'xgboost': ML_LIBRARIES_STATUS['xgboost'],
        'catboost': ML_LIBRARIES_STATUS['catboost'],
        'lightgbm': ML_LIBRARIES_STATUS['lightgbm'],
        'neural_network': ML_LIBRARIES_STATUS['tensorflow'] or ML_LIBRARIES_STATUS['torch']
    }
    
    return available_models

def get_recommended_model(preferred_model: str) -> str:
    """선호 모델이 사용 불가능할 때 권장 모델 반환"""
    available_models = get_available_models()
    
    if available_models.get(preferred_model, False):
        return preferred_model
    
    # 대체 모델 제안
    if preferred_model in FALLBACK_MODELS:
        fallback = FALLBACK_MODELS[preferred_model]
        if available_models.get(fallback, False):
            logger.info(f"'{preferred_model}' 대신 '{fallback}' 모델을 사용합니다.")
            return fallback
    
    # 기본값으로 Random Forest 반환
    logger.info(f"'{preferred_model}' 모델을 사용할 수 없어 'random_forest'를 사용합니다.")
    return 'random_forest'

def install_missing_libraries():
    """누락된 라이브러리 설치 안내"""
    missing_libs = []
    install_commands = []
    
    for lib, available in ML_LIBRARIES_STATUS.items():
        if not available:
            missing_libs.append(lib)
    
    if missing_libs:
        logger.warning("⚠️ 다음 ML 라이브러리들이 설치되지 않았습니다:")
        for lib in missing_libs:
            logger.warning(f"   - {lib}")
        
        logger.info("📦 설치 명령어:")
        if 'xgboost' in missing_libs:
            logger.info("   pip install xgboost")
        if 'catboost' in missing_libs:
            logger.info("   pip install catboost")
        if 'lightgbm' in missing_libs:
            logger.info("   pip install lightgbm")
        if 'tensorflow' in missing_libs:
            logger.info("   pip install tensorflow")
        if 'torch' in missing_libs:
            logger.info("   pip install torch")
        if 'statsmodels' in missing_libs:
            logger.info("   pip install statsmodels")
        
        logger.info("   또는 한번에: pip install -r requirements-fix.txt")

def handle_model_prediction_error(model_name: str, error: Exception) -> Dict[str, Any]:
    """모델 예측 오류 처리"""
    logger.error(f"❌ {model_name} 모델 예측 실패: {error}")
    
    # 기본 예측값 반환
    default_predictions = {
        'purity': 95.0,
        'yield': 85.0,
        'total_cost': 100000.0,
        'quality_score': 90.0,
        'error': f"{model_name} 예측 실패, 기본값 사용",
        'warning': f"{model_name} 모델을 사용할 수 없어 기본값을 반환합니다."
    }
    
    return default_predictions

# 초기화
check_ml_library_availability()

# 라이브러리 상태 요약 출력
def print_library_status():
    """ML 라이브러리 상태 요약 출력"""
    logger.info("🔍 ML 라이브러리 상태 요약:")
    for lib, available in ML_LIBRARIES_STATUS.items():
        status = "✅ 사용 가능" if available else "❌ 사용 불가"
        logger.info(f"   {lib}: {status}")
    
    available_count = sum(ML_LIBRARIES_STATUS.values())
    total_count = len(ML_LIBRARIES_STATUS)
    logger.info(f"📊 전체 {total_count}개 중 {available_count}개 라이브러리 사용 가능")

# 모듈 로드 시 상태 출력
print_library_status()

__all__ = [
    'ML_LIBRARIES_STATUS',
    'check_ml_library_availability',
    'safe_import',
    'get_available_models',
    'get_recommended_model',
    'install_missing_libraries',
    'handle_model_prediction_error',
    'print_library_status'
] 