import os
import traceback
from typing import Union, List, Dict, Any, Optional, Tuple, Iterator

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from langchain_ollama import ChatOllama
from langchain.schema import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import BasePromptTemplate, PromptTemplate, ChatPromptTemplate
from langchain_core.prompt_values import PromptValue
from langchain_core.output_parsers import StrOutputParser

# Ollama 서버 URL 설정
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def _invoke_prompt(prompt: Union[str, PromptTemplate, ChatPromptTemplate, List[BaseMessage]]) -> Union[PromptValue, str]:
    """프롬프트 변환 함수

    사용자가 입력한 다양한 형태의 프롬프트를 PromptValue / str으로 변환합니다.
    문자열 형태의 프롬프트는 그대로 반환되고,
    PromptTemplate, ChatPromptTemplate, List[BaseMessage] 형태의 프롬프트는 PromptValue 형태로 변환됩니다.

    Args:
        prompt: 문자열, PromptTemplate, ChatPromptTemplate 또는 List[BaseMessage] 형태의 프롬프트

    Returns:
        PromptValue / str: 변환된 PromptValue / str 형태의 프롬프트
    """
    # 프롬프트 유형에 따라 적절한 문자열 생성
    if isinstance(prompt, str):
        result_prompt = prompt
    elif isinstance(prompt, PromptTemplate):
        result_prompt = prompt.invoke({})
    elif isinstance(prompt, ChatPromptTemplate):
        result_prompt = prompt.invoke({})
    elif isinstance(prompt, list) and all(isinstance(m, BaseMessage) for m in prompt):
        result_prompt = ChatPromptTemplate(messages=prompt).invoke({})
    else:
        result_prompt = str(prompt)

    return result_prompt

def _invoke_llm(prompt: Union[PromptValue, str]) -> str:
    """LLM 호출 함수

    Args:
        prompt: PromptValue / str 형태의 프롬프트

    Returns:
        str: 응답 텍스트
    """
    try:
        llm = ChatOllama(
            model=st.session_state.get("selected_model", "gemma3:4b-it-qat"),
            temperature=st.session_state.get("temperature", 0.2)
        )
        full_response = (llm | StrOutputParser()).invoke(prompt)
        return full_response
    except Exception as e:
        return f"에러 발생: {str(e)}"

def _stream_llm(prompt: Union[PromptValue, str]) -> Iterator[BaseMessage]:
    """LLM 스트리밍 호출 함수

    Args:
        prompt_template: PromptTemplate, ChatPromptTemplate 형태의 프롬프트

    Returns:
        Iterator[BaseMessage]: 스트리밍 응답 생성기
    """
    try:
        llm = ChatOllama(
            model=st.session_state.get("selected_model", "gemma3:4b-it-qat"),
            temperature=st.session_state.get("temperature", 0.2)
        )
        return (llm | StrOutputParser()).stream(prompt)
    except Exception as e:
        return Iterator[str]([f"에러 발생: {str(e)}"])

def generate_ai_analysis(
    prompt: Union[str, PromptTemplate, ChatPromptTemplate, List[BaseMessage]],
    key_prefix: str = "analysis",
    message_placeholder: Optional[DeltaGenerator] = None,
    streaming: bool = True
) -> Tuple[Any, str, Optional[Dict]]:
    """AI 분석 실행 및 결과 반환

    여러 형태의 프롬프트를 지원하며 LLM을 통해 분석 결과를 생성합니다.

    Args:
        prompt: 문자열, PromptTemplate, ChatPromptTemplate 또는 메시지 목록 형태의 프롬프트
        key_prefix: 세션 상태 변수 접두어
        message_placeholder: 메시지를 표시할 streamlit placeholder
        streaming: 스트리밍 응답 사용 여부, 스트리밍 응답 사용 시 message_placeholder 필수

    Returns:
        tuple: (응답 객체, 전체 응답 텍스트, 메타데이터)
    """

    # 세션 상태 키 정의
    running_state_key = f"{key_prefix}_running"

    try:
        # 프롬프트 변환
        prompt = _invoke_prompt(prompt)

        # streaming 여부에 따른 처리
        if streaming:
            response_generator = _stream_llm(prompt)

            full_response = ""
            if message_placeholder:
                full_response = display_streamlit_analysis(response_generator, message_placeholder)
            else:
                for chunk in response_generator:
                    full_response += chunk

            response = {
                "answer": full_response,
                "source_documents": []
            }
        else:
            full_response = _invoke_llm(prompt)

            if message_placeholder:
                message_placeholder.markdown(full_response)

            response = {
                "answer": full_response,
                "source_documents": []
            }

        # 분석 상태 업데이트
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = False

        return response, full_response, None

    except Exception as e:
        error_msg = f"AI 분석 처리 중 오류가 발생했습니다: {str(e)}"
        if message_placeholder:
            message_placeholder.error(error_msg)
            message_placeholder.error(traceback.format_exc())

        # 분석 상태 업데이트
        if running_state_key in st.session_state:
            st.session_state[running_state_key] = False

        return None, error_msg, None

def display_streamlit_analysis(response_generator: Iterator[BaseMessage], message_placeholder: DeltaGenerator):
    """LLM의 분석 스트리밍 응답을 표시하는 함수

    Args:
        response_generator (generator): LLM의 스트리밍 응답 생성기
        message_placeholder (Any): 메시지를 표시할 streamlit placeholder

    Returns:
        str: 전체 응답 텍스트
    """
    # 응답 스트리밍을 위한 변수
    full_response = ""

    # 스트리밍 응답 생성
    for chunk in response_generator:
        full_response += chunk
        message_placeholder.markdown(full_response + "▌")

    # 스트리밍 완료 후 최종 응답 표시
    message_placeholder.markdown(full_response)

    return full_response
