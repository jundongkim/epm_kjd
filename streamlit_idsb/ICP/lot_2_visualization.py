import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt # Matplotlib 제거
# import matplotlib.font_manager as fm # Matplotlib 제거
# import matplotlib.dates as mdates # Matplotlib 제거
import plotly.figure_factory as ff # Plotly 간트 차트용
import plotly.graph_objects as go # Plotly 커스텀용
from datetime import datetime, timedelta
import os
import json

# 그래프 설정 파일 로드
# try:
#     with open('ICP/config/graph_settings.json', 'r', encoding='utf-8') as f:
#         graph_settings = json.load(f)
#     print("그래프 설정 파일을 성공적으로 로드했습니다.")
# except (FileNotFoundError, json.JSONDecodeError) as e:
#     print(f"그래프 설정 파일을 로드할 수 없습니다: {e}")
# 기본 설정값 사용
graph_settings = {
    "icp_trend_height": 800,
    "total_time_height": 800,
    "correlation_heatmap_height": 700,
    "duration_comparison_height": 600,
    "gantt_chart_height": 800,
    "pca_scatter_height": 700,
    "boxplot_height": 600,
    "individual_icp_scatter_height": 800,
    "default_width": 1200,
    "font_family": "Arial, Malgun Gothic, sans-serif",
    "plot_bgcolor": "white",
    "grid_color": "lightgray"
}
# print("기본 그래프 설정값을 사용합니다.")

# 데이터 파일 경로
data_files = {
    1: 'lot_normalized_data_1.csv',
    2: 'lot_normalized_data_2.csv',
    3: 'lot_normalized_data_3.csv'
}

# 컬러 매핑 - 모든 공정 단계에 대한 일관된 색상 (Plotly는 약간 다른 형식 선호)
process_colors_plotly = {
    'mixer': 'rgb(168, 216, 234)',      # 연한 파란색 (A8D8EA)
    'hopper': 'rgb(170, 150, 218)',     # 보라색 (AA96DA)
    'auger_a': 'rgb(252, 186, 211)',      # 분홍색 (FCBAD3)
    'auger_b': 'rgb(255, 255, 210)',  # 연한 노란색 (FFFFD2)
    'rhk': 'rgb(161, 229, 171)', # 연한 녹색 (A1E5AB)
    'rotary_cooler': 'rgb(255, 218, 193)',        # 연한 주황색 (FFDAC1)
    'washing': 'rgb(168, 216, 234)',    # 연한 파란색 (A8D8EA)
    'filter_press': 'rgb(170, 150, 218)',# 보라색 (AA96DA)
    'dry': 'rgb(252, 186, 211)',        # 분홍색 (FCBAD3)
    'cooler': 'rgb(255, 255, 210)',     # 연한 노란색 (FFFFD2)
    'shifter': 'rgb(161, 229, 171)',    # 연한 녹색 (A1E5AB)
    'ems': 'rgb(255, 218, 193)',        # 연한 주황색 (FFDAC1)
    'packing': 'rgb(181, 234, 215)'     # 민트색 (B5EAD7)
}

# 데이터 로드 함수
def load_data(process_num):
    df = pd.read_csv(data_files[process_num])
    
    # 날짜/시간 열을 datetime 형식으로 변환
    for col in df.columns:
        if '_start' in col or '_end' in col:
            df[col] = pd.to_datetime(df[col])
    print(df)
    return df

