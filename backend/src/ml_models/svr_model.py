"""
SVR (Support Vector Regression) 모델 구현
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.svm import SVR, SVC
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

from .utils import (
    preprocess_data, 
    scale_features,
    calculate_regression_metrics,
    calculate_classification_metrics,
    save_model,
    load_model,
    validate_data
)


class SVRModel:
    """SVR 모델 클래스"""
    
    def __init__(self, task_type: str = 'regression'):
        """
        Args:
            task_type: 'regression' 또는 'classification'
        """
        self.task_type = task_type
        self.model = None
        self.scaler = None
        self.metrics = {}
        self.feature_names = []
        self.target_name = ""
        
    def _safe_to_list(self, data):
        """안전하게 데이터를 리스트로 변환"""
        if data is None:
            return []
        elif isinstance(data, list):
            return data
        elif hasattr(data, 'tolist'):
            try:
                return data.tolist()
            except (AttributeError, TypeError):
                return list(data) if hasattr(data, '__iter__') else [data]
        elif hasattr(data, '__iter__') and not isinstance(data, (str, bytes)):
            return list(data)
        else:
            return [data]

    def train_model(self, df: pd.DataFrame, target_col: str, 
                   test_size: float = 0.2, random_state: int = 42,
                   hyperparameter_tuning: bool = False, show_progress: bool = True) -> Dict[str, Any]:
        """
        모델 훈련
        
        Args:
            df: 데이터프레임
            target_col: 타겟 컬럼명
            test_size: 테스트 데이터 비율
            random_state: 랜덤 시드
            hyperparameter_tuning: 하이퍼파라미터 튜닝 여부
            show_progress: 진행상황 표시 여부
            
        Returns:
            훈련 결과 딕셔너리
        """
        return self.train(df, target_col, test_size=test_size, random_state=random_state, 
                         hyperparameter_tuning=hyperparameter_tuning, show_progress=show_progress)
    
    def train(self, df: pd.DataFrame, target_col: str, 
               kernel: str = 'rbf', C: float = 1.0, epsilon: float = 0.1,
               gamma: str = 'scale', test_size: float = 0.2, 
               random_state: int = 42, hyperparameter_tuning: bool = False, 
               show_progress: bool = True, callback=None) -> Dict[str, Any]:
        """
        SVR 모델 훈련 (콜백 지원)
        
        Args:
            df: 훈련 데이터
            target_col: 타겟 변수명
            kernel: 커널 함수
            C: 정규화 파라미터
            epsilon: 엡실론 파라미터
            gamma: 커널 계수
            test_size: 테스트 데이터 비율
            random_state: 랜덤 시드
            callback: 훈련 진행 상황 콜백
            
        Returns:
            훈련 결과 딕셔너리
        """
        # 데이터 전처리
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        self.feature_names = X.columns.tolist()
        self.target_name = target_col
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # 데이터 스케일링 (SVR은 스케일링이 중요)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 모델 초기화
        if self.task_type == 'regression':
            self.model = SVR(
                kernel=kernel,
                C=C,
                epsilon=epsilon,
                gamma=gamma
            )
        else:
            self.model = SVC(
                kernel=kernel,
                C=C,
                gamma=gamma,
                random_state=random_state
            )
        
        # 콜백 시뮬레이션 (SVR은 반복 학습이 아니므로 단계별 시뮬레이션)
        if callback:
            # SVR 훈련 과정 시뮬레이션 (5단계)
            for step in range(1, 6):
                # 부분 데이터로 훈련 시뮬레이션
                partial_size = int(len(X_train_scaled) * step / 5)
                if partial_size < 10:
                    partial_size = len(X_train_scaled)
                
                # 임시 모델로 부분 훈련
                temp_model = type(self.model)(**self.model.get_params())
                temp_model.fit(X_train_scaled[:partial_size], y_train[:partial_size])
                
                # 메트릭 계산
                try:
                    y_pred_train = temp_model.predict(X_train_scaled[:partial_size])
                    y_pred_test = temp_model.predict(X_test_scaled)
                    
                    train_rmse = np.sqrt(mean_squared_error(y_train[:partial_size], y_pred_train))
                    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                    
                    metrics = {
                        'training_samples': partial_size,
                        'train_rmse': train_rmse,
                        'test_rmse': test_rmse
                    }
                except:
                    metrics = {'training_samples': partial_size}
                
                callback.on_iteration_end(step, metrics)
                
                # 마지막 단계에서는 실제 모델 저장
                if step == 5:
                    self.model = temp_model
        else:
            # 일반 훈련
            self.model.fit(X_train_scaled, y_train)
        
        # 예측
        y_pred = self.model.predict(X_test_scaled)
        
        # 성능 평가
        if self.task_type == 'regression':
            self.metrics = calculate_regression_metrics(y_test, y_pred)
        else:
            self.metrics = calculate_classification_metrics(y_test, y_pred)
        
        # 교차 검증 스코어
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=5, 
            scoring='neg_mean_squared_error' if self.task_type == 'regression' else 'accuracy'
        )
        self.metrics['cv_score_mean'] = cv_scores.mean()
        self.metrics['cv_score_std'] = cv_scores.std()
        
        # SVR은 서포트 벡터 정보 포함
        if hasattr(self.model, 'n_support_'):
            self.metrics['n_support'] = self._safe_to_list(self.model.n_support_)
        if hasattr(self.model, 'support_'):
            self.metrics['support_vectors'] = len(self.model.support_)
        
        # 피처 중요도 (SVR은 피처 중요도 직접 계산 불가)
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': [1.0 / len(self.feature_names)] * len(self.feature_names)  # 동일한 중요도
        }).sort_values('importance', ascending=False)
        
        # 결과 반환
        return {
            'model': self.model,
            'scaler': self.scaler,
            'metrics': self.metrics,
            'feature_importance': feature_importance,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'test_actual': y_test,
            'test_predictions': y_pred,
            'training_history': {}  # SVR은 학습 곡선 지원 안함
        }
    
    def hyperparameter_tuning(self, df: pd.DataFrame, target_col: str, 
                            test_size: float = 0.2, cv: int = 5) -> Dict[str, Any]:
        """
        하이퍼파라미터 튜닝
        
        Args:
            df: 훈련 데이터
            target_col: 타겟 변수
            test_size: 테스트 데이터 비율
            cv: 교차 검증 폴드 수
            
        Returns:
            최적 하이퍼파라미터 및 성능
        """
        # 데이터 전처리
        X_train, X_test, y_train, y_test = preprocess_data(df, target_col, test_size)
        
        # 피처 스케일링
        X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)
        
        # 하이퍼파라미터 그리드
        if self.task_type == 'regression':
            param_grid = {
                'kernel': ['rbf', 'poly', 'linear'],
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1],
                'epsilon': [0.01, 0.1, 0.2]
            }
            base_model = SVR()
            scoring = 'neg_mean_squared_error'
        else:
            param_grid = {
                'kernel': ['rbf', 'poly', 'linear'],
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1, 1]
            }
            base_model = SVC(random_state=42, probability=True)
            scoring = 'accuracy'
        
        # 그리드 서치
        grid_search = GridSearchCV(
            base_model, param_grid, cv=cv, scoring=scoring, 
            n_jobs=-1, verbose=1
        )
        grid_search.fit(X_train_scaled, y_train)
        
        # 최적 모델로 예측
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test_scaled)
        
        # 성능 평가
        if self.task_type == 'regression':
            metrics = calculate_regression_metrics(y_test, y_pred)
        else:
            metrics = calculate_classification_metrics(y_test, y_pred)
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'best_model': best_model,
            'metrics': metrics,
            'scaler': scaler,
            'grid_search_results': grid_search.cv_results_
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """예측 수행"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        if self.scaler is None:
            raise ValueError("스케일러가 설정되지 않았습니다.")
        
        # 피처 선택 (훈련 시 사용한 피처만, 입력 데이터에 있는 것만)
        if self.feature_names:
            # 입력 데이터에 실제로 있는 피처만 선택
            available_features = [col for col in self.feature_names if col in X.columns]
            if available_features:
                X = X[available_features]
            else:
                # 모든 피처가 없는 경우 입력 데이터 그대로 사용
                pass
        
        X = X.fillna(X.mean())
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """예측 확률 반환 (분류 모델만)"""
        if self.task_type != 'classification':
            raise ValueError("분류 모델에서만 사용 가능합니다.")
        
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        if self.scaler is None:
            raise ValueError("스케일러가 설정되지 않았습니다.")
        
        # 피처 선택 (훈련 시 사용한 피처만, 입력 데이터에 있는 것만)
        if self.feature_names:
            # 입력 데이터에 실제로 있는 피처만 선택
            available_features = [col for col in self.feature_names if col in X.columns]
            if available_features:
                X = X[available_features]
            else:
                # 모든 피처가 없는 경우 입력 데이터 그대로 사용
                pass
        
        X = X.fillna(X.mean())
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict_proba(X_scaled)
    
    def get_support_vectors(self) -> Dict[str, Any]:
        """서포트 벡터 정보 반환"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        if not hasattr(self.model, 'support_'):
            return {"message": "서포트 벡터 정보가 없습니다."}
        
        return {
            'n_support_vectors': len(self.model.support_),
            'support_vector_indices': self.model.support_,
            'support_vectors': self.model.support_vectors_,
            'n_support_per_class': self.model.n_support_ if hasattr(self.model, 'n_support_') else None
        }
    
    def save_model(self, model_name: str) -> str:
        """모델 저장"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        # 모델과 스케일러를 함께 저장
        model_data = {
            'model': self.model,
            'scaler': self.scaler
        }
        
        return save_model(
            model_data, 
            model_name, 
            'svr',
            self.metrics,
            self.feature_names
        )
    
    def load_model(self, model_path: str):
        """모델 로드"""
        model_data = load_model(model_path)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        
        # 메타데이터 로드
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        try:
            with open(metadata_path, 'r') as f:
                import json
                metadata = json.load(f)
                self.feature_names = metadata.get('feature_names', [])
                self.metrics = metadata.get('metrics', {})
        except FileNotFoundError:
            print(f"메타데이터 파일을 찾을 수 없습니다: {metadata_path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        if self.model is None:
            return {"message": "모델이 훈련되지 않았습니다."}
        
        return {
            'model_type': 'SVR' if self.task_type == 'regression' else 'SVC',
            'task_type': self.task_type,
            'kernel': self.model.kernel,
            'C': self.model.C,
            'gamma': self.model.gamma,
            'epsilon': self.model.epsilon if hasattr(self.model, 'epsilon') else None,
            'n_support_vectors': len(self.model.support_) if hasattr(self.model, 'support_') else None,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'metrics': self.metrics,
            'model_params': self.model.get_params()
        } 