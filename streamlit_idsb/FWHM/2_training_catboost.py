import pandas as pd
import numpy as np
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pickle
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.preprocessing import StandardScaler
import json
import sys
from scipy import stats # Added for normality test
import shap # Add SHAP import
import glob # 추가: 파일 패턴 검색용
import argparse # 추가: 커맨드 라인 인자 처리용

# 프로젝트 루트 디렉토리 경로 계산 (FWHM 폴더의 부모 폴더)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path에 프로젝트 루트 추가
sys.path.append(project_root)

# 이제 utils 패키지 임포트 가능
try:
    from utils.style import ECOPRO_COLORS, ECOPRO_SEQUENTIAL
except ImportError:
    print("스타일 유틸을 찾을 수 없습니다. 기본 색상 사용.")
    ECOPRO_COLORS = {
        'dark_blue': '#164193',
        'light_blue': '#26A9E0',
        'blue_dark_light': '#1d75b7',
        'orange': '#FF7A00',
        'green': '#2dcccd',
        'text': '#333333',
    }
    ECOPRO_SEQUENTIAL = ['#164193', '#1d75b7', '#26A9E0', '#2dcccd', '#FF7A00']

# Add RANDOM_SEED definition here if not already present globally
RANDOM_SEED = 42 # Or use the same seed as in train_model if defined globally

# 시각화 설정
VISUALIZATION = True

def parse_arguments():
    """
    커맨드 라인 인자를 파싱합니다.
    """
    parser = argparse.ArgumentParser(description='CatBoost 모델 학습 스크립트')
    parser.add_argument('--data_file', type=str, 
                        help='학습에 사용할 특정 데이터 파일 (CSV). 지정하지 않으면 모든 normalized_data*.csv 파일 처리')
    parser.add_argument('--model_dir', type=str, 
                        help='모델 저장 디렉토리 (기본값: "models_cbm")')
    parser.add_argument('--plot_dir', type=str, 
                        help='시각화 저장 디렉토리 (기본값: "plots_cbm")')
    return parser.parse_args()

def load_data(file_path="normalized_data.csv"):
    """
    데이터 파일을 로드합니다.
    """
    print(f"로드 중: {file_path}")
    
    # lot_id를 명시적으로 string 타입으로 로드
    df = pd.read_csv(file_path, dtype={'lot_id': str})
    
    # lot_id 열이 있는지 확인하고 string 타입으로 변환
    if 'lot_id' in df.columns and not pd.api.types.is_string_dtype(df['lot_id']):
        print("lot_id를 문자열 타입으로 변환 중...")
        df['lot_id'] = df['lot_id'].astype(str)
    
    print(f"로드된 데이터 크기: {df.shape}")
    return df

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

def prepare_data(df, test_size=0.2, random_state=42):
    """
    데이터를 학습용과 테스트용으로 분리합니다.
    """
    column_info = categorize_columns(df)
    target_col = column_info['target_col']
    id_col = column_info['id_col']
    
    if not target_col:
        raise ValueError("Target column 'Target_F' not found in dataset")
    
    # ID 칼럼을 포함한 제외할 칼럼 확인
    drop_cols = [target_col]
    if id_col:
        drop_cols.append(id_col)
    
    # 존재하는 칼럼만 제외
    drop_cols = [col for col in drop_cols if col in df.columns]
    
    X = df.drop(drop_cols, axis=1)
    y = df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    print(f"학습 데이터 크기: {X_train.shape}")
    print(f"테스트 데이터 크기: {X_test.shape}")
    
    # CatBoost의 Pool 객체 생성
    train_pool = Pool(X_train, y_train)
    test_pool = Pool(X_test, y_test)
    
    return X_train, X_test, y_train, y_test, train_pool, test_pool, column_info