# 1. 간트 차트 시각화 (Plotly로 변경)
def create_gantt_chart(process_num, df):
    """
    Plotly를 사용하여 공정 간트 차트 시각화 및 HTML 저장

    Args:
        process_num (int): 공정 번호 (1, 2, 3)
        df (DataFrame): 공정 데이터
    """
    if process_num in [1,2]:    
        stages = ['mixer', 'hopper', 'auger_a', 'auger_b', 'rhk', 'rotary_cooler']
    else:  # process_num == 3
        stages = ['washing', 'filter_press', 'dry', 'cooler', 'shifter', 'ems', 'packing']

    # 데이터 필터링: 처음 30일 이내에 시작된 Lot만 포함 (성능 개선 목적)
    if not df.empty:
        first_stage_start_col = f'{stages[0]}_start'
        if first_stage_start_col in df.columns:
            min_overall_start_time = df[first_stage_start_col].min()
            if pd.notna(min_overall_start_time):
                filter_end_date = min_overall_start_time + timedelta(days=30)
                original_lot_count = len(df)
                df_filtered = df[df[first_stage_start_col] <= filter_end_date].copy()
                filtered_lot_count = len(df_filtered)
                print(f"간트 차트 데이터 필터링: {original_lot_count}개 Lot 중 처음 30일 내 시작 Lot {filtered_lot_count}개만 포함.")
                if df_filtered.empty:
                    print("경고: 필터링 후 간트 차트에 표시할 데이터가 없습니다.")
                    return # 데이터 없으면 함수 종료
                df = df_filtered # 필터링된 데이터 사용
            else:
                print("경고: 데이터의 시작 시간을 결정할 수 없어 필터링을 건너뛰었습니다.")
        else:
            print(f"경고: 첫 단계 시작 컬럼('{first_stage_start_col}')을 찾을 수 없어 필터링을 건너뛰었습니다.")
    else:
        print("경고: 입력 데이터프레임이 비어있습니다.")
        return

    # Plotly 간트 차트에 맞는 데이터 형식 생성
    gantt_data = []
    for i, row in df.iterrows(): # 필터링된 df 사용
        lot_id = row['lot_id']
        for stage in stages:
            start_col = f'{stage}_start'
            end_col = f'{stage}_end'
            gantt_data.append(dict(
                Task=str(lot_id), # Y축 레이블 (Lot ID)
                Start=row[start_col],
                Finish=row[end_col],
                Resource=stage # 색상 구분을 위한 리소스 (설비 이름)
            ))

    # Lot ID 순서 정렬 (날짜 기준 내림차순)
    #ot_ids_sorted = sorted(df['lot_id'].astype(str).unique(), reverse=True)
    lot_ids_sorted = df['lot_id'].astype(str).unique()
    # 카테고리 순서 지정 (Y축 순서)
    fig = ff.create_gantt(gantt_data,
                          colors=process_colors_plotly, # 위에서 정의한 색상 매핑 사용
                          index_col='Resource', # 색상 기준
                          show_colorbar=False, # 기본 컬러바 숨김
                          group_tasks=True, # 동일 Task (Lot ID)를 그룹화하여 y축에 표시
                          showgrid_x=True, showgrid_y=True,
                          title=f'{process_num}차 공정 설비 운영 시간')

    # Y축 순서 설정
    fig.update_yaxes(categoryorder='array', categoryarray=lot_ids_sorted)

    # 레이아웃 업데이트 (폰트, 크기 등)
    fig.update_layout(
        title_font_size=16,
        font=dict(family=graph_settings["font_family"]), # 설정 파일의 폰트 사용
        xaxis_title="시간",
        yaxis_title="Lot ID",
        plot_bgcolor=graph_settings["plot_bgcolor"], # 설정 파일의 배경색 사용
        width=graph_settings["default_width"], # 설정 파일의 너비 사용
        height=max(graph_settings["gantt_chart_height"], len(lot_ids_sorted) * 30), # 높이 동적 조정 (기본값 사용)
        margin=dict(l=100, r=50, t=50, b=100) # 여백 조정
    )

    # 초기 X축 범위 설정 (예: 첫 Lot 시작일부터 30일)
    if not df.empty:
        # 모든 시작 시간 컬럼에서 가장 이른 시간 찾기
        start_cols = [f'{s}_start' for s in stages if f'{s}_start' in df.columns]
        if start_cols:
            min_start_time = df[start_cols].min().min()
            if pd.notna(min_start_time):
                initial_end_time = min_start_time + timedelta(days=7)
                fig.update_xaxes(range=[min_start_time, initial_end_time])
            else:
                 print("경고: 간트 차트의 시작 시간을 결정할 수 없어 초기 범위를 설정하지 못했습니다.")
        else:
            print("경고: 간트 차트의 시작 시간 컬럼을 찾을 수 없어 초기 범위를 설정하지 못했습니다.")

    # X축 눈금 형식 및 간격 조정 (옵션)
    # fig.update_xaxes(tickformat="%m-%d\n%H:%M") # 필요시 형식 변경

    # 범례 추가 (직접 생성)
    legend_traces = []
    for stage in stages:
        legend_traces.append(go.Bar(x=[None], y=[None], 
                                    marker_color=process_colors_plotly[stage], 
                                    name=stage))
    
    fig.add_traces(legend_traces)
    fig.update_layout(legend=dict(orientation="h",
                              yanchor="bottom",
                              y=-0.2, # 범례 위치 조정
                              xanchor="center",
                              x=0.5))

    # HTML 파일로 저장
    output_dir = "lot_visualization" # 상대 경로로 수정
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'process{process_num}_gantt.html')
    fig.write_html(output_path)
    print(f"간트 차트 저장 완료: {output_path}")

    # 작은 버전 저장 (옵션)
    # fig.update_layout(height=max(400, len(lot_ids_sorted) * 20)) # 더 작은 높이
    # output_path_small = os.path.join(output_dir, f'process{process_num}_gantt_small.html')
    # fig.write_html(output_path_small)
    # print(f"작은 간트 차트 저장 완료: {output_path_small}")

