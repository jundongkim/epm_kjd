"""
DX-AI Manufacturing Copilot - 페이지 모듈

각 기능별 페이지를 관리하는 모듈입니다.
"""

# from .home import main_home  # 더 이상 사용 안함 (Next.js로 이전)
# from .data_generation import data_generation_page  # 더 이상 사용 안함 (Next.js로 이전)
# from .process_management import process_management_page  # 더 이상 사용 안함 (Next.js로 이전)
# from .product_modeling import product_modeling_page  # 더 이상 사용 안함 (Next.js로 이전)
# from .experimental_design import experimental_design_page  # 더 이상 사용 안함 (Next.js로 이전)
from .cost_management import cost_management_page
from .ai_report import show_ai_report_page

__all__ = [
    # 'main_home',  # 더 이상 사용 안함 (Next.js로 이전)
    # 'data_generation_page',  # 더 이상 사용 안함 (Next.js로 이전)
    # 'process_management_page',  # 더 이상 사용 안함 (Next.js로 이전)
    # 'product_modeling_page',  # 더 이상 사용 안함 (Next.js로 이전)
    # 'experimental_design_page',  # 더 이상 사용 안함 (Next.js로 이전)
    'cost_management_page',
    'show_ai_report_page'
] 