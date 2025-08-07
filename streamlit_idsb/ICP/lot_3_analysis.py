import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt # Matplotlib/Seaborn 제거
# import seaborn as sns
# import matplotlib.font_manager as fm # Matplotlib 제거
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
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

# 한글 폰트 설정 제거 (Plotly 사용)

# 데이터 로드 함수
def load_process_data(process_num):
    """
    공정 데이터 로드 및 전처리
    
    Args:
        process_num (int): 공정 번호 (1, 2, 3)
        
    Returns:
        DataFrame: 전처리된 공정 데이터
    """
    # 파일 경로
    file_path = f'lot_normalized_data_{process_num}.csv'
    
    # 데이터 로드
    df = pd.read_csv(file_path)
    
    # 날짜/시간 열 변환
    for col in df.columns:
        if '_start' in col or '_end' in col:
            df[col] = pd.to_datetime(df[col])
    
    # 날짜 열 변환
    df['date'] = pd.to_datetime(df['date'])
    
    return df

# 소요 시간 계산 함수
def calculate_durations(df, process_num):
    """
    각 공정 단계별 소요 시간 계산
    
    Args:
        df (DataFrame): 공정 데이터
        process_num (int): 공정 번호 (1, 2, 3)
        
    Returns:
        DataFrame: 각 단계별 소요 시간이 추가된 데이터프레임
    """
    # 공정 단계 목록
    if process_num in [1,2]:    
        stages = ['mixer', 'hopper', 'auger_a', 'auger_b', 'rhk', 'rotary_cooler']
    else:  # process_num == 3
        stages = ['washing', 'filter_press', 'dry', 'cooler', 'shifter', 'ems', 'packing']
    
    # 각 단계별 소요 시간 계산 (분 단위)
    for stage in stages:
        start_col = f'{stage}_start'
        end_col = f'{stage}_end'
        duration_col = f'{stage}_duration'
        
        df[duration_col] = (df[end_col] - df[start_col]).dt.total_seconds() / 60
    
    # 전체 공정 소요 시간 계산
    if process_num in [1, 2]:
        df['total_duration'] = (df['rotary_cooler_end'] - df['mixer_start']).dt.total_seconds() / 60
    else:  # process_num == 3
        df['total_duration'] = (df['packing_end'] - df['washing_start']).dt.total_seconds() / 60
    
    return df

# 1. 상관관계 분석
def analyze_correlations(df, process_num):
    """
    공정 단계 소요 시간과 ICP 값 간의 상관관계 분석 (Plotly 사용)
    
    Args:
        df (DataFrame): 소요 시간이 계산된 공정 데이터
        process_num (int): 공정 번호 (1, 2, 3)
    """
    # 분석 결과 저장 디렉토리
    output_dir = "lot_analysis" # 상대 경로로 수정
    os.makedirs(output_dir, exist_ok=True)
    
    # 소요 시간 데이터 및 ICP 값 추출
    duration_cols = [col for col in df.columns if 'duration' in col]
    icp_col = f'target_icp{process_num}'
    if icp_col not in df.columns:
        print(f"경고: {icp_col} 열이 없어 상관관계 분석을 건너<0xEB><0x9C><0x8D>니다.")
        return
        
    corr_df = df[duration_cols + [icp_col]].copy()
    correlation_matrix = corr_df.corr()
     
        
    # --- ICP와의 상관관계 바 차트 (Plotly) ---
    icp_corr = correlation_matrix[icp_col].drop(icp_col).sort_values(ascending=False)
    
    colors = ['indianred' if v > 0 else 'steelblue' for v in icp_corr.values]
    
    fig_bar = go.Figure(data=[go.Bar(
        x=icp_corr.index,
        y=icp_corr.values,
        marker_color=colors,
        text=[f'{v:.2f}' for v in icp_corr.values],
        textposition='outside'
    )])
    
    fig_bar.update_layout(
        title=f'{process_num}차 공정 ICP 값과 각 단계 소요 시간 간의 상관관계',
        xaxis_title='공정 단계',
        yaxis_title='상관 계수',
        plot_bgcolor=graph_settings["plot_bgcolor"],
        yaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        font=dict(family=graph_settings["font_family"]),
        height=graph_settings["correlation_heatmap_height"] # 설정 파일 값 사용
    )
    fig_bar.add_hline(y=0, line_width=1, line_dash="dash", line_color="black")
    
    # 저장 (HTML)
    bar_path = os.path.join(output_dir, f'process{process_num}_icp_correlation_bar.html')
    fig_bar.write_html(bar_path)
    print(f"ICP 상관관계 바 차트 저장 완료: {bar_path}")