# 2. ICP 값 시각화 함수 (Plotly로 수정)
def create_icp_visualization(process_num, df):
    """
    공정별 Target ICP 값 시각화 (Plotly 사용)
    
    Args:
        process_num (int): 공정 번호 (1, 2, 3)
        df (DataFrame): 공정 데이터
    """
    icp_col = f'target_icp{process_num}'
    if icp_col not in df.columns:
        print(f"경고: {icp_col} 열이 데이터프레임에 없습니다.")
        return

    # 날짜별 평균 ICP 계산
    df['date'] = pd.to_datetime(df['date']).dt.date # 날짜만 추출
    daily_avg_icp = df.groupby('date')[icp_col].mean().reset_index()
    daily_avg_icp = daily_avg_icp.sort_values('date') # 날짜 순 정렬

    # 7일 이동 평균 계산
    daily_avg_icp['7d_moving_avg'] = daily_avg_icp[icp_col].rolling(window=7, min_periods=1).mean()

    # --- 통계량 계산 ---
    icp_stats = {
        "전체_평균_ICP": round(df[icp_col].mean(), 4) if icp_col in df.columns and not df[icp_col].dropna().empty else None,
        "전체_중앙값_ICP": round(df[icp_col].median(), 4) if icp_col in df.columns and not df[icp_col].dropna().empty else None,
        "전체_표준편차_ICP": round(df[icp_col].std(), 4) if icp_col in df.columns and not df[icp_col].dropna().empty else None,
        "전체_최소_ICP": round(df[icp_col].min(), 4) if icp_col in df.columns and not df[icp_col].dropna().empty else None,
        "전체_최대_ICP": round(df[icp_col].max(), 4) if icp_col in df.columns and not df[icp_col].dropna().empty else None,
        "표시된_일수": len(daily_avg_icp),
        "최근_7일_이동평균": round(daily_avg_icp['7d_moving_avg'].iloc[-1], 4) if not daily_avg_icp.empty and '7d_moving_avg' in daily_avg_icp.columns else None
    }

    # Plotly 라인 차트 생성
    fig = go.Figure()
    
    # 라인 추가 (일별 평균)
    fig.add_trace(go.Scatter(
        x=daily_avg_icp['date'], 
        y=daily_avg_icp[icp_col], 
        mode='lines+markers',
        name='평균 Target ICP', # 범례 이름
        line=dict(color='#164193', width=2), # 에코프로 다크 블루
        marker=dict(color='#26A9E0', size=8)  # 에코프로 라이트 블루
    ))

    # 라인 추가 (7일 이동 평균)
    fig.add_trace(go.Scatter(
        x=daily_avg_icp['date'], 
        y=daily_avg_icp['7d_moving_avg'], 
        mode='lines',
        name='7일 이동 평균', # 범례 이름
        line=dict(color='#FF0000', width=2.5, dash='dash') # 빨간색, 약간 굵은 점선
    ))

    # 레이아웃 설정
    fig.update_layout(
        title=dict(text=f'{process_num}차 공정 일별 평균 Target ICP 변화', font_size=16),
        xaxis_title="날짜",
        yaxis_title="평균 Target ICP",
        xaxis=dict(tickformat='%m-%d', showgrid=True, gridcolor=graph_settings["grid_color"]), # 설정 파일의 그리드 색상 사용
        yaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        plot_bgcolor=graph_settings["plot_bgcolor"], # 설정 파일의 배경색 사용
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        font=dict(family=graph_settings["font_family"]), # 설정 파일의 폰트 사용
        height=graph_settings["icp_trend_height"]  # 설정 파일의 높이 사용
    )

    # HTML 파일로 저장
    output_dir = "lot_visualization" # 경로 수정 (루트의 lot_visualization 사용)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'process{process_num}_icp_trend.html')
    fig.write_html(output_path)
    print(f"ICP 트렌드 차트 저장 완료: {output_path}")

    # --- 통계량 JSON 파일 저장 ---
    stats_output_path = output_path.replace('.html', '_stats.json')
    try:
        with open(stats_output_path, 'w', encoding='utf-8') as f_stats:
            json.dump(icp_stats, f_stats, ensure_ascii=False, indent=4)
        print(f"ICP 트렌드 통계 저장 완료: {stats_output_path}")
    except Exception as e:
        print(f"오류: ICP 트렌드 통계 저장 실패 - {e}")

