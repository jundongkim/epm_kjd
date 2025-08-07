import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
from datetime import datetime, timedelta

def show_cmms_risk_assessment():
    """
    CMMS 설비별 위험도 평가 컴포넌트
    """
    st.title("설비별 위험도 평가")
    
    # 일일업무일지 데이터 확인
    if "cmms_data" not in st.session_state:
        st.warning("일일업무일지 데이터가 로드되지 않았습니다. 샘플 데이터를 사용합니다.")
    else:
        st.success(f"일일업무일지 데이터 {len(st.session_state.cmms_data)}건이 로드되었습니다.")
    
    # 샘플 데이터 생성
    if 'cmms_risk_data' not in st.session_state:
        st.session_state.cmms_risk_data = generate_risk_data()
    
    # 데이터 필터링 옵션
    with st.expander("데이터 필터링 옵션", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            equipment_types = sorted(st.session_state.cmms_risk_data['설비유형'].unique())
            selected_equipment = st.multiselect(
                "설비 유형 선택", 
                options=equipment_types,
                default=equipment_types
            )
            
        with col2:
            importance_levels = sorted(st.session_state.cmms_risk_data['중요도'].unique())
            selected_importance = st.multiselect(
                "중요도 선택", 
                options=importance_levels,
                default=importance_levels
            )
    
    # 필터링된 데이터
    filtered_data = st.session_state.cmms_risk_data[
        (st.session_state.cmms_risk_data['설비유형'].isin(selected_equipment)) &
        (st.session_state.cmms_risk_data['중요도'].isin(selected_importance))
    ]
    
    if filtered_data.empty:
        st.warning("선택한 필터에 맞는 데이터가 없습니다.")
        return
    
    # 위험도 매트릭스 (주요 시각화)
    st.subheader("위험도 매트릭스")
    
    # 위험도 점수 계산 (발생가능성 x 영향도)
    filtered_data['위험도점수'] = filtered_data['발생가능성'] * filtered_data['영향도']
    
    # 위험도에 따른 범례 추가
    def risk_category(score):
        if score <= 4:
            return '낮음'
        elif score <= 9:
            return '중간'
        elif score <= 16:
            return '높음'
        else:
            return '매우 높음'
    
    filtered_data['위험도등급'] = filtered_data['위험도점수'].apply(risk_category)
    
    # 위험도 등급별 색상 매핑
    risk_colors = {
        '낮음': 'green',
        '중간': 'yellow',
        '높음': 'orange',
        '매우 높음': 'red'
    }
    
    # 버블 차트 (위험도 매트릭스)
    fig = px.scatter(
        filtered_data,
        x='발생가능성',
        y='영향도',
        size='위험도점수',
        color='위험도등급',
        hover_name='설비ID',
        text='설비ID',
        color_discrete_map=risk_colors,
        size_max=40,
        labels={
            '발생가능성': '발생 가능성 (1-5)',
            '영향도': '영향도 (1-5)'
        },
        title="설비별 위험도 매트릭스"
    )
    
    # 매트릭스 그리드 추가
    for i in range(1, 6):
        fig.add_shape(
            type="line", x0=i, y0=1, x1=i, y1=5, 
            line=dict(color="lightgray", width=1)
        )
        fig.add_shape(
            type="line", x0=1, y0=i, x1=5, y1=i, 
            line=dict(color="lightgray", width=1)
        )
    
    # 위험 영역 하이라이트
    fig.add_shape(
        type="rect", x0=3, y0=3, x1=5.5, y1=5.5,
        fillcolor="rgba(255, 0, 0, 0.1)", line=dict(width=0)
    )
    
    fig.add_shape(
        type="rect", x0=1, y0=3, x1=3, y1=5.5,
        fillcolor="rgba(255, 165, 0, 0.1)", line=dict(width=0)
    )
    
    fig.add_shape(
        type="rect", x0=3, y0=1, x1=5.5, y1=3,
        fillcolor="rgba(255, 165, 0, 0.1)", line=dict(width=0)
    )
    
    # 레이아웃 업데이트
    fig.update_layout(
        xaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1,
            range=[0.5, 5.5]
        ),
        yaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1,
            range=[0.5, 5.5]
        ),
        legend=dict(
            title="위험도 등급",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 텍스트 위치 조정
    fig.update_traces(textposition='top center')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 위험도 분석 탭
    tab1, tab2 = st.tabs(["설비 유형별 위험도", "상위 위험 설비"])
    
    with tab1:
        st.subheader("설비 유형별 위험도 분석")
        
        # 설비 유형별 평균 위험도
        type_risk = filtered_data.groupby('설비유형').agg({
            '발생가능성': 'mean',
            '영향도': 'mean',
            '위험도점수': 'mean',
            '설비ID': 'count'
        }).reset_index()
        
        type_risk.columns = ['설비유형', '평균발생가능성', '평균영향도', '평균위험도점수', '설비수']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 설비 유형별 평균 위험도 점수
            fig = px.bar(
                type_risk.sort_values('평균위험도점수', ascending=False),
                x='설비유형',
                y='평균위험도점수',
                color='평균위험도점수',
                color_continuous_scale=['green', 'yellow', 'orange', 'red'],
                labels={'평균위험도점수': '평균 위험도 점수'},
                title="설비 유형별 평균 위험도 점수"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # 설비 유형별 발생가능성 vs 영향도
            fig = px.scatter(
                type_risk,
                x='평균발생가능성',
                y='평균영향도',
                size='설비수',
                color='평균위험도점수',
                color_continuous_scale=['green', 'yellow', 'orange', 'red'],
                hover_name='설비유형',
                text='설비유형',
                size_max=50,
                labels={
                    '평균발생가능성': '평균 발생 가능성',
                    '평균영향도': '평균 영향도',
                    '평균위험도점수': '평균 위험도 점수'
                },
                title="설비 유형별 발생가능성 vs 영향도"
            )
            
            # 위험 영역 구분선 추가
            fig.add_shape(
                type="line", x0=1, y0=3, x1=3, y1=3, 
                line=dict(color="gray", width=1, dash="dash")
            )
            fig.add_shape(
                type="line", x0=3, y0=1, x1=3, y1=3, 
                line=dict(color="gray", width=1, dash="dash")
            )
            
            # 영역 표시
            fig.add_annotation(x=2, y=2, text="저위험", showarrow=False, font=dict(color="green"))
            fig.add_annotation(x=4, y=2, text="중위험", showarrow=False, font=dict(color="orange"))
            fig.add_annotation(x=2, y=4, text="중위험", showarrow=False, font=dict(color="orange"))
            fig.add_annotation(x=4, y=4, text="고위험", showarrow=False, font=dict(color="red"))
            
            # 텍스트 위치 조정
            fig.update_traces(textposition='top center')
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("상위 위험 설비 목록")
        
        # 위험도점수 기준 정렬
        high_risk_equipment = filtered_data.sort_values('위험도점수', ascending=False).head(10)
        
        # 위험도 점수가 높은 상위 10개 설비
        fig = px.bar(
            high_risk_equipment,
            x='설비ID',
            y='위험도점수',
            color='위험도등급',
            hover_data=['설비유형', '발생가능성', '영향도', '고장내역', '최근점검일'],
            color_discrete_map=risk_colors,
            labels={'위험도점수': '위험도 점수'},
            title="상위 10개 고위험 설비"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 상위 위험 설비 데이터 테이블
        st.dataframe(
            high_risk_equipment[['설비ID', '설비유형', '중요도', '발생가능성', '영향도', '위험도점수', '위험도등급', '고장내역', '최근점검일']],
            use_container_width=True,
            column_config={
                "설비ID": st.column_config.TextColumn("설비 ID"),
                "설비유형": st.column_config.TextColumn("설비 유형"),
                "중요도": st.column_config.TextColumn("중요도"),
                "발생가능성": st.column_config.NumberColumn("발생 가능성", format="%.1f"),
                "영향도": st.column_config.NumberColumn("영향도", format="%.1f"),
                "위험도점수": st.column_config.NumberColumn("위험도 점수", format="%.1f"),
                "위험도등급": st.column_config.TextColumn("위험도 등급"),
                "고장내역": st.column_config.TextColumn("고장 내역"),
                "최근점검일": st.column_config.DateColumn("최근 점검일")
            }
        )
    
    # 위험도 개선 계획
    st.subheader("위험도 개선 권장사항")
    
    # 고위험 설비 필터링
    critical_equipment = filtered_data[filtered_data['위험도등급'].isin(['높음', '매우 높음'])]
    
    if not critical_equipment.empty:
        # 고위험 설비별 개선 권장사항
        for i, row in critical_equipment.iterrows():
            with st.expander(f"{row['설비ID']} - {row['설비유형']} (위험도: {row['위험도점수']:.1f}, 등급: {row['위험도등급']})"):
                st.write(f"**설비 정보:** {row['설비유형']} (중요도: {row['중요도']})")
                st.write(f"**위험 요소:** 발생가능성 {row['발생가능성']:.1f}/5, 영향도 {row['영향도']:.1f}/5")
                st.write(f"**고장 내역:** {row['고장내역']}")
                st.write(f"**최근 점검일:** {row['최근점검일'].strftime('%Y-%m-%d')}")
                
                # 임의의 권장사항 생성
                if row['발생가능성'] > 3:
                    st.write("**발생가능성 감소 방안:**")
                    st.write("- 예방 정비 주기 단축 (현재 주기의 75%로 조정)")
                    st.write("- 핵심 부품 교체 또는 업그레이드 검토")
                    st.write("- 설비 운영 매뉴얼 준수 여부 점검")
                
                if row['영향도'] > 3:
                    st.write("**영향도 감소 방안:**")
                    st.write("- 백업 시스템 또는 대체 설비 확보 검토")
                    st.write("- 고장 대응 절차 개선 및 훈련 강화")
                    st.write("- 핵심 예비 부품 재고 확보")
                
                st.write("**우선 조치사항:**")
                st.write("1. 긴급 안전 점검 실시")
                st.write("2. 위험 요소에 대한 상세 분석 수행")
                st.write("3. 개선 계획 수립 (2주 이내)")
    else:
        st.info("고위험으로 분류된 설비가 없습니다.")
    
    # 전체 설비 데이터 테이블
    with st.expander("전체 설비 위험도 데이터", expanded=False):
        st.dataframe(
            filtered_data.sort_values('위험도점수', ascending=False),
            use_container_width=True,
            column_config={
                "설비ID": st.column_config.TextColumn("설비 ID"),
                "설비유형": st.column_config.TextColumn("설비 유형"),
                "중요도": st.column_config.TextColumn("중요도"),
                "발생가능성": st.column_config.NumberColumn("발생 가능성", format="%.1f"),
                "영향도": st.column_config.NumberColumn("영향도", format="%.1f"),
                "위험도점수": st.column_config.NumberColumn("위험도 점수", format="%.1f"),
                "위험도등급": st.column_config.TextColumn("위험도 등급"),
                "고장내역": st.column_config.TextColumn("고장 내역"),
                "최근점검일": st.column_config.DateColumn("최근 점검일")
            }
        )

def generate_risk_data(num_equipments=30):
    """샘플 위험도 평가 데이터 생성"""
    np.random.seed(42)  # 재현성을 위한 시드 설정
    
    # 설비 ID 및 유형
    equipment_types = ['믹서', '코팅기', '압연기', '건조기', '검사기', '포장기']
    equipment_ids = []
    equipment_types_list = []
    
    for equip_type in equipment_types:
        for i in range(1, 6):  # 각 유형별 5개 장비
            equipment_ids.append(f"{equip_type[:1]}{i:02d}")
            equipment_types_list.append(equip_type)
    
    # 중요도 수준
    importance_levels = ['핵심', '주요', '일반']
    importance_weights = [0.3, 0.5, 0.2]  # 중요도별 가중치
    
    # 고장 내역 템플릿
    failure_templates = [
        "{component} 고장으로 {time}시간 생산 중단",
        "{component} 마모로 인한 {issue}",
        "{component}의 {issue}로 품질 저하",
        "{issue}로 인한 {component} 교체 필요",
        "정기 점검 중 {component}의 {issue} 발견"
    ]
    
    components = [
        "모터", "펌프", "밸브", "베어링", "센서", "컨트롤러", 
        "파이프", "실린더", "필터", "히터", "쿨러", "기어박스"
    ]
    
    issues = [
        "과열", "누수", "파손", "오작동", "진동", "소음", 
        "부식", "압력 저하", "통신 오류", "전원 문제"
    ]
    
    # 데이터 생성
    data = {
        '설비ID': equipment_ids[:num_equipments],
        '설비유형': equipment_types_list[:num_equipments],
        '중요도': np.random.choice(importance_levels, num_equipments, p=importance_weights),
        '발생가능성': np.random.uniform(1, 5, num_equipments),
        '영향도': np.random.uniform(1, 5, num_equipments),
        '고장내역': [],
        '최근점검일': []
    }
    
    # 고장 내역 생성
    for _ in range(num_equipments):
        template = np.random.choice(failure_templates)
        component = np.random.choice(components)
        issue = np.random.choice(issues)
        time = np.random.randint(1, 24)
        
        failure_desc = template.format(component=component, issue=issue, time=time)
        data['고장내역'].append(failure_desc)
    
    # 최근 점검일 생성 (현재부터 90일 이내)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    for _ in range(num_equipments):
        days = np.random.randint(0, 90)
        inspection_date = end_date - timedelta(days=days)
        data['최근점검일'].append(inspection_date)
    
    # 데이터프레임 생성
    df = pd.DataFrame(data)
    
    # 중요도에 따른 영향도 조정
    df.loc[df['중요도'] == '핵심', '영향도'] = df.loc[df['중요도'] == '핵심', '영향도'] * 1.2
    df.loc[df['중요도'] == '일반', '영향도'] = df.loc[df['중요도'] == '일반', '영향도'] * 0.8
    
    # 영향도와 발생가능성 범위 제한 (1-5)
    df['영향도'] = df['영향도'].clip(1, 5)
    df['발생가능성'] = df['발생가능성'].clip(1, 5)
    
    return df 