"""
AI Advisor - 문서/임베딩 라우터 분리

기존 `routers/aiadvisor.py`에서 문서 처리 및 임베딩 관련 엔드포인트를 분리했습니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.aiadvisor import (
    DocumentProcessor,
    OntologyManager,
    OntologyGenerator,
    EmbeddingManager,
    AIAdvisorConfig,
    get_config as get_aiadvisor_config,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Advisor Documents"])


# 내부 의존성 (메인 라우터와 독립적으로 동작)
_config: Optional[AIAdvisorConfig] = None
_document_processor: Optional[DocumentProcessor] = None
_ontology_manager: Optional[OntologyManager] = None
_embedding_manager: Optional[EmbeddingManager] = None


async def get_config() -> AIAdvisorConfig:
    global _config
    if _config is None:
        _config = get_aiadvisor_config()
    return _config


async def get_document_processor() -> DocumentProcessor:
    global _document_processor
    if _document_processor is None:
        config = await get_config()
        _document_processor = DocumentProcessor(config)
    return _document_processor


async def get_ontology_manager() -> OntologyManager:
    global _ontology_manager
    if _ontology_manager is None:
        config = await get_config()
        _ontology_manager = OntologyManager(config)
    return _ontology_manager


async def get_embedding_manager() -> EmbeddingManager:
    global _embedding_manager
    if _embedding_manager is None:
        config = await get_config()
        _embedding_manager = EmbeddingManager(config)
    return _embedding_manager


class DocumentProcessRequest(BaseModel):
    file_paths: List[str]
    extract_ontology: bool = True
    create_embeddings: bool = True


class DocumentProcessResponse(BaseModel):
    processing_status: str
    processed_documents: List[Dict[str, Any]]
    total_processed: int
    failed_count: int


class EmbeddingRequest(BaseModel):
    processed_documents: List[Dict[str, Any]]
    index_name: str = "default"


class OntologyGenerationRequest(BaseModel):
    extraction_results: List[Dict[str, Any]]
    ontology_name: str = "default"


class OntologyGenerationResponse(BaseModel):
    generation_status: str
    ontology_path: str
    statistics: Dict[str, Any]


@router.post("/documents/process", response_model=DocumentProcessResponse)
async def process_documents(
    request: DocumentProcessRequest,
    processor: DocumentProcessor = Depends(get_document_processor),
):
    try:
        file_paths = []
        for path_str in request.file_paths:
            file_path = Path(path_str)
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {path_str}")
            file_paths.append(file_path)

        results = await processor.process_multiple_documents(file_paths)
        successful_results = [r for r in results if r.get("processing_status") == "completed"]
        failed_results = [r for r in results if r.get("processing_status") == "failed"]

        return DocumentProcessResponse(
            processing_status="completed",
            processed_documents=successful_results,
            total_processed=len(successful_results),
            failed_count=len(failed_results),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 처리 실패: {str(e)}")


@router.post("/embeddings/create")
async def create_embeddings(
    request: EmbeddingRequest,
    embedding_manager: EmbeddingManager = Depends(get_embedding_manager),
):
    try:
        result = await embedding_manager.create_embeddings(
            request.processed_documents, request.index_name
        )
        return result
    except Exception as e:
        logger.error(f"임베딩 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"임베딩 생성 실패: {str(e)}")


# 온톨로지 관리
@router.post("/ontology/generate", response_model=OntologyGenerationResponse)
async def generate_ontology(
    request: OntologyGenerationRequest,
    config: AIAdvisorConfig = Depends(get_aiadvisor_config),
):
    try:
        generator = OntologyGenerator(config)
        result = await generator.generate_ontology(request.extraction_results)
        if result["generation_status"] != "success":
            raise HTTPException(status_code=500, detail="온톨로지 생성 실패")
        ontology_path = await generator.save_ontology(f"{request.ontology_name}.ttl")
        return OntologyGenerationResponse(
            generation_status=result["generation_status"],
            ontology_path=ontology_path,
            statistics=result["statistics"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온톨로지 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"온톨로지 생성 실패: {str(e)}")


@router.get("/ontology/list")
async def list_ontologies(ontology_manager: OntologyManager = Depends(get_ontology_manager)):
    try:
        ontologies = ontology_manager.get_available_ontologies()
        return {"ontologies": ontologies, "total_count": len(ontologies)}
    except Exception as e:
        logger.error(f"온톨로지 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"온톨로지 목록 조회 실패: {str(e)}")


@router.post("/ontology/{ontology_name}/load")
async def load_ontology(
    ontology_name: str,
    ontology_manager: OntologyManager = Depends(get_ontology_manager),
    config: AIAdvisorConfig = Depends(get_aiadvisor_config),
):
    try:
        ontology_path = config.ontology_dir / f"{ontology_name}.ttl"
        success = await ontology_manager.load_ontology_file(ontology_path, ontology_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"온톨로지를 로드할 수 없습니다: {ontology_name}")
        return {
            "load_status": "success",
            "ontology_name": ontology_name,
            "loaded_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온톨로지 로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"온톨로지 로드 실패: {str(e)}")


@router.get("/ontology/{ontology_name}/statistics")
async def get_ontology_statistics(
    ontology_name: str, ontology_manager: OntologyManager = Depends(get_ontology_manager)
):
    try:
        stats = ontology_manager.get_ontology_statistics(ontology_name)
        if not stats:
            raise HTTPException(status_code=404, detail=f"온톨로지를 찾을 수 없습니다: {ontology_name}")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온톨로지 통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"온톨로지 통계 조회 실패: {str(e)}")


@router.get("/documents")
async def list_documents(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    document_processor: DocumentProcessor = Depends(get_document_processor),
):
    try:
        documents = await document_processor.list_documents(
            category=category, limit=limit, offset=offset
        )
        return {
            "documents": documents,
            "total_count": await document_processor.get_document_count(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"문서 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 목록 조회 실패: {str(e)}")


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    document_processor: DocumentProcessor = Depends(get_document_processor),
):
    try:
        document = await document_processor.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return document
    except Exception as e:
        logger.error(f"문서 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 조회 실패: {str(e)}")


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    document_processor: DocumentProcessor = Depends(get_document_processor),
):
    try:
        document = await document_processor.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

        file_path_str = document.get("file_path", "")
        filename = document.get("filename", f"document_{document_id}")
        safe_filename = document.get("safe_filename", filename)

        if file_path_str and file_path_str != "":
            file_path = Path(file_path_str)
            if not (file_path.exists() and file_path.is_file()):
                file_path = None
        else:
            file_path = None

        if file_path is None:
            upload_dir = Path("data/aiadvisor/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / safe_filename
            if not file_path.exists() or not file_path.is_file():
                found_files = list(upload_dir.glob(f"*{filename}"))
                if found_files:
                    file_path = found_files[0]
                else:
                    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    found_files = list(upload_dir.glob(f"*{base_name}*"))
                    if found_files:
                        file_path = found_files[0]

        if not file_path or not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="원본 파일을 찾을 수 없습니다.")

        original_filename = document.get("filename", f"document_{document_id}")
        return FileResponse(
            path=str(file_path), filename=original_filename, media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 다운로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"문서 다운로드 실패: {str(e)}")


