"""
SEM-EDS 분석 모듈 패키지

이 패키지는 SEM(주사전자현미경) 이미지와 EDS(에너지 분산형 분광법) 스펙트럼을
분석하기 위한 기능을 제공합니다.
"""

from components.sem_eds.server import check_ollama_server
from components.sem_eds.file_utils import (
    create_sem_eds_folders,
    save_uploaded_file
)
from components.sem_eds.image_utils import (
    encode_image_to_base64,
    serialize_image,
    deserialize_image,
    process_uploaded_image
)
from components.sem_eds.analysis import (
    extract_image_info,
    generate_analysis_report,
    evaluate_report_quality
)
from components.sem_eds.ui import (
    show_sem_analysis,
    show_eds_analysis,
    show_operation_inference,
    show_equipment_inference
)

__all__ = [
    'check_ollama_server',
    'create_sem_eds_folders',
    'save_uploaded_file',
    'encode_image_to_base64',
    'serialize_image',
    'deserialize_image',
    'process_uploaded_image',
    'extract_image_info',
    'generate_analysis_report',
    'evaluate_report_quality',
    'show_sem_analysis',
    'show_eds_analysis',
    'show_operation_inference',
    'show_equipment_inference'
]