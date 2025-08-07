"""
DX-AI Manufacturing Copilot - 스마트 제조 솔루션

스마트 제조 공정 관리를 위한 AI 솔루션
"""

__version__ = "1.0.0"
__author__ = "DX-AI Manufacturing Copilot Team"
__email__ = "support@manufacturing-copilot.com"
__description__ = "DX-AI Manufacturing Copilot - 스마트 제조 공정 관리 AI 솔루션 프로토타입"

# 패키지 레벨 imports
from .copilot.config import settings
from .copilot.data_models import *

__all__ = [
    "settings",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
] 