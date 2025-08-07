"""
DX-AI Manufacturing Copilot - ML 모델링 패키지

실험 데이터를 기반으로 한 머신러닝 모델 훈련 및 예측 모듈입니다.
"""

from .random_forest import RandomForestModel
from .neural_network import NeuralNetworkModel
from .svr_model import SVRModel
from .model_manager import ModelManager

# XGBoost는 optional로 처리
try:
    from .xgboost_model import XGBoostModel
    XGBOOST_AVAILABLE = True
except ImportError as e:
    print(f"XGBoost import failed: {e}")
    XGBoostModel = None
    XGBOOST_AVAILABLE = False
except Exception as e:
    # OpenMP 런타임 오류 등 다른 에러도 catch
    print(f"XGBoost library loading failed: {e}")
    XGBoostModel = None
    XGBOOST_AVAILABLE = False

# CatBoost는 optional로 처리
try:
    from .catboost_model import CatBoostModel
    CATBOOST_AVAILABLE = True
except ImportError as e:
    print(f"CatBoost import failed: {e}")
    CatBoostModel = None
    CATBOOST_AVAILABLE = False
except Exception as e:
    print(f"CatBoost library loading failed: {e}")
    CatBoostModel = None
    CATBOOST_AVAILABLE = False

__all__ = [
    'RandomForestModel',
    'NeuralNetworkModel',
    'SVRModel',
    'ModelManager',
    'XGBOOST_AVAILABLE',
    'CATBOOST_AVAILABLE'
]

if XGBOOST_AVAILABLE:
    __all__.append('XGBoostModel')

if CATBOOST_AVAILABLE:
    __all__.append('CatBoostModel') 