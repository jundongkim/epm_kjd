import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal
import pywt
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

# 시간-주파수 도메인 웨이블릿 변환 함수
def create_wavelet_transform(df, wavelet_type, scales, sensor_col):
    """웨이블릿 변환을 수행하고 시간-주파수 분석 결과를 반환합니다."""
    # 샘플링된 데이터 사용
    from ..utils import create_sample_dataframe
    df_sample = create_sample_dataframe(df, max_points=10000)
    
    # 데이터 추출
    data = df_sample[sensor_col].values
    
    # 선형 트렌드 제거
    data = signal.detrend(data)
    
    # 웨이블릿 변환 수행
    coeffs, freqs = pywt.cwt(data, scales, wavelet_type)
    
    # 시간축 생성 (데이터 길이에 맞춰)
    time_axis = np.arange(len(data))
    
    return coeffs, freqs, time_axis, data

# 시간-주파수 도메인 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, sensor_type_display, wavelet_type, scales, freq_bands, band_energy, pattern_threshold):
    """시간-주파수 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()
    
    # 시간-주파수 분석 전용 키 접두사 사용
    key_prefix = "timefreq_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 웨이블릿 유형을 세션 상태에 저장
    current_wavelet_type_key = f"{key_prefix}_current_wavelet_type"
    
    # 웨이블릿 유형이 변경되었는지 확인
    wavelet_type_changed = False
    if current_wavelet_type_key in st.session_state:
        if st.session_state[current_wavelet_type_key] != wavelet_type:
            wavelet_type_changed = True
    else:
        # 최초 실행 시
        wavelet_type_changed = True
    
    # 현재 웨이블릿 유형 업데이트
    st.session_state[current_wavelet_type_key] = wavelet_type
    
    # AI 분석 프롬프트 키
    timefreq_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 웨이블릿 유형이 변경되었거나 프롬프트가 없으면 새로 생성
    if wavelet_type_changed or timefreq_prompt_key not in st.session_state:
        # 웨이블릿 유형에 대한 설명 추가
        wavelet_type_description = ""
        wavelet_type_context = ""
        
        if wavelet_type == "morl":
            wavelet_type_description = "모렛(Morlet) 웨이블릿은 사인파에 가우시안 윈도우를 적용한 형태로, 시간-주파수 지역화에 뛰어나며 주기적 신호 검출에 적합합니다."
            wavelet_type_context = "모렛 웨이블릿은 주파수 해상도가 높아 주기적 패턴 식별에 유용하며, 시간에 따른 주파수 변화를 분석하는 데 적합합니다."
        elif wavelet_type == "cmor":
            wavelet_type_description = "복소 모렛(Complex Morlet) 웨이블릿은 복소수 기반 웨이블릿으로, 위상 정보를 포함하고 있어 시간-주파수 분석에 더 풍부한 정보를 제공합니다."
            wavelet_type_context = "복소 모렛 웨이블릿은 진폭과 위상 정보를 모두 분석할 수 있어, 신호의 순간적인 주파수 변화와 위상 시프트를 검출하는 데 유용합니다."
        elif wavelet_type == "gaus1":
            wavelet_type_description = "가우시안 1차 도함수(Gaussian derivative) 웨이블릿은 신호의 변화율을 감지하는 데 특화되어 있어 급격한 변화나 에지 검출에 유용합니다."
            wavelet_type_context = "가우시안 1차 도함수 웨이블릿은 신호의 급격한 변화와 트렌드 전환점을 식별하는 데 적합하며, 이상 징후의 시작점을 감지하는 데 활용될 수 있습니다."
        elif wavelet_type == "mexh":
            wavelet_type_description = "멕시칸 햇(Mexican hat) 웨이블릿은 가우시안 2차 도함수 형태로, 피크와 밸리 검출에 뛰어나고 특히 국소적 특징을 감지하는 데 유용합니다."
            wavelet_type_context = "멕시칸 햇 웨이블릿은 시간 해상도가 높아 국소적인 이벤트와 특이점을 감지하는 데 적합하며, 신호의 일시적인 특성 분석에 활용됩니다."
        
        # 주파수 대역 정보를 문자열로 변환
        freq_bands_str = ""
        for band_name, band_range in freq_bands.items():
            energy_ratio = band_energy[band_name] / sum(band_energy.values()) if band_name in band_energy else 0
            freq_bands_str += f"- {band_name}: {band_range[0]:.4f} ~ {band_range[1]:.4f} Hz (에너지 비율: {energy_ratio:.2%})\n"
        
        # 스케일 정보
        scale_info = f"스케일 범위: {scales[0]:.1f} ~ {scales[-1]:.1f} (총 {len(scales)}개 스케일)"
        
        # 분석 정보 요약
        analysis_summary = f"""
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 웨이블릿 타입: {wavelet_type} ({wavelet_type_description})
- {scale_info}
- 패턴 강조 임계값: {pattern_threshold}
- 데이터 포인트 수: {len(df):,}개

