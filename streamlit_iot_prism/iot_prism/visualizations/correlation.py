import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

def calculate_pvalues(df, method='pearson'):
    """상관관계의 p값을 계산합니다."""
    df = df.dropna()
    dfcols = df.columns
    pvalues = pd.DataFrame(index=dfcols, columns=dfcols, dtype=float)
    
    for i, c1 in enumerate(dfcols):
        for j, c2 in enumerate(dfcols):
            if method == 'pearson':
                pvalues.iloc[i, j] = stats.pearsonr(df[c1], df[c2])[1]
            elif method == 'spearman':
                pvalues.iloc[i, j] = stats.spearmanr(df[c1], df[c2])[1]
    
    return pvalues

def render_correlation_ui(df):
    """상관관계 분석 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    st.subheader("상관관계 분석")
    
    # Get equipment type using the helper function
    equipment_type = get_equipment_type(df)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 상관관계 계산
    try:
        # 시간 관련 변수 추가
        df_copy = df.copy()
        df_copy['hour'] = df_copy['timestamp'].dt.hour
        df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek
        df_copy['day_of_month'] = df_copy['timestamp'].dt.day
        df_copy['month'] = df_copy['timestamp'].dt.month
        df_copy['quarter'] = df_copy['timestamp'].dt.quarter
        df_copy['time_idx'] = range(len(df_copy))  # 시간 인덱스 추가
        
        # 순환 시간 변수 (사인, 코사인 변환)
        df_copy['hour_sin'] = np.sin(2 * np.pi * df_copy['hour'] / 24)
        df_copy['hour_cos'] = np.cos(2 * np.pi * df_copy['hour'] / 24)
        df_copy['day_of_week_sin'] = np.sin(2 * np.pi * df_copy['day_of_week'] / 7)
        df_copy['day_of_week_cos'] = np.cos(2 * np.pi * df_copy['day_of_week'] / 7)
        df_copy['month_sin'] = np.sin(2 * np.pi * df_copy['month'] / 12)
        df_copy['month_cos'] = np.cos(2 * np.pi * df_copy['month'] / 12)
        
        # 상관관계 옵션
        corr_options = st.columns([1, 1])
        
        with corr_options[0]:
            corr_method = st.selectbox(
                "상관관계 계산 방법",
                ["피어슨(Pearson)", "스피어만(Spearman)", "켄달(Kendall)"]
            )
            
            if corr_method == "피어슨(Pearson)":
                method = 'pearson'
            elif corr_method == "스피어만(Spearman)":
                method = 'spearman'
            else:
                method = 'kendall'
        
        with corr_options[1]:
            include_cyclical = st.checkbox("순환 시간 변수 포함", value=True)
            show_pvalues = st.checkbox("p값 표시", value=False)
        
        # 상관관계 계산할 변수 선택
        variables = [sensor_col, 'hour', 'day_of_week', 'day_of_month', 'month', 'quarter', 'time_idx']
        
        if include_cyclical:
            variables.extend(['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos'])
        
        # 상관관계 계산
        corr_df = df_copy[variables].corr(method=method)
        
        # 히트맵으로 시각화
        fig = px.imshow(
            corr_df,
            text_auto='.2f',
            color_continuous_scale='RdBu_r',
            aspect="auto",
            title=f"{corr_method} 상관관계 히트맵"
        )
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # p값 계산 및 표시
        sig_correlations = None
        if show_pvalues and (method == 'pearson' or method == 'spearman'):
            try:
                # p값 계산
                p_values = calculate_pvalues(df_copy[variables], method=method)
                
                # p값 히트맵
                st.subheader("상관관계 p값")
                
                # 유의성 레벨 설정
                sig_level = 0.05
                
                # 유의미한 상관관계만 표시
                sig_corr = corr_df.copy()
                sig_corr[p_values > sig_level] = np.nan
                
                # 시각화
                fig2 = px.imshow(
                    sig_corr,
                    text_auto='.2f',
                    color_continuous_scale='RdBu_r',
                    aspect="auto",
                    title=f"통계적으로 유의미한 상관관계 (p < {sig_level})"
                )
                
                fig2.update_layout(height=600)
                st.plotly_chart(fig2, use_container_width=True)
                
                # 유의미한 상관관계 리스트 추출
                sig_correlations = []
                for i, var1 in enumerate(variables):
                    for j, var2 in enumerate(variables):
                        if i < j and p_values.iloc[i, j] < sig_level:
                            sig_correlations.append((var1, var2, corr_df.iloc[i, j], p_values.iloc[i, j]))
                
            except Exception as e:
                st.error(f"p값 계산 중 오류가 발생했습니다: {str(e)}")
        
        # 상관관계 해석
        with st.expander("상관관계 해석"):
            st.write("#### 주요 상관관계 분석")
            
            # 센서 값과의 상관관계만 추출
            value_corr = corr_df[sensor_col].drop(sensor_col).sort_values(ascending=False)
            
            # 상위 상관관계 추출
            top_correlations = [(var, corr) for var, corr in value_corr.head(5).items()]
            
            # 상위 3개, 하위 3개 상관관계 표시
            st.write(f"**{sensor_type_display}와(과)의 강한 양의 상관관계:**")
            for var, corr in value_corr.head(3).items():
                st.write(f"- {var}: {corr:.4f}")
                
                if var == 'hour':
                    st.write(f"  → 시간대에 따라 {sensor_type_display}이(가) 변화하는 경향이 있습니다. 주간/야간 패턴일 수 있습니다.")
                elif var == 'day_of_week':
                    st.write(f"  → 요일에 따라 {sensor_type_display}이(가) 변화하는 경향이 있습니다. 주중/주말 패턴일 수 있습니다.")
                elif var == 'month':
                    st.write(f"  → 월별로 {sensor_type_display}이(가) 변화하는 경향이 있습니다. 계절적 영향이 있을 수 있습니다.")
                elif var == 'quarter':
                    st.write(f"  → 분기별로 {sensor_type_display}이(가) 변화하는 경향이 있습니다.")
                elif var == 'time_idx':
                    st.write(f"  → 시간이 지남에 따라 {sensor_type_display}이(가) 증가하는 경향이 있습니다. 장기적인 상승 추세입니다.")
                elif 'sin' in var or 'cos' in var:
                    st.write("  → 주기적인 패턴이 감지되었습니다.")
            
            st.write(f"**{sensor_type_display}와(과)의 강한 음의 상관관계:**")
            for var, corr in value_corr.tail(3).items():
                st.write(f"- {var}: {corr:.4f}")
                
                if var == 'hour':
                    st.write(f"  → 시간대에 따라 {sensor_type_display}이(가) 반대로 변화하는 경향이 있습니다.")
                elif var == 'day_of_week':
                    st.write(f"  → 요일에 따라 {sensor_type_display}이(가) 반대로 변화하는 경향이 있습니다.")
                elif var == 'month':
                    st.write(f"  → 월별로 {sensor_type_display}이(가) 반대로 변화하는 경향이 있습니다.")
                elif var == 'quarter':
                    st.write(f"  → 분기별로 {sensor_type_display}이(가) 반대로 변화하는 경향이 있습니다.")
                elif var == 'time_idx':
                    st.write(f"  → 시간이 지남에 따라 {sensor_type_display}이(가) 감소하는 경향이 있습니다. 장기적인 하락 추세입니다.")
                elif 'sin' in var or 'cos' in var:
                    st.write("  → 주기적인 패턴이 감지되었습니다.")
            
        # 추가 시각화: 시간별 산점도
        with st.expander("시간 변수별 산점도"):
            # 선택할 시간 변수
            time_vars = {
                'hour': '시간(시)',
                'day_of_week': '요일',
                'day_of_month': '일',
                'month': '월',
                'quarter': '분기'
            }
            
            selected_var = st.selectbox("시간 변수 선택", list(time_vars.keys()), format_func=lambda x: time_vars[x])
            
            # 산점도 생성
            scatter_fig = px.scatter(
                df_copy, 
                x=selected_var, 
                y=sensor_col,
                color=selected_var if selected_var in ['day_of_week', 'month', 'quarter'] else None,
                title=f'{time_vars[selected_var]}별 {sensor_type_display} 분포',
                labels={selected_var: time_vars[selected_var], sensor_col: f'{sensor_type_display} 값'},
                opacity=0.6
            )
            
            # 추세선 추가
            scatter_fig.update_traces(marker=dict(size=5))
            scatter_fig.update_layout(height=500)
            
            scatter_fig.add_trace(
                go.Scatter(
                    x=df_copy.groupby(selected_var)[sensor_col].mean().index,
                    y=df_copy.groupby(selected_var)[sensor_col].mean().values,
                    mode='lines+markers',
                    name='평균값',
                    line=dict(color='red', width=3)
                )
            )
            
            st.plotly_chart(scatter_fig, use_container_width=True)
            
            # 시간 변수별 평균 및 표준편차 테이블
            stats_df = df_copy.groupby(selected_var)[sensor_col].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
            stats_df.columns = [time_vars[selected_var], '평균', '표준편차', '최소값', '최대값', '데이터 수']
            
            st.dataframe(stats_df)
        
        # AI 분석 부분 호출
        render_ai_analysis(
            df=df_copy,
            equipment_type=equipment_type,
            corr_method=method,
            top_correlations=top_correlations,
            sig_correlations=sig_correlations
        )
    
    except Exception as e:
        st.error(f"상관관계 분석 중 오류가 발생했습니다: {str(e)}")

def render_ai_analysis(df, equipment_type, corr_method, top_correlations=None, sig_correlations=None):
    """상관관계 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 상관관계 분석 전용 키 접두사 사용
    key_prefix = "correlation_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 상관관계 분석 방법을 세션 상태에 저장
    current_method_key = f"{key_prefix}_current_method"
    
    # 상관관계 방법이 변경되었는지 확인
    method_changed = False
    if current_method_key in st.session_state:
        if st.session_state[current_method_key] != corr_method:
            method_changed = True
    else:
        # 최초 실행 시
        method_changed = True
    
    # 현재 방법 업데이트
    st.session_state[current_method_key] = corr_method
    
    # AI 분석 프롬프트 키
    corr_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 상관관계 방법이 변경되었거나 프롬프트가 없으면 새로 생성
    if method_changed or corr_prompt_key not in st.session_state:
        # 상관관계 방법에 대한 설명 추가
        method_description = ""
        method_context = ""
        
        if corr_method == 'pearson':
            method_description = "피어슨 상관관계는 두 변수 간의 선형 관계를 측정합니다. 피어슨 계수는 -1(완전한 음의 상관관계)에서 1(완전한 양의 상관관계) 사이의 값을 가집니다."
            method_context = "피어슨 상관관계는 데이터가 정규 분포를 따르고 변수 간에 선형 관계가 있을 때 가장 적합합니다. 이상치에 민감할 수 있습니다."
            
        elif corr_method == 'spearman':
            method_description = "스피어만 상관관계는 두 변수의 순위 간의 관계를 측정하는 비모수적 방법입니다. 데이터의 분포에 대한 가정이 적어 비선형 관계도 감지할 수 있습니다."
            method_context = "스피어만 상관관계는 데이터가 정규 분포를 따르지 않거나 이상치가 있을 때 유용합니다. 변수 간의 단조 관계(같이 증가하거나 같이 감소하는 경향)를 측정합니다."
            
        else:  # kendall
            method_description = "켄달 상관관계는 두 변수 간의 순위 일치도를 측정하는 비모수적 방법입니다. 순서쌍의 일치 여부를 기반으로 계산됩니다."
            method_context = "켄달 상관관계는 작은 표본 크기에 더 적합하며, 이상치에 덜 민감합니다. 스피어만보다 계산 방식이 다르고, 일반적으로 값의 크기가 더 작습니다."
        
        # 상관관계 분석 데이터의 통계 및 특성 요약
        stats_summary = f"""
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 상관관계 분석 방법: {corr_method} ({method_description})
- 데이터 포인트 수: {len(df):,}개
- 데이터 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}
"""
        
        # 상위 상관관계 정보 추가
        if top_correlations is not None:
            stats_summary += f"\n{sensor_type_display}와(과)의 상위 상관관계:\n"
            for var, corr in top_correlations:
                stats_summary += f"* {var}: {corr:.4f}\n"
            
        # 유의미한 상관관계 정보 추가
        if sig_correlations is not None:
            stats_summary += f"\n통계적으로 유의미한 상관관계 (p < 0.05):\n"
            for var1, var2, corr, p_val in sig_correlations:
                stats_summary += f"* {var1} vs {var2}: 상관계수 = {corr:.4f}, p = {p_val:.4e}\n"
            
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 상관관계 분석을 통해 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {corr_method} 방법으로 분석되었습니다.
이 분석은 {method_description}

