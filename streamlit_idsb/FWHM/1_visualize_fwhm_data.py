import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import argparse
import glob # 추가: 파일 패턴 검색용
from sklearn.decomposition import PCA # Added PCA
from scipy import stats # Added stats for QQ plot

# 프로젝트 루트 디렉토리 경로 계산 (FWHM 폴더의 부모 폴더)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path에 프로젝트 루트 추가
if project_root not in sys.path:
    sys.path.append(project_root)

# 이제 utils 패키지 임포트 가능
try:
    from utils.style import ECOPRO_COLORS, ECOPRO_SEQUENTIAL # 스타일 임포트
except ImportError:
    print("Warning: utils.style not found. Using default colors.")
    ECOPRO_COLORS = {
        'dark_blue': '#164193',
        'light_blue': '#26A9E0',
        'orange': '#F58220',
        'gray': '#A9A9A9',
        'blue_dark_light': '#5D7DB8', # Example intermediate color
        'text': '#333333'
    }
    ECOPRO_SEQUENTIAL = px.colors.sequential.Blues

def parse_arguments():
    """
    커맨드 라인 인자를 파싱합니다.
    """
    parser = argparse.ArgumentParser(description='FWHM 데이터 시각화 스크립트')
    parser.add_argument('--normalized_file', type=str, 
                        help='정규화된 특정 데이터 파일 (CSV). 지정하지 않으면 모든 normalized_data*.csv 파일 처리')
    parser.add_argument('--output_dir', type=str, 
                        help='시각화 결과 기본 저장 디렉토리 (기본값: "visualization")')
    return parser.parse_args()

# 데이터 로드 함수
def load_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Data file not found at {file_path}")
        print("Please run generate_fwhm_data.py first.")
        sys.exit(1)
    print(f"Loading data from {file_path}...")
    
    # lot_id를 명시적으로 string 타입으로 로드
    df = pd.read_csv(file_path, dtype={'lot_id': str})
    
    # lot_id 열이 있는지 확인하고 string 타입으로 변환
    if 'lot_id' in df.columns and not pd.api.types.is_string_dtype(df['lot_id']):
        print("Converting lot_id to string type...")
        df['lot_id'] = df['lot_id'].astype(str)
    
    print(f"Loaded data shape: {df.shape}")
    return df

# 데이터 칼럼 분류 함수
def categorize_columns(df):
    """
    데이터프레임의 칼럼을 타입(Li, Pre_L, Pre_S, Qcp 등)별로 분류합니다.
    """
    # 필수 칼럼
    target_col = 'Target_F' if 'Target_F' in df.columns else None
    id_col = 'lot_id' if 'lot_id' in df.columns else None
    
    # 특성 칼럼 분류
    feature_types = {
        'Li': [],
        'Pre_L': [],
        'Pre_S': [],
        'Qcp': []  # 기타 모든 칼럼은 Qcp로 분류
    }
    
    for col in df.columns:
        if col == target_col or col == id_col:
            continue
            
        # 칼럼 이름의 접두사로 분류
        if col.startswith('Li'):
            feature_types['Li'].append(col)
        elif col.startswith('Pre_L'):
            feature_types['Pre_L'].append(col)
        elif col.startswith('Pre_S'):
            feature_types['Pre_S'].append(col)
        elif col.startswith('Qcp'):
            # 다른 모든 컬럼은 Qcp로 분류
            feature_types['Qcp'].append(col)
    
    # 모든 특성 칼럼 리스트
    all_feature_cols = []
    for cols in feature_types.values():
        all_feature_cols.extend(cols)
    
    # 모든 수치형 칼럼 (특성 + 타겟)
    all_numeric_cols = all_feature_cols.copy()
    if target_col:
        all_numeric_cols.append(target_col)
    
    return {
        'target_col': target_col,
        'id_col': id_col,
        'feature_types': feature_types,
        'all_feature_cols': all_feature_cols,
        'all_numeric_cols': all_numeric_cols
    }

