"""
AI Advisor - 고급 스트리밍 라우터

기존 `routers/aiadvisor.py`의 고급 스트리밍 엔드포인트를 분리했습니다.
경로는 변경 없이 `/aiadvisor/advanced/*`를 유지합니다.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from src.aiadvisor import (
    EmbeddingManager,
    OntologyManager,
    AdvisorAgentManager,
    AIAdvisorConfig,
    get_config as get_aiadvisor_config,
)


logger = logging.getLogger(__name__)

# 부모 라우터(`/aiadvisor`)에 include될 것을 가정하고 하위 prefix만 설정
router = APIRouter(prefix="/advanced", tags=["AI Advisor Advanced"])

# 내부 의존성 (메인 라우터와 독립적으로 동작)
_config: Optional[AIAdvisorConfig] = None
_embedding_manager: Optional[EmbeddingManager] = None
_ontology_manager: Optional[OntologyManager] = None
_agent_manager: Optional[AdvisorAgentManager] = None


async def get_config() -> AIAdvisorConfig:
    global _config
    if _config is None:
        _config = get_aiadvisor_config()
    return _config


async def get_embedding_manager() -> EmbeddingManager:
    global _embedding_manager
    if _embedding_manager is None:
        config = await get_config()
        _embedding_manager = EmbeddingManager(config)
    return _embedding_manager


async def get_ontology_manager() -> OntologyManager:
    global _ontology_manager
    if _ontology_manager is None:
        config = await get_config()
        _ontology_manager = OntologyManager(config)
    return _ontology_manager


async def get_agent_manager() -> AdvisorAgentManager:
    global _agent_manager
    if _agent_manager is None:
        config = await get_config()
        _agent_manager = AdvisorAgentManager(config)
    return _agent_manager


@router.post("/stream")
async def advanced_stream_query(
    request: Dict[str, Any],
    agent_manager: AdvisorAgentManager = Depends(get_agent_manager),
    embedding_manager: EmbeddingManager = Depends(get_embedding_manager),
    ontology_manager: OntologyManager = Depends(get_ontology_manager),
):
    """고급 스트리밍 질의 (컨텍스트 강화 + 실시간 피드백)"""
    try:
        user_query: str = request.get("query", "")
        agent_id: Optional[str] = request.get("agent_id")
        use_workflow: bool = request.get("use_workflow", True)
        k: int = request.get("k", 5)
        include_metadata: bool = request.get("include_metadata", True)
        stream_format: str = request.get("stream_format", "text")  # text, json, sse

        if not user_query:
            raise HTTPException(status_code=400, detail="질의 내용이 없습니다.")

        # 문서 검색을 통한 컨텍스트 추가
        search_results = []
        try:
            search_results = await embedding_manager.search_documents(user_query, k=k)
        except Exception as search_error:
            logger.warning(f"문서 검색 실패: {str(search_error)}")

        # 온톨로지에서 관련 정보 검색
        ontology_context: Dict[str, Any] = {}
        try:
            ontology_context = await ontology_manager.search_entities(user_query)
        except Exception as ont_error:
            logger.warning(f"온톨로지 검색 실패: {str(ont_error)}")

        # 컨텍스트를 포함한 질문 구성
        enhanced_query = f"""
질문: {user_query}

관련 문서 정보:
{json.dumps(search_results, ensure_ascii=False, indent=2) if search_results else "관련 문서가 없습니다."}

온톨로지 정보:
{json.dumps(ontology_context, ensure_ascii=False, indent=2) if ontology_context else "관련 온톨로지 정보가 없습니다."}

위 정보를 참고하여 질문에 답변해주세요.
"""

        # 에이전트 가져오기
        if agent_id:
            agent = await agent_manager.get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail="지정된 에이전트를 찾을 수 없습니다.")
        else:
            agent = await agent_manager.get_default_agent()

        # 스트리밍 응답 생성
        async def generate_advanced_response():
            try:
                # 메타데이터 스트리밍 (선택사항)
                if include_metadata:
                    metadata_chunk = {
                        "type": "metadata",
                        "query": user_query,
                        "search_results_count": len(search_results),
                        "ontology_entities_count": len(ontology_context),
                        "timestamp": datetime.now().isoformat(),
                    }
                    if stream_format == "json":
                        yield f"data: {json.dumps(metadata_chunk, ensure_ascii=False)}\n\n"
                    else:
                        yield f"metadata: {json.dumps(metadata_chunk, ensure_ascii=False)}\n"

                # 컨텍스트 정보 스트리밍 (선택사항)
                if include_metadata and search_results:
                    context_chunk = {
                        "type": "context",
                        "search_results": search_results[:2],  # 처음 2개만
                        "ontology_context": ontology_context,
                    }
                    if stream_format == "json":
                        yield f"data: {json.dumps(context_chunk, ensure_ascii=False)}\n\n"
                    else:
                        yield f"context: {json.dumps(context_chunk, ensure_ascii=False)}\n"

                # 메인 응답 스트리밍
                response_started = False
                async for chunk in agent.stream_response(enhanced_query):
                    if not response_started:
                        response_started = True
                        # 응답 시작 신호
                        start_chunk = {
                            "type": "response_start",
                            "timestamp": datetime.now().isoformat(),
                        }
                        if stream_format == "json":
                            yield f"data: {json.dumps(start_chunk, ensure_ascii=False)}\n\n"
                        else:
                            yield f"start: {json.dumps(start_chunk, ensure_ascii=False)}\n"

                    # 실제 응답 내용
                    if stream_format == "json":
                        response_chunk = {
                            "type": "response_chunk",
                            "content": chunk,
                            "timestamp": datetime.now().isoformat(),
                        }
                        yield f"data: {json.dumps(response_chunk, ensure_ascii=False)}\n\n"
                    else:
                        yield f"chunk: {chunk}\n"

                # 응답 완료 신호
                end_chunk = {
                    "type": "response_end",
                    "timestamp": datetime.now().isoformat(),
                    "total_chunks": "completed",
                }
                if stream_format == "json":
                    yield f"data: {json.dumps(end_chunk, ensure_ascii=False)}\n\n"
                else:
                    yield f"end: {json.dumps(end_chunk, ensure_ascii=False)}\n"

            except Exception as e:
                error_chunk = {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                if stream_format == "json":
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                else:
                    yield f"error: {json.dumps(error_chunk, ensure_ascii=False)}\n"

        # 스트리밍 응답 반환
        if stream_format == "sse":
            return StreamingResponse(
                generate_advanced_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control",
                },
            )
        else:
            return StreamingResponse(
                generate_advanced_response(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )

    except Exception as e:
        logger.error(f"고급 스트리밍 질의 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"고급 스트리밍 처리 실패: {str(e)}")


