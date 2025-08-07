"""
Neural Network 모델 구현
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.model_selection import GridSearchCV, cross_val_score
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


class NeuralNetworkCallback:
    """Neural Network 훈련 진행 상황 시뮬레이션 콜백"""
    
    def __init__(self, training_callback=None):
        self.training_callback = training_callback
        self.iteration = 0
        
    def simulate_progress(self, max_iter: int, model, X_train, y_train, X_test, y_test):
        """훈련 진행 상황 시뮬레이션"""
        if self.training_callback is None:
            return
        
        # 주기적으로 메트릭 계산 및 콜백 호출
        update_interval = max(1, max_iter // 20)  # 20번 업데이트
        
        for i in range(0, max_iter, update_interval):
            # 현재까지의 훈련 상태 추정
            if hasattr(model, 'loss_curve_') and len(model.loss_curve_) > 0:
                current_loss = model.loss_curve_[-1]
                
                # 간단한 메트릭 계산
                try:
                    # 중간 예측 시도
                    if hasattr(model, 'predict'):
                        y_pred_train = model.predict(X_train)
                        y_pred_test = model.predict(X_test)
                        
                        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                        
                        metrics = {
                            'train_loss': current_loss,
                            'train_rmse': train_rmse,
                            'test_rmse': test_rmse
                        }
                    else:
                        metrics = {'train_loss': current_loss}
                        
                except:
                    metrics = {'train_loss': current_loss}
            else:
                # 손실 정보가 없는 경우 더미 메트릭
                metrics = {'iteration': i}
            
            # 콜백 호출
            self.training_callback.on_iteration_end(i, metrics)


class NeuralNetworkModel:
    """Neural Network 모델 클래스"""
    
    def __init__(self, task_type: str = 'regression'):
        """
        Args:
            task_type: 'regression' 또는 'classification'
        """
        self.task_type = task_type
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.target_name = None
        self.metrics = {}
        
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
               hidden_layer_sizes: tuple = (100, 100), max_iter: int = 200,
               alpha: float = 0.0001, learning_rate: str = 'constant',
               learning_rate_init: float = 0.001, activation: str = 'relu',
               solver: str = 'adam', batch_size: str = 'auto',
               test_size: float = 0.2, random_state: int = 42,
               hyperparameter_tuning: bool = False, show_progress: bool = True,
               callback=None) -> Dict[str, Any]:
        """
        모델 훈련
        
        Args:
            df: 훈련 데이터
            target_col: 타겟 변수 컬럼명
            hidden_layer_sizes: 은닉층 크기 튜플
            activation: 활성화 함수
            solver: 최적화 알고리즘
            alpha: L2 정규화 계수
            learning_rate: 학습률 스케줄
            learning_rate_init: 초기 학습률
            max_iter: 최대 반복 횟수
            test_size: 테스트 데이터 비율
            random_state: 랜덤 시드
            
        Returns:
            훈련 결과 딕셔너리
        """
        # 데이터 유효성 검증
        required_columns = [target_col]
        validation = validate_data(df, required_columns)
        if not validation['is_valid']:
            raise ValueError(f"데이터 유효성 검증 실패: {validation['errors']}")
        
        # 데이터 전처리
        X_train, X_test, y_train, y_test = preprocess_data(
            df, target_col, test_size, random_state
        )
        
        # 피처 스케일링 (신경망은 스케일링 필수)
        X_train_scaled, X_test_scaled, self.scaler = scale_features(X_train, X_test)
        
        # 피처명 저장
        self.feature_names = X_train.columns.tolist()
        self.target_name = target_col
        
        # 모델 초기화
        if self.task_type == 'regression':
            self.model = MLPRegressor(
                hidden_layer_sizes=hidden_layer_sizes,
                activation=activation,
                solver=solver,
                alpha=alpha,
                learning_rate=learning_rate,
                learning_rate_init=learning_rate_init,
                max_iter=max_iter,
                random_state=random_state
            )
        else:
            self.model = MLPClassifier(
                hidden_layer_sizes=hidden_layer_sizes,
                activation=activation,
                solver=solver,
                alpha=alpha,
                learning_rate=learning_rate,
                learning_rate_init=learning_rate_init,
                max_iter=max_iter,
                random_state=random_state
            )
        
        # 콜백 설정
        if callback:
            nn_callback = NeuralNetworkCallback(callback)
            
            # 훈련 전 콜백 시뮬레이션을 위한 부분 훈련
            partial_max_iter = max(1, max_iter // 5)  # 5단계로 나누어 훈련
            
            for step in range(5):
                # 부분 훈련
                current_iter = (step + 1) * partial_max_iter
                if current_iter > max_iter:
                    current_iter = max_iter
                
                # 임시 모델로 부분 훈련
                temp_params = self.model.get_params()
                temp_params['max_iter'] = current_iter
                temp_model = type(self.model)(**temp_params)
                temp_model.fit(X_train_scaled, y_train)
                
                # 메트릭 계산 및 콜백 호출
                if hasattr(temp_model, 'loss_curve_') and len(temp_model.loss_curve_) > 0:
                    current_loss = temp_model.loss_curve_[-1]
                    
                    try:
                        y_pred_train = temp_model.predict(X_train_scaled)
                        y_pred_test = temp_model.predict(X_test_scaled)
                        
                        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                        
                        metrics = {
                            'train_loss': current_loss,
                            'train_rmse': train_rmse,
                            'test_rmse': test_rmse
                        }
                    except:
                        metrics = {'train_loss': current_loss}
                else:
                    metrics = {'iteration': current_iter}
                
                callback.on_iteration_end(current_iter, metrics)
                
                # 마지막 단계에서는 실제 모델 저장
                if step == 4:
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
        
        # 훈련 과정 정보
        self.metrics['n_iter'] = int(self.model.n_iter_) if hasattr(self.model, 'n_iter_') else None
        self.metrics['n_layers'] = int(self.model.n_layers_) if hasattr(self.model, 'n_layers_') else None
        self.metrics['n_outputs'] = int(self.model.n_outputs_) if hasattr(self.model, 'n_outputs_') else None
        
        # 피처 중요도 (Neural Network는 피처 중요도 직접 계산 불가)
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': [1.0 / len(self.feature_names)] * len(self.feature_names)  # 동일한 중요도
        }).sort_values('importance', ascending=False)
        
        # 학습 곡선 정보 (Neural Network의 경우 loss curve 사용)
        training_history = {}
        if hasattr(self.model, 'loss_curve_') and self.model.loss_curve_ is not None:
            try:
                loss_curve = self.model.loss_curve_
                if hasattr(loss_curve, 'tolist'):
                    loss_list = loss_curve.tolist()
                elif isinstance(loss_curve, list):
                    loss_list = loss_curve
                else:
                    loss_list = list(loss_curve) if hasattr(loss_curve, '__iter__') else []
                
                training_history = {
                    'loss': loss_list,
                    'iterations': list(range(1, len(loss_list) + 1))
                }
            except (AttributeError, TypeError) as e:
                # Loss curve 처리 실패 시 빈 딕셔너리 반환
                training_history = {}
        
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
            'loss_curve': self.model.loss_curve_ if hasattr(self.model, 'loss_curve_') else None,
            'training_history': training_history
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
        param_grid = {
            'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
            'activation': ['relu', 'tanh'],
            'solver': ['adam', 'lbfgs'],
            'alpha': [0.0001, 0.001, 0.01],
            'learning_rate_init': [0.001, 0.01]
        }
        
        # 모델 초기화
        if self.task_type == 'regression':
            base_model = MLPRegressor(random_state=42, max_iter=500)
            scoring = 'neg_mean_squared_error'
        else:
            base_model = MLPClassifier(random_state=42, max_iter=500)
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
    
    def get_loss_curve(self, plot: bool = False) -> np.ndarray:
        """손실 곡선 반환"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        loss_curve = self.model.loss_curve_
        
        if plot:
            plt.figure(figsize=(10, 6))
            plt.plot(loss_curve)
            plt.title('Neural Network Loss Curve')
            plt.xlabel('Iterations')
            plt.ylabel('Loss')
            plt.grid(True)
            plt.show()
        
        return loss_curve
    
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
            'neural_network',
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
            'model_type': 'Neural Network',
            'task_type': self.task_type,
            'hidden_layer_sizes': self.model.hidden_layer_sizes,
            'activation': self.model.activation,
            'solver': self.model.solver,
            'alpha': self.model.alpha,
            'learning_rate': self.model.learning_rate,
            'n_iter': self.model.n_iter_,
            'n_layers': self.model.n_layers_,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'metrics': self.metrics,
            'model_params': self.model.get_params()
        } 