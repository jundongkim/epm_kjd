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
from components.cmms.cmms_images import get_all_image_paths
from components.cmms.cmms_data_loader import find_image_file

# 필요한 유틸리티 함수들
def get_all_image_paths(cmms_data):
    """모든 이미지 경로와 관련 정보를 가져옵니다."""
    all_images = []
    for entry in cmms_data:
        if "작업사진" in entry and entry["작업사진"]:
            image_descriptions = entry.get("이미지설명", {})
            for img_filename in entry["작업사진"]:
                image_path = find_image_file(img_filename)
                if image_path and os.path.exists(image_path):
                    all_images.append({
                        "path": image_path,
                        "filename": img_filename,
                        "description": image_descriptions.get(img_filename, ""),
                        "line": entry.get("라인", ""),
                        "equipment_no": entry.get("설비번호", "").split('\n')[0] if entry.get("설비번호") else "",
                        "work_date": entry.get("작업 일자", "").split('\n')[0] if entry.get("작업 일자") else "",
                        "work_details": entry.get("작업 상세내용", ""),
                        "equipment_name": entry.get("설비명", ""),
                        "work_type": entry.get("작업 종류", ""),
                        "relevance_score": 0  # 기본 관련성 점수 초기화
                    })
    return all_images

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

        # 기타 메타데이터 매칭 (라인, 설비번호 등)
        meta_text = f"{img.get('line', '')} {img.get('equipment_no', '')}".lower()
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

# ChainWrapper 클래스 (CMMS/utils/chain_wrapper.py에서 가져옴)
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

            # 검색 결과가 없는 경우 안내 표시

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
                line = metadata.get('line', '')
                equipment_no = metadata.get('equipment_no', '')
                work_date = metadata.get('work_date', '')
                work_type = metadata.get('work_type', '')
                equipment_name = metadata.get('equipment_name', '')

                # 문서 포맷팅 (더 자세한 정보 포함)
                formatted_doc = f"""[문서{i}] {line}/{equipment_no}/{equipment_name}
작업일자: {work_date}
작업유형: {work_type}
작업설명: {doc.page_content.strip()}"""

                # 이미지 정보가 있는 경우 추가
                if "image_info" in metadata and metadata["image_info"]:
                    formatted_doc += f"\n관련 이미지: {len(metadata['image_info'])}개"

                formatted_docs.append(formatted_doc)

                # 로깅을 통해 각 문서의 세부 정보 기록
                logging.info(f"문서 {i} 세부 정보 - 라인: {line}, 설비: {equipment_no}, 설비명: {equipment_name}, 작업일자: {work_date}")

            except Exception as e:
                # 메시지에 특정 에러 패턴이 포함된 경우 (벡터 차원 불일치)
                error_str = str(e)
                if "assert d == self.d" in error_str or "dimension mismatch" in error_str:
                    st.error("벡터 차원 불일치 오류가 발생했습니다. '벡터 DB 재설정' 버튼을 클릭하여 문제를 해결해 보세요.")
                    try:
                        # 현재 엠베딩 모델 차원과 FAISS 인덱스 차원 정보 표시
                        if hasattr(self.retriever.vectorstore, 'index'):
                            st.info(f"FAISS 인덱스 차원: {self.retriever.vectorstore.index.d}")
                    except:
                        pass

                # 문서 포맷팅 중 오류가 발생해도 계속 진행
                st.warning(f"문서 {i} 포맷팅 중 오류: {str(e)}")
                formatted_docs.append(f"[문서{i}] 오류로 인해 형식화 실패")

                # 세부 오류 정보 로깅
                import traceback
                logging.error(f"문서 {i} 포맷팅 중 오류: {str(e)}")
                logging.error(traceback.format_exc())

        # 모든 문서를 하나의 문자열로 결합
        return "\n\n---\n\n".join(formatted_docs)

