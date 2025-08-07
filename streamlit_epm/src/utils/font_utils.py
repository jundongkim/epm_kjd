"""
Font utilities for DX-AI Manufacturing Copilot Streamlit application.

This module provides utilities for loading and applying custom fonts in the DX-AI Manufacturing Copilot application.
"""

import streamlit as st
import base64
import os


def load_font_from_file(font_path):
    """
    Load a font from a local file and return it as a base64 encoded string
    
    Args:
        font_path (str): Path to the font file
        
    Returns:
        str: Base64 encoded font string
    """
    try:
        with open(font_path, "rb") as f:
            font_data = f.read()
        return base64.b64encode(font_data).decode()
    except Exception as e:
        st.error(f"폰트 로딩 오류: {e}")
        return None


def apply_paperlogy_font():
    """
    Apply Paperlogy font to the Streamlit application
    """
    font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'fonts', 'Paperlogy.ttf')
    
    if os.path.exists(font_path):
        font_base64 = load_font_from_file(font_path)
        if font_base64:
            st.markdown(f"""
            <style>
            @font-face {{
                font-family: 'Paperlogy';
                src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
            
            html, body, [class*="css"] {{
                font-family: 'Paperlogy', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            </style>
            """, unsafe_allow_html=True)
        else:
            st.error("Paperlogy 폰트를 로드할 수 없습니다.")
    else:
        st.warning("Paperlogy 폰트 파일을 찾을 수 없습니다.") 