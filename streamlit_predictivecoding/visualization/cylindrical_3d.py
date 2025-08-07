import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math
from scipy.interpolate import interp1d, griddata
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
import multiprocessing as mp
from tqdm import tqdm
import logging
import warnings

# Suppress Streamlit warnings during parallel processing
logging.getLogger('streamlit').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime.caching').setLevel(logging.CRITICAL)
logging.getLogger('streamlit.runtime.state').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore', category=UserWarning, module='streamlit')
warnings.filterwarnings('ignore', message='.*No runtime found.*')
warnings.filterwarnings('ignore', message='.*Session state does not function.*')
warnings.filterwarnings('ignore', message='.*to view a Streamlit app.*')

# Color Theme Definitions
COLOR_THEMES = {
    'Viridis': {
        'name': '🌿 Viridis (Default)',
        'colorscale': 'Viridis',
        'description': 'Natural green-blue gradient for general purpose visualization'
    },
    'Steel': {
        'name': '🔩 Steel (Specialty Steel)',
        'colorscale': [[0, '#2C3E50'], [0.2, '#34495E'], [0.4, '#5D6D7E'], 
                      [0.6, '#85929E'], [0.8, '#AEB6BF'], [1, '#D5DBDB']],
        'description': 'Gray-silver gradient inspired by specialty steel materials'
    },
    'Plasma': {
        'name': '🔥 Plasma (Heat Treatment)',
        'colorscale': 'Plasma',
        'description': 'Purple-orange gradient representing heat treatment processes'
    },
    'Inferno': {
        'name': '🌋 Inferno (Furnace)',
        'colorscale': 'Inferno',
        'description': 'Black-red-yellow gradient inspired by furnace operations'
    },
    'Cividis': {
        'name': '🔬 Cividis (Analysis)',
        'colorscale': 'Cividis',
        'description': 'Colorblind-friendly gradient for scientific analysis'
    },
    'Blues': {
        'name': '💙 Blues (Cooling)',
        'colorscale': 'Blues',
        'description': 'Blue gradient representing cooling processes'
    },
    'Reds': {
        'name': '❤️ Reds (Heating)',
        'colorscale': 'Reds',
        'description': 'Red gradient representing heating processes'
    },
    'Greys': {
        'name': '⚫ Greys (Monochrome)',
        'colorscale': 'Greys',
        'description': 'Black and white monochrome gradient'
    },
    'Turbo': {
        'name': '🌈 Turbo (High Contrast)',
        'colorscale': 'Turbo',
        'description': 'High contrast rainbow gradient for detailed analysis'
    },
    'Copper': {
        'name': '🟫 Copper (Copper Alloy)',
        'colorscale': [[0, '#8B4513'], [0.3, '#CD853F'], [0.6, '#DEB887'], [1, '#F5DEB3']],
        'description': 'Brown-gold gradient inspired by copper alloy materials'
    }
}

def load_bar_data(file_path):
    """
    Load and parse BAR CSV file or TR CSV file data structure
    TR file: Has headers, no skiprows needed
    BAR file: Starts from 7th line (skiprows=6)
    """
    # 파일명으로 TR 파일 여부 판단
    is_tr_file = 'TR.CSV' in file_path.upper() or 'TR.csv' in file_path
    
    if is_tr_file:
        # TR 파일: 헤더가 있으므로 skiprows 불필요
        df = pd.read_csv(file_path)
    else:
        # 원본 BAR 파일: 헤더와 데이터 읽기 (7번째 줄부터)
        df = pd.read_csv(file_path, skiprows=6)
    
    # 10개 채널 정의
    channels = ['CH-A1', 'CH-A2', 'CH-A3', 'CH-A4', 'CH-A5', 
               'CH-B1', 'CH-B2', 'CH-B3', 'CH-B4', 'CH-B5']
    
    # TR 파일의 경우 빈 값들을 NaN으로 처리
    if is_tr_file:
        # 빈 문자열을 NaN으로 변환
        df = df.replace('', pd.NA)
        # 채널 컬럼들을 숫자형으로 변환
        for channel in channels:
            if channel in df.columns:
                df[channel] = pd.to_numeric(df[channel], errors='coerce')
        
        # Point 컬럼도 숫자형으로 변환
        if 'Point' in df.columns:
            df['Point'] = pd.to_numeric(df['Point'], errors='coerce')
    
    return df, channels

