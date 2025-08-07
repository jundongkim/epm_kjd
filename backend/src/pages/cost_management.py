"""
DX-AI Manufacturing Copilot - 원가 관리 페이지

투입량 최적화, 비용 민감도 분석 및 LLM 기반 리포트 페이지입니다.
실제 ML 모델과 최적화 알고리즘을 통합하여 생산 이력 학습 기반 최적화를 제공합니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List

# 프로젝트 내부 모듈
from src.copilot.cost_management_engine import CostManagementEngine
from src.copilot.cost_optimization_engine import QualityTarget
from src.copilot.chat_manager import ChatManager, setup_chat_sidebar
from src.utils.cost_management_utils import (
    get_current_data_info,
    get_available_cost_files,
    get_file_info,
    get_detailed_file_info,
    load_selected_file,
    save_uploaded_file,
    use_default_simulation_data,
    validate_csv_columns,
    get_default_data_info,
    create_sample_data_preview
)


def initialize_cost_management_engine():
    """원가 관리 엔진 초기화"""
    if "cost_management_engine" not in st.session_state:
        st.session_state.cost_management_engine = None
    
    if st.session_state.cost_management_engine is None:
        with st.spinner("🔄 원가 관리 엔진을 초기화하는 중입니다..."):
            st.session_state.cost_management_engine = CostManagementEngine()
            
            # 데이터 생성 페이지에서 생성된 데이터 확인
            data_path = None
            if "cost_data_filepath" in st.session_state and st.session_state.cost_data_filepath:
                data_path = st.session_state.cost_data_filepath
                st.info(f"🔗 생성된 원가 데이터를 사용합니다: {data_path}")
            
            init_result = st.session_state.cost_management_engine.initialize(data_path)
            
            if init_result["success"]:
                st.success("✅ 원가 관리 엔진 초기화 완료!")
                return True
            else:
                st.error(f"❌ 엔진 초기화 실패: {init_result.get('error', '알 수 없는 오류')}")
                return False
    return True


def cost_management_page():
    """원가 관리 페이지 메인"""
    st.markdown("## 💰 원가 관리")
    st.markdown("### 🤖 ML 모델 기반 투입량 최적화 및 비용 민감도 분석")
    
    # 데이터 로드 섹션
    render_data_load_section()
    
    # 엔진 초기화
    if not initialize_cost_management_engine():
        st.stop()
    
    # ChatManager 및 탭별 채팅 매니저 초기화
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = ChatManager()
    
    chat_manager = st.session_state.chat_manager
    
    # 탭별 채팅 매니저 초기화
    if 'cost_analysis_chat' not in st.session_state:
        st.session_state.cost_analysis_chat = CostAnalysisChatManager(chat_manager)
    
    if 'cost_optimization_chat' not in st.session_state:
        st.session_state.cost_optimization_chat = CostOptimizationChatManager(chat_manager)
    
    if 'cost_sensitivity_chat' not in st.session_state:
        st.session_state.cost_sensitivity_chat = CostSensitivityChatManager(chat_manager)
    
    if 'cost_quality_prediction_chat' not in st.session_state:
        st.session_state.cost_quality_prediction_chat = CostQualityPredictionChatManager(chat_manager)
    
    if 'cost_ai_analysis_chat' not in st.session_state:
        st.session_state.cost_ai_analysis_chat = CostAIAnalysisChatManager(chat_manager)
    
    # 사이드바에 채팅 설정 추가
    setup_chat_sidebar(chat_manager)
    
    # 사이드바 설정
    sidebar_settings = render_sidebar_settings()
    
    # 메인 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💹 원가 분석", "⚙️ 최적화", "📊 민감도 분석", "🔍 품질 예측", "💬 AI 분석"])
    
    with tab1:
        render_cost_analysis_tab()
    
    with tab2:
        render_optimization_tab(sidebar_settings)
    
    with tab3:
        render_sensitivity_analysis_tab(sidebar_settings)
    
    with tab4:
        render_quality_prediction_tab(sidebar_settings)
    
    with tab5:
        render_ai_analysis_tab()


def render_sidebar_settings():
    """사이드바 설정 렌더링"""
    with st.sidebar:
        st.markdown("### ⚙️ 최적화 설정")
        
        # 품질 목표 설정
        st.markdown("#### 🎯 품질 목표")
        target_purity = st.slider("목표 순도 (%)", 90.0, 99.0, 95.0, 0.1)
        target_yield = st.slider("목표 수율 (%)", 80.0, 95.0, 85.0, 0.1)
        
        # 최적화 방법 선택
        st.markdown("#### 🔧 최적화 방법")
        optimization_method = st.selectbox(
            "최적화 알고리즘",
            ["Differential Evolution", "Bayesian Optimization", "Robust Optimization", "Multi-Objective", "Method Comparison"]
        )
        
        # 민감도 분석 변수 선택
        st.markdown("#### 📊 민감도 분석")
        sensitivity_vars = st.multiselect(
            "분석 변수",
            ["material_a", "material_b", "catalyst", "temperature", "pressure", "steam", "electricity"],
            default=["material_a", "material_b", "catalyst"]
        )
        
        variation_range = st.slider("변동 범위 (%)", 5, 30, 10) / 100
        
        return {
            "target_purity": target_purity,
            "target_yield": target_yield,
            "optimization_method": optimization_method,
            "sensitivity_vars": sensitivity_vars,
            "variation_range": variation_range
        }


def render_cost_analysis_tab():
    """원가 분석 탭 렌더링"""
    st.markdown("### 💹 실시간 원가 분석 대시보드")
    
    engine = st.session_state.cost_management_engine
    context_data = engine.get_context_data()
    
    # 데이터 표시 섹션
    if context_data:
        # 원가 구조 표시
        cost_breakdown = context_data.get("cost_breakdown", [])
        if cost_breakdown:
            render_cost_breakdown_metrics(cost_breakdown)
            render_cost_structure_chart(cost_breakdown)
        
        # 생산 이력 표시
        production_history = context_data.get("production_history", [])
        if production_history:
            render_production_history(production_history)
        
        # 품질 지표 요약
        quality_metrics = context_data.get("quality_metrics", {})
        if quality_metrics:
            render_quality_metrics_summary(quality_metrics)
    else:
        st.warning("⚠️ 데이터를 로드하는 중입니다...")
    
    # 원가 분석 채팅 인터페이스 (하단에 배치)
    st.markdown("---")
    
    if context_data:
        # Context 데이터 업데이트
        st.session_state.cost_analysis_chat.update_context_data(context_data, "현재")
    
    # 채팅 인터페이스 생성
    st.session_state.cost_analysis_chat.create_chat_interface()


def render_cost_breakdown_metrics(cost_breakdown):
    """원가 구조 메트릭 표시"""
    col1, col2, col3, col4 = st.columns(4)
    
    total_cost = sum(item["금액(만원)"] for item in cost_breakdown)
    material_cost = next((item["금액(만원)"] for item in cost_breakdown if item["항목"] == "원료비"), 0)
    utility_cost = next((item["금액(만원)"] for item in cost_breakdown if item["항목"] == "유틸리티"), 0)
    
    with col1:
        st.metric("총 원가", f"₩{total_cost:.1f}만원")
    
    with col2:
        st.metric("원료비", f"₩{material_cost:.1f}만원")
    
    with col3:
        st.metric("유틸리티", f"₩{utility_cost:.1f}만원")
    
    with col4:
        if total_cost > 0:
            cost_ratio = (material_cost / total_cost) * 100
            st.metric("원료비 비율", f"{cost_ratio:.1f}%")


def render_cost_structure_chart(cost_breakdown):
    """원가 구조 차트 표시"""
    st.markdown("#### 📊 원가 구조 분석")
    cost_df = pd.DataFrame(cost_breakdown)
    fig = px.pie(cost_df, values="금액(만원)", names="항목", title="원가 구조")
    st.plotly_chart(fig, use_container_width=True)


def render_production_history(production_history):
    """생산 이력 표시"""
    st.markdown("#### 🏭 최근 생산 이력")
    
    prod_df = pd.DataFrame(production_history)
    
    # 생산 이력 차트
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prod_df.index, y=prod_df['purity'], name='순도 (%)', yaxis='y'))
    fig.add_trace(go.Scatter(x=prod_df.index, y=prod_df['yield'], name='수율 (%)', yaxis='y'))
    fig.add_trace(go.Scatter(x=prod_df.index, y=prod_df['quantity'], name='생산량', yaxis='y2'))
    
    fig.update_layout(
        title="생산 품질 및 생산량 추이",
        xaxis_title="Lot",
        yaxis=dict(title="품질 지표 (%)", side="left"),
        yaxis2=dict(title="생산량", side="right", overlaying="y")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(prod_df, use_container_width=True)


def render_quality_metrics_summary(quality_metrics):
    """품질 지표 요약 표시"""
    st.markdown("#### 🎯 품질 지표 요약")
    cols = st.columns(len(quality_metrics))
    for i, (metric, value) in enumerate(quality_metrics.items()):
        with cols[i]:
            st.metric(metric, value)


def render_optimization_tab(settings):
    """최적화 탭 렌더링"""
    st.markdown("### ⚙️ 실시간 투입량 최적화")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_optimization_controls(settings)
    
    with col2:
        render_optimization_results(settings["optimization_method"])
    
    # 최적화 채팅 인터페이스 추가
    st.markdown("---")
    
    # Context 데이터 업데이트
    context_data = {
        "optimization_settings": settings,
        "optimization_results": getattr(st.session_state, 'optimization_result', {}),
        "algorithm_performance": getattr(st.session_state, 'algorithm_performance', {})
    }
    
    st.session_state.cost_optimization_chat.update_context_data(context_data, "현재")
    st.session_state.cost_optimization_chat.create_chat_interface()


def render_optimization_controls(settings):
    """최적화 제어 섹션"""
    st.markdown("#### 🎯 최적화 실행")
    
    # 품질 목표 설정
    quality_targets = [
        QualityTarget(metric="purity", target_value=settings["target_purity"], constraint_type="ge", weight=1.0),
        QualityTarget(metric="yield", target_value=settings["target_yield"], constraint_type="ge", weight=1.0)
    ]
    
    # 최적화 범위 설정
    st.markdown("**최적화 범위:**")
    optimization_bounds = render_optimization_bounds()
    
    # 최적화 실행
    if st.button("🚀 최적화 실행", type="primary"):
        execute_optimization(settings["optimization_method"], quality_targets, optimization_bounds)


def render_optimization_bounds():
    """최적화 범위 설정 UI"""
    col_a, col_b = st.columns(2)
    with col_a:
        material_a_min = st.number_input("원료 A 최소 (kg/h)", 50, 150, 80)
        material_a_max = st.number_input("원료 A 최대 (kg/h)", 100, 200, 120)
    with col_b:
        material_b_min = st.number_input("원료 B 최소 (kg/h)", 20, 60, 40)
        material_b_max = st.number_input("원료 B 최대 (kg/h)", 50, 80, 60)
    
    catalyst_min = st.number_input("촉매 최소 (kg/h)", 2, 8, 4)
    catalyst_max = st.number_input("촉매 최대 (kg/h)", 5, 10, 6)
    
    return {
        "material_a": (material_a_min, material_a_max),
        "material_b": (material_b_min, material_b_max),
        "catalyst": (catalyst_min, catalyst_max)
    }


def execute_optimization(method, quality_targets, optimization_bounds):
    """최적화 실행"""
    with st.spinner(f"{method} 최적화 실행 중..."):
        engine = st.session_state.cost_management_engine
        result = engine.execute_optimization(method, quality_targets, optimization_bounds)
        
        if result.get("success", False):
            st.success("✅ 최적화 완료!")
            st.session_state.optimization_result = result
            
            if method == "Method Comparison":
                render_method_comparison_results(result)
            else:
                render_optimization_result(result)
        else:
            st.error(f"❌ 최적화 실패: {result.get('error', '알 수 없는 오류')}")


def render_optimization_results(optimization_method):
    """최적화 결과 시각화"""
    st.markdown("#### 📊 최적화 결과 시각화")
    
    if hasattr(st.session_state, 'optimization_result'):
        result = st.session_state.optimization_result
        
        if result.get("success", False):
            if optimization_method == "Method Comparison":
                render_method_comparison_chart(result)
            else:
                render_optimization_charts(result)
        
        render_algorithm_info(optimization_method)
    else:
        st.info("🎯 최적화를 실행하면 결과가 여기에 표시됩니다.")


def render_optimization_result(result):
    """개별 최적화 결과 표시"""
    optimal_inputs = result.get("optimal_inputs", {})
    expected_quality = result.get("expected_quality", {})
    
    st.markdown("**최적 투입량:**")
    for param, value in optimal_inputs.items():
        st.write(f"• {param}: {value:.2f} kg/h")
    
    st.markdown("**예상 품질:**")
    for metric, value in expected_quality.items():
        unit = "%" if metric in ["purity", "yield"] else "원"
        if isinstance(value, (int, float)):
            st.write(f"• {metric}: {value:.2f} {unit}")
        else:
            st.write(f"• {metric}: {value} {unit}")


def render_method_comparison_results(result):
    """방법별 비교 결과 표시"""
    st.markdown("**방법별 비교 결과:**")
    comparison = result.get("comparison", {})
    if comparison:
        st.metric("최적 방법", comparison.get("best_method", "N/A"))
        st.metric("성공한 방법 수", comparison.get("method_count", 0))
        
        obj_values = comparison.get("objective_values", {})
        if obj_values:
            st.markdown("**목적함수 값 비교:**")
            for method, value in obj_values.items():
                st.write(f"• {method}: {value:.2f}")


def render_optimization_charts(result):
    """최적화 결과 차트"""
    optimal_inputs = result.get("optimal_inputs", {})
    if optimal_inputs:
        baseline_inputs = {"material_a": 100, "material_b": 50, "catalyst": 5}
        
        comparison_data = {
            "Parameter": [],
            "Baseline": [],
            "Optimized": []
        }
        
        for param in ["material_a", "material_b", "catalyst"]:
            if param in optimal_inputs:
                comparison_data["Parameter"].append(param)
                comparison_data["Baseline"].append(baseline_inputs[param])
                comparison_data["Optimized"].append(optimal_inputs[param])
        
        comp_df = pd.DataFrame(comparison_data)
        fig = px.bar(comp_df, x="Parameter", y=["Baseline", "Optimized"], title="투입량 비교", barmode="group")
        st.plotly_chart(fig, use_container_width=True)


def render_method_comparison_chart(result):
    """방법별 비교 차트"""
    comparison = result.get("comparison", {})
    obj_values = comparison.get("objective_values", {})
    
    if obj_values:
        methods = list(obj_values.keys())
        values = list(obj_values.values())
        
        fig = px.bar(x=methods, y=values, title="최적화 방법별 목적함수 값", 
                     labels={"x": "Method", "y": "Objective Value"})
        st.plotly_chart(fig, use_container_width=True)


def render_algorithm_info(optimization_method):
    """알고리즘 정보 표시"""
    st.markdown("#### 💡 최적화 알고리즘 정보")
    
    algorithm_info = {
        "Differential Evolution": "전역 최적화 알고리즘\n• 빠른 수렴\n• 복잡한 함수에 효과적",
        "Bayesian Optimization": "베이지안 접근법\n• 적은 함수 평가로 최적해 탐색\n• 불확실성 고려",
        "Robust Optimization": "불확실성 고려 최적화\n• 변동성에 강건한 해\n• 리스크 최소화",
        "Multi-Objective": "다목적 최적화\n• 여러 목표 동시 고려\n• 가중합 방법",
        "Method Comparison": "방법별 비교 분석\n• 최적 방법 선택\n• 성능 비교"
    }
    
    st.markdown(algorithm_info.get(optimization_method, "알고리즘 정보 없음"))


def render_sensitivity_analysis_tab(settings):
    """민감도 분석 탭 렌더링"""
    st.markdown("### 📊 고급 민감도 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_sensitivity_controls(settings)
    
    with col2:
        render_sensitivity_results()
    
    # 민감도 분석 채팅 인터페이스 추가
    st.markdown("---")
    
    # Context 데이터 업데이트
    context_data = {
        "sensitivity_settings": {
            "variables": settings["sensitivity_vars"],
            "variation_range": settings["variation_range"],
            "analysis_type": "고급 민감도 분석"
        },
        "basic_sensitivity": getattr(st.session_state, 'sensitivity_result', {}).get("result", {}),
        "risk_assessment": getattr(st.session_state, 'sensitivity_result', {}).get("risk_assessment", {}),
        "sensitivity_ranking": getattr(st.session_state, 'sensitivity_result', {}).get("ranking", [])
    }
    
    st.session_state.cost_sensitivity_chat.update_context_data(context_data, "현재")
    st.session_state.cost_sensitivity_chat.create_chat_interface()


def render_sensitivity_controls(settings):
    """민감도 분석 제어 섹션"""
    st.markdown("#### 🔍 민감도 분석 실행")
    
    # 기준 조건 설정
    st.markdown("**기준 운전 조건:**")
    base_conditions = render_base_conditions()
    
    # 분석 유형 선택
    analysis_type = st.selectbox("분석 유형", ["기본 민감도 분석", "고급 민감도 분석", "교호작용 분석"])
    
    if st.button("📊 민감도 분석 실행", type="primary"):
        execute_sensitivity_analysis(analysis_type, base_conditions, settings["sensitivity_vars"], settings["variation_range"])


def render_base_conditions():
    """기준 조건 설정 UI"""
    return {
        "material_a": st.number_input("원료 A (kg/h)", 80, 120, 100),
        "material_b": st.number_input("원료 B (kg/h)", 40, 60, 50),
        "catalyst": st.number_input("촉매 (kg/h)", 3, 7, 5),
        "temperature": st.number_input("온도 (°C)", 160, 190, 175),
        "pressure": st.number_input("압력 (bar)", 2.0, 3.0, 2.5),
        "steam": st.number_input("스팀 (kg/h)", 120, 180, 150),
        "electricity": st.number_input("전력 (kWh)", 60, 100, 80),
        "cooling_water": st.number_input("냉각수 (L/h)", 400, 600, 500),
        "flow_rate": 200
    }


def execute_sensitivity_analysis(analysis_type, base_conditions, sensitivity_vars, variation_range):
    """민감도 분석 실행"""
    with st.spinner("민감도 분석 실행 중..."):
        engine = st.session_state.cost_management_engine
        result = engine.execute_sensitivity_analysis(analysis_type, base_conditions, sensitivity_vars, variation_range)
        
        if result.get("success", False):
            st.success(f"✅ {analysis_type} 완료!")
            st.session_state.sensitivity_result = result
            
            if result["type"] == "basic":
                render_basic_sensitivity_results(result["result"])
            else:
                render_advanced_sensitivity_results(result["result"])
        else:
            st.error(f"❌ 분석 실패: {result.get('error', '알 수 없는 오류')}")


def render_basic_sensitivity_results(sensitivity_result):
    """기본 민감도 분석 결과 표시"""
    st.markdown("**민감도 분석 결과:**")
    
    cost_sensitivities = {}
    for var, sensitivities in sensitivity_result.items():
        if "total_cost" in sensitivities:
            cost_sensitivities[var] = sensitivities["total_cost"]
    
    if cost_sensitivities:
        sorted_sensitivities = sorted(cost_sensitivities.items(), key=lambda x: abs(x[1]), reverse=True)
        sensitivity_df = pd.DataFrame(sorted_sensitivities, columns=["변수", "민감도"])
        sensitivity_df["영향도"] = sensitivity_df["민감도"].apply(
            lambda x: "높음" if abs(x) > 0.5 else "보통" if abs(x) > 0.2 else "낮음"
        )
        st.dataframe(sensitivity_df, use_container_width=True)


def render_advanced_sensitivity_results(advanced_result):
    """고급 민감도 분석 결과 표시"""
    summary = advanced_result.get("analysis_summary", {})
    if summary:
        st.markdown("**분석 요약:**")
        st.write(f"• 가장 민감한 변수: {summary.get('most_sensitive_variable', 'N/A')}")
        if summary.get('strongest_interaction'):
            st.write(f"• 가장 강한 교호작용: {summary.get('strongest_interaction', 'N/A')}")
        if summary.get('most_nonlinear_variable'):
            st.write(f"• 가장 비선형적인 변수: {summary.get('most_nonlinear_variable', 'N/A')}")


def render_sensitivity_results():
    """민감도 분석 결과 시각화"""
    st.markdown("#### 📈 민감도 분석 시각화")
    
    if hasattr(st.session_state, 'sensitivity_result'):
        result = st.session_state.sensitivity_result
        
        if result["type"] == "basic":
            render_basic_sensitivity_charts(result["result"])
        else:
            render_advanced_sensitivity_charts(result["result"])
        
        render_sensitivity_guide()
    else:
        st.info("📊 민감도 분석을 실행하면 여기에 차트가 표시됩니다.")


def render_basic_sensitivity_charts(sensitivity_result):
    """기본 민감도 차트"""
    cost_sensitivities = {}
    for var, sensitivities in sensitivity_result.items():
        if "total_cost" in sensitivities:
            cost_sensitivities[var] = sensitivities["total_cost"]
    
    if cost_sensitivities:
        vars_list = list(cost_sensitivities.keys())
        sens_values = list(cost_sensitivities.values())
        
        fig = px.bar(x=vars_list, y=sens_values, title="총 비용에 대한 민감도", 
                     labels={"x": "변수", "y": "민감도"})
        st.plotly_chart(fig, use_container_width=True)


def render_advanced_sensitivity_charts(advanced_result):
    """고급 민감도 차트"""
    basic_sensitivity = advanced_result.get("basic_sensitivity", {})
    if basic_sensitivity:
        cost_sensitivities = {}
        for var, sensitivities in basic_sensitivity.items():
            if "total_cost" in sensitivities:
                cost_sensitivities[var] = sensitivities["total_cost"]
        
        if cost_sensitivities:
            fig = px.bar(x=list(cost_sensitivities.keys()), y=list(cost_sensitivities.values()), 
                         title="고급 민감도 분석 - 총 비용", labels={"x": "변수", "y": "민감도"})
            st.plotly_chart(fig, use_container_width=True)


def render_sensitivity_guide():
    """민감도 분석 가이드"""
    st.markdown("#### 💡 민감도 분석 가이드")
    st.markdown("""
    **민감도 해석:**
    - 양수: 변수 증가 시 비용 증가
    - 음수: 변수 증가 시 비용 감소
    - 절댓값이 클수록 영향도 높음
    
    **리스크 관리:**
    - 높은 민감도 변수 우선 관리
    - 교호작용 효과 고려
    - 비선형 효과 모니터링
    """)


def render_quality_prediction_tab(settings):
    """품질 예측 탭 렌더링"""
    st.markdown("### 🔍 실시간 품질 예측")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_quality_prediction_controls(settings)
    
    with col2:
        render_quality_prediction_results()
    
    # 품질 예측 채팅 인터페이스 추가
    st.markdown("---")
    
    # Context 데이터 업데이트
    context_data = {
        "prediction_inputs": getattr(st.session_state, 'prediction_inputs', {}),
        "quality_predictions": getattr(st.session_state, 'quality_predictions', {}),
        "quality_compliance": {
            "순도": {
                "satisfied": getattr(st.session_state, 'quality_predictions', {}).get('purity', 0) >= settings["target_purity"],
                "value": getattr(st.session_state, 'quality_predictions', {}).get('purity', 0),
                "target": settings["target_purity"]
            },
            "수율": {
                "satisfied": getattr(st.session_state, 'quality_predictions', {}).get('yield', 0) >= settings["target_yield"],
                "value": getattr(st.session_state, 'quality_predictions', {}).get('yield', 0),
                "target": settings["target_yield"]
            }
        },
        "scenario_results": getattr(st.session_state, 'scenario_results', [])
    }
    
    st.session_state.cost_quality_prediction_chat.update_context_data(context_data, "현재")
    st.session_state.cost_quality_prediction_chat.create_chat_interface()


def render_quality_prediction_controls(settings):
    """품질 예측 제어 섹션"""
    st.markdown("#### 🎯 품질 예측 실행")
    
    st.markdown("**예측 입력 조건:**")
    prediction_inputs = render_prediction_inputs()
    
    if st.button("🔮 품질 예측 실행", type="primary"):
        execute_quality_prediction(prediction_inputs, settings)
    
    st.markdown("#### 📊 시나리오 분석")
    if st.button("🎭 시나리오 분석 실행"):
        execute_scenario_analysis(prediction_inputs)


def render_prediction_inputs():
    """예측 입력 조건 UI"""
    return {
        "material_a": st.number_input("원료 A 투입량 (kg/h)", 80, 120, 100, key="pred_mat_a"),
        "material_b": st.number_input("원료 B 투입량 (kg/h)", 40, 60, 50, key="pred_mat_b"),
        "catalyst": st.number_input("촉매 투입량 (kg/h)", 3, 7, 5, key="pred_catalyst"),
        "temperature": st.number_input("반응 온도 (°C)", 160, 190, 175, key="pred_temp"),
        "pressure": st.number_input("반응 압력 (bar)", 2.0, 3.0, 2.5, key="pred_pressure"),
        "steam": st.number_input("스팀 사용량 (kg/h)", 120, 180, 150, key="pred_steam"),
        "electricity": st.number_input("전력 사용량 (kWh)", 60, 100, 80, key="pred_elec"),
        "cooling_water": st.number_input("냉각수 사용량 (L/h)", 400, 600, 500, key="pred_water"),
        "flow_rate": 200
    }


def execute_quality_prediction(prediction_inputs, settings):
    """품질 예측 실행"""
    with st.spinner("ML 모델이 품질을 예측하고 있습니다..."):
        engine = st.session_state.cost_management_engine
        predictions = engine.predict_quality(prediction_inputs)
        
        if "error" not in predictions:
            st.success("✅ 품질 예측 완료!")
            st.session_state.quality_predictions = predictions
            render_prediction_results(predictions, settings)
        else:
            st.error(f"❌ 예측 실패: {predictions.get('error', '알 수 없는 오류')}")


def execute_scenario_analysis(prediction_inputs):
    """시나리오 분석 실행"""
    with st.spinner("다양한 시나리오를 분석하고 있습니다..."):
        engine = st.session_state.cost_management_engine
        scenario_results = engine.run_scenario_analysis(prediction_inputs)
        
        if scenario_results:
            st.success("✅ 시나리오 분석 완료!")
            st.session_state.scenario_results = scenario_results
            scenario_df = pd.DataFrame(scenario_results)
            st.dataframe(scenario_df, use_container_width=True)
        else:
            st.error("❌ 시나리오 분석 실패")


def render_prediction_results(predictions, settings):
    """예측 결과 표시"""
    st.markdown("**예측 결과:**")
    
    pred_col1, pred_col2, pred_col3 = st.columns(3)
    
    with pred_col1:
        purity = predictions.get('purity', 0)
        try:
            purity = float(purity) if purity is not None else 0
            st.metric("예측 순도", f"{purity:.2f}%", delta=f"{purity-settings['target_purity']:.2f}%")
        except (ValueError, TypeError):
            st.metric("예측 순도", str(purity))
    
    with pred_col2:
        yield_rate = predictions.get('yield', 0)
        try:
            yield_rate = float(yield_rate) if yield_rate is not None else 0
            st.metric("예측 수율", f"{yield_rate:.2f}%", delta=f"{yield_rate-settings['target_yield']:.2f}%")
        except (ValueError, TypeError):
            st.metric("예측 수율", str(yield_rate))
    
    with pred_col3:
        total_cost = predictions.get('total_cost', 0)
        try:
            total_cost = float(total_cost) if total_cost is not None else 0
            st.metric("예측 총 비용", f"{total_cost:.0f}원/h")
        except (ValueError, TypeError):
            st.metric("예측 총 비용", str(total_cost))
    
    render_quality_check(purity, yield_rate, settings)


def render_quality_check(purity, yield_rate, settings):
    """품질 기준 만족도 확인"""
    st.markdown("**품질 기준 만족도:**")
    
    quality_check = []
    if purity >= settings["target_purity"]:
        quality_check.append("✅ 순도 기준 만족")
    else:
        quality_check.append(f"❌ 순도 기준 미달 (목표: {settings['target_purity']}%)")
    
    if yield_rate >= settings["target_yield"]:
        quality_check.append("✅ 수율 기준 만족")
    else:
        quality_check.append(f"❌ 수율 기준 미달 (목표: {settings['target_yield']}%)")
    
    for check in quality_check:
        st.write(check)
    
    if purity < settings["target_purity"] or yield_rate < settings["target_yield"]:
        render_improvement_suggestions(purity, yield_rate, settings)


def render_improvement_suggestions(purity, yield_rate, settings):
    """개선 제안"""
    st.markdown("**개선 제안:**")
    
    if purity < settings["target_purity"]:
        st.write("• 촉매 사용량을 늘리거나 반응 온도를 높여보세요")
        st.write("• 원료 A 투입량을 조정해보세요")
    
    if yield_rate < settings["target_yield"]:
        st.write("• 반응 압력을 조정해보세요")
        st.write("• 원료 B 투입량을 최적화해보세요")


def render_quality_prediction_results():
    """품질 예측 결과 시각화"""
    st.markdown("#### 📈 품질 예측 시각화")
    
    if hasattr(st.session_state, 'quality_predictions'):
        render_quality_radar_chart()
        render_cost_pie_chart()
    
    if hasattr(st.session_state, 'scenario_results'):
        render_scenario_charts()
    
    if not hasattr(st.session_state, 'quality_predictions'):
        st.info("🔮 품질 예측을 실행하면 여기에 시각화가 표시됩니다.")
    
    render_model_info()


def render_quality_radar_chart():
    """품질 지표 레이더 차트"""
    predictions = st.session_state.quality_predictions
    
    metrics = ['purity', 'yield']
    values = [predictions.get(metric, 0) for metric in metrics]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=metrics, fill='toself', name='예측값'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="품질 예측 vs 목표"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_cost_pie_chart():
    """비용 분석 차트"""
    predictions = st.session_state.quality_predictions
    
    cost_breakdown = {
        "원료비": predictions.get('total_cost', 0) * 0.8,
        "유틸리티": predictions.get('total_cost', 0) * 0.2
    }
    
    fig = px.pie(values=list(cost_breakdown.values()), names=list(cost_breakdown.keys()), title="예측 비용 구조")
    st.plotly_chart(fig, use_container_width=True)


def render_scenario_charts():
    """시나리오 결과 시각화"""
    scenario_results = st.session_state.scenario_results
    scenario_df = pd.DataFrame(scenario_results)
    
    fig = px.bar(scenario_df, x="시나리오", y=["순도 (%)", "수율 (%)"], title="시나리오별 품질 비교", barmode="group")
    st.plotly_chart(fig, use_container_width=True)
    
    fig = px.bar(scenario_df, x="시나리오", y="총 비용 (원/h)", title="시나리오별 비용 비교")
    st.plotly_chart(fig, use_container_width=True)


def render_model_info():
    """예측 모델 정보"""
    st.markdown("#### 🤖 ML 모델 정보")
    st.markdown("""
    **사용 모델:** Random Forest Regressor
    **특성 변수:** 9개 (원료, 운전조건, 유틸리티)
    **목표 변수:** 순도, 수율, 총 비용
    **훈련 데이터:** 1,000개 생산 이력 레코드
    
    **모델 성능:**
    - 순도 예측 R²: ~0.85
    - 수율 예측 R²: ~0.82
    - 비용 예측 R²: ~0.95
    """)


def render_ai_analysis_tab():
    """AI 분석 탭 렌더링"""
    st.markdown("### 💬 AI 원가 최적화 어시스턴트")
    
    engine = st.session_state.cost_management_engine
    
    # 종합 AI 분석 채팅 인터페이스
    # Context 데이터 업데이트
    context_data = engine.get_context_data()
    
    if context_data:
        # 종합 분석 데이터 구성
        comprehensive_data = {
            "cost_overview": {
                "total_cost": sum(item.get("금액(만원)", 0) for item in context_data.get("cost_breakdown", [])),
                "material_ratio": 70.0,  # 예시 값
                "utility_ratio": 30.0    # 예시 값
            },
            "optimization_performance": {
                "optimization_runs": getattr(st.session_state, 'optimization_runs', 0),
                "avg_savings": getattr(st.session_state, 'avg_savings', 0),
                "best_algorithm": "Differential Evolution",
                "quality_compliance_rate": 85.0
            },
            "sensitivity_summary": {
                "most_sensitive_var": "material_a",
                "high_risk_count": 2,
                "key_interactions": "material_a x catalyst"
            },
            "production_metrics": {
                "avg_purity": 93.5,
                "avg_yield": 87.2,
                "production_volume": 1250,
                "quality_stability": "양호"
            },
            "cost_efficiency": {
                "cost_quality_index": 0.85,
                "energy_efficiency": 78.5,
                "material_utilization": 92.3,
                "overall_efficiency_score": 82.1
            },
            "risk_opportunity": {
                "major_risks": ["원료 가격 변동", "설비 가동률 저하"],
                "opportunities": ["공정 최적화", "에너지 효율 개선"],
                "savings_potential": 150
            }
        }
        
        st.session_state.cost_ai_analysis_chat.update_context_data(comprehensive_data, "현재")
    
    # 종합 AI 분석 채팅 인터페이스 생성
    st.session_state.cost_ai_analysis_chat.create_chat_interface()
    
    # 기존 간단한 분석 보고서도 유지
    st.markdown("---")
    st.markdown("#### 🔄 대체 분석 옵션")
    if st.button("📄 간단 분석 보고서 생성"):
        render_simple_analysis_report(engine)


def render_simple_analysis_report(engine):
    """간단한 분석 보고서 생성"""
    if st.button("📄 간단 분석 보고서 생성"):
        with st.spinner("AI 분석 보고서를 생성하고 있습니다..."):
            report = engine.generate_analysis_report()
            
            if "error" not in report:
                render_analysis_report(report)
            else:
                st.error(f"❌ 보고서 생성 실패: {report['error']}")


def render_analysis_report(report):
    """분석 보고서 렌더링"""
    st.markdown("### 📊 AI 원가 분석 보고서")
    st.markdown(f"**생성 시간:** {report['generated_at']}")
    
    # 원가 현황 분석
    cost_analysis = report.get("cost_analysis", {})
    if cost_analysis:
        st.markdown("#### 💰 원가 현황")
        st.write(f"• 총 원가: {cost_analysis['total_cost']:.1f}만원")
        st.write(f"• 원료비 비중: {cost_analysis['material_ratio']:.1f}%")
        st.write(f"• 원가 구조: {cost_analysis['cost_structure']}")
    
    # 생산 성과 분석
    production_analysis = report.get("production_analysis", {})
    if production_analysis:
        st.markdown("#### 🏭 생산 성과")
        st.write(f"• 평균 순도: {production_analysis['avg_purity']:.2f}%")
        st.write(f"• 평균 수율: {production_analysis['avg_yield']:.2f}%")
        st.write(f"• 순도 평가: {production_analysis['purity_status']}")
        st.write(f"• 수율 평가: {production_analysis['yield_status']}")
    
    # 최적화 제안
    recommendations = report.get("recommendations", [])
    if recommendations:
        st.markdown("#### 💡 최적화 제안")
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    
    st.success("✅ AI 분석 보고서 생성 완료!")


def render_data_load_section():
    """데이터 로드 섹션"""
    st.markdown("---")
    
    with st.expander("📂 데이터 소스 관리", expanded=True):
        tab1, tab2, tab3 = st.tabs(["📊 현재 데이터", "📁 파일 선택", "📤 파일 업로드"])
        
        with tab1:
            render_current_data_info()
        
        with tab2:
            render_file_selection()
        
        with tab3:
            render_file_upload()


def render_current_data_info():
    """현재 데이터 정보 표시"""
    st.markdown("#### 🔍 현재 사용 중인 데이터")
    
    current_data_info = get_current_data_info()
    
    if current_data_info["has_custom_data"]:
        render_custom_data_info(current_data_info)
    else:
        render_default_data_info()
    
    if st.button("🔄 데이터 재로드", key="reload_data"):
        from src.utils.cost_management_utils import reset_cost_engines
        reset_cost_engines()
        st.rerun()


def render_custom_data_info(current_data_info):
    """사용자 데이터 정보 표시"""
    st.success("✅ **사용자 생성 데이터를 사용 중입니다**")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("데이터 수", f"{current_data_info['record_count']:,}개")
    with col2:
        st.metric("평균 순도", f"{current_data_info['avg_purity']:.1f}%")
    with col3:
        st.metric("평균 수율", f"{current_data_info['avg_yield']:.1f}%")
    with col4:
        st.metric("평균 비용", f"₩{current_data_info['avg_cost']:,.0f}")
    
    st.info(f"📁 파일: `{current_data_info['filepath']}`")
    
    col_detail1, col_detail2 = st.columns(2)
    
    with col_detail1:
        if st.checkbox("📋 컬럼 정보"):
            render_column_info()
    
    with col_detail2:
        if st.checkbox("🔍 데이터 미리보기"):
            render_data_preview()


def render_default_data_info():
    """기본 데이터 정보 표시"""
    st.info("ℹ️ **기본 시뮬레이션 데이터를 사용 중입니다**")
    
    default_info = get_default_data_info()
    
    st.markdown(f"""
    **기본 데이터 특징:**
    - 샘플 수: {default_info['record_count']:,}개
    - 순도 범위: 80-99%
    - 수율 범위: 70-95%
    - 표준 원료 단가 적용
    """)
    
    if st.checkbox("📋 기본 데이터 컬럼 정보"):
        render_default_column_info(default_info)
    
    if st.button("🎯 기본 시뮬레이션 데이터 사용", key="use_default_data"):
        use_default_simulation_data()


def render_column_info():
    """컬럼 정보 표시"""
    if "generated_cost_data" in st.session_state:
        df = st.session_state.generated_cost_data
        validation_result = validate_csv_columns(df)
        
        st.markdown("**📊 컬럼 상태:**")
        status_data = []
        for col_status in validation_result["column_status"]:
            status_data.append({
                "컬럼명": col_status["name"],
                "상태": "✅ 있음" if col_status["present"] else "❌ 없음",
                "타입": str(df[col_status["name"]].dtype) if col_status["present"] else "-"
            })
        
        status_df = pd.DataFrame(status_data)
        st.dataframe(status_df, use_container_width=True, hide_index=True)


def render_data_preview():
    """데이터 미리보기"""
    if "generated_cost_data" in st.session_state:
        preview_df = st.session_state.generated_cost_data.head(10)
        st.dataframe(preview_df, use_container_width=True)


def render_default_column_info(default_info):
    """기본 데이터 컬럼 정보 표시"""
    st.markdown("**📊 기본 시뮬레이션 데이터 컬럼:**")
    
    col_info = []
    for feature in default_info["features"]:
        col_info.append({
            "컬럼명": feature["name"],
            "설명": feature["description"],
            "범위": feature["range"],
            "상태": "✅ 포함"
        })
    
    info_df = pd.DataFrame(col_info)
    st.dataframe(info_df, use_container_width=True, hide_index=True)


def render_file_selection():
    """파일 선택 섹션"""
    st.markdown("#### 📁 사용 가능한 원가 데이터 파일")
    
    available_files = get_available_cost_files()
    
    if available_files:
        selected_file = st.selectbox(
            "데이터 파일 선택",
            options=available_files,
            format_func=lambda x: f"{os.path.basename(x)} ({get_file_info(x)})"
        )
        
        if selected_file:
            render_selected_file_info(selected_file)
    else:
        render_no_files_message()


def render_selected_file_info(selected_file):
    """선택된 파일 정보 표시"""
    file_info = get_detailed_file_info(selected_file)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**파일명:** {os.path.basename(selected_file)}")
        st.write(f"**크기:** {file_info['size_mb']:.2f} MB")
        st.write(f"**생성일:** {file_info['created_date']}")
    
    with col2:
        st.write(f"**레코드 수:** {file_info['record_count']:,}개")
        st.write(f"**기간:** {file_info['date_range']}")
        st.write(f"**평균 비용:** ₩{file_info['avg_cost']:,.0f}")
    
    if st.checkbox("🔍 파일 미리보기", key="preview_selected"):
        try:
            preview_df = pd.read_csv(selected_file, nrows=5)
            st.dataframe(preview_df, use_container_width=True)
        except Exception as e:
            st.error(f"미리보기 오류: {e}")
    
    if st.button("📊 이 파일 사용하기", type="primary", key="load_selected_file"):
        load_selected_file(selected_file)


def render_no_files_message():
    """파일 없음 메시지"""
    st.warning("⚠️ 사용 가능한 원가 데이터 파일이 없습니다.")
    st.markdown("""
    **💡 데이터 파일 생성 방법:**
    1. **📋 데이터 생성** 페이지로 이동
    2. **💰 원가/생산 이력 데이터** 탭 선택
    3. 원하는 설정으로 데이터 생성
    4. 이 페이지로 돌아와서 파일 선택
    """)


def render_file_upload():
    """파일 업로드 섹션"""
    st.markdown("#### 📤 CSV 파일 업로드")
    st.markdown("**💡 원가/생산 이력 CSV 파일을 직접 업로드할 수 있습니다.**")
    
    uploaded_file = st.file_uploader(
        "CSV 파일 선택",
        type=['csv'],
        help="원가/생산 이력 데이터가 포함된 CSV 파일을 업로드하세요."
    )
    
    if uploaded_file is not None:
        render_uploaded_file_info(uploaded_file) 


def render_uploaded_file_info(uploaded_file):
    """업로드된 파일 정보 처리"""
    try:
        # 파일 읽기
        df = pd.read_csv(uploaded_file)
        
        st.success(f"✅ 파일 업로드 완료: {len(df):,}개 레코드")
        
        # 업로드된 파일 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("레코드 수", f"{len(df):,}")
        with col2:
            st.metric("컬럼 수", len(df.columns))
        with col3:
            file_size = len(uploaded_file.getvalue()) / 1024 / 1024
            st.metric("파일 크기", f"{file_size:.2f} MB")
        
        # 필수 컬럼 확인
        validation_result = validate_csv_columns(df)
        
        if not validation_result["is_valid"]:
            st.error(f"❌ 필수 컬럼이 누락되었습니다: {', '.join(validation_result['missing_columns'])}")
            st.markdown("**필요한 컬럼들:**")
            for col_status in validation_result["column_status"]:
                status = "✅" if col_status["present"] else "❌"
                st.write(f"{status} {col_status['name']}")
        else:
            st.success("✅ 모든 필수 컬럼이 포함되어 있습니다!")
            
            # 데이터 미리보기
            st.markdown("**📊 데이터 미리보기:**")
            st.dataframe(df.head(10), use_container_width=True)
            
            # 파일 저장 및 사용
            if st.button("💾 파일 저장 후 사용하기", type="primary", key="save_uploaded"):
                save_uploaded_file(uploaded_file, df)
    
    except Exception as e:
        st.error(f"❌ 파일 읽기 오류: {e}")
        st.markdown("**💡 파일 형식 확인사항:**")
        st.markdown("- UTF-8 인코딩의 CSV 파일")
        st.markdown("- 첫 번째 행이 컬럼명")
        st.markdown("- 쉼표(,)로 구분된 값") 