"""
DX-AI Manufacturing Copilot - 가상 데이터 생성 페이지

파라미터 기반 생산·실험·원가 데이터 생성 및 시뮬레이션 UI 페이지입니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 백엔드 엔진 및 유틸리티 import
from src.core.data_generation_engine import (
    ProductionDataGenerator,
    ExperimentalDataGenerator,
    CostProductionDataGenerator
)
from src.utils.data_utils import (
    DataFileManager,
    get_available_data_files,
    get_data_summary
)


def data_generation_page():
    """가상 데이터 생성 페이지"""
    st.markdown("## 📊 가상 데이터 생성")
    
    # 탭 구조로 데이터 유형별 분리
    tab1, tab2, tab3 = st.tabs(["🏭 생산 데이터", "🧪 실험 데이터", "💰 원가/생산 이력 데이터"])
    
    with tab1:
        production_data_tab()
    
    with tab2:
        experimental_data_tab()
    
    with tab3:
        cost_production_history_tab()


def production_data_tab():
    """생산 데이터 생성 탭"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🔧 생산 데이터 생성 설정")
        
        # 기본 파라미터
        with st.expander("📝 기본 파라미터", expanded=True):
            lot_count = st.slider("Lot 개수", min_value=10, max_value=1000, value=100, step=10)
            equipment_count = st.slider("설비 개수", min_value=1, max_value=50, value=10, step=1)
            time_period = st.selectbox("기간", ["1일", "1주", "1개월", "3개월", "6개월"])
            
            # 작업 일자 설정
            st.markdown("#### 📅 작업 일자 설정")
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                work_date_start = st.date_input(
                    "작업 시작 날짜",
                    value=datetime.now() - timedelta(days=30),
                    max_value=datetime.now()
                )
            with date_col2:
                work_date_end = st.date_input(
                    "작업 종료 날짜",
                    value=datetime.now(),
                    min_value=work_date_start,
                    max_value=datetime.now()
                )
            
            # 시간대 설정
            shift_type = st.selectbox("시간대 설정", ["주간(08:00-16:00)", "야간(22:00-06:00)", "전체(24시간)", "사용자 정의"])
            
            shift_config = {"shift_type": shift_type}
            
            if shift_type == "사용자 정의":
                time_col1, time_col2 = st.columns(2)
                with time_col1:
                    shift_start = st.time_input("작업 시작 시간", value=datetime.strptime("08:00", "%H:%M").time())
                with time_col2:
                    shift_end = st.time_input("작업 종료 시간", value=datetime.strptime("16:00", "%H:%M").time())
                
                shift_config.update({
                    "start_hour": shift_start.hour,
                    "end_hour": shift_end.hour
                })
        
        # 품질 지표
        with st.expander("📈 품질 지표 설정"):
            purity_range = st.slider("순도 범위 (%)", min_value=90.0, max_value=99.9, value=(95.0, 98.5), step=0.1)
            yield_range = st.slider("수율 범위 (%)", min_value=80.0, max_value=100.0, value=(85.0, 95.0), step=0.5)
        
        # 시뮬레이션 옵션
        with st.expander("🎛️ 시뮬레이션 옵션"):
            add_noise = st.checkbox("노이즈 추가", value=True)
            noise_level = st.slider("노이즈 레벨", min_value=0.1, max_value=5.0, value=1.0, step=0.1) if add_noise else 1.0
            
            add_anomalies = st.checkbox("이상치 추가", value=False)
            anomaly_ratio = st.slider("이상치 비율 (%)", min_value=1, max_value=10, value=3) if add_anomalies else 0
        
        # 생성 버튼
        if st.button("🚀 생산 데이터 생성", type="primary"):
            with st.spinner("생산 데이터 생성 중..."):
                try:
                    # 생산 데이터 생성기 초기화
                    generator = ProductionDataGenerator()
                    
                    # 데이터 생성
                    df = generator.generate_production_data(
                        lot_count=lot_count,
                        equipment_count=equipment_count,
                        work_date_start=work_date_start,
                        work_date_end=work_date_end,
                        shift_config=shift_config,
                        purity_range=purity_range,
                        yield_range=yield_range,
                        add_noise=add_noise,
                        noise_level=noise_level,
                        add_anomalies=add_anomalies,
                        anomaly_ratio=anomaly_ratio
                    )
                    
                    # 파일 저장
                    filepath = generator.save_production_data(df, lot_count)
                    
                    st.success(f"✅ 생산 데이터 생성 완료! 저장 위치: `{filepath}`")
                    st.dataframe(df, use_container_width=True)
                    
                    # CSV 다운로드
                    csv = df.to_csv(index=False)
                    filename = f"manufacturing_copilot_production_data_{lot_count}lots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=csv,
                        file_name=filename,
                        mime="text/csv"
                    )
                    
                    # 저장 정보 표시
                    st.info(f"📁 파일이 서버에 저장되었습니다: `{filepath}`")
                    st.info(f"📊 총 {len(df)} 개의 데이터 행이 생성되었습니다.")
                    
                except Exception as e:
                    st.error(f"❌ 생산 데이터 생성 실패: {str(e)}")
    
    with col2:
        st.markdown("### 🎯 생산 데이터 가이드")
        
        st.markdown("""
        **📊 생산 데이터 특징:**
        - 실제 생산 공정 시뮬레이션
        - Lot 단위 품질 관리
        - 설비별 성능 차이 반영
        - 시간 순서 기반 데이터
        - 작업 일자 및 시간대 정보 포함
        
        **📅 작업 일자 기능:**
        - 작업 시작/종료 날짜 설정
        - 주간/야간/24시간 시간대 선택
        - 사용자 정의 시간대 설정
        - 프로세스 관리에서 일자별 추적 가능
        
        **🎛️ 시뮬레이션 옵션:**
        - 노이즈: 실제 측정 오차 반영
        - 이상치: 시스템 오류 상황 모사
        
        **💾 자동 저장:**
        - 서버에 자동 저장됨
        - 타임스탬프 기반 파일명
        - CSV 형식으로 저장
        """)
        
        # 저장된 데이터 관리 섹션
        show_data_management_section(key_prefix="production", data_type_filter="생산")


