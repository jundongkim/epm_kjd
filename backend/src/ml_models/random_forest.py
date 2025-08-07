"""
Random Forest 모델 구현
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.inspection import permutation_importance
from typing import Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error

from .utils import (
    preprocess_data, 
    calculate_regression_metrics,
    calculate_classification_metrics,
    save_model,
    load_model,
    validate_data
)


class RandomForestModel:
    """Random Forest 모델 클래스"""
    
    def __init__(self, task_type: str = 'regression'):
        """
        Args:
            task_type: 'regression' 또는 'classification'
        """
        self.task_type = task_type
        self.model = None
        self.feature_names = None
        self.target_name = None
        self.metrics = {}
        self.scaler = None
        
    def train(self, df: pd.DataFrame, target_col: str, 
              n_estimators: int = 100, max_depth: int = None,
              min_samples_split: int = 2, min_samples_leaf: int = 1,
              test_size: float = 0.2, random_state: int = 42,
              callback=None) -> Dict[str, Any]:
        """
        Random Forest 모델 훈련 (콜백 지원)
        
        Args:
            df: 훈련 데이터
            target_col: 타겟 변수명
            n_estimators: 트리 개수
            max_depth: 최대 깊이
            min_samples_split: 최소 분할 샘플 수
            min_samples_leaf: 최소 리프 샘플 수
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
        
        # 모델 초기화
        if self.task_type == 'regression':
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                random_state=random_state
            )
        else:
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                random_state=random_state
            )
        
        # 콜백 시뮬레이션 (Random Forest는 트리를 단계별로 학습)
        if callback:
            # 단계별 훈련 시뮬레이션
            step_size = max(1, n_estimators // 10)  # 10단계로 나누어 시뮬레이션
            
            for step in range(0, n_estimators, step_size):
                current_n_estimators = min(step + step_size, n_estimators)
                
                # 임시 모델로 부분 훈련
                temp_model = type(self.model)(
                    **{**self.model.get_params(), 'n_estimators': current_n_estimators}
                )
                temp_model.fit(X_train, y_train)
                
                # 메트릭 계산
                try:
                    y_pred_train = temp_model.predict(X_train)
                    y_pred_test = temp_model.predict(X_test)
                    
                    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                    
                    metrics = {
                        'trees_trained': current_n_estimators,
                        'train_rmse': train_rmse,
                        'test_rmse': test_rmse
                    }
                except:
                    metrics = {'trees_trained': current_n_estimators}
                
                callback.on_iteration_end(current_n_estimators, metrics)
                
                # 마지막 단계에서는 실제 모델 저장
                if current_n_estimators == n_estimators:
                    self.model = temp_model
        else:
            # 일반 훈련
            self.model.fit(X_train, y_train)
        
        # 예측
        y_pred = self.model.predict(X_test)
        
        # 성능 평가
        if self.task_type == 'regression':
            self.metrics = calculate_regression_metrics(y_test, y_pred)
        else:
            self.metrics = calculate_classification_metrics(y_test, y_pred)
        
        # 교차 검증 스코어
        cv_scores = cross_val_score(
            self.model, X_train, y_train, cv=5, 
            scoring='neg_mean_squared_error' if self.task_type == 'regression' else 'accuracy'
        )
        self.metrics['cv_score_mean'] = cv_scores.mean()
        self.metrics['cv_score_std'] = cv_scores.std()
        
        # 피처 중요도
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Random Forest의 경우 트리 개수별 성능 변화 추적
        training_history = {}
        if callback:
            # 콜백이 있었다면 간단한 트리 개수 vs 성능 이력 생성
            n_steps = 5
            step_size = max(1, n_estimators // n_steps)
            
            train_rmse_history = []
            test_rmse_history = []
            tree_counts = []
            
            for i in range(1, n_steps + 1):
                current_trees = min(i * step_size, n_estimators)
                tree_counts.append(current_trees)
                
                # 임시 모델로 성능 측정
                temp_model = type(self.model)(
                    **{**self.model.get_params(), 'n_estimators': current_trees}
                )
                temp_model.fit(X_train, y_train)
                
                # 예측 및 RMSE 계산
                y_pred_train = temp_model.predict(X_train)
                y_pred_test = temp_model.predict(X_test)
                
                train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
                test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                
                train_rmse_history.append(train_rmse)
                test_rmse_history.append(test_rmse)
            
            training_history = {
                'train': {'rmse': train_rmse_history},
                'test': {'rmse': test_rmse_history},
                'tree_counts': tree_counts
            }
        
        # 결과 반환
        return {
            'model': self.model,
            'metrics': self.metrics,
            'feature_importance': feature_importance,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'test_actual': y_test,
            'test_predictions': y_pred,
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
        
        # 하이퍼파라미터 그리드
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        # 모델 초기화
        if self.task_type == 'regression':
            base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
            scoring = 'neg_mean_squared_error'
        else:
            base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
            scoring = 'accuracy'
        
        # 그리드 서치
        grid_search = GridSearchCV(
            base_model, param_grid, cv=cv, scoring=scoring, 
            n_jobs=-1, verbose=1
        )
        grid_search.fit(X_train, y_train)
        
        # 최적 모델로 예측
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test)
        
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
            'grid_search_results': grid_search.cv_results_
        }
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        예측 수행
        
        Args:
            X: 예측할 데이터
            
        Returns:
            예측 결과
        """
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        # 피처 선택 (훈련 시 사용한 피처만, 입력 데이터에 있는 것만)
        if self.feature_names:
            # 입력 데이터에 실제로 있는 피처만 선택
            available_features = [col for col in self.feature_names if col in X.columns]
            if available_features:
                X = X[available_features]
            else:
                # 모든 피처가 없는 경우 입력 데이터 그대로 사용
                pass
        
        # 결측치 처리
        X = X.fillna(X.mean())
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        예측 확률 반환 (분류 모델만)
        
        Args:
            X: 예측할 데이터
            
        Returns:
            예측 확률
        """
        if self.task_type != 'classification':
            raise ValueError("분류 모델에서만 사용 가능합니다.")
        
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        # 피처 선택 (훈련 시 사용한 피처만, 입력 데이터에 있는 것만)
        if self.feature_names:
            # 입력 데이터에 실제로 있는 피처만 선택
            available_features = [col for col in self.feature_names if col in X.columns]
            if available_features:
                X = X[available_features]
            else:
                # 모든 피처가 없는 경우 입력 데이터 그대로 사용
                pass
        
        # 결측치 처리
        X = X.fillna(X.mean())
        
        return self.model.predict_proba(X)
    
    def get_feature_importance(self, plot: bool = False) -> pd.DataFrame:
        """
        피처 중요도 반환
        
        Args:
            plot: 시각화 여부
            
        Returns:
            피처 중요도 데이터프레임
        """
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        if plot:
            plt.figure(figsize=(10, 8))
            sns.barplot(data=feature_importance.head(10), x='importance', y='feature')
            plt.title('Top 10 Feature Importance')
            plt.tight_layout()
            plt.show()
        
        return feature_importance
    
    def save_model(self, model_name: str) -> str:
        """
        모델 저장
        
        Args:
            model_name: 모델명
            
        Returns:
            저장된 모델 경로
        """
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        return save_model(
            self.model, 
            model_name, 
            'random_forest',
            self.metrics,
            self.feature_names
        )
    
    def load_model(self, model_path: str):
        """
        모델 로드
        
        Args:
            model_path: 모델 파일 경로
        """
        self.model = load_model(model_path)
        
        # 메타데이터 로드 (경로에서 추출)
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
        """
        모델 정보 반환
        
        Returns:
            모델 정보 딕셔너리
        """
        if self.model is None:
            return {"message": "모델이 훈련되지 않았습니다."}
        
        return {
            'model_type': 'Random Forest',
            'task_type': self.task_type,
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'metrics': self.metrics,
            'model_params': self.model.get_params()
        } 