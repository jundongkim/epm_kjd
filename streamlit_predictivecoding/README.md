# Predictive Coding - Real-time AI Simulation Platform

🧠 **실시간 예측 코딩 시뮬레이션 및 MLFT 3D 시각화 플랫폼**

고급 예측 코딩 모델들을 실시간으로 시뮬레이션하고, MLFT(Multi-Layer Frequency Transform) 데이터를 3D 원통형으로 시각화하는 통합 플랫폼입니다.

## 🎯 주요 기능

### 1. 📊 예측 코딩 모델 시뮬레이션
8가지 고급 예측 코딩 모델을 실시간으로 시뮬레이션:

| 모델 | 복잡도 | 주요 특징 |
|------|---------|-----------|
| **Basic** | 1.0 | 기본 가우시안 필터 기반 예측 |
| **Hierarchical** | 3.0 | 다층 계층적 예측 구조 |
| **Event-Driven** | 1.5 | 이벤트 기반 스파스 예측 |
| **Precision-Weighting** | 2.0 | 정밀도 가중 예측 모델 |
| **Deep Hierarchical** | 5.0 | 깊은 계층 구조 (3층+) |
| **Adaptive Hierarchical** | 7.5 | 적응형 학습 가중치 |
| **STDP Hierarchical** | 8.0 | 신경가소성 기반 학습 |
| **Active Inference** | 2.5 | FFT 기반 능동 추론 |

### 2. 🔬 MLFT 3D 시각화
전문 산업용 MLFT 데이터를 3D 원통형으로 시각화:

#### 시각화 유형
- **🎯 Basic 3D**: 포인트 + 트랙 시각화
- **🌊 3D Surface**: 부드러운 표면 렌더링
- **🔄 Combined**: 표면 + 포인트 + 트랙 통합
- **🎨 Complete Surface**: CH-A1↔CH-B5 연결 표면
- **✨ Smooth Surface**: 채널 보간 (5x-10x)
- **🚀 Ultra-Smooth**: 채널 + 포인트 보간 (최대 20x)
- **📊 Heatmap**: 2D 전개 히트맵

#### 고급 기능
- **⚡ 병렬 처리**: 다중 코어 활용 (최대 효율성)
- **🎨 테마**: 10가지 전문 색상 테마 (철강, 구리 등)
- **📏 범위 선택**: 특정 포인트 범위 시각화
- **💾 성능 최적화**: 메모리 및 CPU 최적화

### 3. 📈 고급 성능 분석
실시간 성능 모니터링 및 분석:

#### 계산 성능 지표
- **⏱️ Total Time**: 시뮬레이션 총 소요 시간
- **🚀 Throughput**: 초당 처리 데이터 포인트 수
- **💾 Peak Memory**: 최대 메모리 사용량 (MB)
- **🔢 Total Operations**: 총 계산 연산 수
- **📊 Complexity Score**: 모델별 상대적 복잡도

#### 성능 벤치마크
```
🟢 > 1000 pts/s    우수 (실시간 처리)
🟡 100-1000 pts/s  양호 (준실시간)  
🟠 10-100 pts/s    보통 (배치 처리)
🔴 < 10 pts/s      느림 (복잡 모델)
```

### 4. 📁 데이터 처리 스크립트
독립 실행 가능한 데이터 처리 도구들:

- **📊 BAR File Transform**: BAR → TR 형식 변환
- **🔄 Serialize Extraction**: 순환 패턴 기반 직렬화 추출
- **✅ Data Validation**: 데이터 무결성 검증

## 🏗️ 프로젝트 구조

```
Predictive-Coding/
├── 🎯 app.py                          # 메인 Streamlit 애플리케이션
├── ⚙️ config.py                       # 전역 설정 및 상수
├── 📦 pyproject.toml                  # 패키지 설정 (Poetry)
├── 📖 README.md                       # 이 문서
│
├── 🧠 pc_lib/                         # 예측 코딩 라이브러리
│   ├── 🤖 models.py                   # 8가지 예측 코딩 모델 구현
│   ├── 📊 data_loader.py             # 데이터 로딩 및 시나리오 생성
│   ├── 🎮 model_runner.py            # 모델 실행 및 관리
│   ├── 📈 visualization.py           # 결과 시각화 및 분석
│   ├── 🎲 scenarios.py               # 시뮬레이션 시나리오
│   └── 🛠️ utils.py                   # 유틸리티 함수
│
├── 🎨 visualization/                  # 시각화 모듈
│   ├── 🌐 cylindrical_3d.py         # 3D 원통형 MLFT 시각화
│   └── 🎛️ ui_components.py           # Streamlit UI 컴포넌트
│
├── 🔧 utils/                          # 유틸리티 모듈
│   ├── ⚡ performance_utils.py       # 성능 모니터링 및 최적화
│   └── 🎮 simulation_engine.py       # 시뮬레이션 엔진
│
├── 📜 scripts/                        # 독립 실행 스크립트
│   ├── 📖 README.md                  # 스크립트 사용법
│   ├── 🔄 transform_bar_files.py    # BAR 파일 변환
│   └── 📊 extract_serialize_datasets.py # 직렬화 데이터 추출
│
├── 💾 data/                          # 데이터 저장소
│   └── 🏭 iot/                       # IoT/MLFT 데이터 파일
│
├── 🎨 fonts/                         # 사용자 정의 폰트
├── 💾 backup/                        # 백업 파일
├── 📚 docs/                          # 추가 문서
└── 🧪 test/                          # 테스트 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/your-repo/Predictive-Coding.git
cd Predictive-Coding

# Poetry를 사용한 의존성 설치 (권장)
poetry install
poetry shell

# 또는 pip 사용
pip install streamlit==1.35.0 numpy==1.26.4 pandas==2.3.0 plotly==5.22.0 \
           scipy==1.15.3 psutil==7.0.0 scikit-learn==1.7.0 tqdm==4.67.1
```

