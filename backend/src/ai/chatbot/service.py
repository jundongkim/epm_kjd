"""
DX-AI Manufacturing Copilot - Chatbot 서비스
LangGraph 기반 상태 관리와 스트리밍 채팅 기능
새로운 AI 모듈 구조에 맞게 리팩토링된 버전
"""

import asyncio
import logging
from typing import Dict, List, Optional, TypedDict, AsyncGenerator, Annotated, Any
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from ..core.base import BaseAIService, SessionManager, ContextManager
from ..providers.ollama import OllamaProvider, get_ollama_provider
from ..core.context_engineering import get_context_engineer
from ...copilot.config import settings

logger = logging.getLogger(__name__)


class ChatbotState(TypedDict):
    """챗봇 상태 정의"""
    messages: Annotated[List[BaseMessage], add_messages]
    context: str
    topic: str
    turn_count: int
    session_id: str


class ChatbotService(BaseAIService):
    """LangGraph 기반 챗봇 서비스"""
    
    def __init__(self, 
                 model: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2048,
                 max_turn_count: int = 10):
        """
        챗봇 서비스 초기화
        
        Args:
            model: 사용할 모델 이름
            temperature: 생성 온도
            max_tokens: 최대 토큰 수
            max_turn_count: 최대 대화 턴 수
        """
        # Ollama 제공자 초기화
        provider = get_ollama_provider(
            model=model or settings.ollama_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 부모 클래스 초기화
        super().__init__("ChatbotService", provider)
        
        self.max_turn_count = max_turn_count
        
        # 메모리 저장소 및 그래프 초기화
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
        # 컨텍스트 엔지니어
        self.context_engineer = get_context_engineer()
        
        # 세션 관리자 초기화
        self.session_manager = SessionManager(max_sessions=1000)
        
        # 컨텍스트 관리자 초기화
        self.context_manager = ContextManager(max_context_length=10000)
        
        logger.info(f"챗봇 서비스 초기화 완료: {provider.model}")
    
    @property
    def model(self) -> str:
        """현재 사용 중인 모델"""
        return self.provider.model
    
    def _create_graph(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(ChatbotState)
        
        # 노드 추가
        workflow.add_node("context_processor", self._process_context)
        workflow.add_node("chatbot", self._chatbot_node)
        workflow.add_node("response_formatter", self._format_response)
        
        # 엣지 추가
        workflow.add_edge(START, "context_processor")
        workflow.add_edge("context_processor", "chatbot")
        workflow.add_edge("chatbot", "response_formatter")
        workflow.add_edge("response_formatter", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _process_context(self, state: ChatbotState) -> Dict:
        """컨텍스트 처리 노드"""
        context = state.get("context", "")
        topic = state.get("topic", "general")
        
        # 시스템 프롬프트 생성
        system_prompt = self._create_system_prompt(context, topic)
        
        messages = state.get("messages", [])
        if not messages or not any(isinstance(msg, AIMessage) for msg in messages):
            messages.insert(0, system_prompt)
        
        return {
            "messages": messages,
            "context": context,
            "topic": topic,
            "turn_count": state.get("turn_count", 0)
        }
    
    def _chatbot_node(self, state: ChatbotState) -> Dict:
        """챗봇 응답 생성 노드"""
        messages = state["messages"]
        response = self.provider.client.invoke(messages)
        turn_count = state.get("turn_count", 0) + 1
        
        return {
            "messages": [response],
            "turn_count": turn_count
        }
    
    def _format_response(self, state: ChatbotState) -> Dict:
        """응답 포맷팅 노드"""
        messages = state["messages"]
        last_message = messages[-1] if messages else None
        
        if last_message and isinstance(last_message, AIMessage):
            # 구조화된 응답 생성
            formatted_content = self._structure_response(
                last_message.content, 
                state["topic"]
            )
            last_message.content = formatted_content
        
        return {"messages": messages}
    
    def _create_system_prompt(self, context: str, topic: str) -> HumanMessage:
        """주제별 시스템 프롬프트 생성"""
        base_prompt = f"""당신은 {topic} 분야의 전문가입니다.
        
교육적 효과를 극대화하기 위해 다음 지침을 따라주세요:
1. 정확하고 신뢰할 수 있는 정보만 제공
2. 복잡한 개념은 단계별로 설명
3. 실제 예시와 함께 설명
4. 학습자의 수준에 맞는 언어 사용
5. 추가 학습을 위한 방향성 제시

컨텍스트 정보:
{context or "특별한 컨텍스트 정보가 제공되지 않았습니다."}

응답은 다음 구조로 작성해주세요:
- 핵심 개념 설명
- 구체적인 예시
- 실제 적용 방법
- 추가 학습 자료 추천
"""
        
        return HumanMessage(content=base_prompt)
    
    def _structure_response(self, content: str, topic: str) -> str:
        """응답 구조화 - 마크다운 형식으로 반환"""
        # 이미 구조화된 마크다운 콘텐츠는 그대로 반환
        if content.strip().startswith('#') or '```' in content:
            return content
        
        # 일반 텍스트는 적절한 마크다운 형식으로 변환
        return f"""## 📚 {topic.replace('_', ' ').title()} 전문가 답변

{content}

---
*더 자세한 정보가 필요하시면 언제든 질문해주세요!*
"""
    
    async def chat_stream(
        self, 
        message: str, 
        context: str = "", 
        topic: str = "general",
        session_id: str = "default"
    ) -> AsyncGenerator[str, None]:
        """스트리밍 채팅"""
        try:
            config = {"configurable": {"thread_id": session_id}}
            
            # 현재 상태 확인
            current_state = self.graph.get_state(config)
            turn_count = current_state.values.get("turn_count", 0) if current_state.values else 0
            
            # 컨텍스트 처리
            full_context = self.context_engineer.create_context(topic, {}, message)
            if context:
                full_context = self.context_manager.process_context(
                    full_context, 
                    context, 
                    message
                )
            
            # 메시지 구성
            system_message = self._create_system_prompt(full_context, topic)
            user_message = HumanMessage(content=message)
            
            # 이전 메시지 히스토리 가져오기
            messages = [system_message]
            if current_state.values and "messages" in current_state.values:
                history_messages = current_state.values["messages"]
                # 최대 기억 턴수에 따라 메모리 제한
                max_history_messages = self.max_turn_count * 2
                if len(history_messages) > max_history_messages:
                    history_messages = history_messages[-max_history_messages:]
                messages.extend(history_messages)
            
            messages.append(user_message)
            
            # Ollama 제공자를 통한 스트리밍 호출
            full_response = ""
            async for chunk in self.provider.generate_from_messages_stream(messages):
                full_response += chunk
                yield chunk
            
            # 상태 업데이트 (시스템 메시지는 제외하고 대화 히스토리만 저장)
            assistant_message = AIMessage(content=full_response)
            
            # 현재 대화 히스토리에 새 메시지 추가
            conversation_history = []
            if current_state.values and "messages" in current_state.values:
                conversation_history = current_state.values["messages"]
            
            # 새 사용자 메시지와 AI 응답 추가
            conversation_history.extend([user_message, assistant_message])
            
            # 메모리 제한 적용
            max_history_messages = self.max_turn_count * 2
            if len(conversation_history) > max_history_messages:
                conversation_history = conversation_history[-max_history_messages:]
            
            updated_state = {
                "messages": conversation_history,
                "context": full_context,
                "topic": topic,
                "turn_count": turn_count + 1,
                "session_id": session_id
            }
            
            self.graph.update_state(config, updated_state)
            
        except Exception as e:
            logger.error(f"스트리밍 채팅 오류: {e}")
            yield f"오류가 발생했습니다: {str(e)}"
    
    async def process_request(self, request: Any) -> Any:
        """요청 처리 (BaseAIService 구현)"""
        # ChatRequest 객체가 들어올 것으로 예상
        if hasattr(request, 'message'):
            response_generator = self.chat_stream(
                message=request.message,
                context=getattr(request, 'context', ''),
                topic=getattr(request, 'topic', 'general'),
                session_id=getattr(request, 'session_id', 'default')
            )
            
            # 전체 응답 수집
            full_response = ""
            async for chunk in response_generator:
                full_response += chunk
            
            return full_response
        else:
            raise ValueError("Invalid request format")
    
    def get_session_info(self, session_id: str = "default") -> Dict:
        """세션 정보 조회"""
        try:
            config = {"configurable": {"thread_id": session_id}}
            state = self.graph.get_state(config)
            
            if state.values:
                return {
                    "session_id": session_id,
                    "turn_count": state.values.get("turn_count", 0),
                    "topic": state.values.get("topic", "general"),
                    "message_count": len(state.values.get("messages", [])),
                    "created_at": datetime.now().isoformat(),
                    "model_used": self.provider.model
                }
            else:
                return {
                    "session_id": session_id,
                    "turn_count": 0,
                    "topic": "general",
                    "message_count": 0,
                    "created_at": datetime.now().isoformat(),
                    "model_used": self.provider.model
                }
        except Exception as e:
            logger.error(f"세션 정보 조회 오류: {e}")
            return {"error": str(e)}
    
    def reset_session(self, session_id: str = "default") -> bool:
        """세션 초기화"""
        try:
            config = {"configurable": {"thread_id": session_id}}
            initial_state = {
                "messages": [],
                "context": "",
                "topic": "general",
                "turn_count": 0,
                "session_id": session_id
            }
            self.graph.update_state(config, initial_state)
            logger.info(f"세션 초기화 완료: {session_id}")
            return True
        except Exception as e:
            logger.error(f"세션 초기화 실패: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """현재 설정 조회"""
        base_config = super().config
        
        # ChatConfig 모델에 맞게 필드명 매핑
        config = {
            "current_model": self.provider.model,
            "temperature": base_config.get("temperature", 0.7),
            "max_tokens": base_config.get("max_tokens", 2048),
            "max_turn_count": self.max_turn_count,
            "ollama_base_url": base_config.get("base_url", "http://localhost:11434"),
            "enable_streaming": True
        }
        
        return config


# 싱글톤 인스턴스 관리
_chatbot_instances = {}
_current_model = settings.ollama_model


def get_chatbot_service(model: Optional[str] = None) -> ChatbotService:
    """챗봇 서비스 인스턴스 반환 (싱글톤)"""
    global _current_model
    
    # 모델이 명시적으로 지정되지 않으면 현재 활성 모델 사용
    model_key = model or _current_model
    
    if model_key not in _chatbot_instances:
        _chatbot_instances[model_key] = ChatbotService(model_key)
    
    return _chatbot_instances[model_key]


def set_current_model(model: str):
    """현재 활성 모델 설정"""
    global _current_model
    _current_model = model
    logger.info(f"현재 활성 모델 변경: {model}")


def get_current_model() -> str:
    """현재 활성 모델 반환"""
    return _current_model


def clear_chatbot_instances():
    """모든 챗봇 인스턴스 정리"""
    global _chatbot_instances
    _chatbot_instances.clear()


def get_current_chatbot_service() -> Optional[ChatbotService]:
    """현재 활성화된 챗봇 서비스 반환 (첫 번째 인스턴스)"""
    if _chatbot_instances:
        return next(iter(_chatbot_instances.values()))
    return None 