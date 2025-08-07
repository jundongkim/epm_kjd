import pandas as pd
import numpy as np
from scipy import stats
import io
import base64
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..insights_plotly_style import apply_insights_plotly_style


def generate_anomaly_section(df, equipment_type, sensor_type, analysis_depth, include_visuals):
    """이상치 분석 섹션을 생성하는 함수"""
    section = {
        'title': '이상치 분석',
        'content': '',
        'image': None,
        'table': None
    }
    
    # 기본 통계량 계산
    mean_val = df[sensor_type].mean()
    std_val = df[sensor_type].std()
    
    # 분위수 계산
    q1 = df[sensor_type].quantile(0.25)
    q3 = df[sensor_type].quantile(0.75)
    iqr = q3 - q1
    
    # 이상치 경계 계산
    lower_bound_iqr = q1 - 1.5 * iqr
    upper_bound_iqr = q3 + 1.5 * iqr
    
    # Z-score 기반 이상치 경계 (3-시그마)
    lower_bound_z = mean_val - 3 * std_val
    upper_bound_z = mean_val + 3 * std_val
    
    # 이상치 식별
    outliers_iqr = df[(df[sensor_type] < lower_bound_iqr) | (df[sensor_type] > upper_bound_iqr)]
    outliers_z = df[(df[sensor_type] < lower_bound_z) | (df[sensor_type] > upper_bound_z)]
    
    # 이상치 비율
    outliers_iqr_pct = len(outliers_iqr) / len(df) * 100 if len(df) > 0 else 0
    outliers_z_pct = len(outliers_z) / len(df) * 100 if len(df) > 0 else 0
    
    # 이상치 분석 내용 생성
    anomaly_content = f"""
{equipment_type}의 {sensor_type} 데이터에 대한 이상치 분석 결과입니다.

### 이상치 탐지 요약
- **IQR 방법 기준 이상치**: {len(outliers_iqr)}개 ({outliers_iqr_pct:.2f}%)
- **Z-score 방법 기준 이상치**: {len(outliers_z)}개 ({outliers_z_pct:.2f}%)
- **IQR 정상 범위**: {lower_bound_iqr:.4f} ~ {upper_bound_iqr:.4f}
- **Z-score 정상 범위**: {lower_bound_z:.4f} ~ {upper_bound_z:.4f}
"""
    
    # 이상치 심각도 평가
    if outliers_iqr_pct > 0:
        # 이상치 평균 편차
        outliers_mean_deviation = abs(outliers_iqr[sensor_type] - mean_val).mean()
        # 정상치 평균 편차
        normal_data = df[(df[sensor_type] >= lower_bound_iqr) & (df[sensor_type] <= upper_bound_iqr)]
        normal_mean_deviation = abs(normal_data[sensor_type] - mean_val).mean()
        
        # 이상치 심각도 (이상치 편차 / 정상치 편차)
        if normal_mean_deviation > 0:
            severity = outliers_mean_deviation / normal_mean_deviation
            
            anomaly_content += f"""
### 이상치 심각도 평가
- **이상치 평균 편차**: {outliers_mean_deviation:.4f}
- **정상치 평균 편차**: {normal_mean_deviation:.4f}
- **심각도 지수**: {severity:.2f}x (이상치가 정상치보다 평균적으로 {severity:.2f}배 더 편차가 큼)
- **심각도 평가**: {'매우 심각' if severity > 10 else '심각' if severity > 5 else '중간' if severity > 3 else '경미'}
"""
    
    # 시간별/요일별 이상치 변수 초기화
    hour_counts = pd.Series()
    day_counts = pd.Series()
    
    # 분석 깊이에 따른 추가 정보
    if analysis_depth >= 3 and len(outliers_iqr) > 0:
        # 이상치 시간 패턴 분석
        outliers_copy = outliers_iqr.copy()
        outliers_copy['hour'] = outliers_copy['timestamp'].dt.hour
        outliers_copy['day_of_week'] = outliers_copy['timestamp'].dt.day_name()
        
        # 시간별 이상치 빈도
        hour_counts = outliers_copy['hour'].value_counts().sort_index()
        
        # 요일별 이상치 빈도
        day_counts = outliers_copy['day_of_week'].value_counts()
        
        # 가장 빈번한 시간대와 요일
        if not hour_counts.empty:
            most_common_hour = hour_counts.idxmax()
            most_common_hour_count = hour_counts.max()
            
            anomaly_content += f"""
### 이상치 발생 패턴
- **가장 빈번한 발생 시간**: {most_common_hour}시 ({most_common_hour_count}회)
"""
        
        if not day_counts.empty:
            most_common_day = day_counts.idxmax()
            most_common_day_count = day_counts.max()
            
            anomaly_content += f"""
- **가장 빈번한 발생 요일**: {most_common_day} ({most_common_day_count}회)
"""
    
    if analysis_depth >= 4 and len(outliers_iqr) > 0:
        # 이상치 군집 분석
        # 연속된 이상치 발생 탐지
        outliers_sorted = outliers_iqr.sort_values('timestamp')
        
        if len(outliers_sorted) > 1:
            # 타임스탬프 간 차이 계산
            outliers_sorted['time_diff'] = outliers_sorted['timestamp'].diff().dt.total_seconds()
            
            # 연속된 이상치 그룹 식별 (60초 이내 발생을 연속으로 간주)
            outliers_sorted['group'] = (outliers_sorted['time_diff'] > 60).cumsum()
            
            # 그룹별 개수
            group_counts = outliers_sorted['group'].value_counts().sort_values(ascending=False)
            
            if not group_counts.empty:
                largest_group = group_counts.index[0]
                largest_group_count = group_counts.iloc[0]
                
                if largest_group_count > 1:
                    # 가장 큰 군집의 시작과 끝 시간
                    largest_group_data = outliers_sorted[outliers_sorted['group'] == largest_group]
                    start_time = largest_group_data['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S')
                    end_time = largest_group_data['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
                    duration = (largest_group_data['timestamp'].max() - largest_group_data['timestamp'].min()).total_seconds() / 60
                    
                    anomaly_content += f"""
### 이상치 군집 분석
- **가장 큰 이상치 군집**: {largest_group_count}개의 연속 이상치
- **발생 시간**: {start_time} ~ {end_time}
- **지속 시간**: {duration:.1f}분
- **군집 내 평균값**: {largest_group_data[sensor_type].mean():.4f}
- **군집 내 최대값**: {largest_group_data[sensor_type].max():.4f}
"""
    
    if analysis_depth >= 5:
        # 이상치 발생 추이 분석
        # 데이터 기간을 균등하게 나누어 이상치 비율 계산
        date_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 86400  # 일 단위
        
        if date_range >= 3:  # 최소 3일 이상의 데이터가 있는 경우
            # 데이터를 5개 구간으로 나누기
            df_copy = df.copy()
            min_date = df_copy['timestamp'].min()
            max_date = df_copy['timestamp'].max()
            interval = (max_date - min_date) / 5
            
            periods = []
            for i in range(5):
                start_date = min_date + i * interval
                end_date = min_date + (i + 1) * interval if i < 4 else max_date + timedelta(seconds=1)
                
                period_data = df_copy[(df_copy['timestamp'] >= start_date) & (df_copy['timestamp'] < end_date)]
                
                if len(period_data) > 0:
                    # IQR 방법으로 이상치 계산
                    period_outliers = period_data[(period_data[sensor_type] < lower_bound_iqr) | (period_data[sensor_type] > upper_bound_iqr)]
                    outlier_ratio = len(period_outliers) / len(period_data) * 100
                    
                    periods.append({
                        'period': i + 1,
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': (end_date - timedelta(seconds=1)).strftime('%Y-%m-%d'),
                        'outlier_count': len(period_outliers),
                        'total_count': len(period_data),
                        'outlier_ratio': outlier_ratio
                    })
            
            if periods:
                # 기간별 이상치 비율 표 생성
                section['table'] = pd.DataFrame(periods)
                
                # 추이 분석
                first_period_ratio = periods[0]['outlier_ratio']
                last_period_ratio = periods[-1]['outlier_ratio']
                ratio_change = last_period_ratio - first_period_ratio
                
                trend_description = '증가' if ratio_change > 1 else '감소' if ratio_change < -1 else '유지'
                
                anomaly_content += f"""
### 이상치 발생 추이 분석
- **초기 이상치 비율**: {first_period_ratio:.2f}%
- **최근 이상치 비율**: {last_period_ratio:.2f}%
- **변화**: {abs(ratio_change):.2f}% {trend_description}
- **추이 평가**: {'이상치 발생이 증가하는 추세로, 주의가 필요합니다.' if ratio_change > 2 else '이상치 발생이 감소하는 추세로, 긍정적인 변화입니다.' if ratio_change < -2 else '이상치 발생 비율이 안정적으로 유지되고 있습니다.'}
"""
    
    # 시각화 추가
    if include_visuals:
        try:
            # Plotly로 2x2 서브플롯 생성
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    '시계열 데이터와 이상치',
                    '박스플롯',
                    '시간별 이상치 발생 빈도',
                    '이상치 발생 추이'
                ),
                specs=[
                    [{"type": "scatter"}, {"type": "box"}],
                    [{"type": "bar"}, {"type": "scatter"}]
                ]
            )
            
            # 1. 시계열 그래프와 이상치 표시
            # 정상 데이터
            normal_data = df[(df[sensor_type] >= lower_bound_iqr) & (df[sensor_type] <= upper_bound_iqr)]
            
            # 샘플링 (시각화에 너무 많은 포인트가 있는 경우)
            max_points = 5000
            if len(normal_data) > max_points:
                step = len(normal_data) // max_points
                normal_data_sample = normal_data.iloc[::step]
            else:
                normal_data_sample = normal_data
                
            # 정상 데이터 트레이스
            fig.add_trace(
                go.Scatter(
                    x=normal_data_sample['timestamp'],
                    y=normal_data_sample[sensor_type],
                    mode='lines',
                    name='정상 데이터',
                    line=dict(color='rgba(25, 118, 210, 0.5)', width=1)
                ),
                row=1, col=1
            )
            
            # 이상치 트레이스 (IQR 기준)
            if len(outliers_iqr) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=outliers_iqr['timestamp'],
                        y=outliers_iqr[sensor_type],
                        mode='markers',
                        name='이상치 (IQR 기준)',
                        marker=dict(
                            color='rgba(255, 0, 0, 0.8)',
                            size=8
                        )
                    ),
                    row=1, col=1
                )
            
            # 경계선 추가
            fig.add_hline(
                y=upper_bound_iqr,
                line_dash="dash",
                line_color="red",
                opacity=0.7,
                row=1, col=1,
                annotation_text="상한 경계"
            )
            
            fig.add_hline(
                y=lower_bound_iqr,
                line_dash="dash",
                line_color="red",
                opacity=0.7,
                row=1, col=1,
                annotation_text="하한 경계"
            )
            
            # 2. 박스플롯 추가
            fig.add_trace(
                go.Box(
                    y=df[sensor_type],
                    name=sensor_type,
                    boxmean=True,
                    marker_color='rgba(76, 175, 80, 0.7)'
                ),
                row=1, col=2
            )
            
            # 3. 시간별 이상치 발생 빈도
            if 'hour_counts' in locals() and not hour_counts.empty:
                fig.add_trace(
                    go.Bar(
                        x=hour_counts.index,
                        y=hour_counts.values,
                        name='시간별 이상치 빈도',
                        marker_color='rgba(156, 39, 176, 0.7)'
                    ),
                    row=2, col=1
                )
            
            # 4. 이상치 발생 추이 (periods가 있는 경우)
            if 'periods' in locals() and periods:
                period_df = pd.DataFrame(periods)
                
                fig.add_trace(
                    go.Scatter(
                        x=period_df['period'],
                        y=period_df['outlier_ratio'],
                        mode='lines+markers',
                        name='이상치 비율 추이',
                        line=dict(color='rgba(255, 87, 34, 0.9)', width=2)
                    ),
                    row=2, col=2
                )
                
                # 추세선 추가
                if len(period_df) > 1:
                    x_values = period_df['period'].values
                    y_values = period_df['outlier_ratio'].values
                    
                    # 선형 회귀 계산
                    slope, intercept = np.polyfit(x_values, y_values, 1)
                    trend_line = slope * x_values + intercept
                    
                    fig.add_trace(
                        go.Scatter(
                            x=x_values,
                            y=trend_line,
                            mode='lines',
                            name='추세선',
                            line=dict(color='rgba(0, 150, 136, 0.8)', width=2, dash='dash')
                        ),
                        row=2, col=2
                    )
            
            # 레이아웃 설정
            fig.update_layout(
                height=800,
                title_text=f"{equipment_type} {sensor_type} 이상치 분석",
                showlegend=True
            )
            
            # 스타일 적용
            apply_insights_plotly_style(fig)
            
            # 그림을 이미지로 변환
            img_bytes = fig.to_image(format="png", engine="kaleido", width=1200, height=800)
            img_str = base64.b64encode(img_bytes).decode('utf-8')
            
            section['image'] = img_str
            
        except Exception as e:
            print(f"이상치 시각화 생성 중 오류 발생: {e}")
    
    section['content'] = anomaly_content
    return section 