def train_model(train_pool, test_pool, plot_dir="plots_cbm", model_dir="models_cbm", iterations=1000, learning_rate=0.01, depth=8, random_state=44):
    """
    CatBoost 모델을 학습시킵니다.
    """
    print("모델 학습 시작...")
    
    # 모델 정의
    model = CatBoostRegressor(
        iterations=iterations,
        learning_rate=learning_rate,
        depth=depth,
        loss_function='MAE',
        random_state=random_state,
        verbose=100,  # 학습 진행 상황을 100번째 반복마다 출력
        task_type='CPU'
    )
    
    # 모델 학습 (학습 이력 저장)
    model.fit(
        train_pool,
        eval_set=test_pool,
        use_best_model=True
    )
    
    # 학습 이력 가져오기
    train_losses = model.get_evals_result()['learn']['MAE']
    test_losses = model.get_evals_result()['validation']['MAE']
    iterations_list = list(range(len(train_losses)))
    
    print(f"학습 손실 (처음/마지막): {train_losses[0]:.6f}/{train_losses[-1]:.6f}")
    print(f"검증 손실 (처음/마지막): {test_losses[0]:.6f}/{test_losses[-1]:.6f}")
    
    # 학습 과정 시각화 - plotly 사용
    fig = go.Figure()
    
    # 학습 손실 곡선 추가
    fig.add_trace(
        go.Scatter(
            x=iterations_list, 
            y=train_losses, 
            mode='lines', 
            name='Train Loss',
            line=dict(color=ECOPRO_COLORS['dark_blue'], width=2)
        )
    )
    
    # 검증 손실 곡선 추가
    fig.add_trace(
        go.Scatter(
            x=iterations_list, 
            y=test_losses, 
            mode='lines', 
            name='Validation Loss',
            line=dict(color=ECOPRO_COLORS['orange'], width=2)
        )
    )
    
    # 차트 레이아웃 설정
    fig.update_layout(
        title=dict(
            text='CatBoost 학습 & 검증 손실',
            font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
        ),
        xaxis_title='반복 횟수',
        yaxis_title='MAE 손실',
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.5)',
            bordercolor='rgba(0, 0, 0, 0.1)',
            borderwidth=1
        ),
        template='plotly_white',
        height=600,
        width=1000,
        font=dict(color=ECOPRO_COLORS['text'])
    )
    
    # y축 범위 설정 (0부터 시작하여 최대값의 1.1배로 설정)
    max_loss = max(max(train_losses), max(test_losses))
    fig.update_yaxes(range=[0, max_loss * 1.1])
    
    # 차트 저장 (동적 경로 사용)
    fig.write_html(f"{plot_dir}/training_history.html")
    
    # 모델 저장 코드 추가 (이 부분이 누락되었음)
    # Pickle 형식으로 저장
    model_path = f"{model_dir}/catboost_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # CatBoost 내장 형식으로 저장
    cbm_path = f"{model_dir}/catboost_model.cbm"
    model.save_model(cbm_path)
    
    print(f"모델 학습 완료. 최적 반복 횟수: {model.get_best_iteration()}")
    print(f"모델이 저장되었습니다:")
    print(f"  - Pickle 형식: {model_path}")
    print(f"  - CatBoost 형식: {cbm_path}")
    
    return model, train_losses, test_losses

def evaluate_model(model, X_test, y_test, plot_dir="plots_cbm"):
    """
    학습된 모델을 평가합니다.
    """
    print("모델 평가 중...")
    y_pred = model.predict(X_test)
    
    # 메트릭 계산
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # MAPE 계산 추가 (0으로 나누기 오류 방지)
    mape = np.mean(np.abs((y_test - y_pred) / np.maximum(np.abs(y_test), 1e-10))) * 100
    
    print(f"RMSE: {rmse:.6f}")
    print(f"MAE: {mae:.6f}")
    print(f"MAPE: {mape:.6f}%")
    print(f"R^2: {r2:.6f}")
    
    # 예측 대 실제 값 비교 시각화 - plotly 사용
    fig = go.Figure()
    
    # 완벽한 예측을 나타내는 대각선
    max_val = max(max(y_test), max(y_pred))
    min_val = min(min(y_test), min(y_pred))
    fig.add_trace(
        go.Scatter(
            x=[min_val, max_val], 
            y=[min_val, max_val],
            mode='lines',
            name='Perfect Prediction',
            line=dict(color=ECOPRO_COLORS['orange'], dash='dash', width=1)
        )
    )
    
    # 실제 예측값
    fig.add_trace(
        go.Scatter(
            x=y_test, 
            y=y_pred,
            mode='markers',
            name='Predictions',
            marker=dict(
                color=ECOPRO_COLORS['light_blue'],
                size=8,
                opacity=0.7
            )
        )
    )
    
    # 차트 레이아웃 설정
    fig.update_layout(
        title=dict(
            text=f'CatBoost 예측값 vs 실제값 (RMSE: {rmse:.4f}, MAE: {mae:.4f}, MAPE: {mape:.2f}%, R²: {r2:.4f})',
            font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
        ),
        xaxis_title='실제값',
        yaxis_title='예측값',
        template='plotly_white',
        height=600,
        width=1000,
        font=dict(color=ECOPRO_COLORS['text'])
    )
    
    # 예측 대 실제 값 플롯 저장 (동적 경로 사용)
    fig.write_html(f"{plot_dir}/prediction_vs_actual.html")
    
    # 예측 잔차(residuals) 시각화
    residuals = y_test - y_pred
    
    # 잔차 플롯
    fig_res = make_subplots(rows=2, cols=1, 
                            subplot_titles=('Residuals vs Predicted', 'Residuals Distribution'))
    
    # 잔차 대 예측값 산점도
    fig_res.add_trace(
        go.Scatter(
            x=y_pred, 
            y=residuals,
            mode='markers',
            name='Residuals',
            marker=dict(
                color=ECOPRO_COLORS['dark_blue'],
                size=8,
                opacity=0.7
            )
        ),
        row=1, col=1
    )
    
    # 잔차 히스토그램
    fig_res.add_trace(
        go.Histogram(
            x=residuals,
            nbinsx=30,
            opacity=0.7,
            marker_color=ECOPRO_COLORS['light_blue']
        ),
        row=2, col=1
    )
    
    # 0선 추가 (잔차 대 예측값 플롯)
    fig_res.add_trace(
        go.Scatter(
            x=[min(y_pred), max(y_pred)], 
            y=[0, 0],
            mode='lines',
            name='Zero Line',
            line=dict(color=ECOPRO_COLORS['orange'], dash='dash', width=1)
        ),
        row=1, col=1
    )
    
    # 차트 레이아웃 설정
    fig_res.update_layout(
        title=dict(
            text='잔차 분석',
            font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
        ),
        xaxis_title='예측값',
        yaxis_title='잔차',
        xaxis2_title='잔차 값',
        yaxis2_title='빈도',
        template='plotly_white',
        height=600,
        width=1000,
        showlegend=False,
        font=dict(color=ECOPRO_COLORS['text'])
    )
    
    # 차트 저장 (동적 경로 사용)
    fig_res.write_html(f"{plot_dir}/residual_analysis.html")
    
    return rmse, mae, r2, y_pred

