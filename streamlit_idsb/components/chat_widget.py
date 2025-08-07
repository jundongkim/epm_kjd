import streamlit as st
import requests
import json
import os
# from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate

# Ollama 서버 URL 설정
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# 대화형 체인 프롬프트 템플릿
DEFAULT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 EcoPro iDSB 대시보드를 위한 유용한 어시스턴트입니다. 제공된 컨텍스트와 이전 대화 내용을 바탕으로 사용자의 질문에 답변하세요.


컨텍스트: {context}"""
    ),
    ("human", "{question}")
])

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

def get_conversation_chain(vector_store=None, selected_model="gemma3:4b", temperature=0.2, memory_length=5):
    """대화형 체인을 생성합니다.

    Args:
        vector_store: FAISS 벡터 저장소 인스턴스 (선택 사항)
        selected_model (str): 사용할 Ollama 모델 이름 (기본값: "gemma3:4b")
        temperature (float): 생성 모델의 temperature 값 (기본값: 0.2)
        memory_length (int): 대화 기억 길이 (기본값: 5)

    Returns:
        ChainWrapper: 대화형 체인 래퍼 인스턴스
    """
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough

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

def ollama_chat(model, prompt, context=None, system=''):
    """
    LangChain의 ChatOllama를 사용하여 메시지 전송

    Args:
        model (str): Ollama 모델 이름
        prompt (str): 사용자 입력 프롬프트
        context (list): 대화 이력
        system (str): 시스템 메시지

    Returns:
        tuple: (response_text, new_context)
    """
    messages = []

    # 시스템 메시지 추가
    if system:
        messages.append(SystemMessage(content=system))

    # 컨텍스트(이전 대화) 추가
    if context:
        for msg in context:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                messages.append(SystemMessage(content=msg["content"]))

    # 현재 메시지 추가
    messages.append(HumanMessage(content=prompt))

    try:
        # ChatOllama 모델 초기화
        chat_model = ChatOllama(
            model=model,
            base_url=OLLAMA_BASE_URL,
            temperature=0.2,
            request_timeout=60.0,  # 요청 타임아웃 60초로 설정
        )

        # 응답 생성
        response = chat_model.invoke(messages)
        assistant_message = response.content

        # 새로운 컨텍스트 생성 (기존 방식과 호환되도록)
        if not context:
            context = []
            if system:
                context.append({"role": "system", "content": system})

        # 현재 메시지와 응답 추가
        new_context = context + [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": assistant_message}
        ]

        return assistant_message, new_context

    except Exception as e:
        print(f"Ollama API 오류: {str(e)}")
        error_msg = f"죄송합니다. 응답 생성 중에 오류가 발생했습니다. Ollama API 서버가 실행 중이고 '{model}' 모델이 설치되어 있는지 확인해주세요."
        return error_msg, context if context else []

def get_tab_context(tab_index):
    """
    Returns context information based on the active tab

    Args:
        tab_index (int): Index of the active tab

    Returns:
        str: Context information for the selected tab
    """
    tab_contexts = {
        0: "You are a helpful assistant providing insights about the dataset overview. Answer questions about data statistics, distributions, and general information about the dataset.",
        1: "You are a helpful assistant analyzing feature importance and correlations. Help explain feature relationships, importance scores, and how they influence the target variable.",
        2: "You are a helpful assistant explaining model results. Provide insights on model performance, accuracy metrics, and interpreting prediction outcomes.",
        3: "You are a helpful assistant explaining data visualizations. Help interpret charts, graphs, and identify patterns in the visual data representations.",
        4: "You are a helpful assistant for simulation scenarios. Help with parameter adjustment suggestions and interpret simulation results.",
        5: "You are a helpful assistant for SEM analysis. Help interpret SEM images and identify particle characteristics such as size, shape, and surface features.",
        6: "You are a helpful assistant for ICP analysis. Help analyze elemental compositions, interpret concentration patterns, and identify significant variations in the ICP data.",
        7: "You are a helpful assistant for CMMS maintenance data analysis. Help analyze equipment maintenance records, interpret maintenance metrics, and identify maintenance patterns and trends.",
        8: "You are a helpful assistant for equipment risk assessment. Help interpret risk matrices, analyze risk scores, and provide insights on risk mitigation strategies for equipment.",
        9: "You are a helpful assistant for EDS analysis. Help interpret EDS spectra and elemental composition data, identify key elements, and analyze material properties.",
        10: "You are a helpful assistant for combined SEM-EDS analysis. Help interpret the relationship between SEM images and EDS compositional data, providing comprehensive insights on particles and materials."
    }

    return tab_contexts.get(tab_index, "You are a helpful assistant for the EcoPro dashboard.")

# 모델 선택 옵션
model_options = {
    "gemma3:1b": "Gemma3:1b",
    "gemma3:1b-it-qat": "Gemma3:1b-it-qat",
    "gemma3:4b": "Gemma3:4b",
    "gemma3:4b-it-qat": "Gemma3:4b-it-qat",
    "gemma3:12b": "Gemma3:12b",
    "gemma3:12b-it-qat": "Gemma3:12b-it-qat",
    "gemma3:27b": "Gemma3:27b",
    "gemma3:27b-it-qat": "Gemma3:27b-it-qat"
}

# 모델 스펙 정보
MODEL_SPECS = {
    "gemma3:1b": {
        "size": "1B parameters",
        "context_length": 8192,
        "languages": "한국어, English",
        "modalities": ["Text"]
    },
    "gemma3:4b": {
        "size": "4B parameters",
        "context_length": 8192,
        "languages": "한국어, English",
        "modalities": ["Text"]
    },
    "gemma3:12b": {
        "size": "12B parameters",
        "context_length": 8192,
        "languages": "한국어, English",
        "modalities": ["Text"]
    },
    "gemma3:27b": {
        "size": "27B parameters",
        "context_length": 8192,
        "languages": "한국어, English",
        "modalities": ["Text"]
    }
}

def get_available_models():
    """사용 가능한 모델 목록 반환"""
    return list(model_options.keys())

def show_chat_widget(tab_index):
    """
    Displays an Ollama-powered chat widget in the dashboard

    Args:
        tab_index (int): Current active tab index
    """
    # 초기 모델 값 설정
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gemma3:4b-it-qat"

    # 초기 temperature 값 설정
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.2

    # 초기 memory_length 값 설정
    if "memory_length" not in st.session_state:
        st.session_state.memory_length = 5

    # 대화 체인 초기화
    if "conversation_chain" not in st.session_state:
        st.session_state.conversation_chain = get_conversation_chain(
            selected_model=st.session_state.selected_model,
            temperature=st.session_state.temperature,
            memory_length=st.session_state.memory_length
        )

    # 탭별 고유한 세션 상태 키 생성
    chat_history_key = f"chat_history_{tab_index}"
    chat_context_key = f"chat_context_{tab_index}"

    # Initialize conversation history in session state
    if chat_history_key not in st.session_state:
        st.session_state[chat_history_key] = []

    # Initialize context in session state
    if chat_context_key not in st.session_state:
        st.session_state[chat_context_key] = []

    # Get the system message based on current tab
    system_message = get_tab_context(tab_index)

    # 채팅 UI 시작
    st.subheader("💬 iDSB AI 어시스턴트")

    # 모델 설정 UI를 작은 expander로 제공
    with st.expander("모델 설정"):
        selected_model = st.selectbox(
            "모델 선택",
            get_available_models(),
            index=list(model_options.keys()).index(st.session_state.selected_model),
            key=f"model_select_{tab_index}"
        )

        col1, col2 = st.columns(2)
        with col1:
            memory_length = st.slider(
                "대화 기억 길이",
                min_value=0,
                max_value=10,
                value=st.session_state.memory_length,
                key=f"memory_length_{tab_index}"
            )
        with col2:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.temperature,
                step=0.1,
                key=f"temperature_{tab_index}"
            )

        # 모델 설정이 변경되었다면 대화 체인 다시 초기화
        if (selected_model != st.session_state.selected_model or
            temperature != st.session_state.temperature or
            memory_length != st.session_state.memory_length):
            st.session_state.selected_model = selected_model
            st.session_state.temperature = temperature
            st.session_state.memory_length = memory_length
            st.session_state.conversation_chain = get_conversation_chain(
                selected_model=selected_model,
                temperature=temperature,
                memory_length=memory_length
            )

    # 채팅 메시지를 표시할 컨테이너
    chat_messages = st.container(height=350)

    # 채팅 메시지 표시
    with chat_messages:
        for message in st.session_state[chat_history_key]:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

    # 채팅 입력 UI
    user_input = st.chat_input("iDSB AI에게 질문하세요...", key=f"chat_input_{tab_index}")

    # Ollama 상태 표시
    st.caption(f"Powered by Ollama + {model_options[st.session_state.selected_model]} | Temp: {st.session_state.temperature}")

    # 채팅 초기화 버튼
    if st.button("대화 초기화", key=f"clear_chat_{tab_index}"):
        st.session_state[chat_history_key] = []
        st.session_state[chat_context_key] = []
        st.rerun()

    # 사용자 입력 처리
    if user_input:
        # 사용자 메시지를 채팅 기록에 추가
        st.session_state[chat_history_key].append({"role": "user", "content": user_input})

        # Ollama에서 응답 가져오기
        with st.spinner("생각 중..."):
            try:
                # LangChain 대화 체인 사용
                history = [
                    {"type": "human" if msg["role"] == "user" else "ai", "content": msg["content"]}
                    for msg in st.session_state[chat_history_key][:-1]  # 현재 메시지 제외
                ]

                response = st.session_state.conversation_chain(user_input, history)

                # 현재 컨텍스트 업데이트
                st.session_state[chat_context_key].append({"role": "user", "content": user_input})
                st.session_state[chat_context_key].append({"role": "assistant", "content": response})

            except Exception as e:
                # 오류 발생 시 기존 ollama_chat 함수 사용 (대체 방안)
                response, new_context = ollama_chat(
                    model=st.session_state.selected_model,
                    prompt=user_input,
                    context=st.session_state[chat_context_key],
                    system=system_message
                )
                st.session_state[chat_context_key] = new_context

        # 어시스턴트 응답을 채팅 기록에 추가
        st.session_state[chat_history_key].append({"role": "assistant", "content": response})

        # 채팅 표시 업데이트를 위해 재실행
        st.rerun()

def create_two_column_layout(main_content_function, tab_index=0):
    """
    Create a two-column layout with the main content on the left and chat widget on the right

    Args:
        main_content_function: Function to render the main content
        tab_index: Current active tab index
    """
    # 스크롤과 무관하게 고정 위치를 위한 CSS 추가 (반드시 칼럼 생성 전에 적용)
    st.markdown("""
    <style>
    .main-content {
        width: 70%;
        padding-right: 30px;
        box-sizing: border-box;
    }

    .chat-sidebar {
        position: fixed;
        right: 0;
        top: 0;
        width: 30%;
        height: 100vh;
        overflow-y: auto;
        background-color: white;
        padding: 1rem;
        border-left: 1px solid #f0f0f0;
        box-sizing: border-box;
        z-index: 1000;
    }

    /* Streamlit 기본 요소들의 너비 조정 */
    .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 레이아웃 컨테이너 생성
    left_col, right_col = st.columns([7, 3])

    # 왼쪽 열에 메인 콘텐츠 표시
    with left_col:
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        main_content_function()
        st.markdown('</div>', unsafe_allow_html=True)

    # 오른쪽 열에 채팅 위젯 표시
    with right_col:
        # 오른쪽 사이드바 시작
        st.markdown('<div class="chat-sidebar">', unsafe_allow_html=True)
        show_chat_widget(tab_index)
        st.markdown('</div>', unsafe_allow_html=True)

