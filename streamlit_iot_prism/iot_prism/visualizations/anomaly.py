import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from ..utils import get_equipment_type, get_sensor_type
from ..utils.style import load_iot_font_css, apply_custom_style
from ..utils.ai_utils import init_session_state, display_analysis_ui, generate_ai_response, display_chat_interface
from ..utils.ai_settings import render_ai_settings_ui, init_ai_settings
import json

# Plotly 렌더러 설정 (이미지 다운로드 문제 해결)
pio.renderers.default = "browser"

# 이상치 분석 AI 분석 랜더링
def render_ai_analysis(df, equipment_type, sensor_type_display, threshold, anomalies, pos_count, neg_count, num_clusters, avg_cluster_size, max_cluster_size, single_anomalies_pct, hour_anomaly, day_anomaly, month_anomaly, largest_cluster_info=None, has_anomalies=True):
    """이상치 분석을 위한 AI 분석 부분을 별도 함수로 분리합니다."""
    # 세션 상태 초기화 (AI 분석용)
    from ..utils.ai_settings import init_ai_settings
    init_ai_settings()  # 먼저 AI 설정 초기화
    
    # 이상치 분석 전용 키 접두사 사용
    key_prefix = "anomaly_analysis"
    init_session_state(key_prefix=key_prefix)
    
    # 현재 분석 설정을 세션 상태에 저장
    current_analysis_key = f"{key_prefix}_current_analysis"
    
    # 분석 설정이 변경되었는지 확인
    analysis_changed = False
    if current_analysis_key in st.session_state:
        current_analysis = st.session_state[current_analysis_key]
        if (current_analysis["threshold"] != threshold or 
            current_analysis["anomaly_count"] != len(anomalies) or
            current_analysis["pos_count"] != pos_count or
            current_analysis["neg_count"] != neg_count or
            current_analysis["num_clusters"] != num_clusters):
            analysis_changed = True
    else:
        # 최초 실행 시
        analysis_changed = True
    
    # 현재 분석 설정 업데이트
    st.session_state[current_analysis_key] = {
        "threshold": threshold,
        "anomaly_count": len(anomalies),
        "pos_count": pos_count,
        "neg_count": neg_count,
        "num_clusters": num_clusters
    }
    
    # AI 분석 프롬프트 키
    anomaly_prompt_key = f"{key_prefix}_specific_prompt"
    
    # 분석 설정이 변경되었거나 프롬프트가 없으면 새로 생성
    if analysis_changed or anomaly_prompt_key not in st.session_state:
        # 이상치 통계 정보
        if has_anomalies:
            anomaly_stats = f"""
## 이상치 통계 정보
- 사용된 임계값: Z-score > {threshold}
- 감지된 이상치 수: {len(anomalies):,}개 ({len(anomalies)/len(df)*100:.2f}%)
- 상단 이상치 (높은 값): {pos_count}개 ({pos_count/(pos_count+neg_count)*100:.1f}%)
- 하단 이상치 (낮은 값): {neg_count}개 ({neg_count/(pos_count+neg_count)*100:.1f}%)
"""

            # 군집 분석 정보
            cluster_analysis = f"""
## 이상치 군집 분석
- 이상치 군집 수: {num_clusters}개
- 평균 군집 크기: {avg_cluster_size:.1f}개 이상치/군집
- 최대 군집 크기: {max_cluster_size}개 이상치
- 단일 이상치(군집이 아닌) 비율: {single_anomalies_pct:.1f}%
"""

            # 가장 큰 군집 정보 추가
            if largest_cluster_info:
                cluster_analysis += f"""
- 가장 큰 이상치 군집:
  - 시작 시간: {largest_cluster_info['start_time']}
  - 종료 시간: {largest_cluster_info['end_time']}
  - 지속 시간: {largest_cluster_info['duration']:.1f} 시간
"""

            # 시간별 이상치 분포
            hour_data = hour_anomaly.sort_values('count', ascending=False).head(3)
            hour_list = [f"{row['hour']}시 ({row['count']}개)" for _, row in hour_data.iterrows()]
            hour_top = ", ".join(hour_list)
            
            # 요일별 이상치 분포
            day_data = day_anomaly.sort_values('count', ascending=False).head(3)
            day_list = [f"{row['day_name']}요일 ({row['count']}개)" for _, row in day_data.iterrows()]
            day_top = ", ".join(day_list)
            
            # 월별 이상치 분포
            month_data = month_anomaly.sort_values('count', ascending=False).head(3)
            month_list = [f"{row['month']}월 ({row['count']}개)" for _, row in month_data.iterrows()]
            month_top = ", ".join(month_list)
            
            distribution_analysis = f"""
## 이상치 분포 분석
- 이상치가 가장 많이 발생하는 시간대 (상위 3개): {hour_top}
- 이상치가 가장 많이 발생하는 요일 (상위 3개): {day_top}
- 이상치가 가장 많이 발생하는 월 (상위 3개): {month_top}
"""
        else:
            # 이상치가 없는 경우의 통계 정보
            anomaly_stats = f"""
## 이상치 통계 정보
- 사용된 임계값: Z-score > {threshold}
- 감지된 이상치 수: 0개 (0.0%)
- 현재 설정된 임계값에서는 이상치가 감지되지 않았습니다.
"""
            cluster_analysis = ""
            distribution_analysis = ""

        # 시스템 프롬프트 부분 추가
        system_prompt = f"""당신은 IoT 센서 데이터 분석 전문가입니다. 이상치 분석 데이터에 대한 인사이트를 제공합니다.

분석 중인 데이터는 {equipment_type}의 {sensor_type_display} 값으로, Z-score 기반 이상치 탐지 방법을 사용하여 분석되었습니다.
이 분석은 Z-score {threshold} 이상인 값을 이상치로 간주하며, 이상치의 분포와 패턴을 보여줍니다.

주요 분석 포인트:
1. 이상치의 전반적인 특성 (빈도, 상/하단 분포)
2. 이상치 발생의 시간적 패턴 (시간/요일/월별)
3. 이상치 군집의 특성과 의미
4. 이상치가 장비 성능에 주는 의미
5. 이상치 감소 및 장비 유지보수를 위한 제안
"""
            
        # 분석 프롬프트 생성
        analysis_prompt = f"""{system_prompt}

다음은 IoT {sensor_type_display} 데이터의 이상치 분석 결과입니다.

## 이상치 분석 정보
- 장비 유형: {equipment_type}
- 센서 유형: {sensor_type_display}
- 분석 방법: Z-score 기반 이상치 탐지 (임계값: {threshold})

{anomaly_stats}
"""

        # 이상치가 있는 경우에만 나머지 분석 정보 추가
        if has_anomalies:
            analysis_prompt += f"""
{cluster_analysis}

{distribution_analysis}

## 분석 과제
위 이상치 데이터에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {sensor_type_display} 이상치의 전반적인 특성과 패턴
   - 이상치 발생 빈도의 의미와 심각성 평가
   - 상단/하단 이상치 분포의 의미와 장비 상태에 주는 시사점

2. {sensor_type_display} 이상치 발생의 시간적 패턴 분석
   - 시간대별/요일별/월별 이상치 발생 패턴의 의미
   - 특정 시간대에 이상치가 집중되는 이유와 그 영향

3. {sensor_type_display} 이상치 군집 분석 결과 해석
   - 군집 패턴이 나타내는 장비 문제의 특성
   - 단일 이상치와 군집 이상치의 차이점과 각각의 의미

4. {sensor_type_display} 이상치가 장비 성능 및 운영에 미치는 영향
   - 이상치 패턴이 장비 성능에 미치는 영향
   - 이상치 패턴에서 도출할 수 있는 장비 상태 진단

5. {sensor_type_display} 이상치 감소 및 장비 유지보수를 위한 실용적인 제안
   - 이상치 패턴을 고려한 예방적 유지보수 전략
   - 이상치가 자주 발생하는 시간대/요일/월에 대한 운영 최적화 방안
"""
        else:
            # 이상치가 없는 경우의 분석 과제
            analysis_prompt += f"""
## 분석 과제
현재 설정된 임계값(Z-score > {threshold})에서는 {sensor_type_display} 이상치가 감지되지 않았습니다. 이에 대한 인사이트를 마크다운 형식으로 제공해주세요. 다음 내용을 포함해주세요:

1. {sensor_type_display} 이상치가 없다는 결과의 의미
   - 장비 상태와 성능 관점에서 이상치 부재의 의미
   - 현재 임계값 설정의 적절성 평가

2. {sensor_type_display} 데이터의 전반적인 특성 분석
   - 데이터 분포의 정규성 및 안정성 평가
   - {sensor_type_display} 값의 변동성과 그 의미

3. {sensor_type_display} 장비 모니터링 전략 제안
   - 현재 상황에서의 적절한 모니터링 전략
   - 더 효과적인 이상치 탐지를 위한 임계값 조정 제안

4. {sensor_type_display} 예방 유지보수 관점의 조언
   - 이상치가 없는 상황에서의 예방 유지보수 전략
   - 향후 잠재적 문제를 조기에 감지하기 위한 방안

5. {sensor_type_display} 데이터 품질 및 센서 성능에 대한 평가
   - 이상치 부재가 데이터 품질이나 센서 성능에 대해 알려주는 정보
   - 추가적인 데이터 검증이나 분석이 필요한지 여부
"""

        analysis_prompt += """
결과는 명확하고 간결하게 작성하고, 중요한 사항은 **볼드체**로 강조해주세요.
"""

        # 이상치 전용 프롬프트로 저장
        st.session_state[anomaly_prompt_key] = analysis_prompt
        
        # 분석 설정이 변경되면 캐시도 초기화
        if analysis_changed:
            cache_state_key = f"{key_prefix}_cache"
            if cache_state_key in st.session_state:
                st.session_state[cache_state_key] = {}
                print(f"이상치 분석 설정이 변경되어 캐시 초기화")
        
        # 디버깅용 로깅
        print(f"이상치 분석 프롬프트 생성 완료 (길이: {len(analysis_prompt)})")
    else:
        # 캐시된 이상치 전용 프롬프트 사용
        analysis_prompt = st.session_state[anomaly_prompt_key]
        print(f"캐시된 이상치 프롬프트 사용 (길이: {len(analysis_prompt)})")

    # AI 분석 섹션 추가
    st.markdown("---")
    st.subheader("🤖 AI 이상치 분석")

    # 세션 상태 키 정의 - 모두 이상치 전용 키 사용
    chat_history_key = f"{key_prefix}_history"
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    
    # 메모리 길이 확인 및 설정 (대화 기억을 위해 메모리 길이 설정 강제)
    if st.session_state.memory_length < 2:
        print(f"메모리 길이가 너무 작음: {st.session_state.memory_length}. 5로 설정합니다.")
        st.session_state.memory_length = 5
    
    # 분석 실행 여부 확인 - 이상치 전용 키 사용
    if running_key in st.session_state:
        is_running = st.session_state[running_key]
    else:
        is_running = False
    
    # 분석 버튼 클릭 콜백 함수 - 이상치 분석 전용
    def on_anomaly_analyze_click():
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
        print(f"이상치 분석 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # 최초 AI 분석 결과 요청에 대한 UI 표시 - 이상치 전용 버튼
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            "AI 이상치 분석 실행", 
            key=f"{key_prefix}_button", 
            on_click=on_anomaly_analyze_click,
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
            print(f"이상치 분석: 캐시된 결과를 사용함")
    
    # 분석 실행 중인 경우
    elif is_running:
        # 대화 기록 초기화 (새로운 분석 시작)
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
            print(f"이상치 분석: 대화 기록 초기화됨")
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 이상치 데이터를 분석하고 있습니다..."):
                print(f"이상치 분석: generate_ai_response 함수 호출 전")
                print(f"프롬프트 첫 100자: {analysis_prompt[:100]}...")
                generate_ai_response(
                    prompt=analysis_prompt,
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
                print(f"이상치 분석: generate_ai_response 함수 호출 후")
        
        # 실행 완료 후 상태 업데이트
        st.session_state[running_key] = False
    
    # 분석 전 안내 메시지
    else:
        if has_anomalies:
            st.info("AI 분석을 실행하려면 'AI 이상치 분석 실행' 버튼을 클릭하세요. 이상치 데이터의 패턴과 인사이트를 분석합니다.")
        else:
            st.info("AI 분석을 실행하려면 'AI 이상치 분석 실행' 버튼을 클릭하세요. 현재 임계값에서 이상치가 없는 상황에 대한 인사이트를 분석합니다.")
    
    # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
    # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
    has_previous_analysis = (
        cache_state_key in st.session_state and 
        len(st.session_state[cache_state_key]) > 0
    )
    
    if has_previous_analysis:
        # 대화형 인터페이스 표시
        st.markdown("---")
        if has_anomalies:
            st.subheader("🤖 이상치 데이터에 대해 질문하기")
        else:
            st.subheader("🤖 이상치 부재 상황에 대해 질문하기")
        
        # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
        if chat_history_key in st.session_state:
            print(f"이상치: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
            roles = [msg["role"] for msg in st.session_state[chat_history_key]]
            print(f"이상치: 대화 기록 역할 목록: {roles}")
        
        # 대화형 인터페이스 표시
        display_chat_interface(key_prefix=key_prefix)
    elif not is_running:
        # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
        if has_anomalies:
            st.info("AI 데이터 분석을 먼저 실행하여 이상치 데이터에 대한 인사이트를 얻은 후 질문할 수 있습니다.")
        else:
            st.info("AI 데이터 분석을 먼저 실행하여 이상치 부재 상황에 대한 인사이트를 얻은 후 질문할 수 있습니다.") 

# 이상치 분석 UI 랜더링
def render_anomaly_ui(df):
    """이상치 분석 UI를 렌더링합니다."""
    # Apply styles
    load_iot_font_css()
    apply_custom_style()
    
    # AI 관련 세션 상태 초기화
    init_ai_settings()  # 반드시 먼저 호출하여 세션 상태 초기화
    
    # 사이드바에 AI 모델 설정 추가
    with st.sidebar:
        # 공유 AI 설정 UI 렌더링
        render_ai_settings_ui()
    
    st.subheader("이상치 분석")
    
    # Get equipment type using the helper function
    equipment_type = get_equipment_type(df)
    
    # 센서 컬럼 이름 가져오기
    sensor_col = get_sensor_type()
    if sensor_col not in df.columns:
        sensor_col = "value"  # 기본값으로 fallback
    
    # 센서 타입 표시용 이름
    sensor_type_display = sensor_col
    
    # 운전/중지 패턴 분석 옵션 추가
    with st.expander("운전/중지 패턴 필터링 설정", expanded=False):
        enable_operation_filter = st.checkbox("운전/중지 상태에 따라 이상치 분석 수행", 
                                            help="체크하면 선택한 운전 상태(운전/중지)에 대해서만 이상치를 분석합니다.")
        
        if enable_operation_filter:
            col1, col2 = st.columns(2)
            
            with col1:
                operation_state = st.radio(
                    "분석할 상태 선택",
                    ["운전 상태만", "중지 상태만", "모든 상태"],
                    help="이상치를 분석할 운전 상태를 선택합니다."
                )
            
            with col2:
                # 운전/중지 상태 결정 방법
                if "state" in df.columns:
                    # 이미 상태 열이 있는 경우
                    st.info("데이터에 상태 열(state)이 존재합니다. 해당 열을 사용하여 운전/중지 상태를 구분합니다.")
                    use_existing_state = True
                else:
                    # 상태 열이 없는 경우, 임계값 기반으로 상태 결정
                    use_existing_state = False
                    state_threshold = st.slider(
                        "운전/중지 구분 임계값",
                        min_value=float(df[sensor_col].min()),
                        max_value=float(df[sensor_col].max()),
                        value=float((df[sensor_col].min() + df[sensor_col].max()) / 2),
                        help="이 값보다 큰 센서값은 운전 상태로, 작거나 같은 값은 중지 상태로 간주합니다."
                    )
    
    # 이상치 분석 설정
    threshold = st.slider("이상치 임계값 (Z-score)", 1.0, 5.0, 3.0, 0.1)
    
    # 원본 데이터 복사
    df_copy = df.copy()
    
    # 운전/중지 상태 필터링 적용
    if enable_operation_filter:
        # 상태 열이 없는 경우 임계값 기반으로 상태 결정
        if not use_existing_state:
            df_copy['state'] = (df_copy[sensor_col] > state_threshold).astype(int)  # 1: 운전, 0: 중지
        
        # 선택한 상태에 따라 데이터 필터링
        if operation_state == "운전 상태만":
            filtered_df = df_copy[df_copy['state'] == 1]
            state_label = "운전 상태"
        elif operation_state == "중지 상태만":
            filtered_df = df_copy[df_copy['state'] == 0]
            state_label = "중지 상태"
        else:  # "모든 상태"
            filtered_df = df_copy
            state_label = "모든 상태"
        
        # 필터링된 데이터가 없는 경우 처리
        if len(filtered_df) == 0:
            st.warning(f"선택한 {state_label}에 해당하는 데이터가 없습니다.")
            return
            
        # 필터링 정보 표시
        st.info(f"{state_label}에 대한 이상치를 분석합니다. (전체 {len(df_copy)}개 중 {len(filtered_df)}개 데이터 포인트)")
    else:
        # 필터링 없이 모든 데이터 사용
        filtered_df = df_copy
    
    # Calculate z-scores for anomaly detection
    filtered_df['z_score'] = (filtered_df[sensor_col] - filtered_df[sensor_col].mean()) / filtered_df[sensor_col].std()
    
    # Mark anomalies
    filtered_df['is_anomaly'] = abs(filtered_df['z_score']) > threshold
    anomalies = filtered_df[filtered_df['is_anomaly']]
    
    # Sample for visualization if too large
    if len(filtered_df) > 5000:
        sample_size = min(5000, len(filtered_df) // 10)  # 최대 5000개 또는 10%만 샘플링
        step = max(1, len(filtered_df) // sample_size)
        df_sample = filtered_df.iloc[::step].copy()
        # Make sure to include anomalies (최대 1000개 이상치만 포함)
        if len(anomalies) > 1000:
            anomalies_sample = anomalies.sample(1000, random_state=42)
            st.caption(f"데이터 크기가 큰 관계로 샘플링된 데이터와 1000개의 이상치만 시각화합니다. 원본 데이터: {len(filtered_df):,}개, 표시: {len(df_sample):,}개, 이상치: {len(anomalies):,}개 중 1000개")
            df_sample = pd.concat([df_sample, anomalies_sample]).drop_duplicates()
        else:
            df_sample = pd.concat([df_sample, anomalies]).drop_duplicates()
            st.caption(f"데이터 크기가 큰 관계로 샘플링된 데이터를 시각화합니다. 원본 데이터: {len(filtered_df):,}개, 표시: {len(df_sample):,}개")
    else:
        df_sample = filtered_df.copy()
    
    # 신뢰구간 계산
    mean_val = filtered_df[sensor_col].mean()
    std_val = filtered_df[sensor_col].std()
    upper_bound = mean_val + threshold * std_val
    lower_bound = mean_val - threshold * std_val
    
    # 기본 이상치 시각화
    fig = go.Figure()
    
    # 정상 데이터 추가
    fig.add_trace(go.Scatter(
        x=df_sample[~df_sample['is_anomaly']]['timestamp'],
        y=df_sample[~df_sample['is_anomaly']][sensor_col],
        mode='markers',
        name='정상 데이터',
        marker=dict(
            size=5,
            color='rgba(0, 150, 255, 0.5)'
        )
    ))
    
    # 이상치 데이터 추가
    fig.add_trace(go.Scatter(
        x=df_sample[df_sample['is_anomaly']]['timestamp'],
        y=df_sample[df_sample['is_anomaly']][sensor_col],
        mode='markers',
        name='이상치',
        marker=dict(
            size=10,
            symbol='diamond',
            color='red',
            line=dict(width=2, color='black')
        )
    ))
    
    # 상한 임계값 추가
    fig.add_trace(go.Scatter(
        x=[filtered_df['timestamp'].min(), filtered_df['timestamp'].max()],
        y=[upper_bound, upper_bound],
        mode='lines',
        name=f'상한 임계값 (+{threshold}σ)',
        line=dict(color='red', width=1, dash='dash')
    ))
    
    # 하한 임계값 추가
    fig.add_trace(go.Scatter(
        x=[filtered_df['timestamp'].min(), filtered_df['timestamp'].max()],
        y=[lower_bound, lower_bound],
        mode='lines',
        name=f'하한 임계값 (-{threshold}σ)',
        line=dict(color='red', width=1, dash='dash')
    ))
    
    # 평균선 추가
    fig.add_trace(go.Scatter(
        x=[filtered_df['timestamp'].min(), filtered_df['timestamp'].max()],
        y=[mean_val, mean_val],
        mode='lines',
        name='평균',
        line=dict(color='green', width=1)
    ))
    
    # 신뢰구간 영역 추가 (영역 채우기) - 메모리 최적화 버전
    # 날짜 범위의 양 끝점만 사용해 사각형 생성
    x_dates = [filtered_df['timestamp'].min(), filtered_df['timestamp'].max(),
               filtered_df['timestamp'].max(), filtered_df['timestamp'].min()]
    y_values = [lower_bound, lower_bound, upper_bound, upper_bound]
    
    fig.add_trace(go.Scatter(
        x=x_dates,
        y=y_values,
        fill='toself',
        fillcolor='rgba(0, 255, 0, 0.1)',
        line=dict(color='rgba(255, 255, 255, 0)'),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # 차트 레이아웃 설정
    fig.update_layout(
        title=f"{equipment_type} 이상치 분석 (Z-score > {threshold})",
        xaxis_title="시간",
        yaxis_title=f"{sensor_type_display}",
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='closest'
    )
    
    # 기본 플롯 표시 설정
    config = {
        'responsive': True, 
        'displaylogo': False,
        'toImageButtonOptions': {
            'format': 'png', 
            'filename': f'{equipment_type}_anomaly_analysis',
            'height': 800,
            'width': 1200,
            'scale': 2
        }
    }
    
    st.plotly_chart(fig, use_container_width=True, config=config)

    # Display anomaly statistics
    st.metric("감지된 이상치 수", f"{len(anomalies):,} ({len(anomalies)/len(filtered_df)*100:.2f}%)")
    
    # AI 분석에 필요한 변수들 초기화
    hour_anomaly = pd.DataFrame()
    day_anomaly = pd.DataFrame()
    month_anomaly = pd.DataFrame()
    pos_count = 0
    neg_count = 0
    num_clusters = 0
    avg_cluster_size = 0
    max_cluster_size = 0
    single_anomalies_pct = 0
    largest_cluster_info = None
    
    if len(anomalies) > 0:
        st.subheader("상위 이상치 목록")
        # Sort by absolute z-score
        sorted_anomalies = anomalies.sort_values(by='z_score', key=abs, ascending=False)
        
        # 운전/중지 상태 열 추가 (필터링 모드에서)
        if enable_operation_filter and 'state' in sorted_anomalies.columns:
            sorted_anomalies['상태'] = sorted_anomalies['state'].map({1: '운전', 0: '중지'})
            st.dataframe(sorted_anomalies.head(10)[['timestamp', sensor_col, 'z_score', '상태']])
        else:
            st.dataframe(sorted_anomalies.head(10)[['timestamp', sensor_col, 'z_score']])
        
        # 이상치 분포 분석
        with st.expander("이상치 분포 분석"):
            # 시간별 이상치 분포
            anomalies['hour'] = anomalies['timestamp'].dt.hour
            anomalies['day_of_week'] = anomalies['timestamp'].dt.dayofweek
            anomalies['month'] = anomalies['timestamp'].dt.month
            
            # 요일 이름 추가
            day_names = ['월', '화', '수', '목', '금', '토', '일']
            anomalies['day_name'] = anomalies['day_of_week'].apply(lambda x: day_names[x])
            
            # 시간별 이상치 분포
            hour_anomaly = anomalies.groupby('hour').size().reset_index(name='count')
            
            # 상태별 제목 설정
            if enable_operation_filter and operation_state != "모든 상태":
                title_prefix = f"{state_label}의 {sensor_type_display}"
            else:
                title_prefix = f"{sensor_type_display}"
            
            fig1 = px.bar(hour_anomaly, x='hour', y='count',
                        title=f"시간별 {title_prefix} 이상치 발생 빈도",
                        labels={"hour": "시간", "count": "이상치 수"})
            
            st.plotly_chart(fig1, use_container_width=True)
            
            # 요일별 이상치 분포
            day_anomaly = anomalies.groupby('day_name').size().reset_index(name='count')
            day_anomaly['day_name'] = pd.Categorical(day_anomaly['day_name'], categories=day_names, ordered=True)
            day_anomaly = day_anomaly.sort_values('day_name')
            
            fig2 = px.bar(day_anomaly, x='day_name', y='count',
                        title=f"요일별 {title_prefix} 이상치 발생 빈도",
                        labels={"day_name": "요일", "count": "이상치 수"})
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # 월별 이상치 분포
            month_anomaly = anomalies.groupby('month').size().reset_index(name='count')
            
            fig3 = px.bar(month_anomaly, x='month', y='count',
                        title=f"월별 {title_prefix} 이상치 발생 빈도",
                        labels={"month": "월", "count": "이상치 수"})
            
            # X축 레이블 설정
            fig3.update_xaxes(tickvals=list(range(1, 13)), ticktext=[f"{i}월" for i in range(1, 13)])
            
            st.plotly_chart(fig3, use_container_width=True)
        
        # 이상치 패턴 분석
        with st.expander("이상치 패턴 분석"):
            # 이상치 타입 분석 (양수/음수)
            positive_anomalies = anomalies[anomalies['z_score'] > 0]
            negative_anomalies = anomalies[anomalies['z_score'] < 0]
            
            pos_count = len(positive_anomalies)
            neg_count = len(negative_anomalies)
            total_count = pos_count + neg_count
            
            st.write(f"**이상치 타입 분석:**")
            st.write(f"- 상단 이상치 (높은 값): {pos_count}개 ({pos_count/total_count*100:.1f}%)")
            st.write(f"- 하단 이상치 (낮은 값): {neg_count}개 ({neg_count/total_count*100:.1f}%)")
            
            # 운전/중지 상태별 이상치 분석 (모든 상태 선택 시)
            if enable_operation_filter and 'state' in anomalies.columns and operation_state == "모든 상태":
                on_anomalies = anomalies[anomalies['state'] == 1]
                off_anomalies = anomalies[anomalies['state'] == 0]
                
                on_count = len(on_anomalies)
                off_count = len(off_anomalies)
                
                st.write(f"**운전/중지 상태별 이상치 분석:**")
                st.write(f"- 운전 상태 이상치: {on_count}개 ({on_count/total_count*100:.1f}%)")
                st.write(f"- 중지 상태 이상치: {off_count}개 ({off_count/total_count*100:.1f}%)")
                
                # 운전/중지 상태별 상/하단 이상치 비율
                on_pos = len(on_anomalies[on_anomalies['z_score'] > 0])
                on_neg = len(on_anomalies[on_anomalies['z_score'] < 0])
                off_pos = len(off_anomalies[off_anomalies['z_score'] > 0])
                off_neg = len(off_anomalies[off_anomalies['z_score'] < 0])
                
                if on_count > 0:
                    st.write(f"  - 운전 상태 상단 이상치: {on_pos}개 ({on_pos/on_count*100:.1f}%)")
                    st.write(f"  - 운전 상태 하단 이상치: {on_neg}개 ({on_neg/on_count*100:.1f}%)")
                
                if off_count > 0:
                    st.write(f"  - 중지 상태 상단 이상치: {off_pos}개 ({off_pos/off_count*100:.1f}%)")
                    st.write(f"  - 중지 상태 하단 이상치: {off_neg}개 ({off_neg/off_count*100:.1f}%)")
            
            # 이상치 군집 분석
            # 타임스탬프로 정렬
            sorted_anomalies = anomalies.sort_values('timestamp')
            
            # 연속된 이상치 확인 (1시간 이내)
            sorted_anomalies['prev_timestamp'] = sorted_anomalies['timestamp'].shift(1)
            sorted_anomalies['time_diff'] = (sorted_anomalies['timestamp'] - sorted_anomalies['prev_timestamp']).dt.total_seconds() / 3600  # 시간 단위
            
            # 새로운 군집 시작 지점 (이전 이상치와 1시간 이상 차이)
            sorted_anomalies['new_cluster'] = sorted_anomalies['time_diff'] > 1
            sorted_anomalies['new_cluster'] = sorted_anomalies['new_cluster'].fillna(True)  # 첫 번째 행은 새 군집으로 처리
            
            # 군집 ID 부여
            sorted_anomalies['cluster_id'] = sorted_anomalies['new_cluster'].cumsum()
            
            # 군집별 크기 계산
            cluster_sizes = sorted_anomalies.groupby('cluster_id').size()
            
            # 군집 수와 평균 크기
            num_clusters = len(cluster_sizes)
            avg_cluster_size = cluster_sizes.mean()
            max_cluster_size = cluster_sizes.max()
            
            st.write(f"**이상치 군집 분석:**")
            st.write(f"- 이상치 군집 수: {num_clusters}개")
            st.write(f"- 평균 군집 크기: {avg_cluster_size:.1f}개 이상치/군집")
            st.write(f"- 최대 군집 크기: {max_cluster_size}개 이상치")
            
            # 가장 큰 군집의 시작과 끝 시간
            largest_cluster_id = cluster_sizes.idxmax()
            largest_cluster = sorted_anomalies[sorted_anomalies['cluster_id'] == largest_cluster_id]
            
            start_time = largest_cluster['timestamp'].min()
            end_time = largest_cluster['timestamp'].max()
            duration = (end_time - start_time).total_seconds() / 3600  # 시간 단위
            
            # 가장 큰 군집 정보 저장
            largest_cluster_info = {
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration
            }
            
            st.write(f"- 가장 큰 이상치 군집:")
            st.write(f"  - 시작 시간: {start_time}")
            st.write(f"  - 종료 시간: {end_time}")
            st.write(f"  - 지속 시간: {duration:.1f} 시간")
            
            # 단일 이상치(군집이 아닌) 비율
            single_anomalies = cluster_sizes[cluster_sizes == 1].count()
            single_anomalies_pct = single_anomalies/num_clusters*100
            st.write(f"- 단일 이상치(군집이 아닌) 비율: {single_anomalies_pct:.1f}%")
    
    # 운전/중지 상태 필터링 정보 추가
    operation_filter_info = ""
    if enable_operation_filter:
        operation_filter_info = f" ({state_label})"
    
    # AI 분석 부분 호출 (이상치가 있는 경우에만)
    if len(anomalies) > 0:
        render_ai_analysis(
            df=filtered_df,  # 필터링된 데이터 전달
            equipment_type=equipment_type,
            sensor_type_display=f"{sensor_type_display}{operation_filter_info}",  # 상태 정보 포함
            threshold=threshold,
            anomalies=anomalies,
            pos_count=pos_count,
            neg_count=neg_count,
            num_clusters=num_clusters,
            avg_cluster_size=avg_cluster_size,
            max_cluster_size=max_cluster_size,
            single_anomalies_pct=single_anomalies_pct,
            hour_anomaly=hour_anomaly,
            day_anomaly=day_anomaly,
            month_anomaly=month_anomaly,
            largest_cluster_info=largest_cluster_info
        )
    else:
        # 이상치가 없는 경우에도 AI 분석 부분 호출
        render_ai_analysis(
            df=filtered_df,  # 필터링된 데이터 전달
            equipment_type=equipment_type,
            sensor_type_display=f"{sensor_type_display}{operation_filter_info}",  # 상태 정보 포함
            threshold=threshold,
            anomalies=pd.DataFrame(),  # 빈 데이터프레임 전달
            pos_count=0,
            neg_count=0,
            num_clusters=0,
            avg_cluster_size=0,
            max_cluster_size=0,
            single_anomalies_pct=0,
            hour_anomaly=pd.DataFrame(),
            day_anomaly=pd.DataFrame(),
            month_anomaly=pd.DataFrame(),
            largest_cluster_info=None,
            has_anomalies=False  # 이상치 없음 플래그 추가
        )