# 2. 이상치 분석
def analyze_outliers(df, process_num):
    """
    ICP 값과 공정 소요 시간의 이상치 분석 (Plotly 사용)
    
    Args:
        df (DataFrame): 소요 시간이 계산된 공정 데이터
        process_num (int): 공정 번호 (1, 2, 3)
    """
    output_dir = "lot_analysis" # 상대 경로로 수정
    os.makedirs(output_dir, exist_ok=True)

    duration_cols = [col for col in df.columns if 'duration' in col]
    icp_col = f'target_icp{process_num}'
    if icp_col not in df.columns:
        print(f"경고: {icp_col} 열이 없어 ICP 이상치 분석을 건너<0xEB><0x9C><0x8D>니다.")
    else:
        # --- ICP 값 박스 플롯 (Plotly) ---
        fig_icp_box = go.Figure(data=[go.Box(
            x=df[icp_col],
            name=icp_col.replace('target_',''), 
            boxpoints='all' # 이상치뿐만 아니라 모든 점 표시
        )])
        fig_icp_box.update_layout(
            title=f'{process_num}차 공정 ICP 값 분포 (Box Plot)',
            xaxis_title='Target ICP 값',
            plot_bgcolor=graph_settings["plot_bgcolor"],
            xaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
            font=dict(family=graph_settings["font_family"]),
            height=graph_settings["boxplot_height"] # 설정 파일 값 사용
        )
        icp_box_path = os.path.join(output_dir, f'process{process_num}_icp_boxplot.html')
        fig_icp_box.write_html(icp_box_path)
        print(f"ICP 박스 플롯 저장 완료: {icp_box_path}")
    
    # --- 소요 시간 박스 플롯 (Plotly) ---
    fig_dur_box = go.Figure()
    for col in duration_cols:
        fig_dur_box.add_trace(go.Box(
            x=df[col],
            name=col.replace('_duration', ''),
            boxpoints='outliers'
        ))
    
    fig_dur_box.update_layout(
        title=f'{process_num}차 공정 단계별 소요 시간 분포 (Box Plot)',
        xaxis_title='소요 시간 (분)',
        yaxis_title='공정 단계',
        plot_bgcolor=graph_settings["plot_bgcolor"],
        xaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        font=dict(family=graph_settings["font_family"]),
        height=graph_settings["boxplot_height"] # 설정 파일 값 사용
    )
    dur_box_path = os.path.join(output_dir, f'process{process_num}_duration_boxplot.html')
    fig_dur_box.write_html(dur_box_path)
    print(f"소요 시간 박스 플롯 저장 완료: {dur_box_path}")