# 3. 설비별 소요 시간 비교 (Plotly로 수정)
def create_duration_comparison(process_num, df):
    """
    공정별 설비 소요 시간 비교 바 차트 (Plotly 사용)
    
    Args:
        process_num (int): 공정 번호 (1, 2, 3)
        df (DataFrame): 공정 데이터
    """
    if process_num == 1:    
        stages = ['mixer', 'hopper', 'auger_a', 'auger_b', 'rhk', 'rotary_cooler']
    elif process_num == 2:
        stages = ['mixer', 'hopper', 'auger_a', 'auger_b', 'rhk', 'rotary_cooler']
    else: # process_num == 3
        stages = ['washing', 'filter_press', 'dry', 'cooler', 'shifter', 'ems', 'packing']

    durations = []
    for stage in stages:
        start_col = f'{stage}_start'
        end_col = f'{stage}_end'
        # 평균 소요 시간 계산 (분 단위)
        avg_duration = (df[end_col] - df[start_col]).mean().total_seconds() / 60
        durations.append(avg_duration)

    # Plotly 바 차트 생성
    fig = go.Figure(data=[go.Bar(
        x=stages,
        y=durations,
        marker_color=[process_colors_plotly[stage] for stage in stages], # 스테이지별 색상 적용
        text=[f'{d:.1f}분' for d in durations], # 막대 위에 값 표시
        textposition='outside' # 값을 막대 바깥쪽에 표시
    )])

    # 레이아웃 설정
    fig.update_layout(
        title=dict(text=f'{process_num}차 공정 설비별 평균 소요 시간', font_size=16),
        xaxis_title="설비 단계",
        yaxis_title="평균 소요 시간 (분)",
        plot_bgcolor=graph_settings["plot_bgcolor"],
        yaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        font=dict(family=graph_settings["font_family"]), # 설정 파일의 폰트 사용
        height=graph_settings["duration_comparison_height"] # 설정 파일의 높이 사용
    )

    # HTML 파일로 저장
    output_dir = "lot_visualization" # 상대 경로로 수정
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'process{process_num}_duration_comparison.html')
    fig.write_html(output_path)
    print(f"소요 시간 비교 차트 저장 완료: {output_path}")

