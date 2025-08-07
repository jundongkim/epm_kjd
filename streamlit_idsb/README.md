# EcoPro BM iDSB 프로젝트

## 프로젝트 개요
본 프로젝트는 배터리 제조 공정 데이터를 생성하고 시각화하는 도구입니다. 여러 모듈(ICP, SEM_EDS, CMMS, 반가폭, 공정관리이력)을 통해 실제 생산 환경에서 발생할 수 있는 데이터와 유사한 테스트 데이터셋을 생성합니다. 각 모듈은 배터리 제조 공정의 다양한 측면을 시뮬레이션하고 분석하는 기능을 제공합니다.

## 주요 기능
- 배터리 제조 공정 데이터 생성 및 시각화
- 공정 단계별 시간, 품질 지표 분석
- 장비 유지보수 데이터 관리 및 분석
- 물질 분석 결과 시뮬레이션
- 결정 구조 분석 데이터 생성
- AI 기반 유지보수 및 공정관리 챗봇

## 파일 구조
```
EcoPro_iDSB/
├── app.py                       # 메인 Streamlit 앱
├── .streamlit/                  # Streamlit 설정
├── components/                  # UI 컴포넌트
│   ├── landing_page.py          # 랜딩 페이지 컴포넌트
│   ├── chat_widget.py           # 채팅 위젯 컴포넌트
│   ├── cmms/                    # CMMS 관련 컴포넌트
│   ├── sem_eds/                 # SEM-EDS 관련 컴포넌트
│   ├── process/                 # 공정관리이력 관련 컴포넌트
│   ├── statistics/              # 통계 관련 컴포넌트
│   ├── fwhm_*.py                # 반가폭 관련 컴포넌트
│   └── icp_*.py                 # ICP 관련 컴포넌트
├── utils/                       # 유틸리티 함수
│   ├── data_loader.py           # 데이터 로드 유틸리티
│   └── style.py                 # UI 스타일 관련 유틸리티
├── models/                      # 모델 관련 파일
├── ICP/                         # ICP 모듈
│   ├── lot_data_generator.py    # Lot 데이터 생성
│   ├── lot_visualization.py     # Lot 시각화
│   ├── lot_analysis.py          # Lot 분석
│   └── lot_visualization/       # Lot 시각화 결과
├── SEM_EDS/                     # SEM_EDS 모듈
│   ├── images/                  # SEM 이미지
│   ├── json/                    # EDS 데이터 JSON
│   └── reports/                 # 분석 보고서
├── CMMS/                        # CMMS 모듈
│   ├── 1_pdf_to_json_converter.py # PDF 변환 도구
│   ├── 2_view_json_results.py   # JSON 결과 조회
│   ├── image_analyzer.py        # 이미지 분석기
│   ├── vector_db/               # 벡터 데이터베이스
│   ├── models/                  # CMMS 관련 모델
│   └── output/                  # 출력 파일
├── FWHM/                        # 반가폭(FWHM) 모듈
│   ├── 1_generate_data.py       # 데이터 생성
│   ├── 2_training_catboost.py   # CatBoost 모델 학습
│   ├── 3_training_xgboost.py    # XGBoost 모델 학습
│   ├── models_cbm/              # CatBoost 모델 저장소
│   ├── models_xgb/              # XGBoost 모델 저장소
│   ├── plots_cbm/               # CatBoost 시각화
│   ├── plots_xgb/               # XGBoost 시각화
│   └── visualization/           # 기타 시각화
├── PROCESS/                     # 공정관리이력 모듈
├── fonts/                       # 커스텀 폰트
├── logo/                        # 로고 이미지
├── optimization_results/        # 최적화 결과
├── samples/                     # 샘플 데이터
├── pyproject.toml               # Poetry 의존성 관리 파일
├── poetry.lock                  # Poetry 의존성 잠금 파일
└── README.md
```

## 설치 및 요구사항