def analyze_feature_importance(model, X_train, column_info, plot_dir="plots_cbm"):
    """
    모델의 특성 중요도를 분석합니다.
    """
    print("특성 중요도 분석 중...")
    
    # 특성 중요도 계산
    feature_importance = model.get_feature_importance()
    feature_names = X_train.columns
    
    # 특성 중요도 데이터프레임 생성
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': feature_importance
    })
    
    # 중요도 기준으로 정렬
    importance_df = importance_df.sort_values('Importance', ascending=False)
    
    # 상위 20개 특성 출력
    print("상위 20개 중요 특성:")
    print(importance_df.head(20))
    
    # 상위 20개 특성 시각화 - plotly 사용 (XGBoost 방식과 동일)
    top_n = 20
    top_features = importance_df.head(top_n)
    
    # XGBoost 스타일로 변경: 단일 add_trace 호출로 변경하고 전체 레이아웃 설정을 간결하게 통합
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_features['Importance'], 
        y=top_features['Feature'], 
        orientation='h', 
        marker=dict(
            color=top_features['Importance'], 
            colorscale=[[0, ECOPRO_COLORS['light_blue']], [0.5, ECOPRO_COLORS['blue_dark_light']], [1, ECOPRO_COLORS['dark_blue']]], 
            colorbar=dict(title='중요도')
        )
    ))
    
    # XGBoost 스타일의 통합된 레이아웃 설정
    fig.update_layout(
        title=dict(text=f'CatBoost 상위 {top_n}개 특성 중요도', font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)), 
        xaxis_title='중요도 점수', 
        yaxis_title='특성', 
        template='plotly_white', 
        height=600, 
        width=1000, 
        font=dict(color=ECOPRO_COLORS['text']), 
        yaxis={'categoryorder':'total ascending'}
    )
    
    # 차트 저장 (동적 경로 사용)
    fig.write_html(f"{plot_dir}/feature_importance.html")
    
    # 특성 유형 별로 분석
    feature_types = column_info['feature_types']
    
    # 특성 유형별 중요도 합계
    type_importance = {}
    for ftype, features in feature_types.items():
        filtered_features = [feat for feat in features if feat in importance_df['Feature'].values]
        if filtered_features:
            type_importance[ftype] = importance_df[importance_df['Feature'].isin(filtered_features)]['Importance'].sum()
    
    type_importance_df = pd.DataFrame({
        'Feature Type': list(type_importance.keys()),
        'Total Importance': list(type_importance.values())
    })
    
    # 색상 매핑 (XGBoost와 동일)
    color_map = {
        'Li': ECOPRO_COLORS.get('dark_blue', '#1f77b4'),
        'Pre_L': ECOPRO_COLORS.get('light_blue', '#aec7e8'),
        'Pre_S': ECOPRO_COLORS.get('orange', '#ff7f0e'),
        'Qcp': ECOPRO_COLORS.get('green', '#2ca02c'),
    }
    
    # 활성화된 유형의 색상 목록 생성
    colors = [color_map.get(ftype, '#808080') for ftype in type_importance.keys()]
    
    # 특성 유형별 중요도 시각화 - plotly 사용
    fig_types = go.Figure()
    fig_types.add_trace(
        go.Bar(
            x=type_importance_df['Feature Type'],
            y=type_importance_df['Total Importance'],
            marker=dict(color=colors)
        )
    )
    
    # 차트 레이아웃 설정 (XGBoost와 동일)
    fig_types.update_layout(
        title=dict(
            text='CatBoost 특성 유형별 중요도',
            font=dict(color=ECOPRO_COLORS['dark_blue'], size=20)
        ),
        xaxis_title='특성 유형',
        yaxis_title='총 중요도',
        font=dict(color=ECOPRO_COLORS['text']),
        template='plotly_white',
        height=600,
        width=1000
    )
    
    # 차트 저장 (동적 경로 사용)
    fig_types.write_html(f"{plot_dir}/feature_type_importance.html")
    
    return importance_df, type_importance

