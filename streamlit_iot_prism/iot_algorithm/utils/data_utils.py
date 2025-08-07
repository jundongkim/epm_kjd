import pandas as pd
import streamlit as st
import re

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

@st.cache_data
def load_data(file):
    try:
        # 먼저 일반적인 방식으로 CSV 파일 로드
        # 첫 번째 행이 숫자로만 구성된 경우 인덱스로 처리될 수 있으므로 index_col=None으로 설정
        df = pd.read_csv(file, index_col=None)
        
        # Unnamed: 0 열이 있으면 인덱스로 설정하고 제거
        if 'Unnamed: 0' in df.columns:
            # Unnamed: 0 열이 숫자로 구성되어 있는지 확인
            if pd.to_numeric(df['Unnamed: 0'], errors='coerce').notna().all():
                st.info("'Unnamed: 0' 열을 인덱스로 설정하고 제거했습니다.")
                df = df.set_index('Unnamed: 0')
                df.index.name = None  # 인덱스 이름 제거
            
        # timestamp 열이 있는지 확인
        timestamp_columns = []
        for col in df.columns:
            # 열 이름에 'time', 'date', 'timestamp' 등이 포함된 경우 확인
            if any(time_word in col.lower() for time_word in ['time', 'date', 'timestamp']):
                # 열의 첫 번째 값이 날짜/시간 형식인지 확인
                if isinstance(df[col].iloc[0], str):
                    # 날짜/시간 패턴 확인 (YYYY-MM-DD 또는 YYYY/MM/DD 형식)
                    date_pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
                    if re.search(date_pattern, str(df[col].iloc[0])):
                        timestamp_columns.append(col)
        
        # 타임스탬프 열을 datetime 타입으로 변환
        for col in timestamp_columns:
            try:
                df[col] = pd.to_datetime(df[col])
                st.info(f"'{col}' 열을 datetime 타입으로 변환했습니다.")
            except Exception as e:
                st.warning(f"'{col}' 열을 datetime 타입으로 변환하지 못했습니다: {e}")
        
        # 모든 열에 대해 데이터 타입 확인 및 출력
        dtypes_info = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            dtypes_info.append(f"{col}: {dtype_str}")
        
        st.info(f"데이터 열 타입: {', '.join(dtypes_info)}")
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None 