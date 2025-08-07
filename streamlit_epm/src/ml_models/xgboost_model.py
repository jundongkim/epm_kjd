"""
XGBoost 모델 구현
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# XGBoost import - OpenMP 런타임 오류 등을 안전하게 처리
try:
    import xgboost as xgb
    from xgboost import XGBRegressor, XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError as e:
    print(f"XGBoost import failed: {e}")
    xgb = None
    XGBRegressor = None
    XGBClassifier = None
    XGBOOST_AVAILABLE = False
except Exception as e:
    # OpenMP 런타임 오류, 라이브러리 로딩 오류 등 다른 에러도 catch
    print(f"XGBoost library loading failed: {e}")
    print("Common solutions:")
    print("  - macOS: brew install libomp")
    print("  - Linux: sudo apt-get install libomp-dev")
    print("  - Windows: Reinstall XGBoost")
    xgb = None
    XGBRegressor = None
    XGBClassifier = None
    XGBOOST_AVAILABLE = False

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


class XGBoostCallback:
    """XGBoost 훈련 진행 상황 콜백"""
    
    def __init__(self, training_callback=None):
        self.training_callback = training_callback
        self.iteration = 0
        
    def __call__(self, env):
        """XGBoost 콜백 함수"""
        if self.training_callback is None:
            return
        
        # 현재 iteration 정보 추출
        self.iteration = env.iteration
        
        # 메트릭 정보 추출
        metrics = {}
        if hasattr(env, 'evaluation_result_list') and env.evaluation_result_list:
            for eval_result in env.evaluation_result_list:
                if len(eval_result) >= 3:
                    dataset_name = eval_result[0]
                    metric_name = eval_result[1]
                    metric_value = eval_result[2]
                    metrics[f"{dataset_name}_{metric_name}"] = metric_value
        
        # 콜백 호출
        self.training_callback.on_iteration_end(self.iteration, metrics)
        
        # 조기 종료 확인
        if hasattr(env, 'best_iteration') and env.best_iteration is not None:
            if env.iteration >= env.best_iteration + env.early_stopping_rounds:
                self.training_callback.on_early_stopping(env.best_iteration)


class XGBoostModel:
    """XGBoost 모델 클래스"""
    
    def __init__(self, task_type: str = 'regression'):
        """
        Args:
            task_type: 'regression' 또는 'classification'
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost가 설치되지 않았습니다. 'pip install xgboost'로 설치해주세요.")
        
        self.task_type = task_type
        self.model = None
        self.feature_names = None
        self.target_name = None
        self.metrics = {}
        self.training_history = {}
        
    def train(self, df: pd.DataFrame, target_col: str, 
              n_estimators: int = 1000, max_depth: int = 6,
              learning_rate: float = 0.1, subsample: float = 0.8,
              colsample_bytree: float = 0.8, reg_alpha: float = 0,
              reg_lambda: float = 1, gamma: float = 0,
              min_child_weight: float = 1, early_stopping_rounds: int = None,
              eval_metric: str = 'rmse', use_core_api: bool = False,
              objective: str = None, verbose: int = 1,
              test_size: float = 0.2, random_state: int = 42,
              callback=None) -> Dict[str, Any]:
        """
        모델 훈련
        
        Args:
            df: 훈련 데이터
            target_col: 타겟 변수 컬럼명
            n_estimators: 트리 개수
            max_depth: 최대 깊이
            learning_rate: 학습률
            subsample: 서브샘플링 비율
            colsample_bytree: 컬럼 샘플링 비율
            reg_alpha: L1 정규화
            reg_lambda: L2 정규화
            gamma: 최소 분할 손실
            min_child_weight: 최소 자식 가중치
            early_stopping_rounds: 조기 종료 라운드
            eval_metric: 평가 메트릭
            use_core_api: Core API 사용 여부
            objective: 목적 함수
            verbose: 출력 레벨
            test_size: 테스트 데이터 비율
            random_state: 랜덤 시드
            callback: 훈련 진행 상황 콜백
            
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
        
        # 목적 함수 설정
        if objective is None:
            if self.task_type == 'regression':
                objective = 'reg:squarederror'
            else:
                objective = 'binary:logistic'
        
        # XGBoost 파라미터 설정
        xgb_params = {
            'objective': objective,
            'learning_rate': learning_rate,
            'max_depth': max_depth,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'reg_alpha': reg_alpha,
            'reg_lambda': reg_lambda,
            'gamma': gamma,
            'min_child_weight': min_child_weight,
            'random_state': random_state,
            'eval_metric': eval_metric
        }
        
        # Core API 사용 여부에 따른 모델 훈련
        if use_core_api:
            # Core API 사용 (더 세밀한 제어 가능)
            dtrain = xgb.DMatrix(X_train, label=y_train)
            dtest = xgb.DMatrix(X_test, label=y_test)
            
            # 평가 결과 저장을 위한 딕셔너리
            evals_result = {}
            
            # 콜백 설정
            callbacks = []
            if callback:
                xgb_callback = XGBoostCallback(callback)
                callbacks.append(xgb_callback)
            
            # 모델 훈련
            self.model = xgb.train(
                xgb_params,
                dtrain,
                num_boost_round=n_estimators,
                evals=[(dtrain, 'train'), (dtest, 'test')],
                early_stopping_rounds=early_stopping_rounds,
                evals_result=evals_result,
                callbacks=callbacks,
                verbose_eval=verbose if verbose > 0 else False
            )
            
            # 평가 결과 저장
            self.model.evals_result_dict = evals_result
            self.training_history = evals_result
            
            # 예측
            y_pred = self.model.predict(dtest)
            
        else:
            # scikit-learn API 사용
            # 기본 파라미터 설정
            base_params = {
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'learning_rate': learning_rate,
                'subsample': subsample,
                'colsample_bytree': colsample_bytree,
                'reg_alpha': reg_alpha,
                'reg_lambda': reg_lambda,
                'gamma': gamma,
                'min_child_weight': min_child_weight,
                'random_state': random_state,
                'n_jobs': -1
            }
            
            # objective가 None이 아닌 경우에만 추가
            if objective is not None:
                base_params['objective'] = objective
            
            # 일부 XGBoost 버전에서는 early_stopping_rounds를 모델 초기화 시에 전달할 수 있음
            try:
                if early_stopping_rounds is not None:
                    base_params['early_stopping_rounds'] = early_stopping_rounds
            except:
                pass  # 지원하지 않는 경우 무시
            
            if self.task_type == 'regression':
                self.model = XGBRegressor(**base_params)
            else:
                self.model = XGBClassifier(**base_params)
            
            # 조기 종료 설정 (XGBoost 버전 호환성 완전 대응)
            def _safe_fit_with_early_stopping():
                """안전한 XGBoost 피팅 (다양한 버전 호환성)"""
                fit_params = {}
                
                # 콜백 설정
                if callback:
                    # Scikit-learn API에서는 간단한 콜백 시뮬레이션
                    for i in range(0, n_estimators, max(1, n_estimators // 20)):
                        metrics = {'iteration': i}
                        callback.on_iteration_end(i, metrics)
                
                if early_stopping_rounds is not None:
                    # 방법 1: eval_set과 early_stopping_rounds를 fit에 전달
                    try:
                        fit_params['eval_set'] = [(X_test, y_test)]
                        fit_params['early_stopping_rounds'] = early_stopping_rounds
                        if verbose > 0:
                            fit_params['verbose'] = True
                        
                        self.model.fit(X_train, y_train, **fit_params)
                        print(f"✅ XGBoost 조기 종료 적용됨 (rounds: {early_stopping_rounds})")
                        return True
                        
                    except TypeError as e:
                        if "early_stopping_rounds" in str(e):
                            print(f"⚠️ XGBoost early_stopping_rounds 파라미터 미지원: {e}")
                        else:
                            print(f"⚠️ XGBoost fit TypeError: {e}")
                    except Exception as e:
                        print(f"⚠️ XGBoost fit 오류: {e}")
                
                # 방법 2: 조기 종료 없이 기본 훈련
                try:
                    if verbose > 0:
                        self.model.fit(X_train, y_train, verbose=True)
                    else:
                        self.model.fit(X_train, y_train)
                    print("✅ XGBoost 기본 훈련 완료 (조기 종료 미적용)")
                    return True
                except Exception as e:
                    print(f"❌ XGBoost 기본 훈련도 실패: {e}")
                    return False
            
            # 안전한 피팅 실행
            success = _safe_fit_with_early_stopping()
            if not success:
                raise RuntimeError("XGBoost 모델 훈련에 실패했습니다.")
            
            # 예측
            y_pred = self.model.predict(X_test)
        
        # 성능 평가
        if self.task_type == 'regression':
            self.metrics = calculate_regression_metrics(y_test, y_pred)
        else:
            self.metrics = calculate_classification_metrics(y_test, y_pred)
        
        # 교차 검증 스코어 (scikit-learn API인 경우만)
        if not use_core_api:
            cv_scores = cross_val_score(
                self.model, X_train, y_train, cv=5, 
                scoring='neg_mean_squared_error' if self.task_type == 'regression' else 'accuracy'
            )
            self.metrics['cv_score_mean'] = cv_scores.mean()
            self.metrics['cv_score_std'] = cv_scores.std()
        
        # 피처 중요도 계산
        feature_importance = self._get_feature_importance()
        
        return {
            'model': self.model,
            'metrics': self.metrics,
            'feature_importance': feature_importance,
            'test_predictions': y_pred.tolist() if hasattr(y_pred, 'tolist') else y_pred,
            'test_actual': y_test.tolist() if hasattr(y_test, 'tolist') else y_test,
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
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 6, 10],
            'learning_rate': [0.01, 0.1, 0.2],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0]
        }
        
        # 모델 초기화
        if self.task_type == 'regression':
            base_model = XGBRegressor(random_state=42, n_jobs=-1)
            scoring = 'neg_mean_squared_error'
        else:
            base_model = XGBClassifier(random_state=42, n_jobs=-1)
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
        
        # Core API 모델인지 확인
        if hasattr(self.model, 'predict') and not hasattr(self.model, 'fit'):
            # Core API 모델인 경우 DMatrix로 변환
            dmat = xgb.DMatrix(X)
            return self.model.predict(dmat)
        else:
            # scikit-learn API 모델인 경우
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
        
        # Core API 모델인지 확인
        if hasattr(self.model, 'predict') and not hasattr(self.model, 'fit'):
            # Core API 모델인 경우 DMatrix로 변환
            dmat = xgb.DMatrix(X)
            proba = self.model.predict(dmat)
            # 이진 분류의 경우 확률을 2차원으로 변환
            if len(proba.shape) == 1:
                proba = np.column_stack([1 - proba, proba])
            return proba
        else:
            # scikit-learn API 모델인 경우
            return self.model.predict_proba(X)
    
    def _get_feature_importance(self) -> pd.DataFrame:
        """피처 중요도 계산 (iot_algorithm 구현 방식 참조)"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        try:
            importance = None
            
            # 방식 1: Core API 모델 (xgb.train으로 훈련된 모델)
            if hasattr(self.model, 'get_score') and not hasattr(self.model, 'fit'):
                try:
                    # Core API models use get_score directly
                    importance_dict = self.model.get_score(importance_type='gain')
                    
                    if isinstance(importance_dict, dict):
                        # Convert dictionary to array matching feature_names order
                        importance_series = pd.Series(importance_dict)
                        importance = np.zeros(len(self.feature_names))
                        
                        for i, feature in enumerate(self.feature_names):
                            if feature in importance_series:
                                importance[i] = importance_series[feature]
                    
                    print(f"Core API 피처 중요도 계산 성공: {len(importance_dict)} 피처")
                except Exception as e:
                    print(f"Core API get_score 실패: {e}")
                    importance = None
            
            # 방식 2: Scikit-learn API 모델 (XGBRegressor/XGBClassifier)
            else:
                try:
                    # Try feature_importances_ first
                    if hasattr(self.model, 'feature_importances_'):
                        importance = self.model.feature_importances_
                        print(f"Scikit-learn API feature_importances_ 사용: {len(importance)} 피처")
                except Exception as e:
                    print(f"feature_importances_ 실패: {e}")
                    importance = None
                
                # Fallback: get_booster().get_score() 
                if importance is None:
                    try:
                        booster = self.model.get_booster()
                        importance_dict = booster.get_score(importance_type='gain')
                        
                        # Convert dictionary to list matching feature_names order
                        importance = np.zeros(len(self.feature_names))
                        for i, feature in enumerate(self.feature_names):
                            # Try both actual feature name and f{i} format
                            if feature in importance_dict:
                                importance[i] = importance_dict[feature]
                            else:
                                feature_key = f"f{i}"
                                if feature_key in importance_dict:
                                    importance[i] = importance_dict[feature_key]
                        
                        print(f"get_booster().get_score() 사용: {len(importance_dict)} 피처")
                    except Exception as e:
                        print(f"get_booster().get_score() 실패: {e}")
                        importance = None
            
            # 최종 fallback: 균등 분배
            if importance is None or np.sum(importance) == 0:
                print("Warning: 피처 중요도를 계산할 수 없습니다. 균등 분배로 설정합니다.")
                importance = np.ones(len(self.feature_names)) / len(self.feature_names)
            
            # Feature importance DataFrame 생성
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False)
            
            # 결과 요약 출력
            print(f"피처 중요도 계산 완료: Top 3 - {feature_importance.head(3)['feature'].tolist()}")
            
            return feature_importance
            
        except Exception as e:
            print(f"피처 중요도 계산 중 치명적 오류: {e}")
            # 최종 안전장치: 균등한 중요도 반환
            importance = np.ones(len(self.feature_names)) / len(self.feature_names)
            
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False)
            
            return feature_importance
    
    def get_feature_importance(self, plot: bool = False) -> pd.DataFrame:
        """피처 중요도 반환"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")
        
        feature_importance = self._get_feature_importance()
        
        if plot:
            plt.figure(figsize=(10, 8))
            sns.barplot(data=feature_importance.head(10), x='importance', y='feature')
            plt.title('Top 10 Feature Importance (XGBoost)')
            plt.tight_layout()
            plt.show()
        
        return feature_importance
    
    def get_training_history(self) -> Dict[str, Any]:
        """학습 이력 반환"""
        return self.training_history
    
    def plot_learning_curve(self) -> Optional[plt.Figure]:
        """학습 곡선 플롯"""
        if not self.training_history:
            print("학습 이력이 없습니다. Core API로 훈련된 모델에서만 사용 가능합니다.")
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 학습 이력에서 메트릭 추출
        if 'train' in self.training_history and 'test' in self.training_history:
            train_metric = list(self.training_history['train'].keys())[0]
            test_metric = list(self.training_history['test'].keys())[0]
            
            train_scores = self.training_history['train'][train_metric]
            test_scores = self.training_history['test'][test_metric]
            iterations = list(range(1, len(train_scores) + 1))
            
            ax.plot(iterations, train_scores, 'b-', label=f'Train {train_metric}')
            ax.plot(iterations, test_scores, 'r-', label=f'Test {test_metric}')
            
            # 최적 반복 표시 (조기 종료가 사용된 경우)
            if hasattr(self.model, 'best_iteration'):
                ax.axvline(x=self.model.best_iteration, color='green', linestyle='--', 
                          label=f'Best Iteration: {self.model.best_iteration}')
            
            ax.set_xlabel('Iterations')
            ax.set_ylabel(train_metric.upper())
            ax.set_title('XGBoost Learning Curve')
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
            'xgboost',
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
        
        # Core API 모델인지 확인
        if hasattr(self.model, 'get_params'):
            model_params = self.model.get_params()
        else:
            model_params = {}
        
        return {
            'model_type': 'XGBoost',
            'task_type': self.task_type,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'metrics': self.metrics,
            'model_params': model_params,
            'training_history': self.training_history
        } 