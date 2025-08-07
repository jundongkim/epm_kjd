import os
import json
import re
import glob
from datetime import datetime
from typing import List, Dict, Optional, Any
import fitz  # PyMuPDF
import logging
from PIL import Image
import io
import shutil
import base64
import requests  # Ollama API 호출용
import time
from dotenv import load_dotenv
import pytesseract
import numpy as np
import socket
import random
import subprocess
import shlex
import tempfile
from requests.exceptions import RequestException
import gc

# Load environment variables from .env file
load_dotenv()

# Ollama 서버 URL 설정
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
USE_CLI = os.getenv("USE_CLI", "n").lower() in ["y", "yes", "true", "1"]

# Ollama CLI 경로 설정 (기본값과 환경변수에서 가져옴)
OLLAMA_CLI_PATH = os.getenv("OLLAMA_CLI_PATH", "/usr/local/bin/ollama")
if not os.path.exists(OLLAMA_CLI_PATH):
    # 시스템 PATH에서 찾기 시도
    try:
        OLLAMA_CLI_PATH = subprocess.check_output(["which", "ollama"], text=True).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        OLLAMA_CLI_PATH = "ollama"  # 기본값으로 설정

# 모델 스펙 정보
MODEL_SPECS = {
    "gemma3:1b": {
        "size": "1B",
        "context_length": 32768,  # 32k
        "languages": "English",
        "modalities": ["Text"]
    },
    "gemma3:4b": {
        "size": "4B",
        "context_length": 131072,  # 128k
        "languages": "+140 Languages",
        "modalities": ["Text", "Image"]
    },
    "gemma3:12b": {
        "size": "12B",
        "context_length": 131072,  # 128k
        "languages": "+140 Languages",
        "modalities": ["Text", "Image"]
    },
    "gemma3:27b": {
        "size": "27B",
        "context_length": 131072,  # 128k
        "languages": "+140 Languages",
        "modalities": ["Text", "Image"]
    },
    "shield-gemma2": {
        "size": "4B",
        "context_length": 8192,  # 8k
        "languages": "+140 Languages",
        "modalities": ["Text", "Image"]
    }
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFConverter:
    def __init__(self, pdf_path, output_dir, image_dir, use_image_description=True):
        """
        Initialize the PDF converter

        Args:
            pdf_path (str): Path to the PDF file
            output_dir (str): Directory to save the JSON output
            image_dir (str): Directory to save extracted images
            use_image_description (bool): Whether to generate image descriptions using Ollama
        """
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.image_dir = image_dir
        self.use_image_description = use_image_description
        self.doc = fitz.open(pdf_path)
        self.ensure_directories()

        # Ollama 서버 URL 설정
        self.ollama_url = OLLAMA_BASE_URL
        logger.info(f"Ollama URL set to {self.ollama_url} for image descriptions")

        # CLI 모드 체크
        self.use_cli = USE_CLI
        self.ollama_cli_path = OLLAMA_CLI_PATH
        if self.use_cli:
            logger.info(f"Using Ollama CLI mode for image descriptions (CLI path: {self.ollama_cli_path})")

        # Initialize work type classifier patterns
        self.work_type_patterns = {
            "점검": r"점검|확인|모니터링|체크",
            "수리": r"수리|교체|조치|보수|수정",
            "조정": r"조정|조절|설정|세팅",
            "청소": r"청소|클리닝|세척",
            "주입": r"주입|충진|충유",
            "설치": r"설치|장착|부착|설비"
        }

        # Initialize equipment name patterns
        self.equipment_patterns = {
            "건조기": r"건조기|드라이어",
            "소성로": r"소성로|furnace",
            "분급기": r"분급기|classifier",
            "필터": r"필터|filter",
            "프레스": r"프레스|press",
            "밸브": r"밸브|valve",
            "센서": r"센서|sensor",
            "모터": r"모터|motor",
            "펌프": r"펌프|pump"
        }

    def ensure_directories(self):
        """Create output and image directories if they don't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    def extract_text_from_page(self, page: fitz.Page) -> str:
        """
        Extract text from a PDF page with improved layout preservation.
        """
        print(f"** filename: {os.path.splitext(os.path.basename(self.doc.name))[0]}")
        print(f"** page: {page.number}")
        # 테이블 레이아웃 보존을 위해 "dict" 형식으로 먼저 추출
        text_dict = page.get_text("dict")

        # 블록 단위로 처리하여 테이블 구조 보존 시도
        blocks = []
        for block in text_dict["blocks"]:
            if "lines" in block:
                block_text = ""
                for line in block["lines"]:
                    if "spans" in line:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"] + " "
                        block_text += line_text.strip() + "\n"
                blocks.append(block_text)

        # 일반 텍스트 추출 (백업)
        regular_text = page.get_text("text")

        # 둘 중 더 긴 텍스트 선택 (더 많은 정보 포함)
        combined_text = "\n".join(blocks)
        if len(combined_text) < len(regular_text):
            text = regular_text
        else:
            text = combined_text

        # 테이블 형식 인식을 위한 특수 패턴 전처리
        # 라인 헤더와 값이 표로 구성된 패턴을 인식하기 쉽게 변환
        text = re.sub(r'라\s*인\s*([A-Za-z0-9\-가-힣\s]+?)설비', '라인 | \\1 |\n설비', text)

        # 라인을 표현할 수 있는 다양한 형태를 처리
        # 예: "라 인" -> "라인"
        text = re.sub(r'라\s+인', '라인', text)

        # 설비번호 표현 정규화
        text = re.sub(r'설\s*비\s*번\s*호', '설비번호', text)

        # Clean up text
        text = re.sub(r'[\u200b\ufeff]', '', text)  # Remove zero-width spaces
        print("="*100)
        return text.strip()

    def _optimize_image(self, image: Image.Image, max_size=(400, 400)) -> Image.Image:
        """이미지 최적화 (리사이징 및 포맷 변환)"""
        try:
            # 이미지 크기 확인 및 리사이징
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.info(f"이미지 리사이징 완료: {image.size}")

            # RGBA를 RGB로 변환
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            return image
        except Exception as e:
            logger.error(f"이미지 최적화 중 오류 발생: {str(e)}")
            return image

    def extract_images_from_page(self, page: fitz.Page, page_num: int) -> List[Dict]:
        """PDF 페이지에서 이미지를 추출하고 저장합니다."""
        images = []
        image_list = page.get_images()

        for img_idx, img in enumerate(image_list, start=1):
            try:
                # 이미지 정보 추출
                xref = img[0]
                base_image = self.doc.extract_image(xref)

                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    filename = os.path.splitext(os.path.basename(self.doc.name))[0]

                    # 이미지 파일명 생성
                    image_filename = f"image_f{filename}_p{page_num}_i{img_idx}.{image_ext}"
                    image_path = os.path.join(self.image_dir, image_filename)

                    # PIL Image로 변환
                    image = Image.open(io.BytesIO(image_bytes))

                    # 이미지 최적화
                    optimized_image = self._optimize_image(image)

                    # 최적화된 이미지 저장
                    optimized_image.save(
                        image_path,
                        format="JPEG",
                        quality=85,
                        optimize=True
                    )

                    # 이미지 메타데이터 기록
                    image_info = {
                        "filename": image_filename,
                        "path": image_path,
                        "page": page_num,
                        "index": img_idx,
                        "size": optimized_image.size,
                        "format": "JPEG"
                    }

                    images.append(image_info)
                    logger.info(f"이미지 저장 완료: {image_filename} (크기: {optimized_image.size})")

            except Exception as e:
                logger.error(f"이미지 추출 중 오류 발생 (페이지 {page_num}, 이미지 {img_idx}): {str(e)}")
                continue

        return images

    def classify_work_type(self, text: str) -> str:
        """
        Classify work type based on content analysis.
        """
        for work_type, pattern in self.work_type_patterns.items():
            if re.search(pattern, text):
                return work_type
        return "기타"

    def extract_equipment_name(self, text: str) -> str:
        """
        Extract equipment name from text.
        """
        for equip_type, pattern in self.equipment_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Try to extract full equipment name with identifier
                full_name_match = re.search(f"{match.group(0)}[-\s]*[A-Z0-9#]+", text)
                if full_name_match:
                    return full_name_match.group(0)
                return match.group(0)
        return ""

    def parse_entry(self, text: str, images: List[Dict]) -> Dict:
        """
        Parse a single work log entry with improved accuracy.
        """
        entry = {}

        # 라인 정보 추출 로직 개선
        # 1. 표 형식 패턴
        table_patterns = [
            r'\|\s*라\s*인\s*\|\s*([A-Za-z0-9\-가-힣\s]+?)\s*\|',  # | 라 인 | CAM5N-5Line-1차 소성 |
            r'라\s*인\s*[:\|]\s*([A-Za-z0-9\-가-힣\s]+?)(?=\n|\|)',  # 라인: CAM5N-5Line-1차 소성
            r'라\s*인\s*\n+\s*([A-Za-z0-9\-가-힣\s]+?)(?=\n)'      # 라인\nCAM5N-5Line-1차 소성
        ]

        # 2. 직접적인 라인 패턴
        direct_patterns = [
            r'CAM\d[NW][-\s]?\d+Line[-\s]?[가-힣\d\s]+',  # CAM5N-5Line-1차 소성
            r'[A-Za-z0-9]+[-\s][가-힣\d\s]+차\s*소성',    # CAM5N-1차 소성
            r'\d+차\s*[가-힣]+',                         # 1차 소성
            r'[A-Za-z0-9\-]+Line[가-힣\d\s]+',          # 5Line-1차 소성
            r'CAM\d[NW][-\s]?\d+L[-\s]?[가-힣\d\s]+',   # CAM5N-4L-수세 패턴 추가
            r'[A-Za-z0-9\-]+L[가-힣\d\s]+'              # 4L-수세 패턴 추가
        ]

        # 3. 설비번호에서 라인 정보 추출
        equipment_line_pattern = r'EP-CAM(\d[NW])-\d{4}'

        # 라인 정보 추출 시도
        line_found = False

        # 1단계: 표 형식에서 추출
        for pattern in table_patterns:
            match = re.search(pattern, text)
            if match:
                entry["라인"] = match.group(1).strip()
                line_found = True
                break

        # 2단계: 직접적인 패턴에서 추출
        if not line_found:
            for pattern in direct_patterns:
                match = re.search(pattern, text)
                if match:
                    entry["라인"] = match.group(0).strip()
                    line_found = True
                    break

        # 3단계: 설비번호에서 라인 정보 추출
        if not line_found and "설비번호" in entry:
            match = re.search(equipment_line_pattern, entry["설비번호"])
            if match:
                cam_line = match.group(1)
                # 작업 내용에서 추가 정보 찾기
                if "작업 상세내용" in entry:
                    work_details = entry["작업 상세내용"]
                    # L 또는 Line 번호 찾기
                    line_match = re.search(r'(\d+)L|(\d+)\s*Line', work_details)
                    if line_match:
                        line_num = line_match.group(1) or line_match.group(2)
                        entry["라인"] = f"CAM{cam_line}-{line_num}Line"
                        line_found = True

        # 라인 정보를 찾지 못한 경우 로그 출력
        if not line_found:
            logger.warning(f"라인 정보를 찾을 수 없습니다. 텍스트 내용:\n{text[:300]}...")
            # 설비번호가 있는 경우 기본값 설정
            if "설비번호" in entry:
                match = re.search(equipment_line_pattern, entry["설비번호"])
                if match:
                    entry["라인"] = f"CAM{match.group(1)}"
                    logger.info(f"설비번호에서 기본 라인 정보 추출: {entry['라인']}")

        # Extract basic information using refined patterns
        other_patterns = {
            "설비번호": [
                r'설비\s*번호\s*[:\|]\s*(EP-CAM\d[NW]-\d{4})',
                r'\|\s*설비\s*번호\s*\|\s*(EP-CAM\d[NW]-\d{4})\s*\|',
                r'(EP-CAM\d[NW]-\d{4})'
            ],
            "작업 일자": [
                r'작업\s*일자\s*[:\|]\s*(\d{4}-\d{2}-\d{2})',
                r'\|\s*작업\s*일자\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|',
                r'(\d{4}-\d{2}-\d{2})'
            ],
            "작업 시작": [
                r'작업\s*시작\s*[:\|]\s*(\d{2}:\d{2})',
                r'\|\s*작업\s*시작\s*\|\s*(\d{2}:\d{2})\s*\|',
                r'(\d{2}:\d{2})'
            ],
            "담당자": [
                r'담당\s*자\s*[:\|]\s*([가-힣]{2,4})',
                r'\|\s*담\s*당\s*자\s*\|\s*([가-힣]{2,4})\s*\|',
                r'담당자[:\s]*([가-힣]{2,4})'
            ],
            "작업 상세내용": [
                r'작업\s*상세\s*내용[:\s]*([\s\S]+?)(?=\n\s*\n|\Z)',
                r'\|\s*작\s*업\s*명\s*\|\s*([\s\S]+?)(?=\n\s*\n|\||\Z)'
            ]
        }

        for field, patterns in other_patterns.items():
            if field not in entry or not entry[field]:
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        entry[field] = match.group(1).strip()
                        break

        # 설비 정보 정규화 (줄바꿈 제거)
        for field in ["설비번호", "작업 일자", "작업 시작"]:
            if field in entry and entry[field]:
                entry[field] = entry[field].split('\n')[0].strip()

        # Extract and clean up work details
        if "작업 상세내용" in entry:
            # Clean up work details
            work_details = entry["작업 상세내용"]
            work_details = re.sub(r'\s+', ' ', work_details)
            work_details = work_details.strip()
            entry["작업 상세내용"] = work_details

            # Classify work type
            entry["작업 종류"] = self.classify_work_type(work_details)

            # Extract equipment name
            entry["설비명"] = self.extract_equipment_name(work_details)

        # Add images if available
        if images:
            entry["작업사진"] = [img["filename"] for img in images]

        # 디버깅: 라인 정보가 없는 경우 로그 출력
        if "라인" not in entry or not entry["라인"]:
            logger.warning(f"라인 정보를 찾을 수 없습니다:\n{text[:300]}...")

        return entry

    def parse_entry_by_coordinates(self, page: fitz.Page, images: List[Dict]) -> Dict:
        """
        PDF 페이지의 텍스트 블록 좌표 기반으로 업무일지 항목을 파싱합니다.
        """
        entry = {}
        text_dict = page.get_text("dict")

        # 작업 상세내용 데이터를 위한 배열 초기화
        work_details_blocks = []

        # 블록 순회
        for block in text_dict["blocks"]:
            # 텍스트 블록이 아닌 경우 건너뛰기
            if "lines" not in block:
                continue

            # 블록의 바운딩 박스 좌표 추출
            bbox = block["bbox"]
            x0, y0, x1, y1 = bbox

            # 텍스트 추출
            block_text = ""
            for line in block["lines"]:
                for span in line["spans"]:
                    block_text += span["text"] + " "
            block_text = block_text.strip()

            if block_text == "":
                continue

            # y좌표가 30 이상 55 미만이면 문서 제목 또는 기준시간
            if 30 <= y0 < 55:
                if "일일업무일지" in block_text:
                    print(f"일일업무일지 제목 발견: {block_text}")
                if 160 <= x0 < 390:
                    entry["일지 기준시간"] = block_text
                # 텍스트 기반 로직 추가
                if "일지 기준시간" not in entry and "일지 기준시간" in block_text:
                    time_text = block_text.split("일지 기준시간")[-1].strip()
                    entry["일지 기준시간"] = time_text

            # y좌표가 55 이상 72 미만이면 라인, 작업 일자, 라인정지시간
            if 55 <= y0 < 72:
                if 105 <= x0 < 300:
                    entry["라인"] = block_text
                if 380 <= x0 < 500:
                    entry["작업 일자"] = block_text
                if x0 >= 500:
                    entry["라인정지시간"] = block_text + " 분"
                # 텍스트 기반 로직 추가
                if "라인" not in entry and "라 인" in block_text:
                    line_text = block_text.split("라 인")[-1].split("작업 일자")[0].strip()
                    entry["라인"] = line_text
                if "작업 일자" not in entry and "작업 일자" in block_text:
                    date_text = block_text.split("작업 일자")[-1].split("라인정지시간(분)")[0].strip()
                    entry["작업 일자"] = date_text
                if "라인정지시간" not in entry and "라인정지시간(분)" in block_text:
                    stop_time_text = block_text.split("라인정지시간(분)")[-1].strip()
                    entry["라인정지시간"] = stop_time_text

            # y좌표가 72 이상 86 미만이면 설비번호, 작업 시작, 담당자
            if 72 <= y0 < 86:
                if 100 <= x0 < 300:
                    entry["설비번호"] = block_text
                if 380 <= x0 < 500:
                    entry["작업 시작"] = block_text
                if x0 >= 570:
                    entry["담당자"] = block_text
                # 텍스트 기반 로직 추가
                if "설비번호" not in entry and "설비번호" in block_text:
                    equip_no_text = block_text.split("설비번호")[-1].split("작업 시작")[0].strip()
                    entry["설비번호"] = equip_no_text
                if "작업 시작" not in entry and "작업 시작" in block_text:
                    start_time_text = block_text.split("작업 시작")[-1].split("담 당 자")[0].strip()
                    entry["작업 시작"] = start_time_text
                if "담당자" not in entry and "담 당 자" in block_text:
                    person_text = block_text.split("담 당 자")[-1].strip()
                    entry["담당자"] = person_text

            # y좌표가 86 이상 101 미만이면 설비명, 작업 종료
            if 86 <= y0 < 101:
                if 100 <= x0 < 300:
                    entry["설비명"] = block_text
                if 380 <= x0 < 500:
                    entry["작업 종료"] = block_text
                # 텍스트 기반 로직 추가
                if "설비명" not in entry and "설 비 명" in block_text:
                    equip_name_text = block_text.split("설 비 명")[-1].split("작업 종료")[0].strip()
                    entry["설비명"] = equip_name_text
                if "작업 종료" not in entry and "작업 종료" in block_text:
                    end_time_text = block_text.split("작업 종료")[-1].strip()
                    entry["작업 종료"] = end_time_text

            # y좌표가 101 이상 120 미만이면 작업명
            if 101 <= y0 < 120:
                if x0 >= 100:
                    entry["작업명"] = block_text
                # 텍스트 기반 로직 추가
                if "작업명" not in entry and "작 업 명" in block_text:
                    work_name_text = block_text.split("작 업 명")[-1].strip()
                    entry["작업명"] = work_name_text

            # y좌표가 120 이상의 텍스트블록이면 작업 상세내용
            if 120 <= y0 and block_text != "작업 사진":
                # 텍스트 기반 로직 추가
                if "작업 상세내용" in block_text:
                    details_text = block_text.split("작업 상세내용")[-1].strip()
                    work_details_blocks.append(details_text)
                else:
                    work_details_blocks.append(block_text)

        # 작업 상세내용 병합
        if work_details_blocks:
            entry["작업 상세내용"] = "\n".join(work_details_blocks)

            # 작업 종류 분류
            entry["작업 종류"] = self.classify_work_type(entry["작업 상세내용"])

        return entry

    def _encode_image_to_base64(self, image: Image.Image) -> Optional[str]:
        """이미지를 base64로 인코딩"""
        try:
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=85, optimize=True)
            image_bytes = buffered.getvalue()

            # 이미지 크기 확인
            image_size = len(image_bytes)
            if image_size > 5 * 1024 * 1024:  # 5MB로 제한
                logger.warning(f"이미지 크기가 너무 큽니다: {image_size/1024/1024:.1f}MB")
                return None

            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"이미지 인코딩 중 오류 발생: {str(e)}")
            return None

    def generate_image_descriptions(self, images: List[Dict], entry: Dict) -> Dict:
        """이미지 설명을 생성합니다."""
        if not self._check_ollama_server():
            logger.error("Ollama 서버에 연결할 수 없습니다.")
            return {"error": "서버 연결 실패"}

        descriptions = {}

        # 작업 컨텍스트 준비 (간소화)
        context = {
            "설비": f"{entry.get('설비명', '')} ({entry.get('설비번호', '')})",
            "작업": f"{entry.get('작업 종류', '')} - {entry.get('작업명', '')}",
            "내용": entry.get('작업 상세내용', '')
        }

        for img in images:
            filename = img['filename']
            image_path = img['path']

            try:
                # 이미지 준비
                with Image.open(image_path) as image:
                    # 이미지 최적화 및 인코딩
                    optimized_image = self._optimize_image(image)
                    image_base64 = self._encode_image_to_base64(optimized_image)

                    if not image_base64:
                        logger.error(f"이미지 '{filename}' 인코딩 실패")
                        continue

                    # 프롬프트 준비 (gemma3:12b에 최적화)
                    prompt = f"""설비 유지보수 전문가로서 다음 이미지를 분석해주세요.

작업 정보:
- 설비: {context['설비']}
- 작업: {context['작업']}
- 내용: {context['내용']}

분석 요청 사항:
1. 설비 상태: 현재 상태와 이상 징후
2. 수행된 작업: 작업 종류와 결과
3. 특이사항: 주목할만한 사항

이미지를 기반으로 위 항목들을 간단히 설명해주세요."""

                    # API 요청 데이터 준비 (gemma3:12b-it-qat 설정)
                    request_data = {
                        "model": "gemma3:4b-it-qat",
                        "prompt": prompt,
                        "stream": False,
                        "images": [image_base64],
                        "options": {
                            "temperature": 0.3,
                            "num_ctx": 131072,  # 128k 컨텍스트
                            # "num_predict": 512  # 응답 길이 제한
                        }
                    }

                    # API 호출 및 재시도 로직
                    max_retries = 3
                    base_timeout = 100  # 타임아웃 100초로 증가

                    for retry in range(max_retries):
                        try:
                            current_timeout = min(base_timeout * (1.5 ** retry), 100)  # 최대 100초

                            logger.info(f"이미지 '{filename}' 분석 시도 중 (시도: {retry+1}/{max_retries}, 타임아웃: {current_timeout:.1f}초)")

                            # 서버 상태 확인
                            if not self._check_ollama_server():
                                logger.warning("Ollama 서버 연결 실패, 재시도 중...")
                                time.sleep(3)  # 서버 복구 대기 시간
                                continue

                            start_time = time.time()
                            response = requests.post(
                                f"{self.ollama_url}/api/generate",
                                json=request_data,
                                timeout=current_timeout
                            )
                            process_time = time.time() - start_time

                            if response.status_code == 200:
                                result = response.json()
                                if "response" in result:
                                    description = result["response"].strip()
                                    if len(description) > 30:  # 최소 길이 확인
                                        descriptions[filename] = description
                                        logger.info(f"이미지 '{filename}' 분석 성공 (처리 시간: {process_time:.1f}초)")
                                        break
                                    else:
                                        logger.warning(f"생성된 설명이 너무 짧습니다 ({len(description)} 글자)")
                                else:
                                    logger.warning("API 응답에 'response' 필드가 없습니다.")
                            else:
                                error_msg = f"API 호출 실패 (상태 코드: {response.status_code})"
                                try:
                                    error_details = response.json()
                                    error_msg += f"\n상세 오류: {error_details}"
                                except:
                                    pass
                                logger.warning(error_msg)

                            if retry < max_retries - 1:
                                wait_time = min(2 ** retry * 3, 15)  # 재시도 간격 감소, 최대 15초
                                logger.info(f"다음 시도까지 {wait_time}초 대기...")
                                time.sleep(wait_time)

                        except requests.exceptions.Timeout:
                            logger.warning(f"API 타임아웃 발생 ({current_timeout:.1f}초)")
                            if retry < max_retries - 1:
                                wait_time = min(2 ** retry * 3, 15)
                                logger.info(f"다음 시도까지 {wait_time}초 대기...")
                                time.sleep(wait_time)
                            continue
                        except Exception as e:
                            logger.warning(f"API 요청 예외 발생: {str(e)}")
                            if retry < max_retries - 1:
                                wait_time = min(2 ** retry * 3, 15)
                                logger.info(f"다음 시도까지 {wait_time}초 대기...")
                                time.sleep(wait_time)
                            continue

            except Exception as e:
                logger.error(f"이미지 '{filename}' 처리 중 오류 발생: {str(e)}")
                continue

            if filename not in descriptions:
                descriptions[filename] = "이미지 분석 실패"
                logger.error(f"이미지 '{filename}' 분석 최종 실패")

        return descriptions

    def _check_ollama_server(self) -> bool:
        """Ollama 서버 상태를 확인하고 재시도하는 함수"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    return True
                elif attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
        return False

    def convert(self) -> List[Dict]:
        """
        Convert PDF to JSON with improved coordinate-based parsing logic.
        """
        try:
            all_entries = []
            current_entry = None
            current_entry_images = []

            # PDF 처리
            for page_num in range(len(self.doc)):
                try:
                    page = self.doc[page_num]
                    text_dict = page.get_text("dict")
                    images = self.extract_images_from_page(page, page_num + 1)

                    # 현재 페이지에 "일일업무일지" 텍스트가 있는지 확인
                    has_daily_log_title = False

                    for block in text_dict["blocks"]:
                        if "lines" not in block:
                            continue

                        bbox = block["bbox"]
                        x0, y0, x1, y1 = bbox

                        # y좌표가 30 이상 55 미만인 블록만 확인
                        if 30 <= y0 < 55:
                            block_text = ""
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    block_text += span["text"] + " "
                            block_text = block_text.strip()

                            if "일일업무일지" in block_text:
                                # 새로운 업무일지 entry 시작
                                has_daily_log_title = True

                                # 이전 entry가 있으면 마무리 작업 후 목록에 추가
                                if current_entry is not None and current_entry:
                                    # 이미지 설명 생성
                                    if self.use_image_description:
                                        if current_entry_images:
                                            current_entry["이미지설명"] = self.generate_image_descriptions(current_entry_images, current_entry)
                                    # 현재 entry를 목록에 추가
                                    all_entries.append(current_entry)
                                    # 현재 entry 초기화
                                    current_entry = None
                                    current_entry_images = []

                                # 새 entry 생성
                                current_entry = self.parse_entry_by_coordinates(page, images)
                                logger.info(f"새 업무일지 항목 시작 (페이지 {page_num + 1})")
                                break

                    # "일일업무일지" 제목이 없는 경우
                    if not has_daily_log_title:
                        # 이미지만 있는 페이지인지 확인
                        if images and current_entry is not None:
                            # 현재 entry에 이미지 추가
                            if "작업사진" not in current_entry:
                                current_entry["작업사진"] = []

                            for img in images:
                                current_entry["작업사진"].append(img["filename"])
                                current_entry_images.append(img)

                            logger.info(f"기존 업무일지에 이미지 추가 (페이지 {page_num + 1}, 이미지 {len(images)}개)")
                        else:
                            # 이미지도 없고 "일일업무일지" 제목도 없으면 현재 entry 완료
                            if current_entry is not None and current_entry:
                                # 이미지 설명 생성
                                if self.use_image_description:
                                    if current_entry_images:
                                        current_entry["이미지설명"] = self.generate_image_descriptions(current_entry_images, current_entry)
                                # 현재 entry를 목록에 추가
                                all_entries.append(current_entry)
                                # 현재 entry 초기화
                                current_entry = None
                                current_entry_images = []

                                logger.info(f"업무일지 항목 완료 (페이지 {page_num + 1})")
                    else:
                        # "일일업무일지" 제목이 있고 이미지가 있는 경우
                        if images and current_entry is not None:
                            # 현재 entry에 이미지 추가
                            if "작업사진" not in current_entry:
                                current_entry["작업사진"] = []

                            for img in images:
                                current_entry["작업사진"].append(img["filename"])
                                current_entry_images.append(img)

                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                    continue

            # 마지막 entry 추가
            if current_entry is not None and current_entry:
                all_entries.append(current_entry)

            # Create output JSON
            # output = {
            #     "metadata": {
            #         "source_file": os.path.basename(self.pdf_path),
            #         "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            #         "entries_count": len(all_entries),
            #         "image_directory": "images"
            #     },
            #     "entries": all_entries
            # }

            logger.info(f"Total entries extracted from {os.path.basename(self.pdf_path)}: {len(all_entries)}")
            logger.info(f"Total images extracted: {sum(len(entry.get('작업사진', [])) for entry in all_entries)}")

            return all_entries  # 파싱된 entries 리스트 반환

        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            raise
        finally:
            # Close the PDF document and release resources
            if hasattr(self, 'doc'):
                try:
                    self.doc.close()
                except:
                    pass

def process_all_pdfs(directory_path, output_dir, image_dir, use_image_description=True):
    """
    Process all PDF files in the specified directory
    """
    # Ensure all directories exist
    for dir_path in [directory_path, output_dir, image_dir]:
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Directory confirmed: {dir_path}")
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {str(e)}")
            raise

    # Find all PDF files in the directory
    pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")

    all_entries = [] # 모든 PDF의 파싱 결과를 저장할 리스트
    processed_files_count = 0
    final_output_path = None # 최종적으로 성공한 파일 경로
    output_path = os.path.join(output_dir, "일일업무일지.json") # 출력 파일 경로 고정

    # Process each PDF file
    for pdf_file in pdf_files:
        converter = None # 루프 시작 시 초기화
        try:
            logger.info(f"Starting processing of {pdf_file}")

            # PDF 파일 접근성 확인 (선택 사항, 이미 converter에서 처리할 수 있음)
            # try:
            #     with open(pdf_file, 'rb') as f:
            #         pass
            # except IOError as e:
            #     logger.error(f"Cannot access PDF file {pdf_file}: {str(e)}")
            #     continue

            converter = PDFConverter(pdf_file, output_dir, image_dir, use_image_description)
            entries = converter.convert() # 파싱 결과 (entries 리스트) 반환 받음

            if entries is not None:
                all_entries.extend(entries) # 전체 리스트에 추가
                processed_files_count += 1
                logger.info(f"Successfully processed {pdf_file}, added {len(entries)} entries. Current total: {len(all_entries)}")

                # 현재까지 누적된 데이터로 JSON 파일 즉시 저장 (덮어쓰기)
                current_output_data = {
                    "metadata": {
                        "source_directory": os.path.relpath(directory_path),
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "total_entries": len(all_entries),
                        "processed_files": processed_files_count,
                        "image_directory": "images"
                    },
                    "entries": all_entries
                }

                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(current_output_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"Successfully updated {output_path}. Total entries: {len(all_entries)}")
                    final_output_path = output_path # 마지막 성공 경로 업데이트
                except IOError as e:
                    logger.error(f"Error writing to {output_path} after processing {pdf_file}: {str(e)}")
                    # 쓰기 오류 발생 시 해당 파일 처리는 실패로 간주하고 다음 파일 진행
            else:
                logger.warning(f"Conversion returned no entries for {pdf_file}. Skipping update.")

        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}")
            continue # 에러 발생 시 다음 파일로 넘어감
        finally:
            # PDF 문서 닫기 및 메모리 정리
            if converter is not None and hasattr(converter, 'doc'):
                try:
                    converter.doc.close()
                except Exception as close_err:
                    logger.warning(f"Error closing PDF document {pdf_file}: {close_err}")
            gc.collect()

    # 최종적으로 성공적으로 저장된 파일 경로 반환
    if final_output_path:
        logger.info(f"Finished processing all PDFs. Final data saved to {final_output_path}")
    else:
        logger.warning("No PDF files were processed successfully or no data was saved.")

    return final_output_path # 저장 성공 시 경로, 아니면 None 반환

def main():
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir) if script_dir.endswith('scripts') else script_dir

    pdf_directory = os.path.join(workspace_dir, "업무일지")
    output_dir = os.path.join(workspace_dir, "output")
    image_dir = os.path.join(output_dir, "images")

    # 해당 디렉토리가 없으면 생성
    os.makedirs(pdf_directory, exist_ok=True)

    # Process all PDF files in the directory
    use_image_description = False  # Set to False to disable image description generation
    final_output_file = process_all_pdfs(pdf_directory, output_dir, image_dir, use_image_description)

    # Print summary
    if final_output_file:
        logger.info(f"Conversion complete. Final consolidated data saved to {final_output_file}")
        logger.info(f"Images saved to {image_dir}")
    else:
        logger.error("JSON file generation failed or no PDFs were processed.")

if __name__ == "__main__":
    main()