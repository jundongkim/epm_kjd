import pandas as pd
import numpy as np
import io
import base64
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from ..insights_plotly_style import apply_insights_plotly_style


def generate_patterns_section(df, equipment_type, sensor_type, analysis_depth, include_visuals):
    """패턴 분석 섹션을 생성하는 함수"""
    section = {
        'title': '패턴 분석',
        'content': '',
        'image': None,
        'table': None
    }
    
    # 데이터 복사본 생성 및 시간 특성 추출
    df_copy = df.copy()
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek  # 0=월요일, 6=일요일
    df_copy['day_name'] = df_copy['timestamp'].dt.day_name()
    df_copy['month'] = df_copy['timestamp'].dt.month
    df_copy['day'] = df_copy['timestamp'].dt.day
    df_copy['week'] = df_copy['timestamp'].dt.isocalendar().week
    
    # 시간별 패턴
    hourly_pattern = df_copy.groupby('hour')[sensor_type].agg(['mean', 'std', 'min', 'max']).reset_index()
    hourly_pattern.columns = ['시간', '평균', '표준편차', '최소값', '최대값']
    
    # 최대/최소 시간대 찾기
    max_hour = hourly_pattern.loc[hourly_pattern['평균'].idxmax()]['시간']
    min_hour = hourly_pattern.loc[hourly_pattern['평균'].idxmin()]['시간']
    
    # 일별 패턴
    daily_pattern = df_copy.groupby('day_of_week')[sensor_type].agg(['mean', 'std', 'min', 'max']).reset_index()
    day_names = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    daily_pattern['요일'] = daily_pattern['day_of_week'].apply(lambda x: day_names[x])
    daily_pattern = daily_pattern[['요일', 'mean', 'std', 'min', 'max']]
    daily_pattern.columns = ['요일', '평균', '표준편차', '최소값', '최대값']
    
    # 최대/최소 요일 찾기
    max_day_idx = daily_pattern['평균'].idxmax()
    min_day_idx = daily_pattern['평균'].idxmin()
    max_day = daily_pattern.loc[max_day_idx]['요일']
    min_day = daily_pattern.loc[min_day_idx]['요일']
    
    # 패턴 분석 내용 생성
    patterns_content = f"""
{equipment_type}의 {sensor_type} 데이터에 대한 패턴 분석 결과입니다.

### 시간별 패턴
- **최대값 시간대**: {int(max_hour)}시 (평균: {hourly_pattern.loc[hourly_pattern['시간'] == max_hour, '평균'].values[0]:.4f})
- **최소값 시간대**: {int(min_hour)}시 (평균: {hourly_pattern.loc[hourly_pattern['시간'] == min_hour, '평균'].values[0]:.4f})
- **일중 변동폭**: {(hourly_pattern['평균'].max() - hourly_pattern['평균'].min()):.4f} ({(hourly_pattern['평균'].max() - hourly_pattern['평균'].min()) / hourly_pattern['평균'].mean() * 100:.1f}%)

### 요일별 패턴
- **최대값 요일**: {max_day} (평균: {daily_pattern.loc[max_day_idx, '평균']:.4f})
- **최소값 요일**: {min_day} (평균: {daily_pattern.loc[min_day_idx, '평균']:.4f})
- **주간 변동폭**: {(daily_pattern['평균'].max() - daily_pattern['평균'].min()):.4f} ({(daily_pattern['평균'].max() - daily_pattern['평균'].min()) / daily_pattern['평균'].mean() * 100:.1f}%)
"""
    
    # 테이블 데이터 생성
    section['table'] = hourly_pattern
    
    # 분석 깊이에 따른 추가 정보
    if analysis_depth >= 3:
        # 시간대별 변동성 분석
        hourly_cv = hourly_pattern['표준편차'] / hourly_pattern['평균'] * 100
        most_stable_hour = hourly_pattern.loc[hourly_cv.idxmin()]['시간']
        most_variable_hour = hourly_pattern.loc[hourly_cv.idxmax()]['시간']
        
        patterns_content += f"""
### 시간대별 변동성
- **가장 안정적인 시간대**: {int(most_stable_hour)}시 (변동계수: {hourly_cv.min():.2f}%)
- **가장 변동이 큰 시간대**: {int(most_variable_hour)}시 (변동계수: {hourly_cv.max():.2f}%)
"""
    
    if analysis_depth >= 4 and len(df) > 72:  # 최소 3일 이상의 데이터
        # 주기성 분석 (자기상관)
        try:
            from statsmodels.tsa.stattools import acf
            
            # 시계열 데이터 준비
            ts_data = df.set_index('timestamp')[sensor_type].resample('1H').mean().dropna()
            
            if len(ts_data) >= 48:  # 최소 48시간 데이터 필요
                # 자기상관 계산 (최대 48시간 지연)
                lag_max = min(48, len(ts_data) - 1)
                acf_values = acf(ts_data, nlags=lag_max)
                
                # 첫 번째 값은 항상 1이므로 제외
                acf_values = acf_values[1:]
                lag_hours = np.arange(1, len(acf_values) + 1)
                
                # 가장 강한 자기상관 찾기
                strongest_lag = lag_hours[np.argmax(acf_values)]
                strongest_corr = acf_values[strongest_lag - 1]
                
                # 24시간 주기성 확인
                daily_corr = acf_values[23] if len(acf_values) > 23 else None
                
                if daily_corr is not None:
                    patterns_content += f"""
### 주기성 분석
- **가장 강한 주기**: {strongest_lag}시간 (상관계수: {strongest_corr:.4f})
- **24시간 주기성**: {'강함' if daily_corr > 0.5 else '중간' if daily_corr > 0.3 else '약함'} (상관계수: {daily_corr:.4f})
- **해석**: {equipment_type}의 {sensor_type} 데이터는 {'뚜렷한 일일 패턴을 보입니다.' if daily_corr > 0.5 else '약한 일일 패턴을 보입니다.' if daily_corr > 0.3 else '뚜렷한 일일 패턴이 관찰되지 않습니다.'}
"""
        except Exception as e:
            # 주기성 분석에 실패한 경우 무시
            pass
    
    if analysis_depth >= 5 and len(df) > 24 * 7:  # 최소 1주일 이상의 데이터
        # 시간-요일 패턴 분석 (히트맵 데이터 준비)
        try:
            # 시간과 요일별 평균값 피벗 테이블 생성
            hour_day_pattern = df_copy.pivot_table(
                index='hour', 
                columns='day_name', 
                values=sensor_type, 
                aggfunc='mean'
            )
            
            # 요일 순서 정렬
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            kor_day_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
            
            # 영어 요일명이 있는 경우
            if all(day in hour_day_pattern.columns for day in day_order):
                hour_day_pattern = hour_day_pattern[day_order]
            # 한글 요일명이 있는 경우
            elif all(day in hour_day_pattern.columns for day in kor_day_order):
                hour_day_pattern = hour_day_pattern[kor_day_order]
            
            # 최대값과 최소값 찾기
            max_hour_day = np.unravel_index(np.argmax(hour_day_pattern.values), hour_day_pattern.shape)
            min_hour_day = np.unravel_index(np.argmin(hour_day_pattern.values), hour_day_pattern.shape)
            
            max_hour_val = max_hour_day[0]
            max_day_val = hour_day_pattern.columns[max_hour_day[1]]
            min_hour_val = min_hour_day[0]
            min_day_val = hour_day_pattern.columns[min_hour_day[1]]
            
            patterns_content += f"""
### 시간-요일 복합 패턴
- **최대값 시점**: {max_day_val} {max_hour_val}시 (값: {hour_day_pattern.iloc[max_hour_day]:.4f})
- **최소값 시점**: {min_day_val} {min_hour_val}시 (값: {hour_day_pattern.iloc[min_hour_day]:.4f})
- **패턴 특징**: {equipment_type}의 {sensor_type} 값은 주로 {max_day_val}의 {max_hour_val}시에 가장 높고, {min_day_val}의 {min_hour_val}시에 가장 낮습니다.
"""
            
            # 주중/주말 패턴 비교
            weekday_mask = df_copy['day_of_week'] < 5  # 0-4: 월-금
            weekend_mask = df_copy['day_of_week'] >= 5  # 5-6: 토-일
            
            weekday_avg = df_copy[weekday_mask][sensor_type].mean()
            weekend_avg = df_copy[weekend_mask][sensor_type].mean()
            
            diff_pct = abs(weekend_avg - weekday_avg) / weekday_avg * 100 if weekday_avg != 0 else 0
            
            patterns_content += f"""
- **주중/주말 비교**: 주중 평균({weekday_avg:.4f})과 주말 평균({weekend_avg:.4f})의 차이는 {diff_pct:.1f}%로, {'주중과 주말의 패턴이 뚜렷하게 다릅니다.' if diff_pct > 10 else '주중과 주말의 패턴이 유사합니다.'}
"""
        except Exception as e:
            # 시간-요일 패턴 분석에 실패한 경우 무시
            pass
    
    # 시각화 추가
    if include_visuals:
        try:
            # Plotly 2x2 서브플롯 생성
            fig = make_subplots(rows=2, cols=2, 
                                subplot_titles=('시간별 평균 패턴', '요일별 평균 패턴', 
                                              '자기상관 함수 (ACF)' if analysis_depth >= 4 and 'acf_values' in locals() else '시간대별 분포',
                                              '시간-요일 패턴 히트맵' if analysis_depth >= 5 and 'hour_day_pattern' in locals() else '요일별 분포'),
                                vertical_spacing=0.12,
                                horizontal_spacing=0.08)
            
            # 1. 시간별 평균 패턴 (Scatter + Ribbon)
            fig.add_trace(
                go.Scatter(
                    x=hourly_pattern['시간'],
                    y=hourly_pattern['평균'],
                    mode='lines+markers',
                    name='평균',
                    line=dict(color='rgba(40, 100, 200, 0.9)', width=2),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )
            
            # 표준편차 리본 추가
            fig.add_trace(
                go.Scatter(
                    x=hourly_pattern['시간'].tolist() + hourly_pattern['시간'].tolist()[::-1],
                    y=(hourly_pattern['평균'] + hourly_pattern['표준편차']).tolist() + 
                      (hourly_pattern['평균'] - hourly_pattern['표준편차']).tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(40, 100, 200, 0.2)',
                    line=dict(color='rgba(40, 100, 200, 0)'),
                    hoverinfo='skip',
                    showlegend=False
                ),
                row=1, col=1
            )
            
            # 시간별 패턴 그래프 레이아웃 설정
            fig.update_xaxes(title_text='시간', tickmode='array', tickvals=list(range(0, 24, 2)), row=1, col=1)
            fig.update_yaxes(title_text=f'{sensor_type} 평균', row=1, col=1)
            
            # 2. 요일별 평균 패턴 (Bar + Error bars)
            day_indices = list(range(len(daily_pattern)))
            
            # 바 차트 추가
            fig.add_trace(
                go.Bar(
                    x=daily_pattern['요일'],
                    y=daily_pattern['평균'],
                    error_y=dict(
                        type='data',
                        array=daily_pattern['표준편차'],
                        visible=True,
                        color='rgba(40, 100, 200, 0.8)'
                    ),
                    marker_color='rgba(65, 165, 220, 0.7)',
                    name='요일별 평균'
                ),
                row=1, col=2
            )
            
            # 요일별 패턴 그래프 레이아웃 설정
            fig.update_xaxes(title_text='요일', row=1, col=2)
            fig.update_yaxes(title_text=f'{sensor_type} 평균', row=1, col=2)
            
            # 3. 자기상관 함수 또는 시간대별 분포
            if analysis_depth >= 4 and 'acf_values' in locals():
                # 자기상관 함수 바 차트
                fig.add_trace(
                    go.Bar(
                        x=lag_hours,
                        y=acf_values,
                        marker_color='rgba(60, 180, 100, 0.7)',
                        name='자기상관계수'
                    ),
                    row=2, col=1
                )
                
                # 95% 신뢰구간 선 추가
                conf_level = 1.96 / np.sqrt(len(ts_data))
                fig.add_trace(
                    go.Scatter(
                        x=[0, max(lag_hours)],
                        y=[0, 0],
                        mode='lines',
                        line=dict(color='rgba(255, 0, 0, 0.2)', width=1),
                        showlegend=False
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=[0, max(lag_hours)],
                        y=[conf_level, conf_level],
                        mode='lines',
                        line=dict(color='rgba(255, 0, 0, 0.5)', width=1, dash='dash'),
                        name='95% 신뢰구간'
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=[0, max(lag_hours)],
                        y=[-conf_level, -conf_level],
                        mode='lines',
                        line=dict(color='rgba(255, 0, 0, 0.5)', width=1, dash='dash'),
                        showlegend=False
                    ),
                    row=2, col=1
                )
                
                # ACF 그래프 레이아웃 설정
                fig.update_xaxes(title_text='지연 시간 (시간)', row=2, col=1)
                fig.update_yaxes(title_text='자기상관계수', row=2, col=1)
                
            else:
                # 시간대별 분포 (Box plot)
                sample_df = df_copy.sample(min(1000, len(df_copy)))
                hours = sorted(sample_df['hour'].unique())
                
                for hour in hours:
                    hour_data = sample_df[sample_df['hour'] == hour][sensor_type]
                    if len(hour_data) > 0:
                        fig.add_trace(
                            go.Box(
                                y=hour_data,
                                name=str(hour),
                                marker_color='rgba(65, 165, 220, 0.7)'
                            ),
                            row=2, col=1
                        )
                
                # 시간대별 분포 그래프 레이아웃 설정
                fig.update_xaxes(title_text='시간', row=2, col=1)
                fig.update_yaxes(title_text=sensor_type, row=2, col=1)
            
            # 4. 시간-요일 히트맵 또는 요일별 분포
            if analysis_depth >= 5 and 'hour_day_pattern' in locals():
                # 히트맵 생성
                heatmap_data = []
                for hour in hour_day_pattern.index:
                    for day_idx, day in enumerate(hour_day_pattern.columns):
                        heatmap_data.append([hour, day, hour_day_pattern.loc[hour, day]])
                
                heatmap_df = pd.DataFrame(heatmap_data, columns=['시간', '요일', 'value'])
                
                # Heatmap 추가
                fig.add_trace(
                    go.Heatmap(
                        z=hour_day_pattern.values,
                        x=hour_day_pattern.columns,
                        y=hour_day_pattern.index,
                        colorscale='Viridis',
                        colorbar=dict(title=sensor_type)
                    ),
                    row=2, col=2
                )
                
                # 히트맵 레이아웃 설정
                fig.update_xaxes(title_text='요일', row=2, col=2)
                fig.update_yaxes(title_text='시간', row=2, col=2)
                
            else:
                # 요일별 분포 (Box plot)
                sample_df = df_copy.sample(min(1000, len(df_copy)))
                
                for day in day_names:
                    day_data = sample_df[sample_df['day_name'] == day][sensor_type]
                    if len(day_data) > 0:
                        fig.add_trace(
                            go.Box(
                                y=day_data,
                                name=day,
                                marker_color='rgba(65, 165, 220, 0.7)'
                            ),
                            row=2, col=2
                        )
                
                # 요일별 분포 그래프 레이아웃 설정
                fig.update_xaxes(title_text='요일', row=2, col=2)
                fig.update_yaxes(title_text=sensor_type, row=2, col=2)
            
            # 전체 레이아웃 설정
            fig.update_layout(
                height=800,
                width=1000,
                template='plotly_white',
                showlegend=False,
                title=dict(
                    text=f'{equipment_type} {sensor_type} 패턴 분석',
                    x=0.5
                )
            )
            
            # 공통 스타일 적용
            apply_insights_plotly_style(fig)
            
            # 그래프를 이미지로 변환
            img_bytes = fig.to_image(format="png", scale=2)
            img_str = base64.b64encode(img_bytes).decode('utf-8')
            
            section['image'] = img_str
            
        except Exception as e:
            print(f"패턴 시각화 생성 중 오류 발생: {e}")
    
    section['content'] = patterns_content
    return section 