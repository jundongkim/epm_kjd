import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cdist
from tslearn.clustering import TimeSeriesKMeans
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
import matplotlib.pyplot as plt
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json
import warnings
warnings.filterwarnings('ignore')

def extract_daily_patterns(df, sensor_col, n_samples=24):
    """
    일별 패턴 추출 함수
    
    Args:
        df: 센서 데이터가 포함된 데이터프레임
        sensor_col: 센서 값이 저장된 열 이름
        n_samples: 하루당 샘플 수 (기본값: 시간별 24개)
        
    Returns:
        일별 패턴 데이터와 날짜 인덱스
    """
    # 날짜별로 그룹화
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    
    # 날짜별, 시간별 평균 계산
    daily_patterns = df.groupby(['date', 'hour'])[sensor_col].mean().unstack()
    
    # 결측치가 있는 날짜 제거 (완전한 일별 패턴만 사용)
    daily_patterns = daily_patterns.dropna()
    
    # 클러스터링을 위한 형태로 변환
    X = daily_patterns.values
    dates = daily_patterns.index
    
    return X, dates

def extract_weekly_patterns(df, sensor_col):
    """
    주간 패턴 추출 함수
    
    Args:
        df: 센서 데이터가 포함된 데이터프레임
        sensor_col: 센서 값이 저장된 열 이름
        
    Returns:
        주간 패턴 데이터와 주 인덱스
    """
    # 주별, 요일별로 그룹화
    df['date'] = df['timestamp'].dt.date
    df['week'] = df['timestamp'].dt.isocalendar().week
    df['year'] = df['timestamp'].dt.isocalendar().year
    df['weekday'] = df['timestamp'].dt.dayofweek  # 0=월요일, 6=일요일
    
    # 주별, 요일별 평균 계산
    weekly_patterns = df.groupby(['year', 'week', 'weekday'])[sensor_col].mean().unstack()
    
    # 결측치가 있는 주 제거 (완전한 주간 패턴만 사용)
    weekly_patterns = weekly_patterns.dropna()
    
    # 클러스터링을 위한 형태로 변환
    X = weekly_patterns.values
    weeks = weekly_patterns.index
    
    return X, weeks

def find_optimal_k(X, max_k=10):
    """
    최적의 클러스터 수를 찾는 함수 (실루엣 점수와 엘보우 방법 사용)
    
    Args:
        X: 클러스터링할 데이터
        max_k: 검사할 최대 클러스터 수
        
    Returns:
        최적의 클러스터 수, 실루엣 점수, 왜곡도(distortion) 값
    """
    distortions = []
    silhouette_scores = []
    k_values = range(2, max_k + 1)
    
    for k in k_values:
        # KMeans 클러스터링
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        
        # 왜곡도 계산 (클러스터 내 거리 제곱합)
        distortions.append(kmeans.inertia_)
        
        # 실루엣 점수 계산 (클러스터 품질 평가)
        score = silhouette_score(X, kmeans.labels_) if len(np.unique(kmeans.labels_)) > 1 else 0
        silhouette_scores.append(score)
    
    # 최적의 k 선택 (실루엣 점수 최대값)
    optimal_k = k_values[np.argmax(silhouette_scores)]
    
    return optimal_k, silhouette_scores, distortions, k_values

