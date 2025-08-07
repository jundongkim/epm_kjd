import streamlit as st
from .style import load_iot_font_css, apply_custom_style

def init_ai_settings():
    """Initialize the shared AI settings in session state"""
    # Model selection
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gemma3:4b-it-qat"
    
    # Temperature setting
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.2
    
    # Memory length setting
    if "memory_length" not in st.session_state:
        st.session_state.memory_length = 10

def render_ai_settings_ui():
    """Render the AI settings UI in the sidebar"""
    # Apply styles at the beginning of the function
    load_iot_font_css()
    apply_custom_style()
    
    st.sidebar.subheader("AI 분석 설정")
    
    # Model selection
    model_options = {
        "gemma3:1b": "Gemma3:1b",
        "gemma3:1b-it-qat": "Gemma3:1b-it-qat",
        "gemma3:4b": "Gemma3:4b",
        "gemma3:4b-it-qat": "Gemma3:4b-it-qat",
        "gemma3:12b": "Gemma3:12b",
        "gemma3:12b-it-qat": "Gemma3:12b-it-qat",
        "gemma3:27b": "Gemma3:27b",
        "gemma3:27b-it-qat": "Gemma3:27b-it-qat"
    }
    
    selected_model = st.sidebar.selectbox(
        "모델 선택", 
        list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=list(model_options.keys()).index(st.session_state.selected_model) 
            if st.session_state.selected_model in model_options 
            else 2
    )
    st.session_state.selected_model = selected_model
    
    # Temperature setting
    temperature = st.sidebar.slider(
        "온도", 
        min_value=0.0, 
        max_value=1.0, 
        value=st.session_state.temperature,
        step=0.1,
        help="높을수록 더 다양한 응답을 생성합니다."
    )
    st.session_state.temperature = temperature
    
    # Memory length setting
    memory_length = st.sidebar.slider(
        "대화 기록 길이", 
        min_value=0, 
        max_value=20, 
        value=st.session_state.memory_length,
        step=1,
        help="이전 대화를 기억하는 횟수 (0이면 기억하지 않음)"
    )
    st.session_state.memory_length = memory_length 