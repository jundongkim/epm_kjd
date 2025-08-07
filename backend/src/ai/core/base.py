"""
DX-AI Manufacturing Copilot - AI 기본 클래스들
모든 AI 서비스의 공통 기능 및 인터페이스 정의
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class AIProviderInterface(ABC):
    """AI 제공자 인터페이스"""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """응답 생성"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """스트리밍 응답 생성"""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        pass
    
    @abstractmethod
    def update_config(self, **kwargs) -> None:
        """설정 업데이트"""
        pass


class BaseAIService(ABC):
    """AI 서비스 기본 클래스"""
    
    def __init__(self, service_name: str, provider: AIProviderInterface):
        """
        AI 서비스 초기화
        
        Args:
            service_name: 서비스 이름
            provider: AI 제공자 인스턴스
        """
        self.service_name = service_name
        self.provider = provider
        self.created_at = datetime.now()
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
        
        self.logger.info(f"{service_name} 서비스 초기화 완료")
    
    @property
    def config(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        base_config = {
            "service_name": self.service_name,
            "created_at": self.created_at.isoformat(),
            "provider_type": type(self.provider).__name__
        }
        base_config.update(self.provider.get_config())
        return base_config
    
    def update_config(self, **kwargs) -> Dict[str, Any]:
        """설정 업데이트"""
        try:
            self.provider.update_config(**kwargs)
            self.logger.info(f"{self.service_name} 설정 업데이트 완료: {kwargs}")
            return self.config
        except Exception as e:
            self.logger.error(f"{self.service_name} 설정 업데이트 실패: {e}")
            raise
    
    @abstractmethod
    async def process_request(self, request: Any) -> Any:
        """요청 처리 (각 서비스에서 구현)"""
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """헬스체크"""
        return {
            "service": self.service_name,
            "status": "healthy",
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "provider": type(self.provider).__name__,
            "timestamp": datetime.now().isoformat()
        }


class SessionManager:
    """세션 관리 클래스"""
    
    def __init__(self, max_sessions: int = 1000):
        """
        세션 관리자 초기화
        
        Args:
            max_sessions: 최대 세션 수
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self.logger = logging.getLogger(f"{__name__}.SessionManager")
    
    def create_session(self, session_id: str, initial_data: Dict[str, Any] = None) -> bool:
        """새 세션 생성"""
        try:
            if len(self.sessions) >= self.max_sessions:
                # 가장 오래된 세션 제거
                oldest_session = min(
                    self.sessions.keys(),
                    key=lambda x: self.sessions[x].get("created_at", datetime.min)
                )
                del self.sessions[oldest_session]
                self.logger.warning(f"세션 한도 초과로 가장 오래된 세션 제거: {oldest_session}")
            
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "last_accessed": datetime.now(),
                "data": initial_data or {}
            }
            
            self.logger.info(f"새 세션 생성: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"세션 생성 실패: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_accessed"] = datetime.now()
            return self.sessions[session_id]["data"]
        return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """세션 데이터 업데이트"""
        try:
            if session_id not in self.sessions:
                return self.create_session(session_id, data)
            
            self.sessions[session_id]["data"].update(data)
            self.sessions[session_id]["last_accessed"] = datetime.now()
            return True
            
        except Exception as e:
            self.logger.error(f"세션 업데이트 실패: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                self.logger.info(f"세션 삭제: {session_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"세션 삭제 실패: {e}")
            return False
    
    def cleanup_sessions(self, max_age_hours: int = 24) -> int:
        """오래된 세션 정리"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_info in self.sessions.items():
                age = current_time - session_info["last_accessed"]
                if age.total_seconds() > max_age_hours * 3600:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                self.logger.info(f"만료된 세션 {len(expired_sessions)}개 정리 완료")
            
            return len(expired_sessions)
            
        except Exception as e:
            self.logger.error(f"세션 정리 실패: {e}")
            return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 정보"""
        return {
            "total_sessions": len(self.sessions),
            "max_sessions": self.max_sessions,
            "active_sessions": len([
                s for s in self.sessions.values()
                if (datetime.now() - s["last_accessed"]).total_seconds() < 3600
            ])
        }


class ContextManager:
    """컨텍스트 관리 클래스"""
    
    def __init__(self, max_context_length: int = 10000):
        """
        컨텍스트 관리자 초기화
        
        Args:
            max_context_length: 최대 컨텍스트 길이
        """
        self.max_context_length = max_context_length
        self.logger = logging.getLogger(f"{__name__}.ContextManager")
    
    def process_context(
        self, 
        base_context: str, 
        additional_context: Optional[str] = None,
        user_input: Optional[str] = None
    ) -> str:
        """컨텍스트 처리 및 최적화"""
        try:
            contexts = [base_context]
            
            if additional_context:
                contexts.append(f"\n### 추가 컨텍스트\n{additional_context}")
            
            if user_input:
                contexts.append(f"\n### 사용자 입력\n{user_input}")
            
            full_context = "\n".join(contexts)
            
            # 길이 제한 적용
            if len(full_context) > self.max_context_length:
                # 끝에서부터 자르기 (최신 정보 우선 보존)
                full_context = full_context[-self.max_context_length:]
                self.logger.warning(f"컨텍스트가 최대 길이를 초과하여 잘림: {len(full_context)}/{self.max_context_length}")
            
            return full_context
            
        except Exception as e:
            self.logger.error(f"컨텍스트 처리 실패: {e}")
            return base_context or ""
    
    def extract_key_info(self, context: str, max_length: int = 1000) -> str:
        """핵심 정보 추출"""
        if len(context) <= max_length:
            return context
        
        # 간단한 키워드 기반 요약 (향후 AI 기반으로 개선 가능)
        lines = context.split('\n')
        important_lines = []
        current_length = 0
        
        # 제목이나 중요 섹션 우선 선택
        for line in lines:
            if current_length + len(line) > max_length:
                break
            
            if any(keyword in line.lower() for keyword in ['#', '###', '중요', '핵심', '요약']):
                important_lines.append(line)
                current_length += len(line)
        
        # 남은 공간에 일반 내용 추가
        for line in lines:
            if current_length + len(line) > max_length:
                break
            if line not in important_lines:
                important_lines.append(line)
                current_length += len(line)
        
        return '\n'.join(important_lines) 