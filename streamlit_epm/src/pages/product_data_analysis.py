"""
DX-AI Manufacturing Copilot - 제품 데이터 분석 페이지

EDA, 기술통계, 상관관계 분석 등 탐색적 데이터 분석 페이지입니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

# Core engines and utilities
from src.core.chat_manager import ChatManager, setup_chat_sidebar
from src.core.tab_chat_managers import (
    ProductDataAnalysisChatManager,
    ProductDataPreprocessingChatManager
)
from src.core.product_data_analysis_engine import (
    ProductDataAnalysisEngine,
    DataAnalysisEngine,
    DataPreprocessingEngine,
    OutlierDetectionMethod
)
from src.utils.product_data_analysis_utils import (
    display_preprocessing_results,
    get_correlation_strength,
    format_correlation_pairs,
    DataAnalysisFormatter,
    PreprocessingResultsDisplayer,
    DataAnalysisHelper
)


def product_data_analysis_page():
    """제품 데이터 분석 페이지"""
    st.markdown("## 📊 제품 데이터 분석")
    
    # ChatManager 인스턴스 생성
    if 'chat_manager' not in st.session_state:
        st.session_state.chat_manager = ChatManager()
    
    chat_manager = st.session_state.chat_manager
    
    # 데이터 분석 전용 챗봇 매니저 초기화
    if 'product_data_analysis_chat' not in st.session_state:
        st.session_state.product_data_analysis_chat = ProductDataAnalysisChatManager(chat_manager)
    
    # 데이터 전처리 전용 챗봇 매니저 초기화
    if 'product_data_preprocessing_chat' not in st.session_state:
        st.session_state.product_data_preprocessing_chat = ProductDataPreprocessingChatManager(chat_manager)
    
    # 사이드바에 챗봇 설정 추가
    setup_chat_sidebar(chat_manager)
    
    # 탭 생성
    tab1, tab2 = st.tabs(["📊 데이터 분석 (EDA)", "🔧 데이터 전처리"])
    
    with tab1:
        data_analysis_tab()
    
    with tab2:
        st.markdown("### 🔧 모델링을 위한 데이터 전처리")
        data_preprocessing_tab()


def data_analysis_tab():
    """데이터 분석 탭 내용"""
    
    # 데이터 업로드
    st.markdown("#### 📁 데이터 업로드")
    uploaded_file = st.file_uploader("실험 데이터 파일 업로드", type=['csv', 'xlsx'])
    
    if uploaded_file is None:
        # 예시 데이터 사용
        st.info("📊 예시 데이터를 사용합니다. 실제 데이터를 업로드해주세요.")
        
        np.random.seed(42)
        sample_data = pd.DataFrame({
            "온도": np.random.uniform(150, 200, 50),
            "압력": np.random.uniform(1.5, 3.0, 50),
            "pH": np.random.uniform(6.5, 8.5, 50),
            "순도": np.random.uniform(95, 99, 50),
            "수율": np.random.uniform(85, 98, 50)
        })
        
        # 세션 상태에 예시 데이터 저장
        st.session_state.analysis_data = sample_data
        
        # 예시 데이터 분석 수행
        _display_sample_data_analysis(sample_data)
    
    else:
        # 업로드된 파일 처리
        try:
            # 파일 형식에 따라 읽기
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("❌ 지원하지 않는 파일 형식입니다. CSV 또는 Excel 파일을 업로드해주세요.")
                return
            
            # 세션 상태에 데이터 저장
            st.session_state.analysis_data = df
            
            st.success(f"✅ 파일 업로드 성공! 파일명: {uploaded_file.name}")
            
            # 종합 데이터 분석 수행
            _display_comprehensive_analysis(df, uploaded_file.name)
        
        except Exception as e:
            st.error(f"❌ 파일 처리 중 오류가 발생했습니다: {str(e)}")
    
    # 데이터 분석 챗봇 인터페이스
    _create_data_analysis_chat_interface(uploaded_file)


def _display_sample_data_analysis(sample_data: pd.DataFrame):
    """예시 데이터 분석 표시"""
    # 상관관계 분석 (예시 데이터)
    st.markdown("#### 🔗 변수 간 상관관계")
    
    # 예시 데이터의 모든 컬럼을 선택된 컬럼으로 설정
    st.session_state.selected_correlation_cols = list(sample_data.columns)
    st.session_state.correlation_threshold = 0.7
    
    # 데이터 분석 엔진 사용
    analysis_engine = DataAnalysisEngine()
    correlation_result = analysis_engine.analyze_correlation(
        sample_data, list(sample_data.columns), 0.7
    )
    
    st.write("상관계수 행렬:")
    st.dataframe(correlation_result.correlation_matrix.round(3), use_container_width=True)
    
    # 데이터 요약
    st.markdown("#### 📈 기술통계")
    basic_stats = analysis_engine.get_basic_statistics(sample_data)
    formatted_stats = DataAnalysisFormatter.format_basic_statistics(basic_stats)
    st.dataframe(formatted_stats, use_container_width=True)


def _display_comprehensive_analysis(df: pd.DataFrame, filename: str):
    """종합 데이터 분석 수행 및 표시"""
    # 제품 데이터 분석 엔진 초기화
    analysis_engine = ProductDataAnalysisEngine()
    
    # 데이터 기본 정보
    st.markdown("#### 📊 데이터 기본 정보")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 행 수", len(df))
    with col2:
        st.metric("총 열 수", len(df.columns))
    with col3:
        missing_values = df.isnull().sum().sum()
        st.metric("결측치 수", missing_values)
    
    # 데이터 미리보기
    st.markdown("#### 👀 데이터 미리보기")
    st.dataframe(df.head(10), use_container_width=True)
    
    # 컬럼 정보
    st.markdown("#### 📋 컬럼 정보")
    column_info = pd.DataFrame({
        '컬럼명': df.columns,
        '데이터 타입': df.dtypes.astype(str),
        '결측치 수': df.isnull().sum(),
        '고유값 수': df.nunique()
    })
    st.dataframe(column_info, use_container_width=True)
    
    # 수치형 컬럼만 필터링
    numeric_cols = _identify_numeric_columns(df)
    
    if len(numeric_cols) > 1:
        # 상관관계 분석
        _display_correlation_analysis(df, numeric_cols, analysis_engine)
    else:
        st.warning("⚠️ 수치형 컬럼이 2개 미만이어서 상관관계 분석을 수행할 수 없습니다.")
    
    # 기본 통계
    _display_basic_statistics(df, numeric_cols, analysis_engine)
    
    # 분포 분석
    if numeric_cols:
        _display_distribution_analysis(df, numeric_cols)


def _identify_numeric_columns(df: pd.DataFrame) -> List[str]:
    """수치형 컬럼 식별 (날짜 형식 제외)"""
    numeric_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]) and not _is_date_like_analysis(df[col]):
            try:
                pd.to_numeric(df[col], errors='raise')
                numeric_cols.append(col)
            except (ValueError, TypeError):
                continue
    return numeric_cols


def _is_date_like_analysis(series: pd.Series) -> bool:
    """시리즈가 날짜 형식인지 확인"""
    if series.dtype == 'object':
        sample_size = min(10, len(series))
        sample_values = series.dropna().head(sample_size)
        
        date_count = 0
        for value in sample_values:
            if isinstance(value, str):
                try:
                    pd.to_datetime(value, errors='raise')
                    date_count += 1
                except (ValueError, TypeError):
                    continue
        
        return date_count / len(sample_values) >= 0.5 if len(sample_values) > 0 else False
    return False


def _display_correlation_analysis(df: pd.DataFrame, numeric_cols: List[str], analysis_engine: ProductDataAnalysisEngine):
    """상관관계 분석 표시"""
    st.markdown("#### 🔗 변수 간 상관관계")
    
    # 상관관계 계산할 컬럼 선택
    selected_cols = st.multiselect(
        "상관관계 분석할 컬럼 선택",
        numeric_cols,
        default=numeric_cols[:min(6, len(numeric_cols))],
        help="너무 많은 컬럼을 선택하면 히트맵이 복잡해집니다."
    )
    
    # 선택된 컬럼들을 세션 상태에 저장 (AI Context에서 사용)
    st.session_state.selected_correlation_cols = selected_cols
    
    if selected_cols:
        try:
            correlation_result = analysis_engine.analysis_engine.analyze_correlation(
                df, selected_cols, 0.7
            )
            
            # 상관계수 행렬 표시
            st.write("**상관계수 행렬:**")
            st.dataframe(correlation_result.correlation_matrix.round(3), use_container_width=True)
            
            # 상관관계 히트맵
            _display_correlation_heatmap(correlation_result.correlation_matrix)
            
            # 높은 상관관계 필터링
            _display_high_correlation_filter(correlation_result)
        
        except Exception as e:
            st.error(f"❌ 상관관계 분석 중 오류가 발생했습니다: {str(e)}")


def _display_correlation_heatmap(correlation_matrix: pd.DataFrame):
    """상관관계 히트맵 표시"""
    try:
        import plotly.express as px
        
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdBu_r',
            title="상관관계 히트맵"
        )
        fig.update_layout(
            width=600,
            height=500,
            title_x=0.5
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("💡 plotly가 설치되지 않아서 히트맵을 표시할 수 없습니다.")


def _display_high_correlation_filter(correlation_result):
    """높은 상관관계 필터링 표시"""
    st.markdown("**🔍 높은 상관관계 필터링:**")
    
    correlation_threshold = st.slider(
        "상관계수 임계값 (|r|)",
        min_value=0.1,
        max_value=0.9,
        value=0.7,
        step=0.05,
        help="이 값 이상의 절댓값을 가진 상관계수만 표시합니다."
    )
    
    # 임계값을 세션 상태에 저장 (AI Context에서 사용)
    st.session_state.correlation_threshold = correlation_threshold
    
    # 높은 상관관계 찾기 (새로운 임계값 적용)
    high_corr_pairs = format_correlation_pairs(correlation_result.correlation_matrix, correlation_threshold)
    
    if high_corr_pairs:
        st.write(f"**📊 임계값 {correlation_threshold} 이상의 상관관계:**")
        high_corr_df = pd.DataFrame(high_corr_pairs)
        high_corr_df['상관계수'] = high_corr_df['상관계수'].round(3)
        st.dataframe(high_corr_df, use_container_width=True)
    else:
        st.info(f"임계값 {correlation_threshold} 이상의 상관관계가 없습니다.")


def _display_basic_statistics(df: pd.DataFrame, numeric_cols: List[str], analysis_engine: ProductDataAnalysisEngine):
    """기본 통계 표시"""
    st.markdown("#### 📈 기술통계")
    
    if numeric_cols:
        basic_stats = analysis_engine.analysis_engine.get_basic_statistics(df, numeric_cols)
        formatted_stats = DataAnalysisFormatter.format_basic_statistics(basic_stats)
        st.dataframe(formatted_stats, use_container_width=True)
    else:
        st.info("수치형 데이터가 없어서 기술통계를 표시할 수 없습니다.")


def _display_distribution_analysis(df: pd.DataFrame, numeric_cols: List[str]):
    """분포 분석 표시"""
    st.markdown("#### 📊 데이터 분포 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_column = st.selectbox("분포를 확인할 컬럼 선택", numeric_cols)
    
    with col2:
        chart_type = st.selectbox("차트 유형", ["히스토그램", "박스플롯", "바이올린플롯"])
    
    if selected_column:
        _display_chart(df, selected_column, chart_type)
        _display_column_statistics(df, selected_column)


def _display_chart(df: pd.DataFrame, column: str, chart_type: str):
    """차트 표시"""
    try:
        import plotly.express as px
        
        if chart_type == "히스토그램":
            fig = px.histogram(df, x=column, title=f"{column} 분포")
        elif chart_type == "박스플롯":
            fig = px.box(df, y=column, title=f"{column} 박스플롯")
        else:  # 바이올린플롯
            fig = px.violin(df, y=column, title=f"{column} 바이올린플롯")
        
        st.plotly_chart(fig, use_container_width=True)
    
    except ImportError:
        st.info("💡 plotly가 설치되지 않아서 차트를 표시할 수 없습니다.")
        # 대안으로 pandas 기본 히스토그램 사용
        st.line_chart(df[column].value_counts().sort_index())


def _display_column_statistics(df: pd.DataFrame, column: str):
    """컬럼 통계 표시"""
    col_stats = df[column].describe()
    st.markdown(f"**{column} 기본 통계:**")
    
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    with stats_col1:
        st.metric("평균", f"{col_stats['mean']:.2f}")
    with stats_col2:
        st.metric("표준편차", f"{col_stats['std']:.2f}")
    with stats_col3:
        st.metric("최솟값", f"{col_stats['min']:.2f}")
    with stats_col4:
        st.metric("최댓값", f"{col_stats['max']:.2f}")


def data_preprocessing_tab():
    """데이터 전처리 탭 내용"""
    
    # 분석된 데이터가 있는지 확인
    analysis_data = st.session_state.get('analysis_data', None)
    if analysis_data is None:
        st.warning("⚠️ 먼저 **데이터 분석** 탭에서 데이터를 업로드해주세요.")
        st.info("💡 데이터 업로드 후 이 탭에서 모델링을 위한 전처리를 수행할 수 있습니다.")
        return
    
    _display_preprocessing_intro()
    _display_current_data_info(analysis_data)
    
    # 전처리 실행
    if st.button("🔧 데이터 전처리 실행", type="primary"):
        _execute_preprocessing(analysis_data)
    
    # 이전 전처리 결과 표시
    _display_previous_preprocessing_results()
    
    # 데이터 전처리 챗봇 인터페이스
    _create_data_preprocessing_chat_interface()


def _display_preprocessing_intro():
    """전처리 소개 표시"""
    st.markdown("""
    모델링에 앞서 데이터를 전처리해야 합니다. 다음과 같은 문제들을 자동으로 확인하고 처리합니다:
    
    - 📅 **날짜/시간 데이터**: 모델링에서 제외하거나 특성 엔지니어링 필요
    - 📝 **범주형 변수**: 수치형으로 인코딩 필요
    - ❓ **결측치**: 대체 또는 제거 필요
    - 📊 **분산이 0인 변수**: 모델링에 기여하지 않아 제거 필요
    - 🔍 **이상치**: 모델 성능에 영향을 줄 수 있음
    - 🔗 **다중공선성**: 상관관계가 높은 변수들 확인 필요
    """)


def _display_current_data_info(analysis_data: pd.DataFrame):
    """현재 데이터 정보 표시"""
    st.markdown("#### 📊 현재 데이터 정보")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("데이터 크기", f"{analysis_data.shape[0]} × {analysis_data.shape[1]}")
    with col2:
        missing_count = analysis_data.isnull().sum().sum()
        st.metric("총 결측치", missing_count)
    with col3:
        numeric_cols = len([col for col in analysis_data.columns if pd.api.types.is_numeric_dtype(analysis_data[col])])
        st.metric("수치형 컬럼", numeric_cols)


def _execute_preprocessing(analysis_data: pd.DataFrame):
    """전처리 실행"""
    with st.spinner("데이터 전처리 중..."):
        try:
            # 데이터 전처리 엔진 사용
            preprocessing_engine = DataPreprocessingEngine()
            preprocessing_results = preprocessing_engine.preprocess_for_modeling(analysis_data)
            
            # 전처리 결과 표시
            display_preprocessing_results(preprocessing_results)
            
            # 세션 상태에 전처리 결과 저장 (모델링 페이지에서 사용)
            st.session_state.preprocessing_results = preprocessing_results
            st.session_state.processed_data = preprocessing_results.processed_data
            
            # 전처리 완료 플래그 설정 (Context 업데이트용)
            st.session_state.preprocessing_completed = True
            
            st.success("✅ 데이터 전처리가 완료되었습니다!")
            st.info("💡 전처리된 데이터가 저장되었습니다. 이제 '제품 예측 모델링' 페이지에서 모델 훈련을 진행할 수 있습니다.")
            
            # 모델링 페이지로 이동 안내
            st.markdown("**다음 단계:** 사이드바에서 '제품 예측 모델링' 페이지로 이동하여 모델을 훈련하세요.")
            
            # 전처리 완료 후 페이지 새로고침하여 Context 업데이트
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 데이터 전처리 중 오류가 발생했습니다: {str(e)}")


def _display_previous_preprocessing_results():
    """이전 전처리 결과 표시"""
    if 'preprocessing_results' in st.session_state:
        st.markdown("---")
        st.markdown("#### 📋 이전 전처리 결과")
        prev_results = st.session_state.preprocessing_results
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("처리된 데이터 크기", f"{prev_results.final_shape[0]} × {prev_results.final_shape[1]}")
        with col2:
            st.metric("제거된 컬럼 수", len(prev_results.removed_columns))
        with col3:
            warning_count = len(prev_results.warnings)
            st.metric("경고사항 수", warning_count)
        
        # 전처리 결과 재표시 토글
        if st.checkbox("전처리 결과 상세 보기"):
            display_preprocessing_results(prev_results)
        
        # 전처리된 데이터 다운로드 기능
        if st.button("📥 전처리된 데이터 다운로드"):
            processed_csv = prev_results.processed_data.to_csv(index=False)
            st.download_button(
                label="💾 CSV 파일로 다운로드",
                data=processed_csv,
                file_name="preprocessed_data.csv",
                mime="text/csv"
            )


def _create_data_analysis_chat_interface(uploaded_file):
    """데이터 분석 챗봇 인터페이스 생성"""
    st.markdown("---")
    st.markdown("### 💬 데이터 분석 AI 어시스턴트")
    
    # 데이터 분석 전용 챗봇 매니저 사용
    data_analysis_chat_manager = st.session_state.product_data_analysis_chat
    
    # Context 데이터 업데이트
    analysis_data = st.session_state.get('analysis_data', None)
    if analysis_data is not None:
        # 현재 데이터가 예시 데이터인지 실제 업로드 데이터인지 확인
        is_sample_data = uploaded_file is None
        
        # 수치형 컬럼 필터링
        numeric_columns = _identify_numeric_columns(analysis_data)
        
        # 기본 통계 정보 생성
        analysis_engine = DataAnalysisEngine()
        basic_statistics = analysis_engine.get_basic_statistics(analysis_data, numeric_columns)
        
        # 데이터 품질 정보 생성
        quality_info = analysis_engine.analyze_data_quality(analysis_data)
        
        # 샘플 데이터 생성 (상위 3행)
        sample_data = []
        for idx, row in analysis_data.head(3).iterrows():
            row_dict = {col: str(row[col])[:50] + '...' if len(str(row[col])) > 50 else str(row[col]) 
                       for col in analysis_data.columns}
            sample_data.append(row_dict)
        
        data_context = {
            'current_tab': 'data_analysis',
            'data_info': {
                'data_source': '예시 데이터' if is_sample_data else f'업로드 데이터 ({uploaded_file.name})',
                'is_sample_data': is_sample_data
            },
            'data_summary': {
                'rows': len(analysis_data),
                'columns': list(analysis_data.columns),
                'numeric_columns': numeric_columns,
                'missing_values': analysis_data.isnull().sum().to_dict(),
                'data_types': analysis_data.dtypes.astype(str).to_dict(),
                'basic_statistics': basic_statistics
            },
            'data_quality': quality_info,
            'sample_data': sample_data
        }
        
        # 상관관계 정보 추가
        if len(numeric_columns) > 1:
            try:
                selected_cols = st.session_state.get('selected_correlation_cols', numeric_columns[:min(6, len(numeric_columns))])
                correlation_result = analysis_engine.analyze_correlation(analysis_data, selected_cols, 0.7)
                
                data_context['correlation_analysis'] = {
                    'selected_columns': selected_cols,
                    'correlation_matrix': correlation_result.correlation_matrix.to_dict(),
                    'high_correlations': correlation_result.high_correlation_pairs,
                    'threshold_used': st.session_state.get('correlation_threshold', 0.7),
                    'total_pairs_above_threshold': correlation_result.total_pairs_above_threshold
                }
            except Exception as e:
                data_context['correlation_analysis'] = {
                    'error': f"상관관계 분석 오류: {str(e)}",
                    'selected_columns': numeric_columns
                }
        else:
            data_context['correlation_analysis'] = {
                'message': '수치형 컬럼이 2개 미만이어서 상관관계 분석 불가능',
                'numeric_columns_count': len(numeric_columns)
            }
        
        data_analysis_chat_manager.update_context_data(data_context, "데이터 분석 탭")
    else:
        data_analysis_chat_manager.update_context_data({
            'current_tab': 'data_analysis',
            'message': '현재 분석할 데이터가 없습니다. 데이터를 업로드해주세요.'
        }, "데이터 분석 탭")
    
    # 데이터 분석 전용 챗봇 인터페이스 생성
    data_analysis_chat_manager.create_chat_interface()


def _create_data_preprocessing_chat_interface():
    """데이터 전처리 챗봇 인터페이스 생성"""
    st.markdown("---")
    st.markdown("### 💬 데이터 전처리 AI 어시스턴트")
    
    # 데이터 전처리 전용 챗봇 매니저 사용
    data_preprocessing_chat_manager = st.session_state.product_data_preprocessing_chat
    
    # Context 데이터 업데이트
    analysis_data = st.session_state.get('analysis_data', None)
    if analysis_data is not None:
        # 전처리된 데이터가 있으면 우선 사용, 없으면 원본 데이터 사용
        processed_data = st.session_state.get('processed_data', None)
        current_data = processed_data if processed_data is not None else analysis_data
        data_source = "전처리된 데이터" if processed_data is not None else "원본 데이터"
        
        # 현재 데이터 기준으로 분석
        analysis_engine = DataAnalysisEngine()
        quality_info = analysis_engine.analyze_data_quality(current_data)
        basic_statistics = analysis_engine.get_basic_statistics(current_data)
        
        data_context = {
            'current_tab': 'data_preprocessing',
            'data_info': {
                'data_source': data_source,
                'is_preprocessed': processed_data is not None,
                'original_data_shape': f"{analysis_data.shape[0]} × {analysis_data.shape[1]}",
                'current_data_shape': f"{current_data.shape[0]} × {current_data.shape[1]}"
            },
            'data_summary': {
                'rows': len(current_data),
                'columns': list(current_data.columns),
                'numeric_columns': [col for col in current_data.columns if pd.api.types.is_numeric_dtype(current_data[col])],
                'missing_values': current_data.isnull().sum().to_dict(),
                'data_types': current_data.dtypes.astype(str).to_dict(),
                'basic_statistics': basic_statistics
            },
            'data_quality': quality_info
        }
        
        # 전처리 결과 정보 추가
        if 'preprocessing_results' in st.session_state:
            preprocessing_results = st.session_state.preprocessing_results
            data_context['preprocessing_results'] = {
                'original_shape': preprocessing_results.original_shape,
                'final_shape': preprocessing_results.final_shape,
                'removed_columns': preprocessing_results.removed_columns,
                'numeric_columns': preprocessing_results.numeric_columns,
                'steps_completed': len(preprocessing_results.steps),
                'warnings_count': len(preprocessing_results.warnings),
                'success_rate': preprocessing_results.success_rate,
                'has_outliers': preprocessing_results.outlier_info is not None,
                'has_high_correlation': preprocessing_results.high_correlation_pairs is not None,
                'is_ready_for_modeling': True
            }
        
        data_preprocessing_chat_manager.update_context_data(data_context, "데이터 전처리 탭")
    else:
        data_preprocessing_chat_manager.update_context_data({'current_tab': 'data_preprocessing'}, "데이터 전처리 탭")
    
    # 데이터 전처리 전용 챗봇 인터페이스 생성
    data_preprocessing_chat_manager.create_chat_interface() 