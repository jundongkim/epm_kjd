"""
DX-AI Advisor - AI 어드바이저 모듈

제조 현장 문서를 분석하여 공정 문제를 진단하고 해결책을 제시하는 AI 전문가 시스템
온톨로지 기반 지식 그래프와 고도화된 임베딩 검색을 통한 하이브리드 지식 관리
"""

from .document_processor import DocumentProcessor, DocumentParser, InformationExtractor
from .ontology import OntologyGenerator, OntologyManager
from .embedding import EmbeddingManager
from .search_engine import VectorSearchEngine
from .agent import AdvisorAgent, AdvisorAgentManager
from .source_tracker import SourceTracker, StreamingSourceTracker

from .utils import AIAdvisorConfig, AIAdvisorException, get_config

__version__ = "1.0.0"
__author__ = "DX-AI Manufacturing Copilot Team"
__description__ = "AI 어드바이저 - 온톨로지 기반 제조업 전문 AI 시스템"

__all__ = [
    # Document Processing
    "DocumentProcessor",
    "DocumentParser", 
    "InformationExtractor",
    
    # Ontology Management
    "OntologyGenerator",
    "OntologyManager",
    
    # Embedding & Search
    "EmbeddingManager",
    "VectorSearchEngine",
    
    # AI Agent
    "AdvisorAgent",
    "AdvisorAgentManager",
    
    # Source Tracking
    "SourceTracker",
    "StreamingSourceTracker",
    
    # Utilities
    "AIAdvisorConfig",
    "AIAdvisorException",
    "get_config",
    
    # Metadata
    "__version__",
    "__author__",
    "__description__"
] 