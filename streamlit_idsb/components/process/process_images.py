"""
공정관리이력 이미지 처리 모듈
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import io
import datetime
import re
from components.process.process_data_loader import find_image_file

def get_all_image_paths(process_data):
    """모든 이미지 경로와 관련 정보를 가져옵니다."""
    all_images = []
    for entry in process_data:
        # 새로운 구조 JSON 파일 처리
        if 'parsed_data' in entry and 'image_metadata' in entry:
            # 이미지 메타데이터에서 이미지 추출
            for img_id, img_meta in entry['image_metadata'].items():
                filename = img_meta.get('filename', '')
                path = img_meta.get('path', '')
                
                # 이미지 설명 찾기
                description = ""
                xref = img_meta.get('xref')
                
                # 여러 방식으로 설명 찾기 시도
                # 1. 직접 이미지에 있는 description 필드 확인
                if 'description' in img_meta and img_meta['description']:
                    description = img_meta['description']
                # 2. 파일명으로 직접 찾기
                elif 'image_descriptions' in entry and filename in entry['image_descriptions']:
                    description = entry['image_descriptions'][filename]
                # 3. xref로 찾기
                elif xref and 'image_descriptions' in entry:
                    if f'image_{entry["metadata"]["source_file"].split(".")[0]}_p{img_meta.get("page", 1)}_xref{xref}.jpeg' in entry['image_descriptions']:
                        description = entry['image_descriptions'][f'image_{entry["metadata"]["source_file"].split(".")[0]}_p{img_meta.get("page", 1)}_xref{xref}.jpeg']
                # 4. 부분 매칭으로 찾기
                if not description and 'image_descriptions' in entry:
                    for desc_key, desc_value in entry['image_descriptions'].items():
                        if filename in desc_key:
                            description = desc_value
                            break
                
                # 공정, 설비 정보 찾기
                process_name = ""
                equipment_name = ""
                work_details = ""
                
                # 이미지가 사용된 파싱 데이터 항목 찾기
                for key, data in entry['parsed_data'].items():
                    if 'images' in data:
                        for img in data['images']:
                            if img.get('filename') == filename:
                                # 키에서 정보 추출
                                parts = key.split(' - ')
                                process_name = parts[1] if len(parts) > 1 else parts[0] if parts else "미분류"
                                equipment_name = ""
                                # 내용에서 설비명 추출 시도
                                content_lines = data.get('text', '').split('\n')
                                for line in content_lines:
                                    if line and len(line.strip()) > 0 and not any(x in line for x in ["CAM5", "CAM5N", "Line"]):
                                        equipment_name = line.strip()
                                        break
                                work_details = data.get('text', '')
                                break
                
                # 이미지 경로 확인 및 추가
                image_path = find_image_file(path)
                if image_path and os.path.exists(image_path):
                    all_images.append({
                        "path": image_path,
                        "filename": filename,
                        "description": description,
                        "process_name": process_name,
                        "manager": "자동 추출",
                        "work_date": entry.get('metadata', {}).get('extraction_date', ''),
                        "work_details": work_details,
                        "equipment_name": equipment_name,
                        "work_type": "",
                        "relevance_score": 0  # 기본 관련성 점수 초기화
                    })
        # 기존 구조 처리
        elif "작업사진" in entry and entry["작업사진"]:
            image_descriptions = entry.get("이미지설명", {})
            for img_filename in entry["작업사진"]:
                image_path = find_image_file(img_filename)
                if image_path and os.path.exists(image_path):
                    all_images.append({
                        "path": image_path,
                        "filename": img_filename,
                        "description": image_descriptions.get(img_filename, ""),
                        "process_name": entry.get("공정명", ""),
                        "manager": entry.get("담당자", "").split('\n')[0] if entry.get("담당자") else "",
                        "work_date": entry.get("작업 일자", "").split('\n')[0] if entry.get("작업 일자") else "",
                        "work_details": entry.get("작업 상세내용", ""),
                        "equipment_name": entry.get("설비명", ""),
                        "work_type": entry.get("작업 종류", ""),
                        "relevance_score": 0  # 기본 관련성 점수 초기화
                    })
    return all_images

def filter_images_by_date(images, start_date=None, end_date=None):
    """날짜 범위로 이미지를 필터링합니다."""
    if not start_date and not end_date:
        return images
    
    filtered_images = []
    for img in images:
        work_date_str = img.get("work_date", "")
        
        # 날짜 문자열 파싱 시도
        try:
            # 다양한 날짜 형식 처리
            date_formats = [
                "%Y-%m-%d",            # 2023-01-01
                "%Y.%m.%d",            # 2023.01.01
                "%Y/%m/%d",            # 2023/01/01
                "%Y년 %m월 %d일",       # 2023년 01월 01일
                "%Y-%m-%d %H:%M:%S",   # 2023-01-01 12:30:45
                "%Y.%m.%d %H:%M:%S",   # 2023.01.01 12:30:45
            ]
            
            parsed_date = None
            for date_format in date_formats:
                try:
                    parsed_date = datetime.datetime.strptime(work_date_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                # 정규식으로 날짜 추출 시도
                date_match = re.search(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', work_date_str)
                if date_match:
                    year, month, day = map(int, date_match.groups())
                    parsed_date = datetime.date(year, month, day)
            
            # 날짜 필터링
            if parsed_date:
                if start_date and end_date:
                    if start_date <= parsed_date <= end_date:
                        filtered_images.append(img)
                elif start_date:
                    if start_date <= parsed_date:
                        filtered_images.append(img)
                elif end_date:
                    if parsed_date <= end_date:
                        filtered_images.append(img)
            else:
                # 날짜를 파싱할 수 없는 경우 (옵션)
                # 날짜가 없는 항목을 포함하거나 제외
                if not start_date and not end_date:
                    filtered_images.append(img)
        except:
            # 날짜 파싱 오류 시 (옵션)
            # 오류가 있는 항목을 포함하거나 제외
            if not start_date and not end_date:
                filtered_images.append(img)
    
    return filtered_images

def filter_images_by_process(images, process_name=None):
    """공정명으로 이미지를 필터링합니다."""
    if not process_name:
        return images
    
    return [img for img in images if process_name.lower() in img.get("process_name", "").lower()]

def search_images_by_keyword(images, keyword=None):
    """키워드로 이미지를 검색합니다."""
    if not keyword or keyword.strip() == "":
        return images
    
    keyword = keyword.lower()
    filtered_images = []
    
    for img in images:
        # 검색 대상 필드
        searchable_fields = [
            img.get("description", ""),
            img.get("process_name", ""),
            img.get("manager", ""),
            img.get("work_details", ""),
            img.get("equipment_name", ""),
            img.get("work_type", "")
        ]
        
        # 모든 필드에서 키워드 검색
        for field in searchable_fields:
            if keyword in str(field).lower():
                filtered_images.append(img)
                break
    
    return filtered_images

def show_process_images():
    """공정관리이력 이미지 갤러리를 표시합니다."""
    st.title("공정관리이력 이미지 갤러리")
    
    # 공정관리이력 데이터 확인
    if "process_data" not in st.session_state:
        st.error("공정관리이력 데이터가 로드되지 않았습니다.")
        return
    
    # 모든 이미지 정보 가져오기
    all_images = get_all_image_paths(st.session_state.process_data)
    
    if not all_images:
        st.warning("등록된 이미지가 없습니다.")
        return
    
    # 필터링 컨트롤
    st.subheader("이미지 필터링")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 날짜 범위 필터
        start_date = st.date_input("시작일", value=None)
        end_date = st.date_input("종료일", value=None)
    
    with col2:
        # 공정명 필터
        all_processes = set(img.get("process_name", "") for img in all_images if img.get("process_name"))
        selected_process = st.selectbox(
            "공정명 선택",
            options=["전체"] + sorted(list(all_processes))
        )
        
        # 키워드 검색
        search_keyword = st.text_input("키워드 검색 (설명, 작업 내용 등)")
    
    # 필터 적용
    filtered_images = all_images
    
    # 날짜 필터 적용
    if start_date or end_date:
        filtered_images = filter_images_by_date(filtered_images, start_date, end_date)
    
    # 공정명 필터 적용
    if selected_process and selected_process != "전체":
        filtered_images = filter_images_by_process(filtered_images, selected_process)
    
    # 키워드 검색 적용
    if search_keyword:
        filtered_images = search_images_by_keyword(filtered_images, search_keyword)
    
    # 결과 표시
    st.subheader(f"이미지 결과 ({len(filtered_images)}개)")
    
    if not filtered_images:
        st.info("조건에 맞는 이미지가 없습니다.")
        return
    
    # 이미지 갤러리 표시
    columns_per_row = 3
    rows = [filtered_images[i:i+columns_per_row] for i in range(0, len(filtered_images), columns_per_row)]
    
    for row in rows:
        cols = st.columns(columns_per_row)
        
        for i, img in enumerate(row):
            if i < len(cols):
                with cols[i]:
                    try:
                        # 이미지 표시
                        if os.path.exists(img["path"]):
                            st.image(img["path"], caption=img["filename"], use_column_width=True)
                            
                            # 이미지 정보 표시
                            with st.expander("이미지 정보"):
                                if img.get("description"):
                                    st.markdown("**이미지 설명:**")
                                    st.markdown(img['description'])
                                
                                st.markdown(f"""
                                - **공정명:** {img.get('process_name', 'N/A')}
                                - **담당자:** {img.get('manager', 'N/A')}
                                - **작업일자:** {img.get('work_date', 'N/A')}
                                - **설비명:** {img.get('equipment_name', 'N/A')}
                                """)
                                
                                if img.get('work_details'):
                                    st.markdown("**작업 내용:**")
                                    st.text(img.get('work_details', ''))
                    except Exception as e:
                        st.error(f"이미지 로딩 오류: {str(e)}")
    
    # 이미지 다운로드
    st.subheader("이미지 다운로드")
    
    # 다운로드할 이미지 선택
    image_options = {f"{img['filename']} ({img.get('process_name', 'N/A')})": img for img in filtered_images}
    selected_image_key = st.selectbox("다운로드할 이미지 선택", list(image_options.keys()))
    
    if selected_image_key:
        selected_image = image_options[selected_image_key]
        
        try:
            if os.path.exists(selected_image["path"]):
                with open(selected_image["path"], "rb") as file:
                    btn = st.download_button(
                        label="이미지 다운로드",
                        data=file,
                        file_name=selected_image["filename"],
                        mime="image/jpeg"
                    )
        except Exception as e:
            st.error(f"다운로드 오류: {str(e)}") 