import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
import os

# 데이터 로드 함수
def load_icp_data():
    """
    ICP 데이터 로드 및 전처리
    
    Returns:
        DataFrame: 전처리된 ICP 데이터
    """
    # 파일 경로
    file_path = 'icp_normalized_data_1.csv'
    
    # 데이터 로드
    try:
        df = pd.read_csv(file_path)
        print(f"데이터 로드 완료: {file_path}")
        print(f"데이터 형태: {df.shape}")
        #print(f"타겟 분포: 1={df['target'].sum()}, 0={len(df)-df['target'].sum()}, 2={len(df)-df['target'].sum()}")
        print(f"타겟 분포: 0={df[df['target']==0].count()}, 1={df[df['target']==1].count()}, 2={df[df['target']==2].count()}")
        return df
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
        return None

# 1. 상관관계 분석
def analyze_correlations(df):
    """
    각 특성과 타겟 간의 상관관계 분석 (Plotly 사용)
    
    Args:
        df (DataFrame): ICP 데이터
    """
    # 분석 결과 저장 디렉토리
    analysis_dir = "icp_analysis"
    viz_dir = "icp_visualization" 
    os.makedirs(analysis_dir, exist_ok=True)
    os.makedirs(viz_dir, exist_ok=True)
    
    # 모든 특성 컬럼 추출
    feature_cols = [col for col in df.columns if col != 'target']
    
    # 각 특성과 타겟 간의 상관계수 계산
    correlations = []
    for col in feature_cols:
        corr = df[col].corr(df['target'])
        correlations.append((col, corr))
    
    # 상관계수 기준 정렬
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    print(correlations[:50])  # 상위 20개 특성 출력
    
    # 상관관계 분석 결과 저장
    corr_df = pd.DataFrame(correlations, columns=['feature', 'correlation'])
    corr_df.to_csv(os.path.join(analysis_dir, 'target_correlations.csv'), index=False)
    print(f"상관관계 분석 결과 CSV 저장 완료: {os.path.join(analysis_dir, 'target_correlations.csv')}")
    
    # 상위 20개 특성만 선택 (시각화를 위해)
    top_features = correlations[:20]
    top_feature_names = [item[0] for item in top_features]
    top_correlations = [item[1] for item in top_features]
    
    # --- 상관관계 바 차트 (Plotly) ---
    colors = ['indianred' if c > 0 else 'steelblue' for c in top_correlations]
    
    fig_bar = go.Figure(data=[go.Bar(
        #x=[f.replace('qcp_', 'QCP ') for f in top_feature_names],
        x=top_feature_names,
        y=top_correlations,
        marker_color=colors,
        text=[f'{v:.2f}' for v in top_correlations],
        textposition='outside'
    )])
    
    fig_bar.update_layout(
        title='상위 20개 특성과 타겟(불량 여부) 간의 상관관계',
        xaxis_title='특성',
        yaxis_title='상관 계수',
        plot_bgcolor='white',
        yaxis=dict(showgrid=True, gridcolor='lightgray', range=[-1, 1]),
        font=dict(family="Arial, Malgun Gothic, sans-serif"),
        height=700,
        width=800
    )
    fig_bar.add_hline(y=0, line_width=1, line_dash="dash", line_color="black")
    
    # 저장 (HTML)
    bar_path = os.path.join(viz_dir, 'top_correlations_bar.html')
    fig_bar.write_html(bar_path)
    print(f"상관관계 바 차트 저장 완료: {bar_path}")
    
    # 상관계수가 높은 상위 5개 특성 사이의 상관관계 히트맵
    top5_features = [item[0] for item in correlations[:5]] + ['target']
    top5_corr = df[top5_features].corr()
    
    # 상위 5개 특성 간 상관관계 저장
    top5_corr.to_csv(os.path.join(analysis_dir, 'top5_feature_correlations.csv'))
    print(f"상위 5개 특성 상관관계 CSV 저장 완료: {os.path.join(analysis_dir, 'top5_feature_correlations.csv')}")
    
    fig_heatmap = go.Figure(data=go.Heatmap(
                   z=top5_corr.values,
                   x=top5_corr.columns,
                   y=top5_corr.columns,
                   colorscale='RdBu',
                   zmin=-1, zmax=1,
                   colorbar=dict(title='Correlation'),
                   text=top5_corr.round(2).astype(str).values, 
                   texttemplate="%{text}",
                   textfont={"size":10}
                   ))
    
    fig_heatmap.update_layout(
        title='상위 5개 특성 간의 상관관계 히트맵',
        height=700,
        width=800,
        font=dict(family="Arial, Malgun Gothic, sans-serif")
    )
    
    # 저장 (HTML)
    heatmap_path = os.path.join(viz_dir, 'top5_correlation_heatmap.html')
    fig_heatmap.write_html(heatmap_path)
    print(f"상관관계 히트맵 저장 완료: {heatmap_path}")

