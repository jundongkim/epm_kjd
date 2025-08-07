import streamlit as st
import pandas as pd
import numpy as np
import os
from PIL import Image
from langchain.schema import Document
from components.process.process_images import get_all_image_paths

def search_similar_cases(query, vector_store, k=5):
    """유사한 케이스를 검색합니다."""
    try:
        results = vector_store.similarity_search_with_score(query, k=k)
        
        # 검색 결과 이미지 정보 강화
        if "process_data" in st.session_state:
            # 모든 이미지 정보 가져오기
            all_images = get_all_image_paths(st.session_state.process_data)
            
            # 검색 결과 문서의 이미지 정보 강화
            enhanced_results = []
            for doc, score in results:
                # 이미지 정보가 있는 경우 처리
                if 'image_info' in doc.metadata and doc.metadata['image_info']:
                    for img_info in doc.metadata['image_info']:
                        # 파일명 기준으로 전체 이미지 목록에서 추가 정보 찾기
                        filename = img_info.get('filename', '')
                        for full_img in all_images:
                            if full_img.get('filename') == filename:
                                # 설명이 없는 경우 전체 이미지 목록의 설명으로 대체
                                if 'description' not in img_info or not img_info['description']:
                                    img_info['description'] = full_img.get('description', '')
                                break
                
                enhanced_results.append((doc, score))
            return enhanced_results
        
        return [(doc, score) for doc, score in results]
    except Exception as e:
        st.error(f"검색 중 오류 발생: {str(e)}")
        return []

def display_search_results(results):
    """검색 결과를 표시합니다."""
    if not results:
        st.warning("검색 결과가 없습니다.")
        return
        
    for doc, score in results:
        similarity = (1 - score) * 100  # 유사도를 백분율로 변환
        
        # 결과 카드 스타일의 컨테이너 생성
        with st.container():
            st.markdown("---")  # 구분선 추가
            
            # 헤더 정보 (유사도 점수)
            st.markdown(f"### 📑 유사도: {similarity:.2f}%")
            
            # 기본 정보를 표 형식으로 표시
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📍 기본 정보**")
                info_md = f"""
                - **공정명:** {doc.metadata.get('process_name', 'N/A')}
                - **설비명:** {doc.metadata.get('equipment_name', 'N/A')}
                """
                # 담당자 정보가 있는 경우에만 표시
                if doc.metadata.get('manager') and doc.metadata.get('manager') != 'N/A':
                    info_md += f"- **담당자:** {doc.metadata.get('manager', 'N/A')}\n"
                    
                st.markdown(info_md)
            
            with col2:
                st.markdown("**📅 작업 정보**")
                work_md = f"""
                - **작업일자:** {doc.metadata.get('work_date', 'N/A')}
                """
                # 작업구분 정보가 있는 경우에만 표시
                if doc.metadata.get('work_type') and doc.metadata.get('work_type') != 'N/A':
                    work_md += f"- **작업구분:** {doc.metadata.get('work_type', 'N/A')}\n"
                    
                st.markdown(work_md)
            
            # 작업 내용 표시
            st.markdown("**📝 작업 상세내용**")
            content = doc.page_content.strip()
            if content:
                with st.expander("작업 내용 전체 보기", expanded=True):
                    st.markdown(content.replace('\n', '<br>'), unsafe_allow_html=True)
            
            # 디버그 모드인 경우 메타데이터 표시
            if st.session_state.get('debug_mode', False):
                with st.expander("메타데이터 디버그 정보", expanded=False):
                    st.json({k: v for k, v in doc.metadata.items() if k != 'image_info'})
            
            # 이미지 표시
            image_info = doc.metadata.get('image_info', [])
            if image_info:
                st.markdown("**📸 관련 이미지**")
                
                # 각 이미지를 개별적으로 처리
                for i, img_info in enumerate(image_info):
                    # 각 이미지와 설명을 위한 두 개의 열 생성
                    img_col, desc_col = st.columns([1, 1.5])
                    
                    # 이미지 열
                    with img_col:
                        if os.path.exists(img_info['path']):
                            st.image(img_info['path'], caption=img_info['filename'], use_container_width=True)
                        else:
                            st.error(f"이미지를 로드할 수 없습니다: {img_info.get('filename', '알 수 없는 파일')}")
                    
                    # 설명 열
                    with desc_col:
                        # 항상 이미지 설명 섹션 표시
                        st.markdown("**이미지 설명:**")
                        
                        # 설명이 있으면 표시, 없으면 '설명 없음' 표시
                        desc = img_info.get('description', '')
                        if desc and desc.strip():
                            st.markdown(desc)
                        else:
                            st.markdown("*설명 없음*")
                        
                        # 디버깅 정보 표시 (개발 중에만 활성화)
                        if st.session_state.get('debug_mode', False):
                            with st.expander("이미지 디버깅 정보", expanded=False):
                                st.json(img_info)
                        
                        # 기타 메타데이터
                        st.markdown(f"""
                        - **공정명:** {img_info.get('process_name', 'N/A')}
                        - **설비명:** {img_info.get('equipment_name', 'N/A')}
                        - **작업일자:** {img_info.get('work_date', 'N/A')}
                        """)
                    
                    # 이미지 사이에 구분선 추가
                    if i < len(image_info) - 1:
                        st.markdown("---")

