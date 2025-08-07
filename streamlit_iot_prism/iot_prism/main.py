import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import time

# 모듈 임포트
from .utils import process_dataframe, convert_df_to_csv, save_df_to_file, get_equipment_type, get_sensor_type, DATA_DIR, generate_iot_data, load_iot_font_css
from .visualizations import (
    render_timeseries_ui, render_histogram_ui, render_boxplot_ui, 
    render_heatmap_ui, render_pattern_ui, render_anomaly_ui, 
    render_fft_ui, render_trend_ui, render_correlation_ui, render_threed_ui,
    render_distribution_ui, render_clustering_ui,
    render_alarm_threshold_ui, render_timefreq_ui, 
    render_visualization_guide_ui, render_cycle_analysis_ui
)
from .insights import render_insights_ui
from .utils.style import apply_custom_style, apply_graph_themes
from .utils.ai_settings import init_ai_settings
from .guide import render_intro_guide, render_visualization_guide_explanation

# 항상 스타일 적용 (전역 범위)
load_iot_font_css()
apply_custom_style()
apply_graph_themes()

# 시각화 옵션 정의 - 시각화 타입에 따른 렌더링 함수 매핑
visualization_functions = {
    "시간 차트": render_timeseries_ui,
    "히스토그램": render_histogram_ui,
    "박스플롯": render_boxplot_ui,
    "히트맵": render_heatmap_ui,
    "일별/시간별 패턴": render_pattern_ui,
    "이상치 분석": render_anomaly_ui,
    "주파수 분석": render_fft_ui,
    "시간-주파수 분석": render_timefreq_ui,
    "트렌드 분석": render_trend_ui,
    "상관관계 분석": render_correlation_ui,
    "분포 비교": render_distribution_ui,
    "3D 시각화": render_threed_ui,
    "패턴 클러스터링": render_clustering_ui,
    "경보 및 임계값 설정": render_alarm_threshold_ui,
    "운전/정지 주기 분석": render_cycle_analysis_ui,
    "종합 인사이트": render_insights_ui,
}

# 모든 AI 분석 관련 세션 상태 초기화 함수
def reset_all_ai_session_states():
    """모든 AI 관련 및 시각화 세션 상태를 초기화하는 함수"""
    # AI 분석 및 AI 질문 기능 초기화
    if "ai_analysis_results" in st.session_state:
        del st.session_state.ai_analysis_results
    if "ai_chat_history" in st.session_state:
        del st.session_state.ai_chat_history
    if "ai_analysis_completed" in st.session_state:
        st.session_state.ai_analysis_completed = False
    
    # 시각화 모듈별 세션 상태 초기화
    modules = [
        "visualization_guide",        # 시각화 가이드
        "timeseries_analysis",        # 시계열 차트
        "histogram_analysis",         # 히스토그램
        "boxplot_analysis",           # 박스 플롯
        "heatmap_analysis",           # 히트맵
        "pattern_analysis",           # 일별/시간별 패턴
        "anomaly_analysis",           # 이상치 분석
        "fft_analysis",               # 주파수 분석(FFT)
        "timefreq_analysis",          # 시간-주파수 분석
        "trend_analysis",             # 트렌드 분석
        "correlation_analysis",       # 상관관계 분석
        "distribution_analysis",      # 분포 비교
        "threed_analysis",            # 3D 시각화
        "clustering_analysis",        # 패턴 클러스터링
        "alarm_threshold_analysis",   # 경보 및 임계값 설정
        "cycle_analysis",             # 운전/정지 주기 분석
        "insights_analysis"           # 종합 인사이트
    ]
    
    # 모든 모듈에 대해서 세션 상태 초기화
    for prefix in modules:
        # 캐시, 실행 상태, 대화 기록 초기화
        if f"{prefix}_cache" in st.session_state:
            st.session_state[f"{prefix}_cache"] = {}
        if f"{prefix}_running" in st.session_state:
            st.session_state[f"{prefix}_running"] = False
        if f"{prefix}_history" in st.session_state:
            st.session_state[f"{prefix}_history"] = []
        
        # 모듈별 특수 키 초기화
        
        # 시각화 가이드 특수 키
        if prefix == "visualization_guide" and f"{prefix}_initial_analysis_added" in st.session_state:
            st.session_state[f"{prefix}_initial_analysis_added"] = False
        
        # 시계열 차트 특수 키
        if prefix == "timeseries_analysis":
            if f"{prefix}_specific_prompt" in st.session_state:
                del st.session_state[f"{prefix}_specific_prompt"]
            if f"{prefix}_current_chart_type" in st.session_state:
                del st.session_state[f"{prefix}_current_chart_type"]
        
        # 히스토그램 특수 키
        if prefix == "histogram_analysis":
            if f"{prefix}_specific_prompt" in st.session_state:
                del st.session_state[f"{prefix}_specific_prompt"]
            if f"{prefix}_current_hist_type" in st.session_state:
                del st.session_state[f"{prefix}_current_hist_type"]
        
        # 박스 플롯 특수 키
        if prefix == "boxplot_analysis":
            if f"{prefix}_specific_prompt" in st.session_state:
                del st.session_state[f"{prefix}_specific_prompt"]
            if f"{prefix}_current_groupby" in st.session_state:
                del st.session_state[f"{prefix}_current_groupby"]
        
        # 히트맵 특수 키
        if prefix == "heatmap_analysis":
            if f"{prefix}_specific_prompt" in st.session_state:
                del st.session_state[f"{prefix}_specific_prompt"]
            if f"{prefix}_current_config" in st.session_state:
                del st.session_state[f"{prefix}_current_config"]
        
        # 상관관계 분석 특수 키
        if prefix == "correlation_analysis":
            if f"{prefix}_specific_prompt" in st.session_state:
                del st.session_state[f"{prefix}_specific_prompt"]
            if f"{prefix}_current_method" in st.session_state:
                del st.session_state[f"{prefix}_current_method"]
        
        # 클러스터링 특수 키
        if prefix == "clustering_analysis":
            if f"{prefix}_specific_prompt" in st.session_state:
                del st.session_state[f"{prefix}_specific_prompt"]
            if f"{prefix}_current_config" in st.session_state:
                del st.session_state[f"{prefix}_current_config"]
        
        # 이외의 모듈에 대한 일반적인 특수 키 처리
        if f"{prefix}_specific_prompt" in st.session_state:
            del st.session_state[f"{prefix}_specific_prompt"]
    
    # 디버깅용 로깅
    print(f"모든 AI 및 시각화 세션 상태 초기화 완료. 총 {len(modules)} 모듈 처리됨.")
    
    # 데이터 샘플 표시 및 결측값 처리 설정 초기화
    if "sample_expander_open" in st.session_state:
        st.session_state.sample_expander_open = False
    if "sample_rows" in st.session_state:
        st.session_state.sample_rows = 10
    if "show_full_data" in st.session_state:
        st.session_state.show_full_data = False
    if "data_page" in st.session_state:
        st.session_state.data_page = 1
    
    # 결측값 처리 방법 초기화 - 기본값으로 설정
    if "null_handling_method" in st.session_state:
        st.session_state.null_handling_method = "remove"  # 기본값: 결측값이 있는 행 제거

