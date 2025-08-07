"""
PRD (생산이슈리포트) components for EcoPro iDSB.
This package contains various PRD-related components for maintenance, risk assessment,
statistics, images, chat, and search functionality.
"""

from components.prd.prd_maintenance import show_prd_maintenance
# from components.prd.prd_risk_assessment import show_prd_risk_assessment # Commented out
from components.prd.prd_chat import show_prd_chat
from components.prd.prd_images import show_prd_images, find_image_file
from components.prd.prd_search import show_prd_similar_search
from components.prd.prd_statistics import show_prd_statistics
from components.prd.prd_semantic import show_prd_semantic_analysis

# 데이터 로더 임포트 
from components.prd.prd_data_loader import (
    load_prd_data, create_documents, create_vector_db, 
    load_or_create_vector_db, find_image_file
)

__all__ = [
    'show_prd_maintenance',
    # 'show_prd_risk_assessment', # Commented out
    'show_prd_chat',
    'show_prd_images',
    'find_image_file',
    'show_prd_similar_search',
    'show_prd_statistics',
    'show_prd_semantic_analysis',
    
    'load_prd_data',
    'create_documents',
    'create_vector_db',
    'load_or_create_vector_db',
] 