def perform_clustering(X, n_clusters, method='kmeans'):
    """
    클러스터링 수행 함수
    
    Args:
        X: 클러스터링할 데이터
        n_clusters: 클러스터 수
        method: 클러스터링 방법 ('kmeans', 'dbscan', 'tskmeans')
        
    Returns:
        클러스터 레이블, 클러스터 중심
    """
    if method == 'kmeans':
        # 표준 KMeans 클러스터링
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(X)
        centers = model.cluster_centers_
        
    elif method == 'dbscan':
        # DBSCAN 클러스터링 (밀도 기반)
        model = DBSCAN(eps=1.0, min_samples=5)
        labels = model.fit_predict(X)
        
        # DBSCAN은 클러스터 중심이 없으므로 각 클러스터의 평균으로 계산
        unique_labels = np.unique(labels)
        centers = np.zeros((len(unique_labels), X.shape[1]))
        
        for i, label in enumerate(unique_labels):
            if label != -1:  # -1은 노이즈 포인트
                centers[i] = X[labels == label].mean(axis=0)
        
    elif method == 'tskmeans':
        # 시계열 특화 KMeans (DTW 거리 사용)
        X_reshaped = X.reshape(X.shape[0], X.shape[1], 1)  # TimeSeriesKMeans 형식에 맞게 변환
        
        # 시계열 정규화
        scaler = TimeSeriesScalerMeanVariance()
        X_scaled = scaler.fit_transform(X_reshaped)
        
        model = TimeSeriesKMeans(n_clusters=n_clusters, metric="dtw", random_state=42)
        labels = model.fit_predict(X_scaled)
        
        # 중심 추출 및 형태 변환
        centers = model.cluster_centers_.reshape(n_clusters, X.shape[1])
    
    return labels, centers

