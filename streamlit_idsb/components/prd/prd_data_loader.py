"""
PRD(생산관리이력) 데이터 로드 및 벡터 데이터베이스 관리 모듈
"""

import os
import json
import streamlit as st
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def find_image_file(image_filename):
    """이미지 파일 경로를 찾습니다."""
    # 경로 후보 목록 (상대 경로 및 절대 경로)
    image_dir_candidates = [
        "PRD/images",  # 기본 이미지 경로
        "PRD/output/images",  # 출력 이미지 경로
        os.path.join(os.getcwd(), "PRD/images"),  # 절대 경로
        os.path.join(os.getcwd(), "PRD/output/images"),  # 절대 경로
    ]

    # 후보 경로에서 이미지 파일 찾기
    for image_dir in image_dir_candidates:
        image_path = os.path.join(image_dir, image_filename)
        if os.path.exists(image_path):
            return image_path

    return None

def load_prd_data():
    """생산관리이력 데이터를 로드합니다."""
    try:
        # 데이터 파일 경로
        prd_data_path = "PRD/output/일일업무일지.json"

        # 파일 존재 여부 확인
        if not os.path.exists(prd_data_path):
            st.warning(f"PRD 데이터 파일이 존재하지 않습니다: {prd_data_path}")
            return []

        # JSON 파일 로드
        with open(prd_data_path, 'r', encoding='utf-8') as f:
            prd_data = json.load(f)

        # 데이터 구조 확인 및 추출
        if isinstance(prd_data, dict) and "entries" in prd_data:
            # 일일업무일지.json 구조에 맞게 entries 추출
            entries = prd_data.get("entries", [])
            st.success(f"생산관리이력 데이터 로드 완료: {len(entries)}건")
            return entries
        else:
            # 다른 구조일 경우 그대로 반환
            st.success(f"생산관리이력 데이터 로드 완료")
            return prd_data

    except Exception as e:
        st.error(f"생산관리이력 데이터 로드 중 오류 발생: {str(e)}")
        return []

def create_documents(prd_data):
    """PRD 데이터로부터 문서를 생성합니다."""
    documents = []

    # for entry in prd_data:
    #     # 작업 내용 추출
    #     content = entry.get("작업 상세내용", "")

    #     # 메타데이터 구성
    #     metadata = {
    #         "line": entry.get("라인", ""),
    #         "product": entry.get("제품", ""),
    #         "issue": entry.get("이슈", ""),
    #         "equipment_no": entry.get("설비번호", "").split('\n')[0] if entry.get("설비번호") else "",
    #         "equipment_name": entry.get("설비명", ""),
    #         "work_date": entry.get("작업 일자", "").split('\n')[0] if entry.get("작업 일자") else "",
    #         "work_type": entry.get("작업 종류", ""),
    #         "title": entry.get("제목", "")
    #     }

    #     # 이미지 정보 추가
    #     if "작업사진" in entry and entry["작업사진"]:
    #         image_info = []
    #         image_descriptions = entry.get("이미지설명", {})

    #         for img_filename in entry["작업사진"]:
    #             image_path = find_image_file(img_filename)
    #             if image_path and os.path.exists(image_path):
    #                 image_info.append({
    #                     "path": image_path,
    #                     "filename": img_filename,
    #                     "description": image_descriptions.get(img_filename, ""),
    #                     "line": entry.get("라인", ""),
    #                     "product": entry.get("제품", ""),
    #                     "equipment_no": metadata["equipment_no"],
    #                     "work_date": metadata["work_date"],
    #                     "work_details": content
    #                 })

    #         metadata["image_info"] = image_info

    #     # 문서 객체 생성
    #     document = Document(page_content=content, metadata=metadata)
    #     documents.append(document)

    # 기본 이미지 경로
    base_image_dir = os.getcwd() + "/PRD/output/images"

    for file in prd_data:
        # 파일별 이미지 디렉토리
        image_dir = os.path.join(base_image_dir, os.path.splitext(file["file_name"])[0])

        # 파일 메타데이터 구성
        file_metadata = {
            **file,
            "is_file": True,
            # "image_dir": image_dir,
        }

        # 파일 제목 추출
        file_title = file.get("title", "제목 없음")

        # 파일 요약 추출
        file_summary = file.get("summary", {}).get("full_text", "요약 없음")

        # 파일 Document 객체 생성
        file_document = Document(
            page_content=f"### {file_title}\n\n{file_summary}",
            metadata=file_metadata
        )
        documents.append(file_document)

        # 페이지별 Document 객체 생성
        for page in file["pages"]:
            # 페이지 메타데이터 구성
            page_metadata = {
                "parent_file": {
                    "file_name": file["file_name"],
                    "file_path": file["file_path"],
                    "title": file.get("title", "제목 없음"),
                    "summary": file.get("summary", {}),
                    "date": file.get("date", "날짜 정보 없음"),
                    "lines": file.get("lines", ["대상 라인 정보 없음"]),
                    "equipments": file.get("equipments", ["대상 설비 정보 없음"]),
                    "issues": file.get("issues", ["발생 이슈 정보 없음"]),
                },
                **page,
                "is_file": False,
                # "image_dir": page.get("image_path", ""),
            }

            page_title = page.get("title", "제목 없음")
            page_summary = page.get("summary", "요약 없음")

            page_document = Document(
                page_content=f"### {file_title}\n\n#### {page_title}\n\n{page_summary}",
                metadata=page_metadata
            )
            documents.append(page_document)

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

