import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="💎 DX-AI IoT Algorithm",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# iot_algorithm 패키지에서 직접 main 함수 import
from iot_algorithm.main import main

# 애플리케이션 실행
if __name__ == "__main__":
    main() 