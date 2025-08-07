# iot_algorithm 패키지 초기화

# 스타일 모듈 임포트 및 적용
try:
    # 스타일 적용 (Streamlit 앱에서만 작동)
    from .utils.style import apply_graph_themes, load_iot_font_css, apply_custom_style
    
    # 그래프 테마 적용 (Matplotlib, Plotly)
    apply_graph_themes()
    
    # 참고: load_iot_font_css와 apply_custom_style은 Streamlit 앱 실행 시
    # 메인 파일에서 직접 호출해야 합니다. (Streamlit 객체 필요)
except ImportError:
    pass  # Streamlit이 없는 환경에서는 무시

# 주요 함수 및 모듈 노출
from .main import main 