def configure_sidebar_chat(tab_index=0, chat_height=400):
    """
    Configure the sidebar for chat functionality

    Args:
        tab_index (int): Current active tab index
        chat_height (int): Height of the chat messages container in pixels
    """
    # 사이드바 너비 조정을 위한 CSS 추가 (Streamlit의 기본 반응형 동작 유지)
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 450px !important;
        background-color: transparent !important;
    }

    /* 사이드바 내부 요소 배경 투명화 */
    [data-testid="stSidebar"] > div {
        background-color: transparent !important;
    }

    /* 사이드바 내용물 배경색 설정 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        background-color: transparent !important;
    }

    /* 사이드바 토글 버튼에 대한 스타일 */
    button[kind="header"] {
        display: block !important;
    }

    /* 사이드바 스크롤바 숨기기 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        overflow-y: auto;
        scrollbar-width: none;  /* Firefox */
    }

    /* Chrome, Safari, Edge 브라우저에서 스크롤바 숨기기 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"]::-webkit-scrollbar {
        width: 0 !important;
        display: none;
    }

    /* 채팅 메시지 스크롤바는 표시하되 세련되게 */
    [data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"] {
        scrollbar-width: thin;
    }

    [data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"]::-webkit-scrollbar {
        width: 5px !important;
        display: block;
    }

    [data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 10px;
    }

    /* 채팅 컨테이너 스타일 */
    [data-testid="stChatMessageContent"] {
        background-color: rgba(247, 247, 247, 0.8) !important;
        backdrop-filter: blur(5px);
    }

    /* 채팅 입력 필드 스타일 - 항상 테두리 표시 */
    .stTextInput > div > div > input {
        border: 1px solid #0f766e !important;
        border-radius: 20px !important;
        padding-left: 15px !important;
    }

    .stTextInput > div {
        border: none !important;
        border-radius: 20px !important;
    }

    /* 채팅 입력 필드 포커스 시 스타일 */
    .stTextInput > div > div > input:focus {
        box-shadow: 0 0 0 1px #0f766e !important;
        border-color: #0f766e !important;
    }

    /* 모델 설정 expander 배경 반투명 */
    .streamlit-expanderContent {
        background-color: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(5px);
    }
    </style>
    """, unsafe_allow_html=True)

    # 사이드바에 채팅 위젯 표시
    st.header("💬 iDSB AI 어시스턴트")

    # 초기 모델 값 설정
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "gemma3:4b-it-qat"

    # 초기 temperature 값 설정
    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.2

    # 초기 memory_length 값 설정
    if "memory_length" not in st.session_state:
        st.session_state.memory_length = 5

    # 대화 체인 초기화
    if "conversation_chain" not in st.session_state:
        try:
            st.session_state.conversation_chain = get_conversation_chain(
                selected_model=st.session_state.selected_model,
                temperature=st.session_state.temperature,
                memory_length=st.session_state.memory_length
            )
        except Exception as e:
            print(f"대화 체인 초기화 오류: {str(e)}")
            st.error("AI 모델 초기화 중 오류가 발생했습니다. Ollama가 실행 중인지 확인하세요.")

    # 탭별 고유한 세션 상태 키 생성
    chat_history_key = f"chat_history_{tab_index}"
    chat_context_key = f"chat_context_{tab_index}"

    # Initialize conversation history in session state
    if chat_history_key not in st.session_state:
        st.session_state[chat_history_key] = []

    # Initialize context in session state
    if chat_context_key not in st.session_state:
        st.session_state[chat_context_key] = []

    # Get the system message based on current tab
    system_message = get_tab_context(tab_index)

    # 채팅 높이 조정 UI
    if "chat_height" not in st.session_state:
        st.session_state.chat_height = chat_height

    # 모델 설정 UI를 작은 expander로 제공
    with st.expander("모델 설정"):
        selected_model = st.selectbox(
            "모델 선택",
            get_available_models(),
            index=list(model_options.keys()).index(st.session_state.selected_model),
            key=f"model_select_{tab_index}"
        )

        col1, col2 = st.columns(2)
        with col1:
            memory_length = st.slider(
                "대화 기억 길이",
                min_value=0,
                max_value=10,
                value=st.session_state.memory_length,
                key=f"memory_length_{tab_index}"
            )
        with col2:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.temperature,
                step=0.1,
                key=f"temperature_{tab_index}"
            )

        # 채팅 높이 조정 슬라이더
        chat_height = st.slider(
            "채팅창 높이",
            min_value=200,
            max_value=800,
            value=st.session_state.chat_height,
            step=50,
            key=f"chat_height_{tab_index}"
        )

        # 채팅 높이가 변경된 경우 저장
        if chat_height != st.session_state.chat_height:
            st.session_state.chat_height = chat_height

        # 모델 설정이 변경되었다면 대화 체인 다시 초기화
        if (selected_model != st.session_state.selected_model or
            temperature != st.session_state.temperature or
            memory_length != st.session_state.memory_length):
            st.session_state.selected_model = selected_model
            st.session_state.temperature = temperature
            st.session_state.memory_length = memory_length
            try:
                st.session_state.conversation_chain = get_conversation_chain(
                    selected_model=selected_model,
                    temperature=temperature,
                    memory_length=memory_length
                )
                st.success(f"모델이 {selected_model}로 변경되었습니다.")
            except Exception as e:
                print(f"모델 변경 오류: {str(e)}")
                st.error(f"모델 {selected_model}로 변경 중 오류가 발생했습니다.")

    # 채팅 메시지를 표시할 컨테이너
    chat_messages = st.container(height=st.session_state.chat_height)

    # 채팅 메시지 표시
    with chat_messages:
        for message in st.session_state[chat_history_key]:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

    # 채팅 입력 처리를 위한 함수 정의
    def process_input():
        if st.session_state[f"chat_input_{tab_index}"]:
            user_message = st.session_state[f"chat_input_{tab_index}"]

            # 사용자 메시지를 채팅 기록에 추가
            st.session_state[chat_history_key].append({"role": "user", "content": user_message})

            # 입력 필드 초기화
            st.session_state[f"chat_input_{tab_index}"] = ""

            # 채팅 메시지를 표시할 새 메시지 자리 만들기
            with chat_messages:
                st.chat_message("user").write(user_message)
                ai_message = st.chat_message("assistant")

                # Ollama에서 응답 가져오기
                with st.spinner("생각 중..."):
                    try:
                        # LangChain 대화 체인 사용
                        history = [
                            {"type": "human" if msg["role"] == "user" else "ai", "content": msg["content"]}
                            for msg in st.session_state[chat_history_key][:-1]  # 현재 메시지 제외
                        ]

                        response = st.session_state.conversation_chain(user_message, history)

                        # 현재 컨텍스트 업데이트
                        st.session_state[chat_context_key].append({"role": "user", "content": user_message})
                        st.session_state[chat_context_key].append({"role": "assistant", "content": response})

                        # 어시스턴트 응답을 채팅 기록에 추가
                        st.session_state[chat_history_key].append({"role": "assistant", "content": response})

                        # 응답 표시
                        ai_message.write(response)

                    except Exception as e:
                        print(f"응답 생성 오류: {str(e)}")

                        # 오류 발생 시 기존 ollama_chat 함수 사용 (대체 방안)
                        try:
                            response, new_context = ollama_chat(
                                model=st.session_state.selected_model,
                                prompt=user_message,
                                context=st.session_state[chat_context_key],
                                system=system_message
                            )
                            st.session_state[chat_context_key] = new_context

                            # 어시스턴트 응답을 채팅 기록에 추가
                            st.session_state[chat_history_key].append({"role": "assistant", "content": response})

                            # 응답 표시
                            ai_message.write(response)
                        except Exception as inner_e:
                            print(f"대체 응답 생성 오류: {str(inner_e)}")
                            error_msg = "죄송합니다. 응답을 생성할 수 없습니다. Ollama 서버가 실행 중인지 확인해주세요."
                            ai_message.write(error_msg)
                            st.session_state[chat_history_key].append({"role": "assistant", "content": error_msg})

    # 채팅 입력 UI
    st.text_input(
        "iDSB AI에게 질문하세요...",
        key=f"chat_input_{tab_index}",
        on_change=process_input
    )

    # Ollama 상태 표시
    st.caption(f"Powered by Ollama + {model_options[st.session_state.selected_model]} | Temp: {st.session_state.temperature}")

    # 채팅 초기화 버튼
    if st.button("대화 초기화", key=f"clear_chat_{tab_index}"):
        st.session_state[chat_history_key] = []
        st.session_state[chat_context_key] = []
        st.rerun()