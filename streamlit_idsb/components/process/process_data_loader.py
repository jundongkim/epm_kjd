"""
공정관리이력 데이터 로드 및 벡터 데이터베이스 관리 모듈
"""

import os
import json
import glob
import streamlit as st
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def find_image_file(image_filename):
    """이미지 파일 경로를 찾습니다."""
    # 절대 경로인 경우 바로 확인
    if os.path.isabs(image_filename) and os.path.exists(image_filename):
        return image_filename

    # 경로 후보 목록 (상대 경로 및 절대 경로)
    image_dir_candidates = [
        "PROCESS/images",  # 기본 이미지 경로
        "PROCESS/output/images",  # 출력 이미지 경로
        os.path.join(os.getcwd(), "PROCESS/images"),  # 절대 경로
        os.path.join(os.getcwd(), "PROCESS/output/images"),  # 절대 경로
    ]

    # 후보 경로에서 이미지 파일 찾기
    for image_dir in image_dir_candidates:
        image_path = os.path.join(image_dir, os.path.basename(image_filename))
        if os.path.exists(image_path):
            return image_path

    # 파일 이름만으로 검색
    for image_dir in image_dir_candidates:
        if os.path.exists(image_dir):
            for filename in os.listdir(image_dir):
                if os.path.basename(image_filename) == filename:
                    return os.path.join(image_dir, filename)

    return image_filename  # 원본 경로 반환 (없으면 나중에 확인)

def load_process_data():
    """공정관리이력 데이터를 로드합니다."""
    try:
        # PROCESS/output 디렉토리 내의 모든 JSON 파일 찾기
        process_data_path = "PROCESS/output"
        json_files = glob.glob(f"{process_data_path}/*.json")

        if not json_files:
            st.warning(f"공정관리이력 데이터 파일이 존재하지 않습니다: {process_data_path}")
            return []

        all_entries = []

        # 모든 JSON 파일에서 데이터 로드
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                # 파일 이름 추출 (디버깅용)
                # file_name = os.path.basename(json_file)
                # st.info(f"파일 로드: {file_name}")

                # 데이터 구조에 따라 처리
                if 'parsed_data' in file_data:
                    # 새로운 형식의 파일
                    all_entries.append(file_data)
                elif isinstance(file_data, dict) and "entries" in file_data:
                    # 기존 형식의 파일 (entries 키가 있는 경우)
                    entries = file_data.get("entries", [])
                    all_entries.extend(entries)
                elif isinstance(file_data, list):
                    # 기존 형식의 파일 (리스트 형식)
                    all_entries.extend(file_data)
                else:
                    # 기존 형식의 파일 (단일 항목)
                    all_entries.append(file_data)

            except Exception as e:
                st.warning(f"파일 로드 중 오류 발생: {json_file} - {str(e)}")
                continue

        st.success(f"공정관리이력 데이터 로드 완료: {len(all_entries)}건")
        return all_entries

    except Exception as e:
        st.error(f"공정관리이력 데이터 로드 중 오류 발생: {str(e)}")
        return []