# 2. 이상치 분석
def analyze_outliers(df):
    """
    특성값의 이상치 분석 (Plotly 사용)
    
    Args:
        df (DataFrame): ICP 데이터
    """
    analysis_dir = "icp_analysis"
    viz_dir = "icp_visualization"
    os.makedirs(analysis_dir, exist_ok=True)
    os.makedirs(viz_dir, exist_ok=True)
    
    # 상관계수가 가장 높은 10개 특성 선택
    feature_cols = [col for col in df.columns if col != 'target']
    corr_values = [(col, abs(df[col].corr(df['target']))) for col in feature_cols]
    corr_values.sort(key=lambda x: x[1], reverse=True)
    top10_features = [item[0] for item in corr_values[:10]]
    
    # 이상치 분석 결과 저장
    outlier_results = []
    
    for feature in top10_features:
        # 정상 그룹 (타겟=0)의 특성값 통계
        normal_stats = df[df['target'] == 0][feature].describe()
        
        # 고위험 그룹 (타겟=1, 2)의 특성값 통계
        defect_stats = df[(df['target'] == 1)|(df['target'] == 2)][feature].describe()
        
        # IQR을 이용한 이상치 경계 계산 (정상 그룹 기준)
        q1 = normal_stats['25%']
        q3 = normal_stats['75%']
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # 각 그룹의 이상치 수 계산
        normal_outliers = ((df[df['target'] == 0][feature] < lower_bound) | 
                          (df[df['target'] == 0][feature] > upper_bound)).sum()
        
        defect_outliers = ((df[(df['target'] == 1)|(df['target'] == 2)][feature] < lower_bound) | 
                          (df[(df['target'] == 1)|(df['target'] == 2)][feature] > upper_bound)).sum()
        
        outlier_results.append({
            'feature': feature,
            'normal_min': normal_stats['min'],
            'normal_max': normal_stats['max'],
            'normal_mean': normal_stats['mean'],
            'normal_std': normal_stats['std'],
            'defect_min': defect_stats['min'],
            'defect_max': defect_stats['max'],
            'defect_mean': defect_stats['mean'],
            'defect_std': defect_stats['std'],
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'normal_outliers': normal_outliers,
            'defect_outliers': defect_outliers
        })
    
    # 이상치 분석 결과 저장
    outlier_df = pd.DataFrame(outlier_results)
    outlier_df.to_csv(os.path.join(analysis_dir, 'feature_outliers_analysis.csv'), index=False)
    print(f"이상치 분석 결과 CSV 저장 완료: {os.path.join(analysis_dir, 'feature_outliers_analysis.csv')}")
    
    # --- 타겟별 박스플롯 ---
    for i, feature in enumerate(top10_features):
        fig_box = go.Figure()
        
        # 타겟이 0인 데이터의 박스플롯
        fig_box.add_trace(go.Box(
            x=df[df['target'] == 0][feature],
            name='정상 (0)',
            boxpoints='outliers',
            marker_color='steelblue'
        ))
        
        # 타겟이 1인 데이터의 박스플롯
        fig_box.add_trace(go.Box(
            x=df[(df['target'] == 1)|(df['target'] == 2)][feature],
            name='불량 (1, 2)',
            boxpoints='outliers',
            marker_color='indianred'
        ))
        
        fig_box.update_layout(
            title=f'특성 {feature}의 타겟별 분포',
            xaxis_title='특성값',
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgray'),
            font=dict(family="Arial, Malgun Gothic, sans-serif"),
            showlegend=True
        )
        
        # 저장 (HTML)
        box_path = os.path.join(viz_dir, f'boxplot_{feature}.html')
        fig_box.write_html(box_path)
        
        # 상위 5개만 출력 메시지 표시
        if i < 5:
            print(f"박스 플롯 저장 완료: {box_path}")
        elif i == 5:
            print("추가 박스 플롯 저장 중...")
    
    print(f"총 {len(top10_features)}개 박스 플롯 저장 완료")

