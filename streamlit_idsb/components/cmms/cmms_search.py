import streamlit as st
import pandas as pd
import numpy as np
import os
from PIL import Image
from langchain.schema import Document

def search_similar_cases(query, vector_store, k=5):
    """유사한 케이스를 검색합니다."""
    try:
        results = vector_store.similarity_search_with_score(query, k=k)
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
                - **라인:** {doc.metadata.get('line', 'N/A')}
                - **설비번호:** {doc.metadata.get('equipment_no', 'N/A')}
                - **설비명:** {doc.metadata.get('equipment_name', 'N/A')}
                """
                st.markdown(info_md)
            
            with col2:
                st.markdown("**📅 작업 정보**")
                work_md = f"""
                - **작업일자:** {doc.metadata.get('work_date', 'N/A')}
                - **작업구분:** {doc.metadata.get('work_type', 'N/A')}
                """
                st.markdown(work_md)
            
            # 작업 내용 표시
            st.markdown("**📝 작업 상세내용**")
            content = doc.page_content.strip()
            if content:
                with st.expander("작업 내용 전체 보기", expanded=True):
                    st.markdown(content)
            
            # 이미지 표시
            image_info = doc.metadata.get('image_info', [])
            if image_info:
                st.markdown("**📸 관련 이미지**")
                cols = st.columns(min(len(image_info), 3))
                
                for i, img_info in enumerate(image_info):
                    col_idx = i % len(cols)
                    with cols[col_idx]:
                        if os.path.exists(img_info['path']):
                            st.image(img_info['path'], caption=img_info['filename'], use_container_width=True)
                            
                            if img_info.get('description'):
                                st.markdown(f"**설명:** {img_info['description']}")

def show_cmms_similar_search():
    """CMMS 유사 케이스 검색 컴포넌트"""
    st.title("🔍 유사 케이스 검색")
    
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
    
    # 검색 인터페이스
    st.markdown("""
    ### 설비 유지보수 유사 케이스 검색
    작업 내용이나 증상을 입력하면 유사한 과거 사례를 찾아 표시합니다.
    """)
    
    # 검색 쿼리 입력
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "검색어를 입력하세요:", 
            height=100,
            placeholder="예: 모터 과열 문제, 센서 오작동, 베어링 교체 방법 등"
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
        "모터 과열", "베어링 교체", "센서 오작동", 
        "누수 수리", "진동 문제", "소음 발생", 
        "펌프 고장", "전기 배선 수리", "컨트롤러 에러"
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