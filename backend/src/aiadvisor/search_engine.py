"""
검색 엔진 모듈

`EmbeddingManager`를 활용한 고급 검색 기능을 제공합니다.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .utils import AIAdvisorException
from .embedding import EmbeddingManager


logger = logging.getLogger(__name__)


class VectorSearchEngine:
    """벡터 검색 엔진 클래스 - 고급 검색 기능 제공"""

    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager
        self.search_history: List[Dict[str, Any]] = []

    async def hybrid_search(self, query: str, ontology_context: Optional[Dict[str, Any]] = None, k: int = 5) -> Dict[str, Any]:
        """하이브리드 검색 - 벡터 검색 + 온톨로지 컨텍스트"""
        try:
            # 1. 기본 벡터 검색
            vector_results = await self.embedding_manager.search_similar_documents(query, k=k)

            # 2. 온톨로지 컨텍스트가 있는 경우 컨텍스트 기반 검색
            ontology_results: List[Dict[str, Any]] = []
            if ontology_context:
                ontology_results = await self._search_with_ontology_context(query, ontology_context, k=k)

            # 3. 결과 통합 및 점수 조정
            integrated_results = self._integrate_search_results(vector_results, ontology_results)

            # 4. 검색 기록 저장
            search_record = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "vector_results_count": len(vector_results),
                "ontology_results_count": len(ontology_results),
                "integrated_results_count": len(integrated_results),
                "used_ontology": ontology_context is not None,
            }
            self.search_history.append(search_record)

            return {
                "query": query,
                "search_type": "hybrid",
                "results": integrated_results[:k],
                "vector_results": vector_results,
                "ontology_results": ontology_results,
                "search_metadata": search_record,
            }

        except Exception as e:
            logger.error(f"하이브리드 검색 오류: {str(e)}")
            raise AIAdvisorException(f"하이브리드 검색 중 오류 발생: {str(e)}")

    async def _search_with_ontology_context(self, query: str, ontology_context: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        """온톨로지 컨텍스트를 활용한 검색"""
        try:
            # 온톨로지에서 관련 엔티티 추출
            related_entities = ontology_context.get("entities", [])

            # 확장된 쿼리 생성
            expanded_query_terms = [query]

            # 관련 엔티티 추가
            for entity in related_entities[:5]:  # 최대 5개까지
                if entity.get("name"):
                    expanded_query_terms.append(entity["name"])

            # 확장된 쿼리로 검색
            expanded_query = " ".join(expanded_query_terms)

            results = await self.embedding_manager.search_similar_documents(expanded_query, k=k)

            # 온톨로지 컨텍스트 정보 추가
            for result in results:
                result["search_type"] = "ontology_enhanced"
                result["ontology_context"] = ontology_context
                result["expanded_query"] = expanded_query

            return results

        except Exception as e:
            logger.error(f"온톨로지 컨텍스트 검색 오류: {str(e)}")
            return []

    def _integrate_search_results(self, vector_results: List[Dict[str, Any]], ontology_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """검색 결과 통합"""
        try:
            integrated: List[Dict[str, Any]] = []
            seen_contents = set()

            # 벡터 검색 결과 우선 추가
            for result in vector_results:
                content_hash = hash(result["content"][:200])  # 첫 200자로 중복 체크
                if content_hash not in seen_contents:
                    result["integration_score"] = result["similarity_score"] * 1.0  # 원본 점수 유지
                    result["source"] = "vector_search"
                    integrated.append(result)
                    seen_contents.add(content_hash)

            # 온톨로지 결과 추가 (중복되지 않는 것만)
            for result in ontology_results:
                content_hash = hash(result["content"][:200])
                if content_hash not in seen_contents:
                    result["integration_score"] = result["similarity_score"] * 0.8  # 가중치 조정
                    result["source"] = "ontology_enhanced"
                    integrated.append(result)
                    seen_contents.add(content_hash)

            # 통합 점수로 정렬
            integrated.sort(key=lambda x: x["integration_score"], reverse=True)

            return integrated

        except Exception as e:
            logger.error(f"검색 결과 통합 오류: {str(e)}")
            # 오류 발생 시 벡터 검색 결과만 반환
            return vector_results

    async def semantic_search_with_expansion(self, query: str, expansion_terms: Optional[List[str]] = None, k: int = 5) -> List[Dict[str, Any]]:
        """의미론적 검색 with 쿼리 확장"""
        try:
            expanded_terms = [query]

            if expansion_terms:
                expanded_terms.extend(expansion_terms)

            # 확장된 쿼리로 검색
            expanded_query = " ".join(expanded_terms)
            results = await self.embedding_manager.search_similar_documents(expanded_query, k=k)

            # 확장 정보 추가
            for result in results:
                result["original_query"] = query
                result["expanded_query"] = expanded_query
                result["expansion_terms"] = expansion_terms or []
                result["search_type"] = "semantic_expanded"

            return results

        except Exception as e:
            logger.error(f"의미론적 확장 검색 오류: {str(e)}")
            raise AIAdvisorException(f"의미론적 확장 검색 중 오류 발생: {str(e)}")

    async def multi_query_search(self, queries: List[str], k: int = 5) -> Dict[str, Any]:
        """다중 쿼리 검색"""
        try:
            all_results: Dict[str, List[Dict[str, Any]]] = {}
            combined_results: List[Dict[str, Any]] = []

            for query in queries:
                results = await self.embedding_manager.search_similar_documents(query, k=k)
                all_results[query] = results

                # 쿼리 정보 추가
                for result in results:
                    result["source_query"] = query
                    result["search_type"] = "multi_query"

                combined_results.extend(results)

            # 중복 제거 및 점수 기반 정렬
            unique_results: List[Dict[str, Any]] = []
            seen_contents = set()

            for result in combined_results:
                content_hash = hash(result["content"][:200])
                if content_hash not in seen_contents:
                    unique_results.append(result)
                    seen_contents.add(content_hash)

            # 유사도 점수로 정렬
            unique_results.sort(key=lambda x: x["similarity_score"], reverse=True)

            return {
                "queries": queries,
                "individual_results": all_results,
                "combined_results": unique_results[: k * 2],  # 더 많이 반환
                "search_type": "multi_query",
                "total_unique_results": len(unique_results),
            }

        except Exception as e:
            logger.error(f"다중 쿼리 검색 오류: {str(e)}")
            raise AIAdvisorException(f"다중 쿼리 검색 중 오류 발생: {str(e)}")

    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """검색 기록 조회"""
        return self.search_history[-limit:]

    def clear_search_history(self) -> None:
        """검색 히스토리 초기화"""
        self.search_history.clear()


