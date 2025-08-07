"""
SEM-EDS 분석을 위한 서버 연결 관련 유틸리티
"""

import requests
import streamlit as st

def check_ollama_server():
    """Ollama 서버 연결 상태 확인

    Returns:
        bool: 서버 연결 상태 (True: 연결됨, False: 연결 안됨)
    """
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except Exception as e:
        return False