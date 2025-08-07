import os
import json
import re
import glob
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
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

# Target keys for extraction
TARGET_KEYS = [
    "작성일자",
    "YE Part - CAM5 1 Line - 변경점 및 TEST 진행 현황",
    "YE Part - CAM5 1 Line - 비고 (품질 특이사항 등)",
    "YE Part - CAM5 2 Line - 변경점 및 TEST 진행 현황",
    "YE Part - CAM5 2 Line - 비고 (품질 특이사항 등)",
    "YE Part - CAM5 3 Line - 변경점 및 TEST 진행 현황",
    "YE Part - CAM5 3 Line - 비고 (품질 특이사항 등)",
    "YE Part - CAM5N 4 Line - 변경점 및 TEST 진행 현황",
    "YE Part - CAM5N 4 Line - 비고 (품질 특이사항 등)",
    "YE Part - CAM5N 5 Line - 변경점 및 TEST 진행 현황",
    "YE Part - CAM5N 5 Line - 비고 (품질 특이사항 등)",
    "요소기술 Part - Part 통합 - TEST 진행 현황 및 신공법 검토"
]

class PDFConverter:
    def __init__(self, pdf_path: str, output_dir: str, image_dir: str = None,
                 use_image_description: bool = False, use_ollama_processing: bool = False):
        """Initialize the converter with the PDF path and output directories."""
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.image_dir = image_dir or os.path.join(output_dir, "images")
        self.use_image_description = use_image_description
        self.use_ollama_processing = use_ollama_processing

        # Ollama 서버 URL 및 모델 설정
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = "gemma3:12b-it-qat"  # 기본 모델 설정
        logger.info(f"Using Ollama model: {self.ollama_model} at {self.ollama_url}")

        # 이미지 설명 캐싱 추가
        self.image_description_cache = {}

        # Define target sections to extract
        self.target_keys = [
            "작성일자",
            "YE Part - CAM5 1 Line - 변경점 및 TEST 진행 현황",
            "YE Part - CAM5 1 Line - 비고 (품질 특이사항 등)",
            "YE Part - CAM5 2 Line - 변경점 및 TEST 진행 현황",
            "YE Part - CAM5 2 Line - 비고 (품질 특이사항 등)",
            "YE Part - CAM5 3 Line - 변경점 및 TEST 진행 현황",
            "YE Part - CAM5 3 Line - 비고 (품질 특이사항 등)",
            "YE Part - CAM5N 4 Line - 변경점 및 TEST 진행 현황",
            "YE Part - CAM5N 4 Line - 비고 (품질 특이사항 등)",
            "YE Part - CAM5N 5 Line - 변경점 및 TEST 진행 현황",
            "YE Part - CAM5N 5 Line - 비고 (품질 특이사항 등)",
            "요소기술 Part - Part 통합 - TEST 진행 현황 및 신공법 검토",
        ]

        # 추가: 업무일지 템플릿 정의
        self.template = {
            "작성일자": {"page": 0, "region": (40, 40, 300, 100)},  # 예시 좌표
            "table_main": {"page": 0, "region": (50, 150, 550, 700)},  # 메인 테이블 위치
            "table_part": {"page": 1, "region": (50, 150, 550, 600)}   # Part 테이블 위치
        }

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        # Open the PDF
        try:
            self.doc = fitz.open(pdf_path)
            logger.info(f"Successfully opened PDF with {len(self.doc)} pages: {pdf_path}")
        except Exception as e:
            logger.error(f"Failed to open PDF {pdf_path}: {e}")
            raise

    def ensure_directories(self):
        """Create output and image directories if they don't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    def extract_text_from_doc(self) -> str:
        """
        Extract text from all pages of the PDF document.
        DEPRECATED for region-based parsing, but kept for fallback or simple text needs.
        """
        full_text = ""
        logger.info(f"Extracting text from all pages of {os.path.basename(self.pdf_path)}")
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                page_text = page.get_text("text", sort=True) # Use simple text extraction, sorting helps
                full_text += page_text + "\n\n--- Page Break ---\n\n" # Add page breaks for context
            except Exception as e:
                logger.error(f"Error extracting text from page {page_num + 1}: {e}")
                continue

        # Basic cleaning
        full_text = re.sub(r'[\u200b\ufeff]', '', full_text) # Remove zero-width spaces
        full_text = re.sub(r'\s{2,}', ' ', full_text) # Replace multiple spaces with single space
        full_text = re.sub(r'\n{3,}', '\n\n', full_text) # Reduce multiple newlines

        logger.info(f"Total text length extracted: {len(full_text)} characters")
        return full_text.strip()

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

    def _is_likely_graph(self, image: Image.Image) -> bool:
        """Determine if an image is likely a graph or chart based on image analysis."""
        try:
            # 먼저 테이블인지 확인 - 테이블이면 그래프가 아님
            if self._is_likely_table(image):
                return False

            # Convert to numpy array for analysis
            img_array = np.array(image)

            # Simple heuristics for graph detection:
            # 1. Check for straight lines (common in graphs)
            # 2. Check color distribution (graphs often have limited color palette)
            # 3. Check for text density (graphs often have scattered text)

            # Convert to grayscale for line detection
            if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                gray = np.mean(img_array[:, :, :3], axis=2).astype(np.uint8)
            else:
                gray = img_array.astype(np.uint8)

            # Count potential horizontal and vertical lines
            h_lines = 0
            v_lines = 0

            # Simplistic line detection through variance analysis
            h_variance = np.var(gray, axis=1)
            v_variance = np.var(gray, axis=0)

            h_lines = np.sum(h_variance < np.mean(h_variance) * 0.5)
            v_lines = np.sum(v_variance < np.mean(v_variance) * 0.5)

            # Color analysis - count unique colors
            if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                # Downsample for efficiency
                downsampled = img_array[::4, ::4, :3]
                flattened = downsampled.reshape(-1, 3)
                unique_colors = np.unique(flattened, axis=0)
                color_count = len(unique_colors)
                limited_palette = color_count < 50  # Graphs often have limited colors
            else:
                limited_palette = True

            # Simple scoring system
            score = 0
            if h_lines > 5:  # Multiple horizontal lines suggest axis or grid
                score += 1
            if v_lines > 5:  # Multiple vertical lines suggest axis or grid
                score += 1
            if limited_palette:
                score += 1

            # 그래프 특성: 축 레이블, 범례, 타이틀 등이 존재할 가능성
            has_graph_features = False
            if (h_lines > 0 and v_lines > 0) and (h_lines < 20 or v_lines < 20):  # 그래프는 보통 테이블보다 적은 라인 수
                has_graph_features = True
                score += 1

            return score >= 2  # If at least 2 criteria met, likely a graph

        except Exception as e:
            logger.warning(f"Graph detection error: {e}")
            return False  # Default to regular image on error

    def _is_likely_table(self, image: Image.Image) -> bool:
        """Determine if an image is likely a table based on image analysis."""
        try:
            # Convert to numpy array for analysis
            img_array = np.array(image)

            # Simple heuristics for table detection:
            # 1. Check for grid patterns (regularly spaced lines)
            # 2. Check for uniformity in cell sizes
            # 3. Check for aligned text blocks
            # 4. Check for border lines

            # Convert to grayscale for line detection
            if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                gray = np.mean(img_array[:, :, :3], axis=2).astype(np.uint8)
            else:
                gray = img_array.astype(np.uint8)

            # Line detection using variance analysis
            h_variance = np.var(gray, axis=1)
            v_variance = np.var(gray, axis=0)

            # Count potential horizontal and vertical lines
            h_lines = np.sum(h_variance < np.mean(h_variance) * 0.5)
            v_lines = np.sum(v_variance < np.mean(v_variance) * 0.5)

            # Check for grid pattern - look for regular spacing between lines
            h_peaks = np.where(h_variance < np.mean(h_variance) * 0.5)[0]
            v_peaks = np.where(v_variance < np.mean(v_variance) * 0.5)[0]

            # Calculate distances between adjacent lines
            h_distances = [h_peaks[i+1] - h_peaks[i] for i in range(len(h_peaks)-1)] if len(h_peaks) > 1 else []
            v_distances = [v_peaks[i+1] - v_peaks[i] for i in range(len(v_peaks)-1)] if len(v_peaks) > 1 else []

            # Check for regularity in line spacing (indicates table grid)
            h_regular = False
            v_regular = False

            if h_distances:
                h_std = np.std(h_distances)
                h_mean = np.mean(h_distances)
                h_regular = h_std / h_mean < 0.3 and len(h_distances) >= 3  # Low variance in spacing

            if v_distances:
                v_std = np.std(v_distances)
                v_mean = np.mean(v_distances)
                v_regular = v_std / v_mean < 0.3 and len(v_distances) >= 3  # Low variance in spacing

            # Check for limited color palette (tables typically have few colors)
            limited_palette = False
            if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                # Downsample for efficiency
                downsampled = img_array[::4, ::4, :3]
                flattened = downsampled.reshape(-1, 3)
                unique_colors = np.unique(flattened, axis=0)
                color_count = len(unique_colors)
                limited_palette = color_count < 30  # Tables often have very limited colors
            else:
                limited_palette = True

            # Simple scoring system for table likelihood
            score = 0

            # Many horizontal and vertical lines indicate a table
            if h_lines > 5 and v_lines > 5:
                score += 1

            # 테이블은 보통 많은 라인을 가짐
            if h_lines >= 10 and v_lines >= 5:  # 더 많은 라인은 테이블일 가능성이 높음
                score += 2

            # Regular spacing between lines strongly indicates a table
            if h_regular or v_regular:
                score += 1

            # If both horizontal and vertical lines show regular spacing, very likely a table
            if h_regular and v_regular:
                score += 2

            # Limited color palette common in tables
            if limited_palette:
                score += 1

            # Check for grid-like ratio
            if 0.5 < h_lines / max(v_lines, 1) < 2:  # Roughly same number of h and v lines
                score += 1

            # Check for high density of lines - tables typically have more lines than graphs
            image_area = img_array.shape[0] * img_array.shape[1]
            line_density = (h_lines + v_lines) / (image_area ** 0.5)  # Normalize by sqrt of area
            if line_density > 0.2:  # Arbitrary threshold based on testing
                score += 1

            # 테이블 특성: 행/열의 균일성
            row_height_consistency = h_std / h_mean < 0.2 if h_distances else False
            col_width_consistency = v_std / v_mean < 0.2 if v_distances else False
            if row_height_consistency and col_width_consistency:
                score += 2

            logger.debug(f"Table detection score: {score}, h_lines: {h_lines}, v_lines: {v_lines}, h_regular: {h_regular}, v_regular: {v_regular}")

            return score >= 4  # 기준 점수를 높여서 더 확실한 테이블만 감지

        except Exception as e:
            logger.warning(f"Table detection error: {e}")
            return False  # Default to regular image on error

    def _process_image(self, image_bytes: bytes, image_ext: str, page_num: int, xref: int,
                      filename_base: str, processed_image_xrefs: set, img_bbox: fitz.Rect = None) -> Optional[Dict]:
        """이미지 처리 및 저장을 위한 공통 메서드"""
        if xref in processed_image_xrefs:
            return None

        try:
            img_idx_str = f"xref{xref}"
            image = Image.open(io.BytesIO(image_bytes))
            optimized_image = self._optimize_image(image)

            save_format = "JPEG" if optimized_image.mode == "RGB" else "PNG"
            image_filename = f"image_{filename_base}_p{page_num + 1}_{img_idx_str}.{save_format.lower()}"
            image_path = os.path.join(self.image_dir, image_filename)

            # 이미지가 이미 존재하는지 확인
            if os.path.exists(image_path):
                logger.debug(f"Image already exists: {image_filename}")
                # 존재하더라도 이미지 정보 반환하도록 수정
                image_info_dict = {
                    "filename": image_filename,
                    "path": image_path,
                    "page": page_num + 1,
                    "xref": xref,
                    "size": optimized_image.size,
                    "format": save_format,
                    "bbox": self._get_bbox_list(img_bbox),
                    "image_type": "unknown"  # 분류는 나중에 수행
                }
                processed_image_xrefs.add(xref)
                return image_info_dict

            # 이미지 저장
            optimized_image.save(
                image_path,
                format=save_format,
                quality=85 if save_format == "JPEG" else None,
                optimize=True
            )

            # bbox 정보를 리스트로 변환
            bbox_list = self._get_bbox_list(img_bbox)

            # 이미지 정보 딕셔너리 생성
            image_info_dict = {
                "filename": image_filename,
                "path": image_path,
                "page": page_num + 1,
                "xref": xref,
                "size": optimized_image.size,
                "format": save_format,
                "bbox": bbox_list,
                "image_type": "unknown"  # 분류는 추후 별도로 수행
            }

            processed_image_xrefs.add(xref)
            logger.debug(f"Successfully processed image: {image_filename}")
            return image_info_dict

        except Exception as e:
            logger.error(f"Error processing image xref {xref}: {e}")
            return None

    def _get_bbox_list(self, bbox: fitz.Rect) -> Optional[List[float]]:
        """이미지 bbox를 리스트로 안전하게 변환"""
        if bbox and isinstance(bbox, fitz.Rect):
            return [bbox.x0, bbox.y0, bbox.x1, bbox.y1]
        return None

    def _detect_tables(self, page: fitz.Page, rect: fitz.Rect) -> List[Dict]:
        """테이블 감지 및 추출을 위한 공통 메서드"""
        found_tables = []

        # 테이블 감지 전략 정의
        table_strategies = [
            {"strategy": "lines_strict", "params": {}},
            {"strategy": "text", "params": {}},
            {"strategy": "text", "params": {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "vertical_tolerance": 5.0,
                "horizontal_tolerance": 5.0
            }}
        ]

        for strategy_config in table_strategies:
            try:
                tables = page.find_tables(clip=rect, **strategy_config)
                if tables and tables.tables:
                    logger.debug(f"Found {len(tables.tables)} table(s) using '{strategy_config['strategy']}' strategy")
                    found_tables = tables.tables
                    break
            except Exception as e:
                logger.debug(f"Table strategy '{strategy_config['strategy']}' failed: {e}")
                continue

        return found_tables

    def extract_data_for_region(self, region_rects: List[Tuple[int, fitz.Rect]], key_name: str) -> Dict:
        """Extract text, images, and tables from a given region."""
        extracted_text = ""
        region_images = []
        region_tables = []
        region_graphs = []
        region_image_tables = []  # New list for image-based tables
        filename_base = os.path.splitext(os.path.basename(self.doc.name))[0]
        processed_image_xrefs = set()

        if not region_rects:
            logger.debug(f"No region rectangles provided for key '{key_name}', returning empty data.")
            return {"text": "", "images": [], "tables": [], "graphs": [], "image_tables": []}

        logger.debug(f"Extracting data for region of key '{key_name}' spanning {len(region_rects)} rect(s)...")

        for page_num, rect in region_rects:
            if page_num < 0 or page_num >= len(self.doc):
                logger.warning(f"Invalid page number {page_num} for region of key '{key_name}")
                continue

            page = self.doc[page_num]

            # Extract Text
            try:
                text = page.get_text("text", clip=rect, sort=True)
                if text:
                    extracted_text += text.strip() + "\n"
            except Exception as e:
                logger.error(f"Error extracting text from page {page_num+1}, rect {rect} for key '{key_name}': {e}")

            # Extract Images
            try:
                image_list = page.get_images(full=True)
                for img_info in image_list:
                    xref = img_info[0]
                    try:
                        img_bbox = page.get_image_bbox(img_info)
                        if not img_bbox.is_valid or img_bbox.is_empty or not img_bbox.intersects(rect):
                            continue

                        base_image = self.doc.extract_image(xref)
                        if not base_image or not base_image.get("image"):
                            continue

                        image_info_dict = self._process_image(
                            base_image["image"],
                            base_image["ext"],
                            page_num,
                            xref,
                            filename_base,
                            processed_image_xrefs,
                            img_bbox
                        )

                        if image_info_dict:
                            # 이미지 추가 (분류는 나중에 수행)
                            region_images.append(image_info_dict)

                    except Exception as e_img:
                        logger.error(f"Error processing image xref {xref} in region for key '{key_name}': {e_img}")

            except Exception as e_img_list:
                logger.error(f"Error getting images from page {page_num+1} for key '{key_name}': {e_img_list}")

            # Extract Tables
            try:
                found_tables = self._detect_tables(page, rect)
                for tbl in found_tables:
                    try:
                        table_data = tbl.extract()
                        if table_data and len(table_data) > 1 and any(len(row) > 1 for row in table_data):
                            bbox_list = self._get_table_bbox(tbl)
                            region_tables.append({
                                "page": page_num + 1,
                                "bbox": bbox_list,
                                "data": table_data,
                                "confidence": "high" if len(table_data) > 2 else "medium"
                            })
                    except Exception as e_tbl:
                        logger.error(f"Error extracting data from table on page {page_num+1} for key '{key_name}': {e_tbl}")

            except Exception as e_find_tbl:
                logger.error(f"Error finding tables on page {page_num+1} for key '{key_name}': {e_find_tbl}")

        # Enhance with table content mapping
        if any("CAM5" in key_name for key in [key_name]) and region_tables:
            enhanced_data = self._map_table_content_to_section(key_name, region_tables, extracted_text)
            if enhanced_data:
                extracted_text = enhanced_data.get("text", extracted_text)

        # 이미지 분류 및 설명 생성
        if region_images and self.use_image_description:
            try:
                # 이미지 분류
                classified_images = self.classify_images(region_images)

                # 분류된 이미지 구분하기
                pictures = []
                graphs = []
                image_tables = []

                for img in classified_images:
                    img_type = img.get("image_type", "unknown")
                    if img_type == "table":
                        image_tables.append(img)
                    elif img_type == "graph":
                        graphs.append(img)
                    else:  # "picture" 또는 "unknown"
                        pictures.append(img)

                # 분류 결과 로깅
                logger.info(f"Classified images for '{key_name}': {len(pictures)} pictures, {len(graphs)} graphs, {len(image_tables)} tables")

                # 각 이미지 유형에 대한 설명 생성
                for img in classified_images:
                    img_description = self._generate_image_description(img)
                    if img_description:
                        img["description"] = img_description

                # 결과 업데이트
                region_images = pictures
                region_graphs = graphs
                region_image_tables = image_tables

            except Exception as e:
                logger.error(f"Error during image classification and description: {e}")

        # Clean final text
        cleaned_text = re.sub(r'\s{2,}', ' ', extracted_text).strip()
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text).strip()

        logger.info(f"Extracted from region for '{key_name}': {len(cleaned_text)} chars text, {len(region_images)} images, {len(region_tables)} tables, {len(region_graphs)} graphs, {len(region_image_tables)} image-based tables.")

        return {
            "text": cleaned_text,
            "images": region_images,
            "tables": region_tables,
            "graphs": region_graphs,
            "image_tables": region_image_tables
        }

    def _get_table_bbox(self, table) -> List[float]:
        """테이블 bbox를 안전하게 추출하는 헬퍼 메서드"""
        try:
            if isinstance(table.bbox, fitz.Rect):
                return [table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1]
            elif isinstance(table.bbox, (tuple, list)) and len(table.bbox) >= 4:
                return list(table.bbox[:4])
            else:
                logger.warning(f"Unexpected bbox type: {type(table.bbox)}")
                return [0, 0, 0, 0]
        except Exception as e:
            logger.warning(f"Error converting bbox to list: {e}")
            return [0, 0, 0, 0]

    def _map_table_content_to_section(self, key_name: str, tables: List[Dict], current_text: str) -> Dict:
        """Map specific table cells to section content based on the section key name."""
        if not tables:
            return None

        result = {"text": current_text}

        try:
            # Parse the key name to determine what content to extract
            parts = key_name.split(" - ")
            if len(parts) < 3:
                return None

            # Extract section identifiers
            section_id = parts[1].strip()  # e.g. "CAM5 1 Line" or "CAM5N 4 Line"
            content_type = parts[2].strip()  # e.g. "변경점 및 TEST 진행 현황" or "비고 (품질 특이사항 등)"

            # Extract line number and type
            line_match = re.search(r'(CAM5N?)\s*(\d+)\s*Line', section_id)
            if not line_match:
                return None

            cam_type = line_match.group(1)  # CAM5 or CAM5N
            line_num = line_match.group(2)  # 1, 2, 3, 4, 5

            # Search through tables to find matching content
            for table in tables:
                # Safely get table data
                try:
                    table_data = table.get("data", [])
                    # Check if table_data is directly a list
                    if not isinstance(table_data, list):
                        logger.warning(f"Table data is not a list: {type(table_data)}")
                        continue

                    # Check if we have enough data to process
                    if not table_data or len(table_data) < 2:
                        continue
                except Exception as e_table_get:
                    logger.debug(f"Error accessing table data: {e_table_get}")
                    continue

                # Find the row that contains our target section
                target_row = None
                for row in table_data:
                    # Safely check row
                    if not isinstance(row, (list, tuple)) or len(row) < 1:
                        continue

                    # Safely get first cell
                    try:
                        first_cell = row[0]
                        # Convert to string if needed
                        if not isinstance(first_cell, str):
                            first_cell = str(first_cell) if first_cell is not None else ""
                    except (IndexError, TypeError):
                        continue

                    # Look for our target section identifier
                    if cam_type in first_cell and line_num in first_cell and "Line" in first_cell:
                        target_row = row
                        break

                if not target_row:
                    continue

                # Determine which column contains our content type
                content_col_idx = None
                if "변경점" in content_type or "TEST" in content_type:
                    content_col_idx = 1  # Usually second column
                elif "비고" in content_type or "품질" in content_type:
                    content_col_idx = 2  # Usually third column

                # Extract the content if we found the column
                if content_col_idx is not None:
                    try:
                        # Safely check if the target row has enough columns
                        if len(target_row) > content_col_idx:
                            content = target_row[content_col_idx]
                            # Convert content to string if not None
                            if content is not None:
                                result["text"] = str(content)
                                logger.info(f"Found specific table content for {key_name}")
                                return result
                    except Exception as e_content:
                        logger.debug(f"Error extracting content from column {content_col_idx}: {e_content}")

        except Exception as e:
            logger.error(f"Error mapping table content to section {key_name}: {e}")

        return None

    def _classify_image_with_llm(self, image_path: str) -> str:
        """LLM을 사용하여 이미지 종류(picture/table/graph)를 분류합니다."""
        try:
            # Check if Ollama server is available
            if not self._check_ollama_server():
                logger.warning("Ollama server not available for image classification.")
                return "unknown"

            # 이미지 파일이 존재하는지 확인
            if not os.path.exists(image_path):
                logger.error(f"Image file not found for classification: {image_path}")
                return "unknown"

            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")

            # 이미지 분류를 위한 프롬프트
            prompt = """다음 이미지가 아래 세 가지 중 어떤 종류인지 가장 정확하게 분류해주세요:

