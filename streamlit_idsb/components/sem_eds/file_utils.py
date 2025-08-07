"""
SEM-EDS 분석을 위한 파일 관리 유틸리티
"""

from pathlib import Path
import os

def create_sem_eds_folders():
    """SEM-EDS 분석을 위한 폴더 구조 생성

    Returns:
        Path: 생성된 기본 디렉토리 경로
    """
    base_dir = Path("SEM_EDS")
    folders = ["images", "json", "reports"]

    for folder in folders:
        (base_dir / folder).mkdir(parents=True, exist_ok=True)
    return base_dir

def save_uploaded_file(uploaded_file, folder):
    """업로드된 파일 저장

    Args:
        uploaded_file: Streamlit의 업로드된 파일 객체
        folder (str): 저장할 하위 폴더 이름

    Returns:
        str: 저장된 파일의 경로
    """
    file_path = Path("SEM_EDS") / folder / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(file_path)

def get_image_files_in_directory(folder="images"):
    """SEM_EDS 디렉토리 내의 이미지 파일 목록 가져오기
    
    Args:
        folder (str): 이미지가 저장된 하위 폴더 이름
        
    Returns:
        list: 이미지 파일 이름 목록
    """
    image_dir = Path("SEM_EDS") / folder
    if not image_dir.exists():
        return []
        
    # 이미지 확장자 필터링
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff']
    
    # 이미지 파일 목록 반환
    return [
        f.name for f in image_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in image_extensions
    ]