def generate_shap_analysis(model, X_test, plot_dir="plots_cbm"):
    """
    CatBoost 모델에 대한 SHAP 분석을 수행합니다.
    """
    print("\n--- SHAP 분석 시작 ---")

    # 샘플 제한 (계산량이 많을 경우)
    sample_size = min(100, X_test.shape[0])
    X_sample = X_test.iloc[:sample_size]
    feature_names = X_test.columns

    try:
        # SHAP 값 계산을 위한 explainer 생성
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        
        # CatBoost는 때로 차원이 다른 SHAP 값을 반환할 수 있으므로 확인
        if isinstance(shap_values, list):
            # 단일 출력 회귀 문제에서는 첫 번째 요소만 사용
            shap_values = shap_values[0]
        
        # SHAP 값 저장
        shap_df = pd.DataFrame(shap_values, columns=feature_names)
        shap_df['prediction'] = model.predict(X_sample)
        
        shap_csv_path = os.path.join(plot_dir, "catboost_shap_values.csv")
        shap_df.to_csv(shap_csv_path, index=False)
        
        # 1. SHAP 요약 플롯 (특성 중요도)
        # SHAP 값 평균 계산하여 특성 중요도 시각화
        shap_importance = pd.DataFrame({
            'Feature': feature_names,
            'Importance': np.abs(shap_values).mean(0)
        }).sort_values('Importance', ascending=False)
        
        # 상위 20개 특성 선택
        top_shap_features = shap_importance.head(20)
        
        # SHAP 특성 중요도 시각화
        fig_shap_importance = px.bar(
            top_shap_features, 
            x='Importance', 
            y='Feature',
            orientation='h',
            color='Importance',
            color_continuous_scale='RdBu_r'
        )
        
        fig_shap_importance.update_layout(
            title='SHAP 기반 CatBoost 특성 중요도',
            xaxis=dict(title='평균 SHAP 절대값'),
            yaxis=dict(title='특성', categoryorder='total ascending'),
            template='plotly_white',
            height=600,
            width=1000,
            font=dict(color=ECOPRO_COLORS['text'])
        )
        
        # HTML 저장 (동적 경로 사용)
        shap_importance_html_path = os.path.join(plot_dir, "catboost_shap_feature_importance.html")
        fig_shap_importance.write_html(shap_importance_html_path)
        
        # 2. SHAP 요약 플롯 (개선된 버전) - 추가
        # 상위 10개 특성에 대한 요약 시각화
        top10_features = shap_importance['Feature'].head(10).tolist()
        
        # SHAP 요약 플롯 (개선된 버전) - 모든 특성에 대한 분포와 영향
        fig_summary = go.Figure()
        
        # 각 특성별로 처리 (scatter plot 방식으로 변경)
        for i, feature in enumerate(top10_features[::-1]):  # 역순으로 처리하여 중요도 순으로 표시
            feature_idx = list(feature_names).index(feature)
            feature_vals = X_sample[feature].values
            feature_shap_vals = shap_values[:, feature_idx]
            
            # 특성 값 기준으로 정규화 (0-1 사이 값으로)
            min_val = np.min(feature_vals)
            max_val = np.max(feature_vals)
            norm_range = max_val - min_val
            if norm_range == 0:  # 모든 값이 같은 경우
                norm_vals = np.ones_like(feature_vals) * 0.5
            else:
                norm_vals = (feature_vals - min_val) / norm_range
                
            # 색상 매핑 (0: 파란색, 1: 빨간색)
            colors = ['rgba(0,0,255,0.7)' if v < 0.5 else 'rgba(255,0,0,0.7)' for v in norm_vals]
            
            # 작은 jitter 추가하여 y축 위치 조정
            y_jitter = np.random.normal(0, 0.1, size=len(feature_shap_vals))
            
            # 특성별 산점도 추가
            fig_summary.add_trace(
                go.Scatter(
                    x=feature_shap_vals,
                    y=[i] * len(feature_shap_vals) + y_jitter,  # 각 특성별 y 위치 + jitter
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=colors,
                        opacity=0.7
                    ),
                    name=feature,
                    hovertemplate=
                    f"{feature}<br>" +
                    "SHAP 값: %{x:.4f}<br>" +
                    "특성 값: %{text:.4f}" +
                    "<extra></extra>",
                    text=feature_vals
                )
            )
            
            # 각 특성별 SHAP 값의 분포를 보여주는 바이올린 플롯 추가
            violin_data = []
            for j, val in enumerate(feature_shap_vals):
                violin_data.append({
                    'x': val,
                    'y': i,
                    'feature': feature
                })
            
            df_violin = pd.DataFrame(violin_data)
            
            # SHAP 값의 음수/양수 분포를 표시하기 위한 KDE 계산
            pos_vals = feature_shap_vals[feature_shap_vals >= 0]
            neg_vals = feature_shap_vals[feature_shap_vals < 0]
            
            # 양수 영역 KDE (충분한 데이터가 있는 경우만)
            if len(pos_vals) > 5:
                try:
                    from scipy import stats
                    kde_pos = stats.gaussian_kde(pos_vals)
                    x_pos = np.linspace(0, np.max(pos_vals), 100)
                    y_pos = kde_pos(x_pos)
                    
                    # KDE 스케일 조정
                    y_pos = y_pos / np.max(y_pos) * 0.2
                    
                    # 양수 영역 KDE 추가
                    fig_summary.add_trace(
                        go.Scatter(
                            x=x_pos,
                            y=i + y_pos,
                            mode='lines',
                            line=dict(color='rgba(255,0,0,0.5)', width=1.5),
                            fill='toself',
                            fillcolor='rgba(255,0,0,0.2)',
                            showlegend=False,
                            hoverinfo='skip'
                        )
                    )
                    
                    fig_summary.add_trace(
                        go.Scatter(
                            x=x_pos,
                            y=i - y_pos,
                            mode='lines',
                            line=dict(color='rgba(255,0,0,0.5)', width=1.5),
                            fill='toself',
                            fillcolor='rgba(255,0,0,0.2)',
                            showlegend=False,
                            hoverinfo='skip'
                        )
                    )
                except Exception as e:
                    print(f"KDE 계산 중 오류 (양수 영역): {e}")
            
            # 음수 영역 KDE (충분한 데이터가 있는 경우만)
            if len(neg_vals) > 5:
                try:
                    from scipy import stats
                    kde_neg = stats.gaussian_kde(neg_vals)
                    x_neg = np.linspace(np.min(neg_vals), 0, 100)
                    y_neg = kde_neg(x_neg)
                    
                    # KDE 스케일 조정
                    y_neg = y_neg / np.max(y_neg) * 0.2
                    
                    # 음수 영역 KDE 추가
                    fig_summary.add_trace(
                        go.Scatter(
                            x=x_neg,
                            y=i + y_neg,
                            mode='lines',
                            line=dict(color='rgba(0,0,255,0.5)', width=1.5),
                            fill='toself',
                            fillcolor='rgba(0,0,255,0.2)',
                            showlegend=False,
                            hoverinfo='skip'
                        )
                    )
                    
                    fig_summary.add_trace(
                        go.Scatter(
                            x=x_neg,
                            y=i - y_neg,
                            mode='lines',
                            line=dict(color='rgba(0,0,255,0.5)', width=1.5),
                            fill='toself',
                            fillcolor='rgba(0,0,255,0.2)',
                            showlegend=False,
                            hoverinfo='skip'
                        )
                    )
                except Exception as e:
                    print(f"KDE 계산 중 오류 (음수 영역): {e}")
        
        # 범례 정보 추가
        fig_summary.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(size=10, color='rgba(255,0,0,0.7)'),
                name='높은 특성값',
                showlegend=True
            )
        )
        
        fig_summary.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(size=10, color='rgba(0,0,255,0.7)'),
                name='낮은 특성값',
                showlegend=True
            )
        )
        
        # 0 기준선 추가
        fig_summary.add_vline(x=0, line_width=1, line_dash="dash", line_color="gray")
        
        # SHAP 값 범위 계산
        max_abs_shap = np.max(np.abs(shap_values))
        shap_range = [-max_abs_shap * 1.05, max_abs_shap * 1.05]
        
        # 레이아웃 설정
        fig_summary.update_layout(
            title='SHAP 요약 플롯 (상위 10개 특성)',
            xaxis=dict(
                title='SHAP 값 (모델 출력에 대한 영향)',
                range=shap_range,
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='gray'
            ),
            yaxis=dict(
                title='특성',
                tickvals=list(range(len(top10_features))),
                ticktext=top10_features[::-1]  # 중요도 높은 순으로 표시
            ),
            template='plotly_white',
            height=700,
            width=1000,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            font=dict(color=ECOPRO_COLORS['text'])
        )
        
        # HTML 저장 (동적 경로 사용)
        summary_html_path = os.path.join(plot_dir, "catboost_shap_summary_enhanced.html")
        fig_summary.write_html(summary_html_path)
        
        # 3. 기존 SHAP 요약 시각화 (특성-값 관계) - 추가
        shap_summary_data = []
        
        for feature in top10_features:
            feature_idx = list(feature_names).index(feature)
            feature_vals = X_sample[feature].values
            feature_shap_vals = shap_values[:, feature_idx]
            
            for i in range(len(feature_vals)):
                shap_summary_data.append({
                    'Feature': feature,
                    'Feature Value': feature_vals[i],
                    'SHAP Value': feature_shap_vals[i]
                })
        
        shap_summary_df = pd.DataFrame(shap_summary_data)
        
        # SHAP 요약 시각화
        fig_shap_summary = px.scatter(
            shap_summary_df,
            x='Feature Value',
            y='SHAP Value',
            color='SHAP Value',
            facet_col='Feature',
            facet_col_wrap=2,
            color_continuous_scale='RdBu_r',
            height=1000
        )
        
        fig_shap_summary.update_layout(
            title='SHAP 값 vs 특성 값',
            template='plotly_white',
            height=700,
            width=1000,
            font=dict(color=ECOPRO_COLORS['text'])
        )
        
        # HTML 저장 (동적 경로 사용)
        shap_summary_html_path = os.path.join(plot_dir, "catboost_shap_summary.html")
        fig_shap_summary.write_html(shap_summary_html_path)
        
        # 4. SHAP 의존성 플롯 (상위 특성들에 대해)
        # 상위 10개 특성에 대한 의존성 플롯 생성
        top20_features = shap_importance['Feature'].head(20).tolist()
        
        for feature in top20_features:
            feature_idx = list(feature_names).index(feature)
            feature_vals = X_sample[feature].values
            feature_shap_vals = shap_values[:, feature_idx]
            
            fig_dep = go.Figure()
            
            # 기본 산점도 추가
            fig_dep.add_trace(
                go.Scatter(
                    x=feature_vals,
                    y=feature_shap_vals,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=feature_shap_vals,
                        colorscale='RdBu_r',
                        showscale=True,
                        colorbar=dict(title='SHAP 값')
                    ),
                    name=feature
                )
            )
            
            # 스무딩된 트렌드 라인 추가 (LOESS 대체)
            try:
                from scipy.stats import binned_statistic
                
                # 25개 빈으로 데이터 그룹화
                bins = 25
                bin_means, bin_edges, _ = binned_statistic(
                    feature_vals, feature_shap_vals, statistic='mean', bins=bins
                )
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                
                # 결측값 제거
                valid_mask = ~np.isnan(bin_means)
                bin_centers = bin_centers[valid_mask]
                bin_means = bin_means[valid_mask]
                
                if len(bin_centers) > 3:  # 최소 4개 포인트 필요
                    # 스무딩된 라인 추가
                    fig_dep.add_trace(
                        go.Scatter(
                            x=bin_centers,
                            y=bin_means,
                            mode='lines',
                            line=dict(color='black', width=2),
                            name='Trend'
                        )
                    )
            except Exception as e:
                print(f"트렌드 라인 생성 중 오류: {e}")
            
            # 0 기준선 추가
            fig_dep.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
            
            # 레이아웃 설정
            fig_dep.update_layout(
                title=f'SHAP 의존성 플롯: {feature}',
                xaxis=dict(title=feature),
                yaxis=dict(title='SHAP 값 (모델 예측에 대한 영향)'),
                template='plotly_white',
                height=700,
                width=1000,
                font=dict(color=ECOPRO_COLORS['text'])
            )
            
            # HTML 저장 (동적 경로 사용)
            dep_html_path = os.path.join(plot_dir, f"catboost_shap_dependence_{feature}.html")
            fig_dep.write_html(dep_html_path)
        
        # 5. SHAP Force 플롯 
        # 몇 개의 샘플에 대한 Force 플롯 생성 
        n_samples = min(5, sample_size)
        sample_indices = np.random.choice(sample_size, size=n_samples, replace=False)
        
        # 기대값 추출
        base_value = explainer.expected_value
        
        # 모든 force plot을 한 화면에 표시할 figure 생성
        fig_force = make_subplots(rows=n_samples, cols=1, 
                               subplot_titles=[f"샘플 #{i+1} (예측: {shap_df['prediction'].iloc[idx]:.3f})" 
                                              for i, idx in enumerate(sample_indices)])
        
        # 각 샘플에 대한 force plot 생성
        for i, idx in enumerate(sample_indices, 1):
            sample_shap = shap_values[idx]
            
            # 상위 영향력 있는 특성만 선택 (상위 10개)
            feature_indices = np.argsort(-np.abs(sample_shap))[:10]
            selected_features = [feature_names[j] for j in feature_indices]
            selected_shap = sample_shap[feature_indices]
            
            # 누적값 계산
            cumulative = np.zeros(len(selected_features) + 1)
            cumulative[0] = base_value
            cumulative[1:] = base_value + np.cumsum(selected_shap)
            
            # 각 특성 기여도 막대 추가
            for j in range(len(selected_features)):
                feature = selected_features[j]
                impact = selected_shap[j]
                
                # 양수/음수 기여도에 따라 색상 결정
                color = 'rgba(255,0,0,0.7)' if impact > 0 else 'rgba(0,0,255,0.7)'
                
                fig_force.add_trace(
                    go.Bar(
                        x=[impact],
                        y=[0],
                        orientation='h',
                        base=cumulative[j],
                        marker=dict(color=color),
                        text=feature,
                        hoverinfo='text',
                        name=feature,
                        showlegend=False,
                        width=0.7
                    ),
                    row=i, col=1
                )
            
            # 시작점(base value) 표시
            fig_force.add_trace(
                go.Scatter(
                    x=[base_value],
                    y=[0],
                    mode='markers',
                    marker=dict(size=12, color='black', symbol='circle'),
                    hoverinfo='text',
                    text=f'Base value: {base_value:.3f}',
                    name='Base value',
                    showlegend=(i == 1)  # 첫 번째 샘플에만 범례 표시
                ),
                row=i, col=1
            )
            
            # 최종 예측값 표시
            fig_force.add_trace(
                go.Scatter(
                    x=[cumulative[-1]],
                    y=[0],
                    mode='markers',
                    marker=dict(size=12, color='red', symbol='diamond'),
                    hoverinfo='text',
                    text=f'Prediction: {cumulative[-1]:.3f}',
                    name='Prediction',
                    showlegend=(i == 1)  # 첫 번째 샘플에만 범례 표시
                ),
                row=i, col=1
            )
        
        # 레이아웃 설정
        fig_force.update_layout(
            title='SHAP Force Plot - 예측에 대한 특성 기여도',
            height=250 * n_samples,
            width=1000,
            template='plotly_white',
            font=dict(color=ECOPRO_COLORS['text'])
        )
        
        # 모든 서브플롯에 동일한 X축 범위 적용
        for i in range(1, n_samples + 1):
            fig_force.update_xaxes(title='특성 기여도 (SHAP 값)', row=i, col=1)
            fig_force.update_yaxes(visible=False, row=i, col=1)
        
        # HTML 저장 (동적 경로 사용)
        force_html_path = os.path.join(plot_dir, "catboost_shap_force_plot.html")
        fig_force.write_html(force_html_path)
        
        # 6. SHAP 상호작용 분석 (선택적으로 수행)
        # 상위 2개 특성에 대해 상호작용 플롯 생성
        if len(top5_features) >= 2:
            feature1 = top5_features[0]
            feature2 = top5_features[1]
            
            idx1 = list(feature_names).index(feature1)
            idx2 = list(feature_names).index(feature2)
            
            feature1_vals = X_sample[feature1].values
            feature2_vals = X_sample[feature2].values
            shap1_vals = shap_values[:, idx1]
            shap2_vals = shap_values[:, idx2]
            
            # 상호작용 산점도
            fig_interaction = go.Figure()
            
            # 산점도 추가
            fig_interaction.add_trace(
                go.Scatter(
                    x=feature1_vals,
                    y=feature2_vals,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=shap1_vals + shap2_vals,
                        colorscale='RdBu_r',
                        showscale=True,
                        colorbar=dict(title='SHAP 합계')
                    ),
                    text=[f"{feature1}: {v1:.4f}<br>{feature2}: {v2:.4f}<br>SHAP 합계: {s1+s2:.4f}"
                          for v1, v2, s1, s2 in zip(feature1_vals, feature2_vals, shap1_vals, shap2_vals)],
                    hoverinfo='text'
                )
            )
            
            # 레이아웃 설정
            fig_interaction.update_layout(
                title=f'SHAP 상호작용 플롯: {feature1} vs {feature2}',
                xaxis=dict(title=feature1),
                yaxis=dict(title=feature2),
                template='plotly_white',
                height=700,
                width=1000,
                font=dict(color=ECOPRO_COLORS['text'])
            )
            
            # HTML 저장 (동적 경로 사용)
            interaction_html_path = os.path.join(plot_dir, f"catboost_shap_interaction_{feature1}_{feature2}.html")
            fig_interaction.write_html(interaction_html_path)
        
        print(f"SHAP 분석 결과 저장 완료: {plot_dir}")
        print(f"생성된 SHAP 시각화 파일:")
        print(f"  - 특성 중요도: catboost_shap_feature_importance.html")
        print(f"  - SHAP 요약 플롯 (향상된): catboost_shap_summary_enhanced.html")
        print(f"  - SHAP 요약 플롯 (기본): catboost_shap_summary.html")
        print(f"  - 의존성 플롯: catboost_shap_dependence_*.html")
        print(f"  - Force 플롯: catboost_shap_force_plot.html")
        if len(top5_features) >= 2:
            print(f"  - 상호작용 플롯: catboost_shap_interaction_{top5_features[0]}_{top5_features[1]}.html")
        
        return shap_importance
        
    except Exception as e:
        print(f"SHAP 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()  # 상세 오류 추적 정보 출력
        return None

def main():
    """
    메인 실행 함수 - 단일 CSV 파일 또는 모든 normalized_data로 시작하는 CSV 파일을 처리
    """
    # 커맨드 라인 인자 파싱
    args = parse_arguments()
    
    print("CatBoost 모델링 및 시각화 작업 시작")
    
    # 데이터 파일 결정 (단일 파일 또는 모든 파일)
    if args.data_file:
        data_files = [args.data_file]
        print(f"지정된 데이터 파일: {args.data_file}")
    else:
        # normalized_data로 시작하는 모든 CSV 파일 검색
        data_files = glob.glob("normalized_data*.csv")
        
        if not data_files:
            print("경고: 'normalized_data'로 시작하는 CSV 파일을 찾을 수 없습니다.")
            return
            
        print(f"처리할 데이터 파일 목록: {data_files}")
    
    # 각 데이터 파일에 대해 모델 학습 및 평가 수행
    for data_file in data_files:
        print(f"\n===== 파일 '{data_file}' 처리 시작 =====")
        
        # 파일 이름에서 접미사 추출 (예: normalized_data_A.csv -> _A)
        file_name = os.path.basename(data_file)
        file_name_without_ext = os.path.splitext(file_name)[0]  # 확장자 제거
        suffix = file_name_without_ext.replace("normalized_data", "")  # "normalized_data" 제거
        if not suffix:  # 접미사가 없는 경우 (기본 파일)
            suffix = "_base"
            
        # 모델 및 결과 저장 디렉토리 동적 생성
        PLOT_DIR = args.plot_dir if args.plot_dir else f"plots_cbm{suffix}"
        MODEL_DIR = args.model_dir if args.model_dir else f"models_cbm{suffix}"
        os.makedirs(PLOT_DIR, exist_ok=True)
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        print(f"모델 저장 디렉토리: {MODEL_DIR}")
        print(f"시각화 저장 디렉토리: {PLOT_DIR}")
        
        # 데이터 로드
        df = load_data(data_file)
        
        # 데이터 준비
        X_train, X_test, y_train, y_test, train_pool, test_pool, column_info = prepare_data(df)

        # X_test와 y_test를 합쳐서 FWHM 폴더에 저장
        os.makedirs("test_data", exist_ok=True)  # 폴더가 없으면 생성
        test_merged = X_test.copy()
        test_merged['Target_F'] = y_test.values  # 타겟 컬럼명에 맞게
        
        # lot_id를 첫 번째 컬럼으로 추가
        if 'lot_id' in df.columns:
            test_merged.insert(0, 'lot_id', df.loc[X_test.index, 'lot_id'])
        
        merged_filename = f"test_data{suffix}.csv"  # 파일명 형식 변경
        test_merged.to_csv(os.path.join("test_data", merged_filename), index=False)
        print(f"테스트 데이터(피처+타겟)가 test_data/{merged_filename}로 저장되었습니다.")
        
        # 칼럼 정보 출력
        print("\n데이터 칼럼 정보:")
        print(f"타겟 변수: {column_info['target_col']}")
        print(f"ID 칼럼: {column_info['id_col']}")
        print("특성 타입별 칼럼 수:")
        for feature_type, cols in column_info['feature_types'].items():
            print(f"  - {feature_type}: {len(cols)} 칼럼")
        print(f"총 특성 수: {len(column_info['all_feature_cols'])}")
        
        # 모델 학습 (수정: 경로 파라미터 추가)
        model, train_losses, test_losses = train_model(
            train_pool, 
            test_pool, 
            plot_dir=PLOT_DIR, 
            model_dir=MODEL_DIR
        )
        
        # 모델 평가 (동적 경로 전달)
        metrics = evaluate_model(model, X_test, y_test, plot_dir=PLOT_DIR)
        rmse, mae, r2, y_pred = metrics
        residuals = y_test - y_pred # Calculate residuals here
    
        # 특성 중요도 분석 (동적 경로 전달)
        importance_df, type_importance = analyze_feature_importance(model, X_train, column_info, plot_dir=PLOT_DIR)
    
        # SHAP 분석 수행 (동적 경로 전달)
        try:
            # SHAP 분석 수행
            shap_importance = generate_shap_analysis(model, X_test, plot_dir=PLOT_DIR)
        except Exception as e:
            print(f"SHAP 분석을 수행할 수 없습니다: {e}")
            shap_importance = None
    
        # ----- 결과 저장을 위한 데이터 수집 ----- 
        top_10_features = importance_df.head(10).set_index('Feature')['Importance'].to_dict()
        
        # Residual Statistics
        residual_mean = np.mean(residuals)
        residual_std = np.std(residuals)
        
        # MAPE 계산 추가 (main 함수에서도)
        mape = np.mean(np.abs((y_test - y_pred) / np.maximum(np.abs(y_test), 1e-10))) * 100
        
        try:
            # Use only a subset for normality test if data is large
            sample_size = min(len(residuals), 5000)
            # Ensure sample size is at least 3 for Shapiro-Wilk test
            if sample_size >= 3:
                 shapiro_test_sample = residuals.sample(sample_size, random_state=RANDOM_SEED) if len(residuals) > sample_size else residuals
                 shapiro_stat, shapiro_p = stats.shapiro(shapiro_test_sample)
            else:
                print("Warning: Not enough data points (less than 3) for Shapiro-Wilk test.")
                shapiro_p = None
        except Exception as e:
            print(f"Warning: Shapiro-Wilk test failed: {e}")
            shapiro_p = None # Indicate test failure
    
        # Final Losses from training history
        final_train_loss = train_losses[-1] if train_losses else None
        final_val_loss = test_losses[-1] if test_losses else None
    
        results_data = {
            "model_type": "CatBoost",
            "evaluation_metrics": {
                "RMSE": rmse,
                "MAE": mae,
                "MAPE": mape,
                "R-squared": r2
            },
            "learning_curve_summary": {
                 "final_training_loss (MAE)": final_train_loss,
                 "final_validation_loss (MAE)": final_val_loss,
                 "best_iteration": model.get_best_iteration() if hasattr(model, 'get_best_iteration') else None
            },
            "residual_analysis_summary": {
                "mean": residual_mean,
                "standard_deviation": residual_std,
                "shapiro_wilk_p_value": shapiro_p
            },
            "feature_importance": {
                "top_10_features": top_10_features,
                "type_importance": type_importance # Add the calculated type importance
            }
        }
        
        # SHAP 결과 추가
        if shap_importance is not None:
            top_10_shap_features = shap_importance.head(10).set_index('Feature')['Importance'].to_dict()
            results_data["shap_analysis"] = {
                "top_10_features": top_10_shap_features
            }
        
        # 결과를 JSON 파일로 저장
        results_file_path = os.path.join(MODEL_DIR, 'catboost_results.json')
        try:
            with open(results_file_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=4)
            print(f"모델 결과 요약 정보가 {results_file_path}에 저장되었습니다.")
        except Exception as e:
            print(f"Error saving results to JSON: {e}")
            
        print(f"\n===== 파일 '{data_file}' 처리 완료 =====\n")
    
    print("\n모든 파일 처리 완료!")
    
    # XGBoost 모델에 대한 안내 메시지 추가
    print("\n--- XGBoost 모델 학습 방법 ---")
    if args.data_file:
        print(f"다음 명령을 실행하여 '{args.data_file}' 파일에 대한 XGBoost 모델을 학습할 수 있습니다:")
        print(f"python 3_training_xgboost.py --data_file {args.data_file}")
    else:
        print("다음 명령을 실행하여 모든 normalized_data*.csv 파일에 대한 XGBoost 모델을 학습할 수 있습니다:")
        print("python 3_training_xgboost.py")
    print("특정 모델 및 시각화 저장 디렉토리 지정 예시:")
    print("python 3_training_xgboost.py --data_file data_file.csv --model_dir models_xgb_custom --plot_dir plots_xgb_custom")
    print("----------------------------")

if __name__ == "__main__":
    main() 