def show_process_similar_search():
    """공정관리이력 유사 케이스 검색 컴포넌트"""
    st.title("🔍 유사 케이스 검색")
    
    # 공정관리이력 데이터와 벡터 저장소 확인
    if "process_data" not in st.session_state:
        st.error("공정관리이력 데이터가 로드되지 않았습니다.")
        return
        
    if "process_vector_store" not in st.session_state:
        st.error("벡터 저장소가 초기화되지 않았습니다.")
        return
        
    # 데이터 및 벡터 저장소 가져오기
    process_data = st.session_state.process_data
    vector_store = st.session_state.process_vector_store
    
    # 디버그 모드 토글 (사이드바)
    with st.sidebar:
        st.subheader("디버그 옵션")
        if st.checkbox("디버그 모드 활성화", key="debug_mode_toggle"):
            st.session_state.debug_mode = True
            
            # 디버그 정보 표시
            if st.checkbox("이미지 메타데이터 확인", key="check_image_metadata"):
                st.info("이미지 메타데이터를 확인합니다.")
                
                # 처음 5개의 이미지 메타데이터 표시
                all_images = get_all_image_paths(process_data)
                if all_images:
                    st.write(f"총 {len(all_images)}개 이미지 중 일부 샘플")
                    for i, img in enumerate(all_images[:3]):
                        st.write(f"이미지 {i+1}: {img.get('filename', 'N/A')}")
                        st.json(img)
                else:
                    st.warning("이미지 메타데이터가 없습니다.")
        else:
            st.session_state.debug_mode = False
    
    # 검색 인터페이스
    st.markdown("""
    ### 공정관리 유사 케이스 검색
    작업 내용이나 공정 특징을 입력하면 유사한 과거 사례를 찾아 표시합니다.
    """)
    
    # 검색 쿼리 입력
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "검색어를 입력하세요:", 
            height=100,
            placeholder="예: 온도 제어, 밸브 배관, AI 이상 탐지 시스템 등"
        )
    
    with col2:
        st.markdown("### 검색 옵션")
        k = st.number_input(
            "표시할 결과 수:",
            min_value=1,
            max_value=10,
            value=5
        )
        
        st.markdown("")  # 간격 조정
        
        search_button = st.button(
            "검색",
            type="primary",
            use_container_width=True
        )
    
    # 검색 수행
    if search_button:
        if query:
            with st.spinner("유사한 케이스를 검색 중입니다..."):
                results = search_similar_cases(query, vector_store, k=k)
                
                if results:
                    st.success(f"{len(results)}개의 유사 케이스를 찾았습니다.")
                    display_search_results(results)
                else:
                    st.warning("검색 결과가 없습니다. 다른 검색어로 시도해보세요.")
        else:
            st.warning("검색어를 입력해주세요.")
            
    # 자주 찾는 검색어 제안
    st.markdown("### 자주 찾는 검색어")
    example_queries = [
        "센서 추가 설치", "Rotary Cooler", "소성로", 
        "이상 발생률", "환기 시스템", "자동화 프로세스",
        "온도 제어", "압력 모니터링", "유량 조절"
    ]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        for q in example_queries[:3]:
            if st.button(q, key=f"example_query_{q}"):
                # 버튼 클릭 시 세션 상태에 쿼리 저장 후 페이지 재실행
                st.session_state.search_query = q
                st.rerun()
    
    with col2:
        for q in example_queries[3:6]:
            if st.button(q, key=f"example_query_{q}"):
                st.session_state.search_query = q
                st.rerun()
    
    with col3:
        for q in example_queries[6:]:
            if st.button(q, key=f"example_query_{q}"):
                st.session_state.search_query = q
                st.rerun()
    
    # 예시 쿼리가 선택되었으면 자동 검색 실행
    if hasattr(st.session_state, 'search_query') and st.session_state.search_query:
        query = st.session_state.search_query
        
        # 검색어 표시
        st.info(f"선택한 검색어: {query}")
        
        # 검색 수행
        with st.spinner("유사한 케이스를 검색 중입니다..."):
            results = search_similar_cases(query, vector_store, k=k)
            
            if results:
                st.success(f"{len(results)}개의 유사 케이스를 찾았습니다.")
                display_search_results(results)
            else:
                st.warning("검색 결과가 없습니다. 다른 검색어로 시도해보세요.")
        
        # 세션 상태 초기화
        st.session_state.search_query = None 