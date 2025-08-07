import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
from scipy import stats
from ..utils import create_sample_dataframe, get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

# 히스토그램 생성
def create_histogram(_df, _nbins, _hist_type, _equipment_type, _show_kde=True, _show_rug=False):
    """히스토그램을 생성합니다."""
    # 샘플링된 데이터 사용
    df_sample = create_sample_dataframe(_df, max_points=10000)
    
    # Get sensor column name
    sensor_col = get_sensor_type()
    if sensor_col not in df_sample.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름 가져오기
    sensor_type_display = sensor_col
    
    # 기본 히스토그램 생성
    if _hist_type == "기본":
        fig = px.histogram(df_sample, x=sensor_col, nbins=_nbins,
                         title=f"{_equipment_type} {sensor_type_display} 분포",
                         labels={sensor_col: f"{sensor_type_display} 값", "count": "빈도"})
        
    elif _hist_type == "밀도":
        fig = px.histogram(df_sample, x=sensor_col, nbins=_nbins,
                         title=f"{_equipment_type} {sensor_type_display} 분포 (밀도)",
                         histnorm='density',
                         labels={sensor_col: f"{sensor_type_display} 값", "density": "밀도"})
        
    elif _hist_type == "누적":
        fig = px.histogram(df_sample, x=sensor_col, nbins=_nbins,
                         title=f"{_equipment_type} {sensor_type_display} 분포 (누적)",
                         histnorm='probability',
                         cumulative=True,
                         labels={sensor_col: f"{sensor_type_display} 값", "probability": "누적 확률"})
    
    # KDE 추가
    if _show_kde and _hist_type != "누적":
        hist_data = np.histogram(df_sample[sensor_col], bins=_nbins)
        x_kde = np.linspace(df_sample[sensor_col].min(), df_sample[sensor_col].max(), 1000)
        
        # KDE 계산
        kde = stats.gaussian_kde(df_sample[sensor_col])
        y_kde = kde(x_kde)
        
        # 적절한 스케일링
        if _hist_type == "기본":
            y_kde_scaled = y_kde * (len(df_sample) * (df_sample[sensor_col].max() - df_sample[sensor_col].min()) / _nbins)
        else:
            y_kde_scaled = y_kde
        
        fig.add_scatter(x=x_kde, y=y_kde_scaled, mode='lines', 
                      name='KDE', line=dict(color='red', width=2))
    
    # 러그 플롯 추가
    if _show_rug:
        rug_data = df_sample[sensor_col].sample(min(1000, len(df_sample))).values
        
        # 안전하게 y값 계산 (데이터가 없을 경우 기본값 사용)
        try:
            if len(fig.data) > 0 and hasattr(fig.data[0], 'y') and fig.data[0].y is not None:
                y_max = fig.data[0].y.max()
                if y_max:  # y_max가 0이 아닌 경우
                    rug_y_pos = np.ones_like(rug_data) * -0.03 * y_max
                    y_axis_range = [-0.05 * y_max, y_max * 1.05]
                else:
                    rug_y_pos = np.zeros_like(rug_data) - 0.01
                    y_axis_range = None
            else:
                rug_y_pos = np.zeros_like(rug_data) - 0.01
                y_axis_range = None
        except (AttributeError, IndexError, TypeError):
            # 오류 발생 시 안전한 기본값 사용
            rug_y_pos = np.zeros_like(rug_data) - 0.01
            y_axis_range = None
        
        # 러그 플롯 추가
        fig.add_scatter(
            x=rug_data, 
            y=rug_y_pos,
            mode='markers',
            marker=dict(symbol='line-ns', color='rgba(0, 0, 255, 0.7)', size=15, line=dict(width=1)),
            name='데이터 포인트 (러그 플롯)'
        )
        
        # y축 범위 조정 (안전하게)
        if y_axis_range is not None and (_hist_type == "기본" or _hist_type == "밀도"):
            fig.update_layout(yaxis=dict(range=y_axis_range))
    
    fig.update_layout(height=500)
    return fig

# 통계 계산
def get_additional_stats(_df):
    """추가 통계 정보를 계산합니다."""
    from ..utils import get_sensor_type
    
    # Get sensor column name
    sensor_col = get_sensor_type()
    if sensor_col not in _df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    return {
        "kurtosis": _df[sensor_col].kurtosis(),
        "skew": _df[sensor_col].skew()
    }