def interpolate_point_data(df, channels, point_interpolation_factor=1, full_range=False):
    """
    Point(길이) 방향 데이터를 보간하여 조밀한 간격 생성
    point_interpolation_factor: Point 보간 배수 (1=원본, 2이상=보간)
    full_range: True면 최대 해상도로 보간 (1mm 간격)
    """
    if point_interpolation_factor <= 1 and not full_range:
        return df.copy()
    
    # Point 컬럼의 유효한 값들 추출
    valid_points = df['Point'].dropna().values
    if len(valid_points) < 2:
        print("⚠️ Not enough valid points for interpolation")
        return df.copy()
    
    # 새로운 Point 값들 생성 (더 조밀한 간격)
    min_point = valid_points.min()
    max_point = valid_points.max()
    
    if full_range:
        # Full range: 1mm 간격으로 최대 해상도
        new_interval = 1.0
        actual_factor = "Full"
        print(f"🔄 Starting Point interpolation with FULL RANGE (1mm intervals)...")
    else:
        # 원본 간격의 최소값 계산
        point_diffs = np.diff(np.sort(valid_points))
        min_interval = point_diffs[point_diffs > 0].min() if len(point_diffs[point_diffs > 0]) > 0 else 1.0
        
        # 새로운 간격 계산
        new_interval = min_interval / point_interpolation_factor
        actual_factor = point_interpolation_factor
        print(f"🔄 Starting Point interpolation with factor {point_interpolation_factor}...")
    
    # 새로운 Point 배열 생성
    new_points = np.arange(min_point, max_point + new_interval, new_interval)
    
    print(f"📊 Original points: {len(valid_points)}, New points: {len(new_points)}")
    print(f"📏 Point range: {min_point:.1f} ~ {max_point:.1f}, New interval: {new_interval:.2f}")
    print(f"🔍 Interpolation factor: {actual_factor}")
    
    # 각 채널별로 보간 수행
    interpolated_data = []
    
    for new_point in new_points:
        row_data = {'Point': new_point}
        
        for channel in channels:
            # 원본 데이터에서 유효한 값들 추출
            channel_data = df[df['Point'].notna() & df[channel].notna()]
            
            if len(channel_data) < 2:
                # 데이터가 부족한 경우 기본값
                row_data[channel] = 0.1
                continue
            
            points_vals = channel_data['Point'].values
            channel_vals = channel_data[channel].values
            
            try:
                # 선형 보간 사용
                from scipy.interpolate import interp1d
                interp_func = interp1d(points_vals, channel_vals, 
                                     kind='linear', 
                                     bounds_error=False, 
                                     fill_value='extrapolate')
                
                interpolated_val = interp_func(new_point)
                
                # 음수값이나 이상값 처리
                interpolated_val = np.clip(interpolated_val, 0.001, 10.0)
                row_data[channel] = float(interpolated_val)
                
            except Exception as e:
                # 보간 실패시 기본값
                row_data[channel] = 0.1
        
        interpolated_data.append(row_data)
    
    result_df = pd.DataFrame(interpolated_data)
    print(f"✅ Point interpolation completed! Generated {len(result_df)} rows")
    
    return result_df

def _process_single_row(row_data, channels, original_angles, interpolated_angles):
    """
    단일 행에 대한 보간 처리 (병렬 처리용 헬퍼 함수)
    """
    # Suppress Streamlit warnings in parallel workers
    import logging
    import warnings
    logging.getLogger('streamlit').setLevel(logging.CRITICAL)
    logging.getLogger('streamlit.runtime').setLevel(logging.CRITICAL)
    logging.getLogger('streamlit.runtime.caching').setLevel(logging.CRITICAL)
    logging.getLogger('streamlit.runtime.state').setLevel(logging.CRITICAL)
    warnings.filterwarnings('ignore', category=UserWarning, module='streamlit')
    warnings.filterwarnings('ignore', message='.*No runtime found.*')
    warnings.filterwarnings('ignore', message='.*Session state does not function.*')
    warnings.filterwarnings('ignore', message='.*to view a Streamlit app.*')
    
    idx, row = row_data
    point_value = row['Point']
    
    if pd.isna(point_value):
        return None
        
    # 현재 Point에서 모든 채널의 깊이 값 추출
    channel_depths = []
    valid_angles = []
    
    for i, channel in enumerate(channels):
        depth = row[channel]
        if not pd.isna(depth) and depth != '':
            try:
                depth_val = float(depth)
                if depth_val != 0:  # 0이 아닌 값만 사용
                    channel_depths.append(depth_val)
                    valid_angles.append(original_angles[i])
            except (ValueError, TypeError):
                continue
    
    # 데이터가 부족한 경우 기본값으로 채움
    if len(channel_depths) < 3:
        # 모든 채널에 대해 기본값 사용 (평균값 또는 작은 값)
        default_depth = 0.1
        row_data = {'Point': point_value}
        for i in range(len(interpolated_angles)):
            row_data[f'CH-INT-{i:03d}'] = default_depth
        return row_data
    
    # 중복 제거 및 정렬
    combined = list(zip(valid_angles, channel_depths))
    combined = sorted(list(set(combined)))  # 중복 제거 후 정렬
    
    if len(combined) < 3:
        # 기본값으로 채움
        default_depth = np.mean(channel_depths) if channel_depths else 0.1
        row_data = {'Point': point_value}
        for i in range(len(interpolated_angles)):
            row_data[f'CH-INT-{i:03d}'] = default_depth
        return row_data
        
    valid_angles = [x[0] for x in combined]
    channel_depths = [x[1] for x in combined]
    
    # 원형 보간을 위한 데이터 확장
    # 양쪽 끝에 데이터 추가하여 원형 연속성 보장
    extended_angles = []
    extended_depths = []
    
    # 왼쪽 확장 (2π 빼기)
    extended_angles.extend([angle - 2*np.pi for angle in valid_angles[-2:]])
    extended_depths.extend(channel_depths[-2:])
    
    # 원본 데이터
    extended_angles.extend(valid_angles)
    extended_depths.extend(channel_depths)
    
    # 오른쪽 확장 (2π 더하기)
    extended_angles.extend([angle + 2*np.pi for angle in valid_angles[:2]])
    extended_depths.extend(channel_depths[:2])
    
    try:
        # 보간 함수 생성 (fallback 방식)
        if len(extended_angles) >= 4:
            interp_func = interp1d(extended_angles, extended_depths, kind='cubic', 
                                  bounds_error=False, fill_value='extrapolate')
        elif len(extended_angles) >= 3:
            interp_func = interp1d(extended_angles, extended_depths, kind='quadratic', 
                                  bounds_error=False, fill_value='extrapolate')
        else:
            interp_func = interp1d(extended_angles, extended_depths, kind='linear', 
                                  bounds_error=False, fill_value='extrapolate')
        
        # 보간된 값 계산
        interpolated_depths = interp_func(interpolated_angles)
        
        # 음수값이나 이상값 처리
        interpolated_depths = np.clip(interpolated_depths, 0.001, 10.0)  # 합리적인 범위로 제한
        
    except Exception as e:
        # 보간이 완전히 실패한 경우 평균값 사용
        avg_depth = np.mean(channel_depths)
        interpolated_depths = np.full(len(interpolated_angles), avg_depth)
    
    # 보간된 데이터 저장
    row_data = {'Point': point_value}
    for i, depth in enumerate(interpolated_depths):
        row_data[f'CH-INT-{i:03d}'] = depth
    
    return row_data

