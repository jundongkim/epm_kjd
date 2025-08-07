import streamlit as st
import os
import time
import re
from datetime import datetime
import pandas as pd
import numpy as np
from PIL import Image
from langchain_community.llms import Ollama
from langchain_ollama import ChatOllama
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.prompts import MessagesPlaceholder
import logging
from components.process.process_images import get_all_image_paths
from components.process.process_data_loader import find_image_file
from components.process.process_prompt import PROCESS_PROMPT_DICT

# 필요한 유틸리티 함수들
def evaluate_image_relevance(images, query_text):
    """이미지의 관련성을 평가하고 점수를 부여합니다."""
    if not query_text or not images:
        return images

    # 키워드 가중치 설정
    query_keywords = set(re.findall(r'\w+', query_text.lower()))

    for img in images:
        score = 0

        # 설명에서 키워드 매칭
        description = img.get('description', '').lower()
        for keyword in query_keywords:
            if keyword in description:
                score += 3  # 설명에 키워드가 있으면 높은 점수

        # 작업 내용에서 키워드 매칭
        work_details = img.get('work_details', '').lower()
        for keyword in query_keywords:
            if keyword in work_details:
                score += 2  # 작업 내용에 키워드가 있으면 중간 점수

        # 기타 메타데이터 매칭 (공정명, 담당자 등)
        meta_text = f"{img.get('process_name', '')} {img.get('equipment_name', '')} {img.get('manager', '')}".lower()
        for keyword in query_keywords:
            if keyword in meta_text:
                score += 1  # 메타데이터에 키워드가 있으면 낮은 점수

        img['relevance_score'] = score

    return images

def get_top_relevant_images(images, query_text, max_count=3):
    """가장 관련성 높은 이미지를 최대 개수만큼 반환합니다."""
    if not images:
        return []

    # 이미지 관련성 평가
    evaluated_images = evaluate_image_relevance(images, query_text)

    # 관련성 점수로 정렬하고 상위 N개 선택
    relevant_images = sorted(evaluated_images, key=lambda x: x.get('relevance_score', 0), reverse=True)

    return relevant_images[:max_count]


# 컨텍스트 길이 제한 함수
def truncate_context(context: str, max_length: int = 4000) -> str:
    """컨텍스트 길이를 제한하는 함수"""
    if len(context) <= max_length:
        return context

    # 문서 단위로 분리
    docs = context.split("\n\n---\n\n")
    result = []
    current_length = 0

    for doc in docs:
        doc_length = len(doc)
        if current_length + doc_length <= max_length:
            result.append(doc)
            current_length += doc_length
        else:
            break

    return "\n\n---\n\n".join(result)