def render_clustering_ui(df_processed):
    """패턴 클러스터링 시각화 UI를 렌더링합니다."""
    # 폰트 적용
    load_iot_font_css()
    apply_custom_style()
    
    st.subheader("패턴 클러스터링 분석")
    
    # Get equipment type
    equipment_type = get_equipment_type(df_processed)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df_processed.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 클러스터링 옵션
    clustering_options = st.columns([1, 1])
    
    with clustering_options[0]:
        clustering_method = st.selectbox(
            "클러스터링 방법",
            ["K-Means", "시계열 K-Means (DTW)", "DBSCAN (밀도 기반)"],
            help="K-Means: 유클리드 거리 기반 클러스터링\n시계열 K-Means: DTW 거리 기반 시계열 특화 클러스터링\nDBSCAN: 밀도 기반 클러스터링 (이상치 식별에 유용)"
        )
        
        if clustering_method == "K-Means":
            method = 'kmeans'
        elif clustering_method == "시계열 K-Means (DTW)":
            method = 'tskmeans'
        else:
            method = 'dbscan'
    
    with clustering_options[1]:
        pattern_type = st.selectbox(
            "패턴 유형",
            ["일별 패턴 (시간별)", "주간 패턴 (일별)"],
            help="일별 패턴: 각 날짜의 시간별 패턴을 클러스터링\n주간 패턴: 각 주의 일별 패턴을 클러스터링"
        )
    
    # 클러스터링 수행
    try:
        with st.spinner("패턴 클러스터링 중..."):
            df_copy = df_processed.copy()
            
            # 패턴 유형에 따라 데이터 추출
            if pattern_type == "일별 패턴 (시간별)":
                X, time_indices = extract_daily_patterns(df_copy, sensor_col)
                x_labels = [f"{i}시" for i in range(24)]
                pattern_unit = "일"
                time_unit = "시간"
            else:  # "주간 패턴 (일별)"
                X, time_indices = extract_weekly_patterns(df_copy, sensor_col)
                x_labels = ["월", "화", "수", "목", "금", "토", "일"]
                pattern_unit = "주"
                time_unit = "요일"
            
            # 데이터가 충분한지 확인
            if len(X) < 2:
                st.warning(f"클러스터링을 위한 충분한 {pattern_unit} 데이터가 없습니다. 최소 2개 이상의 완전한 {pattern_unit} 데이터가 필요합니다.")
                return
            
            # 최적의 클러스터 수 찾기 (DBSCAN은 제외)
            if method != 'dbscan':
                optimal_k, silhouette_scores, distortions, k_values = find_optimal_k(X, max_k=min(10, len(X)-1))
                n_clusters = st.slider("클러스터 수", min_value=2, max_value=min(10, len(X)-1), value=optimal_k)
            else:
                n_clusters = 2  # DBSCAN은 자동으로 클러스터 수 결정
            
            # 클러스터링 수행
            labels, centers = perform_clustering(X, n_clusters, method)
            
            # 클러스터별 패턴 수 계산
            unique_labels = np.unique(labels)
            cluster_counts = {label: np.sum(labels == label) for label in unique_labels}
            
            # 클러스터링 결과 시각화
            st.subheader(f"{pattern_unit}별 패턴 클러스터링 결과")
            
            # 클러스터별 패턴 시각화
            fig = make_subplots(rows=1, cols=2, 
                              subplot_titles=[f"클러스터별 평균 패턴", f"클러스터별 {pattern_unit} 수"],
                              specs=[[{"type": "scatter"}, {"type": "pie"}]])
            
            # 색상 팔레트
            colors = px.colors.qualitative.Plotly
            
            # 클러스터별 평균 패턴 그래프
            for i, label in enumerate(unique_labels):
                if label != -1:  # -1은 DBSCAN의 노이즈 포인트
                    color_idx = i % len(colors)
                    
                    # 클러스터 중심 (평균 패턴) 추가
                    fig.add_trace(
                        go.Scatter(
                            x=list(range(len(x_labels))), 
                            y=centers[i], 
                            mode='lines+markers',
                            name=f'클러스터 {label} ({cluster_counts[label]}개)',
                            line=dict(color=colors[color_idx], width=3)
                        ),
                        row=1, col=1
                    )
            
            # x축 레이블 설정
            fig.update_xaxes(
                tickvals=list(range(len(x_labels))),
                ticktext=x_labels,
                title=time_unit,
                row=1, col=1
            )
            
            fig.update_yaxes(title=sensor_type_display, row=1, col=1)
            
            # 파이 차트 추가 (클러스터별 패턴 수)
            labels_for_pie = [f"클러스터 {label}" if label != -1 else "이상치" for label in unique_labels]
            values_for_pie = [cluster_counts[label] for label in unique_labels]
            
            fig.add_trace(
                go.Pie(
                    labels=labels_for_pie,
                    values=values_for_pie,
                    hole=0.4,
                    marker=dict(colors=[colors[i % len(colors)] for i in range(len(unique_labels))])
                ),
                row=1, col=2
            )
            
            fig.update_layout(height=500, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # 3D 시각화를 위한 차원 축소
            if X.shape[1] > 3:
                # PCA로 차원 축소
                pca = PCA(n_components=3)
                X_pca = pca.fit_transform(X)
                
                # 3D 산점도
                fig_3d = px.scatter_3d(
                    x=X_pca[:, 0], 
                    y=X_pca[:, 1], 
                    z=X_pca[:, 2],
                    color=[str(label) if label != -1 else "이상치" for label in labels],
                    title="패턴 클러스터링 3D 시각화 (PCA 차원 축소)",
                    labels={"color": "클러스터"}
                )
                
                # 마커 크기 및 불투명도 조정
                fig_3d.update_traces(marker=dict(size=5, opacity=0.7))
                
                fig_3d.update_layout(height=600)
                st.plotly_chart(fig_3d, use_container_width=True)
                
                # 설명 추가
                st.caption("참고: 3D 시각화는 PCA를 통해 고차원 패턴 데이터를 3차원으로 축소한 결과입니다.")
            
            # 클러스터 간 비교 레이더 차트
            if len(unique_labels) > 1:
                st.subheader("클러스터 간 패턴 비교 (레이더 차트)")
                
                fig_radar = go.Figure()
                
                for i, label in enumerate(unique_labels):
                    if label != -1:  # 노이즈 포인트 제외
                        color_idx = i % len(colors)
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=centers[i],
                            theta=x_labels,
                            fill='toself',
                            name=f'클러스터 {label}',
                            line_color=colors[color_idx]
                        ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[min(centers.min(), 0), centers.max() * 1.1]
                        )
                    ),
                    showlegend=True,
                    height=500
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
            
            # 개별 클러스터 상세 분석
            st.subheader("클러스터별 상세 분석")
            
            selected_cluster = st.selectbox(
                "분석할 클러스터 선택", 
                [f"클러스터 {label}" if label != -1 else "이상치" for label in unique_labels]
            )
            
            selected_label = int(selected_cluster.split(" ")[-1]) if "이상치" not in selected_cluster else -1
            
            # 선택된 클러스터의 모든 패턴 시각화
            cluster_patterns = X[labels == selected_label]
            cluster_indices = time_indices[labels == selected_label]
            
            if len(cluster_patterns) > 0:
                st.write(f"**{selected_cluster}** ({len(cluster_patterns)}개 {pattern_unit})")
                
                # 평균과 표준편차 계산
                cluster_mean = cluster_patterns.mean(axis=0)
                cluster_std = cluster_patterns.std(axis=0)
                
                # 평균 패턴과 개별 패턴 시각화
                fig_detail = go.Figure()
                
                # 개별 패턴 추가 (최대 30개까지만)
                max_patterns = min(30, len(cluster_patterns))
                for i in range(max_patterns):
                    fig_detail.add_trace(
                        go.Scatter(
                            x=list(range(len(x_labels))),
                            y=cluster_patterns[i],
                            mode='lines',
                            line=dict(color='rgba(100, 100, 100, 0.2)'),
                            showlegend=False
                        )
                    )
                
                # 평균 패턴 추가
                fig_detail.add_trace(
                    go.Scatter(
                        x=list(range(len(x_labels))),
                        y=cluster_mean,
                        mode='lines+markers',
                        name='평균 패턴',
                        line=dict(color='red', width=3)
                    )
                )
                
                # 표준편차 범위 추가
                fig_detail.add_trace(
                    go.Scatter(
                        x=list(range(len(x_labels))),
                        y=cluster_mean + cluster_std,
                        mode='lines',
                        line=dict(color='rgba(255, 0, 0, 0.3)'),
                        showlegend=False
                    )
                )
                
                fig_detail.add_trace(
                    go.Scatter(
                        x=list(range(len(x_labels))),
                        y=cluster_mean - cluster_std,
                        mode='lines',
                        fill='tonexty',
                        line=dict(color='rgba(255, 0, 0, 0.3)'),
                        name='±1 표준편차'
                    )
                )
                
                # x축 레이블 설정
                fig_detail.update_xaxes(
                    tickvals=list(range(len(x_labels))),
                    ticktext=x_labels,
                    title=time_unit
                )
                
                fig_detail.update_yaxes(title=sensor_type_display)
                fig_detail.update_layout(title=f"{selected_cluster}의 모든 패턴", height=500)
                
                st.plotly_chart(fig_detail, use_container_width=True)
                
                # 패턴이 발생한 날짜/주 리스트
                if pattern_type == "일별 패턴 (시간별)":
                    st.write(f"**이 패턴이 나타난 날짜 (총 {len(cluster_indices)}일):**")
                else:
                    st.write(f"**이 패턴이 나타난 주 (총 {len(cluster_indices)}주):**")
                
                # 날짜 테이블 생성 (최대 20개만 표시)
                date_df = pd.DataFrame({"날짜" if pattern_type == "일별 패턴 (시간별)" else "연도-주": cluster_indices})
                st.dataframe(date_df.head(20))
                
                if len(cluster_indices) > 20:
                    st.caption(f"총 {len(cluster_indices)}개 중 20개만 표시됩니다.")
                
                # 클러스터 통계 표시
                st.write("**클러스터 통계:**")
                
                stat_cols = st.columns(4)
                
                with stat_cols[0]:
                    st.metric("패턴 개수", len(cluster_patterns))
                
                with stat_cols[1]:
                    avg_value = cluster_mean.mean()
                    st.metric(f"평균 {sensor_type_display}", f"{avg_value:.2f}")
                
                with stat_cols[2]:
                    max_time_idx = np.argmax(cluster_mean)
                    st.metric(f"최대값 {time_unit}", x_labels[max_time_idx])
                
                with stat_cols[3]:
                    min_time_idx = np.argmin(cluster_mean)
                    st.metric(f"최소값 {time_unit}", x_labels[min_time_idx])
                
                # 클러스터 특성 요약
                peak_to_valley = cluster_mean.max() - cluster_mean.min()
                variability = cluster_std.mean()
                
                st.write(f"**클러스터 특성:**")
                st.write(f"- 패턴 진폭 (최대-최소): {peak_to_valley:.2f}")
                st.write(f"- 평균 표준편차: {variability:.2f}")
                
                # 다른 클러스터와의 거리 계산
                st.write("**다른 클러스터와의 거리:**")
                
                for i, label in enumerate(unique_labels):
                    if label != selected_label and label != -1:  # 자기 자신과 노이즈 제외
                        # 유클리드 거리 계산
                        distance = np.sqrt(np.sum((cluster_mean - centers[i]) ** 2))
                        st.write(f"- 클러스터 {label}과의 거리: {distance:.2f}")
            
            else:
                st.write("선택한 클러스터에 패턴이 없습니다.")
            
            # 클러스터링 평가 지표
            if method != 'dbscan':
                with st.expander("클러스터링 평가 지표"):
                    # 클러스터 최적 개수 찾기 차트
                    eval_fig = make_subplots(rows=1, cols=2, subplot_titles=["실루엣 점수", "엘보우 방법"])
                    
                    # 실루엣 점수 그래프
                    eval_fig.add_trace(
                        go.Scatter(x=list(k_values), y=silhouette_scores, mode='lines+markers'),
                        row=1, col=1
                    )
                    
                    # 왜곡도 그래프 (엘보우 방법)
                    eval_fig.add_trace(
                        go.Scatter(x=list(k_values), y=distortions, mode='lines+markers'),
                        row=1, col=2
                    )
                    
                    eval_fig.update_xaxes(title="클러스터 수", row=1, col=1)
                    eval_fig.update_xaxes(title="클러스터 수", row=1, col=2)
                    eval_fig.update_yaxes(title="실루엣 점수", row=1, col=1)
                    eval_fig.update_yaxes(title="왜곡도", row=1, col=2)
                    
                    eval_fig.update_layout(height=400)
                    st.plotly_chart(eval_fig, use_container_width=True)
                    
                    st.write(f"최적의 클러스터 수 (실루엣 점수 기준): **{optimal_k}**")
                    st.write(f"현재 클러스터 수: **{n_clusters}**")
                    
                    # 실루엣 점수 설명
                    st.info("""
                    **실루엣 점수**: -1에서 1 사이의 값으로, 1에 가까울수록 클러스터링 품질이 좋음을 의미합니다.
                    **엘보우 방법**: 왜곡도 그래프에서 '팔꿈치' 모양의 굽은 지점이 최적의 클러스터 수를 나타냅니다.
                    """)
    
    except Exception as e:
        st.error(f"클러스터링 분석 중 오류가 발생했습니다: {str(e)}")
    
    # AI 분석 부분 호출
    render_ai_analysis(
        df=df_processed,
        equipment_type=equipment_type,
        sensor_type_display=sensor_type_display,
        clustering_method=clustering_method,
        pattern_type=pattern_type,
        labels=labels if 'labels' in locals() else None,
        centers=centers if 'centers' in locals() else None,
        cluster_counts=cluster_counts if 'cluster_counts' in locals() else None,
        x_labels=x_labels if 'x_labels' in locals() else None
    ) 

