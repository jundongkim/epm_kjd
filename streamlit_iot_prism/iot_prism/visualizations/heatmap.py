import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

# 히트맵 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, sensor_type_display, color_scale, show_cell_values, peak_hour, low_hour, peak_month, low_month, max_period, min_period, max_season, min_season):
    """히트맵 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 히트맵 분석 전용 키 접두사 사용
    key_prefix = "heatmap_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 시각화 설정을 세션 상태에 저장
    current_config_key = f"{key_prefix}_current_config"
    
    # 시각화 설정이 변경되었는지 확인
    config_changed = False
    if current_config_key in st.session_state:
        current_config = st.session_state[current_config_key]
        if current_config["color_scale"] != color_scale or current_config["show_cell_values"] != show_cell_values:
            config_changed = True
    else:
        # 최초 실행 시
        config_changed = True
    
    # 현재 시각화 설정 업데이트
    st.session_state[current_config_key] = {
        "color_scale": color_scale,
        "show_cell_values": show_cell_values
    }
    
    # AI 분석 프롬프트 키
    heatmap_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 시각화 설정이 변경되었거나 프롬프트가 없으면 새로 생성
    if config_changed or heatmap_prompt_key not in st.session_state:
        # 시간대별 분석 정보
        time_analysis = f"""
## 시간대별 분석
- 최대값 시간대: {peak_hour}시 (평균값이 가장 높음)
- 최소값 시간대: {low_hour}시 (평균값이 가장 낮음)
- 일중 값이 가장 높은 시간대: {max_period[0]} (평균: {max_period[1]:.4f})
- 일중 값이 가장 낮은 시간대: {min_period[0]} (평균: {min_period[1]:.4f})
"""

        # 월별 분석 정보
        month_analysis = f"""