# ChainWrapper 클래스
class ChainWrapper:
    """대화형 체인 래퍼 클래스"""
    def __init__(self, chain, retriever, max_history=5):
        self.chain = chain
        self.retriever = retriever
        self.max_history = max_history

    def invoke(self, inputs):
        try:
            # 문서 검색 수행
            question = inputs["question"]
            try:
                docs = self.retriever.get_relevant_documents(question)
                # 검색 결과 로깅
                logging.info(f"invoke 검색 결과: {len(docs)}개 문서")
                if docs:
                    for i, doc in enumerate(docs[:2]):  # 처음 2개만 로깅
                        logging.info(f"문서 {i+1} 내용: {doc.page_content[:100]}...")
                else:
                    logging.warning("검색 결과가 없습니다.")
            except Exception as search_error:
                error_str = str(search_error)
                # 차원 불일치 오류 처리
                if "assert d == self.d" in error_str or "dimension mismatch" in error_str:
                    st.error("벡터 차원 불일치 오류가 발생했습니다. 새로운 벡터 DB를 생성해주세요.")
                    return {
                        "answer": "죄송합니다. 벡터 DB 오류가 발생했습니다. 사이드바의 '벡터 DB 재설정' 버튼을 클릭한 후 데이터를 다시 로드해주세요.",
                        "source_documents": []
                    }
                # 기타 검색 오류 처리
                logging.error(f"검색 중 오류: {error_str}")
                docs = []  # 빈 문서 리스트로 진행

            # 검색된 문서들의 컨텍스트 구성 및 길이 제한
            context = truncate_context(self._format_context(docs))

            # 문서가 없는 경우 특별한 컨텍스트 제공
            if not docs:
                context += "\n\n참고: 일치하는 문서를 찾지 못했습니다. 일반적인 지식을 기반으로 답변하겠습니다."

            # 대화 이력 관리
            history = self._manage_history(inputs.get("history", []))

            # 체인 실행 (컨텍스트 포함)
            chain_response = self.chain.invoke({
                "question": question,
                "context": context,
                "history": history
            })

            # 응답과 소스 문서 반환
            return {
                "answer": chain_response,
                "source_documents": docs
            }
        except Exception as e:
            import traceback
            logging.error(f"응답 생성 중 오류: {str(e)}")
            logging.error(traceback.format_exc())
            return {
                "answer": f"오류가 발생했습니다: {str(e)}",
                "source_documents": []
            }

    def stream_response(self, inputs, message_placeholder):
        try:
            # 문서 검색 수행
            question = inputs["question"]

            try:
                docs = self.retriever.invoke(question)
                # 검색 결과 로깅
                logging.info(f"검색 결과: {len(docs)}개 문서")
                if docs:
                    for i, doc in enumerate(docs[:3]):  # 처음 3개만 로깅
                        logging.info(f"문서 {i+1} 내용: {doc.page_content[:100]}...")
                else:
                    logging.warning("검색 결과가 없습니다.")
            except Exception as search_error:
                error_str = str(search_error)
                # 차원 불일치 오류 처리
                if "assert d == self.d" in error_str or "dimension mismatch" in error_str:
                    message_placeholder.error("벡터 차원 불일치 오류가 발생했습니다. 새로운 벡터 DB를 생성해주세요.")
                    error_msg = "죄송합니다. 벡터 DB 오류가 발생했습니다. 사이드바의 '벡터 DB 재설정' 버튼을 클릭한 후 데이터를 다시 로드해주세요."
                    message_placeholder.markdown(error_msg)
                    return {"answer": error_msg, "source_documents": []}, error_msg
                # 기타 검색 오류 처리
                logging.error(f"검색 중 오류: {error_str}")
                docs = []

            # 검색된 문서들의 컨텍스트 구성 및 길이 제한
            context = truncate_context(self._format_context(docs))

            # 문서가 없는 경우 특별한 컨텍스트 제공
            if not docs:
                context += "\n\n참고: 일치하는 문서를 찾지 못했습니다. 일반적인 지식을 기반으로 답변하겠습니다."

            # 대화 이력 관리
            history = self._manage_history(inputs.get("history", []))

            # 응답 생성 시작
            full_response = ""

            # 스트리밍 응답 처리
            for chunk in self.chain.stream({
                "question": question,
                "context": context,
                "history": history
            }):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)  # 자연스러운 타이핑 효과

            # 최종 응답 표시
            message_placeholder.markdown(full_response)

            return {"answer": full_response, "source_documents": docs}, full_response
        except Exception as e:
            import traceback
            logging.error(f"스트리밍 응답 생성 중 오류: {str(e)}")
            logging.error(traceback.format_exc())
            error_msg = f"오류가 발생했습니다: {str(e)}"
            message_placeholder.error(error_msg)
            return {"answer": error_msg, "source_documents": []}, error_msg

    def _manage_history(self, history):
        """대화 이력 관리 함수"""
        # 최대 이력 길이 제한
        if len(history) > self.max_history * 2:
            return history[-self.max_history * 2:]
        return history

    def _format_context(self, docs):
        """문서 컨텍스트 포맷팅"""
        if not docs:
            return "관련 정보를 찾지 못했습니다."

        formatted_docs = []

        for i, doc in enumerate(docs):
            metadata = doc.metadata
            content = doc.page_content.strip()

            # 문서별 메타데이터 및 내용 포맷팅
            doc_info = [
                f"### 문서 {i+1}",
                f"**공정명:** {metadata.get('process_name', 'N/A')}",
                f"**설비명:** {metadata.get('equipment_name', 'N/A')}"
            ]

            # 담당자 정보가 있는 경우에만 추가
            if metadata.get('manager') and metadata.get('manager') != 'N/A':
                doc_info.append(f"**담당자:** {metadata.get('manager', 'N/A')}")

            # 작업일자 정보가 있는 경우에만 추가
            if metadata.get('work_date') and metadata.get('work_date') != 'N/A':
                doc_info.append(f"**작업일자:** {metadata.get('work_date', 'N/A')}")

            # 작업종류 정보가 있는 경우에만 추가
            if metadata.get('work_type') and metadata.get('work_type') != 'N/A':
                doc_info.append(f"**작업종류:** {metadata.get('work_type', 'N/A')}")

            # 작업내용 추가
            doc_info.append("\n**작업내용:**")
            doc_info.append(content)

            formatted_docs.append("\n".join(doc_info))

        return "\n\n---\n\n".join(formatted_docs)


