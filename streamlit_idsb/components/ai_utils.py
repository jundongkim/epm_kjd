import streamlit as st
import time
import hashlib
import json
import traceback
from components.chat_widget import get_conversation_chain

# 스트리밍 콜백 핸들러 클래스 정의
class StreamlitCallbackHandler:
    def __init__(self, container):
        self.container = container
        self.text = ""
        
    def on_llm_new_token(self, token, **kwargs):
        self.text += token
        self.container.markdown(self.text + "▌")
        # 약간의 지연을 추가하여 시각적 효과 강화
        time.sleep(0.005)

def init_session_state(key_prefix="analysis"):
    """세션 상태 초기화 함수
    
    Args:
        key_prefix (str): 캐시와 상태 변수에 사용할 접두어
    """
    # 모델 관련 설정
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gemma3:4b"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.3
    if "memory_length" not in st.session_state:
        st.session_state.memory_length = 0
    
    # 캐시 및 상태 변수
    cache_key = f"{key_prefix}_cache"
    running_key = f"{key_prefix}_running"
    result_key = f"{key_prefix}_result"
    
    if cache_key not in st.session_state:
        st.session_state[cache_key] = {}
    if running_key not in st.session_state:
        st.session_state[running_key] = False
    if result_key not in st.session_state:
        st.session_state[result_key] = None

def generate_cache_key(prompt: str, model: str, temperature: float) -> str:
    """캐시 키 생성 함수"""
    key_string = f"{prompt}_{model}_{temperature}"
    return hashlib.md5(key_string.encode()).hexdigest()

def generate_ai_analysis(prompt, key_prefix="analysis", message_placeholder=None, metadata_placeholder=None):
    """AI 분석 실행 및 결과 반환
    
    Args:
        prompt (str): 분석에 사용할 프롬프트
        key_prefix (str): 세션 상태 변수 접두어
        message_placeholder (streamlit.empty): 메시지 표시할 placeholder
        metadata_placeholder (streamlit.empty): 메타데이터 표시할 placeholder
        
    Returns:
        tuple: (응답 객체, 전체 응답 텍스트, 메타데이터)
    """
    cache_key = generate_cache_key(
        prompt=prompt,
        model=st.session_state.selected_model,
        temperature=st.session_state.temperature
    )
    
    # 세션 상태 키 정의
    cache_state_key = f"{key_prefix}_cache"
    running_state_key = f"{key_prefix}_running"
    
    try:
        # 대화 체인 생성
        conversation_chain = get_conversation_chain(
            selected_model=st.session_state.selected_model,
            temperature=st.session_state.temperature,
            memory_length=st.session_state.memory_length
        )
        
        # 스트리밍 응답 생성
        response, full_response = conversation_chain.stream_response(
            {"question": prompt}, 
            message_placeholder
        )
        
        # 응답 메타데이터 처리
        source_documents = response.get("source_documents", [])
        metadata = None
        
        if source_documents:
            metadata = {
                "source_count": len(source_documents),
                "sources": [doc.metadata for doc in source_documents] if hasattr(source_documents[0], 'metadata') else []
            }
            
            if metadata_placeholder:
                metadata_text = "\n\n---\n**참고 자료**\n```json\n"
                metadata_text += json.dumps(metadata, indent=2, ensure_ascii=False)
                metadata_text += "\n```"
                metadata_placeholder.markdown(metadata_text)
        
        # 결과 캐싱
        if cache_state_key in st.session_state:
            st.session_state[cache_state_key][cache_key] = {
                "response": full_response,
                "metadata": metadata
            }
        
        # 분석 상태 업데이트
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = False
            
        return response, full_response, metadata
        
    except Exception as e:
        error_msg = f"AI 분석 처리 중 오류가 발생했습니다: {str(e)}"
        st.error(error_msg)
        st.error(traceback.format_exc())
        
        # 분석 상태 업데이트
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = False
            
        return None, error_msg, None

def display_analysis_ui(prompt, button_label="분석 시작", key_prefix="analysis", info_message=None):
    """분석 UI 표시 및 처리
    
    Args:
        prompt (str): 분석에 사용할 프롬프트
        button_label (str): 버튼에 표시할 텍스트
        key_prefix (str): 세션 상태 변수 접두어
        info_message (str): 분석 전 표시할 안내 메시지
        
    Returns:
        bool: 분석 실행 여부
    """
    # 세션 상태 키 정의
    cache_state_key = f"{key_prefix}_cache"
    running_state_key = f"{key_prefix}_running"
    
    # 캐시 키 생성
    cache_key = generate_cache_key(
        prompt=prompt,
        model=st.session_state.selected_model,
        temperature=st.session_state.temperature
    )
    
    # 분석 버튼 추가
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(button_label, key=f"{key_prefix}_button", use_container_width=True)
    
    # 분석 버튼 클릭 시 처리
    if analyze_button:
        if cache_state_key in st.session_state:
            st.session_state[cache_state_key].pop(cache_key, None)  # 캐시 무효화
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = True
        st.rerun()  # 분석 시작을 위한 페이지 새로고침
    
    # 이전 분석 결과가 있는 경우 (캐시에 있는 경우)
    if cache_state_key in st.session_state and cache_key in st.session_state[cache_state_key]:
        cached_response = st.session_state[cache_state_key][cache_key]
        with st.chat_message("assistant"):
            st.markdown(cached_response["response"])
            if cached_response.get("metadata"):
                metadata_text = "\n\n---\n**처리 정보**\n```json\n"
                metadata_text += json.dumps(cached_response["metadata"], indent=2, ensure_ascii=False)
                metadata_text += "\n```"
                st.markdown(metadata_text)
        return False
    
    # 분석 실행 중인 경우 (버튼 클릭 후)
    elif running_state_key in st.session_state and st.session_state[running_state_key]:
        return True
    
    # 분석 전 안내 메시지
    else:
        if info_message is None:
            info_message = f"AI 분석을 실행하려면 '{button_label}' 버튼을 클릭하세요."
        st.info(info_message)
        return False 