# 4. Lot별 총 공정 시간 (Plotly로 수정)
def create_total_process_time(process_num, df):
    """
    Lot별 총 공정 시간 비교 바 차트 (Plotly 사용)
    
    Args:
        process_num (int): 공정 번호 (1, 2, 3)
        df (DataFrame): 공정 데이터
    """
    if process_num in [1, 2]:
        start_stage = 'mixer'
        end_stage = 'rotary_cooler'
    else: # process_num == 3
        start_stage = 'washing'
        end_stage = 'packing'
        
    start_col = f'{start_stage}_start'
    end_col = f'{end_stage}_end'
    
    # total_time 계산 전 컬럼 존재 확인 및 타입 확인
    if start_col in df.columns and end_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[start_col]) and pd.api.types.is_datetime64_any_dtype(df[end_col]):
        df['total_time'] = (df[end_col] - df[start_col]).dt.total_seconds() / 3600
    else:
        print(f"경고: {process_num}차 공정 데이터에 {start_col} 또는 {end_col} 컬럼이 없거나 datetime 타입이 아니어서 total_time 계산 및 분석을 건너뛰었습니다.")
        return
    
    # Lot ID별 총 공정 시간 데이터 준비
    lot_times = df[['lot_id', 'total_time']].sort_values('lot_id')
    
    # 이상치 탐지 (IQR 기반) - df['total_time'] NaN 값 고려
    valid_times = lot_times['total_time'].dropna()
    if valid_times.empty:
        print(f"경고: {process_num}차 공정의 'total_time'에 유효한 데이터가 없어 이상치 및 통계 계산을 건너뛰었습니다.")
        Q1, Q3, IQR, lower_bound, upper_bound = np.nan, np.nan, np.nan, np.nan, np.nan
        lot_times['is_outlier'] = False # 모든 값을 정상으로 처리
        outlier_count = 0
    else:
        Q1 = valid_times.quantile(0.25)
        Q3 = valid_times.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        # 이상치 여부 표시 - lot_times df에 적용, NaN은 False(정상) 처리
        lot_times['is_outlier'] = lot_times['total_time'].apply(lambda x: False if pd.isna(x) else (x < lower_bound or x > upper_bound))
        outlier_count = lot_times['is_outlier'].sum()

    # --- 통계량 계산 ---
    total_time_stats = {
        "평균_총_소요시간_시간": round(valid_times.mean(), 2) if not valid_times.empty else None,
        "중앙값_총_소요시간_시간": round(valid_times.median(), 2) if not valid_times.empty else None,
        "표준편차_총_소요시간_시간": round(valid_times.std(), 2) if not valid_times.empty else None,
        "최소_총_소요시간_시간": round(valid_times.min(), 2) if not valid_times.empty else None,
        "최대_총_소요시간_시간": round(valid_times.max(), 2) if not valid_times.empty else None,
        "Lot_개수": len(lot_times),
        "이상치_개수": int(outlier_count),
        "이상치_비율": round(outlier_count / len(lot_times) * 100, 1) if len(lot_times) > 0 else 0,
        "IQR_하한_경계": round(lower_bound, 2) if not pd.isna(lower_bound) else None,
        "IQR_상한_경계": round(upper_bound, 2) if not pd.isna(upper_bound) else None
    }
    
    # 색상 정의 (is_outlier 컬럼 사용)
    colors = lot_times['is_outlier'].apply(lambda x: '#FF6B6B' if x else '#4ECDC4')

    # Plotly 바 차트 생성
    fig = go.Figure(data=[go.Bar(
        x=lot_times['lot_id'].astype(str),
        y=lot_times['total_time'],
        marker_color=colors.tolist(),
        text=[f'{t:.1f}시간' if pd.notna(t) else 'N/A' for t in lot_times['total_time']], # NaN 처리
        textposition='outside'
    )])
    
    # 레이아웃 설정
    fig.update_layout(
        title=dict(text=f'{process_num}차 공정 Lot별 총 소요 시간', font_size=16),
        xaxis_title="Lot ID",
        yaxis_title="총 소요 시간 (시간)",
        plot_bgcolor=graph_settings["plot_bgcolor"],
        yaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        font=dict(family=graph_settings["font_family"]), # 설정 파일의 폰트 사용
        height=graph_settings["total_time_height"]  # 설정 파일의 높이 사용
    )
    
    # HTML 파일로 저장
    output_dir = "lot_visualization" # 경로 수정 (루트의 lot_visualization 사용)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'process{process_num}_total_time.html')
    fig.write_html(output_path)
    print(f"총 공정 시간 차트 저장 완료: {output_path}")

    # --- 통계량 JSON 파일 저장 ---
    stats_output_path = output_path.replace('.html', '_stats.json')
    try:
        with open(stats_output_path, 'w', encoding='utf-8') as f_stats:
            json.dump(total_time_stats, f_stats, ensure_ascii=False, indent=4)
        print(f"총 공정 시간 통계 저장 완료: {stats_output_path}")
    except Exception as e:
        print(f"오류: 총 공정 시간 통계 저장 실패 - {e}")

