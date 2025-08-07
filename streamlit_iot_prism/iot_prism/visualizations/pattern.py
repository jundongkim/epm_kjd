import streamlit as st
import pandas as pd
import plotly.express as px
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

# 일별/시간별 패턴 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, sensor_type_display, day_pattern, hour_pattern, weekend_avg, weekday_avg):
    """패턴 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 패턴 분석 전용 키 접두사 사용
    key_prefix = "pattern_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 요일별 최대/최소
    max_day_idx = day_pattern[sensor_type_display].idxmax()
    min_day_idx = day_pattern[sensor_type_display].idxmin()
    max_day = day_pattern.iloc[max_day_idx]['day_name']
    min_day = day_pattern.iloc[min_day_idx]['day_name']
    max_day_value = day_pattern.iloc[max_day_idx][sensor_type_display]
    min_day_value = day_pattern.iloc[min_day_idx][sensor_type_display]
    
    # 시간별 최대/최소
    max_hour_idx = hour_pattern[sensor_type_display].idxmax()
    min_hour_idx = hour_pattern[sensor_type_display].idxmin()
    max_hour = hour_pattern.iloc[max_hour_idx]['hour']
    min_hour = hour_pattern.iloc[min_hour_idx]['hour']
    max_hour_value = hour_pattern.iloc[max_hour_idx][sensor_type_display]
    min_hour_value = hour_pattern.iloc[min_hour_idx][sensor_type_display]
    
    # 현재 분석 설정을 세션 상태에 저장
    current_analysis_key = f"{key_prefix}_current_analysis"
    
    # 분석 설정이 변경되었는지 확인
    analysis_changed = False
    if current_analysis_key in st.session_state:
        current_analysis = st.session_state[current_analysis_key]
        if (current_analysis["max_day"] != max_day or 
            current_analysis["min_day"] != min_day or
            current_analysis["max_hour"] != max_hour or
            current_analysis["min_hour"] != min_hour or
            abs(current_analysis["weekend_avg"] - weekend_avg) > 0.01 or
            abs(current_analysis["weekday_avg"] - weekday_avg) > 0.01):
            analysis_changed = True
    else:
        # 최초 실행 시
        analysis_changed = True
    
    # 현재 분석 설정 업데이트
    st.session_state[current_analysis_key] = {
        "max_day": max_day,
        "min_day": min_day,
        "max_hour": max_hour,
        "min_hour": min_hour,
        "weekend_avg": weekend_avg,
        "weekday_avg": weekday_avg
    }
    
    # AI 분석 프롬프트 키
    pattern_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 분석 설정이 변경되었거나 프롬프트가 없으면 새로 생성
    if analysis_changed or pattern_prompt_key not in st.session_state:
        # 요일 패턴 분석 정보
        day_analysis = f"""
## 요일별 패턴 분석
- 평균 값이 가장 높은 요일: {max_day} ({max_day_value:.2f})
- 평균 값이 가장 낮은 요일: {min_day} ({min_day_value:.2f})
- 주말 평균 값: {weekend_avg:.2f}
- 평일 평균 값: {weekday_avg:.2f}
- {'주말' if weekend_avg > weekday_avg else '평일'} 평균이 {'평일' if weekend_avg > weekday_avg else '주말'}보다 {(abs(weekend_avg - weekday_avg) / min(weekend_avg, weekday_avg)) * 100:.1f}% 높음
"""

        # 시간별 패턴 분석 정보
        hour_analysis = f"""
## 시간별 패턴 분석
- 평균 값이 가장 높은 시간: {max_hour}시 ({max_hour_value:.2f})
- 평균 값이 가장 낮은 시간: {min_hour}시 ({min_hour_value:.2f})
"""

        # 월별 패턴
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month
        
        # 센서 컬럼 이름 가져오기
        sensor_col = get_sensor_type()
        if sensor_col not in df_copy.columns:
            sensor_col = "value"  # 기본값으로 fallback
            
        month_pattern = df_copy.groupby('month')[sensor_col].mean()
        
        peak_month = month_pattern.idxmax()
        low_month = month_pattern.idxmin()
        
        month_analysis = f"""
