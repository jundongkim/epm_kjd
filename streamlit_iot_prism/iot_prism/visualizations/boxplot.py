import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

# 박스플롯 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, primary_groupby, boxplot_type, split_by_weekday, x_col, x_title, summary_stats=None, f_stat=None, p_val=None):
    """박스플롯 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 박스플롯 분석 전용 키 접두사 사용
    key_prefix = "boxplot_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 그룹화 기준을 세션 상태에 저장
    current_groupby_key = f"{key_prefix}_current_groupby"
    
    # 그룹화 기준이 변경되었는지 확인
    groupby_changed = False
    if current_groupby_key in st.session_state:
        if st.session_state[current_groupby_key] != primary_groupby:
            groupby_changed = True
    else:
        # 최초 실행 시
        groupby_changed = True
    
    # 현재 그룹화 기준 업데이트
    st.session_state[current_groupby_key] = primary_groupby
    
    # AI 분석 프롬프트 키
    boxplot_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 그룹화 기준이 변경되었거나 프롬프트가 없으면 새로 생성
    if groupby_changed or boxplot_prompt_key not in st.session_state:
        # 그룹화 기준에 대한 설명 추가
        groupby_description = ""
        groupby_context = ""
        group_value_meanings = ""
        
        if primary_groupby == "월":
            groupby_description = "1월부터 12월까지 월별로 데이터를 분석합니다. 이는 계절적 패턴과 월별 변동성을 확인하는 데 유용합니다."
            groupby_context = "월별 분석에서는 계절적 요인, 월간 생산 목표, 정기 유지보수 일정 등이 센서 값에 영향을 줄 수 있습니다."
            group_value_meanings = "그룹 1은 1월, 2는 2월, ... 12는 12월을 의미합니다. 월별 그룹 간 비교는 계절적 패턴과 연간 주기성을 파악하는 데 중요합니다."
            
        elif primary_groupby == "요일":
            groupby_description = "월요일부터 일요일까지 요일별로 데이터를 분석합니다. 이는 주중/주말 패턴과 요일별 변동성을 확인하는 데 유용합니다."
            groupby_context = "요일별 분석에서는 주간 작업 패턴, 교대 근무, 주말 가동률 변화 등이 센서 값에 영향을 줄 수 있습니다."
            group_value_meanings = "그룹은 '월', '화', '수', '목', '금', '토', '일'로 표시됩니다. 주중(월-금)과 주말(토-일) 비교는 작업 패턴의 영향을 파악하는 데 중요합니다."
            
        elif primary_groupby == "시간대":
            groupby_description = "새벽(0-6시), 오전(6-12시), 오후(12-18시), 저녁(18-24시)으로 시간대별 데이터를 분석합니다. 이는 일중 패턴과 시간대별 변동성을 확인하는 데 유용합니다."
            groupby_context = "시간대별 분석에서는 일과 시간, 교대 근무, 피크 시간 운영, 야간 운영 등이 센서 값에 영향을 줄 수 있습니다."
            group_value_meanings = "그룹은 '새벽(0-6시)', '오전(6-12시)', '오후(12-18시)', '저녁(18-24시)'으로 구분됩니다. 각 시간대는 다른 운영 조건과 작업 환경을 반영합니다."
            
        elif primary_groupby == "분기":
            groupby_description = "1분기부터 4분기까지 분기별로 데이터를 분석합니다. 이는 분기별 패턴과 변동성을 확인하는 데 유용합니다."
            groupby_context = "분기별 분석에서는 계절적 요인, 분기별 생산 목표, 정기 유지보수 일정 등이 센서 값에 영향을 줄 수 있습니다."
            group_value_meanings = "그룹 1은 1분기(1-3월), 2는 2분기(4-6월), 3은 3분기(7-9월), 4는 4분기(10-12월)를 의미합니다. 분기별 비교는 계절 변화와 사업 주기의 영향을 파악하는 데 중요합니다."
            
        else:  # "없음"
            groupby_description = "그룹화 없이 전체 데이터를 단일 박스플롯으로 분석합니다."
            groupby_context = "전체 데이터 분석에서는 총체적인 성능 지표와 분포를 확인할 수 있습니다."
            group_value_meanings = "그룹화가 없으므로 단일 데이터 세트로 전체 성능을 평가합니다."
        
        # 박스플롯 데이터의 통계 및 특성 요약
        stats_summary = f"""
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 박스플롯 유형: {boxplot_type}
- 기본 그룹화 기준: {primary_groupby} ({groupby_description})
- 주말/평일 분리: {'예' if split_by_weekday else '아니오'}
- 데이터 포인트 수: {len(df):,}개
"""
        
        # 그룹별 통계 요약 추가
        if summary_stats is not None and x_col is not None:
            stats_summary += f"\n{sensor_type_display} 그룹별 통계 요약:\n"
            for _, row in summary_stats.iterrows():
                group_name = row[x_title]
                stats_summary += f"* {group_name}: 평균={row['평균']:.2f}, 중앙값={row['중앙값']:.2f}, 최소값={row['최소값']:.2f}, 최대값={row['최대값']:.2f}\n"
        
        # ANOVA 결과 추가
        if f_stat is not None and p_val is not None:
            stats_summary += f"\n{sensor_type_display} ANOVA 분석 결과:\n"
            stats_summary += f"* F 통계량: {f_stat:.4f}\n"
            stats_summary += f"* p-value: {p_val:.4e}\n"
            stats_summary += f"* 결론: 그룹 간 {'통계적으로 유의한 차이가 있습니다' if p_val < 0.05 else '통계적으로 유의한 차이가 없습니다'} (p {'<' if p_val < 0.05 else '>='} 0.05)"
            
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 박스플롯을 통해 시각화된 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {primary_groupby}별로 그룹화되어 있습니다. 
이 그룹화는 {groupby_description}

그룹화 컨텍스트: {groupby_context}
그룹 값의 의미: {group_value_meanings}

주요 분석 포인트:
1. {primary_groupby} 그룹 간 {sensor_type_display} 분포 차이와 통계적 유의성
2. {sensor_type_display} 이상치의 존재 여부 및 패턴
3. 그룹별 {sensor_type_display} 분포가 장비 성능에 주는 의미
4. 장비 운영 및 유지보수 관련 인사이트
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 박스플롯 분석 결과입니다.

## 데이터 정보
{stats_summary}

## 분석 과제
위 박스플롯 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {primary_groupby} 그룹 간 {sensor_type_display} 분포 차이의 전반적인 특성
   - 각 {primary_groupby} 그룹의 명확한 특성과 차이점 설명
   - 통계적 유의성이 있는 경우 어떤 그룹 간 차이가 두드러지는지 구체적으로 설명

2. {sensor_type_display} 이상치의 존재 여부 및 분포 패턴
   - 어떤 {primary_groupby} 그룹에서 이상치가 많이 발생하는지 명시
   - 이상치 패턴의 실제적 의미 해석

3. 각 그룹별 {sensor_type_display} 분포가 장비 성능에 주는 의미
   - {primary_groupby} 그룹별 특성이 장비 성능에 미치는 영향 분석
   - 어떤 {primary_groupby}에 장비가 가장 안정적/불안정적으로 작동하는지 설명

4. {primary_groupby}별 {sensor_type_display} 패턴과 그 의미
   - {primary_groupby} 특성에 따른 패턴 설명 (예: 월별이면 계절성, 요일별이면 주간 패턴 등)
   - 이러한 패턴이 비즈니스나 운영에 주는 의미

5. 장비 운영 또는 예방 정비에 대한 실용적인 제안
   - {primary_groupby} 특성을 고려한 구체적인 운영/정비 제안
   - 데이터에 기반한 최적 운영 시점 또는 조건 제시

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 각 분석 포인트에서 {primary_groupby} 그룹을 명확하게 언급하여 분석의 맥락을 유지해주세요.
"""
        # 박스플롯 전용 프롬프트로 저장
        st.session_state[boxplot_prompt_key] = analysis_prompt
        
        # 그룹화 기준이 변경되면 캐시도 초기화
        if groupby_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"그룹화 기준이 변경되어 캐시 초기화: {primary_groupby}")
        
        # 디버깅용 로깅
        print(f"박스플롯 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
        print(f"stats_summary: {stats_summary}")
        print(f"시스템 프롬프트: {system_prompt}")
        if groupby_changed:
            print(f"그룹화 기준 변경: {primary_groupby}")
    else:
        # 캐시된 박스플롯 전용 프롬프트 사용
        analysis_prompt = st.session_state[boxplot_prompt_key]
        print(f"캐시된 박스플롯 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 박스플롯 분석")

    # 세션 상태 키 정의 - 모두 박스플롯 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 박스플롯 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 박스플롯 분석 전용
    def on_boxplot_analyze_click():
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
        print(f"박스플롯 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 박스플롯 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 박스플롯 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_boxplot_analyze_click,
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
            print(f"박스플롯 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"박스플롯 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 박스플롯 데이터를 분석하고 있습니다..."):
                print(f"박스플롯 분석: generate_ai_response 함수 호출 전")
                print(f"프롬프트 첫 100자: {analysis_prompt[:100]}...")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"박스플롯 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 박스플롯 분석 실행' 버튼을 클릭하세요. 박스플롯 데이터의 분포와 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 박스플롯 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"박스플롯: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
            roles = [msg["role"] for msg in st.session_state[chat_history_key]]
            print(f"박스플롯: 대화 기록 역할 목록: {roles}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 박스플롯 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.")

# 박스플롯 UI 랜더링
def render_boxplot_ui(df):
    """박스플롯 UI를 렌더링합니다."""
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
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    st.subheader(f"{sensor_type_display} 분포 비교")
    
    groupby_options = st.columns(2)
    with groupby_options[0]:
        primary_groupby = st.selectbox(
            "기본 그룹화 기준",
            ["월", "요일", "시간대", "분기", "없음"]
        )
    
    with groupby_options[1]:
        boxplot_type = st.radio("박스플롯 유형", ["기본", "바이올린", "포인트 표시", "노치 표시"])
        split_by_weekday = st.checkbox("주말/평일 분리", value=False)
    
    # 그룹화 기준에 따라 데이터 준비
    df_copy = df.copy()
    df_copy['month'] = df_copy['timestamp'].dt.month
    df_copy['day_of_week'] = df_copy['timestamp'].dt.dayofweek
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    df_copy['quarter'] = df_copy['timestamp'].dt.quarter
    
    # 시간대 분류
    time_bins = [0, 6, 12, 18, 24]
    time_labels = ['새벽(0-6시)', '오전(6-12시)', '오후(12-18시)', '저녁(18-24시)']
    df_copy['time_of_day'] = pd.cut(df_copy['hour'], bins=time_bins, labels=time_labels, right=False)
    
    # 주말/평일 분류
    df_copy['is_weekend'] = df_copy['day_of_week'].apply(lambda x: '주말' if x >= 5 else '평일')
    
    # 요일 이름 추가
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    df_copy['day_name'] = df_copy['day_of_week'].apply(lambda x: day_names[x])
    
    # 그룹화 기준에 따라 x축 설정
    if primary_groupby == "월":
        x_col = 'month'
        x_title = "월"
        category_orders = {x_col: list(range(1, 13))}
        x_tickvals = list(range(1, 13))
        x_ticktext = [f"{i}월" for i in range(1, 13)]
        
    elif primary_groupby == "요일":
        x_col = 'day_name'
        x_title = "요일"
        category_orders = {x_col: day_names}
        x_tickvals = day_names
        x_ticktext = day_names
        
    elif primary_groupby == "시간대":
        x_col = 'time_of_day'
        x_title = "시간대"
        category_orders = {x_col: time_labels}
        x_tickvals = time_labels
        x_ticktext = time_labels
        
    elif primary_groupby == "분기":
        x_col = 'quarter'
        x_title = "분기"
        category_orders = {x_col: list(range(1, 5))}
        x_tickvals = list(range(1, 5))
        x_ticktext = [f"Q{i}" for i in range(1, 5)]
        
    else:  # "없음"
        x_col = None
        x_title = ""
        category_orders = None
        x_tickvals = None
        x_ticktext = None
    
    # 색상 분류 설정
    if split_by_weekday and x_col != 'day_name' and x_col is not None:
        color_col = 'is_weekend'
        color_title = "주말/평일"
    else:
        color_col = None
        color_title = None
    
    # 박스플롯 생성
    if boxplot_type == "기본":
        if x_col is not None:
            fig = px.box(df_copy, x=x_col, y=sensor_col, color=color_col,
                       category_orders=category_orders,
                       title=f"{equipment_type} {x_title}별 {sensor_type_display} 분포",
                       labels={sensor_col: f"{sensor_type_display}", x_col: x_title, color_col: color_title})
        else:
            fig = px.box(df_copy, y=sensor_col,
                       title=f"{equipment_type} {sensor_type_display} 분포",
                       labels={sensor_col: f"{sensor_type_display}"})
            
    elif boxplot_type == "바이올린":
        if x_col is not None:
            fig = px.violin(df_copy, x=x_col, y=sensor_col, color=color_col,
                          category_orders=category_orders,
                          box=True, points=False,
                          title=f"{equipment_type} {x_title}별 {sensor_type_display} 분포 (바이올린)",
                          labels={sensor_col: f"{sensor_type_display}", x_col: x_title, color_col: color_title})
        else:
            fig = px.violin(df_copy, y=sensor_col,
                          box=True, points=False,
                          title=f"{equipment_type} {sensor_type_display} 분포 (바이올린)",
                          labels={sensor_col: f"{sensor_type_display}"})
            
    elif boxplot_type == "포인트 표시":
        # 데이터 샘플링 (포인트가 너무 많으면 과부하 발생)
        if len(df_copy) > 5000:
            if x_col is not None:
                # 그룹별로 균등하게 샘플링
                grouped = df_copy.groupby(x_col)
                sampled_groups = []
                for name, group in grouped:
                    sampled_groups.append(group.sample(min(1000 // grouped.ngroups, len(group))))
                df_sample = pd.concat(sampled_groups)
            else:
                df_sample = df_copy.sample(5000)
        else:
            df_sample = df_copy
        
        if x_col is not None:
            fig = px.box(df_sample, x=x_col, y=sensor_col, color=color_col,
                      category_orders=category_orders,
                      points="all",
                      title=f"{equipment_type} {x_title}별 {sensor_type_display} 분포 (포인트 표시)",
                      labels={sensor_col: f"{sensor_type_display}", x_col: x_title, color_col: color_title})
        else:
            fig = px.box(df_sample, y=sensor_col,
                      points="all",
                      title=f"{equipment_type} {sensor_type_display} 분포 (포인트 표시)",
                      labels={sensor_col: f"{sensor_type_display}"})
    
    elif boxplot_type == "노치 표시":
        if x_col is not None:
            fig = px.box(df_copy, x=x_col, y=sensor_col, color=color_col,
                      category_orders=category_orders,
                      notched=True,
                      title=f"{equipment_type} {x_title}별 {sensor_type_display} 분포 (노치 표시)",
                      labels={sensor_col: f"{sensor_type_display}", x_col: x_title, color_col: color_title})
        else:
            fig = px.box(df_copy, y=sensor_col,
                      notched=True,
                      title=f"{equipment_type} {sensor_type_display} 분포 (노치 표시)",
                      labels={sensor_col: f"{sensor_type_display}"})
    
    # x축 라벨 설정
    if x_tickvals is not None and x_ticktext is not None:
        fig.update_xaxes(tickvals=x_tickvals, ticktext=x_ticktext)
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # ANOVA 결과 저장 변수
    f_stat = None
    p_val = None
    summary_stats = None
    
    # 그룹별 통계 요약
    if x_col is not None:
        with st.expander(f"{x_title}별 {sensor_type_display} 통계 요약"):
            summary_stats = df_copy.groupby(x_col)[sensor_col].agg([
                'count', 'mean', 'std', 'min', 
                lambda x: x.quantile(0.25),
                'median',
                lambda x: x.quantile(0.75),
                'max'
            ]).reset_index()
            
            summary_stats.columns = [x_title, '개수', '평균', '표준편차', '최소값', '25%', '중앙값', '75%', '최대값']
            
            st.dataframe(summary_stats)
            
            # ANOVA 분석 (그룹 간 차이 검정)
            try:
                from scipy import stats
                
                # 일원 분산 분석
                groups = [group[sensor_col].values for name, group in df_copy.groupby(x_col)]
                
                # 빈 그룹이 있는지 확인하고 데이터가 있는 그룹만 사용
                valid_groups = [group for group in groups if len(group) > 0]
                
                if len(valid_groups) >= 2:  # 최소 2개 이상의 그룹이 필요
                    f_stat, p_val = stats.f_oneway(*valid_groups)
                    
                    st.write(f"#### {sensor_type_display} 그룹 간 차이 검정 (ANOVA)")
                    st.write(f"F 통계량: {f_stat:.4f}")
                    st.write(f"p-value: {p_val:.4e}")
                    
                    if p_val < 0.05:
                        st.write(f"결론: {sensor_type_display} 그룹 간 통계적으로 유의한 차이가 있습니다 (p < 0.05)")
                    else:
                        st.write(f"결론: {sensor_type_display} 그룹 간 통계적으로 유의한 차이가 없습니다 (p >= 0.05)")
                else:
                    st.warning("ANOVA 분석을 위한 유효한 그룹이 충분하지 않습니다.")
            except Exception as e:
                st.error(f"ANOVA 분석 중 오류가 발생했습니다: {str(e)}")
    
    # AI 분석 부분 호출 
    render_ai_analysis(
        df=df_copy,
        equipment_type=equipment_type,
        primary_groupby=primary_groupby, 
        boxplot_type=boxplot_type,
        split_by_weekday=split_by_weekday,
        x_col=x_col,
        x_title=x_title,
        summary_stats=summary_stats,
        f_stat=f_stat,
        p_val=p_val
    ) 