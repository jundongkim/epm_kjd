import streamlit as st
import base64
import functools
import warnings

def conditional_st_cache(func):
    """
    Conditional Streamlit cache decorator that only applies caching when Streamlit runtime is available.
    This prevents warnings during parallel processing or standalone execution.
    """
    try:
        # Check if Streamlit runtime is available
        if hasattr(st, 'runtime') and st.runtime.exists():
            # Use Streamlit caching when runtime is available
            return st.cache_data(func)
        else:
            # Use simple function caching when Streamlit runtime is not available
            return functools.lru_cache(maxsize=128)(func)
    except:
        # Fallback to simple function caching if any error occurs
        return functools.lru_cache(maxsize=128)(func)

@conditional_st_cache
def get_font_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def inject_custom_font(font_path: str):
    """
    Injects a custom font into the Streamlit app by encoding it in base64.
    """
    try:
        font_base64 = get_font_as_base64(font_path)
        st.markdown(
            f"""
            <style>
            @font-face {{
                font-family: 'Paperlogy';
                src: url(data:font/ttf;base64,{font_base64}) format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
            * {{
                font-family: 'Paperlogy', sans-serif !important;
            }}
            /* Keep code blocks monospaced for readability */
            .stCodeBlock, code, kbd, samp, pre {{
                font-family: 'Courier New', Courier, monospace !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        ) 
    except Exception as e:
        # Silently ignore font injection errors when Streamlit runtime is not available
        pass 