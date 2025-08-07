"""
ML 모델 통합 관리자
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import os
import json
from datetime import datetime
import streamlit as st

from .utils import validate_data, save_model, load_model, get_model_metadata, get_available_models

# 모델 클래스 import
try:
    from .random_forest import RandomForestModel
    RF_AVAILABLE = True
except ImportError:
    RF_AVAILABLE = False

try:
    from .neural_network import NeuralNetworkModel
    NN_AVAILABLE = True
except ImportError:
    NN_AVAILABLE = False

try:
    from .svr_model import SVRModel
    SVR_AVAILABLE = True
except ImportError:
    SVR_AVAILABLE = False

try:
    from .xgboost_model import XGBoostModel
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from .catboost_model import CatBoostModel
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False


class TrainingCallback:
    """모델 훈련 진행 상황 콜백 클래스"""
    
    def __init__(self, use_streamlit: bool = True):
        self.use_streamlit = use_streamlit
        self.reset()
        
    def reset(self):
        """콜백 상태 초기화"""
        self.iteration = 0
        self.max_iterations = 100
        self.current_metrics = {}
        self.training_history = []
        self.is_early_stopped = False
        self.best_iteration = None
        
        # Streamlit 컴포넌트 초기화
        if self.use_streamlit:
            self.progress_bar = None
            self.status_text = None
            self.metrics_container = None
            self.chart_container = None
            
    def setup_streamlit_components(self):
        """Streamlit 컴포넌트 설정"""
        if not self.use_streamlit:
            return
            
        # 진행 상황 표시 컨테이너
        st.markdown("### 🔄 모델 훈련 진행 상황")
        
        # 진행 바와 상태 텍스트
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
        # 메트릭 표시 컨테이너 (2개 열)
        col1, col2 = st.columns(2)
        with col1:
            self.metrics_container = st.empty()
        with col2:
            self.chart_container = st.empty()
    
    def on_train_begin(self, max_iterations: int):
        """훈련 시작 시 호출"""
        self.max_iterations = max_iterations
        self.iteration = 0
        self.training_history = []
        
        if self.use_streamlit:
            self.setup_streamlit_components()
            self.status_text.text(f"🚀 모델 훈련 시작... (총 {max_iterations}회 반복)")
    
    def on_iteration_end(self, iteration: int, metrics: Dict[str, float]):
        """각 iteration 종료 시 호출"""
        self.iteration = iteration
        self.current_metrics = metrics
        self.training_history.append({
            'iteration': iteration,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            **metrics
        })
        
        if self.use_streamlit:
            self._update_streamlit_display()
    
    def on_early_stopping(self, best_iteration: int):
        """조기 종료 시 호출"""
        self.is_early_stopped = True
        self.best_iteration = best_iteration
        
        if self.use_streamlit:
            self.status_text.text(f"⏹️ 조기 종료: {best_iteration}번째 iteration에서 최적 성능")
    
    def on_train_end(self, final_metrics: Dict[str, float]):
        """훈련 종료 시 호출"""
        if self.use_streamlit:
            self.progress_bar.progress(1.0)
            
            if self.is_early_stopped:
                self.status_text.text(f"✅ 훈련 완료! (조기 종료: {self.best_iteration}/{self.max_iterations})")
            else:
                self.status_text.text(f"✅ 훈련 완료! ({self.iteration}/{self.max_iterations})")
            
            # 최종 메트릭 표시
            self._display_final_metrics(final_metrics)
    
    def _update_streamlit_display(self):
        """Streamlit 디스플레이 업데이트"""
        if not self.use_streamlit:
            return
        
        # 진행 바 업데이트
        progress = self.iteration / self.max_iterations
        self.progress_bar.progress(progress)
        
        # 상태 텍스트 업데이트
        self.status_text.text(f"🔄 훈련 중... {self.iteration}/{self.max_iterations} ({progress:.1%})")
        
        # 현재 메트릭 표시
        if self.metrics_container and self.current_metrics:
            with self.metrics_container:
                st.markdown("**📊 현재 메트릭:**")
                for key, value in self.current_metrics.items():
                    if isinstance(value, (int, float)):
                        st.metric(key.upper(), f"{value:.4f}")
        
        # 학습 곡선 차트 업데이트
        if self.chart_container and len(self.training_history) > 1:
            with self.chart_container:
                self._update_learning_curve()
    
    def _update_learning_curve(self):
        """학습 곡선 차트 업데이트"""
        if len(self.training_history) < 2:
            return
            
        # 데이터프레임 생성
        df = pd.DataFrame(self.training_history)
        
        # 메트릭 열 선택 (iteration과 timestamp 제외)
        metric_cols = [col for col in df.columns if col not in ['iteration', 'timestamp']]
        
        if not metric_cols:
            return
        
        # 차트 표시
        st.markdown("**📈 학습 곡선:**")
        
        # iteration을 인덱스로 설정
        chart_data = df.set_index('iteration')[metric_cols]
        
        # 최근 50개 포인트만 표시 (성능 최적화)
        if len(chart_data) > 50:
            chart_data = chart_data.tail(50)
        
        st.line_chart(chart_data, height=300)
    
    def _display_final_metrics(self, final_metrics: Dict[str, float]):
        """최종 메트릭 표시"""
        if not final_metrics:
            return
            
        st.markdown("### 🎯 최종 성능 지표")
        
        # 메트릭을 2개 열로 표시
        cols = st.columns(2)
        col_idx = 0
        
        for key, value in final_metrics.items():
            if isinstance(value, (int, float)):
                with cols[col_idx % 2]:
                    st.metric(key.upper(), f"{value:.4f}")
                col_idx += 1
        
        # 훈련 이력 요약
        if self.training_history:
            st.markdown("### 📋 훈련 이력 요약")
            
            # 마지막 10개 iteration 표시
            recent_history = self.training_history[-10:]
            history_df = pd.DataFrame(recent_history)
            
            # 컬럼 순서 조정
            if 'iteration' in history_df.columns:
                cols = ['iteration', 'timestamp'] + [col for col in history_df.columns if col not in ['iteration', 'timestamp']]
                history_df = history_df[cols]
            
            st.dataframe(history_df, use_container_width=True)


class ModelManager:
    """ML 모델 통합 관리 클래스"""
    
    def __init__(self):
        self.models = {}
        self.active_model = None
        self.available_model_types = {}
        self.callback = TrainingCallback(use_streamlit=True)
        
        # 사용 가능한 모델 타입 등록
        if RF_AVAILABLE:
            self.available_model_types['random_forest'] = RandomForestModel
        if NN_AVAILABLE:
            self.available_model_types['neural_network'] = NeuralNetworkModel
        if SVR_AVAILABLE:
            self.available_model_types['svr'] = SVRModel
        if XGBOOST_AVAILABLE:
            self.available_model_types['xgboost'] = XGBoostModel
        if CATBOOST_AVAILABLE:
            self.available_model_types['catboost'] = CatBoostModel
    
    def create_model(self, model_type: str, model_name: str, 
                    task_type: str = 'regression') -> bool:
        """
        새 모델 생성
        
        Args:
            model_type: 모델 타입 (random_forest, xgboost, neural_network, svr)
            model_name: 모델명
            task_type: 태스크 타입 (regression, classification)
            
        Returns:
            생성 성공 여부
        """
        if model_type not in self.available_model_types:
            raise ValueError(f"지원되지 않는 모델 타입: {model_type}")
        
        # XGBoost 가용성 체크
        if model_type == 'xgboost' and not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost가 설치되지 않았습니다. OpenMP 런타임을 설치하거나 다른 모델을 사용해주세요.")
        
        # CatBoost 가용성 체크
        if model_type == 'catboost' and not CATBOOST_AVAILABLE:
            raise ImportError("CatBoost가 설치되지 않았습니다. 'pip install catboost'로 설치하거나 다른 모델을 사용해주세요.")
        
        try:
            model_class = self.available_model_types[model_type]
            
            model_instance = model_class(task_type=task_type)
            self.models[model_name] = {
                'model': model_instance,
                'type': model_type,
                'task_type': task_type,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return True
            
        except Exception as e:
            print(f"모델 생성 중 오류 발생: {e}")
            return False
    
    def train_model(self, model_name: str, df: pd.DataFrame, 
                   target_col: str, show_progress: bool = True, **kwargs) -> Dict[str, Any]:
        """
        모델 훈련 (진행 상황 실시간 표시)
        
        Args:
            model_name: 모델명
            df: 훈련 데이터
            target_col: 타겟 변수
            show_progress: 진행 상황 표시 여부
            **kwargs: 모델별 파라미터
            
        Returns:
            훈련 결과
        """
        if model_name not in self.models:
            raise ValueError(f"모델 '{model_name}'이 존재하지 않습니다.")
        
        # 데이터 유효성 검증
        required_columns = [target_col]
        validation = validate_data(df, required_columns)
        if not validation['is_valid']:
            raise ValueError(f"데이터 유효성 검증 실패: {validation['errors']}")
        
        # 디버깅 정보 출력
        import streamlit as st
        st.write(f"📊 **훈련 데이터 정보**: {df.shape}")
        st.write(f"🎯 **타겟 변수**: {target_col} (타입: {df[target_col].dtype})")
        
        # 날짜 형식 컬럼 확인
        date_like_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                # 샘플 값 확인
                sample_values = df[col].dropna().head(3).tolist()
                if sample_values:
                    st.write(f"📝 **{col}** 샘플 값: {sample_values}")
                    # 날짜 형식인지 확인
                    try:
                        pd.to_datetime(sample_values[0], errors='raise')
                        date_like_columns.append(col)
                    except:
                        pass
        
        if date_like_columns:
            st.warning(f"⚠️ **날짜 형식 컬럼 감지**: {date_like_columns}")
        
        model_instance = self.models[model_name]['model']
        model_type = self.models[model_name]['type']
        
        # 콜백 설정
        if show_progress:
            self.callback.reset()
            kwargs['callback'] = self.callback
        
        try:
            # 모델별 특화 훈련 파라미터 설정
            if model_type == 'xgboost':
                # XGBoost는 n_estimators를 이용해 max_iterations 설정
                max_iterations = kwargs.get('n_estimators', 1000)
                if show_progress:
                    self.callback.on_train_begin(max_iterations)
                    
            elif model_type == 'catboost':
                # CatBoost는 iterations를 이용해 max_iterations 설정
                max_iterations = kwargs.get('iterations', 1000)
                if show_progress:
                    self.callback.on_train_begin(max_iterations)
                    
            elif model_type == 'neural_network':
                # Neural Network는 max_iter를 이용해 max_iterations 설정
                max_iterations = kwargs.get('max_iter', 200)
                if show_progress:
                    self.callback.on_train_begin(max_iterations)
                    
            else:
                # 기타 모델들은 기본값 사용
                if show_progress:
                    self.callback.on_train_begin(100)
            
            # 모델 훈련 실행
            result = model_instance.train(df, target_col, **kwargs)
            
            # 훈련 완료 콜백
            if show_progress:
                final_metrics = result.get('metrics', {})
                self.callback.on_train_end(final_metrics)
            
            # 모델 상태 업데이트
            self.models[model_name]['last_trained'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.models[model_name]['trained'] = True
            
            return result
            
        except Exception as e:
            print(f"모델 훈련 중 오류 발생: {e}")
            raise e
    
    def predict(self, model_name: str, X: pd.DataFrame) -> np.ndarray:
        """
        예측 수행
        
        Args:
            model_name: 모델명
            X: 예측 데이터
            
        Returns:
            예측 결과
        """
        if model_name not in self.models:
            raise ValueError(f"모델 '{model_name}'이 존재하지 않습니다.")
        
        model_instance = self.models[model_name]['model']
        return model_instance.predict(X)
    
    def predict_proba(self, model_name: str, X: pd.DataFrame) -> np.ndarray:
        """
        예측 확률 반환 (분류 모델만)
        
        Args:
            model_name: 모델명
            X: 예측 데이터
            
        Returns:
            예측 확률
        """
        if model_name not in self.models:
            raise ValueError(f"모델 '{model_name}'이 존재하지 않습니다.")
        
        model_instance = self.models[model_name]['model']
        return model_instance.predict_proba(X)
    
    def save_model(self, model_name: str, save_name: str = None) -> str:
        """
        모델 저장
        
        Args:
            model_name: 모델명
            save_name: 저장할 이름 (None이면 model_name 사용)
            
        Returns:
            저장된 모델 경로
        """
        if model_name not in self.models:
            raise ValueError(f"모델 '{model_name}'이 존재하지 않습니다.")
        
        if save_name is None:
            save_name = model_name
        
        model_instance = self.models[model_name]['model']
        return model_instance.save_model(save_name)
    
    def load_model(self, model_type: str, model_name: str, 
                  model_path: str, task_type: str = 'regression') -> bool:
        """
        모델 로드
        
        Args:
            model_type: 모델 타입
            model_name: 모델명
            model_path: 모델 파일 경로
            task_type: 태스크 타입
            
        Returns:
            로드 성공 여부
        """
        try:
            # 모델 인스턴스 생성
            if not self.create_model(model_type, model_name, task_type):
                return False
            
            # 모델 로드
            model_instance = self.models[model_name]['model']
            model_instance.load_model(model_path)
            
            self.models[model_name]['loaded_from'] = model_path
            self.models[model_name]['loaded_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return True
            
        except Exception as e:
            print(f"모델 로드 중 오류 발생: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        모델 정보 반환
        
        Args:
            model_name: 모델명
            
        Returns:
            모델 정보
        """
        if model_name not in self.models:
            raise ValueError(f"모델 '{model_name}'이 존재하지 않습니다.")
        
        model_data = self.models[model_name]
        model_instance = model_data['model']
        
        info = model_instance.get_model_info()
        info.update({
            'manager_info': {
                'model_name': model_name,
                'created_at': model_data.get('created_at'),
                'last_trained': model_data.get('last_trained'),
                'trained': model_data.get('trained', False),
                'loaded_from': model_data.get('loaded_from'),
                'loaded_at': model_data.get('loaded_at')
            }
        })
        
        return info
    
    def get_feature_importance(self, model_name: str, plot: bool = False) -> pd.DataFrame:
        """
        피처 중요도 반환
        
        Args:
            model_name: 모델명
            plot: 시각화 여부
            
        Returns:
            피처 중요도 데이터프레임
        """
        if model_name not in self.models:
            raise ValueError(f"모델 '{model_name}'이 존재하지 않습니다.")
        
        model_instance = self.models[model_name]['model']
        
        # 피처 중요도 지원 여부 확인
        if hasattr(model_instance, 'get_feature_importance'):
            return model_instance.get_feature_importance(plot=plot)
        else:
            raise ValueError(f"모델 '{model_name}'은 피처 중요도를 지원하지 않습니다.")
    
    def hyperparameter_tuning(self, model_name: str, df: pd.DataFrame,
                             target_col: str, **kwargs) -> Dict[str, Any]:
        """
        하이퍼파라미터 튜닝
        
        Args:
            model_name: 모델명
            df: 훈련 데이터
            target_col: 타겟 변수
            **kwargs: 튜닝 파라미터
            
        Returns:
            튜닝 결과
        """
        if model_name not in self.models:
            raise ValueError(f"모델 '{model_name}'이 존재하지 않습니다.")
        
        model_instance = self.models[model_name]['model']
        return model_instance.hyperparameter_tuning(df, target_col, **kwargs)
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        등록된 모델 목록 반환
        
        Returns:
            모델 목록
        """
        model_list = []
        for name, data in self.models.items():
            model_list.append({
                'name': name,
                'type': data['type'],
                'task_type': data['task_type'],
                'created_at': data.get('created_at'),
                'last_trained': data.get('last_trained'),
                'trained': data.get('trained', False)
            })
        return model_list
    
    def list_saved_models(self, model_type: str = None) -> List[Dict[str, Any]]:
        """
        저장된 모델 목록 반환
        
        Args:
            model_type: 모델 타입 (옵션)
            
        Returns:
            저장된 모델 목록
        """
        return get_available_models(model_type)
    
    def delete_model(self, model_name: str) -> bool:
        """
        모델 삭제
        
        Args:
            model_name: 모델명
            
        Returns:
            삭제 성공 여부
        """
        if model_name not in self.models:
            return False
        
        del self.models[model_name]
        return True
    
    def set_active_model(self, model_name: str) -> bool:
        """
        활성 모델 설정
        
        Args:
            model_name: 모델명
            
        Returns:
            설정 성공 여부
        """
        if model_name not in self.models:
            return False
        
        self.active_model = model_name
        return True
    
    def get_active_model(self) -> Optional[str]:
        """
        활성 모델 반환
        
        Returns:
            활성 모델명
        """
        return self.active_model
    
    def compare_models(self, model_names: List[str]) -> Dict[str, Any]:
        """
        모델 성능 비교
        
        Args:
            model_names: 비교할 모델명 리스트
            
        Returns:
            비교 결과
        """
        comparison = {}
        
        for name in model_names:
            if name in self.models:
                model_info = self.get_model_info(name)
                comparison[name] = {
                    'type': model_info.get('model_type'),
                    'task_type': model_info.get('task_type'),
                    'metrics': model_info.get('metrics', {})
                }
        
        return comparison
    
    def get_model_recommendations(self, df: pd.DataFrame, 
                                 target_col: str) -> List[Dict[str, Any]]:
        """
        데이터에 적합한 모델 추천
        
        Args:
            df: 데이터프레임
            target_col: 타겟 변수
            
        Returns:
            추천 모델 리스트
        """
        recommendations = []
        
        # 데이터 크기 확인
        n_samples, n_features = df.shape
        
        # 타겟 변수 타입 확인
        target_type = 'regression' if pd.api.types.is_numeric_dtype(df[target_col]) else 'classification'
        
        # 추천 로직
        if n_samples < 1000:
            # 소규모 데이터
            recommendations.append({
                'model_type': 'random_forest',
                'reason': '소규모 데이터에 적합하며 해석 가능한 모델',
                'priority': 1
            })
            recommendations.append({
                'model_type': 'svr',
                'reason': '소규모 데이터에서 좋은 성능을 보이는 모델',
                'priority': 2
            })
        else:
            # 대규모 데이터
            if XGBOOST_AVAILABLE:
                recommendations.append({
                    'model_type': 'xgboost',
                    'reason': '대규모 데이터에서 우수한 성능을 보이는 모델',
                    'priority': 1
                })
                recommendations.append({
                    'model_type': 'random_forest',
                    'reason': '안정적인 성능과 해석 가능성',
                    'priority': 2
                })
            else:
                recommendations.append({
                    'model_type': 'random_forest',
                    'reason': '안정적인 성능과 해석 가능성',
                    'priority': 1
                })
        
        if n_features > 10:
            recommendations.append({
                'model_type': 'neural_network',
                'reason': '고차원 데이터에서 복잡한 패턴 학습 가능',
                'priority': 3
            })
        
        # 우선순위 정렬
        recommendations.sort(key=lambda x: x['priority'])
        
        return recommendations 