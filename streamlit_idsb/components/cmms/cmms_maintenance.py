import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
from datetime import datetime, timedelta

def show_cmms_maintenance():
    """
    CMMS 설비 유지보수 데이터 분석 컴포넌트
    """
    st.title("설비 유지보수 데이터 분석")
    
    # 일일업무일지 데이터 확인
    if "cmms_data" not in st.session_state:
        st.warning("일일업무일지 데이터가 로드되지 않았습니다. 샘플 데이터를 사용합니다.")
    else:
        st.success(f"일일업무일지 데이터 {len(st.session_state.cmms_data)}건이 로드되었습니다.")
    
    # 샘플 데이터 생성
    if 'cmms_maintenance_data' not in st.session_state:
        st.session_state.cmms_maintenance_data = generate_maintenance_data()
    
    # 데이터 필터링 옵션
    with st.expander("데이터 필터링 옵션", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            equipment_types = sorted(st.session_state.cmms_maintenance_data['설비유형'].unique())
            selected_equipment = st.multiselect(
                "설비 유형 선택", 
                options=equipment_types,
                default=equipment_types[:2]
            )
            
        with col2:
            # 기간 선택 (시작일)
            min_date = st.session_state.cmms_maintenance_data['정비일자'].min()
            max_date = st.session_state.cmms_maintenance_data['정비일자'].max()
            start_date = st.date_input(
                "시작일",
                min_date,
                min_value=min_date,
                max_value=max_date
            )
            
        with col3:
            # 기간 선택 (종료일)
            end_date = st.date_input(
                "종료일",
                max_date,
                min_value=min_date,
                max_value=max_date
            )
    
    # 필터링된 데이터
    filtered_data = st.session_state.cmms_maintenance_data[
        (st.session_state.cmms_maintenance_data['설비유형'].isin(selected_equipment)) &
        (st.session_state.cmms_maintenance_data['정비일자'] >= pd.Timestamp(start_date)) &
        (st.session_state.cmms_maintenance_data['정비일자'] <= pd.Timestamp(end_date))
    ]
    
    if filtered_data.empty:
        st.warning("선택한 필터에 맞는 데이터가 없습니다.")
        return
    
    # 주요 지표 요약
    st.subheader("주요 정비 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_repairs = len(filtered_data)
        st.metric("총 정비 건수", f"{total_repairs:,}건")
        
    with col2:
        avg_downtime = filtered_data['정비시간(시간)'].mean()
        st.metric("평균 정비시간", f"{avg_downtime:.2f}시간")
        
    with col3:
        mtbf = calculate_mtbf(filtered_data)
        st.metric("평균 고장간격(MTBF)", f"{mtbf:.2f}일")
        
    with col4:
        mttr = filtered_data['정비시간(시간)'].mean()
        st.metric("평균 정비소요시간(MTTR)", f"{mttr:.2f}시간")
    
    # 그래프 탭
    tab1, tab2, tab3 = st.tabs(["정비 유형 분석", "고장 원인 분석", "정비 시간 추이"])
    
    with tab1:
        st.subheader("정비 유형별 분포")
        
        # 정비 유형별 카운트
        repair_type_counts = filtered_data['정비유형'].value_counts().reset_index()
        repair_type_counts.columns = ['정비유형', '건수']
        
        # 정비 유형별 평균 정비 시간
        repair_type_times = filtered_data.groupby('정비유형')['정비시간(시간)'].mean().reset_index()
        repair_type_times.columns = ['정비유형', '평균정비시간']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                repair_type_counts, 
                values='건수', 
                names='정비유형',
                title="정비 유형별 분포",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.bar(
                repair_type_times,
                x='정비유형',
                y='평균정비시간',
                title="정비 유형별 평균 정비 시간",
                color='정비유형',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("고장 원인 분석")
        
        # 고장 원인별 카운트
        failure_cause_counts = filtered_data['고장원인'].value_counts().reset_index()
        failure_cause_counts.columns = ['고장원인', '건수']
        
        # 설비 유형별 고장 원인 분포
        failure_by_equipment = filtered_data.groupby(['설비유형', '고장원인']).size().reset_index(name='건수')
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                failure_cause_counts,
                x='고장원인',
                y='건수',
                title="고장 원인별 발생 빈도",
                color='고장원인',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.bar(
                failure_by_equipment,
                x='설비유형',
                y='건수',
                color='고장원인',
                title="설비 유형별 고장 원인 분포",
                barmode='stack',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("정비 시간 추이 분석")
        
        # 월별 정비 건수 및 평균 정비 시간
        filtered_data['월'] = filtered_data['정비일자'].dt.to_period('M')
        monthly_stats = filtered_data.groupby('월').agg(
            정비건수=('정비ID', 'count'),
            평균정비시간=('정비시간(시간)', 'mean')
        ).reset_index()
        monthly_stats['월'] = monthly_stats['월'].astype(str)
        
        # 설비 유형별 월간 정비 건수
        monthly_by_equipment = filtered_data.groupby(['월', '설비유형']).size().reset_index(name='건수')
        monthly_by_equipment['월'] = monthly_by_equipment['월'].astype(str)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    x=monthly_stats['월'],
                    y=monthly_stats['정비건수'],
                    name="정비 건수",
                    marker_color='rgba(22, 65, 147, 0.7)'
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(
                    x=monthly_stats['월'],
                    y=monthly_stats['평균정비시간'],
                    name="평균 정비 시간",
                    marker_color='rgba(38, 169, 224, 1)',
                    mode='lines+markers'
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title_text="월별 정비 건수 및 평균 정비 시간",
                xaxis_title="월",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            fig.update_yaxes(title_text="정비 건수", secondary_y=False)
            fig.update_yaxes(title_text="평균 정비 시간 (시간)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.line(
                monthly_by_equipment, 
                x='월', 
                y='건수', 
                color='설비유형',
                title="설비 유형별 월간 정비 건수",
                markers=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # 정비 데이터 테이블
    with st.expander("정비 데이터 테이블", expanded=False):
        st.dataframe(
            filtered_data.sort_values('정비일자', ascending=False),
            use_container_width=True,
            column_config={
                "정비ID": st.column_config.TextColumn("정비 ID"),
                "설비ID": st.column_config.TextColumn("설비 ID"),
                "설비유형": st.column_config.TextColumn("설비 유형"),
                "정비유형": st.column_config.TextColumn("정비 유형"),
                "고장원인": st.column_config.TextColumn("고장 원인"),
                "정비일자": st.column_config.DateColumn("정비 일자"),
                "정비시간(시간)": st.column_config.NumberColumn("정비 시간(시간)", format="%.2f"),
                "비용(만원)": st.column_config.NumberColumn("비용(만원)", format="%d"),
                "담당자": st.column_config.TextColumn("담당자")
            }
        )

def generate_maintenance_data(num_records=200):
    """샘플 정비 데이터 생성"""
    np.random.seed(42)  # 재현성을 위한 시드 설정
    
    # 설비 ID 및 유형
    equipment_types = ['믹서', '코팅기', '압연기', '건조기', '검사기', '포장기']
    equipment_ids = []
    equipment_types_list = []
    
    for equip_type in equipment_types:
        for i in range(1, 6):  # 각 유형별 5개 장비
            equipment_ids.append(f"{equip_type[:1]}{i:02d}")
            equipment_types_list.append(equip_type)
    
    # 정비 유형 및 고장 원인
    maintenance_types = ['예방정비', '사후정비', '예측정비', '개량정비']
    failure_causes = ['기계적마모', '전기적결함', '소프트웨어오류', '작업자오류', '재료불량', '환경요인']
    
    # 담당자
    technicians = ['김기술', '이정비', '박엔지니어', '최기계', '정전기']
    
    # 날짜 생성 (최근 1년)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    
    # 데이터 생성
    maintenance_ids = [f"M{i+1:05d}" for i in range(num_records)]
    equipment_idx = np.random.randint(0, len(equipment_ids), num_records)
    
    data = {
        '정비ID': maintenance_ids,
        '설비ID': [equipment_ids[idx] for idx in equipment_idx],
        '설비유형': [equipment_types_list[idx] for idx in equipment_idx],
        '정비유형': np.random.choice(maintenance_types, num_records, p=[0.4, 0.3, 0.2, 0.1]),
        '고장원인': np.random.choice(failure_causes, num_records),
        '정비일자': np.random.choice(dates, num_records),
        '정비시간(시간)': np.random.exponential(scale=4, size=num_records),
        '비용(만원)': np.random.randint(10, 200, num_records),
        '담당자': np.random.choice(technicians, num_records)
    }
    
    df = pd.DataFrame(data)
    
    # 예방정비는 고장원인이 없음
    df.loc[df['정비유형'] == '예방정비', '고장원인'] = '해당없음'
    
    # 정비 시간 조정 (정비 유형에 따라)
    df.loc[df['정비유형'] == '예방정비', '정비시간(시간)'] *= 0.7
    df.loc[df['정비유형'] == '사후정비', '정비시간(시간)'] *= 1.5
    df.loc[df['정비유형'] == '개량정비', '정비시간(시간)'] *= 2.0
    
    # 날짜를 datetime 형식으로 변환
    df['정비일자'] = pd.to_datetime(df['정비일자'])
    
    # 정비 비용 조정
    df['비용(만원)'] = (df['정비시간(시간)'] * np.random.randint(5, 15, num_records)).astype(int)
    
    return df

def calculate_mtbf(df):
    """
    평균 고장간격(MTBF) 계산
    """
    # 설비별로 정비일자 그룹화
    equipment_failures = df[df['정비유형'] == '사후정비'].groupby('설비ID')['정비일자'].apply(list)
    
    mtbf_values = []
    
    for equip_id, failure_dates in equipment_failures.items():
        if len(failure_dates) > 1:
            # 날짜 정렬
            sorted_dates = sorted(failure_dates)
            
            # 고장 간격 계산 (일 단위)
            intervals = [(sorted_dates[i+1] - sorted_dates[i]).days for i in range(len(sorted_dates)-1)]
            
            if intervals:
                mtbf_values.append(np.mean(intervals))
    
    # 전체 평균 계산
    return np.mean(mtbf_values) if mtbf_values else 0 