주파수 대역별 에너지 분포:
{freq_bands_str}
"""
        
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터의 시간-주파수 분석 전문가입니다. 웨이블릿 변환을 통해 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {wavelet_type} 웨이블릿을 사용한 시간-주파수 분석이 수행되었습니다.
웨이블릿 설명: {wavelet_type_description}

웨이블릿 분석 컨텍스트: {wavelet_type_context}

시간-주파수 분석에서 주목할 주요 포인트:
1. 시간에 따른 주파수 변화 패턴
2. 주요 주파수 대역의 에너지 분포와 의미
3. 특정 시간대에 감지되는 비정상적 주파수 패턴
4. 장비 상태 모니터링 관점에서의 시간-주파수 패턴 해석
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 시간-주파수 분석 결과입니다.

## 데이터 정보
{analysis_summary}

## 분석 과제
위 시간-주파수 분석 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {sensor_type_display} 데이터의 시간-주파수 특성 개요
   - 주요 주파수 대역의 분포와 시간에 따른 변화 패턴
   - {wavelet_type} 웨이블릿 변환을 통해 발견된 특징적인 패턴 설명

2. 주파수 대역별 특성 분석
   - 각 주파수 대역(저주파/중주파/고주파)이 나타내는 장비 작동 특성
   - 에너지가 집중된 주파수 대역의 의미와 중요성

3. 시간에 따른 주파수 변화 패턴 해석
   - 특정 시간대에 집중되는 주파수 패턴과 그 의미
   - 시간-주파수 패턴의 정상/비정상 여부 판단

4. 이상 징후 및 특이 패턴 식별
   - 비정상적인 시간-주파수 패턴 존재 여부와 의미
   - 일반적인 패턴에서 벗어나는 특이점 분석

5. 장비 모니터링 및 유지보수 관점의 제안
   - 시간-주파수 분석을 활용한 모니터링 전략
   - 특정 주파수 대역 모니터링을 통한 장비 상태 평가 방법

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 {wavelet_type} 웨이블릿의 특성을 고려하여 분석하고, 이 유형의 시간-주파수 분석이 제공하는 특별한 인사이트를 강조해주세요.
"""
        # 시간-주파수 전용 프롬프트로 저장
        st.session_state[timefreq_prompt_key] = analysis_prompt
        
        # 웨이블릿 유형이 변경되면 캐시도 초기화
        if wavelet_type_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"웨이블릿 유형이 변경되어 캐시 초기화: {wavelet_type}")
    else:
        # 캐시된 시간-주파수 전용 프롬프트 사용
        analysis_prompt = st.session_state[timefreq_prompt_key]

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 시간-주파수 분석")

    # 세션 상태 키 정의 - 모두 시간-주파수 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 시간-주파수 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 시간-주파수 분석 전용
    def on_timefreq_analyze_click():
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
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 시간-주파수 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 시간-주파수 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_timefreq_analyze_click,
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
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 시간-주파수 데이터를 분석하고 있습니다..."):
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 시간-주파수 분석 실행' 버튼을 클릭하세요. 시간-주파수 데이터의 패턴과 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 시간-주파수 데이터에 대해 질문하기")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 시간-주파수 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 