def create_documents(process_data):
    """공정관리이력 데이터로부터 문서를 생성합니다."""
    documents = []

    for entry in process_data:
        # JSON 구조 확인
        if 'parsed_data' in entry:
            # 새로운 구조의 JSON 파일 처리
            for key, data in entry['parsed_data'].items():
                # 작업 내용 추출
                content = data.get("text", "")
                if not content:
                    continue

                # 내용에서 기본 정보 추출
                lines = content.strip().split('\n')

                # 공정명/설비명 추출 (키 이름에서 추출 및 내용에서 보완)
                parts = key.split(' - ')
                process_name = ""
                equipment_name = ""

                # 키에서 공정명과 라인 정보 추출
                if len(parts) > 1:
                    # YE Part - CAM5 1 Line - 변경점 및 TEST 진행 현황 형식에서 추출
                    line_info = parts[1].strip() if len(parts) > 1 else ""
                    process_name = line_info

                # 내용에서 공정명과 설비명 추출 (보통 첫 몇 줄에 나타남)
                if "CAM5" in content or "CAM5N" in content:
                    for i, line in enumerate(lines):
                        if "CAM5" in line or "CAM5N" in line:
                            process_name = line.strip()
                        # 설비명은 보통 CAM5/CAM5N 다음 라인에 표시
                        elif i > 0 and (process_name and not equipment_name) and len(line.strip()) > 0:
                            # 기존 설비명이 있으면 보존
                            if len(equipment_name) == 0:
                                equipment_name = line.strip()
                        # Line 정보가 포함된 경우 (예: "1 Line", "2 Line")
                        elif "Line" in line and process_name:
                            process_name = f"{process_name} {line.strip()}"

                # 작업 종류 추출 (키 이름에서 세번째 부분 추출 또는 빈 문자열)
                work_type = parts[2] if len(parts) > 2 else ""

                # 이미지 정보 처리
                image_info = []
                if 'images' in data:
                    for img in data['images']:
                        img_filename = img.get('filename', '')
                        img_path = find_image_file(img.get('path', ''))

                        # 이미지 설명 찾기
                        description = ""
                        img_xref = img.get('xref')

                        # 이미지 설명 찾기 - 여러 방법 시도
                        # 1. 직접 이미지에 있는 description 필드 확인
                        if 'description' in img and img['description']:
                            description = img['description']
                        # 2. 파일명으로 직접 찾기
                        elif 'image_descriptions' in entry and img_filename in entry['image_descriptions']:
                            description = entry['image_descriptions'][img_filename]
                        # 3. xref로 찾기
                        elif 'image_descriptions' in entry:
                            for desc_key, desc_value in entry['image_descriptions'].items():
                                if img_filename in desc_key:
                                    description = desc_value
                                    break

                        # 직접 참조 시도
                        if not description and img_xref and 'image_descriptions' in entry:
                            if f'image_{entry["metadata"]["source_file"].split(".")[0]}_p{img.get("page", 1)}_xref{img_xref}.jpeg' in entry['image_descriptions']:
                                description = entry['image_descriptions'][f'image_{entry["metadata"]["source_file"].split(".")[0]}_p{img.get("page", 1)}_xref{img_xref}.jpeg']

                        if os.path.exists(img_path):
                            image_info.append({
                                "path": img_path,
                                "filename": img_filename,
                                "description": description,
                                "process_name": process_name,
                                "equipment_name": equipment_name,
                                "work_type": work_type,
                                "work_details": content
                            })

                # 작업 일자는 메타데이터에서 추출
                work_date = entry.get('metadata', {}).get('extraction_date', '')

                # 메타데이터 구성
                metadata = {
                    "process_name": process_name,
                    "equipment_name": equipment_name,
                    "work_type": work_type,
                    "work_date": work_date,
                    "manager": "N/A",  # 메타데이터에서 담당자 정보가 없으므로 기본값 설정
                    "page": data.get("page", ""),
                    "image_info": image_info
                }

                # 문서 객체 생성
                document = Document(page_content=content, metadata=metadata)
                documents.append(document)
        else:
            # 기존 구조의 데이터 처리
            content = entry.get("작업 상세내용", "")

            # 메타데이터 구성
            metadata = {
                "process_name": entry.get("공정명", ""),
                "manager": entry.get("담당자", "").split('\n')[0] if entry.get("담당자") else "",
                "equipment_name": entry.get("설비명", ""),
                "work_date": entry.get("작업 일자", "").split('\n')[0] if entry.get("작업 일자") else "",
                "work_type": entry.get("작업 종류", ""),
            }

            # 이미지 정보 추가
            if "작업사진" in entry and entry["작업사진"]:
                image_info = []
                image_descriptions = entry.get("이미지설명", {})

                for img_filename in entry["작업사진"]:
                    image_path = find_image_file(img_filename)
                    if image_path and os.path.exists(image_path):
                        image_info.append({
                            "path": image_path,
                            "filename": img_filename,
                            "description": image_descriptions.get(img_filename, ""),
                            "process_name": entry.get("공정명", ""),
                            "manager": metadata["manager"],
                            "work_date": metadata["work_date"],
                            "work_details": content
                        })

                metadata["image_info"] = image_info

            # 문서 객체 생성
            document = Document(page_content=content, metadata=metadata)
            documents.append(document)

    return documents

def create_vector_db(documents, vector_dir="vector_db"):
    """문서로부터 벡터 데이터베이스를 생성합니다."""
    try:
        # 임베딩 모델 초기화
        embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large-instruct",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
            cache_folder="models/multilingual-e5-large-instruct"
        )

        # 벡터 저장소 생성
        vector_store = FAISS.from_documents(documents, embeddings)

        # 디렉토리에 저장
        os.makedirs(vector_dir, exist_ok=True)
        vector_store.save_local(vector_dir)

        return vector_store
    except Exception as e:
        st.error(f"벡터 데이터베이스 생성 중 오류 발생: {str(e)}")
        return None