def render_ai_analysis(df, equipment_type, sensor_type_display, clustering_method, pattern_type, labels=None, centers=None, cluster_counts=None, x_labels=None):
    """패턴 클러스터링을 위한 AI 분석 부분을 구현합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 클러스터링 분석 전용 키 접두사 사용
    key_prefix = "clustering_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 클러스터링 설정을 세션 상태에 저장
    current_config_key = f"{key_prefix}_current_config"
    
    # 클러스터링 설정이 변경되었는지 확인
    config_changed = False
    if current_config_key in st.session_state:
        current_config = st.session_state[current_config_key]
        if (current_config["clustering_method"] != clustering_method or 
            current_config["pattern_type"] != pattern_type):
            config_changed = True
    else:
        # 최초 실행 시
        config_changed = True
    
    # 현재 클러스터링 설정 업데이트
    st.session_state[current_config_key] = {
        "clustering_method": clustering_method,
        "pattern_type": pattern_type
    }
    
    # AI 분석 프롬프트 키
    clustering_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 클러스터링 설정이 변경되었거나 분석 데이터가 없거나 프롬프트가 없으면 새로 생성
    if config_changed or labels is None or clustering_prompt_key not in st.session_state:
        # 클러스터링 방법에 대한 설명 추가
        method_description = ""
        method_context = ""
        
        if clustering_method == "K-Means":
            method_description = "K-Means는 유클리드 거리를 기반으로 데이터 포인트를 K개의 클러스터로 그룹화하는 알고리즘입니다."
            method_context = "K-Means는 구형(spherical) 클러스터를 찾는 데 적합하며, 각 클러스터의 중심(centroid)을 기준으로 데이터 포인트를 할당합니다."
        elif clustering_method == "시계열 K-Means (DTW)":
            method_description = "시계열 K-Means는 DTW(Dynamic Time Warping) 거리 측정법을 사용하여 시계열 패턴의 유사성을 평가합니다."
            method_context = "DTW는 시간 축에서의 왜곡(시간 지연, 압축, 확장 등)을 허용하므로 시계열 패턴 분석에 적합합니다."
        else:  # "DBSCAN (밀도 기반)"
            method_description = "DBSCAN은 밀도 기반 클러스터링 알고리즘으로, 임의 형태의 클러스터를 찾고 이상치를 식별할 수 있습니다."
            method_context = "DBSCAN은 클러스터 수를 사전에 지정할 필요가 없으며, 밀도가 높은 영역을 클러스터로 식별하고 밀도가 낮은 영역을 이상치로 처리합니다."
        
        # 패턴 유형에 대한 설명 추가
        pattern_description = ""
        if pattern_type == "일별 패턴 (시간별)":
            pattern_description = "일별 패턴 분석은 각 날짜의 시간별 센서 값을 클러스터링하여 유사한 일간 패턴을 식별합니다."
            time_unit = "시간"
        else:  # "주간 패턴 (일별)"
            pattern_description = "주간 패턴 분석은 각 주의 요일별 센서 값을 클러스터링하여 유사한 주간 패턴을 식별합니다."
            time_unit = "요일"
        
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 패턴 클러스터링을 통해 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {clustering_method} 방법을 사용하여 {pattern_type}을 클러스터링했습니다.
이 클러스터링 분석은 {method_description}

클러스터링 컨텍스트: {method_context}
패턴 분석 컨텍스트: {pattern_description}

주요 분석 포인트:
1. 발견된 주요 패턴 클러스터의 특성과 의미
2. 각 클러스터가 나타내는 운영 모드 또는 상태
3. 클러스터 간 차이점과 유사점
4. 시간에 따른 패턴 클러스터 분포 변화
5. 클러스터링 결과를 활용한 장비 운영 최적화 방안
"""
        
        # 분석 프롬프트 생성 (클러스터링 데이터가 있는 경우)
        if labels is not None and centers is not None and x_labels is not None:
            # 클러스터 정보 요약
            unique_labels = np.unique(labels)
            cluster_info = []
            
            for i, label in enumerate(unique_labels):
                if label != -1:  # -1은 DBSCAN의 노이즈 포인트
                    # 클러스터 크기
                    cluster_size = cluster_counts[label]
                    
                    # 클러스터 중심 (평균 패턴)
                    center = centers[i]
                    
                    # 주요 특성 추출
                    max_idx = np.argmax(center)
                    min_idx = np.argmin(center)
                    peak_to_valley = center.max() - center.min()
                    
                    cluster_info.append({
                        "label": label,
                        "size": cluster_size,
                        "max_time": x_labels[max_idx],
                        "min_time": x_labels[min_idx],
                        "peak_to_valley": peak_to_valley,
                        "avg_value": center.mean()
                    })
            
            # 클러스터 정보 문자열로 변환
            clusters_summary = ""
            for info in cluster_info:
                clusters_summary += f"""
## 클러스터 {info['label']} ({info['size']}개 패턴)
- 평균 {sensor_type_display}: {info['avg_value']:.2f}
- 최대값 {time_unit}: {info['max_time']}
- 최소값 {time_unit}: {info['min_time']}
- 패턴 진폭 (최대-최소): {info['peak_to_valley']:.2f}
"""
            
            # 노이즈 포인트 정보 (DBSCAN의 경우)
            noise_count = np.sum(labels == -1) if -1 in unique_labels else 0
            noise_info = f"- 이상치(노이즈) 수: {noise_count}\n" if noise_count > 0 else ""
            
            # 클러스터 간 거리 정보
            distance_info = ""
            if len(unique_labels) > 1 and -1 not in unique_labels:
                distance_info = "\n## 클러스터 간 거리\n"
                for i in range(len(cluster_info)):
                    for j in range(i+1, len(cluster_info)):
                        center_i = centers[cluster_info[i]["label"]]
                        center_j = centers[cluster_info[j]["label"]]
                        distance = np.sqrt(np.sum((center_i - center_j) ** 2))
                        distance_info += f"- 클러스터 {cluster_info[i]['label']}과 클러스터 {cluster_info[j]['label']} 사이: {distance:.2f}\n"
            
            analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 패턴 클러스터링 분석 결과입니다.

