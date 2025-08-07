"""
UI 유틸리티 함수
"""
import os
import base64
import streamlit as st
from src.utils.config import FONT_PATH

def get_font_base64(font_file):
    """폰트 파일을 base64로 인코딩하는 함수"""
    if os.path.isfile(font_file):
        with open(font_file, "rb") as f:
            font_data = f.read()
            font_base64 = base64.b64encode(font_data).decode('utf-8')
            return font_base64
    return None

def apply_custom_css():
    """커스텀 CSS 스타일을 적용하는 함수"""
    # 폰트 로딩
    font_base64 = get_font_base64('fonts/Paperlogy-3Light.ttf')
    
    # 기본 CSS 스타일
    css = """
    <style>
    """
    
    # 폰트가 로딩되었으면 적용
    if font_base64:
        css += f"""
        @font-face {{
            font-family: 'Paperlogy-3Light';
            src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
        
        * {{
            font-family: 'Paperlogy-3Light', sans-serif !important;
        }}
        """
    
    # CSS 닫기
    css += """
    </style>
    """
    
    # CSS 적용
    st.markdown(css, unsafe_allow_html=True) 