def interpolate_channel_data(df, channels, interpolation_factor=100, point_interpolation_factor=1, point_full_range=False, use_parallel=True, n_workers=None):
    """
    채널 데이터를 보간하여 부드러운 표면 생성
    interpolation_factor: 채널 보간 배수 (기본 100배)
    point_interpolation_factor: Point 보간 배수 (기본 1배=원본)
    point_full_range: Point 최대 해상도 보간 (1mm 간격)
    use_parallel: 병렬 처리 사용 여부 (기본 True)
    n_workers: 워커 프로세스 수 (기본 None은 CPU 코어 수)
    """
    point_factor_text = "Full Range" if point_full_range else f"{point_interpolation_factor}x"
    print(f"🚀 Starting interpolation - Channel: {interpolation_factor}x, Point: {point_factor_text}...")
    
    # 1단계: Point 방향 보간 (먼저 수행)
    if point_interpolation_factor > 1 or point_full_range:
        df = interpolate_point_data(df, channels, point_interpolation_factor, point_full_range)
    
    # 2단계: 채널 방향 보간
    # 원래 10개 채널을 interpolation_factor배로 증강
    original_angles = np.linspace(0, 2*np.pi, len(channels), endpoint=False)
    interpolated_angles = np.linspace(0, 2*np.pi, len(channels) * interpolation_factor, endpoint=False)
    
    # 첫 번째 행에서 채널 이름 생성
    interpolated_channels = []
    for i in range(len(interpolated_angles)):
        interpolated_channels.append(f'CH-INT-{i:03d}')
    
    # 빈 행 제거
    valid_rows = [(idx, row) for idx, row in df.iterrows() if not pd.isna(row['Point'])]
    
    if not use_parallel or len(valid_rows) < 100:
        # 순차 처리 (작은 데이터셋이거나 병렬처리 비활성화)
        print("📊 Processing sequentially...")
        interpolated_data = []
        for row_data in tqdm(valid_rows, desc="Processing rows"):
            result = _process_single_row(row_data, channels, original_angles, interpolated_angles)
            if result is not None:
                interpolated_data.append(result)
    else:
        # 병렬 처리
        if n_workers is None:
            n_workers = min(mp.cpu_count(), max(1, len(valid_rows) // 100))  # 적절한 워커 수 계산
        
        print(f"⚡ Processing with {n_workers} parallel workers...")
        
        # 병렬 처리를 위한 부분 함수 생성
        process_func = partial(_process_single_row, 
                              channels=channels, 
                              original_angles=original_angles, 
                              interpolated_angles=interpolated_angles)
        
        interpolated_data = []
        
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # 작업 제출
            future_to_idx = {executor.submit(process_func, row_data): idx 
                           for idx, row_data in enumerate(valid_rows)}
            
            # 결과 수집 (진행률 표시)
            results = {}
            for future in tqdm(as_completed(future_to_idx), 
                             total=len(future_to_idx), 
                             desc="Processing rows"):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    if result is not None:
                        results[idx] = result
                except Exception as exc:
                    print(f'⚠️ Row {idx} generated an exception: {exc}')
            
            # 원래 순서로 정렬
            for idx in sorted(results.keys()):
                interpolated_data.append(results[idx])
    
    # DataFrame 생성
    interpolated_df = pd.DataFrame(interpolated_data)
    
    print(f"✅ Interpolation completed! Generated {len(interpolated_df)} rows with {len(interpolated_channels)} interpolated channels")
    
    return interpolated_df, interpolated_channels

def create_cylindrical_coordinates(df, channels, base_radius=50, orientation='vertical'):
    """
    원통 좌표계로 변환
    Point: 길이 방향
    Channels: 원주 방향 (36도씩 배치)
    Channel values: 반지름 방향 깊이
    orientation: 'vertical' (세로) 또는 'horizontal' (눕힌 상태)
    """
    # 각 채널의 각도 (360도를 10등분하되, CH-A1과 CH-B5가 연결되도록)
    # CH-A1부터 시계방향으로 배치하고 마지막에 CH-B5가 CH-A1과 연결되도록
    angles = np.linspace(0, 2*np.pi, len(channels) + 1, endpoint=True)[:-1]  # 마지막 점 제외로 연결
    
    # 3D 좌표 저장 리스트
    x_coords = []
    y_coords = []
    z_coords = []
    values = []
    colors = []
    channel_names = []
    
    for idx, row in df.iterrows():
        length = row['Point']  # mm 단위 길이
        
        # Point가 NaN이면 건너뛰기
        if pd.isna(length):
            continue
        
        for i, channel in enumerate(channels):
            depth = row[channel]  # mm 단위 깊이
            
            # 깊이가 NaN이거나 빈 값이면 건너뛰기
            if pd.isna(depth) or depth == '':
                continue
                
            angle = angles[i]
            
            # 원통 표면에서 깊이만큼 안쪽으로 들어감
            radius = base_radius - depth
            
            if orientation == 'vertical':
                # 세로 방향 (기존)
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                z = length
            else:  # horizontal
                # 눕힌 상태 (90도 회전)
                x = length
                y = radius * np.cos(angle)
                z = radius * np.sin(angle)
            
            x_coords.append(x)
            y_coords.append(y)
            z_coords.append(z)
            values.append(depth)
            colors.append(i)  # 채널별 색상
            channel_names.append(channel)
    
    return x_coords, y_coords, z_coords, values, colors, channel_names, angles

def create_cylinder_surface(base_radius=50, height=2500, resolution=50, orientation='vertical'):
    """
    기본 원통 표면 생성 (참조용)
    orientation: 'vertical' (세로) 또는 'horizontal' (눕힌 상태)
    """
    # 원주 방향 각도
    theta = np.linspace(0, 2*np.pi, resolution)
    # 높이 방향
    length = np.linspace(0, height, resolution)
    
    # 메쉬 그리드 생성
    THETA, LENGTH = np.meshgrid(theta, length)
    
    if orientation == 'vertical':
        # 세로 방향 (기존)
        X = base_radius * np.cos(THETA)
        Y = base_radius * np.sin(THETA)
        Z = LENGTH
    else:  # horizontal
        # 눕힌 상태 (90도 회전)
        X = LENGTH
        Y = base_radius * np.cos(THETA)
        Z = base_radius * np.sin(THETA)
    
    return X, Y, Z

def create_surface_mesh(df, channels, base_radius=50, orientation='vertical'):
    """
    3D 표면 메쉬 생성
    """
    # Point와 채널을 격자로 배열
    points = df['Point'].values
    angles = np.linspace(0, 2*np.pi, len(channels), endpoint=False)
    
    # 메쉬 그리드 생성
    POINTS, ANGLES = np.meshgrid(points, angles)
    
    # 깊이 데이터 배열
    depth_matrix = np.zeros((len(channels), len(points)))
    for i, channel in enumerate(channels):
        depth_matrix[i, :] = df[channel].values
    
    # 반지름 계산
    radius_matrix = base_radius - depth_matrix
    
    if orientation == 'vertical':
        # 세로 방향
        X = radius_matrix * np.cos(ANGLES)
        Y = radius_matrix * np.sin(ANGLES)
        Z = POINTS
    else:  # horizontal
        # 눕힌 상태
        X = POINTS
        Y = radius_matrix * np.cos(ANGLES)
        Z = radius_matrix * np.sin(ANGLES)
    
    return X, Y, Z, depth_matrix

def create_complete_surface_mesh(df, channels, base_radius=50, orientation='vertical'):
    """
    완전한 원통 표면 메쉬 생성 (CH-A1과 CH-B5 연결)
    """
    # Point와 채널을 격자로 배열
    points = df['Point'].dropna().values
    
    # 각 채널의 각도 (CH-A1과 CH-B5가 연결되도록 360도 완전 순환)
    angles = np.linspace(0, 2*np.pi, len(channels) + 1, endpoint=True)  # 연결을 위해 +1
    
    # 메쉬 그리드 생성
    POINTS, ANGLES = np.meshgrid(points, angles)
    
    # 깊이 데이터 배열 (채널 순환 + 연결)
    depth_matrix = np.zeros((len(channels) + 1, len(points)))
    
    for i, channel in enumerate(channels):
        channel_data = []
        for point in points:
            # 해당 Point에서 채널 값 찾기
            row_data = df[df['Point'] == point]
            if not row_data.empty and not pd.isna(row_data.iloc[0][channel]):
                channel_data.append(row_data.iloc[0][channel])
            else:
                # 빈 값인 경우 주변 값으로 보간 또는 기본값 사용
                channel_data.append(0.1)  # 기본 깊이값
        depth_matrix[i, :] = channel_data
    
    # 마지막 행을 첫 번째 행과 동일하게 만들어 연결
    depth_matrix[-1, :] = depth_matrix[0, :]
    
    # 반지름 계산
    radius_matrix = base_radius - depth_matrix
    
    if orientation == 'vertical':
        # 세로 방향
        X = radius_matrix * np.cos(ANGLES)
        Y = radius_matrix * np.sin(ANGLES)
        Z = POINTS
    else:  # horizontal
        # 눕힌 상태
        X = POINTS
        Y = radius_matrix * np.cos(ANGLES)
        Z = radius_matrix * np.sin(ANGLES)
    
    return X, Y, Z, depth_matrix

def plot_cylindrical_3d(file_path='iot/BAR00001TR.CSV', orientation='vertical', show_surface=False, show_points=True, show_tracks=True, color_theme='Viridis'):
    """
    원통형 3D 시각화 메인 함수
    orientation: 'vertical' (세로) 또는 'horizontal' (눕힌 상태)
    show_surface: 3D 표면 메쉬 표시 여부
    show_points: 포인트 표시 여부
    show_tracks: 궤적 라인 표시 여부
    color_theme: 색상 테마 (COLOR_THEMES 키 중 하나)
    """
    # 색상 테마 가져오기
    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES['Viridis'])
    colorscale = theme['colorscale']
    
    df, channels = load_bar_data(file_path)
    x_coords, y_coords, z_coords, values, colors, channel_names, angles = create_cylindrical_coordinates(df, channels, orientation=orientation)
    
    # 기본 원통 표면
    cyl_x, cyl_y, cyl_z = create_cylinder_surface(orientation=orientation)
    
    # Plotly figure 생성
    fig = go.Figure()
    
    # 1. 기본 원통 표면 (반투명)
    fig.add_trace(go.Surface(
        x=cyl_x, y=cyl_y, z=cyl_z,
        colorscale='Greys',
        opacity=0.2,
        showscale=False,
        name='Cylinder Base',
        hovertemplate='Base Cylinder<extra></extra>',
        visible=True
    ))
    
    # 2. 3D 표면 메쉬 (옵션)
    if show_surface:
        mesh_x, mesh_y, mesh_z, depth_matrix = create_surface_mesh(df, channels, orientation=orientation)
        fig.add_trace(go.Surface(
            x=mesh_x, y=mesh_y, z=mesh_z,
            surfacecolor=depth_matrix,
            colorscale=colorscale,
            colorbar=dict(
                title='Depth (mm)',
                titleside='right',
                x=1.02
            ),
            name='3D Surface',
            hovertemplate='Channel: %{y}<br>' +
                         'Point: %{x} mm<br>' +
                         'Depth: %{surfacecolor:.3f} mm<extra></extra>',
            opacity=0.8
        ))
    
    # 3. 측정 데이터 포인트들 (깊이에 따른 색상)
    if show_points:
        fig.add_trace(go.Scatter3d(
            x=x_coords,
            y=y_coords, 
            z=z_coords,
            mode='markers',
            marker=dict(
                size=3,
                color=values,
                colorscale=colorscale,
                colorbar=dict(
                    title='Depth (mm)',
                    titleside='right',
                    x=0.98 if not show_surface else 1.04
                ),
                opacity=0.8
            ),
            name='Measurement Points',
            hovertemplate='<b>%{text}</b><br>' +
                         ('Point: %{z:.1f} mm<br>' if orientation == 'vertical' else 'Point: %{x:.1f} mm<br>') +
                         'Depth: %{marker.color:.3f} mm<br>' +
                         'X: %{x:.1f}<br>' +
                         'Y: %{y:.1f}<br>' +
                         'Z: %{z:.1f}<extra></extra>',
            text=channel_names,
            visible=show_points
        ))
    
    # 4. 각 채널별 궤적 라인
    if show_tracks:
        colors_list = px.colors.qualitative.Set3
        for i, channel in enumerate(channels):
            # 해당 채널의 모든 포인트 추출
            channel_indices = [j for j, name in enumerate(channel_names) if name == channel]
            channel_x = [x_coords[j] for j in channel_indices]
            channel_y = [y_coords[j] for j in channel_indices]
            channel_z = [z_coords[j] for j in channel_indices]
            
            fig.add_trace(go.Scatter3d(
                x=channel_x,
                y=channel_y,
                z=channel_z,
                mode='lines',
                line=dict(
                    color=colors_list[i % len(colors_list)],
                    width=4
                ),
                name=f'{channel} Track',
                hovertemplate=f'<b>{channel}</b><br>' +
                             ('Point: %{z:.1f} mm<br>' if orientation == 'vertical' else 'Point: %{x:.1f} mm<br>') +
                             'X: %{x:.1f}<br>' +
                             'Y: %{y:.1f}<br>' +
                             'Z: %{z:.1f}<extra></extra>',
                visible=show_tracks
            ))
    
    # 레이아웃 설정
    if orientation == 'vertical':
        scene_config = dict(
            xaxis_title='X (mm)',
            yaxis_title='Y (mm)', 
            zaxis_title='Length (mm)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=2)
        )
    else:  # horizontal
        scene_config = dict(
            xaxis_title='Length (mm)',
            yaxis_title='Y (mm)',
            zaxis_title='Z (mm)',
            camera=dict(eye=dict(x=1.2, y=1.5, z=1.5)),
            aspectmode='manual',
            aspectratio=dict(x=2, y=1, z=1)
        )
    
    fig.update_layout(
        title={
            'text': f'Cylindrical 3D Visualization - BAR00001 ({orientation.capitalize()})',
            'x': 0.5,
            'font': {'size': 20}
        },
        scene=scene_config,
        width=1200,
        height=800,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )
    
    return fig

def plot_heatmap_unwrapped(file_path='iot/BAR00001TR.CSV', color_theme='Viridis'):
    """
    원통을 펼친 히트맵 시각화
    color_theme: 색상 테마 (COLOR_THEMES 키 중 하나)
    """
    # 색상 테마 가져오기
    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES['Viridis'])
    colorscale = theme['colorscale']
    
    df, channels = load_bar_data(file_path)
    
    # 히트맵용 데이터 매트릭스 생성
    heatmap_data = []
    for channel in channels:
        heatmap_data.append(df[channel].values)
    
    heatmap_data = np.array(heatmap_data)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=df['Point'],
        y=channels,
        colorscale=colorscale,
        colorbar=dict(title='Depth (mm)'),
        hoverongaps=False,
        hovertemplate='Point: %{x} mm<br>' +
                     'Channel: %{y}<br>' +
                     'Depth: %{z:.3f} mm<extra></extra>'
    ))
    
    fig.update_layout(
        title='Unwrapped Cylindrical Surface (Heatmap)',
        xaxis_title='Point (mm)',
        yaxis_title='Channel (Circumferential)',
        width=1400,
        height=600
    )
    
    return fig