# 상관관계 행렬 시각화
def visualize_correlation_matrix(df_final, column_info, visualization_dir):
    print("Calculating and visualizing feature correlations...")
    all_feature_cols = column_info['all_feature_cols']
    target_col = column_info['target_col']
    
    if not target_col:
        print("Error: Target column 'Target_F' not found for correlation analysis.")
        return
    
    # 각 특성 타입에서 최대 3개씩 선택
    selected_features = []
    for feature_type, cols in column_info['feature_types'].items():
        selected_features.extend(cols[:min(3, len(cols))])
    
    # 타겟 칼럼 추가
    selected_features = selected_features + [target_col]
    
    # 선택한 특성이 데이터프레임에 존재하는지 확인
    existing_features = [f for f in selected_features if f in df_final.columns]
    if len(existing_features) < len(selected_features):
        print(f"Warning: Some selected features for correlation plot not found: {set(selected_features) - set(existing_features)}")
    if not existing_features:
        print("Error: No selected features found for correlation plot.")
        return
        
    corr_df = df_final[existing_features].corr()

    fig_corr = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns,
        y=corr_df.columns,
        colorscale=[[0, ECOPRO_COLORS['light_blue']], [0.5, 'white'], [1, ECOPRO_COLORS['orange']]],
        zmin=-1, zmax=1,
        text=np.round(corr_df.values, 2),
        texttemplate='%{text}',
        hoverinfo='text'
    ))
    
    fig_corr.update_layout(
        title=dict(
            text='선택된 특성의 상관관계 행렬 (정규화된 데이터)',
            font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
        ),
        height=800,
        width=800,
        font=dict(color=ECOPRO_COLORS['text'])
    )
    
    save_path = os.path.join(visualization_dir, 'correlation_matrix.html')
    fig_corr.write_html(save_path)
    print(f"Correlation matrix saved to {save_path}")

# 타겟 변수와의 특성 상관관계 시각화
def visualize_feature_target_correlation(df_final, column_info, visualization_dir):
    print("Visualizing feature importance (correlation with target)...")
    target_col = column_info['target_col']
    numeric_cols = column_info['all_numeric_cols']
    
    if not target_col:
        print("Error: 'Target_F' column not found for correlation analysis.")
        return
        
    # id_col 제외
    numeric_cols_in_df = [col for col in numeric_cols if col in df_final.columns and col != column_info['id_col']]
    
    target_corr = df_final[numeric_cols_in_df].corr()[target_col].drop(target_col).sort_values(ascending=False)
    top_features = target_corr.head(20)
    bottom_features = target_corr.tail(20)
    
    fig_feat = make_subplots(rows=2, cols=1, 
                            subplot_titles=['상위 20개 특성 (타겟과의 상관관계)',
                                         '하위 20개 특성 (타겟과의 상관관계)'])
    
    fig_feat.add_trace(
        go.Bar(
            x=top_features.values,
            y=top_features.index,
            orientation='h',
            marker_color=ECOPRO_COLORS['light_blue'],
            text=np.round(top_features.values, 3),
            textposition='auto'
        ),
        row=1, col=1
    )
    
    fig_feat.add_trace(
        go.Bar(
            x=bottom_features.values,
            y=bottom_features.index,
            orientation='h',
            marker_color=ECOPRO_COLORS['orange'],
            text=np.round(bottom_features.values, 3),
            textposition='auto'
        ),
        row=2, col=1
    )
    
    fig_feat.update_layout(
        title=dict(
            text='타겟 변수와의 특성 상관관계 (정규화된 데이터)',
            font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
        ),
        height=900,
        width=900,
        showlegend=False,
        font=dict(color=ECOPRO_COLORS['text'])
    )
    
    fig_feat.update_xaxes(title_text='상관관계', row=1, col=1)
    fig_feat.update_xaxes(title_text='상관관계', row=2, col=1)
    
    save_path = os.path.join(visualization_dir, 'feature_target_correlation.html')
    fig_feat.write_html(save_path)
    print(f"Feature target correlation saved to {save_path}")
    return top_features # Return for use in other plots

