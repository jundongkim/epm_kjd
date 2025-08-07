import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils import get_sensor_type
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

def render_threed_ui(df_processed):
    """3D 데이터 시각화 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    st.subheader("3D 데이터 시각화")
    
    # Get equipment type
    equipment_type = get_equipment_type(df_processed)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df_processed.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 3D 시각화 설정
    viz_3d_options = st.columns([1, 1])
    
    with viz_3d_options[0]:
        plot_type = st.selectbox(
            "3D 플롯 유형",
            ["3D 산점도", "3D 표면도", "3D 선 그래프"]
        )
    
    with viz_3d_options[1]:
        time_unit = st.selectbox(
            "시간 단위",
            ["월별", "일별", "시간별"]
        )
    
    # 데이터 준비
    df_3d = df_processed.copy()
    
    if time_unit == "월별":
        df_3d['time_x'] = df_3d['timestamp'].dt.month
        df_3d['time_y'] = df_3d['timestamp'].dt.day
        x_title = "월"
        y_title = "일"
    elif time_unit == "일별":
        df_3d['time_x'] = df_3d['timestamp'].dt.day
        df_3d['time_y'] = df_3d['timestamp'].dt.hour
        x_title = "일"
        y_title = "시간"
    else:  # "시간별"
        df_3d['time_x'] = df_3d['timestamp'].dt.hour
        df_3d['time_y'] = df_3d['timestamp'].dt.minute
        x_title = "시간"
        y_title = "분"
    
    # 3D 시각화
    if plot_type == "3D 산점도":
        # 데이터 샘플링 (최대 10,000개 포인트)
        if len(df_3d) > 10000:
            df_sample = df_3d.sample(10000)
        else:
            df_sample = df_3d
        
        fig = px.scatter_3d(
            df_sample, 
            x='time_x',
            y='time_y',
            z=sensor_col,
            color=sensor_col,
            title=f"3D 산점도 ({time_unit})",
            labels={'time_x': x_title, 'time_y': y_title, sensor_col: f'{sensor_type_display} 값'}
        )
        
    elif plot_type == "3D 표면도":
        # 피벗 테이블 생성
        pivot_df = df_3d.pivot_table(
            values=sensor_col,
            index='time_y',
            columns='time_x',
            aggfunc='mean'
        )
        
        # NaN 값 처리
        pivot_df = pivot_df.fillna(method='ffill').fillna(method='bfill')
        
        # 표면도 생성
        fig = go.Figure(data=[go.Surface(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index
        )])
        
        fig.update_layout(
            title=f"3D 표면도 ({time_unit})",
            scene=dict(
                xaxis_title=x_title,
                yaxis_title=y_title,
                zaxis_title=f'{sensor_type_display} 값'
            )
        )
        
    else:  # "3D 선 그래프"
        # 시간별 평균 계산
        df_line = df_3d.groupby(['time_x', 'time_y'])[sensor_col].mean().reset_index()
        
        # 선택된 시간 단위에 맞게 정렬
        df_line = df_line.sort_values(['time_x', 'time_y'])
        
        # 3D 선 그래프 생성
        fig = go.Figure()
        
        for x_val in df_line['time_x'].unique():
            df_sub = df_line[df_line['time_x'] == x_val]
            
            fig.add_trace(go.Scatter3d(
                x=[x_val] * len(df_sub),
                y=df_sub['time_y'],
                z=df_sub[sensor_col],
                mode='lines',
                name=f"{x_title} {x_val}"
            ))
        
        fig.update_layout(
            title=f"3D 선 그래프 ({time_unit})",
            scene=dict(
                xaxis_title=x_title,
                yaxis_title=y_title,
                zaxis_title=f'{sensor_type_display} 값'
            )
        )
    
    fig.update_layout(height=700)
    st.plotly_chart(fig, use_container_width=True)
    
    # 3D 시각화 인사이트
    with st.expander("3D 시각화 분석"):
        st.write("#### 3D 시각화 분석")
        
        # 시간 차원별 최대/최소값
        max_by_x = df_3d.groupby('time_x')[sensor_col].max()
        min_by_x = df_3d.groupby('time_x')[sensor_col].min()
        
        st.write(f"**{x_title}별 최대값:**")
        max_x_fig = px.bar(
            x=max_by_x.index,
            y=max_by_x.values,
            labels={'x': x_title, 'y': f'최대 {sensor_type_display} 값'}
        )
        st.plotly_chart(max_x_fig, use_container_width=True)
        
        st.write(f"**{y_title}별 변동성:**")
        std_by_y = df_3d.groupby('time_y')[sensor_col].std()
        
        std_y_fig = px.bar(
            x=std_by_y.index,
            y=std_by_y.values,
            labels={'x': y_title, 'y': f'{sensor_type_display} 값 표준편차'}
        )
        st.plotly_chart(std_y_fig, use_container_width=True)
    
    # AI 분석 부분 호출
    render_ai_analysis(
        df=df_processed,
        equipment_type=equipment_type,
        plot_type=plot_type,
        time_unit=time_unit,
        x_title=x_title,
        y_title=y_title,
        sensor_type_display=sensor_type_display,
        max_by_x=max_by_x,
        std_by_y=std_by_y
    )

def get_equipment_type(df=None):
    """데이터프레임, 세션 상태 또는 파일 이름에서 equipment_type 값을 가져옵니다."""
    # 세션 상태에서 확인
    if 'equipment_type' in st.session_state:
        return st.session_state.equipment_type
    
    # 현재 사용 중인 데이터에서 파일 이름 확인
    if 'current_filename' in st.session_state and st.session_state.current_filename:
        filename = st.session_state.current_filename
        # iot_장비유형_날짜.csv 형식에서 장비 유형 추출
        try:
            import os
            parts = os.path.basename(filename).split('_')
            if len(parts) >= 2 and parts[0] == 'iot':
                return parts[1]
        except:
            pass
    
    # 기본값 반환
    return "장비" 

def render_ai_analysis(df, equipment_type, plot_type, time_unit, x_title, y_title, sensor_type_display, max_by_x=None, std_by_y=None):
    """3D 시각화를 위한 AI 분석 기능을 구현합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 3D 분석 전용 키 접두사 사용
    key_prefix = "threed_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 3D 플롯 유형을 세션 상태에 저장
    current_plot_key = f"{key_prefix}_current_plot"
    current_time_key = f"{key_prefix}_current_time"
    
    # 플롯 유형이나 시간 단위가 변경되었는지 확인
    config_changed = False
    if current_plot_key in st.session_state and current_time_key in st.session_state:
        if (st.session_state[current_plot_key] != plot_type or 
            st.session_state[current_time_key] != time_unit):
            config_changed = True
    else:
        # 최초 실행 시
        config_changed = True
    
    # 현재 설정 업데이트
    st.session_state[current_plot_key] = plot_type
    st.session_state[current_time_key] = time_unit
    
    # AI 분석 프롬프트 키
    threed_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 설정이 변경되었거나 프롬프트가 없으면 새로 생성
    if config_changed or threed_prompt_key not in st.session_state:
        # 플롯 유형에 대한 설명 추가
        method_description = ""
        method_context = ""
        
        if plot_type == "3D 산점도":
            method_description = "3D 산점도는 3차원 공간에서 데이터 포인트들을 표시하는 시각화 방법입니다. x축, y축은 시간 차원을, z축은 센서 값을 나타냅니다."
            method_context = "3D 산점도는 시간의 두 차원(예: 월과 일, 일과 시간 등)에 따른 센서 값의 분포를 한눈에 파악하는 데 유용합니다. 패턴, 군집, 이상치 등을 파악할 수 있습니다."
        elif plot_type == "3D 표면도":
            method_description = "3D 표면도는 3차원 공간에서 연속적인 표면으로 데이터를 표현하는 방법입니다. x축, y축은 시간 차원을, z축 높이는 센서 값을 나타냅니다."
            method_context = "3D 표면도는 시간의 두 차원에 따른 센서 값의 변화 추세를 표면으로 시각화합니다. 특정 시간 조합에서의 값 변화 패턴, 피크, 계곡 등을 파악하는 데 효과적입니다."
        else:  # "3D 선 그래프"
            method_description = "3D 선 그래프는 3차원 공간에서 선으로 데이터 추세를 연결하는 방법입니다. 첫 번째 시간 차원별로 다른 선들이 그려지며, 각 선은 두 번째 시간 차원에 따른 값 변화를 보여줍니다."
            method_context = "3D 선 그래프는 첫 번째 시간 차원(예: 월)별로 다른 선을 표시하고, 각 선이 두 번째 시간 차원(예: 일)에 따른 센서 값의 변화를 보여줍니다. 시간 차원 간의 센서 값 패턴 차이를 비교하는 데 유용합니다."
            
        # 시간 단위에 대한 설명 추가
        time_description = ""
        if time_unit == "월별":
            time_description = "월별 데이터는 월과 일을 기준으로 센서 값을 시각화합니다. 월간 패턴과 월 내 일별 패턴을 동시에 파악할 수 있습니다."
        elif time_unit == "일별":
            time_description = "일별 데이터는 일과 시간을 기준으로 센서 값을 시각화합니다. 일간 패턴과 일 내 시간별 패턴을 동시에 파악할 수 있습니다."
        else:  # "시간별"
            time_description = "시간별 데이터는 시간과 분을 기준으로 센서 값을 시각화합니다. 시간별 패턴과 시간 내 분 단위 패턴을 동시에 파악할 수 있습니다."
            
        # 3D 시각화 통계 요약 추가
        stats_summary = f"""
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 3D 플롯 유형: {plot_type} ({method_description})
- 시간 단위: {time_unit} ({time_description})
- 첫 번째 시간 차원(x축): {x_title}
- 두 번째 시간 차원(y축): {y_title}
- 측정값(z축): {sensor_type_display}
"""
        
        # x 차원 최대값 정보 추가
        if max_by_x is not None and not max_by_x.empty:
            stats_summary += f"\n{x_title} 차원별 {sensor_type_display} 최대값:\n"
            for idx, value in max_by_x.items():
                stats_summary += f"* {x_title} {idx}: {value:.4f}\n"
            
            # 최대값이 나타난 x 값
            max_x = max_by_x.idxmax()
            max_val = max_by_x.max()
            stats_summary += f"\n최대 {sensor_type_display} 값이 나타난 {x_title}: {max_x} (값: {max_val:.4f})\n"
            
        # y 차원 표준편차 정보 추가
        if std_by_y is not None and not std_by_y.empty:
            stats_summary += f"\n{y_title} 차원별 {sensor_type_display} 표준편차:\n"
            
            # 상위 3개 표준편차 값
            top_stds = std_by_y.nlargest(3)
            for idx, value in top_stds.items():
                stats_summary += f"* {y_title} {idx}: {value:.4f}\n"
                
            # 평균적인 표준편차
            avg_std = std_by_y.mean()
            stats_summary += f"\n{y_title} 차원별 평균 표준편차: {avg_std:.4f}\n"
        
        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 3D 시각화를 통해 시간에 따른 패턴과 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, {plot_type} 방법으로 {time_unit} 기준 3D 시각화되었습니다.
