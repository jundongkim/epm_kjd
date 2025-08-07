"""
DX-AI Manufacturing Copilot - 실험 설계 페이지

실험 설계 도구, DoE 분석 및 최적화 페이지입니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from typing import Dict, List, Any, Optional

# 새로운 백엔드 엔진 및 유틸리티 import
from src.core.experimental_design_engine import (
    DOEDesignEngine,
    BayesianOptimizationEngine,
    ReportGenerationEngine,
    ExperimentType,
    OptimizationGoal
)
from src.utils.experimental_design_utils import (
    analyze_experiment_efficiency,
    get_correlation_analysis,
    analyze_optimization_results,
    create_experiment_summary,
    validate_experiment_setup
)
from src.core.chat_manager import ChatManager, setup_chat_sidebar
from src.core.tab_chat_managers import (
    ExperimentDesignChatManager, 
    OptimizationChatManager, 
    ExperimentReportChatManager
)


def experimental_design_page():
    """실험 설계 페이지 메인 함수"""
    st.markdown("## 🔬 실험 설계")
    
    # 챗봇 매니저 초기화
    _initialize_chat_managers()
    
    # 사이드바 챗봇 설정
    setup_chat_sidebar(st.session_state.chat_manager)
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🔬 실험 설계", "📊 최적화", "📋 AI 보고서"])
    
    with tab1:
        experiment_design_tab()
    
    with tab2:
        optimization_tab()
    
    with tab3:
        report_generation_tab()


def _initialize_chat_managers():
    """챗봇 매니저 초기화"""
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = ChatManager()
    
    if 'experimental_design_chat' not in st.session_state:
        st.session_state.experimental_design_chat = ExperimentDesignChatManager(st.session_state.chat_manager)
    
    if 'optimization_chat' not in st.session_state:
        st.session_state.optimization_chat = OptimizationChatManager(st.session_state.chat_manager)
    
    if 'experiment_report_chat' not in st.session_state:
        st.session_state.experiment_report_chat = ExperimentReportChatManager(st.session_state.chat_manager)


def experiment_design_tab():
    """실험 설계 탭"""
    st.markdown("### 🔬 실험 설계 도구")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # 실험 파라미터 설정
        experiment_params = _render_experiment_parameters()
        
        # 실험 계획 생성
        if st.button("🧪 실험 계획 생성", type="primary", key="generate_experiment_plan"):
            _generate_experiment_plan(experiment_params)
    
    with col2:
        # 실험 설계 가이드
        _render_experiment_guide()
    
    # 챗봇 인터페이스
    _render_experiment_chat_interface()


def _render_experiment_parameters() -> Dict[str, Any]:
    """실험 파라미터 설정 UI"""
    st.markdown("#### 📝 실험 파라미터")
    
    params = {}
    
    # DoE 설정
    with st.expander("⚙️ DoE (Design of Experiments) 설정", expanded=True):
        params['experiment_type'] = st.selectbox(
            "실험 유형", 
            [e.value for e in ExperimentType]
        )
        
        params['factors'] = st.multiselect(
            "실험 인자 선택",
            ["온도", "압력", "pH", "반응시간", "촉매농도", "교반속도"],
            default=["온도", "압력", "pH"]
        )
        
        params['num_runs'] = st.slider("실험 횟수", 10, 100, 25)
        params['replications'] = st.slider("반복 횟수", 1, 5, 2)
    
    # 목표 설정
    with st.expander("🎯 목표 설정"):
        params['target_purity'] = st.slider("목표 순도 (%)", 95.0, 99.0, 97.5)
        params['target_yield'] = st.slider("목표 수율 (%)", 85.0, 98.0, 92.0)
        params['optimization_goal'] = st.selectbox(
            "최적화 목표", 
            [g.value for g in OptimizationGoal]
        )
    
    return params


def _generate_experiment_plan(params: Dict[str, Any]):
    """실험 계획 생성"""
    try:
        # 파라미터 유효성 검증
        validation = validate_experiment_setup(params)
        
        if not validation['is_valid']:
            st.error(f"❌ 실험 설정 오류: {', '.join(validation['errors'])}")
            return
        
        if validation['warnings']:
            for warning in validation['warnings']:
                st.warning(f"⚠️ {warning}")
        
        # DoE 엔진 사용하여 실험 계획 생성
        doe_engine = DOEDesignEngine()
        
        with st.spinner("실험 계획 생성 중..."):
            experiment_plan, metadata = doe_engine.generate_experiment_plan(
                experiment_type=params['experiment_type'],
                factors=params['factors'],
                num_runs=params['num_runs'],
                replications=params['replications'],
                target_purity=params['target_purity'],
                target_yield=params['target_yield']
            )
            
            # 세션 상태에 저장
            st.session_state.experiment_plan = experiment_plan
            st.session_state.experiment_metadata = metadata
            
            st.success("✅ 실험 계획이 생성되었습니다!")
            
            # 실험 계획 표시
            st.dataframe(experiment_plan, use_container_width=True)
            
            # 실험 계획 분석
            analysis = analyze_experiment_efficiency(experiment_plan, params['factors'])
            
            # 분석 결과 표시
            _display_experiment_analysis(analysis, metadata)
            
    except Exception as e:
        st.error(f"❌ 실험 계획 생성 중 오류 발생: {str(e)}")


def _display_experiment_analysis(analysis: Dict[str, Any], metadata: Dict[str, Any]):
    """실험 계획 분석 결과 표시"""
    st.markdown("#### 📊 실험 계획 분석")
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 실험 횟수", analysis.get('total_runs', 0))
    
    with col2:
        st.metric("분석 인자 수", analysis.get('factors_analyzed', 0))
    
    with col3:
        st.metric("설계 효율성", f"{metadata.get('design_efficiency', 0)}%")
    
    with col4:
        power_analysis = metadata.get('power_analysis', {})
        st.metric("검정력", f"{power_analysis.get('statistical_power', 0):.3f}")
    
    # 권장사항
    if analysis.get('recommendations'):
        st.markdown("#### 💡 권장사항")
        for rec in analysis['recommendations']:
            st.info(f"• {rec}")


def _render_experiment_guide():
    """실험 설계 가이드 UI"""
    st.markdown("#### 📈 실험 계획 요약")
    
    if 'experiment_plan' in st.session_state:
        plan = st.session_state.experiment_plan
        metadata = st.session_state.experiment_metadata
        
        st.success("✅ 실험 계획이 준비되었습니다!")
        
        # 요약 정보
        st.markdown(f"**실험 유형**: {metadata.get('experiment_type', 'N/A')}")
        st.markdown(f"**실험 횟수**: {len(plan)}회")
        st.markdown(f"**인자 수**: {len(metadata.get('factors', []))}개")
        st.markdown(f"**목표 순도**: {metadata.get('target_purity', 0)}%")
        st.markdown(f"**목표 수율**: {metadata.get('target_yield', 0)}%")
        
        # 상관관계 분석
        correlation_analysis = get_correlation_analysis(plan, metadata.get('factors', []))
        if 'pairwise_correlations' in correlation_analysis:
            st.markdown("#### 🔗 인자 상관관계")
            for pair, corr_info in correlation_analysis['pairwise_correlations'].items():
                st.markdown(f"- {pair}: {corr_info['strength']} ({corr_info['correlation']:.3f})")
    else:
        st.info("🔬 실험 계획을 생성하면 여기에 요약이 표시됩니다.")
    
    # 실험 설계 방법론 가이드
    _render_methodology_guide()


def _render_methodology_guide():
    """실험 설계 방법론 가이드"""
    st.markdown("#### 🔬 **실험 설계 방법론 가이드**")
    
    with st.expander("📈 **Full Factorial (완전요인설계)**"):
        st.markdown("""
        **✨ 특징:**
        - 모든 인자 조합을 다 실험
        - 완전한 정보 확보 가능
        - 상호작용 효과 정확 분석
        
        **🎯 적용 상황:**
        - 인자 3-4개 이하
        - 정확한 상호작용 필요
        - 충분한 실험 자원
        """)
    
    with st.expander("🎯 **Fractional Factorial (부분요인설계)**"):
        st.markdown("""
        **✨ 특징:**
        - 실험 횟수 대폭 감소
        - 효율적 스크리닝
        - 중요 인자 빠른 선별
        
        **🎯 적용 상황:**
        - 인자 5개 이상
        - 초기 스크리닝 단계
        - 제한된 실험 자원
        """)
    
    with st.expander("🎪 **Central Composite (중심합성설계)**"):
        st.markdown("""
        **✨ 특징:**
        - 2차 곡선 모델링
        - 응답표면방법론(RSM)
        - 최적점 탐색 가능
        
        **🎯 적용 상황:**
        - 최적화가 목표
        - 곡선 관계 예상
        - 품질/수율 최대화
        """)
    
    with st.expander("🎲 **Box-Behnken Design**"):
        st.markdown("""
        **✨ 특징:**
        - 3수준 설계 (-1, 0, +1)
        - 경계점 없음 (안전)
        - 적당한 실험 횟수
        
        **🎯 적용 상황:**
        - 극단조건 위험
        - 안전한 실험 범위
        - 중간 수준 최적화
        """)


def _render_experiment_chat_interface():
    """실험 설계 챗봇 인터페이스"""
    st.markdown("---")
    
    # 컨텍스트 데이터 업데이트
    experiment_data = {
        'experiment_plan': st.session_state.get('experiment_plan'),
        'experiment_metadata': st.session_state.get('experiment_metadata')
    }
    
    st.session_state.experimental_design_chat.update_context_data(experiment_data, "현재 세션")
    st.session_state.experimental_design_chat.create_chat_interface()


def optimization_tab():
    """최적화 탭"""
    st.markdown("### 🎯 실험 최적화")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 최적화 설정
        optimization_settings = _render_optimization_settings()
        
        # 최적화 실행
        if st.button("🚀 최적화 실행", type="primary"):
            _run_optimization(optimization_settings)
    
    with col2:
        # 최적화 가이드
        _render_optimization_guide()
    
    # 챗봇 인터페이스
    _render_optimization_chat_interface()


def _render_optimization_settings() -> Dict[str, Any]:
    """최적화 설정 UI"""
    st.markdown("#### 📊 베이지안 최적화")
    
    settings = {}
    
    # 실험 설계 탭에서 설정한 인자들 확인
    experiment_factors = []
    experiment_metadata = st.session_state.get('experiment_metadata', {})
    
    if experiment_metadata and 'factors' in experiment_metadata:
        experiment_factors = experiment_metadata['factors']
        st.success(f"✅ 실험 설계에서 설정한 인자들: {', '.join(experiment_factors)}")
    else:
        st.warning("⚠️ 실험 설계 탭에서 먼저 실험 계획을 생성하세요.")
    
    with st.expander("⚙️ 최적화 설정", expanded=True):
        # 목표 함수 설정
        st.markdown("**🎯 목표 함수 설정**")
        settings['objectives'] = st.multiselect(
            "최적화 목표",
            [g.value for g in OptimizationGoal],
            default=["순도 최대화", "수율 최대화"]
        )
        
        # 제약 조건 - 실험 설계 인자들 기반으로 동적 생성
        st.markdown("**⚠️ 제약 조건**")
        settings['constraints'] = {}
        
        if experiment_factors:
            # 실험 설계에서 설정한 인자들에 대해 제약조건 설정
            for factor in experiment_factors:
                factor_constraint = st.checkbox(f"{factor} 제약", value=True, key=f"constraint_{factor}")
                
                if factor_constraint:
                    # 인자별 기본 범위 설정
                    if factor == "온도":
                        min_val, max_val = st.slider(
                            f"{factor} 범위 (°C)", 
                            100, 300, (150, 200), 
                            key=f"slider_{factor}"
                        )
                        settings['constraints']['temperature'] = {'min': min_val, 'max': max_val}
                    
                    elif factor == "압력":
                        min_val, max_val = st.slider(
                            f"{factor} 범위 (bar)", 
                            1.0, 5.0, (1.5, 3.0), 
                            key=f"slider_{factor}"
                        )
                        settings['constraints']['pressure'] = {'min': min_val, 'max': max_val}
                    
                    elif factor == "pH":
                        min_val, max_val = st.slider(
                            f"{factor} 범위", 
                            4.0, 10.0, (6.5, 8.5), 
                            key=f"slider_{factor}"
                        )
                        settings['constraints']['ph'] = {'min': min_val, 'max': max_val}
                    
                    elif factor == "반응시간":
                        min_val, max_val = st.slider(
                            f"{factor} 범위 (분)", 
                            30, 300, (60, 180), 
                            key=f"slider_{factor}"
                        )
                        settings['constraints']['reaction_time'] = {'min': min_val, 'max': max_val}
                    
                    elif factor == "촉매농도":
                        min_val, max_val = st.slider(
                            f"{factor} 범위 (M)", 
                            0.1, 2.0, (0.3, 1.5), 
                            key=f"slider_{factor}"
                        )
                        settings['constraints']['catalyst_concentration'] = {'min': min_val, 'max': max_val}
                    
                    elif factor == "교반속도":
                        min_val, max_val = st.slider(
                            f"{factor} 범위 (rpm)", 
                            100, 1000, (200, 800), 
                            key=f"slider_{factor}"
                        )
                        settings['constraints']['stirring_speed'] = {'min': min_val, 'max': max_val}
                    
                    else:
                        # 기타 인자들에 대한 일반적인 설정
                        min_val, max_val = st.slider(
                            f"{factor} 범위", 
                            0.0, 100.0, (10.0, 90.0), 
                            key=f"slider_{factor}"
                        )
                        settings['constraints'][factor.lower().replace(' ', '_')] = {'min': min_val, 'max': max_val}
        
        else:
            # 실험 설계가 없는 경우 기본 제약조건 제공
            st.info("💡 실험 설계 탭에서 실험 계획을 생성하면 해당 인자들에 대한 제약조건이 자동으로 설정됩니다.")
            
            # 기본 제약조건
            temp_constraint = st.checkbox("온도 제약", value=True)
            if temp_constraint:
                temp_min, temp_max = st.slider("온도 범위 (°C)", 100, 300, (150, 200))
                settings['constraints']['temperature'] = {'min': temp_min, 'max': temp_max}
            
            pressure_constraint = st.checkbox("압력 제약", value=True)
            if pressure_constraint:
                pressure_min, pressure_max = st.slider("압력 범위 (bar)", 1.0, 5.0, (1.5, 3.0))
                settings['constraints']['pressure'] = {'min': pressure_min, 'max': pressure_max}
        
        # 최적화 알고리즘 설정
        st.markdown("**🔧 알고리즘 설정**")
        settings['optimizer'] = st.selectbox(
            "최적화 알고리즘",
            ["Gaussian Process", "Tree-structured Parzen Estimator", "Random Search"]
        )
        
        settings['max_iterations'] = st.slider("최대 반복 횟수", 10, 100, 50)
        settings['acquisition_function'] = st.selectbox(
            "획득 함수", 
            ["Expected Improvement", "Upper Confidence Bound", "Probability of Improvement"]
        )
        
        # 실험 설계 정보 표시
        if experiment_factors:
            st.markdown("**📋 실험 설계 정보**")
            experiment_type = experiment_metadata.get('experiment_type', 'N/A')
            num_runs = experiment_metadata.get('num_runs', 0)
            target_purity = experiment_metadata.get('target_purity', 0)
            target_yield = experiment_metadata.get('target_yield', 0)
            
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.write(f"**실험 유형**: {experiment_type}")
                st.write(f"**실험 횟수**: {num_runs}회")
            with info_col2:
                st.write(f"**목표 순도**: {target_purity}%")
                st.write(f"**목표 수율**: {target_yield}%")
    
    return settings


def _run_optimization(settings: Dict[str, Any]):
    """최적화 실행"""
    try:
        # 베이지안 최적화 엔진 사용
        optimization_engine = BayesianOptimizationEngine()
        
        with st.spinner("최적화 실행 중..."):
            # 진행 상황 표시
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # 최적화 실행
            result = optimization_engine.run_optimization(
                objectives=settings['objectives'],
                constraints=settings['constraints'],
                optimizer=settings['optimizer'],
                max_iterations=settings['max_iterations'],
                acquisition_function=settings['acquisition_function']
            )
            
            # 결과 저장
            st.session_state.optimization_result = result
            
            st.success("✅ 최적화가 완료되었습니다!")
            
            # 결과 표시
            _display_optimization_results(result)
            
    except Exception as e:
        st.error(f"❌ 최적화 실행 중 오류 발생: {str(e)}")


def _display_optimization_results(result):
    """최적화 결과 표시"""
    st.markdown("#### 📋 최적화 결과")
    
    # 최적 조건 표시
    if result.optimal_parameters:
        st.markdown("##### 🎯 최적 조건")
        
        optimal_df = pd.DataFrame([
            {"Parameter": param, "Optimal Value": value, "Confidence": f"{result.confidence_levels.get(param, 0):.0f}%"}
            for param, value in result.optimal_parameters.items()
        ])
        
        st.dataframe(optimal_df, use_container_width=True)
    
    # 예측 성능 표시
    if result.predicted_performance:
        st.markdown("##### 📊 예측 성능")
        
        col_a, col_b = st.columns(2)
        
        performance = result.predicted_performance
        
        with col_a:
            if '예측 순도' in performance:
                st.metric("예측 순도", performance['예측 순도'], f"+{result.improvement_rate:.1f}%")
            if '예측 수율' in performance:
                st.metric("예측 수율", performance['예측 수율'], f"+{result.improvement_rate:.1f}%")
        
        with col_b:
            if '예상 비용' in performance:
                st.metric("예상 비용", performance['예상 비용'], f"-{result.improvement_rate/2:.1f}%")
            if '예상 시간' in performance:
                st.metric("예상 시간", performance['예상 시간'], f"-{result.improvement_rate/3:.1f}%")
    
    # 최적화 분석
    analysis = analyze_optimization_results(result.__dict__)
    
    if analysis.get('recommendations'):
        st.markdown("##### 💡 권장사항")
        for rec in analysis['recommendations']:
            st.info(f"• {rec}")


def _render_optimization_guide():
    """최적화 가이드 UI"""
    st.markdown("#### 📈 최적화 가이드")
    
    if 'optimization_result' in st.session_state:
        result = st.session_state.optimization_result
        
        st.success("✅ 최적화가 완료되었습니다!")
        
        # 수렴 정보
        convergence = result.convergence_info
        st.markdown(f"**수렴률**: {convergence.get('convergence_rate', 0):.1f}%")
        st.markdown(f"**사용 반복**: {convergence.get('iterations_used', 0)}회")
        st.markdown(f"**개선률**: {result.improvement_rate:.1f}%")
        
    else:
        st.info("🎯 최적화 실행 후 결과가 표시됩니다.")
    
    # 최적화 방법론 가이드
    _render_optimization_methodology_guide()


def _render_optimization_methodology_guide():
    """최적화 방법론 가이드"""
    st.markdown("#### 🔍 **베이지안 최적화 가이드**")
    
    with st.expander("📊 **Gaussian Process**"):
        st.markdown("""
        **✨ 특징:**
        - 확률적 surrogate 모델
        - 불확실성 정량화
        - 연속 함수 최적화
        
        **🎯 적용:**
        - 비선형 복잡한 함수
        - 노이즈가 있는 데이터
        - 적은 실험 횟수로 최적화
        """)
    
    with st.expander("🌳 **Tree-structured Parzen Estimator**"):
        st.markdown("""
        **✨ 특징:**
        - 히스토그램 기반 모델
        - 이산/연속 변수 모두 처리
        - 하이퍼파라미터 최적화
        
        **🎯 적용:**
        - 혼합 변수 타입
        - 조건부 변수 존재
        - 빠른 수렴 필요
        """)
    
    st.markdown("#### 🎯 **획득 함수**")
    st.markdown("""
    **Expected Improvement (EI):**
    - 기댓값 개선량 최대화
    - 탐험과 활용의 균형
    
    **Upper Confidence Bound (UCB):**
    - 신뢰 구간 상한 최대화
    - 불확실성 고려
    
    **Probability of Improvement (PI):**
    - 개선 확률 최대화
    - 보수적 접근
    """)


def _render_optimization_chat_interface():
    """최적화 챗봇 인터페이스"""
    st.markdown("---")
    
    # 컨텍스트 데이터 업데이트
    optimization_data = {
        'optimization_result': st.session_state.get('optimization_result'),
        'optimization_settings': st.session_state.get('optimization_settings')
    }
    
    st.session_state.optimization_chat.update_context_data(optimization_data, "현재 세션")
    st.session_state.optimization_chat.create_chat_interface()


def report_generation_tab():
    """보고서 생성 탭"""
    st.markdown("### 📋 GenAI 보고서 생성")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 보고서 설정
        report_settings = _render_report_settings()
        
        # 보고서 생성
        if st.button("📄 보고서 생성", type="primary"):
            _generate_report(report_settings)
    
    with col2:
        # 보고서 가이드
        _render_report_guide()
    
    # 챗봇 인터페이스
    _render_report_chat_interface()


def _render_report_settings() -> Dict[str, Any]:
    """보고서 설정 UI"""
    st.markdown("#### 📝 보고서 설정")
    
    settings = {}
    
    settings['report_type'] = st.selectbox(
        "보고서 유형", 
        ["실험 계획 요약", "최적화 결과", "DoE 분석", "종합 보고서"]
    )
    
    settings['include_sections'] = st.multiselect(
        "포함할 섹션",
        ["실행 요약", "실험 설계", "최적화 결과", "결과 해석", "개선 제안", "다음 단계"],
        default=["실행 요약", "실험 설계", "최적화 결과"]
    )
    
    settings['report_length'] = st.selectbox(
        "보고서 길이", 
        ["간단 (1-2페이지)", "표준 (3-5페이지)", "상세 (5-10페이지)"]
    )
    
    return settings


def _generate_report(settings: Dict[str, Any]):
    """보고서 생성"""
    try:
        # 보고서 생성 엔진 사용
        report_engine = ReportGenerationEngine()
        
        with st.spinner("AI 보고서 생성 중..."):
            # 진행 상황 표시
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
            
            # 실험 데이터 수집
            experiment_data = {}
            if 'experiment_metadata' in st.session_state:
                experiment_data = st.session_state.experiment_metadata
            
            # 최적화 데이터 수집
            optimization_data = None
            if 'optimization_result' in st.session_state:
                result = st.session_state.optimization_result
                optimization_data = {
                    'optimal_parameters': result.optimal_parameters,
                    'predicted_performance': result.predicted_performance,
                    'improvement_rate': result.improvement_rate,
                    'convergence_info': result.convergence_info
                }
            
            # 보고서 생성
            report = report_engine.generate_report(
                report_type=settings['report_type'],
                include_sections=settings['include_sections'],
                report_length=settings['report_length'],
                experiment_data=experiment_data,
                optimization_data=optimization_data
            )
            
            # 결과 저장
            st.session_state.generated_report = report
            
            st.success("✅ 보고서가 생성되었습니다!")
            
            # 보고서 표시
            _display_generated_report(report)
            
    except Exception as e:
        st.error(f"❌ 보고서 생성 중 오류 발생: {str(e)}")


def _display_generated_report(report: Dict[str, Any]):
    """생성된 보고서 표시"""
    st.markdown("#### 📋 생성된 보고서")
    
    # 메타데이터 표시
    metadata = report.get('metadata', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("단어 수", f"{metadata.get('word_count', 0):,}개")
    
    with col2:
        st.metric("예상 읽기 시간", f"{metadata.get('word_count', 0) // 200}분")
    
    with col3:
        st.metric("예상 페이지 수", f"{metadata.get('word_count', 0) // 250}페이지")
    
    # 보고서 내용 표시
    content = report.get('content', '')
    
    # 다운로드 버튼
    st.download_button(
        label="📥 보고서 다운로드",
        data=content,
        file_name=f"실험설계_보고서_{metadata.get('generation_time', '').replace(':', '-').replace(' ', '_')}.md",
        mime="text/markdown"
    )
    
    # 보고서 내용 표시
    st.markdown(content)


def _render_report_guide():
    """보고서 가이드 UI"""
    st.markdown("#### 📊 보고서 가이드")
    
    if 'generated_report' in st.session_state:
        report = st.session_state.generated_report
        metadata = report.get('metadata', {})
        
        st.success("✅ 보고서가 준비되었습니다!")
        
        st.markdown(f"**보고서 유형**: {metadata.get('report_type', 'N/A')}")
        st.markdown(f"**생성 시간**: {metadata.get('generation_time', 'N/A')}")
        st.markdown(f"**포함 섹션**: {', '.join(metadata.get('sections_included', []))}")
        
    else:
        st.info("📄 보고서 생성 후 가이드가 표시됩니다.")
    
    # 보고서 유형 가이드
    _render_report_type_guide()


def _render_report_type_guide():
    """보고서 유형 가이드"""
    st.markdown("#### 📋 **보고서 유형 가이드**")
    
    with st.expander("📊 **실험 계획 요약**"):
        st.markdown("""
        **포함 내용:**
        - 실험 설계 개요
        - 인자 및 수준 정보
        - 실험 횟수 및 효율성
        - 예상 결과
        """)
    
    with st.expander("🎯 **최적화 결과**"):
        st.markdown("""
        **포함 내용:**
        - 최적 조건 상세
        - 성능 개선 정도
        - 신뢰도 분석
        - 비용 효과 분석
        """)
    
    with st.expander("🔬 **DoE 분석**"):
        st.markdown("""
        **포함 내용:**
        - 설계 방법론 분석
        - 통계적 특성
        - 상호작용 효과
        - 모델 적합성
        """)
    
    with st.expander("📋 **종합 보고서**"):
        st.markdown("""
        **포함 내용:**
        - 모든 섹션 통합
        - 경영진 요약
        - 상세 분석 결과
        - 실행 계획
        """)


def _render_report_chat_interface():
    """보고서 챗봇 인터페이스"""
    st.markdown("---")
    
    # 컨텍스트 데이터 업데이트
    report_data = {
        'generated_report': st.session_state.get('generated_report'),
        'experiment_data': st.session_state.get('experiment_metadata'),
        'optimization_data': st.session_state.get('optimization_result')
    }
    
    st.session_state.experiment_report_chat.update_context_data(report_data, "현재 세션")
    st.session_state.experiment_report_chat.create_chat_interface() 