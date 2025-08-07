"""
Dify AI 에이전트 관리 API 라우터

Dify와의 연동을 통한 AI 에이전트 생성, 관리, 대화 기능 제공
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Generator
import httpx
import os
import json
import logging
from datetime import datetime, timedelta
import asyncio

# 로깅 설정
logger = logging.getLogger(__name__)

# Dify API 설정
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost/console/api")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")  # 관리용 API 키
DIFY_CONSOLE_API_KEY = os.getenv("DIFY_CONSOLE_API_KEY", "")  # 콘솔 API 키 (앱 생성용)

# 라우터 생성
router = APIRouter(
    prefix="/dify",
    tags=["dify-agent"],
    responses={404: {"description": "Not found"}},
)

# Pydantic 모델들
class AgentCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    agent_type: str = "chatbot"  # chatbot, workflow, agent, completion
    instructions: Optional[str] = ""
    opening_statement: Optional[str] = ""
    llm_config: Optional[Dict[str, Any]] = {}
    suggested_questions: Optional[List[str]] = []

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    opening_statement: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    suggested_questions: Optional[List[str]] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: str = "default-user"
    streaming: bool = False

class ConversationRequest(BaseModel):
    agent_id: str
    user_id: str = "default-user"

# 에이전트 상태 관리
from pathlib import Path

# 데이터 저장 경로
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
AGENT_CONFIGS_FILE = DATA_DIR / "agent_configs.json"

def load_agent_configs():
    """에이전트 설정을 파일에서 로드"""
    try:
        if AGENT_CONFIGS_FILE.exists():
            with open(AGENT_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} agent configs from file")
                return data
    except Exception as e:
        logger.error(f"Failed to load agent configs: {e}")
    return {}

def save_agent_configs():
    """에이전트 설정을 파일에 저장"""
    try:
        with open(AGENT_CONFIGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(agent_configs, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(agent_configs)} agent configs to file")
    except Exception as e:
        logger.error(f"Failed to save agent configs: {e}")

# 초기 로드
agent_configs = load_agent_configs()

async def get_dify_headers(api_key: str = None) -> Dict[str, str]:
    """Dify API 요청 헤더 생성"""
    key = api_key or DIFY_API_KEY
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

async def get_dify_console_headers() -> Dict[str, str]:
    """Dify Console API 요청 헤더 생성"""
    if not DIFY_CONSOLE_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Dify Console API key not configured. Please set DIFY_CONSOLE_API_KEY environment variable."
        )
    return {
        "Authorization": f"Bearer {DIFY_CONSOLE_API_KEY}",
        "Content-Type": "application/json"
    }

@router.get("/health")
async def check_dify_health():
    """Dify 서비스 연결 상태 확인"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DIFY_API_URL}/setup")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "dify_url": DIFY_API_URL,
                "response_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Dify health check failed: {e}")
        return {
            "status": "unhealthy",
            "dify_url": DIFY_API_URL,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/agents")
async def list_agents():
    """등록된 AI 에이전트 목록 조회"""
    try:
        # 현재는 로컬 캐시에서 조회 (실제로는 Dify 앱 목록 API 호출)
        agents = []
        for agent_id, config in agent_configs.items():
            agents.append({
                "id": agent_id,
                "name": config.get("name", "Unknown"),
                "description": config.get("description", ""),
                "type": config.get("agent_type", "chatbot"),
                "status": "active",
                "created_at": config.get("created_at", datetime.now().isoformat()),
                "last_used": config.get("last_used", None),
                "conversation_count": config.get("conversation_count", 0),
                "api_key": config.get("api_key", "")[:8] + "..." if config.get("api_key") else "Not set"
            })
        
        return {
            "success": True,
            "agents": agents,
            "total": len(agents),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@router.post("/agents")
async def create_agent(request: AgentCreateRequest):
    """새 AI 에이전트 등록"""
    try:
        agent_id = f"agent_{len(agent_configs) + 1}_{int(datetime.now().timestamp())}"
        
        # 에이전트 설정 저장
        agent_config = {
            "id": agent_id,
            "name": request.name,
            "description": request.description,
            "agent_type": request.agent_type,
            "instructions": request.instructions,
            "opening_statement": request.opening_statement,
            "llm_config": request.llm_config,
            "suggested_questions": request.suggested_questions,
            "created_at": datetime.now().isoformat(),
            "conversation_count": 0,
            "api_key": "",  # 사용자가 설정해야 함
            "status": "inactive"  # API 키 설정 전까지 비활성
        }
        
        agent_configs[agent_id] = agent_config
        save_agent_configs()  # 파일에 저장
        
        return {
            "success": True,
            "agent": agent_config,
            "message": f"AI 에이전트 '{request.name}'가 생성되었습니다. API 키를 설정해주세요.",
            "next_steps": [
                "1. Dify에서 해당 앱의 API 키 복사",
                "2. 에이전트 설정에서 API 키 입력",
                "3. 테스트 대화 실행"
            ]
        }
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, request: AgentUpdateRequest):
    """AI 에이전트 설정 업데이트"""
    try:
        if agent_id not in agent_configs:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_config = agent_configs[agent_id]
        
        # 업데이트할 필드들
        if request.name is not None:
            agent_config["name"] = request.name
        if request.description is not None:
            agent_config["description"] = request.description
        if request.instructions is not None:
            agent_config["instructions"] = request.instructions
        if request.opening_statement is not None:
            agent_config["opening_statement"] = request.opening_statement
        if request.llm_config is not None:
            agent_config["llm_config"] = request.llm_config
        if request.suggested_questions is not None:
            agent_config["suggested_questions"] = request.suggested_questions
        
        agent_config["updated_at"] = datetime.now().isoformat()
        save_agent_configs()  # 파일에 저장
        
        return {
            "success": True,
            "agent": agent_config,
            "message": f"AI 에이전트 '{agent_config['name']}'가 업데이트되었습니다."
        }
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

class ApiKeyRequest(BaseModel):
    api_key: str

@router.post("/agents/{agent_id}/api-key")
async def set_agent_api_key(agent_id: str, request: ApiKeyRequest):
    """AI 에이전트 API 키 설정"""
    try:
        logger.info(f"API key setting request for agent_id: {agent_id}")
        logger.info(f"Current agent_configs keys: {list(agent_configs.keys())}")
        
        if agent_id not in agent_configs:
            logger.error(f"Agent {agent_id} not found in agent_configs")
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # API 키 형식 검증
        if not request.api_key or not request.api_key.startswith('app-'):
            raise HTTPException(status_code=400, detail="API key must start with 'app-' (e.g., app-xxxxxxxxx)")
        
        # API 키 형식만 검증하고 실제 테스트는 첫 대화에서 수행
        logger.info(f"API key validation: format check for {request.api_key[:8]}...")
        
        # 이전 API 키 로깅 (디버깅용)
        old_api_key = agent_configs[agent_id].get("api_key", "")
        logger.info(f"Previous API key for {agent_id}: {old_api_key[:8] + '...' if old_api_key else 'Not set'}")
        
        # API 키 설정
        agent_configs[agent_id]["api_key"] = request.api_key
        agent_configs[agent_id]["status"] = "active"
        agent_configs[agent_id]["updated_at"] = datetime.now().isoformat()
        
        # 설정 후 검증 로깅
        new_api_key = agent_configs[agent_id]["api_key"]
        logger.info(f"New API key set for {agent_id}: {new_api_key[:8] + '...' if new_api_key else 'Failed to set'}")
        
        # 전체 agent_configs 상태 로깅
        logger.info("Current agent_configs summary:")
        for aid, config in agent_configs.items():
            api_key = config.get('api_key', '')
            logger.info(f"  {aid}: {config.get('name', 'Unknown')} - API Key: {api_key[:8] + '...' if api_key else 'Not set'}")
        
        save_agent_configs()  # 파일에 저장
        
        return {
            "success": True,
            "message": "API 키가 설정되었습니다. 에이전트가 활성화되었습니다.",
            "agent_id": agent_id,
            "status": "active"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set API key: {str(e)}")

@router.post("/agents/{agent_id}/chat")
async def chat_with_agent(agent_id: str, request: ChatRequest):
    """AI 에이전트와 대화"""
    try:
        if agent_id not in agent_configs:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_config = agent_configs[agent_id]
        api_key = agent_config.get("api_key")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="Agent API key not configured")
        
        headers = await get_dify_headers(api_key)
        
        # Dify 채팅 API 호출
        chat_data = {
            "inputs": {},
            "query": request.message,
            "response_mode": "streaming" if request.streaming else "blocking",
            "user": request.user_id
        }
        
        # conversation_id가 있으면 포함
        if request.conversation_id:
            chat_data["conversation_id"] = request.conversation_id
            logger.info(f"Using conversation_id: {request.conversation_id}")
        else:
            logger.info("Starting new conversation")
        
        async with httpx.AsyncClient() as client:
            # Dify API 엔드포인트 확인 및 수정
            # 먼저 /v1/chat-messages를 시도하고, 실패하면 다른 엔드포인트 시도
            possible_urls = [
                "http://localhost/v1/chat-messages",
                "http://localhost/api/v1/chat-messages", 
                "http://localhost/console/api/chat-messages"
            ]
            
            response = None
            for app_api_url in possible_urls:
                try:
                    logger.info(f"Trying chat request to: {app_api_url}")
                    logger.info(f"Chat data: {json.dumps(chat_data, indent=2)}")
                    
                    response = await client.post(
                        app_api_url,
                        headers=headers,
                        json=chat_data,
                        timeout=60.0
                    )
                    
                    logger.info(f"Response status: {response.status_code}")
                    
                    # 성공하거나 인증 오류가 아닌 경우 (404는 URL 문제)
                    if response.status_code != 404:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to connect to {app_api_url}: {e}")
                    continue
            
            if response is None:
                raise HTTPException(status_code=503, detail="Could not connect to Dify API. Please check if Dify service is running.")
            
            logger.info(f"Dify API response status: {response.status_code}")
            
            # 404 오류 시 conversation_id 없이 재시도
            if response.status_code == 404 and request.conversation_id:
                logger.warning(f"Conversation {request.conversation_id} not found, retrying without conversation_id")
                
                # conversation_id 제거하고 새 대화로 시작
                retry_chat_data = {
                    "inputs": {},
                    "query": request.message,
                    "response_mode": "streaming" if request.streaming else "blocking",
                    "user": request.user_id
                }
                
                # 마지막으로 성공한 URL을 그대로 사용 (중복 path 추가 방지)
                retry_response = await client.post(
                    app_api_url,
                    headers=headers,
                    json=retry_chat_data,
                    timeout=60.0
                )
                
                logger.info(f"Retry response status: {retry_response.status_code}")
                response = retry_response
            
            if response.status_code != 200:
                # 더 자세한 에러 정보 로깅
                error_text = ""
                try:
                    error_detail = response.json()
                    error_text = json.dumps(error_detail, indent=2)
                    logger.error(f"Dify API error response: {error_text}")
                except:
                    error_text = response.text
                    logger.error(f"Dify API error text: {error_text}")
                
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Dify API error (HTTP {response.status_code}): {error_text}"
                )
            
            # 대화 카운트 업데이트
            agent_configs[agent_id]["conversation_count"] += 1
            agent_configs[agent_id]["last_used"] = datetime.now().isoformat()
            save_agent_configs()  # 파일에 저장
            
            if request.streaming:
                # 스트리밍 응답 처리
                return StreamingResponse(
                    response.aiter_bytes(),
                    media_type="text/plain"
                )
            else:
                # 일반 응답 처리
                result = response.json()
                logger.info(f"Chat response: {json.dumps(result, indent=2)}")
                return {
                    "success": True,
                    "response": result,
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to chat with agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to chat with agent: {str(e)}")

@router.get("/agents/{agent_id}/conversations")
async def get_agent_conversations(agent_id: str, user_id: str = "default-user", limit: int = 20):
    """AI 에이전트의 대화 목록 조회"""
    try:
        if agent_id not in agent_configs:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_config = agent_configs[agent_id]
        api_key = agent_config.get("api_key")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="Agent API key not configured")
        
        headers = await get_dify_headers(api_key)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DIFY_API_URL}/conversations",
                headers=headers,
                params={"user": user_id, "limit": limit},
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Dify API error")
            
            conversations = response.json()
            return {
                "success": True,
                "conversations": conversations,
                "agent_id": agent_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """AI 에이전트 삭제"""
    try:
        if agent_id not in agent_configs:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_name = agent_configs[agent_id]["name"]
        del agent_configs[agent_id]
        save_agent_configs()  # 파일에 저장
        
        return {
            "success": True,
            "message": f"AI 에이전트 '{agent_name}'가 삭제되었습니다.",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@router.get("/templates")
async def get_agent_templates():
    """AI 에이전트 템플릿 목록"""
    templates = [
        {
            "id": "manufacturing_consultant",
            "name": "제조업 상담 봇",
            "description": "제조 공정, 품질 관리, 안전 관리 전문 상담",
            "category": "industry",
            "agent_type": "chatbot",
            "instructions": """당신은 20년 경력의 제조업 전문 상담원입니다. 다음 분야에 대해 정확하고 실용적인 조언을 제공해주세요:

## 전문 분야:
- 제조 공정 최적화 (생산성 향상, 공정 개선)
- 품질 관리 (QC/QA, 불량률 감소, 품질 시스템)
- 안전 관리 (산업 안전, 위험 평가, 안전 교육)
- 장비 관리 (예방 정비, 고장 진단, 장비 선택)
- 생산 계획 (스케줄링, 재고 관리, 납기 관리)

## 응답 방식:
1. 구체적이고 실행 가능한 해결책 제시
2. 관련 법규나 표준이 있으면 함께 언급
3. 안전과 관련된 사항은 반드시 강조
4. 필요시 단계별 가이드 제공

현재 어떤 제조업 관련 문제나 궁금한 점이 있으신가요?""",
            "opening_statement": "안녕하세요! 저는 제조업 전문 상담 봇입니다. 🏭\n\n생산 공정, 품질 관리, 안전 관리 등 제조업 전반에 대해 도움을 드릴 수 있습니다. 어떤 문제로 고민이신가요?",
            "suggested_questions": [
                "생산 라인 효율성을 높이는 방법은?",
                "품질 불량률을 줄이는 체계적인 접근법은?",
                "제조업 안전사고 예방을 위한 체크리스트는?",
                "예방 정비 계획을 어떻게 수립해야 하나요?"
            ]
        },
        {
            "id": "it_support",
            "name": "IT 지원 봇",
            "description": "기술 지원, 문제 해결, 시스템 관리 전문",
            "category": "technical",
            "agent_type": "chatbot",
            "instructions": """당신은 숙련된 IT 지원 전문가입니다. 다음 분야에 대해 도움을 제공합니다:

- 하드웨어/소프트웨어 문제 해결
- 네트워크 및 보안 이슈
- 시스템 최적화 및 유지보수
- 사용자 교육 및 가이드

단계별로 명확한 해결책을 제시하고, 필요시 스크린샷이나 명령어를 안내해주세요.""",
            "opening_statement": "안녕하세요! IT 지원 봇입니다. 💻\n\n기술적인 문제나 궁금한 점이 있으시면 언제든 문의해주세요!",
            "suggested_questions": [
                "컴퓨터가 느려진 이유와 해결법은?",
                "네트워크 연결 문제를 어떻게 해결하나요?",
                "백업 시스템을 어떻게 구축해야 하나요?",
                "보안 강화를 위한 방법은?"
            ]
        },
        {
            "id": "project_manager",
            "name": "프로젝트 관리 봇",
            "description": "프로젝트 계획, 일정 관리, 팀 협업 지원",
            "category": "management",
            "agent_type": "chatbot",
            "instructions": """당신은 경험 많은 프로젝트 매니저입니다. 다음 분야를 지원합니다:

- 프로젝트 계획 수립 및 일정 관리
- 리스크 관리 및 이슈 해결
- 팀 협업 및 커뮤니케이션
- 성과 측정 및 보고서 작성

실용적이고 단계별 가이드를 제공하며, 프로젝트 성공을 위한 베스트 프랙티스를 공유합니다.""",
            "opening_statement": "안녕하세요! 프로젝트 관리 봇입니다. 📋\n\n프로젝트 계획부터 실행까지 모든 단계를 지원해드립니다!",
            "suggested_questions": [
                "새 프로젝트 계획을 어떻게 수립하나요?",
                "프로젝트 일정 지연을 어떻게 관리하나요?",
                "팀 협업을 효과적으로 하는 방법은?",
                "프로젝트 리스크를 어떻게 식별하고 관리하나요?"
            ]
        }
    ]
    
    return {
        "success": True,
        "templates": templates,
        "total": len(templates),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/agents/from-template/{template_id}")
async def create_agent_from_template(template_id: str, name: str, description: str = ""):
    """템플릿으로부터 AI 에이전트 생성"""
    try:
        # 템플릿 조회
        templates_response = await get_agent_templates()
        templates = templates_response["templates"]
        
        template = next((t for t in templates if t["id"] == template_id), None)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # 템플릿 기반 에이전트 생성 요청
        create_request = AgentCreateRequest(
            name=name,
            description=description or template["description"],
            agent_type=template["agent_type"],
            instructions=template["instructions"],
            opening_statement=template["opening_statement"],
            suggested_questions=template["suggested_questions"]
        )
        
        return await create_agent(create_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create agent from template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent from template: {str(e)}") 

@router.post("/agents/auto-create/{template_id}")
async def auto_create_agent_from_template(template_id: str, name: str, description: str = ""):
    """템플릿으로부터 완전 자동화된 AI 에이전트 생성 (Dify 앱 포함)"""
    try:
        # 템플릿 조회
        templates_response = await get_agent_templates()
        templates = templates_response["templates"]
        
        template = next((t for t in templates if t["id"] == template_id), None)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        agent_name = name or template["name"]
        agent_description = description or template["description"]
        
        logger.info(f"Starting auto-creation for agent: {agent_name}")
        
        try:
            # 1. Dify 앱 생성 시도
            dify_app_data = await create_dify_app_automatically({
                "name": agent_name,
                "description": agent_description,
                "mode": "chat",
                "icon": "🤖"
            })
            
            if not dify_app_data.get("success"):
                raise Exception(f"Dify app creation failed: {dify_app_data.get('error', 'Unknown error')}")
            
            app_id = dify_app_data["app"]["id"]
            logger.info(f"Dify app created with ID: {app_id}")
            
            # 2. 앱 설정 구성
            await configure_dify_app(app_id, {
                "model_config": {
                    "provider": "ollama",
                    "model": "gemma3:4b-it-qat",
                    "mode": "chat",
                    "completion_params": {
                        "temperature": 0.7,
                        "max_tokens": 2048
                    }
                },
                "prompt_template": template["instructions"],
                "opening_statement": template["opening_statement"],
                "suggested_questions": template["suggested_questions"]
            })
            
            # 3. API 키 생성
            api_key_data = await generate_dify_api_key(app_id)
            if not api_key_data.get("success"):
                raise Exception(f"API key generation failed: {api_key_data.get('error', 'Unknown error')}")
            
            api_key = api_key_data["api_key"]["token"]
            logger.info(f"API key generated: {api_key[:8]}...")
            
            # 4. 로컬 에이전트 생성 및 API 키 설정
            agent_id = f"agent_{len(agent_configs) + 1}_{int(datetime.now().timestamp())}"
            
            agent_config = {
                "id": agent_id,
                "name": agent_name,
                "description": agent_description,
                "agent_type": template["agent_type"],
                "instructions": template["instructions"],
                "opening_statement": template["opening_statement"],
                "llm_config": dify_app_data["app"],
                "suggested_questions": template["suggested_questions"],
                "created_at": datetime.now().isoformat(),
                "conversation_count": 0,
                "api_key": api_key,
                "status": "active",  # 바로 활성화
                "dify_app_id": app_id,
                "auto_created": True
            }
            
            agent_configs[agent_id] = agent_config
            save_agent_configs()  # 파일에 저장
            
            return {
                "success": True,
                "agent": agent_config,
                "dify_app_id": app_id,
                "message": f"AI 에이전트 '{agent_name}'가 완전 자동으로 생성되어 바로 사용 가능합니다!",
                "ready_to_use": True,
                "auto_created": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException as http_error:
            # Console API 인증 오류인 경우 폴백 모드로 전환
            if http_error.status_code == 500 and "Console API key not configured" in str(http_error.detail):
                logger.warning("Console API key not configured, falling back to manual setup mode")
                
                # 수동 설정을 위한 에이전트 생성
                fallback_result = await create_agent_from_template(template_id, agent_name, agent_description)
                
                return {
                    "success": True,
                    "agent": fallback_result["agent"],
                    "message": f"AI 에이전트 '{agent_name}'가 생성되었습니다. Dify Console API 키가 설정되지 않아 수동 설정이 필요합니다.",
                    "ready_to_use": False,
                    "auto_created": False,
                    "fallback_mode": True,
                    "setup_required": True,
                    "setup_instructions": [
                        "1. Dify 콘솔(http://localhost:3001)에 접속하여 수동으로 앱을 생성하세요",
                        "2. 생성된 앱의 API 키를 복사하세요",
                        "3. 에이전트 설정에서 API 키를 입력하세요",
                        "또는 DIFY_CONSOLE_API_KEY 환경변수를 설정하여 자동 생성을 활성화하세요"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise
        except Exception as e:
            logger.error(f"Auto-creation failed, falling back to manual mode: {e}")
            
            # 일반적인 오류의 경우도 폴백 모드로 전환
            fallback_result = await create_agent_from_template(template_id, agent_name, agent_description)
            
            return {
                "success": True,
                "agent": fallback_result["agent"],
                "message": f"AI 에이전트 '{agent_name}'가 생성되었습니다. 자동 설정에 실패하여 수동 설정이 필요합니다.",
                "ready_to_use": False,
                "auto_created": False,
                "fallback_mode": True,
                "setup_required": True,
                "error_details": str(e),
                "setup_instructions": [
                    "1. Dify 콘솔(http://localhost:3001)에 접속하여 수동으로 앱을 생성하세요",
                    "2. 생성된 앱의 API 키를 복사하세요",
                    "3. 에이전트 설정에서 API 키를 입력하세요"
                ],
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to auto-create agent: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-creation failed: {str(e)}")

async def create_dify_app_automatically(app_data: dict):
    """Dify Management API를 사용하여 자동으로 앱 생성"""
    try:
        dify_management_url = "http://localhost/console/api/apps"
        
        payload = {
            "name": app_data["name"],
            "description": app_data["description"],
            "mode": app_data["mode"],
            "icon": app_data["icon"],
            "icon_background": "#FF6B35"
        }
        
        headers = await get_dify_console_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                dify_management_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "app": response.json()
                }
            else:
                logger.error(f"Dify app creation failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Dify app: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def configure_dify_app(app_id: str, config: dict):
    """Dify 앱 설정 구성"""
    try:
        config_url = f"http://localhost/console/api/apps/{app_id}/model-config"
        
        payload = {
            "opening_statement": config["opening_statement"],
            "suggested_questions": config["suggested_questions"],
            "model": config["model_config"],
            "user_input_form": [],
            "pre_prompt": config["prompt_template"]
        }
        
        headers = await get_dify_console_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                logger.warning(f"App configuration warning: {response.status_code}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring Dify app: {e}")

async def generate_dify_api_key(app_id: str):
    """Dify 앱 API 키 생성"""
    try:
        api_key_url = f"http://localhost/console/api/apps/{app_id}/api-keys"
        
        payload = {
            "name": f"Auto-generated-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
        
        headers = await get_dify_console_headers()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_key_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "api_key": response.json()
                }
            else:
                logger.error(f"API key generation failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        return {
            "success": False,
            "error": str(e)
        } 