# 체인 프롬프트 - 한국어
system_template_kr = """당신은 CMMS(Computerized Maintenance Management System) 일일업무일지 데이터에 대한 질문에 답변하는 AI 어시스턴트입니다.
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
- **표**: 데이터 비교가 필요할 때 마크다운 표를 사용하세요. 예:
  ```
  | 항목 | 내용 | 비고 |
  | --- | --- | --- |
  | 예시1 | 설명1 | 참고1 |
  ```
- **인용**: 참고 내용이나 중요 정보는 `>` 기호로 인용구 형식을 사용하세요.
- **코드**: 기술적 명령어나 코드는 ``` 로 감싸 코드 블록으로 표시하세요.
- **섹션 구분**: 주요 섹션 사이에는 `---` 구분선을 사용하세요.
- **정보 상자**: 중요 정보는 `> **참고:** 내용` 형식으로 강조하세요.

### 응답 형식 ###
답변을 다음 세 단계로 구조화하여 제공하세요:
Start of Format ---
## 분석 결과
### 1. 기본 정보 분석
- 설비 정보(라인, 번호, 명칭)
- 작업 이력 및 패턴
- 관련 이미지 정보

---

### 2. 상세 분석
- 작업 종류별 특징
- 장애 패턴 분석
- 조치 이력 검토

---

### 3. 개선 방안
- 예방 정비 제안
- 운영 최적화 방안
- 위험 관리 대책
--- End of Format


### 중요 ###
- 반드시 컨텍스트에서 찾은 정보는 출처 문서 번호를 포함하여 답변의 근거를 제시하세요. 예: [문서1에 따르면...]
- 만약 특정 단계에 대한 정보가 부족하다면, 일반적인 지식을 바탕으로 합리적인 제안을 제공하되 이것이 추론임을 명시하세요.
- 다음 지정된 언어로 답변하세요.
"""
# 체인 프롬프트 - 헝가리어
system_template_hu = """Ön egy AI asszisztens, aki a CMMS (Számítógépes Karbantartásirányítási Rendszer) napi munkanapló adatával kapcsolatos kérdésekre válaszol.
Használja az alábbi kontextusinformációkat a felhasználói kérdések pontos megválaszolásához.

### Kontextusinformációk ###
{context}

### Válaszadási elvek ###
Ha szakszavak jelennek meg, mindenképp egészítse ki azokat könnyen érthető magyarázattal.

Nyújtson objektív elemzést az adatok alapján.

Javasoljon konkrét és végrehajtható megoldásokat.

### Válasz nyelvezete ###
- **Cím**: A válasz tetején mindig szerepeljen `## Cím` formátumú témacím.
- **Alcímek**: Minden szakaszhoz használja a `### Alcím` formátumot az egyértelmű elkülönítés érdekében.
- **Kiemelés**: A fontos tartalmakat `**kiemelés**` vagy `__kiemelés__` jelöléssel emelje ki.
- **Listák**: Használjon `-` vagy `*` felsorolást, illetve `1.` sorszámozást.
- **Táblázatok**: Amikor összehasonlításra van szükség, használjon Markdown táblázatot, pl.:
```
| Elem | Leírás | Megjegyzés |
| ---- | ------ | ---------- |
| Példa1 | Magyarázat1 | Hivatkozás1 |
```
- **Idézetek**: Fontos megjegyzésekhez vagy forrásmegjelöléshez használja a `>` karaktert.
- **Kód**: Technikai parancsokat vagy kódrészleteket ``` karakterek közé helyezzen.
- **Szakaszelválasztás**: A főbb részeket `---` jellel válassza el.
- **Információs doboz**: Fontos információkat `> **Megjegyzés:**` formátumban emeljen ki.

### Válasz formátuma ###
A válasz három fő szakaszra legyen bontva az alábbi struktúrában:
<AnswerFormat>
## Elemzési eredmények
### 1. Alapinformációk elemzése
- Berendezés adatai (vonal, szám, megnevezés)
- Munkavégzés előzményei és mintázatok
- Kapcsolódó képi információk
---
### 2. Részletes elemzés
- Munkatípusok jellemzői
- Hiba mintázatok elemzése
- Beavatkozási előzmények vizsgálata
---
### 3. Fejlesztési javaslatok
- Megelőző karbantartásra vonatkozó ajánlások
- Üzemeltetés optimalizálási lehetőségei
- Kockázatkezelési intézkedések
</AnswerFormat>


### Fontos ###
- A kontextusból vett információkhoz minden esetben adja meg a hivatkozási dokumentum számát. Példa: [A dokumentum1 szerint...]
- Amennyiben valamelyik lépéshez nem áll rendelkezésre elegendő adat, nyújtson általános ismereteken alapuló ésszerű javaslatot, és egyértelműen jelölje, hogy ez következtetés.
- A válasz nyelve a megadott célnyelv legyen.
"""

