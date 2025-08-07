"""
스타일 및 폰트 관련 모듈

이 모듈은 시각화 가이드의 UI 스타일과 폰트 적용 관련 함수를 제공합니다.
"""

import streamlit as st
import os
import base64
import logging
from iot_prism.utils import get_font_path  # 폰트 경로 가져오기

def apply_custom_font():
    """Paperlogy 폰트를 적용합니다. 없을 경우 Noto Sans KR 폰트로 대체합니다."""
    # 로깅 설정
    logger = logging.getLogger(__name__)
    
    # IoT 디렉토리의 폰트 사용
    font_path = get_font_path()
    
    if not os.path.exists(font_path):
        logger.warning(f"폰트 파일을 찾을 수 없습니다: {font_path}")
        # 폰트 파일이 없는 경우 웹 폰트 사용
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

        * {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        /* 모든 텍스트 요소에 강제 적용 */
        p, h1, h2, h3, h4, h5, h6, div, span, button, a, input, textarea, select, label, code {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        /* 시각화 카드 스타일 통일 */
        .recommendation-card {
            font-family: 'Noto Sans KR', sans-serif !important;
        }
        
        .card-title {
            font-family: 'Noto Sans KR', sans-serif !important;
            font-weight: 700;
        }
        
        .viz-title {
            font-family: 'Noto Sans KR', sans-serif !important;
            font-weight: 500;
        }
        
        .viz-desc {
            font-family: 'Noto Sans KR', sans-serif !important;
            font-weight: 300;
        }
        </style>
        """, unsafe_allow_html=True)
        return

    try:
        # 폰트 파일을 base64로 인코딩
        with open(font_path, "rb") as font_file:
            encoded_font = base64.b64encode(font_file.read()).decode()
        
        # CSS에 폰트 적용
        custom_css = f"""
        @font-face {{
            font-family: 'Paperlogy';
            src: url(data:font/ttf;base64,{encoded_font});
            font-weight: normal;
            font-style: normal;
        }}

        * {{
            font-family: 'Paperlogy', sans-serif !important;
        }}

        /* 모든 텍스트 요소에 강제 적용 */
        p, h1, h2, h3, h4, h5, h6, div, span, button, a, input, textarea, select, label, code {{
            font-family: 'Paperlogy', sans-serif !important;
        }}

        /* 시각화 카드 스타일 통일 */
        .recommendation-card {{
            font-family: 'Paperlogy', sans-serif !important;
        }}
        
        .card-title {{
            font-family: 'Paperlogy', sans-serif !important;
            font-weight: 700;
        }}
        
        .viz-title {{
            font-family: 'Paperlogy', sans-serif !important;
            font-weight: 500;
        }}
        
        .viz-desc {{
            font-family: 'Paperlogy', sans-serif !important;
            font-weight: 300;
        }}
        """
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
        logger.info("Paperlogy 폰트가 성공적으로 적용되었습니다.")
    except Exception as e:
        logger.error(f"폰트 적용 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본 웹 폰트 사용
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

        * {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        /* 모든 텍스트 요소에 강제 적용 */
        p, h1, h2, h3, h4, h5, h6, div, span, button, a, input, textarea, select, label, code {
            font-family: 'Noto Sans KR', sans-serif !important;
        }

        /* 시각화 카드 스타일 통일 */
        .recommendation-card {
            font-family: 'Noto Sans KR', sans-serif !important;
        }
        
        .card-title {
            font-family: 'Noto Sans KR', sans-serif !important;
            font-weight: 700;
        }
        
        .viz-title {
            font-family: 'Noto Sans KR', sans-serif !important;
            font-weight: 500;
        }
        
        .viz-desc {
            font-family: 'Noto Sans KR', sans-serif !important;
            font-weight: 300;
        }
        </style>
        """, unsafe_allow_html=True) 