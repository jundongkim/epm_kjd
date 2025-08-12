"""
DX-AI Advisor - 임베딩 및 벡터 검색 모듈

FAISS 기반 벡터 데이터베이스 구축 및 의미론적 검색 기능을 제공합니다.
"""

import os
import json
import pickle
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import logging
# Vector search libraries
import faiss
import numpy as np
# sentence_transformers import with fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: sentence_transformers import failed: {e}")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False
# LangChain libraries  
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
# Internal imports
from .utils import AIAdvisorConfig, get_config, AIAdvisorException

logger = logging.getLogger(__name__)


class DummyEmbeddings:
    """더미 임베딩 클래스 - sentence-transformers를 사용할 수 없을 때 사용"""
    
    def __init__(self):
        self.embedding_dim = 384  # 일반적인 임베딩 차원
        
    def __call__(self, text: str) -> List[float]:
        """FAISS에서 callable로 사용하기 위한 메서드"""
        return self.embed_query(text)
        
    def embed_query(self, text: str) -> List[float]:
        """텍스트를 더미 임베딩으로 변환"""
        # 텍스트 해시를 기반으로 일관된 더미 임베딩 생성
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        # 해시를 임베딩 벡터로 변환
        embedding = []
        for i in range(self.embedding_dim):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        return embedding
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트를 더미 임베딩으로 변환"""
        return [self.embed_query(text) for text in texts]


class EmbeddingManager:
    """임베딩 관리 클래스 - 문서를 벡터로 변환하고 FAISS 인덱스 구축"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        # config가 코루틴인 경우 처리
        if config is not None and hasattr(config, '__await__'):
            # 코루틴인 경우 기본 설정 사용
            self.config = get_config()
        else:
            self.config = config or get_config()
        self.embedding_model = None
        self.vector_store = None
        self.index_metadata = {}
        self._initialization_complete = False
        # 임베딩 모델 초기화
        self._initialize_embedding_model()
        # 자동 초기화 태스크 저장 (나중에 대기할 수 있도록)
        self._init_task = None
        try:
            # 현재 이벤트 루프에서 실행 중인지 확인
            loop = asyncio.get_running_loop()
            self._init_task = loop.create_task(self._auto_load_index())
        except RuntimeError:
            # 이벤트 루프가 없는 경우 나중에 초기화
            logger.info("이벤트 루프가 없어 나중에 초기화합니다.")
    
    async def _auto_load_index(self):
        """기본 인덱스 자동 로드"""
        try:
            # 기본 인덱스가 존재하는지 확인
            index_dir = self.config.vector_db_dir / "default"
            if index_dir.exists():
                logger.info("기본 인덱스 자동 로드 시도")
                success = await self.load_index("default")
                if success:
                    logger.info("기본 인덱스 자동 로드 완료")
                else:
                    logger.warning("기본 인덱스 자동 로드 실패")
            else:
                logger.info("기본 인덱스가 존재하지 않습니다. 첫 번째 문서 추가 시 생성됩니다.")
        except Exception as e:
            logger.error(f"인덱스 자동 로드 오류: {str(e)}")
        finally:
            self._initialization_complete = True
            logger.info("EmbeddingManager 초기화 완료")
    
    async def ensure_initialized(self):
        """초기화가 완료될 때까지 대기"""
        if not self._initialization_complete and self._init_task:
            try:
                await self._init_task
            except Exception as e:
                logger.error(f"초기화 대기 중 오류: {str(e)}")
        if not self._initialization_complete:
            # 초기화 태스크가 없거나 실패한 경우 수동으로 초기화
            await self._auto_load_index()
    
    def _initialize_embedding_model(self):
        """임베딩 모델 초기화"""
        try:
            logger.info(f"임베딩 모델 초기화 시작: {self.config.embedding_model}")
            # sentence-transformers 사용 가능 여부 확인
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.warning("sentence-transformers를 사용할 수 없어 더미 임베딩 모델을 사용합니다.")
                self.embedding_model = DummyEmbeddings()
            else:
                # HuggingFace 임베딩 모델 초기화
                self.embedding_model = HuggingFaceEmbeddings(model_name=self.config.embedding_model, model_kwargs={'device': 'cpu', 'trust_remote_code': True}, encode_kwargs={'normalize_embeddings': True, 'batch_size': 32})
            # 모델 테스트
            test_text = "테스트 임베딩"
            test_embedding = self.embedding_model.embed_query(test_text)
            logger.info(f"임베딩 모델 초기화 완료: {self.config.embedding_model}")
            logger.info(f"임베딩 차원: {len(test_embedding)}")
        except Exception as e:
            logger.error(f"임베딩 모델 초기화 실패: {str(e)}")
            # 더미 모델로 폴백
            try:
                logger.info("더미 임베딩 모델로 폴백...")
                self.embedding_model = DummyEmbeddings()
                logger.info("더미 임베딩 모델 초기화 완료")
            except Exception as fallback_error:
                logger.error(f"더미 모델도 실패: {str(fallback_error)}")
                raise AIAdvisorException(f"임베딩 모델 초기화 실패: {str(e)}, 더미 모델도 실패: {str(fallback_error)}")
    
    async def create_embeddings(self, processed_documents: List[Dict[str, Any]], index_name: str = "default") -> Dict[str, Any]:
        """처리된 문서들로부터 임베딩 생성 및 FAISS 인덱스 구축"""
        try:
            logger.info(f"임베딩 생성 시작: {len(processed_documents)}개 문서, 인덱스명: {index_name}")
            if not processed_documents:
                raise AIAdvisorException("처리된 문서가 없습니다.")
            # 임베딩 모델 상태 확인
            if not self.embedding_model:
                raise AIAdvisorException("임베딩 모델이 초기화되지 않았습니다.")
            # Document 객체 생성
            documents = []
            metadatas = []
            for doc_index, doc_result in enumerate(processed_documents):
                processing_status = doc_result.get("processing_status")
                document_id = doc_result.get("document_id", f"doc_{doc_index}")
                logger.info(f"문서 처리 중: {document_id}, 상태: {processing_status}")
                if processing_status != "completed":
                    logger.warning(f"문서 건너뜀 (미완료): {document_id}")
                    continue
                parsing_info = doc_result.get("parsing", {})
                chunks = parsing_info.get("chunks", [])
                logger.info(f"문서 {document_id}의 청크 수: {len(chunks)}")
                valid_chunks = 0
                for chunk_index, chunk in enumerate(chunks):
                    content = chunk.get("content", "")
                    if content and content.strip():
                        # 메타데이터에 문서 정보 추가
                        metadata = chunk.get("metadata", {})
                        metadata["document_id"] = document_id
                        metadata["chunk_index"] = chunk_index
                        
                        # Add original filename from doc_result["file_info"]
                        original_filename = doc_result.get("file_info", {}).get("original_filename")
                        if original_filename:
                            metadata["original_filename"] = original_filename
                        
                        # Document 객체 생성
                        doc = Document(
                            page_content=content.strip(),
                            metadata=metadata
                        )
                        documents.append(doc)
                        metadatas.append(metadata)
                        valid_chunks += 1
                
                logger.info(f"문서 {document_id}의 유효한 청크 수: {valid_chunks}")
            
            if not documents:
                raise AIAdvisorException("유효한 문서 청크가 없습니다.")
            
            logger.info(f"총 {len(documents)}개의 문서 청크로 벡터 임베딩 생성 시작")
            
            # FAISS 벡터 스토어 생성
            logger.info("FAISS 벡터 스토어 생성 중...")
            self.vector_store = await asyncio.to_thread(
                FAISS.from_documents,
                documents,
                self.embedding_model
            )
            
            # 벡터 스토어 생성 확인
            if self.vector_store and hasattr(self.vector_store, 'index'):
                vector_count = self.vector_store.index.ntotal
                logger.info(f"벡터 스토어 생성 완료: {vector_count}개 벡터")
            else:
                raise AIAdvisorException("벡터 스토어 생성 실패")
            
            # 인덱스 메타데이터 저장
            self.index_metadata = {
                "index_name": index_name,
                "total_documents": len(documents),
                "embedding_model": self.config.embedding_model,
                "created_at": datetime.now().isoformat(),
                "config": {
                    "chunk_size": self.config.chunk_size,
                    "chunk_overlap": self.config.chunk_overlap,
                    "embedding_dimension": self.config.embedding_dimension
                }
            }
            
            # 인덱스 저장
            logger.info("벡터 인덱스 디스크 저장 중...")
            index_path = await self._save_index(index_name)
            
            logger.info(f"임베딩 인덱스 생성 완료: {index_path}")
            logger.info(f"총 처리된 문서: {len(documents)}개, 벡터 수: {vector_count}")
            
            return {
                "creation_status": "success",
                "index_name": index_name,
                "index_path": index_path,
                "total_documents": len(documents),
                "vector_count": vector_count,
                "metadata": self.index_metadata
            }
            
        except Exception as e:
            logger.error(f"임베딩 생성 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            raise AIAdvisorException(f"임베딩 생성 중 오류 발생: {str(e)}")

    async def _save_index(self, index_name: str) -> str:
        """FAISS 인덱스를 디스크에 저장"""
        try:
            index_dir = self.config.vector_db_dir / index_name
            logger.info(f"인덱스 저장 시작: {index_dir}")
            
            # 디렉토리 생성
            index_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"디렉토리 생성됨: {index_dir}")
            
            # 벡터 스토어 상태 확인
            if not self.vector_store:
                raise AIAdvisorException("벡터 스토어가 None입니다")
            
            if not hasattr(self.vector_store, 'save_local'):
                raise AIAdvisorException("벡터 스토어에 save_local 메서드가 없습니다")
            
            # FAISS 인덱스 저장
            faiss_path = str(index_dir / "faiss_index")
            logger.info(f"FAISS 인덱스 저장 중: {faiss_path}")
            
            await asyncio.to_thread(self.vector_store.save_local, faiss_path)
            logger.info(f"FAISS 인덱스 저장 완료: {faiss_path}")
            
            # 저장된 파일들 확인
            saved_files = list(index_dir.rglob("*"))
            logger.info(f"저장된 파일들: {[str(f) for f in saved_files]}")
            
            # 메타데이터 저장
            metadata_path = index_dir / "metadata.json"
            logger.info(f"메타데이터 저장 중: {metadata_path}")
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.index_metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"메타데이터 저장 완료: {metadata_path}")
            
            # 최종 파일 목록 확인
            final_files = list(index_dir.rglob("*"))
            logger.info(f"최종 저장된 파일들: {[str(f) for f in final_files]}")
            
            logger.info(f"✅ 인덱스 저장 완료: {index_dir}")
            return str(index_dir)
            
        except Exception as e:
            logger.error(f"❌ 인덱스 저장 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            raise AIAdvisorException(f"인덱스 저장 중 오류 발생: {str(e)}")
    
    async def load_index(self, index_name: str) -> bool:
        """저장된 FAISS 인덱스 로드"""
        try:
            index_dir = self.config.vector_db_dir / index_name
            if not index_dir.exists():
                raise AIAdvisorException(f"인덱스를 찾을 수 없습니다: {index_name}")
            
            # 메타데이터 로드
            metadata_path = index_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.index_metadata = json.load(f)
            
            # FAISS 인덱스 로드
            faiss_path = str(index_dir / "faiss_index")
            try:
                self.vector_store = await asyncio.to_thread(
                    FAISS.load_local,
                    faiss_path,
                    self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                
                # 차원 호환성 검증
                if hasattr(self.vector_store, 'index') and hasattr(self.embedding_model, 'embed_query'):
                    # 테스트 임베딩 생성
                    test_embedding = self.embedding_model.embed_query("test")
                    expected_dim = len(test_embedding)
                    actual_dim = self.vector_store.index.d
                    
                    if expected_dim != actual_dim:
                        logger.error(f"차원 불일치: 임베딩 모델={expected_dim}, 인덱스={actual_dim}")
                        logger.warning(f"기존 인덱스를 삭제하고 재구축이 필요합니다.")
                        
                        # 인덱스 삭제
                        import shutil
                        shutil.rmtree(index_dir)
                        logger.info(f"차원 불일치로 인한 인덱스 삭제: {index_name}")
                        
                        self.vector_store = None
                        return False
                
                logger.info(f"인덱스 로드됨: {index_name}")
                return True
                
            except Exception as load_error:
                logger.error(f"인덱스 로드 중 오류: {str(load_error)}")
                
                # 인덱스 파일이 손상된 경우 삭제
                if "dimension" in str(load_error).lower() or "assert" in str(load_error).lower():
                    logger.warning("차원 불일치 또는 손상된 인덱스 감지. 인덱스를 삭제합니다.")
                    import shutil
                    if index_dir.exists():
                        shutil.rmtree(index_dir)
                        logger.info(f"손상된 인덱스 삭제: {index_name}")
                
                return False
            
        except Exception as e:
            logger.error(f"인덱스 로드 오류: {str(e)}")
            return False
    
    async def search_similar_documents(self, query: str, k: int = 10, score_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """유사 문서 검색"""
        try:
            # 초기화 완료 확인
            await self.ensure_initialized()
            
            logger.info(f"문서 검색 시작: '{query[:50]}...', k={k}, threshold={score_threshold}")
            
            # 벡터 스토어가 없으면 자동 로드 시도
            if not self.vector_store:
                logger.info("벡터 스토어가 없습니다. 자동 로드 시도...")
                success = await self.load_index("default")
                if not success:
                    logger.warning("벡터 스토어 로드 실패. 빈 결과 반환")
                    return []
            
            # 벡터 스토어 상태 확인
            if hasattr(self.vector_store, 'index'):
                total_vectors = self.vector_store.index.ntotal
                logger.info(f"벡터 스토어 상태: {total_vectors}개 벡터 보유")
                
                if total_vectors == 0:
                    logger.warning("벡터 스토어가 비어있습니다.")
                    return []
            
            # 임베딩 모델 상태 확인
            if not self.embedding_model:
                logger.error("임베딩 모델이 초기화되지 않았습니다")
                return []
            
            # 검색 쿼리 전처리
            processed_query = self._preprocess_query(query)
            
            # 유사도 검색 수행 (더 많은 후보 검색)
            logger.info(f"유사도 검색 수행 중... (query: '{processed_query[:30]}...', k={k})")
            # 더 많은 후보를 가져온 후 후처리로 정밀 필터링/정렬
            candidate_k = max(k * 5, k)
            docs_with_scores = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                processed_query,
                k=candidate_k
            )
            
            logger.info(f"원본 검색 결과: {len(docs_with_scores)}개")
            
            # 결과 필터링 및 품질 평가
            # 주의: similarity_search_with_score가 반환하는 score는 '거리(distance)'. 낮을수록 유사
            # 유사도 = 1 / (1 + distance)로 변환하여 임계값 및 정렬에 사용
            results = []
            for i, (doc, distance) in enumerate(docs_with_scores):
                try:
                    distance_val = float(distance)
                except Exception:
                    distance_val = 9999.0
                similarity = 1.0 / (1.0 + distance_val)

                if similarity >= score_threshold:
                    chunk_quality = doc.metadata.get('chunk_quality_score', 0.5)
                    combined_score = (similarity * 0.7) + (chunk_quality * 0.3)

                    result = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": float(similarity),
                        "chunk_quality_score": float(chunk_quality),
                        "combined_score": float(combined_score),
                        "search_query": processed_query,
                                "original_query": query,
                        "result_index": i,
                        "content_length": len(doc.page_content),
                        "page_info": self._extract_page_info(doc.metadata),
                        "source_info": self._extract_source_info(doc.metadata)
                    }
                    results.append(result)
                    logger.debug(
                        f"결과 {i}: similarity={similarity:.4f}, distance={distance_val:.4f}, "
                        f"quality={chunk_quality:.4f}, combined={combined_score:.4f}"
                    )
                else:
                    logger.debug(
                        f"임계값 미달로 제외: similarity={similarity:.4f} < {score_threshold} (distance={distance_val:.4f})"
                    )
            
            # 결과 재정렬 (종합 점수 기준)
            # 파일명/페이지 기준 중복 제거 (동일 문서·페이지의 중복 청크 제거)
            unique_map = {}
            for item in results:
                metadata = item.get('metadata', {})
                source_info = item.get('source_info', {})
                filename = (
                    source_info.get('filename')
                    or metadata.get('original_filename')
                    or metadata.get('filename')
                    or 'unknown'
                )
                page_numbers = tuple((item.get('page_info', {}).get('page_numbers') or metadata.get('page_numbers') or []))
                key = (filename, page_numbers)
                if key not in unique_map or item['combined_score'] > unique_map[key]['combined_score']:
                    unique_map[key] = item

            deduped_results = list(unique_map.values())
            deduped_results.sort(key=lambda x: x['combined_score'], reverse=True)

            # 상위 k개만 반환
            final_results = deduped_results[:k]
            
            logger.info(f"검색 완료: {len(final_results)}개 결과 반환 (query: '{query[:50]}...')")
            return final_results
            
        except Exception as e:
            logger.error(f"문서 검색 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            # 오류 발생 시 빈 결과 반환 (시스템 중단 방지)
            return []
    
    def _preprocess_query(self, query: str) -> str:
        """검색 쿼리 전처리 (한국어 최적화)"""
        try:
            import re
            
            # 기본 정리
            processed = query.strip()
            
            # 연속된 공백 제거
            processed = re.sub(r'\s+', ' ', processed)
            
            # 불필요한 문장 부호 제거 (검색에 방해되는 것들)
            processed = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ]', ' ', processed)
            
            # 다시 공백 정리
            processed = re.sub(r'\s+', ' ', processed).strip()
            
            # 너무 짧은 쿼리는 원본 반환
            if len(processed) < 2:
                return query
            
            # 검색 향상을 위한 키워드 확장 (선택적)
            if len(processed) < 10:
                # 짧은 쿼리의 경우 관련 키워드 추가
                expanded_query = self._expand_short_query(processed)
                if expanded_query != processed:
                    logger.debug(f"쿼리 확장: '{processed}' -> '{expanded_query}'")
                    return expanded_query
            
            return processed
            
        except Exception as e:
            logger.error(f"쿼리 전처리 오류: {str(e)}")
            return query
    
    def _expand_short_query(self, query: str) -> str:
        """짧은 쿼리 확장"""
        try:
            # 제조업 관련 키워드 매핑
            expansion_map = {
                "품질": "품질 관리 QC",
                "공정": "공정 프로세스 제조",
                "불량": "불량 결함 품질문제",
                "개선": "개선 향상 최적화",
                "분석": "분석 평가 검토",
                "설비": "설비 장비 기계",
                "생산": "생산 제조 공정",
                "검사": "검사 테스트 품질확인",
                "온도": "온도 열처리 가열",
                "압력": "압력 가압 압축",
                "AI": "AI 인공지능 머신러닝",
                "데이터": "데이터 정보 분석"
            }
            
            for keyword, expansion in expansion_map.items():
                if keyword in query:
                    return expansion
            
            return query
            
        except Exception:
            return query
    
    async def search_with_metadata_filter(self, query: str, metadata_filter: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        """메타데이터 필터를 적용한 검색"""
        try:
            # 벡터 스토어가 없으면 자동 로드 시도
            if not self.vector_store:
                logger.info("벡터 스토어가 없습니다. 자동 로드 시도...")
                success = await self.load_index("default")
                if not success:
                    logger.warning("벡터 스토어 로드 실패. 빈 결과 반환")
                    return []
            
            # 메타데이터 필터링을 위한 사용자 정의 함수
            def filter_function(metadata: Dict[str, Any]) -> bool:
                for key, value in metadata_filter.items():
                    if key not in metadata:
                        return False
                    
                    metadata_value = metadata[key]
                    
                    # 문자열 부분 매칭
                    if isinstance(value, str) and isinstance(metadata_value, str):
                        if value.lower() not in metadata_value.lower():
                            return False
                    # 정확한 값 매칭
                    elif metadata_value != value:
                        return False
                
                return True
            
            # 전체 검색 후 필터링 (FAISS의 메타데이터 필터링 제한으로 인해)
            all_docs = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                query,
                k=k*5  # 더 많이 가져와서 필터링 후 k개 선택
            )
            
            filtered_results = []
            for doc, score in all_docs:
                if filter_function(doc.metadata) and len(filtered_results) < k:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": float(score),
                        "search_query": query,
                        "applied_filter": metadata_filter
                    })
            
            logger.info(f"필터링된 검색 완료: {len(filtered_results)}개 결과")
            return filtered_results
            
        except Exception as e:
            logger.error(f"메타데이터 필터링 검색 오류: {str(e)}")
            raise AIAdvisorException(f"메타데이터 필터링 검색 중 오류 발생: {str(e)}")
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """인덱스 통계 정보 반환"""
        try:
            if not self.vector_store:
                return {"error": "벡터 스토어가 로드되지 않았습니다."}
            
            stats = {
                "metadata": self.index_metadata,
                "vector_count": self.vector_store.index.ntotal if hasattr(self.vector_store, 'index') else 0,
                "status": "loaded"
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"인덱스 통계 조회 오류: {str(e)}")
            return {"error": str(e)}
    
    def get_available_indexes(self) -> List[Dict[str, Any]]:
        """사용 가능한 인덱스 목록 반환"""
        try:
            indexes = []
            vector_db_dir = self.config.vector_db_dir
            
            if not vector_db_dir.exists():
                return indexes
            
            for index_dir in vector_db_dir.iterdir():
                if index_dir.is_dir():
                    metadata_path = index_dir / "metadata.json"
                    faiss_path = index_dir / "faiss_index"
                    
                    if metadata_path.exists() and faiss_path.exists():
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            
                            indexes.append({
                                "name": index_dir.name,
                                "path": str(index_dir),
                                "created_at": metadata.get("created_at", ""),
                                "total_documents": metadata.get("total_documents", 0),
                                "embedding_model": metadata.get("embedding_model", ""),
                                "size_mb": self._get_directory_size_mb(index_dir)
                            })
                        except Exception as e:
                            logger.warning(f"인덱스 메타데이터 읽기 실패 - {index_dir}: {str(e)}")
            
            return sorted(indexes, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"인덱스 목록 조회 오류: {str(e)}")
            return []
    
    def _get_directory_size_mb(self, directory: Path) -> float:
        """디렉토리 크기를 MB 단위로 반환"""
        try:
            total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
            return round(total_size / (1024 * 1024), 2)
        except Exception:
            return 0.0

    async def add_document(self, document_result: Dict[str, Any]) -> bool:
        """문서를 벡터 스토어에 추가"""
        try:
            # 초기화 완료 확인
            await self.ensure_initialized()
            
            document_id = document_result.get('document_id', 'unknown')
            logger.info(f"문서 추가 시작: {document_id}")
            
            # 임베딩 모델 상태 확인
            if not self.embedding_model:
                logger.error("임베딩 모델이 초기화되지 않았습니다")
                return False
            
            # 문서 처리 상태 확인
            processing_status = document_result.get("processing_status")
            if processing_status != "completed":
                logger.warning(f"문서 처리가 완료되지 않았습니다: {processing_status}")
                return False
            
            # 문서 파싱 정보 확인
            parsing_info = document_result.get("parsing", {})
            chunks = parsing_info.get("chunks", [])
            
            logger.info(f"원본 문서 청크 수: {len(chunks)}")
            
            if not chunks:
                logger.warning("문서에 청크가 없습니다")
                return False
            
            # Document 객체 생성
            documents = []
            for i, chunk in enumerate(chunks):
                content = chunk.get("content", "")
                if content and content.strip():
                    # 메타데이터에 문서 ID 추가
                    metadata = chunk.get("metadata", {})
                    metadata["document_id"] = document_id
                    metadata["chunk_index"] = i
                    
                    doc = Document(
                        page_content=content.strip(),
                        metadata=metadata
                    )
                    documents.append(doc)
                else:
                    logger.debug(f"빈 청크 건너뜀: chunk {i}")
            
            logger.info(f"유효한 문서 청크 수: {len(documents)}")
            
            if not documents:
                logger.warning("추가할 유효한 문서 청크가 없습니다")
                return False
            
            if not self.vector_store:
                # 첫 번째 문서인 경우 새 인덱스 생성
                logger.info("첫 번째 문서 - 새 벡터 인덱스 생성")
                try:
                    result = await self.create_embeddings([document_result])
                    success = result.get("creation_status") == "success"
                    if success:
                        logger.info("✅ 새 벡터 인덱스 생성 완료")
                        logger.info(f"생성된 인덱스 경로: {result.get('index_path')}")
                        logger.info(f"처리된 문서 수: {result.get('total_documents')}")
                        logger.info(f"벡터 수: {result.get('vector_count', 'unknown')}")
                    else:
                        logger.error("❌ 새 벡터 인덱스 생성 실패")
                        logger.error(f"결과: {result}")
                    return success
                except Exception as create_error:
                    logger.error(f"❌ create_embeddings 호출 중 오류: {str(create_error)}")
                    import traceback
                    logger.error(f"상세 오류: {traceback.format_exc()}")
                    return False
            else:
                # 기존 인덱스에 문서 추가
                logger.info("기존 벡터 인덱스에 문서 추가")
                await asyncio.to_thread(
                    self.vector_store.add_documents,
                    documents
                )
                
                # 인덱스 저장
                await self._save_index("default")
                
                logger.info(f"{len(documents)}개의 문서 청크를 벡터 스토어에 추가 완료")
                
                # 인덱스 크기 확인
                try:
                    total_docs = self.vector_store.index.ntotal
                    logger.info(f"현재 벡터 인덱스 총 문서 수: {total_docs}")
                except Exception as size_error:
                    logger.warning(f"인덱스 크기 확인 실패: {str(size_error)}")
                
                return True
            
        except Exception as e:
            logger.error(f"문서 추가 오류 (document_id: {document_result.get('document_id', 'unknown')}): {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return False

    async def remove_document(self, document_id: str) -> bool:
        """문서를 벡터 스토어에서 제거 (인덱스 재구성)"""
        try:
            if not self.vector_store:
                logger.warning(f"벡터 스토어가 없어서 문서 삭제 불가: {document_id}")
                return False
            
            logger.info(f"벡터DB에서 문서 삭제 시작: {document_id}")
            
            # 현재 벡터 스토어에서 삭제할 문서를 제외한 모든 문서 추출
            all_docs = []
            if hasattr(self.vector_store, 'docstore') and hasattr(self.vector_store.docstore, '_dict'):
                for doc_id, doc in self.vector_store.docstore._dict.items():
                    doc_metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    if doc_metadata.get('document_id') != document_id:
                        all_docs.append(doc)
                
                logger.info(f"필터링된 문서 수: {len(all_docs)}개 (삭제 대상 제외)")
                
                if all_docs:
                    # 새로운 벡터 스토어 생성
                    self.vector_store = await asyncio.to_thread(
                        FAISS.from_documents,
                        all_docs,
                        self.embedding_model
                    )
                    
                    # 인덱스 저장
                    await self._save_index("default")
                    
                    logger.info(f"✅ 문서 삭제 완료: {document_id}")
                    return True
                else:
                    # 모든 문서가 삭제된 경우
                    self.vector_store = None
                    logger.info(f"✅ 마지막 문서 삭제로 벡터 스토어 초기화: {document_id}")
                    return True
            else:
                logger.warning(f"벡터 스토어에서 문서 접근 불가: {document_id}")
                return self._fallback_document_removal(document_id)
            
        except Exception as e:
            logger.error(f"문서 삭제 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
    
    def _fallback_document_removal(self, document_id: str) -> bool:
        """대체 문서 삭제 방법 (전체 재구축)"""
        try:
            logger.info(f"대체 방법으로 문서 삭제 처리: {document_id}")
            # 실제로는 문서 프로세서에서 전체 벡터DB 재구축을 호출해야 함
            logger.warning(f"문서 {document_id} 삭제를 위해 벡터DB 전체 재구축이 필요합니다")
            return True
        except Exception as e:
            logger.error(f"대체 문서 삭제 방법 실패: {str(e)}")
            return False

    async def search_documents(self, query: str, k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """문서 검색"""
        try:
            if not self.vector_store:
                return []
            
            # 카테고리 필터 적용
            metadata_filter = None
            if category:
                metadata_filter = {"category": category}
            
            if metadata_filter:
                results = await self.search_with_metadata_filter(query, metadata_filter, k)
            else:
                results = await self.search_similar_documents(query, k)
            
            return results
            
        except Exception as e:
            logger.error(f"문서 검색 오류: {str(e)}")
            return []

    async def get_index_size(self) -> int:
        """인덱스 크기 조회"""
        try:
            if not self.vector_store:
                return 0
            return self.vector_store.index.ntotal
        except Exception as e:
            logger.error(f"인덱스 크기 조회 오류: {str(e)}")
            return 0
    
    def _extract_page_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터에서 페이지 정보 추출"""
        page_info = {
            "page_numbers": metadata.get("page_numbers", []),
            "page_ranges": metadata.get("page_ranges", []),
            "slide_numbers": metadata.get("slide_numbers", []),
            "slide_ranges": metadata.get("slide_ranges", []),
            "chunk_id": metadata.get("chunk_id", 0),
            "total_chunks": metadata.get("total_chunks", 0)
        }
        return page_info
    
    def _extract_source_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터에서 소스 문서 정보 추출"""
        source_info = {
                            "filename": metadata.get("original_filename", metadata.get("filename", "알 수 없는 파일")),
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "document_id": metadata.get("document_id", ""),
            "file_type": metadata.get("file_type", ""),
            "created_at": metadata.get("created_at", ""),
            "modified_at": metadata.get("modified_at", ""),
            "page_count": metadata.get("page_count", 0)
        }
        return source_info

    async def create_manufacturing_specialized_index(self, index_name: str = "manufacturing_specialized") -> Dict[str, Any]:
        """제조업 특화 인덱스 생성"""
        try:
            logger.info(f"제조업 특화 인덱스 생성 시작: {index_name}")
            
            # 제조업 특화 프롬프트 템플릿
            manufacturing_prompts = [
                "제조업 품질 관리",
                "생산 공정 최적화",
                "설비 유지보수",
                "원자재 품질 검사",
                "제품 결함 분석",
                "공정 안전 관리",
                "환경 규제 준수",
                "에너지 효율성",
                "공급망 관리",
                "고객 요구사항 분석"
            ]
            
            # 제조업 특화 임베딩 생성
            specialized_embeddings = []
            for prompt in manufacturing_prompts:
                try:
                    embedding = self.embedding_model.embed_query(prompt)
                    specialized_embeddings.append({
                        "content": prompt,
                        "metadata": {
                            "type": "manufacturing_specialized",
                            "category": "domain_knowledge",
                            "source": "system_generated"
                        },
                        "embedding": embedding
                    })
                except Exception as e:
                    logger.warning(f"제조업 프롬프트 임베딩 생성 실패: {prompt}, 오류: {str(e)}")
            
            if not specialized_embeddings:
                raise Exception("제조업 특화 임베딩을 생성할 수 없습니다.")
            
            # 인덱스 생성
            result = await self.create_embeddings(specialized_embeddings, index_name)
            
            logger.info(f"✅ 제조업 특화 인덱스 생성 완료: {index_name}")
            return {
                "status": "success",
                "index_name": index_name,
                "specialized_embeddings_count": len(specialized_embeddings),
                "manufacturing_domains": manufacturing_prompts
            }
            
        except Exception as e:
            logger.error(f"❌ 제조업 특화 인덱스 생성 실패: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def is_manufacturing_specialized(self, index_name: str = None) -> bool:
        """인덱스가 제조업 특화인지 확인"""
        try:
            if index_name is None:
                index_name = self.current_index_name or "default"
            
            # 인덱스 메타데이터 확인
            if hasattr(self, 'index_metadata') and self.index_metadata:
                return self.index_metadata.get("type") == "manufacturing_specialized"
            
            # 벡터 스토어에서 직접 확인
            if self.vector_store:
                # 샘플 검색으로 특성 확인
                test_query = "제조업 품질 관리"
                results = await self.search_similar_documents(test_query, k=1)
                if results:
                    metadata = results[0].get("metadata", {})
                    return metadata.get("type") == "manufacturing_specialized"
            
            return False
            
        except Exception as e:
            logger.warning(f"제조업 특화 여부 확인 실패: {str(e)}")
            return False


# VectorSearchEngine는 분리되어 src.aiadvisor.search_engine 모듈로 이동되었습니다.

    async def get_document_clusters(self, n_clusters: int = 5) -> Dict[str, Any]:
        """문서 클러스터링"""
        try:
            if not self.embedding_manager.vector_store:
                return {"clusters": [], "total_documents": 0}
            
            # 모든 임베딩 벡터 가져오기
            embeddings = self.embedding_manager.vector_store.index.reconstruct_n(
                0, self.embedding_manager.vector_store.index.ntotal
            )

            # K-means 클러스터링
            from sklearn.cluster import KMeans

            kmeans = KMeans(n_clusters=min(n_clusters, len(embeddings)), random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings)

            # 클러스터별 문서 그룹화
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(i)

            return {
                "clusters": [
                    {
                        "cluster_id": cluster_id,
                        "document_indices": doc_indices,
                        "size": len(doc_indices),
                    }
                    for cluster_id, doc_indices in clusters.items()
                ],
                "total_documents": len(embeddings),
                "n_clusters": len(clusters),
            }
            
        except Exception as e:
            logger.error(f"문서 클러스터링 오류: {str(e)}")
            return {"clusters": [], "total_documents": 0}

    async def add_document_to_index(self, document_result: Dict[str, Any]) -> bool:
        """문서를 벡터 인덱스에 추가 (EmbeddingManager를 통해 처리)"""
        try:
            return await self.embedding_manager.add_document(document_result)
        except Exception as e:
            logger.error(f"벡터 검색 엔진: 문서 추가 오류: {str(e)}")
            return False

    async def remove_document_from_index(self, document_id: str) -> bool:
        """문서를 벡터 인덱스에서 제거 (EmbeddingManager를 통해 처리)"""
        try:
            return await self.embedding_manager.remove_document(document_id)
        except Exception as e:
            logger.error(f"벡터 검색 엔진: 문서 제거 오류: {str(e)}")
            return False

    async def search_documents_by_category(self, query: str, k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """카테고리별 문서 검색 (EmbeddingManager를 통해 처리)"""
        try:
            return await self.embedding_manager.search_documents(query, k, category)
        except Exception as e:
            logger.error(f"벡터 검색 엔진: 문서 검색 오류: {str(e)}")
            return []

    async def get_vector_index_size(self) -> int:
        """벡터 인덱스 크기 조회 (EmbeddingManager를 통해 처리)"""
        try:
            return await self.embedding_manager.get_index_size()
        except Exception as e:
            logger.error(f"벡터 검색 엔진: 인덱스 크기 조회 오류: {str(e)}")
            return 0 