분석 컨텍스트: {method_context}

주요 분석 포인트:
1. {sensor_type_display}와 시간 변수 간의 주요 상관관계 패턴
2. 각 상관관계의 강도, 방향 및 통계적 유의성
3. 센서 값에 영향을 미치는 주요 시간 요소
4. 시간 패턴이 장비 성능 또는 작동 조건에 주는 의미
5. 장비 운영 최적화를 위한 실용적인 인사이트
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 {corr_method} 상관관계 분석 결과입니다.

## 데이터 정보
{stats_summary}

## 분석 과제
위 상관관계 분석 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {sensor_type_display}와 가장 강한 상관관계를 보이는 시간 변수 분석
   - 양의 상관관계와 음의 상관관계 모두 고려
   - 각 상관관계의 강도와 방향성 설명

2. 발견된 주요 시간 패턴 해석
   - 일중 패턴(시간별)의 의미
   - 주간 패턴(요일별)의 의미
   - 계절 또는 월간 패턴의 의미

3. 순환 시간 변수(사인, 코사인 변환)의 중요성 평가
   - 순환 변수가 일반 시간 변수보다 더 높은 상관관계를 보이는 경우 특별히 언급
   - 주기적 패턴이 센서 값에 미치는 영향

4. {sensor_type_display} 값의 장기 추세 분석(time_idx와의 상관관계 기반)
   - 시간에 따른 증가 또는 감소 추세
   - 장기 추세의 강도와 의미