# --- 새로운 함수 추가: 통합 ICP 트렌드 비교 ---
def create_combined_icp_trend(df_list):
    """
    모든 공정의 일별 평균 ICP 트렌드를 하나의 그래프에서 비교 시각화합니다.

    Args:
        df_list (list): 각 공정 데이터프레임 리스트 [df1, df2, df3]
    """
    output_dir = "lot_visualization" # 루트의 lot_visualization 사용
    os.makedirs(output_dir, exist_ok=True)

    fig = go.Figure()
    combined_stats = {}
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # Plotly 기본 색상 사용 (파랑, 주황, 초록)

    all_daily_data = [] # 나중에 전체 기간 계산용

    print("--- 통합 ICP 트렌드 생성 시작 ---")
    df_index = 0 # df_list 인덱스
    for i in range(1, 4): # 공정 번호 기준 루프 (1, 2, 3)
        # df_list에서 해당 공정 번호의 df 찾기 (로드 실패 고려)
        df = None
        if df_index < len(df_list):
            # 아주 간단한 체크: 컬럼 이름으로 몇 차 공정인지 추측
            # (더 확실한 방법은 main에서 dict 형태로 전달하는 것)
            if f'target_icp{i}' in df_list[df_index].columns:
                 df = df_list[df_index]
                 df_index += 1 # 다음 df로 이동 준비
            # 만약 순서가 맞지 않거나 중간에 누락된 df가 있다면 해당 공정은 건너뛰니다.

        process_num = i # 현재 처리 중인 공정 번호
        icp_col = f'target_icp{process_num}'

        if df is None or icp_col not in df.columns or 'date' not in df.columns:
            print(f"경고: {process_num}차 공정 데이터가 없거나 필요한 컬럼({icp_col}, date)이 없어 통합 트렌드에서 제외됩니다.")
            continue

        # 날짜 형식 변환 확인
        try:
            df['date'] = pd.to_datetime(df['date']).dt.date
        except Exception as e:
             print(f"경고: {process_num}차 공정 날짜 변환 오류로 통합 트렌드에서 제외됩니다: {e}")
             continue

        # 일별 평균 계산
        daily_avg = df.groupby('date')[icp_col].mean().reset_index()
        daily_avg = daily_avg.sort_values('date')
        all_daily_data.append(daily_avg[['date', icp_col]].rename(columns={icp_col: f'icp_{process_num}'}))

        # 통계 계산
        valid_icp = df[icp_col].dropna()
        if not valid_icp.empty:
             process_stats = {
                 f"평균_ICP": round(valid_icp.mean(), 4),
                 f"중앙값_ICP": round(valid_icp.median(), 4),
                 f"표준편차_ICP": round(valid_icp.std(), 4)
             }
             combined_stats[f"{process_num}차_공정"] = process_stats
        else:
             combined_stats[f"{process_num}차_공정"] = {"평균_ICP": None, "중앙값_ICP": None, "표준편차_ICP": None}


        # 그래프에 트레이스 추가 (이동 평균선 제외)
        fig.add_trace(go.Scatter(
            x=daily_avg['date'],
            y=daily_avg[icp_col],
            mode='lines',
            name=f'{process_num}차 공정 ICP',
            line=dict(color=colors[i-1], width=2), # 인덱스 조정
            legendgroup=f"group{process_num}" # 범례 그룹화
        ))
        print(f"{process_num}차 공정 트렌드 추가 완료.")


    if not fig.data: # 추가된 트레이스가 없으면
         print("통합 ICP 트렌드 그래프를 생성할 데이터가 없습니다.")
         return

    # 전체 기간 계산 (모든 데이터 기준)
    if all_daily_data:
         # outer 조인으로 모든 날짜 포함
         merged_daily = pd.DataFrame(columns=['date']) # 빈 데이터프레임 시작
         for df_daily in all_daily_data:
              merged_daily = pd.merge(merged_daily, df_daily, on='date', how='outer')
         # 날짜 컬럼 변환 및 정렬
         merged_daily['date'] = pd.to_datetime(merged_daily['date'])
         merged_daily = merged_daily.sort_values('date')
         min_date = merged_daily['date'].min()
         max_date = merged_daily['date'].max()
         combined_stats["분석_기간_시작"] = min_date.strftime('%Y-%m-%d') if pd.notna(min_date) else None
         combined_stats["분석_기간_종료"] = max_date.strftime('%Y-%m-%d') if pd.notna(max_date) else None


    # 레이아웃 설정
    fig.update_layout(
        title=dict(text='공정별 일별 평균 Target ICP 트렌드 비교', font_size=16),
        xaxis_title="날짜",
        yaxis_title="평균 Target ICP",
        xaxis=dict(tickformat='%Y-%m-%d', showgrid=True, gridcolor=graph_settings["grid_color"]),
        yaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        plot_bgcolor=graph_settings["plot_bgcolor"],
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, title="범례"),
        font=dict(family=graph_settings["font_family"]),
        height=graph_settings.get("icp_trend_height", 800) # 개별 트렌드와 유사한 높이
    )

    # HTML 파일 저장
    output_path = os.path.join(output_dir, 'all_processes_icp_trend.html')
    fig.write_html(output_path)
    print(f"통합 ICP 트렌드 비교 차트 저장 완료: {output_path}")

    # 통계량 JSON 파일 저장
    stats_output_path = output_path.replace('.html', '_stats.json')
    try:
        with open(stats_output_path, 'w', encoding='utf-8') as f_stats:
            json.dump(combined_stats, f_stats, ensure_ascii=False, indent=4)
        print(f"통합 ICP 트렌드 통계 저장 완료: {stats_output_path}")
    except Exception as e:
        print(f"오류: 통합 ICP 트렌드 통계 저장 실패 - {e}")

