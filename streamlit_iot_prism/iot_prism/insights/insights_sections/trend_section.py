import pandas as pd
import numpy as np
import io
import base64
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose
from ..insights_plotly_style import apply_insights_plotly_style


def generate_trend_section(df, equipment_type, sensor_type, analysis_depth, include_visuals):
    """추세 섹션을 생성하는 함수"""
    section = {
        'title': '추세 분석',
        'content': '',
        'image': None
    }
    
    # 데이터 기간 확인
    date_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 86400  # 일 단위
    
    # 추세 분석 - 시작과 끝 부분 평균 비교
    start_segment = df[sensor_type].iloc[:int(len(df)*0.1)] if len(df) > 10 else df[sensor_type].iloc[:1]
    end_segment = df[sensor_type].iloc[-int(len(df)*0.1):] if len(df) > 10 else df[sensor_type].iloc[-1:]
    
    start_avg = start_segment.mean()
    end_avg = end_segment.mean()
    
    # 변화율 계산
    change_rate = ((end_avg - start_avg) / start_avg) * 100 if start_avg != 0 else 0
    
    # 추세 방향
    if change_rate > 10:
        trend_direction = "강한 상승"
    elif change_rate > 3:
        trend_direction = "상승"
    elif change_rate > 1:
        trend_direction = "약한 상승"
    elif change_rate < -10:
        trend_direction = "강한 하락"
    elif change_rate < -3:
        trend_direction = "하락"
    elif change_rate < -1:
        trend_direction = "약한 하락"
    else:
        trend_direction = "안정적"
    
    # 이동평균 계산
    window_size = max(len(df) // 20, 1)
    df['moving_avg'] = df[sensor_type].rolling(window=window_size).mean()
    
    # 추세 분석 내용 생성
    trend_content = f"""
{equipment_type}의 {sensor_type} 데이터에 대한 추세 분석 결과입니다.

### 장기 추세 분석
- **관측 기간**: {date_range:.1f}일
- **초기 평균값**: {start_avg:.4f}
- **최종 평균값**: {end_avg:.4f}
- **변화율**: {change_rate:.2f}% ({'증가' if change_rate > 0 else '감소' if change_rate < 0 else '변화 없음'})
- **추세 판정**: {trend_direction}
"""
    
    # 분석 깊이에 따른 추가 정보
    if analysis_depth >= 3 and len(df) > 24:
        # 시간별 추세 변화
        df_copy = df.copy()
        df_copy['hour'] = df_copy['timestamp'].dt.hour
        
        # 기간을 전반부/후반부로 나누기
        mid_point = df_copy['timestamp'].min() + (df_copy['timestamp'].max() - df_copy['timestamp'].min()) / 2
        
        first_half = df_copy[df_copy['timestamp'] < mid_point]
        second_half = df_copy[df_copy['timestamp'] >= mid_point]
        
        if not first_half.empty and not second_half.empty:
            # 시간대별 평균 계산
            first_half_hourly = first_half.groupby('hour')[sensor_type].mean()
            second_half_hourly = second_half.groupby('hour')[sensor_type].mean()
            
            # 조인해서 비교
            hourly_comparison = pd.DataFrame({
                '전반부': first_half_hourly,
                '후반부': second_half_hourly
            }).reset_index()
            
            hourly_comparison['변화율'] = ((hourly_comparison['후반부'] - hourly_comparison['전반부']) / 
                                          hourly_comparison['전반부'] * 100)
            
            # 가장 많이 변한 시간대
            if not hourly_comparison['변화율'].isna().all():
                most_changed_hour = hourly_comparison.loc[hourly_comparison['변화율'].abs().idxmax()]
                
                trend_content += f"""
### 시간대별 추세 변화
- **가장 큰 변화가 있는 시간대**: {most_changed_hour['hour']}시
- **해당 시간 변화율**: {most_changed_hour['변화율']:.2f}% ({'증가' if most_changed_hour['변화율'] > 0 else '감소'})
- **전반부 평균**: {most_changed_hour['전반부']:.4f}
- **후반부 평균**: {most_changed_hour['후반부']:.4f}
"""

    if analysis_depth >= 4 and len(df) > 72:
        # 계절성 분해 시도
        try:
            # 타임스탬프를 인덱스로 설정
            ts_df = df.set_index('timestamp')
            # 균일한 시간 간격으로 리샘플링 (필요한 경우)
            # 데이터가 불규칙하다면 1시간 간격으로 리샘플링
            resampled = ts_df[sensor_type].resample('1H').mean().interpolate(method='linear')
            
            # 계절성 분해
            # 데이터에 적합한 주기 선택 (일반적으로 24시간, 168시간(1주) 등)
            period = 24  # 일일 주기
            
            # 충분한 데이터가 있는지 확인
            if len(resampled) >= 2 * period:
                result = seasonal_decompose(resampled, model='additive', period=period)
                
                # 추세 강도
                trend_strength = 1 - (np.var(result.resid) / np.var(resampled - result.seasonal))
                # 계절성 강도
                seasonal_strength = 1 - (np.var(result.resid) / np.var(resampled - result.trend))
                
                trend_content += f"""
### 시계열 분해 분석 (일일 주기)
- **추세 강도**: {trend_strength:.4f} ({'강함' if trend_strength > 0.6 else '중간' if trend_strength > 0.3 else '약함'})
- **계절성 강도**: {seasonal_strength:.4f} ({'강함' if seasonal_strength > 0.6 else '중간' if seasonal_strength > 0.3 else '약함'})
- **해석**: {equipment_type}의 {sensor_type} 데이터는 {'뚜렷한 추세와 ' if trend_strength > 0.6 else '약한 추세와 ' if trend_strength > 0.3 else '추세가 거의 없고 '}{'뚜렷한 일일 주기성을 보입니다.' if seasonal_strength > 0.6 else '약한 일일 주기성을 보입니다.' if seasonal_strength > 0.3 else '일일 주기성이 거의 없습니다.'}
"""
        except Exception as e:
            pass  # 계절성 분해에 실패한 경우 무시

    if analysis_depth >= 5 and len(df) > 30:
        # 변화점 감지 (갑작스러운 추세 변화)
        try:
            from ruptures import Pelt
            from ruptures.costs import CostL2
            
            # 이동평균 데이터로 변화점 감지
            signal = df['moving_avg'].dropna().values
            
            if len(signal) > 2:  # 최소 3개 이상의 데이터 포인트 필요
                # 변화점 감지 알고리즘
                algo = Pelt(model="rbf").fit(signal.reshape(-1, 1))
                result = algo.predict(pen=10)
                
                # 유의미한 변화점이 있는 경우
                if len(result) > 1:  # 첫 번째 값은 항상 신호의 길이
                    # 인덱스를 원래 데이터의 타임스탬프로 변환
                    change_points = []
                    for point in result[:-1]:  # 마지막 점은 신호의 길이
                        # 드롭한 NaN 값 때문에 인덱스 보정이 필요할 수 있음
                        if point < len(df) - window_size + 1:
                            change_points.append(point + window_size - 1)
                    
                    if change_points:
                        # 변화점이 있는 경우, 가장 중요한 변화점 3개만 선택
                        significant_points = change_points[:min(3, len(change_points))]
                        
                        trend_content += """
### 주요 추세 변화점
변화점은 데이터의 추세가 유의미하게 변경된 시점을 나타냅니다:
"""
                        
                        for i, point in enumerate(significant_points):
                            date = df.iloc[point]['timestamp'].strftime('%Y-%m-%d %H:%M')
                            value = df.iloc[point][sensor_type]
                            
                            # 변화 전후 평균값 비교
                            if point > 10 and point < len(df) - 10:
                                before_avg = df.iloc[point-10:point][sensor_type].mean()
                                after_avg = df.iloc[point:point+10][sensor_type].mean()
                                change_pct = ((after_avg - before_avg) / before_avg) * 100 if before_avg != 0 else 0
                                
                                trend_content += f"""
- **변화점 {i+1}**: {date} (값: {value:.4f})
  - 변화 전 평균: {before_avg:.4f}
  - 변화 후 평균: {after_avg:.4f}
  - 변화율: {change_pct:.2f}% ({'증가' if change_pct > 0 else '감소' if change_pct < 0 else '변화 없음'})
"""
        except Exception as e:
            pass  # 변화점 감지에 실패한 경우 무시
    
    # 시각화 추가
    if include_visuals:
        try:
            # Plotly 차트 생성
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=(
                    f'{equipment_type} {sensor_type} 추세 분석',
                    f'{sensor_type} 추세 성분 (계절성 제거)'
                ),
                shared_xaxes=False,
                vertical_spacing=0.15
            )
            
            # 원본 데이터와 이동평균 플롯
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[sensor_type],
                    mode='lines',
                    name=f'{sensor_type} 원본',
                    line=dict(color='rgba(25, 118, 210, 0.5)', width=1)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['moving_avg'],
                    mode='lines',
                    name=f'이동평균 (창크기: {window_size})',
                    line=dict(color='rgba(255, 87, 34, 0.9)', width=2)
                ),
                row=1, col=1
            )
            
            # 시작과 끝 부분 강조
            if len(df) > 2:
                start_end = df.iloc[[0, -1]]
                fig.add_trace(
                    go.Scatter(
                        x=start_end['timestamp'],
                        y=start_end[sensor_type],
                        mode='markers',
                        name='시작/종료 지점',
                        marker=dict(size=10, color='green')
                    ),
                    row=1, col=1
                )
            
            # 변화점 표시 (analysis_depth >= 5인 경우)
            if 'change_points' in locals() and change_points:
                for point in change_points[:min(3, len(change_points))]:
                    if point < len(df):
                        change_point_time = df.iloc[point]['timestamp']
                        fig.add_vline(
                            x=change_point_time, 
                            line_dash="dash", 
                            line_color="purple",
                            opacity=0.7,
                            row=1, col=1
                        )
            
            # 계절성 분해 결과 (analysis_depth >= 4인 경우)
            if analysis_depth >= 4 and 'result' in locals():
                fig.add_trace(
                    go.Scatter(
                        x=result.trend.index,
                        y=result.trend,
                        mode='lines',
                        name='추세 성분',
                        line=dict(color='rgba(76, 175, 80, 0.9)', width=2)
                    ),
                    row=2, col=1
                )
            else:
                # 계절성 분해가 실패한 경우 원본 데이터 표시
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df[sensor_type],
                        mode='lines',
                        name=f'{sensor_type} 원본',
                        line=dict(color='rgba(25, 118, 210, 0.5)', width=1)
                    ),
                    row=2, col=1
                )
                
                # 선형 추세선 추가
                x_numeric = np.arange(len(df))
                model = np.polyfit(x_numeric, df[sensor_type], 1)
                trend_values = np.poly1d(model)(x_numeric)
                
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=trend_values,
                        mode='lines',
                        name='선형 추세선',
                        line=dict(color='rgba(76, 175, 80, 0.9)', width=2, dash='dash')
                    ),
                    row=2, col=1
                )
            
            # 레이아웃 설정
            fig.update_layout(
                height=800,
                title_text=f"{equipment_type} {sensor_type} 추세 분석",
                showlegend=True
            )
            
            # 스타일 적용
            apply_insights_plotly_style(fig)
            
            # 그림을 이미지로 변환
            img_bytes = fig.to_image(format="png", engine="kaleido", width=1200, height=800)
            img_str = base64.b64encode(img_bytes).decode('utf-8')
            
            section['image'] = img_str
            
        except Exception as e:
            print(f"추세 시각화 생성 중 오류 발생: {e}")
    
    section['content'] = trend_content
    return section 