# # 3. PCA를 통한 차원 축소 및 분석
# def analyze_with_pca(df):
#     """
#     PCA를 이용한 특성 차원 축소 및 시각화 (Plotly 사용)
    
#     Args:
#         df (DataFrame): ICP 데이터
#     """
#     analysis_dir = "icp_analysis"
#     viz_dir = "icp_visualization"
#     os.makedirs(analysis_dir, exist_ok=True)
#     os.makedirs(viz_dir, exist_ok=True)
    
#     # 특성과 타겟 분리
#     X = df.drop('target', axis=1).values
#     y = df['target'].values
    
#     # 정규화
#     scaler = StandardScaler()
#     X_scaled = scaler.fit_transform(X)
    
#     # PCA 수행 (3차원으로 축소)
#     pca = PCA(n_components=3)
#     X_pca = pca.fit_transform(X_scaled)
    
#     # PCA 결과를 데이터프레임으로 변환
#     pca_df = pd.DataFrame(X_pca, columns=['PC1', 'PC2', 'PC3'])
#     pca_df['target'] = y
    
#     # PCA 결과 저장
#     pca_df.to_csv(os.path.join(analysis_dir, 'pca_results.csv'), index=False)
#     print(f"PCA 결과 CSV 저장 완료: {os.path.join(analysis_dir, 'pca_results.csv')}")
    
#     # 주성분 기여도 저장
#     feature_names = [col for col in df.columns if col != 'target']
#     components_df = pd.DataFrame(
#         pca.components_,
#         columns=feature_names,
#         index=['PC1', 'PC2', 'PC3']
#     )
#     components_df.to_csv(os.path.join(analysis_dir, 'pca_components.csv'))
#     print(f"PCA 주성분 기여도 CSV 저장 완료: {os.path.join(analysis_dir, 'pca_components.csv')}")
    
#     # --- 2D PCA 산점도 (Plotly) ---
#     fig_scatter2d = px.scatter(
#         pca_df, 
#         x='PC1', 
#         y='PC2', 
#         color='target',
#         color_discrete_map={0: 'steelblue', 1: 'indianred'},
#         labels={'PC1': f'주성분 1 ({pca.explained_variance_ratio_[0]:.1%})',
#                 'PC2': f'주성분 2 ({pca.explained_variance_ratio_[1]:.1%})'},
#         title='PCA 축소 결과 (2D)',
#         category_orders={'target': [0, 1]},
#         hover_data={'PC1': ':.2f', 'PC2': ':.2f'}
#     )
    
#     fig_scatter2d.update_layout(
#         plot_bgcolor='white',
#         xaxis=dict(showgrid=True, gridcolor='lightgray'),
#         yaxis=dict(showgrid=True, gridcolor='lightgray'),
#         font=dict(family="Arial, Malgun Gothic, sans-serif"),
#         legend_title='타겟(불량 여부)',
#         height=700,
#         width=800
#     )
    
#     # 저장 (HTML)
#     scatter2d_path = os.path.join(viz_dir, 'pca_scatter_2d.html')
#     fig_scatter2d.write_html(scatter2d_path)
#     print(f"PCA 2D 산점도 저장 완료: {scatter2d_path}")
    