def main():
    # Title
    st.title("💎 DX-AI IoT Prism")
    st.markdown("제조 설비 IoT 데이터를 시각화하고 분석 합니다.")
    
    # 소개 섹션 추가 (별도 모듈로 분리)
    render_intro_guide()
    
    # 세션 상태 초기화
    if "data_generated" not in st.session_state:
        st.session_state.data_generated = False
    
    # AI 설정 미리 초기화
    init_ai_settings()
    
    # 폰트 재설정 체크 - 항상 실행
    load_iot_font_css()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("IoT 데이터 생성/로드 설정")
        
        # 데이터 소스 선택
        data_source = st.radio(
            "데이터 소스 선택",
            ["새로 생성", "생성 후 파일 저장", "CSV 파일 업로드", "CSV 파일 읽기"],
            help="새로 생성: 새로운 데이터를 생성합니다. 생성 후 파일 저장: 생성된 데이터를 파일로 저장합니다. CSV 파일 업로드: 브라우저에서 CSV 파일을 업로드합니다. CSV 파일 읽기: 로컬 디렉토리에서 CSV 파일을 읽습니다."
        )
        
        # 메모리 관리 옵션 추가
        memory_option = st.radio(
            "메모리 관리 방식",
            ["모든 데이터 메모리에 로드", "샘플링하여 메모리 절약"],
            help="대용량 데이터셋은 샘플링하여 메모리 사용량을 줄일 수 있습니다."
        )
        
        if memory_option == "샘플링하여 메모리 절약":
            max_memory_points = st.slider(
                "최대 메모리 포인트 수", 
                min_value=10000, 
                max_value=1000000, 
                value=100000, 
                step=10000,
                help="시각화 및 분석에 사용할 최대 데이터 포인트 수입니다. 원본 데이터는 CSV에 모두 저장됩니다."
            )
        else:
            max_memory_points = 1000000  # 기본값 설정
        
        # 로컬 CSV 파일 업로드
        if data_source == "CSV 파일 업로드":
            st.subheader("CSV 파일 업로드")
            uploaded_file = st.file_uploader("CSV 파일을 업로드 하세요.", type="csv")
            if uploaded_file is not None:
                try:
                    # 파일 이름에서 equipment_type 추출 시도
                    filename = uploaded_file.name
                    st.session_state.current_filename = filename
                    try:
                        parts = filename.split('_')
                        if len(parts) >= 2 and parts[0] == 'iot':
                            extracted_equipment_type = parts[1]
                        else:
                            extracted_equipment_type = "장비"
                    except:
                        extracted_equipment_type = "장비"
                    
                    # Equipment type selection (같은 들여쓰기 수준으로 수정)
                    col1, col2 = st.columns(2)
                    with col1:
                        equipment_type_option = st.radio(
                            "업로드된 데이터의 설비 종류 선택 방식",
                            ["파일명에서 추출", "직접 입력"],
                            key="equipment_type_option_upload"  # 고유한 키 추가
                        )
                    with col2:
                        if equipment_type_option == "파일명에서 추출":
                            extracted_equipment_display = st.text_input("추출된 설비 종류", value=extracted_equipment_type, key="extracted_equipment", disabled=True)
                            temp_equipment_type = extracted_equipment_type
                        else:
                            input_equipment_type = st.text_input("설비 종류 직접 입력", placeholder="예: 펌프, 컴프레서, 모터 등", key="upload_equipment_direct")
                            temp_equipment_type = input_equipment_type if input_equipment_type else "장비"
                    
                    # Sensor type
                    col1, col2 = st.columns(2)
                    with col1:
                        sensor_type_option = st.radio(
                            "업로드된 데이터의 센서 종류 선택 방식",
                            ["기본 센서 선택", "직접 입력"], 
                            key="sensor_type_option_upload"
                        )
                    with col2:
                        if sensor_type_option == "기본 센서 선택":
                            # 업로드된 파일의 헤더를 읽어 숫자형 컬럼을 표시
                            try:
                                # 파일 포인터 위치 저장
                                current_position = uploaded_file.tell()
                                # 파일 포인터 리셋
                                uploaded_file.seek(0)
                                
                                # 헤더만 읽기
                                df_header = pd.read_csv(uploaded_file, nrows=5)
                                
                                # 파일 포인터 복원
                                uploaded_file.seek(current_position)
                                
                                # 숫자형 컬럼 찾기
                                numeric_columns = df_header.select_dtypes(include=['number']).columns.tolist()
                                # id와 timestamp 제외
                                numeric_columns = [col for col in numeric_columns if col != 'id' and col != 'timestamp']
                                
                                if numeric_columns:
                                    temp_sensor_type = st.selectbox(
                                        "파일의 센서 컬럼 선택", 
                                        numeric_columns, 
                                        key="upload_sensor_type"
                                    )
                                else:
                                    st.warning("파일에서 숫자형 컬럼을 찾을 수 없습니다.")
                                    temp_sensor_type = st.text_input("센서 이름 직접 입력", value="value", key="upload_sensor_fallback")
                            except Exception as e:
                                st.error(f"파일 헤더 읽기 오류: {str(e)}")
                                temp_sensor_type = "value"
                        else:
                            temp_sensor_type = st.text_input("센서 종류 직접 입력", placeholder="예: 온도센서, 압력센서 등", key="upload_sensor_direct")
                    
                    # 장비/센서 설정 적용 버튼
                    if st.button("장비/센서 설정 적용", key="apply_settings_button"):
                        st.session_state.equipment_type = temp_equipment_type
                        st.session_state.sensor_type = temp_sensor_type
                        st.success(f"설비 종류 '{temp_equipment_type}'와 센서 종류 '{temp_sensor_type}'가 적용되었습니다.")
                        # 세션 상태에 적용 완료 표시
                        st.session_state.settings_applied = True
                    
                    # 메모리 옵션에 따라 데이터 로드
                    if memory_option == "샘플링하여 메모리 절약":
                        # 파일의 총 행 수 확인
                        df_temp = pd.read_csv(uploaded_file, nrows=2)
                        uploaded_file.seek(0)  # 파일 포인터 리셋
                        
                        # 파일 크기로 대략적인 행 수 추정
                        file_size = uploaded_file.size
                        row_size = file_size / 2  # 2개 행의 평균 크기
                        estimated_rows = int(file_size / row_size)
                        
                        if estimated_rows > max_memory_points:
                            # 적절한 샘플링 비율 계산
                            sampling_ratio = max_memory_points / estimated_rows
                            df_upload = pd.read_csv(uploaded_file, skiprows=lambda i: i > 0 and np.random.random() > sampling_ratio)
                            # timestamp 기준으로 정렬
                            if 'timestamp' in df_upload.columns:
                                df_upload = df_upload.sort_values('timestamp')
                            st.info(f"대용량 파일을 감지했습니다. 약 {len(df_upload):,}개의 행을 샘플링한 후 timestamp 기준으로 정렬했습니다 (원본: 약 {estimated_rows:,}개 행).")
                        else:
                            df_upload = pd.read_csv(uploaded_file)
                    else:
                        # 모든 데이터 로드
                        df_upload = pd.read_csv(uploaded_file)
                        # timestamp 기준으로 정렬
                        if 'timestamp' in df_upload.columns:
                            df_upload = df_upload.sort_values('timestamp')
                    
                    # 필수 컬럼 확인 및 datetime 컬럼 감지
                    required_columns = ['id']
                    datetime_columns = []
                    
                    # timestamp 컬럼 이름을 찾기 위한 일반적인 패턴
                    timestamp_patterns = ['timestamp', 'date', 'time', 'datetime', 'dt', 'created_at', 'modified_at', '시간', '날짜']
                    
                    # 데이터 타입 확인 및 datetime 컬럼 찾기
                    for col in df_upload.columns:
                        # 컬럼 이름이 timestamp 패턴과 일치하는지 확인
                        is_timestamp_name = any(pattern.lower() in col.lower() for pattern in timestamp_patterns)
                        
                        # datetime으로 변환 가능한지 확인
                        try:
                            if df_upload[col].dtype == 'object':
                                # 첫 몇 개 행만 시도해서 datetime으로 변환 가능한지 테스트
                                test_result = pd.to_datetime(df_upload[col].head(), errors='coerce')
                                if not test_result.isna().all():  # 모두 NaN이 아니면 변환 가능
                                    datetime_columns.append((col, is_timestamp_name))
                            elif pd.api.types.is_datetime64_any_dtype(df_upload[col]):
                                # 이미 datetime 타입인 경우
                                datetime_columns.append((col, is_timestamp_name))
                        except:
                            pass  # 변환할 수 없는 경우 무시
                    
                    # datetime 컬럼이 발견되었을 경우
                    if datetime_columns:
                        # timestamp 패턴과 일치하는 컬럼을 우선적으로 선택
                        timestamp_cols = [col for col, is_timestamp in datetime_columns if is_timestamp]
                        if timestamp_cols:
                            timestamp_col = timestamp_cols[0]
                        else:
                            # 패턴과 일치하는 컬럼이 없으면 첫 번째 datetime 컬럼 사용
                            timestamp_col = datetime_columns[0][0]
                        
                        # 기존 timestamp 컬럼이 있으면 이름을 'timestamp'로 통일
                        if timestamp_col != 'timestamp':
                            df_upload = df_upload.rename(columns={timestamp_col: 'timestamp'})
                            st.info(f"'{timestamp_col}' 컬럼을 timestamp로 사용합니다.")
                        
                        # datetime으로 변환
                        if df_upload['timestamp'].dtype != 'datetime64[ns]':
                            df_upload['timestamp'] = pd.to_datetime(df_upload['timestamp'], errors='coerce')
                            # 변환 불가능한 날짜가 있으면 경고
                            if df_upload['timestamp'].isna().any():
                                invalid_count = df_upload['timestamp'].isna().sum()
                                st.warning(f"일부 날짜/시간 값({invalid_count}개)을 변환할 수 없습니다. 이 행들은 분석에서 제외될 수 있습니다.")
                        
                        # timestamp 기준으로 정렬
                        df_upload = df_upload.sort_values('timestamp')
                    else:
                        # datetime 컬럼이 없는 경우 인덱스를 기반으로 timestamp 생성
                        st.warning("날짜/시간 컬럼을 찾을 수 없습니다. 인덱스를 기반으로 timestamp를 생성합니다.")
                        df_upload['timestamp'] = pd.date_range(start=datetime.now(), periods=len(df_upload), freq='S')
                    
                    # id 컬럼이 없는 경우 생성
                    if 'id' not in df_upload.columns:
                        st.warning("'id' 컬럼이 없습니다. 인덱스를 기반으로 id를 생성합니다.")
                        df_upload['id'] = range(1, len(df_upload) + 1)
                    
                    # 현재 선택된 설정을 적용
                    st.session_state.equipment_type = temp_equipment_type
                    sensor_type = temp_sensor_type
                    
                    # equipment_type 컬럼 제거 (필요하면)
                    if 'equipment_type' in df_upload.columns:
                        # equipment_type 정보 세션에 저장
                        st.session_state.equipment_type = df_upload['equipment_type'].iloc[0]
                        # 컬럼 제거
                        df_upload = df_upload.drop(columns=['equipment_type'])
                    
                    # sensor_type 설정 (사용자가 선택한 컬럼 또는 'value' 컬럼)
                    if "settings_applied" in st.session_state and st.session_state.settings_applied:
                        # 사용자가 설정 적용 버튼을 눌렀을 경우, 이미 저장된 sensor_type 값 사용
                        sensor_type = st.session_state.sensor_type
                    else:
                        # 설정이 적용되지 않은 경우 temp_sensor_type 사용
                        sensor_type = temp_sensor_type
                    
                    if sensor_type in df_upload.columns:
                        # 이미 선택한 컬럼이 데이터에 있는 경우
                        st.session_state.sensor_type = sensor_type
                        # 기본 센서 선택 방식에서 선택한 컬럼을 분석 데이터로 사용
                        if sensor_type_option == "기본 센서 선택" and sensor_type != "value":
                            # 다른 모든 숫자형 컬럼 제외하고 선택한 컬럼만 유지
                            numeric_columns = df_upload.select_dtypes(include=['number']).columns.tolist()
                            columns_to_drop = [col for col in numeric_columns if col != 'id' and col != 'timestamp' and col != sensor_type]
                            if columns_to_drop:
                                # 선택한 컬럼을 제외한 모든 숫자형 컬럼 제거
                                df_upload = df_upload.drop(columns=columns_to_drop)
                                st.info(f"'{sensor_type}' 컬럼만 분석 데이터로 사용합니다. 다른 숫자형 컬럼은 제거되었습니다.")
                    elif 'value' in df_upload.columns and sensor_type != 'value':
                        # 'value' 컬럼이 있고 사용자가 다른 이름을 지정한 경우 이름 변경
                        df_upload = df_upload.rename(columns={'value': sensor_type})
                        st.session_state.sensor_type = sensor_type
                    else:
                        # 숫자형 컬럼 찾기
                        numeric_columns = df_upload.select_dtypes(include=['number']).columns.tolist()
                        numeric_columns = [col for col in numeric_columns if col != 'id' and col != 'timestamp']
                        
                        if numeric_columns:
                            # 기본 센서 선택 방식에서 사용자가 선택한 컬럼과 실제 컬럼 이름이 다를 수 있음
                            if sensor_type_option == "기본 센서 선택" and sensor_type in numeric_columns:
                                # 선택한 컬럼을 그대로 사용
                                st.session_state.sensor_type = sensor_type
                            else:
                                # 첫 번째 숫자형 컬럼을 센서 컬럼으로 사용하고 이름 변경
                                first_numeric_col = numeric_columns[0]
                                if sensor_type != first_numeric_col:
                                    df_upload = df_upload.rename(columns={first_numeric_col: sensor_type})
                                    st.session_state.sensor_type = sensor_type
                        else:
                            st.error("업로드된 파일에 적합한 숫자형 컬럼이 없습니다.")
                            return
                    
                    st.success(f"파일을 성공적으로 업로드했습니다. 총 {len(df_upload):,}개의 레코드가 로드되었습니다.")
                    st.session_state.df = df_upload
                    
                    # AI 분석 및 시각화 세션 상태 초기화
                    reset_all_ai_session_states()
                    
                    st.session_state.data_generated = True
                    
                    # 파일 업로드 후 폰트 강제 재적용
                    if "custom_font_applied" in st.session_state:
                        st.session_state.custom_font_applied = False
                    load_iot_font_css()
                except Exception as e:
                    st.error(f"파일 업로드 중 오류가 발생했습니다: {str(e)}")
        
        # 로컬 CSV 파일 목록 표시
        if data_source == "CSV 파일 읽기":
            st.subheader("로컬 파일 목록에서 CSV 파일을 선택하세요.")
            csv_files = st.text_input("CSV 파일 경로 (여러 파일은 쉼표로 구분)", os.path.join(DATA_DIR, "*.csv"))
            
            # 세션 상태 초기화
            if "csv_paths" not in st.session_state:
                st.session_state.csv_paths = []
            if "searched_files" not in st.session_state:
                st.session_state.searched_files = False
                
            search_button = st.button("로컬 파일 검색")
            
            # 1. 버튼을 누르면 검색 수행 및 세션 상태 업데이트
            if search_button:
                try:
                    csv_paths = []
                    for pattern in csv_files.split(','):
                        pattern = pattern.strip()
                        # 패턴이 절대 경로가 아니면 DATA_DIR과 결합
                        if not os.path.isabs(pattern) and not pattern.startswith(DATA_DIR):
                            pattern = os.path.join(DATA_DIR, pattern)
                        found_files = glob.glob(pattern)
                        csv_paths.extend(found_files)
                    
                    # 파일을 수정 시간 기준으로 정렬 (최신 파일이 먼저 오도록)
                    csv_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    
                    st.session_state.csv_paths = csv_paths
                    st.session_state.searched_files = True
                    st.rerun()  # 재실행하여 결과 표시
                except Exception as e:
                    st.error(f"파일 검색 중 오류가 발생했습니다: {str(e)}")
            
            # 2. 검색 결과 표시 (세션 상태 기반)
            if st.session_state.searched_files:
                if st.session_state.csv_paths:
                    selected_file = st.selectbox(
                        "로드할 CSV 파일 선택", 
                        st.session_state.csv_paths,
                        format_func=lambda x: f"{os.path.basename(x)} ({os.path.getsize(x) / (1024*1024):.1f} MB)"
                    )
                    
                    # 파일 이름에서 equipment_type 추출 시도
                    filename = os.path.basename(selected_file)
                    try:
                        parts = filename.split('_')
                        if len(parts) >= 2 and parts[0] == 'iot':
                            extracted_equipment_type = parts[1]
                        else:
                            extracted_equipment_type = "장비"
                    except:
                        extracted_equipment_type = "장비"
                    
                    # Equipment type selection for local files
                    col1, col2 = st.columns(2)
                    with col1:
                        equipment_type_option = st.radio(
                            "로컬 데이터의 설비 종류 선택 방식",
                            ["파일명에서 추출", "직접 입력"],
                            key="equipment_type_option_local"
                        )
                    with col2:
                        if equipment_type_option == "파일명에서 추출":
                            extracted_equipment_display = st.text_input("추출된 설비 종류", value=extracted_equipment_type, key="local_extracted_equipment", disabled=True)
                            temp_equipment_type = extracted_equipment_type
                        else:
                            input_equipment_type = st.text_input("설비 종류 직접 입력", placeholder="예: 펌프, 컴프레서, 모터 등", key="local_equipment_direct")
                            temp_equipment_type = input_equipment_type if input_equipment_type else "장비"
                    
                    # Sensor type selection for local files
                    col1, col2 = st.columns(2)
                    with col1:
                        sensor_type_option = st.radio(
                            "로컬 데이터의 센서 종류 선택 방식",
                            ["기본 센서 선택", "직접 입력"],
                            key="local_sensor_option"
                        )
                    with col2:
                        if sensor_type_option == "기본 센서 선택":
                            # 선택된 CSV 파일의 헤더를 읽어 숫자형 컬럼을 표시
                            try:
                                # 선택된 파일의 헤더만 읽기
                                df_header = pd.read_csv(selected_file, nrows=5)
                                # 숫자형 컬럼 찾기
                                numeric_columns = df_header.select_dtypes(include=['number']).columns.tolist()
                                # id와 timestamp 제외
                                numeric_columns = [col for col in numeric_columns if col != 'id' and col != 'timestamp']
                                
                                if numeric_columns:
                                    temp_sensor_type = st.selectbox(
                                        "파일의 센서 컬럼 선택", 
                                        numeric_columns, 
                                        key="local_sensor_type"
                                    )
                                else:
                                    st.warning("파일에서 숫자형 컬럼을 찾을 수 없습니다.")
                                    temp_sensor_type = st.text_input("센서 이름 직접 입력", value="value", key="local_sensor_fallback")
                            except Exception as e:
                                st.error(f"파일 헤더 읽기 오류: {str(e)}")
                                temp_sensor_type = "value"
                        else:
                            temp_sensor_type = st.text_input("센서 종류 직접 입력", placeholder="예: 온도센서, 압력센서 등", key="local_sensor_direct")
                    
                    # 장비/센서 설정 정보 메시지
                    st.info(f"파일을 로드하면 설비 종류 '{temp_equipment_type}'와 센서 종류 '{temp_sensor_type}'가 적용됩니다.")
                    
                    # 파일 로드 버튼
                    if st.button(f"'{os.path.basename(selected_file)}' 로드"):
                        try:
                            # 파일 이름 저장
                            filename = os.path.basename(selected_file)
                            st.session_state.current_filename = filename
                            
                            # 메모리 옵션에 따라 데이터 로드
                            if memory_option == "샘플링하여 메모리 절약":
                                file_size = os.path.getsize(selected_file)
                                # 샘플 행으로 평균 행 크기 추정
                                df_temp = pd.read_csv(selected_file, nrows=1000)
                                avg_row_size = file_size / len(df_temp) if len(df_temp) > 0 else 100
                                estimated_rows = int(file_size / avg_row_size)
                                
                                if estimated_rows > max_memory_points:
                                    sampling_ratio = max_memory_points / estimated_rows
                                    df_local = pd.read_csv(selected_file, skiprows=lambda i: i > 0 and np.random.random() > sampling_ratio)
                                    # timestamp 기준으로 정렬
                                    if 'timestamp' in df_local.columns:
                                        df_local = df_local.sort_values('timestamp')
                                    st.info(f"대용량 파일을 감지했습니다. 약 {len(df_local):,}개의 행을 샘플링한 후 timestamp 기준으로 정렬했습니다 (원본: 약 {estimated_rows:,}개 행).")
                                else:
                                    df_local = pd.read_csv(selected_file)
                                    # timestamp 기준으로 정렬
                                    if 'timestamp' in df_local.columns:
                                        df_local = df_local.sort_values('timestamp')
                            else:
                                df_local = pd.read_csv(selected_file)
                                # timestamp 기준으로 정렬
                                if 'timestamp' in df_local.columns:
                                    df_local = df_local.sort_values('timestamp')
                            
                            # 필수 컬럼 확인
                            required_columns = ['id']
                            datetime_columns = []
                            
                            # timestamp 컬럼 이름을 찾기 위한 일반적인 패턴
                            timestamp_patterns = ['timestamp', 'date', 'time', 'datetime', 'dt', 'created_at', 'modified_at', '시간', '날짜']
                            
                            # 데이터 타입 확인 및 datetime 컬럼 찾기
                            for col in df_local.columns:
                                # 컬럼 이름이 timestamp 패턴과 일치하는지 확인
                                is_timestamp_name = any(pattern.lower() in col.lower() for pattern in timestamp_patterns)
                                
                                # datetime으로 변환 가능한지 확인
                                try:
                                    if df_local[col].dtype == 'object':
                                        # 첫 몇 개 행만 시도해서 datetime으로 변환 가능한지 테스트
                                        test_result = pd.to_datetime(df_local[col].head(), errors='coerce')
                                        if not test_result.isna().all():  # 모두 NaN이 아니면 변환 가능
                                            datetime_columns.append((col, is_timestamp_name))
                                    elif pd.api.types.is_datetime64_any_dtype(df_local[col]):
                                        # 이미 datetime 타입인 경우
                                        datetime_columns.append((col, is_timestamp_name))
                                except:
                                    pass  # 변환할 수 없는 경우 무시
                            
                            # datetime 컬럼이 발견되었을 경우
                            if datetime_columns:
                                # timestamp 패턴과 일치하는 컬럼을 우선적으로 선택
                                timestamp_cols = [col for col, is_timestamp in datetime_columns if is_timestamp]
                                if timestamp_cols:
                                    timestamp_col = timestamp_cols[0]
                                else:
                                    # 패턴과 일치하는 컬럼이 없으면 첫 번째 datetime 컬럼 사용
                                    timestamp_col = datetime_columns[0][0]
                                
                                # 기존 timestamp 컬럼이 있으면 이름을 'timestamp'로 통일
                                if timestamp_col != 'timestamp':
                                    df_local = df_local.rename(columns={timestamp_col: 'timestamp'})
                                    st.info(f"'{timestamp_col}' 컬럼을 timestamp로 사용합니다.")
                                
                                # datetime으로 변환
                                if df_local['timestamp'].dtype != 'datetime64[ns]':
                                    df_local['timestamp'] = pd.to_datetime(df_local['timestamp'], errors='coerce')
                                    # 변환 불가능한 날짜가 있으면 경고
                                    if df_local['timestamp'].isna().any():
                                        invalid_count = df_local['timestamp'].isna().sum()
                                        st.warning(f"일부 날짜/시간 값({invalid_count}개)을 변환할 수 없습니다. 이 행들은 분석에서 제외될 수 있습니다.")
                                
                                # timestamp 기준으로 정렬
                                df_local = df_local.sort_values('timestamp')
                            else:
                                # datetime 컬럼이 없는 경우 인덱스를 기반으로 timestamp 생성
                                st.warning("날짜/시간 컬럼을 찾을 수 없습니다. 인덱스를 기반으로 timestamp를 생성합니다.")
                                df_local['timestamp'] = pd.date_range(start=datetime.now(), periods=len(df_local), freq='S')
                            
                            # id 컬럼이 없는 경우 생성
                            if 'id' not in df_local.columns:
                                st.warning("'id' 컬럼이 없습니다. 인덱스를 기반으로 id를 생성합니다.")
                                df_local['id'] = range(1, len(df_local) + 1)
                            
                            # 현재 선택된 설정을 적용
                            st.session_state.equipment_type = temp_equipment_type
                            sensor_type = temp_sensor_type
                            
                            # equipment_type 컬럼 제거 (필요하면)
                            if 'equipment_type' in df_local.columns:
                                # equipment_type 정보 세션에 저장
                                st.session_state.equipment_type = df_local['equipment_type'].iloc[0]
                                # 컬럼 제거
                                df_local = df_local.drop(columns=['equipment_type'])
                            
                            if sensor_type in df_local.columns:
                                # 이미 선택한 컬럼이 데이터에 있는 경우 그대로 사용
                                st.session_state.sensor_type = sensor_type
                                # 기본 센서 선택 방식에서 선택한 컬럼을 분석 데이터로 사용
                                if sensor_type_option == "기본 센서 선택" and sensor_type != "value":
                                    # 다른 모든 숫자형 컬럼 제외하고 선택한 컬럼만 유지
                                    numeric_columns = df_local.select_dtypes(include=['number']).columns.tolist()
                                    columns_to_drop = [col for col in numeric_columns if col != 'id' and col != 'timestamp' and col != sensor_type]
                                    if columns_to_drop:
                                        # 선택한 컬럼을 제외한 모든 숫자형 컬럼 제거
                                        df_local = df_local.drop(columns=columns_to_drop)
                                        st.info(f"'{sensor_type}' 컬럼만 분석 데이터로 사용합니다. 다른 숫자형 컬럼은 제거되었습니다.")
                            elif 'value' in df_local.columns and sensor_type != 'value':
                                # 'value' 컬럼이 있고 사용자가 다른 이름을 지정한 경우 이름 변경
                                df_local = df_local.rename(columns={'value': sensor_type})
                                st.session_state.sensor_type = sensor_type
                            else:
                                # 숫자형 컬럼 찾기
                                numeric_columns = df_local.select_dtypes(include=['number']).columns.tolist()
                                numeric_columns = [col for col in numeric_columns if col != 'id' and col != 'timestamp']
                                
                                if numeric_columns:
                                    # 기본 센서 선택 방식에서 사용자가 선택한 컬럼과 실제 컬럼 이름이 다를 수 있음
                                    if sensor_type_option == "기본 센서 선택" and sensor_type in numeric_columns:
                                        # 선택한 컬럼을 그대로 사용
                                        st.session_state.sensor_type = sensor_type
                                    else:
                                        # 첫 번째 숫자형 컬럼을 센서 컬럼으로 사용하고 이름 변경
                                        first_numeric_col = numeric_columns[0]
                                        if sensor_type != first_numeric_col:
                                            df_local = df_local.rename(columns={first_numeric_col: sensor_type})
                                        st.session_state.sensor_type = sensor_type
                                else:
                                    st.error("로컬 파일에 적합한 숫자형 컬럼이 없습니다.")
                                return
                        
                            st.success(f"로컬 파일을 성공적으로 로드했습니다. 총 {len(df_local):,}개의 레코드가 로드되었습니다.")
                            st.session_state.df = df_local
                            
                            # AI 분석 및 시각화 세션 상태 초기화
                            reset_all_ai_session_states()
                            
                            st.session_state.data_generated = True
                            
                            # 로컬 파일 로드 후 폰트 강제 재적용
                            if "custom_font_applied" in st.session_state:
                                st.session_state.custom_font_applied = False
                            load_iot_font_css()
                        except Exception as e:
                            st.error(f"로컬 파일 로드 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.warning("지정한 패턴과 일치하는 CSV 파일을 찾을 수 없습니다.")
                    
                # 검색 결과 초기화 버튼
                if st.session_state.searched_files and st.button("검색 결과 초기화"):
                    st.session_state.searched_files = False
                    st.session_state.csv_paths = []
                    st.rerun()
        
        # 데이터 생성
        if data_source in ["새로 생성", "생성 후 파일 저장"]:
            # Data generation parameters
            total_records = st.number_input("생성할 총 레코드 수", min_value=1000, max_value=3000000, value=100000, step=1000)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("시작 날짜", datetime(2025, 1, 1))
            with col2:
                end_date = st.date_input("종료 날짜", datetime(2025, 12, 31))
            
            # Equipment type
            col1, col2 = st.columns(2)
            with col1:
                equipment_type_option = st.radio(
                    "설비 종류 선택 방식",
                    ["기본 설비 선택", "직접 입력"]
                )
            with col2:
                if equipment_type_option == "기본 설비 선택":
                    equipment_type = st.selectbox("설비 종류", ["펌프", "컴프레서", "모터", "팬", "보일러"])
                else:
                    equipment_type = st.text_input("설비 종류 직접 입력", placeholder="예: 열교환기, 증발기 등")
            
            # Sensor type
            col1, col2 = st.columns(2)
            with col1:
                sensor_type_option = st.radio(
                    "센서 종류 선택 방식",
                    ["기본 센서 선택", "직접 입력"]
                )
            with col2:
                if sensor_type_option == "기본 센서 선택":
                    sensor_type = st.selectbox("센서 종류", ["온도", "압력", "전류", "전압", "회전수", "위치", "기타"])
                else:
                    sensor_type = st.text_input("센서 종류 직접 입력", placeholder="예: 온도센서, 압력센서 등")

            # Sensor value settings
            st.subheader("센서 값 설정")
            
            col1, col2 = st.columns(2)
            with col1:
                min_value = st.number_input("최소값", value=20.0, step=1.0)
            with col2:
                max_value = st.number_input("최대값", value=80.0, step=1.0)
            
            # Pattern settings
            st.subheader("패턴 설정")
            
            pattern_type = st.selectbox(
                "패턴 유형", 
                ["정상", "점진적 증가", "점진적 감소", "주기적 변동", "랜덤 스파이크", "계절적 변동", "운전/정지 주기"]
            )
            
            noise_level = st.slider("노이즈 수준", 0.0, 3.0, 0.1, 0.01, 
                                     help="노이즈 수준이 높을수록 데이터가 더 불규칙적이고 변동성이 높아집니다.")
            
            # 운전/정지 주기 패턴이 선택된 경우 추가 옵션 표시
            if pattern_type == "운전/정지 주기":
                st.subheader("운전/정지 주기 설정")
                col1, col2 = st.columns(2)
                with col1:
                    operation_minutes = st.number_input("운전 시간 (분)", min_value=1, max_value=1440, value=60)
                with col2:
                    shutdown_minutes = st.number_input("정지 시간 (분)", min_value=1, max_value=1440, value=30)
            else:
                # 다른 패턴 유형인 경우 기본값 설정
                operation_minutes = 60
                shutdown_minutes = 30
            
            # Failure simulation
            simulate_failures = st.checkbox("이상 시뮬레이션")
            
            if simulate_failures:
                col1, col2 = st.columns(2)
                with col1:
                    failure_count = st.number_input("이상 횟수", min_value=1, max_value=50, value=5)
                with col2:
                    failure_duration = st.number_input("평균 이상 지속시간 (시간)", min_value=1, max_value=48, value=6)
            else:
                failure_count = 0
                failure_duration = 0
            
            # 파일 저장 옵션
            if data_source == "생성 후 파일 저장":
                save_dir = st.text_input("저장 디렉토리", DATA_DIR) 
                # 파일 이름에 equipment_type 포함
                save_file = f"iot_{equipment_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                save_path = os.path.join(save_dir, save_file)
            
            # Generate button
            generate_btn = st.button("데이터 생성")
            
            if generate_btn:
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("데이터 생성 중...")
                
                # Simulate progress
                for i in range(0, 50):
                    progress_bar.progress(i)
                    time.sleep(0.01)
                
                try:
                    # Convert dates to datetime
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    
                    progress_bar.progress(50)
                    
                    # Generate data using the data_generator function and ensure it's sorted by timestamp
                    df = generate_iot_data(
                        total_records=total_records,
                        start_date=start_datetime,
                        end_date=end_datetime,
                        equipment_type=equipment_type,
                        min_value=min_value,
                        max_value=max_value,
                        pattern_type=pattern_type,
                        noise_level=noise_level,
                        simulate_failures=simulate_failures,
                        failure_count=failure_count,
                        failure_duration=failure_duration,
                        operation_minutes=operation_minutes,
                        shutdown_minutes=shutdown_minutes,
                        sensor_type=sensor_type
                    )
                    
                    progress_bar.progress(80)
                    
                    # CSV로 저장
                    if data_source == "생성 후 파일 저장":
                        try:
                            # 원본 데이터 저장
                            os.makedirs(os.path.dirname(save_path), exist_ok=True)
                            df.to_csv(save_path, index=False)
                            status_text.text(f"데이터 생성 완료! 파일 저장됨: {save_path}")
                            
                            # 메모리 관리 옵션 적용
                            if memory_option == "샘플링하여 메모리 절약" and len(df) > max_memory_points:
                                # 데이터 샘플링
                                df_memory = df.sample(max_memory_points)
                                st.info(f"메모리 절약을 위해 {max_memory_points:,}개의 데이터 포인트를 샘플링하여 분석에 사용합니다. 모든 데이터는 '{save_path}'에 저장되었습니다.")
                                # 세션 상태 업데이트
                                st.session_state.df = df_memory
                            else:
                                # 모든 데이터 메모리에 로드
                                st.session_state.df = df
                        except Exception as e:
                            status_text.error(f"파일 저장 중 오류 발생: {str(e)}")
                            status_text.text("데이터 생성은 완료되었으나 파일 저장에 실패했습니다.")
                            # 파일 저장에 실패해도 데이터는 메모리에 로드
                            st.session_state.df = df
                    else:
                        status_text.text("데이터 생성 완료!")
                        
                        # 메모리 관리 옵션 적용
                        if memory_option == "샘플링하여 메모리 절약" and len(df) > max_memory_points:
                            # 데이터 샘플링
                            df_memory = df.sample(max_memory_points)
                            st.info(f"메모리 절약을 위해 {max_memory_points:,}개의 데이터 포인트를 샘플링하여 분석에 사용합니다.")
                            # 세션 상태 업데이트
                            st.session_state.df = df_memory
                        else:
                            # 모든 데이터 메모리에 로드
                            st.session_state.df = df
                    
                    # AI 분석 및 시각화 세션 상태 초기화
                    reset_all_ai_session_states()
                    
                    # 데이터 생성 완료 표시
                    st.session_state.data_generated = True
                    
                    progress_bar.progress(100)
                    time.sleep(1)
                    status_text.empty()
                    progress_bar.empty()
                    
                    # 데이터 생성 후 폰트 강제 재적용
                    if "custom_font_applied" in st.session_state:
                        st.session_state.custom_font_applied = False
                    load_iot_font_css()
                    
                except Exception as e:
                    status_text.error(f"데이터 생성 중 오류 발생: {str(e)}")
                    progress_bar.empty()
    
    # Display and visualization after data generation
    if st.session_state.data_generated and "df" in st.session_state and st.session_state.df is not None:
        df = st.session_state.df
        
        # 데이터 처리 후 폰트 재적용
        load_iot_font_css()
        
        # 성능 개선 팁
        with st.sidebar.expander("💡 성능 향상 팁", expanded=False):
            st.markdown("""
            **앱 성능 최적화 방법:**
            - Record 수를 줄이면 성능이 향상됩니다.
            - 대용량 데이터(300만 건 이상)의 경우 샘플링하여 메모리를 절약하세요.
            - 복잡한 차트를 여러 개 열어두면 브라우저 성능이 저하될 수 있습니다.
            - 필요 없는 차트는 닫아서 메모리를 확보하세요.
            """)
        
        # timestamp로 정렬 확인
        if 'timestamp' in df.columns and not df['timestamp'].equals(df['timestamp'].sort_values()):
            df = df.sort_values('timestamp')
            st.info("데이터를 timestamp 기준으로 재정렬했습니다.")
            
        # 데이터 전처리 및 캐싱
        with st.spinner('데이터 처리 중...'):
            df_processed, stats = process_dataframe(df)
        
        # Display current equipment type
        current_equipment_type = get_equipment_type()
        st.info(f"현재 데이터셋 장비 유형: {current_equipment_type}, 현재 센서 유형: {get_sensor_type()}")
        
        # 결측값 처리 옵션 (사이드바)
        with st.sidebar.expander("결측값(Null) 처리 옵션", expanded=False):
            null_count = stats.get("null_count", 0)
            total_count = stats.get("total_count", len(df))
            
            if null_count > 0:
                st.warning(f"선택한 센서 컬럼에 {null_count:,}개의 결측값이 있습니다. ({null_count/total_count:.1%})")
                
                null_handling_options = {
                    "remove": "결측값이 있는 행 제거",
                    "fill_mean": "평균값으로 대체",
                    "fill_median": "중앙값으로 대체",
                    "fill_zero": "0으로 대체",
                    "fill_previous": "인접한 값으로 대체",
                    "interpolation": "선형 보간법으로 대체"
                }
                
                selected_method = st.radio(
                    "결측값 처리 방법 선택",
                    options=list(null_handling_options.keys()),
                    format_func=lambda x: null_handling_options.get(x),
                    index=list(null_handling_options.keys()).index(st.session_state.get("null_handling_method", "remove"))
                )
                
                if st.button("결측값 처리 방법 적용"):
                    st.session_state.null_handling_method = selected_method
                    st.rerun()  # 페이지 재실행하여 변경사항 적용
            else:
                st.success("선택한 센서 컬럼에 결측값이 없습니다.")
        
        # # Display data sample
        # st.header("데이터 샘플")
        
        # 세션 상태에 sample_expander_open이 없으면 초기화
        if "sample_expander_open" not in st.session_state:
            st.session_state.sample_expander_open = False
        
        # 표시할 샘플 수 설정을 위한 세션 상태
        if "sample_rows" not in st.session_state:
            st.session_state.sample_rows = 10
        
        # 데이터 샘플 컨트롤
        col1, col2 = st.columns([3, 1])
        with col1:
            # Display data sample
            st.header("데이터 샘플")
            st.caption("원본 데이터 샘플을 보여줍니다.")
        with col2:
            sample_rows = st.selectbox(
                "표시 행 수", 
                options=[10, 20, 50, 100, 200], 
                index=0, 
                key="sample_rows_select",
                on_change=lambda: setattr(st.session_state, "sample_rows", st.session_state.sample_rows_select)
            )
        
        # 세션 상태에 따라 데이터 샘플 표시
        expander_open = st.expander("데이터 샘플 보기", expanded=st.session_state.sample_expander_open)
        
        # expander 상태 변경 감지 및 세션 상태 업데이트
        if expander_open:
            st.session_state.sample_expander_open = True
        
        with expander_open:
            # 스크롤 가능한 컨테이너에 데이터프레임 표시
            container_height = min(400, 35 + st.session_state.sample_rows * 35)  # 행 수에 비례한 높이 (최대 400px)
            with st.container():
                st.markdown(f"""
                <style>
                    .stDataFrame {{
                        height: {container_height}px;
                        overflow-y: auto;
                    }}
                </style>
                """, unsafe_allow_html=True)
                st.dataframe(df.head(st.session_state.sample_rows))
            
            # 전체 데이터 크기 정보 표시
            total_rows = len(df)
            st.caption(f"전체 데이터: {total_rows:,}개 행 중 {st.session_state.sample_rows}개 표시 ({st.session_state.sample_rows/total_rows:.1%})")
            
            if st.button("전체 데이터 보기", key="view_full_data"):
                with st.spinner("전체 데이터를 로드 중입니다..."):
                    # 페이지네이션 효과로 전체 데이터 표시
                    # 원본 데이터를 1000행 단위로 페이지네이션
                    st.session_state.show_full_data = True
                    st.session_state.data_page = 1
                    st.rerun()
        
            if "show_full_data" in st.session_state and st.session_state.show_full_data:
                page_size = 1000
                total_pages = (total_rows + page_size - 1) // page_size
                
                # 페이지 선택기
                page = st.selectbox(
                    f"페이지 (총 {total_pages}페이지)", 
                    options=range(1, total_pages + 1),
                    index=st.session_state.data_page - 1,
                    key="data_page_select"
                )
                st.session_state.data_page = page
                
                # 선택된 페이지의 데이터 표시
                start_idx = (page - 1) * page_size
                end_idx = min(start_idx + page_size, total_rows)
                
                st.markdown(f"**{start_idx+1:,}번째부터 {end_idx:,}번째 행 ({end_idx-start_idx:,}행)**")
                st.dataframe(df.iloc[start_idx:end_idx], height=500)
        
        # Summary statistics (캐시된 통계 사용)
        st.header("데이터 요약")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 레코드 수", f"{stats['count']:,}")
        with col2:
            st.metric("시작 날짜", df['timestamp'].min().strftime('%Y-%m-%d'))
        with col3:
            st.metric("종료 날짜", df['timestamp'].max().strftime('%Y-%m-%d'))
        
        # Data download option
        st.header("데이터 다운로드")
        csv = convert_df_to_csv(df)
        
        # 파일 이름에 equipment_type 포함
        equipment_type_for_filename = get_equipment_type(df)
        download_filename = f'iot_{equipment_type_for_filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="CSV로 다운로드",
                data=csv,
                file_name=download_filename,
                mime='text/csv',
            )
        
        with col2:
            if st.button("로컬에 CSV 저장"):
                success, result = save_df_to_file(df, equipment_type_for_filename)
                if success:
                    st.success(f"파일을 성공적으로 저장했습니다: {result}")
                else:
                    st.error(f"파일 저장 중 오류가 발생했습니다: {result}")
        
        # Visualizations
        st.header("데이터 시각화")
        
        # 시각화 유형 선택 (URL 파라미터에서 받은 값이 있으면 우선 적용)
        viz_options = ["시각화 가이드", "시계열 차트", "히스토그램", "박스 플롯", "히트맵", "일별/시간별 패턴", "이상치 분석", 
                      "주파수 분석(FFT)", "시간-주파수 분석", "트렌드 분석", "상관관계 분석", "분포 비교", "3D 데이터 시각화", 
                      "패턴 클러스터링", "경보 및 임계값 설정", "운전/정지 주기 분석", "종합 인사이트"]
        
        # URL 파라미터에서 가져온 값이 있으면 기본 값으로 설정
        default_viz = "시각화 가이드"
        
        # 1. 버튼에서 선택된 시각화가 있는지 확인
        if "selected_viz_from_button" in st.session_state:
            button_viz = st.session_state.selected_viz_from_button
            
            # 옵션 목록에서 확인
            if button_viz in viz_options:
                default_viz = button_viz
            else:
                # 부분 일치 확인
                for option in viz_options:
                    if button_viz in option or option in button_viz:
                        default_viz = option
                        break
        
        # 2. URL 파라미터 확인 (버튼 선택이 없는 경우)
        elif "selected_viz_from_param" in st.session_state:
            param_viz = st.session_state.selected_viz_from_param
            # 옵션 목록에서 가장 가까운 매칭 찾기
            for option in viz_options:
                if param_viz == option or param_viz in option or option in param_viz:
                    default_viz = option
                    break
        
        # 시각화 유형 선택이 변경될 때 호출되는 콜백 함수
        def on_viz_type_change():
            # 명시적으로 사용자가 변경했을 때만 세션 상태 업데이트
            current_viz = st.session_state.selected_visualization_type
            st.session_state.selected_viz_from_button = current_viz
            # 디버깅 메시지 (필요시 주석 해제)
            print(f"시각화 타입이 '{current_viz}'로 변경되었습니다.")
        
        # 시각화 유형 선택
        viz_type = st.selectbox(
            "시각화 유형",
            viz_options,
            index=viz_options.index(default_viz),
            key="selected_visualization_type",  # 세션 상태 키 추가
            on_change=on_viz_type_change  # 변경 콜백 추가
        )
        
        # Content for different visualization types
        if viz_type == "시각화 가이드":
            render_visualization_guide_explanation()  # 시각화 가이드에 대한 상세 설명 표시
            render_visualization_guide_ui(df_processed)
        elif viz_type == "시계열 차트":
            render_timeseries_ui(df_processed)
        elif viz_type == "히스토그램":
            render_histogram_ui(df_processed, stats)
        elif viz_type == "박스 플롯":
            render_boxplot_ui(df_processed)
        elif viz_type == "히트맵":
            render_heatmap_ui(df_processed)
        elif viz_type == "일별/시간별 패턴":
            render_pattern_ui(df_processed)
        elif viz_type == "이상치 분석":
            render_anomaly_ui(df_processed)
        elif viz_type == "주파수 분석(FFT)":
            render_fft_ui(df_processed)
        elif viz_type == "시간-주파수 분석":
            render_timefreq_ui(df_processed)
        elif viz_type == "트렌드 분석":
            render_trend_ui(df_processed)
        elif viz_type == "상관관계 분석":
            render_correlation_ui(df_processed)
        elif viz_type == "분포 비교":
            render_distribution_ui(df_processed)
        elif viz_type == "3D 데이터 시각화":
            render_threed_ui(df_processed)
        elif viz_type == "패턴 클러스터링":
            render_clustering_ui(df_processed)
        elif viz_type == "경보 및 임계값 설정":
            render_alarm_threshold_ui(df_processed)
        elif viz_type == "운전/정지 주기 분석":
            render_cycle_analysis_ui(df_processed)
        elif viz_type == "종합 인사이트":
            render_insights_ui(df_processed)
    
    # Footer 추가 (항상 표시되도록 함수 마지막에 배치)
    st.markdown("---")
    st.markdown("© 2025 DX-AI IoT Prism | Copyright 2025 DX-AI")

if __name__ == "__main__":
    main() 