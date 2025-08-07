"""
CatBoost 모델 구현
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error

from .utils import (
    preprocess_data, 
    calculate_regression_metrics,
    calculate_classification_metrics,
    save_model,
    load_model,
    validate_data
)


class CatBoostCallback:
    """CatBoost 훈련 진행 상황 콜백"""
    
    def __init__(self, training_callback=None):
        self.training_callback = training_callback
        self.iteration = 0
        
    def after_iteration(self, info):
        """CatBoost 콜백 함수"""
        if self.training_callback is None:
            return True
        
        # 현재 iteration 정보 추출
        self.iteration = info.iteration
        
        # 메트릭 정보 추출
        metrics = {}
        if hasattr(info, 'metrics') and info.metrics:
            for metric_name, metric_values in info.metrics.items():
                if 'learn' in metric_values:
                    metrics[f"train_{metric_name}"] = metric_values['learn'][-1]
                if 'validation' in metric_values:
                    metrics[f"val_{metric_name}"] = metric_values['validation'][-1]
        
        # 콜백 호출
        self.training_callback.on_iteration_end(self.iteration, metrics)
        
        return True


class CatBoostModel:
    """CatBoost 모델 클래스"""
    
    def __init__(self, task_type: str = 'regression'):
        """
        Args:
            task_type: 'regression' 또는 'classification'
        """
        if not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost가 설치되지 않았습니다. 'pip install catboost'로 설치해주세요.")
        
        self.task_type = task_type
        self.model = None
        self.feature_names = None
        self.target_name = None
        self.metrics = {}
        self.training_history = {}
        
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
               iterations: int = 1000, learning_rate: float = 0.01,
               depth: int = 6, early_stopping_rounds: int = None,
               use_best_model: bool = True, verbose: int = 1,
               test_size: float = 0.2, random_state: int = 42,
               hyperparameter_tuning: bool = False, show_progress: bool = True,
               callback=None) -> Dict[str, Any]:
        """
        모델 훈련
        
        Args:
            df: 훈련 데이터
            target_col: 타겟 변수 컬럼명
            iterations: 반복 횟수
            learning_rate: 학습률
            depth: 트리 깊이
            early_stopping_rounds: 조기 종료 라운드
            use_best_model: 최적 모델 사용 여부
            verbose: 출력 레벨
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
        
        # 피처명 저장
        self.feature_names = X_train.columns.tolist()
        self.target_name = target_col
        
        # 모델 초기화
        model_params = {
            'iterations': iterations,
            'learning_rate': learning_rate,
            'depth': depth,
            'random_seed': random_state,
            'verbose': verbose
        }
        
        if self.task_type == 'regression':
            model_params.update({
                'loss_function': 'RMSE',
                'eval_metric': 'RMSE'
            })
            self.model = cb.CatBoostRegressor(**model_params)
        else:
            model_params.update({
                'loss_function': 'Logloss',
                'eval_metric': 'Accuracy'
            })
            self.model = cb.CatBoostClassifier(**model_params)
        
        # 훈련 파라미터 설정
        fit_params = {
            'eval_set': [(X_test, y_test)],
            'verbose': verbose
        }
        
        if early_stopping_rounds is not None:
            fit_params['early_stopping_rounds'] = early_stopping_rounds
        
        if use_best_model:
            fit_params['use_best_model'] = use_best_model
        
        # 콜백 설정
        if callback:
            catboost_callback = CatBoostCallback(callback)
            fit_params['callbacks'] = [catboost_callback]
        
        # 모델 훈련
        self.model.fit(X_train, y_train, **fit_params)
        
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
        
        # 학습 이력 저장
        try:
            eval_results = self.model.get_evals_result()
            if eval_results:
                self.training_history = eval_results
        except:
            pass
        
        # 피처 중요도
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.get_feature_importance()
        }).sort_values('importance', ascending=False)
        
        return {
            'model': self.model,
            'metrics': self.metrics,
            'feature_importance': feature_importance,
            'test_predictions': self._safe_to_list(y_pred),
            'test_actual': self._safe_to_list(y_test),
            'feature_names': self.feature_names,
            'training_history': self.training_history
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
            'iterations': [500, 1000, 1500],
            'learning_rate': [0.01, 0.1, 0.2],
            'depth': [4, 6, 8],
            'l2_leaf_reg': [1, 3, 5]
        }
        
        # 모델 초기화
        if self.task_type == 'regression':
            base_model = cb.CatBoostRegressor(random_seed=42, verbose=False)
            scoring = 'neg_mean_squared_error'
        else:
            base_model = cb.CatBoostClassifier(random_seed=42, verbose=False)
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
        """예측 수행"""
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
        
        X = X.fillna(X.mean())
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """예측 확률 반환 (분류 모델만)"""
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
        
        X = X.fillna(X.mean())
        return self.model.predict_proba(X)
    
    def get_feature_importance(self, plot: bool = False) -> pd.DataFrame:
        """피처 중요도 반환"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.get_feature_importance()
        }).sort_values('importance', ascending=False)
        
        if plot:
            plt.figure(figsize=(10, 8))
            sns.barplot(data=feature_importance.head(10), x='importance', y='feature')
            plt.title('Top 10 Feature Importance (CatBoost)')
            plt.tight_layout()
            plt.show()
        
        return feature_importance
    
    def get_training_history(self) -> Dict[str, Any]:
        """학습 이력 반환"""
        return self.training_history
    
    def plot_learning_curve(self) -> Optional[plt.Figure]:
        """학습 곡선 플롯"""
        if not self.training_history:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 학습 이력에서 메트릭 추출
        if 'learn' in self.training_history:
            metric_names = list(self.training_history['learn'].keys())
            if metric_names:
                metric_name = metric_names[0]
                train_scores = self.training_history['learn'][metric_name]
                iterations = list(range(1, len(train_scores) + 1))
                
                ax.plot(iterations, train_scores, 'b-', label=f'Train {metric_name}')
                
                # 검증 데이터 점수
                for key in self.training_history:
                    if key != 'learn':
                        test_scores = self.training_history[key][metric_name]
                        ax.plot(iterations, test_scores, 'r-', label=f'Validation {metric_name}')
                        break
                
                ax.set_xlabel('Iterations')
                ax.set_ylabel(metric_name)
                ax.set_title('CatBoost Learning Curve')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        return fig
    
    def save_model(self, model_name: str) -> str:
        """모델 저장"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        return save_model(
            self.model, 
            model_name, 
            'catboost',
            self.metrics,
            self.feature_names
        )
    
    def load_model(self, model_path: str):
        """모델 로드"""
        self.model = load_model(model_path)
        
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
            'model_type': 'CatBoost',
            'task_type': self.task_type,
            'iterations': self.model.get_param('iterations'),
            'learning_rate': self.model.get_param('learning_rate'),
            'depth': self.model.get_param('depth'),
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'metrics': self.metrics,
            'model_params': self.model.get_params() if hasattr(self.model, 'get_params') else {}
        } 