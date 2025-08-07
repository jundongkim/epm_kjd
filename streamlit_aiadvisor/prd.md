

# 📄 **PRD: DX-AI Advisor - 산업 동향 보고서 생성 시스템 (Streamlit 기반)**

---

## 🎯 **프로젝트 개요**
**DX-AI Advisor**는 사용자 업로드 파일을 자동으로 분석하여, **산업/시장/경쟁사 동향 보고서를 AI가 End-to-End로 생성**하는 시스템입니다.  
**Streamlit 기반**으로 사용자 인터페이스(UI)를 제공하며, **Ontology + Vector 기반 검색과 LLM Summarization** 기능을 통합합니다.

---

## 🚀 **시스템 주요 기능 (기능 흐름)**

### Font는 전역에서 fonts/Freesentation.ttf 적용

### conda 가상환경에서 실행 필요하므로 필요한 패키지 명시 필요

### 1️⃣ **파일 업로드 & 파싱**
- data 폴더의 산업 동향 관련 파일(PDF, Word, PPT, txt 등) 파싱
- 추가로 사용자가 **Streamlit UI**에서 산업 동향 관련 파일(PDF, Word, PPT, txt 등)을 업로드
- Streamlit backend에서 **File Parser 모듈 실행**
  - **파일명, 작성일, 작성자 등 메타데이터 추출**
  - 본문 내용 파싱
- 새로운 정보 있을 경우 해당 정보 파싱

---

### 2️⃣ **주요 클래스 추출 (Gemma3:12b 사용)**
- Parsing된 내용을 기반으로 **주요 정보 추출**
  - **파일명, 제목, 작성일, 주제어, 요약, 주요 내용**
- **Streamlit Progress bar**로 처리 상태 표시
- 추출된 정보는 **Ontology 가능 JSON 구조로 저장**
  ```json
  {
    "filename": "2025_Market_Trend.pdf",
    "title": "2025 Battery Material Market Trend",
    "keywords": ["Battery", "Cathode", "NCM811", "Market Trend"],
    "date": "2025-03-01",
    "summary": "2025년 배터리 소재 시장의 주요 트렌드와 경쟁사 동향을 정리",
    "content": [ "Paragraph 1", "Paragraph 2", ... ]
  }
  ```

---

### 3️⃣ **Ontology 파일 생성 (TTL 포맷)**
- 추출된 JSON을 기반으로 자동 **TTL (RDF/OWL)** 파일 생성
- 관계 정의 예시
  - `related`, `include`, `caused_by`, `resulted_in`, `competes_with`
- 생성된 온톨로지 현황을 시각적으로 표시 필요 (3D)

---

### 4️⃣ **Embedding & Vector DB 구축**
- **Embedding 모델: intfloat/multilingual-e5-large-instruct**
- **FAISS 기반 Vector Database 자동 구축**
- Ontology 정보도 **Neo4j 또는 rdflib 기반으로 저장**

---

### 5️⃣ **Advisor 검색 Agent 구성**
- Streamlit 내 **검색 입력창 제공**
- 사용자의 질문 처리 흐름:
  1. **FAISS Vector Similarity Search**
  2. **Ontology 기반 Semantic Search**
  3. **Gemma3 모델로 요약 및 결과 보완**
      - 모델 선택 옵션 제공:
        - gemma3:1b
        - gemma3:4b
        - gemma3:12b
        - gemma3:27b

---

### 6️⃣ **최종 보고서 생성**
- **Gemma3 모델로 요약 및 결과 보완**
      - 모델 선택 옵션 제공:
        - gemma3:1b
        - gemma3:4b
        - gemma3:12b
        - gemma3:27b
- 보고서 주요 기본 색션 에서 사용자 정의 가능 (추가/삭제)
- 검색된 결과를 자동으로 정리하여 **Streamlit 화면에 보고서 초안 출력**
- 보고서 생성 결과 를 outputparser로 처리 하고, 마크다운 형식으로 표시.
- 보고서 정리 부분에 표 형태로 상세하게 표시 필요
  
  예를 들어, 
  이차전지에 대한 미국 정부의 대 중국 관세 인상안와 같은 질문에
  제품별 기존 관세 / 신규 관세 / 적용 시점 / 특이점

  또는,
  미국의 중국 배터리 수입 현황 및 국내 Cell 업체 영향 분석 질문에
  회사별 생산 공장의 현황 / 미국의 수입 현황 / 특이점 (비고)

- 보고서 내용이 최대한 상세하고, 기술적이고 구체적이어야 함.
- **저장 기능** 제공 (Markdown, Word, PDF 다운로드)

---

## 🛠️ **사용 기술 스택**
| 구성요소                         | 기술                                                   |
|-----------------------------------|------------------------------------------------------|
| UI                               | **Streamlit**                                        |
| LLM                              | **Ollama Gemma3 (1b, 4b, 12b, 27b)**                |
| Embedding Model                  | intfloat/multilingual-e5-large-instruct              |
| Vector DB                        | FAISS                                               |
| Ontology DB                      | rdflib, Protégé, Neo4j                               |
| Orchestration                    | LangChain + LangGraph                                |
| 개발 언어                         | Python                                              |

---

## ✅ **시연 시나리오 예시**
1. 사용자가 **시장 보고서 PDF 3건 추가 업로드**
2. Parsing → JSON → TTL 자동 생성
3. **Streamlit UI에서 질문: "이차전지에 대한 미국 정부의 대 중국 관세 인상안에 대한 주제로 분석"**



4. Vector Search + Ontology 검색 → 요약 & 보고서 초안 자동 생성
5. **최종 보고서 다운로드**

