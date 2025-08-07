# Scripts Directory

이 폴더에는 독립적으로 실행 가능한 유틸리티 스크립트들이 포함되어 있습니다.

## 📄 스크립트 목록

### 1. `extract_serialize_datasets.py`
BAR CSV 파일에서 순환 패턴에 따라 10개의 직렬화 데이터셋을 추출합니다.

**사용법:**
```bash
cd scripts
python extract_serialize_datasets.py
```

**기능:**
- BAR 파일에서 색칠된 셀 패턴 분석
- 순환 패턴에 따른 채널 데이터 추출
- 10개의 serialize dataset 생성 (L820169-18-01.csv ~ L820169-18-10.csv)
- BAR 파일들을 번호 순서로 연결하여 통합 serialize 파일 생성

**입력:** `data/iot/BAR*.csv` 파일들
**출력:** `data/iot/L*-*-*.csv` 파일들

### 2. `transform_bar_files.py`
BAR CSV 파일을 TR (Transformed) 형식으로 변환합니다.

**사용법:**
```bash
cd scripts
python transform_bar_files.py
```

**기능:**
- BAR 파일을 확장된 참조 패턴으로 변환
- 각 행에서 다른 행의 데이터를 참조하는 패턴 생성
- 데이터 무결성 검증 기능 포함

**변환 패턴:**
```
1행: (1, CH-A1)
2행: (2, CH-A1), (1, CH-A2)
3행: (3, CH-A1), (2, CH-A2), (1, CH-A3)
...
```

**입력:** `data/iot/BAR*.csv` 파일들
**출력:** `data/iot/BAR*TR.csv` 파일들

## 🔧 요구사항

### Python 패키지
- pandas
- numpy
- glob
- os

### 데이터 폴더 구조
```
data/
└── iot/
    ├── BAR00001.CSV
    ├── BAR00002.CSV
    ├── ...
    └── (생성된 파일들)
```

## 📝 주의사항

1. 이 스크립트들은 프로젝트 루트에서 실행되어야 합니다
2. `data/iot` 폴더가 존재하고 BAR 파일들이 있어야 합니다
3. 스크립트 실행 전에 기존 생성 파일들을 백업하는 것을 권장합니다
4. 대용량 파일 처리 시 메모리 사용량에 주의하세요

## 🚀 빠른 시작

```bash
# 프로젝트 루트로 이동
cd /path/to/Predictive-Coding

# BAR 파일을 TR 형식으로 변환
python scripts/transform_bar_files.py

# Serialize 데이터셋 추출
python scripts/extract_serialize_datasets.py
``` 