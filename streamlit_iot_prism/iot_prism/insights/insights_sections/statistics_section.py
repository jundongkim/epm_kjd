import pandas as pd
import numpy as np
import io
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats as scipy_stats
from ..insights_plotly_style import apply_insights_plotly_style


def generate_statistics_section(df, equipment_type, sensor_type, analysis_depth, include_visuals):
    """통계 섹션을 생성하는 함수"""
    section = {
        'title': '통계 분석',
        'content': '',
        'image': None,
        'table': None
    }
    
    # 기본 통계량 계산
    stats = df[sensor_type].describe()
    
    # 편차 및 변동성 지표 계산
    cv = stats['std'] / stats['mean'] * 100  # 변동 계수 (%)
    skewness = df[sensor_type].skew()
    kurtosis = df[sensor_type].kurtosis()
    
    # 분위수 계산
    q1 = stats['25%']
    q2 = stats['50%']
    q3 = stats['75%']
    iqr = q3 - q1
    
    # 이상치 경계
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # 통계 내용 생성
    statistics = f"""
{equipment_type}의 {sensor_type} 데이터에 대한 통계 분석 결과입니다.

### 기본 통계량
- **평균**: {stats['mean']:.4f}
- **표준편차**: {stats['std']:.4f}
- **최소값**: {stats['min']:.4f}
- **최대값**: {stats['max']:.4f}
- **중앙값**: {stats['50%']:.4f}

### 분포 특성
- **변동계수(CV)**: {cv:.2f}% ({'매우 안정적' if cv < 5 else '안정적' if cv < 15 else '변동성 있음' if cv < 30 else '매우 변동적'})
- **왜도(Skewness)**: {skewness:.4f} ({'좌측 편향(왼쪽으로 긴 꼬리)' if skewness < -0.5 else '대칭에 가까움' if abs(skewness) <= 0.5 else '우측 편향(오른쪽으로 긴 꼬리)'})
- **첨도(Kurtosis)**: {kurtosis:.4f} ({'정규분포보다 뾰족함' if kurtosis > 0 else '정규분포에 가까움' if abs(kurtosis) <= 0.5 else '정규분포보다 완만함'})

### 분위수 분석
- **1사분위수(Q1)**: {q1:.4f}
- **2사분위수(중앙값)**: {q2:.4f}
- **3사분위수(Q3)**: {q3:.4f}
- **IQR(Q3-Q1)**: {iqr:.4f}
"""

    # 분석 깊이에 따른 추가 정보
    if analysis_depth >= 3:
        # 시간별 통계량
        df_copy = df.copy()
        df_copy['hour'] = df_copy['timestamp'].dt.hour
        hourly_stats = df_copy.groupby('hour')[sensor_type].agg(['mean', 'std', 'min', 'max'])
        hourly_stats.columns = ['평균', '표준편차', '최소값', '최대값']
        
        # 가장 변동성이 큰 시간대
        hourly_cv = hourly_stats['표준편차'] / hourly_stats['평균'] * 100
        most_variable_hour = hourly_cv.idxmax()
        most_stable_hour = hourly_cv.idxmin()
        
        statistics += f"""
### 시간대별 특성
- **가장 변동성이 큰 시간대**: {most_variable_hour}시 (CV: {hourly_cv[most_variable_hour]:.2f}%)
- **가장 안정적인 시간대**: {most_stable_hour}시 (CV: {hourly_cv[most_stable_hour]:.2f}%)
"""

        # 테이블 데이터 생성
        section['table'] = hourly_stats.reset_index()
        section['table'].columns = ['시간', '평균', '표준편차', '최소값', '최대값']
    
    if analysis_depth >= 4:
        # 정규성 검정 (Shapiro-Wilk)
        # 데이터가 많은 경우 샘플링
        sample_size = min(5000, len(df))
        sample_data = df[sensor_type].sample(sample_size) if len(df) > sample_size else df[sensor_type]
        
        try:
            shapiro_test = scipy_stats.shapiro(sample_data)
            shapiro_stat = shapiro_test[0]
            shapiro_p = shapiro_test[1]
            
            statistics += f"""
### 정규성 검정 (Shapiro-Wilk)
- **검정 통계량**: {shapiro_stat:.4f}
- **p-값**: {shapiro_p:.8f}
- **해석**: 데이터는 {'정규 분포를 따르지 않습니다' if shapiro_p < 0.05 else '정규 분포를 따를 가능성이 있습니다'} (유의수준 0.05 기준)
"""
        except:
            # 정규성 검정에 실패한 경우 대체 메시지
            statistics += """
### 정규성 검정
- 데이터 특성으로 인해 정규성 검정을 수행할 수 없습니다.
"""
    
    if analysis_depth >= 5:
        # 이상치(Outlier) 통계
        outliers = df[(df[sensor_type] < lower_bound) | (df[sensor_type] > upper_bound)]
        outliers_count = len(outliers)
        outliers_percentage = outliers_count / len(df) * 100
        
        # 극단값(Extreme Values) 확인
        z_scores = abs((df[sensor_type] - stats['mean']) / stats['std'])
        extreme_values = df[z_scores > 3]
        extreme_values_count = len(extreme_values)
        extreme_values_percentage = extreme_values_count / len(df) * 100
        
        statistics += f"""
### 이상치 및 극단값 분석
- **IQR 기준 이상치**: {outliers_count}개 ({outliers_percentage:.2f}%)
- **3-시그마 기준 극단값**: {extreme_values_count}개 ({extreme_values_percentage:.2f}%)
- **정상 범위(IQR 기준)**: {lower_bound:.4f} ~ {upper_bound:.4f}
"""
        
        if extreme_values_count > 0:
            # 극단값의 패턴 분석
            extreme_values_copy = extreme_values.copy()
            extreme_values_copy['hour'] = extreme_values_copy['timestamp'].dt.hour
            extreme_values_copy['day'] = extreme_values_copy['timestamp'].dt.day_name()
            
            hour_counts = extreme_values_copy['hour'].value_counts().sort_index()
            most_common_hour = hour_counts.idxmax() if not hour_counts.empty else None
            
            day_counts = extreme_values_copy['day'].value_counts()
            most_common_day = day_counts.idxmax() if not day_counts.empty else None
            
            if most_common_hour is not None and most_common_day is not None:
                statistics += f"""
- **극단값 패턴**: 극단값은 주로 {most_common_day}요일의 {most_common_hour}시에 가장 빈번하게 발생함
"""
    
    # 시각화 추가
    if include_visuals:
        try:
            # Plotly로 2x2 서브플롯 생성
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    f'{sensor_type} 분포',
                    '상자 그림',
                    '시간별 평균 및 표준편차',
                    'QQ Plot (정규성 확인)'
                ),
                specs=[
                    [{"type": "histogram"}, {"type": "box"}],
                    [{"type": "scatter"}, {"type": "scatter"}]
                ]
            )
            
            # 히스토그램
            fig.add_trace(
                go.Histogram(
                    x=df[sensor_type],
                    name=sensor_type,
                    opacity=0.7,
                    marker_color='rgba(25, 118, 210, 0.7)'
                ),
                row=1, col=1
            )
            
            # KDE 추가
            x_kde = np.linspace(df[sensor_type].min(), df[sensor_type].max(), 1000)
            kde = scipy_stats.gaussian_kde(df[sensor_type].dropna())
            y_kde = kde(x_kde)
            
            # 히스토그램에 맞게 KDE 스케일링
            hist_values, bin_edges = np.histogram(df[sensor_type], bins=30)
            scaling_factor = max(hist_values) / max(y_kde) if max(y_kde) > 0 else 1
            
            fig.add_trace(
                go.Scatter(
                    x=x_kde,
                    y=y_kde * scaling_factor,
                    mode='lines',
                    name='KDE',
                    line=dict(color='rgba(255, 87, 34, 0.8)', width=2)
                ),
                row=1, col=1
            )
            
            # 상자 그림
            fig.add_trace(
                go.Box(
                    y=df[sensor_type],
                    name=sensor_type,
                    marker_color='rgba(76, 175, 80, 0.7)'
                ),
                row=1, col=2
            )
            
            # 시간별 평균 및 표준편차
            if analysis_depth >= 3:  # 시간별 데이터는 분석 깊이 3 이상에서만 계산됨
                hourly_means = df_copy.groupby('hour')[sensor_type].mean()
                hourly_stds = df_copy.groupby('hour')[sensor_type].std()
                
                fig.add_trace(
                    go.Scatter(
                        x=hourly_means.index,
                        y=hourly_means.values,
                        mode='lines+markers',
                        name='시간별 평균',
                        line=dict(color='rgba(25, 118, 210, 0.9)', width=2)
                    ),
                    row=2, col=1
                )
                
                # 표준편차 범위 추가
                fig.add_trace(
                    go.Scatter(
                        x=hourly_means.index,
                        y=hourly_means + hourly_stds,
                        mode='lines',
                        name='상한 (평균+표준편차)',
                        line=dict(color='rgba(25, 118, 210, 0.3)', width=1, dash='dash'),
                        showlegend=False
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=hourly_means.index,
                        y=hourly_means - hourly_stds,
                        mode='lines',
                        name='하한 (평균-표준편차)',
                        line=dict(color='rgba(25, 118, 210, 0.3)', width=1, dash='dash'),
                        fill='tonexty',
                        fillcolor='rgba(25, 118, 210, 0.1)',
                        showlegend=False
                    ),
                    row=2, col=1
                )
            
            # QQ Plot 데이터 생성
            sample_data = df[sensor_type].sample(min(1000, len(df))) if len(df) > 1000 else df[sensor_type]
            sample_data = sample_data.dropna()
            
            # 데이터 정규화
            sorted_data = np.sort(sample_data)
            n = len(sorted_data)
            mean = np.mean(sorted_data)
            std = np.std(sorted_data)
            normalized_data = (sorted_data - mean) / std if std > 0 else sorted_data - mean
            
            # 이론적 분위수
            theoretical_quantiles = scipy_stats.norm.ppf(np.arange(1, n + 1) / (n + 1))
            
            # NaN 및 Infinity 값 필터링
            valid_indices = np.isfinite(theoretical_quantiles)
            theoretical_quantiles = theoretical_quantiles[valid_indices]
            normalized_data = normalized_data[valid_indices] if len(normalized_data) > 0 else normalized_data
            
            # QQ Plot 트레이스 추가
            fig.add_trace(
                go.Scatter(
                    x=theoretical_quantiles,
                    y=normalized_data,
                    mode='markers',
                    name='데이터 포인트',
                    marker=dict(
                        size=6,
                        color='rgba(156, 39, 176, 0.7)',
                        line=dict(width=1, color='purple')
                    )
                ),
                row=2, col=2
            )
            
            # 기준선 추가
            if len(theoretical_quantiles) > 0:
                min_x = theoretical_quantiles.min()
                max_x = theoretical_quantiles.max()
                line_x = np.linspace(min_x, max_x, 100)
                
                fig.add_trace(
                    go.Scatter(
                        x=line_x,
                        y=line_x,
                        mode='lines',
                        name='정규분포 기준선',
                        line=dict(color='red', width=2, dash='dash')
                    ),
                    row=2, col=2
                )
            
            # 레이아웃 설정
            fig.update_layout(
                height=800,
                title_text=f"{equipment_type}의 {sensor_type} 통계 분석",
                showlegend=True
            )
            
            # 스타일 적용
            apply_insights_plotly_style(fig)
            
            # 그림을 이미지로 변환
            img_bytes = fig.to_image(format="png", engine="kaleido", width=1200, height=800)
            img_str = base64.b64encode(img_bytes).decode('utf-8')
            
            section['image'] = img_str
            
        except Exception as e:
            print(f"통계 시각화 생성 중 오류 발생: {e}")
    
    section['content'] = statistics
    return section 