# 메인 실행 함수 (각 시각화 함수 호출)
def main():
    """각 공정별 데이터를 로드하고 모든 시각화를 생성합니다."""
    # 모든 데이터 미리 로드
    all_dfs = {}
    print("\n--- 모든 공정 데이터 로딩 시작 ---")
    for i in range(1, 4):
        try:
            df = load_data(i)
            all_dfs[i] = df
            print(f"{i}차 공정 데이터 로딩 완료.")
        except FileNotFoundError:
            print(f"경고: {i}차 공정 데이터 파일({data_files[i]})을 찾을 수 없습니다.")
            all_dfs[i] = None
        except Exception as e:
            print(f"오류: {i}차 공정 데이터 로딩 중 예외 발생 - {str(e)}")
            all_dfs[i] = None
    print("--- 모든 공정 데이터 로딩 완료 ---\n")

    # 개별 공정 시각화 생성
    for i in range(1, 4):
        df_process = all_dfs.get(i)
        if df_process is None:
            print(f"\n--- {i}차 공정 시각화 건너뛰었습니다. (데이터 로드 실패) ---")
            continue

        print(f"\n--- {i}차 공정 시각화 생성 시작 ---")
        try:
            # create_gantt_chart(i, df_process.copy()) # 간트는 필터링하므로 원본 유지 위해 복사본 전달 (선택적)
            create_gantt_chart(i, df_process) # 간트 필터링은 함수 내부에서 처리
            create_icp_visualization(i, df_process)
            create_duration_comparison(i, df_process)
            create_total_process_time(i, df_process)
            print(f"--- {i}차 공정 시각화 생성 완료 ---")
        except KeyError as e:
             print(f"경고: {i}차 공정 데이터에 필요한 컬럼({e})이 없습니다. 일부 시각화를 건너뛰었습니다.")
        except Exception as e:
            print(f"오류: {i}차 공정 시각화 중 예외 발생 - {str(e)}")

    # 통합 ICP 트렌드 시각화 생성
    # 로드 성공한 데이터프레임만 리스트로 만듬
    loaded_dfs = [df for df in all_dfs.values() if df is not None]
    if loaded_dfs: # 로드된 데이터가 하나라도 있으면 시도
        try:
            create_combined_icp_trend(loaded_dfs) # 로드된 데이터 리스트 전달
        except Exception as e:
            print(f"오류: 통합 ICP 트렌드 생성 중 예외 발생 - {str(e)}")
    else:
        print("경고: 로드된 공정 데이터가 없어 통합 ICP 트렌드를 생성할 수 없습니다.")

if __name__ == "__main__":
    main() 