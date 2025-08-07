import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

# 트렌드 분석 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, trend_type, trend_stats=None):
    """트렌드 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 트렌드 분석 전용 키 접두사 사용
    key_prefix = "trend_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 트렌드 유형을 세션 상태에 저장
    current_trend_type_key = f"{key_prefix}_current_trend_type"
    
    # 트렌드 유형이 변경되었는지 확인
    trend_type_changed = False
    if current_trend_type_key in st.session_state:
        if st.session_state[current_trend_type_key] != trend_type:
            trend_type_changed = True
    else:
        # 최초 실행 시
        trend_type_changed = True
    
    # 현재 트렌드 유형 업데이트
    st.session_state[current_trend_type_key] = trend_type
    
    # AI 분석 프롬프트 키
    trend_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 트렌드 유형이 변경되었거나 프롬프트가 없으면 새로 생성
    if trend_type_changed or trend_prompt_key not in st.session_state:
        # 트렌드 유형에 대한 설명 추가
        trend_description = ""
        trend_context = ""
        
        if trend_type == "단순 이동평균":
            trend_description = "단순 이동평균은 데이터의 노이즈를 줄이고 추세를 더 잘 파악할 수 있도록 해줍니다. 지정된 기간 동안의 평균을 계산하여 시간에 따른 변화 추세를 분석합니다."
            trend_context = "이동평균은 시계열 데이터의 단기 변동성을 줄이고 장기 추세를 식별하는 데 유용합니다. 윈도우 크기에 따라 분석의 민감도가 달라집니다."
            
        elif trend_type == "지수 가중 이동평균":
            trend_description = "지수 가중 이동평균은 최근 데이터에 더 높은 가중치를 부여하여 단순 이동평균보다 현재 추세를 더 잘 반영합니다. 과거로 갈수록 가중치가 지수적으로 감소합니다."
            trend_context = "지수 가중치를 사용하면 최근 데이터에 더 민감하게 반응하므로 추세 변화를 더 빠르게 감지할 수 있습니다. 스무딩 파라미터(알파)에 따라 민감도와 안정성이 결정됩니다."
            
        elif trend_type == "계절성 분해":
            trend_description = "시계열 데이터를 추세, 계절성, 잔차 성분으로 분해하여 분석합니다. 계절적 패턴, 장기 추세, 불규칙한 변동을 분리하여 이해할 수 있습니다."
            trend_context = "계절성 분해는 데이터에 내재된 주기적 패턴을 식별하고 장기 추세와 분리하는 데 유용합니다. 일별, 주별, 월별 패턴을 식별하고 예측에 활용할 수 있습니다."
            
        else:  # "추세선"
            trend_description = "다항식 회귀를 사용하여 데이터의 전반적인 추세를 모델링합니다. 차수에 따라 선형 또는 비선형 추세를 캡처할 수 있습니다."
            trend_context = "추세선은 데이터의 장기적인 방향성을 파악하는 데 유용합니다. 다항식 차수가 높을수록 더 복잡한 패턴을 모델링할 수 있지만, 과적합의 위험도 있습니다."
        
        # 트렌드 분석 데이터의 통계 및 특성 요약
        stats_summary = f"""
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 트렌드 분석 유형: {trend_type} ({trend_description})
- 데이터 포인트 수: {len(df):,}개
- 데이터 기간: {df['timestamp'].min()} ~ {df['timestamp'].max()}
"""
        
        # 트렌드별 추가 통계 정보
        if trend_stats is not None:
            stats_summary += f"\n{trend_type} 분석 통계 요약:\n"
            for key, value in trend_stats.items():
                stats_summary += f"* {key}: {value}\n"
            
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 시계열 트렌드 분석을 통해 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {trend_type} 방법으로 분석되었습니다.
이 분석은 {trend_description}

분석 컨텍스트: {trend_context}

주요 분석 포인트:
1. {trend_type}을 통해 확인된 {sensor_type_display}의 주요 패턴 및 추세
2. 시간에 따른 {sensor_type_display} 변화의 의미와 영향
3. 장비 성능, 효율성, 또는 상태 관련 인사이트
4. 이상 패턴 또는 주목할 만한 변동성의 잠재적 원인
5. 장비 운영 및 유지보수 관련 인사이트
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 {trend_type} 분석 결과입니다.

## 데이터 정보
{stats_summary}

## 분석 과제
위 트렌드 분석 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {trend_type}을 통해 확인된 {sensor_type_display}의 주요 패턴 및 추세
   - 주요 추세 방향(상승, 하락, 안정)의 명확한 설명
   - 시간에 따른 변화 속도와 특성

2. 눈에 띄는 주기적 패턴 또는 이상점
   - 주기적 변동이 있다면 그 주기와 강도 분석
   - 특이점 또는 이상 패턴이 관찰되는 시점과 그 특성

3. {sensor_type_display} 트렌드가 장비 성능에 주는 의미
   - 트렌드가 장비의 효율성, 상태, 또는 성능에 어떤 영향을 미치는지 분석
   - 장기적인 추세가 장비 수명이나 운영에 미치는 잠재적 영향

4. 최근 데이터 포인트의 동향 분석
   - 가장 최근 기간의 데이터가 보여주는 특별한 패턴이나 변화
   - 이러한 최근 패턴이 미래 추세에 대해 시사하는 바

5. 장비 운영 또는 예방 정비에 대한 실용적인 제안
   - 관찰된 트렌드를 바탕으로 한 구체적인 운영/정비 제안
   - 성능 최적화나 비용 절감을 위한 데이터 기반 권장사항

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 분석에서 발견된 구체적인 수치나 패턴을 언급하여 인사이트에 신뢰성을 더해주세요.
"""
        # 트렌드 전용 프롬프트로 저장
        st.session_state[trend_prompt_key] = analysis_prompt
        
        # 트렌드 유형이 변경되면 캐시도 초기화
        if trend_type_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"트렌드 유형이 변경되어 캐시 초기화: {trend_type}")
        
        # 디버깅용 로깅
        print(f"트렌드 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
        if trend_type_changed:
            print(f"트렌드 유형 변경: {trend_type}")
    else:
        # 캐시된 트렌드 전용 프롬프트 사용
        analysis_prompt = st.session_state[trend_prompt_key]
        print(f"캐시된 트렌드 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 트렌드 분석")

    # 세션 상태 키 정의 - 모두 트렌드 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 트렌드 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 트렌드 분석 전용
    def on_trend_analyze_click():
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
        print(f"트렌드 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 트렌드 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 트렌드 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_trend_analyze_click,
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
            print(f"트렌드 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"트렌드 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 트렌드 데이터를 분석하고 있습니다..."):
                print(f"트렌드 분석: generate_ai_response 함수 호출 전")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"트렌드 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 트렌드 분석 실행' 버튼을 클릭하세요. 시계열 트렌드 데이터의 패턴과 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 트렌드 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"트렌드: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 트렌드 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 

# 트렌드 분석 UI 랜더링
def render_trend_ui(df):
    """트렌드 분석 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    st.subheader("트렌드 분석")
    
    # Get equipment type using the helper function
    equipment_type = get_equipment_type(df)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 트렌드 분석 유형 선택
    trend_type = st.selectbox(
        "트렌드 분석 유형",
        ["단순 이동평균", "지수 가중 이동평균", "계절성 분해", "추세선"]
    )
    
    if trend_type == "단순 이동평균":
        window_size = st.slider("윈도우 크기", 5, 500, 30)
    elif trend_type == "지수 가중 이동평균":
        window_size = st.slider("윈도우 크기", 5, 500, 30)
    elif trend_type == "계절성 분해":
        period = st.slider("계절성 주기 (일)", 1, 30, 7)
        period_hours = period * 24
    elif trend_type == "추세선":
        poly_degree = st.slider("다항식 차수", 1, 5, 1)
    
    # 데이터 준비
    # 시간 균등하게 리샘플링
    df_copy = df.copy()
    
    # 데이터 시각화
    if trend_type == "단순 이동평균":
        # 이동평균 계산
        df_copy['MA'] = df_copy[sensor_col].rolling(window=window_size).mean()
        
        # 시각화 (원본 + 이동평균)
        # 큰 데이터셋의 경우 샘플링
        if len(df_copy) > 10000:
            sample_size = 10000
            step = len(df_copy) // sample_size
            df_sample = df_copy.iloc[::step].copy()
        else:
            df_sample = df_copy.copy()
            
            fig = go.Figure()
            
        # 원본 데이터
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=df_sample[sensor_col],
            mode='lines',
            name='원본 데이터',
            line=dict(color='blue', width=1)
        ))
        
        # 이동평균
        fig.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=df_sample['MA'],
            mode='lines',
            name=f'{window_size} 포인트 이동평균',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title=f'{sensor_type_display} 단순 이동평균 (윈도우 크기: {window_size})',
            xaxis_title='시간',
            yaxis_title=f'{sensor_type_display} 값',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 추가 분석: 이동평균과 원본 데이터 간의 차이
        df_copy['MA_diff'] = df_copy[sensor_col] - df_copy['MA']
        
        # 차이 히스토그램
        fig2 = px.histogram(
            df_copy.dropna(), 
            x='MA_diff',
            nbins=50,
            title=f'{sensor_type_display} 이동평균과의 편차 분포',
            labels={'MA_diff': '이동평균과의 편차'}
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 편차 통계
        with st.expander("이동평균 편차 통계"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("평균 편차", f"{df_copy['MA_diff'].mean():.4f}")
                st.metric("표준 편차", f"{df_copy['MA_diff'].std():.4f}")
            
            with col2:
                st.metric("최소 편차", f"{df_copy['MA_diff'].min():.4f}")
                st.metric("최대 편차", f"{df_copy['MA_diff'].max():.4f}")
            
            with col3:
                st.metric("절대 편차 평균", f"{np.abs(df_copy['MA_diff']).mean():.4f}")
                st.metric("중앙 절대 편차", f"{np.median(np.abs(df_copy['MA_diff'].dropna() - np.median(df_copy['MA_diff'].dropna()))):.4f}")
        
        # 트렌드 통계 수집
        trend_stats = {
            "윈도우 크기": window_size,
            "평균 편차": f"{df_copy['MA_diff'].mean():.4f}",
            "표준 편차": f"{df_copy['MA_diff'].std():.4f}",
            "최소 편차": f"{df_copy['MA_diff'].min():.4f}",
            "최대 편차": f"{df_copy['MA_diff'].max():.4f}",
            "절대 편차 평균": f"{np.abs(df_copy['MA_diff']).mean():.4f}"
        }
        
        # AI 분석 호출
        render_ai_analysis(df=df_copy, equipment_type=equipment_type, trend_type=trend_type, trend_stats=trend_stats)
        
    elif trend_type == "지수 가중 이동평균":
        # 지수 가중 이동평균 계산
        df_copy['EWMA'] = df_copy[sensor_col].ewm(span=window_size).mean()
        
        # 시각화 (원본 + 지수 가중 이동평균)
        # 큰 데이터셋의 경우 샘플링
        if len(df_copy) > 10000:
            sample_size = 10000
            step = len(df_copy) // sample_size
            df_sample = df_copy.iloc[::step].copy()
        else:
            df_sample = df_copy.copy()
        
        fig = go.Figure()
        
        # 원본 데이터
        fig.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=df_sample[sensor_col],
            mode='lines',
            name='원본 데이터',
            line=dict(color='blue', width=1)
        ))
        
        # 지수 가중 이동평균
        fig.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=df_sample['EWMA'],
            mode='lines',
            name=f'지수 가중 이동평균 (span={window_size})',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title=f'{sensor_type_display} 지수 가중 이동평균 (span: {window_size})',
            xaxis_title='시간',
            yaxis_title=f'{sensor_type_display} 값',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 추가 분석: 알파 값에 따른 EWMA 비교
        st.write("#### 다양한 스무딩 파라미터 비교")
        
        alphas = [0.1, 0.2, 0.5]
        span_values = [int(2/alpha - 1) for alpha in alphas]
        
        fig2 = go.Figure()
        
        # 원본 데이터
        fig2.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=df_sample[sensor_col],
            mode='lines',
            name='원본 데이터',
            line=dict(color='gray', width=1)
        ))
        
        # 다양한 알파 값에 대한 EWMA
        colors = ['red', 'green', 'blue']
        for i, (alpha, span) in enumerate(zip(alphas, span_values)):
            ewma = df_sample[sensor_col].ewm(alpha=alpha).mean()
            
            fig2.add_trace(go.Scatter(
                x=df_sample['timestamp'],
                y=ewma,
                mode='lines',
                name=f'EWMA (α={alpha}, span={span})',
                line=dict(color=colors[i], width=2)
            ))
        
        fig2.update_layout(
            title=f'{sensor_type_display} 다양한 스무딩 파라미터의 지수 가중 이동평균 비교',
            xaxis_title='시간',
            yaxis_title=f'{sensor_type_display} 값',
            height=500
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # EWMA와 원본 데이터 간의 차이 계산
        df_copy['EWMA_diff'] = df_copy[sensor_col] - df_copy['EWMA']
        
        # 트렌드 통계 수집
        trend_stats = {
            "윈도우 크기(span)": window_size,
            "알파 값": f"{2/(window_size+1):.4f}",
            "평균 편차": f"{df_copy['EWMA_diff'].mean():.4f}",
            "표준 편차": f"{df_copy['EWMA_diff'].std():.4f}",
            "최소 편차": f"{df_copy['EWMA_diff'].min():.4f}",
            "최대 편차": f"{df_copy['EWMA_diff'].max():.4f}",
            "절대 편차 평균": f"{np.abs(df_copy['EWMA_diff']).mean():.4f}"
        }
        
        # AI 분석 호출
        render_ai_analysis(df=df_copy, equipment_type=equipment_type, trend_type=trend_type, trend_stats=trend_stats)
        
    elif trend_type == "계절성 분해":
        try:
            # 필요한 모듈 임포트
            try:
                from statsmodels.tsa.seasonal import seasonal_decompose
                from plotly.subplots import make_subplots
            except ImportError:
                st.error("계절성 분해 기능을 위해 statsmodels 패키지가 필요합니다. 'pip install statsmodels'를 실행하세요.")
                st.info("계절성 분해 기능을 사용할 수 없어 기본 차트만 표시합니다.")
                
                # 기본 시계열 차트 표시
                fig = px.line(
                    df.sample(min(10000, len(df))), 
                    x='timestamp', 
                    y=sensor_col,
                    title='시계열 데이터'
                )
                st.plotly_chart(fig, use_container_width=True)
                raise ImportError("statsmodels 패키지가 설치되어 있지 않습니다.")
            
            # 시계열 데이터로 변환 (균등한 시간 간격 필요)
            # 1시간 간격으로 리샘플링
            # value 열이 수치형인지 확인하고 변환
            df_with_numeric = df.copy()
            df_with_numeric[sensor_col] = pd.to_numeric(df_with_numeric[sensor_col], errors='coerce')
            
            # 비어있는 데이터가 있는지 확인
            if df_with_numeric[sensor_col].isna().any():
                st.warning("데이터에 숫자로 변환할 수 없는 값이 포함되어 있습니다. 해당 값들은 제외됩니다.")
                # NaN 값 제거
                df_with_numeric = df_with_numeric.dropna(subset=[sensor_col])
            
            # 데이터가 충분한지 확인
            if len(df_with_numeric) < 2 * period_hours:
                st.error(f"계절성 분해를 위해 최소 {2 * period_hours}개의 데이터 포인트가 필요합니다.")
                raise ValueError(f"데이터 포인트 수가 부족합니다: {len(df_with_numeric)} < {2 * period_hours}")
            
            # 리샘플링 - 명시적으로 수치 데이터만 리샘플링
            try:
                df_hourly = df_with_numeric.set_index('timestamp').resample('1h')[sensor_col].mean().reset_index()
                
                # NaN 값이 있는지 확인
                if df_hourly[sensor_col].isna().any():
                    st.warning(f"리샘플링 후 {df_hourly[sensor_col].isna().sum()}개의 NaN 값이 발생했습니다. 선형 보간법으로 처리합니다.")
                    # 결측값 처리
                    df_hourly[sensor_col] = df_hourly[sensor_col].interpolate(method='linear')
                
                # 시작과 끝의 NaN 값 처리 (보간할 수 없는 경우)
                df_hourly = df_hourly.dropna(subset=[sensor_col])
                
                # 데이터가 충분한지 다시 확인
                if len(df_hourly) < 2 * period_hours:
                    st.error(f"리샘플링 후 데이터가 부족합니다. 계절성 분해를 위해 최소 {2 * period_hours}개의 데이터 포인트가 필요합니다.")
                    raise ValueError(f"리샘플링 후 데이터 부족: {len(df_hourly)} < {2 * period_hours}")
                
            except Exception as e:
                st.error(f"리샘플링 중 오류가 발생했습니다: {str(e)}")
                raise e
            
            # 계절성 분해
            result = seasonal_decompose(
                df_hourly[sensor_col],
                model='additive',
                period=period_hours
            )
            
            # 분해 결과 시각화
            trend = result.trend
            seasonal = result.seasonal
            residual = result.resid
            
            # 원본 데이터 + 분해 결과 시각화
            fig = make_subplots(
                rows=4, 
                cols=1,
                subplot_titles=(f'원본 {sensor_type_display} 데이터', f'{sensor_type_display} 추세 성분', f'{sensor_type_display} 계절성 성분 (주기: {period}일)', f'{sensor_type_display} 잔차'),
                shared_xaxes=True,
                vertical_spacing=0.05
            )
            
            # 원본 데이터
            fig.add_trace(
                go.Scatter(x=df_hourly['timestamp'], y=df_hourly[sensor_col], mode='lines', name='원본 데이터'),
                row=1, col=1
            )
            
            # 추세 성분
            fig.add_trace(
                go.Scatter(x=df_hourly['timestamp'], y=trend, mode='lines', name='추세', line=dict(color='red')),
                row=2, col=1
            )
            
            # 계절성 성분
            fig.add_trace(
                go.Scatter(x=df_hourly['timestamp'], y=seasonal, mode='lines', name='계절성', line=dict(color='green')),
                row=3, col=1
            )
            
            # 잔차
            fig.add_trace(
                go.Scatter(x=df_hourly['timestamp'], y=residual, mode='lines', name='잔차', line=dict(color='purple')),
                row=4, col=1
            )
            
            fig.update_layout(height=800, title_text=f"{sensor_type_display} 시계열 분해 분석 (주기: {period}일)")
            st.plotly_chart(fig, use_container_width=True)
            
            # 계절성 패턴 자세히 보기
            with st.expander("계절성 패턴 상세 분석"):
                # 계절성 성분의 한 주기만 시각화
                seasonal_pattern = seasonal[:period_hours]
                hours = np.arange(period_hours)
                
                fig2 = px.line(
                    x=hours, 
                    y=seasonal_pattern,
                    labels={'x': '시간 (시)', 'y': f'{sensor_type_display} 계절성 효과'},
                    title=f'{sensor_type_display} {period}일 주기의 계절성 패턴'
                )
                
                fig2.update_xaxes(tickvals=np.arange(0, period_hours, 24), 
                                ticktext=[f'Day {i+1}' for i in range(period)])
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # 시간대별 효과
                hours_in_day = 24
                daily_pattern = np.zeros(hours_in_day)
                valid_days = 0
                
                # 데이터가 24시간 단위로 구성되어 있지 않을 수 있으므로, 전체 시간을 24시간 단위로 재구성
                # 모든 데이터를 24시간 단위(시간 별)로 접기
                for i in range(len(seasonal_pattern)):
                    hour_of_day = i % hours_in_day
                    daily_pattern[hour_of_day] += seasonal_pattern[i]
                    if hour_of_day == hours_in_day - 1:  # 하루가 완료되면 유효 일수 증가
                        valid_days += 1
                
                # 유효한 일수로 나누어 평균 계산
                if valid_days > 0:
                    # 각 시간대별로 유효한 데이터 포인트 수를 계산
                    hours_count = np.zeros(hours_in_day)
                    for i in range(len(seasonal_pattern)):
                        hour_of_day = i % hours_in_day
                        hours_count[hour_of_day] += 1
                    
                    # 각 시간대를 해당 시간대의 데이터 포인트 수로 나눔
                    for h in range(hours_in_day):
                        if hours_count[h] > 0:
                            daily_pattern[h] /= hours_count[h]
                    
                    # 플롯 데이터 준비
                    plot_hours = np.arange(hours_in_day)
                    plot_data = pd.DataFrame({
                        '시간': plot_hours,
                        '효과': daily_pattern
                    })
                    
                    # 시각화
                    fig3 = px.line(
                        plot_data,
                        x='시간', 
                        y='효과',
                        labels={'시간': '시간 (시)', '효과': f'{sensor_type_display} 평균 일간 효과'},
                        title=f'{sensor_type_display} 일 중 시간대별 평균 효과'
                    )
                    
                    fig3.update_xaxes(tickvals=np.arange(0, 24, 3))
                    
                    # y축 범위 명시적 설정
                    max_abs_val = max(abs(daily_pattern.min()), abs(daily_pattern.max()))
                    if max_abs_val > 0:
                        y_range = [-max_abs_val*1.1, max_abs_val*1.1]
                        fig3.update_layout(yaxis_range=y_range)
                    
                    # 그래프 표시
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.warning("일 중 시간대별 평균 효과를 계산할 데이터가 충분하지 않습니다.")
            
            # 성분별 기여도 분석
            with st.expander("성분별 기여도 분석"):
                # 각 성분의 분산 계산
                trend_var = np.nanvar(trend)
                seasonal_var = np.nanvar(seasonal)
                residual_var = np.nanvar(residual)
                total_var = trend_var + seasonal_var + residual_var
                
                # 기여도 계산
                trend_contrib = trend_var / total_var * 100
                seasonal_contrib = seasonal_var / total_var * 100
                residual_contrib = residual_var / total_var * 100
                
                # 기여도 시각화
                contrib_fig = px.pie(
                    values=[trend_contrib, seasonal_contrib, residual_contrib],
                    names=['추세', '계절성', '잔차'],
                    title=f'{sensor_type_display} 각 성분의 변동 기여도 (%)'
                )
                
                st.plotly_chart(contrib_fig, use_container_width=True)
                
                # 성분별 통계량
                st.write("#### 성분별 통계량")
                
                contrib_df = pd.DataFrame({
                    '성분': ['추세', '계절성', '잔차', '전체'],
                    '분산': [trend_var, seasonal_var, residual_var, total_var],
                    '표준편차': [np.sqrt(trend_var), np.sqrt(seasonal_var), np.sqrt(residual_var), np.sqrt(total_var)],
                    '기여도 (%)': [trend_contrib, seasonal_contrib, residual_contrib, 100.0]
                })
                
                st.dataframe(contrib_df)
                
            # 트렌드 통계 수집
            trend_stats = {
                "계절성 주기(일)": period,
                "추세 기여도(%)": f"{trend_contrib:.2f}%",
                "계절성 기여도(%)": f"{seasonal_contrib:.2f}%",
                "잔차 기여도(%)": f"{residual_contrib:.2f}%",
                "추세 표준편차": f"{np.sqrt(trend_var):.4f}",
                "계절성 표준편차": f"{np.sqrt(seasonal_var):.4f}",
                "잔차 표준편차": f"{np.sqrt(residual_var):.4f}"
            }
            
            # AI 분석 호출
            render_ai_analysis(df=df_copy, equipment_type=equipment_type, trend_type=trend_type, trend_stats=trend_stats)
                
        except Exception as e:
            st.error(f"계절성 분해 중 오류가 발생했습니다: {str(e)}")
            st.info("참고: 계절성 분해는 균등한 시간 간격의 데이터가 필요합니다.")
            
            # 오류 발생 시에도 기본 AI 분석 제공
            render_ai_analysis(df=df_copy, equipment_type=equipment_type, trend_type=trend_type)
        
    elif trend_type == "추세선":
        # 데이터 준비
        # 날짜를 숫자로 변환
        df_copy['time_idx'] = np.arange(len(df_copy))
        
        # 다항식 추세선 계산
        poly_model = np.polyfit(df_copy['time_idx'], df_copy[sensor_col], poly_degree)
        poly_trend = np.polyval(poly_model, df_copy['time_idx'])
        
        # 다항식 방정식 문자열 생성
        equation = "y = "
        for i, coef in enumerate(poly_model):
            power = poly_degree - i
            if power > 1:
                equation += f"{coef:.2e}x^{power} + "
            elif power == 1:
                equation += f"{coef:.2e}x + "
            else:
                equation += f"{coef:.2e}"
        
        # 시각화
        # 큰 데이터셋의 경우 샘플링
        if len(df_copy) > 10000:
            sample_size = 10000
            step = len(df_copy) // sample_size
            df_sample = df_copy.iloc[::step].copy()
        else:
            df_sample = df_copy.copy()
        
        # 추세선 시각화
        fig = go.Figure()
        
        # 원본 데이터
        fig.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=df_sample[sensor_col],
            mode='markers',
            name='원본 데이터',
            marker=dict(size=3, color='blue', opacity=0.5)
        ))
        
        # 추세선
        fig.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=poly_trend[df_sample.index],
            mode='lines',
            name=f'{poly_degree}차 다항식 추세선',
            line=dict(color='red', width=3)
        ))
        
        fig.update_layout(
            title=f'{sensor_type_display} {poly_degree}차 다항식 추세선 (방정식: {equation})',
            xaxis_title='시간',
            yaxis_title=f'{sensor_type_display} 값',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 추세선과의 잔차 분석
        df_copy['residual'] = df_copy[sensor_col] - poly_trend
        
        # 잔차 시각화
        fig2 = go.Figure()
        
        # 잔차 산점도
        fig2.add_trace(go.Scatter(
            x=df_sample['timestamp'],
            y=df_copy['residual'].iloc[df_sample.index],
            mode='markers',
            name='잔차',
            marker=dict(size=3, color='green', opacity=0.5)
        ))
        
        # 영선
        fig2.add_hline(y=0, line_dash="dash", line_color="red")
        
        fig2.update_layout(
            title=f'{sensor_type_display} 추세선과의 잔차',
            xaxis_title='시간',
            yaxis_title='잔차',
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 모델 평가
        with st.expander("추세선 모델 평가"):
            # RMSE, R² 계산
            mse = np.mean(df_copy['residual'] ** 2)
            rmse = np.sqrt(mse)
            
            ss_total = np.sum((df_copy[sensor_col] - df_copy[sensor_col].mean()) ** 2)
            ss_residual = np.sum(df_copy['residual'] ** 2)
            r2 = 1 - (ss_residual / ss_total)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("RMSE (평균 제곱근 오차)", f"{rmse:.4f}")
                st.metric("평균 절대 오차", f"{np.mean(np.abs(df_copy['residual'])):.4f}")
            
            with col2:
                st.metric("R² (결정계수)", f"{r2:.4f}")
                st.metric("평균 백분율 오차", f"{np.mean(np.abs(df_copy['residual'] / df_copy[sensor_col])) * 100:.2f}%")
            
            # 잔차 분포
            fig3 = px.histogram(
                df_copy, 
                x='residual',
                nbins=50,
                title=f'{sensor_type_display} 잔차 분포',
                labels={'residual': '잔차'}
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            # 다항식 차수에 따른 R² 비교
            degrees = range(1, min(6, poly_degree + 2))
            r2_values = []
            
            for degree in degrees:
                poly_model_i = np.polyfit(df_copy['time_idx'], df_copy[sensor_col], degree)
                poly_trend_i = np.polyval(poly_model_i, df_copy['time_idx'])
                residual_i = df_copy[sensor_col] - poly_trend_i
                
                ss_residual_i = np.sum(residual_i ** 2)
                r2_i = 1 - (ss_residual_i / ss_total)
                r2_values.append(r2_i)
            
            fig4 = px.line(
                x=degrees, 
                y=r2_values,
                markers=True,
                labels={'x': '다항식 차수', 'y': 'R² (결정계수)'},
                title=f'{sensor_type_display} 다항식 차수에 따른 R² 변화'
            )
            
            st.plotly_chart(fig4, use_container_width=True)
            
        # 트렌드 통계 수집
        trend_stats = {
            "다항식 차수": poly_degree,
            "R² (결정계수)": f"{r2:.4f}",
            "RMSE": f"{rmse:.4f}",
            "평균 절대 오차": f"{np.mean(np.abs(df_copy['residual'])):.4f}",
            "평균 백분율 오차": f"{np.mean(np.abs(df_copy['residual'] / df_copy[sensor_col])) * 100:.2f}%",
            "방정식": equation
        }
        
        # AI 분석 호출
        render_ai_analysis(df=df_copy, equipment_type=equipment_type, trend_type=trend_type, trend_stats=trend_stats)