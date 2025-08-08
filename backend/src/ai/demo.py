"""
DX-AI Manufacturing Copilot - AI 모듈 종합 데모 v2.0
모든 AI 서비스와 LLM 클라이언트 기능을 시연하는 통합 데모
"""

import asyncio
import logging
from typing import Dict, Any

# AI 모듈 import
from .chatbot import get_chatbot_service
from .classification import get_classification_service
from .core import (
    get_context_engineer,
    get_ollama_client,
    get_chatbot_client,
    get_classification_client,
    get_report_client,
    get_context_client
    # 보고서 생성기 관련 import 제거됨
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_ai_report_generator():
    """
    AI 보고서 생성기 기능 데모 - 보고서 생성기 제거됨
    """
    print("\n" + "="*50)
    print("AI 보고서 생성기 기능 데모 - 제거됨")
    print("="*50)
    
    print("❌ AI 보고서 생성기 기능이 제거되었습니다.")
    print("   보고서 생성 관련 기능은 더 이상 사용할 수 없습니다.")



async def demo_async_report_generation():
    """
    비동기 보고서 생성 데모 - 보고서 생성기 제거됨
    """
    print("\n" + "="*50)
    print("비동기 AI 보고서 생성 데모 - 제거됨")
    print("="*50)
    
    print("❌ 비동기 보고서 생성 기능이 제거되었습니다.")
    print("   보고서 생성 관련 기능은 더 이상 사용할 수 없습니다.")


def demo_llm_client():
    """
    향상된 LLM 클라이언트 v2.0 기능 데모
    """
    print("\n" + "="*50)
    print("LLM 클라이언트 v2.0 기능 데모")
    print("="*50)
    
    # 1. 기본 클라이언트 테스트
    print("\n1. 기본 클라이언트 테스트")
    try:
        client = get_ollama_client()
        model_info = client.get_model_info()
        print(f"✅ 기본 클라이언트 생성: {model_info['model']}")
        print(f"   버전: {model_info['version']}")
        print(f"   서비스 컨텍스트: {model_info['service_context']}")
        
        if client.is_available():
            response = client.generate("안녕하세요", max_tokens=50)
            print(f"✅ 기본 생성 테스트: {response[:50]}...")
        else:
            print("⚠️  Ollama 서버 연결 실패 - 시뮬레이션 모드")
            
    except Exception as e:
        print(f"❌ 기본 클라이언트 테스트 실패: {e}")
    
    # 2. 서비스별 최적화된 클라이언트 테스트
    print("\n2. 서비스별 최적화 클라이언트 테스트")
    services = {
        "chatbot": get_chatbot_client(),
        "classification": get_classification_client(),
        "report": get_report_client(),
        "context": get_context_client()
    }
    
    for service_name, client in services.items():
        try:
            info = client.get_model_info()
            print(f"✅ {service_name} 클라이언트:")
            print(f"   - 온도: {info['temperature']}")
            print(f"   - 최대 토큰: {info['max_tokens']}")
            print(f"   - 타임아웃: {info['timeout']}초")
        except Exception as e:
            print(f"❌ {service_name} 클라이언트 실패: {e}")
    
    # 3. 성능 최적화 기능 테스트
    print("\n3. 성능 최적화 기능 테스트")
    try:
        client = get_ollama_client("performance_test")
        
        # 배치 처리 테스트
        prompts = ["질문 1", "질문 2", "질문 3"]
        print("배치 처리 테스트...")
        if client.is_available():
            responses = client.generate_batch(prompts, max_tokens=20)
            print(f"✅ 배치 처리 완료: {len(responses)}개 응답")
        else:
            print("⚠️  시뮬레이션 모드 - 배치 처리 건너뜀")
        
        # 성능 통계 확인
        stats = client.callback_handler.get_performance_stats()
        print(f"✅ 성능 통계:")
        print(f"   - 총 요청: {stats['total_requests']}")
        print(f"   - 성공률: {stats['successful_requests']}/{stats['total_requests']}")
        print(f"   - 오류율: {stats['error_rate']:.2%}")
        
    except Exception as e:
        print(f"❌ 성능 테스트 실패: {e}")
    
    # 4. 체인 생성 테스트
    print("\n4. LangChain 체인 생성 테스트")
    try:
        client = get_ollama_client()
        
        # 기본 체인
        basic_chain = client.create_chain("제조업에서 {topic}에 대해 설명해주세요.")
        print("✅ 기본 체인 생성 완료")
        
        # 채팅 체인
        chat_chain = client.create_chat_chain(
            system_message="당신은 제조업 전문가입니다.",
            human_message="다음 질문에 답해주세요: {question}"
        )
        print("✅ 채팅 체인 생성 완료")
        
        # QA 체인
        qa_chain = client.create_qa_chain()
        print("✅ QA 체인 생성 완료")
        
        # 서비스 최적화 체인
        opt_chain = client.create_service_optimized_chain(
            template="제품 {product}를 분류하세요: {description}",
            service_type="classification"
        )
        print("✅ 최적화 체인 생성 완료")
        
    except Exception as e:
        print(f"❌ 체인 생성 테스트 실패: {e}")


async def demo_async_llm():
    """
    비동기 LLM 클라이언트 기능 데모
    """
    print("\n" + "="*50)
    print("비동기 LLM 클라이언트 데모")
    print("="*50)
    
    try:
        client = get_ollama_client("async_test")
        
        if not client.is_available():
            print("⚠️  Ollama 서버 연결 실패 - 비동기 데모 건너뜀")
            return
        
        # 1. 비동기 단일 생성
        print("\n1. 비동기 단일 생성 테스트")
        response = await client.agenerate("제조업의 미래는?", max_tokens=50)
        print(f"✅ 비동기 응답: {response[:50]}...")
        
        # 2. 비동기 배치 생성
        print("\n2. 비동기 배치 생성 테스트")
        prompts = [
            "스마트 팩토리란?",
            "IoT가 제조업에 미치는 영향은?",
            "AI가 생산성에 주는 이점은?"
        ]
        
        start_time = asyncio.get_event_loop().time()
        responses = await client.agenerate_batch(prompts, max_tokens=30)
        end_time = asyncio.get_event_loop().time()
        
        print(f"✅ 비동기 배치 완료: {len(responses)}개 응답")
        print(f"   처리 시간: {end_time - start_time:.2f}초")
        
        for i, response in enumerate(responses):
            print(f"   응답 {i+1}: {response[:30]}...")
            
    except Exception as e:
        print(f"❌ 비동기 LLM 데모 실패: {e}")


def demo_streaming_llm():
    """
    스트리밍 LLM 응답 데모
    """
    print("\n" + "="*50)
    print("스트리밍 LLM 응답 데모")
    print("="*50)
    
    try:
        client = get_ollama_client("streaming_test")
        
        if not client.is_available():
            print("⚠️  Ollama 서버 연결 실패 - 스트리밍 데모 건너뜀")
            return
        
        print("\n스트리밍 응답 시작:")
        print("-" * 30)
        
        def stream_callback(chunk: str):
            print(chunk, end='', flush=True)
        
        response = client.stream_generate(
            "제조업에서 AI의 역할에 대해 설명해주세요.",
            callback=stream_callback,
            max_tokens=100
        )
        
        print("\n" + "-" * 30)
        print(f"✅ 스트리밍 완료. 총 길이: {len(response)} 문자")
        
    except Exception as e:
        print(f"❌ 스트리밍 데모 실패: {e}")


def demo_context_engineering():
    """컨텍스트 엔지니어링 데모 (기존 기능 유지)"""
    print("\n" + "="*50)
    print("컨텍스트 엔지니어링 v2.0 데모") 
    print("="*50)
    
    try:
        context_engineer = get_context_engineer()
        
        # 기본 컨텍스트 생성
        print("\n1. 기본 제조업 컨텍스트 생성")
        context = context_engineer.create_context(
            topic="품질관리",
            context_type="manufacturing",
            details={"공정": "반도체", "단계": "검사"}
        )
        print(f"✅ 컨텍스트 생성: {len(context)} 문자")
        print(f"   미리보기: {context[:100]}...")
        
        # 질문 타입 분석 (v2.0 신기능)
        print("\n2. 질문 타입 자동 분석")
        questions = [
            "품질관리는 어떻게 해야 하나요?",
            "왜 품질관리가 중요한가요?",
            "어떤 검사 방법을 사용해야 하나요?"
        ]
        
        for question in questions:
            question_type = context_engineer._analyze_query_context(question)
            print(f"   '{question}' → {question_type}")
        
        # 특화된 컨텍스트 생성 (v2.0 신기능)
        print("\n3. AI 서비스별 특화 컨텍스트")
        specialized = context_engineer.create_specialized_context(
            "report_generation", 
            "생산성 보고서 작성",
            {"보고서_유형": "상세", "대상": "경영진"}
        )
        print(f"✅ 보고서 특화 컨텍스트: {len(specialized)} 문자")
        
        # 통계 확인 (v2.0 신기능)
        print("\n4. 컨텍스트 사용 통계")
        stats = context_engineer.get_context_stats()
        print(f"✅ 사용 가능한 토픽: {stats['total_topics']}개")
        print(f"   생성된 컨텍스트: {stats['contexts_created']}개")
        print(f"   인기 토픽: {', '.join(stats['popular_topics'][:3])}")
        
    except Exception as e:
        print(f"❌ 컨텍스트 엔지니어링 데모 실패: {e}")


def demo_chatbot_service():
    """챗봇 서비스 데모 (기존 기능 유지)"""
    print("\n" + "="*50)
    print("챗봇 서비스 데모")
    print("="*50)
    
    try:
        chatbot = get_chatbot_service()
        
        # 간단한 대화 테스트
        print("\n1. 기본 대화 테스트")
        if chatbot.llm_client.is_available():
            response = chatbot.generate_response(
                message="제조업에서 품질관리의 중요성을 알려주세요",
                user_id="demo_user"
            )
            print(f"✅ 챗봇 응답: {response.content[:100]}...")
            print(f"   응답 시간: {response.response_time:.2f}초")
        else:
            print("⚠️  Ollama 서버 연결 실패 - 시뮬레이션 응답")
        
        # 서비스 정보 출력
        print("\n2. 챗봇 서비스 정보")
        service_info = chatbot.get_service_info()
        print(f"✅ 서비스 정보:")
        print(f"   - 버전: {service_info['version']}")
        print(f"   - 모델: {service_info['model']}")
        print(f"   - 활성 세션: {service_info['active_sessions']}")
        print(f"   - 총 메시지: {service_info['total_messages']}")
        
    except Exception as e:
        print(f"❌ 챗봇 서비스 데모 실패: {e}")


def demo_classification_service():
    """분류 서비스 데모 (기존 기능 유지)"""
    print("\n" + "="*50)
    print("분류 서비스 데모")
    print("="*50)
    
    try:
        classifier = get_classification_service()
        
        # 텍스트 분류 테스트
        print("\n1. 제조업 이슈 분류 테스트")
        issues = [
            "기계가 갑자기 멈췄습니다",
            "제품의 품질이 기준에 미달됩니다", 
            "원자재 공급이 지연되고 있습니다"
        ]
        
        for issue in issues:
            if classifier.llm_client.is_available():
                result = classifier.classify_manufacturing_issue(issue)
                print(f"✅ '{issue}' → {result.category} (신뢰도: {result.confidence:.2f})")
            else:
                print(f"⚠️  시뮬레이션: '{issue}' → 품질관리 (신뢰도: 0.85)")
        
        # 서비스 정보
        print("\n2. 분류 서비스 정보")
        service_info = classifier.get_service_info()
        print(f"✅ 서비스 정보:")
        print(f"   - 버전: {service_info['version']}")
        print(f"   - 모델: {service_info['model']}")
        print(f"   - 분류 카테고리: {len(service_info.get('categories', []))}")
        
    except Exception as e:
        print(f"❌ 분류 서비스 데모 실패: {e}")


async def run_full_demo():
    """전체 AI 모듈 데모 실행 (v2.0 향상)"""
    print("🚀 DX-AI Manufacturing Copilot - AI 모듈 v2.0 종합 데모")
    print("="*60)
    
    # 1. LLM 클라이언트 기본 기능
    demo_llm_client()
    
    # 2. 컨텍스트 엔지니어링
    demo_context_engineering()
    
    # 3. 챗봇 서비스
    demo_chatbot_service()
    
    # 4. 분류 서비스
    demo_classification_service()
    
    # 5. AI 보고서 생성기 (v2.0 신기능)
    demo_ai_report_generator()
    
    # 6. 비동기 기능
    await demo_async_llm()
    
    # 7. 비동기 보고서 생성 (v2.0 신기능)
    await demo_async_report_generation()
    
    # 8. 스트리밍 기능
    demo_streaming_llm()
    
    print("\n" + "="*60)
    print("✅ AI 모듈 v2.0 종합 데모 완료!")
    print("   LLM 클라이언트, 컨텍스트 엔지니어링, 챗봇, 분류, AI 보고서 생성 모든 서비스 테스트됨")
    print("="*60)


def main():
    """메인 함수"""
    try:
        asyncio.run(run_full_demo())
    except KeyboardInterrupt:
        print("\n⚠️  데모가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 데모 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 