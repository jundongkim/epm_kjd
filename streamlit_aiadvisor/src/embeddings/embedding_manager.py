"""
문서 내용으로부터 임베딩을 생성하고 벡터 DB를 구축하는 모듈
"""
import os
import json
import pickle
from typing import List, Dict, Any, Optional, Union, Tuple

import numpy as np
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.utils.config import EMBEDDING_MODEL, VECTOR_DB_DIR, MODELS_DIR


class EmbeddingManager:
    """문서 임베딩 생성 및 벡터 DB 관리 클래스"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        임베딩 관리자 초기화
        
        Args:
            model_name (str): 사용할 임베딩 모델명
        """
        self.model_name = model_name
        
        # 임베딩 모델 초기화 - 로컬 캐시 사용
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
            cache_folder=os.path.join(MODELS_DIR, "multilingual-e5-large-instruct")
        )
        
        # 벡터 DB 저장 경로
        self.vector_db_path = VECTOR_DB_DIR
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # 기본 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # 벡터 DB 인스턴스
        self.vectorstore = None
    
    def create_document_from_text(self, text: str, metadata: Dict[str, Any] = None) -> Document:
        """
        텍스트로부터 Document 객체 생성
        
        Args:
            text (str): Document 내용
            metadata (Dict[str, Any], optional): 메타데이터
            
        Returns:
            Document: 생성된 Document 객체
        """
        if metadata is None:
            metadata = {}
        
        return Document(page_content=text, metadata=metadata)
    
    def create_documents_from_chunks(self, chunks: List[str], metadata: Dict[str, Any] = None) -> List[Document]:
        """
        텍스트 청크 리스트로부터 Document 객체 리스트 생성
        
        Args:
            chunks (List[str]): 청크 리스트 
            metadata (Dict[str, Any], optional): 공통 메타데이터
            
        Returns:
            List[Document]: Document 객체 리스트
        """
        if metadata is None:
            metadata = {}
            
        return [self.create_document_from_text(chunk, metadata) for chunk in chunks]
    
    def create_documents_from_parsed_results(self, parsed_results: List[Dict[str, Any]]) -> List[Document]:
        """
        파싱된 결과로부터 Document 객체 리스트 생성 (원본 파서 결과용)
        
        Args:
            parsed_results (List[Dict[str, Any]]): 파싱된 결과 목록
            
        Returns:
            List[Document]: Document 객체 리스트
        """
        documents = []
        
        for result in parsed_results:
            # 파싱 결과의 직접 메타데이터 사용
            filename = result.get('filename', 'unknown')
            file_extension = result.get('file_extension', '')
            file_date = result.get('modified_date', '')
            file_path = result.get('file_path', '')
            file_size = result.get('file_size_kb', 0)
            
            base_metadata = {
                'filename': filename,
                'file_extension': file_extension,
                'file_date': file_date,
                'file_path': file_path,
                'file_size_kb': file_size,
                'source': 'parsed_document'
            }
            
            # 내용 항목별로 Document 생성
            for i, content_item in enumerate(result.get('content', [])):
                if content_item and isinstance(content_item, str):
                    item_metadata = base_metadata.copy()
                    item_metadata['chunk_id'] = i
                    item_metadata['chunk_index'] = i
                    item_metadata['chunk_type'] = 'content'
                    
                    # 청크 분할
                    chunks = self.text_splitter.split_text(content_item)
                    
                    # 각 청크에 대해 Document 생성
                    for j, chunk in enumerate(chunks):
                        chunk_metadata = item_metadata.copy()
                        chunk_metadata['sub_chunk_id'] = j
                        document = self.create_document_from_text(chunk, chunk_metadata)
                        documents.append(document)
        
        return documents

    def create_documents_from_extraction_results(self, extraction_results: List[Dict[str, Any]]) -> List[Document]:
        """
        정보 추출 결과로부터 Document 객체 리스트 생성
        
        Args:
            extraction_results (List[Dict[str, Any]]): 정보 추출 결과 목록
            
        Returns:
            List[Document]: Document 객체 리스트
        """
        documents = []
        
        print(f"[DEBUG] 정보 추출 결과 처리 시작: {len(extraction_results)}개 파일")
        
        for idx, result in enumerate(extraction_results):
            print(f"[DEBUG] 파일 {idx+1} 처리 중...")
            
            # 파일 정보 가져오기
            file_info = result.get('file_info', {})
            filename = file_info.get('filename', 'unknown')
            file_extension = file_info.get('file_extension', '')
            file_date = file_info.get('modified_date', '')
            file_path = file_info.get('file_path', '')
            file_size = file_info.get('file_size_kb', 0)
            
            print(f"[DEBUG] 파일명: {filename}")
            
            # 메타데이터 가져오기
            extracted_metadata = result.get('metadata', {})
            title = extracted_metadata.get('title', filename)
            keywords = extracted_metadata.get('keywords', [])
            topics = extracted_metadata.get('topics', [])
            summary = extracted_metadata.get('summary', '')
            author = extracted_metadata.get('author', '')
            creation_date = extracted_metadata.get('creation_date', '')
            
            print(f"[DEBUG] 추출된 메타데이터 - 제목: {title}, 키워드 수: {len(keywords)}, 요약 길이: {len(summary)}")
            
            base_metadata = {
                'filename': filename,
                'file_extension': file_extension,
                'file_date': file_date,
                'file_path': file_path,
                'file_size_kb': file_size,
                'title': title,
                'keywords': keywords,
                'topics': topics,
                'summary': summary,
                'author': author,
                'creation_date': creation_date,
                'source': 'extraction_result'
            }
            
            # 전체 내용 처리
            full_content = result.get('full_content', {})
            content_items = full_content.get('content_items', [])
            
            print(f"[DEBUG] full_content 키들: {list(full_content.keys())}")
            print(f"[DEBUG] content_items 수: {len(content_items)}")
            if content_items:
                print(f"[DEBUG] 첫 번째 content_item 길이: {len(content_items[0])}")
            
            # full_content가 비어있으면 원본 데이터에서 content 가져오기 (추출 실패 시 대비)
            if not content_items:
                print(f"[DEBUG] content_items가 비어있음, full_text 확인 중...")
                # extraction_results에는 원본 parsed_results의 content가 포함되어 있지 않을 수 있음
                # 이 경우 full_content의 full_text를 사용하거나 다른 방법으로 처리
                full_text = full_content.get('full_text', '')
                print(f"[DEBUG] full_text 길이: {len(full_text)}")
                if full_text:
                    content_items = [full_text]  # 전체 텍스트를 하나의 아이템으로 처리
                    print(f"[DEBUG] full_text를 content_items로 변환")
                else:
                    # full_text도 없으면 메타데이터에서 내용 추출 시도
                    metadata_text = extracted_metadata.get('summary', '')
                    print(f"[DEBUG] summary 길이: {len(metadata_text)}")
                    if metadata_text:
                        content_items = [metadata_text]
                        print(f"[DEBUG] summary를 content_items로 사용")
                    else:
                        # 최후의 수단: 빈 내용이라도 파일 정보를 기반으로 문서 생성
                        content_items = [f"파일: {filename} (내용 추출 실패)"]
                        print(f"[DEBUG] 대체 텍스트 생성: {content_items[0]}")
            
            file_document_count = 0
            
            # 내용 항목별로 Document 생성
            for i, content_item in enumerate(content_items):
                if content_item and isinstance(content_item, str) and content_item.strip():
                    item_metadata = base_metadata.copy()
                    item_metadata['chunk_id'] = i
                    item_metadata['chunk_index'] = i
                    item_metadata['chunk_type'] = 'content'
                    
                    # 청크 분할
                    chunks = self.text_splitter.split_text(content_item)
                    print(f"[DEBUG] content_item {i} → {len(chunks)}개 청크로 분할")
                    
                    # 각 청크에 대해 Document 생성
                    for j, chunk in enumerate(chunks):
                        if chunk.strip():  # 빈 청크 제외
                            chunk_metadata = item_metadata.copy()
                            chunk_metadata['sub_chunk_id'] = j
                            document = self.create_document_from_text(chunk, chunk_metadata)
                            documents.append(document)
                            file_document_count += 1
            
            print(f"[DEBUG] 파일 '{filename}'에서 생성된 content 문서 수: {file_document_count}")
            
            # 구조화된 데이터에서 Document 생성
            structured_data = result.get('structured_data', {})
            structured_document_count = 0
            
            if structured_data:
                print(f"[DEBUG] 구조화된 데이터 처리 중...")
                print(f"[DEBUG] 구조화된 데이터 키들: {list(structured_data.keys())}")
                
                # 테이블 데이터
                tables = structured_data.get('tables', [])
                print(f"[DEBUG] 테이블 수: {len(tables)}")
                for table_idx, table in enumerate(tables):
                    table_text = f"Table: {table.get('title', f'Table {table_idx}')}\n"
                    
                    # 헤더 추가
                    headers = table.get('headers', [])
                    if headers:
                        table_text += " | ".join(headers) + "\n"
                    
                    # 행 데이터 추가
                    for row in table.get('rows', []):
                        table_text += " | ".join([str(cell) for cell in row]) + "\n"
                    
                    # 테이블 메타데이터
                    table_metadata = base_metadata.copy()
                    table_metadata['chunk_type'] = 'table'
                    table_metadata['table_id'] = table_idx
                    table_metadata['table_title'] = table.get('title', '')
                    
                    document = self.create_document_from_text(table_text, table_metadata)
                    documents.append(document)
                    structured_document_count += 1
                
                # 목록 데이터
                lists = structured_data.get('lists', [])
                print(f"[DEBUG] 목록 수: {len(lists)}")
                for list_idx, list_data in enumerate(lists):
                    list_text = f"List: {list_data.get('title', f'List {list_idx}')}\n"
                    
                    # 항목 추가
                    for item in list_data.get('items', []):
                        list_text += f"- {item}\n"
                    
                    # 목록 메타데이터
                    list_metadata = base_metadata.copy()
                    list_metadata['chunk_type'] = 'list'
                    list_metadata['list_id'] = list_idx
                    list_metadata['list_title'] = list_data.get('title', '')
                    
                    document = self.create_document_from_text(list_text, list_metadata)
                    documents.append(document)
                    structured_document_count += 1

                # 통계 데이터
                statistics = structured_data.get('statistics', [])
                print(f"[DEBUG] 통계 수: {len(statistics)}")
                for stat_idx, stat in enumerate(statistics):
                    stat_text = f"Statistic: {stat.get('name', f'Stat {stat_idx}')} = {stat.get('value', '')}\n"
                    
                    # 통계 메타데이터
                    stat_metadata = base_metadata.copy()
                    stat_metadata['chunk_type'] = 'statistic'
                    stat_metadata['stat_id'] = stat_idx
                    stat_metadata['stat_name'] = stat.get('name', '')
                    stat_metadata['stat_value'] = stat.get('value', '')
                    
                    document = self.create_document_from_text(stat_text, stat_metadata)
                    documents.append(document)
                    structured_document_count += 1

                # 타임라인 데이터
                timeline = structured_data.get('timeline', [])
                print(f"[DEBUG] 타임라인 수: {len(timeline)}")
                for timeline_idx, event in enumerate(timeline):
                    event_text = f"Timeline Event: {event.get('date', '')} - {event.get('event', '')}\n"
                    
                    # 타임라인 메타데이터
                    timeline_metadata = base_metadata.copy()
                    timeline_metadata['chunk_type'] = 'timeline'
                    timeline_metadata['timeline_id'] = timeline_idx
                    timeline_metadata['event_date'] = event.get('date', '')
                    timeline_metadata['event_description'] = event.get('event', '')
                    
                    document = self.create_document_from_text(event_text, timeline_metadata)
                    documents.append(document)
                    structured_document_count += 1
            
            print(f"[DEBUG] 파일 '{filename}'에서 생성된 구조화 데이터 문서 수: {structured_document_count}")
            print(f"[DEBUG] 파일 '{filename}' 총 문서 수: {file_document_count + structured_document_count}")
        
        print(f"[DEBUG] 정보 추출 결과 처리 완료: 총 {len(documents)}개 문서 생성")
        return documents
    
    def create_documents_from_ontology(self, ontology_data: Dict[str, Any]) -> List[Document]:
        """
        온톨로지 데이터로부터 Document 객체 리스트 생성
        
        Args:
            ontology_data (Dict[str, Any]): 온톨로지 데이터
            
        Returns:
            List[Document]: Document 객체 리스트
        """
        documents = []
        
        print(f"[DEBUG] 온톨로지 데이터 처리 시작")
        print(f"[DEBUG] 온톨로지 키들: {list(ontology_data.keys())}")
        
        entities = ontology_data.get('entities', [])
        relations = ontology_data.get('relations', [])
        
        print(f"[DEBUG] 엔티티 수: {len(entities)}, 관계 수: {len(relations)}")
        
        # 엔티티들을 그룹화하여 하나의 문서로 생성 (개별 문서 대신)
        if entities:
            # 엔티티들을 10개씩 묶어서 하나의 문서로 생성
            chunk_size = 10
            for i in range(0, len(entities), chunk_size):
                entity_chunk = entities[i:i+chunk_size]
                entity_text = "Entities: " + ", ".join(entity_chunk) + "\n"
                entity_text += "This document contains entity information from the knowledge base.\n"
                
                entity_metadata = {
                    'entity_names': entity_chunk,
                    'entity_type': 'entity_group',
                    'entity_count': len(entity_chunk),
                    'chunk_type': 'entity_group',
                    'source': 'ontology'
                }
                
                document = self.create_document_from_text(entity_text, entity_metadata)
                documents.append(document)
                print(f"[DEBUG] 엔티티 그룹 문서 생성: {len(entity_chunk)}개 엔티티")
        
        # 관계들을 그룹화하여 하나의 문서로 생성
        if relations:
            # 관계들을 5개씩 묶어서 하나의 문서로 생성
            chunk_size = 5
            for i in range(0, len(relations), chunk_size):
                relation_chunk = relations[i:i+chunk_size]
                relation_texts = []
                
                for relation in relation_chunk:
                    source = relation.get('source', '')
                    rel_type = relation.get('relation', '')
                    target = relation.get('target', '')
                    
                    if source and rel_type and target:
                        relation_texts.append(f"{source} {rel_type} {target}")
                
                if relation_texts:
                    relation_text = "Relations: " + "; ".join(relation_texts) + "\n"
                    relation_text += "This document contains relationship information from the knowledge base.\n"
                    
                    relation_metadata = {
                        'relation_count': len(relation_texts),
                        'entity_type': 'relation_group',
                        'chunk_type': 'relation_group',
                        'source': 'ontology'
                    }
                    
                    document = self.create_document_from_text(relation_text, relation_metadata)
                    documents.append(document)
                    print(f"[DEBUG] 관계 그룹 문서 생성: {len(relation_texts)}개 관계")
        
        print(f"[DEBUG] 온톨로지에서 생성된 총 문서 수: {len(documents)}")
        return documents
    
    def create_vector_db(self, 
                         documents: List[Document], 
                         index_name: str = "document_index") -> FAISS:
        """
        Document 리스트로부터 벡터 DB 생성
        
        Args:
            documents (List[Document]): Document 객체 리스트
            index_name (str): 인덱스 이름
            
        Returns:
            FAISS: 생성된 벡터 DB
        """
        if not documents:
            raise ValueError("Empty document list provided")
        
        # FAISS 벡터 DB 생성
        vectorstore = FAISS.from_documents(documents, self.embeddings)
        
        # 벡터 DB 저장
        self.save_vector_db(vectorstore, index_name)
        
        self.vectorstore = vectorstore
        return vectorstore
    
    def save_vector_db(self, 
                       vectorstore: FAISS, 
                       index_name: str = "document_index") -> str:
        """
        벡터 DB 저장
        
        Args:
            vectorstore (FAISS): 벡터 DB
            index_name (str): 인덱스 이름
            
        Returns:
            str: 저장 경로
        """
        save_path = os.path.join(self.vector_db_path, index_name)
        vectorstore.save_local(save_path)
        return save_path
    
    def load_vector_db(self, index_name: str = "document_index") -> Optional[FAISS]:
        """
        벡터 DB 로드
        
        Args:
            index_name (str): 인덱스 이름
            
        Returns:
            Optional[FAISS]: 로드된 벡터 DB 또는 None (로드 실패 시)
        """
        load_path = os.path.join(self.vector_db_path, index_name)
        
        if not os.path.exists(load_path):
            return None
        
        try:
            vectorstore = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
            self.vectorstore = vectorstore
            return vectorstore
        except Exception as e:
            print(f"Error loading vector DB: {e}")
            return None
    
    def add_documents(self, 
                      documents: List[Document], 
                      index_name: str = "document_index") -> bool:
        """
        기존 벡터 DB에 Document 추가
        
        Args:
            documents (List[Document]): 추가할 Document 리스트
            index_name (str): 인덱스 이름
            
        Returns:
            bool: 성공 여부
        """
        if not documents:
            return False
            
        # 벡터 DB 로드 또는 생성
        if self.vectorstore is None:
            vectorstore = self.load_vector_db(index_name)
            if vectorstore is None:
                self.create_vector_db(documents, index_name)
                return True
        
        # 기존 DB에 추가
        try:
            self.vectorstore.add_documents(documents)
            self.save_vector_db(self.vectorstore, index_name)
            return True
        except Exception as e:
            print(f"Error adding documents to vector DB: {e}")
            return False
    
    def similarity_search(self, 
                          query: str, 
                          k: int = 5,
                          index_name: str = "document_index") -> List[Tuple[Document, float]]:
        """
        유사도 검색 수행
        
        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수
            index_name (str): 인덱스 이름
            
        Returns:
            List[Tuple[Document, float]]: 검색 결과와 유사도 점수
        """
        # 벡터 DB 로드
        if self.vectorstore is None:
            vectorstore = self.load_vector_db(index_name)
            if vectorstore is None:
                return []
            self.vectorstore = vectorstore
        
        # 유사도 검색 실행
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        return docs_with_scores
    
    def filter_search(self, 
                      query: str, 
                      filter_dict: Dict[str, Any], 
                      k: int = 5,
                      index_name: str = "document_index") -> List[Tuple[Document, float]]:
        """
        필터를 적용한 유사도 검색 수행
        
        Args:
            query (str): 검색 쿼리
            filter_dict (Dict[str, Any]): 필터 조건
            k (int): 반환할 결과 수
            index_name (str): 인덱스 이름
            
        Returns:
            List[Tuple[Document, float]]: 검색 결과와 유사도 점수
        """
        # 벡터 DB 로드
        if self.vectorstore is None:
            vectorstore = self.load_vector_db(index_name)
            if vectorstore is None:
                return []
            self.vectorstore = vectorstore
        
        # 필터 검색 실행
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query, k=k, filter=filter_dict)
        return docs_with_scores
    
    def get_most_similar_documents(self, documents: List[Document], top_n: int = 10) -> List[List[Tuple[Document, float]]]:
        """
        문서 간 유사도를 계산하여 각 문서와 가장 유사한 문서들 반환
        
        Args:
            documents (List[Document]): 문서 리스트
            top_n (int): 각 문서마다 반환할 유사 문서 수
            
        Returns:
            List[List[Tuple[Document, float]]]: 각 문서별 유사 문서 리스트
        """
        if not documents:
            return []
            
        # 임시 벡터 DB 생성
        temp_db = FAISS.from_documents(documents, self.embeddings)
        
        similar_docs_list = []
        for doc in documents:
            # 문서 내용으로 유사 문서 검색
            similar_docs = temp_db.similarity_search_with_score(doc.page_content, k=top_n+1)
            # 자신을 제외한 유사 문서 반환
            similar_docs = [d for d in similar_docs if d[0].page_content != doc.page_content][:top_n]
            similar_docs_list.append(similar_docs)
            
        return similar_docs_list
    
    def generate_embeddings_report(self, index_name: str = "document_index") -> Dict[str, Any]:
        """
        임베딩 통계 리포트 생성
        
        Args:
            index_name (str): 인덱스 이름
            
        Returns:
            Dict[str, Any]: 통계 리포트
        """
        # 벡터 DB 로드
        if self.vectorstore is None:
            vectorstore = self.load_vector_db(index_name)
            if vectorstore is None:
                return {"error": "Vector DB not found"}
            self.vectorstore = vectorstore
        
        # 문서 수
        doc_count = len(self.vectorstore.docstore._dict)
        
        # 메타데이터 통계
        metadata_stats = {}
        for doc_id, doc in self.vectorstore.docstore._dict.items():
            for key, value in doc.metadata.items():
                if key not in metadata_stats:
                    metadata_stats[key] = {}
                
                str_value = str(value)
                if str_value not in metadata_stats[key]:
                    metadata_stats[key][str_value] = 0
                metadata_stats[key][str_value] += 1
        
        # 문서 타입별 통계
        doc_types = {}
        for doc_id, doc in self.vectorstore.docstore._dict.items():
            doc_type = doc.metadata.get('chunk_type', 'unknown')
            if doc_type not in doc_types:
                doc_types[doc_type] = 0
            doc_types[doc_type] += 1
        
        # 파일별 문서 수
        file_stats = {}
        for doc_id, doc in self.vectorstore.docstore._dict.items():
            filename = doc.metadata.get('filename', 'unknown')
            if filename not in file_stats:
                file_stats[filename] = 0
            file_stats[filename] += 1
        
        return {
            "document_count": doc_count,
            "document_types": doc_types,
            "file_statistics": file_stats,
            "metadata_statistics": metadata_stats
        }


