import streamlit as st
import time
import hashlib
import json
import traceback
import requests
import os
from . import ai_settings
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Ollama 서버 URL 설정
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# 대화형 체인 프롬프트 템플릿
DEFAULT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 DX-AI IoT Prism 데이터 분석 전문가 입니다. 
     제공된 컨텍스트와 이전 대화 내용을 바탕으로 사용자의 질문에 답변하세요.
     문서 컨텍스트가 있는 경우 문서 컨텍스트를 참고하여 답변하세요.

컨텍스트: {context}"""
    ),
    ("human", "{question}")
])

# 메타데이터 포맷팅 유틸리티 함수
def format_metadata(metadata, title="참고 자료"):
    """메타데이터를 마크다운 형식으로 포맷팅합니다."""
    metadata_text = f"\n\n---\n**{title}**\n```json\n"
    metadata_text += json.dumps(metadata, indent=2, ensure_ascii=False)
    metadata_text += "\n```"
    return metadata_text

class ChainWrapper:
    """대화형 체인 래퍼 클래스

    LangChain 체인을 감싸서 더 편리하게 사용할 수 있도록 합니다.
    """

    def __init__(self, chain, retriever=None, prompt=DEFAULT_PROMPT):
        """
        Args:
            chain: LangChain 체인
            retriever: 벡터 DB의 retriever (선택 사항)
            prompt: 프롬프트 템플릿
        """
        self.chain = chain
        self.retriever = retriever
        self.prompt = prompt

    def __call__(self, query, history=None):
        """체인 호출

        Args:
            query (str): 사용자 질문
            history (list): 이전 대화 내역

        Returns:
            str: 응답 텍스트
        """
        context = ""
        if self.retriever:
            # retriever로부터 관련 문서 검색
            docs = self.retriever.get_relevant_documents(query)
            if docs:
                # 관련 문서 포맷팅
                context = "\n\n".join([doc.page_content for doc in docs])

        # 체인 실행
        return self.chain.invoke({
            "context": context,
            "question": query,
            "history": history if history else []
        })

    def stream_response(self, inputs, message_placeholder):
        """스트리밍 응답 생성

        Args:
            inputs (dict): 입력값 (question, history 등)
            message_placeholder: Streamlit 메시지 플레이스홀더

        Returns:
            tuple: (응답 객체, 전체 응답 텍스트)
        """
        # 문서 검색 수행
        question = inputs["question"]
        context = ""
        docs = []

        if self.retriever:
            docs = self.retriever.get_relevant_documents(question)
            if docs:
                # 관련 문서 포맷팅
                context = "\n\n".join([doc.page_content for doc in docs])

        # 대화 이력 관리
        history = inputs.get("history", [])

        # 응답 스트리밍을 위한 변수
        full_response = ""

        # 스트리밍 응답 생성
        for chunk in self.chain.stream({
            "context": context,
            "question": question,
            "history": history
        }):
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")

        # 스트리밍 완료 후 최종 응답 표시
        message_placeholder.markdown(full_response)

        # 최종 응답과 소스 문서 반환
        response = {
            "answer": full_response,
            "source_documents": docs
        }

        return response, full_response

def get_conversation_chain(vector_store=None, selected_model=None, temperature=None, memory_length=None):
    """대화형 체인을 생성합니다.

    Args:
        vector_store: FAISS 벡터 저장소 인스턴스 (선택 사항)
        selected_model (str): 사용할 Ollama 모델 이름 (기본값: None, session_state에서 가져옴)
        temperature (float): 생성 모델의 temperature 값 (기본값: None, session_state에서 가져옴)
        memory_length (int): 대화 기억 길이 (기본값: None, session_state에서 가져옴)

    Returns:
        ChainWrapper: 대화형 체인 래퍼 인스턴스
    """
    # ai_settings에서 설정 값 가져오기 (인자로 전달된 값이 없을 경우)
    if selected_model is None:
        selected_model = st.session_state.selected_model
    if temperature is None:
        temperature = st.session_state.temperature
    if memory_length is None:
        memory_length = st.session_state.memory_length
        
    print(f"대화 체인 생성: 모델={selected_model}, 온도={temperature}, 메모리 길이={memory_length}")
    
    # Ollama 모델 초기화
    llm = ChatOllama(
        model=selected_model,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        streaming=True,  # 스트리밍 응답 활성화
        request_timeout=60.0,  # 요청 타임아웃 60초로 설정
    )

    retriever = None
    if vector_store:
        # 벡터 스토어를 retriever로 변환
        retriever = vector_store.as_retriever(
            search_type="similarity",  # 유사도 기반 검색 사용
            search_kwargs={
                "k": 5,  # 상위 5개 문서 검색
                "score_threshold": 0.5  # 유사도 임계값 설정
            }
        )

    # LCEL 체인 구성
    chain = (
        {
            "context": lambda x: x["context"],  # 이미 포맷팅된 컨텍스트 사용
            "question": RunnablePassthrough(),
            "history": lambda x: x.get("history", []),
        }
        | DEFAULT_PROMPT
        | llm
        | StrOutputParser()
    )

    return ChainWrapper(chain, retriever)

# 스트리밍 콜백 핸들러 클래스 정의
class StreamlitCallbackHandler:
    def __init__(self, container):
        self.container = container
        self.text = ""
        
    def on_llm_new_token(self, token, **kwargs):
        self.text += token
        self.container.markdown(self.text + "▌")
        # 약간의 지연을 추가하여 시각적 효과 강화
        time.sleep(0.005)

def init_session_state(key_prefix="visualization_analysis"):
    """세션 상태 초기화 함수
    
    Args:
        key_prefix (str): 캐시와 상태 변수에 사용할 접두어
    """
    # 공유 AI 설정 초기화
    ai_settings.init_ai_settings()
    
    # 이전 AI 설정 확인용 세션 상태 변수가 없으면 초기화
    if "previous_ai_settings" not in st.session_state:
        st.session_state.previous_ai_settings = {
            "selected_model": st.session_state.selected_model,
            "temperature": st.session_state.temperature
        }
    
    # AI 설정이 변경되었는지 확인
    settings_changed = (
        st.session_state.previous_ai_settings.get("selected_model") != st.session_state.selected_model or
        st.session_state.previous_ai_settings.get("temperature") != st.session_state.temperature
    )
    
    # 설정이 변경되었다면 관련 캐시 무효화
    if settings_changed:
        print(f"AI 설정 변경 감지: {st.session_state.previous_ai_settings} -> (모델: {st.session_state.selected_model}, 온도: {st.session_state.temperature})")
        
        # 캐시 상태 초기화 (특정 prefix에 해당하는 캐시 초기화)
        cache_key = f"{key_prefix}_cache"
        if cache_key in st.session_state:
            # 캐시 내용만 비우고 캐시 객체는 유지
            st.session_state[cache_key] = {}
            print(f"캐시 초기화됨: {cache_key}")
        
        # 실행 상태 업데이트 (실행 중 아님)
        running_key = f"{key_prefix}_running"
        if running_key in st.session_state:
            st.session_state[running_key] = False
        
        # 이전 설정 업데이트
        st.session_state.previous_ai_settings = {
            "selected_model": st.session_state.selected_model,
            "temperature": st.session_state.temperature
        }
    
    # 캐시 상태 초기화
    cache_state_key = f"{key_prefix}_cache"
    if cache_state_key not in st.session_state:
        st.session_state[cache_state_key] = {}
    
    # 실행 상태 초기화
    running_state_key = f"{key_prefix}_running"
    if running_state_key not in st.session_state:
        st.session_state[running_state_key] = False
    
    # 채팅 기록 초기화
    chat_history_key = f"{key_prefix}_history"
    if chat_history_key not in st.session_state:
        st.session_state[chat_history_key] = []
    
    print(f"세션 상태 초기화 완료 (key_prefix: {key_prefix})")
    print(f"AI 설정: 모델={st.session_state.selected_model}, 온도={st.session_state.temperature}, 메모리 길이={st.session_state.memory_length}")

def generate_cache_key(prompt: str, model: str = None, temperature: float = None) -> str:
    """캐시 키 생성 함수
    
    Args:
        prompt (str): 프롬프트 텍스트
        model (str): 사용할 모델 (기본값: session_state의 selected_model)
        temperature (float): 온도 값 (기본값: session_state의 temperature)
        
    Returns:
        str: 해시 기반 캐시 키
    """
    if model is None:
        model = st.session_state.selected_model
    if temperature is None:
        temperature = st.session_state.temperature
        
    key_string = f"{prompt}_{model}_{temperature}"
    return hashlib.md5(key_string.encode()).hexdigest()

def generate_ai_response(prompt, key_prefix="visualization_analysis", message_placeholder=None, metadata_placeholder=None):
    """AI 응답 생성 함수
    
    Args:
        prompt (str): 분석에 사용할 프롬프트
        key_prefix (str): 세션 상태 변수 접두어
        message_placeholder (streamlit.empty): 메시지 표시할 placeholder
        metadata_placeholder (streamlit.empty): 메타데이터 표시할 placeholder
        
    Returns:
        str: 생성된 응답 텍스트
    """
    # AI 설정 상태 확인
    if "selected_model" not in st.session_state or "temperature" not in st.session_state:
        ai_settings.init_ai_settings()
    
    cache_key = generate_cache_key(prompt)
    
    # 세션 상태 키 정의
    cache_state_key = f"{key_prefix}_cache"
    running_state_key = f"{key_prefix}_running"
    chat_history_key = f"{key_prefix}_history"
    
    # 대화 기록이 없을 경우 초기화
    if chat_history_key not in st.session_state:
        st.session_state[chat_history_key] = []
    
    # 디버깅용 로깅
    print(f"generate_ai_response 함수 호출됨 (prompt 길이: {len(prompt)})")
    print(f"시작 시 대화 기록 길이: {len(st.session_state[chat_history_key])}")
    print(f"대화 기록 내용: {[msg['role'] for msg in st.session_state[chat_history_key]]}")
    print(f"현재 AI 설정: 모델={st.session_state.selected_model}, 온도={st.session_state.temperature}")
    print("--------------------------------")
    
    try:
        # 대화 체인 생성 (get_conversation_chain 함수는 이제 session_state에서 기본값 가져옴)
        conversation_chain = get_conversation_chain()
        
        # 대화 기록을 채팅 엔진에서 사용할 수 있는 형식으로 변환
        history = []
        for msg in st.session_state[chat_history_key]:
            if msg["role"] == "user":
                history.append({"type": "human", "content": msg["content"]})
            elif msg["role"] == "assistant":
                history.append({"type": "ai", "content": msg["content"]})
        
        # 스트리밍 응답 생성 (대화 기록 전달)
        response, full_response = conversation_chain.stream_response(
            {"question": prompt, "history": history}, 
            message_placeholder
        )
        
        # 응답 메타데이터 처리
        source_documents = response.get("source_documents", [])
        metadata = None
        
        if source_documents:
            metadata = {
                "source_count": len(source_documents),
                "sources": [doc.metadata for doc in source_documents] if hasattr(source_documents[0], 'metadata') else []
            }
            
            if metadata_placeholder:
                metadata_placeholder.markdown(format_metadata(metadata))
        
        # 사용자 메시지 및 AI 응답을 대화 기록에 추가
        # display_chat_interface에서 사용자 메시지를 이미 추가했는지 확인
        last_message = st.session_state[chat_history_key][-1] if st.session_state[chat_history_key] else None
        
        # 마지막 메시지가 user가 아닐 때만 사용자 메시지를 추가
        if not last_message or last_message["role"] != "user" or last_message["content"] != prompt:
            st.session_state[chat_history_key].append({
                "role": "user",
                "content": prompt
            })
        
        # AI 응답 추가
        st.session_state[chat_history_key].append({
            "role": "assistant",
            "content": full_response
        })
        
        # 대화 기록 길이 제한
        max_history = st.session_state.memory_length * 2
        if max_history > 0 and len(st.session_state[chat_history_key]) > max_history:
            st.session_state[chat_history_key] = st.session_state[chat_history_key][-max_history:]
        
        # 결과 캐싱
        if cache_state_key in st.session_state:
            st.session_state[cache_state_key][cache_key] = {
                "response": full_response,
                "metadata": metadata
            }
        
        # 분석 상태 업데이트
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = False
        
        # 디버깅용 로깅
        print(f"응답 생성 완료 (길이: {len(full_response)})")
        print(f"종료 시 대화 기록 길이: {len(st.session_state[chat_history_key])}")
        print(f"대화 기록 내용: {[msg['role'] for msg in st.session_state[chat_history_key]]}")
        print("================================")

        return full_response
        
    except Exception as e:
        error_msg = f"AI 분석 처리 중 오류가 발생했습니다: {str(e)}"
        st.error(error_msg)
        st.error(traceback.format_exc())
        
        # 분석 상태 업데이트
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = False
            
        return error_msg

def display_analysis_ui(prompt, button_label="AI 분석", key_prefix="visualization_analysis", info_message=None):
    """분석 UI 표시 및 처리
    
    Args:
        prompt (str): 분석에 사용할 프롬프트
        button_label (str): 버튼에 표시할 텍스트
        key_prefix (str): 세션 상태 변수 접두어
        info_message (str): 분석 전 표시할 안내 메시지
        
    Returns:
        bool: 분석 실행 여부
    """
    # AI 설정 상태 확인
    if "selected_model" not in st.session_state or "temperature" not in st.session_state:
        ai_settings.init_ai_settings()
        
    # 세션 상태 키 정의
    cache_state_key = f"{key_prefix}_cache"
    running_state_key = f"{key_prefix}_running"
    
    # 캐시 키 생성
    cache_key = generate_cache_key(prompt)
    
    # 분석 버튼 클릭 콜백 함수 정의
    def on_analyze_click():
        if cache_state_key in st.session_state:
            st.session_state[cache_state_key].pop(cache_key, None)  # 캐시 무효화
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = True
    
    # 분석 버튼 추가
    col1, col2 = st.columns([3, 1])
    with col1:
        model_info = f"사용 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature}"
        st.caption(model_info)
    with col2:
        analyze_button = st.button(
            button_label, 
            key=f"{key_prefix}_button", 
            on_click=on_analyze_click,
            use_container_width=True
        )
    
    # 이전 분석 결과가 있는 경우 (캐시에 있는 경우)
    if cache_state_key in st.session_state and cache_key in st.session_state[cache_state_key]:
        cached_response = st.session_state[cache_state_key][cache_key]
        with st.chat_message("assistant"):
            st.markdown(cached_response["response"])
            if cached_response.get("metadata"):
                st.markdown(format_metadata(cached_response["metadata"], "처리 정보"))
        return False
    
    # 분석 실행 중인 경우 (버튼 클릭 후)
    elif running_state_key in st.session_state and st.session_state[running_state_key]:
        return True
    
    # 분석 전 안내 메시지
    else:
        if info_message is None:
            info_message = f"AI 분석을 실행하려면 '{button_label}' 버튼을 클릭하세요."
        st.info(info_message)
        return False

def display_chat_interface(key_prefix="visualization_analysis"):
    """대화형 인터페이스 표시
    
    Args:
        key_prefix (str): 세션 상태 변수 접두어
    """
    # AI 설정 상태 확인
    if "selected_model" not in st.session_state or "temperature" not in st.session_state:
        ai_settings.init_ai_settings()
        
    chat_history_key = f"{key_prefix}_history"
    chat_input_key = f"{key_prefix}_chat_input"
    
    # 대화 기록이 없을 경우 초기화
    if chat_history_key not in st.session_state:
        st.session_state[chat_history_key] = []
    
    # 채팅 입력 콜백 함수
    def on_chat_submit():
        user_input = st.session_state[chat_input_key]
        if user_input:
            # 사용자 메시지를 대화 기록에 즉시 추가
            st.session_state[chat_history_key].append({
                "role": "user",
                "content": user_input
            })
            # 입력 필드 초기화 및 상태 설정
            st.session_state[f"{key_prefix}_pending_response"] = True
            st.session_state[f"{key_prefix}_pending_question"] = user_input
            # 입력 필드 초기화
            st.session_state[chat_input_key] = ""
    
    # 모델 정보 표시
    st.caption(f"AI 모델: {st.session_state.selected_model} | 온도: {st.session_state.temperature} | 기억 길이: {st.session_state.memory_length}")
    
    # 모든 대화 기록을 표시 (처음 두 개의 시스템 프롬프트/응답 제외)
    # 첫 번째 분석 프롬프트와 응답만 건너뛰고 실제 대화는 모두 표시
    start_idx = min(2, len(st.session_state[chat_history_key]))
    
    # 대화 기록 복사본 만들기 (표시용)
    display_history = st.session_state[chat_history_key][start_idx:]
    
    # 디버깅 정보
    print(f"Chat interface showing {len(display_history)} messages")
    print(f"Full history has {len(st.session_state[chat_history_key])} messages")
    
    # 대화 기록 표시
    for message in display_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자가 새 질문을 했고 응답 대기 중인 경우
    if f"{key_prefix}_pending_response" in st.session_state and st.session_state[f"{key_prefix}_pending_response"]:
        # 대화 기록에 이미 추가된 사용자 메시지를 다시 표시하지 않음
        # with st.chat_message("user"):
        #     st.markdown(st.session_state[f"{key_prefix}_pending_question"])
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            metadata_placeholder = st.empty()
            with st.spinner("AI가 응답을 생성하고 있습니다..."):
                generate_ai_response(
                    prompt=st.session_state[f"{key_prefix}_pending_question"],
                    key_prefix=key_prefix,
                    message_placeholder=message_placeholder,
                    metadata_placeholder=metadata_placeholder
                )
            
            # 응답 완료 후 상태 초기화
            st.session_state[f"{key_prefix}_pending_response"] = False
            st.session_state[f"{key_prefix}_pending_question"] = ""
    
    # 사용자 입력
    st.text_input(
        "질문을 입력하세요...",
        key=chat_input_key,
        on_change=on_chat_submit,
        value=""
    ) 