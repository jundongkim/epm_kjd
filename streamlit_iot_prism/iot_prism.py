import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="💎 DX-AI IoT Prism",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from iot_prism import main

# 애플리케이션 실행
if __name__ == "__main__":
    main() 