def load_or_create_vector_db(prd_data, vector_dir="PRD/vector_db"):
    """벡터 데이터베이스를 로드하거나 생성합니다."""
    try:
        # JSON 파일 경로 및 벡터 저장소 경로
        prd_data_path = "PRD/output/일일업무일지.json"
        vector_index_path = os.path.join(vector_dir, "index.faiss")

        # 벡터 저장소 디렉토리와 인덱스 파일 확인
        vector_exists = os.path.exists(vector_dir) and os.path.exists(vector_index_path) and len(os.listdir(vector_dir)) > 0

        # 파일 변경 여부 확인을 위한 상태 파일 경로
        status_file = os.path.join(vector_dir, "last_modified.txt")

        # 벡터 저장소가 있을 경우, JSON 파일 변경 여부 확인
        if vector_exists and os.path.exists(prd_data_path):
            # 현재 JSON 파일의 수정 시간
            current_mtime = os.path.getmtime(prd_data_path)

            # 마지막으로 저장된 수정 시간 확인
            last_mtime = 0
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding="utf-8") as f:
                    try:
                        last_mtime = float(f.read().strip())
                    except:
                        last_mtime = 0

            # 변경되지 않았다면 기존 벡터 저장소 로드
            if abs(current_mtime - last_mtime) < 1:  # 1초 이내의 차이는 무시
                st.info("JSON 파일에 변경 사항이 없어 기존 벡터 DB를 사용합니다.")

                # 임베딩 모델 초기화
                embeddings = HuggingFaceEmbeddings(
                    model_name="intfloat/multilingual-e5-large-instruct",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True},
                    cache_folder="models/multilingual-e5-large-instruct"
                )

                # 로컬 저장소에서 로드
                vector_store = FAISS.load_local(
                    vector_dir,
                    embeddings,
                    allow_dangerous_deserialization=True  # 신뢰할 수 있는 소스에서만 설정
                )
                return vector_store
            else:
                # 변경이 있으면 다시 생성
                st.info("JSON 파일이 변경되어 벡터 DB를 다시 생성합니다.")
                documents = create_documents(prd_data)
                vector_store = create_vector_db(documents, vector_dir)

                # 수정 시간 저장
                os.makedirs(vector_dir, exist_ok=True)
                with open(status_file, 'w') as f:
                    f.write(str(current_mtime))

                return vector_store

        # 벡터 저장소가 없으면 새로 생성
        if not vector_exists:
            st.info("벡터 DB가 없어 새로 생성합니다.")
            documents = create_documents(prd_data)
            vector_store = create_vector_db(documents, vector_dir)

            # 수정 시간 저장
            if os.path.exists(prd_data_path):
                current_mtime = os.path.getmtime(prd_data_path)
                os.makedirs(vector_dir, exist_ok=True)
                with open(status_file, 'w') as f:
                    f.write(str(current_mtime))

            return vector_store

        # 임베딩 모델 초기화
        embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large-instruct",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
            cache_folder="models/multilingual-e5-large-instruct"
        )

        # 로컬 저장소에서 로드
        vector_store = FAISS.load_local(
            vector_dir,
            embeddings,
            allow_dangerous_deserialization=True  # 신뢰할 수 있는 소스에서만 설정
        )
        return vector_store
    except Exception as e:
        st.error(f"벡터 데이터베이스 로드 중 오류 발생: {str(e)}")
        return None

# __init__.py에 노출할 함수들
__all__ = [
    'load_prd_data',
    'create_documents',
    'create_vector_db',
    'load_or_create_vector_db',
    'find_image_file'
]