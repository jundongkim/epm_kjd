"""
DX-AI Manufacturing Copilot - 제품 예측 모델링 페이지

예측 모델 구축 및 AI 보고서 생성 페이지입니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from src.core.chat_manager import ChatManager, setup_chat_sidebar
from src.core.tab_chat_managers import (
    ProductModelingChatManager,
    ProductReportChatManager
)


def product_modeling_page():
    """제품 예측 모델링 페이지"""
    st.markdown("## 🤖 제품 예측 모델링")
    
    def _safe_feature_importance_to_dict(feature_importance):
        """피처 중요도 데이터를 안전하게 dict로 변환"""
        # None 체크
        if feature_importance is None:
            return {}
        
        # pandas 객체인 경우 .empty 사용
        if hasattr(feature_importance, 'empty') and feature_importance.empty:
            return {}
        
        # dict인 경우 빈 dict 체크
        if isinstance(feature_importance, dict):
            if len(feature_importance) == 0:
                return {}
            else:
                return feature_importance
        
        # pandas Series/DataFrame인 경우 to_dict() 사용
        if hasattr(feature_importance, 'to_dict'):
            # Series인 경우 바로 to_dict() 사용
            if hasattr(feature_importance, 'index'):
                return feature_importance.to_dict()
            else:
                return feature_importance
        else:
            return feature_importance
    
    # ChatManager 인스턴스 생성
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = ChatManager()
    
    chat_manager = st.session_state.chat_manager
    
    # 예측 모델링 전용 챗봇 매니저 초기화
    if 'product_modeling_chat' not in st.session_state:
        st.session_state.product_modeling_chat = ProductModelingChatManager(chat_manager)
    
    if 'product_report_chat' not in st.session_state:
        st.session_state.product_report_chat = ProductReportChatManager(chat_manager)
    
    # 사이드바에 챗봇 설정 추가
    setup_chat_sidebar(chat_manager)
    
    tab1, tab2 = st.tabs(["🤖 예측 모델", "📋 AI 보고서"])
    
    with tab1:
        modeling_tab(_safe_feature_importance_to_dict)
    
    with tab2:
        report_tab(_safe_feature_importance_to_dict)


def modeling_tab(safe_feature_importance_to_dict):
    """예측 모델 구축 탭"""
    st.markdown("### 🤖 예측 모델 구축")
    
    # ModelManager 초기화
    if 'model_manager' not in st.session_state:
        from src.ml_models import ModelManager
        st.session_state.model_manager = ModelManager()
    
    # 훈련 데이터 확인
    training_data, using_preprocessed_data, preprocessing_info = _get_training_data()
    
    if training_data is None:
        training_data = _create_sample_data()
    
    # 모델 구축 섹션
    col1, col2 = st.columns([1, 1])
    
    with col1:
        _display_model_configuration(training_data)
    
    with col2:
        _display_model_performance(training_data, using_preprocessed_data, preprocessing_info)
    
    # ChatBot 인터페이스 추가
    _create_modeling_chat_interface(training_data, using_preprocessed_data, preprocessing_info)


def report_tab(safe_feature_importance_to_dict):
    """AI 보고서 생성 탭"""
    st.markdown("### 📋 GenAI 보고서 생성")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        _display_report_configuration()
    
    with col2:
        _display_ai_settings()
    
    # ChatBot 인터페이스 추가
    _create_report_chat_interface(safe_feature_importance_to_dict)


def _get_training_data():
    """훈련 데이터 확인 및 반환"""
    training_data = None
    using_preprocessed_data = False
    preprocessing_info = None
    
    # 1. 전처리된 데이터가 있는 경우 우선 사용
    if 'processed_data' in st.session_state:
        training_data = st.session_state.processed_data
        using_preprocessed_data = True
        preprocessing_info = st.session_state.get('preprocessing_results', {})
        st.success("✅ 전처리된 데이터를 사용합니다.")
        
        # 전처리 정보 표시
        if preprocessing_info:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("전처리된 데이터 크기", f"{preprocessing_info.final_shape[0]} × {preprocessing_info.final_shape[1]}")
            with col2:
                st.metric("제거된 컬럼 수", len(preprocessing_info.removed_columns))
            with col3:
                st.metric("처리 단계 수", len(preprocessing_info.steps))
            
            # 전처리 경고사항 표시
            if preprocessing_info.warnings:
                with st.expander("⚠️ 전처리 주의사항"):
                    for warning in preprocessing_info.warnings:
                        st.warning(warning)
    
    # 2. 원본 분석 데이터 사용
    elif 'analysis_data' in st.session_state:
        training_data = st.session_state.analysis_data
        st.warning("⚠️ 원본 데이터를 사용합니다. 데이터 분석 페이지에서 전처리를 권장합니다.")
        
        # 전처리 추천 메시지
        st.info("💡 더 나은 모델 성능을 위해 **제품 데이터 분석** 페이지에서 데이터 전처리를 먼저 수행하세요.")
        
    # 3. 업로드된 데이터 사용
    elif 'uploaded_data' in st.session_state:
        training_data = st.session_state.uploaded_data
        st.warning("⚠️ 업로드된 원본 데이터를 사용합니다. 데이터 분석 페이지에서 전처리를 권장합니다.")
    
    return training_data, using_preprocessed_data, preprocessing_info


def _create_sample_data():
    """예시 데이터 생성"""
    st.warning("⚠️ 먼저 데이터 분석 페이지에서 데이터를 업로드해주세요.")
    st.markdown("#### 📊 예시 데이터로 진행")
    
    # 예시 데이터 생성
    np.random.seed(42)
    training_data = pd.DataFrame({
        "온도": np.random.uniform(150, 200, 50),
        "압력": np.random.uniform(1.5, 3.0, 50),
        "pH": np.random.uniform(6.5, 8.5, 50),
        "순도": np.random.uniform(95, 99, 50),
        "수율": np.random.uniform(85, 98, 50)
    })
    
    st.session_state.analysis_data = training_data
    st.info("📊 예시 데이터로 모델 훈련을 진행합니다.")
    
    return training_data


def _display_model_configuration(training_data):
    """모델 설정 표시"""
    st.markdown("#### 🛠️ 모델 설정")
    
    # 모델 타입 매핑
    model_type_mapping = {
        "Random Forest": "random_forest",
        "Neural Network": "neural_network",
        "SVR": "svr"
    }
    
    # XGBoost가 사용 가능한 경우에만 추가
    if st.session_state.get('xgboost_available', False):
        model_type_mapping["XGBoost"] = "xgboost"
    else:
        st.info("💡 XGBoost 모델: OpenMP 런타임 설치 필요 (`brew install libomp`)")
    
    # CatBoost가 사용 가능한 경우에만 추가
    if st.session_state.get('catboost_available', False):
        model_type_mapping["CatBoost"] = "catboost"
    else:
        st.info("💡 CatBoost 모델: `pip install catboost` 설치 필요")
    
    model_type_display = st.selectbox("모델 유형", list(model_type_mapping.keys()))
    model_type = model_type_mapping[model_type_display]
    
    # 수치형 컬럼 필터링
    numeric_cols = _get_numeric_columns(training_data)
    
    if len(numeric_cols) == 0:
        st.error("❌ 수치형 컬럼이 없습니다. 데이터를 확인해주세요.")
        return
    
    target_variable = st.selectbox("예측 변수", numeric_cols)
    
    # 세션 상태에 저장 (tab2에서 사용하기 위해)
    st.session_state.current_target_variable = target_variable
    st.session_state.current_model_type = model_type
    
    # 모델명 입력
    model_name = st.text_input("모델명", f"{model_type_display}_{target_variable}")
    
    # 하이퍼파라미터 설정
    params = _get_hyperparameters(model_type)
    
    # 모델 훈련
    if st.button("🚀 모델 훈련", type="primary", key="train_model"):
        _train_model(training_data, model_type, model_name, target_variable, params)


def _get_numeric_columns(training_data):
    """수치형 컬럼 필터링"""
    def is_date_like(series: pd.Series) -> bool:
        """시리즈가 날짜 형식인지 확인"""
        if series.dtype == 'object':
            sample_size = min(10, len(series))
            sample_values = series.dropna().head(sample_size)
            
            date_count = 0
            for value in sample_values:
                if isinstance(value, str):
                    try:
                        pd.to_datetime(value, errors='raise')
                        date_count += 1
                    except (ValueError, TypeError):
                        continue
            
            return date_count / len(sample_values) >= 0.5 if len(sample_values) > 0 else False
        return False
    
    # 수치형 컬럼 필터링
    numeric_cols = []
    for col in training_data.columns:
        if pd.api.types.is_numeric_dtype(training_data[col]) and not is_date_like(training_data[col]):
            try:
                pd.to_numeric(training_data[col], errors='raise')
                numeric_cols.append(col)
            except (ValueError, TypeError):
                continue
    
    return numeric_cols


def _get_hyperparameters(model_type):
    """하이퍼파라미터 설정"""
    st.markdown("**하이퍼파라미터 설정:**")
    
    params = {}
    if model_type == "random_forest":
        params['n_estimators'] = st.slider("트리 개수", 10, 200, 100)
        params['max_depth'] = st.slider("최대 깊이", 3, 20, 10)
        params['min_samples_split'] = st.slider("분할 최소 샘플", 2, 10, 2)
        
    elif model_type == "xgboost":
        params['n_estimators'] = st.slider("트리 개수", 100, 2000, 1000)
        params['max_depth'] = st.slider("최대 깊이", 3, 10, 6)
        params['learning_rate'] = st.slider("학습률", 0.01, 0.5, 0.1)
        
        col1_xgb, col2_xgb = st.columns(2)
        with col1_xgb:
            params['use_core_api'] = st.checkbox("Core API 사용", value=False)
        with col2_xgb:
            early_stopping = st.checkbox("조기 종료 사용", value=True)
            if early_stopping:
                params['early_stopping_rounds'] = st.slider("조기 종료 라운드", 10, 100, 50)
            else:
                params['early_stopping_rounds'] = None
        
    elif model_type == "catboost":
        params['iterations'] = st.slider("반복 횟수", 100, 2000, 1000)
        params['depth'] = st.slider("최대 깊이", 3, 10, 6)
        params['learning_rate'] = st.slider("학습률", 0.01, 0.3, 0.01)
        params['early_stopping_rounds'] = st.slider("조기 중단 라운드", 10, 100, 20)
        params['use_best_model'] = st.checkbox("최적 모델 사용", value=True)
        
    elif model_type == "neural_network":
        layer_sizes = st.selectbox("은닉층 구조", 
                                 ["(100,)", "(50, 50)", "(100, 50)", "(100, 100, 50)"])
        params['hidden_layer_sizes'] = eval(layer_sizes)
        params['activation'] = st.selectbox("활성화 함수", ["relu", "tanh", "logistic"])
        params['learning_rate_init'] = st.slider("초기 학습률", 0.0001, 0.01, 0.001)
        
    elif model_type == "svr":
        params['kernel'] = st.selectbox("커널", ["rbf", "linear", "poly"])
        params['C'] = st.slider("C (정규화)", 0.1, 100.0, 1.0)
        params['epsilon'] = st.slider("엡실론", 0.01, 0.5, 0.1)
    
    params['test_size'] = 1.0 - st.slider("훈련 데이터 비율", 0.6, 0.9, 0.8)
    
    return params


def _train_model(training_data, model_type, model_name, target_variable, params):
    """모델 훈련 실행"""
    try:
        # 데이터 정리
        clean_data = training_data.copy()
        
        # 문제가 있는 컬럼 제거
        cols_to_remove = []
        for col in clean_data.columns:
            if col != target_variable and clean_data[col].dtype == 'object':
                sample_val = clean_data[col].dropna().iloc[0] if not clean_data[col].dropna().empty else None
                if sample_val is not None:
                    try:
                        pd.to_datetime(str(sample_val), errors='raise')
                        cols_to_remove.append(col)
                        st.warning(f"🗑️ 날짜 형식 컬럼 '{col}' 제거됨")
                    except:
                        try:
                            float(str(sample_val))
                        except:
                            cols_to_remove.append(col)
                            st.warning(f"🗑️ 문자열 컬럼 '{col}' 제거됨")
        
        if cols_to_remove:
            clean_data = clean_data.drop(columns=cols_to_remove)
        
        # 모델 생성
        success = st.session_state.model_manager.create_model(
            model_type, model_name, 'regression'
        )
        
        if success:
            # 모델 훈련
            result = st.session_state.model_manager.train_model(
                model_name, clean_data, target_variable, 
                show_progress=True, **params
            )
            
            # 결과 저장
            st.session_state.last_training_result = result
            st.session_state.active_model = model_name
            
            st.success("✅ 모델 훈련 완료!")
            
            # 모델 저장
            saved_path = st.session_state.model_manager.save_model(model_name)
            st.info(f"💾 모델이 저장되었습니다: {saved_path}")
            
        else:
            st.error("❌ 모델 생성에 실패했습니다.")
            
    except Exception as e:
        st.error(f"❌ 모델 훈련 중 오류가 발생했습니다: {str(e)}")


def _display_model_performance(training_data, using_preprocessed_data, preprocessing_info):
    """모델 성능 표시"""
    st.markdown("#### 📊 모델 성능")
    
    # 훈련 결과 표시
    if 'last_training_result' in st.session_state:
        result = st.session_state.last_training_result
        metrics = result['metrics']
        
        _display_performance_metrics(metrics)
        _display_learning_curve(result)
        _display_feature_importance(result)
        _display_prediction_scatter(result)
        
    else:
        st.info("🤖 모델을 훈련하면 성능 지표가 여기에 표시됩니다.")
    
    # 예측 수행
    _display_prediction_section(training_data)


def _display_performance_metrics(metrics):
    """성능 지표 표시"""
    st.markdown("**모델 성능 지표:**")
    
    col2_1, col2_2 = st.columns(2)
    
    with col2_1:
        st.metric("R² Score", f"{metrics['r2_score']:.4f}")
        st.metric("RMSE", f"{metrics['rmse']:.4f}")
        
    with col2_2:
        st.metric("MAE", f"{metrics['mae']:.4f}")
        st.metric("MSE", f"{metrics['mse']:.4f}")


def _display_learning_curve(result):
    """학습 곡선 표시"""
    st.markdown("**학습 곡선:**")
    
    if 'training_history' in result and result['training_history']:
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            
            training_history = result['training_history']
            
            if isinstance(training_history, dict):
                fig_learning = go.Figure()
                
                if 'tree_counts' in training_history:
                    tree_counts = training_history['tree_counts']
                    
                    if 'train' in training_history:
                        train_rmse = training_history['train'].get('rmse', [])
                        if train_rmse:
                            fig_learning.add_trace(go.Scatter(
                                x=tree_counts,
                                y=train_rmse,
                                mode='lines+markers',
                                name='Train RMSE',
                                line=dict(color='blue')
                            ))
                    
                    if 'test' in training_history:
                        test_rmse = training_history['test'].get('rmse', [])
                        if test_rmse:
                            fig_learning.add_trace(go.Scatter(
                                x=tree_counts,
                                y=test_rmse,
                                mode='lines+markers',
                                name='Test RMSE',
                                line=dict(color='red')
                            ))
                    
                    fig_learning.update_layout(
                        title='학습 곡선 (RMSE vs Trees)',
                        xaxis_title='Number of Trees',
                        yaxis_title='RMSE',
                        height=400,
                        showlegend=True
                    )
                
                st.plotly_chart(fig_learning, use_container_width=True)
        
        except Exception as e:
            st.info(f"📊 학습 곡선 표시 중 오류: {str(e)}")


def _display_feature_importance(result):
    """피처 중요도 표시"""
    if 'feature_importance' in result:
        st.markdown("**피처 중요도 (Top 5):**")
        importance_df = result['feature_importance'].head(5)
        
        try:
            import plotly.express as px
            fig_importance = px.bar(
                importance_df, 
                x='importance', 
                y='feature',
                orientation='h',
                title='피처 중요도'
            )
            fig_importance.update_layout(height=300)
            st.plotly_chart(fig_importance, use_container_width=True)
        except:
            st.dataframe(importance_df)


def _display_prediction_scatter(result):
    """예측 vs 실제 값 산점도 표시"""
    st.markdown("**예측 vs 실제 값:**")
    pred_actual_df = pd.DataFrame({
        '실제값': result['test_actual'],
        '예측값': result['test_predictions']
    })
    
    try:
        import plotly.express as px
        fig_scatter = px.scatter(
            pred_actual_df, 
            x='실제값', 
            y='예측값',
            title='예측 vs 실제 값'
        )
        fig_scatter.add_shape(
            type="line",
            x0=pred_actual_df['실제값'].min(),
            y0=pred_actual_df['실제값'].min(),
            x1=pred_actual_df['실제값'].max(),
            y1=pred_actual_df['실제값'].max(),
            line=dict(color="red", dash="dash")
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    except:
        st.line_chart(pred_actual_df)


def _display_prediction_section(training_data):
    """예측 수행 섹션"""
    st.markdown("#### 🎯 예측 수행")
    
    if 'active_model' in st.session_state:
        feature_names = st.session_state.last_training_result.get('feature_names', [])
        
        if feature_names:
            st.markdown("**예측을 위한 입력값:**")
            
            input_data = {}
            for feature in feature_names:
                if feature in training_data.columns:
                    min_val = float(training_data[feature].min())
                    max_val = float(training_data[feature].max())
                    mean_val = float(training_data[feature].mean())
                    
                    input_data[feature] = st.number_input(
                        f"{feature}",
                        min_value=min_val,
                        max_value=max_val,
                        value=mean_val,
                        help=f"범위: {min_val:.2f} ~ {max_val:.2f}"
                    )
            
            if st.button("🔮 예측 실행", key="predict_execute"):
                _execute_prediction(input_data)
        else:
            st.warning("⚠️ 먼저 모델을 훈련해주세요.")
    else:
        st.info("🤖 먼저 모델을 훈련해주세요.")


def _execute_prediction(input_data):
    """예측 실행"""
    try:
        pred_df = pd.DataFrame([input_data])
        prediction = st.session_state.model_manager.predict(
            st.session_state.active_model, pred_df
        )
        
        target_variable = st.session_state.current_target_variable
        st.success(f"📊 예측 {target_variable}: {prediction[0]:.2f}")
        
        # 신뢰구간 계산
        metrics = st.session_state.last_training_result['metrics']
        rmse = metrics['rmse']
        confidence_interval = 1.96 * rmse
        
        st.info(f"🎯 95% 신뢰구간: {prediction[0] - confidence_interval:.2f} ~ {prediction[0] + confidence_interval:.2f}")
        
    except Exception as e:
        st.error(f"❌ 예측 중 오류가 발생했습니다: {str(e)}")


def _display_report_configuration():
    """보고서 설정 표시"""
    st.markdown("#### 📝 보고서 설정")
    
    report_type = st.selectbox("보고서 유형", ["실험 계획 요약", "결과 분석", "최적화 제안", "종합 보고서"])
    
    include_sections = st.multiselect(
        "포함할 섹션",
        ["실행 요약", "실험 설계", "데이터 분석", "결과 해석", "개선 제안", "다음 단계"],
        default=["실행 요약", "결과 해석", "개선 제안"]
    )
    
    report_length = st.selectbox("보고서 길이", ["간단 (1-2페이지)", "표준 (3-5페이지)", "상세 (5-10페이지)"])
    
    if st.button("📄 AI 보고서 생성", type="primary", key="generate_ai_report"):
        _generate_ai_report(report_type, include_sections, report_length)


def _generate_ai_report(report_type, include_sections, report_length):
    """AI 보고서 생성"""
    with st.spinner("AI가 보고서를 생성 중입니다..."):
        time.sleep(3)
        
        st.success("✅ AI 보고서 생성 완료!")
        
        # 예시 보고서
        st.markdown("---")
        st.markdown("## 📋 제품 예측 모델링 보고서")
        st.markdown("**생성일**: 2024-01-15")
        st.markdown("**분석 대상**: 제품 예측 모델링 결과")
        
        st.markdown("""
        ### 🔍 실행 요약
        본 예측 모델링에서는 제품 품질 예측을 위한 머신러닝 모델을 구축했습니다.
        주요 성과는 다음과 같습니다:
        
        - 예측 정확도 R² Score: 0.85 이상 달성
        - 온도가 품질에 가장 큰 영향 (중요도: 0.42)
        - 압력과 pH의 상호작용 효과 확인
        
        ### 📊 결과 해석
        Random Forest 모델이 가장 우수한 성능을 보였으며, 과적합 없이 안정적인 예측을 제공합니다.
        RMSE 값이 낮아 실제 운영 환경에서 활용 가능한 수준입니다.
        
        ### 💡 개선 제안
        1. 더 많은 훈련 데이터 확보로 모델 성능 향상
        2. 특성 공학(Feature Engineering) 적용
        3. 앙상블 모델 고려
        4. 실시간 예측 시스템 구축
        
        ### 📋 다음 단계
        - 모델 배포 및 운영 환경 구축
        - 지속적인 모델 모니터링 및 재훈련
        - 추가 데이터 수집 계획 수립
        """)


def _display_ai_settings():
    """AI 모델 설정 표시"""
    st.markdown("#### 🤖 AI 모델 설정")
    
    llm_model = st.selectbox("LLM 모델", ["Gemma 3 (12B-QAT)", "Gemma 3 (27B-QAT)", "Gemini 2.5 Pro"])
    
    temperature = st.slider("창의성", 0.0, 1.0, 0.3, 0.1)
    max_length = st.slider("최대 길이", 500, 3000, 1500, 100)
    
    st.markdown("#### 📄 보고서 템플릿")
    st.markdown("""
    **포함 요소:**
    - 📊 모델 성능 지표
    - 📈 학습 곡선 분석
    - 🔍 피처 중요도 해석
    - 💡 최적화 제안
    - 📋 운영 계획
    """)


def _create_modeling_chat_interface(training_data, using_preprocessed_data, preprocessing_info):
    """예측 모델링 챗봇 인터페이스 생성"""
    st.markdown("---")
    
    # 예측 모델링 전용 챗봇 매니저 사용
    modeling_chat_manager = st.session_state.product_modeling_chat
    
    # Context 데이터 업데이트
    if 'last_training_result' in st.session_state:
        result = st.session_state.last_training_result
        metrics = result['metrics']
        
        # 세션 상태에서 변수 가져오기
        model_type = st.session_state.get('current_model_type', 'Unknown')
        model_name = st.session_state.get('active_model', 'Unknown')
        target_variable = st.session_state.get('current_target_variable', 'Unknown')
        
        context_data = {
            'model_info': {
                'model_type': model_type,
                'model_name': model_name,
                'target_variable': target_variable,
                'feature_names': result.get('feature_names', []),
                'performance_metrics': metrics
            },
            'training_data': {
                'shape': training_data.shape,
                'columns': list(training_data.columns),
                'summary': training_data.describe().to_dict()
            }
        }
        
        # 전처리 정보 추가
        if using_preprocessed_data and preprocessing_info:
            context_data['preprocessing_info'] = {
                'used_preprocessed_data': True,
                'original_shape': preprocessing_info.original_shape,
                'final_shape': preprocessing_info.final_shape,
                'removed_columns': preprocessing_info.removed_columns,
                'preprocessing_steps': preprocessing_info.steps,
                'warnings': preprocessing_info.warnings,
                'has_outliers': preprocessing_info.outlier_info is not None,
                'has_high_correlation': preprocessing_info.high_correlation_pairs is not None
            }
        else:
            context_data['preprocessing_info'] = {
                'used_preprocessed_data': False,
                'recommendation': "데이터 분석 페이지에서 전처리를 수행하면 더 나은 모델 성능을 얻을 수 있습니다."
            }
        
        if 'feature_importance' in result:
            # 피처 중요도 데이터 안전하게 처리
            feature_importance = result['feature_importance']
            if hasattr(feature_importance, 'to_dict'):
                # Series인 경우 바로 to_dict() 사용
                if hasattr(feature_importance, 'index'):
                    context_data['feature_importance'] = feature_importance.to_dict()
                else:
                    context_data['feature_importance'] = feature_importance
            else:
                context_data['feature_importance'] = feature_importance
        
        modeling_chat_manager.update_context_data(context_data, "현재 세션")
    else:
        modeling_chat_manager.update_context_data({}, "현재 세션")
    
    # 탭별 챗봇 인터페이스 생성
    modeling_chat_manager.create_chat_interface()


def _create_report_chat_interface(safe_feature_importance_to_dict):
    """보고서 생성 챗봇 인터페이스 생성"""
    st.markdown("---")
    
    # 보고서 생성 전용 챗봇 매니저 사용
    report_chat_manager = st.session_state.product_report_chat
    
    # Context 데이터 업데이트
    if 'last_training_result' in st.session_state:
        result = st.session_state.last_training_result
        metrics = result['metrics']
        
        # 세션 상태에서 변수 가져오기
        current_target_variable = st.session_state.get('current_target_variable', 'Unknown')
        current_model_type = st.session_state.get('current_model_type', 'Unknown')
        
        # 훈련 데이터 가져오기
        training_data = st.session_state.get('processed_data')
        if training_data is None:
            training_data = st.session_state.get('analysis_data')
        
        context_data = {
            'model_results': {
                'model_type': current_model_type,
                'performance_metrics': metrics,
                'feature_importance': safe_feature_importance_to_dict(result.get('feature_importance', {})) if 'feature_importance' in result else {},
                'training_completed': True
            },
            'data_context': {
                'data_shape': training_data.shape if training_data is not None else (0, 0),
                'target_variable': current_target_variable,
                'features_count': len(result.get('feature_names', [])) if 'feature_names' in result else 0
            }
        }
        
        # 전처리 정보 추가
        if 'preprocessing_results' in st.session_state:
            preprocessing_info = st.session_state.preprocessing_results
            context_data['preprocessing_info'] = {
                'used_preprocessed_data': True,
                'original_shape': preprocessing_info.original_shape,
                'final_shape': preprocessing_info.final_shape,
                'removed_columns': preprocessing_info.removed_columns,
                'preprocessing_steps': preprocessing_info.steps,
                'warnings': preprocessing_info.warnings,
                'data_quality_improvements': True
            }
        else:
            context_data['preprocessing_info'] = {
                'used_preprocessed_data': False,
                'data_quality_improvements': False,
                'recommendation': "전처리된 데이터를 사용하면 보고서에 더 상세한 데이터 품질 정보를 포함할 수 있습니다."
            }
        
        report_chat_manager.update_context_data(context_data, "현재 세션")
    else:
        report_chat_manager.update_context_data({}, "현재 세션")
    
    # 탭별 챗봇 인터페이스 생성
    report_chat_manager.create_chat_interface() 