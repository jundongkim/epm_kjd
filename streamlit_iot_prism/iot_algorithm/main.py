import streamlit as st
import os
import base64
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from iot_algorithm.data_generation import generate_iot_data
from iot_algorithm.preprocessing import handle_missing_values, handle_outliers, normalize_data
from iot_algorithm.analysis import calculate_statistics, plot_feature_distributions, plot_correlation_heatmap, plot_boxplots, plot_scatter_matrix
from iot_algorithm.modeling import train_model, evaluate_model, plot_model_predictions, plot_feature_importance, perform_cross_validation, compare_models, plot_learning_curve
# Import all utilities from the utils package
from iot_algorithm.utils import (
    load_iot_font_css, 
    apply_custom_style, 
    apply_graph_themes,
    convert_df_to_csv, 
    load_data
)

# Apply custom styles and themes
load_iot_font_css()
apply_custom_style()
apply_graph_themes()

# --- Session State Initialization ---
# Define workflow stages
STAGES = {
    'DATA_LOADED': 1,
    'PREPROCESSING_DONE': 2,
    'FEATURE_SELECTION_DONE': 3,
    'DATA_SPLIT_DONE': 4,
    'NORMALIZATION_DONE': 5,
    'MODEL_TRAINED': 6
}

# Function to reset stages
def reset_from_stage(stage):
    """Reset all session state variables from a specific stage onwards"""
    if stage <= STAGES['DATA_LOADED']:
        st.session_state.current_stage = 0
        st.session_state.data = None
        st.session_state.processed_data = None
        st.session_state.features = []
        st.session_state.target = None
        st.session_state.selected_features = []
        st.session_state.preprocessing_params = {}
        st.session_state.split_params = {}
        st.session_state.normalization_params = {}
        st.session_state.X_train = None
        st.session_state.X_test = None
        st.session_state.y_train = None
        st.session_state.y_test = None
        st.session_state.scaler = None
        st.session_state.target_scaler = None
        st.session_state.models = []
        st.session_state.metrics = []
        st.session_state.model_names = []
        st.session_state.random_seed = None
    elif stage <= STAGES['PREPROCESSING_DONE']:
        st.session_state.current_stage = STAGES['DATA_LOADED']
        st.session_state.processed_data = st.session_state.data.copy() if st.session_state.data is not None else None
        st.session_state.selected_features = []
        st.session_state.preprocessing_params = {}
        st.session_state.split_params = {}
        st.session_state.normalization_params = {}
        st.session_state.X_train = None
        st.session_state.X_test = None
        st.session_state.y_train = None
        st.session_state.y_test = None
        st.session_state.scaler = None
        st.session_state.models = []
        st.session_state.metrics = []
        st.session_state.model_names = []
    elif stage <= STAGES['FEATURE_SELECTION_DONE']:
        st.session_state.current_stage = STAGES['PREPROCESSING_DONE']
        st.session_state.selected_features = []
        st.session_state.split_params = {}
        st.session_state.normalization_params = {}
        st.session_state.X_train = None
        st.session_state.X_test = None
        st.session_state.y_train = None
        st.session_state.y_test = None
        st.session_state.scaler = None
        st.session_state.models = []
        st.session_state.metrics = []
        st.session_state.model_names = []
    elif stage <= STAGES['DATA_SPLIT_DONE']:
        st.session_state.current_stage = STAGES['FEATURE_SELECTION_DONE']
        st.session_state.split_params = {}
        st.session_state.normalization_params = {}
        st.session_state.X_train = None
        st.session_state.X_test = None
        st.session_state.y_train = None
        st.session_state.y_test = None
        st.session_state.scaler = None
        st.session_state.models = []
        st.session_state.metrics = []
        st.session_state.model_names = []
    elif stage <= STAGES['NORMALIZATION_DONE']:
        st.session_state.current_stage = STAGES['DATA_SPLIT_DONE']
        st.session_state.normalization_params = {}
        st.session_state.scaler = None
        st.session_state.target_scaler = None
        st.session_state.models = []
        st.session_state.metrics = []
        st.session_state.model_names = []
    elif stage <= STAGES['MODEL_TRAINED']:
        st.session_state.current_stage = STAGES['NORMALIZATION_DONE']
        # Keep models and metrics for comparison

