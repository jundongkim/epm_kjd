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
import base64
import requests  # Ollama API 호출용
import time
from dotenv import load_dotenv
import subprocess
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

    def ensure_directories(self):
        """Create output and image directories if they don't exist"""
        # 출력 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)
        # 이미지 디렉토리 생성
        os.makedirs(self.image_dir, exist_ok=True)
        # 이미지 디렉토리 하위에 파일별 이미지 저장 디렉토리 생성
        file_name = os.path.basename(self.pdf_path)
        os.makedirs(os.path.join(self.image_dir, os.path.splitext(file_name)[0]), exist_ok=True)

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

        # Clean up text
        text = re.sub(r'[\u200b\ufeff]', '', text)  # Remove zero-width spaces
        return text.strip()

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

    def _optimize_image(self, image: Image.Image, max_size=(800, 800)) -> Image.Image:
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

    def _is_useful_image(self, image: Image.Image, image_rect=None, page_size=None) -> bool:
        """주요 이미지인지 판단하는 함수 (로고, 선, 배경 등 제외)"""
        try:
            # 1. 이미지 크기 확인: 너무 작은 이미지는 제외 (로고, 아이콘 등)
            width, height = image.size
            image_area = width * height

            # 너무 작은 이미지 제외 (50x50 미만)
            if width < 50 or height < 50:
                logger.debug(f"이미지가 너무 작습니다: {width}x{height}. 제외합니다.")
                return False

            # 2. 이미지 종횡비 확인: 극단적인 비율은 라인일 가능성 높음
            aspect_ratio = width / max(height, 1)  # 0으로 나누기 방지
            if aspect_ratio > 10 or aspect_ratio < 0.1:
                logger.debug(f"이미지 종횡비가 극단적입니다: {aspect_ratio}. 제외합니다.")
                return False

            # 3. 로고 이미지 특성 기반 필터링 (OCR 대체 방법)
            # 3.1. 일반적인 로고 크기 범위 확인 (통계적 접근)
            # 로고는 주로 넓고 높이가 낮은 직사각형 형태 (가로형 로고)
            is_logo_sized = (70 < height < 100 and 300 < width < 400) or (width > height * 3 and height < 100)

            # 3.2. 이미지가 페이지 상단에 위치하는지 확인 (일반적인 로고 위치)
            is_in_header_position = False
            if image_rect:
                x0, y0, x1, y1 = image_rect
                if y0 < 100:  # 페이지 상단 부분에 위치
                    is_in_header_position = True

            # 4. 페이지 위치 정보가 있는 경우 헤더/푸터 영역 확인
            if image_rect and page_size:
                x0, y0, x1, y1 = image_rect
                page_width, page_height = page_size

                # 페이지 상단 20% 또는 하단 20% 영역에 있는 이미지는
                # 헤더/푸터 요소(로고 등)일 가능성 높음
                header_zone = page_height * 0.2
                footer_zone = page_height * 0.8

                # 이미지의 중심점
                image_center_y = (y0 + y1) / 2

                if image_center_y < header_zone or image_center_y > footer_zone:
                    # 헤더/푸터 영역의 작은 이미지는 로고일 가능성 높음
                    if image_area < (page_width * page_height * 0.05):  # 페이지 면적의 5% 미만
                        logger.debug(f"헤더/푸터 영역의 작은 이미지입니다. 제외합니다.")
                        return False

            # 모든 필터를 통과한 이미지는 유용한 이미지로 간주
            return True

        except Exception as e:
            logger.warning(f"이미지 유용성 확인 중 오류 발생: {str(e)}")
            # 오류 발생 시 일단 포함 (제외하지 않음)
            return True

    def extract_images_from_page(self, page: fitz.Page, page_num: int) -> List[Dict]:
        """PDF 페이지에서 이미지를 추출하고 저장합니다."""
        images = []
        image_list = page.get_images()
        page_width, page_height = page.rect.width, page.rect.height
        page_size = (page_width, page_height)

        for img_idx, img in enumerate(image_list, start=1):
            try:
                # 이미지 정보 추출
                xref = img[0]
                base_image = self.doc.extract_image(xref)

                # 이미지 위치 정보 추출 (가능한 경우)
                image_rect = None
                try:
                    for item in page.get_drawings():
                        if item.get('xref') == xref:
                            image_rect = item.get('rect')
                            break
                except:
                    pass  # 위치 정보 추출 실패 시 무시

                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    filename = os.path.splitext(os.path.basename(self.doc.name))[0]

                    # PIL Image로 변환
                    image = Image.open(io.BytesIO(image_bytes))

                    # 유용한 이미지인지 확인
                    if not self._is_useful_image(image, image_rect, page_size):
                        logger.info(f"불필요한 이미지로 판단되어 제외합니다: 페이지 {page_num}, 이미지 {img_idx}")
                        continue

                    # 이미지 파일명 생성
                    image_filename = f"image_f{filename}_p{page_num}_i{img_idx}.{image_ext}"
                    image_path = os.path.join(self.image_dir, image_filename)

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

        logger.info(f"페이지 {page_num}에서 {len(images)}/{len(image_list)} 개의 유용한 이미지 추출 완료")
        return images

    def convert_page_to_image(self, page: fitz.Page) -> str:
        """
        Convert a PDF page to an image and save it.
        """
        actual_page_num = page.number + 1  # 페이지 번호는 1부터 시작
        pdf_filename = os.path.splitext(os.path.basename(self.pdf_path))[0]
        image_filename = f"{pdf_filename}_page_{actual_page_num:02d}.png"
        image_path = os.path.join(self.image_dir, pdf_filename, image_filename)
        # 페이지를 이미지로 추출
        pix = page.get_pixmap(dpi=300)
        # 이미지 저장
        pix.save(image_path)
        logger.info(f"{pdf_filename} 파일 페이지 {actual_page_num} 이미지를 저장했습니다: {image_path}")
        return image_path

    def generate_page_description(self, page_entry: dict, model: str = "gemma3:4b-it-qat") -> dict:
        """
        Generate a summary of a page using Ollama API.
        """
        # Ollama 서버 연결 확인
        if not self._check_ollama_server():
            logger.error("Ollama 서버에 연결할 수 없습니다.")
            return "서버 연결 실패"

        # 이미지 준비
        try:
            image_path = page_entry["image_path"]
            with Image.open(image_path) as image:
                # 이미지 최적화 및 인코딩
                optimized_image = self._optimize_image(image)
                image_base64 = self._encode_image_to_base64(optimized_image)

                if not image_base64:
                    logger.error(f"이미지 '{image_path}' 인코딩 실패")
        except Exception as e:
                logger.error(f"이미지 '{image_path}' 처리 중 오류 발생: {str(e)}")
                return {
                    "title": "이미지 처리 오류 발생",
                    "summary": str(e)
                }

        # 프롬프트 준비
        prompt = f"""당신의 업무는 배터리 양극재 생산 공정 중 발생한 이슈에 대한 보고서의 내용을 요약하는 것입니다.
        보고서의 한 페이지의 내용이 주어지면, 그 페이지의 내용을 요약해주세요. 첨부한 이미지는 해당 페이지의 이미지입니다.

        ### 페이지 내용 텍스트 ###
        <page_content>
        {page_entry["content"]}
        </page_content>

        ---

        다음과 같은 JSON 형식으로 요약해주세요:
        <summary_format>
        {{
            "title": [페이지 좌상단의 제목],
            "summary": [페이지 내용 요약]
        }}
        </summary_format>
        """

        # API 요청 데이터 준비
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "images": [image_base64],
            "options": {
                "temperature": 0.3,
                "num_ctx": 131072,  # 128k 컨텍스트
            }
        }

        # API 요청
        try:
            logger.info(f"페이지 설명 생성중: {page_entry['image_path']}")
            response = requests.post(f"{self.ollama_url}/api/generate", json=request_data)
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    # JSON 형식으로 파싱
                    result_str = result["response"].strip()
                    try:
                        # ```으로 감싸진 부분 추출
                        json_str = re.search(r'```json(.*?)```', result_str, re.DOTALL)
                        if json_str:
                            json_str = json_str.group(1).strip()
                            # JSON 파싱
                            summary = json.loads(json_str)
                            title = summary.get("title", "제목 없음")
                            summary_text = summary.get("summary", "요약 없음")
                            logger.info(f"페이지 설명 생성완료: {page_entry['image_path']}")
                            return {"title": title, "summary": summary_text}
                        else:
                            logger.warning("JSON 형식이 아닙니다.")
                            return {"title": "JSON 형식 오류", "summary": result_str}
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 파싱 오류: {str(e)}")
                        return {"title": "JSON 파싱 오류", "summary": result_str}
                else:
                    logger.warning("API 응답에 'response' 필드가 없습니다.")
                    return {"title": "요약 생성 실패", "summary": "API 응답에 'response' 필드가 없습니다."}
            else:
                logger.warning(f"API 호출 실패 (상태 코드: {response.status_code})")
                return {"title": "API 호출 실패", "summary": f"API 호출 실패 (상태 코드: {response.status_code})"}
        except RequestException as e:
            logger.error(f"API 요청 중 오류 발생: {str(e)}")
            return {"title": "요청 오류 발생", "summary": str(e)}

    def generate_file_summary(self, file_entry: dict, model: str = "gemma3:4b-it-qat") -> dict:
        """
        Generate a summary of the file entry using Ollama API.
        """
        if not self._check_ollama_server():
            logger.error("Ollama 서버에 연결할 수 없습니다.")
            return "서버 연결 실패"

        # 페이지를 순회하면서 요약 내용 취합
        pages = file_entry.get("pages", [])
        page_summaries = []
        for page in pages:
            page_title = page.get("title", "")
            page_summary = page.get("summary", "")
            page_summaries.append({
                "title": page_title,
                "summary": page_summary
            })

        # 프롬프트 준비
        prompt = f"""당신의 업무는 배터리 양극재 생산 공정 중 발생한 이슈에 대한 보고서의 내용을 요약하는 것입니다.
        주어진 보고서 파일 각 페이지의 요약 내용을 참고하여 보고서의 내용을 요약해주세요.

        ### 각 페이지의 요약 ###
        ```
        <page_summaries>
        {json.dumps(page_summaries, ensure_ascii=False, indent=2)}
        </page_summaries>
        ```

        ### 요약 형식 ###
        ```
        <summary_format>
        #### 현황
        [현황 내용]

        #### 원인
        [원인 내용]

        #### 조치사항 및 재발 방지 대책
        [조치사항 혹은 재발 방지 대책 내용]
        </summary_format>
        ```
        """

        # API 요청 데이터 준비
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 131072,  # 128k 컨텍스트
            }
        }

        # API 요청
        summary_obj = {
            "full_text": "",
            "situation": "",
            "cause": "",
            "action": ""
        }
        try:
            logger.info(f"파일 내용 요약 생성중: {file_entry['file_name']}")
            response = requests.post(f"{self.ollama_url}/api/generate", json=request_data)
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    logger.info(f"파일 내용 요약 생성완료: {file_entry['file_name']}")
                    full_text = result["response"].strip()
                    summary_obj["full_text"] = full_text
                    # 현황, 원인, 조치사항 및 재발 방지 대책 추출
                    match = re.search(r'#### 현황\n([\S\s\n]+?)\n#### 원인\n([\S\s\n]+?)\n#### 조치사항 및 재발 방지 대책\n([\S\s\n]*)', full_text)
                    if match:
                        summary_obj["situation"] = match.group(1).strip()
                        summary_obj["cause"] = match.group(2).strip()
                        summary_obj["action"] = match.group(3).strip()
                    return summary_obj
                else:
                    logger.warning("API 응답에 'response' 필드가 없습니다.")
                    summary_obj["full_text"] = "요약 생성 실패"
                    return summary_obj
            else:
                logger.warning(f"API 호출 실패 (상태 코드: {response.status_code})")
                summary_obj["full_text"] = "API 호출 실패"
                return summary_obj
        except RequestException as e:
            logger.error(f"API 요청 중 오류 발생: {str(e)}")
            summary_obj["full_text"] = "요청 오류 발생"
            return summary_obj

    def generate_file_metadata(self, file_entry: dict, model: str = "gemma3:4b-it-qat") -> dict:
        """
        Generate a metadata of the file entry using Ollama API.
        """
        if not self._check_ollama_server():
            logger.error("Ollama 서버에 연결할 수 없습니다.")
            return "서버 연결 실패"

        # 파일 내용 취합
        file_title = file_entry.get("title", "제목 없음")
        file_summary = file_entry.get("summary", {"full_text": "요약 없음"}).get("full_text", "요약 없음")

        pages = file_entry.get("pages", [])
        page_contents = []
        for page in pages:
            page_number = page.get("page_number", "정보 없음")
            page_title = page.get("title", "제목 없음")
            page_summary = page.get("summary", "요약 없음")
            page_content = f"""## {page_number} 페이지
            ### 제목: {page_title}
            ### 요약: {page_summary}
            """
            page_contents.append(page_content)

        page_contents_str = "\n\n".join(page_contents)
        file_content = f"""# 제목: {file_title}

        # 파일 내용 요약
        {file_summary}

        # 페이지 요약
        {page_contents_str}
        """

        # 프롬프트 준비
        prompt = f"""당신의 업무는 배터리 양극재 생산 공정 중 발생한 이슈에 대한 보고서의 내용을 정리하는 것입니다.
        주어진 보고서 요약 내용을 참고하여 해당 보고서의 메타데이터를 추출해주세요.
        추출해야 할 메타데이터는 보고서의 '대상 공정 라인', '대상 설비', '발생 이슈' 입니다.

        ### 보고서 내용 ###
        ```
        <file_content>
        {file_content}
        </file_content>
        ```

        ### 메타데이터 형식 ###
        ```
        <metadata_format>
        아래와 같은 JSON 형식으로 추출해주세요:
        {{
            "lines": [대상 공정 라인 리스트],
            "equipments": [대상 설비 리스트],
            "issues": [발생 이슈 리스트],
        }}
        </metadata_format>
        ```
        """

        # API 요청 데이터 준비
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        # API 요청
        try:
            logger.info(f"파일 메타데이터 추출중: {file_entry['file_name']}")
            response = requests.post(f"{self.ollama_url}/api/generate", json=request_data)
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    # JSON 형식으로 파싱
                    result_str = result["response"].strip()
                    try:
                        # ```으로 감싸진 부분 추출
                        json_str = re.search(r'```json(.*?)```', result_str, re.DOTALL)
                        if json_str:
                            json_str = json_str.group(1).strip()
                            # JSON 파싱
                            metadata = json.loads(json_str)
                            lines = metadata.get("lines", ["대상 라인 정보 없음"])
                            equipments = metadata.get("equipments", ["대상 설비 정보 없음"])
                            issues = metadata.get("issues", ["발생 이슈 정보 없음"])
                            logger.info(f"파일 메타데이터 추출완료: {file_entry['file_name']}")
                            return {"lines": lines, "equipments": equipments, "issues": issues}
                        else:
                            logger.warning("JSON 형식이 아닙니다.")
                            return {"lines": "JSON 형식 오류", "equipments": "JSON 형식 오류", "issues": "JSON 형식 오류"}
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 파싱 오류: {str(e)}")
                        return {"lines": "JSON 파싱 오류", "equipments": "JSON 파싱 오류", "issues": "JSON 파싱 오류"}
                else:
                    logger.warning("API 응답에 'response' 필드가 없습니다.")
                    return {"lines": "API 응답 오류", "equipments": "API 응답 오류", "issues": "API 응답 오류"}
            else:
                logger.warning(f"API 호출 실패 (상태 코드: {response.status_code})")
                return {"lines": "API 호출 실패", "equipments": "API 호출 실패", "issues": "API 호출 실패"}
        except RequestException as e:
            logger.error(f"API 요청 중 오류 발생: {str(e)}")
            return {"lines": "요청 오류 발생", "equipments": "요청 오류 발생", "issues": "요청 오류 발생"}


    def parse_page(self, page: fitz.Page) -> Dict:
        """
        PDF 페이지의 내용을 파싱합니다.
        """
        # 페이지 entry 객체 초기화
        entry = {}

        # 페이지 번호
        entry["page_number"] = page.number + 1

        # 페이지를 이미지로 변환하여 저장
        page_image_path = self.convert_page_to_image(page)
        entry["image_path"] = os.path.relpath(page_image_path)

        # 페이지 텍스트 추출
        # ----- 단순 추출 -----
        page_text = page.get_text("text")
        # ----- 텍스트 블록 기반 추출 -----
        # page_text = ""
        # text_dict = page.get_text("dict")
        # for block in text_dict["blocks"]:
        #     # 텍스트 블록이 아닌 경우 건너뛰기
        #     if "lines" not in block:
        #         continue
        #     # 텍스트 추출
        #     block_text = ""
        #     for line in block["lines"]:
        #         for span in line["spans"]:
        #             block_text += span["text"] + " "
        #     page_text += block_text + "\n"
        entry["content"] = page_text.strip()

        return entry

    def convert(self) -> List[Dict]:
        """
        Convert PDF to JSON with improved coordinate-based parsing logic.
        """
        try:
            # 모델 선택
            model = "gemma3:12b-it-qat"
            # model = "gemma3:4b-it-qat"

            file_name = os.path.basename(self.pdf_path)

            # 각 페이지별 entry 저장 리스트
            page_entries = []

            # 파일 전체에 대한 entry
            file_entry = {
                "file_name": file_name,
                "file_path": os.path.relpath(self.pdf_path),
                "date": "",
                "title": "",
                "pages": page_entries,
                "summary": "",
                "lines": [],
                "equipments": [],
                "issues": []
            }

            # # 파일명에서 날짜 정보 추출
            # date_match = re.search(r'(\d{6})', file_name)
            # if date_match:
            #     date_str = date_match.group(0)
            #     # 날짜 형식 변환 (YYMMDD -> YYYY-MM-DD)
            #     year = int(date_str[:2])
            #     month = int(date_str[2:4])
            #     day = int(date_str[4:6])
            #     # 2000년대로 가정
            #     year += 2000
            #     file_entry["date"] = f"{year}-{month:02d}-{day:02d}"
            #     logger.info(f"파일명에서 날짜 정보 추출: {file_entry['date']}")

            # 파일명에서 날짜 정보 추출
            date_match = re.search(r'(\d{8})', file_name)
            if date_match:
                date_str = date_match.group(0)
                # 날짜 형식 변환 (YYYYMMDD -> YYYY-MM-DD)
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                file_entry["date"] = f"{year}-{month:02d}-{day:02d}"
                logger.info(f"파일명에서 날짜 정보 추출: {file_entry['date']}")

            # 각 페이지 처리
            for page_num in range(len(self.doc)):
                try:
                    page = self.doc[page_num]

                    # 현재 페이지 처리
                    current_page_entry = self.parse_page(page)

                    # 페이지에서 추출된 정보가 있는 경우
                    if current_page_entry:
                        if self.use_image_description:
                            # 페이지 제목 추출, 페이지 요약 생성
                            current_page_description = self.generate_page_description(current_page_entry, model)
                            current_page_entry["title"] = current_page_description["title"]
                            current_page_entry["summary"] = current_page_description["summary"]
                            # 첫 페이지인 경우 페이지 제목을 파일의 제목으로 설정
                            if page_num == 0:
                                file_entry["title"] = current_page_description["title"]

                        # 페이지 엔트리 추가
                        page_entries.append(current_page_entry)
                        logger.info(f"엔트리 생성: {current_page_entry.get('title', '무제')}")

                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                    continue

            file_entry["pages"] = page_entries

            # 파일 내용 요약 생성
            if self.use_image_description:
                file_summary = self.generate_file_summary(file_entry, model)
                file_entry["summary"] = file_summary

            # 파일 메타데이터 생성
            if self.use_image_description:
                file_metadata = self.generate_file_metadata(file_entry, model)
                file_entry["lines"] = file_metadata.get("lines", ["대상 라인 정보 없음"])
                file_entry["equipments"] = file_metadata.get("equipments", ["대상 설비 정보 없음"])
                file_entry["issues"] = file_metadata.get("issues", ["발생 이슈 정보 없음"])

            logger.info(f"Total pages extracted from {os.path.basename(self.pdf_path)}: {len(page_entries)}")

            return file_entry  # 파싱된 file_entry 반환

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
        converter = None # 각 루프 시작 시 초기화
        try:
            logger.info(f"Starting processing of {pdf_file}")

            converter = PDFConverter(pdf_file, output_dir, image_dir, use_image_description)
            file_entry = converter.convert() # 파싱 결과 (현재 파일의 entry) 반환 받음

            if file_entry is not None:
                all_entries.append(file_entry) # 전체 리스트에 추가
                processed_files_count += 1
                logger.info(f"Successfully processed {pdf_file}, added {len(file_entry['pages'])} entries. Current total: {len(all_entries)}")

                # 현재까지 누적된 데이터로 JSON 파일 즉시 저장 (덮어쓰기)
                current_output_data = {
                    "metadata": {
                        "source_directory": os.path.relpath(directory_path),
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "total_entries": len(all_entries),
                        "processed_files": processed_files_count,
                        "image_directory": os.path.relpath(image_dir)
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.split(base_dir)[0]
    # 코드베이스 루트 경로로 디렉토리 커서 이동
    os.chdir(root_dir)

    # 업무일지 디렉토리 설정 - PRD 폴더 내부의 업무일지 폴더
    pdf_directory = os.path.join(base_dir, "업무일지")
    output_dir = os.path.join(base_dir, "output")
    image_dir = os.path.join(output_dir, "images")

    # 로그에 경로 출력
    logger.info(f"cwd: {os.getcwd()}")
    logger.info(f"PDF 디렉토리: {pdf_directory}")
    logger.info(f"출력 디렉토리: {output_dir}")
    logger.info(f"이미지 디렉토리: {image_dir}")

    # 해당 디렉토리가 없으면 생성
    os.makedirs(pdf_directory, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    # Process all PDF files in the directory
    use_image_description = True  # Set to False to disable image description generation
    final_output_file = process_all_pdfs(pdf_directory, output_dir, image_dir, use_image_description)

    # Print summary
    if final_output_file:
        logger.info(f"Conversion complete. Final consolidated data saved to {final_output_file}")
        logger.info(f"Images saved to {image_dir}")
    else:
        logger.error("JSON file generation failed or no PDFs were processed.")

if __name__ == "__main__":
    main()