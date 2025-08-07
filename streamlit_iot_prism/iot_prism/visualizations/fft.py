import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import signal
from ..utils import calculate_fft, get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

# 주파수 분석 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, sensor_type_display, sample_rate, window_type, peak_threshold, peak_freqs=None, peak_amps=None, period_labels=None):
    """주파수 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 주파수 분석 전용 키 접두사 사용
    key_prefix = "fft_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 분석 설정을 세션 상태에 저장
    current_analysis_key = f"{key_prefix}_current_analysis"
    
    # 분석 설정이 변경되었는지 확인
    analysis_changed = False
    if current_analysis_key in st.session_state:
        current_analysis = st.session_state[current_analysis_key]
        if (current_analysis["sample_rate"] != sample_rate or 
            current_analysis["window_type"] != window_type or
            current_analysis["peak_threshold"] != peak_threshold):
            analysis_changed = True
    else:
        # 최초 실행 시
        analysis_changed = True
    
    # 현재 분석 설정 업데이트
    st.session_state[current_analysis_key] = {
        "sample_rate": sample_rate,
        "window_type": window_type,
        "peak_threshold": peak_threshold
    }
    
    # AI 분석 프롬프트 키
    fft_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 분석 설정이 변경되었거나 프롬프트가 없으면 새로 생성
    if analysis_changed or fft_prompt_key not in st.session_state:
        # FFT 분석 설정 정보
        fft_settings = f"""
## FFT 분석 설정
- 샘플링 빈도: {sample_rate} Hz (초당)
- 윈도우 함수: {window_type}
- 피크 임계값: {peak_threshold}
"""
        
        # 주파수 피크 정보
        if peak_freqs is not None and period_labels is not None and len(peak_freqs) > 0:
            # 피크 해석을 위한 데이터 준비
            peak_info = []
            for i, (freq, period, amp) in enumerate(zip(peak_freqs, period_labels, peak_amps)):
                if i >= 10:  # 상위 10개만 포함
                    break
                amp_ratio = amp / max(peak_amps) * 100
                peak_info.append({
                    "주파수": f"{freq:.6f} Hz",
                    "주기": period,
                    "진폭 비율": f"{amp_ratio:.2f}%"
                })
            
            # 피크 정보 문자열 생성
            peaks_str = ""
            for i, info in enumerate(peak_info):
                peaks_str += f"{i+1}. **{info['주기']}** 주기 (주파수: {info['주파수']}, 진폭: {info['진폭 비율']})\n"
            
            frequency_analysis = f"""
## 주요 주파수 피크 분석
검출된 주요 주파수 피크:

