"""
DX-AI Manufacturing Copilot - Chatbot 데이터 모델
챗봇 서비스에서 사용되는 모든 데이터 모델 정의
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")
    timestamp: str = Field(..., description="타임스탬프")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str = Field(..., description="사용자 메시지")
    topic: Optional[str] = Field("process_analysis", description="주제")
    session_id: Optional[str] = Field("default", description="세션 ID")
    context: Optional[str] = Field(None, description="추가 컨텍스트")
    simulation_params: Optional[Dict[str, Any]] = Field(None, description="시뮬레이션 파라미터")
    model: Optional[str] = Field(None, description="사용할 모델")
    temperature: Optional[float] = Field(None, description="창의성 설정")


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    message: str = Field(..., description="AI 응답")
    session_id: str = Field(..., description="세션 ID")
    topic: str = Field(..., description="주제")
    turn_count: int = Field(..., description="대화 턴 수")
    timestamp: str = Field(..., description="타임스탬프")
    model_used: str = Field(..., description="사용된 모델")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")


class ChatSession(BaseModel):
    """채팅 세션 모델"""
    session_id: str = Field(..., description="세션 ID")
    topic: str = Field(..., description="주제")
    turn_count: int = Field(..., description="대화 턴 수")
    message_count: int = Field(..., description="메시지 수")
    created_at: str = Field(..., description="생성 시간")
    model_used: str = Field(..., description="사용된 모델")


class StreamData(BaseModel):
    """스트리밍 데이터 모델"""
    type: str = Field(..., description="데이터 타입 (session_info, content, done, error)")
    content: Optional[str] = Field(None, description="내용")
    session_id: Optional[str] = Field(None, description="세션 ID")
    topic: Optional[str] = Field(None, description="주제")
    turn_count: Optional[int] = Field(None, description="대화 턴 수")
    model_used: Optional[str] = Field(None, description="사용된 모델")
    error: Optional[str] = Field(None, description="에러 메시지")
    timestamp: Optional[str] = Field(None, description="타임스탬프")


class ChatConfig(BaseModel):
    """챗봇 설정 모델"""
    current_model: str = Field(..., description="현재 모델")
    temperature: float = Field(..., description="창의성 설정")
    max_tokens: int = Field(..., description="최대 토큰 수")
    max_turn_count: int = Field(..., description="최대 턴 수")
    ollama_base_url: str = Field(..., description="Ollama 베이스 URL")
    enable_streaming: bool = Field(..., description="스트리밍 활성화 여부")


class ChatConfigRequest(BaseModel):
    """설정 변경 요청 모델"""
    model: Optional[str] = Field(None, description="모델")
    temperature: Optional[float] = Field(None, description="창의성 설정")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")
    max_turn_count: Optional[int] = Field(None, description="최대 턴 수")
    enable_streaming: Optional[bool] = Field(None, description="스트리밍 활성화 여부") 