# 대화형 체인 생성 함수
def get_conversation_chain(vector_store, selected_model="gemma3:4b", temperature=0.2, memory_length=5):
    """대화형 체인을 생성합니다.

    Args:
        vector_store: FAISS 벡터 저장소 인스턴스
        selected_model (str): 사용할 Ollama 모델 이름 (기본값: "gemma3:4b")
        temperature (float): 생성 모델의 temperature 값 (기본값: 0.2)
        memory_length (int): 대화 기억 길이 (기본값: 5)

    Returns:
        ChainWrapper: 대화형 체인 래퍼 인스턴스
    """
    global CHAT_PROMPT

    # 프롬프트 템플릿 초기화
    system_template = system_template_hu if st.session_state["cmms_language"] == "헝가리어" else system_template_kr
    language_prompt = "Válasz magyarul." if st.session_state["cmms_language"] == "헝가리어" else "한국어로 답변하세요."

    # 프롬프트 템플릿 갱신
    CHAT_PROMPT = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        SystemMessagePromptTemplate.from_template(language_prompt),
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

    # 세션 상태에서 점수 임계값 가져오기 (헝가리어인 경우 검색 결과를 존재하게 만들기 위해 threshold 사용 안함)
    score_threshold = None if st.session_state["cmms_language"] == "헝가리어" else st.session_state.get('score_threshold', 0.3)

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