# Parallel Coordinates Plot 시각화
def visualize_parallel_coordinates(df_final, top_features, column_info, visualization_dir):
    print("Generating parallel coordinates plot...")
    target_col = column_info['target_col']
    
    if not target_col:
        print("Error: 'Target_F' column not found for parallel coordinates plot.")
        return
        
    if top_features is None or top_features.empty:
        print("Skipping parallel coordinates plot: No top features available.")
        return
        
    top_5_features = list(top_features.head(5).index)
    cols_for_plot = top_5_features + [target_col]
    existing_cols = [f for f in cols_for_plot if f in df_final.columns]
    
    if len(existing_cols) < 2: # Need at least two columns
        print("Error: Not enough columns found for parallel coordinates plot.")
        return
        
    n_samples = df_final.shape[0]
    pair_df = df_final[existing_cols].sample(min(500, n_samples))

    dimensions = []
    for col in existing_cols:
        dimensions.append(dict(
            label=col,
            values=pair_df[col]
        ))
    
    fig_parallel = go.Figure(data=
        go.Parcoords(
            line=dict(color=pair_df[target_col] if target_col in pair_df else None,
                     colorscale='Viridis',
                     showscale=True,
                     cmin=pair_df[target_col].min() if target_col in pair_df else None,
                     cmax=pair_df[target_col].max() if target_col in pair_df else None),
            dimensions=dimensions
        )
    )
    
    fig_parallel.update_layout(
        title='Parallel Coordinates Plot of Top Correlated Features (Normalized Data)',
        height=600,
        width=1000
    )
    
    save_path = os.path.join(visualization_dir, 'parallel_coords.html')
    fig_parallel.write_html(save_path)
    print(f"Parallel coordinates plot saved to {save_path}")

# Scatter Matrix 시각화
def visualize_scatter_matrix(df_final, top_features, column_info, visualization_dir):
    print("Generating scatter matrix plot...")
    target_col = column_info['target_col']
    
    if not target_col:
        print("Error: 'Target_F' column not found for scatter matrix plot.")
        return
        
    if top_features is None or top_features.empty:
        print("Skipping scatter matrix plot: No top features available.")
        return

    top_5_features = list(top_features.head(5).index)
    cols_for_plot = top_5_features + [target_col]
    existing_cols = [f for f in cols_for_plot if f in df_final.columns]
    
    if len(existing_cols) < 2:
         print("Error: Not enough columns found for scatter matrix plot.")
         return
         
    n_samples = df_final.shape[0]
    pair_df = df_final[existing_cols].sample(min(500, n_samples))

    fig_scatter = px.scatter_matrix(
        pair_df,
        dimensions=existing_cols,
        color=target_col if target_col in pair_df else None,
        color_continuous_scale='Viridis',
        opacity=0.7
    )
    
    fig_scatter.update_layout(
        title='Scatter Matrix of Top Correlated Features (Normalized Data)',
        height=900,
        width=900
    )
    
    save_path = os.path.join(visualization_dir, 'scatter_matrix.html')
    fig_scatter.write_html(save_path)
    print(f"Scatter matrix plot saved to {save_path}")

