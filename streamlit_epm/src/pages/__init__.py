"""
DX-AI Manufacturing Copilot - 페이지 모듈

각 기능별 페이지를 관리하는 모듈입니다.
"""

from .home import main_home
from .data_generation import data_generation_page
from .process_management import process_management_page
from .product_data_analysis import product_data_analysis_page
from .product_modeling import product_modeling_page
from .experimental_design import experimental_design_page
from .cost_management import cost_management_page
from .ai_report import show_ai_report_page

__all__ = [
    'main_home',
    'data_generation_page', 
    'process_management_page',
    'product_data_analysis_page',
    'product_modeling_page',
    'experimental_design_page',
    'cost_management_page',
    'show_ai_report_page'
] 