### Poetry를 이용한 설치 (권장)
이 프로젝트는 [Poetry](https://python-poetry.org)를 사용하여 의존성을 관리합니다. Poetry가 설치되어 있지 않다면 먼저 설치하세요.

```bash
# Poetry 설치
curl -sSL https://install.python-poetry.org | python3 -

# 프로젝트 디렉토리로 이동
cd ecopro_idsb

# 의존성 설치
poetry install
```

Poetry는 프로젝트에 필요한 모든 패키지를 `pyproject.toml` 파일에 정의된 대로 설치합니다. 주요 의존성은 다음과 같습니다:

- pandas, numpy: 데이터 처리 및 분석
- matplotlib, seaborn, altair, plotly: 데이터 시각화
- streamlit: 인터랙티브 대시보드 UI
- flask, flask-cors: API 서비스
- langchain 관련 패키지: 자연어 처리 및 AI 모델 연동
- catboost, xgboost, torch: 머신러닝 및 딥러닝
- rdflib: 온톨로지 및 지식 그래프 처리
- sentence-transformers, faiss-cpu: 임베딩 및 벡터 검색

## 대시보드 실행 방법

대시보드는 Streamlit을 기반으로 구현되었으며, 다음 명령어로 실행할 수 있습니다:

```bash
poetry run streamlit run app.py
```

대시보드는 기본적으로 http://localhost:8501 에서 접근할 수 있습니다.

## 대시보드 메뉴 소개

EcoPro BM iDSB 대시보드는 다음과 같은 주요 모듈을 포함하고 있습니다:

### 1. ICP (Inductively Coupled Plasma) 예측 모듈
배터리 제조 공정 중 주요 원소 농도를 예측하여 실시간 품질 관리를 지원하는 모듈입니다.

- **핵심 목표**: 각 공정(1, 2, 3차)의 QPC(Quick Process Control) 데이터를 기반으로 **ICP 분석 값(원소 농도)을 예측**합니다.
- **배경**: ICP 분석은 원소 농도를 정확하게 측정하지만 시간과 비용이 많이 소요됩니다. 이 모듈은 QPC 데이터를 활용하여 ICP 값을 신속하게 예측함으로써, **실시간 품질 관리** 및 **이상 감지**를 가능하게 합니다.
- **주요 기능**:
  - QPC 데이터 기반 ICP 값 예측 모델링
  - 예측된 ICP 값 기반 실시간 공정 모니터링
  - Lot 데이터 시각화 및 분석
  - 잠재적 품질 이슈 조기 경보

### 2. SEM-EDS (주사전자현미경 및 에너지분산형분광법) 모듈
배터리 소재의 미세구조 및 원소 조성을 분석합니다.

- **주요 기능**:
  - SEM 이미지 분석
  - EDS 스펙트럼 분석
  - 원소 매핑 시각화
  - 통합 분석 보고서 생성

- **SEM-EDS 분석 프로세스**:
  - 시료 준비 → 전자빔 조사 → 신호 생성 → SEM 형태 이미지/EDS 원소 조성 → 통합 분석

### 3. CMMS (Computerized Maintenance Management System) 모듈
설비 유지보수 및 관리를 위한 AI 지원 시스템입니다.

- **주요 기능**:
  - 유지보수 챗봇 인터페이스
  - 작업 이미지 관리 및 분석
  - 유사 케이스 검색 및 통계
  - 문서 기반 의미론적 분석

- **CMMS 순환형 스마트 유지보수 프로세스**:
  - 계획 → 실행 → 분석 → 개선의 순환 구조
  - AI 의사결정 지원 시스템을 통한 최적화

### 4. 반가폭(FWHM, Full Width at Half Maximum) 모듈
X선 회절 패턴의 반가폭 데이터를 분석하고 예측합니다.

- **주요 기능**:
  - 데이터 생성 및 개요 시각화
  - 특성 중요도 평가
  - CatBoost 및 XGBoost 기반 예측 모델
  - 대화형 시뮬레이션 도구

- **반가폭 분석 프로세스**:
  - 데이터 생성 → 모델 학습 → 특성 분석 → 결과 시각화 → 시뮬레이션

### 5. 공정관리이력 모듈
공정 관리 이력을 효율적으로 검색하고 분석할 수 있는 AI 기반 시스템입니다.

- **주요 기능**:
  - 공정 관리 챗봇 인터페이스
  - 유사 케이스 검색
  - 텍스트 기반 지식 검색

- **공정관리이력 분석 프로세스**:
  - 문서 색인화 → 임베딩 생성 → 벡터 DB 구축 → 검색 및 질의응답

## 모듈별 데이터 설명

### 1. ICP 모듈 데이터
- **QPC 데이터**: 각 공정 단계(1, 2, 3차)에서 빠르게 측정 가능한 공정 변수들 (온도, 압력, 시간, 유량 등).
- **Target ICP 데이터**: 실제 ICP 분석을 통해 측정된 목표 원소(예: Ni, Co, Mn 등)의 농도 값 (예측 모델의 Target 값으로 사용).
- **예측 데이터**: QPC 데이터를 기반으로 모델이 예측한 ICP 값.
- **Lot 데이터**: 각 Lot의 공정 단계별 시작 및 종료 시간, 품질 지표 등 (컨텍스트 정보로 활용).

### 2. SEM-EDS 모듈 데이터
- **SEM 데이터**: 입자 크기, 형태, 분포 등의 미세구조 특성
- **EDS 데이터**: 원소 조성비, 분포, 매핑 데이터
- **통합 분석 결과**: SEM과 EDS 분석 결과를 통합한 소재 특성 데이터

### 3. CMMS 모듈 데이터
- **장비 정보**: 장비 ID, 유형, 위치, 설치일 등의 기본 정보
- **유지보수 이력**: 예방 정비, 고장 정비, 점검 등의 유지보수 활동 기록
- **고장 데이터**: 고장 유형, 원인, 조치 내용, 다운타임 등의 정보
- **부품 관리**: 부품 재고, 교체 주기, 비용 등의 정보
- **이미지 데이터**: 작업 사진 및 분석 이미지

### 4. 반가폭 모듈 데이터
- **XRD 데이터**: 2θ 각도, 강도, 피크 위치 등의 기본 회절 데이터
- **반가폭 측정값**: 주요 피크의 반가폭 수치
- **결정 크기**: Scherrer 방정식을 통해 계산된 결정 크기
- **결정성 지표**: 반가폭 기반 결정성 평가 지표
- **예측 모델 결과**: CatBoost 및 XGBoost 모델 기반 예측 결과 및 비교

### 5. 공정관리이력 모듈 데이터
- **공정 문서**: 공정 관련 매뉴얼, 지침서, 보고서 등
- **관리 이력**: 공정 변경 이력, 이상 발생 및 조치 기록
- **설비 관련 정보**: 설비 운영 조건, 파라미터 조정 내역 등

## 기술 스택

이 프로젝트는 다음과 같은 주요 기술을 활용합니다:

- **프론트엔드**: Streamlit, Altair, Plotly, Matplotlib, Seaborn
- **백엔드**: Flask, Python
- **데이터 분석**: Pandas, NumPy
- **머신러닝**: CatBoost, XGBoost, PyTorch
- **AI 및 NLP**: LangChain, Sentence-Transformers, HuggingFace, FAISS
- **온톨로지 및 지식 그래프**: RDFLib, NetworkX

## 프로젝트 특징

1. **통합 데이터 분석**: 여러 모듈의 데이터를 통합하여 배터리 제조 공정의 다양한 측면을 종합적으로 분석할 수 있습니다.
2. **실제 공정 시뮬레이션 및 예측**: 실제 배터리 제조 공정과 유사한 데이터를 생성하고, QPC 데이터를 통해 **핵심 품질 지표(ICP 값)를 예측**하여 선제적 품질 관리를 지원합니다.
3. **모듈식 구조**: 각 모듈은 독립적으로 사용할 수 있으며, 필요에 따라 통합하여 사용할 수 있습니다.
4. **AI 기반 상호작용**: 챗봇 인터페이스를 통해 유지보수 및 공정 관리 데이터에 쉽게 접근하고 질의할 수 있습니다.
5. **대화형 시뮬레이션**: 반가폭 모듈의 대화형 시뮬레이션 도구를 통해 다양한 파라미터 변화에 따른 결과를 실시간으로 확인할 수 있습니다.

## 활용 방안

- 배터리 제조 공정 모니터링 시스템 개발
- 공정 효율성 분석 및 개선점 도출
- 품질 예측 모델 구축
- 설비 유지보수 최적화
- 소재 특성과 제품 품질 간의 상관관계 분석
- AI 기반 의사결정 지원 시스템 구축

## 라이센스
이 프로젝트는 미소정보기술 소유입니다. 무단 복제 및 배포를 금지합니다.

