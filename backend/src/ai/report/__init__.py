"""
AI 보고서 생성 시스템 v2.0
도메인별 특화 보고서 생성기 모음
"""

from .experimental_design_report_generator import (
    ExperimentalDesignReportGenerator,
    create_experimental_design_report_generator
)

__all__ = [
    'ExperimentalDesignReportGenerator',
    'create_experimental_design_report_generator'
]

__version__ = '2.0.0' 