"""
PRD(생산이슈리포트) 챗봇 인터페이스 모듈
"""

import os
import re
import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.prompts import MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.callbacks.base import BaseCallbackHandler

from components.prd.prd_data_loader import load_prd_data, load_or_create_vector_db, find_image_file

# 문서 관련성 평가 함수
def evaluate_docs_relevance(docs, query_text):
    """문서의 관련성을 평가하고 점수를 부여합니다."""
    if not query_text or not docs:
        return docs

    # 키워드 가중치 설정
    query_keywords = set(re.findall(r'\w+', query_text.lower()))

    for doc in docs:
        score = 0

        is_file = doc.get('is_file', False)

        # 요약에서 키워드 매칭
        if is_file:
            # 현황 + 원인만 사용
            summary = f"{doc.get('summary', {}).get('situation', '').lower()} {doc.get('summary', {}).get('cause', '').lower()}"
            # 이슈 정보 포함
            summary += " ".join(doc.get('issues', [])).lower()
        else:
            summary = doc.get('summary', '').lower()

        for keyword in query_keywords:
            if keyword in summary:
                score += 3  # 요약에 키워드가 있으면 높은 점수

        # 파일인 경우; 요약-조치사항에서 키워드 매칭
        if is_file:
            action = doc.get('summary', {}).get('action', '').lower()
            for keyword in query_keywords:
                if keyword in action:
                    score += 1  # 조치사항에 키워드가 있으면 낮은 점수

        # 제목에서 키워드 매칭
        if is_file:
            title = doc.get('title', '').lower()
        else:
            # 파일 제목 + 페이지 제목
            title = f"{doc.get('parent_file', {}).get('title', '').lower()} {doc.get('title', '').lower()}"

        for keyword in query_keywords:
            if keyword in title:
                score += 2  # 제목에 키워드가 있으면 중간 점수

        # # 파일인 경우; 기타 메타데이터 매칭 (라인, 설비번호 등)
        # if is_file:
        #     meta_text = f"{doc.get('line', '')} {doc.get('equipment', '')}".lower()

        #     for keyword in query_keywords:
        #         if keyword in meta_text:
        #             score += 1  # 메타데이터에 키워드가 있으면 낮은 점수

        doc['relevance_score'] = score

    return docs