# 타겟 변수 분포 시각화
def visualize_target_distribution(df_normalized, column_info, visualization_dir):
    print("\nVisualizing target variable (Target_F) distribution...")
    target_col = column_info['target_col']
    
    if not target_col:
        print(f"Error: Target column not found. Skipping target distribution plot.")
        return

    target_data = df_normalized[target_col].dropna()

    fig = make_subplots(rows=1, cols=2, subplot_titles=[f'{target_col} Distribution', f'{target_col} QQ Plot'])

    # Histogram
    fig.add_trace(
        go.Histogram(x=target_data, nbinsx=50, name='Histogram', marker_color=ECOPRO_COLORS['dark_blue'], opacity=0.7),
        row=1, col=1
    )

    # QQ Plot
    qq_data = stats.probplot(target_data, dist="norm")
    theoretical_quantiles = qq_data[0][0]
    sample_quantiles = qq_data[0][1]

    fig.add_trace(
        go.Scatter(x=theoretical_quantiles, y=sample_quantiles, mode='markers', name='Data Quantiles', marker=dict(color=ECOPRO_COLORS['light_blue'])),
        row=1, col=2
    )
    # Add reference line y=x
    min_q = min(theoretical_quantiles.min(), sample_quantiles.min())
    max_q = max(theoretical_quantiles.max(), sample_quantiles.max())
    fig.add_trace(
        go.Scatter(x=[min_q, max_q], y=[min_q, max_q], mode='lines', name='Reference Line', line=dict(color=ECOPRO_COLORS['orange'], dash='dash')),
        row=1, col=2
    )

    fig.update_layout(
        title=dict(
            text=f'Target Variable ({target_col}) Distribution Analysis (Normalized Data)',
            font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
        ),
        height=500,
        width=1000,
        showlegend=False,
        font=dict(color=ECOPRO_COLORS['text'])
    )
    fig.update_xaxes(title_text=f'{target_col} Value', row=1, col=1)
    fig.update_yaxes(title_text='Frequency', row=1, col=1)
    fig.update_xaxes(title_text='Theoretical Quantiles (Normal Distribution)', row=1, col=2)
    fig.update_yaxes(title_text='Sample Quantiles', row=1, col=2)

    save_path = os.path.join(visualization_dir, 'target_distribution_analysis.html')
    fig.write_html(save_path)
    print(f"Target distribution analysis saved to {save_path}")

# PCA 시각화
def visualize_pca(df_normalized, column_info, visualization_dir):
    print("\nPerforming PCA and visualizing first two components...")
    feature_cols = column_info['all_feature_cols']
    target_col = column_info['target_col']
    
    if not feature_cols:
        print("Error: No feature columns found for PCA.")
        return
    if not target_col:
        print("Error: Target column not found for PCA coloring.")
        return

    # 데이터프레임에 존재하는 특성만 선택
    feature_cols = [col for col in feature_cols if col in df_normalized.columns]
    
    if not feature_cols:
        print("Error: No valid feature columns for PCA.")
        return

    X = df_normalized[feature_cols].dropna()
    y = df_normalized.loc[X.index, target_col] # Align target with potentially dropped rows

    if X.empty:
        print("Error: No data left for PCA after dropping NaNs.")
        return

    pca = PCA(n_components=2)
    try:
        principal_components = pca.fit_transform(X)
        explained_variance_ratio = pca.explained_variance_ratio_
    except Exception as e:
        print(f"Error during PCA fitting: {e}")
        return

    pca_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2'], index=X.index)
    pca_df[target_col] = y

    fig_pca = px.scatter(
        pca_df,
        x='PC1',
        y='PC2',
        color=target_col,
        color_continuous_scale=px.colors.sequential.Viridis,
        opacity=0.8,
        title=f'PCA of Features (Normalized Data)<br>Explained Variance: PC1={explained_variance_ratio[0]:.2%}, PC2={explained_variance_ratio[1]:.2%}',
        labels={'color': target_col}
    )

    fig_pca.update_layout(
        height=700,
        width=900,
        title_font=dict(color=ECOPRO_COLORS['dark_blue'], size=20),
        font=dict(color=ECOPRO_COLORS['text'])
    )
    fig_pca.update_traces(marker=dict(size=8))

    save_path = os.path.join(visualization_dir, 'pca_visualization.html')
    fig_pca.write_html(save_path)
    print(f"PCA visualization saved to {save_path}")