## 월별 패턴 분석
- 평균 값이 가장 높은 월: {peak_month}월 ({month_pattern[peak_month]:.2f})
- 평균 값이 가장 낮은 월: {low_month}월 ({month_pattern[low_month]:.2f})
"""

        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 요일별/시간별 패턴으로 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, 요일별(월-일)/시간별(0-23시)로 그룹화되어 있습니다.
이 패턴 분석은 시간과 요일에 따른 {sensor_type_display} 값의 변화를 보여줍니다.

주요 분석 포인트:
1. 요일별 패턴과 의미 (주중 vs 주말)
2. 시간별 패턴과 의미 (일중 변화)
3. 주말/평일 패턴 차이와 그 의미
4. 월별 패턴과 장기 주기성
5. 패턴에 기반한 장비 운영 최적화 방안
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 패턴 분석 결과입니다.

## 패턴 정보
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 시각화: 요일별/시간별 패턴

{day_analysis}

{hour_analysis}

{month_analysis}

## 분석 과제
위 패턴 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. 요일별 패턴의 전반적인 특성과 의미
   - 요일별 패턴에서 발견되는 뚜렷한 특징 설명
   - 주중 및 주말 패턴의 차이와 그 의미

2. 시간별 패턴의 전반적인 특성과 의미
   - 하루 중 {sensor_type_display} 값이 높아지는/낮아지는 시간대의 패턴 설명
   - 피크 시간과 최저 시간의 차이가 의미하는 바

3. 주말/평일 차이와 운영에 미치는 영향
   - 주말과 평일의 패턴 차이가 장비 운영에 주는 의미
   - 이러한 차이를 활용한 최적화 방안

4. 월별 패턴과 장기 주기성
   - 월별 패턴에서 발견되는 주기성의 분석
   - 계절적 요인이 {sensor_type_display} 값에 미치는 영향

5. 패턴 기반 장비 운영 최적화를 위한 실용적인 제안
   - 패턴에서 관찰된 규칙성에 기반한 운영 전략
   - 최적/비최적 운영 시간대와 요일에 대한 구체적인 권장사항

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요.
"""
        # 패턴 전용 프롬프트로 저장
        st.session_state[pattern_prompt_key] = analysis_prompt
        
        # 분석 설정이 변경되면 캐시도 초기화
        if analysis_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"분석 설정이 변경되어 캐시 초기화")
        
        # 디버깅용 로깅
        print(f"패턴 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
    else:
        # 캐시된 패턴 전용 프롬프트 사용
        analysis_prompt = st.session_state[pattern_prompt_key]
        print(f"캐시된 패턴 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 패턴 분석")

    # 세션 상태 키 정의 - 모두 패턴 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 패턴 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 패턴 분석 전용
    def on_pattern_analyze_click():
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
        print(f"패턴 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 패턴 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 패턴 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_pattern_analyze_click,
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
            print(f"패턴 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"패턴 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 패턴 데이터를 분석하고 있습니다..."):
                print(f"패턴 분석: generate_ai_response 함수 호출 전")
                print(f"프롬프트 첫 100자: {analysis_prompt[:100]}...")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"패턴 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 패턴 분석 실행' 버튼을 클릭하세요. 패턴 데이터의 경향과 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 패턴 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"패턴: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
            roles = [msg["role"] for msg in st.session_state[chat_history_key]]
            print(f"패턴: 대화 기록 역할 목록: {roles}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 패턴 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.")

# 일별/시간별 패턴 UI 랜더링
def render_pattern_ui(df):
    """일별/시간별 패턴 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    st.subheader("일별/시간별 패턴")
    
    # Get equipment type using the helper function
    equipment_type = get_equipment_type(df)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # Add day and hour columns
    df_copy = df.copy()
    df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    
    # Create two visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Day of week pattern
        day_pattern = df_copy.groupby('day_of_week')[sensor_col].mean().reset_index()
        day_names = ['월', '화', '수', '목', '금', '토', '일']
        day_pattern['day_name'] = day_pattern['day_of_week'].apply(lambda x: day_names[x])
        
        fig1 = px.bar(day_pattern, x='day_name', y=sensor_col,
                    title=f"요일별 평균 {sensor_type_display}",
                    labels={"day_name": "요일", sensor_col: f"평균 {sensor_type_display}"})
        
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
        

    with col2:
        # Hour pattern
        hour_pattern = df_copy.groupby('hour')[sensor_col].mean().reset_index()
        
        fig2 = px.line(hour_pattern, x='hour', y=sensor_col,
                     title=f"시간별 평균 {sensor_type_display}",
                     labels={"hour": "시간", sensor_col: f"평균 {sensor_type_display}"})
        
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # 추가 패턴 분석
    with st.expander("패턴 세부 분석"):
        # 주말/평일 패턴 비교
        df_copy['is_weekend'] = df_copy['day_of_week'].apply(lambda x: '주말' if x >= 5 else '평일')
        weekday_pattern = df_copy.groupby(['is_weekend', 'hour'])[sensor_col].mean().reset_index()
        
        fig3 = px.line(weekday_pattern, x='hour', y=sensor_col, color='is_weekend',
                     title=f"주말/평일 시간별 평균 {sensor_type_display}",
                     labels={"hour": "시간", sensor_col: f"평균 {sensor_type_display}", "is_weekend": "구분"})
        
        st.plotly_chart(fig3, use_container_width=True)
        
        # 월별 패턴
        df_copy['month'] = df_copy['timestamp'].dt.month
        month_pattern = df_copy.groupby('month')[sensor_col].mean().reset_index()
        
        fig4 = px.line(month_pattern, x='month', y=sensor_col, markers=True,
                     title=f"월별 평균 {sensor_type_display}",
                     labels={"month": "월", sensor_col: f"평균 {sensor_type_display}"})
        
        # X축 레이블 설정
        fig4.update_xaxes(tickvals=list(range(1, 13)), ticktext=[f"{i}월" for i in range(1, 13)])
        
        st.plotly_chart(fig4, use_container_width=True)
        
        # 패턴 요약
        st.subheader("패턴 요약")
        
        # 요일별 최대/최소
        max_day_idx = day_pattern[sensor_col].idxmax()
        min_day_idx = day_pattern[sensor_col].idxmin()
        
        st.write(f"- 평균 값이 가장 높은 요일: **{day_pattern.iloc[max_day_idx]['day_name']}** ({day_pattern.iloc[max_day_idx][sensor_col]:.2f})")
        st.write(f"- 평균 값이 가장 낮은 요일: **{day_pattern.iloc[min_day_idx]['day_name']}** ({day_pattern.iloc[min_day_idx][sensor_col]:.2f})")
        
        # 시간별 최대/최소
        max_hour_idx = hour_pattern[sensor_col].idxmax()
        min_hour_idx = hour_pattern[sensor_col].idxmin()
        
        st.write(f"- 평균 값이 가장 높은 시간: **{hour_pattern.iloc[max_hour_idx]['hour']}시** ({hour_pattern.iloc[max_hour_idx][sensor_col]:.2f})")
        st.write(f"- 평균 값이 가장 낮은 시간: **{hour_pattern.iloc[min_hour_idx]['hour']}시** ({hour_pattern.iloc[min_hour_idx][sensor_col]:.2f})")
        
        # 주말/평일 비교
        weekend_avg = df_copy[df_copy['is_weekend'] == '주말'][sensor_col].mean()
        weekday_avg = df_copy[df_copy['is_weekend'] == '평일'][sensor_col].mean()
        
        if weekend_avg > weekday_avg:
            st.write(f"- 주말 평균 값 ({weekend_avg:.2f})이 평일 평균 값 ({weekday_avg:.2f})보다 {((weekend_avg/weekday_avg)-1)*100:.1f}% 높습니다.")
        else:
            st.write(f"- 평일 평균 값 ({weekday_avg:.2f})이 주말 평균 값 ({weekend_avg:.2f})보다 {((weekday_avg/weekend_avg)-1)*100:.1f}% 높습니다.")
    
    # AI 분석 부분 호출
    render_ai_analysis(
        df=df,
        equipment_type=equipment_type,
        sensor_type_display=sensor_type_display,  # 센서 타입 정보 전달
        day_pattern=day_pattern,
        hour_pattern=hour_pattern,
        weekend_avg=weekend_avg,
        weekday_avg=weekday_avg
    ) 