# 4. 통계적 검정
def statistical_tests(df, process_num):
    """
    ICP 값에 따른 공정 시간 차이 통계적 검정 (Plotly 사용)
    
    Args:
        df (DataFrame): 소요 시간이 계산된 공정 데이터
        process_num (int): 공정 번호 (1, 2, 3)
    """
    output_dir = "lot_analysis" # 상대 경로로 수정
    os.makedirs(output_dir, exist_ok=True)

    duration_cols = [col for col in df.columns if 'duration' in col]
    icp_col = f'target_icp{process_num}'
    if icp_col not in df.columns:
        print(f"경고: {icp_col} 열이 없어 통계 검정을 건너<0xEB><0x9C><0x8D>니다.")
        return
        
    #median_icp = df[icp_col].median()
    #high_icp_group = df[df[icp_col] >= median_icp]
    #low_icp_group = df[df[icp_col] < median_icp]
    high_icp_group = df[df['label']==2]
    low_icp_group = df[(df['label']==1)|(df['label']==0)]
    
    results = []
    for col in duration_cols:
        t_stat, p_val = stats.ttest_ind(
            high_icp_group[col].fillna(high_icp_group[col].median()), # NaN 값 중앙값으로 대체
            low_icp_group[col].fillna(low_icp_group[col].median()),
            equal_var=False
        )
        high_mean = high_icp_group[col].mean()
        low_mean = low_icp_group[col].mean()
        results.append({
            'variable': col.replace('_duration', ''),
            'high_icp_mean': high_mean,
            'low_icp_mean': low_mean,
            'difference': high_mean - low_mean,
            'p_value': p_val,
            'significant': p_val < 0.05
        })
        
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('difference', key=abs, ascending=False) # 차이 절대값 기준 정렬
    
    # 결과 CSV 저장 (기존 유지)
    results_df.to_csv(os.path.join(output_dir, f'process{process_num}_ttest_results.csv'), index=False)
    print(f"T-test 결과 CSV 저장 완료: analysis/process{process_num}_ttest_results.csv")

    # --- 그룹 비교 바 차트 (Plotly) ---
    fig_comp_bar = go.Figure()
    
    fig_comp_bar.add_trace(go.Bar(
        x=results_df['variable'], 
        y=results_df['high_icp_mean'], 
        #name=f'높은 ICP 그룹 (>= {median_icp:.4f})',
        name=f'높은 ICP 그룹 (Spec out : 2)',
        marker_color='indianred'
    ))
    fig_comp_bar.add_trace(go.Bar(
        x=results_df['variable'], 
        y=results_df['low_icp_mean'], 
        #name=f'낮은 ICP 그룹 (< {median_icp:.4f})',
        name=f'낮은 ICP 그룹 (Spec in : 0,1)',
        marker_color='steelblue'
    ))
    
    # 유의미한 차이에 별표 추가 (주석 형태로)
    annotations = []
    for i, row in results_df.iterrows():
        if row['significant']:
            annotations.append(dict(
                x=row['variable'], 
                y=max(row['high_icp_mean'], row['low_icp_mean']) * 1.05, # 막대 위에 표시
                text="*", 
                showarrow=False,
                font=dict(size=20)
            ))
            
    fig_comp_bar.update_layout(
        title=f'{process_num}차 공정 ICP 값 그룹별 소요 시간 비교 (T-test)',
        xaxis_title='공정 단계',
        yaxis_title='평균 소요 시간 (분)',
        barmode='group', # 그룹 바 차트
        plot_bgcolor=graph_settings["plot_bgcolor"],
        yaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        font=dict(family=graph_settings["font_family"]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        annotations=annotations,
        height=graph_settings["duration_comparison_height"] # 설정 파일 값 사용
    )
    
    # 저장 (HTML)
    comp_bar_path = os.path.join(output_dir, f'process{process_num}_group_comparison_bar.html')
    fig_comp_bar.write_html(comp_bar_path)
    print(f"그룹 비교 바 차트 저장 완료: {comp_bar_path}")

# --- 새로운 함수 추가 ---
def create_individual_icp_scatter(df_list):
    """
    모든 공정의 개별 Lot ICP 값을 시간에 따라 산점도로 시각화합니다.

    Args:
        df_list (list): 각 공정 데이터프레임 (전처리 및 소요시간 계산 완료된 상태) 리스트 [df1, df2, df3]
    """
    output_dir = "lot_analysis"
    os.makedirs(output_dir, exist_ok=True)

    combined_data = []
    for i, df in enumerate(df_list):
        process_num = i + 1
        icp_col = f'target_icp{process_num}'
        if process_num in [1, 2]:
            start_col = 'mixer_start'
            # stages = ['mixer', 'hopper', 'auger', 'rhk_input', 'rhk_output', 'roc'] # 함수 내에서 stage 리스트는 불필요
        else: # process_num == 3
            start_col = 'washing_start'
            # stages = ['washing', 'filter_press', 'dry', 'cooler', 'shifter', 'ems', 'packing']

        if icp_col not in df.columns or start_col not in df.columns:
            print(f"경고: {process_num}차 공정 데이터에 {icp_col} 또는 {start_col}이 없어 개별 ICP 산점도에서 제외됩니다.")
            continue

        # 필요한 컬럼 선택 및 이름 변경
        temp_df = df[['lot_id', start_col, icp_col]].copy()
        temp_df.rename(columns={start_col: 'start_time', icp_col: 'target_icp'}, inplace=True)
        temp_df['process'] = str(process_num) # Plotly 색상 구분을 위해 문자열로 변환

        combined_data.append(temp_df)

    if not combined_data:
        print("개별 ICP 산점도를 생성할 데이터가 없습니다.")
        return

    # 모든 데이터 결합
    df_combined = pd.concat(combined_data, ignore_index=True)
    df_combined['start_time'] = pd.to_datetime(df_combined['start_time']) # 혹시 모를 타입 변환
    df_combined.sort_values('start_time', inplace=True)

    # Plotly 산점도 생성
    fig = px.scatter(
        df_combined,
        x='start_time',
        y='target_icp',
        color='process', # 공정 번호별 색상 구분
        hover_data=['lot_id', 'process'],
        title='시간에 따른 개별 Lot Target ICP 분포 (공정별)',
        labels={'start_time': '공정 시작 시간', 'target_icp': 'Target ICP', 'process': '공정'}
    )

    fig.update_layout(
        plot_bgcolor=graph_settings["plot_bgcolor"],
        xaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        yaxis=dict(showgrid=True, gridcolor=graph_settings["grid_color"]),
        font=dict(family=graph_settings["font_family"]),
        height=graph_settings.get("individual_icp_scatter_height", 800), # 새 설정 키 사용
        legend_title_text='공정 번호'
    )

    # 마커 크기 조절 (옵션)
    fig.update_traces(marker=dict(size=5), selector=dict(mode='markers'))

    output_path = os.path.join(output_dir, 'all_processes_individual_icp_scatter.html')
    fig.write_html(output_path)
    print(f"개별 ICP 산점도 저장 완료: {output_path}")

# 메인 함수
def main():
    # 모든 공정 데이터 미리 로드 및 준비
    all_dfs = {}
    processed_dfs = []
    print("\n--- 모든 공정 데이터 로딩 및 준비 시작 ---")
    for process_num in [1, 2, 3]:
        try:
            df = load_process_data(process_num)
            df = calculate_durations(df, process_num)
            all_dfs[process_num] = df
            processed_dfs.append(df) # 리스트에도 추가 (순서대로)
            print(f"{process_num}차 공정 데이터 로딩 및 준비 완료.")
        except FileNotFoundError:
            print(f"경고: {process_num}차 공정 데이터 파일(lot_normalized_data_{process_num}.csv)을 찾을 수 없습니다.")
            all_dfs[process_num] = None # 로드 실패 표시
        except Exception as e:
            print(f"오류: {process_num}차 공정 데이터 로딩 중 예외 발생 - {str(e)}")
            all_dfs[process_num] = None
    print("--- 모든 공정 데이터 로딩 및 준비 완료 ---\n")

    # 개별 ICP 산점도 생성 (새 함수 호출)
    if len(processed_dfs) == 3: # 3개 데이터 모두 성공적으로 로드된 경우에만 실행
        print("--- 개별 ICP 산점도 생성 시작 ---")
        try:
             create_individual_icp_scatter(processed_dfs)
        except Exception as e:
             print(f"오류: 개별 ICP 산점도 생성 중 예외 발생 - {str(e)}")
        print("--- 개별 ICP 산점도 생성 완료 ---\n")
    else:
        print("경고: 모든 공정 데이터를 성공적으로 로드하지 못해 개별 ICP 산점도를 생성할 수 없습니다.")

    # 각 공정별 분석 수행 (로드된 데이터 사용)
    for process_num, df in all_dfs.items():
        if df is None:
            print(f"\n--- {process_num}차 공정 분석 건너<0xEB><0x9C><0x8D> (데이터 로드 실패) ---")
            continue # 데이터 로드 실패 시 건너<0xEB><0x9C><0x8D>

        print(f"\n--- {process_num}차 공정 분석 시작 ---")
        try:
            # df는 이미 로드되고 duration이 계산된 상태
            analyze_correlations(df, process_num)
            analyze_outliers(df, process_num)
            statistical_tests(df, process_num)
            print(f"--- {process_num}차 공정 분석 완료 ---")
        except KeyError as e:
            print(f"경고: {process_num}차 공정 데이터에 필요한 컬럼({e})이 없습니다. 일부 분석을 건너<0xEB><0x9C><0x8D>니다.")
        except Exception as e:
            print(f"오류: {process_num}차 공정 분석 중 예외 발생 - {str(e)}")

if __name__ == "__main__":
    main() 