# 대화 체인 생성 함수
def get_conversation_chain(vector_store, selected_model="gemma3:4b", temperature=0.2, memory_length=5):
    """공정관리이력 대화 체인을 생성합니다."""

    # 레트리버 (벡터 스토어 기반 검색) 설정
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4,  # 검색 결과 개수
            "include_metadata": True,
            "score_threshold": 0.45  # 유사도 임계값 (0.45 이상만 반환)
        }
    )

    # 프롬프트 초기화
    language = st.session_state["process_language"]
    # 시스템 프롬프트 구성
    system_prompt = PROCESS_PROMPT_DICT[language]["system_template"]
    language_prompt = PROCESS_PROMPT_DICT[language]["language_prompt"]

    # 전체 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        SystemMessagePromptTemplate.from_template(language_prompt),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ])

    # 모델 초기화
    try:
        model_kwargs = {"temperature": temperature}
        if "max_tokens" in st.session_state and st.session_state.max_tokens:
            model_kwargs["max_tokens"] = st.session_state.max_tokens

        llm = ChatOllama(
            model=selected_model,
            base_url=st.session_state.get("ollama_base_url", "http://localhost:11434"),
            **model_kwargs
        )
    except Exception as e:
        st.error(f"모델 초기화 오류: {str(e)}")
        return None

    # 전체 체인 구성
    chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    # 최종 체인 래퍼 반환
    return ChainWrapper(chain, retriever, max_history=memory_length)