### 2. 애플리케이션 실행

```bash
# 메인 애플리케이션 실행
streamlit run app.py

# 사용자 정의 포트로 실행
streamlit run app.py --server.port 8502
```

### 3. 브라우저 접속
```
http://localhost:8501
```

## 🎮 사용법

### 예측 코딩 시뮬레이션

1. **🎯 Application Mode**에서 "Predictive Coding Demo" 선택
2. **🤖 모델 선택**: 8가지 모델 중 선택
3. **📊 시나리오 설정**: 
   - Sine Wave (기본)
   - Noisy Sine Wave
   - Multiple Frequencies  
   - Random Walk
   - CSV Upload (사용자 데이터)
4. **⚙️ 파라미터 조정**: sigma, threshold 등
5. **▶️ 시뮬레이션 실행**: "Run Simulation" 버튼

### MLFT 3D 시각화

1. **🎯 Application Mode**에서 "MLFT - 3D Cylindrical Visualization" 선택
2. **📁 파일 선택**: BAR 또는 TR 파일 선택
3. **🎨 시각화 옵션**:
   - 시각화 유형 (8가지)
   - 방향 (수직/수평)
   - 색상 테마 (10가지)
   - 보간 설정 (채널 5x, 포인트 1x-20x)
4. **⚡ 성능 설정**: 병렬 처리, 워커 수 조정

### 독립 스크립트 실행

```bash
# BAR 파일을 TR 형식으로 변환
python scripts/transform_bar_files.py

# 직렬화 데이터셋 추출
python scripts/extract_serialize_datasets.py
```

## 🔧 주요 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| streamlit | 1.35.0 | 웹 애플리케이션 프레임워크 |
| numpy | 1.26.4 | 수치 계산 |
| pandas | 2.3.0 | 데이터 처리 |
| plotly | 5.22.0 | 인터랙티브 시각화 |
| scipy | 1.15.3 | 과학 계산 (필터링, 보간) |
| scikit-learn | 1.7.0 | 머신러닝 (성능 평가) |
| psutil | 7.0.0 | 시스템 성능 모니터링 |
| tqdm | 4.67.1 | 진행률 표시 |

## ⚡ 성능 최적화 기능

### 1. 메모리 최적화
- **스트리밍 처리**: 대용량 데이터 청크 단위 처리
- **조건부 캐싱**: Streamlit 런타임 상태에 따른 지능형 캐싱
- **메모리 모니터링**: 실시간 메모리 사용량 추적

### 2. 계산 최적화
- **병렬 처리**: 3D 보간 시 다중 코어 활용
- **NumPy 벡터화**: 효율적인 수치 계산
- **조기 종료**: 성능 임계값 기반 최적화

### 3. 시각화 최적화
- **점 밀도 조절**: 성능에 따른 자동 해상도 조정
- **프레임 스킵**: 실시간 시뮬레이션 최적화
- **선택적 렌더링**: 필요한 요소만 렌더링

## 🎨 MLFT 색상 테마

| 테마 | 설명 | 적용 분야 |
|------|------|-----------|
| 🌿 Viridis | 자연스러운 녹색-파랑 그라데이션 | 일반 목적 |
| 🔩 Steel | 회색-은색 그라데이션 | 특수강 소재 |
| 🔥 Plasma | 보라-주황 그라데이션 | 열처리 공정 |
| 🌋 Inferno | 검정-빨강-노랑 그라데이션 | 용광로 작업 |
| 🔬 Cividis | 색맹 친화적 그라데이션 | 과학적 분석 |
| 💙 Blues | 파랑 그라데이션 | 냉각 공정 |
| ❤️ Reds | 빨강 그라데이션 | 가열 공정 |
| ⚫ Greys | 흑백 모노크롬 | 단색 분석 |
| 🌈 Turbo | 고대비 무지개 | 상세 분석 |
| 🟫 Copper | 갈색-금색 그라데이션 | 구리 합금 |

## 🧪 개발 및 테스트

### 개발 환경 설정
```bash
# Poetry 개발 의존성 설치
poetry install --with dev

# 코드 포맷팅
black .
isort .

# 타입 체크
mypy .

# 테스트 실행
pytest
```

### 프로파일링
```bash
# 성능 프로파일링 활성화하여 실행
ENABLE_PROFILING=1 streamlit run app.py
```

## 📊 시스템 요구사항

### 최소 요구사항
- **Python**: 3.11+
- **RAM**: 4GB
- **CPU**: 2코어
- **디스크**: 1GB 여유 공간

### 권장 사양
- **Python**: 3.11 또는 3.12
- **RAM**: 8GB+ (대용량 MLFT 데이터용)
- **CPU**: 4코어+ (병렬 처리용)
- **디스크**: 5GB+ (데이터 저장용)

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- **Streamlit**: 훌륭한 웹 앱 프레임워크
- **Plotly**: 강력한 시각화 라이브러리
- **NumPy/SciPy**: 과학 계산의 기반
- **Open Source Community**: 지속적인 지원과 개선

---

📧 **문의사항**: gyjong@gmail.com  
🔗 **프로젝트 홈**: [GitHub Repository](https://github.com/your-repo/Predictive-Coding)  
📖 **문서**: [Documentation](docs/)

**⭐ 이 프로젝트가 도움이 되었다면 별표를 눌러주세요!** 