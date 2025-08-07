"""
DX-AI Manufacturing Copilot - 탭별 챗봇 매니저

각 탭별로 전용 챗봇 매니저를 제공하여 Context 처리와 분석 보고서 생성을 분리합니다.
"""

from .process_lot_tracking_chat import LotTrackingChatManager
from .process_equipment_monitoring_chat import EquipmentMonitoringChatManager
from .process_anomaly_detection_chat import AnomalyDetectionChatManager
from .experiment_design_chat import ExperimentDesignChatManager
from .experiment_optimization_chat import OptimizationChatManager
from .experiment_report_chat import ExperimentReportChatManager
from .product_data_analysis_chat import ProductDataAnalysisChatManager
from .product_data_preprocessing_chat import ProductDataPreprocessingChatManager
from .product_modeling_chat import ProductModelingChatManager
from .product_report_chat import ProductReportChatManager
from .cost_management_chat import CostManagementChatManager
from .base_tab_chat import BaseTabChatManager

# 새로운 원가 관리 서브메뉴별 채팅 매니저들 추가
from .cost_analysis_chat import CostAnalysisChatManager
from .cost_optimization_chat import CostOptimizationChatManager
from .cost_sensitivity_chat import CostSensitivityChatManager
from .cost_quality_prediction_chat import CostQualityPredictionChatManager
from .cost_ai_analysis_chat import CostAIAnalysisChatManager

__all__ = [
    'LotTrackingChatManager',
    'EquipmentMonitoringChatManager', 
    'AnomalyDetectionChatManager',
    'ExperimentDesignChatManager',
    'OptimizationChatManager',
    'ExperimentReportChatManager',
    'ProductDataAnalysisChatManager',
    'ProductDataPreprocessingChatManager',
    'ProductModelingChatManager',
    'ProductReportChatManager',
    'CostManagementChatManager',
    'BaseTabChatManager',
    # 새로운 원가 관리 서브메뉴별 채팅 매니저들
    'CostAnalysisChatManager',
    'CostOptimizationChatManager',
    'CostSensitivityChatManager',
    'CostQualityPredictionChatManager',
    'CostAIAnalysisChatManager'
] 