# --- Main Execution ---
if __name__ == "__main__":
    # 커맨드 라인 인자 파싱
    args = parse_arguments()
    
    # 기본 설정
    OUTPUT_DIR = '.'  # 현재 디렉토리 (FWHM 폴더)
    
    # 정규화된 데이터 파일 결정 (단일 파일 또는 모든 파일)
    if args.normalized_file:
        normalized_data_files = [args.normalized_file]
        print(f"지정된 정규화 데이터 파일: {args.normalized_file}")
    else:
        # normalized_data로 시작하는 모든 CSV 파일 검색
        normalized_data_files = glob.glob("normalized_data*.csv")
        
        if not normalized_data_files:
            print("경고: 'normalized_data'로 시작하는 CSV 파일을 찾을 수 없습니다.")
            sys.exit(1)
            
        print(f"처리할 정규화 데이터 파일 목록: {normalized_data_files}")
    
    # 각 정규화된 데이터 파일에 대해 시각화 수행
    for normalized_file in normalized_data_files:
        print(f"\n===== 파일 '{normalized_file}' 시각화 시작 =====")
        
        # 파일 이름에서 접미사 추출 (예: normalized_data_A.csv -> _A)
        file_name = os.path.basename(normalized_file)
        file_name_without_ext = os.path.splitext(file_name)[0]  # 확장자 제거
        suffix = file_name_without_ext.replace("normalized_data", "")  # "normalized_data" 제거
        if not suffix:  # 접미사가 없는 경우 (기본 파일)
            suffix = "_base"
            
        # 시각화 저장 디렉토리 동적 생성
        VISUALIZATION_DIR = args.output_dir or f"visualization{suffix}"
        os.makedirs(VISUALIZATION_DIR, exist_ok=True)
        
        print(f"시각화 저장 디렉토리: {VISUALIZATION_DIR}")
        
        # 정규화된 데이터 로드
        df_normalized = load_data(normalized_file)
        
        # 데이터 칼럼 분류
        column_info = categorize_columns(df_normalized)
        
        # 칼럼 정보 출력
        print("\n데이터 분석 정보:")
        print(f"타겟 변수: {column_info['target_col']}")
        print(f"ID 칼럼: {column_info['id_col']}")
        print("특성 타입별 칼럼 수:")
        for feature_type, cols in column_info['feature_types'].items():
            print(f"  - {feature_type}: {len(cols)} 칼럼")
        print(f"총 특성 수: {len(column_info['all_feature_cols'])}")
        
        # 시각화 함수 호출
        visualize_correlation_matrix(df_normalized, column_info, VISUALIZATION_DIR)
        top_features = visualize_feature_target_correlation(df_normalized, column_info, VISUALIZATION_DIR)
        visualize_parallel_coordinates(df_normalized, top_features, column_info, VISUALIZATION_DIR)
        visualize_scatter_matrix(df_normalized, top_features, column_info, VISUALIZATION_DIR)
        visualize_target_distribution(df_normalized, column_info, VISUALIZATION_DIR)
        visualize_pca(df_normalized, column_info, VISUALIZATION_DIR)
    
        print(f"\n파일 '{normalized_file}'의 시각화 파일이 {VISUALIZATION_DIR} 디렉토리에 저장되었습니다.")
        
        # 학습 스크립트 실행 방법 안내
        print("\n--- 모델 학습 방법 ---")
        print("다음 명령을 실행하여 이 데이터에 대한 CatBoost 모델을 학습할 수 있습니다:")
        print(f"python 2_training_catboost.py --data_file {normalized_file}")
        print("\n다음 명령을 실행하여 이 데이터에 대한 XGBoost 모델을 학습할 수 있습니다:")
        print(f"python 3_training_xgboost.py --data_file {normalized_file}")
        print("----------------------------")
        
        print(f"===== 파일 '{normalized_file}' 시각화 완료 =====\n")
    
    print("\n모든 파일 시각화 작업 완료!") 