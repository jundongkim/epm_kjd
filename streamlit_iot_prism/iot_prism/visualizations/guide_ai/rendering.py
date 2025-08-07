"""
AI 분석 결과 렌더링 모듈

이 모듈은 AI 분석 결과를 UI에 렌더링하는 함수를 제공합니다.
"""

import streamlit as st
import json
from .prompts import construct_ai_prompt
from ...utils.ai_utils import init_session_state, generate_ai_response, display_chat_interface

def render_ai_analysis(df, recommendations, df_info):
    """AI 분석 부분을 랜더링합니다"""
    # 세션 상태 초기화 (AI 분석용)
    key_prefix = "visualization_guide"
    init_session_state(key_prefix=key_prefix)
    
    # AI 분석 프롬프트 구성
    prompt = construct_ai_prompt(df_info, recommendations)
    
    # 세션 상태 키 정의
    cache_state_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    chat_history_key = f"{key_prefix}_history"
    initial_analysis_added_key = f"{key_prefix}_initial_analysis_added"
    
    # 분석 버튼 클릭 콜백 함수 정의
    def on_analyze_click():
        # 캐시 초기화
        if cache_state_key in st.session_state:
            # 캐시 키 생성
            from ...utils.ai_utils import generate_cache_key
            cache_key = generate_cache_key(
                prompt=prompt,
                model=st.session_state.selected_model,
                temperature=st.session_state.temperature
            )
            st.session_state[cache_state_key].pop(cache_key, None)
        # 대화 기록 초기화
        if chat_history_key in st.session_state:
            st.session_state[chat_history_key] = []
        # 초기 분석 추가 상태 초기화
        st.session_state[initial_analysis_added_key] = False
        # 실행 상태 설정
        st.session_state[running_key] = True
        
        # 디버깅용 로깅
        print(f"분석 가이드 버튼 클릭됨. 캐시 초기화 및 분석 시작.")
    
    # UI 컴포넌트 구성
    analysis_container = st.container()
    with analysis_container:
        st.subheader("AI 기반 분석 추천")
        
        # 최초 AI 분석 결과 요청에 대한 UI 표시
        col1, col2 = st.columns([3, 1])
        with col1:
            model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
            st.caption(model_info)
        with col2:
            analyze_button = st.button(
                "AI 분석 추천 생성", 
                key=f"{key_prefix}_button", 
                on_click=on_analyze_click,
                use_container_width=True
            )
        
        # 이전 분석 결과가 있는 경우 (캐시에 있는 경우)
        if cache_state_key in st.session_state and len(st.session_state[cache_state_key]) > 0:
            # 캐시 키 생성
            from ...utils.ai_utils import generate_cache_key
            cache_key = generate_cache_key(
                prompt=prompt,
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
                print(f"분석 가이드: 캐시된 결과를 사용함")
                
                # 중요: 캐시된 결과를 대화 기록에 추가 (최초 1회만)
                if not st.session_state.get(initial_analysis_added_key, False):
                    # 대화 기록 초기화 (이전 내용 제거)
                    if chat_history_key in st.session_state:
                        st.session_state[chat_history_key] = []
                    
                    # 대화 기록에 초기 프롬프트와 응답 추가
                    st.session_state[chat_history_key].append({
                        "role": "user",
                        "content": prompt
                    })
                    st.session_state[chat_history_key].append({
                        "role": "assistant", 
                        "content": cached_response["response"]
                    })
                    
                    # 초기 분석 추가 완료 표시
                    st.session_state[initial_analysis_added_key] = True
                    print(f"분석 가이드: 초기 분석을 대화 기록에 추가함")
        
        # 분석 실행 중인 경우
        elif running_key in st.session_state and st.session_state[running_key]:
            # 대화 기록 초기화 (새로운 분석 시작)
            if chat_history_key in st.session_state:
                st.session_state[chat_history_key] = []
                print(f"분석 가이드: 대화 기록 초기화됨")
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                metadata_placeholder = st.empty()
                with st.spinner("AI가 데이터를 분석하고 추천 방법을 생성하고 있습니다..."):
                    print(f"분석 가이드: generate_ai_response 함수 호출 전")
                    print(f"프롬프트 첫 100자: {prompt[:100]}...")
                    generate_ai_response(
                        prompt=prompt,
                        key_prefix=key_prefix,
                        message_placeholder=message_placeholder,
                        metadata_placeholder=metadata_placeholder
                    )
                    print(f"분석 가이드: generate_ai_response 함수 호출 후")
            
            # 실행 완료 후 상태 업데이트
            st.session_state[running_key] = False
            # 초기 분석 추가 완료 표시
            st.session_state[initial_analysis_added_key] = True
        
        # 분석 전 안내 메시지
        else:
            st.info("'AI 기반 분석 추천 버튼'을 클릭하여 AI 분석 추천을 받으세요. AI는 데이터 특성에 맞춘 분석 순서와 방법을 제안합니다.")
        
        # 대화형 인터페이스는 분석이 한 번 이상 실행된 경우에만 표시
        # 캐시에 결과가 있으면 분석이 실행된 것으로 간주
        has_previous_analysis = (
            cache_state_key in st.session_state and 
            len(st.session_state[cache_state_key]) > 0
        )
        
        if has_previous_analysis:
            # 대화형 인터페이스 표시
            st.markdown("---")
            st.subheader("분석 방법 질의응답")
            st.markdown("데이터 분석에 관한 추가 질문이 있으시면 아래에 입력하세요.")
            
            # 이 시점에서 대화 기록의 상태 로깅 (디버깅용)
            if chat_history_key in st.session_state:
                print(f"분석 가이드: 대화 인터페이스 표시 전 대화 기록 길이: {len(st.session_state[chat_history_key])}")
                roles = [msg["role"] for msg in st.session_state[chat_history_key]]
                print(f"분석 가이드: 대화 기록 역할 목록: {roles}")
            
            # 대화형 인터페이스 표시
            display_chat_interface(key_prefix=key_prefix)
        elif not (running_key in st.session_state and st.session_state[running_key]):
            # 분석이 아직 실행되지 않았고 현재 실행 중도 아닌 경우 안내 메시지 표시
            st.info("AI 분석을 먼저 실행하여 추천을 받은 후 추가 질문할 수 있습니다.") 