#     # --- 3D PCA 산점도 (Plotly) ---
#     fig_scatter3d = px.scatter_3d(
#         pca_df, 
#         x='PC1', 
#         y='PC2', 
#         z='PC3',
#         color='target',
#         color_discrete_map={0: 'steelblue', 1: 'indianred'},
#         labels={'PC1': f'주성분 1 ({pca.explained_variance_ratio_[0]:.1%})',
#                 'PC2': f'주성분 2 ({pca.explained_variance_ratio_[1]:.1%})',
#                 'PC3': f'주성분 3 ({pca.explained_variance_ratio_[2]:.1%})'},
#         title='PCA 축소 결과 (3D)',
#         category_orders={'target': [0, 1]}
#     )
    
#     fig_scatter3d.update_layout(
#         scene=dict(
#             xaxis=dict(showgrid=True, gridcolor='lightgray'),
#             yaxis=dict(showgrid=True, gridcolor='lightgray'),
#             zaxis=dict(showgrid=True, gridcolor='lightgray')
#         ),
#         font=dict(family="Arial, Malgun Gothic, sans-serif"),
#         legend_title='타겟(불량 여부)',
#         height=800,
#         width=800
#     )
    
#     # 저장 (HTML)
#     scatter3d_path = os.path.join(viz_dir, 'pca_scatter_3d.html')
#     fig_scatter3d.write_html(scatter3d_path)
#     print(f"PCA 3D 산점도 저장 완료: {scatter3d_path}")
    
#     # --- PCA 설명된 분산 그래프 ---
#     # 모든 주성분에 대한 설명된 분산 계산
#     full_pca = PCA()
#     full_pca.fit(X_scaled)
    
#     explained_var = full_pca.explained_variance_ratio_
#     cumulative_var = np.cumsum(explained_var)
    
#     # 설명된 분산 결과 저장
#     var_df = pd.DataFrame({
#         'component': range(1, len(explained_var) + 1),
#         'explained_variance': explained_var,
#         'cumulative_variance': cumulative_var
#     })
#     var_df.to_csv(os.path.join(analysis_dir, 'pca_explained_variance.csv'), index=False)
#     print(f"PCA 설명된 분산 CSV 저장 완료: {os.path.join(analysis_dir, 'pca_explained_variance.csv')}")
    
#     # 처음 20개의 주성분만 표시
#     n_components = min(20, len(explained_var))
    
#     fig_var = go.Figure()
    
#     # 개별 설명 분산
#     fig_var.add_trace(go.Bar(
#         x=list(range(1, n_components+1)),
#         y=explained_var[:n_components],
#         name='개별 설명 분산',
#         marker_color='steelblue'
#     ))
    
#     # 누적 설명 분산
#     fig_var.add_trace(go.Scatter(
#         x=list(range(1, n_components+1)),
#         y=cumulative_var[:n_components],
#         name='누적 설명 분산',
#         mode='lines+markers',
#         marker_color='indianred',
#         yaxis='y2'
#     ))
    
#     fig_var.update_layout(
#         title='주성분별 설명된 분산',
#         xaxis_title='주성분 번호',
#         yaxis_title='설명된 분산 비율',
#         yaxis2=dict(
#             title='누적 설명 분산',
#             overlaying='y',
#             side='right',
#             range=[0, 1]
#         ),
#         plot_bgcolor='white',
#         yaxis=dict(showgrid=True, gridcolor='lightgray', range=[0, max(explained_var[:n_components])*1.1]),
#         font=dict(family="Arial, Malgun Gothic, sans-serif"),
#         legend=dict(x=0.01, y=0.99),
#         height=700,
#         width=800
#     )
    
#     # 저장 (HTML)
#     var_path = os.path.join(viz_dir, 'pca_explained_variance.html')
#     fig_var.write_html(var_path)
#     print(f"PCA 설명된 분산 그래프 저장 완료: {var_path}")