# 시간-주파수 도메인 분석 UI 랜더링
def render_timefreq_ui(df):
    """시간-주파수 도메인 분석 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    init_ai_settings()
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        render_ai_settings_ui()
    
    # 장비 유형 가져오기
    equipment_type = get_equipment_type(df)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    st.subheader("시간-주파수 도메인 분석")
    
    # 분석 옵션 설정
    timefreq_options = st.columns([1, 2])
    with timefreq_options[0]:
        # 웨이블릿 타입 선택
        wavelet_type = st.selectbox("웨이블릿 타입", 
                                 ["morl", "cmor", "gaus1", "mexh"], 
                                 index=0)
        
        # 스케일 범위 설정
        scale_min = st.number_input("최소 스케일", min_value=1, max_value=64, value=1)
        scale_max = st.number_input("최대 스케일", min_value=8, max_value=128, value=64)
        scale_count = st.slider("스케일 개수", min_value=8, max_value=64, value=32)
        
        # 컬러맵 선택
        colormap = st.selectbox("컬러맵", 
                              ["viridis", "plasma", "inferno", "magma", "jet"], 
                              index=0)
        
        # 패턴 강조 임계값
        pattern_threshold = st.slider("패턴 강조 임계값", 0.1, 1.0, 0.3, 0.05)
        
    with timefreq_options[1]:
        st.write("시간-주파수 도메인 분석은 신호의 주파수 특성이 시간에 따라 어떻게 변화하는지 분석합니다.")
        st.write("웨이블릿 변환을 통해 특정 시간대에 나타나는 주기적 패턴을 식별할 수 있습니다.")
        st.write("데이터의 비정상성 패턴 분석과 순간적인 주파수 변화 감지에 유용합니다.")

    # 웨이블릿 분석 실행
    try:
        # 스케일 배열 생성
        scales = np.linspace(scale_min, scale_max, scale_count)
        
        # 웨이블릿 변환 수행
        coeffs, freqs, time_axis, detrended_data = create_wavelet_transform(df, wavelet_type, scales, sensor_col)
        
        # 시간-주파수 히트맵 표시
        fig1 = go.Figure()
        
        # 히트맵 데이터 추가
        fig1.add_trace(
            go.Heatmap(
                z=np.abs(coeffs),
                x=time_axis,
                y=freqs,
                colorscale=colormap,
                colorbar=dict(title="진폭"),
                zmin=0,
                zmax=np.max(np.abs(coeffs)) * pattern_threshold
            )
        )
        
        fig1.update_layout(
            title=f"{equipment_type} {sensor_type_display} 웨이블릿 변환 (시간-주파수 분석)",
            xaxis_title="시간 인덱스",
            yaxis_title="주파수 (Hz)",
            yaxis=dict(type="log"),
            height=500
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # 원본 시계열 데이터 플롯
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=time_axis,
                y=detrended_data,
                mode="lines",
                name=f"{sensor_type_display} 값"
            )
        )
        
        fig2.update_layout(
            title=f"{equipment_type} {sensor_type_display} 시계열 데이터 (트렌드 제거)",
            xaxis_title="시간 인덱스",
            yaxis_title=f"{sensor_type_display} 값",
            height=300
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 주파수 별 특성 분석
        st.subheader("주파수 대역별 특성")
        
        # 주요 주파수 대역 선택
        freq_bands = {}
        if np.max(freqs) > 0.5:  # 고주파 데이터
            freq_bands = {
                "저주파": [0, 0.1],
                "중저주파": [0.1, 0.3], 
                "중주파": [0.3, 0.6],
                "고주파": [0.6, np.max(freqs)]
            }
        else:  # 저주파 데이터
            freq_bands = {
                "초저주파": [0, 0.01],
                "저주파": [0.01, 0.05],
                "중주파": [0.05, 0.2],
                "고주파": [0.2, np.max(freqs)]
            }
        
        # 주파수 대역별 에너지 계산
        band_energy = {}
        for band_name, band_range in freq_bands.items():
            # 주파수 대역에 해당하는 인덱스 찾기
            band_indices = np.where((freqs >= band_range[0]) & (freqs <= band_range[1]))[0]
            
            if len(band_indices) > 0:
                # 해당 주파수 대역의 에너지 계산
                energy = np.sum(np.abs(coeffs[band_indices, :]))
                band_energy[band_name] = energy
        
        # 에너지 분포 시각화
        fig3 = px.pie(
            values=list(band_energy.values()),
            names=list(band_energy.keys()),
            title=f"{equipment_type} {sensor_type_display} 주파수 대역별 에너지 분포"
        )
        
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
        
        # 주파수 대역별 해석
        for band_name, energy in band_energy.items():
            with st.expander(f"{band_name} 대역 특성"):
                st.write(f"**에너지 비율**: {energy / sum(band_energy.values()):.2%}")
                
                if band_name in ["초저주파", "저주파"]:
                    st.write("- 장기적인 트렌드 또는 느린 변화 패턴과 관련이 있을 수 있습니다.")
                    st.write("- 계절적 변화, 일간/주간 주기성 등이 이 대역에서 감지됩니다.")
                elif band_name in ["중저주파", "중주파"]:
                    st.write("- 중간 주기성의 패턴과 관련이 있을 수 있습니다.")
                    st.write("- 시간/일간 단위의 장비 작동 사이클이 이 대역에서 나타날 수 있습니다.")
                elif band_name == "고주파":
                    st.write("- 빠른 변화와 순간적인 이벤트가 이 대역에서 감지됩니다.")
                    st.write("- 장비의 고주파 진동, 순간적인 이상 징후 등이 이 대역에 나타날 수 있습니다.")
        
        # AI 분석 부분 호출
        render_ai_analysis(
            df=df,
            equipment_type=equipment_type,
            sensor_type_display=sensor_type_display,
            wavelet_type=wavelet_type,
            scales=scales,
            freq_bands=freq_bands,
            band_energy=band_energy,
            pattern_threshold=pattern_threshold
        )
        
    except Exception as e:
        st.error(f"시간-주파수 분석 중 오류가 발생했습니다: {str(e)}")
        st.exception(e)