def create_dashboard():
    """
    대시보드 생성 (3D + 히트맵)
    """
    from plotly.subplots import make_subplots
    
    # 3D 플롯
    fig_3d = plot_cylindrical_3d()
    
    # 히트맵
    fig_heatmap = plot_heatmap_unwrapped()
    
    return fig_3d, fig_heatmap

def plot_complete_cylindrical_3d(file_path='iot/BAR00001TR.CSV', orientation='vertical', show_wireframe=True, show_surface=True, show_points=False, color_theme='Viridis'):
    """
    완전한 원통 표면으로 증강된 3D 시각화
    CH-A1과 CH-B5가 연결된 완전한 원통 표면
    color_theme: 색상 테마 (COLOR_THEMES 키 중 하나)
    """
    # 색상 테마 가져오기
    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES['Viridis'])
    colorscale = theme['colorscale']
    
    df, channels = load_bar_data(file_path)
    
    # 완전한 표면 메쉬 생성
    mesh_x, mesh_y, mesh_z, depth_matrix = create_complete_surface_mesh(df, channels, orientation=orientation)
    
    # 기본 원통 표면 (참조용)
    cyl_x, cyl_y, cyl_z = create_cylinder_surface(orientation=orientation)
    
    # Plotly figure 생성
    fig = go.Figure()
    
    # 1. 기본 원통 표면 (매우 투명하게)
    fig.add_trace(go.Surface(
        x=cyl_x, y=cyl_y, z=cyl_z,
        colorscale='Greys',
        opacity=0.1,
        showscale=False,
        name='Base Cylinder',
        hovertemplate='Base Cylinder<extra></extra>',
        visible=True
    ))
    
    # 2. 완전한 표면 메쉬
    if show_surface:
        fig.add_trace(go.Surface(
            x=mesh_x, y=mesh_y, z=mesh_z,
            surfacecolor=depth_matrix,
            colorscale=colorscale,
            colorbar=dict(
                title='Surface Depth (mm)',
                titleside='right',
                x=0.96
            ),
            name='Complete Surface',
            hovertemplate='Point: %{customdata[0]:.1f} mm<br>' +
                         'Angle: %{customdata[1]:.1f}°<br>' +
                         'Depth: %{surfacecolor:.3f} mm<extra></extra>',
            opacity=0.8,
            visible=show_surface
        ))
    
    # 3. 와이어프레임 (표면 구조 강조)
    if show_wireframe:
        # 길이 방향 와이어프레임
        for i in range(0, mesh_x.shape[0], 2):  # 2개씩 건너뛰어 간소화
            fig.add_trace(go.Scatter3d(
                x=mesh_x[i, :],
                y=mesh_y[i, :],
                z=mesh_z[i, :],
                mode='lines',
                line=dict(color='white', width=2),
                name=f'Wire {i}' if i == 0 else '',
                showlegend=i == 0,
                hovertemplate='Wireframe<extra></extra>',
                visible=show_wireframe
            ))
        
        # 원주 방향 와이어프레임
        for j in range(0, mesh_x.shape[1], 20):  # 20개씩 건너뛰어 간소화
            fig.add_trace(go.Scatter3d(
                x=mesh_x[:, j],
                y=mesh_y[:, j],
                z=mesh_z[:, j],
                mode='lines',
                line=dict(color='yellow', width=2),
                name='Wire Circumferential' if j == 0 else '',
                showlegend=j == 0,
                hovertemplate='Wireframe<extra></extra>',
                visible=show_wireframe
            ))
    
    # 4. 측정 포인트들 (옵션)
    if show_points:
        x_coords, y_coords, z_coords, values, colors, channel_names, angles = create_cylindrical_coordinates(df, channels, orientation=orientation)
        
        fig.add_trace(go.Scatter3d(
            x=x_coords,
            y=y_coords, 
            z=z_coords,
            mode='markers',
            marker=dict(
                size=4,
                color=values,
                colorscale='Plasma',
                colorbar=dict(
                    title='Point Depth (mm)',
                    titleside='right',
                    x=1.04
                ),
                opacity=0.9
            ),
            name='Measurement Points',
            hovertemplate='<b>%{text}</b><br>' +
                         ('Point: %{z:.1f} mm<br>' if orientation == 'vertical' else 'Point: %{x:.1f} mm<br>') +
                         'Depth: %{marker.color:.3f} mm<br>' +
                         'X: %{x:.1f}<br>' +
                         'Y: %{y:.1f}<br>' +
                         'Z: %{z:.1f}<extra></extra>',
            text=channel_names,
            visible=show_points
        ))
    
    # 레이아웃 설정
    if orientation == 'vertical':
        scene_config = dict(
            xaxis_title='X (mm)',
            yaxis_title='Y (mm)', 
            zaxis_title='Length (mm)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=2)
        )
    else:  # horizontal
        scene_config = dict(
            xaxis_title='Length (mm)',
            yaxis_title='Y (mm)',
            zaxis_title='Z (mm)',
            camera=dict(eye=dict(x=1.2, y=1.5, z=1.5)),
            aspectmode='manual',
            aspectratio=dict(x=2, y=1, z=1)
        )
    
    fig.update_layout(
        title={
            'text': f'Complete Cylindrical 3D Surface - BAR00001TR ({orientation.capitalize()})',
            'x': 0.5,
            'font': {'size': 20}
        },
        scene=scene_config,
        width=1200,
        height=800,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )
    
    return fig

