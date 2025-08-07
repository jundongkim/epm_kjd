"""
AI Advisor - n8n 워크플로우 통합 문서 처리 모듈

기존 문서 처리 과정을 n8n 워크플로우로 자동화하여
백그라운드에서 비동기적으로 처리하는 시스템
"""

import os
import json
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
from pathlib import Path

from .utils import AIAdvisorConfig, get_config, AIAdvisorException
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class N8NDocumentProcessor:
    """n8n 워크플로우 기반 문서 처리기"""
    
    def __init__(self, config: Optional[AIAdvisorConfig] = None):
        self.config = config or get_config()
        
        # n8n API 설정
        self.n8n_api_url = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
        self.n8n_api_key = os.getenv("N8N_API_KEY", "")
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook")
        
        # 기존 문서 처리기 (폴백용)
        self.fallback_processor = DocumentProcessor(config)
        
        # HTTP 클라이언트
        self.http_client = None
        
        # 워크플로우 ID들
        self.workflow_ids = {
            "document_processing": None,  # 자동 감지 또는 설정에서 로드
            "vector_generation": None,
            "ontology_update": None
        }
        
        # 처리 상태 콜백
        self.status_callbacks: Dict[str, Callable] = {}
        
        logger.info("n8n 문서 처리기 초기화")
    
    async def _ensure_http_client(self):
        """HTTP 클라이언트 초기화"""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def _get_headers(self) -> Dict[str, str]:
        """n8n API 헤더 생성"""
        headers = {"Content-Type": "application/json"}
        if self.n8n_api_key:
            headers["X-N8N-API-KEY"] = self.n8n_api_key
        return headers
    
    async def initialize(self) -> bool:
        """n8n 연결 및 워크플로우 초기화"""
        try:
            await self._ensure_http_client()
            
            # n8n 연결 테스트
            if not await self._test_n8n_connection():
                logger.error("n8n API 연결 실패")
                return False
            
            # 필요한 워크플로우 확인/생성
            await self._ensure_workflows()
            
            logger.info("✅ n8n 문서 처리기 초기화 성공")
            return True
            
        except Exception as e:
            logger.error(f"❌ n8n 문서 처리기 초기화 실패: {str(e)}")
            return False
    
    async def _test_n8n_connection(self) -> bool:
        """n8n API 연결 테스트"""
        try:
            headers = await self._get_headers()
            response = await self.http_client.get(
                f"{self.n8n_api_url}/workflows",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("n8n API 연결 성공")
                return True
            else:
                logger.error(f"n8n API 연결 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"n8n API 연결 테스트 오류: {str(e)}")
            return False
    
    async def _ensure_workflows(self):
        """필요한 워크플로우 확인 및 생성"""
        try:
            # 기존 워크플로우 조회
            headers = await self._get_headers()
            response = await self.http_client.get(
                f"{self.n8n_api_url}/workflows",
                headers=headers
            )
            
            if response.status_code == 200:
                workflows = response.json().get("data", []) # AI Advisor 관련 워크플로우 찾기
                for workflow in workflows:
                    name = workflow.get("name", "").lower()
                    if "aiadvisor-document-processing" in name:
                        self.workflow_ids["document_processing"] = workflow["id"]
                    elif "aiadvisor-vector-generation" in name:
                        self.workflow_ids["vector_generation"] = workflow["id"]
                    elif "aiadvisor-ontology-update" in name:
                        self.workflow_ids["ontology_update"] = workflow["id"]
                
                # 없는 워크플로우 생성
                if not self.workflow_ids["document_processing"]:
                    await self._create_document_processing_workflow()
                
                logger.info(f"워크플로우 준비 완료: {self.workflow_ids}")
            
        except Exception as e:
            logger.error(f"워크플로우 확인 오류: {str(e)}")
    
    async def _create_document_processing_workflow(self) -> Optional[str]:
        """문서 처리 워크플로우 생성"""
        try:
            headers = await self._get_headers()
            
            # AI Advisor 전용 문서 처리 워크플로우 정의
            workflow_definition = {
                "name": "AIAdvisor-Document-Processing",
                "nodes": [
                    {
                        "parameters": {
                            "httpMethod": "POST",
                            "path": "aiadvisor-document-upload",
                            "responseMode": "responseNode",
                            "responseData": "allEntries"
                        },
                        "id": "webhook-trigger",
                        "name": "Document Upload Trigger",
                        "type": "n8n-nodes-base.webhook",
                        "typeVersion": 1,
                        "position": [240, 300]
                    },
                    {
                        "parameters": {
                            "functionCode": "// AI Advisor 문서 처리 로직\\nconst fileData = items[0].json;\\nconst documentId = fileData.document_id;\\nconst filename = fileData.filename;\\n\\n// 처리 상태 업데이트\\nreturn [{\\n  json: {\\n    document_id: documentId,\\n    filename: filename,\\n    stage: 'parsing',\\n    progress: 10,\\n    message: '문서 파싱 시작...'\\n  }\\n}];"
                        },
                        "id": "document-parser",
                        "name": "Document Parser",
                        "type": "n8n-nodes-base.function",
                        "typeVersion": 1,
                        "position": [460, 300]
                    },
                    {
                        "parameters": {
                            "functionCode": "// 청크 생성 로직\\nconst docData = items[0].json;\\n\\nreturn [{\\n  json: {\\n    ...docData,\\n    stage: 'chunking',\\n    progress: 40,\\n    message: '문서를 청크로 분할 중...'\\n  }\\n}];"
                        },
                        "id": "chunk-generator",
                        "name": "Chunk Generator",
                        "type": "n8n-nodes-base.function",
                        "typeVersion": 1,
                        "position": [680, 300]
                    },
                    {
                        "parameters": {
                            "functionCode": "// 벡터 생성 로직\\nconst chunkData = items[0].json;\\n\\nreturn [{\\n  json: {\\n    ...chunkData,\\n    stage: 'embedding',\\n    progress: 70,\\n    message: '벡터 데이터베이스에 저장 중...'\\n  }\\n}];"
                        },
                        "id": "vector-generator",
                        "name": "Vector Generator",
                        "type": "n8n-nodes-base.function",
                        "typeVersion": 1,
                        "position": [900, 300]
                    },
                    {
                        "parameters": {
                            "url": "http://localhost:8000/api/v1/aiadvisor/documents/processing-complete",
                            "httpMethod": "POST",
                            "sendQuery": False,
                            "sendHeaders": False,
                            "sendBodyData": True,
                            "bodyData": "={{ JSON.stringify($json) }}"
                        },
                        "id": "completion-callback",
                        "name": "Processing Complete Callback",
                        "type": "n8n-nodes-base.httpRequest",
                        "typeVersion": 1,
                        "position": [1120, 300]
                    },
                    {
                        "parameters": {
                            "respondWith": "json",
                            "responseBody": "={{ { status: 'success', message: '문서 처리 완료', document_id: $json.document_id } }}"
                        },
                        "id": "webhook-response",
                        "name": "Webhook Response",
                        "type": "n8n-nodes-base.respondToWebhook",
                        "typeVersion": 1,
                        "position": [1340, 300]
                    }
                ],
                "connections": {
                    "Document Upload Trigger": {
                        "main": [[{"node": "Document Parser", "type": "main", "index": 0}]]
                    },
                    "Document Parser": {
                        "main": [[{"node": "Chunk Generator", "type": "main", "index": 0}]]
                    },
                    "Chunk Generator": {
                        "main": [[{"node": "Vector Generator", "type": "main", "index": 0}]]
                    },
                    "Vector Generator": {
                        "main": [[{"node": "Processing Complete Callback", "type": "main", "index": 0}]]
                    },
                    "Processing Complete Callback": {
                        "main": [[{"node": "Webhook Response", "type": "main", "index": 0}]]
                    }
                },
                "active": True,
                "settings": {
                    "timezone": "Asia/Seoul"
                },
                "tags": ["aiadvisor", "document-processing"]
            }
            
            response = await self.http_client.post(
                f"{self.n8n_api_url}/workflows",
                headers=headers,
                json=workflow_definition
            )
            
            if response.status_code == 201:
                result = response.json()
                workflow_id = result.get("data", {}).get("id")
                self.workflow_ids["document_processing"] = workflow_id
                logger.info(f"문서 처리 워크플로우 생성 성공: {workflow_id}")
                return workflow_id
            else:
                logger.error(f"워크플로우 생성 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"워크플로우 생성 오류: {str(e)}")
            return None
    
    async def process_document_async(self, 
                                   file_path: Path, 
                                   category: str = "general",
                                   description: str = "",
                                   callback_url: str = None) -> Dict[str, Any]:
        """비동기 문서 처리 (n8n 워크플로우 활용)"""
        try:
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # n8n이 사용 가능한 경우
            if self.workflow_ids["document_processing"]:
                return await self._process_with_n8n(
                    file_path=file_path,
                    document_id=document_id,
                    category=category,
                    description=description,
                    callback_url=callback_url
                )
            else:
                # 폴백: 기존 동기식 처리
                logger.warning("n8n 워크플로우 사용 불가, 기존 방식으로 처리")
                return await self.fallback_processor.process_document(
                    file_path=file_path,
                    category=category,
                    description=description
                )
                
        except Exception as e:
            logger.error(f"비동기 문서 처리 오류: {str(e)}")
            raise AIAdvisorException(f"문서 처리 실패: {str(e)}")
    
    async def _process_with_n8n(self,
                               file_path: Path,
                               document_id: str,
                               category: str,
                               description: str,
                               callback_url: str = None) -> Dict[str, Any]:
        """n8n 워크플로우로 문서 처리"""
        try:
            # 워크플로우 트리거 데이터
            trigger_data = {
                "document_id": document_id,
                "filename": file_path.name,
                "file_path": str(file_path),
                "category": category,
                "description": description,
                "callback_url": callback_url or f"http://localhost:8000/api/v1/aiadvisor/documents/{document_id}/status",
                "started_at": datetime.now().isoformat()
            }
            
            # n8n 웹훅으로 워크플로우 실행
            webhook_url = f"{self.n8n_webhook_url}/aiadvisor-document-upload"
            
            response = await self.http_client.post(
                webhook_url,
                json=trigger_data,
                timeout=10.0  # 웹훅은 빠르게 응답해야 함
            )
            
            if response.status_code == 200:
                logger.info(f"✅ n8n 워크플로우 실행 시작: {document_id}")
                
                return {
                    "document_id": document_id,
                    "processing_status": "started",
                    "processing_mode": "n8n_workflow",
                    "workflow_id": self.workflow_ids["document_processing"],
                    "started_at": trigger_data["started_at"],
                    "expected_completion": "5-10분 예상",
                    "status_url": f"/api/v1/aiadvisor/documents/{document_id}/status"
                }
            else:
                logger.error(f"n8n 워크플로우 실행 실패: {response.status_code}")
                raise AIAdvisorException(f"워크플로우 실행 실패: {response.status_code}")
                
        except Exception as e:
            logger.error(f"n8n 워크플로우 처리 오류: {str(e)}")
            raise AIAdvisorException(f"n8n 워크플로우 처리 실패: {str(e)}")
    
    async def get_processing_status(self, document_id: str) -> Dict[str, Any]:
        """문서 처리 상태 조회"""
        try:
            # 상태 콜백에서 정보 조회
            if document_id in self.status_callbacks:
                return self.status_callbacks[document_id]
            
            # 기본 상태 반환
            return {
                "document_id": document_id,
                "status": "unknown",
                "message": "처리 상태를 확인할 수 없습니다."
            }
            
        except Exception as e:
            logger.error(f"상태 조회 오류: {str(e)}")
            return {
                "document_id": document_id,
                "status": "error",
                "message": f"상태 조회 실패: {str(e)}"
            }
    
    async def handle_processing_complete(self, result_data: Dict[str, Any]):
        """n8n 워크플로우 완료 콜백 처리"""
        try:
            document_id = result_data.get("document_id")
            
            if document_id:
                # 상태 업데이트
                self.status_callbacks[document_id] = {
                    "document_id": document_id,
                    "status": "completed",
                    "progress": 100,
                    "message": "문서 처리 완료",
                    "completed_at": datetime.now().isoformat(),
                    "result": result_data
                }
                
                logger.info(f"✅ 문서 처리 완료: {document_id}")
            
        except Exception as e:
            logger.error(f"완료 콜백 처리 오류: {str(e)}")
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """AI Advisor 관련 워크플로우 목록 조회"""
        try:
            headers = await self._get_headers()
            response = await self.http_client.get(
                f"{self.n8n_api_url}/workflows",
                headers=headers
            )
            
            if response.status_code == 200:
                all_workflows = response.json().get("data", [])
                
                # AI Advisor 관련 워크플로우 필터링
                aiadvisor_workflows = []
                for workflow in all_workflows:
                    tags = workflow.get("tags", [])
                    if "aiadvisor" in tags or "aiadvisor" in workflow.get("name", "").lower():
                        aiadvisor_workflows.append({
                            "id": workflow["id"],
                            "name": workflow["name"],
                            "active": workflow.get("active", False),
                            "tags": tags,
                            "created_at": workflow.get("createdAt"),
                            "updated_at": workflow.get("updatedAt")
                        })
                
                return aiadvisor_workflows
            else:
                logger.error(f"워크플로우 목록 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"워크플로우 목록 조회 오류: {str(e)}")
            return []
    
    async def close(self):
        """클라이언트 종료"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        logger.info("n8n 문서 처리기 종료")