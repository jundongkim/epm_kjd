"""
데이터 분석 및 처리 모듈 (guide_data)

이 패키지는 IoT 데이터 분석 가이드를 위한 데이터 분석 및 특성 파악과 관련된 기능을 제공합니다.
"""

from .analysis import analyze_data_characteristics
from .recommendations import ANALYSIS_RECOMMENDATIONS

__all__ = ['analyze_data_characteristics', 'ANALYSIS_RECOMMENDATIONS'] 