def plot_smooth_cylindrical_3d(file_path='iot/BAR00001TR.CSV', orientation='vertical', interpolation_factor=5, point_interpolation_factor=1, point_full_range=False, show_wireframe=False, show_original_points=False, color_theme='Viridis', use_parallel=True, n_workers=None):
    """
    보간된 데이터로 부드러운 원통형 3D 시각화
    interpolation_factor: 채널 보간 배수 (기본 5배)
    point_interpolation_factor: Point 보간 배수 (기본 1배=원본)
    show_wireframe: 와이어프레임 표시 여부
    show_original_points: 원본 측정 포인트 표시 여부
    color_theme: 색상 테마 (COLOR_THEMES 키 중 하나)
    use_parallel: 병렬 처리 사용 여부 (기본 True)
    n_workers: 워커 프로세스 수 (기본 None은 CPU 코어 수)
    """
    # 색상 테마 가져오기
    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES['Viridis'])
    colorscale = theme['colorscale']
    
    # 원본 데이터 로드
    df, channels = load_bar_data(file_path)
    
    # 데이터 보간 (Channel과 Point 모두)
    interpolated_df, interpolated_channels = interpolate_channel_data(df, channels, interpolation_factor, point_interpolation_factor, point_full_range, use_parallel, n_workers)
    
    if interpolated_df.empty:
        raise ValueError("보간된 데이터가 없습니다. 원본 데이터를 확인해주세요.")
    
    # 보간된 데이터로 완전한 표면 메쉬 생성
    mesh_x, mesh_y, mesh_z, depth_matrix = create_complete_surface_mesh(
        interpolated_df, interpolated_channels, orientation=orientation
    )
    
    # Plotly figure 생성
    fig = go.Figure()
    
    # 1. 부드러운 표면 메쉬
    fig.add_trace(go.Surface(
        x=mesh_x, y=mesh_y, z=mesh_z,
        surfacecolor=depth_matrix,
        colorscale=colorscale,
        colorbar=dict(
            title='Depth (mm)',
            titleside='right',
            x=1.02
        ),
        name='Smooth Surface',
        hovertemplate='Point: %{customdata[0]:.1f} mm<br>' +
                     'Angle: %{customdata[1]:.1f}°<br>' +
                     'Depth: %{surfacecolor:.3f} mm<extra></extra>',
        opacity=0.9,
        lighting=dict(
            ambient=0.4,
            diffuse=0.8,
            specular=0.1
        )
    ))
    
    # 2. 와이어프레임 (옵션)
    if show_wireframe:
        # 길이 방향 와이어프레임 (더 세밀하게)
        for i in range(0, mesh_x.shape[0], max(1, mesh_x.shape[0]//20)):
            fig.add_trace(go.Scatter3d(
                x=mesh_x[i, :],
                y=mesh_y[i, :],
                z=mesh_z[i, :],
                mode='lines',
                line=dict(color='white', width=1),
                name='Wireframe' if i == 0 else '',
                showlegend=i == 0,
                hovertemplate='Wireframe<extra></extra>'
            ))
        
        # 원주 방향 와이어프레임
        for j in range(0, mesh_x.shape[1], max(1, mesh_x.shape[1]//30)):
            fig.add_trace(go.Scatter3d(
                x=mesh_x[:, j],
                y=mesh_y[:, j],
                z=mesh_z[:, j],
                mode='lines',
                line=dict(color='yellow', width=1),
                name='Wire Circumferential' if j == 0 else '',
                showlegend=j == 0,
                hovertemplate='Wireframe<extra></extra>'
            ))
    
    # 3. 원본 측정 포인트들 (옵션)
    if show_original_points:
        x_coords, y_coords, z_coords, values, colors, channel_names, angles = create_cylindrical_coordinates(
            df, channels, orientation=orientation
        )
        
        fig.add_trace(go.Scatter3d(
            x=x_coords,
            y=y_coords, 
            z=z_coords,
            mode='markers',
            marker=dict(
                size=6,
                color='red',
                symbol='circle',
                opacity=1.0,
                line=dict(color='darkred', width=2)
            ),
            name='Original Points',
            hovertemplate='<b>%{text}</b><br>' +
                         ('Point: %{z:.1f} mm<br>' if orientation == 'vertical' else 'Point: %{x:.1f} mm<br>') +
                         'Depth: %{customdata:.3f} mm<br>' +
                         'X: %{x:.1f}<br>' +
                         'Y: %{y:.1f}<br>' +
                         'Z: %{z:.1f}<extra></extra>',
            text=channel_names,
            customdata=values
        ))
    
    # 레이아웃 설정
    if orientation == 'vertical':
        scene_config = dict(
            xaxis_title='X (mm)',
            yaxis_title='Y (mm)', 
            zaxis_title='Length (mm)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=2)
        )
    else:  # horizontal
        scene_config = dict(
            xaxis_title='Length (mm)',
            yaxis_title='Y (mm)',
            zaxis_title='Z (mm)',
            camera=dict(eye=dict(x=1.2, y=1.5, z=1.5)),
            aspectmode='manual',
            aspectratio=dict(x=2, y=1, z=1)
        )
    
    fig.update_layout(
        title={
            'text': f'Smooth Surface ({orientation.capitalize()}) - Ch:{interpolation_factor}x + Pt:{point_interpolation_factor}x',
            'x': 0.5,
            'font': {'size': 18}
        },
        scene=scene_config,
        width=1200,
        height=800,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )
    
    return fig

def plot_smooth_cylindrical_3d_with_range_selector(file_path='iot/BAR00001TR.CSV', orientation='vertical', 
                                                  interpolation_factor=5, point_interpolation_factor=1,
                                                  point_full_range=False, show_wireframe=False, show_original_points=False, 
                                                  color_theme='Viridis', use_parallel=True, n_workers=None,
                                                  point_range=None):
    """
    구간 선택 기능이 있는 부드러운 원통형 3D 시각화
    point_range: (min_point, max_point) 튜플로 표시할 구간 지정
    """
    # 색상 테마 가져오기
    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES['Viridis'])
    colorscale = theme['colorscale']
    
    # 원본 데이터 로드
    df, channels = load_bar_data(file_path)
    
    # 데이터 보간 (Point와 Channel 모두)
    interpolated_df, interpolated_channels = interpolate_channel_data(
        df, channels, interpolation_factor, point_interpolation_factor, point_full_range, use_parallel, n_workers
    )
    
    if interpolated_df.empty:
        raise ValueError("보간된 데이터가 없습니다. 원본 데이터를 확인해주세요.")
    
    # 구간 필터링
    if point_range is not None:
        min_point, max_point = point_range
        mask = (interpolated_df['Point'] >= min_point) & (interpolated_df['Point'] <= max_point)
        interpolated_df = interpolated_df[mask].copy()
        
        if interpolated_df.empty:
            raise ValueError(f"지정된 구간 ({min_point}-{max_point})에 데이터가 없습니다.")
    
    # 보간된 데이터로 완전한 표면 메쉬 생성
    mesh_x, mesh_y, mesh_z, depth_matrix = create_complete_surface_mesh(
        interpolated_df, interpolated_channels, orientation=orientation
    )
    
    # Plotly figure 생성
    fig = go.Figure()
    
    # 1. 부드러운 표면 메쉬
    fig.add_trace(go.Surface(
        x=mesh_x, y=mesh_y, z=mesh_z,
        surfacecolor=depth_matrix,
        colorscale=colorscale,
        colorbar=dict(
            title='Depth (mm)',
            titleside='right',
            x=1.02
        ),
        name='Ultra-Smooth Surface',
        hovertemplate='Point: %{customdata[0]:.1f} mm<br>' +
                     'Angle: %{customdata[1]:.1f}°<br>' +
                     'Depth: %{surfacecolor:.3f} mm<extra></extra>',
        opacity=0.9,
        lighting=dict(
            ambient=0.4,
            diffuse=0.8,
            specular=0.1
        )
    ))
    
    # 2. 와이어프레임 (옵션)
    if show_wireframe:
        # 길이 방향 와이어프레임
        wireframe_step = max(1, mesh_x.shape[0]//15)
        for i in range(0, mesh_x.shape[0], wireframe_step):
            fig.add_trace(go.Scatter3d(
                x=mesh_x[i, :],
                y=mesh_y[i, :],
                z=mesh_z[i, :],
                mode='lines',
                line=dict(color='rgba(255,255,255,0.5)', width=1),
                name='Length Wire' if i == 0 else '',
                showlegend=i == 0,
                hovertemplate='Wireframe (Length)<extra></extra>'
            ))
        
        # 원주 방향 와이어프레임
        circumf_step = max(1, mesh_x.shape[1]//20)
        for j in range(0, mesh_x.shape[1], circumf_step):
            fig.add_trace(go.Scatter3d(
                x=mesh_x[:, j],
                y=mesh_y[:, j],
                z=mesh_z[:, j],
                mode='lines',
                line=dict(color='rgba(255,255,0,0.5)', width=1),
                name='Circumf Wire' if j == 0 else '',
                showlegend=j == 0,
                hovertemplate='Wireframe (Circumferential)<extra></extra>'
            ))
    
    # 3. 원본 측정 포인트들 (옵션)
    if show_original_points:
        x_coords, y_coords, z_coords, values, colors, channel_names, angles = create_cylindrical_coordinates(
            df, channels, orientation=orientation
        )
        
        # 구간 필터링
        if point_range is not None:
            filtered_indices = []
            min_point, max_point = point_range
            for i, (x, y, z) in enumerate(zip(x_coords, y_coords, z_coords)):
                point_val = z if orientation == 'vertical' else x
                if min_point <= point_val <= max_point:
                    filtered_indices.append(i)
            
            x_coords = [x_coords[i] for i in filtered_indices]
            y_coords = [y_coords[i] for i in filtered_indices]
            z_coords = [z_coords[i] for i in filtered_indices]
            values = [values[i] for i in filtered_indices]
            channel_names = [channel_names[i] for i in filtered_indices]
        
        if x_coords:  # 필터링 후 데이터가 있는 경우만
            fig.add_trace(go.Scatter3d(
                x=x_coords, y=y_coords, z=z_coords,
                mode='markers',
                marker=dict(
                    size=8,
                    color='red',
                    symbol='circle',
                    opacity=1.0,
                    line=dict(color='darkred', width=2)
                ),
                name='Original Points',
                hovertemplate='<b>%{text}</b><br>' +
                             ('Point: %{z:.1f} mm<br>' if orientation == 'vertical' else 'Point: %{x:.1f} mm<br>') +
                             'Depth: %{customdata:.3f} mm<br>' +
                             'X: %{x:.1f}<br>' +
                             'Y: %{y:.1f}<br>' +
                             'Z: %{z:.1f}<extra></extra>',
                text=channel_names,
                customdata=values
            ))
    
    # 레이아웃 설정
    point_min = interpolated_df['Point'].min()
    point_max = interpolated_df['Point'].max()
    
    if orientation == 'vertical':
        scene_config = dict(
            xaxis_title='X (mm)',
            yaxis_title='Y (mm)', 
            zaxis_title='Length (mm)',
            zaxis=dict(range=[point_min, point_max]),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=2)
        )
    else:  # horizontal
        scene_config = dict(
            xaxis_title='Length (mm)',
            xaxis=dict(range=[point_min, point_max]),
            yaxis_title='Y (mm)',
            zaxis_title='Z (mm)',
            camera=dict(eye=dict(x=1.2, y=1.5, z=1.5)),
            aspectmode='manual',
            aspectratio=dict(x=2, y=1, z=1)
        )
    
    # 제목 생성
    range_text = f" (Range: {point_min:.1f}-{point_max:.1f}mm)" if point_range else ""
    title_text = f'Ultra-Smooth Surface ({orientation.capitalize()}) - Ch:{interpolation_factor}x + Pt:{point_interpolation_factor}x{range_text}'
    
    fig.update_layout(
        title={
            'text': title_text,
            'x': 0.5,
            'font': {'size': 16}
        },
        scene=scene_config,
        width=1200,
        height=800,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)'
        ),
        # 범위 슬라이더 추가
        annotations=[
            dict(
                text=f"📊 Data Points: {len(interpolated_df)} | Channels: {len(interpolated_channels)}",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.02, y=0.02,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="gray",
                borderwidth=1
            )
        ]
    )
    
    return fig

 