# QQ Plot 생성 함수
def create_qq_plot(data, title):
    """정규성 검증을 위한 QQ Plot을 생성합니다."""
    # 샘플링 (데이터가 너무 많을 경우)
    if len(data) > 5000:
        data = data.sample(5000)
    
    # NaN 값 제거
    data = data.dropna()
    
    # 데이터 준비
    sorted_data = np.sort(data)
    n = len(sorted_data)
    
    # 데이터 정규화 (표준화)
    mean = np.mean(sorted_data)
    std = np.std(sorted_data)
    if std > 0:  # 표준편차가 0이 아닐 때만 정규화
        normalized_data = (sorted_data - mean) / std
    else:
        normalized_data = sorted_data - mean
    
    # 이론적 분위수 계산
    theoretical_quantiles = stats.norm.ppf(np.arange(1, n + 1) / (n + 1))
    
    # NaN 및 Infinity 값 필터링 (이론적 분위수에서 발생할 수 있음)
    valid_indices = np.isfinite(theoretical_quantiles)
    theoretical_quantiles = theoretical_quantiles[valid_indices]
    normalized_data = normalized_data[valid_indices] if len(normalized_data) > 0 else normalized_data
    
    # QQ Plot 생성
    fig = go.Figure()
    
    # 산점도 추가
    fig.add_trace(go.Scatter(
        x=theoretical_quantiles,
        y=normalized_data,
        mode='markers',
        marker=dict(
            size=6,
            color='rgba(0, 0, 255, 0.7)',
            line=dict(width=1, color='blue')
        ),
        name='데이터 포인트'
    ))
    
    # 기준선 (y=x) 추가 - 데이터 포인트의 범위에 맞추기
    min_x = theoretical_quantiles.min() if len(theoretical_quantiles) > 0 else -3
    max_x = theoretical_quantiles.max() if len(theoretical_quantiles) > 0 else 3
    
    # 기준선의 범위를 데이터 범위에 맞게 설정
    line_x = np.linspace(min_x, max_x, 100)
    
    fig.add_trace(go.Scatter(
        x=line_x,
        y=line_x,  # 정규화된 데이터이므로 y=x 직선 사용
        mode='lines',
        line=dict(color='red', width=2, dash='dash'),
        name='정규분포 기준선'
    ))
    
    # 범위 계산 (데이터 및 이론적 분위수의 범위를 모두 포함)
    if len(normalized_data) > 0 and len(theoretical_quantiles) > 0:
        min_val = min(theoretical_quantiles.min(), normalized_data.min())
        max_val = max(theoretical_quantiles.max(), normalized_data.max())
        
        # 10% 여유 추가
        padding = (max_val - min_val) * 0.1
        axis_range = [min_val - padding, max_val + padding]
    else:
        axis_range = [-3, 3]  # 기본 범위
    
    # 레이아웃 설정
    fig.update_layout(
        title=title,
        xaxis_title='이론적 분위수 (Normal Distribution)',
        yaxis_title='표준화된 데이터 분위수',
        height=500,
        width=700,
        showlegend=True,
        xaxis=dict(range=axis_range),
        yaxis=dict(range=axis_range)
    )
    
    return fig

