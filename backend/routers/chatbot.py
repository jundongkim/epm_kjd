"""
DX-AI Manufacturing Copilot - 챗봇 API 라우터
스트리밍 채팅 및 설정 관리 엔드포인트
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse

from src.ai.chatbot.service import get_chatbot_service, ChatbotService
from src.ai.core.context_engineering import get_context_engineer, ContextEngineer
from src.ai.chatbot.models import (
    ChatRequest, ChatResponse, ChatSession, ChatConfig, 
    ChatConfigRequest, StreamData
)
from src.copilot.data_models import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
    context_engineer: ContextEngineer = Depends(get_context_engineer)
):
    """스트리밍 채팅"""
    try:
        # 컨텍스트 생성
        context = context_engineer.create_context(
            topic=request.topic,
            simulation_params=request.simulation_params,
            user_query=request.message
        )
        
        if request.context:
            context = f"{context}\n\n### 추가 컨텍스트\n{request.context}"
        
        async def generate_stream():
            """스트리밍 생성기"""
            try:
                # 세션 정보 전송
                session_info = chatbot_service.get_session_info(request.session_id)
                initial_data = {
                    "type": "session_info",
                    "session_id": request.session_id,
                    "topic": request.topic,
                    "turn_count": session_info.get("turn_count", 0),
                    "model_used": chatbot_service.model
                }
                yield f"{json.dumps(initial_data)}\n\n"
                
                # 스트리밍 시작
                async for chunk in chatbot_service.chat_stream(
                    message=request.message,
                    context=context,
                    topic=request.topic,
                    session_id=request.session_id
                ):
                    data = {
                        "type": "content",
                        "content": chunk,
                        "session_id": request.session_id
                    }
                    yield f"{json.dumps(data)}\n\n"
                
                # 완료 신호
                final_data = {
                    "type": "done",
                    "session_id": request.session_id,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"{json.dumps(final_data)}\n\n"
                
            except Exception as e:
                logger.error(f"스트리밍 생성 오류: {e}")
                error_data = {
                    "type": "error",
                    "error": str(e),
                    "session_id": request.session_id
                }
                yield f"{json.dumps(error_data)}\n\n"
        
        return EventSourceResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"스트리밍 채팅 처리 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"스트리밍 채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/config", response_model=ChatConfig)
async def get_chat_config(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """현재 설정 조회"""
    try:
        config = chatbot_service.get_config()
        return ChatConfig(**config)
    except Exception as e:
        logger.error(f"설정 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/config", response_model=ChatConfig)
async def update_chat_config(
    config: ChatConfigRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """설정 업데이트"""
    try:
        # 설정 업데이트
        update_data = {}
        if config.model is not None:
            update_data["model"] = config.model
        if config.temperature is not None:
            update_data["temperature"] = config.temperature
        if config.max_tokens is not None:
            update_data["max_tokens"] = config.max_tokens
        if config.max_turn_count is not None:
            update_data["max_turn_count"] = config.max_turn_count
        if config.enable_streaming is not None:
            update_data["enable_streaming"] = config.enable_streaming
        
        if update_data:
            # 모델이 변경된 경우 새로운 서비스 인스턴스 필요
            if "model" in update_data:
                from src.ai.chatbot.service import clear_chatbot_instances, get_chatbot_service, set_current_model
                # 전역 활성 모델 변경
                set_current_model(update_data["model"])
                # 모든 기존 인스턴스 정리
                clear_chatbot_instances()
                # 새 모델로 서비스 인스턴스 생성
                chatbot_service = get_chatbot_service(update_data["model"])
            else:
                chatbot_service.update_config(**update_data)
        
        # max_turn_count는 서비스 레벨에서 별도 처리
        if config.max_turn_count is not None:
            chatbot_service.max_turn_count = config.max_turn_count
        
        # 업데이트된 설정 반환
        updated_config = chatbot_service.get_config()
        return ChatConfig(**updated_config)
        
    except Exception as e:
        logger.error(f"설정 업데이트 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"설정 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=ChatSession)
async def get_session_info(
    session_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """세션 정보 조회"""
    try:
        session_info = chatbot_service.get_session_info(session_id)
        if "error" in session_info:
            raise HTTPException(status_code=404, detail=session_info["error"])
        
        return ChatSession(**session_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 정보 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"세션 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/session/{session_id}", response_model=ApiResponse)
async def reset_session(
    session_id: str,
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """세션 초기화"""
    try:
        success = chatbot_service.reset_session(session_id)
        
        if success:
            return ApiResponse(
                success=True,
                message=f"세션 '{session_id}'가 성공적으로 초기화되었습니다.",
                data={"session_id": session_id}
            )
        else:
            return ApiResponse(
                success=False,
                message=f"세션 '{session_id}' 초기화에 실패했습니다.",
                error_code="SESSION_RESET_FAILED"
            )
            
    except Exception as e:
        logger.error(f"세션 초기화 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"세션 초기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health", response_model=ApiResponse)
async def health_check(
    chatbot_service: ChatbotService = Depends(get_chatbot_service)
):
    """챗봇 서비스 헬스체크"""
    try:
        config = chatbot_service.get_config()
        
        return ApiResponse(
            success=True,
            message="챗봇 서비스가 정상적으로 작동 중입니다.",
            data={
                "model": config["current_model"],
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"헬스체크 오류: {e}")
        return ApiResponse(
            success=False,
            message=f"챗봇 서비스에 문제가 있습니다: {str(e)}",
            error_code="SERVICE_UNHEALTHY"
        ) 