def show_cmms_chat():
    """CMMS 채팅 인터페이스 컴포넌트"""
    st.title("💬 일일업무일지 채팅 인터페이스")

    # 더 많은 옵션 제공
    with st.sidebar.expander("고급 설정"):
        # 검색 점수 임계값 조정
        score_threshold = st.slider(
            "검색 점수 임계값",
            min_value=0.1,
            max_value=0.7,
            value=0.3,
            step=0.05,
            help="낮을수록 더 많은 관련 문서를 검색합니다."
        )

        # 점수 임계값만 세션 상태에 저장
        st.session_state['score_threshold'] = score_threshold

    # 일일업무일지 데이터와 벡터 저장소 확인
    if "cmms_data" not in st.session_state:
        st.error("일일업무일지 데이터가 로드되지 않았습니다.")
        return

    if "vector_store" not in st.session_state:
        st.error("벡터 저장소가 초기화되지 않았습니다.")
        return

    # 데이터 및 벡터 저장소 가져오기
    cmms_data = st.session_state.cmms_data
    vector_store = st.session_state.vector_store

    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 대화 기록 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 채팅 이력 이후에 이미지 표시
    last_msg_with_images = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant" and "image_details" in msg and msg["image_details"]:
            last_msg_with_images = msg
            break

    # 이미지가 있을 때만 섹션 표시
    if last_msg_with_images and last_msg_with_images["image_details"]:
        st.markdown("---")
        st.markdown("### 📷 관련 작업 이미지 (최대 3장)")

        # 이미지 관련성 평가 및 상위 3개 선택
        top_images = get_top_relevant_images(
            last_msg_with_images["image_details"],
            last_msg_with_images["content"],
            max_count=3
        )

        # 이미지를 직접 표시 (최대 3장)
        for i, img_detail in enumerate(top_images):
            if os.path.exists(img_detail["path"]):
                with st.expander(f"{img_detail.get('equipment_no', '')} - {img_detail.get('work_date', '')} (관련성 점수: {img_detail.get('relevance_score', 0)})", expanded=True):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.image(img_detail["path"], use_container_width=True, caption=img_detail["filename"])

                    with col2:
                        st.markdown("### 이미지 정보")
                        st.markdown(f"""
                        **라인**: {img_detail.get('line', '')}
                        **설비번호**: {img_detail.get('equipment_no', '')}
                        **설비명**: {img_detail.get('equipment_name', '')}
                        **작업일자**: {img_detail.get('work_date', '')}
                        **작업종류**: {img_detail.get('work_type', '')}
                        """)

                        if img_detail.get("description", ""):
                            st.markdown("### 이미지 설명")
                            st.markdown(img_detail.get("description", ""))

                    st.markdown("### 작업 상세내용")
                    st.markdown(img_detail.get("work_details", ""))

                    st.markdown("---")

    language_col, input_col = st.columns([1.2, 8.8])
    # 출력 언어 선택
    with language_col:
        language = st.selectbox("언어 선택", ["한국어", "헝가리어"], index=0, format_func=lambda x: f"🌐 {x}", label_visibility="collapsed")
        st.session_state["cmms_language"] = language

        # 모델 설정
        selected_model = st.session_state.get("selected_model", "gemma3:4b-it-qat")  # 고정 모델 사용
        memory_length = st.session_state.get("memory_length", 5)
        temperature = st.session_state.get("temperature", 0.2)

        try:
            # 대화 체인 초기화 - 언어 선택 시마다 새로 생성하여 설정 변경사항 반영
            st.session_state.conversation_chain = get_conversation_chain(
                vector_store,
                selected_model=selected_model,
                temperature=temperature,
                memory_length=memory_length
            )
        except Exception as e:
            st.error(f"대화 체인 초기화 중 오류 발생: {str(e)}")
            return

    # 사용자 입력 처리
    with input_col:
        input_placeholder = "Kérdés a napi üzleti naplóval kapcsolatban..." if language == "헝가리어" else "일일업무일지에 대해 궁금한 점을 입력해주세요..."
        if question := st.chat_input(input_placeholder):
            # 사용자 메시지를 채팅 기록에 추가
            st.session_state.messages.append({"role": "user", "content": question})

            # 사용자 메시지 표시
            with st.chat_message("user"):
                st.markdown(question)

            # 응답 생성
            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                try:
                    with st.spinner("응답 생성 중..."):
                        # 스트리밍 응답 생성
                        response, full_response = st.session_state.conversation_chain.stream_response(
                            {"question": question},
                            message_placeholder
                        )

                        # 관련 이미지 찾기
                        image_details = []

                        if response and "source_documents" in response:
                            for doc in response["source_documents"]:
                                if hasattr(doc, 'metadata') and 'image_info' in doc.metadata:
                                    for img in doc.metadata.get('image_info', []):
                                        if os.path.exists(img['path']):
                                            image_details.append(img)

                        # 관련성 평가 및 중복 제거
                        if image_details:
                            unique_images = {}
                            for img in image_details:
                                if img['path'] not in unique_images:
                                    unique_images[img['path']] = img

                            # 최대 3개의 관련 이미지 선택
                            top_images = get_top_relevant_images(
                                list(unique_images.values()),
                                question,
                                max_count=3
                            )
                            image_details = top_images

                        # 응답을 채팅 기록에 추가
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response,
                            "image_details": image_details
                        })

                except Exception as e:
                    error_msg = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)

                    message_placeholder.markdown("죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요.")

                    # 간단한 오류 메시지 로깅 및 표시
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
                        "image_details": []
                    })

                # 채팅 후 UI 업데이트를 위해 페이지 새로고침
                st.rerun()