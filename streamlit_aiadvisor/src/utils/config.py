"""
설정 및 상수를 관리하는 모듈
"""
import os
from pathlib import Path

# 프로젝트 기본 경로
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))).resolve()
DATA_DIR = os.path.join(BASE_DIR, "data")
# FONT_PATH = os.path.join(BASE_DIR, "fonts", "Freesentation.ttf")
FONT_PATH = os.path.join(BASE_DIR, "fonts", "Paperlogy-3Light.ttf")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db")
TTL_DIR = os.path.join(BASE_DIR, "ttl_files")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")  # 파일 업로드 디렉토리
REPORTS_DIR = os.path.join(BASE_DIR, "reports")  # 보고서 저장 디렉토리
MODELS_DIR = os.path.join(BASE_DIR, "models")  # 모델 저장 디렉토리

# 모델 설정
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
DEFAULT_LLM_MODEL = "gemma3:12b-it-qat"
AVAILABLE_LLM_MODELS = {
    "Gemma 3 (1B)": "gemma3:1b",
    "Gemma 3 (1B-QAT)": "gemma3:1b-it-qat",
    "Gemma 3 (4B)": "gemma3:4b", 
    "Gemma 3 (4B-QAT)": "gemma3:4b-it-qat",
    "Gemma 3 (12B)": "gemma3:12b",
    "Gemma 3 (12B-QAT)": "gemma3:12b-it-qat",
    "Gemma 3 (27B)": "gemma3:27b",
    "Gemma 3 (27B-QAT)": "gemma3:27b-it-qat"
}

# LLM 타임아웃 설정 (초)
LLM_TIMEOUT = 360

# Ontology 관계 유형들
RELATIONSHIPS = [
    # 기본 관계
    "related",          # 일반적인 관련성
    "include",          # 포함 관계 (컴포넌트/부품)
    "contains",         # 포함 관계 (물질/성분)
    "belongs_to",       # 소속 관계
    
    # 인과 관계
    "caused_by",        # 원인-결과 관계 (문제 원인)
    "resulted_in",      # 결과 관계 (문제 결과)
    "affected_by",      # 영향 관계
    "contributes_to",   # 기여 관계
    
    # 비즈니스/제조 관계
    "competes_with",    # 경쟁 관계
    "supply_to",        # 공급 관계
    "receive_from",     # 수신 관계
    "manufactured_by",  # 제조 관계
    "processed_in",     # 공정 관계
    "distributed_to",   # 유통/분배 관계
    
    # 장비/공정 관계
    "used_in",          # 사용 관계 (장비/도구 사용)
    "part_of",          # 부분-전체 관계 (장비 구성)
    "connected_to",     # 연결 관계 (배관/장비)
    "measured_by",      # 측정 관계 (센서/계측기)
    "controlled_by",    # 제어 관계
    "operates_with",    # 작동 관계
    "feeds_into",       # 투입 관계
    "processes",        # 처리 관계
    
    # 품질/문제 관계
    "detected_in",      # 불량 발견 관계
    "improved_by",      # 개선 관계
    "failed_due_to",    # 고장 원인 관계
    "contaminated_by",  # 오염 관계
    "exceeds_limit",    # 한계치 초과 관계
    "below_limit",      # 한계치 미달 관계
    "causes_defect",    # 불량 유발 관계
    
    # 물질/화학적 관계
    "reacts_with",      # 반응 관계
    "dissolves_in",     # 용해 관계
    "precipitates_from",# 침전 관계
    "catalyzes",        # 촉매 관계
    
    # 유지보수/관리 관계
    "maintained_by",    # 유지보수 관계
    "replaced_by",      # 교체 관계
    "calibrated_by",    # 교정 관계
    "cleaned_by",       # 청소 관계
    "regulated_by",     # 규제 관계
    "inspected_by",     # 검사 관계
    
    # 시간/순서 관계
    "precedes",         # 선행 관계
    "follows",          # 후행 관계
    "occurs_during",    # 발생 시점 관계
    "scheduled_for",    # 일정 관계
    
    # 분석/테스트 관계
    "analyzed_with",    # 분석 방법 관계
    "tested_by",        # 테스트 방법 관계
    "sampled_from",     # 샘플링 관계
    "verified_by",      # 검증 관계
    
    # 비즈니스/규제 관계
    "invested_in",      # 투자 관계
    "complies_with",    # 준수 관계
    "certified_by",     # 인증 관계
    "approved_by"       # 승인 관계
]

# 디렉토리 생성
for directory in [DATA_DIR, VECTOR_DB_DIR, TTL_DIR, OUTPUT_DIR, UPLOADS_DIR, REPORTS_DIR, MODELS_DIR]:
    os.makedirs(directory, exist_ok=True)

# 보고서 기본 섹션
DEFAULT_REPORT_SECTIONS = [
    "1. 개요",
    "2. 기록",
    "3. 원인 분석",
    "4. 영향 평가",
    "5. 조치 결과",
    "6. 향후 대응",
    "7. 결론"
] 