def get_top_relevant_docs(docs, query_text, max_count=3):
    """가장 관련성 높은 문서를 최대 개수만큼 반환합니다."""
    if not docs:
        return []

    # 이미지 관련성 평가
    evaluated_docs = evaluate_docs_relevance(docs, query_text)

    # 관련성 점수로 정렬하고 상위 N개 선택
    relevant_docs = sorted(evaluated_docs, key=lambda x: x.get('relevance_score', 0), reverse=True)
    return relevant_docs[:max_count]

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
                docs = []  # 빈 문서 리스트로 진행

            # 검색된 문서들의 컨텍스트 구성 및 길이 제한
            context = truncate_context(self._format_context(docs))

            # 문서가 없는 경우 특별한 컨텍스트 제공
            if not docs:
                context += "\n\n참고: 일치하는 문서를 찾지 못했습니다. 일반적인 지식을 기반으로 답변하겠습니다."

            # 대화 이력 관리
            history = self._manage_history(inputs.get("history", []))

            # 응답 스트리밍을 위한 변수
            full_response = ""

            # 스트리밍 응답 생성 (컨텍스트 포함)
            for chunk in self.chain.stream({
                "question": question,
                "context": context,
                "history": history
            }):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

            # 최종 응답 (커서 없이)
            message_placeholder.markdown(full_response)

            # 최종 응답과 소스 문서 반환
            return {
                "answer": full_response,
                "source_documents": docs
            }, full_response
        except Exception as e:
            # 오류 세부 정보 로깅
            st.error(f"Stream 응답 생성 중 오류: {str(e)}")
            import traceback
            logging.error(f"스트리밍 응답 생성 중 오류: {str(e)}")
            logging.error(traceback.format_exc())
            error_msg = f"오류가 발생했습니다: {str(e)}"
            message_placeholder.markdown(error_msg)
            # 빈 응답 반환
            return {"answer": error_msg, "source_documents": []}, error_msg

    def _manage_history(self, history):
        """대화 이력을 관리하는 함수"""
        if not history:
            return []

        # 최근 N개의 대화만 유지
        return history[-self.max_history:]

    def _format_context(self, docs):
        """검색된 문서들을 포맷팅하여 컨텍스트 생성"""
        if not docs:
            return "관련 문서를 찾을 수 없습니다."

        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            try:
                # 메타데이터 추출
                metadata = doc.metadata
                is_file = metadata.get('is_file', False)
                if is_file:
                    # Document = 파일
                    file_name = metadata.get('file_name', '파일명 정보 없음')
                    date = metadata.get('date', '날짜 정보 없음')
                    line = metadata.get('lines', ['대상 라인 정보 없읍'])
                    equipment = metadata.get('equipments', ['대상 설비 정보 없읍'])
                    issue = metadata.get('issues', ['발생 이슈 정보 없음'])
                    title = metadata.get('title', '제목 없음')
                    # 문서 포맷팅 (더 자세한 정보 포함)
                    formatted_doc = f"""#### 문서: {file_name}
제목: {title}
날짜: {date}
라인: {line}
설비: {equipment}
이슈: {issue}
내용:
{doc.page_content.strip()}"""
                    # 로깅을 통해 각 문서의 세부 정보 기록
                    logging.info(f"문서 {i} 세부 정보 - 라인: {line}, 설비: {equipment}, 날짜: {date}, 제목: {title}")
                else:
                    # Document = 페이지
                    # 파일 정보 추출
                    parent_file = metadata.get('parent_file', {})
                    file_name = parent_file.get('file_name', '파일명 정보 없음')
                    date = parent_file.get('date', '날짜 정보 없음')
                    line = parent_file.get('lines', ['대상 라인 정보 없읍'])
                    equipment = parent_file.get('equipments', ['대상 설비 정보 없읍'])
                    issue = parent_file.get('issues', ['발생 이슈 정보 없음'])
                    title = parent_file.get('title', '제목 없음')
                    # 페이지 정보 추출
                    page_number = metadata.get('page_number', '페이지 번호 정보 없음')
                    # 문서 포맷팅 (더 자세한 정보 포함)
                    formatted_doc = f"""#### 문서: {file_name} - {page_number} 페이지
제목: {title}
날짜: {date}
라인: {line}
설비: {equipment}
이슈: {issue}
내용:
{doc.page_content.strip()}"""
                    # 로깅을 통해 각 문서의 세부 정보 기록
                    logging.info(f"문서 {i} 세부 정보 - 라인: {line}, 설비: {equipment}, 날짜: {date}, 제목: {title}, 페이지 번호: {page_number}")

                # 이미지 정보 추가
                # if "image_dir" in metadata and metadata["image_dir"]:
                #     formatted_doc += f"\n관련 이미지: {len(metadata['image_dir'])}개"

                # 로깅을 통해 각 문서의 세부 정보 기록
                # logging.info(f"문서 {i} 세부 정보 - 라인: {line}, 설비: {equipment}, 제목: {title}, 날짜: {date}")

                formatted_docs.append(formatted_doc)

            except Exception as e:
                # 문서 포맷팅 중 오류가 발생해도 계속 진행
                st.warning(f"문서 {i} 포맷팅 중 오류: {str(e)}")
                formatted_docs.append(f"[문서{i}] 오류로 인해 형식화 실패")

        # 모든 문서를 하나의 문자열로 결합
        return "\n\n---\n\n".join(formatted_docs)

