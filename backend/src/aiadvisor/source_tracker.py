"""
출처 추적 및 표시 모듈

AI 어드바이저의 답변에서 참조한 문서와 페이지 정보를 추적하고 표시하는 기능
"""

import re
from typing import Dict, List, Any, Set, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SourceTracker:
    """출처 추적 및 관리 클래스"""
    
    def __init__(self):
        self.used_sources = set()  # 사용된 문서 ID 집합
        self.source_details = defaultdict(set)  # 문서별 페이지 정보
        self.source_metadata = {}  # 문서 메타데이터 캐시
    
    def add_source(self, document_id: str, metadata: Dict[str, Any], page_info: Optional[str] = None):
        """출처 정보 추가"""
        try:
            self.used_sources.add(document_id)
            
            # 문서 메타데이터 캐시
            if document_id not in self.source_metadata:
                self.source_metadata[document_id] = metadata
            
            # 페이지 정보 추가
            if page_info:
                self.source_details[document_id].add(page_info)
            else:
                # 페이지 정보가 없으면 기본값 추가
                self.source_details[document_id].add("전체")
                
        except Exception as e:
            logger.error(f"출처 정보 추가 오류: {str(e)}")
    
    def extract_page_info(self, content: str) -> Optional[str]:
        """콘텐츠에서 페이지 정보 추출"""
        try:
            # "--- 페이지 X ---" 패턴 찾기
            page_match = re.search(r'---\s*페이지\s*(\d+)\s*---', content)
            if page_match:
                return f"{page_match.group(1)}페이지"
            
            # "슬라이드 X" 패턴 찾기 (PPTX)
            slide_match = re.search(r'---\s*슬라이드\s*(\d+)\s*---', content)
            if slide_match:
                return f"{slide_match.group(1)}슬라이드"
            
            return None
            
        except Exception as e:
            logger.error(f"페이지 정보 추출 오류: {str(e)}")
            return None
    
    def get_formatted_sources(self) -> str:
        """포맷된 출처 정보 반환"""
        try:
            if not self.used_sources:
                return ""
            
            source_lines = []
            source_lines.append("\n\n--- 📚 참고 문서 ---")
            
            for doc_id in sorted(self.used_sources):
                metadata = self.source_metadata.get(doc_id, {})
                filename = metadata.get('filename', f'문서_{doc_id}')
                
                # 고유 코드 제거하고 원본 제목만 추출
                original_filename = self._extract_original_filename(filename)
                
                # 페이지 정보 정리
                pages = sorted(self.source_details[doc_id])
                if len(pages) == 1 and pages[0] == "전체":
                    page_info = "전체"
                else:
                    # 페이지 번호 정렬 (숫자 추출 후 정렬)
                    def extract_page_num(page_str):
                        match = re.search(r'(\d+)', page_str)
                        return int(match.group(1)) if match else 0
                    
                    sorted_pages = sorted(pages, key=extract_page_num)
                    page_info = ", ".join(sorted_pages)
                
                source_lines.append(f"• {original_filename} ({page_info})")
            
            return "\n".join(source_lines)
            
        except Exception as e:
            logger.error(f"출처 정보 포맷 오류: {str(e)}")
            return "\n\n--- 📚 참고 문서 ---\n(출처 정보 처리 중 오류 발생)"
    
    def _extract_original_filename(self, filename: str) -> str:
        """파일명에서 고유 코드를 제거하고 원본 제목만 추출"""
        try:
            # temp_로 시작하는 고유 코드 패턴 제거
            # 예: temp_d1293ca6-57d5-4d11-911d-d51d0c8d4fac__AIIndex2025주요내용과시사점.pdf
            # → AIIndex2025주요내용과시사점.pdf
            
            # UUID 패턴 매칭 (8-4-4-4-12 형식)
            uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}__'
            
            # temp_ 접두사와 UUID 패턴 제거
            if filename.startswith('temp_'):
                # temp_ 제거
                filename = filename[5:]
                # UUID 패턴 제거
                filename = re.sub(uuid_pattern, '', filename)
            
            # 다른 고유 코드 패턴들도 처리
            # 숫자와 하이픈으로 구성된 패턴 (예: 1754445397__)
            timestamp_pattern = r'^\d+__'
            filename = re.sub(timestamp_pattern, '', filename)
            
            # 빈 문자열이 되면 원본 반환
            if not filename.strip():
                return filename
            
            return filename.strip()
            
        except Exception as e:
            logger.error(f"원본 파일명 추출 오류: {str(e)}")
            return filename
    
    def clear(self):
        """출처 정보 초기화"""
        self.used_sources.clear()
        self.source_details.clear()
        self.source_metadata.clear()
    
    def get_source_summary(self) -> Dict[str, Any]:
        """출처 요약 정보 반환"""
        try:
            summary = {
                "total_sources": len(self.used_sources),
                "sources": []
            }
            
            for doc_id in sorted(self.used_sources):
                metadata = self.source_metadata.get(doc_id, {})
                pages = sorted(self.source_details[doc_id])
                
                summary["sources"].append({
                    "document_id": doc_id,
                    "filename": metadata.get('filename', f'문서_{doc_id}'),
                    "pages": pages,
                    "file_size": metadata.get('file_size', ''),
                    "category": metadata.get('category', 'general')
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"출처 요약 생성 오류: {str(e)}")
            return {"total_sources": 0, "sources": []}


class StreamingSourceTracker:
    """스트리밍 응답용 출처 추적기"""
    
    def __init__(self):
        self.tracker = SourceTracker()
        self.response_content = ""
        self.is_complete = False
    
    def add_search_results(self, search_results: List[Dict[str, Any]]):
        """검색 결과에서 출처 정보 추출"""
        try:
            for result in search_results:
                metadata = result.get("metadata", {})
                content = result.get("content", "")
                
                # document_id 추출 (여러 키 시도)
                document_id = metadata.get("document_id") or metadata.get("id") or metadata.get("filename", "")
                
                if document_id:
                    # 페이지 정보 추출
                    page_info = self.tracker.extract_page_info(content)
                    self.tracker.add_source(document_id, metadata, page_info)
                    
        except Exception as e:
            logger.error(f"검색 결과 출처 추적 오류: {str(e)}")
    
    def add_response_chunk(self, chunk: str):
        """응답 청크 추가"""
        self.response_content += chunk
    
    def get_final_response_with_sources(self) -> str:
        """출처 정보가 포함된 최종 응답 반환"""
        try:
            if not self.response_content.strip():
                return ""
            
            # 출처 정보 추가
            sources_text = self.tracker.get_formatted_sources()
            if sources_text:
                return self.response_content + sources_text
            else:
                return self.response_content
                
        except Exception as e:
            logger.error(f"최종 응답 생성 오류: {str(e)}")
            return self.response_content
    
    def get_source_summary(self) -> Dict[str, Any]:
        """출처 요약 반환"""
        return self.tracker.get_source_summary()
    
    def clear(self):
        """초기화"""
        self.tracker.clear()
        self.response_content = ""
        self.is_complete = False