## 클러스터링 정보
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 클러스터링 방법: {clustering_method}
- 패턴 유형: {pattern_type}
- 총 패턴 수: {len(labels)}
- 클러스터 수: {len(unique_labels) - (1 if -1 in unique_labels else 0)}
{noise_info}

{clusters_summary}

{distance_info}

## 분석 과제
위 클러스터링 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. 발견된 주요 패턴 클러스터의 특성과 의미
   - 각 클러스터의 고유한 특징과 시간적 패턴 설명
   - 클러스터 크기와 분포가 의미하는 바

2. 클러스터와 운영 모드의 연관성
   - 각 클러스터가 나타내는 장비의 운영 모드 또는 상태 추론
   - 패턴 특성(최대값, 최소값, 진폭 등)에 기반한 해석

3. 클러스터 간 차이점과 유사점 분석
   - 주요 클러스터 간의 핵심적인 차이점
   - 클러스터 패턴 형태의 유사성 및 차이점이 의미하는 바

4. 이상 패턴(존재하는 경우) 분석
   - 이상 패턴의 특성과 정상 패턴과의 차이점
   - 이러한 이상 패턴이 장비 운영에 미치는 영향 추론

5. 클러스터링 결과를 활용한 장비 운영 최적화 방안
   - 효율적인 운영을 위한 최적 패턴 식별
   - 특정 클러스터 패턴이 장비 성능에 미치는 영향과 개선 방안
   - 패턴 클러스터링 결과를 활용한 예측 유지보수 전략

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요.
"""
        else:
            # 클러스터링 데이터가 없는 경우의 기본 프롬프트
            analysis_prompt = f"""{system_prompt}

