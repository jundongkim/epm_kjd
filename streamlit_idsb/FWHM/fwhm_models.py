import streamlit as st
import pandas as pd
import os
import catboost as cbm
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np
import time
import base64 # Import standard base64 module
import plotly.graph_objects as go # Import Plotly for interactive charts
import plotly.express as px
from plotly.subplots import make_subplots
import json # For parsing evaluation results
from scipy.stats import uniform, randint # For parameter distributions

# --- Page Configuration ---
st.set_page_config(
    page_title="Model Training Comparison",
    page_icon="📊",
    layout="wide"
)

# --- Custom Font ---
# Check if font file exists at the project root level
font_path = "fonts/Paperlogy.ttf" # Assuming fonts folder is at the workspace root
# Use absolute path for checking existence based on workspace root
workspace_root = "/Users/kenny/GitHub/ecopro_idsb" # Inferring workspace root
absolute_font_path = os.path.join(workspace_root, font_path)

if os.path.exists(absolute_font_path):
    try:
        with open(absolute_font_path, "rb") as f:
            font_bytes = f.read()
        # Encode font bytes for CSS embedding using standard base64 module
        font_base64 = base64.b64encode(font_bytes).decode()
        # Inject custom CSS for the font with !important flag
        st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'Paperlogy';
            src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        }}
        html, body, [class*="st-"], .stApp, button, input, select, textarea, .stButton>button, .stSelectbox select, .stTextInput input, .stTextArea textarea {{
            font-family: 'Paperlogy', sans-serif !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"폰트 파일 ({absolute_font_path})을 로드하는 중 오류 발생: {e}. 기본 폰트를 사용합니다.")
else:
    st.warning(f"폰트 파일 '{absolute_font_path}'을(를) 찾을 수 없습니다. 프로젝트 루트에 'fonts/Paperlogy.ttf' 파일이 있는지 확인해주세요. 기본 폰트를 사용합니다.")


# --- App Title ---
st.title("📊 FWHM 데이터 모델링 비교 분석")
st.markdown("CatBoost와 XGBoost 모델의 학습 및 성능을 비교합니다.")

# --- Sidebar ---
st.sidebar.header("⚙️ 설정")

# --- Data Selection ---
st.sidebar.subheader("1. 데이터 선택")
fwhm_folder = os.path.dirname(os.path.abspath(__file__)) # Get the directory of the script
csv_files = [f for f in os.listdir(fwhm_folder) if f.endswith('.csv')]

if not csv_files:
    st.error(f"'{fwhm_folder}' 폴더에 CSV 파일이 없습니다. CSV 파일을 폴더에 추가해주세요.")
    st.stop()

selected_file = st.sidebar.selectbox("CSV 파일 선택", csv_files)
file_path = os.path.join(fwhm_folder, selected_file)

# --- Data Loading ---
@st.cache_data # Cache data loading
def load_data(path):
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        st.error(f"데이터 로딩 오류: {e}")
        return None

df = load_data(file_path)

if df is not None:
    st.subheader(f"📜 데이터 미리보기: `{selected_file}`")
    st.dataframe(df.head())

    # --- Feature and Target Selection ---
    st.sidebar.subheader("2. 변수 선택")
    columns = df.columns.tolist()
    default_target = columns[-1] if columns else None
    target_variable = st.sidebar.selectbox("🎯 타겟 변수 선택", columns, index=len(columns)-1 if columns else 0)

    if target_variable:
        feature_options = [col for col in columns if col != target_variable]
        selected_features = st.sidebar.multiselect("🧬 피처 변수 선택", feature_options, default=feature_options)
    else:
        selected_features = []

    if not target_variable or not selected_features:
        st.warning("타겟 변수와 하나 이상의 피처 변수를 선택해주세요.")
        st.stop()

    # Prepare data
    X = df[selected_features].copy() # Use copy to avoid SettingWithCopyWarning
    y = df[target_variable].copy()

    # --- Data Type Validation and Conversion ---
    st.sidebar.subheader("데이터 타입 확인 및 변환")
    numeric_features = []
    non_numeric_issues = []

    # Check and convert features
    for col in selected_features:
        try:
            # Attempt conversion to numeric, coercing errors to NaN
            original_type = X[col].dtype
            X[col] = pd.to_numeric(X[col], errors='coerce')
            if X[col].isnull().any():
                # If NaNs were introduced, it means there were non-numeric values
                nan_count = X[col].isnull().sum()
                non_numeric_issues.append(f"'{col}' (원래 타입: {original_type}): {nan_count}개의 숫자형 변환 불가 값 발견. NaN으로 처리됨.")
            numeric_features.append(col)
        except Exception as e:
            # Catch any other potential errors during conversion
            non_numeric_issues.append(f"'{col}' 처리 중 오류 발생: {e}")
            # Keep the original column but warn the user it might cause issues
            numeric_features.append(col) # Still include, model might handle or error later

    # Check and convert target variable
    try:
        original_target_type = y.dtype
        y = pd.to_numeric(y, errors='coerce')
        if y.isnull().any():
            nan_count = y.isnull().sum()
            st.error(f"🚨 타겟 변수 '{target_variable}' (원래 타입: {original_target_type})에 숫자형 변환 불가 값이 {nan_count}개 포함되어 있습니다. 모델 학습을 진행할 수 없습니다. 데이터를 확인해주세요.")
            st.stop() # Stop execution if target has non-numeric values
    except Exception as e:
        st.error(f"🚨 타겟 변수 '{target_variable}' 처리 중 심각한 오류 발생: {e}. 모델 학습을 진행할 수 없습니다.")
        st.stop()

    # Display warnings for features with non-numeric values
    if non_numeric_issues:
        st.warning("⚠️ **피처 변수 경고:**")
        for issue in non_numeric_issues:
            st.warning(issue)
        st.warning("➡️ 숫자형 변환 불가 값은 NaN으로 처리되었습니다. 모델 학습 전 결측치 처리가 필요할 수 있습니다 (현재는 평균값으로 대체). 식별자 등 불필요한 변수는 피처 선택에서 제외하는 것을 권장합니다.")
        # Simple Imputation (replace NaNs with mean for numeric columns)
        # More sophisticated imputation might be needed depending on the data
        for col in numeric_features:
            if X[col].isnull().any():
                mean_val = X[col].mean()
                X[col] = X[col].fillna(mean_val)
                st.info(f"'{col}'의 NaN 값이 평균값({mean_val:.4f})으로 대체되었습니다.")


    # Ensure we only use potentially converted numeric features for splitting
    X = X[numeric_features]


    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    st.sidebar.subheader("3. 모델 하이퍼파라미터")

    # Define placeholder for model results at the top of the script, before any model training
    # --- Model Results Storage ---
    # Initialize session state for model results if it doesn't exist
    if 'model_results' not in st.session_state:
        st.session_state.model_results = {}

    # Initialize session state for training buttons
    if 'cb_trained' not in st.session_state:
        st.session_state.cb_trained = False
    if 'xgb_trained' not in st.session_state:
        st.session_state.xgb_trained = False

    # --- Model Tabs ---
    tab1, tab2 = st.tabs(["🚀 CatBoost", "⚡ XGBoost"])

    # Use session state instead of regular dict
    model_params = {}
    training_logs = {}

    # --- CatBoost Tab ---
    with tab1:
        st.header("🚀 CatBoost 설정 및 학습")
        
        # Check if parameters should be updated from optimization
        if 'cb_apply_requested' in st.session_state and st.session_state.cb_apply_requested:
            # Reset the flag
            st.session_state.cb_apply_requested = False
            
            if 'catboost_best_params' in st.session_state:
                best_params = st.session_state.catboost_best_params
                # Update session state for sliders before rendering them
                st.session_state.cb_lr = best_params['learning_rate']
                st.session_state.cb_depth = int(best_params['depth'])
                st.success("최적 파라미터가 하이퍼파라미터 설정에 적용되었습니다!")
        
        with st.expander("하이퍼파라미터 설정", expanded=True):
            # Default values from 2_training_catboost.py
            cb_iterations = st.slider("Iterations", 100, 2000, 1000, 100, key="cb_iter")  # Default: 1000
            cb_learning_rate = st.slider("Learning Rate", 0.01, 0.5, 0.01, 0.01, key="cb_lr")  # Default: 0.01
            cb_depth = st.slider("Depth", 3, 10, 3, 1, key="cb_depth")  # Default: 3
            cb_loss_function_display = st.selectbox("Loss Function", ['RMSE', 'MAE', 'MAPE'], index=2, key="cb_loss")  # Default: MAPE
            
            # Map display names to actual CatBoost loss function names
            if cb_loss_function_display == 'RMSE':
                cb_loss_function = 'RMSE'
                cb_eval_metric = 'RMSE'
            elif cb_loss_function_display == 'MAE':
                cb_loss_function = 'MAE'
                cb_eval_metric = 'MAE'
            elif cb_loss_function_display == 'MAPE':
                cb_loss_function = 'MAPE'  # CatBoost에서 MAPE 직접 지원
                cb_eval_metric = 'MAPE'    # 평가도 MAPE 지표 사용
            else:
                cb_loss_function = 'RMSE'
                cb_eval_metric = 'RMSE'
                
            cb_early_stopping_rounds = st.slider("Early Stopping Rounds", 10, 100, 50, 10, key="cb_esr")  # Default: 50

        # Default model parameters from 2_training_catboost.py
        model_params['CatBoost'] = {
            'iterations': cb_iterations,
            'learning_rate': cb_learning_rate,
            'depth': cb_depth,
            'loss_function': cb_loss_function,
            'eval_metric': cb_eval_metric,  # 추가: 평가 지표
            'early_stopping_rounds': cb_early_stopping_rounds,
            'random_seed': 44,  # 2_training_catboost.py와 동일한 random_seed
            'verbose': 100,  # 100번째 반복마다 출력
            'task_type': 'CPU'  # CPU 모드 명시적 지정
        }

        # Check if we have previously optimized parameters
        have_optimized_params = 'catboost_best_params' in st.session_state and st.session_state.catboost_best_params
        
        if have_optimized_params:
            st.success("최적화된 파라미터를 사용할 수 있습니다.")
            use_optimized = st.checkbox("최적화된 파라미터 사용", value=False, key="cb_use_optimized")
            
            if use_optimized:
                # Update model parameters with optimized values
                best_params = st.session_state.catboost_best_params
                
                # Save original parameters to display the difference
                original_lr = model_params['CatBoost']['learning_rate']
                original_depth = model_params['CatBoost']['depth']
                
                # Update parameters
                model_params['CatBoost'].update({
                    'learning_rate': best_params['learning_rate'],
                    'depth': best_params['depth'],
                    'l2_leaf_reg': best_params.get('l2_leaf_reg', 3.0),
                    'random_strength': best_params.get('random_strength', 1.0),
                    'bagging_temperature': best_params.get('bagging_temperature', 1.0),
                    'grow_policy': best_params.get('grow_policy', 'SymmetricTree'),
                })
                
                # Display which parameters are being used, showing the changes
                st.info(f"""
                **최적 파라미터가 적용됨 (슬라이더 값과 다를 수 있음):**
                - 학습률(Learning Rate): {original_lr} → **{best_params['learning_rate']:.4f}**
                - 깊이(Depth): {original_depth} → **{best_params['depth']}**
                - 추가 파라미터:
                  - L2 Leaf Reg: {best_params.get('l2_leaf_reg', 3.0):.2f}
                  - Random Strength: {best_params.get('random_strength', 1.0):.2f}
                  - Bagging Temperature: {best_params.get('bagging_temperature', 1.0):.2f}
                  - Grow Policy: {best_params.get('grow_policy', 'SymmetricTree')}
                """)
                
                st.warning("슬라이더값은 변경되지 않았지만, 모델 학습에는 위 최적 파라미터가 사용됩니다.")
                
        # Create columns for buttons
        col1, col2 = st.columns(2)
        
        with col1:
            train_button = st.button("CatBoost 모델 학습 시작", key="cb_train")
            if train_button:
                st.session_state.cb_trained = True
            
        with col2:
            optimize_button = st.button("하이퍼파라미터 최적화", key="cb_optimize")

        # Hyperparameter optimization
        if optimize_button:
            st.subheader("⚙️ CatBoost 하이퍼파라미터 최적화 중")
            progress_bar_opt = st.progress(0)
            status_text_opt = st.empty()
            
            try:
                status_text_opt.text("하이퍼파라미터 최적화를 위한 탐색 공간 준비 중...")
                
                # Define parameter search space
                param_dist = {
                    'learning_rate': uniform(0.01, 0.3),
                    'depth': randint(3, 10),
                    'l2_leaf_reg': uniform(1, 10),
                    'random_strength': uniform(0, 10),
                    'bagging_temperature': uniform(0, 1),
                    'grow_policy': ['SymmetricTree', 'Depthwise'],
                }
                
                # Create CatBoost model for optimization
                catboost_opt = cbm.CatBoostRegressor(
                    iterations=300,  # Reduced for faster optimization
                    loss_function=cb_loss_function,
                    eval_metric=cb_eval_metric,  # 평가 지표 추가
                    random_seed=42,
                    verbose=False  # Disable verbose output during optimization
                )
                
                status_text_opt.text("랜덤 탐색을 통한 최적 파라미터 탐색 중...")
                progress_bar_opt.progress(20)
                
                # RandomizedSearchCV for hyperparameter optimization
                random_search = RandomizedSearchCV(
                    estimator=catboost_opt,
                    param_distributions=param_dist,
                    n_iter=100,  # Number of parameter settings sampled
                    cv=5,  # 3-fold cross-validation
                    verbose=0,
                    random_state=42,
                    n_jobs=-1  # Use all available cores
                )
                
                # Fit the random search
                random_search.fit(X_train, y_train)
                
                progress_bar_opt.progress(80)
                status_text_opt.text("최적 파라미터 적용 중...")
                
                # Get best parameters
                best_params = random_search.best_params_
                
                # Update model parameters without changing sliders
                model_params['CatBoost'].update({
                    'learning_rate': best_params['learning_rate'],
                    'depth': best_params['depth'],
                    'l2_leaf_reg': best_params.get('l2_leaf_reg', 3.0),
                    'random_strength': best_params.get('random_strength', 1.0),
                    'bagging_temperature': best_params.get('bagging_temperature', 1.0),
                    'grow_policy': best_params.get('grow_policy', 'SymmetricTree'),
                })
                
                progress_bar_opt.progress(100)
                status_text_opt.success("최적화 완료! 최적 파라미터가 계산되었습니다.")
                
                # Store best parameters in session state for later use
                if 'catboost_best_params' not in st.session_state:
                    st.session_state.catboost_best_params = {}
                st.session_state.catboost_best_params = best_params
                
                # Display best parameters
                st.info(f"""
                **최적 파라미터:**
                - Learning Rate: {best_params['learning_rate']:.4f}
                - Depth: {best_params['depth']}
                - L2 Leaf Reg: {best_params.get('l2_leaf_reg', 3.0):.2f}
                - Random Strength: {best_params.get('random_strength', 1.0):.2f}
                - Bagging Temperature: {best_params.get('bagging_temperature', 1.0):.2f}
                - Grow Policy: {best_params.get('grow_policy', 'SymmetricTree')}
                """)
                
                # Add button to apply best parameters
                if st.button("최적 파라미터 적용", key="cb_apply_params"):
                    # Set a flag to indicate parameters should be updated on next render
                    st.session_state.cb_apply_requested = True
                    # This will trigger a rerun with the flag set
                    st.rerun()
                
                # Add a note to inform the user to start training with the new parameters
                st.info("최적 파라미터 적용 후 '모델 학습 시작' 버튼을 눌러 학습을 시작하세요.")
                
            except Exception as e:
                status_text_opt.error(f"최적화 오류: {e}")
                progress_bar_opt.progress(0)

        if train_button or st.session_state.cb_trained:
            st.subheader("⏳ CatBoost 학습 진행")
            progress_bar_cb = st.progress(0)
            status_text_cb = st.empty()
            log_placeholder_cb = st.empty()
            # Create placeholders for learning curve
            learning_curve_cb = st.empty()

            try:
                # Configure CatBoost regressor with parameters from 2_training_catboost.py
                catboost_model = cbm.CatBoostRegressor(
                    iterations=model_params['CatBoost']['iterations'],
                    learning_rate=model_params['CatBoost']['learning_rate'],
                    depth=model_params['CatBoost']['depth'],
                    loss_function=model_params['CatBoost']['loss_function'],
                    eval_metric=model_params['CatBoost']['eval_metric'],
                    random_seed=44,
                    verbose=100,  # 학습 진행 상황을 100번째 반복마다 출력
                    task_type='CPU'
                )

                # Prepare data pools for CatBoost
                train_pool = cbm.Pool(X_train, y_train)
                test_pool = cbm.Pool(X_test, y_test)

                start_time = time.time()
                status_text_cb.text("모델 학습 중...")
                
                # Fit the model
                catboost_model.fit(
                    train_pool,
                    eval_set=test_pool,
                    early_stopping_rounds=model_params['CatBoost']['early_stopping_rounds'],
                    use_best_model=True
                )

                end_time = time.time()
                training_time = end_time - start_time
                status_text_cb.success(f"CatBoost 학습 완료! (소요 시간: {training_time:.2f}초)")
                progress_bar_cb.progress(100)

                # Get training history - 사용된 평가 지표에 맞게 결과 가져오기
                eval_metric = model_params['CatBoost']['eval_metric']
                train_losses = catboost_model.get_evals_result()['learn'][eval_metric]
                test_losses = catboost_model.get_evals_result()['validation'][eval_metric]
                iterations_list = list(range(len(train_losses)))

                # Store logs
                training_logs['CatBoost'] = f"모델 학습 완료. 최적 반복: {catboost_model.get_best_iteration()} 반복 수행됨."
                log_placeholder_cb.info(training_logs['CatBoost'])
                
                # Plot learning curves
                fig = go.Figure()
                
                # Add training loss curve
                fig.add_trace(
                    go.Scatter(
                        x=iterations_list, 
                        y=train_losses, 
                        mode='lines', 
                        name='Train Loss',
                        line=dict(color='blue', width=2)
                    )
                )
                
                # Add validation loss curve
                fig.add_trace(
                    go.Scatter(
                        x=iterations_list, 
                        y=test_losses, 
                        mode='lines', 
                        name='Validation Loss',
                        line=dict(color='orange', width=2)
                    )
                )
                
                # Setup chart layout - 선택된 평가 지표로 제목 표시
                fig.update_layout(
                    title='CatBoost 학습 & 검증 손실',
                    xaxis_title='반복 횟수',
                    yaxis_title=f'{eval_metric} 손실',
                    legend=dict(
                        x=0.02,
                        y=0.98,
                        bgcolor='rgba(255, 255, 255, 0.5)',
                        bordercolor='rgba(0, 0, 0, 0.1)',
                        borderwidth=1
                    ),
                    template='plotly_white',
                    height=600
                )
                
                # Set y-axis range (start from 0 to max value * 1.1)
                max_loss = max(max(train_losses), max(test_losses))
                fig.update_yaxes(range=[0, max_loss * 1.1])
                
                # Display the plot
                learning_curve_cb.plotly_chart(fig, use_container_width=True)

                st.subheader("📈 CatBoost 결과")
                y_pred_cb = catboost_model.predict(X_test)
                rmse_cb = np.sqrt(mean_squared_error(y_test, y_pred_cb))
                mae_cb = mean_absolute_error(y_test, y_pred_cb)
                r2_cb = r2_score(y_test, y_pred_cb)

                # Update metric storage in session state
                st.session_state.model_results['CatBoost'] = {
                    'RMSE': rmse_cb,
                    'MAE': mae_cb,
                    'R2 Score': r2_cb,
                    'MAPE': np.mean(np.abs((y_test - y_pred_cb) / y_test)) * 100,  # MAPE 추가 (단위: %)
                    'Training Time (s)': training_time,
                    'Best Iteration': catboost_model.get_best_iteration(),
                    'Predictions': y_pred_cb,  # Store predictions
                    'Test_Actual': y_test.values  # Store actual values
                }

                st.metric("RMSE", f"{rmse_cb:.4f}")
                st.metric("MAE", f"{mae_cb:.4f}")
                st.metric("R2 Score", f"{r2_cb:.4f}")
                st.metric("MAPE", f"{st.session_state.model_results['CatBoost']['MAPE']:.4f}%")  # MAPE 표시 추가

                # Feature Importance
                try:
                    # 특성 중요도 계산
                    feature_importance = catboost_model.get_feature_importance()
                    feature_names = selected_features
                    
                    # 특성 중요도 데이터프레임 생성 후 Series로 변환 (기존 시각화 유지)
                    importance_df = pd.DataFrame({
                        'Feature': feature_names,
                        'Importance': feature_importance
                    })
                    importance_df = importance_df.sort_values('Importance', ascending=False)
                    
                    # Series로 변환하여 기존 시각화 방식 유지
                    feature_importance_cb = pd.Series(
                        importance_df['Importance'].values,
                        index=importance_df['Feature'].values
                    )
                    
                    st.subheader("📊 CatBoost 피처 중요도")
                    
                    # Create plotly bar chart for feature importance (기존 방식)
                    fig_importance_cb = px.bar(
                        x=feature_importance_cb.values,
                        y=feature_importance_cb.index,
                        orientation='h',
                        title='피처 중요도 (CatBoost)',
                        labels={'x': '중요도', 'y': '피처'},
                        color=feature_importance_cb.values,
                        color_continuous_scale='Blues'
                    )
                    
                    # Customize layout
                    fig_importance_cb.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        height=600,  # 고정 높이 설정
                        template='plotly_white'
                    )
                    
                    # Display the plotly chart
                    st.plotly_chart(fig_importance_cb, use_container_width=True)
                    
                except Exception as e:
                    st.warning(f"피처 중요도를 계산하는 중 오류 발생: {e}")
                
                # Add visualization section
                st.subheader("📊 CatBoost 모델 시각화")
                
                # Create tabs for different visualizations
                viz_tabs_cb = st.tabs(["예측 vs 실제", "잔차 분석", "잔차 분포"])
                
                with viz_tabs_cb[0]:
                    # Predicted vs Actual plot
                    fig_actual_pred_cb = px.scatter(
                        x=y_test, y=y_pred_cb, 
                        labels={'x': '실제값', 'y': '예측값'},
                        title='실제값 vs 예측값'
                    )
                    # Add perfect prediction line (y=x)
                    fig_actual_pred_cb.add_trace(
                        go.Scatter(
                            x=[y_test.min(), y_test.max()], 
                            y=[y_test.min(), y_test.max()],
                            mode='lines', 
                            name='완벽한 예측',
                            line=dict(color='red', dash='dash')
                        )
                    )
                    st.plotly_chart(fig_actual_pred_cb, use_container_width=True)
                
                with viz_tabs_cb[1]:
                    # Calculate residuals
                    residuals_cb = y_test - y_pred_cb
                    
                    # Residuals vs Predicted plot
                    fig_resid_pred_cb = px.scatter(
                        x=y_pred_cb, y=residuals_cb,
                        labels={'x': '예측값', 'y': '잔차'},
                        title='예측값 vs 잔차'
                    )
                    # Add zero line
                    fig_resid_pred_cb.add_hline(y=0, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_resid_pred_cb, use_container_width=True)
                
                with viz_tabs_cb[2]:
                    # Residual distribution
                    fig_resid_hist_cb = px.histogram(
                        residuals_cb, 
                        nbins=30,
                        labels={'value': '잔차', 'count': '빈도'},
                        title='잔차 분포'
                    )
                    st.plotly_chart(fig_resid_hist_cb, use_container_width=True)

            except Exception as e:
                status_text_cb.error(f"CatBoost 학습 오류: {e}")
                progress_bar_cb.progress(0)


    # --- XGBoost Tab ---
    with tab2:
        st.header("⚡ XGBoost 설정 및 학습")
        
        # Check if parameters should be updated from optimization
        if 'xgb_apply_requested' in st.session_state and st.session_state.xgb_apply_requested:
            # Reset the flag
            st.session_state.xgb_apply_requested = False
            
            if 'xgboost_best_params' in st.session_state:
                best_params = st.session_state.xgboost_best_params
                # Update session state for sliders before rendering them
                st.session_state.xgb_lr = best_params['learning_rate']
                st.session_state.xgb_max_depth = int(best_params['max_depth'])
                st.success("최적 파라미터가 하이퍼파라미터 설정에 적용되었습니다!")
        
        with st.expander("하이퍼파라미터 설정", expanded=True):
            xgb_n_estimators = st.slider("Iterations", 100, 2000, 1000, 100, key="xgb_n_est")
            xgb_learning_rate = st.slider("Learning Rate", 0.01, 0.5, 0.01, 0.01, key="xgb_lr")
            xgb_max_depth = st.slider("Depth", 3, 10, 8, 1, key="xgb_max_depth")
            
            # Change labels for objective selection to more user-friendly names
            objective_options = {"RMSE": "reg:squarederror", "MAE": "reg:absoluteerror", "MAPE": "reg:squarederror"}
            xgb_objective_display = st.selectbox("Loss Function", list(objective_options.keys()), index=2, key="xgb_obj")
            # Map display name back to actual XGBoost parameter value
            xgb_objective = objective_options[xgb_objective_display]
            
            # 추가 파라미터 UI 요소
            xgb_subsample = st.slider("Subsample", 0.1, 1.0, 0.8, 0.1, key="xgb_subsample")
            xgb_colsample_bytree = st.slider("Column Sample by Tree", 0.1, 1.0, 0.8, 0.1, key="xgb_colsample")
            
            xgb_early_stopping_rounds = st.slider("Early Stopping Rounds", 10, 100, 10, 10, key="xgb_esr")

        # Set eval_metric based on the selected loss function display name
        if xgb_objective_display == "RMSE":
            xgb_eval_metric = "rmse"
        elif xgb_objective_display == "MAE":
            xgb_eval_metric = "mae"
        elif xgb_objective_display == "MAPE":
            xgb_eval_metric = "mape"
        else:
            xgb_eval_metric = "rmse"  # 기본값

        model_params['XGBoost'] = {
            'n_estimators': xgb_n_estimators,
            'learning_rate': xgb_learning_rate,
            'max_depth': xgb_max_depth,
            'objective': xgb_objective,  # This is now the mapped technical value
            'early_stopping_rounds': xgb_early_stopping_rounds,
            'random_state': 42,
            'eval_metric': xgb_eval_metric,  # Use the determined eval_metric
            'subsample': xgb_subsample,
            'colsample_bytree': xgb_colsample_bytree,
            'nthread': -1  # 사용 가능한 모든 CPU 스레드 사용
        }

        # Check if we have previously optimized parameters
        have_optimized_params = 'xgboost_best_params' in st.session_state and st.session_state.xgboost_best_params
        
        if have_optimized_params:
            st.success("최적화된 파라미터를 사용할 수 있습니다.")
            use_optimized = st.checkbox("최적화된 파라미터 사용", value=False, key="xgb_use_optimized")
            
            if use_optimized:
                # Update model parameters with optimized values
                best_params = st.session_state.xgboost_best_params
                
                # Save original parameters to display the difference
                original_lr = model_params['XGBoost']['learning_rate']
                original_depth = model_params['XGBoost']['max_depth']
                
                # Update parameters
                model_params['XGBoost'].update({
                    'learning_rate': best_params['learning_rate'],
                    'max_depth': best_params['max_depth'],
                    'min_child_weight': best_params.get('min_child_weight', 1),
                    'subsample': best_params.get('subsample', 1.0),
                    'colsample_bytree': best_params.get('colsample_bytree', 1.0),
                    'gamma': best_params.get('gamma', 0),
                })
                
                # Display which parameters are being used, showing the changes
                st.info(f"""
                **최적 파라미터가 적용됨 (슬라이더 값과 다를 수 있음):**
                - 학습률(Learning Rate): {original_lr} → **{best_params['learning_rate']:.4f}**
                - 깊이(Max Depth): {original_depth} → **{best_params['max_depth']}**
                - 추가 파라미터:
                  - Min Child Weight: {best_params.get('min_child_weight', 1)}
                  - Subsample: {best_params.get('subsample', 1.0):.2f}
                  - Column Sample by Tree: {best_params.get('colsample_bytree', 1.0):.2f}
                  - Gamma: {best_params.get('gamma', 0):.2f}
                """)
                
                st.warning("슬라이더값은 변경되지 않았지만, 모델 학습에는 위 최적 파라미터가 사용됩니다.")

        # Create columns for buttons
        col1, col2 = st.columns(2)
        
        with col1:
            train_button = st.button("XGBoost 모델 학습 시작", key="xgb_train")
            if train_button:
                st.session_state.xgb_trained = True
            
        with col2:
            optimize_button = st.button("하이퍼파라미터 최적화", key="xgb_optimize")

        # Hyperparameter optimization
        if optimize_button:
            st.subheader("⚙️ XGBoost 하이퍼파라미터 최적화 중")
            progress_bar_opt = st.progress(0)
            status_text_opt = st.empty()
            
            try:
                status_text_opt.text("하이퍼파라미터 최적화를 위한 탐색 공간 준비 중...")
                
                # Define parameter search space for XGBoost
                param_dist = {
                    'learning_rate': uniform(0.01, 0.3),
                    'max_depth': randint(3, 10),
                    'min_child_weight': randint(1, 10),
                    'subsample': uniform(0.6, 0.4),
                    'colsample_bytree': uniform(0.6, 0.4),
                    'gamma': uniform(0, 5),
                }
                
                # Set base model for XGBoost
                xgboost_opt = xgb.XGBRegressor(
                    n_estimators=300,  # Reduced for faster optimization
                    objective=xgb_objective,
                    random_state=42,
                    verbosity=0  # Disable verbose output during optimization
                )
                
                status_text_opt.text("랜덤 탐색을 통한 최적 파라미터 탐색 중...")
                progress_bar_opt.progress(20)
                
                # RandomizedSearchCV for hyperparameter optimization
                random_search = RandomizedSearchCV(
                    estimator=xgboost_opt,
                    param_distributions=param_dist,
                    n_iter=100,  # Number of parameter settings sampled
                    cv=5,  # 5-fold cross-validation
                    verbose=0,
                    random_state=42,
                    n_jobs=-1  # Use all available cores
                )
                
                # Fit the random search
                random_search.fit(X_train, y_train)
                
                progress_bar_opt.progress(80)
                status_text_opt.text("최적 파라미터 적용 중...")
                
                # Get best parameters
                best_params = random_search.best_params_
                
                # Update model parameters without changing sliders
                model_params['XGBoost'].update({
                    'learning_rate': best_params['learning_rate'],
                    'max_depth': best_params['max_depth'],
                    'min_child_weight': best_params.get('min_child_weight', 1),
                    'subsample': best_params.get('subsample', 1.0),
                    'colsample_bytree': best_params.get('colsample_bytree', 1.0),
                    'gamma': best_params.get('gamma', 0),
                })
                
                progress_bar_opt.progress(100)
                status_text_opt.success("최적화 완료! 최적 파라미터가 계산되었습니다.")
                
                # Store best parameters in session state for later use
                if 'xgboost_best_params' not in st.session_state:
                    st.session_state.xgboost_best_params = {}
                st.session_state.xgboost_best_params = best_params
                
                # Display best parameters
                st.info(f"""
                **최적 파라미터:**
                - Learning Rate: {best_params['learning_rate']:.4f}
                - Max Depth: {best_params['max_depth']}
                - Min Child Weight: {best_params.get('min_child_weight', 1)}
                - Subsample: {best_params.get('subsample', 1.0):.2f}
                - Column Sample by Tree: {best_params.get('colsample_bytree', 1.0):.2f}
                - Gamma: {best_params.get('gamma', 0):.2f}
                """)
                
                # Add button to apply best parameters
                if st.button("최적 파라미터 적용", key="xgb_apply_params"):
                    # Set a flag to indicate parameters should be updated on next render
                    st.session_state.xgb_apply_requested = True
                    # This will trigger a rerun with the flag set
                    st.rerun()
                
                # Add a note to inform the user to start training with the new parameters
                st.info("최적 파라미터 적용 후 '모델 학습 시작' 버튼을 눌러 학습을 시작하세요.")
                
            except Exception as e:
                status_text_opt.error(f"최적화 오류: {e}")
                progress_bar_opt.progress(0)

        if train_button or st.session_state.xgb_trained:
            st.subheader("⏳ XGBoost 학습 진행")
            progress_bar_xgb = st.progress(0)
            status_text_xgb = st.empty()
            log_placeholder_xgb = st.empty()
            # Create placeholders for learning curve
            learning_curve_xgb = st.empty()
            
            try:
                # Setup XGBoost parameters
                xgb_params = {
                    'objective': model_params['XGBoost']['objective'],
                    'learning_rate': model_params['XGBoost']['learning_rate'],
                    'max_depth': model_params['XGBoost']['max_depth'],
                    'eval_metric': model_params['XGBoost']['eval_metric'],
                    'random_state': model_params['XGBoost']['random_state']
                }
                
                # Add additional parameters if they exist in model_params
                for param in ['min_child_weight', 'subsample', 'colsample_bytree', 'gamma']:
                    if param in model_params['XGBoost']:
                        xgb_params[param] = model_params['XGBoost'][param]
                
                start_time = time.time()
                status_text_xgb.text("모델 학습 중...")
                
                # Create DMatrix objects for XGBoost
                dtrain = xgb.DMatrix(X_train, label=y_train)
                dtest = xgb.DMatrix(X_test, label=y_test)
                
                # Dictionary to store training history
                evals_result = {}
                
                # Train the model using xgb.train (core API)
                xgb_model = xgb.train(
                    xgb_params,
                    dtrain,
                    num_boost_round=model_params['XGBoost']['n_estimators'],
                    evals=[(dtrain, 'train'), (dtest, 'test')],
                    early_stopping_rounds=model_params['XGBoost']['early_stopping_rounds'],
                    evals_result=evals_result, # Store evaluation history
                    verbose_eval=100  # Print info every 100 iterations
                )
                
                end_time = time.time()
                training_time = end_time - start_time
                status_text_xgb.success(f"XGBoost 학습 완료! (소요 시간: {training_time:.2f}초)")
                progress_bar_xgb.progress(100)
                
                # Get training history from evals_result
                train_metric_name = list(evals_result['train'].keys())[0]
                test_metric_name = list(evals_result['test'].keys())[0]
                
                train_losses = evals_result['train'][train_metric_name]
                test_losses = evals_result['test'][test_metric_name]
                iterations_list = list(range(len(train_losses)))
                
                # Store logs
                best_iter = xgb_model.best_iteration
                training_logs['XGBoost'] = f"모델 학습 완료. 최적 반복: {best_iter}"
                log_placeholder_xgb.info(training_logs['XGBoost'])

                # Plot learning curves
                fig = go.Figure()
                
                # Add training loss curve
                fig.add_trace(
                    go.Scatter(
                        x=iterations_list, 
                        y=train_losses, 
                        mode='lines', 
                        name='Train Loss',
                        line=dict(color='blue', width=2)
                    )
                )
                
                # Add validation loss curve
                fig.add_trace(
                    go.Scatter(
                        x=iterations_list, 
                        y=test_losses, 
                        mode='lines', 
                        name='Validation Loss',
                        line=dict(color='orange', width=2)
                    )
                )
                
                # Add a vertical line at the best iteration
                fig.add_vline(
                    x=best_iter, 
                    line_width=2, 
                    line_dash="dash", 
                    line_color="green", 
                    annotation_text=f"Best Iteration: {best_iter}", 
                    annotation_position="top right"
                )
                
                # Setup chart layout
                fig.update_layout(
                    title='XGBoost 학습 & 검증 손실',
                    xaxis_title='반복 횟수',
                    yaxis_title=f'{train_metric_name.upper()} 손실',
                    legend=dict(
                        x=0.02,
                        y=0.98,
                        bgcolor='rgba(255, 255, 255, 0.5)',
                        bordercolor='rgba(0, 0, 0, 0.1)',
                        borderwidth=1
                    ),
                    template='plotly_white',
                    height=600
                )
                
                # Set y-axis range (start from 0 to max value * 1.1)
                max_loss = max(max(train_losses), max(test_losses))
                fig.update_yaxes(range=[0, max_loss * 1.1])
                
                # Display the plot
                learning_curve_xgb.plotly_chart(fig, use_container_width=True)

                st.subheader("📈 XGBoost 결과")
                
                # Predict using the core model
                y_pred_xgb = xgb_model.predict(dtest)
                rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred_xgb))
                mae_xgb = mean_absolute_error(y_test, y_pred_xgb)
                r2_xgb = r2_score(y_test, y_pred_xgb)

                # Update metric storage in session state
                st.session_state.model_results['XGBoost'] = {
                    'RMSE': rmse_xgb,
                    'MAE': mae_xgb,
                    'R2 Score': r2_xgb,
                    'MAPE': np.mean(np.abs((y_test - y_pred_xgb) / y_test)) * 100,  # MAPE 추가 (단위: %)
                    'Training Time (s)': training_time,
                    'Best Iteration': best_iter,
                    'Predictions': y_pred_xgb,  # Store predictions
                    'Test_Actual': y_test.values  # Store actual values
                }

                st.metric("RMSE", f"{rmse_xgb:.4f}")
                st.metric("MAE", f"{mae_xgb:.4f}")
                st.metric("R2 Score", f"{r2_xgb:.4f}")
                st.metric("MAPE", f"{st.session_state.model_results['XGBoost']['MAPE']:.4f}%")  # MAPE 표시 추가

                # Feature Importance
                try:
                    # Get feature importance from the model
                    feature_importance = xgb_model.get_score(importance_type='gain')
                    # Convert to Series for easier plotting - don't try to convert feature names to indices
                    feature_importance_xgb = pd.Series(feature_importance, name='Importance').sort_values(ascending=False)
                        
                    st.subheader("📊 XGBoost 피처 중요도 (Gain)")
                        
                    # Create plotly bar chart for feature importance
                    fig_importance_xgb = px.bar(
                        x=feature_importance_xgb.values,
                        y=feature_importance_xgb.index,
                        orientation='h',
                        title='피처 중요도 (XGBoost - Gain)',
                        labels={'x': '중요도 (Gain)', 'y': '피처'},
                        color=feature_importance_xgb.values,
                        color_continuous_scale='Greens'
                    )
                        
                    # Customize layout
                    fig_importance_xgb.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        height=600,  # 고정 높이 설정
                        template='plotly_white'
                    )
                        
                    # Display the plotly chart
                    st.plotly_chart(fig_importance_xgb, use_container_width=True)
                        
                except Exception as e:
                    st.warning(f"피처 중요도를 계산하는 중 오류 발생: {e}")

                # Add visualization section
                st.subheader("📊 XGBoost 모델 시각화")
                
                # Create tabs for different visualizations
                viz_tabs_xgb = st.tabs(["예측 vs 실제", "잔차 분석", "잔차 분포"])
                
                with viz_tabs_xgb[0]:
                    # Predicted vs Actual plot
                    fig_actual_pred_xgb = px.scatter(
                        x=y_test, y=y_pred_xgb, 
                        labels={'x': '실제값', 'y': '예측값'},
                        title='실제값 vs 예측값'
                    )
                    # Add perfect prediction line (y=x)
                    fig_actual_pred_xgb.add_trace(
                        go.Scatter(
                            x=[y_test.min(), y_test.max()], 
                            y=[y_test.min(), y_test.max()],
                            mode='lines', 
                            name='완벽한 예측',
                            line=dict(color='red', dash='dash')
                        )
                    )
                    st.plotly_chart(fig_actual_pred_xgb, use_container_width=True)
                
                with viz_tabs_xgb[1]:
                    # Calculate residuals
                    residuals_xgb = y_test - y_pred_xgb
                    
                    # Residuals vs Predicted plot
                    fig_resid_pred_xgb = px.scatter(
                        x=y_pred_xgb, y=residuals_xgb,
                        labels={'x': '예측값', 'y': '잔차'},
                        title='예측값 vs 잔차'
                    )
                    # Add zero line
                    fig_resid_pred_xgb.add_hline(y=0, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_resid_pred_xgb, use_container_width=True)
                
                with viz_tabs_xgb[2]:
                    # Residual distribution
                    fig_resid_hist_xgb = px.histogram(
                        residuals_xgb, 
                        nbins=30,
                        labels={'value': '잔차', 'count': '빈도'},
                        title='잔차 분포'
                    )
                    st.plotly_chart(fig_resid_hist_xgb, use_container_width=True)

            except Exception as e:
                status_text_xgb.error(f"XGBoost 학습 오류: {e}")
                progress_bar_xgb.progress(0)


    # --- Comparison Section ---
    st.divider()
    st.header("⚔️ 모델 성능 비교")

    # Check if results are available before trying to display them
    if st.session_state.model_results:
        # Create a filtered version of the results without the prediction arrays
        filtered_results = {}
        for model, metrics in st.session_state.model_results.items():
            filtered_results[model] = {k: v for k, v in metrics.items() 
                                     if k not in ['Predictions', 'Test_Actual']}
        
        # Display metrics table with filtered results
        results_df = pd.DataFrame(filtered_results).T

        # Display metrics table
        st.subheader("📋 성능 지표 비교")
        st.dataframe(results_df)

        # Highlight best model based on R2 score (higher is better)
        if 'R2 Score' in results_df.columns:
            best_model_r2 = results_df['R2 Score'].idxmax()
            st.success(f"🏆 **{best_model_r2}** 모델이 R2 Score 기준으로 가장 좋은 성능을 보입니다 ({results_df.loc[best_model_r2, 'R2 Score']:.4f}).")
        # Highlight best model based on RMSE score (lower is better)
        if 'RMSE' in results_df.columns:
            best_model_rmse = results_df['RMSE'].idxmin()
            st.info(f"📉 **{best_model_rmse}** 모델이 RMSE 기준으로 가장 좋은 성능을 보입니다 ({results_df.loc[best_model_rmse, 'RMSE']:.4f}).")
        # Highlight best model based on MAPE score (lower is better)
        if 'MAPE' in results_df.columns:
            best_model_mape = results_df['MAPE'].idxmin()
            st.info(f"📊 **{best_model_mape}** 모델이 MAPE 기준으로 가장 좋은 성능을 보입니다 ({results_df.loc[best_model_mape, 'MAPE']:.4f}%).")
        
        # Add visual comparison of metrics
        st.subheader("📊 성능 지표 시각화 비교")
        
        # Check if we have more than one model to compare
        if len(results_df) > 1:
            # Create tabs for different metric visualizations
            comp_tabs = st.tabs(["RMSE", "MAE", "MAPE", "R2 Score"])
            
            with comp_tabs[0]:
                # RMSE comparison (lower is better)
                fig_rmse = px.bar(
                    results_df, y='RMSE',
                    labels={'index': '모델', 'value': 'RMSE'},
                    title='RMSE 비교 (낮을수록 좋음)',
                    text_auto='.4f'  # 값 표시 (소수점 4자리)
                )
                fig_rmse.update_traces(textposition='outside')  # 값을 바 위에 표시
                st.plotly_chart(fig_rmse, use_container_width=True)
            
            with comp_tabs[1]:
                # MAE comparison (lower is better)
                fig_mae = px.bar(
                    results_df, y='MAE',
                    labels={'index': '모델', 'value': 'MAE'},
                    title='MAE 비교 (낮을수록 좋음)',
                    text_auto='.4f'  # 값 표시 (소수점 4자리)
                )
                fig_mae.update_traces(textposition='outside')  # 값을 바 위에 표시
                st.plotly_chart(fig_mae, use_container_width=True)
            
            with comp_tabs[2]:
                # MAPE comparison (lower is better)
                fig_mape = px.bar(
                    results_df, y='MAPE',
                    labels={'index': '모델', 'value': 'MAPE (%)'},
                    title='MAPE 비교 (낮을수록 좋음)',
                    text_auto='.4f'  # 값 표시 (소수점 4자리)
                )
                fig_mape.update_traces(textposition='outside')  # 값을 바 위에 표시
                st.plotly_chart(fig_mape, use_container_width=True)
            
            with comp_tabs[3]:
                # R2 Score comparison (higher is better)
                fig_r2 = px.bar(
                    results_df, y='R2 Score',
                    labels={'index': '모델', 'value': 'R2 Score'},
                    title='R2 Score 비교 (높을수록 좋음)',
                    text_auto='.4f'  # 값 표시 (소수점 4자리)
                )
                fig_r2.update_traces(textposition='outside')  # 값을 바 위에 표시
                st.plotly_chart(fig_r2, use_container_width=True)
                
            # Compare training time
            if 'Training Time (s)' in results_df.columns:
                st.subheader("⏱️ 학습 시간 비교")
                fig_time = px.bar(
                    results_df, y='Training Time (s)',
                    labels={'index': '모델', 'value': '학습 시간 (초)'},
                    title='학습 시간 비교',
                    text_auto='.2f'  # 값 표시 (소수점 2자리)
                )
                fig_time.update_traces(textposition='outside')  # 값을 바 위에 표시
                st.plotly_chart(fig_time, use_container_width=True)
            
            # If both models have been trained, show residual comparison
            if 'CatBoost' in st.session_state.model_results and 'XGBoost' in st.session_state.model_results:
                st.subheader("📉 모델 잔차 비교")
                
                # Create a dataframe for residual comparison
                try:
                    # Use predictions stored in session state
                    y_test_values = st.session_state.model_results['CatBoost']['Test_Actual']
                    y_pred_cb = st.session_state.model_results['CatBoost']['Predictions']
                    y_pred_xgb = st.session_state.model_results['XGBoost']['Predictions']
                    
                    residual_data = pd.DataFrame({
                        'Actual': y_test_values,
                        'CatBoost_Predicted': y_pred_cb,
                        'XGBoost_Predicted': y_pred_xgb,
                        'CatBoost_Residual': y_test_values - y_pred_cb,
                        'XGBoost_Residual': y_test_values - y_pred_xgb
                    })
                    
                    # Create a scatter plot of residuals
                    fig_residual_comp = go.Figure()
                    
                    fig_residual_comp.add_trace(
                        go.Box(
                            y=residual_data['CatBoost_Residual'], 
                            name='CatBoost',
                            boxmean=True,
                            boxpoints='all',  # 모든 점 표시 (points가 아닌 boxpoints 사용)
                            jitter=0.3,    # 점들이 겹치지 않도록 분산
                            pointpos=-1.8, # 점들의 위치 (박스 왼쪽)
                            marker=dict(color='blue', size=4, opacity=0.5)
                        )
                    )
                    
                    fig_residual_comp.add_trace(
                        go.Box(
                            y=residual_data['XGBoost_Residual'], 
                            name='XGBoost',
                            boxmean=True,
                            boxpoints='all',  # 모든 점 표시 (points가 아닌 boxpoints 사용)
                            jitter=0.3,    # 점들이 겹치지 않도록 분산
                            pointpos=-1.8, # 점들의 위치 (박스 왼쪽)
                            marker=dict(color='green', size=4, opacity=0.5)
                        )
                    )
                    
                    fig_residual_comp.update_layout(
                        title='모델별 잔차 분포 비교',
                        yaxis_title='잔차',
                        showlegend=True,
                        boxmode='group',
                        height=600  # 높이 키워서 점들을 더 잘 볼 수 있게 함
                    )
                    
                    st.plotly_chart(fig_residual_comp, use_container_width=True)
                except Exception as e:
                    st.warning(f"잔차 비교 시각화 중 오류 발생: {e}")
        else:
            st.info("두 개 이상의 모델을 학습시켜야 모델 간 비교를 볼 수 있습니다.")

    else:
        st.info("모델을 학습시킨 후 성능 비교 결과가 여기에 표시됩니다.")

else:
    st.warning("데이터 파일을 먼저 로드해주세요.")

# Add instructions on how to run
st.sidebar.markdown("---")
st.sidebar.info("앱을 실행하려면 터미널에서 다음 명령어를 입력하세요:")
st.sidebar.code("streamlit run FWHM/fwhm_models.py")