# 4. 통계적 검정
def statistical_tests(df):
    """
    특성별 정상/불량 그룹 간 차이 통계적 검정 (Plotly 사용)
    
    Args:
        df (DataFrame): ICP 데이터
    """
    analysis_dir = "icp_analysis"
    viz_dir = "icp_visualization"
    os.makedirs(analysis_dir, exist_ok=True)
    os.makedirs(viz_dir, exist_ok=True)
    
    # 모든 특성 컬럼
    feature_cols = [col for col in df.columns if col != 'target']
    
    # 타겟 그룹 분리
    normal_group = df[df['target'] == 0]
    defect_group = df[(df['target'] == 1)|(df['target'] == 2)]
    
    # 각 특성에 대한 t-test 수행
    results = []
    for col in feature_cols:
        t_stat, p_val = stats.ttest_ind(
            normal_group[col].fillna(normal_group[col].median()), 
            defect_group[col].fillna(defect_group[col].median()),
            equal_var=False  # Welch's t-test 사용
        )
        normal_mean = normal_group[col].mean()
        defect_mean = defect_group[col].mean()
        results.append({
            'feature': col,
            'normal_mean': normal_mean,
            'defect_mean': defect_mean,
            'difference': defect_mean - normal_mean,
            'p_value': p_val,
            'significant': p_val < 0.05
        })
    
    # 결과를 데이터프레임으로 변환하고 차이의 절대값을 기준으로 정렬
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('difference', key=abs, ascending=False)
    
    # 결과 CSV 저장
    results_df.to_csv(os.path.join(analysis_dir, 'ttest_results.csv'), index=False)
    print(f"T-test 결과 CSV 저장 완료: {os.path.join(analysis_dir, 'ttest_results.csv')}")
    
    # 상위 20개 특성에 대한 그룹 비교 시각화
    top20_results = results_df.head(20)
    
    # --- 그룹 비교 바 차트 (Plotly) ---
    fig_comp_bar = go.Figure()
    
    # 특성 이름 가독성을 위해 수정
    display_features = [f.replace('qcp_', 'QCP ') for f in top20_results['feature']]
    
    fig_comp_bar.add_trace(go.Bar(
        x=display_features, 
        y=top20_results['normal_mean'], 
        name=f'정상 그룹 (0)',
        marker_color='steelblue'
    ))
    fig_comp_bar.add_trace(go.Bar(
        x=display_features, 
        y=top20_results['defect_mean'], 
        name=f'불량 그룹 (1)',
        marker_color='indianred'
    ))
    
    # 유의미한 차이에 별표 추가
    annotations = []
    for i, row in top20_results.iterrows():
        if row['significant']:
            feature_name = row['feature'].replace('qcp_', 'QCP ')
            idx = display_features.index(feature_name)
            annotations.append(dict(
                x=idx / len(display_features),
                y=max(row['normal_mean'], row['defect_mean']) * 1.05,
                text="*", 
                showarrow=False,
                font=dict(size=20),
                xref="x domain"
            ))
            
    fig_comp_bar.update_layout(
        title='상위 20개 특성의 정상/불량 그룹 간 평균값 비교 (T-test)',
        xaxis_title='특성',
        yaxis_title='평균값',
        barmode='group',
        plot_bgcolor='white',
        yaxis=dict(showgrid=True, gridcolor='lightgray'),
        font=dict(family="Arial, Malgun Gothic, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        annotations=annotations,
        height=600  # 높이 조정
    )
    
    # x축 레이블 회전
    fig_comp_bar.update_xaxes(tickangle=-45)
    
    # 저장 (HTML)
    comp_bar_path = os.path.join(viz_dir, 'group_comparison_bar.html')
    fig_comp_bar.write_html(comp_bar_path)
    print(f"그룹 비교 바 차트 저장 완료: {comp_bar_path}")

# 메인 함수
def main():
    print("\n--- ICP 데이터 분석 시작 ---")
    try:
        # 데이터 로드
        df = load_icp_data()
        if df is None:
            return
        
        # 각종 분석 수행
        analyze_correlations(df)
        analyze_outliers(df)
        #analyze_with_pca(df)
        statistical_tests(df)
        print("--- ICP 데이터 분석 완료 ---")
    except Exception as e:
        print(f"오류: ICP 데이터 분석 중 예외 발생 - {str(e)}")

if __name__ == "__main__":
    main() 