5. 장비 운영에 대한 실용적인 제안
   - 최적의 운영 시간대 또는 조건
   - 유지보수 계획에 도움이 될 수 있는 시간 패턴
   - 효율성 또는 성능 개선을 위한 구체적인 권장사항

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 상관관계 계수의 실제 값을 언급하여 인사이트에 신뢰성을 더해주세요.
"""
        # 상관관계 전용 프롬프트로 저장
        st.session_state[corr_prompt_key] = analysis_prompt
        
        # 방법이 변경되면 캐시도 초기화
        if method_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"상관관계 방법이 변경되어 캐시 초기화: {corr_method}")
        
        # 디버깅용 로깅
        print(f"상관관계 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
        if method_changed:
            print(f"상관관계 방법 변경: {corr_method}")
    else:
        # 캐시된 상관관계 전용 프롬프트 사용
        analysis_prompt = st.session_state[corr_prompt_key]
        print(f"캐시된 상관관계 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 상관관계 분석")

    # 세션 상태 키 정의 - 모두 상관관계 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 상관관계 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 상관관계 분석 전용
    def on_correlation_analyze_click():
        # 캐시 초기화
        if cache_state_key in st.session_state:
            # 캐시 키 생성
            from ..utils.ai_utils import generate_cache_key
            cache_key = generate_cache_key(
                prompt=analysis_prompt,
                model=st.session_state.selected_model,
                temperature=st.session_state.temperature
            )
            st.session_state[cache_state_key].pop(cache_key, None)
        # 대화 기록 초기화
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
        # 실행 상태 설정
        st.session_state[running_key] = True
        
        # 디버깅용 로깅
        print(f"상관관계 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 상관관계 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 상관관계 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_correlation_analyze_click,
            use_container_width=True
        )
    
    # 이전 분석 결과가 있는 경우 (캐시에 있는 경우)
    if cache_state_key in st.session_state and len(st.session_state[cache_state_key]) > 0:
        # 캐시 키 생성
        from ..utils.ai_utils import generate_cache_key
        cache_key = generate_cache_key(
            prompt=analysis_prompt,
            model=st.session_state.selected_model,
            temperature=st.session_state.temperature
        )
        
        if cache_key in st.session_state[cache_state_key]:
            cached_response = st.session_state[cache_state_key][cache_key]
            with st.chat_message("assistant"):
                st.markdown(cached_response["response"])
                if cached_response.get("metadata"):
                    metadata_text = "\n\n---\n**처리 정보**\n```json\n"
                    metadata_text += json.dumps(cached_response["metadata"], indent=2, ensure_ascii=False)
                    metadata_text += "\n```"
                    st.markdown(metadata_text)
            # 실행 상태 업데이트
            st.session_state[running_key] = False
            print(f"상관관계 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"상관관계 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 상관관계 데이터를 분석하고 있습니다..."):
                print(f"상관관계 분석: generate_ai_response 함수 호출 전")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"상관관계 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 상관관계 분석 실행' 버튼을 클릭하세요. 변수 간의 상관관계와 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 상관관계 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"상관관계: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 상관관계 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 