# 채팅 인터페이스 표시 함수
def show_process_chat():
    """공정관리이력 채팅 인터페이스를 표시합니다."""
    st.title("💬 공정관리이력 채팅")

    # 공정관리이력 데이터 및 벡터 스토어 확인
    if "process_data" not in st.session_state:
        st.error("공정관리이력 데이터가 로드되지 않았습니다.")
        return

    if "process_vector_store" not in st.session_state:
        st.error("벡터 저장소가 초기화되지 않았습니다.")
        return

    # 채팅 이력 초기화
    if "process_chat_history" not in st.session_state:
        st.session_state.process_chat_history = []

    # 사이드바 - 대화 초기화 버튼만 표시
    with st.sidebar:
        # 대화 초기화 버튼
        if st.button("대화 초기화", type="primary", key="process_chat_reset_btn"):
            st.session_state.process_chat_history = []
            st.rerun()

    # 대화 이력 표시
    for message in st.session_state.process_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # 소스 문서 표시 (AI 응답인 경우)
            if message["role"] == "assistant" and "source_documents" in message:
                source_docs = message["source_documents"]
                if source_docs:
                    with st.expander("참고 문서", expanded=False):
                        for i, doc in enumerate(source_docs):
                            st.markdown(f"**문서 {i+1}**")

                            # 메타데이터 표시
                            metadata = doc.metadata
                            st.markdown(f"""
                            - **공정명:** {metadata.get('process_name', 'N/A')}
                            - **담당자:** {metadata.get('manager', 'N/A')}
                            - **작업일자:** {metadata.get('work_date', 'N/A')}
                            """)

                            # 내용 표시
                            st.markdown("**내용:**")
                            st.markdown(doc.page_content)

                            # 구분선 추가
                            if i < len(source_docs) - 1:
                                st.markdown("---")

            # 관련 이미지 표시 (AI 응답인 경우)
            if message["role"] == "assistant" and "related_images" in message and message["related_images"]:
                with st.expander("관련 이미지", expanded=False):
                    images = message["related_images"]
                    # 이미지를 3열로 표시
                    cols = st.columns(min(len(images), 3))

                    for i, img in enumerate(images):
                        col_idx = i % len(cols)
                        with cols[col_idx]:
                            if os.path.exists(img["path"]):
                                st.image(img["path"], caption=img["filename"])

                                if img.get("description"):
                                    st.markdown("**이미지 설명:**")
                                    st.markdown(img['description'])

                                # 기타 메타데이터
                                st.markdown(f"""
                                - **공정명:** {img.get('process_name', 'N/A')}
                                - **설비명:** {img.get('equipment_name', 'N/A')}
                                - **일자:** {img.get('work_date', 'N/A')}
                                """)

    language_col, input_col = st.columns([1.2, 8.8])
    # 출력 언어 선택
    with language_col:
        language = st.selectbox("언어 선택", ["한국어", "헝가리어", "인도네시아어"], index=0, format_func=lambda x: f"🌐 {x}", label_visibility="collapsed")
        st.session_state["process_language"] = language

        try:
            # 앱 설정이나 기본값 사용
            # 앱 전체 설정 확인, 없으면 기본값 사용
            selected_model = st.session_state.get("selected_model", "gemma3:4b")
            temperature = st.session_state.get("temperature", 0.2)
            memory_length = st.session_state.get("memory_length", 5)

            # 대화 체인 초기화 - 언어 선택 시마다 새로 생성하여 설정 변경사항 반영
            chain = get_conversation_chain(
                vector_store=st.session_state.process_vector_store,
                selected_model=selected_model,
                temperature=temperature,
                memory_length=memory_length
            )
        except Exception as e:
            st.error(f"대화 체인 초기화 중 오류 발생: {str(e)}")
            return

    # 사용자 입력 처리
    with input_col:
        input_placeholder = PROCESS_PROMPT_DICT[language]["input_placeholder"]

        if question := st.chat_input(input_placeholder):
            # 사용자 메시지 추가
            st.session_state.process_chat_history.append({"role": "user", "content": question})

            # 사용자 메시지 표시
            with st.chat_message("user"):
                st.markdown(question)

            # 대화 이력 변환 (langchain 형식)
            history = []
            for msg in st.session_state.process_chat_history[:-1]:  # 방금 추가한 메시지 제외
                if msg["role"] == "user":
                    history.append({"type": "human", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    history.append({"type": "ai", "content": msg["content"]})

            if not chain:
                st.error("대화 체인을 생성할 수 없습니다.")
                return

            # AI 응답 생성
            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                # 응답 생성 (스트리밍)
                with st.spinner("응답 생성 중..."):
                    try:
                        # 스트리밍 응답 생성
                        response_obj, response_text = chain.stream_response(
                            {"question": question, "history": history},
                            message_placeholder
                        )

                        # 소스 문서 준비
                        source_documents = response_obj.get("source_documents", [])

                        # 관련 이미지 찾기
                        all_images = get_all_image_paths(st.session_state.process_data)
                        related_images = get_top_relevant_images(all_images, question, max_count=3)

                        # 응답에 소스 문서 및 관련 이미지 추가
                        st.session_state.process_chat_history.append({
                            "role": "assistant",
                            "content": response_text,
                            "source_documents": source_documents,
                            "related_images": related_images
                        })

                        # 소스 문서 표시
                        if source_documents:
                            with st.expander("참고 문서", expanded=False):
                                for i, doc in enumerate(source_documents):
                                    st.markdown(f"**문서 {i+1}**")

                                    # 메타데이터 표시
                                    metadata = doc.metadata
                                    st.markdown(f"""
                                    - **공정명:** {metadata.get('process_name', 'N/A')}
                                    - **담당자:** {metadata.get('manager', 'N/A')}
                                    - **작업일자:** {metadata.get('work_date', 'N/A')}
                                    """)

                                    # 내용 표시
                                    st.markdown("**내용:**")
                                    st.markdown(doc.page_content)

                                    # 구분선 추가
                                    if i < len(source_documents) - 1:
                                        st.markdown("---")

                        # 관련 이미지 표시
                        if related_images:
                            with st.expander("관련 이미지", expanded=False):
                                # 이미지를 3열로 표시
                                cols = st.columns(min(len(related_images), 3))

                                for i, img in enumerate(related_images):
                                    col_idx = i % len(cols)
                                    with cols[col_idx]:
                                        if os.path.exists(img["path"]):
                                            st.image(img["path"], caption=img["filename"])

                                            if img.get("description"):
                                                st.markdown("**이미지 설명:**")
                                                st.markdown(img['description'])

                                            # 기타 메타데이터
                                            st.markdown(f"""
                                            - **공정명:** {img.get('process_name', 'N/A')}
                                            - **설비명:** {img.get('equipment_name', 'N/A')}
                                            - **일자:** {img.get('work_date', 'N/A')}
                                            """)

                    except Exception as e:
                        st.error(f"응답 생성 중 오류 발생: {str(e)}")
                        # 오류 메시지도 대화 이력에 추가
                        st.session_state.process_chat_history.append({
                            "role": "assistant",
                            "content": f"오류가 발생했습니다: {str(e)}"
                        })