def main():
    """테스트용 메인 함수"""
    
    # 임시 테스트용 문서
    test_documents = [
        Document(
            page_content="미국이 중국산 전기차에 100% 관세를 부과하기로 결정했습니다.",
            metadata={"filename": "news1.txt", "source": "test", "category": "news"}
        ),
        Document(
            page_content="전기차 관세 인상으로 테슬라 주가가 상승했습니다.",
            metadata={"filename": "news2.txt", "source": "test", "category": "news"}
        ),
        Document(
            page_content="중국의 배터리 기업들은 미국의 관세 정책에 대응책을 마련하고 있습니다.",
            metadata={"filename": "news3.txt", "source": "test", "category": "news"}
        ),
        Document(
            page_content="한국 배터리 기업들은 미국과 중국 간 무역 분쟁의 반사이익을 얻을 것으로 예상됩니다.",
            metadata={"filename": "news4.txt", "source": "test", "category": "analysis"}
        )
    ]
    
    # 임베딩 매니저 생성
    embedding_manager = EmbeddingManager()
    
    # 벡터 DB 생성
    vectorstore = embedding_manager.create_vector_db(test_documents, "test_index")
    print(f"벡터 DB가 생성되었습니다: {embedding_manager.vector_db_path}/test_index")
    
    # 검색 테스트
    query = "미국의 중국 전기차 관세 정책"
    results = embedding_manager.similarity_search(query, k=2, index_name="test_index")
    print(f"\n검색 쿼리: '{query}'")
    print("검색 결과:")
    for doc, score in results:
        print(f"- 문서: {doc.page_content}")
        print(f"  점수: {score:.4f}")
        print(f"  메타데이터: {doc.metadata}")
    
    # 필터 검색 테스트
    filter_query = "배터리 기업"
    filter_dict = {"category": "analysis"}
    filter_results = embedding_manager.filter_search(
        filter_query, filter_dict, k=2, index_name="test_index")
    print(f"\n필터 검색 쿼리: '{filter_query}'")
    print(f"필터 조건: {filter_dict}")
    print("필터 검색 결과:")
    for doc, score in filter_results:
        print(f"- 문서: {doc.page_content}")
        print(f"  점수: {score:.4f}")
        print(f"  메타데이터: {doc.metadata}")
    
    # 통계 리포트
    report = embedding_manager.generate_embeddings_report("test_index")
    print("\n임베딩 통계 리포트:")
    print(f"총 문서 수: {report['document_count']}")
    print("문서 타입별 통계:")
    for doc_type, count in report.get('document_types', {}).items():
        print(f"- {doc_type}: {count}개")
    print("파일별 문서 수:")
    for filename, count in report.get('file_statistics', {}).items():
        print(f"- {filename}: {count}개")

if __name__ == "__main__":
    main() 