이 분석은 {method_description}

분석 컨텍스트: {method_context}
시간 컨텍스트: {time_description}

주요 분석 포인트:
1. 3D 시각화에서 발견되는 주요 패턴과 트렌드
2. 첫 번째 시간 차원({x_title})에 따른 센서 값 변화 특성
3. 두 번째 시간 차원({y_title})에 따른 센서 값 변화 특성
4. 두 시간 차원 간의 상호작용과 그 의미
5. 장비 운영 최적화를 위한 실용적인 인사이트
"""
        
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 {time_unit} 기반 3D 시각화 분석 결과입니다.

## 데이터 정보
{stats_summary}

## 분석 과제
위 3D 시각화 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. 3D 시각화에서 발견되는 주요 패턴
   - 전반적인 분포 형태와 특징
   - 특이점 또는 집중 분포 영역 식별
   - 3차원 공간에서 발견되는 주요 트렌드

2. {x_title} 차원 분석
   - {x_title}에 따른 {sensor_type_display} 값의 변화 패턴
   - 가장 높은 값과 낮은 값이 나타나는 {x_title} 지점
   - {x_title} 차원의 주기성 또는 계절성 평가

3. {y_title} 차원 분석
   - {y_title}에 따른 {sensor_type_display} 값의 변화 패턴
   - {y_title} 차원에서의 변동성이 큰 구간과 작은 구간
   - {y_title} 차원의 주기적 패턴 식별

4. 두 시간 차원 간의 상호작용
   - 특정 {x_title}에서 {y_title}에 따른 값 변화의 특이성
   - 두 시간 차원이 결합하여 나타나는 복합적 패턴
   - 특정 시간 조합(특정 {x_title}와 {y_title})에서 나타나는 주목할 만한 현상

5. 장비 운영에 대한 실용적인 제안
   - 최적의 운영 시간대 조합 제안
   - 3D 시각화에서 나타난 패턴에 기반한 유지보수 일정 제안
   - 효율성 또는 성능 향상을 위한 시간 관련 권장사항

결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요. 특히 구체적인 수치와 시간대를 언급하여 인사이트에 신뢰성을 더해주세요.
"""
        # 3D 시각화 전용 프롬프트로 저장
        st.session_state[threed_prompt_key] = analysis_prompt
        
        # 설정이 변경되면 캐시도 초기화
        if config_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"3D 시각화 설정이: {plot_type}, {time_unit}으로 변경되어 캐시 초기화")
        
        # 디버깅용 로깅
        print(f"3D 시각화 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
        if config_changed:
            print(f"3D 시각화 설정 변경: {plot_type}, {time_unit}")
    else:
        # 캐시된 3D 시각화 전용 프롬프트 사용
        analysis_prompt = st.session_state[threed_prompt_key]
        print(f"캐시된 3D 시각화 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 3D 시각화 분석")

    # 세션 상태 키 정의 - 모두 3D 시각화 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 3D 시각화 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 3D 시각화 전용
    def on_threed_analyze_click():
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
        print(f"3D 시각화 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 3D 시각화 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 3D 시각화 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_threed_analyze_click,
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
            print(f"3D 시각화 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"3D 시각화 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 3D 시각화 데이터를 분석하고 있습니다..."):
                print(f"3D 시각화 분석: generate_ai_response 함수 호출 전")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"3D 시각화 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        st.info("AI 분석을 실행하려면 'AI 3D 시각화 분석 실행' 버튼을 클릭하세요. 3D 데이터에서 패턴과 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        st.subheader("🤖 3D 시각화 데이터에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"3D 시각화: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        st.info("AI 데이터 분석을 먼저 실행하여 3D 시각화 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 