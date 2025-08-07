"""
DX-AI Advisor - 유틸리티 모듈

공통 설정, 예외 처리, 헬퍼 함수들을 제공합니다.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AIAdvisorException(Exception):
    """AI Advisor 모듈 전용 예외 클래스"""
    pass


class DocumentType(str, Enum):
    """지원되는 문서 타입"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"


class ProcessingStatus(str, Enum):
    """처리 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AIAdvisorConfig(BaseModel):
    """AI Advisor 모듈 설정"""
    
    # 기본 경로 설정
    data_dir: Path = Field(default_factory=lambda: Path("data/aiadvisor"))
    uploads_dir: Path = Field(default_factory=lambda: Path("data/aiadvisor/uploads"))
    processed_dir: Path = Field(default_factory=lambda: Path("data/aiadvisor/processed"))
    documents_dir: Path = Field(default_factory=lambda: Path("data/aiadvisor/documents"))
    vector_db_dir: Path = Field(default_factory=lambda: Path("data/aiadvisor/vector_db"))
    ontology_dir: Path = Field(default_factory=lambda: Path("data/aiadvisor/ontology"))
    reports_dir: Path = Field(default_factory=lambda: Path("data/aiadvisor/reports"))
    
    # LLM 설정
    default_llm_model: str = "gemma3:4b-it-qat"
    available_llm_models: Dict[str, str] = Field(default_factory=lambda: {
        "Gemma 3 (1B)": "gemma3:1b",
        "Gemma 3 (1B-QAT)": "gemma3:1b-it-qat",
        "Gemma 3 (4B)": "gemma3:4b",
        "Gemma 3 (4B-QAT)": "gemma3:4b-it-qat",
        "Gemma 3 (12B)": "gemma3:12b",
        "Gemma 3 (12B-QAT)": "gemma3:12b-it-qat",
        "Gemma 3 (27B)": "gemma3:27b",
        "Gemma 3 (27B-QAT)": "gemma3:27b-it-qat"
    })
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 300
    llm_temperature: float = 0.2
    
    # 임베딩 설정 (한국어 최적화)
    embedding_model: str = "jhgan/ko-sroberta-multitask"
    embedding_dimension: int = 768
    faiss_index_type: str = "flat"  # flat, ivf, hnsw
    
    # 문서 처리 설정 (한국어 최적화)
    supported_document_types: List[str] = Field(default_factory=lambda: ["pdf", "docx", "pptx", "txt", "md"])
    max_file_size_mb: int = 100
    chunk_size: int = 512
    chunk_overlap: int = 128
    
    # 온톨로지 설정
    ontology_namespace: str = "http://dxai.advisor/ontology#"
    entity_types: List[str] = Field(default_factory=lambda: [
        "Product", "Material", "Component", "Chemical", "Precursor", "Dopant",
        "Equipment", "Process", "ProcessLine", "Instrument", "Sensor", "Filter",
        "Defect", "FailureMode", "RootCause", "Contaminant", "Quality",
        "TestMethod", "AnalysisResult", "Measurement", "SamplePoint"
    ])
    relation_types: List[str] = Field(default_factory=lambda: [
        "caused_by", "resulted_in", "contributes_to",
        "processed_in", "used_in", "feeds_into", "operates_with",
        "detected_in", "exceeds_limit", "causes_defect",
        "reacts_with", "dissolves_in", "catalyzes",
        "maintained_by", "replaced_by", "calibrated_by"
    ])
    
    # 보고서 설정
    default_report_sections: List[str] = Field(default_factory=lambda: [
        "executive_summary",
        "situation_analysis", 
        "root_cause_analysis",
        "improvement_recommendations",
        "implementation_plan",
        "risk_assessment"
    ])
    
    def __init__(self, **data):
        super().__init__(**data)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리들을 생성합니다."""
        directories = [
            self.data_dir,
            self.uploads_dir,
            self.processed_dir,
            self.documents_dir,
            self.vector_db_dir,
            self.ontology_dir,
            self.reports_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    class Config:
        use_enum_values = True


def get_config() -> AIAdvisorConfig:
    """AI Advisor 설정 인스턴스를 반환합니다."""
    return AIAdvisorConfig()


def validate_file_type(filename: str, supported_types: List[str] = None) -> bool:
    """파일 타입이 지원되는지 확인합니다."""
    if supported_types is None:
        supported_types = get_config().supported_document_types
    
    file_extension = Path(filename).suffix.lower().lstrip('.')
    return file_extension in supported_types


def get_file_size_mb(file_path: Path) -> float:
    """파일 크기를 MB 단위로 반환합니다."""
    return file_path.stat().st_size / (1024 * 1024)


def sanitize_filename(filename: str) -> str:
    """파일명을 안전하게 정리합니다."""
    import re
    # 특수문자 제거 및 공백을 언더스코어로 변경
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.strip('_')


def format_processing_time(seconds: float) -> str:
    """처리 시간을 사용자 친화적 형식으로 포맷합니다."""
    if seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}분"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}시간"


def create_progress_tracker(total_steps: int) -> Dict[str, Any]:
    """진행률 추적기를 생성합니다."""
    return {
        "total_steps": total_steps,
        "current_step": 0,
        "progress_percentage": 0.0,
        "status": ProcessingStatus.PENDING,
        "messages": []
    }


def update_progress(tracker: Dict[str, Any], step: int, message: str = "") -> Dict[str, Any]:
    """진행률을 업데이트합니다."""
    tracker["current_step"] = step
    tracker["progress_percentage"] = (step / tracker["total_steps"]) * 100
    
    if step >= tracker["total_steps"]:
        tracker["status"] = ProcessingStatus.COMPLETED
    elif step > 0:
        tracker["status"] = ProcessingStatus.PROCESSING
    
    if message:
        tracker["messages"].append({
            "step": step,
            "message": message,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
    
    return tracker 