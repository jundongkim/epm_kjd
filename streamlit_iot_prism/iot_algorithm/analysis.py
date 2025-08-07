import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def calculate_statistics(df, numerical_cols):
    # 수치형 열만 필터링
    numeric_cols_only = [col for col in numerical_cols 
                        if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    stats = {}
    
    # 수치형 열이 없는 경우 처리
    if not numeric_cols_only:
        import streamlit as st
        st.warning("수치형 열이 없어 기본 통계를 계산할 수 없습니다.")
        stats['basic'] = pd.DataFrame()  # 빈 DataFrame 반환
        stats['missing'] = pd.DataFrame({
            'count': df[numerical_cols].isnull().sum(),
            'percentage': df[numerical_cols].isnull().sum() / len(df) * 100
        })
        stats['outliers'] = {}
        return stats
    
    # 수치형 열이 있는 경우 정상 처리
    stats['basic'] = df[numeric_cols_only].describe()
    stats['missing'] = pd.DataFrame({
        'count': df[numerical_cols].isnull().sum(),
        'percentage': df[numerical_cols].isnull().sum() / len(df) * 100
    })
    
    outliers = {}
    for col in numeric_cols_only:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers[col] = {
            'count': ((df[col] < lower_bound) | (df[col] > upper_bound)).sum(),
            'percentage': ((df[col] < lower_bound) | (df[col] > upper_bound)).sum() / len(df) * 100,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        }
    stats['outliers'] = outliers
    return stats

def plot_feature_distributions(df, numerical_cols):
    # 수치형 열만 필터링
    numeric_cols_only = [col for col in numerical_cols 
                        if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    fig = go.Figure()
    for col in numeric_cols_only:
        fig.add_trace(go.Histogram(x=df[col], name=col, opacity=0.7, histnorm='probability density'))
    fig.update_layout(title_text="Feature Distributions", showlegend=False)
    return fig

def plot_correlation_heatmap(df, numerical_cols):
    # datetime 타입의 열 제외
    import plotly.express as px
    
    numeric_cols_only = []
    excluded_cols = []
    
    for col in numerical_cols:
        if col in df.columns:
            # datetime 타입이거나 숫자로 변환할 수 없는 열은 제외
            if pd.api.types.is_datetime64_dtype(df[col]) or not pd.api.types.is_numeric_dtype(df[col]):
                excluded_cols.append(col)
            else:
                numeric_cols_only.append(col)
    
    # 제외된 열이 있으면 메시지 출력
    if excluded_cols and len(excluded_cols) < len(numerical_cols):
        import streamlit as st
        st.info(f"상관관계 계산에서 제외된 비수치형 열: {', '.join(excluded_cols)}")
    
    # 수치형 열이 없으면 빈 상관관계 행렬 반환
    if not numeric_cols_only:
        import numpy as np
        empty_corr = pd.DataFrame(np.array([[]]), columns=[])
        fig = px.imshow(empty_corr, color_continuous_scale='RdBu_r', aspect="auto", 
                       title="상관관계를 계산할 수치형 열이 없습니다")
        return fig
    
    # 수치형 열만 사용하여 상관관계 계산
    corr_matrix = df[numeric_cols_only].corr()
    fig = px.imshow(corr_matrix, x=numeric_cols_only, y=numeric_cols_only, 
                   color_continuous_scale='RdBu_r', aspect="auto", 
                   title="Feature Correlation Heatmap")
    return fig

def plot_boxplots(df, numerical_cols):
    # 수치형 열만 필터링
    numeric_cols_only = [col for col in numerical_cols 
                        if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    fig = go.Figure()
    for col in numeric_cols_only:
        fig.add_trace(go.Box(y=df[col], name=col))
    fig.update_layout(title="Boxplots for Outlier Detection", height=600, yaxis_title="Value")
    return fig

def plot_scatter_matrix(df, numerical_cols, limit=5):
    # 수치형 열만 필터링
    numeric_cols_only = [col for col in numerical_cols 
                        if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(numeric_cols_only) > limit:
        numeric_cols_only = numeric_cols_only[:limit]
    
    if not numeric_cols_only:
        import streamlit as st
        st.warning("산점도 행렬을 그릴 수치형 열이 없습니다.")
        fig = go.Figure()
        fig.update_layout(title="No numeric columns available for scatter matrix")
        return fig
    
    fig = px.scatter_matrix(df, dimensions=numeric_cols_only, title="Feature Scatter Matrix")
    fig.update_layout(height=800)
    return fig 