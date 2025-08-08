"""
DX-AI Advisor - 문서 처리 모듈

다양한 형식의 문서를 파싱하고 LLM을 통해 정보를 추출하는 모듈
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

# Document parsing libraries
import pdfplumber
from docx import Document as DocxDocument
from pptx import Presentation
import fitz  # PyMuPDF

# AI/ML libraries
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate

# Internal imports
from .utils import AIAdvisorConfig, get_config, AIAdvisorException, sanitize_filename, validate_file_type
from ..ai.core.llm_client import get_ollama_client

logger = logging.getLogger(__name__)


class DocumentParser:
    """문서 파싱 클래스 - 다양한 형식의 문서를 텍스트로 변환"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
    
    async def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """파일을 파싱하여 텍스트와 메타데이터 추출"""
        try:
            if not file_path.exists():
                raise AIAdvisorException(f"파일을 찾을 수 없습니다: {file_path}")
            
            # 파일 타입 검증
            if not validate_file_type(file_path.name):
                raise AIAdvisorException(f"지원하지 않는 파일 형식입니다: {file_path.suffix}")
            
            file_extension = file_path.suffix.lower()
            
            # 파일 기본 정보
            stat = file_path.stat()
            base_metadata = {
                "filename": file_path.name,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_type": file_extension.lstrip('.')
            }
            
            # 파일 타입별 파싱
            if file_extension == '.pdf':
                content, metadata = await self._parse_pdf(file_path)
            elif file_extension == '.docx':
                content, metadata = await self._parse_docx(file_path)
            elif file_extension == '.pptx':
                content, metadata = await self._parse_pptx(file_path)
            elif file_extension in ['.txt', '.md']:
                content, metadata = await self._parse_text(file_path)
            else:
                raise AIAdvisorException(f"지원하지 않는 파일 형식: {file_extension}")
            
            # 메타데이터 병합
            combined_metadata = {**base_metadata, **metadata}
            
            # 텍스트 청킹
            chunks = await self._create_chunks(content, combined_metadata)
            
            return {
                "content": content,
                "metadata": combined_metadata,
                "chunks": chunks,
                "parsing_status": "success"
            }
            
        except Exception as e:
            logger.error(f"파일 파싱 오류 - {file_path}: {str(e)}")
            raise AIAdvisorException(f"파일 파싱 중 오류 발생: {str(e)}")
    
    async def _parse_pdf(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """PDF 파일 파싱 (PyMuPDF 우선, 성능 최적화)"""
        content = ""
        metadata = {}
        
        # PyMuPDF를 우선 사용 (더 빠르고 안정적)
        try:
            pdf_document = fitz.open(file_path)
            metadata["page_count"] = len(pdf_document)
            
            # PDF 메타데이터 추출
            pdf_info = pdf_document.metadata
            if pdf_info:
                metadata.update({
                    "title": pdf_info.get("title", ""),
                    "author": pdf_info.get("author", ""),
                    "subject": pdf_info.get("subject", ""),
                    "creator": pdf_info.get("creator", ""),
                    "producer": pdf_info.get("producer", ""),
                    "creation_date": str(pdf_info.get("creationDate", "")),
                    "modification_date": str(pdf_info.get("modDate", ""))
                })
            
            # 텍스트 추출 (성능 최적화)
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # 텍스트 추출
                page_text = page.get_text()
                if page_text and page_text.strip():
                    content += f"\n\n--- 페이지 {page_num + 1} ---\n{page_text.strip()}"
                
                # 표 데이터 추출 (PyMuPDF의 표 추출 기능)
                try:
                    tables = page.get_tables()
                    if tables:
                        for table_idx, table in enumerate(tables):
                            if table and any(any(cell for cell in row if cell) for row in table):
                                content += f"\n\n[표 {page_num + 1}-{table_idx + 1}]\n"
                                for row in table:
                                    if row and any(cell for cell in row if cell):
                                        row_text = " | ".join(str(cell or "").strip() for cell in row)
                                        if row_text.strip():
                                            content += row_text + "\n"
                except Exception as table_error:
                    logger.warning(f"표 추출 실패 (페이지 {page_num + 1}): {str(table_error)}")
            
            pdf_document.close()
            
        except Exception as e:
            # pdfplumber로 대체 시도
            try:
                with pdfplumber.open(file_path) as pdf:
                    # PDF 메타데이터 추출
                    pdf_info = pdf.metadata or {}
                    metadata.update({
                        "title": pdf_info.get("Title", ""),
                        "author": pdf_info.get("Author", ""),
                        "subject": pdf_info.get("Subject", ""),
                        "creator": pdf_info.get("Creator", ""),
                        "producer": pdf_info.get("Producer", ""),
                        "creation_date": str(pdf_info.get("CreationDate", "")),
                        "modification_date": str(pdf_info.get("ModDate", "")),
                        "page_count": len(pdf.pages)
                    })
                    
                    # 텍스트 추출
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            content += f"\n\n--- 페이지 {page_num} ---\n{page_text}"
                            
                            # 표 데이터 추출 시도
                            tables = page.extract_tables()
                            if tables:
                                for table_idx, table in enumerate(tables):
                                    content += f"\n\n[표 {page_num}-{table_idx + 1}]\n"
                                    for row in table:
                                        if row and any(cell for cell in row if cell):
                                            content += " | ".join(str(cell or "") for cell in row) + "\n"
            except Exception as fallback_error:
                raise AIAdvisorException(f"PDF 파싱 실패: PyMuPDF 오류 - {str(e)}, pdfplumber 대체 방법도 실패 - {str(fallback_error)}")
        
        return content.strip(), metadata
    
    async def _parse_docx(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """DOCX 파일 파싱"""
        try:
            doc = DocxDocument(file_path)
            
            # 메타데이터 추출
            core_props = doc.core_properties
            metadata = {
                "title": core_props.title or "",
                "author": core_props.author or "",
                "subject": core_props.subject or "",
                "keywords": core_props.keywords or "",
                "comments": core_props.comments or "",
                "created": str(core_props.created) if core_props.created else "",
                "modified": str(core_props.modified) if core_props.modified else "",
                "paragraph_count": len(doc.paragraphs)
            }
            
            # 텍스트 추출
            content = ""
            for para in doc.paragraphs:
                if para.text.strip():
                    content += para.text + "\n"
            
            # 표 데이터 추출
            for table_idx, table in enumerate(doc.tables):
                content += f"\n\n[표 {table_idx + 1}]\n"
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    if any(row_data):
                        content += " | ".join(row_data) + "\n"
            
            return content.strip(), metadata
            
        except Exception as e:
            raise AIAdvisorException(f"DOCX 파싱 실패: {str(e)}")
    
    async def _parse_pptx(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """PPTX 파일 파싱"""
        try:
            prs = Presentation(file_path)
            
            # 메타데이터 추출
            core_props = prs.core_properties
            metadata = {
                "title": core_props.title or "",
                "author": core_props.author or "",
                "subject": core_props.subject or "",
                "keywords": core_props.keywords or "",
                "comments": core_props.comments or "",
                "created": str(core_props.created) if core_props.created else "",
                "modified": str(core_props.modified) if core_props.modified else "",
                "slide_count": len(prs.slides)
            }
            
            # 텍스트 추출
            content = ""
            for slide_idx, slide in enumerate(prs.slides, 1):
                content += f"\n\n--- 슬라이드 {slide_idx} ---\n"
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        content += shape.text + "\n"
                    
                    # 표 데이터 추출
                    if shape.has_table:
                        content += "\n[표]\n"
                        table = shape.table
                        for row in table.rows:
                            row_data = [cell.text.strip() for cell in row.cells]
                            if any(row_data):
                                content += " | ".join(row_data) + "\n"
            
            return content.strip(), metadata
            
        except Exception as e:
            raise AIAdvisorException(f"PPTX 파싱 실패: {str(e)}")
    
    async def _parse_text(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """텍스트 파일 파싱"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            metadata = {
                "character_count": len(content),
                "line_count": len(content.splitlines()),
                "word_count": len(content.split())
            }
            
            return content, metadata
            
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            try:
                with open(file_path, 'r', encoding='cp949') as file:
                    content = file.read()
                
                metadata = {
                    "character_count": len(content),
                    "line_count": len(content.splitlines()),
                    "word_count": len(content.split()),
                    "encoding": "cp949"
                }
                
                return content, metadata
            except Exception as e:
                raise AIAdvisorException(f"텍스트 파일 인코딩 오류: {str(e)}")
        except Exception as e:
            raise AIAdvisorException(f"텍스트 파일 파싱 실패: {str(e)}")
    
    async def _create_chunks(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """텍스트를 청크로 분할 (한국어 최적화, 성능 개선)"""
        # 내용이 너무 짧으면 청킹하지 않음
        if len(content.strip()) < 100:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_id": 0,
                "chunk_size": len(content),
                "total_chunks": 1,
                "chunk_quality_score": self._calculate_chunk_quality(content)
            })
            return [{
                "content": content.strip(),
                "metadata": chunk_metadata
            }]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=[
                "\n\n",        # 문단 구분
                "\n",          # 줄바꿈
                "。", ".",      # 문장 끝 (일본식, 서양식)
                "!", "?",     # 감탄부, 의문부
                "、", ",",      # 콤마 (일본식, 서양식)
                "；", ";",      # 세미콜론
                " ",           # 공백
                ""
            ]
        )
        
        chunks = text_splitter.split_text(content)
        
        # 빈 청크 제거 및 품질 필터링 (성능 최적화)
        filtered_chunks = []
        for chunk in chunks:
            chunk_stripped = chunk.strip()
            # 최소 길이 및 의미있는 내용 확인 (개선된 조건)
            if (len(chunk_stripped) >= 30 and 
                any(c.isalnum() or ord(c) > 127 for c in chunk_stripped) and
                not chunk_stripped.isspace()):
                filtered_chunks.append(chunk_stripped)
        
        # 청크 수가 너무 많으면 품질 기준으로 필터링
        if len(filtered_chunks) > 50:
            quality_chunks = []
            for chunk in filtered_chunks:
                quality_score = self._calculate_chunk_quality(chunk)
                if quality_score > 0.4:  # 품질 기준 완화
                    quality_chunks.append((chunk, quality_score))
            
            # 품질 점수로 정렬하여 상위 청크만 선택
            quality_chunks.sort(key=lambda x: x[1], reverse=True)
            filtered_chunks = [chunk for chunk, _ in quality_chunks[:50]]
        
        chunk_documents = []
        for i, chunk in enumerate(filtered_chunks):
            chunk_metadata = metadata.copy()
            quality_score = self._calculate_chunk_quality(chunk)
            chunk_metadata.update({
                "chunk_id": i,
                "chunk_size": len(chunk),
                "total_chunks": len(filtered_chunks),
                "chunk_quality_score": quality_score
            })
            
            chunk_documents.append({
                "content": chunk,
                "metadata": chunk_metadata
            })
        
        return chunk_documents
    
    def _calculate_chunk_quality(self, chunk: str) -> float:
        """청크 품질 점수 계산 (개선된 버전)"""
        try:
            if not chunk or len(chunk.strip()) == 0:
                return 0.0
            
            score = 0.0
            chunk_clean = chunk.strip()
            
            # 1. 기본 길이 점수 (최적화된 계산)
            length = len(chunk_clean)
            if length < 20:
                return 0.1  # 너무 짧은 청크는 낮은 점수
            elif length < 100:
                length_score = length / 100
            else:
                length_score = min(length / 500, 1.0)  # 500자 기준으로 조정
            score += length_score * 0.25
            
            # 2. 한글 비율 (제조업 문서에서 중요)
            korean_chars = sum(1 for c in chunk_clean if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
            korean_ratio = korean_chars / length if length > 0 else 0
            score += korean_ratio * 0.3
            
            # 3. 문장 구조 점수 (개선된 계산)
            sentence_markers = (chunk_clean.count('.') + chunk_clean.count('。') + 
                              chunk_clean.count('!') + chunk_clean.count('?') +
                              chunk_clean.count('\n'))
            structure_score = min(sentence_markers / 2, 1.0)  # 기준 완화
            score += structure_score * 0.2
            
            # 4. 기술적 내용 점수 (제조업 특화)
            # 숫자와 영문 혼재
            has_digits = any(c.isdigit() for c in chunk_clean)
            has_letters = any(c.isalpha() for c in chunk_clean)
            if has_digits and has_letters:
                score += 0.15
            
            # 5. 특수 용어 및 키워드 점수
            technical_terms = ['품질', '공정', '설비', '검사', '측정', '관리', '표준', '규격', 
                             '불량', '개선', '분석', '데이터', '시스템', '프로세스', '제조']
            term_count = sum(1 for term in technical_terms if term in chunk_clean)
            term_score = min(term_count / 3, 1.0) * 0.1
            score += term_score
            
            # 6. 가독성 점수 (공백과 문장 부호 비율)
            readable_chars = sum(1 for c in chunk_clean if c.isspace() or c in '.,;:!?()[]{}')
            readability_ratio = readable_chars / length if length > 0 else 0
            if 0.1 <= readability_ratio <= 0.3:  # 적절한 가독성 범위
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.warning(f"청크 품질 계산 오류: {str(e)}")
            return 0.5  # 기본값


class InformationExtractor:
    """LLM을 사용한 정보 추출 클래스"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
        self.llm_client = None
    
    async def initialize(self):
        """LLM 클라이언트 초기화"""
        if not self.llm_client:
            self.llm_client = get_ollama_client(service_context="aiadvisor")
    
    async def extract_information(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """문서에서 주요 정보 추출"""
        await self.initialize()
        
        try:
            # 메타데이터 추출
            metadata_info = await self._extract_metadata(content)
            
            # 온톨로지 정보 추출
            ontology_info = await self._extract_ontology_information(content)
            
            # 구조화 데이터 추출
            structured_info = await self._extract_structured_data(content)
            
            return {
                "extracted_metadata": metadata_info,
                "ontology_information": ontology_info,
                "structured_data": structured_info,
                "extraction_status": "success",
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"정보 추출 오류: {str(e)}")
            raise AIAdvisorException(f"정보 추출 중 오류 발생: {str(e)}")
    
    async def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """메타데이터 추출"""
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""다음 문서에서 메타데이터를 추출해주세요.

문서 내용:
{content}

다음 정보를 JSON 형식으로 추출해주세요:
- title: 문서 제목
- keywords: 주요 키워드 (리스트)
- summary: 문서 요약 (2-3문장)
- main_topics: 주요 주제들 (리스트)
- document_type: 문서 유형 (보고서, 매뉴얼, 기술문서 등)
- language: 언어

JSON 형식으로만 응답해주세요."""
        )
        
        try:
            response = await self.llm_client.llm.ainvoke(prompt.format(content=content[:3000]))  # 토큰 제한
            
            # JSON 파싱 시도
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # JSON 부분만 추출
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                logger.warning("메타데이터 추출 응답에서 JSON을 찾을 수 없음")
                return {}
                
        except Exception as e:
            logger.error(f"메타데이터 추출 오류: {str(e)}")
            return {}
    
    async def _extract_ontology_information(self, content: str) -> Dict[str, Any]:
        """온톨로지 정보 추출"""
        prompt = PromptTemplate(
            input_variables=["content", "entity_types", "relation_types"],
            template="""다음 제조업 문서에서 온톨로지 정보를 추출해주세요.

문서 내용:
{content}

엔티티 타입들: {entity_types}
관계 타입들: {relation_types}

다음 형식의 JSON으로 추출해주세요:
{{
    "entities": [
        {{"name": "엔티티명", "type": "엔티티타입", "description": "설명"}},
        ...
    ],
    "relations": [
        {{"subject": "주체엔티티", "predicate": "관계타입", "object": "객체엔티티", "confidence": 0.8}},
        ...
    ]
}}

JSON 형식으로만 응답해주세요."""
        )
        
        try:
            formatted_prompt = prompt.format(
                content=content[:4000],  # 토큰 제한
                entity_types=", ".join(self.config.entity_types[:10]),  # 처음 10개만
                relation_types=", ".join(self.config.relation_types[:10])  # 처음 10개만
            )
            
            response = await self.llm_client.llm.ainvoke(formatted_prompt)
            
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # JSON 파싱
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"entities": [], "relations": []}
                
        except Exception as e:
            logger.error(f"온톨로지 정보 추출 오류: {str(e)}")
            return {"entities": [], "relations": []}
    
    async def _extract_structured_data(self, content: str) -> Dict[str, Any]:
        """구조화 데이터 추출"""
        prompt = PromptTemplate(
            input_variables=["content"],
            template="""다음 문서에서 구조화된 데이터를 추출해주세요.

문서 내용:
{content}

다음 정보를 JSON 형식으로 추출해주세요:
- tables: 표 데이터들 (있는 경우)
- lists: 목록들 (번호나 불릿 포인트)
- key_values: 주요 키-값 쌍들
- measurements: 측정값, 수치 데이터
- dates: 중요한 날짜들
- locations: 위치 정보

JSON 형식으로만 응답해주세요."""
        )
        
        try:
            response = await self.llm_client.llm.ainvoke(prompt.format(content=content[:3000]))
            
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # JSON 파싱
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            logger.error(f"구조화 데이터 추출 오류: {str(e)}")
            return {}


class DocumentProcessor:
    """문서 처리 통합 클래스"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
        self.parser = DocumentParser(config)
        self.extractor = InformationExtractor(config)
    
    async def process_document(self, file_path: Path) -> Dict[str, Any]:
        """문서를 전체적으로 처리"""
        try:
            # 1. 문서 파싱
            parsing_result = await self.parser.parse_file(file_path)
            
            # 2. 정보 추출
            extraction_result = await self.extractor.extract_information(
                parsing_result["content"],
                parsing_result["metadata"]
            )
            
            # 3. 결과 통합
            processed_result = {
                "file_info": {
                    "original_path": str(file_path),
                    "filename": file_path.name,
                    "processed_at": datetime.now().isoformat()
                },
                "parsing": parsing_result,
                "extraction": extraction_result,
                "processing_status": "completed"
            }
            
            # 4. 결과 저장
            await self._save_processed_result(processed_result, file_path)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"문서 처리 실패 - {file_path}: {str(e)}")
            error_result = {
                "file_info": {
                    "original_path": str(file_path),
                    "filename": file_path.name,
                    "processed_at": datetime.now().isoformat()
                },
                "processing_status": "failed",
                "error": str(e)
            }
            return error_result

    async def process_document_content(self, filename: str, content: bytes, category: str = "general", description: str = "") -> Dict[str, Any]:
        """파일 내용을 직접 처리 (업로드된 파일용, 메모리 최적화)"""
        document_id = None
        temp_file = None
        
        try:
            # 문서 ID 생성
            import uuid
            document_id = str(uuid.uuid4())
            
            # uploads 폴더에 원본 파일 저장
            uploads_dir = Path("data/aiadvisor/uploads")
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # 원본 파일명 사용 (중복 방지를 위해 timestamp 추가)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 파일명과 확장자 분리
            if '.' in filename:
                name_part, ext_part = filename.rsplit('.', 1)
                safe_filename = f"{name_part}_{timestamp}.{ext_part}"
            else:
                safe_filename = f"{filename}_{timestamp}"
                
            uploaded_file = uploads_dir / safe_filename
            
            # 원본 파일 저장
            with open(uploaded_file, 'wb') as f:
                f.write(content)
            
            # 임시 파일 생성 (파싱용)
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            temp_file = temp_dir / f"temp_{document_id}_{filename}"
            
            # 임시 파일에 내용 저장
            with open(temp_file, 'wb') as f:
                f.write(content)
            
            # 원본 content 메모리 해제
            del content
            
            # 1. 문서 파싱 (메모리 효율적 처리)
            parsing_result = await self.parser.parse_file(temp_file)
            
            # 2. 정보 추출 (내용이 너무 크면 일부만 사용)
            content_for_extraction = parsing_result["content"]
            if len(content_for_extraction) > 10000:  # 10KB 제한
                content_for_extraction = content_for_extraction[:10000] + "..."
            
            extraction_result = await self.extractor.extract_information(
                content_for_extraction,
                parsing_result["metadata"]
            )
            
            # 3. 결과 통합 (메모리 효율적)
            processed_result = {
                "document_id": document_id,
                "file_info": {
                    "original_filename": filename,
                    "filename": filename,
                    "safe_filename": safe_filename,
                    "file_path": str(uploaded_file),
                    "processed_at": datetime.now().isoformat(),
                    "category": category,
                    "description": description,
                    "file_size": len(content_for_extraction)
                },
                "parsing": {
                    "content_length": len(parsing_result["content"]),
                    "metadata": parsing_result["metadata"],
                    "chunks_count": len(parsing_result.get("chunks", [])),
                    "parsing_status": parsing_result.get("parsing_status", "success")
                },
                "extraction": extraction_result,
                "processing_status": "completed",
                "sections": parsing_result.get("chunks", [])[:20],  # 상위 20개만 저장
                "entities": extraction_result.get("ontology_information", {}).get("entities", [])[:50]  # 상위 50개만 저장
            }
            
            # 4. 결과 저장
            await self._save_processed_result(processed_result, temp_file)
            
            # 메모리 정리
            import gc
            del parsing_result
            del extraction_result
            del content_for_extraction
            gc.collect()
            
            return processed_result
            
        except Exception as e:
            logger.error(f"문서 내용 처리 실패 - {filename}: {str(e)}")
            error_result = {
                "document_id": document_id if document_id else str(uuid.uuid4()),
                "file_info": {
                    "original_filename": filename,
                    "filename": filename,
                    "processed_at": datetime.now().isoformat(),
                    "category": category,
                    "description": description
                },
                "processing_status": "failed",
                "error": str(e)
            }
            return error_result
            
        finally:
            # 임시 파일 삭제
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"임시 파일 삭제 실패: {str(e)}")
            
            # 메모리 정리
            import gc
            gc.collect()
    
    async def _save_processed_result(self, result: Dict[str, Any], original_path: Path):
        """처리 결과를 저장"""
        try:
            # 문서 ID를 사용하여 저장
            document_id = result.get("document_id", original_path.stem)
            sanitized_name = sanitize_filename(document_id)
            
            # documents_dir에 저장 (문서 목록 조회를 위해)
            output_path = self.config.documents_dir / f"{sanitized_name}.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"처리 결과 저장됨: {output_path}")
            
        except Exception as e:
            logger.error(f"처리 결과 저장 실패: {str(e)}")
    
    async def process_multiple_documents(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """여러 문서 처리"""
        results = []
        
        for file_path in file_paths:
            try:
                result = await self.process_document(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"문서 처리 실패 - {file_path}: {str(e)}")
                results.append({
                    "file_path": str(file_path),
                    "processing_status": "failed",
                    "error": str(e)
                })
        
        return results

    async def list_documents(self, category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """업로드된 문서 목록 조회"""
        try:
            documents_dir = self.config.documents_dir
            if not documents_dir.exists():
                return []
            
            documents = []
            for file_path in documents_dir.iterdir():
                if file_path.is_file() and file_path.suffix in ['.json']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            doc_data = json.load(f)
                            
                        # 카테고리 필터링
                        if category and doc_data.get('file_info', {}).get('category') != category:
                            continue
                            
                        # 문서 요약 생성
                        summary = self._generate_document_summary(doc_data)
                        
                        documents.append({
                            "document_id": file_path.stem,
                            "filename": doc_data.get('file_info', {}).get('original_filename', file_path.name),
                            "category": doc_data.get('file_info', {}).get('category', 'general'),
                            "description": doc_data.get('file_info', {}).get('description', ''),
                            "uploaded_at": doc_data.get('file_info', {}).get('processed_at', ''),
                            "file_size": doc_data.get('file_info', {}).get('file_size', 0),
                            "processing_status": doc_data.get('processing_status', 'unknown'),
                            "processed_sections": len(doc_data.get('sections', [])),
                            "extracted_entities": len(doc_data.get('entities', [])),
                            "summary": summary
                        })
                    except Exception as e:
                        logger.warning(f"문서 정보 읽기 실패 - {file_path}: {str(e)}")
                        continue
            
            # 정렬 (최신순)
            documents.sort(key=lambda x: x.get('uploaded_at', ''), reverse=True)
            
            # 페이지네이션
            return documents[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"문서 목록 조회 오류: {str(e)}")
            return []

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """특정 문서 상세 정보 조회"""
        try:
            document_path = self.config.documents_dir / f"{document_id}.json"
            if not document_path.exists():
                return None
            
            with open(document_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            # 다운로드를 위한 정보 추가
            file_info = doc_data.get('file_info', {})
            result = {
                'document_id': document_id,
                'filename': file_info.get('original_filename', file_info.get('filename', document_id)),
                'safe_filename': file_info.get('safe_filename', file_info.get('filename', document_id)),
                'file_path': file_info.get('file_path', ''),
                'category': file_info.get('category', 'general'),
                'description': file_info.get('description', ''),
                'file_size': file_info.get('file_size', 0),
                'processed_at': file_info.get('processed_at', ''),
                'processing_status': doc_data.get('processing_status', 'unknown'),
                'sections': doc_data.get('sections', []),
                'entities': doc_data.get('entities', [])
            }
            
            return result
                
        except Exception as e:
            logger.error(f"문서 조회 오류 - {document_id}: {str(e)}")
            return None

    async def delete_document(self, document_id: str, embedding_manager=None) -> bool:
        """문서 삭제 (벡터DB 연동)"""
        try:
            document_path = self.config.documents_dir / f"{document_id}.json"
            if not document_path.exists():
                logger.warning(f"삭제할 문서를 찾을 수 없음: {document_id}")
                return False
            
            logger.info(f"문서 삭제 시작: {document_id}")
            
            # 1. 문서 정보 읽기
            doc_data = None
            try:
                with open(document_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
            except Exception as read_error:
                logger.error(f"문서 정보 읽기 실패: {str(read_error)}")
            
            # 2. 벡터DB에서 삭제
            if embedding_manager:
                try:
                    logger.info(f"벡터DB에서 문서 삭제 시도: {document_id}")
                    vector_deleted = await embedding_manager.remove_document(document_id)
                    if vector_deleted:
                        logger.info(f"✅ 벡터DB에서 문서 삭제 성공: {document_id}")
                    else:
                        logger.warning(f"⚠️ 벡터DB에서 문서 삭제 실패: {document_id}")
                except Exception as vector_error:
                    logger.error(f"벡터DB 삭제 중 오류: {str(vector_error)}")
            
            # 3. uploads 폴더에서 실제 파일 삭제
            if doc_data:
                file_info = doc_data.get('file_info', {})
                original_filename = file_info.get('original_filename')
                safe_filename = file_info.get('safe_filename')
                file_path = file_info.get('file_path')
                
                # 1차: file_path로 직접 삭제 시도
                if file_path:
                    try:
                        file_path_obj = Path(file_path)
                        if file_path_obj.exists():
                            file_path_obj.unlink()
                            logger.info(f"✅ 파일 삭제 성공 (file_path): {file_path}")
                        else:
                            logger.warning(f"⚠️ 파일 경로가 존재하지 않음: {file_path}")
                    except Exception as e:
                        logger.error(f"❌ file_path로 삭제 실패: {str(e)}")
                
                # 2차: safe_filename으로 uploads 폴더에서 삭제 시도
                if safe_filename:
                    try:
                        upload_dir = Path("data/aiadvisor/uploads")
                        upload_path = upload_dir / safe_filename
                        if upload_path.exists():
                            upload_path.unlink()
                            logger.info(f"✅ 파일 삭제 성공 (safe_filename): {upload_path}")
                        else:
                            logger.warning(f"⚠️ safe_filename으로 파일을 찾을 수 없음: {upload_path}")
                    except Exception as e:
                        logger.error(f"❌ safe_filename으로 삭제 실패: {str(e)}")
                
                # 3차: 패턴 매칭으로 파일 찾아서 삭제 (백업)
                if original_filename:
                    try:
                        upload_dir = Path("data/aiadvisor/uploads")
                        found_files = list(upload_dir.glob(f"*{original_filename}"))
                        for found_file in found_files:
                            found_file.unlink()
                            logger.info(f"✅ 파일 삭제 성공 (패턴 매칭): {found_file}")
                    except Exception as e:
                        logger.error(f"❌ 패턴 매칭 삭제 실패: {str(e)}")
                
                # 4차: documents 폴더에서도 찾기 (이전 방식 호환)
                if original_filename:
                    try:
                        doc_dir_path = self.config.documents_dir / original_filename
                        if doc_dir_path.exists():
                            doc_dir_path.unlink()
                            logger.info(f"✅ 문서 폴더에서 파일 삭제: {doc_dir_path}")
                    except Exception as e:
                        logger.error(f"❌ documents 폴더 삭제 실패: {str(e)}")
            
            # 4. JSON 메타데이터 파일 삭제
            document_path.unlink()
            logger.info(f"메타데이터 파일 삭제: {document_path}")
            
            logger.info(f"✅ 문서 삭제 완료: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 문서 삭제 오류 - {document_id}: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return False

    def _generate_document_summary(self, doc_data: Dict[str, Any]) -> str:
        """문서 요약 생성 (고도화된 버전)"""
        try:
            # 1. 기본 정보 추출
            file_info = doc_data.get('file_info', {})
            filename = file_info.get('original_filename', '알 수 없는 문서')
            category = file_info.get('category', 'general')
            file_size = file_info.get('file_size', 0)
            
            # 2. 추출된 정보 활용
            extraction_info = doc_data.get('extraction', {})
            extracted_metadata = extraction_info.get('extracted_metadata', {})
            
            # 3. 우선순위 기반 요약 생성
            summary_parts = []
            
            # 3-1. LLM이 추출한 요약이 있으면 우선 사용
            if extracted_metadata.get('summary'):
                llm_summary = extracted_metadata['summary'].strip()
                if len(llm_summary) > 10:  # 의미있는 요약인지 확인
                    summary_parts.append(llm_summary)
            
            # 3-2. 주요 키워드가 있으면 추가
            keywords = extracted_metadata.get('keywords', [])
            if keywords and isinstance(keywords, list):
                keyword_text = ", ".join(keywords[:5])  # 상위 5개만
                if keyword_text:
                    summary_parts.append(f"주요 키워드: {keyword_text}")
            
            # 3-3. 주요 주제가 있으면 추가
            main_topics = extracted_metadata.get('main_topics', [])
            if main_topics and isinstance(main_topics, list):
                topic_text = ", ".join(main_topics[:3])  # 상위 3개만
                if topic_text:
                    summary_parts.append(f"주요 주제: {topic_text}")
            
            # 3-4. 문서 내용에서 직접 추출 (LLM 요약이 없는 경우)
            if not summary_parts:
                sections = doc_data.get('sections', [])
                parsing_info = doc_data.get('parsing', {})
                chunks = parsing_info.get('chunks', sections)
                
                if chunks:
                    # 품질 점수가 높은 청크들을 우선 선택
                    quality_chunks = []
                    for chunk in chunks:
                        quality_score = chunk.get('metadata', {}).get('chunk_quality_score', 0.5)
                        if quality_score > 0.6:  # 품질 점수가 높은 청크만
                            quality_chunks.append(chunk)
                    
                    # 품질 높은 청크가 없으면 전체 청크 사용
                    if not quality_chunks:
                        quality_chunks = chunks[:5]  # 상위 5개만
                    
                    # 청크 내용 추출 및 정리
                    content_parts = []
                    total_chars = 0
                    max_chars = 600
                    
                    for chunk in quality_chunks:
                        content = chunk.get('content', '').strip()
                        if content:
                            # 불필요한 공백과 줄바꿈 정리
                            content = ' '.join(content.split())
                            
                            # 너무 긴 내용은 자르기
                            if len(content) > 150:
                                content = content[:150] + "..."
                            
                            content_parts.append(content)
                            total_chars += len(content)
                            
                            if total_chars > max_chars:
                                break
                    
                    if content_parts:
                        # 첫 번째와 마지막 청크를 조합하여 요약
                        if len(content_parts) > 1:
                            summary_content = f"{content_parts[0]} ... {content_parts[-1]}"
                        else:
                            summary_content = content_parts[0]
                        
                        # 최종 길이 제한
                        if len(summary_content) > 400:
                            summary_content = summary_content[:400] + "..."
                        
                        summary_parts.append(summary_content)
            
            # 4. 최종 요약 조합
            if summary_parts:
                # 첫 번째 요소가 주요 요약이 되도록
                main_summary = summary_parts[0]
                
                # 추가 정보가 있으면 부가 정보로 추가
                additional_info = []
                for part in summary_parts[1:]:
                    if len(part) < 100:  # 짧은 부가 정보만
                        additional_info.append(part)
                
                if additional_info:
                    combined_summary = f"{main_summary} | {' | '.join(additional_info)}"
                else:
                    combined_summary = main_summary
            else:
                # 요약을 생성할 수 없는 경우 기본 정보만
                combined_summary = f"문서 내용을 분석할 수 없습니다."
            
            # 5. 최종 요약 반환 (길이 제한)
            chunk_count = len(doc_data.get('sections', []))
            final_summary = f"[{category}] {filename} ({self._format_file_size(file_size)}, {chunk_count}개 섹션) - {combined_summary}"
            
            # 최대 길이 제한 (500자)
            if len(final_summary) > 500:
                final_summary = final_summary[:500] + "..."
            
            return final_summary
                
        except Exception as e:
            logger.error(f"문서 요약 생성 오류: {str(e)}")
            # 오류 발생 시 기본 정보만 반환
            try:
                file_info = doc_data.get('file_info', {})
                filename = file_info.get('original_filename', '알 수 없는 문서')
                return f"{filename} - 요약 생성 실패"
            except:
                return "요약 생성 실패"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """파일 크기를 사람이 읽기 쉬운 형식으로 변환"""
        try:
            if size_bytes < 1024:
                return f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f}KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f}MB"
        except:
            return "0B"
    
    async def get_document_count(self, category: Optional[str] = None) -> int:
        """문서 개수 조회"""
        try:
            documents_dir = self.config.documents_dir
            if not documents_dir.exists():
                return 0
            
            count = 0
            for file_path in documents_dir.iterdir():
                if file_path.is_file() and file_path.suffix in ['.json']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            doc_data = json.load(f)
                            
                        # 카테고리 필터링
                        if category and doc_data.get('file_info', {}).get('category') != category:
                            continue
                            
                        count += 1
                    except:
                        continue
            
            return count
            
        except Exception as e:
            logger.error(f"문서 개수 조회 오류: {str(e)}")
            return 0 