## 월별 분석
- 최대값 월: {peak_month}월 (평균값이 가장 높음)
- 최소값 월: {low_month}월 (평균값이 가장 낮음)
- 값이 가장 높은 계절: {max_season[0]} (평균: {max_season[1]:.4f})
- 값이 가장 낮은 계절: {min_season[0]} (평균: {min_season[1]:.4f})
"""

        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 히트맵으로 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, 월별/시간별로 그룹화되어 있습니다.
이 히트맵은 시간(0-23시)과 월(1-12월)에 따른 {sensor_type_display} 값의 패턴을 보여줍니다.

주요 분석 포인트:
1. 시간대별/월별 패턴과 주기성
2. 특정 시간대나 월에 나타나는 이상치나 특이점
3. {sensor_type_display} 값의 계절적 변동성과 그 의미
4. 시간대별 패턴이 장비 성능에 주는 의미
5. 장비 운영 최적화를 위한 실용적 제안
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 히트맵 분석 결과입니다.

## 히트맵 정보
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 시각화: 월별(1-12월)/시간별(0-23시) 히트맵
- 색상 스케일: {color_scale}
- 셀 값 표시: {'예' if show_cell_values else '아니오'}

{time_analysis}

{month_analysis}

## 분석 과제
위 히트맵 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. 시간대별/월별 {sensor_type_display} 패턴의 전반적인 특성
   - 하루 중 {sensor_type_display} 값이 높아지는/낮아지는 시간대의 패턴 설명
   - 연중 {sensor_type_display} 값이 높아지는/낮아지는 월의 패턴 설명

2. 히트맵에서 나타나는 주요 패턴과 그 의미
   - 뚜렷한 클러스터나 패턴이 보이는 영역 설명
   - 일/월 주기성과 계절성의 분명한 증거

3. 이상치나 특이점의 존재 여부 및 의미
   - 특정 시간대/월에 나타나는 비정상적인 {sensor_type_display} 값 패턴 설명
   - 이러한 이상치가 장비 성능에 주는 의미 해석

4. 계절적 변동성과 장비 성능 간의 관계
   - 계절에 따른 {sensor_type_display} 값 변화가 장비 성능에 미치는 영향
   - 특정 계절/월에 나타나는 장비 부하 패턴 분석

5. 장비 운영 최적화를 위한 실용적인 제안
   - 히트맵에서 관찰된 패턴에 기반한 운영 전략
   - 최적/비최적 운영 시간대와 월에 대한 구체적인 권장사항

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요.
"""
        # 히트맵 전용 프롬프트로 저장
        st.session_state[heatmap_prompt_key] = analysis_prompt
        
        # 시각화 설정이 변경되면 캐시도 초기화
        if config_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"시각화 설정이 변경되어 캐시 초기화")
        
        # 디버깅용 로깅
        print(f"히트맵 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
    else:
        # 캐시된 히트맵 전용 프롬프트 사용
        analysis_prompt = st.session_state[heatmap_prompt_key]
        print(f"캐시된 히트맵 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 히트맵 분석")

    # 세션 상태 키 정의 - 모두 히트맵 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 히트맵 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 히트맵 분석 전용
    def on_heatmap_analyze_click():
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
        print(f"히트맵 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 히트맵 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 히트맵 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_heatmap_analyze_click,
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
            print(f"히트맵 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"히트맵 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 히트맵 데이터를 분석하고 있습니다..."):
                print(f"히트맵 분석: generate_ai_response 함수 호출 전")
                print(f"프롬프트 첫 100자: {analysis_prompt[:100]}...")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"히트맵 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 히트맵 분석 실행' 버튼을 클릭하세요. 히트맵 데이터의 패턴과 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 히트맵 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"히트맵: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
            roles = [msg["role"] for msg in st.session_state[chat_history_key]]
            print(f"히트맵: 대화 기록 역할 목록: {roles}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 히트맵 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.")

# 히트맵 UI 랜더링
def render_heatmap_ui(df):
    """히트맵 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
        
    st.subheader("월별/시간별 히트맵")
    
    # Get equipment type using the helper function
    equipment_type = get_equipment_type(df)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 히트맵 설정
    st.subheader("히트맵 설정")
    
    col1, col2 = st.columns(2)
    with col1:
        color_scale = st.selectbox(
            "색상 스케일",
            ["Viridis", "Blues", "Plasma", "Inferno", "RdBu_r", "Spectral", "YlOrRd", "YlGnBu"]
        )
        show_cell_values = st.checkbox("셀 값 표시", value=True)
    
    # Add month and hour columns
    df_copy = df.copy()
    df_copy['month'] = df_copy['timestamp'].dt.month
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    
    # Create pivot table
    heatmap_data = df_copy.pivot_table(
        values=sensor_col,  # 'value' 대신 센서 컬럼 사용
        index='hour',
        columns='month',
        aggfunc='mean'
    )
    
    # 상관관계 분석과 유사한 방식으로 히트맵 생성
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[f"{i}월" for i in range(1, 13)], 
        y=[f"{i}시" for i in range(24)],
        colorscale=color_scale,
        colorbar=dict(title=f"평균 {sensor_type_display}"),
        text=np.round(heatmap_data.values, 4),
        texttemplate="%{text}" if show_cell_values else None,
        hoverinfo="x+y+z"
    ))
    
    fig.update_layout(
        title={
            'text': f"{equipment_type} 월별/시간별 평균 {sensor_type_display}",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20}
        },
        height=700,
        width=1800,
        xaxis_title="월",
        yaxis_title="시간",
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(12)),
            ticktext=[f"{i}월" for i in range(1, 13)],
            tickangle=0
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(24)),
            ticktext=[f"{i}시" for i in range(24)]
        ),
        margin=dict(l=50, r=50, t=100, b=80)
    )
    
    # Plotly 차트 표시 (use_container_width=False로 설정하여 지정한 너비 사용)
    st.plotly_chart(fig, use_container_width=False)
    
    # 기본 분석 정보 표시
    with st.expander("히트맵 분석"):
        # 시간대별 분석
        hour_avg = df_copy.groupby('hour')[sensor_col].mean()  # 'value' 대신 센서 컬럼 사용
        peak_hour = hour_avg.idxmax()
        low_hour = hour_avg.idxmin()
        
        st.write(f"**시간대 분석:**")
        st.write(f"- 최대값 시간대: {peak_hour}시 (평균: {hour_avg[peak_hour]:.4f})")
        st.write(f"- 최소값 시간대: {low_hour}시 (평균: {hour_avg[low_hour]:.4f})")
        
        # 월별 분석
        month_avg = df_copy.groupby('month')[sensor_col].mean()  # 'value' 대신 센서 컬럼 사용
        peak_month = month_avg.idxmax()
        low_month = month_avg.idxmin()
        
        st.write(f"**월별 분석:**")
        st.write(f"- 최대값 월: {peak_month}월 (평균: {month_avg[peak_month]:.4f})")
        st.write(f"- 최소값 월: {low_month}월 (평균: {month_avg[low_month]:.4f})")
        
        # 패턴 요약
        st.write("**주요 패턴:**")
        
        # 일간 패턴 분석
        morning_avg = hour_avg[6:12].mean()
        afternoon_avg = hour_avg[12:18].mean()
        evening_avg = hour_avg[18:24].mean()
        night_avg = hour_avg[0:6].mean()
        
        max_period = max(
            ("아침(6-12시)", morning_avg),
            ("오후(12-18시)", afternoon_avg),
            ("저녁(18-24시)", evening_avg),
            ("새벽(0-6시)", night_avg),
            key=lambda x: x[1]
        )
        
        min_period = min(
            ("아침(6-12시)", morning_avg),
            ("오후(12-18시)", afternoon_avg),
            ("저녁(18-24시)", evening_avg),
            ("새벽(0-6시)", night_avg),
            key=lambda x: x[1]
        )
        
        st.write(f"- 일 중 값이 가장 높은 시간대: {max_period[0]} (평균: {max_period[1]:.4f})")
        st.write(f"- 일 중 값이 가장 낮은 시간대: {min_period[0]} (평균: {min_period[1]:.4f})")
        
        # 계절 패턴 분석
        spring_avg = month_avg[3:6].mean()
        summer_avg = month_avg[6:9].mean()
        fall_avg = month_avg[9:12].mean()
        winter_avg = pd.concat([month_avg[1:3], month_avg[12:13] if 12 in month_avg.index else pd.Series()]).mean()
        
        max_season = max(
            ("봄(3-5월)", spring_avg),
            ("여름(6-8월)", summer_avg),
            ("가을(9-11월)", fall_avg),
            ("겨울(12-2월)", winter_avg),
            key=lambda x: x[1]
        )
        
        min_season = min(
            ("봄(3-5월)", spring_avg),
            ("여름(6-8월)", summer_avg),
            ("가을(9-11월)", fall_avg),
            ("겨울(12-2월)", winter_avg),
            key=lambda x: x[1]
        )
        
        st.write(f"- 값이 가장 높은 계절: {max_season[0]} (평균: {max_season[1]:.4f})")
        st.write(f"- 값이 가장 낮은 계절: {min_season[0]} (평균: {min_season[1]:.4f})")
    
    # AI 분석 부분 호출
    render_ai_analysis(
        df=df,
        equipment_type=equipment_type,
        sensor_type_display=sensor_type_display,  # 센서 타입 정보 전달
        color_scale=color_scale,
        show_cell_values=show_cell_values,
        peak_hour=peak_hour,
        low_hour=low_hour,
        peak_month=peak_month,
        low_month=low_month,
        max_period=max_period,
        min_period=min_period,
        max_season=max_season,
        min_season=min_season
    ) 