def main():
    
    # Apply custom styles and themes
    load_iot_font_css()
    apply_custom_style()
    apply_graph_themes()

    # --- App Title ---
    st.title("📊 IoT Data Simulation & Modeling")
    st.markdown("Generate, preprocess, model, and evaluate IoT data for predictive analytics")

    
    # --- Session State Initialization ---
    # Initialize session state
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = 0

    # Initialize other session state variables
    for key, default in [
        ('data', None),
        ('processed_data', None),
        ('models', []),
        ('metrics', []),
        ('model_names', []),
        ('features', []),
        ('selected_features', []),
        ('target', None),
        ('scaler', None),
        ('target_scaler', None),
        ('X_train', None),
        ('X_test', None),
        ('y_train', None),
        ('y_test', None),
        ('preprocessing_params', {}),
        ('split_params', {}),
        ('normalization_params', {}),
        ('random_seed', None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # --- Sidebar: Data Source ---
    st.sidebar.title("Simulator Settings")
    st.sidebar.header("1. Data Source")
    data_source = st.sidebar.radio("Choose data source:", ["Generate Synthetic Data", "Upload CSV"])

    if data_source == "Generate Synthetic Data":
        st.sidebar.subheader("Data Generation Parameters")
        n_samples = st.sidebar.slider("Number of samples:", 100, 100000, 10000)
        n_features = st.sidebar.slider("Number of features:", 2, 500, 50)
        noise_level = st.sidebar.slider("Noise level:", 0.0, 1.0, 0.2)
        missing_rate = st.sidebar.slider("Missing data rate:", 0.0, 0.3, 0.05)
        outlier_rate = st.sidebar.slider("Outlier rate:", 0.0, 0.2, 0.05)
        random_seed = st.sidebar.number_input("Random seed (for reproducibility):", 0, 9999, 42, 
            help="Using the same seed value will generate identical data each time, allowing for consistent model comparisons")
        
        # New parameters for controlling sensor value ranges
        st.sidebar.markdown("---")
        st.sidebar.subheader("Sensor Value Range Settings")
        min_value = st.sidebar.number_input("Minimum value for all sensors:", 0.0, 100.0, 0.0)
        use_diverse_ranges = st.sidebar.checkbox("Use diverse max ranges for sensors", value=True)
        max_range_multiplier = st.sidebar.slider(
            "Max range diversity multiplier:", 
            0.1, 10.0, 1.0, 
            help="Higher values create more diverse maximum values across sensors"
        )
        
        # Show example of possible ranges based on current settings
        if use_diverse_ranges:
            st.sidebar.markdown("**Example sensor ranges with current settings:**")
            np.random.seed(42)  # For consistent examples
            example_ranges = []
            for i in range(5):  # Show 5 example sensors
                if i % 5 == 0:  # Every 5th sensor has large values
                    max_val = max(1000, np.random.exponential(scale=300) * max_range_multiplier * 3)
                else:
                    max_val = np.random.exponential(scale=300) * max_range_multiplier
                max_val = min(max_val, 10000)
                example_ranges.append(f"Sensor {i+1}: {min_value:.1f} to {max_val:.1f}")
            st.sidebar.markdown("\n".join(example_ranges))
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Feature Value Distribution")
        dist_type = st.sidebar.selectbox(
            "Distribution type (all features):",
            ["Normal", "Uniform", "LogNormal", "Binomial"]
        )
        if dist_type == "Normal":
            dist_param1 = st.sidebar.number_input("Mean (μ)", value=0.0)
            dist_param2 = st.sidebar.number_input("Std (σ)", min_value=0.01, value=1.0)
        elif dist_type == "Uniform":
            dist_param1 = st.sidebar.number_input("Min", value=-1.0)
            dist_param2 = st.sidebar.number_input("Max", value=1.0)
        elif dist_type == "LogNormal":
            dist_param1 = st.sidebar.number_input("Mean of log (μ)", value=0.0)
            dist_param2 = st.sidebar.number_input("Std of log (σ)", min_value=0.01, value=1.0)
        elif dist_type == "Binomial":
            dist_param1 = st.sidebar.number_input("n (trials)", min_value=1, value=10)
            dist_param2 = st.sidebar.number_input("p (probability)", min_value=0.0, max_value=1.0, value=0.5)
        if st.sidebar.button("Generate Data"):
            with st.spinner("Generating synthetic IoT data..."):
                # Reset all stages when generating new data
                reset_from_stage(STAGES['DATA_LOADED'])
                
                df = generate_iot_data(
                    n_samples, n_features, dist_type, dist_param1, dist_param2,
                    noise_level=noise_level, missing_rate=missing_rate, outlier_rate=outlier_rate,
                    min_value=min_value, max_range_multiplier=max_range_multiplier, 
                    use_diverse_ranges=use_diverse_ranges, seed=random_seed
                )
                st.session_state.data = df
                st.session_state.processed_data = df.copy()
                st.session_state.features = [f"sensor_{i+1}" for i in range(n_features)]
                st.session_state.target = 'target'
                st.session_state.current_stage = STAGES['DATA_LOADED']
                # Store the random seed used for this dataset
                st.session_state.random_seed = random_seed
                st.success(f"Generated dataset with {n_samples} samples and {n_features} features!")
    else:
        upload_file = st.sidebar.file_uploader("Upload CSV file:", type=["csv"])
        # random_seed = st.sidebar.number_input("Random seed (for model training):", 0, 9999, 42, 
        #     help="Sets the random seed for model training to ensure reproducible results")
        if upload_file is not None:
            with st.spinner("Loading data..."):
                # Reset all stages when loading new data
                reset_from_stage(STAGES['DATA_LOADED'])
                
                df = load_data(upload_file)
                if df is not None:
                    st.session_state.data = df
                    st.session_state.processed_data = df.copy()
                    
                    # timestamp 열을 확인하고 특성 선택 시 제외하도록 표시
                    timestamp_cols = [col for col in df.columns if pd.api.types.is_datetime64_dtype(df[col])]
                    if timestamp_cols:
                        st.info(f"다음 열들이 timestamp 타입으로 인식되었습니다: {', '.join(timestamp_cols)}")
                        
                        # 시각화 및 분석에서 제외할 열 표시
                        st.warning(f"timestamp 열은 상관관계 분석 및 모델링에서 자동으로 제외됩니다.")
                    
                    # 열 이름에 'Unnamed'가 포함된 열이 있는지 확인
                    unnamed_cols = [col for col in df.columns if 'Unnamed' in col]
                    if unnamed_cols:
                        st.warning(f"다음 열들이 'Unnamed'로 인식되었습니다: {', '.join(unnamed_cols)}. 이는 CSV 파일의 형식 문제일 수 있습니다.")
                    
                    st.session_state.current_stage = STAGES['DATA_LOADED']
                    # Store the random seed for model training
                    # st.session_state.random_seed = random_seed
                    st.success(f"Loaded dataset with {df.shape[0]} samples and {df.shape[1]} columns!")

    # --- Main Content Based on Current Stage ---
    if st.session_state.current_stage >= STAGES['DATA_LOADED']:
        # --- Step 1: Data Preview ---
        st.header("1. Dataset Preview")
        st.dataframe(st.session_state.data.head(10))
        st.info(f"Dataset shape: {st.session_state.data.shape[0]} rows × {st.session_state.data.shape[1]} columns")
        
        # Display random seed if it was generated data
        if 'random_seed' in st.session_state:
            st.info(f"Random seed used: {st.session_state.random_seed} (Use this same seed to regenerate identical data)")
        
        csv = convert_df_to_csv(st.session_state.data)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"iot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
        if data_source == "Upload CSV" and not st.session_state.features:
            st.subheader("Select Features and Target")
            cols = st.session_state.data.columns.tolist()
            
            # timestamp 열 및 비수치형 열 필터링
            timestamp_cols = [col for col in cols if pd.api.types.is_datetime64_dtype(st.session_state.data[col])]
            non_numeric_cols = [col for col in cols if not pd.api.types.is_numeric_dtype(st.session_state.data[col])]
            
            # 타겟 변수 선택 시 timestamp 열 제외
            target_options = [col for col in cols if col not in timestamp_cols]
            if target_options:
                target_col = st.selectbox("Select target variable:", target_options)
                
                # 특성 변수 선택 시 timestamp 열과 타겟 변수 제외
                feature_options = [col for col in cols if col != target_col and col not in timestamp_cols]
                feature_cols = st.multiselect(
                    "Select feature variables:",
                    feature_options,
                    default=feature_options
                )
                
                # 자동 저장 옵션 추가
                auto_save = st.checkbox("Auto-save selection", value=True, 
                                       help="Automatically save selections without clicking the confirm button")
                
                # 자동 저장이 활성화되어 있으면 선택 즉시 저장
                if auto_save:
                    st.session_state.features = feature_cols
                    st.session_state.target = target_col
                    
                # 기존 버튼도 유지
                if st.button("Confirm Selection"):
                    st.session_state.features = feature_cols
                    st.session_state.target = target_col
                    st.success(f"Selected {len(feature_cols)} features and '{target_col}' as target variable.")
                    
                    # timestamp 열이 있으면 알림
                    if timestamp_cols:
                        st.info(f"Timestamp 열 {timestamp_cols}은(는) 특성에서 제외되었습니다.")
                
                # 자동 저장된 경우 메시지 표시
                if auto_save and st.session_state.features and st.session_state.target:
                    st.success(f"Auto-saved: {len(feature_cols)} features and '{target_col}' as target variable.")
                    
                    # timestamp 열이 있으면 알림
                    if timestamp_cols:
                        st.info(f"Timestamp 열 {timestamp_cols}은(는) 특성에서 제외되었습니다.")
            else:
                st.error("수치형 열이 없습니다. 데이터를 확인해주세요.")
        
        if st.session_state.features and st.session_state.target:
            st.subheader("Selected Variables")
            st.write(f"**Target Variable:** {st.session_state.target}")
            st.write(f"**Feature Variables:** {', '.join(st.session_state.features)}")
            
            # --- Step 2: Feature Analysis ---
            st.header("2. Feature Analysis")
            numerical_cols = st.session_state.features + [st.session_state.target]
            
            # 수치형 열이 있는지 확인
            numeric_cols_only = [col for col in numerical_cols 
                            if col in st.session_state.processed_data.columns and 
                            pd.api.types.is_numeric_dtype(st.session_state.processed_data[col])]
            
            if not numeric_cols_only:
                st.warning("수치형 열이 없어 특성 분석을 수행할 수 없습니다. 데이터 형식을 확인해주세요.")
            else:
                stats = calculate_statistics(st.session_state.processed_data, numerical_cols)
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "Basic Statistics", "Missing Values", "Outliers", "Distributions", "Correlations"
                ])
                with tab1:
                    st.subheader("Basic Statistics")
                    st.dataframe(stats['basic'])
                with tab2:
                    st.subheader("Missing Values")
                    missing_df = stats['missing']
                    fig_missing = px.bar(
                        missing_df.reset_index(),
                        x='index', y='percentage',
                        labels={'index': 'Feature', 'percentage': 'Missing (%)'},
                        title="Missing Values by Feature",
                        color='percentage', color_continuous_scale=px.colors.sequential.Viridis
                    )
                    st.plotly_chart(fig_missing)
                    st.dataframe(missing_df)
                with tab3:
                    st.subheader("Outliers")
                    outlier_data = []
                    if 'outliers' in stats and stats['outliers']:
                        for col, out_stats in stats['outliers'].items():
                            outlier_data.append({'Feature': col, 'Outlier Percentage': out_stats['percentage']})
                        outlier_df = pd.DataFrame(outlier_data)
                        if not outlier_df.empty:
                            fig_outliers = px.bar(
                                outlier_df, x='Feature', y='Outlier Percentage',
                                title="Outliers by Feature", color='Outlier Percentage',
                                color_continuous_scale=px.colors.sequential.Reds
                            )
                            st.plotly_chart(fig_outliers)
                        fig_box = plot_boxplots(st.session_state.processed_data, numerical_cols)
                        st.plotly_chart(fig_box)
                        st.subheader("Outlier Details")
                        for col, data in stats['outliers'].items():
                            st.write(f"**{col}:** {data['count']} outliers ({data['percentage']:.2f}%)")
                            st.write(f"Lower bound: {data['lower_bound']:.4f}, Upper bound: {data['upper_bound']:.4f}")
                    else:
                        st.info("No outliers detected or no numeric columns available for outlier detection.")
                with tab4:
                    st.subheader("Feature Distributions")
                    # Provide feature selection option to the user
                    feature_to_plot = st.selectbox(
                        "Select feature to visualize:",
                        [col for col in numerical_cols if st.session_state.processed_data[col].dtype.kind in 'fi']
                    )
                    if feature_to_plot:
                        fig_hist = px.histogram(
                            st.session_state.processed_data, x=feature_to_plot,
                            marginal="box", title=f"Distribution of {feature_to_plot}",
                            color_discrete_sequence=['royalblue']
                        )
                        st.plotly_chart(fig_hist)
                with tab5:
                    st.subheader("Feature Correlations")
                    corr_fig = plot_correlation_heatmap(st.session_state.processed_data, numerical_cols)
                    st.plotly_chart(corr_fig)
                    scatter_fig = plot_scatter_matrix(st.session_state.processed_data, numerical_cols, limit=5)
                    st.plotly_chart(scatter_fig)

        # --- Step 3: Data Preprocessing ---
        if st.session_state.current_stage >= STAGES['DATA_LOADED']:
            st.sidebar.header("3. Data Preprocessing")
            st.sidebar.subheader("Missing Value Handling")
            missing_method = st.sidebar.selectbox(
                "Method for missing values:",
                ["none", "drop_rows", "drop_columns", "mean", "median", "mode", "zero"],
                format_func=lambda x: {
                    "none": "No handling", "drop_rows": "Drop rows with missing values",
                    "drop_columns": "Drop columns with missing values", "mean": "Replace with mean",
                    "median": "Replace with median", "mode": "Replace with mode", "zero": "Replace with zero"
                }[x],
                key="missing_method_selectbox"
            )
            st.sidebar.subheader("Outlier Handling")
            outlier_method = st.sidebar.selectbox(
                "Method for outliers:",
                ["none", "clip", "remove", "mean", "median"],
                format_func=lambda x: {
                    "none": "No handling", "clip": "Clip to boundaries", "remove": "Remove outliers",
                    "mean": "Replace with mean", "median": "Replace with median"
                }[x],
                key="outlier_method_selectbox"
            )
            st.sidebar.subheader("Normalization")
            normalize_method = st.sidebar.selectbox(
                "Normalization method:",
                ["none", "min_max", "standard"],
                format_func=lambda x: {
                    "none": "No normalization", "min_max": "Min-Max Normalization (0-1)",
                    "standard": "Standardization (mean=0, std=1)"
                }[x],
                key="normalize_method_selectbox"
            )
            
            # Only show this option if normalization is selected
            normalize_target = False
            if normalize_method != "none":
                normalize_target = st.sidebar.checkbox("Also normalize target variable", 
                                                value=True,
                                                help="Also apply normalization to the target variable. This helps with model training but changes the scale of predictions.",
                                                key="normalize_target_preprocessing")
            
            preprocess_button = st.sidebar.button("Apply Preprocessing")
            if preprocess_button:
                with st.spinner("Applying preprocessing..."):
                    # Reset stages from preprocessing onwards
                    reset_from_stage(STAGES['PREPROCESSING_DONE'])
                    
                    df_processed = st.session_state.data.copy()
                    numerical_cols = st.session_state.features + [st.session_state.target]
                    
                    # 수치형 열이 있는지 확인
                    numeric_cols_only = [col for col in numerical_cols 
                                        if col in df_processed.columns and pd.api.types.is_numeric_dtype(df_processed[col])]
                    if not numeric_cols_only:
                        st.error("수치형 열이 없습니다. 데이터 형식을 확인하거나 다른 데이터를 업로드해주세요.")
                        st.stop()
                    
                    if missing_method != "none":
                        df_processed = handle_missing_values(df_processed, missing_method)
                        st.success(f"Applied missing value handling: {missing_method}")
                    
                    if outlier_method != "none":
                        df_processed = handle_outliers(df_processed, numerical_cols, outlier_method, stats)
                        st.success(f"Applied outlier handling: {outlier_method}")
                    
                    if normalize_method != "none":
                        df_processed, _ = normalize_data(df_processed, numerical_cols, normalize_method)
                        st.success(f"Applied normalization: {normalize_method}")
                    
                    st.session_state.processed_data = df_processed
                    # Dynamically use only columns that remain after preprocessing
                    available_cols = [col for col in numerical_cols if col in df_processed.columns]
                    st.session_state.available_numerical_cols = available_cols
                    st.session_state.preprocessing_params = {
                        'missing_method': missing_method,
                        'outlier_method': outlier_method,
                        'normalize_method': normalize_method
                    }
                    st.session_state.current_stage = STAGES['PREPROCESSING_DONE']
                    st.success("Preprocessing completed!")

        # --- Step 3: Data Preprocessing (continued) ---
        if st.session_state.current_stage >= STAGES['PREPROCESSING_DONE']:
            st.header("3. Data Preprocessing")
            # Ensure we're only using columns that exist in the processed data
            available_cols = [col for col in st.session_state.features + [st.session_state.target] 
                            if col in st.session_state.processed_data.columns]
            st.session_state.available_numerical_cols = available_cols
            
            st.subheader("Updated Dataset Statistics")
            stats = calculate_statistics(st.session_state.processed_data, available_cols)
            st.dataframe(stats['basic'])
            csv_processed = convert_df_to_csv(st.session_state.processed_data)
            st.download_button(
                label="Download processed data as CSV",
                data=csv_processed,
                file_name=f"iot_data_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            # --- Step 4: Feature Selection ---
            st.sidebar.header("4. Feature Selection")
            st.header("4. Feature Selection")
            
            # Only use features that still exist in the dataset after preprocessing
            available_features = [col for col in st.session_state.features 
                                if col in st.session_state.processed_data.columns]
            
            # Update features in session state
            st.session_state.features = available_features
            
            # Check if target still exists
            if st.session_state.target not in st.session_state.processed_data.columns:
                st.error(f"Target column '{st.session_state.target}' was removed during preprocessing. Please regenerate data.")
                st.stop()
            
            # Get correlation with target
            try:
                corr_with_target = st.session_state.processed_data[available_cols].corr()[st.session_state.target].drop(st.session_state.target)
                st.subheader("Feature-Target Correlation")
                st.dataframe(corr_with_target.abs().sort_values(ascending=False).to_frame("|corr|").T)
                
                st.sidebar.subheader("Feature Selection Method")
                selection_method = st.sidebar.radio("Select features by:", ["Correlation (Top N)", "Manual"])
                
                if selection_method == "Correlation (Top N)":
                    corr_type = st.sidebar.radio(
                        "Correlation type:",
                        ["|corr| (absolute)", "+corr (positive)", "-corr (negative)"]
                    )
                    max_features = min(len(available_features), 10)
                    top_n = st.sidebar.slider("Number of top features:", 1, len(available_features), 
                                            max_features if max_features > 0 else 1)
                    
                    if corr_type == "|corr| (absolute)":
                        sorted_features = corr_with_target.abs().sort_values(ascending=False)
                    elif corr_type == "+corr (positive)":
                        sorted_features = corr_with_target[corr_with_target > 0].sort_values(ascending=False)
                    elif corr_type == "-corr (negative)":
                        sorted_features = corr_with_target[corr_with_target < 0].abs().sort_values(ascending=False)
                    else:
                        sorted_features = corr_with_target.abs().sort_values(ascending=False)
                    
                    if len(sorted_features) > 0:
                        selected_features = sorted_features.head(top_n).index.tolist()
                    else:
                        selected_features = []
                        st.warning("No features meet the correlation criteria. Try a different selection method.")
                else:
                    selected_features = st.sidebar.multiselect(
                        "Select features:",
                        available_features,
                        default=available_features
                    )
                
                feature_selection_button = st.sidebar.button("Apply Feature Selection")
                
                if feature_selection_button:
                    if not selected_features:
                        st.error("No features selected. Please select at least one feature.")
                    else:
                        # Reset stages from feature selection onwards
                        reset_from_stage(STAGES['FEATURE_SELECTION_DONE'])
                        st.session_state.selected_features = selected_features
                        st.session_state.current_stage = STAGES['FEATURE_SELECTION_DONE']
                        st.success(f"Selected {len(selected_features)} features for modeling.")
            except Exception as e:
                st.error(f"Error in feature selection: {str(e)}")
                st.info("This may happen if preprocessing removed too many values. Try different preprocessing parameters.")
                selected_features = []
            
        # --- Step 4: Feature Selection (continued) ---
        if st.session_state.current_stage >= STAGES['FEATURE_SELECTION_DONE']:
            if not st.session_state.selected_features:
                st.warning("No features are currently selected. Please go back to the Feature Selection step and select features.")
            else:
                st.write(f"**Selected Features ({len(st.session_state.selected_features)}):** {', '.join(st.session_state.selected_features)}")
                
                # Show correlation heatmap for selected features
                try:
                    st.subheader("Correlation Heatmap (Selected Features)")
                    corr_fig = plot_correlation_heatmap(
                        st.session_state.processed_data, 
                        st.session_state.selected_features + [st.session_state.target]
                    )
                    st.plotly_chart(corr_fig, key=f"corr_heatmap_{'_'.join(st.session_state.selected_features)}")
                    
                    # Preview reduced data
                    st.subheader("Preview: Data with Selected Features")
                    columns_to_show = st.session_state.selected_features + [st.session_state.target]
                    if 'timestamp' in st.session_state.processed_data.columns:
                        columns_to_show.append('timestamp')
                        
                    reduced_df = st.session_state.processed_data[columns_to_show].copy()
                    st.dataframe(reduced_df.head())
                    
                    # Download button
                    csv_selected = convert_df_to_csv(reduced_df)
                    st.download_button(
                        label="Download selected-feature data as CSV",
                        data=csv_selected,
                        file_name=f"iot_data_selected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    st.error(f"Error displaying feature selection results: {str(e)}")
                    st.info("This may happen if there are issues with the selected features. Try selecting different features.")
            
            # --- Step 5: Data Split ---
            st.sidebar.header("5. Train/Test Split")
            st.header("5. Train/Test Split")
            
            test_size = st.sidebar.slider("Test set size (%):", 10, 40, 20) / 100
            # Use the stored random seed, but allow overriding it
            if 'random_seed' in st.session_state and st.session_state.random_seed is not None:
                default_seed = st.session_state.random_seed
            else:
                default_seed = 42
            random_state = st.sidebar.number_input("Random seed:", 0, 999, default_seed, 
                help="Using the same seed ensures consistent train/test splits for model comparison")
            
            split_button = st.sidebar.button("Split Data")
            
            if split_button:
                # Check if we have selected features
                if not st.session_state.selected_features:
                    st.error("No features are selected. Please complete the Feature Selection step first.")
                else:
                    # Ensure all selected features still exist in the processed data
                    missing_features = [f for f in st.session_state.selected_features 
                                    if f not in st.session_state.processed_data.columns]
                    if missing_features:
                        st.error(f"Selected features {missing_features} no longer exist in the processed data. Please go back to Feature Selection.")
                    elif st.session_state.target not in st.session_state.processed_data.columns:
                        st.error(f"Target column '{st.session_state.target}' no longer exists in the processed data. Please regenerate data.")
                    else:
                        with st.spinner("Splitting data into train and test sets..."):
                            try:
                                # Reset stages from data split onwards
                                reset_from_stage(STAGES['DATA_SPLIT_DONE'])
                                
                                X = st.session_state.processed_data[st.session_state.selected_features]
                                y = st.session_state.processed_data[st.session_state.target]
                                
                                from sklearn.model_selection import train_test_split
                                X_train, X_test, y_train, y_test = train_test_split(
                                    X, y, test_size=test_size, random_state=random_state
                                )
                                
                                st.session_state.X_train = X_train
                                st.session_state.X_test = X_test
                                st.session_state.y_train = y_train
                                st.session_state.y_test = y_test
                                
                                st.session_state.split_params = {
                                    'test_size': test_size,
                                    'random_state': random_state,
                                    'selected_features': list(st.session_state.selected_features)
                                }
                                
                                st.session_state.current_stage = STAGES['DATA_SPLIT_DONE']
                                st.success(f"Data split into {len(X_train)} training samples and {len(X_test)} test samples.")
                            except Exception as e:
                                st.error(f"Error splitting data: {str(e)}")
                                st.info("This may happen if there are issues with the selected features or target. Check your data and feature selection.")
        
        # --- Step 5: Data Split (continued) ---
        if st.session_state.current_stage >= STAGES['DATA_SPLIT_DONE']:
            if st.session_state.X_train is not None and st.session_state.y_train is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Training Set")
                    st.write(f"X_train shape: {st.session_state.X_train.shape}")
                    st.write(f"y_train shape: {len(st.session_state.y_train)}")
                    st.dataframe(st.session_state.X_train.head())
                with col2:
                    st.subheader("Test Set")
                    st.write(f"X_test shape: {st.session_state.X_test.shape}")
                    st.write(f"y_test shape: {len(st.session_state.y_test)}")
                    st.dataframe(st.session_state.X_test.head())
            
            # --- Step 6: Normalization (New Step) ---
            st.sidebar.header("6. Normalization")
            st.header("6. Normalization")
            
            normalize_method = st.sidebar.selectbox(
                "Normalization method:",
                ["none", "min_max", "standard"],
                format_func=lambda x: {
                    "none": "No normalization", "min_max": "Min-Max Normalization (0-1)",
                    "standard": "Standardization (mean=0, std=1)"
                }[x],
                key="normalize_method_selectbox_step6"
            )
            
            # Only show this option if normalization is selected
            normalize_target = False
            if normalize_method != "none":
                normalize_target = st.sidebar.checkbox("Also normalize target variable", 
                                                value=True,
                                                help="Also apply normalization to the target variable. This helps with model training but changes the scale of predictions.",
                                                key="normalize_target_step6")
            
            normalize_button = st.sidebar.button("Apply Normalization")
            
            if normalize_button:
                if st.session_state.X_train is None or st.session_state.X_test is None:
                    st.error("Training and test data not available. Complete the Data Split step first.")
                else:
                    with st.spinner("Applying normalization to train/test data..."):
                        try:
                            # Reset stages from normalization onwards
                            reset_from_stage(STAGES['NORMALIZATION_DONE'])
                            
                            if normalize_method != "none":
                                # Check for non-numeric columns
                                non_numeric_cols = [col for col in st.session_state.X_train.columns 
                                                if st.session_state.X_train[col].dtype.kind not in 'fi']
                                
                                if non_numeric_cols:
                                    st.warning(f"Non-numeric columns found: {non_numeric_cols}. These will be excluded from normalization.")
                                    numeric_cols = [col for col in st.session_state.X_train.columns 
                                                if col not in non_numeric_cols]
                                    
                                    if not numeric_cols:
                                        st.error("No numeric columns available for normalization.")
                                        st.session_state.scaler = None
                                        st.session_state.normalization_params = {'method': 'none'}
                                        st.session_state.current_stage = STAGES['NORMALIZATION_DONE']
                                        st.stop()
                                else:
                                    numeric_cols = st.session_state.X_train.columns
                                
                                # Create DataFrames for normalized data
                                X_train_normalized = st.session_state.X_train.copy()
                                X_test_normalized = st.session_state.X_test.copy()
                                
                                # Perform normalization on numeric columns
                                try:
                                    # First, check that we have numeric data
                                    numeric_features = X_train_normalized[numeric_cols].select_dtypes(include=['number']).columns.tolist()
                                    
                                    if not numeric_features:
                                        st.warning("No numeric features found for normalization.")
                                        st.session_state.scaler = None
                                        st.session_state.normalization_params = {'method': 'none'}
                                        st.session_state.current_stage = STAGES['NORMALIZATION_DONE']
                                    else:
                                        # Apply normalization
                                        X_train_numeric, scaler = normalize_data(
                                            X_train_normalized[numeric_features], numeric_features, normalize_method
                                        )
                                        
                                        if scaler is None:
                                            st.warning("Normalization could not be applied. Using original data.")
                                            st.session_state.normalization_params = {'method': 'none'}
                                        else:
                                            # Directly reassign the normalized DataFrame
                                            X_train_normalized = X_train_numeric
                                            
                                            # Transform test data using the same scaler
                                            try:
                                                # Apply the same transformation to test data
                                                X_test_values = scaler.transform(X_test_normalized[numeric_features])
                                                X_test_normalized_values = pd.DataFrame(
                                                    X_test_values, 
                                                    columns=numeric_features,
                                                    index=X_test_normalized.index
                                                )
                                                
                                                # Replace just the normalized columns
                                                for col in numeric_features:
                                                    X_test_normalized[col] = X_test_normalized_values[col]
                                                    
                                                st.session_state.X_train = X_train_normalized
                                                st.session_state.X_test = X_test_normalized
                                                st.session_state.scaler = scaler
                                                
                                                # Also normalize the target variable if requested and it has numeric values
                                                if normalize_target and normalize_method != "none" and st.session_state.y_train.dtype.kind in 'fi':
                                                    # Create a separate scaler for the target variable
                                                    if normalize_method == "min_max":
                                                        target_scaler = MinMaxScaler()
                                                    elif normalize_method == "standard":
                                                        target_scaler = StandardScaler()
                                                        
                                                    # Reshape for sklearn's 2D requirement
                                                    y_train_reshaped = st.session_state.y_train.values.reshape(-1, 1)
                                                    y_test_reshaped = st.session_state.y_test.values.reshape(-1, 1)
                                                    
                                                    # Fit on training data and transform both train and test
                                                    y_train_normalized = target_scaler.fit_transform(y_train_reshaped).flatten()
                                                    y_test_normalized = target_scaler.transform(y_test_reshaped).flatten()
                                                    
                                                    # Update the session state with normalized target values
                                                    st.session_state.y_train = pd.Series(y_train_normalized, index=st.session_state.y_train.index)
                                                    st.session_state.y_test = pd.Series(y_test_normalized, index=st.session_state.y_test.index)
                                                    st.session_state.target_scaler = target_scaler
                                                    target_normalized = True
                                                else:
                                                    target_normalized = False
                                                
                                                st.session_state.normalization_params = {
                                                    'method': normalize_method,
                                                    'normalized_columns': numeric_features,
                                                    'target_normalized': target_normalized
                                                }
                                                st.success(f"Applied {normalize_method} normalization to {len(numeric_features)} numeric features.")
                                            except Exception as e:
                                                st.error(f"Error applying normalization to test data: {str(e)}")
                                                st.session_state.normalization_params = {'method': 'none'}
                                except Exception as e:
                                    st.error(f"Error during normalization process: {str(e)}")
                                    st.session_state.normalization_params = {'method': 'none'}
                            else:
                                st.session_state.scaler = None
                                st.session_state.normalization_params = {
                                    'method': 'none'
                                }
                                st.info("No normalization applied.")
                            
                            st.session_state.current_stage = STAGES['NORMALIZATION_DONE']
                        except Exception as e:
                            st.error(f"Error applying normalization: {str(e)}")
                            st.info("This may happen if there are issues with the data. Try different preprocessing or normalization methods.")
        
        # --- Step 6: Normalization (continued) ---
        if st.session_state.current_stage >= STAGES['NORMALIZATION_DONE']:
            st.subheader("Normalized Data Preview")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Normalized Training Data:**")
                if st.session_state.X_train is not None and not st.session_state.X_train.empty:
                    st.dataframe(st.session_state.X_train.head())
                else:
                    st.warning("No training data available.")
            with col2:
                st.write("**Normalized Test Data:**")
                if st.session_state.X_test is not None and not st.session_state.X_test.empty:
                    st.dataframe(st.session_state.X_test.head())
                else:
                    st.warning("No test data available.")
            
            if st.session_state.normalization_params.get('method') != 'none':
                st.info(f"Normalization method: {st.session_state.normalization_params.get('method')}")
                if 'normalized_columns' in st.session_state.normalization_params:
                    st.info(f"Normalized columns: {', '.join(st.session_state.normalization_params['normalized_columns'])}")
                if st.session_state.normalization_params.get('target_normalized', False):
                    st.info(f"Target variable '{st.session_state.target}' was also normalized")
                    # Show the min-max values of the target variable
                    y_min = st.session_state.y_train.min()
                    y_max = st.session_state.y_train.max()
                    st.info(f"Target variable range: min={y_min:.4f}, max={y_max:.4f}")
            else:
                st.info("No normalization was applied.")
            
            # --- Step 7: Model Training ---
            st.sidebar.header("7. Model Training")
            st.header("7. Model Training")
            
            # Check if CatBoost and XGBoost are available
            try:
                import catboost
                catboost_available = True
            except ImportError:
                catboost_available = False
                
            try:
                import xgboost
                xgboost_available = True
            except ImportError:
                xgboost_available = False
            
            # Prepare model options based on availability
            base_models = {
                "linear": "Linear Regression", 
                "ridge": "Ridge Regression", 
                "lasso": "Lasso Regression",
                "random_forest": "Random Forest", 
                "gradient_boosting": "Gradient Boosting", 
                "svr": "Support Vector Regression"
            }
            
            # Add advanced models if available
            if catboost_available:
                base_models["catboost"] = "CatBoost"
            if xgboost_available:
                base_models["xgboost"] = "XGBoost"
            
            model_type = st.sidebar.selectbox(
                "Select model type:",
                list(base_models.keys()),
                format_func=lambda x: base_models[x]
            )
            
            model_params = {}
            if model_type == "ridge":
                alpha = st.sidebar.slider("Alpha (regularization strength):", 0.01, 10.0, 1.0)
                model_params["alpha"] = alpha
            elif model_type == "lasso":
                alpha = st.sidebar.slider("Alpha (regularization strength):", 0.01, 10.0, 1.0)
                model_params["alpha"] = alpha
            elif model_type == "random_forest":
                n_estimators = st.sidebar.slider("Number of trees:", 10, 200, 100)
                max_depth = st.sidebar.slider("Maximum depth:", 2, 20, 10)
                model_params["n_estimators"] = n_estimators
                model_params["max_depth"] = max_depth
                model_params["random_state"] = st.session_state.random_seed
            elif model_type == "gradient_boosting":
                n_estimators = st.sidebar.slider("Number of boosting stages:", 10, 200, 100)
                learning_rate = st.sidebar.slider("Learning rate:", 0.01, 0.5, 0.1)
                max_depth = st.sidebar.slider("Maximum depth:", 2, 10, 3)
                model_params["n_estimators"] = n_estimators
                model_params["learning_rate"] = learning_rate
                model_params["max_depth"] = max_depth
                model_params["random_state"] = st.session_state.random_seed
            elif model_type == "svr":
                kernel = st.sidebar.selectbox("Kernel:", ["linear", "poly", "rbf", "sigmoid"])
                C = st.sidebar.slider("C (regularization parameter):", 0.1, 10.0, 1.0)
                model_params["kernel"] = kernel
                model_params["C"] = C
            elif model_type == "catboost":
                iterations = st.sidebar.slider("Iterations:", 100, 2000, 1000, 100)
                learning_rate = st.sidebar.slider("Learning rate:", 0.01, 0.5, 0.1)
                depth = st.sidebar.slider("Depth:", 3, 10, 6)
                loss_function = st.sidebar.selectbox("Loss function:", ["RMSE", "MAE", "MAPE"], index=0)
                early_stopping = st.sidebar.checkbox("Enable early stopping", value=True)
                early_stopping_rounds = st.sidebar.slider("Early stopping rounds:", 10, 100, 50, 10) if early_stopping else None
                eval_metric = st.sidebar.selectbox("Evaluation metric:", ["RMSE", "MAE", "MAPE"], index=0)
                model_params["iterations"] = iterations
                model_params["learning_rate"] = learning_rate
                model_params["depth"] = depth
                model_params["loss_function"] = loss_function
                model_params["eval_metric"] = eval_metric
                model_params["random_seed"] = st.session_state.random_seed
                model_params["verbose"] = 1
                if early_stopping:
                    model_params["early_stopping_rounds"] = early_stopping_rounds
                    model_params["use_best_model"] = True
            elif model_type == "xgboost":
                n_estimators = st.sidebar.slider("Number of trees:", 100, 2000, 1000, 100)
                learning_rate = st.sidebar.slider("Learning rate:", 0.01, 0.5, 0.1)
                max_depth = st.sidebar.slider("Maximum depth:", 3, 10, 6)
                objective_options = {"RMSE": "reg:squarederror", "MAE": "reg:absoluteerror", "MAPE": "reg:squarederror"}
                objective_display = st.sidebar.selectbox("Objective function:", list(objective_options.keys()), index=0)
                objective = objective_options[objective_display]
                subsample = st.sidebar.slider("Subsample ratio:", 0.5, 1.0, 0.8, 0.1)
                colsample_bytree = st.sidebar.slider("Column sample by tree:", 0.5, 1.0, 0.8, 0.1)
                early_stopping = st.sidebar.checkbox("Enable early stopping", value=True, key="xgb_early_stopping")
                early_stopping_rounds = st.sidebar.slider("Early stopping rounds:", 10, 100, 50, 10, key="xgb_esr") if early_stopping else None
                eval_metric_options = {"RMSE": "rmse", "MAE": "mae", "MAPE": "mape"}
                eval_metric_display = st.sidebar.selectbox("Evaluation metric:", list(eval_metric_options.keys()), index=0)
                eval_metric = eval_metric_options[eval_metric_display]
                model_params["n_estimators"] = n_estimators
                model_params["learning_rate"] = learning_rate
                model_params["max_depth"] = max_depth
                model_params["objective"] = objective
                model_params["subsample"] = subsample
                model_params["colsample_bytree"] = colsample_bytree
                model_params["random_state"] = st.session_state.random_seed
                model_params["eval_metric"] = eval_metric
                model_params["verbose"] = 1
                if early_stopping:
                    model_params["early_stopping_rounds"] = early_stopping_rounds
            
            model_name = st.sidebar.text_input("Model name:", f"{model_type}_{datetime.now().strftime('%H%M%S')}")
            
            # Update the train button text based on the model
            train_button_text = f"Train {base_models[model_type]} Model"
            train_button = st.sidebar.button(train_button_text)
            
            if train_button:
                if st.session_state.X_train is None or st.session_state.y_train is None:
                    st.error("Training data not available. Complete the Data Split and Normalization steps first.")
                elif len(st.session_state.X_train) == 0 or len(st.session_state.y_train) == 0:
                    st.error("Training data is empty. Check your preprocessing and split settings.")
                else:
                    with st.spinner(f"Training {model_type} model..."):
                        try:
                            # For CatBoost and XGBoost, pass test data for validation during training
                            if model_type in ["catboost", "xgboost"]:
                                model = train_model(
                                    st.session_state.X_train, st.session_state.y_train, model_type,
                                    X_test=st.session_state.X_test, y_test=st.session_state.y_test,
                                    **model_params
                                )
                            else:
                                model = train_model(
                                    st.session_state.X_train, st.session_state.y_train, model_type, **model_params
                                )
                            
                            metrics, y_train_pred, y_test_pred = evaluate_model(
                                model, st.session_state.X_train, st.session_state.X_test, 
                                st.session_state.y_train, st.session_state.y_test
                            )
                            
                            # Generate learning curve for all model types
                            learning_curve_fig, learning_history = plot_learning_curve(
                                model, 
                                st.session_state.X_train, 
                                st.session_state.X_test, 
                                st.session_state.y_train, 
                                st.session_state.y_test,
                                model_type,
                                **model_params
                            )
                            
                            # Store the model, metrics, and learning history in session state
                            st.session_state.models.append(model)
                            st.session_state.metrics.append(metrics)
                            st.session_state.model_names.append(model_name)
                            
                            # Store learning history if not present
                            if 'learning_histories' not in st.session_state:
                                st.session_state.learning_histories = {}
                            st.session_state.learning_histories[model_name] = learning_history
                            
                            st.session_state.current_stage = STAGES['MODEL_TRAINED']
                            st.success(f"Model '{model_name}' trained successfully!")
                        except Exception as e:
                            st.error(f"Error training model: {str(e)}")
                            st.info("This may happen due to issues with the data or model parameters. Try different preprocessing or modeling options.")
        
        # --- Step 7: Model Training (continued) ---
        if st.session_state.current_stage >= STAGES['MODEL_TRAINED'] and len(st.session_state.models) > 0:
            # Add model selection dropdown
            st.subheader("📊 Model Selection")
            
            # Create a selectbox to choose which model to display
            if len(st.session_state.model_names) > 1:
                selected_model_name = st.selectbox(
                    "Select model to display:",
                    st.session_state.model_names,
                    index=len(st.session_state.model_names) - 1  # Default to most recent model
                )
                selected_model_idx = st.session_state.model_names.index(selected_model_name)
            else:
                # If only one model, use that one
                selected_model_idx = 0
                selected_model_name = st.session_state.model_names[0]
                st.info(f"Current trained model: {selected_model_name}")
            
            # Display results for the selected model
            selected_model = st.session_state.models[selected_model_idx]
            selected_metrics = st.session_state.metrics[selected_model_idx]
            
            st.subheader(f"Model Performance: {selected_model_name}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Training Dataset Metrics:**")
                st.write(f"- MSE: {selected_metrics['train']['mse']:.4f}")
                st.write(f"- RMSE: {selected_metrics['train']['rmse']:.4f}")
                st.write(f"- MAE: {selected_metrics['train']['mae']:.4f}")
                st.write(f"- R²: {selected_metrics['train']['r2']:.4f}")
            with col2:
                st.write("**Test Dataset Metrics:**")
                st.write(f"- MSE: {selected_metrics['test']['mse']:.4f}")
                st.write(f"- RMSE: {selected_metrics['test']['rmse']:.4f}")
                st.write(f"- MAE: {selected_metrics['test']['mae']:.4f}")
                st.write(f"- R²: {selected_metrics['test']['r2']:.4f}")
            
            # Get predictions for visualization
            try:
                # Try to get predictions from metrics dictionary
                if 'predictions' in selected_metrics['train'] and 'predictions' in selected_metrics['test']:
                    y_train_pred = selected_metrics['train']['predictions']
                    y_test_pred = selected_metrics['test']['predictions']
                else:
                    # If not in metrics, generate them directly from the model
                    st.warning("Saved predictions not found. Generating predictions directly from the model...")
                    y_train_pred = selected_model.predict(st.session_state.X_train)
                    y_test_pred = selected_model.predict(st.session_state.X_test)
                
                # Create tabs for different visualizations
                viz_tabs = st.tabs([
                    "📈 Learning Curve", 
                    "🌟 Feature Importance", 
                    "🎯 Prediction Results", 
                    "📉 Residual Analysis"
                ])
                
                # Tab 1: Learning Curve
                with viz_tabs[0]:
                    st.subheader("📈 Learning Curve")
                    
                    # Extract model type from the name
                    model_type = selected_model_name.split('_')[0]
                    
                    # Check if we have a learning history for this model
                    if 'learning_histories' in st.session_state and selected_model_name in st.session_state.learning_histories:
                        # Generate the learning curve plot
                        learning_curve_fig, _ = plot_learning_curve(
                            selected_model, 
                            st.session_state.X_train, 
                            st.session_state.X_test, 
                            st.session_state.y_train, 
                            st.session_state.y_test,
                            model_type
                        )
                        
                        if learning_curve_fig:
                            st.plotly_chart(learning_curve_fig, use_container_width=True)
                        else:
                            st.info("Learning curve visualization is not available for this model type.")
                    else:
                        st.info("Learning history is not available for this model.")
                
                # Tab 2: Feature Importance
                with viz_tabs[1]:
                    st.subheader("🌟 Feature Importance")
                    
                    # Create feature importance plot
                    try:
                        model_type_name = selected_model_name.split('_')[0]  # Extract model type from name
                        if model_type_name in ["linear", "ridge", "lasso", "random_forest", "gradient_boosting", "catboost", "xgboost"]:
                            importance_fig, importance_df = plot_feature_importance(
                                selected_model, st.session_state.selected_features, model_type_name
                            )
                            
                            if importance_fig and importance_df is not None:
                                st.plotly_chart(importance_fig, use_container_width=True)
                                
                                # Display the importance values in a table
                                st.subheader("Feature Importance Values")
                                st.dataframe(importance_df)
                                
                                # Add download button for feature importance
                                csv = convert_df_to_csv(importance_df)
                                st.download_button(
                                    label="Download Feature Importance CSV",
                                    data=csv,
                                    file_name=f"{selected_model_name}_feature_importance.csv",
                                    mime="text/csv",
                                )
                            else:
                                st.info("Feature importance visualization is not available for this model type.")
                        else:
                            st.info("Feature importance visualization is not available for this model type.")
                    except Exception as e:
                        st.error(f"Error displaying feature importance: {str(e)}")
                        st.info("This error may occur if there are issues with the model structure or feature names.")
                
                # Tab 3: Predictions
                with viz_tabs[2]:
                    st.subheader("🎯 Prediction Visualization")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        train_fig = plot_model_predictions(
                            st.session_state.y_train, y_train_pred, title="Training Dataset: Actual vs Predicted"
                        )
                        st.plotly_chart(train_fig, use_container_width=True)
                    with col2:
                        test_fig = plot_model_predictions(
                            st.session_state.y_test, y_test_pred, title="Test Dataset: Actual vs Predicted"
                        )
                        st.plotly_chart(test_fig, use_container_width=True)
                    
                    # Option to download predictions
                    pred_df = pd.DataFrame({
                        'Actual': st.session_state.y_test.values,
                        'Predicted': y_test_pred
                    })
                    
                    csv_pred = convert_df_to_csv(pred_df)
                    st.download_button(
                        label="Download Test Predictions CSV",
                        data=csv_pred,
                        file_name=f"{selected_model_name}_predictions.csv",
                        mime="text/csv",
                    )
                
                # Tab 4: Residuals
                with viz_tabs[3]:
                    st.subheader("📉 Residual Analysis")
                    
                    # Calculate residuals
                    train_residuals = st.session_state.y_train - y_train_pred
                    test_residuals = st.session_state.y_test - y_test_pred
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Residuals vs Predicted plot
                        residual_fig = go.Figure()
                        residual_fig.add_trace(
                            go.Scatter(
                                x=y_test_pred, 
                                y=test_residuals, 
                                mode='markers',
                                name='Test Residuals',
                                marker=dict(size=8, opacity=0.7, color='red')
                            )
                        )
                        residual_fig.add_hline(
                            y=0, 
                            line=dict(color='black', dash='dash')
                        )
                        residual_fig.update_layout(
                            title="Predicted vs Residuals",
                            xaxis_title="Predicted Values",
                            yaxis_title="Residuals",
                            height=400
                        )
                        st.plotly_chart(residual_fig, use_container_width=True)
                    
                    with col2:
                        # Residual histogram
                        hist_fig = go.Figure()
                        hist_fig.add_trace(
                            go.Histogram(
                                x=test_residuals,
                                nbinsx=30,
                                marker=dict(color='red', opacity=0.7),
                                name='Test Residuals'
                            )
                        )
                        hist_fig.update_layout(
                            title="Residual Distribution",
                            xaxis_title="Residual Values",
                            yaxis_title="Frequency",
                            height=400
                        )
                        st.plotly_chart(hist_fig, use_container_width=True)
                    
                    # Residual statistics
                    residual_stats = pd.DataFrame({
                        'Statistic': ['Mean', 'Median', 'Std Dev', 'Min', 'Max'],
                        'Training Dataset Residuals': [
                            train_residuals.mean(),
                            np.median(train_residuals),
                            train_residuals.std(),
                            train_residuals.min(),
                            train_residuals.max()
                        ],
                        'Test Dataset Residuals': [
                            test_residuals.mean(),
                            np.median(test_residuals),
                            test_residuals.std(),
                            test_residuals.min(),
                            test_residuals.max()
                        ]
                    })
                    
                    st.subheader("Residual Statistics")
                    st.dataframe(residual_stats.round(4))
                    
            except Exception as e:
                st.error(f"Error in prediction visualization: {str(e)}")
                st.info("This error may occur if there are data type incompatibilities or other issues with model predictions.")

    # Add back the model comparison section after the tabs
    if len(st.session_state.models) > 1:
        try:
            st.header("8. Model Comparison")
            comparison_fig, comparison_df = compare_models(
                st.session_state.models, st.session_state.metrics, st.session_state.model_names
            )
            st.subheader("Model Performance Comparison")
            st.plotly_chart(comparison_fig, use_container_width=True)
            st.dataframe(comparison_df)
            
            best_idx = comparison_df['Test RMSE'].idxmin()
            best_model_name = comparison_df.loc[best_idx, 'Model']
            st.success(f"Best performing model based on RMSE: **{best_model_name}** (RMSE = {comparison_df.loc[best_idx, 'Test RMSE']:.4f})")
        except Exception as e:
            st.error(f"Error in model comparison: {str(e)}")
            st.info("This error may occur if model metrics are incompatible.")

    st.markdown("---")
    st.markdown("IoT Data Simulation and Modeling Tool - Created with Kenny using Streamlit") 

if __name__ == "__main__":
    main() 