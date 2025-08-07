"""
SEM-EDS 분석을 위한 이미지 처리 유틸리티
"""

import io
import base64
import streamlit as st
from PIL import Image, ImageFilter
from pathlib import Path
import os

def encode_image_to_base64(image):
    """이미지를 base64로 인코딩

    Args:
        image: PIL 이미지 객체

    Returns:
        str: Base64로 인코딩된 이미지 문자열
    """
    buffered = io.BytesIO()
    # 이미지 모드 변환
    if image.mode in ['RGBA', 'P', 'LA']:
        image = image.convert('RGB')
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def serialize_image(image):
    """이미지를 메모리에 직렬화

    Args:
        image: PIL 이미지 객체

    Returns:
        dict: 직렬화된 이미지 데이터
    """
    if image is None:
        return None
    buffered = io.BytesIO()
    # 이미지 모드 변환
    if image.mode in ['RGBA', 'P', 'LA']:
        image = image.convert('RGB')
    image.save(buffered, format="JPEG")
    return {
        "bytes": buffered.getvalue(),
        "format": "JPEG",
        "mode": image.mode,
        "size": image.size
    }

def deserialize_image(image_data):
    """직렬화된 이미지 데이터로부터 이미지 복원

    Args:
        image_data (dict): 직렬화된 이미지 데이터

    Returns:
        Image: 복원된 PIL 이미지 객체
    """
    if image_data is None:
        return None
    return Image.open(io.BytesIO(image_data["bytes"]))

def process_uploaded_image(uploaded_file):
    """업로드된 이미지 파일 처리

    Args:
        uploaded_file: Streamlit의 업로드된 파일 객체

    Returns:
        dict: 처리된 이미지 정보
    """
    try:
        # 이미지 열기
        image = Image.open(uploaded_file)

        # 이미지 메타데이터 추출
        metadata = {
            "filename": uploaded_file.name,
            "size": f"{uploaded_file.size / 1024:.2f} KB",
            "format": image.format,
            "mode": image.mode,
            "dimensions": image.size
        }

        # 이미지 모드 변환 (필요한 경우)
        if image.mode in ['RGBA', 'P', 'LA']:
            image = image.convert('RGB')

        # 이미지 직렬화
        serialized_image = serialize_image(image)

        return {
            "image": image,
            "serialized": serialized_image,
            "metadata": metadata
        }
    except Exception as e:
        st.error(f"이미지 처리 중 오류가 발생했습니다: {str(e)}")
        return None

def load_image_from_directory(filename, folder="images"):
    """디렉토리에서 이미지 파일 로드

    Args:
        filename (str): 이미지 파일명
        folder (str): 이미지가 저장된 하위 폴더 이름

    Returns:
        dict: 처리된 이미지 정보
    """
    try:
        # 파일 경로 생성
        file_path = Path("SEM_EDS") / folder / filename
        
        # 파일 존재 여부 확인
        if not file_path.exists():
            st.error(f"파일을 찾을 수 없습니다: {file_path}")
            return None
            
        # 이미지 열기
        image = Image.open(file_path)
        
        # 파일 크기 계산
        file_size = os.path.getsize(file_path)
        
        # 이미지 메타데이터 추출
        metadata = {
            "filename": filename,
            "size": f"{file_size / 1024:.2f} KB",
            "format": image.format,
            "mode": image.mode,
            "dimensions": image.size
        }
        
        # 이미지 모드 변환 (필요한 경우)
        if image.mode in ['RGBA', 'P', 'LA']:
            image = image.convert('RGB')
            
        # 이미지 직렬화
        serialized_image = serialize_image(image)
        
        return {
            "image": image,
            "serialized": serialized_image,
            "metadata": metadata,
            "path": str(file_path)
        }
    except Exception as e:
        st.error(f"이미지 처리 중 오류가 발생했습니다: {str(e)}")
        return None

def apply_edge_detection(image, method=None):
    """이미지에 윤곽선 검출 필터 적용

    Args:
        image (PIL.Image): 원본 이미지
        method (str): 윤곽선 검출 방법 ('find_edges', 'contour')

    Returns:
        PIL.Image: 윤곽선 검출된 이미지
    """
    if image is None:
        return None

    if method == "contour":
        # 등고선 필터 적용
        return image.filter(ImageFilter.CONTOUR)
    else:
        # 기본값: PIL 내장 윤곽선 검출 필터 적용
        return image.filter(ImageFilter.FIND_EDGES)