def load_or_create_vector_db(process_data, vector_dir="PROCESS/vector_db"):
    """벡터 데이터베이스를 로드하거나 생성합니다."""
    try:
        st.info("벡터 데이터베이스 초기화 시작...")

        # 벡터 저장소 경로
        vector_index_path = os.path.join(vector_dir, "index.faiss")

        # 벡터 저장소 디렉토리와 인덱스 파일 확인
        vector_exists = os.path.exists(vector_dir) and os.path.exists(vector_index_path) and len(os.listdir(vector_dir)) > 0

        # 파일 변경 여부 확인을 위한 상태 파일 경로
        status_file = os.path.join(vector_dir, "last_modified.txt")

        # 데이터 파일 찾기
        data_files = glob.glob("PROCESS/output/*.json")
        current_mtimes = {}

        # 모든 파일의 수정 시간 확인
        for file_path in data_files:
            if os.path.exists(file_path):
                current_mtimes[file_path] = os.path.getmtime(file_path)

        # 벡터 저장소가 있을 경우, JSON 파일 변경 여부 확인
        if vector_exists and data_files:
            # 마지막으로 저장된 수정 시간 확인
            last_mtimes = {}
            if os.path.exists(status_file):
                try:
                    with open(status_file, 'r', encoding="utf-8") as f:
                        last_mtimes = json.load(f)
                except:
                    last_mtimes = {}

            # 변경 여부 확인
            files_changed = False

            # 새 파일이 추가되었는지 확인
            for file_path in current_mtimes:
                if file_path not in last_mtimes:
                    files_changed = True
                    st.info(f"새 파일 감지: {os.path.basename(file_path)}")
                    break
                elif current_mtimes[file_path] > last_mtimes[file_path]:
                    files_changed = True
                    st.info(f"파일 변경 감지: {os.path.basename(file_path)}")
                    break

            # 기존 파일 수와 현재 파일 수 비교
            if len(current_mtimes) != len(last_mtimes):
                files_changed = True
                st.info(f"파일 수 변경 감지: {len(last_mtimes)} → {len(current_mtimes)}")

            # 파일이 변경되지 않았다면 저장된 벡터 저장소 로드
            if not files_changed:
                try:
                    st.info("기존 벡터 데이터베이스 로드 중...")

                    # 임베딩 모델 초기화
                    embeddings = HuggingFaceEmbeddings(
                        model_name="intfloat/multilingual-e5-large-instruct",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True},
                        cache_folder="models/multilingual-e5-large-instruct"
                    )

                    # 벡터 저장소 로드
                    vector_store = FAISS.load_local(vector_dir, embeddings, allow_dangerous_deserialization=True)

                    st.success(f"벡터 데이터베이스 로드 완료: {vector_dir}")
                    return vector_store
                except Exception as e:
                    st.warning(f"벡터 저장소 로드 중 오류 발생: {str(e)}")
                    # 오류 발생 시 새로 생성
                    st.info("벡터 데이터베이스를 새로 생성합니다.")
            else:
                st.info("데이터 파일이 변경되어 벡터 데이터베이스를 새로 생성합니다.")
        else:
            if not vector_exists:
                st.info("기존 벡터 데이터베이스가 없어 새로 생성합니다.")
            if not data_files:
                st.warning("데이터 파일이 없습니다.")
                return None

        # 문서 생성
        st.info("문서 생성 중...")
        documents = create_documents(process_data)
        st.info(f"문서 생성 완료: {len(documents)}개")

        if not documents:
            st.warning("생성된 문서가 없습니다.")
            return None

        # 벡터 저장소 생성
        st.info("벡터 데이터베이스 생성 중...")
        vector_store = create_vector_db(documents, vector_dir)

        if vector_store:
            # 수정 시간 저장
            try:
                os.makedirs(os.path.dirname(status_file), exist_ok=True)
                with open(status_file, 'w', encoding="utf-8") as f:
                    json.dump(current_mtimes, f, ensure_ascii=False, indent=2)
            except Exception as e:
                st.warning(f"수정 시간 저장 중 오류 발생: {str(e)}")

            st.success(f"벡터 데이터베이스 생성 완료: {vector_dir}")

        return vector_store

    except Exception as e:
        st.error(f"벡터 데이터베이스 처리 중 오류 발생: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None