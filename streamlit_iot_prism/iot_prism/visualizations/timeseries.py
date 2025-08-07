import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from ..utils import create_sample_dataframe, get_equipment_type, calculate_rolling_average, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json
import pandas as pd
import time

# 시계열 차트 생성
def create_timeseries_chart(_df_sample, _chart_type, _equipment_type, _has_rolling_avg=False, _show_trend=False, _rolling_window=0, _show_markers=False, _marker_size=5, _line_width=2, _use_log_scale=False, _main_color="#0000FF", _secondary_color="#FF0000", _outliers_indices=None):
    """시계열 차트를 생성합니다."""
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in _df_sample.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 새로운 방식: 모든 차트를 go.Figure로 통일하여 트레이스 순서를 직접 제어
    fig = go.Figure()
    
    # 차트 타입별 생성
    if _chart_type == "선 그래프":
        # 메인 데이터 트레이스 추가
        mode = 'lines+markers' if _show_markers else 'lines'
        fig.add_trace(
            go.Scatter(
                x=_df_sample['timestamp'],
                y=_df_sample[sensor_col],
                mode=mode,
                name=f'{sensor_col}',
                line=dict(color=_main_color, width=_line_width),
                marker=dict(size=_marker_size) if _show_markers else None,
            )
        )
        chart_title = f"{_equipment_type} {sensor_col} 시계열 데이터"
        
    elif _chart_type == "영역 차트":
        # 영역 차트 트레이스 추가
        mode = 'lines+markers' if _show_markers else 'lines'
        fig.add_trace(
            go.Scatter(
                x=_df_sample['timestamp'],
                y=_df_sample[sensor_col],
                mode=mode,
                name=f'{sensor_col}',
                fill='tozeroy',
                line=dict(color=_main_color, width=_line_width),
                marker=dict(size=_marker_size) if _show_markers else None,
            )
        )
        chart_title = f"{_equipment_type} {sensor_col} 시계열 데이터 (영역)"
        
    elif _chart_type == "산점도":
        # 산점도 트레이스 추가
        fig.add_trace(
            go.Scatter(
                x=_df_sample['timestamp'],
                y=_df_sample[sensor_col],
                mode='markers',
                name=f'{sensor_col}',
                marker=dict(size=_marker_size, color=_main_color, opacity=0.7)
            )
        )
        chart_title = f"{_equipment_type} {sensor_col} 시계열 데이터 (산점도)"
        
    elif _chart_type == "캔들스틱":
        # 캔들스틱 차트 처리
        df_ohlc = _df_sample.set_index('timestamp')
        df_ohlc = df_ohlc.resample('D').agg({sensor_col: ['first', 'max', 'min', 'last']})
        df_ohlc.columns = ['open', 'high', 'low', 'close']
        df_ohlc = df_ohlc.reset_index()
        
        fig.add_trace(
            go.Candlestick(
                x=df_ohlc['timestamp'],
                open=df_ohlc['open'],
                high=df_ohlc['high'],
                low=df_ohlc['low'],
                close=df_ohlc['close'],
                name='OHLC',
                increasing=dict(line=dict(color='green')),
                decreasing=dict(line=dict(color='red'))
            )
        )
        chart_title = f"{_equipment_type} {sensor_col} 일별 OHLC 차트"
    
    # 이동 평균 추가 - 메인 데이터 트레이스 이후에 추가하여 앞에 표시되도록 함
    if _has_rolling_avg and 'rolling_avg' in _df_sample.columns:
        mode = 'lines+markers' if _show_markers else 'lines'
        fig.add_trace(
            go.Scatter(
                x=_df_sample['timestamp'],
                y=_df_sample['rolling_avg'],
                mode=mode,
                name=f'{sensor_col} {_rolling_window} 포인트 이동평균',
                line=dict(color=_secondary_color, width=max(2, _line_width+1)),
                marker=dict(size=_marker_size) if _show_markers else None,
                opacity=0.9
            )
        )
    
    # 추세선 추가
    if _show_trend and _chart_type != "캔들스틱":
        _df_sample_for_trend = _df_sample.copy()
        _df_sample_for_trend['time_idx'] = range(len(_df_sample_for_trend))
        trend_values = calculate_trend(_df_sample_for_trend)
        
        fig.add_trace(
            go.Scatter(
                x=_df_sample['timestamp'],
                y=trend_values,
                mode='lines',
                name='추세선',
                line=dict(color='green', width=_line_width, dash='dash')
            )
        )
    
    # 이상치 표시 (지정된 경우)
    if _outliers_indices is not None and len(_outliers_indices) > 0:
        outliers_df = _df_sample.loc[_outliers_indices]
        fig.add_trace(
            go.Scatter(
                x=outliers_df['timestamp'],
                y=outliers_df[sensor_col],
                mode='markers',
                name='이상치',
                marker=dict(
                    size=_marker_size+4 if _show_markers else 10,
                    color='red',
                    symbol='circle-open',
                    line=dict(width=2, color='red')
                )
            )
        )
    
    # 레이아웃 설정 (로그 스케일 옵션 포함)
    yaxis_settings = dict(
        type="log" if _use_log_scale else "linear"
    )
    
    fig.update_layout(
        title=chart_title,
        xaxis_title="시간",
        yaxis_title=sensor_col,
        yaxis=yaxis_settings,
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# 추세선 계산
def calculate_trend(_df):
    """추세선을 계산합니다."""
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in _df.columns:
        sensor_col = "value"  # 기본값으로 fallback
        
    x = np.arange(len(_df))
    y = _df[sensor_col].values
    model = np.polyfit(x, y, 1)
    return np.poly1d(model)(x)

# 시계열 차트 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, chart_type, rolling_window, has_rolling_avg, show_trend, df_sample):
    """AI 분석 부분을 별도의 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 시계열 분석 전용 키 접두사 사용
    key_prefix = "timeseries_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 차트 유형을 세션 상태에 저장
    current_chart_type_key = f"{key_prefix}_current_chart_type"
    
    # 차트 유형이 변경되었는지 확인
    chart_type_changed = False
    if current_chart_type_key in st.session_state:
        if st.session_state[current_chart_type_key] != chart_type:
            chart_type_changed = True
    else:
        # 최초 실행 시
        chart_type_changed = True
    
    # 현재 차트 유형 업데이트
    st.session_state[current_chart_type_key] = chart_type
    
    # AI 분석 프롬프트 키
    timeseries_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 차트 유형이 변경되었거나 프롬프트가 없으면 새로 생성
    if chart_type_changed or timeseries_prompt_key not in st.session_state:
        # 차트 유형에 대한 설명 추가
        chart_type_description = ""
        chart_type_context = ""
        chart_type_analysis_focus = ""
        
        if chart_type == "선 그래프":
            chart_type_description = "각 데이터 포인트를 선으로 연결하여 시간에 따른 연속적인 변화를 보여주는 기본 시계열 차트입니다."
            chart_type_context = "선 그래프는 데이터의 추세, 패턴, 계절성을 파악하는 데 가장 적합하며, 연속적인 시간에 따른 변화를 직관적으로 보여줍니다."
            chart_type_analysis_focus = "전반적인 추세 방향, 주기적 패턴, 급격한 변화 지점에 주목하세요. 특히 시간에 따른 연속적인 변화와 장기적인 패턴을 분석하는 데 유용합니다."
        
        elif chart_type == "영역 차트":
            chart_type_description = "선 그래프와 유사하지만 선 아래 영역을 채워 시간에 따른 누적 또는 볼륨감 있는 변화를 강조하는 차트입니다."
            chart_type_context = "영역 차트는 데이터의 볼륨과 크기 변화를 시각적으로 강조하며, 특정 기준선(일반적으로 0)으로부터의 변화량을 직관적으로 표현합니다."
            chart_type_analysis_focus = "기준선으로부터의 변동 크기, 영역의 확장/축소 패턴, 전체 볼륨의 변화 추이에 주목하세요. 누적 효과나 총량의 변화를 분석하는 데 유용합니다."
        
        elif chart_type == "산점도":
            chart_type_description = "각 데이터 포인트를 개별 점으로 표시하여 시간에 따른 분포와 밀도를 보여주는 차트입니다."
            chart_type_context = "산점도는 데이터의 분포, 이상치, 클러스터링 패턴을 파악하는 데 유용하며, 연속적인 연결 없이 각 포인트의 독립적인 위치를 보여줍니다."
            chart_type_analysis_focus = "데이터 포인트의 밀집도, 이상치의 존재, 특정 시간대의 데이터 분포 패턴에 주목하세요. 데이터의 분산과 군집 현상을 분석하는 데 유용합니다."
        
        elif chart_type == "캔들스틱":
            chart_type_description = "일정 기간(일반적으로 일별) 동안의 시작값, 최고값, 최저값, 종료값을 하나의 캔들로 표시하는 차트입니다."
            chart_type_context = "캔들스틱 차트는 금융 데이터 분석에서 주로 사용되며, 특정 기간 내 값의 변동폭과 방향성을 한눈에 파악할 수 있게 합니다."
            chart_type_analysis_focus = "캔들의 모양(긴 꼬리, 짧은 몸통 등), 상승/하락 패턴의 연속성, 변동폭의 크기 변화에 주목하세요. 일간 변동성과 단기 추세를 분석하는 데 유용합니다."
        
        # 이동 평균 및 추세선에 대한 설명
        rolling_avg_description = ""
        if has_rolling_avg:
            rolling_avg_description = f"{rolling_window} 포인트 이동 평균은 노이즈를 줄이고 데이터의 중장기 추세를 더 명확하게 보여줍니다. 이동 평균선이 기준선 역할을 하여 단기 변동의 의미를 해석하는 데 도움이 됩니다."
        
        trend_description = ""
        if show_trend:
            # 추세선 계산
            df_for_trend = df_sample.copy()
            df_for_trend['time_idx'] = range(len(df_for_trend))
            
            # 센서 컬럼 이름 가져오기
            sensor_col = get_sensor_type()
            if sensor_col not in df_for_trend.columns:
                sensor_col = "value"  # 기본값으로 fallback
                
            model = np.polyfit(df_for_trend['time_idx'], df_for_trend[sensor_col], 1)
            
            trend_direction = "상승" if model[0] > 0 else "하락"
            trend_slope = abs(model[0])
            
            trend_description = f"추세선은 전체 기간에 대한 선형 회귀를 통해 계산된 {trend_direction} 추세(기울기: {trend_slope:.6f})를 보여줍니다. 이는 데이터의 장기적인 방향성을 나타냅니다."
        
        # 시계열 데이터의 통계 및 특성 요약
        # 센서 컬럼 이름 가져오기
        sensor_col = get_sensor_type()
        if sensor_col not in df.columns:
            sensor_col = "value"  # 기본값으로 fallback
            
        stats_summary = f"""
- 장비 유형: {equipment_type}
- 차트 유형: {chart_type} ({chart_type_description})
- 데이터 기간: {df['timestamp'].min().strftime('%Y-%m-%d')} ~ {df['timestamp'].max().strftime('%Y-%m-%d')}
- 데이터 포인트 수: {len(df):,}개
- 평균값: {df[sensor_col].mean():.4f}
- 중앙값: {df[sensor_col].median():.4f}
- 최소값: {df[sensor_col].min():.4f}
- 최대값: {df[sensor_col].max():.4f}
- 표준편차: {df[sensor_col].std():.4f}
- 변동계수: {df[sensor_col].std() / df[sensor_col].mean():.4f}
"""
        
        if has_rolling_avg:
            stats_summary += f"\n- 이동 평균: {rolling_avg_description}"
            
        if show_trend:
            stats_summary += f"\n- 추세선: {trend_description}"
        
        # 추가 패턴 정보
        pattern_info = ""
        if 'hour' in df.columns:
            peak_hour = df.groupby('hour')[sensor_col].mean().idxmax()
            low_hour = df.groupby('hour')[sensor_col].mean().idxmin()
            pattern_info += f"\n- 시간대별 패턴: 평균값이 가장 높은 시간대는 {peak_hour}시, 가장 낮은 시간대는 {low_hour}시입니다."
        
        if 'day_name' in df.columns:
            peak_day = df.groupby('day_name')[sensor_col].mean().idxmax()
            low_day = df.groupby('day_name')[sensor_col].mean().idxmin()
            pattern_info += f"\n- 요일별 패턴: 평균값이 가장 높은 요일은 {peak_day}, 가장 낮은 요일은 {low_day}입니다."
        
        if pattern_info:
            stats_summary += "\n\n주기 패턴:" + pattern_info
            
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 시계열 데이터를 통해 장비의 성능과 패턴을 분석하여 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_col} 값으로, {chart_type}으로 시각화되어 있습니다.
이 차트 유형은 {chart_type_description}

차트 유형 컨텍스트: {chart_type_context}

분석 시 중점을 두어야 할 사항: {chart_type_analysis_focus}

{rolling_avg_description if has_rolling_avg else ""}
{trend_description if show_trend else ""}

주요 분석 포인트:
1. 시간에 따른 {sensor_col} 값의 추세와 패턴
2. {sensor_col}의 주기성과 계절성 (일별, 주별, 월별 등)
3. {sensor_col} 값의 이상치와 특이 현상
4. {sensor_col} 값의 변화 지점과 원인 추론
5. 장비 운영에 대한 실용적 제안
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT 센서 데이터의 시계열 분석 결과입니다.

## 데이터 정보
{stats_summary}

## 분석 과제
위 시계열 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. 데이터의 전반적인 특성과 패턴
   - {chart_type}에서 관찰되는 {sensor_col} 값의 주요 특성 설명
   - {sensor_col}의 전반적인 추세와 변동성 평가

2. 주요 변동 사항 및 추세 분석
   - {sensor_col} 값의 주목할 만한 상승/하락 구간 식별
   - {chart_type} 관점에서 {sensor_col} 변동 패턴의 의미 해석

3. 시간대별/요일별 패턴 분석 (존재하는 경우)
   - {sensor_col}의 반복되는 주기 패턴 식별
   - 시간/요일에 따른 {sensor_col} 값 변화의 의미

4. 이상치 또는 특이한 패턴 분석
   - {sensor_col}의 비정상적 데이터 포인트 식별
   - 특이 패턴의 잠재적 원인 추론

5. 장비 운영 또는 예방 정비에 대한 실용적인 제안
   - {sensor_col} 시계열 패턴에 기반한 운영 최적화 방안
   - {sensor_col} 데이터 기반 유지보수 시점 및 방법 제안

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 {chart_type}의 특성을 고려한 분석을 제공하세요. 이 데이터는 {sensor_col} 센서에서 수집된 것임을 항상 염두에 두고 분석하세요.
"""
        # 시계열 전용 프롬프트로 저장
        st.session_state[timeseries_prompt_key] = analysis_prompt
        
        # 차트 유형이 변경되면 캐시도 초기화
        if chart_type_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"차트 유형이 변경되어 캐시 초기화: {chart_type}")
        
        # 디버깅용 로깅
        print(f"시계열 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
        print(f"stats_summary: {stats_summary}")
        print(f"시스템 프롬프트: {system_prompt}")
        if chart_type_changed:
            print(f"차트 유형 변경: {chart_type}")
    else:
        # 캐시된 시계열 전용 프롬프트 사용
        analysis_prompt = st.session_state[timeseries_prompt_key]
        print(f"캐시된 시계열 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 시계열 데이터 분석")

    # 세션 상태 키 정의
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 버튼 클릭 콜백 함수 정의
    def on_timeseries_analyze_click():
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
        print(f"시계열 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 시계열 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_timeseries_analyze_click,
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
            if running_key in st.session_state:
                st.session_state[running_key] = False
            print(f"시계열 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif running_key in st.session_state and st.session_state[running_key]:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"시계열 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 시계열 데이터를 분석하고 있습니다..."):
                print(f"시계열 분석: generate_ai_response 함수 호출 전")
                print(f"프롬프트 첫 100자: {analysis_prompt[:100]}...")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"시계열 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 시계열 분석 실행' 버튼을 클릭하세요. 시계열 데이터의 패턴과 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 시계열 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"시계열: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
            roles = [msg["role"] for msg in st.session_state[chat_history_key]]
            print(f"시계열: 대화 기록 역할 목록: {roles}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not (running_key in st.session_state and st.session_state[running_key]):
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 시계열 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.")

# 시계역 차트 UI 랜더링
def render_timeseries_ui(df):
    """시계열 차트 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # 세션 상태 초기화 (AI 분석용) - 먼저 AI 설정 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    # 진행 상태 표시를 위한 상태 체크
    is_ai_running = False
    if "timeseries_analysis_running" in st.session_state:
        is_ai_running = st.session_state.timeseries_analysis_running
    
    # 로딩 중 메시지 표시
    if is_ai_running:
        with st.spinner("데이터 시각화 및 AI 분석 준비 중..."):
            pass
    
    # 메인 UI 시작 - 스피너 안에 있지 않게 함
    st.subheader("시계열 데이터")
    
    # 고급 옵션 전환
    show_advanced = st.checkbox("고급 차트 옵션 표시", value=False)
    
    # 탭으로 옵션 정리
    if show_advanced:
        tabs = st.tabs(["기본 옵션", "시각화 옵션", "집계 옵션", "이상치 옵션"])
    else:
        tabs = [st.container()]
    
    # 기본 옵션 탭 (또는 일반 컨테이너)
    with tabs[0]:
        # Chart options
        chart_options = st.columns([1, 2])
        with chart_options[0]:
            chart_type = st.radio("차트 유형", ["선 그래프", "영역 차트", "산점도", "캔들스틱"])
            
        with chart_options[1]:
            col1, col2 = st.columns(2)
            with col1:
                rolling_window = st.slider("이동 평균 윈도우 크기", 0, 500, 0, 10)
                show_trend = st.checkbox("추세선 표시", value=False)
            with col2:
                st.write("&nbsp;")  # 캐시 초기화 버튼 제거
    
    # 시각화 옵션 탭
    if show_advanced:
        with tabs[1]:
            vis_col1, vis_col2 = st.columns(2)
            with vis_col1:
                show_markers = st.checkbox("데이터 포인트 마커 표시", value=False)
                marker_size = st.slider("마커 크기", 2, 10, 5) if show_markers else 5
                line_width = st.slider("선 두께", 1, 10, 2) if chart_type in ["선 그래프", "영역 차트"] else 2
            with vis_col2:
                use_log_scale = st.checkbox("Y축 로그 스케일 사용", value=False)
                custom_colors = st.checkbox("커스텀 색상 사용", value=False)
                if custom_colors:
                    main_color = st.color_picker("주 데이터 색상", "#0000FF")  # 기본 파란색
                    secondary_color = st.color_picker("보조 데이터 색상", "#FF0000")  # 기본 빨간색
                else:
                    main_color = "#0000FF"
                    secondary_color = "#FF0000"
    else:
        show_markers = False
        marker_size = 5
        line_width = 2
        use_log_scale = False
        custom_colors = False
        main_color = "#0000FF"
        secondary_color = "#FF0000"
    
    # 집계 옵션 탭
    if show_advanced:
        with tabs[2]:
            agg_col1, agg_col2 = st.columns(2)
            with agg_col1:
                apply_aggregation = st.checkbox("시간 집계 적용", value=False)
                if apply_aggregation:
                    agg_freq = st.selectbox(
                        "집계 빈도", 
                        ["시간별", "일별", "주별", "월별"]
                    )
                    agg_freq_map = {
                        "시간별": "H",
                        "일별": "D",
                        "주별": "W",
                        "월별": "M"
                    }
                    pd_freq = agg_freq_map[agg_freq]
            with agg_col2:
                if apply_aggregation:
                    agg_func = st.selectbox(
                        "집계 함수",
                        ["평균", "중앙값", "최소값", "최대값", "합계"]
                    )
                    agg_func_map = {
                        "평균": "mean",
                        "중앙값": "median",
                        "최소값": "min",
                        "최대값": "max",
                        "합계": "sum"
                    }
                    pd_func = agg_func_map[agg_func]
    else:
        apply_aggregation = False
    
    # 이상치 옵션 탭
    if show_advanced:
        with tabs[3]:
            outlier_col1, outlier_col2 = st.columns(2)
            with outlier_col1:
                highlight_outliers = st.checkbox("이상치 하이라이팅", value=False)
                if highlight_outliers:
                    outlier_method = st.selectbox(
                        "이상치 감지 방법",
                        ["Z-점수", "IQR (사분위수 범위)"]
                    )
            with outlier_col2:
                if highlight_outliers:
                    if outlier_method == "Z-점수":
                        z_threshold = st.slider("Z-점수 임계값", 1.0, 5.0, 3.0, 0.1)
                    else:  # IQR
                        iqr_factor = st.slider("IQR 계수", 1.0, 3.0, 1.5, 0.1)
    else:
        highlight_outliers = False
    
    # 날짜 범위 선택 (고급 옵션과 관계없이 항상 표시)
    date_range_container = st.container()
    with date_range_container:
        # 데이터의 시작 및 종료 날짜 가져오기
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        
        # 날짜 범위 선택기
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("시작 날짜", min_date, min_value=min_date, max_value=max_date)
        with date_col2:
            end_date = st.date_input("종료 날짜", max_date, min_value=min_date, max_value=max_date)
        
        # 선택된 날짜로 데이터 필터링
        mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
        df_filtered = df[mask]
        
        # 필터링된 데이터가 없는 경우 처리
        if len(df_filtered) == 0:
            st.warning("선택한 날짜 범위에 데이터가 없습니다. 다른 범위를 선택해주세요.")
            df_filtered = df  # 원본 데이터로 되돌림
    
    # 데이터프레임 생성 (필터링된 데이터 사용)
    if len(df_filtered) > 10000:
        step = len(df_filtered) // 10000
        df_sample = df_filtered.iloc[::step].copy()
    else:
        df_sample = df_filtered.copy()
    
    # 집계 적용 (고급 옵션에서 선택된 경우)
    if show_advanced and apply_aggregation:
        # 타임스탬프를 인덱스로 설정하고 리샘플링
        df_agg = df_filtered.set_index('timestamp')
        sensor_col = get_sensor_type()
        if sensor_col not in df_agg.columns:
            sensor_col = "value"  # 기본값으로 fallback
            
        # 리샘플링 및 집계 함수 적용
        df_agg = df_agg[sensor_col].resample(pd_freq).agg(pd_func).reset_index()
        df_agg = df_agg.rename(columns={0: sensor_col}) if isinstance(df_agg, pd.DataFrame) else pd.DataFrame({
            'timestamp': df_agg.index,
            sensor_col: df_agg.values
        })
        
        # 시각화를 위한 샘플링 (필요한 경우)
        if len(df_agg) > 10000:
            step = len(df_agg) // 10000
            df_sample = df_agg.iloc[::step].copy()
        else:
            df_sample = df_agg.copy()
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df_sample.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 이상치 감지 (고급 옵션에서 선택된 경우)
    outliers_indices = []
    if show_advanced and highlight_outliers:
        if outlier_method == "Z-점수":
            from scipy import stats
            z_scores = stats.zscore(df_sample[sensor_col].dropna())
            outliers_indices = df_sample[sensor_col].dropna().index[abs(z_scores) > z_threshold]
        else:  # IQR
            Q1 = df_sample[sensor_col].quantile(0.25)
            Q3 = df_sample[sensor_col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - iqr_factor * IQR
            upper_bound = Q3 + iqr_factor * IQR
            outliers_indices = df_sample[(df_sample[sensor_col] < lower_bound) | 
                                        (df_sample[sensor_col] > upper_bound)].index
    
    # Apply rolling average if requested
    has_rolling_avg = False
    if rolling_window > 0:
        # 캐시 제거 버전
        df_sample['rolling_avg'] = df_sample[sensor_col].rolling(window=rolling_window).mean()
        has_rolling_avg = True
    
    # Get equipment type
    equipment_type = get_equipment_type()
    
    # 차트 생성 (수정된 버전 - 새 옵션 반영)
    fig = create_timeseries_chart(
        _df_sample=df_sample, 
        _chart_type=chart_type, 
        _equipment_type=equipment_type,
        _has_rolling_avg=has_rolling_avg,
        _show_trend=show_trend,
        _rolling_window=rolling_window,
        _show_markers=show_markers,
        _marker_size=marker_size,
        _line_width=line_width,
        _use_log_scale=use_log_scale,
        _main_color=main_color,
        _secondary_color=secondary_color,
        _outliers_indices=outliers_indices if highlight_outliers else None
    )
    
    # 차트 표시
    st.plotly_chart(fig, use_container_width=True)
    
    # Add statistical insights
    with st.expander("시계열 데이터 분석"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("평균값", f"{df[sensor_col].mean():.4f}")
            st.metric("중앙값", f"{df[sensor_col].median():.4f}")
        with col2:
            st.metric("최소값", f"{df[sensor_col].min():.4f}")
            st.metric("최대값", f"{df[sensor_col].max():.4f}")
        with col3:
            st.metric("표준편차", f"{df[sensor_col].std():.4f}")
            st.metric("변동계수", f"{df[sensor_col].std() / df[sensor_col].mean():.4f}")
            
        # 시계열 분석 추가 기능
        st.subheader("시계열 패턴 분석")
        
        # 시간대별 평균
        st.write("##### 시간대별 패턴")
        if 'hour' in df.columns:
            hourly_avg = df.groupby('hour')[sensor_col].mean().reset_index()
            hourly_fig = px.line(hourly_avg, x='hour', y=sensor_col, 
                               title="시간대별 평균 값",
                               labels={"hour": "시간", sensor_col: f"평균 {sensor_col}"})
            st.plotly_chart(hourly_fig, use_container_width=True)
        
        # 요일별 평균
        st.write("##### 요일별 패턴")
        if 'day_of_week' in df.columns and 'day_name' in df.columns:
            daily_avg = df.groupby(['day_of_week', 'day_name'])[sensor_col].mean().reset_index()
            daily_avg = daily_avg.sort_values('day_of_week')
            
            daily_fig = px.bar(daily_avg, x='day_name', y=sensor_col,
                            title="요일별 평균 값",
                            labels={"day_name": "요일", sensor_col: f"평균 {sensor_col}"})
            st.plotly_chart(daily_fig, use_container_width=True)
    
    # histogram.py와 같은 통합 구조로 변경: 자체 함수 내에서 AI 분석 직접 호출
    render_ai_analysis(df, equipment_type, chart_type, rolling_window, has_rolling_avg, show_trend, df_sample) 