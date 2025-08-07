"""
DX-AI Advisor
산업/시장/경쟁사 트렌드 자동 분석 시스템
"""
import os
import io
import re
import time
import json
import base64
import zipfile
import tempfile
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu

from src.processors.document_parser import DocumentParser
from src.processors.information_extractor import InformationExtractor
from src.ontology.ontology_generator import OntologyGenerator
from src.embeddings.embedding_manager import EmbeddingManager
from src.agents.advisor_agent import AdvisorAgent
from src.visualization.ontology_viz import visualize_ontology_3d
from src.utils.ui_utils import apply_custom_css
from src.utils.config import (
    DATA_DIR, TTL_DIR, VECTOR_DB_DIR, OUTPUT_DIR, UPLOADS_DIR, REPORTS_DIR,
    FONT_PATH, DEFAULT_REPORT_SECTIONS, DEFAULT_LLM_MODEL, 
    AVAILABLE_LLM_MODELS, EMBEDDING_MODEL
)

# 페이지 설정
st.set_page_config(
    page_title="DX-AI Advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 폰트 설정
def load_custom_font():
    """커스텀 폰트를 로드하는 함수"""
    apply_custom_css()


def init_session_state():
    """세션 상태 초기화"""
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'parsed_results' not in st.session_state:
        st.session_state.parsed_results = []
    if 'extraction_results' not in st.session_state:
        st.session_state.extraction_results = []
    if 'ontology_path' not in st.session_state:
        st.session_state.ontology_path = None
    if 'vector_db_path' not in st.session_state:
        st.session_state.vector_db_path = None
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = {
            'upload': False,
            'parse': False,
            'extract': False,
            'ontology': False,
            'embedding': False,
            'report': False
        }
    if 'advisor_agent' not in st.session_state:
        st.session_state.advisor_agent = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'report_topic' not in st.session_state:
        st.session_state.report_topic = ""
    if 'report_sections' not in st.session_state:
        st.session_state.report_sections = DEFAULT_REPORT_SECTIONS
    if 'generated_report' not in st.session_state:
        st.session_state.generated_report = ""
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = DEFAULT_LLM_MODEL
    if 'vector_db_indices_cache' not in st.session_state:
        st.session_state.vector_db_indices_cache = {}
    if 'vector_db_cache_timestamp' not in st.session_state:
        st.session_state.vector_db_cache_timestamp = 0


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        # 로고 이미지가 있으면 표시, 없으면 텍스트로 대체
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=250)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <h1 style="color: #1f77b4; font-size: 2em; margin: 0;">📊</h1>
                <h2 style="color: #1f77b4; margin: 5px 0;">DX-AI</h2>
                <p style="color: #666; margin: 0;">Advisor</p>
            </div>
            """, unsafe_allow_html=True)
        st.title("DX-AI Advisor")
        st.markdown("---")
        
        # 메인 메뉴를 먼저 표시
        selected = option_menu(
            menu_title="메인 메뉴",
            options=["대시보드", "파일 업로드", "문서 처리", "온톨로지 생성", "임베딩 생성", "AI 어드바이저", "보고서 생성"],
            icons=["house", "upload", "file-text", "diagram-3", "search", "robot", "file-earmark-text"],
            menu_icon="cast",
            default_index=0
        )
        
        st.markdown("---")
        
        # 언어 모델 설정 UI를 메인 메뉴 아래로 이동
        st.markdown("### 언어 모델 설정")
        model_display_name = st.selectbox(
            "사용할 언어 모델 선택",
            options=list(AVAILABLE_LLM_MODELS.keys()),
            index=list(AVAILABLE_LLM_MODELS.values()).index(st.session_state.selected_model),
            help="크기가 큰 모델일수록 성능이 좋지만 응답 속도가 느려집니다."
        )
        
        # 선택된 모델 적용
        selected_model = AVAILABLE_LLM_MODELS[model_display_name]
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
            st.session_state.advisor_agent = None  # 에이전트 초기화
            st.info(f"언어 모델이 {model_display_name}로 변경되었습니다.")
            
        # 임베딩 모델 정보 표시
        st.markdown("### 임베딩 모델")
        st.info(f"사용 중인 임베딩 모델: {EMBEDDING_MODEL}")
        
        st.markdown("---")
        st.caption("© 2025 DX-AI Advisor")
        
        return selected


def show_dashboard():
    """대시보드 화면 표시"""
    st.title("🌟 DX-AI Advisor 대시보드")
    
    # 상태 개요
    st.subheader("처리 상태")
    status_cols = st.columns(6)
    with status_cols[0]:
        icon = "✅" if st.session_state.processing_status['upload'] else "❌"
        st.info(f"{icon} 파일 업로드")
    with status_cols[1]:
        icon = "✅" if st.session_state.processing_status['parse'] else "❌"
        st.info(f"{icon} 문서 파싱")
    with status_cols[2]:
        icon = "✅" if st.session_state.processing_status['extract'] else "❌"
        st.info(f"{icon} 정보 추출")
    with status_cols[3]:
        icon = "✅" if st.session_state.processing_status['ontology'] else "❌"
        st.info(f"{icon} 온톨로지")
    with status_cols[4]:
        icon = "✅" if st.session_state.processing_status['embedding'] else "❌"
        st.info(f"{icon} 임베딩")
    with status_cols[5]:
        icon = "✅" if st.session_state.processing_status['report'] else "❌"
        st.info(f"{icon} 보고서")
    
    # 모델 정보 표시
    st.markdown("---")
    st.subheader("모델 정보")
    
    model_cols = st.columns(2)
    with model_cols[0]:
        selected_model = st.session_state.selected_model
        model_display_name = [k for k, v in AVAILABLE_LLM_MODELS.items() if v == selected_model][0]
        st.info(f"현재 언어 모델: {model_display_name}")
    
    with model_cols[1]:
        st.info(f"임베딩 모델: {EMBEDDING_MODEL}")
        st.text("임베딩 모델은 문서 벡터화에 사용됩니다.")
    
    # 메인 통계
    st.markdown("---")
    st.subheader("문서 현황")
    stats_cols = st.columns(3)
    
    with stats_cols[0]:
        num_uploaded = len(st.session_state.uploaded_files)
        st.metric("업로드된 파일", num_uploaded)
    
    with stats_cols[1]:
        num_parsed = len(st.session_state.parsed_results)
        st.metric("파싱된 문서", num_parsed)
    
    with stats_cols[2]:
        num_extracted = len(st.session_state.extraction_results)
        st.metric("정보 추출 완료", num_extracted)
    
    # 온톨로지 및 임베딩 통계
    st.markdown("---")
    st.subheader("데이터 통계")
    
    data_cols = st.columns(2)
    
    with data_cols[0]:
        st.markdown("### 온톨로지 통계")
        if st.session_state.ontology_path:
            ontology_generator = OntologyGenerator()
            stats = ontology_generator.get_statistics(ttl_file_path=st.session_state.ontology_path)
            
            st.metric("총 엔티티 수", stats.get('entity_count', 0))
            st.metric("총 관계 수", stats.get('relation_count', 0))
            
            entity_types = stats.get('entity_types', {})
            if entity_types:
                df_entity = pd.DataFrame(list(entity_types.items()), columns=['유형', '수'])
                st.bar_chart(df_entity.set_index('유형'))
        else:
            st.warning("온톨로지가 아직 생성되지 않았습니다.")
    
    with data_cols[1]:
        st.markdown("### 임베딩 통계")
        if st.session_state.vector_db_path:
            embedding_manager = EmbeddingManager()
            stats = embedding_manager.generate_embeddings_report()
            
            st.metric("총 문서 수", stats.get('document_count', 0))
            
            doc_types = stats.get('document_types', {})
            if doc_types:
                df_types = pd.DataFrame(list(doc_types.items()), columns=['유형', '수'])
                st.bar_chart(df_types.set_index('유형'))
                
                # 상세 통계 표시
                st.markdown("**상세 유형별 통계:**")
                for doc_type, count in doc_types.items():
                    st.markdown(f"- {doc_type}: {count}개")
            else:
                st.warning("문서 유형 통계 정보가 없습니다.")
        else:
            st.warning("임베딩이 아직 생성되지 않았습니다.")


def show_file_upload():
    """파일 업로드 화면 표시"""
    st.title("📤 파일 업로드")
    
    st.markdown("""
    ### 문서 업로드
    분석할 문서 파일을 업로드해주세요. 지원되는 파일 형식: PDF, DOCX, PPTX, TXT, MD
    """)
    
    uploaded_files = st.file_uploader(
        "파일 선택", 
        accept_multiple_files=True,
        type=["pdf", "docx", "pptx", "txt", "md"]
    )
    
    save_btn = st.button("파일 저장", type="primary")
    
    if save_btn and uploaded_files:
        with st.spinner("파일 저장 중..."):
            # 데이터 디렉토리 생성
            os.makedirs(DATA_DIR, exist_ok=True)
            
            saved_files = []
            # 업로드된 파일 저장
            for uploaded_file in uploaded_files:
                file_path = os.path.join(DATA_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_files.append({
                    "filename": uploaded_file.name,
                    "path": file_path,
                    "size": uploaded_file.size,
                    "type": uploaded_file.type,
                    "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            st.session_state.uploaded_files.extend(saved_files)
            st.session_state.processing_status['upload'] = True
            
            st.success(f"{len(saved_files)}개 파일 저장 완료!")
    
    # 업로드된 파일 목록 표시
    if st.session_state.uploaded_files:
        st.markdown("### 업로드된 파일 목록")
        
        file_df = pd.DataFrame(st.session_state.uploaded_files)
        st.dataframe(file_df[["filename", "size", "type", "upload_time"]])
        
        if st.button("초기화"):
            st.session_state.uploaded_files = []
            st.session_state.processing_status['upload'] = False
            st.rerun()


def show_document_processing():
    """문서 처리 화면 표시"""
    st.title("📝 문서 처리")
    
    # 파일이 업로드되지 않은 경우
    if not st.session_state.uploaded_files:
        st.warning("먼저 문서 파일을 업로드해주세요.")
        return
    
    st.markdown("""
    ### 문서 파싱
    업로드된 문서를 파싱하여 내용을 추출합니다.
    """)
    
    parse_btn = st.button("문서 파싱", type="primary")
    
    if parse_btn:
        with st.spinner("문서 파싱 중..."):
            # 문서 파서 생성
            parser = DocumentParser()
            
            # 모든 업로드 파일에 대해 파싱 실행
            file_paths = [file_info["path"] for file_info in st.session_state.uploaded_files]
            parsed_results = parser.parse_directory(DATA_DIR)
            
            # 파싱 결과가 유효한지 확인
            if not parsed_results:
                st.error("문서 파싱 중 오류가 발생했습니다. 파일 형식을 확인해주세요.")
                return
                
            # 파싱 결과 저장
            st.session_state.parsed_results = parsed_results
            st.session_state.processing_status['parse'] = True
            
            st.success(f"{len(parsed_results)}개 문서 파싱 완료!")
    
    # 파싱 결과 표시
    if st.session_state.parsed_results:
        st.markdown("### 파싱 결과")
        
        # 결과를 테이블로 변환
        parsed_summary = []
        for doc in st.session_state.parsed_results:
            # 메타데이터는 문서 객체에 직접 있음
            filename = doc.get("filename", "")
            file_extension = doc.get("file_extension", "")
            content_chunks = len(doc.get("content", []))
            file_size = doc.get("file_size_kb", 0)
            modified_date = doc.get("modified_date", "")
            
            # 결과에 유효한 값이 있는지 확인
            if not filename:
                # 에러 처리: 잘못된 형식의 결과 수정
                if "file_path" in doc:
                    filename = os.path.basename(doc["file_path"])
                    file_extension = os.path.splitext(filename)[1]
            
            parsed_summary.append({
                "filename": filename,
                "file_extension": file_extension,
                "content_chunks": content_chunks,
                "file_size": file_size,
                "modified_date": modified_date
            })
        
        if parsed_summary:
            parse_df = pd.DataFrame(parsed_summary)
            st.dataframe(parse_df)
        else:
            st.warning("파싱 결과를 표시할 수 없습니다. 데이터 형식이 올바르지 않습니다.")
        
        # 정보 추출 섹션
        st.markdown("---")
        st.markdown("""
        ### 정보 추출
        파싱된 문서에서 메타데이터, 온톨로지 관계, 구조화된 데이터를 추출합니다.
        """)
        
        extract_btn = st.button("정보 추출", type="primary")
        
        if extract_btn:
            st.session_state.extraction_results = []  # 기존 결과 초기화
            
            with st.spinner("정보 추출 중... (몇 분 정도 소요될 수 있습니다)"):
                try:
                    # 정보 추출기 생성
                    extractor = InformationExtractor(model_name=st.session_state.selected_model)
                    
                    # 진행 상황 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 문서 수 확인
                    total_docs = len(st.session_state.parsed_results)
                    status_text.text(f"0/{total_docs} 문서 처리 중...")
                    
                    # 파싱된 문서에서 정보 추출 (직접 처리하여 진행 상황 표시)
                    extraction_results = []
                    
                    for i, doc in enumerate(st.session_state.parsed_results):
                        doc_name = doc.get("filename", f"문서 {i+1}")
                        status_text.text(f"{i+1}/{total_docs} 문서 처리 중... ({doc_name})")
                        
                        try:
                            # 문서의 기본 정보 구성
                            file_info = {
                                "filename": doc.get("filename", "unknown"),
                                "file_path": doc.get("file_path", ""),
                                "file_extension": doc.get("file_extension", ""),
                                "file_size_kb": doc.get("file_size_kb", 0),
                                "modified_date": doc.get("modified_date", "")
                            }
                            
                            # 실제 정보 추출 처리
                            extraction_result = extractor.process_document(doc)
                            
                            # 파일 정보 추가
                            extraction_result["file_info"] = file_info
                            
                            # 결과에 추가
                            extraction_results.append(extraction_result)
                            
                            # 진행률 업데이트
                            progress = (i + 1) / total_docs
                            progress_bar.progress(progress)
                            
                        except Exception as e:
                            st.error(f"'{doc_name}' 문서 처리 중 오류 발생: {str(e)}")
                            import traceback
                            print(traceback.format_exc())
                    
                    # 추출 결과 저장
                    st.session_state.extraction_results = extraction_results
                    st.session_state.processing_status['extract'] = True if extraction_results else False
                    
                    # 결과 저장 (JSON)
                    if extraction_results:
                        output_path = os.path.join(OUTPUT_DIR, "extraction_results.json")
                        os.makedirs(OUTPUT_DIR, exist_ok=True)
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(extraction_results, f, ensure_ascii=False, indent=2)
                        
                        st.success(f"{len(extraction_results)}개 문서 정보 추출 완료!")
                    else:
                        st.warning("정보 추출 결과가 없습니다. 추출에 실패했습니다.")
                
                except Exception as e:
                    st.error(f"정보 추출 중 오류가 발생했습니다: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        
        # 추출 결과 표시
        if st.session_state.extraction_results:
            st.markdown("### 추출 결과")
            
            # 결과를 테이블로 변환
            extraction_summary = []
            for result in st.session_state.extraction_results:
                filename = result.get("file_info", {}).get("filename", "")
                
                metadata = result.get("metadata", {})
                ontology = result.get("ontology", {})
                structured_data = result.get("structured_data", {})
                
                extraction_summary.append({
                    "filename": filename,
                    "title": metadata.get("title", ""),
                    "keywords": len(metadata.get("keywords", [])),
                    "topics": len(metadata.get("topics", [])),
                    "entities": len(ontology.get("entities", [])),
                    "relations": len(ontology.get("relations", [])),
                    "tables": len(structured_data.get("tables", [])),
                    "lists": len(structured_data.get("lists", []))
                })
            
            extract_df = pd.DataFrame(extraction_summary)
            st.dataframe(extract_df)


def show_ontology_generation():
    """온톨로지 생성 화면 표시"""
    st.title("🔄 온톨로지 생성")
    
    # 기존 온톨로지 파일 목록 가져오기
    ttl_files = []
    for f in os.listdir(TTL_DIR):
        if f.endswith('.ttl'):
            file_path = os.path.join(TTL_DIR, f)
            file_size = os.path.getsize(file_path) / 1024  # KB 단위
            mod_time = os.path.getmtime(file_path)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
            ttl_files.append({
                "filename": f,
                "path": file_path,
                "size_kb": file_size,
                "modified": mod_time_str,
                "mod_timestamp": mod_time
            })
    
    # 최신 수정 시간 순으로 정렬
    ttl_files.sort(key=lambda x: x["mod_timestamp"], reverse=True)
    
    # 탭 생성: 새로 생성 / 기존 파일 선택
    tab1, tab2 = st.tabs(["새 온톨로지 생성", "기존 온톨로지 선택"])
    
    with tab1:
        # 추출 결과가 없는 경우
        if not st.session_state.extraction_results:
            st.warning("먼저 문서 정보 추출을 진행해주세요.")
        else:
            st.markdown("""
            ### 새 온톨로지 파일 생성
            추출된 정보를 바탕으로 TTL 형식의 온톨로지 파일을 생성합니다.
            """)
            
            # 키워드 추출을 통한 이름 자동 추천
            suggested_name = "ontology"
            keywords_list = []
            
            # 추출 결과에서 주요 키워드 수집
            for result in st.session_state.extraction_results:
                metadata = result.get("metadata", {})
                keywords = metadata.get("keywords", [])
                if keywords and len(keywords) > 0:
                    keywords_list.extend(keywords[:3])  # 각 문서에서 최대 3개 키워드 사용
            
            # 중복 제거 및 상위 키워드 선택
            if keywords_list:
                # 중복 제거하고 가장 많이 등장한 키워드 찾기
                keyword_counter = {}
                for kw in keywords_list:
                    if isinstance(kw, str):
                        keyword_counter[kw] = keyword_counter.get(kw, 0) + 1
                
                # 가장 많이 등장한 키워드 2개 선택
                top_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:2]
                if top_keywords:
                    # 키워드를 조합하여 이름 생성
                    keywords_text = "_".join([k.lower().replace(' ', '_') for k, _ in top_keywords])
                    current_date = datetime.now().strftime("%y%m%d")
                    suggested_name = f"{keywords_text}_{current_date}"
            
            # 온톨로지 이름 입력
            ontology_name = st.text_input(
                "온톨로지 이름",
                suggested_name,
                help="온톨로지와 벡터 DB에 사용할 이름을 입력하세요. 영문, 숫자, 밑줄(_)만 사용 가능합니다."
            )
            
            # 이름 유효성 검사
            name_valid = bool(re.match(r'^[a-zA-Z0-9_]+$', ontology_name))
            if not name_valid:
                st.warning("이름은 영문, 숫자, 밑줄(_)만 사용 가능합니다.")
            
            generate_btn = st.button("온톨로지 생성", type="primary", disabled=not name_valid)
            
            if generate_btn:
                with st.spinner("온톨로지 생성 중..."):
                    # 온톨로지 생성기 생성
                    ontology_generator = OntologyGenerator()
                    
                    # 추출 결과를 처리하여 온톨로지 생성
                    ontology_generator.process_extraction_results(st.session_state.extraction_results)
                    
                    # TTL 파일 저장 - 새 네이밍 규칙 적용
                    filename = f"{ontology_name}.ttl"
                    ontology_path = ontology_generator.save_ttl(filename)
                    
                    # 세션에 온톨로지 이름과 경로 저장
                    st.session_state.ontology_path = ontology_path
                    st.session_state.ontology_name = ontology_name
                    st.session_state.processing_status['ontology'] = True
                    
                    # 온톨로지 통계 가져오기
                    stats = ontology_generator.get_statistics()
                    
                    st.success(f"온톨로지 '{ontology_name}' 생성 완료!")
                    st.info(f"총 엔티티 수: {stats['entity_count']}개, 총 관계 수: {stats['relation_count']}개")
    
    with tab2:
        if not ttl_files:
            st.warning("사용 가능한 온톨로지 파일이 없습니다.")
        else:
            st.markdown("""
            ### 기존 온톨로지 파일 선택
            이전에 생성된 온톨로지 파일 중 하나를 선택하여 사용합니다.
            """)
            
            # 파일 선택을 위한 데이터프레임 생성
            df_ttl = pd.DataFrame([{
                "파일명": f["filename"],
                "크기(KB)": f["size_kb"],
                "수정일": f["modified"]
            } for f in ttl_files])
            
            st.dataframe(df_ttl)
            
            # 파일 선택 드롭다운
            selected_file = st.selectbox(
                "사용할 온톨로지 파일 선택", 
                options=[f["filename"] for f in ttl_files],
                format_func=lambda x: f"{x} ({next((f['modified'] for f in ttl_files if f['filename'] == x), '')})"
            )
            
            if selected_file:
                selected_path = os.path.join(TTL_DIR, selected_file)
                load_btn = st.button("이 온톨로지 사용", type="primary")
                
                if load_btn:
                    # 온톨로지 이름 추출 (확장자 제외)
                    selected_name = os.path.splitext(selected_file)[0]
                    
                    # 온톨로지 로드
                    ontology_generator = OntologyGenerator()
                    stats = ontology_generator.get_statistics(ttl_file_path=selected_path)
                    
                    # 세션에 온톨로지 이름과 경로 저장
                    st.session_state.ontology_path = selected_path
                    st.session_state.ontology_name = selected_name
                    st.session_state.processing_status['ontology'] = True
                    
                    st.success(f"온톨로지 '{selected_name}' 로드 완료!")
                    st.info(f"총 엔티티 수: {stats['entity_count']}개, 총 관계 수: {stats['relation_count']}개")
    
    # 온톨로지 시각화 또는 통계 표시
    if st.session_state.ontology_path:
        st.markdown("### 온톨로지 통계")
        
        # 현재 선택된 파일 표시
        current_file = os.path.basename(st.session_state.ontology_path)
        current_name = os.path.splitext(current_file)[0]
        st.success(f"현재 사용 중인 온톨로지: {current_name}")
        
        # 온톨로지 로드 및 통계 가져오기
        ontology_generator = OntologyGenerator()
        stats = ontology_generator.get_statistics(ttl_file_path=st.session_state.ontology_path)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("엔티티 유형별 통계")
            entity_types = stats.get('entity_types', {})
            
            if entity_types:
                df_entity = pd.DataFrame(list(entity_types.items()), columns=['유형', '수'])
                st.bar_chart(df_entity.set_index('유형'))
            else:
                st.warning("엔티티 통계 정보가 없습니다.")
        
        with col2:
            st.subheader("관계 유형별 통계")
            relation_types = stats.get('relation_types', {})
            
            if relation_types:
                df_relation = pd.DataFrame(list(relation_types.items()), columns=['관계', '수'])
                st.bar_chart(df_relation.set_index('관계'))
            else:
                st.warning("관계 통계 정보가 없습니다.")
        
        # 3D 온톨로지 시각화 추가
        st.markdown("### 온톨로지 3D 시각화")
        
        # 설명 추가
        st.info("온톨로지 그래프를 3차원으로 시각화합니다. 마우스로 회전, 확대/축소가 가능합니다.")
        
        # 그래프 생성 및 시각화
        if st.button("3D 시각화 생성"):
            with st.spinner("온톨로지 3D 그래프 생성 중..."):
                # 시각화 모듈 사용하여 그래프 생성
                fig, viz_stats = visualize_ontology_3d(st.session_state.ontology_path)
                
                # 그래프 표시
                st.plotly_chart(fig, use_container_width=True)
                
                # 통계 정보 표시
                st.markdown("#### 3D 그래프 통계")
                st.info(f"노드 수: {viz_stats['node_count']}개, 엣지 수: {viz_stats['edge_count']}개")
                
                # 유형별 노드 수 표시
                node_types = viz_stats.get('node_types', {})
                if node_types:
                    type_df = pd.DataFrame(list(node_types.items()), columns=['노드 유형', '수'])
                    st.dataframe(type_df)
        
        # 온톨로지 검색 테스트 추가
        st.markdown("### 온톨로지 검색 테스트")
        
        # TTL 파일에서 직접 온톨로지 데이터 로드
        with st.spinner("TTL 파일에서 온톨로지 데이터 로딩 중..."):
            ttl_data = load_ontology_from_ttl(st.session_state.ontology_path)
        
        if ttl_data.get('error'):
            st.error(f"TTL 파일 로딩 오류: {ttl_data['error']}")
        else:
            entities = ttl_data.get('entities', [])
            relations = ttl_data.get('relations', [])
            
            if not entities and not relations:
                st.warning("TTL 파일에서 온톨로지 데이터를 찾을 수 없습니다.")
            else:
                # TTL 기반 통계 계산
                ttl_stats = calculate_ttl_ontology_stats(entities, relations)
                
                # 온톨로지 통계 표시
                st.markdown("#### TTL 파일 기반 온톨로지 통계")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("총 엔티티 수", ttl_stats.get('entity_count', 0))
                with col2:
                    st.metric("총 관계 수", ttl_stats.get('relation_count', 0))
                with col3:
                    st.metric("관계 유형 수", ttl_stats.get('unique_relation_types', 0))
                with col4:
                    avg_connections = ttl_stats.get('average_connections_per_entity', 0)
                    st.metric("평균 연결 수", f"{avg_connections:.1f}")
                
                # 관계 유형별 통계
                relation_types = ttl_stats.get('relation_types', {})
                if relation_types:
                    st.markdown("#### 관계 유형별 분포")
                    # 상위 15개 관계 유형만 표시
                    top_relations = dict(sorted(relation_types.items(), key=lambda x: x[1], reverse=True)[:15])
                    df_relation_types = pd.DataFrame(list(top_relations.items()), columns=['관계 유형', '수'])
                    st.bar_chart(df_relation_types.set_index('관계 유형'))
                    
                    # 상세 관계 유형 표시
                    with st.expander(f"전체 관계 유형 ({len(relation_types)}개)"):
                        for rel_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
                            st.markdown(f"- **{rel_type}**: {count}개")
                
                # 연결성이 높은 엔티티 표시
                top_connected = ttl_stats.get('top_connected_entities', [])
                if top_connected:
                    st.markdown("#### 연결성이 높은 엔티티 (상위 10개)")
                    df_top_connected = pd.DataFrame(top_connected, columns=['엔티티', '연결 수'])
                    st.dataframe(df_top_connected, use_container_width=True)
                
                # 고립된 엔티티 표시
                isolated_entities = ttl_stats.get('isolated_entities', [])
                if isolated_entities:
                    st.markdown("#### 고립된 엔티티 (관계가 없는 엔티티)")
                    st.info(f"총 {len(isolated_entities)}개의 고립된 엔티티가 있습니다.")
                    with st.expander("고립된 엔티티 목록"):
                        # 10개씩 나누어 표시
                        for i in range(0, len(isolated_entities), 10):
                            chunk = isolated_entities[i:i+10]
                            st.write(", ".join(chunk))
                
                # TTL 기반 검색 테스트 섹션
                st.markdown("---")
                st.markdown("#### TTL 기반 온톨로지 검색")
                
                # 검색 유형 선택
                search_type_map = {
                    "엔티티만": "entity",
                    "관계만": "relation", 
                    "엔티티+관계": "both"
                }
                
                search_type_display = st.selectbox(
                    "검색 유형 선택",
                    options=list(search_type_map.keys()),
                    help="검색할 온톨로지 데이터 유형을 선택하세요."
                )
                
                search_type = search_type_map[search_type_display]
                
                # 검색어 입력
                query = st.text_input(
                    "검색어 입력", 
                    placeholder="예: 기업, 기술, 경쟁, Apple, 전기차",
                    help="검색하고 싶은 키워드나 엔티티명을 입력하세요. 부분 매칭을 지원합니다."
                )
                
                # 검색 옵션
                col1, col2 = st.columns(2)
                with col1:
                    max_results = st.slider("최대 결과 수", min_value=5, max_value=50, value=10)
                with col2:
                    show_scores = st.checkbox("매칭 점수 표시", value=True)
                
                # 검색 실행
                search_btn = st.button("TTL 검색", type="primary")
                
                if search_btn and query:
                    with st.spinner("TTL 데이터에서 검색 중..."):
                        try:
                            # TTL 데이터에서 검색
                            search_results = search_ontology_in_ttl(entities, relations, query, search_type)
                            
                            entity_results = search_results.get('entities', [])
                            relation_results = search_results.get('relations', [])
                            
                            total_results = len(entity_results) + len(relation_results)
                            
                            if total_results > 0:
                                st.markdown(f"#### 검색 결과 (총 {total_results}개)")
                                
                                # 엔티티 결과 표시
                                if entity_results:
                                    st.markdown(f"##### 🏷️ 엔티티 ({len(entity_results)}개)")
                                    
                                    displayed_entities = 0
                                    for entity in entity_results:
                                        if displayed_entities >= max_results:
                                            break
                                        
                                        entity_name = entity['name']
                                        match_score = entity['match_score']
                                        
                                        # 제목 구성
                                        title = f"📋 {entity_name}"
                                        if show_scores:
                                            title += f" (매칭: {match_score:.1f})"
                                        
                                        with st.expander(title):
                                            st.markdown(f"**엔티티명**: {entity_name}")
                                            st.markdown(f"**매칭 점수**: {match_score:.2f}")
                                            
                                            # 이 엔티티와 관련된 관계들 찾기
                                            related_relations = []
                                            for rel in relations:
                                                if rel['source'] == entity_name or rel['target'] == entity_name:
                                                    related_relations.append(rel)
                                            
                                            if related_relations:
                                                st.markdown(f"**관련 관계** ({len(related_relations)}개):")
                                                for rel in related_relations[:5]:  # 최대 5개만 표시
                                                    st.markdown(f"- {rel['source']} → **{rel['relation']}** → {rel['target']}")
                                                if len(related_relations) > 5:
                                                    st.markdown(f"... 외 {len(related_relations)-5}개 더")
                                            else:
                                                st.markdown("**관련 관계**: 없음 (고립된 엔티티)")
                                        
                                        displayed_entities += 1
                                
                                # 관계 결과 표시
                                if relation_results:
                                    st.markdown(f"##### 🔗 관계 ({len(relation_results)}개)")
                                    
                                    displayed_relations = 0
                                    for relation in relation_results:
                                        if displayed_relations >= max_results:
                                            break
                                        
                                        source = relation['source']
                                        rel_type = relation['relation']
                                        target = relation['target']
                                        match_score = relation['match_score']
                                        
                                        # 제목 구성
                                        title = f"🔗 {source} → {rel_type} → {target}"
                                        if show_scores:
                                            title += f" (매칭: {match_score:.1f})"
                                        
                                        with st.expander(title):
                                            st.markdown(f"**출발 엔티티**: {source}")
                                            st.markdown(f"**관계 유형**: {rel_type}")
                                            st.markdown(f"**목적 엔티티**: {target}")
                                            st.markdown(f"**매칭 점수**: {match_score:.2f}")
                                        
                                        displayed_relations += 1
                            else:
                                st.warning("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
                                
                                # 검색 힌트 제공
                                st.info("💡 힌트: 부분 매칭을 지원하므로 완전한 단어가 아니어도 검색됩니다.")
                                
                                # 샘플 검색어 제안
                                if top_connected:
                                    sample_entities = [entity for entity, _ in top_connected[:5]]
                                    st.info(f"추천 엔티티: {', '.join(sample_entities)}")
                                
                                if relation_types:
                                    sample_relations = list(relation_types.keys())[:5]
                                    st.info(f"추천 관계 유형: {', '.join(sample_relations)}")
                        
                        except Exception as e:
                            st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
                            import traceback
                            print(traceback.format_exc())
                
                # 샘플 검색어 제안 (항상 표시)
                st.markdown("---")
                st.markdown("#### 💡 추천 검색어")
                
                # 연결성이 높은 엔티티 기반 추천
                if top_connected:
                    sample_entities = [entity for entity, _ in top_connected[:5]]
                    st.info(f"**인기 엔티티**: {', '.join(sample_entities)}")
                
                # 주요 관계 유형 기반 추천
                if relation_types:
                    top_relation_types = sorted(relation_types.items(), key=lambda x: x[1], reverse=True)[:5]
                    sample_relations = [rel_type for rel_type, _ in top_relation_types]
                    st.info(f"**주요 관계 유형**: {', '.join(sample_relations)}")


def get_vector_db_indices_fast():
    """벡터 DB 인덱스 정보를 빠르게 수집하는 함수 (캐시 사용)"""
    current_time = time.time()
    cache_valid_duration = 300  # 5분간 캐시 유효
    
    # 캐시가 유효한지 확인
    if (current_time - st.session_state.vector_db_cache_timestamp < cache_valid_duration and 
        st.session_state.vector_db_indices_cache):
        return st.session_state.vector_db_indices_cache.get('indices', [])
    
    # 캐시가 없거나 만료된 경우 새로 수집
    vector_db_indices = []
    if os.path.exists(VECTOR_DB_DIR):
        for item in os.listdir(VECTOR_DB_DIR):
            item_path = os.path.join(VECTOR_DB_DIR, item)
            if os.path.isdir(item_path):
                # 유효한 인덱스인지 확인 (index.faiss 파일이 있는지)
                index_faiss_path = os.path.join(item_path, 'index.faiss')
                if os.path.exists(index_faiss_path):
                    # 인덱스 디렉토리 크기 계산
                    dir_size = 0
                    for dirpath, dirnames, filenames in os.walk(item_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                dir_size += os.path.getsize(filepath)
                            except:
                                pass  # 파일 접근 오류 무시
                    dir_size_mb = dir_size / (1024 * 1024)  # MB 단위
                    
                    # 최종 수정 시간 (index.faiss 파일 기준)
                    mod_time = os.path.getmtime(index_faiss_path)
                    mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
                    
                    # 문서 수는 캐시에서 확인하거나 "알 수 없음"으로 표시
                    doc_count = "로드 필요"
                    cached_info = st.session_state.vector_db_indices_cache.get(item, {})
                    if cached_info and 'document_count' in cached_info:
                        doc_count = cached_info['document_count']
                    
                    vector_db_indices.append({
                        "index_name": item,
                        "path": item_path,
                        "size_mb": dir_size_mb,
                        "modified": mod_time_str,
                        "mod_timestamp": mod_time,
                        "document_count": doc_count
                    })
    
    # 최신 수정 시간 순으로 정렬
    vector_db_indices.sort(key=lambda x: x["mod_timestamp"], reverse=True)
    
    # 캐시 업데이트
    st.session_state.vector_db_indices_cache = {
        'indices': vector_db_indices,
        **{idx['index_name']: idx for idx in vector_db_indices}
    }
    st.session_state.vector_db_cache_timestamp = current_time
    
    return vector_db_indices


def show_embedding_generation():
    """임베딩 생성 화면 표시"""
    st.title("🔍 임베딩 생성")
    
    # 벡터 DB 인덱스 정보를 빠르게 수집
    vector_db_indices = get_vector_db_indices_fast()
    
    # 탭 생성: 새로 생성 / 기존 인덱스 사용
    tab1, tab2 = st.tabs(["새 임베딩 생성", "기존 임베딩 사용"])
    
    with tab1:
        # 파싱 결과가 없는 경우
        if not st.session_state.parsed_results:
            st.warning("먼저 문서 파싱 및 정보 추출을 진행해주세요.")
        else:
            st.markdown("""
            ### 새 임베딩 및 벡터 DB 생성
            파싱된 문서와 추출된 정보를 바탕으로 임베딩을 생성하고 벡터 데이터베이스를 구축합니다.
            """)
            
            # 임베딩 설정
            st.markdown("#### 임베딩 설정")
            
            # 온톨로지 이름이 있으면 그 이름을 기본값으로 사용
            default_index_name = "document_index"
            if hasattr(st.session_state, 'ontology_name') and st.session_state.ontology_name:
                default_index_name = st.session_state.ontology_name
            
            index_name = st.text_input("인덱스 이름", default_index_name)
            
            # 이름 유효성 검사
            name_valid = bool(re.match(r'^[a-zA-Z0-9_]+$', index_name))
            if not name_valid:
                st.warning("이름은 영문, 숫자, 밑줄(_)만 사용 가능합니다.")
            
            # 온톨로지 데이터 포함 여부
            include_ontology = st.checkbox("온톨로지 데이터 포함", value=True, 
                                          help="온톨로지에서 엔티티와 관계 정보를 임베딩에 포함합니다.")
            
            generate_btn = st.button("임베딩 생성", type="primary", disabled=not name_valid)
            
            if generate_btn:
                with st.spinner("임베딩 생성 및 벡터 DB 구축 중... (수 분이 소요될 수 있습니다)"):
                    # 임베딩 매니저 생성
                    embedding_manager = EmbeddingManager()
                    
                    # 문서에서 임베딩 생성
                    documents = []
                    
                    # 디버그 정보 표시
                    debug_info = st.empty()
                    
                    # 정보 추출 결과가 있으면 사용, 없으면 파싱 결과 사용
                    if st.session_state.extraction_results:
                        debug_info.info(f"정보 추출 결과 사용: {len(st.session_state.extraction_results)}개 파일")
                        documents = embedding_manager.create_documents_from_extraction_results(st.session_state.extraction_results)
                        debug_info.info(f"추출 결과로부터 생성된 문서: {len(documents)}개")
                    else:
                        debug_info.info(f"파싱 결과 사용: {len(st.session_state.parsed_results)}개 파일")
                        documents = embedding_manager.create_documents_from_parsed_results(st.session_state.parsed_results)
                        debug_info.info(f"파싱 결과로부터 생성된 문서: {len(documents)}개")
                    
                    # 온톨로지 문서 수 카운트
                    ontology_doc_count = 0
                    
                    # 추출 결과가 있는 경우 온톨로지 데이터도 추가 (옵션에 따라)
                    if include_ontology and st.session_state.extraction_results:
                        debug_info.info("온톨로지 데이터 처리 중...")
                        ontology_details = []
                        
                        for idx, result in enumerate(st.session_state.extraction_results):
                            ontology_data = result.get("ontology", {})
                            entities = ontology_data.get('entities', [])
                            relations = ontology_data.get('relations', [])
                            
                            file_info = result.get("file_info", {})
                            filename = file_info.get("filename", f"파일{idx+1}")
                            
                            debug_info.info(f"{filename}: 엔티티 {len(entities)}개, 관계 {len(relations)}개 → 문서 생성 중...")
                            ontology_details.append(f"{filename}: E{len(entities)}, R{len(relations)}")
                            
                            ontology_docs = embedding_manager.create_documents_from_ontology(ontology_data)
                            documents.extend(ontology_docs)
                            ontology_doc_count += len(ontology_docs)
                            
                            debug_info.info(f"{filename}: {len(ontology_docs)}개 온톨로지 문서 생성됨")
                        
                        debug_info.info(f"✅ 온톨로지 문서 추가 완료: {ontology_doc_count}개")
                    
                    debug_info.info(f"총 문서 수: {len(documents)}개 (문서: {len(documents)-ontology_doc_count}, 온톨로지: {ontology_doc_count})")
                    
                    # 문서 유형별 카운트 표시
                    if documents:
                        doc_type_counts = {}
                        source_counts = {}
                        for doc in documents:
                            doc_type = doc.metadata.get('chunk_type', 'unknown')
                            source = doc.metadata.get('source', 'unknown')
                            doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1
                            source_counts[source] = source_counts.get(source, 0) + 1
                        
                        debug_info.info(f"문서 유형별: {doc_type_counts}")
                        debug_info.info(f"소스별: {source_counts}")
                    
                    # 벡터 DB 생성
                    vector_db_path = os.path.join(VECTOR_DB_DIR, index_name)
                    vectorstore = embedding_manager.create_vector_db(documents, index_name)
                    
                    st.session_state.vector_db_path = vector_db_path
                    st.session_state.vector_db_name = index_name
                    st.session_state.processing_status['embedding'] = True
                    
                    # 통계 가져오기
                    stats = embedding_manager.generate_embeddings_report(index_name)
                    
                    # 캐시 무효화 (새로운 인덱스가 생성되었으므로)
                    st.session_state.vector_db_cache_timestamp = 0
                    
                    st.success(f"임베딩 생성 및 벡터 DB '{index_name}' 구축 완료!")
                    st.info(f"총 문서 수: {stats['document_count']}개")
    
    with tab2:
        if not vector_db_indices:
            st.warning("사용 가능한 벡터 DB 인덱스가 없습니다.")
        else:
            st.markdown("""
            ### 기존 벡터 DB 인덱스 사용
            이전에 생성된 벡터 데이터베이스 중 하나를 선택하여 사용합니다.
            """)
            
            # 인덱스 선택을 위한 데이터프레임 생성
            df_indices = pd.DataFrame([{
                "인덱스명": idx["index_name"],
                "크기(MB)": f"{idx['size_mb']:.1f}",
                "문서 수": idx["document_count"] if isinstance(idx["document_count"], int) else "로드 필요",
                "수정일": idx["modified"]
            } for idx in vector_db_indices])
            
            st.dataframe(df_indices)
            
            # 인덱스 선택 드롭다운
            selected_index = st.selectbox(
                "사용할 벡터 DB 인덱스 선택", 
                options=[idx["index_name"] for idx in vector_db_indices],
                format_func=lambda x: f"{x} ({next((idx['modified'] for idx in vector_db_indices if idx['index_name'] == x), '')})"
            )
            
            if selected_index:
                selected_path = os.path.join(VECTOR_DB_DIR, selected_index)
                
                # 선택된 인덱스 정보 표시
                selected_idx_info = next((idx for idx in vector_db_indices if idx['index_name'] == selected_index), None)
                if selected_idx_info:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"크기: {selected_idx_info['size_mb']:.1f} MB")
                    with col2:
                        st.info(f"수정일: {selected_idx_info['modified']}")
                    with col3:
                        doc_count_display = selected_idx_info['document_count']
                        if isinstance(doc_count_display, int):
                            st.info(f"문서 수: {doc_count_display}개")
                        else:
                            st.info("문서 수: 로드 후 확인")
                
                load_btn = st.button("이 벡터 DB 사용", type="primary")
                
                if load_btn:
                    with st.spinner(f"벡터 DB '{selected_index}' 로드 중..."):
                        # 벡터 DB 로드 및 상세 정보 가져오기
                        embedding_manager = EmbeddingManager()
                        stats = embedding_manager.generate_embeddings_report(selected_index)
                        
                        # 캐시에 문서 수 정보 업데이트
                        if selected_index in st.session_state.vector_db_indices_cache:
                            st.session_state.vector_db_indices_cache[selected_index]['document_count'] = stats['document_count']
                        
                        st.session_state.vector_db_path = selected_path
                        st.session_state.vector_db_name = selected_index
                        st.session_state.processing_status['embedding'] = True
                        
                        st.success(f"벡터 DB '{selected_index}' 로드 완료!")
                        st.info(f"총 문서 수: {stats['document_count']}개")
    
    # 임베딩 통계 표시
    if st.session_state.vector_db_path:
        st.markdown("### 임베딩 통계")
        
        # 현재 사용 중인 인덱스 표시
        current_index = os.path.basename(st.session_state.vector_db_path)
        st.success(f"현재 사용 중인 벡터 DB: {current_index}")
        
        # 임베딩 통계 가져오기
        embedding_manager = EmbeddingManager()
        stats = embedding_manager.generate_embeddings_report(current_index)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("문서 유형별 통계")
            doc_types = stats.get('document_types', {})
            
            if doc_types:
                df_types = pd.DataFrame(list(doc_types.items()), columns=['유형', '수'])
                st.bar_chart(df_types.set_index('유형'))
                
                # 상세 통계 표시
                st.markdown("**상세 유형별 통계:**")
                for doc_type, count in doc_types.items():
                    st.markdown(f"- {doc_type}: {count}개")
            else:
                st.warning("문서 유형 통계 정보가 없습니다.")
        
        with col2:
            st.subheader("파일별 문서 수")
            file_stats = stats.get('file_statistics', {})
            
            if file_stats:
                df_files = pd.DataFrame(list(file_stats.items()), columns=['파일명', '문서 수'])
                st.bar_chart(df_files.set_index('파일명'))
                
                # 상세 파일별 통계 표시
                st.markdown("**상세 파일별 통계:**")
                for filename, count in file_stats.items():
                    st.markdown(f"- {filename}: {count}개")
            else:
                st.warning("파일별 통계 정보가 없습니다.")
        
        # 소스별 통계 추가
        metadata_stats = stats.get('metadata_statistics', {})
        source_stats = metadata_stats.get('source', {})
        
        if source_stats:
            st.subheader("데이터 소스별 통계")
            st.markdown("**소스별 문서 수:**")
            for source, count in source_stats.items():
                st.markdown(f"- {source}: {count}개")
            
            # 소스별 차트
            df_sources = pd.DataFrame(list(source_stats.items()), columns=['소스', '수'])
            st.bar_chart(df_sources.set_index('소스'))
        
        # 임베딩 검색 테스트
        st.markdown("### 임베딩 검색 테스트")
        
        query = st.text_input("검색어 입력", "...")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            k = st.slider("결과 수", min_value=1, max_value=10, value=3)
        with col2:
            show_full_metadata = st.checkbox("전체 메타데이터 표시", value=False)
        with col3:
            exclude_ontology = st.checkbox("온톨로지 제외", value=False)
        
        search_btn = st.button("검색")
        
        if search_btn:
            with st.spinner("검색 중..."):
                # 검색 실행
                if exclude_ontology:
                    # 온톨로지 제외: 더 많은 결과를 가져온 후 필터링
                    temp_k = k * 3  # 더 많은 결과를 가져와서 필터링
                    all_docs_with_scores = embedding_manager.similarity_search(query, temp_k, current_index)
                    
                    # 온톨로지가 아닌 문서들만 필터링
                    docs_with_scores = []
                    for doc, score in all_docs_with_scores:
                        if doc.metadata.get('source') != 'ontology':
                            docs_with_scores.append((doc, score))
                            if len(docs_with_scores) >= k:
                                break
                else:
                    # 일반 검색
                    docs_with_scores = embedding_manager.similarity_search(query, k, current_index)
                
                if docs_with_scores:
                    st.markdown("#### 검색 결과")
                    
                    for i, (doc, score) in enumerate(docs_with_scores, 1):
                        with st.expander(f"결과 {i} (유사도: {score:.4f})"):
                            st.markdown(f"**내용:** {doc.page_content}")
                            st.markdown("**메타데이터:**")
                            
                            # 메타데이터를 카테고리별로 정리하여 표시
                            metadata = doc.metadata
                            
                            # 기본 정보
                            if metadata.get('source') == 'ontology':
                                st.markdown("📊 **온톨로지 데이터**")
                                if metadata.get('entity_type') == 'entity_group':
                                    st.markdown(f"- 유형: 엔티티 그룹")
                                    entity_count = metadata.get('entity_count', 0)
                                    st.markdown(f"- 엔티티 수: {entity_count}개")
                                    entity_names = metadata.get('entity_names', [])
                                    if entity_names:
                                        entity_preview = ', '.join(entity_names[:3])
                                        if len(entity_names) > 3:
                                            entity_preview += f" 외 {len(entity_names)-3}개"
                                        st.markdown(f"- 엔티티 예시: {entity_preview}")
                                elif metadata.get('entity_type') == 'relation_group':
                                    st.markdown(f"- 유형: 관계 그룹")
                                    relation_count = metadata.get('relation_count', 0)
                                    st.markdown(f"- 관계 수: {relation_count}개")
                                else:
                                    # 기존 개별 온톨로지 항목 (이전 버전 호환성)
                                    if metadata.get('entity_name'):
                                        st.markdown(f"- 엔티티명: {metadata.get('entity_name')}")
                                    if metadata.get('entity_type'):
                                        st.markdown(f"- 유형: {metadata.get('entity_type')}")
                                    if metadata.get('source_entity'):
                                        st.markdown(f"- 출발 엔티티: {metadata.get('source_entity')}")
                                    if metadata.get('relation_type'):
                                        st.markdown(f"- 관계 유형: {metadata.get('relation_type')}")
                                    if metadata.get('target_entity'):
                                        st.markdown(f"- 목적 엔티티: {metadata.get('target_entity')}")
                            else:
                                st.markdown("📄 **문서 데이터**")
                                if metadata.get('filename'):
                                    st.markdown(f"- 파일명: {metadata.get('filename')}")
                                if metadata.get('title'):
                                    st.markdown(f"- 제목: {metadata.get('title')}")
                                if metadata.get('chunk_type'):
                                    st.markdown(f"- 내용 유형: {metadata.get('chunk_type')}")
                                if metadata.get('file_extension'):
                                    st.markdown(f"- 파일 형식: {metadata.get('file_extension')}")
                                if metadata.get('file_date'):
                                    st.markdown(f"- 수정일: {metadata.get('file_date')}")
                                if metadata.get('author'):
                                    st.markdown(f"- 작성자: {metadata.get('author')}")
                                if metadata.get('creation_date'):
                                    st.markdown(f"- 생성일: {metadata.get('creation_date')}")
                                
                                # 키워드 및 주제
                                keywords = metadata.get('keywords', [])
                                if keywords and len(keywords) > 0:
                                    if isinstance(keywords, list):
                                        keywords_str = ", ".join(keywords[:5])  # 최대 5개만 표시
                                    else:
                                        keywords_str = str(keywords)
                                    st.markdown(f"- 키워드: {keywords_str}")
                                
                                topics = metadata.get('topics', [])
                                if topics and len(topics) > 0:
                                    if isinstance(topics, list):
                                        topics_str = ", ".join(topics[:3])  # 최대 3개만 표시
                                    else:
                                        topics_str = str(topics)
                                    st.markdown(f"- 주제: {topics_str}")
                                
                                # 요약
                                summary = metadata.get('summary', '')
                                if summary and summary.strip():
                                    st.markdown(f"- 요약: {summary[:200]}{'...' if len(summary) > 200 else ''}")
                                
                                # 청크 정보
                                if metadata.get('chunk_id') is not None:
                                    st.markdown(f"- 청크 ID: {metadata.get('chunk_id')}")
                                if metadata.get('sub_chunk_id') is not None:
                                    st.markdown(f"- 서브 청크 ID: {metadata.get('sub_chunk_id')}")
                                
                                # 특별한 콘텐츠 유형별 정보
                                chunk_type = metadata.get('chunk_type')
                                if chunk_type == 'table' and metadata.get('table_title'):
                                    st.markdown(f"- 테이블 제목: {metadata.get('table_title')}")
                                elif chunk_type == 'list' and metadata.get('list_title'):
                                    st.markdown(f"- 목록 제목: {metadata.get('list_title')}")
                                elif chunk_type == 'statistic':
                                    if metadata.get('stat_name'):
                                        st.markdown(f"- 통계명: {metadata.get('stat_name')}")
                                    if metadata.get('stat_value'):
                                        st.markdown(f"- 통계값: {metadata.get('stat_value')}")
                                elif chunk_type == 'timeline':
                                    if metadata.get('event_date'):
                                        st.markdown(f"- 이벤트 날짜: {metadata.get('event_date')}")
                                    if metadata.get('event_description'):
                                        st.markdown(f"- 이벤트 설명: {metadata.get('event_description')}")
                            
                            # 출처 정보
                            st.markdown(f"- 데이터 출처: {metadata.get('source', 'unknown')}")
                            
                            # 전체 메타데이터 (체크박스가 선택된 경우에만 표시)
                            if show_full_metadata:
                                st.markdown("---")
                                st.markdown("**전체 메타데이터:**")
                                for key, value in metadata.items():
                                    st.markdown(f"- **{key}**: {value}")
                else:
                    st.warning("검색 결과가 없습니다.")


def show_advisor():
    """AI 어드바이저 화면 표시"""
    print("[INFO] AI 어드바이저 화면 초기화 시작")
    st.title("🤖 AI 어드바이저")
    
    # 임베딩이 생성되지 않은 경우
    if not st.session_state.vector_db_path:
        print("[WARNING] 임베딩이 생성되지 않음")
        st.warning("먼저 임베딩 생성을 진행해주세요.")
        return
    
    st.markdown("""
    ### AI 어드바이저와 대화
    데이터를 기반으로 질문에 답변하고, 다각적 관점에서 심층적인 분석 정보를 제공하는 AI 어드바이저와 대화해보세요.
    단순한 정보 제공을 넘어 원인-결과 분석, 미래 전망, 이해관계자 관점의 영향 분석 등 심층적인 통찰력을 얻을 수 있습니다.
    """)
    
    # 현재 사용 중인 벡터 DB와 온톨로지 정보 표시
    current_index = os.path.basename(st.session_state.vector_db_path)
    print(f"[INFO] 현재 사용 중인 벡터 DB: {current_index}")
    st.success(f"사용 중인 벡터 DB: {current_index}")
    
    if st.session_state.ontology_path:
        current_ontology = os.path.basename(st.session_state.ontology_path)
        print(f"[INFO] 현재 사용 중인 온톨로지: {current_ontology}")
        st.success(f"사용 중인 온톨로지: {current_ontology}")
    
    # 에이전트 초기화 또는 재초기화 조건 확인
    if (st.session_state.advisor_agent is None or 
        not hasattr(st.session_state.advisor_agent, 'vector_db_path') or
        st.session_state.advisor_agent.vector_db_path != st.session_state.vector_db_path or
        not hasattr(st.session_state.advisor_agent, 'ontology_path') or
        st.session_state.advisor_agent.ontology_path != st.session_state.ontology_path):
        
        print("[INFO] 어드바이저 에이전트 초기화 필요")
        with st.spinner("어드바이저 초기화 중..."):
            # AdvisorAgent 생성 - 벡터 DB 경로와 온톨로지 경로 전달
            print(f"[INFO] AdvisorAgent 생성 시작 - 모델: {st.session_state.selected_model}")
            agent = AdvisorAgent(
                model_name=st.session_state.selected_model,
                streaming=True,
                vector_db_path=st.session_state.vector_db_path,
                ontology_path=st.session_state.ontology_path
            )
            st.session_state.advisor_agent = agent
            print("[INFO] AdvisorAgent 생성 완료")
            
            # 초기 환영 메시지 추가
            if not st.session_state.chat_messages:
                print("[INFO] 초기 환영 메시지 추가")
                welcome_message = "안녕하세요! DX-AI 어드바이저입니다. 산업/시장/경쟁사 트렌드에 관한 질문이나 심층 분석이 필요한 주제를 입력해 주세요. 예: '미국 관세 동향과 향후 전망', '전기차 시장의 주요 기업별 전략 분석', '반도체 산업의 지정학적 리스크와 공급망 영향' 등"
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": welcome_message
                })
    
    # 채팅 인터페이스
    st.markdown("#### 대화")
    print("[INFO] 채팅 인터페이스 초기화")
    
    # 채팅 메시지 표시 - 마지막 메시지를 제외하고 표시
    for message in st.session_state.chat_messages[:-1] if len(st.session_state.chat_messages) > 0 else []:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 마지막 메시지가 있으면 표시
    if st.session_state.chat_messages:
        last_message = st.session_state.chat_messages[-1]
        with st.chat_message(last_message["role"]):
            st.markdown(last_message["content"])
    
    # 사용자 입력
    query = st.chat_input("질문이나 분석이 필요한 주제를 입력하세요")
    
    if query:
        print(f"[INFO] 새로운 사용자 질문 수신: {query}")
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(query)
        
        # 사용자 메시지 저장
        st.session_state.chat_messages.append({
            "role": "user",
            "content": query
        })
        print("[INFO] 사용자 메시지 저장 완료")
        
        # 어드바이저 응답 생성 (스트리밍 방식)
        with st.chat_message("assistant"):
            # 응답을 스트리밍으로 표시할 placeholder 생성
            message_placeholder = st.empty()
            
            # 디버그 정보 기록
            print(f"[INFO] 어드바이저 응답 생성 시작")
            
            # 스트리밍 방식으로 에이전트 호출
            response = st.session_state.advisor_agent.stream_response(query, message_placeholder)
            print("[INFO] 어드바이저 응답 생성 완료")
        
        # 어드바이저 메시지 저장
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response
        })
        print("[INFO] 어드바이저 메시지 저장 완료")
        print("==================================")
    
    # 대화 내용 초기화 버튼
    if st.button("대화 초기화"):
        print("[INFO] 대화 내용 초기화 요청")
        st.session_state.chat_messages = []
        st.rerun()


def show_report_generation():
    """보고서 생성 화면 표시"""
    st.title("📊 심층 분석 보고서 생성")
    
    # 임베딩이 생성되지 않은 경우
    if not st.session_state.vector_db_path:
        st.warning("먼저 임베딩 생성을 진행해주세요.")
        return
    
    st.markdown("""
    ### AI 심층 분석 보고서 생성
    문서 내용을 분석하여 다각적 관점에서 주제를 심층적으로 분석하는 보고서를 생성합니다.
    원인-결과 분석, 이해관계자 관점의 영향 평가, 미래 전망, 시사점 등을 포함한 통합적인 분석이 제공됩니다.
    """)
    
    # 현재 사용 중인 벡터 DB와 온톨로지 정보 표시
    current_index = os.path.basename(st.session_state.vector_db_path)
    st.success(f"사용 중인 벡터 DB: {current_index}")
    
    if st.session_state.ontology_path:
        current_ontology = os.path.basename(st.session_state.ontology_path)
        st.success(f"사용 중인 온톨로지: {current_ontology}")
    
    # 에이전트 초기화 또는 재초기화 조건 확인
    if (st.session_state.advisor_agent is None or 
        not hasattr(st.session_state.advisor_agent, 'vector_db_path') or
        st.session_state.advisor_agent.vector_db_path != st.session_state.vector_db_path or
        not hasattr(st.session_state.advisor_agent, 'ontology_path') or
        st.session_state.advisor_agent.ontology_path != st.session_state.ontology_path):
        
        with st.spinner("보고서 생성기 초기화 중..."):
            # AdvisorAgent 생성 - 벡터 DB 경로와 온톨로지 경로 전달
            agent = AdvisorAgent(
                model_name=st.session_state.selected_model,
                streaming=True,
                vector_db_path=st.session_state.vector_db_path,
                ontology_path=st.session_state.ontology_path
            )
            st.session_state.advisor_agent = agent
    
    # 보고서 설정
    st.markdown("#### 보고서 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input("보고서 주제", st.session_state.report_topic)
        st.session_state.report_topic = topic
    
    # 보고서 섹션 설정
    with col2:
        # 기존 섹션이 있으면 사용, 없으면 기본 섹션 사용
        current_sections = ", ".join(st.session_state.report_sections) if st.session_state.report_sections else ", ".join(DEFAULT_REPORT_SECTIONS)
        
        sections_str = st.text_area(
            "보고서 섹션 (쉼표로 구분)", 
            current_sections
        )
        st.session_state.report_sections = [s.strip() for s in sections_str.split(",")]
    
    # 선택된 섹션 미리보기 추가
    st.markdown("#### 보고서 섹션 미리보기")
    sections_preview = "\n".join([f"## {section}" for section in st.session_state.report_sections])
    st.code(sections_preview, language="markdown")
    
    st.info("위의 섹션 구조대로 보고서가 생성됩니다. 필요시 섹션 구성을 수정해주세요.")
    
    generate_btn = st.button("심층 분석 보고서 생성", type="primary")
    
    if generate_btn and topic:
        # 보고서 생성 컨테이너
        report_container = st.container()
        
        with report_container:
            st.markdown("### 생성 중인 심층 분석 보고서")
            
            # 보고서 스트리밍을 위한 placeholder
            report_placeholder = st.empty()
            
            try:
                with st.spinner("심층 분석 보고서 생성 중... (몇 분 정도 소요될 수 있습니다)"):
                    # 스트리밍 방식으로 보고서 생성
                    sections_json = json.dumps(st.session_state.report_sections)
                    
                    # 섹션 정보 로깅
                    print(f"보고서 주제: {topic}")
                    print(f"보고서 섹션: {sections_json}")
                    
                    # 명시적 예외 캐치를 위한 디버그 메시지
                    st.info("AI 모델에 요청을 보내는 중...")
                    
                    # 명시적으로 파라미터명 지정
                    report = st.session_state.advisor_agent.stream_report(
                        topic=topic,
                        sections_json=sections_json,
                        report_placeholder=report_placeholder
                    )
                    
                    # 보고서 저장
                    os.makedirs(REPORTS_DIR, exist_ok=True)
                    report_filename = f"report_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    report_path = os.path.join(REPORTS_DIR, report_filename)
                    
                    with open(report_path, "w", encoding="utf-8") as f:
                        f.write(report)
                    
                    st.session_state.generated_report = report
                    st.session_state.processing_status['report'] = True
                    
                    st.success(f"심층 분석 보고서 생성 완료! 파일 경로: {report_path}")
            
            except Exception as e:
                import traceback
                err_msg = f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
                print(err_msg)
                print(traceback.format_exc())  # 상세 오류 로그
                report_placeholder.error(err_msg)
                st.error("상세 오류 로그를 콘솔에서 확인하세요.")
    
    # 생성된 보고서가 있으면 다운로드 버튼 표시
    if st.session_state.generated_report:
        # 보고서 다운로드 버튼
        st.download_button(
            label="심층 분석 보고서 다운로드 (Markdown)",
            data=st.session_state.generated_report,
            file_name=f"report_{st.session_state.report_topic.replace(' ', '_')}.md",
            mime="text/markdown"
        )


def load_ontology_from_ttl(ttl_file_path):
    """
    TTL 파일에서 직접 온톨로지 데이터를 로드하는 함수
    
    Args:
        ttl_file_path: TTL 파일 경로
        
    Returns:
        Dict: 온톨로지 데이터 (entities, relations)
    """
    try:
        ontology_generator = OntologyGenerator()
        stats = ontology_generator.get_statistics(ttl_file_path=ttl_file_path)
        
        # TTL 파일에서 실제 엔티티와 관계 데이터 추출
        entities = []
        relations = []
        
        # RDFLib을 사용하여 TTL 파일 파싱
        from rdflib import Graph, URIRef, Literal
        
        g = Graph()
        g.parse(ttl_file_path, format="turtle")
        
        # 모든 주어(subject)를 엔티티로 추출
        subjects = set()
        for s, p, o in g:
            if isinstance(s, URIRef):
                # URI에서 엔티티명 추출 (마지막 부분)
                entity_name = str(s).split('/')[-1].replace('_', ' ')
                subjects.add(entity_name)
            if isinstance(o, URIRef):
                # 객체도 엔티티일 수 있음
                entity_name = str(o).split('/')[-1].replace('_', ' ')
                subjects.add(entity_name)
        
        entities = list(subjects)
        
        # 관계 추출
        for s, p, o in g:
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                source = str(s).split('/')[-1].replace('_', ' ')
                target = str(o).split('/')[-1].replace('_', ' ')
                relation = str(p).split('/')[-1].replace('_', ' ')
                
                relations.append({
                    'source': source,
                    'target': target,
                    'relation': relation
                })
        
        return {
            "entities": entities,
            "relations": relations,
            "stats": stats
        }
        
    except Exception as e:
        return {"error": f"TTL 파일 로드 중 오류: {str(e)}"}


def search_ontology_in_ttl(entities, relations, query, search_type="both"):
    """
    TTL 데이터에서 텍스트 기반 검색을 수행하는 함수
    
    Args:
        entities: 엔티티 리스트
        relations: 관계 리스트
        query: 검색어
        search_type: 검색 타입 ("entity", "relation", "both")
        
    Returns:
        Dict: 검색 결과
    """
    query = query.lower()
    results = {
        "entities": [],
        "relations": []
    }
    
    # 엔티티 검색
    if search_type in ["entity", "both"]:
        for entity in entities:
            if query in entity.lower():
                results["entities"].append({
                    "name": entity,
                    "type": "entity",
                    "match_score": 1.0 if query == entity.lower() else 0.5
                })
    
    # 관계 검색
    if search_type in ["relation", "both"]:
        for relation in relations:
            source = relation['source'].lower()
            target = relation['target'].lower()
            rel_type = relation['relation'].lower()
            
            # 관계의 모든 요소에서 검색
            if (query in source or query in target or query in rel_type):
                match_score = 1.0 if query in [source, target, rel_type] else 0.7
                results["relations"].append({
                    "source": relation['source'],
                    "target": relation['target'],
                    "relation": relation['relation'],
                    "type": "relation",
                    "match_score": match_score
                })
    
    # 점수순으로 정렬
    results["entities"].sort(key=lambda x: x["match_score"], reverse=True)
    results["relations"].sort(key=lambda x: x["match_score"], reverse=True)
    
    return results


def calculate_ttl_ontology_stats(entities, relations):
    """
    TTL 데이터에서 온톨로지 통계를 계산하는 함수
    
    Args:
        entities: 엔티티 리스트
        relations: 관계 리스트
        
    Returns:
        Dict: 통계 정보
    """
    # 관계 타입별 통계
    relation_types = {}
    for relation in relations:
        rel_type = relation['relation']
        relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
    
    # 엔티티별 관계 개수 계산
    entity_relation_count = {}
    for entity in entities:
        count = 0
        for relation in relations:
            if relation['source'] == entity or relation['target'] == entity:
                count += 1
        entity_relation_count[entity] = count
    
    # 가장 연결성이 높은 엔티티들 (상위 10개)
    top_connected_entities = sorted(
        entity_relation_count.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    
    # 고립된 엔티티들 (관계가 없는 엔티티)
    isolated_entities = [entity for entity, count in entity_relation_count.items() if count == 0]
    
    return {
        "entity_count": len(entities),
        "relation_count": len(relations),
        "relation_types": relation_types,
        "top_connected_entities": top_connected_entities,
        "isolated_entities": isolated_entities,
        "average_connections_per_entity": sum(entity_relation_count.values()) / len(entities) if entities else 0,
        "unique_relation_types": len(relation_types)
    }


def main():
    """메인 함수"""
    # 사용자 정의 폰트 로드
    load_custom_font()
    
    # 세션 상태 초기화
    init_session_state()
    
    # 사이드바 렌더링
    selected = render_sidebar()
    
    # 선택된 메뉴에 따라 화면 표시
    if selected == "대시보드":
        show_dashboard()
    elif selected == "파일 업로드":
        show_file_upload()
    elif selected == "문서 처리":
        show_document_processing()
    elif selected == "온톨로지 생성":
        show_ontology_generation()
    elif selected == "임베딩 생성":
        show_embedding_generation()
    elif selected == "AI 어드바이저":
        show_advisor()
    elif selected == "보고서 생성":
        show_report_generation()


if __name__ == "__main__":
    main() 