# 한국어 프롬프트
system_template_kr = """당신은 생산이슈리포트 데이터에 대한 질문에 답변하는 AI 어시스턴트입니다.
다음 컨텍스트 정보를 사용하여 사용자의 질문에 정확하게 답변하세요.

### 컨텍스트 정보 ###
{context}

### 답변 원칙 ###
1. 전문 용어가 등장할 경우 반드시 쉬운 설명을 덧붙이세요.
2. 데이터에 기반한 객관적인 분석을 제공하세요.
3. 실행 가능한 구체적인 해결책을 제시하세요.

### 답변 문법 ###
- **제목**: 응답 상단에 `## 제목` 형식의 주제 제목을 반드시 추가하세요.
- **소제목**: 각 섹션에 `### 소제목` 형식을 사용해 명확하게 구분하세요.
- **강조**: 중요한 내용은 **강조** 또는 __강조__ 표시를 활용하세요.
- **목록**: 순서 없는 목록은 `-` 또는 `*`, 순서 있는 목록은 `1.` 형식을 사용하세요.
- **표**: 데이터 비교가 필요할 때 마크다운 표를 사용하세요.

### 응답 형식 ###
```
<answer_format>
답변을 다음 세 단계로 구조화하여 제공하세요:
## 분석 결과
### 1. 기본 정보
- 라인 및 설비 정보
- 날짜 및 이슈 정보

---

### 2. 상세 분석
- 현황 분석
- 원인 분석
- 조치 사항 및 재발 방지 대책 분석

---

### 3. 개선 방안
- 예방 조치 제안
- 생산성 향상 방안
- 위험 관리 대책
</answer_format>
```

### 중요 ###
- 반드시 컨텍스트에서 찾은 정보는 출처 문서 번호를 포함하여 답변의 근거를 제시하세요. 예: [문서1에 따르면...]
- 만약 특정 단계에 대한 정보가 부족하다면, 일반적인 지식을 바탕으로 합리적인 제안을 제공하되 이것이 추론임을 명시하세요.
"""

# 대화형 체인 생성 함수
def get_conversation_chain(vector_store, selected_model="gemma:7b", temperature=0.2, memory_length=5):
    """대화형 체인을 생성합니다.

    Args:
        vector_store: FAISS 벡터 저장소 인스턴스
        selected_model (str): 사용할 Ollama 모델 이름 (기본값: "gemma:7b")
        temperature (float): 생성 모델의 temperature 값 (기본값: 0.2)
        memory_length (int): 대화 기억 길이 (기본값: 5)

    Returns:
        ChainWrapper: 대화형 체인 래퍼 인스턴스
    """

    # 프롬프트 템플릿 초기화
    CHAT_PROMPT = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template_kr),
        SystemMessagePromptTemplate.from_template("한국어로 답변하세요."),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{question}")
    ])

    # Ollama API 서버 URL 설정
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Ollama 모델 초기화
    llm = ChatOllama(
        model=selected_model,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        streaming=True,  # 스트리밍 응답 활성화
    )

    # 세션 상태에서 점수 임계값 가져오기 - 슬라이더 값 직접 사용
    score_threshold = st.session_state.prd_score_threshold

    # 벡터 스토어를 retriever로 변환
    retriever = vector_store.as_retriever(
        search_type="similarity",  # 유사도 기반 검색 사용
        search_kwargs={
            "k": 7,  # 상위 7개 문서 검색
            "score_threshold": score_threshold  # 세션에서 가져온 임계값 사용
        }
    )

    # LCEL 체인 구성
    chain = (
        {
            "context": lambda x: x["context"],  # 이미 포맷팅된 컨텍스트 사용
            "question": lambda x: x["question"],
            "history": lambda x: x.get("history", [])
        }
        | CHAT_PROMPT
        | llm
        | StrOutputParser()
    )

    return ChainWrapper(chain, retriever, max_history=memory_length)