1. PICTURE - 사진, 일반 이미지, 도면 등
2. TABLE - 표, 테이블, 행렬 형태의 데이터를 포함
3. GRAPH - 그래프, 차트, 다이어그램, 데이터 시각화

반드시 위의 세 단어(PICTURE, TABLE, GRAPH) 중 하나만 답변해주세요.
"""

            logger.debug(f"Sending image classification request for {image_path}")

            # Ollama API 호출
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "images": [base64_image],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # 낮은 온도로 명확한 결과 유도
                            "num_predict": 20    # 짧은 응답만 필요
                        }
                    },
                    timeout=30  # 분류는 짧은 시간 내에 완료되어야 함
                )

                if response.status_code == 200:
                    result = response.json()
                    classification_text = result.get("response", "").strip().upper()
                    logger.debug(f"Raw classification response: {classification_text}")

                    # 응답에서 분류 결과 추출
                    if "TABLE" in classification_text:
                        return "table"
                    elif "GRAPH" in classification_text:
                        return "graph"
                    elif "PICTURE" in classification_text:
                        return "picture"
                    else:
                        logger.warning(f"Unclear image classification: '{classification_text}'")
                        return "unknown"
                else:
                    logger.warning(f"LLM classification failed. Status code: {response.status_code}, Response: {response.text}")
                    return "unknown"
            except requests.RequestException as e:
                logger.error(f"API request failed during image classification: {e}")
                return "unknown"

        except Exception as e:
            logger.error(f"Error classifying image with LLM: {e}")
            return "unknown"

    def generate_image_descriptions(self, images: List[Dict], context_data: Dict) -> Dict:
        """Generate descriptions for images using Ollama."""
        descriptions = {}

        # Skip if no image description requested
        if not self.use_image_description:
            logger.info("Image description generation is disabled.")
            return descriptions

        # Check if Ollama is available
        if not self._check_ollama_server():
            logger.warning("Ollama server not available. Skipping image description generation.")
            return descriptions

        # 이미지가 분류되지 않았다면 분류 먼저 수행
        need_classification = any(img.get("image_type", "unknown") == "unknown" for img in images)
        if need_classification:
            logger.info(f"Classifying {len(images)} images before description generation")
            images = self.classify_images(images)

        for img_info in images:
            image_path = img_info.get("path")
            image_filename = img_info.get("filename")

            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Image path invalid or file does not exist: {image_path}")
                continue

            try:
                description = self._generate_image_description(img_info)
                if description:
                    descriptions[image_filename] = description
                    logger.info(f"Added description for {img_info.get('image_type', 'unknown')} image: {image_filename}")

            except Exception as e:
                logger.error(f"Error generating description for image {image_filename}: {e}")

        logger.info(f"Generated descriptions for {len(descriptions)} out of {len(images)} images")
        return descriptions

    def _generate_image_description(self, image_info: Dict) -> Optional[str]:
        """Generate description for an image using Ollama"""
        if not self.use_image_description:
            return None

        # 캐시에서 이미지 설명 확인
        img_xref = image_info.get("xref")
        cache_key = f"{img_xref}_{image_info.get('image_type', 'unknown')}"
        if cache_key in self.image_description_cache:
            logger.debug(f"Using cached description for image {cache_key}")
            return self.image_description_cache[cache_key]

        try:
            # Check if Ollama server is available
            if not self._check_ollama_server():
                logger.warning("Ollama server not available. Skipping image description generation.")
                return None

            # Read the image file
            image_path = image_info["path"]
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None

            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")

            # 이미지 타입에 따른 프롬프트 선택
            image_type = image_info.get("image_type", "unknown")

            if image_type == "table":
                prompt = """이 이미지는 테이블입니다. 테이블의 구조와 내용을 분석하여 다음 형식으로 응답해주세요:

## 테이블 구조
- 행 수: [행의 개수]
- 열 수: [열의 개수]
- 헤더: [헤더 내용 목록]

## 테이블 내용
[각 행과 열의 데이터를 표 형식으로 재구성하여 제시]

## 주요 정보
- [테이블에서 발견된 주요 수치나 패턴]
- [테이블이 보여주는 핵심 정보]

가능한 한 테이블의 전체 내용을 구조적으로 추출해 주세요.
"""
            elif image_type == "graph":
                prompt = """이 이미지는 그래프/차트입니다. 이 그래프를 분석하여 다음 형식으로 응답해주세요:

## 그래프 유형
- 종류: [막대, 선, 원형, 산점도 등]
- 축 정보: [X축, Y축 제목과 단위]
- 범례: [존재하는 경우 범례 내용]

## 데이터 분석
- 주요 데이터 포인트: [그래프에서 확인되는 주요 값들]
- 최대/최소/평균값: [확인 가능한 경우]
- 추세: [시간에 따른 변화 또는 패턴]

## 그래프 해석
- 주요 발견점: [그래프가 보여주는 핵심 메시지]
- 데이터 관계: [변수 간 상관관계 또는 비교점]

가능한 한 그래프의 모든 정보를 구조적으로 분석해 주세요.
"""
            else:  # picture 또는 unknown
                prompt = """이 이미지를 분석하여 다음 형식으로 응답해주세요:

## 이미지 내용
- 주요 대상: [이미지에 보이는 주요 객체나 인물]
- 상황/활동: [이미지에서 일어나고 있는 활동이나 상황]
- 배경/환경: [장소나 환경적 특징]

## 특징
- 주목할 점: [이미지에서 눈에 띄는 특별한 요소나 특징]
- 문맥 정보: [이미지가 전달하려는 메시지나 의미]

이미지의 주요 정보와 내용을 객관적으로 설명해 주세요.
"""

            logger.debug(f"Generating description for {image_type} image: {image_path}")

            # API 요청 준비 및 전송
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "images": [base64_image],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # 구조적이고 일관된 응답 유도
                        }
                    },
                    timeout=100
                )

                if response.status_code == 200:
                    result = response.json()
                    description = result.get("response", "").strip()

                    # 결과 확인
                    if description:
                        logger.info(f"Generated description for {image_type} image: {os.path.basename(image_path)}")

                        # 캐시에 설명 저장
                        self.image_description_cache[cache_key] = description

                        return description
                    else:
                        logger.warning(f"Empty description generated for image: {os.path.basename(image_path)}")
                        return "이미지 설명을 생성할 수 없습니다."
                else:
                    logger.warning(f"Failed to generate description. Status code: {response.status_code}, Response: {response.text}")
                    return "이미지 설명을 생성할 수 없습니다."

            except requests.RequestException as e:
                logger.error(f"API request failed during description generation: {e}")
                return "이미지 설명 생성 중 오류가 발생했습니다."

        except Exception as e:
            logger.error(f"Error generating image description: {e}")
            return None

    def _check_ollama_server(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            logger.debug(f"Checking Ollama server at {self.ollama_url}")
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama server is running and accessible.")
                return True
            else:
                logger.warning(f"Ollama server returned status code {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.warning(f"Ollama server check failed: {e}")
            return False

    def extract_all_tables(self) -> Dict[int, List[Dict]]:
        """
        새로운 메서드: PDF의 모든 페이지에서 테이블을 추출하고 페이지별로 정리합니다.
        여러 테이블 감지 전략을 사용하여 최대한 많은 테이블을 찾습니다.
        """
        all_tables = {}

        logger.info("Extracting all tables from PDF...")
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_tables = []

            # 여러 테이블 감지 전략 시도
            for strategy in ["lines_strict", "text", "text_horizontal", "lines"]:
                try:
                    tables = page.find_tables(strategy=strategy)
                    if tables and tables.tables:
                        logger.info(f"Found {len(tables.tables)} tables on page {page_num+1} using '{strategy}' strategy")

                        for table in tables.tables:
                            try:
                                table_data = table.extract()

                                # 빈 테이블 또는 작은 테이블 필터링
                                if table_data and len(table_data) > 1 and any(len(row) > 1 for row in table_data):
                                    # 테이블 bbox를 안전하게 처리
                                    if isinstance(table.bbox, fitz.Rect):
                                        bbox = [table.bbox.x0, table.bbox.y0, table.bbox.x1, table.bbox.y1]
                                    elif isinstance(table.bbox, (tuple, list)) and len(table.bbox) >= 4:
                                        bbox = list(table.bbox[:4])
                                    else:
                                        logger.warning(f"Unexpected bbox type: {type(table.bbox)}")
                                        bbox = [0, 0, 0, 0]

                                    # 테이블 정보 저장
                                    page_tables.append({
                                        "bbox": bbox,
                                        "data": table_data,
                                        "strategy": strategy,
                                        "confidence": "high" if len(table_data) > 2 else "medium"
                                    })

                                    # 첫 번째 성공한 전략 후 중복 방지를 위해 다음 전략으로 넘어감
                                    if page_tables:
                                        break
                            except Exception as e_table:
                                logger.debug(f"Error extracting table data: {e_table}")
                except Exception as e_strategy:
                    logger.debug(f"Table strategy '{strategy}' failed: {e_strategy}")

            all_tables[page_num] = page_tables
            logger.info(f"Extracted {len(page_tables)} tables from page {page_num+1}")

        return all_tables

    def identify_key_cells_in_tables(self, tables: Dict[int, List[Dict]]) -> Dict[str, Dict]:
        """
        새로운 메서드: 테이블 데이터에서 CAM5/CAM5N 라인 및 기타 주요 키를 식별합니다.
        각 키에 대한 위치 및 관련 데이터를 반환합니다.
        """
        key_cells = {}

        logger.info("Identifying key cells in tables...")

        # 각 페이지의 테이블 처리
        for page_num, page_tables in tables.items():
            for table_idx, table in enumerate(page_tables):
                table_data = table.get("data", [])

                # 테이블 행 분석
                for row_idx, row in enumerate(table_data):
                    if not isinstance(row, (list, tuple)) or len(row) < 1:
                        continue

                    # 첫 번째 셀 분석
                    try:
                        first_cell = row[0]
                        if not isinstance(first_cell, str):
                            first_cell = str(first_cell) if first_cell is not None else ""
                    except (IndexError, TypeError):
                        continue

                    # CAM5/CAM5N 라인 패턴 검색
                    if "CAM5" in first_cell and ("Line" in first_cell or "라인" in first_cell):
                        # 라인 번호 추출
                        line_match = re.search(r'(\d+)\s*Line', first_cell)
                        line_num = line_match.group(1) if line_match else ""

                        if line_num:
                            # 베이스 키 이름 생성
                            if "CAM5N" in first_cell:
                                base_key = f"YE Part - CAM5N {line_num} Line"
                            else:
                                base_key = f"YE Part - CAM5 {line_num} Line"

                            # 변경점 및 비고 컬럼 정보 추출
                            change_text = row[1] if len(row) > 1 and row[1] is not None else ""
                            note_text = row[2] if len(row) > 2 and row[2] is not None else ""

                            # 키 및 데이터 저장
                            key_cells[f"{base_key} - 변경점 및 TEST 진행 현황"] = {
                                "page": page_num,
                                "table_idx": table_idx,
                                "row_idx": row_idx,
                                "col_idx": 1,
                                "text": str(change_text),
                                "bbox": table["bbox"]
                            }

                            key_cells[f"{base_key} - 비고 (품질 특이사항 등)"] = {
                                "page": page_num,
                                "table_idx": table_idx,
                                "row_idx": row_idx,
                                "col_idx": 2,
                                "text": str(note_text),
                                "bbox": table["bbox"]
                            }

                    # 요소기술 Part 검색
                    # elif "요소기술" in first_cell and "Part" in first_cell:
                    elif "Part 통합" in first_cell:
                        # 관련 데이터 있는지 확인
                        if len(row) > 1 and row[1] is not None:
                            key_cells["요소기술 Part - Part 통합 - TEST 진행 현황 및 신공법 검토"] = {
                                "page": page_num,
                                "table_idx": table_idx,
                                "row_idx": row_idx,
                                "col_idx": 1,
                                "text": str(row[1]),
                                "bbox": table["bbox"]
                            }

        # 찾은 키 수 확인
        logger.info(f"Identified {len(key_cells)} key cells in tables")
        return key_cells

    def template_based_extraction(self) -> Dict:
        """
        새로운 메서드: 템플릿 기반 추출을 수행하여 특정 영역의 텍스트 및 이미지를 추출합니다.
        업무일지의 고정 레이아웃에 기반한 방식입니다.
        """
        # 이미지 추출
        all_images = self.extract_all_images()

        # 그래프 이미지 식별 및 설명 생성
        # 여기서 먼저 모든 그래프 이미지에 대한 설명을 생성하여 중복 API 호출 방지
        image_descriptions = {}
        if self.use_image_description:
            for page_images in all_images.values():
                for img in page_images:
                    if img.get("is_graph", False):
                        try:
                            img_ref = f"img_{img['xref']}"
                            description = self._generate_image_description(img)
                            if description:
                                image_descriptions[img_ref] = description
                        except Exception as e:
                            logger.error(f"Error generating description for image {img['filename']}: {e}")

        result = {
            "metadata": {
                "source_file": os.path.basename(self.pdf_path),
                "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "parser_type": "template_based",
                "ollama_image_description": self.use_image_description,
                "ollama_model_used_img_desc": self.ollama_model if self.use_image_description else None
            },
            "image_metadata": {},
            "image_descriptions": image_descriptions,
            "table_structures": {}
        }

        # 각 템플릿 영역의 텍스트 추출
        template_data = {}
        logger.info("Performing template-based extraction...")

        # 템플릿에 정의된 각 영역 처리
        for section_name, location in self.template.items():
            page_num = location["page"]
            if page_num >= len(self.doc):
                logger.warning(f"Template specifies page {page_num+1} but PDF only has {len(self.doc)} pages")
                continue

            page = self.doc[page_num]
            region = fitz.Rect(*location["region"])

            # 해당 영역에서 텍스트 추출
            try:
                text = page.get_text("text", clip=region, sort=True)

                # 이미지 연결
                page_images = all_images.get(page_num, [])
                section_images = []
                for img in page_images:
                    if img.get("bbox") and self._rect_intersects(img["bbox"], list(region)):
                        section_images.append(img)

                        # 직접 설명 생성 없이 이미 생성된 설명만 참조
                        # 이 부분을 삭제하거나 주석 처리합니다
                        # if self.use_image_description and img.get("is_graph", False):
                        #     try:
                        #         description = self._generate_image_description(img)
                        #         if description:
                        #             img_ref = f"img_{img['xref']}"
                        #             result["image_descriptions"][img_ref] = description
                        #     except Exception as e:
                        #         logger.error(f"Error generating description for image {img['filename']}: {e}")

                template_data[section_name] = {
                    "text": text.strip(),
                    "page": page_num,
                    "bbox": list(region),
                    "images": section_images
                }
                logger.info(f"Extracted {len(text)} chars for template section '{section_name}'")
            except Exception as e:
                logger.error(f"Error extracting text for template section '{section_name}': {e}")
                template_data[section_name] = {"text": "", "page": page_num, "bbox": list(region), "images": []}

        # 결과 구성
        result["parsed_data"] = template_data

        # 이미지 메타데이터 추가
        for page_images in all_images.values():
            for img in page_images:
                img_ref = f"img_{img['xref']}"
                result["image_metadata"][img_ref] = {
                    "filename": img["filename"],
                    "path": img["path"],
                    "page": img["page"],
                    "xref": img["xref"],
                    "size": img["size"],
                    "format": img["format"],
                    "is_graph": img.get("is_graph", False),
                    "bbox": img.get("bbox", [0, 0, 0, 0])
                }

        return result

    def _validate_template_based_data(self, data: Dict) -> bool:
        """Validate the template-based conversion result"""
        if not data or not isinstance(data, dict):
            return False

        required_keys = ["metadata", "parsed_data", "image_metadata"]
        if not all(key in data for key in required_keys):
            return False

        if not data["parsed_data"]:
            return False

        return True

    def extract_all_images(self) -> Dict[int, List[Dict]]:
        """
        새로운 메서드: PDF의 모든 페이지에서 이미지를 추출하고 페이지별로 정리합니다.
        """
        all_images = {}
        filename_base = os.path.splitext(os.path.basename(self.doc.name))[0]
        processed_image_xrefs = set()

        logger.info("Extracting all images from PDF...")

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_images = []

            try:
                image_list = page.get_images(full=True)
                for img_info in image_list:
                    xref = img_info[0]
                    if xref in processed_image_xrefs:
                        continue

                    try:
                        img_bbox = page.get_image_bbox(img_info)
                        if not img_bbox.is_valid or img_bbox.is_empty:
                            continue

                        base_image = self.doc.extract_image(xref)
                        if not base_image or not base_image.get("image"):
                            continue

                        image_info_dict = self._process_image(
                            base_image["image"],
                            base_image["ext"],
                            page_num,
                            xref,
                            filename_base,
                            processed_image_xrefs,
                            img_bbox
                        )

                        if image_info_dict:
                            page_images.append(image_info_dict)
                    except Exception as e_img:
                        logger.error(f"Error processing image xref {xref} on page {page_num+1}: {e_img}")
            except Exception as e_img_list:
                logger.error(f"Error getting images from page {page_num+1}: {e_img_list}")

            all_images[page_num] = page_images
            logger.info(f"Extracted {len(page_images)} images from page {page_num+1}")

        return all_images

    def convert_with_table_based_approach(self) -> Optional[Dict]:
        """Convert PDF to JSON using table-based approach"""
        try:
            # Extract all tables from the PDF
            all_tables = self.extract_all_tables()

            # Identify key cells in tables
            key_cells = self.identify_key_cells_in_tables(all_tables)

            # Extract all images
            all_images = self.extract_all_images()

            # 이미지 분류 및 설명 생성
            image_descriptions = {}
            all_classified_images = {}

            if self.use_image_description and self.use_ollama_processing:
                logger.info("Starting image classification and description generation...")

                # Check if Ollama server is available
                if self._check_ollama_server():
                    # 각 페이지의 이미지 분류
                    for page_num, page_images in all_images.items():
                        if page_images:
                            try:
                                # 이미지 분류
                                classified_images = self.classify_images(page_images)
                                all_classified_images[page_num] = classified_images

                                # 분류 결과 로깅
                                picture_count = sum(1 for img in classified_images if img.get('image_type') == 'picture')
                                graph_count = sum(1 for img in classified_images if img.get('image_type') == 'graph')
                                table_count = sum(1 for img in classified_images if img.get('image_type') == 'table')

                                logger.info(f"Page {page_num+1}: Classified {len(classified_images)} images - {picture_count} pictures, {graph_count} graphs, {table_count} tables")

                                # 각 이미지에 대한 설명 생성
                                for img in classified_images:
                                    img_description = self._generate_image_description(img)
                                    if img_description:
                                        img["description"] = img_description
                                        image_descriptions[img["filename"]] = img_description
                            except Exception as e:
                                logger.error(f"Error classifying images on page {page_num+1}: {e}")
                else:
                    logger.warning("Ollama server not available. Skipping image classification and description.")
            else:
                logger.info("Image description generation is disabled.")
                # 분류 없이 원본 이미지 사용
                all_classified_images = all_images

            # Initialize result structure
            result = {
                "metadata": {
                    "source_file": os.path.basename(self.pdf_path),
                    "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "parser_type": "table_based",
                    "ollama_image_description": self.use_image_description and self.use_ollama_processing,
                    "ollama_model_used": self.ollama_model if (self.use_image_description and self.use_ollama_processing) else None
                },
                "parsed_data": {},
                "image_metadata": {},
                "image_descriptions": image_descriptions,
                "table_structures": {}
            }

            # Process each key cell
            for key, cell_info in key_cells.items():
                page_num = cell_info["page"]
                table_idx = cell_info["table_idx"]
                row_idx = cell_info["row_idx"]
                col_idx = cell_info["col_idx"]

                # Get the table data
                table = all_tables[page_num][table_idx]
                table_data = table["data"]

                # Extract table structure
                table_structure = self._extract_table_structure(table_data, table["bbox"])
                if table_structure:
                    result["table_structures"][f"table_{page_num}_{table_idx}"] = table_structure

                # Extract text from the cell and its related cells
                # cell_text = ""
                # if row_idx < len(table_data) and col_idx < len(table_data[row_idx]):
                #     # 현재 셀의 텍스트
                #     cell_text = str(table_data[row_idx][col_idx])

                #     # 관련 셀의 텍스트도 포함 (같은 행의 다른 열)
                #     for i in range(len(table_data[row_idx])):
                #         if i != col_idx and table_data[row_idx][i] is not None:
                #             cell_text += f"\n{table_data[row_idx][i]}"
                cell_text = str(table_data[row_idx][col_idx])

                # Get associated images - 분류된 이미지 사용
                page_images = all_classified_images.get(page_num, [])
                section_images = []
                section_graphs = []
                section_tables = []

                for img in page_images:
                    if img.get("bbox") and self._rect_intersects(img["bbox"], cell_info["bbox"]):
                        img_type = img.get("image_type", "unknown")
                        if img_type == "table":
                            section_tables.append(img)
                        elif img_type == "graph":
                            section_graphs.append(img)
                        else:  # picture 또는 unknown
                            section_images.append(img)

                # Add to parsed data
                result["parsed_data"][key] = {
                    "text": cell_text,
                    "page": page_num + 1,
                    "images": section_images,
                    "graphs": section_graphs,
                    "image_tables": section_tables,
                    "table_position": {
                        "row": row_idx + 1,
                        "column": col_idx + 1,
                        "table_index": table_idx
                    }
                }

            # Add image metadata for all images
            for page_num, page_images in all_classified_images.items():
                for img in page_images:
                    img_ref = f"img_{img['xref']}"
                    result["image_metadata"][img_ref] = {
                        "filename": img["filename"],
                        "path": img["path"],
                        "page": img["page"],
                        "xref": img["xref"],
                        "size": img["size"],
                        "format": img["format"],
                        "image_type": img.get("image_type", "unknown"),
                        "bbox": img.get("bbox", [0, 0, 0, 0])
                    }

            return result

        except Exception as e:
            logger.error(f"Error in table-based conversion: {e}")
            return None

    def _extract_table_structure(self, table_data: List[List[str]], bbox: List[float]) -> Dict:
        """Extract detailed structure information from a table"""
        try:
            # Calculate cell dimensions
            num_rows = len(table_data)
            num_cols = max(len(row) for row in table_data) if table_data else 0

            # Calculate approximate cell dimensions
            table_width = bbox[2] - bbox[0]
            table_height = bbox[3] - bbox[1]
            cell_width = table_width / num_cols if num_cols > 0 else 0
            cell_height = table_height / num_rows if num_rows > 0 else 0

            # Extract column headers
            headers = table_data[0] if table_data else []

            # Analyze data types in each column
            column_types = []
            for col_idx in range(num_cols):
                types = set()
                for row in table_data[1:]:  # Skip header row
                    if col_idx < len(row):
                        cell_value = row[col_idx]
                        # 셀 값이 None이거나 빈 문자열인 경우 처리
                        if cell_value is None:
                            types.add("null")
                            continue

                        # 문자열이 아닌 경우 문자열로 변환
                        if not isinstance(cell_value, str):
                            cell_value = str(cell_value)

                        # 빈 문자열인 경우
                        if not cell_value:
                            types.add("empty")
                        # 정수인 경우
                        elif cell_value.isdigit():
                            types.add("number")
                        # 실수인 경우
                        elif cell_value.replace('.', '', 1).isdigit():
                            types.add("float")
                        # 그 외의 경우 텍스트로 간주
                        else:
                            types.add("text")
                column_types.append(list(types))

            return {
                "dimensions": {
                    "rows": num_rows,
                    "columns": num_cols,
                    "cell_width": cell_width,
                    "cell_height": cell_height
                },
                "headers": headers,
                "column_types": column_types,
                "bbox": bbox
            }
        except Exception as e:
            logger.error(f"Error extracting table structure: {e}")
            return None

    def _rect_intersects(self, rect1: List[float], rect2: List[float]) -> bool:
        """Check if two rectangles intersect"""
        return not (rect1[2] < rect2[0] or rect1[0] > rect2[2] or
                   rect1[3] < rect2[1] or rect1[1] > rect2[3])

    def _validate_table_based_data(self, data: Dict) -> bool:
        """Validate the table-based conversion result"""
        if not data or not isinstance(data, dict):
            return False

        required_keys = ["metadata", "parsed_data", "image_metadata"]
        if not all(key in data for key in required_keys):
            return False

        if not data["parsed_data"]:
            return False

        return True

    def convert(self) -> Optional[Dict]:
        """
        Main conversion method that uses the hybrid approach to convert PDF to JSON.
        This method is called by the process_all_pdfs function.
        """
        try:
            logger.info(f"Starting conversion of {os.path.basename(self.pdf_path)}")
            result = self.convert_with_hybrid_approach()

            if result:
                # Save the result to JSON file
                output_path = os.path.join(self.output_dir, f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"Successfully converted and saved {output_path}")
                return result
            else:
                logger.error(f"Conversion failed for {os.path.basename(self.pdf_path)}")
                return None

        except Exception as e:
            logger.error(f"Error in conversion: {e}")
            return None

    def convert_with_hybrid_approach(self) -> Optional[Dict]:
        """하이브리드 접근 방식으로 PDF를 JSON으로 변환"""
        try:
            # 1. 테이블 기반 파싱 시도
            table_based_data = self.convert_with_table_based_approach()
            if table_based_data and self._validate_table_based_data(table_based_data):
                logger.info("Successfully extracted data using table-based approach")
                return table_based_data

            # 2. 템플릿 매칭 시도
            template_based_data = self.template_based_extraction()
            if template_based_data and self._validate_template_based_data(template_based_data):
                logger.info("Successfully extracted data using template matching")
                return template_based_data

            # 3. 하이브리드 접근 (테이블 + 템플릿)
            logger.info("Attempting hybrid approach (table + template)...")

            # 테이블 데이터 추출
            all_tables = self.extract_all_tables()
            key_cells = self.identify_key_cells_in_tables(all_tables)

            # 이미지 데이터 추출
            all_images = self.extract_all_images()

            # 그래프 이미지 식별 및 설명 생성
            # 여기서 먼저 모든 그래프 이미지에 대한 설명을 생성하여 중복 API 호출 방지
            image_descriptions = {}
            if self.use_image_description:
                for page_images in all_images.values():
                    for img in page_images:
                        if img.get("is_graph", False):
                            try:
                                img_ref = f"img_{img['xref']}"
                                description = self._generate_image_description(img)
                                if description:
                                    image_descriptions[img_ref] = description
                            except Exception as e:
                                logger.error(f"Error generating description for image {img['filename']}: {e}")

            # 기본 결과 구조 설정
            result = {
                "metadata": {
                    "source_file": os.path.basename(self.pdf_path),
                    "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "parser_type": "hybrid_approach",
                    "ollama_image_description": self.use_image_description,
                    "ollama_model_used_img_desc": self.ollama_model if self.use_image_description else None
                },
                "parsed_data": {},
                "image_metadata": {},
                "image_descriptions": image_descriptions,
                "table_structures": {}
            }

            # 테이블 구조 정보 추출
            for page_num, page_tables in all_tables.items():
                for table_idx, table in enumerate(page_tables):
                    table_structure = self._extract_table_structure(table.get("data", []), table.get("bbox", [0,0,0,0]))
                    if table_structure:
                        result["table_structures"][f"table_{page_num}_{table_idx}"] = table_structure

            # 섹션별 데이터 추출
            for key in self.target_keys:
                # 테이블 기반 데이터 추출
                if key in key_cells:
                    cell_info = key_cells[key]
                    page_num = cell_info["page"]
                    table_idx = cell_info["table_idx"]
                    row_idx = cell_info["row_idx"]
                    col_idx = cell_info["col_idx"]

                    # 테이블 데이터 가져오기
                    table = all_tables[page_num][table_idx]
                    table_data = table["data"]

                    # 셀 텍스트 추출
                    # cell_text = ""
                    # if row_idx < len(table_data) and col_idx < len(table_data[row_idx]):
                    #     # 현재 셀의 텍스트
                    #     cell_text = str(table_data[row_idx][col_idx])

                    #     # 관련 셀의 텍스트도 포함 (같은 행의 다른 열)
                    #     for i in range(len(table_data[row_idx])):
                    #         if i != col_idx and table_data[row_idx][i] is not None:
                    #             cell_text += f"\n{table_data[row_idx][i]}"
                    cell_text = str(table_data[row_idx][col_idx])

                    # 연관된 이미지 찾기
                    page_images = all_images.get(page_num, [])
                    section_images = []
                    for img in page_images:
                        if img.get("bbox") and self._rect_intersects(img["bbox"], cell_info["bbox"]):
                            section_images.append(img)

                            # 직접 설명 생성 없이 이미 생성된 설명만 참조
                            # 이 부분을 삭제하거나 주석 처리합니다
                            # if self.use_image_description and img.get("is_graph", False):
                            #     try:
                            #         description = self._generate_image_description(img)
                            #         if description:
                            #             img_ref = f"img_{img['xref']}"
                            #             result["image_descriptions"][img_ref] = description
                            #     except Exception as e:
                            #         logger.error(f"Error generating description for image {img['filename']}: {e}")

                    # 파싱된 데이터에 추가
                    result["parsed_data"][key] = {
                        "text": cell_text,
                        "page": page_num + 1,
                        "images": section_images,
                        "table_position": {
                            "row": row_idx + 1,
                            "column": col_idx + 1,
                            "table_index": table_idx
                        }
                    }

                # 테이블에서 찾지 못한 키는 템플릿 기반으로 시도
                elif key not in result["parsed_data"]:
                    # 템플릿 데이터에서 찾기
                    template_key = None
                    if "작성일자" in key:
                        template_key = "작성일자"
                    elif "YE Part" in key and "Line" in key:
                        template_key = "table_main"
                    elif "요소기술" in key:
                        template_key = "table_part"

                    if template_key and template_key in template_based_data["parsed_data"]:
                        template_section = template_based_data["parsed_data"][template_key]
                        result["parsed_data"][key] = {
                            "text": template_section["text"],
                            "page": template_section["page"] + 1,
                            "images": template_section.get("images", []),
                            "template_source": template_key
                        }

            # 이미지 메타데이터 생성
            for page_images in all_images.values():
                for img in page_images:
                    img_ref = f"img_{img['xref']}"
                    result["image_metadata"][img_ref] = {
                        "filename": img["filename"],
                        "path": img["path"],
                        "page": img["page"],
                        "xref": img["xref"],
                        "size": img["size"],
                        "format": img["format"],
                        "is_graph": img.get("is_graph", False),
                        "bbox": img.get("bbox", [0, 0, 0, 0])
                    }

            # 결과 검증
            if result["parsed_data"] and (result["image_metadata"] or not all_images):
                return result
            else:
                logger.warning("Hybrid approach failed to extract meaningful data.")
                return None

        except Exception as e:
            logger.error(f"Error in hybrid conversion: {e}")
            return None

    def classify_images(self, images: List[Dict]) -> List[Dict]:
        """이미지 목록을 받아 각 이미지를 picture/table/graph로 분류합니다."""
        if not images:
            return []

        classified_images = []
        for img in images:
            try:
                # 이미지 복사본 생성 (원본 수정 방지)
                img_copy = img.copy()

                # LLM으로 이미지 분류 수행
                img_type = self._classify_image_with_llm(img_copy["path"])
                img_copy["image_type"] = img_type

                # 분류 결과 로깅
                logger.debug(f"Classified image {img_copy['filename']} as: {img_type}")

                classified_images.append(img_copy)
            except Exception as e:
                logger.error(f"Error classifying image {img.get('filename')}: {e}")
                # 오류 발생 시에도 원본 이미지 추가
                classified_images.append(img)

        return classified_images

def process_all_pdfs(directory_path, output_dir, image_dir, use_image_description=True, use_ollama_processing=True):
    """Process all PDFs in the given directory."""
    logger.info(f"Processing all PDFs in directory: {directory_path}")
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    logger.info(f"Found {len(pdf_files)} PDF files to process.")

    successful_conversions = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        output_json_name = os.path.splitext(pdf_file)[0] + '.json'
        output_json_path = os.path.join(output_dir, output_json_name)

        logger.info(f"Processing PDF: {pdf_file} -> {output_json_name}")
        try:
            converter = PDFConverter(
                pdf_path=pdf_path,
                output_dir=output_dir,
                image_dir=image_dir,
                use_image_description=use_image_description,
                use_ollama_processing=use_ollama_processing
            )
            result = converter.convert()

            if result:
                with open(output_json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(result, json_file, ensure_ascii=False, indent=2)
                logger.info(f"Successfully converted and saved {output_json_path}")
                successful_conversions += 1
            else:
                logger.error(f"Conversion failed or returned no data for {pdf_file}")
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_file}: {str(e)}", exc_info=True)

    # Print summary
    if successful_conversions > 0:
        logger.info(f"Conversion complete. {successful_conversions} out of {len(pdf_files)} PDF files were successfully converted.")
        if use_image_description or any(os.listdir(image_dir)):
            logger.info(f"Associated images saved to {image_dir}")
    else:
        logger.error("No PDFs were successfully processed.")

def main():
    # Define paths relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Input PDF directory: <workspace>/PROCESS/업무일지
    pdf_directory = os.path.join(script_dir, "업무일지")
    # Output directory: <workspace>/PROCESS/output
    output_dir = os.path.join(script_dir, "output")
    # Image directory: <workspace>/output/images
    image_dir = os.path.join(output_dir, "images")

    # 해당 디렉토리가 없으면 생성
    os.makedirs(pdf_directory, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    # image_dir is created within process_all_pdfs's ensure_directories

    logger.info(f"Script directory (PROCESS): {script_dir}")
    logger.info(f"PDF input directory: {pdf_directory}")
    logger.info(f"JSON output directory: {output_dir}")
    logger.info(f"Image output directory: {image_dir}")

    # --- Configuration Flags ---
    # Set to False to disable generating descriptions for extracted images via Ollama
    use_image_description = True
    # Set to False to disable using Ollama for image descriptions (and potential future text cleanup)
    use_ollama_processing = True # This flag is less critical now, mainly for image desc
    # ---------------------------

    # Process all PDF files in the directory
    process_all_pdfs(
        pdf_directory,
        output_dir,
        image_dir,
        use_image_description,
        use_ollama_processing
    )

if __name__ == "__main__":
    main()