IoT 센서 데이터의 패턴 클러스터링 분석을 위해 다음 정보가 필요합니다:

- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 클러스터링 방법: {clustering_method}
- 패턴 유형: {pattern_type}

현재 클러스터링 결과가 없습니다. 클러스터링 분석을 실행하면 다음과 같은 인사이트를 얻을 수 있습니다:

1. 발견된 주요 패턴 클러스터의 특성과 의미
2. 각 클러스터가 나타내는 운영 모드 또는 상태
3. 클러스터 간 차이점과 유사점
4. 시간에 따른 패턴 클러스터 분포 변화
5. 클러스터링 결과를 활용한 장비 운영 최적화 방안

패턴 클러스터링을 통해 {equipment_type}의 운영 특성을 이해하고 최적화 방안을 도출할 수 있습니다.
"""
        
        # 클러스터링 전용 프롬프트로 저장
        st.session_state[clustering_prompt_key] = analysis_prompt
        
        # 설정이 변경되면 캐시도 초기화
        if config_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"클러스터링 설정이 변경되어 캐시 초기화: {clustering_method}, {pattern_type}")
        
        # 디버깅용 로깅
        print(f"클러스터링 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
    else:
        # 캐시된 클러스터링 전용 프롬프트 사용
        analysis_prompt = st.session_state[clustering_prompt_key]
        print(f"캐시된 클러스터링 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 패턴 클러스터링 분석")

    # 세션 상태 키 정의 - 모두 클러스터링 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 클러스터링 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 클러스터링 분석 전용
    def on_clustering_analyze_click():
        # 캐시 초기화
        if cache_state_key in st.session_state:
            # 캐시 키 생성
            from ..utils.ai_utils import generate_cache_key
            cache_key = generate_cache_key(
                prompt=analysis_prompt,
                model=st.session_state.selected_model,
                temperature=st.session_state.temperature
            )
            st.session_state[cache_state_key].pop(cache_key, None)
        # 대화 기록 초기화
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
        # 실행 상태 설정
        st.session_state[running_key] = True
        
        # 디버깅용 로깅
        print(f"클러스터링 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 클러스터링 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 패턴 클러스터링 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_clustering_analyze_click,
            use_container_width=True
        )
    
    # 이전 분석 결과가 있는 경우 (캐시에 있는 경우)
    if cache_state_key in st.session_state and len(st.session_state[cache_state_key]) > 0:
        # 캐시 키 생성
        from ..utils.ai_utils import generate_cache_key
        cache_key = generate_cache_key(
            prompt=analysis_prompt,
            model=st.session_state.selected_model,
            temperature=st.session_state.temperature
        )
        
        if cache_key in st.session_state[cache_state_key]:
            cached_response = st.session_state[cache_state_key][cache_key]
            with st.chat_message("assistant"):
                st.markdown(cached_response["response"])
                if cached_response.get("metadata"):
                    metadata_text = "\n\n---\n**처리 정보**\n```json\n"
                    metadata_text += json.dumps(cached_response["metadata"], indent=2, ensure_ascii=False)
                    metadata_text += "\n```"
                    st.markdown(metadata_text)
            # 실행 상태 업데이트
            st.session_state[running_key] = False
            print(f"클러스터링 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"클러스터링 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 패턴 클러스터링 데이터를 분석하고 있습니다..."):
                print(f"클러스터링 분석: generate_ai_response 함수 호출 전")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"클러스터링 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        if labels is None:
            st.info("패턴 클러스터링을 먼저 실행한 후 AI 분석을 요청해주세요.")
        else:
            st.info("AI 분석을 실행하려면 'AI 패턴 클러스터링 분석 실행' 버튼을 클릭하세요. 클러스터링 결과에 대한 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 패턴 클러스터링 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"클러스터링: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 패턴 클러스터링에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 