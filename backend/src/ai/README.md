# DX-AI Manufacturing Copilot - AI 모듈 v2.0

스마트 제조를 위한 모듈화된 AI 서비스 플랫폼

## 📋 목차
- [개요](#개요)
- [모듈 구조](#모듈-구조)  
- [새로운 기능 (v2.0)](#새로운-기능-v20)
- [LLM 클라이언트](#llm-클라이언트)
- [AI 서비스](#ai-서비스)
- [사용법](#사용법)
- [성능 최적화](#성능-최적화)

## 🚀 개요

AI 모듈 v2.0은 제조업을 위한 포괄적인 AI 솔루션을 제공합니다:

- **🤖 향상된 LLM 클라이언트**: 서비스별 최적화된 Ollama 클라이언트
- **💬 챗봇 서비스**: 제조업 특화 대화형 AI
- **🔍 분류 서비스**: 제조 이슈 자동 분류  
- **🔧 컨텍스트 엔지니어링**: 지능형 프롬프트 최적화
- **⚡ 성능 최적화**: 비동기, 배치, 스트리밍 지원

## 🏗️ 모듈 구조

```
backend/src/ai/
├── __init__.py                 # 통합 AI 모듈 인터페이스
├── chatbot/                    # 챗봇 서비스
│   ├── __init__.py
│   ├── service.py             # ChatbotService
│   └── models.py              # 챗봇 데이터 모델
├── classification/            # 분류 서비스  
│   ├── __init__.py
│   ├── service.py             # ClassificationService
│   └── models.py              # 분류 데이터 모델
├── core/                      # 핵심 AI 기능
│   ├── __init__.py
│   ├── base.py               # BaseAIService 기본 클래스
│   ├── context_engineering.py # ContextEngineer v2.0
│   └── llm_client.py         # EnhancedOllamaClient v2.0
├── providers/                 # AI 제공자 추상화 (향후 확장)
├── demo.py                   # 종합 데모 스크립트
└── README.md                 # 이 파일
```

## 🆕 새로운 기능 (v2.0)

### LLM 클라이언트 v2.0
- ✅ 서비스별 최적화된 설정 (chatbot, classification, report 등)
- ✅ 스트리밍 응답 지원  
- ✅ 배치 처리 성능 향상
- ✅ 자동 재시도 및 폴백 메커니즘
- ✅ 성능 메트릭 및 모니터링

### 컨텍스트 엔지니어링 v2.0  
- ✅ 자동 질문 타입 분석 ("how", "why", "what" 등)
- ✅ AI 서비스별 특화 컨텍스트
- ✅ 동적 토픽 관리
- ✅ 사용량 통계 및 모니터링

## 🔥 LLM 클라이언트

### 기본 사용법

```python
from src.ai import get_ollama_client, get_chatbot_client

# 기본 클라이언트 
client = get_ollama_client()
response = client.generate("제조업 품질관리란?")

# 서비스별 최적화 클라이언트
chatbot_client = get_chatbot_client()  # 챗봇용 최적화
classify_client = get_classification_client()  # 분류용 최적화  
```

### 고급 기능

```python
# 비동기 처리
async def async_example():
    responses = await client.agenerate_batch([
        "스마트 팩토리란?",
        "IoT의 제조업 활용법은?", 
        "AI가 생산성에 주는 이점은?"
    ])
    return responses

# 스트리밍 응답
def stream_callback(chunk):
    print(chunk, end='', flush=True)

client.stream_generate(
    "제조업 AI 트렌드 설명해줘",
    callback=stream_callback
)

# LangChain 체인 생성
chain = client.create_service_optimized_chain(
    template="제품 {product}를 분류: {description}",
    service_type="classification"  
)
```

### 서비스별 클라이언트

| 서비스 | 클라이언트 함수 | 최적화 |
|--------|---------------|-------|
| 챗봇 | `get_chatbot_client()` | 높은 창의성 (temp: 0.8) |
| 분류 | `get_classification_client()` | 정확성 우선 (temp: 0.1) |
| 보고서 | `get_report_client()` | 균형 (temp: 0.5, 긴 출력) |
| 컨텍스트 | `get_context_client()` | 구조화 (temp: 0.3) |

## 🤖 AI 서비스

### 챗봇 서비스

```python  
from src.ai import get_chatbot_service

chatbot = get_chatbot_service()

# 기본 대화
response = chatbot.generate_response(
    message="품질관리 개선 방법은?",
    user_id="user123"  
)

# 스트리밍 대화
async for chunk in chatbot.chat_stream(
    message="공정 최적화 방법",
    session_id="session456"
):
    print(chunk, end='')
```

### 분류 서비스

```python
from src.ai import get_classification_service

classifier = get_classification_service()

# 제조업 이슈 분류
result = classifier.classify_manufacturing_issue(
    "기계에서 이상한 소음이 나고 있습니다"
)
print(f"분류: {result.category}")
print(f"신뢰도: {result.confidence}")
```

### 컨텍스트 엔지니어링

```python
from src.ai import get_context_engineer

context_engineer = get_context_engineer()

# 기본 컨텍스트 생성
context = context_engineer.create_context(
    topic="품질관리",
    context_type="manufacturing",
    details={"공정": "반도체", "단계": "검사"}
)

# 서비스별 특화 컨텍스트 
specialized = context_engineer.create_specialized_context(
    service_type="chatbot",
    topic="사용자 지원",
    parameters={"톤": "친근한", "레벨": "초급"}
)

# 질문 타입 자동 분석 (v2.0 신기능)
question_type = context_engineer._analyze_query_context(
    "품질관리는 왜 중요한가요?"
)  # → "why"
```

## ⚡ 성능 최적화

### 배치 처리

```python
# 작은 배치 (≤5개): 순차 처리
responses = client.generate_batch(["질문1", "질문2", "질문3"])

# 큰 배치 (>5개): 병렬 처리  
responses = await client.agenerate_batch(many_prompts)
```

### 재시도 및 폴백

```python
# 자동 재시도 설정
client = create_ollama_client(
    retry_attempts=3,
    fallback_model="gemma3:1b-it-qat"  # 빠른 폴백 모델
)
```

### 성능 모니터링

```python  
# 성능 통계 확인
stats = client.callback_handler.get_performance_stats()
print(f"총 요청: {stats['total_requests']}")
print(f"평균 응답시간: {stats['avg_response_time']:.2f}초")
print(f"오류율: {stats['error_rate']:.2%}")

# 모델 정보  
info = client.get_model_info()
print(f"버전: {info['version']}")
print(f"서비스 컨텍스트: {info['service_context']}")
```

## 🚀 빠른 시작

### 1. 기본 설정

```python
from src.ai import get_ai_module_info

# AI 모듈 정보 확인
info = get_ai_module_info()
print(f"AI 모듈 v{info['version']}")
print(f"지원 서비스: {info['services']}")
```

### 2. 종합 데모 실행

```bash
cd backend/src/ai
python demo.py
```

### 3. 개별 서비스 테스트

```python
# 챗봇 테스트
from src.ai import get_chatbot_service
chatbot = get_chatbot_service()
response = chatbot.generate_response("안녕하세요", "test_user")

# 분류 테스트  
from src.ai import get_classification_service
classifier = get_classification_service()
result = classifier.classify_text("기계 고장 신고")
```

## 🎯 최적화 가이드

### 서비스별 권장 모델

```python
# 작업별 모델 추천
recommendations = client.get_service_recommendations()
# {
#   "chatbot": "gemma3:4b-it-qat",
#   "classification": "gemma3:1b-it-qat", 
#   "report_generation": "gemma3:12b-it-qat"
# }

# 동적 모델 전환
success = client.switch_model("gemma3:12b-it-qat")
```

### 동시성 제어

```python
# 비동기 배치에서 동시성 제한 (기본: 3)
await client.agenerate_batch(
    prompts,
    max_concurrent=5  # 서버 성능에 따라 조정
)
```

## 📊 통계 및 모니터링

### 실시간 통계

```python  
# 컨텍스트 엔지니어링 통계
context_stats = context_engineer.get_context_stats()
print(f"총 토픽: {context_stats['total_topics']}")
print(f"생성된 컨텍스트: {context_stats['contexts_created']}")

# LLM 성능 통계
llm_stats = client.callback_handler.get_performance_stats()
print(f"처리량: {llm_stats['successful_requests']}/분")
print(f"평균 응답시간: {llm_stats['avg_response_time']:.2f}초")
```

## 🔧 설정 및 커스터마이징

### 서비스별 파라미터 커스터마이징

```python
# 챗봇용 클라이언트 커스터마이징
chatbot_client = create_ollama_client(
    service_context="chatbot",
    temperature=0.9,  # 더 창의적
    max_tokens=512,
    timeout=30
)

# 분류용 클라이언트 커스터마이징  
classify_client = create_ollama_client(
    service_context="classification",
    temperature=0.05,  # 더 정확  
    max_tokens=20,
    timeout=10
)
```

---

## 🤝 기여 및 지원

이 AI 모듈은 제조업 디지털 전환을 위한 확장 가능한 플랫폼입니다. 
새로운 AI 서비스나 기능 개선에 대한 제안을 환영합니다!

**버전**: v2.0.0  
**최종 업데이트**: 2024-01-XX 