{peaks_str}
"""
        else:
            frequency_analysis = "## 주요 주파수 피크 분석\n주요 피크가 검출되지 않았습니다."
        
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 주파수 분석(FFT) 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, 고속 푸리에 변환(FFT)을 통해 주기적 패턴을 분석했습니다.
이 분석은 시계열 데이터에서 주요 주기성을 찾아내어 장비의 동작 패턴을 이해하는 데 도움을 줍니다.

주요 분석 포인트:
1. 주요 주파수 피크의 의미와 해석
2. 다양한 주기 패턴의 비즈니스적/운영적 의미
3. 일간/주간/월간/계절 패턴의 존재 여부와 강도
4. 특이한 주파수 패턴의 장비 성능 관련성
5. 주파수 분석 결과에 기반한 운영 최적화 방안
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 주파수 분석(FFT) 결과입니다.

## 분석 정보
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 분석 방법: 고속 푸리에 변환(FFT)

{fft_settings}

{frequency_analysis}

## 분석 과제
위 주파수 분석 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. 주요 {sensor_type_display} 주파수 피크의 의미와 해석
   - 가장 강한 주기 패턴의 의미와 장비 운영과의 연관성
   - 다양한 주기 패턴이 나타내는 장비 사용/작동 방식

2. {sensor_type_display} 시간 단위별 패턴 분석
   - 발견된 일일(24시간)/주간(7일)/월간/계절성 패턴의 존재 여부와 의미
   - 이러한 시간 패턴이 장비 운영에 주는 시사점

3. {sensor_type_display} 주파수 분석이 드러내는 장비 운영 특성
   - 주기 패턴에서 유추할 수 있는 장비 사용 방식
   - 특정 주기에 나타나는 패턴과 장비 성능의 연관성

4. {sensor_type_display} 비즈니스 및 운영 관점의 인사이트
   - 주기 패턴이 비즈니스 운영에 주는 의미
   - 생산성, 효율성, 에너지 사용과의 연관성

5. {sensor_type_display} 데이터 기반 운영 개선 제안
   - 주기 패턴을 고려한 장비 운영 최적화 방안
   - 특정 주기에 기반한 예방적 유지보수 전략

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요.
"""
        # 주파수 분석 전용 프롬프트로 저장
        st.session_state[fft_prompt_key] = analysis_prompt
        
        # 분석 설정이 변경되면 캐시도 초기화
        if analysis_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"주파수 분석 설정이 변경되어 캐시 초기화")
        
        # 디버깅용 로깅
        print(f"주파수 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
    else:
        # 캐시된 주파수 분석 전용 프롬프트 사용
        analysis_prompt = st.session_state[fft_prompt_key]
        print(f"캐시된 주파수 분석 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 주파수 분석")

    # 세션 상태 키 정의 - 모두 주파수 분석 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 주파수 분석 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 주파수 분석 전용
    def on_fft_analyze_click():
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
        print(f"주파수 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 주파수 분석 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 주파수 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_fft_analyze_click,
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
            print(f"주파수 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"주파수 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 주파수 데이터를 분석하고 있습니다..."):
                print(f"주파수 분석: generate_ai_response 함수 호출 전")
                print(f"프롬프트 첫 100자: {analysis_prompt[:100]}...")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"주파수 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 주파수 분석 실행' 버튼을 클릭하세요. 주파수 데이터의 패턴과 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 주파수 분석 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"주파수: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
            roles = [msg["role"] for msg in st.session_state[chat_history_key]]
            print(f"주파수: 대화 기록 역할 목록: {roles}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 주파수 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 

# 주파수 분석 UI 랜더링
def render_fft_ui(df):
    """주파수 분석 (FFT) UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # 세션 상태 초기화 (AI 분석용) - 먼저 AI 설정 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    st.subheader("주파수 분석 (Fast Fourier Transform)")
    
    # Get equipment type using the helper function
    equipment_type = get_equipment_type(df)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 분석 옵션 설정
    fft_options = st.columns([1, 2])
    with fft_options[0]:
        # 샘플링 빈도 (기본값: 시간당 1회)
        sample_rate = st.number_input("샘플링 빈도 (초당)", min_value=0.001, max_value=1000.0, value=1.0, step=0.1)
        window_type = st.selectbox("윈도우 함수", ["없음", "해밍(Hamming)", "한닝(Hanning)", "블랙맨(Blackman)"])
        show_peaks = st.checkbox("주요 피크 표시", value=True)
        peak_threshold = st.slider("피크 임계값", 0.1, 1.0, 0.3, 0.05)
    
    with fft_options[1]:
        st.write("주파수 분석은 신호의 주기적 패턴을 확인하는데 유용합니다.")
        st.write("높은 진폭을 가진 주파수는 데이터에서 강한 주기적 패턴을 나타냅니다.")
        st.write("예를 들어, 일일 주기는 1/86400 Hz (하루 = 86400초)에서 피크로 나타납니다.")
        
        # 시계열 리샘플링
        timestamp_diff = np.diff(df['timestamp'].astype(np.int64) // 10**9)
        actual_sample_rate = 1 / np.mean(timestamp_diff)
        st.write(f"실제 평균 샘플링 빈도: {actual_sample_rate:.6f} Hz (초당)")
    
    # AI 분석에 필요한 변수 초기화
    peak_freqs = None
    peak_amps = None
    period_labels = None
    
    try:
        # 데이터 준비
        y = df[sensor_col].values
        
        # 트렌드 제거 (선형 트렌드 제거)
        detrended = signal.detrend(y)
        
        # 윈도우 함수 적용
        if window_type == "해밍(Hamming)":
            window = signal.windows.hamming(len(detrended))
        elif window_type == "한닝(Hanning)":
            window = signal.windows.hann(len(detrended))
        elif window_type == "블랙맨(Blackman)":
            window = signal.windows.blackman(len(detrended))
        else:
            window = np.ones(len(detrended))
            
        windowed = detrended * window
        
        # FFT 계산
        fft_values = np.abs(np.fft.rfft(windowed))
        fft_freq = np.fft.rfftfreq(len(windowed), d=1/sample_rate)
        
        # 노이즈 제거를 위해 낮은 진폭 값 필터링
        threshold = np.max(fft_values) * 0.01
        fft_values[fft_values < threshold] = 0
        
        # 결과 시각화
        fft_df = pd.DataFrame({'frequency': fft_freq, 'amplitude': fft_values})
        
        # 너무 많은 주파수 포인트가 있을 경우 데이터 필터링
        if len(fft_df) > 10000:
            fft_df = fft_df.iloc[::len(fft_df)//10000].copy()
        
        # 기본 FFT 차트
        fig = px.line(fft_df, x='frequency', y='amplitude',
                    labels={'frequency': '주파수 (Hz)', 'amplitude': '진폭'},
                    title=f'{equipment_type} {sensor_type_display} 주파수 영역 분석 (FFT)')
        
        # 주요 피크 표시
        if show_peaks:
            peaks, _ = signal.find_peaks(fft_values, height=np.max(fft_values) * peak_threshold)
            peak_freqs = fft_freq[peaks]
            peak_amps = fft_values[peaks]
            period_labels = []
            
            # 피크 데이터 제한 (상위 10개만)
            if len(peaks) > 10:
                sorted_idx = np.argsort(peak_amps)[::-1][:10]
                peak_freqs = peak_freqs[sorted_idx]
                peak_amps = peak_amps[sorted_idx]
            
            # 피크 추가
            fig.add_scatter(x=peak_freqs, y=peak_amps, mode='markers',
                          name='주요 피크',
                          marker=dict(size=10, color='red', symbol='x'))
            
            # 주기로 변환하여 표시
            for freq in peak_freqs:
                if freq == 0:
                    period_labels.append("∞")
                    continue
                    
                period = 1 / freq
                # 시간 단위 변환
                if period < 60:
                    period_labels.append(f"{period:.1f}초")
                elif period < 3600:
                    period_labels.append(f"{period/60:.1f}분")
                elif period < 86400:
                    period_labels.append(f"{period/3600:.1f}시간")
                elif period < 604800:
                    period_labels.append(f"{period/86400:.1f}일")
                elif period < 2592000:
                    period_labels.append(f"{period/604800:.1f}주")
                elif period < 31536000:
                    period_labels.append(f"{period/2592000:.1f}개월")
                else:
                    period_labels.append(f"{period/31536000:.1f}년")
        
        fig.update_xaxes(type='log')  # 로그 스케일 적용
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # 피크 정보 표시
        if show_peaks and len(peak_freqs) > 0:
            st.subheader("주요 주파수 피크")
            
            peak_data = pd.DataFrame({
                '주파수 (Hz)': peak_freqs,
                '주기': period_labels,
                '진폭': peak_amps,
                '진폭 비율 (%)': peak_amps / np.max(fft_values) * 100
            })
            
            st.dataframe(peak_data)
            
            # 주요 피크 해석
            st.write(f"#### 주요 {sensor_type_display} 주기 패턴 해석")
            
            for i, (freq, period) in enumerate(zip(peak_freqs, period_labels)):
                if i >= 3:  # 상위 3개만 해석
                    break
                    
                st.write(f"**{period}** 주기: ")
                
                # 주기 해석
                if "초" in period or "분" in period:
                    st.write("- 장비의 짧은 주기 작동 패턴일 수 있습니다")
                elif "시간" in period:
                    if float(period.split("시간")[0]) >= 8 and float(period.split("시간")[0]) <= 12:
                        st.write("- 근무 교대 또는 작업 일정과 관련된 패턴일 수 있습니다")
                    else:
                        st.write("- 장비의 시간 단위 작동 주기일 수 있습니다")
                elif "일" in period:
                    if float(period.split("일")[0]) >= 0.9 and float(period.split("일")[0]) <= 1.1:
                        st.write("- 일일(24시간) 주기를 갖는 패턴입니다")
                    elif float(period.split("일")[0]) >= 6.5 and float(period.split("일")[0]) <= 7.5:
                        st.write("- 주간(7일) 주기를 갖는 패턴입니다")
                    else:
                        st.write("- 며칠 단위의 패턴이 있습니다")
                elif "주" in period:
                    st.write("- 주 단위 패턴이 있습니다")
                elif "개월" in period:
                    if float(period.split("개월")[0]) >= 0.9 and float(period.split("개월")[0]) <= 1.1:
                        st.write("- 월간 주기성을 갖는 패턴입니다")
                    elif float(period.split("개월")[0]) >= 2.9 and float(period.split("개월")[0]) <= 3.1:
                        st.write("- 분기별 주기성을 갖는 패턴입니다")
                    elif float(period.split("개월")[0]) >= 5.9 and float(period.split("개월")[0]) <= 6.1:
                        st.write("- 반년 주기성을 갖는 패턴입니다")
                    else:
                        st.write("- 월 단위 주기성을 갖는 패턴입니다")
                elif "년" in period:
                    st.write("- 연간 주기성을 갖는 패턴입니다")
        
        # 추가 옵션: 스펙트로그램 (시간에 따른 주파수 변화)
        if st.checkbox("스펙트로그램 표시 (시간에 따른 주파수 변화)"):
            
            # 시간 축 생성
            x = np.arange(len(y))
            
            # 스펙트로그램 계산
            f, t, Sxx = signal.spectrogram(y, fs=sample_rate)
            
            # 시간 스케일 조정 (실제 타임스탬프와 일치시키기)
            time_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
            t_scaled = np.linspace(0, time_range, len(t))
            
            # 2D 히트맵으로 표시
            fig = go.Figure(data=go.Heatmap(
                z=10 * np.log10(Sxx),  # 로그 스케일 변환
                x=t_scaled,
                y=f,
                colorscale='Viridis',
                zmin=np.min(10 * np.log10(Sxx)),
                zmax=np.max(10 * np.log10(Sxx))
            ))
            
            fig.update_layout(
                title=f'{equipment_type} {sensor_type_display} 스펙트로그램 (시간에 따른 주파수 분포)',
                xaxis_title='시간 (초)',
                yaxis_title='주파수 (Hz)',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # AI 분석 부분 호출 - 모든 시각화 완료 후 마지막에 한 번만 호출
        render_ai_analysis(
            df=df,
            equipment_type=equipment_type,
            sensor_type_display=sensor_type_display,
            sample_rate=sample_rate,
            window_type=window_type,
            peak_threshold=peak_threshold,
            peak_freqs=peak_freqs if peak_freqs is not None and len(peak_freqs) > 0 else None,
            peak_amps=peak_amps if peak_amps is not None and len(peak_amps) > 0 else None,
            period_labels=period_labels if period_labels is not None and len(period_labels) > 0 else None
        )
    except Exception as e:
        st.error(f"FFT 분석 중 오류가 발생했습니다: {str(e)}")