def experimental_data_tab():
    """실험 데이터 생성 탭"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🧪 실험 데이터 생성 설정")
        
        # 실험 설계 방법
        with st.expander("🔬 실험 설계 (DoE)", expanded=True):
            experiment_type = st.selectbox(
                "실험 설계 방법",
                ["Full Factorial", "Fractional Factorial", "Central Composite", "Box-Behnken", "Custom"]
            )
            
            # 실험 인자 선택
            available_factors = ["온도", "압력", "pH", "반응시간", "촉매농도", "교반속도", "원료농도"]
            selected_factors = st.multiselect(
                "실험 인자 선택",
                available_factors,
                default=["온도", "압력", "pH"]
            )
            
            if experiment_type == "Full Factorial":
                levels = st.slider("수준 수", min_value=2, max_value=5, value=3)
                replications = st.slider("반복 횟수", min_value=1, max_value=5, value=2)
            elif experiment_type == "Fractional Factorial":
                levels = st.slider("수준 수", min_value=2, max_value=3, value=2)
                fraction = st.selectbox("분수 설계", ["1/2", "1/4", "1/8"])
                replications = st.slider("반복 횟수", min_value=1, max_value=3, value=1)
            else:
                num_experiments = st.slider("실험 횟수", min_value=10, max_value=100, value=25)
                replications = st.slider("반복 횟수", min_value=1, max_value=3, value=1)
        
        # 실험 조건 설정
        with st.expander("⚙️ 실험 조건 설정"):
            factor_ranges = {}
            for factor in selected_factors:
                if factor == "온도":
                    factor_ranges[factor] = st.slider(f"{factor} 범위 (°C)", 120, 250, (150, 200))
                elif factor == "압력":
                    factor_ranges[factor] = st.slider(f"{factor} 범위 (bar)", 1.0, 5.0, (1.5, 3.0))
                elif factor == "pH":
                    factor_ranges[factor] = st.slider(f"{factor} 범위", 5.0, 9.0, (6.5, 8.5))
                elif factor == "반응시간":
                    factor_ranges[factor] = st.slider(f"{factor} 범위 (분)", 30, 300, (60, 180))
                elif factor == "촉매농도":
                    factor_ranges[factor] = st.slider(f"{factor} 범위 (ppm)", 100, 1000, (200, 500))
                elif factor == "교반속도":
                    factor_ranges[factor] = st.slider(f"{factor} 범위 (rpm)", 100, 1000, (200, 600))
                elif factor == "원료농도":
                    factor_ranges[factor] = st.slider(f"{factor} 범위 (M)", 0.1, 2.0, (0.5, 1.5))
        
        # 실험 일자 설정
        with st.expander("📅 실험 일자 설정"):
            st.markdown("#### 📅 실험 수행 일정")
            exp_date_col1, exp_date_col2 = st.columns(2)
            with exp_date_col1:
                experiment_date_start = st.date_input(
                    "실험 시작 날짜",
                    value=datetime.now(),
                    max_value=datetime.now() + timedelta(days=365)
                )
            with exp_date_col2:
                experiment_date_end = st.date_input(
                    "실험 종료 날짜",
                    value=datetime.now() + timedelta(days=7),
                    min_value=experiment_date_start,
                    max_value=datetime.now() + timedelta(days=365)
                )
            
            # 실험 시간대 설정
            experiment_shift_type = st.selectbox(
                "실험 시간대 설정", 
                ["일반 실험시간(09:00-17:00)", "연장 실험시간(09:00-21:00)", "24시간 연속실험", "사용자 정의"]
            )
            
            if experiment_shift_type == "사용자 정의":
                exp_time_col1, exp_time_col2 = st.columns(2)
                with exp_time_col1:
                    experiment_shift_start = st.time_input("실험 시작 시간", value=datetime.strptime("09:00", "%H:%M").time())
                with exp_time_col2:
                    experiment_shift_end = st.time_input("실험 종료 시간", value=datetime.strptime("17:00", "%H:%M").time())
            
            # 실험 간격 설정
            experiment_interval = st.selectbox(
                "실험 간격",
                ["동시 수행", "1시간 간격", "2시간 간격", "4시간 간격", "일별 수행", "사용자 정의"]
            )
            
            if experiment_interval == "사용자 정의":
                custom_interval = st.number_input("실험 간격 (분)", min_value=15, max_value=1440, value=60)
        
        # 실험 메타데이터
        with st.expander("📋 실험 메타데이터"):
            experimenter = st.text_input("실험자", value="연구원A")
            experiment_purpose = st.text_area("실험 목적", value="공정 조건 최적화를 위한 인자 스크리닝")
            experiment_objective = st.selectbox("실험 목표", ["순도 최대화", "수율 최대화", "비용 최소화", "다목적 최적화"])
        
        # 실험 계획 생성 버튼
        if st.button("🧪 실험 계획 생성", type="primary"):
            with st.spinner("실험 계획 생성 중..."):
                try:
                    # 실험 데이터 생성기 초기화
                    generator = ExperimentalDataGenerator()
                    
                    # 실험 설정 구성
                    experiment_config = {
                        "experiment_type": experiment_type,
                        "selected_factors": selected_factors,
                        "levels": locals().get('levels', 3),
                        "replications": locals().get('replications', 1),
                        "num_experiments": locals().get('num_experiments', 25)
                    }
                    
                    # 실험 일정 설정
                    experiment_schedule = {
                        "experiment_date_start": experiment_date_start,
                        "experiment_date_end": experiment_date_end,
                        "experiment_shift_type": experiment_shift_type,
                        "experiment_interval": experiment_interval
                    }
                    
                    # 메타데이터 설정
                    metadata = {
                        "experimenter": experimenter,
                        "experiment_purpose": experiment_purpose,
                        "experiment_objective": experiment_objective
                    }
                    
                    # 실험 데이터 생성
                    df = generator.generate_experimental_data(
                        experiment_config, factor_ranges, experiment_schedule, metadata
                    )
                    
                    # 파일 저장
                    filepath = generator.save_experimental_data(df, experiment_type)
                    
                    st.success(f"✅ 실험 데이터 생성 완료! 저장 위치: `{filepath}`")
                    st.dataframe(df, use_container_width=True)
                    
                    # CSV 다운로드
                    csv = df.to_csv(index=False)
                    filename = f"manufacturing_copilot_experimental_data_{experiment_type}_{len(df)}runs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=csv,
                        file_name=filename,
                        mime="text/csv"
                    )
                    
                    # 저장 정보 표시
                    st.info(f"📁 파일이 서버에 저장되었습니다: `{filepath}`")
                    st.info(f"📊 총 {len(df)} 개의 실험 데이터 행이 생성되었습니다.")
                    
                    # 실험 계획 요약
                    st.markdown("### 📊 실험 계획 요약")
                    st.write(f"**실험 설계**: {experiment_type}")
                    st.write(f"**실험 인자**: {', '.join(selected_factors)}")
                    st.write(f"**총 실험 횟수**: {len(df)}")
                    st.write(f"**실험 목표**: {experiment_objective}")
                    
                except Exception as e:
                    st.error(f"❌ 실험 데이터 생성 실패: {str(e)}")
    
    with col2:
        st.markdown("### 🔬 실험 설계 가이드")
        
        st.markdown("""
        **📊 실험 설계 방법론 상세 가이드**
        
        실험 설계(Design of Experiments, DoE)는 효율적이고 체계적인 실험을 통해 
        인자들이 결과에 미치는 영향을 파악하는 통계적 방법입니다.
        
        **📅 실험 일정 계획 특징:**
        - 실험 시작/종료 날짜 설정 가능
        - 실험 시간대별 계획 수립 (일반/연장/24시간)
        - 실험 간격 조정으로 효율적 일정 관리
        - 프로세스 관리에서 실험 진행 상황 추적
        """)
        
        # 각 방법론별 상세 설명 (기존과 동일)
        with st.expander("📈 **Full Factorial Design (완전요인설계)**", expanded=False):
            st.markdown("""
            **👍 장점:**
            - 모든 인자의 조합을 다 실험해서 **완전한 정보** 확보
            - 인자 간의 **상호작용 효과**를 정확히 파악 가능
            - 결과의 **신뢰도가 높음**
            
            **👎 단점:**
            - 인자가 많아질수록 실험 횟수가 **기하급수적으로 증가**
            - 예: 5개 인자 × 3수준 = 3⁵ = 243회 실험 😵
            
            **🎯 언제 사용?**
            - 인자가 **3~4개 이하**일 때
            - **정확한 상호작용 효과**를 알아야 할 때
            - 시간과 비용이 충분할 때
            """)
        
        # 저장된 데이터 관리 섹션
        show_data_management_section(key_prefix="experimental", data_type_filter="실험")


def cost_production_history_tab():
    """원가/생산 이력 데이터 생성 탭"""
    st.markdown("### 💰 원가/생산 이력 데이터 생성")
    st.markdown("**원가관리 시스템에서 사용할 수 있는 현실적인 생산 이력 및 비용 데이터를 생성합니다.**")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🔧 데이터 생성 설정")
        
        # 기본 파라미터
        with st.expander("📊 기본 파라미터", expanded=True):
            record_count = st.slider("생산 기록 수", min_value=100, max_value=10000, value=1000, step=100)
            
            # 생산 기간 설정
            st.markdown("**📅 생산 기간**")
            period_col1, period_col2 = st.columns(2)
            with period_col1:
                start_date = st.date_input(
                    "시작일",
                    value=datetime.now() - timedelta(days=180),
                    max_value=datetime.now()
                )
            with period_col2:
                end_date = st.date_input(
                    "종료일",
                    value=datetime.now(),
                    min_value=start_date,
                    max_value=datetime.now()
                )
        
        # 제품 및 품질 설정
        with st.expander("🎯 제품 및 품질 설정"):
            product_grade = st.selectbox("제품 그레이드", ["Premium", "Standard", "Economy", "Mixed"])
            
            if product_grade == "Premium":
                purity_range = (96.0, 99.0)
                yield_range = (88.0, 95.0)
            elif product_grade == "Standard":
                purity_range = (92.0, 96.0)
                yield_range = (85.0, 92.0)
            elif product_grade == "Economy":
                purity_range = (88.0, 93.0)
                yield_range = (82.0, 89.0)
            else:  # Mixed
                purity_range = (88.0, 99.0)
                yield_range = (82.0, 95.0)
            
            st.write(f"순도 목표: {purity_range[0]}% - {purity_range[1]}%")
            st.write(f"수율 목표: {yield_range[0]}% - {yield_range[1]}%")
            
            # 사용자 정의 설정
            if st.checkbox("사용자 정의 품질 범위"):
                custom_purity = st.slider("순도 범위 (%)", min_value=80.0, max_value=99.9, value=purity_range, step=0.1)
                custom_yield = st.slider("수율 범위 (%)", min_value=70.0, max_value=98.0, value=yield_range, step=0.1)
                purity_range = custom_purity
                yield_range = custom_yield
        
        # 원료 및 투입량 설정
        with st.expander("📦 원료 및 투입량 설정"):
            st.markdown("**원료 A (주원료)**")
            material_a_range = st.slider("원료 A 사용량 (kg/h)", min_value=50.0, max_value=200.0, value=(80.0, 120.0), step=5.0)
            material_a_cost = st.number_input("원료 A 단가 (원/kg)", min_value=100, max_value=1000, value=450, step=10)
            
            st.markdown("**원료 B (부원료)**")
            material_b_range = st.slider("원료 B 사용량 (kg/h)", min_value=20.0, max_value=100.0, value=(40.0, 60.0), step=2.5)
            material_b_cost = st.number_input("원료 B 단가 (원/kg)", min_value=200, max_value=1500, value=720, step=20)
            
            st.markdown("**촉매**")
            catalyst_range = st.slider("촉매 사용량 (kg/h)", min_value=1.0, max_value=20.0, value=(3.0, 8.0), step=0.5)
            catalyst_cost = st.number_input("촉매 단가 (원/kg)", min_value=5000, max_value=50000, value=18000, step=500)
        
        # 운전 조건 설정
        with st.expander("⚙️ 운전 조건 설정"):
            temp_range = st.slider("온도 범위 (°C)", min_value=100, max_value=250, value=(160, 190), step=5)
            pressure_range = st.slider("압력 범위 (bar)", min_value=1.0, max_value=5.0, value=(2.0, 3.0), step=0.1)
            flow_range = st.slider("유량 범위 (L/h)", min_value=100, max_value=400, value=(180, 220), step=10)
        
        # 유틸리티 설정
        with st.expander("⚡ 유틸리티 설정"):
            st.markdown("**스팀**")
            steam_range = st.slider("스팀 사용량 (kg/h)", min_value=50, max_value=300, value=(120, 180), step=10)
            steam_cost = st.number_input("스팀 단가 (원/kg)", min_value=20, max_value=100, value=50, step=5)
            
            st.markdown("**전력**")
            electricity_range = st.slider("전력 사용량 (kWh)", min_value=30, max_value=150, value=(60, 100), step=5)
            electricity_cost = st.number_input("전력 단가 (원/kWh)", min_value=50, max_value=200, value=120, step=10)
            
            st.markdown("**냉각수**")
            cooling_range = st.slider("냉각수 사용량 (L/h)", min_value=200, max_value=1000, value=(400, 600), step=25)
            cooling_cost = st.number_input("냉각수 단가 (원/L)", min_value=1, max_value=20, value=5, step=1)
        
        # 시장 변동성 설정
        with st.expander("📈 시장 변동성 설정"):
            price_volatility = st.slider("원료 가격 변동성 (%)", min_value=0, max_value=30, value=10, step=1)
            utility_volatility = st.slider("유틸리티 가격 변동성 (%)", min_value=0, max_value=20, value=5, step=1)
            seasonal_effect = st.checkbox("계절별 효과 적용", value=True)
            
        # 고급 설정
        with st.expander("🔬 고급 설정"):
            correlation_strength = st.slider("투입량-품질 상관관계 강도", min_value=0.3, max_value=0.9, value=0.7, step=0.05)
            noise_level = st.slider("데이터 노이즈 수준", min_value=0.5, max_value=5.0, value=2.0, step=0.1)
            include_shifts = st.checkbox("교대 근무 효과 포함", value=True)
            include_equipment_wear = st.checkbox("설비 마모 효과 포함", value=True)
        
        # 생성 버튼
        if st.button("🚀 원가/생산 이력 데이터 생성", type="primary"):
            with st.spinner("원가/생산 이력 데이터 생성 중..."):
                try:
                    # 원가/생산 데이터 생성기 초기화
                    generator = CostProductionDataGenerator()
                    
                    # 설정 구성
                    config = {
                        'record_count': record_count,
                        'start_date': start_date,
                        'end_date': end_date,
                        'purity_range': purity_range,
                        'yield_range': yield_range,
                        'material_a_range': material_a_range,
                        'material_a_cost': material_a_cost,
                        'material_b_range': material_b_range,
                        'material_b_cost': material_b_cost,
                        'catalyst_range': catalyst_range,
                        'catalyst_cost': catalyst_cost,
                        'temp_range': temp_range,
                        'pressure_range': pressure_range,
                        'flow_range': flow_range,
                        'steam_range': steam_range,
                        'steam_cost': steam_cost,
                        'electricity_range': electricity_range,
                        'electricity_cost': electricity_cost,
                        'cooling_range': cooling_range,
                        'cooling_cost': cooling_cost,
                        'price_volatility': price_volatility,
                        'utility_volatility': utility_volatility,
                        'seasonal_effect': seasonal_effect,
                        'correlation_strength': correlation_strength,
                        'noise_level': noise_level,
                        'include_shifts': include_shifts,
                        'include_equipment_wear': include_equipment_wear
                    }
                    
                    # 데이터 생성
                    df = generator.generate_cost_production_data(config)
                    
                    # 파일 저장
                    filepath = generator.save_cost_production_data(df)
                    
                    st.success(f"✅ 원가/생산 이력 데이터 생성 완료! 저장 위치: `{filepath}`")
                    
                    # 데이터 요약 정보
                    summary_col1, summary_col2, summary_col3 = st.columns(3)
                    
                    with summary_col1:
                        st.metric("총 레코드 수", f"{len(df):,}")
                        avg_purity = df['purity'].mean()
                        st.metric("평균 순도", f"{avg_purity:.1f}%")
                    
                    with summary_col2:
                        avg_yield = df['yield'].mean()
                        st.metric("평균 수율", f"{avg_yield:.1f}%")
                        avg_cost = df['total_cost'].mean()
                        st.metric("평균 총 비용", f"{avg_cost:,.0f}원")
                    
                    with summary_col3:
                        date_range_str = f"{(end_date - start_date).days}일"
                        st.metric("생산 기간", date_range_str)
                        cost_range = df['total_cost'].max() - df['total_cost'].min()
                        st.metric("비용 변동폭", f"{cost_range:,.0f}원")
                    
                    # 데이터 미리보기
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # CSV 다운로드
                    csv = df.to_csv(index=False, encoding='utf-8-sig')
                    filename = f"cost_production_history_{record_count}records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    st.download_button(
                        label="📥 CSV 다운로드",
                        data=csv,
                        file_name=filename,
                        mime="text/csv"
                    )
                    
                    # 원가관리 시스템 연동 옵션
                    st.markdown("---")
                    st.markdown("#### 🔗 원가관리 시스템 연동")
                    if st.button("📊 원가관리 페이지에서 바로 사용"):
                        # 세션 상태에 데이터 저장
                        st.session_state.generated_cost_data = df
                        st.session_state.cost_data_filepath = filepath
                        st.success("✅ 데이터가 원가관리 시스템에 로드되었습니다. 원가관리 페이지로 이동하세요!")
                    
                    st.info(f"📁 파일이 서버에 저장되었습니다: `{filepath}`")
                    
                except Exception as e:
                    st.error(f"❌ 원가/생산 이력 데이터 생성 실패: {str(e)}")
    
    with col2:
        st.markdown("#### 📊 데이터 미리보기 및 생성")
        
        # 예상 데이터 구조 표시
        st.markdown("**📋 생성될 데이터 구조:**")
        sample_data = {
            "lot_number": ["LOT_0001", "LOT_0002", "LOT_0003"],
            "timestamp": ["2024-01-01 08:00:00", "2024-01-01 09:00:00", "2024-01-01 10:00:00"],
            "material_a": [95.2, 98.7, 102.1],
            "material_b": [48.5, 51.2, 49.8],
            "catalyst": [5.1, 5.8, 6.2],
            "temperature": [175.2, 178.5, 172.8],
            "pressure": [2.45, 2.62, 2.38],
            "flow_rate": [195.5, 205.2, 188.9],
            "steam": [145.2, 152.8, 141.5],
            "electricity": [78.5, 82.1, 75.9],
            "cooling_water": [485.2, 512.8, 465.1],
            "purity": [96.8, 97.2, 96.1],
            "yield": [91.5, 92.8, 90.2],
            "material_cost": [65420, 68150, 66890],
            "utility_cost": [18250, 19120, 17680],
            "total_cost": [83670, 87270, 84570]
        }
        
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)
        
        # 원가 데이터 가이드
        st.markdown("---")
        st.markdown("#### 💡 원가/생산 이력 데이터 가이드")
        st.markdown("""
        **📊 원가 데이터 특징:**
        - 실제 생산 이력 기반 비용 분석
        - 원료/유틸리티 단가 변동성 반영
        - 품질과 비용의 상관관계 모델링
        - 시장 변동성 및 계절 효과 적용
        - 교대 근무 및 설비 마모 효과 포함
        
        **🎯 원가관리 시스템 연동:**
        - ML 기반 비용 예측 모델 훈련
        - 최적화 알고리즘 입력 데이터
        - 민감도 분석 기초 자료
        - 실시간 원가 분석 기준
        
        **💾 자동 저장:**
        - cost_production/ 폴더에 저장
        - 타임스탬프 기반 파일명
        - 원가관리 페이지에서 자동 인식
        """)
        
        # 저장된 데이터 관리 섹션
        show_data_management_section(key_prefix="cost_production", data_type_filter="원가")


def show_data_management_section(key_prefix="data", data_type_filter=None):
    """저장된 데이터 관리 섹션 표시"""
    st.markdown("---")
    st.markdown("### 📁 저장된 데이터 관리")
    
    try:
        # 데이터 파일 관리자 초기화
        file_manager = DataFileManager()
        
        # 파일 목록 조회
        if data_type_filter:
            all_files = file_manager.get_all_files(data_type_filter)
        else:
            all_files = file_manager.get_all_files()
        
        if all_files:
            st.markdown("#### 📋 최근 생성된 데이터")
            
            # 탭으로 데이터 유형별 분리
            data_tab_name = "📊 데이터 목록" if data_type_filter else "📊 전체 데이터"
            tab1, tab2 = st.tabs([data_tab_name, "📈 통계"])
            
            with tab1:
                for i, (filepath, data_type) in enumerate(all_files[:5]):  # 최근 5개 파일 표시
                    file_info = file_manager.get_file_info(filepath)
                    
                    # 파일 정보 표시
                    with st.expander(f"{data_type} | {file_info['filename']}", expanded=(i == 0)):
                        file_col1, file_col2 = st.columns(2)
                        
                        with file_col1:
                            st.write(f"**데이터 타입**: {data_type}")
                            st.write(f"**생성시간**: {file_info['create_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                            st.write(f"**파일크기**: {file_info['file_size_kb']:.1f} KB")
                        
                        with file_col2:
                            if 'error' not in file_info:
                                st.write(f"**데이터 수**: {file_info['row_count']} 행")
                                st.write(f"**컬럼 수**: {file_info['col_count']} 개")
                            else:
                                st.error(f"미리보기 오류: {file_info['error']}")
                        
                        # 데이터 미리보기
                        if 'preview_data' in file_info and file_info['preview_data'] is not None:
                            st.dataframe(file_info['preview_data'], use_container_width=True)
                        
                        # 다운로드 버튼
                        file_content = file_manager.read_file_content(filepath)
                        if not file_content.startswith("파일 읽기 오류"):
                            st.download_button(
                                label="📥 다운로드",
                                data=file_content,
                                file_name=file_info['filename'],
                                mime="text/csv",
                                key=f"{key_prefix}_download_{i}"
                            )
            
            with tab2:
                # 데이터 통계 정보
                stats = file_manager.get_data_statistics(data_type_filter)
                
                if data_type_filter:
                    # 특정 데이터 타입만 필터링된 경우
                    stat_col1, stat_col2 = st.columns(2)
                    
                    with stat_col1:
                        st.metric("총 파일 수", stats["total_files"])
                        
                    with stat_col2:
                        if data_type_filter == "생산":
                            st.metric("🏭 생산 데이터", stats["production_count"])
                        elif data_type_filter == "실험":
                            st.metric("🧪 실험 데이터", stats["experimental_count"])
                        elif data_type_filter == "원가":
                            st.metric("💰 원가 데이터", stats["cost_production_count"])
                else:
                    # 전체 데이터 표시
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    
                    with stat_col1:
                        st.metric("총 파일 수", stats["total_files"])
                        
                    with stat_col2:
                        st.metric("🏭 생산 데이터", stats["production_count"])
                        
                    with stat_col3:
                        st.metric("🧪 실험 데이터", stats["experimental_count"])
                
                # 저장소 크기 통계
                st.markdown("#### 💾 저장소 사용량")
                st.metric("총 용량", f"{stats['total_size_mb']} MB")
                
                # 최근 생성 활동
                if stats["date_counts"]:
                    st.markdown("#### 📈 최근 생성 활동")
                    date_counts_df = pd.DataFrame(list(stats["date_counts"].items()), columns=['날짜', '파일 수'])
                    date_counts_df['날짜'] = pd.to_datetime(date_counts_df['날짜'])
                    date_counts_df = date_counts_df.sort_values('날짜')
                    st.bar_chart(date_counts_df.set_index('날짜'))
        
        else:
            if data_type_filter:
                st.info(f"📂 저장된 {data_type_filter} 데이터가 없습니다.")
            else:
                st.info("📂 저장된 데이터가 없습니다.")
            
            # 폴더 생성 안내
            st.markdown("#### 📁 데이터 저장 구조")
            st.markdown("""
            ```            data/
            └── generated/
                ├── production/     # 🏭 생산 데이터
                ├── experimental/   # 🧪 실험 데이터
                └── cost_production/# 💰 원가 데이터
            ```
            
            **💡 안내:**
            - 데이터를 생성하면 자동으로 해당 폴더가 만들어집니다
            - 각 데이터 타입별로 폴더가 분리되어 관리됩니다
            """)
    
    except Exception as e:
        st.error(f"데이터 관리 섹션 로드 오류: {str(e)}")