# 히스토그램 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, hist_type, nbins, show_kde, show_rug, add_stats, percentile_values, shapiro_stat=None, shapiro_p=None):
    """히스토그램 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # Get sensor column name
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 히스토그램 분석 전용 키 접두사 사용
    key_prefix = "histogram_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 히스토그램 유형을 세션 상태에 저장
    current_hist_type_key = f"{key_prefix}_current_hist_type"
    
    # 히스토그램 유형이 변경되었는지 확인
    hist_type_changed = False
    if current_hist_type_key in st.session_state:
        if st.session_state[current_hist_type_key] != hist_type:
            hist_type_changed = True
    else:
        # 최초 실행 시
        hist_type_changed = True
    
    # 현재 히스토그램 유형 업데이트
    st.session_state[current_hist_type_key] = hist_type
    
    # AI 분석 프롬프트 키
    histogram_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 히스토그램 유형이 변경되었거나 프롬프트가 없으면 새로 생성
    if hist_type_changed or histogram_prompt_key not in st.session_state:
        # 히스토그램 유형에 대한 설명 추가
        hist_type_description = ""
        hist_type_context = ""
        
        if hist_type == "기본":
            hist_type_description = "데이터의 빈도(frequency)를 보여주는 기본 히스토그램입니다. 각 막대의 높이는 해당 범위에 속하는 데이터 포인트의 개수를 나타냅니다."
            hist_type_context = "기본 히스토그램은 데이터의 분포 형태와 빈도를 직관적으로 파악하는 데 유용하며, 일반적인 분포 패턴과 이상치를 식별하는 데 적합합니다."
        elif hist_type == "밀도":
            hist_type_description = "데이터의 밀도(density)를 보여주는 히스토그램입니다. 각 막대의 높이는 전체 면적이 1이 되도록 정규화되어, 확률 밀도 함수와 유사하게 해석할 수 있습니다."
            hist_type_context = "밀도 히스토그램은 서로 다른 크기의 데이터셋을 비교하는 데 유용하며, 분포의 형태와 확률 밀도를 분석하는 데 적합합니다. KDE 커널와 함께 해석할 때 더 의미가 있습니다."
        elif hist_type == "누적":
            hist_type_description = "데이터의 누적 분포를 보여주는 히스토그램입니다. 각 막대는 해당 값 이하의 모든 데이터 포인트 비율을 나타내어, 데이터의 백분위수를 시각적으로 확인할 수 있습니다."
            hist_type_context = "누적 히스토그램은 특정 임계값 이하의 데이터 비율을 파악하거나, 백분위수 기반 분석에 유용합니다. 특히 장비의 성능 기준점이나 이상 임계값을 설정하는 데 도움이 됩니다."
        
        # KDE와 러그 플롯에 대한 설명
        kde_description = ""
        if show_kde and hist_type != "누적":
            kde_description = "커널 밀도 추정(KDE)는 데이터의 연속적인 확률 밀도 함수를 추정하는 방법으로, 히스토그램의 빈(bin) 경계에 의한 인위적 영향을 줄이고 부드러운 분포 곡선을 제공합니다."
        
        rug_description = ""
        if show_rug:
            rug_description = "러그 플롯은 개별 데이터 포인트의 위치를 x축 위에 작은 선으로 표시하여, 실제 데이터의 분포를 직관적으로 파악할 수 있게 합니다."
        
        # 히스토그램 데이터의 통계 및 특성 요약
        stats_summary = f"""
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 히스토그램 유형: {hist_type} ({hist_type_description})
- 구간 수: {nbins}
- KDE 표시 여부: {'예' if show_kde else '아니오'}{f' ({kde_description})' if kde_description else ''}
- 러그 플롯 표시 여부: {'예' if show_rug else '아니오'}{f' ({rug_description})' if rug_description else ''}
- 데이터 포인트 수: {len(df):,}개
- 평균값: {df[sensor_col].mean():.2f}
- 중앙값: {df[sensor_col].median():.2f}
- 최소값: {df[sensor_col].min():.2f}
- 최대값: {df[sensor_col].max():.2f}
- 표준편차: {df[sensor_col].std():.2f}
- 첨도: {add_stats['kurtosis']:.2f} (정규분포 대비: {add_stats['kurtosis']-3:.2f})
- 왜도: {add_stats['skew']:.2f}
"""
        
        # 백분위수 정보 추가
        percentiles = [0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]
        stats_summary += "\n주요 백분위수:\n"
        for i, p in enumerate(percentiles):
            stats_summary += f"* {p}%: {percentile_values[i]:.2f}\n"
        
        # 정규성 검정 결과 추가
        if shapiro_stat is not None and shapiro_p is not None:
            stats_summary += f"\n정규성 검정 (Shapiro-Wilk):\n"
            stats_summary += f"* 통계량: {shapiro_stat:.4f}\n"
            stats_summary += f"* p-value: {shapiro_p:.4e}\n"
            stats_summary += f"* 결론: 데이터가 {'정규 분포를 따르지 않습니다' if shapiro_p < 0.05 else '정규 분포를 따를 가능성이 있습니다'} (p {'<' if shapiro_p < 0.05 else '>='} 0.05)"
        
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 히스토그램을 통해 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {hist_type} 유형의 히스토그램으로 시각화되어 있습니다.
이 히스토그램 유형은 {hist_type_description}

히스토그램 유형 컨텍스트: {hist_type_context}

히스토그램에서 분석할 주요 포인트:
1. {sensor_type_display} 분포의 형태와 특성 (정규성, 치우침, 첨도)
2. 주요 구간 및 밀도 패턴
3. 이상치 존재 여부와 의미
4. 장비 성능 평가 및 운영에 대한 통찰
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 히스토그램 분석 결과입니다.

## 데이터 정보
{stats_summary}

## 분석 과제
위 히스토그램 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {sensor_type_display} 데이터 분포의 전반적인 특성
   - 정규성, 치우침(왜도), 첨도 등을 종합적으로 평가
   - {hist_type} 히스토그램에서 특히 주목할 만한 패턴 설명

2. 이상치의 존재 여부 및 의미
   - 분포에서 벗어난 값들의 패턴 분석
   - 이상치가 장비에 미치는 잠재적 영향 설명

3. 분포 형태가 장비 성능에 주는 의미
   - 현재 분포 패턴이 장비 상태와 성능에 대해 알려주는 정보
   - {hist_type} 히스토그램 관점에서 장비 성능 평가

4. 백분위수 기반의 주요 임계값 제안
   - 모니터링 및 알람을 위한 적절한 임계값 제안
   - 각 임계값의 실제적 의미와 적용 방안

5. 장비 운영 또는 예방 정비에 대한 실용적인 제안
   - 분석된 분포를 기반으로 한 구체적인 운영/정비 권장사항
   - 데이터에 기반한 최적 운영 조건 또는 방식 제안

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 {hist_type} 히스토그램의 특성을 고려하여 분석하고, 이 유형의 시각화가 제공하는 특별한 인사이트를 강조해주세요.
"""
        # 히스토그램 전용 프롬프트로 저장
        st.session_state[histogram_prompt_key] = analysis_prompt
        
        # 히스토그램 유형이 변경되면 캐시도 초기화
        if hist_type_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"히스토그램 유형이 변경되어 캐시 초기화: {hist_type}")
        
        # 디버깅용 로깅
        print(f"히스토그램 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
        print(f"stats_summary: {stats_summary}")
        print(f"시스템 프롬프트: {system_prompt}")
        if hist_type_changed:
            print(f"히스토그램 유형 변경: {hist_type}")
    else:
        # 캐시된 히스토그램 전용 프롬프트 사용
        analysis_prompt = st.session_state[histogram_prompt_key]
        print(f"캐시된 히스토그램 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 히스토그램 분석")

    # 세션 상태 키 정의 - 모두 히스토그램 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 히스토그램 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 히스토그램 분석 전용
    def on_hist_analyze_click():
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
        print(f"히스토그램 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 히스토그램 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 히스토그램 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_hist_analyze_click,
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
            print(f"히스토그램 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"히스토그램 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 히스토그램 데이터를 분석하고 있습니다..."):
                print(f"히스토그램 분석: generate_ai_response 함수 호출 전")
                print(f"프롬프트 첫 100자: {analysis_prompt[:100]}...")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"히스토그램 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 히스토그램 분석 실행' 버튼을 클릭하세요. 히스토그램 데이터의 분포와 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 히스토그램 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"히스토그램: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
            roles = [msg["role"] for msg in st.session_state[chat_history_key]]
            print(f"히스토그램: 대화 기록 역할 목록: {roles}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 히스토그램 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.")

# 히스토그램 UI 랜더링
def render_histogram_ui(df, df_stats):
    """히스토그램 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    # Get equipment type
    equipment_type = get_equipment_type(df)
    
    # Get sensor column name
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    st.subheader(f"{sensor_type_display} 분포")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        nbins = st.slider("구간 수", 10, 100, 50)
        hist_type = st.radio("히스토그램 유형", ["기본", "밀도", "누적"])
        show_kde = st.checkbox("커널 밀도 추정(KDE) 표시", value=True)
        show_rug = st.checkbox("러그 플롯 표시", value=False)
    
    # 분포 통계 표시 (캐시된 통계 사용)
    with col2:
        hist_stats = st.container()
        with hist_stats:
            st.metric(f"{sensor_type_display} 평균", f"{df_stats['mean']:.2f}")
            st.metric(f"{sensor_type_display} 표준편차", f"{df_stats['std']:.2f}")
            
            # 추가 통계는 필요할 때 계산 (낮은 빈도로 계산되는 통계)
            add_stats = get_additional_stats(df)
            st.metric("첨도", f"{add_stats['kurtosis']:.2f}", 
                     delta=f"{add_stats['kurtosis']-3:.2f} (정규분포 대비)",
                     delta_color="off")
            st.metric("왜도", f"{add_stats['skew']:.2f}")
    
    # 히스토그램 생성 및 표시
    fig = create_histogram(df, nbins, hist_type, equipment_type, show_kde, show_rug)
    st.plotly_chart(fig, use_container_width=True)
    
    # 정규성 검정 변수 초기화
    shapiro_stat = None
    shapiro_p = None
    
    # 백분위수 계산
    percentiles = [0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]
    percentile_values = np.percentile(df[sensor_col], percentiles)
    
    # 분포 적합성 검정 결과 표시
    with st.expander(f"{sensor_type_display} 분포 적합성 분석"):
        st.write("주요 통계 지표")
        
        # 백분위수 표시
        percentile_df = pd.DataFrame({
            '백분위수': [f"{p}%" for p in percentiles],
            f'{sensor_type_display} 값': percentile_values
        })
        
        st.dataframe(percentile_df)
        
        # QQ Plot 옵션
        show_qq_plot = st.checkbox("QQ Plot으로 정규성 확인", value=False)
        
        # QQ Plot 표시
        if show_qq_plot:
            qq_sample = df[sensor_col].dropna()
            if len(qq_sample) > 0:
                qq_fig = create_qq_plot(
                    qq_sample, 
                    f"{equipment_type} {sensor_type_display} QQ Plot (정규성 검증)"
                )
                st.plotly_chart(qq_fig, use_container_width=True)
                
                st.info("""
                **QQ Plot 해석 방법**:
                - 데이터가 정규 분포를 따르면 점들이 빨간색 대각선(기준선)에 가깝게 정렬됩니다.
                - 점들이 S자 형태를 이루면 데이터의 꼬리가 정규 분포보다 두껍습니다 (첨도가 높음).
                - 점들이 기준선보다 위/아래로 휘어지면 데이터가 왼쪽/오른쪽으로 치우쳐 있습니다 (왜도).
                """)
            else:
                st.warning("QQ Plot을 생성할 수 있는 유효한 데이터가 없습니다.")
        
        # 정규성 검정 결과
        try:
            # Shapiro-Wilk test (sample)
            shapiro_sample = df[sensor_col].sample(min(5000, len(df)))
            
            # 데이터 유효성 확인
            if shapiro_sample.isnull().any():
                st.warning("데이터에 누락된 값(NaN)이 있어 정규성 검정을 수행할 수 없습니다.")
            elif len(shapiro_sample) < 3:
                st.warning("데이터 포인트가 너무 적어 정규성 검정을 수행할 수 없습니다.")
            elif not np.isfinite(shapiro_sample).all():
                st.warning("데이터에 무한값이 있어 정규성 검정을 수행할 수 없습니다.")
            else:
                # 정규성 검정 실행
                shapiro_stat, shapiro_p = stats.shapiro(shapiro_sample)
                
                st.write("정규성 검정 (Shapiro-Wilk)")
                st.write(f"통계량: {shapiro_stat:.4f}, p-value: {shapiro_p:.4e}")
                
                if shapiro_p < 0.05:
                    st.write(f"결론: {sensor_type_display} 데이터가 정규 분포를 따르지 않습니다 (p < 0.05)")
                else:
                    st.write(f"결론: {sensor_type_display} 데이터가 정규 분포를 따를 가능성이 있습니다 (p >= 0.05)")
        except Exception as e:
            st.write(f"정규성 검정을 수행할 수 없습니다. 오류: {str(e)}")
            st.write("데이터 샘플 정보:", shapiro_sample.describe() if 'shapiro_sample' in locals() else "데이터 샘플링 실패")
    
    # AI 분석 부분 호출
    render_ai_analysis(
        df=df, 
        equipment_type=equipment_type,
        hist_type=hist_type,
        nbins=nbins,
        show_kde=show_kde,
        show_rug=show_rug,
        add_stats=add_stats,
        percentile_values=percentile_values,
        shapiro_stat=shapiro_stat,
        shapiro_p=shapiro_p
    ) 