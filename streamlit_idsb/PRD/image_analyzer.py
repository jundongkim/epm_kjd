#!/usr/bin/env python3
"""
이미지 분석 도구 - Ollama gemma3:27b 모델을 사용하여 이미지를 분석합니다.
"""

import os
import sys
import json
import base64
import argparse
import requests
import subprocess
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

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

def check_ollama_service():
    """Ollama 서비스가 실행 중인지 확인합니다."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            return True
        return False
    except Exception:
        return False

def check_ollama_cli():
    """Ollama CLI가 설치되어 있는지 확인합니다."""
    try:
        result = subprocess.run(["ollama", "list"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        return result.returncode == 0
    except Exception:
        return False

def check_model_availability(model_name="gemma3:27b"):
    """특정 모델이 Ollama에서 사용 가능한지 확인합니다."""
    # 방법 1: API 사용
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()

            # 다양한 JSON 응답 구조 처리
            if "models" in data:
                # 새로운 API 구조
                models = data.get("models", [])
                model_names = [model.get("name") for model in models]
                return model_name in model_names
            elif "models" not in data and isinstance(data, list):
                # 가능한 다른 API 구조
                model_names = [model.get("name") for model in data]
                return model_name in model_names
            elif isinstance(data, dict):
                # 조금 더 일반적인 접근법
                return any(model_name in str(data))
    except Exception:
        pass

    # 방법 2: CLI 사용
    try:
        result = subprocess.run(["ollama", "list"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        return model_name in result.stdout
    except Exception:
        return False

    return False

def test_base64_encoding(image_path):
    """이미지의 base64 인코딩을 테스트합니다."""
    try:
        with open(image_path, "rb") as image_file:
            # 방법 1: 표준 base64 인코딩
            encoded_standard = base64.b64encode(image_file.read()).decode('utf-8')
            print(f"표준 base64 인코딩 테스트: {'성공' if encoded_standard else '실패'}")
            print(f"길이: {len(encoded_standard)}")
            print(f"미리보기: {encoded_standard[:50]}...")

            # 파일 포인터를 처음으로 되돌립니다
            image_file.seek(0)

            # 방법 2: base64.b64encode + 바이너리 모드
            encoded_binary = base64.b64encode(image_file.read())
            print(f"바이너리 base64 인코딩 테스트: {'성공' if encoded_binary else '실패'}")
            print(f"길이: {len(encoded_binary)}")

            return encoded_standard
    except Exception as e:
        print(f"base64 인코딩 중 오류: {str(e)}")
        return None

def get_image_info(image_path):
    """이미지 파일에 대한 정보를 가져옵니다."""
    try:
        img = Image.open(image_path)
        info = {
            "파일명": os.path.basename(image_path),
            "크기(바이트)": os.path.getsize(image_path),
            "마지막 수정": datetime.fromtimestamp(os.path.getmtime(image_path)).strftime("%Y-%m-%d %H:%M:%S"),
            "해상도": f"{img.width} x {img.height}",
            "포맷": img.format,
            "모드": img.mode
        }
        return info
    except Exception as e:
        print(f"이미지 정보 가져오기 오류: {str(e)}")
        return {}

def analyze_image_metadata(image_path):
    """이미지 메타데이터를 분석하여 설명을 생성합니다."""
    try:
        # 이미지 정보 가져오기
        image_info = get_image_info(image_path)

        # 프롬프트 생성
        prompt = f"""
        다음은 설비 유지보수 작업 중 촬영된 이미지에 대한 정보입니다.

        이미지 정보:
        파일명: {image_info.get('파일명', 'N/A')}
        크기: {image_info.get('크기(바이트)', 'N/A')} 바이트
        해상도: {image_info.get('해상도', 'N/A')}
        포맷: {image_info.get('포맷', 'N/A')}
        촬영 일시: {image_info.get('촬영일시', 'N/A')}

        분석 요청:
        1. 설비 식별
        - 이미지에서 보이는 설비나 부품의 종류
        - 모델명, 규격, 시리얼 번호 등 식별 가능한 정보
        - 제조사 정보나 브랜드 (가능한 경우)

        2. 상태 분석
        - 설비/부품의 현재 상태
        - 마모, 손상, 오염 등 이상 징후
        - 정상 작동 여부 판단
        - 잠재적인 문제점이나 위험 요소

        3. 기술적 특성
        - 주요 기술 사양 및 특징
        - 작동 원리나 메커니즘
        - 관련 표준이나 규격
        - 성능이나 용량 관련 정보

        4. 유지보수 관점
        - 현재 필요한 점검/조치 사항
        - 예방 정비 포인트
        - 권장되는 유지보수 주기
        - 안전 관련 주의사항
        - 향후 관리 방안

        위 정보를 바탕으로 설비 유지보수 전문가의 관점에서 상세한 기술 분석을 제공해주세요.
        """

        # 방법 1: API 호출 시도 (정식 방법)
        try:
            data = {
                "model": "gemma3:27b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_ctx": MODEL_SPECS["gemma3:27b"]["context_length"],
                    "num_predict": 2048  # 충분한 응답 길이 확보
                }
            }

            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=data,
                timeout=45  # 타임아웃 증가
            )

            if response.status_code == 200:
                result = response.json()
                description = result.get("response", "")
                # 응답 품질 검증
                if len(description.strip()) > 50:  # 최소 길이 확인
                    return description
        except Exception as e:
            print(f"API 호출 오류 (방법 1): {str(e)}")

        # 방법 2: 간단한 API 호출 (대체 방법)
        try:
            simple_data = {
                "model": "gemma3:27b",
                "prompt": prompt
            }

            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=simple_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                description = result.get("response", "")
                # 응답 품질 검증
                if len(description.strip()) > 50:  # 최소 길이 확인
                    return description
        except Exception as e:
            print(f"API 호출 오류 (방법 2): {str(e)}")

        # 방법 3: Ollama CLI 사용
        try:
            if check_ollama_cli():
                print("API 호출 실패, CLI 사용을 시도합니다...")

                # 임시 프롬프트 파일 생성
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                    tmp.write(prompt)
                    prompt_file = tmp.name

                # ollama run 명령어 실행
                result = subprocess.run(
                    ["ollama", "run", "gemma3:27b", "-f", prompt_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60  # CLI 타임아웃 증가
                )

                # 임시 파일 삭제
                os.unlink(prompt_file)

                if result.returncode == 0 and len(result.stdout.strip()) > 50:
                    return result.stdout
                else:
                    print(f"CLI 오류: {result.stderr}")
        except Exception as e:
            print(f"CLI 호출 오류: {str(e)}")

        return "이미지 분석에 실패했습니다. 모든 방법이 실패했습니다."

    except Exception as e:
        return f"이미지 분석 중 오류 발생: {str(e)}"

def analyze_with_cli(image_path):
    """Ollama CLI를 사용하여 이미지를 직접 분석합니다."""
    try:
        print("\n=== Ollama CLI로 이미지 분석 시도 ===")
        prompt = "이 이미지는 설비 유지보수 작업 중에 촬영된 것입니다. 이미지를 상세히 분석하고 기술적인 설명을 해주세요."

        # ollama run 명령어 실행
        result = subprocess.run(
            ["ollama", "run", "gemma3:27b", prompt, "-f", image_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("CLI 분석 성공!")
            return result.stdout
        else:
            print(f"CLI 분석 오류: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print("CLI 명령 시간 초과")
        return None
    except Exception as e:
        print(f"CLI 분석 중 오류 발생: {str(e)}")
        return None

def try_ollama_cli(image_path):
    """Ollama CLI를 사용하여 이미지를 분석합니다."""
    print("\n=== Ollama CLI 명령어 ===")
    prompt = "이 이미지는 설비 유지보수 작업 중에 촬영된 것입니다. 이미지에 대한 전문적인 기술 설명을 해주세요."
    command = f'ollama run gemma3:27b "{prompt}" -f "{image_path}"'
    print(f"다음 명령어를 터미널에서 직접 실행해보세요:")
    print(command)
    print("\n이 명령을 통해 Ollama가 이미지를 처리할 수 있는지 확인할 수 있습니다.")

    # CLI 실행 옵션 제공
    run_now = input("\nCLI 명령을 지금 실행할까요? (y/n): ")
    if run_now.lower() == 'y':
        try:
            # 실제로 명령어 실행
            print("\n=== CLI 명령 실행 결과 ===")
            result = subprocess.run(
                ["ollama", "run", "gemma3:27b", prompt, "-f", image_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120  # 2분 타임아웃
            )

            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"오류: {result.stderr}")
        except Exception as e:
            print(f"CLI 실행 오류: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Ollama gemma3:27b를 사용한 이미지 분석 도구")
    parser.add_argument("image_path", help="분석할 이미지 파일 경로")
    parser.add_argument("--test", action="store_true", help="base64 인코딩 테스트만 실행")
    parser.add_argument("--info", action="store_true", help="이미지 정보만 표시")
    parser.add_argument("--cli", action="store_true", help="Ollama CLI로 직접 이미지 분석")
    args = parser.parse_args()

    # 이미지 파일 존재 확인
    if not os.path.exists(args.image_path):
        print(f"오류: 이미지 파일을 찾을 수 없습니다: {args.image_path}")
        return 1

    # Ollama 서비스 확인
    if not check_ollama_service():
        print(f"오류: Ollama 서비스를 찾을 수 없습니다. {OLLAMA_BASE_URL}에서 Ollama가 실행 중인지 확인하세요.")

        # CLI가 있는지 확인
        if check_ollama_cli():
            print("Ollama CLI는 설치되어 있습니다. 서비스가 실행 중인지 확인하세요.")
            print("서비스 시작 명령어: ollama serve")
        return 1

    # 모델 확인
    if not check_model_availability("gemma3:27b"):
        print("경고: gemma3:27b 모델이 Ollama에 설치되어 있지 않습니다.")
        print("다음 명령어로 모델을 설치해주세요: ollama pull gemma3:27b")

        # 모델 자동 설치 제안
        install_now = input("지금 gemma3:27b 모델을 설치할까요? (y/n): ")
        if install_now.lower() == 'y':
            try:
                print("모델 설치 중... (시간이 오래 걸릴 수 있습니다)")
                result = subprocess.run(
                    ["ollama", "pull", "gemma3:27b"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if result.returncode == 0:
                    print("모델 설치 성공!")
                else:
                    print(f"모델 설치 실패: {result.stderr}")
                    return 1
            except Exception as e:
                print(f"모델 설치 실패: {str(e)}")
                return 1

    # 이미지 정보 표시
    print("\n=== 이미지 정보 ===")
    image_info = get_image_info(args.image_path)
    for key, value in image_info.items():
        print(f"{key}: {value}")

    # base64 인코딩 테스트
    if args.test:
        print("\n=== Base64 인코딩 테스트 ===")
        test_base64_encoding(args.image_path)
        try_ollama_cli(args.image_path)
        return 0

    # 이미지 정보만 표시
    if args.info:
        return 0

    # CLI로 직접 이미지 분석
    if args.cli:
        result = analyze_with_cli(args.image_path)
        if result:
            print("\n=== CLI 분석 결과 ===")
            print(result)
        return 0

    # 이미지 분석
    print("\n=== 이미지 분석 시작 ===")
    print("메타데이터 기반 분석을 시도합니다...")
    description = analyze_image_metadata(args.image_path)
    print("\n=== 분석 결과 ===")
    print(description)

    # Ollama CLI 사용법 안내
    try_ollama_cli(args.image_path)

    return 0

if __name__ == "__main__":
    sys.exit(main())