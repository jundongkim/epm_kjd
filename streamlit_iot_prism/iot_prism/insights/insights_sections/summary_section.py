import pandas as pd
import numpy as np
import io
import base64
from datetime import datetime, timedelta
import plotly.graph_objects as go
from ..insights_plotly_style import apply_insights_plotly_style


def generate_summary_section(df, equipment_type, sensor_type, analysis_depth, include_visuals):
    """요약 섹션을 생성하는 함수"""
    section = {
        'title': '요약',
        'content': '',
        'image': None
    }
    
    # 데이터 기본 정보
    data_count = len(df)
    date_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 86400  # 일 단위
    sensor_avg = df[sensor_type].mean()
    sensor_std = df[sensor_type].std()
    
    # 이상치 수 계산
    z_scores = abs((df[sensor_type] - sensor_avg) / sensor_std)
    anomaly_count = len(df[z_scores > 3.0])
    anomaly_pct = anomaly_count / data_count * 100 if data_count > 0 else 0
    
    # 추세 계산
    start_avg = df[sensor_type].iloc[:int(len(df)*0.1)].mean() if len(df) > 10 else df[sensor_type].iloc[0]
    end_avg = df[sensor_type].iloc[-int(len(df)*0.1):].mean() if len(df) > 10 else df[sensor_type].iloc[-1]
    trend_change = ((end_avg - start_avg) / start_avg) * 100 if start_avg != 0 else 0
    
    # 추세 방향 결정
    if trend_change > 5:
        trend_direction = "상승"
        trend_icon = "↗"
    elif trend_change > 1:
        trend_direction = "소폭 상승"
        trend_icon = "↗"
    elif trend_change < -5:
        trend_direction = "하락"
        trend_icon = "↘"
    elif trend_change < -1:
        trend_direction = "소폭 하락"
        trend_icon = "↘"
    else:
        trend_direction = "안정적"
        trend_icon = "→"
    
    # 요약 내용 생성
    summary = f"""
{equipment_type}의 {sensor_type} 데이터에 대한 분석 요약입니다.

- **데이터 개요**: 총 {data_count:,}개의 데이터 포인트가 {date_range:.1f}일 동안 기록되었습니다.
- **핵심 지표**: 평균값 {sensor_avg:.2f}, 표준편차 {sensor_std:.2f}
- **추세 분석**: {trend_direction}({trend_icon}) - {abs(trend_change):.1f}% {'증가' if trend_change > 0 else '감소'}
- **이상치 분석**: 전체 데이터의 {anomaly_pct:.1f}%({anomaly_count}개)가 이상치로 식별됨
"""
    
    # 분석 깊이에 따른 추가 정보
    if analysis_depth >= 3:
        # 시간대별 패턴 간략 분석
        df_copy = df.copy()
        df_copy['hour'] = df_copy['timestamp'].dt.hour
        hourly_avg = df_copy.groupby('hour')[sensor_type].mean()
        peak_hour = hourly_avg.idxmax()
        low_hour = hourly_avg.idxmin()
        
        summary += f"""
- **시간 패턴**: {peak_hour}시에 최대값, {low_hour}시에 최소값을 보이는 일일 패턴 관찰됨
"""
    
    if analysis_depth >= 4:
        # 변화율 계산 및 급격한 변화 탐지
        df_copy = df.copy()
        df_copy['prev_value'] = df_copy[sensor_type].shift(1)
        df_copy['change_rate'] = (df_copy[sensor_type] - df_copy['prev_value']) / df_copy['prev_value'] * 100
        df_copy = df_copy.dropna()
        
        rapid_changes = df_copy[abs(df_copy['change_rate']) > 10]
        if len(rapid_changes) > 0:
            rapid_change_pct = len(rapid_changes) / len(df_copy) * 100
            summary += f"""
- **급격한 변화**: 전체 데이터의 {rapid_change_pct:.1f}%에서 10% 이상의 급격한 변화가 관찰됨
"""
    
    if analysis_depth >= 5:
        # 정상 운전 범위 및 이상치 발생 추이
        q1 = df[sensor_type].quantile(0.25)
        q3 = df[sensor_type].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        out_of_range = df[(df[sensor_type] < lower_bound) | (df[sensor_type] > upper_bound)]
        
        # 15일 단위로 이상치 비율 계산
        if date_range > 15:
            df_copy = df.copy()
            start_date = df_copy['timestamp'].min()
            periods = []
            
            current_date = start_date
            end_date = df_copy['timestamp'].max()
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=15)
                period_data = df_copy[(df_copy['timestamp'] >= current_date) & (df_copy['timestamp'] < next_date)]
                
                if len(period_data) > 0:
                    period_anomalies = period_data[(period_data[sensor_type] < lower_bound) | (period_data[sensor_type] > upper_bound)]
                    anomaly_ratio = len(period_anomalies) / len(period_data) * 100
                    periods.append({
                        'start_date': current_date.strftime('%Y-%m-%d'),
                        'anomaly_ratio': anomaly_ratio
                    })
                
                current_date = next_date
            
            if len(periods) > 1:
                first_period = periods[0]['anomaly_ratio']
                last_period = periods[-1]['anomaly_ratio']
                if last_period > first_period * 1.5:
                    summary += f"""
- **이상치 발생 추이**: 이상치 발생 비율이 증가 추세를 보이며, 초기 {first_period:.1f}%에서 최근 {last_period:.1f}%로 증가함
"""
                elif first_period > last_period * 1.5:
                    summary += f"""
- **이상치 발생 추이**: 이상치 발생 비율이 감소 추세를 보이며, 초기 {first_period:.1f}%에서 최근 {last_period:.1f}%로 감소함
"""
    
    # 시각화 추가
    if include_visuals:
        try:
            # Plotly를 사용한 시계열 그래프 생성
            fig = go.Figure()
            
            # 원본 데이터 트레이스 추가
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[sensor_type],
                    mode='lines',
                    name=sensor_type,
                    line=dict(color='rgba(40, 100, 200, 0.7)', width=1.5)
                )
            )
            
            # 이동평균선 추가
            window_size = len(df) // 20 if len(df) > 20 else 1
            df['moving_avg'] = df[sensor_type].rolling(window=window_size).mean()
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['moving_avg'],
                    mode='lines',
                    name=f'이동평균({window_size}포인트)',
                    line=dict(color='rgba(255, 0, 0, 0.8)', width=2.5)
                )
            )
            
            # 레이아웃 설정
            fig.update_layout(
                title=f'{equipment_type} {sensor_type} 데이터 추세',
                xaxis_title='시간',
                yaxis_title=sensor_type,
                height=400,
                # template='plotly_white',
                hovermode='x unified'
            )
            
            # 그리드 및 스타일 설정
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200, 200, 200, 0.3)')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200, 200, 200, 0.3)')
            
            # 공통 스타일 적용
            apply_insights_plotly_style(fig)
            
            # 그래프를 이미지로 변환
            img_bytes = fig.to_image(format="png", scale=2)
            img_str = base64.b64encode(img_bytes).decode('utf-8')
            
            section['image'] = img_str
            
        except Exception as e:
            print(f"시각화 생성 중 오류 발생: {e}")
    
    section['content'] = summary
    return section 