def show_prd_chat():
    """생산이슈리포트 챗봇 인터페이스를 표시합니다."""
    st.title("💬 생산이슈리포트 챗봇")

    # 더 많은 옵션 제공
    with st.sidebar.expander("고급 설정"):
        # 검색 점수 임계값 조정
        score_threshold = st.slider(
            "검색 점수 임계값",
            min_value=0.1,
            max_value=0.7,
            value=0.3,
            step=0.05,
            help="낮을수록 더 많은 관련 문서를 검색합니다.",
            key="prd_score_threshold"
        )

    # 데이터 자동 로드
    if "prd_data" not in st.session_state:
        with st.spinner("생산이슈리포트 데이터를 로드 중입니다..."):
            st.session_state.prd_data = load_prd_data()
            if not st.session_state.prd_data:
                st.error("생산이슈리포트 데이터를 로드할 수 없습니다.")
                return

    # 벡터 저장소 자동 초기화
    if "prd_vector_store" not in st.session_state:
        with st.spinner("벡터 데이터베이스를 초기화하는 중입니다..."):
            st.session_state.prd_vector_store = load_or_create_vector_db(
                st.session_state.prd_data,
                vector_dir="PRD/vector_db"
            )
            if not st.session_state.prd_vector_store:
                st.error("벡터 저장소를 초기화할 수 없습니다.")
                return
            else:
                st.success("벡터 저장소가 성공적으로 초기화되었습니다.")

    # 생산이슈리포트 데이터와 벡터 저장소 확인
    if "prd_data" not in st.session_state:
        st.error("생산이슈리포트 데이터가 로드되지 않았습니다.")
        return

    if "prd_vector_store" not in st.session_state:
        st.error("벡터 저장소가 초기화되지 않았습니다.")
        return

    # 데이터 및 벡터 저장소 가져오기
    prd_data = st.session_state.prd_data
    vector_store = st.session_state.prd_vector_store

    # 세션 상태 초기화
    if "prd_messages" not in st.session_state:
        st.session_state.prd_messages = []

    # 대화 기록 표시
    for message in st.session_state.prd_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 채팅 이력 이후에 이미지 표시
    last_msg_with_images = None
    for msg in reversed(st.session_state.prd_messages):
        if msg["role"] == "assistant" and "doc_details" in msg and msg["doc_details"]:
            last_msg_with_images = msg
            break

    # 문서가 있을 때만 섹션 표시
    if last_msg_with_images and last_msg_with_images["doc_details"]:
        st.markdown("---")
        st.markdown("### 📷 관련 보고서 (최대 3건)")

        doc_details = last_msg_with_images["doc_details"]

        # 이미지를 직접 표시 (최대 3장)
        for doc_detail in doc_details:
            is_file = doc_detail.get('is_file', False)
            if is_file:
                # 파일인 경우
                with st.container(border=True):
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        # 각 파일의 첫 페이지를 썸네일로 사용
                        st.image(doc_detail["pages"][0]["image_path"], use_container_width=True)
                    with col2:
                        # 보고서 정보 표시
                        markdown_content = f"""## {doc_detail['file_name']}
### (관련성 점수: {doc_detail.get('relevance_score', 0)})
- **제목**: {doc_detail.get('title', '보고서 제목 없음')}
- **날짜**: {doc_detail.get('date', '날짜 정보 없음')}
- **라인**: {', '.join(doc_detail.get('lines', ['대상 라인 정보 없음']))}
- **설비**: {', '.join(doc_detail.get('equipments', ['대상 설비 정보 없음']))}
- **이슈**: {', '.join(doc_detail.get('issues', ['발생 이슈 정보 없음']))}

#### 요약
{doc_detail.get('summary', {}).get('full_text', '요약 없음')}"""
                        st.markdown(markdown_content)

                    # 보고서 내용 표시
                    with st.expander(f"'{doc_detail.get('title', '보고서 제목 없음')}' 내용 보기", expanded=False):
                        for page in doc_detail["pages"]:
                            col1, col2 = st.columns([2, 3])
                            with col1:
                                st.image(page["image_path"], use_container_width=True)
                            with col2:
                                st.markdown(f"#### 제목\n{page.get('title', '제목 없음')}")
                                st.markdown(f"#### 요약\n{page.get('summary', '요약 없음')}")
                            st.markdown("---")
            else:
                # 페이지인 경우
                if os.path.exists(doc_detail["image_path"]):
                    with st.container(border=True):
                        col1, col2 = st.columns([2, 3])
                        with col1:
                            st.image(doc_detail["image_path"], use_container_width=True)
                        with col2:
                            title = f"## {doc_detail.get('parent_file', {}).get('file_name', '보고서 제목 없음')} - {doc_detail.get('page_number', '페이지 정보 없음')} 페이지"
                            subtitle = f"### {doc_detail.get('title', '페이지 제목 없음')}"
                            score = f"### (관련성 점수: {doc_detail.get('relevance_score', 0)})"
                            summary = f"#### 요약\n{doc_detail.get('summary', '요약 없음')}"
                            st.markdown(title)
                            st.markdown(subtitle)
                            st.markdown(score)
                            st.markdown(summary)

            st.markdown("---")

    # 모델 설정
    selected_model = st.session_state.get("selected_model", "gemma3:4b-it-qat")
    memory_length = st.session_state.get("memory_length", 5)
    temperature = st.session_state.get("temperature", 0.2)

    try:
        # 대화 체인 초기화 - 벡터 저장소가 있을 때만 실행
        if "prd_conversation_chain" not in st.session_state and vector_store:
            st.session_state.prd_conversation_chain = get_conversation_chain(
                vector_store,
                selected_model=selected_model,
                temperature=temperature,
                memory_length=memory_length
            )
    except Exception as e:
        st.error(f"대화 체인 초기화 중 오류 발생: {str(e)}")
        return

    # 사용자 입력 처리
    if question := st.chat_input("생산이슈리포트에 대해 궁금한 점을 입력해주세요..."):
        # 사용자 메시지를 채팅 기록에 추가
        st.session_state.prd_messages.append({"role": "user", "content": question})

        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(question)

        # 응답 생성
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            try:
                with st.spinner("응답 생성 중..."):
                    # 스트리밍 응답 생성
                    response, full_response = st.session_state.prd_conversation_chain.stream_response(
                        {"question": question},
                        message_placeholder
                    )

                    # 관련 문서 정보 추출
                    doc_details = []

                    if response and "source_documents" in response:
                        for doc in response["source_documents"]:
                            doc_details.append(doc.metadata)

                    # 관련성 평가 및 중복 제거
                    if doc_details:
                        # 중복 제거
                        file_docs = []
                        page_docs = []
                        for d in doc_details:
                            is_file = d.get('is_file', False)
                            if is_file:
                                file_docs.append(d)
                            else:
                                page_docs.append(d)

                        unique_docs = {}
                        # 파일 정보 우선 추가
                        for d in file_docs:
                            if d['file_name'] not in unique_docs:
                                unique_docs[d['file_name']] = d
                        # 페이지 정보 추가
                        # - 페이지가 포함된 파일이 이미 추가되어있는 경우, 페이지 추가하지 않음
                        for d in page_docs:
                            parent_file_name = d['parent_file']['file_name']
                            if parent_file_name not in unique_docs:
                                unique_docs[parent_file_name] = d

                        # 최대 3개의 관련 문서 선택
                        top_docs = get_top_relevant_docs(
                            list(unique_docs.values()),
                            question,
                            max_count=3
                        )
                        doc_details = top_docs

                    # 응답을 채팅 기록에 추가
                    st.session_state.prd_messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "doc_details": doc_details
                    })

            except Exception as e:
                error_msg = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)

                message_placeholder.markdown("죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요.")

                # 간단한 오류 메시지 로깅 및 표시
                st.session_state.prd_messages.append({
                    "role": "assistant",
                    "content": "죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
                    "doc_details": []
                })

            # 채팅 후 UI 업데이트를 위해 페이지 새로고침
            st.rerun()

    # 사이드바에 데이터 및 재설정 버튼 추가
    if prd_data:
        st.sidebar.markdown("### 데이터 통계")
        st.sidebar.info(f"생산이슈리포트 데이터: {len(prd_data)}건")

        # 라인별 통계
        line_counts = {}
        for entry in prd_data:
            lines = entry.get("lines", ["대상 라인 정보 없음"])
            for line in lines:
                line_counts[line] = line_counts.get(line, 0) + 1

        # 막대 차트로 표시
        if line_counts:
            df_line = pd.DataFrame({
                "라인": list(line_counts.keys()),
                "건수": list(line_counts.values())
            })
            df_line = df_line.sort_values("건수", ascending=False)

            st.sidebar.markdown("#### 라인별 데이터 수")
            st.sidebar.bar_chart(df_line.set_index("라인"))

    # 대화 기록 초기화 버튼
    if st.sidebar.button("대화 기록 초기화", key="prd_reset_chat"):
        st.session_state.prd_messages = []
        st.rerun()

    # 벡터 DB 초기화 버튼
    if st.sidebar.button("벡터 DB 재생성", key="prd_reset_vector_db"):
        if "prd_vector_store" in st.session_state:
            del st.session_state.prd_vector_store
        if "prd_conversation_chain" in st.session_state:
            del st.session_state.prd_conversation_chain

        with st.spinner("벡터 데이터베이스 재생성 중..."):
            st.session_state.prd_vector_store = load_or_create_vector_db(
                st.session_state.prd_data,
                vector_dir="PRD/vector_db"
            )
            st.success("벡터 DB가 재생성되었습니다.")
            st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="생산이슈리포트 챗봇", layout="wide")
    show_prd_chat()