# DX-AI Manufacturing Copilot - 완전 가이드

🚀 **설치부터 사용까지 모든 것을 하나의 문서로**

## 📋 준비사항

- **Docker & Docker Compose**: 최신 버전
- **Python 3.11+**, **Node.js 18+**
- **포트**: 80, 3000, 5678, 8000 사용 가능

### 🔧 XGBoost ML 모델 사전 요구사항

XGBoost 모델 실행을 위해 **시스템 레벨 의존성**이 필요합니다:

#### macOS:
```bash
# OpenMP 라이브러리 설치 (XGBoost 필수 의존성)
brew install libomp
```

#### Linux (Ubuntu/Debian):
```bash
# OpenMP 개발 라이브러리 설치
sudo apt-get update
sudo apt-get install libomp-dev
```

#### Windows:
```bash
# XGBoost 패키지 재설치 (시스템 의존성 문제 해결)
pip uninstall xgboost
pip install xgboost
```

⚠️ **주의**: OpenMP 의존성이 없으면 XGBoost 모델 로딩 시 런타임 오류가 발생할 수 있습니다.

## 🎯 1단계: 프로젝트 클론 및 기본 구조 설정

```bash
# 1. 메인 프로젝트 클론
git clone [repository-url] && cd epm

# 2. 디렉토리 구조 확인
ls -la  # dify/, n8n/, backend/, frontend/ 등 확인
```

## 🔧 2단계: dify 및 n8n 서비스 설치

### dify AI Platform 설치
```bash
# dify 공식 저장소 클론 (dify 폴더에)
rm -rf dify  # 기존 빈 폴더가 있다면 제거
git clone https://github.com/langgenius/dify.git

# dify 환경 설정 파일 복사
cd dify/docker
cp middleware.env.example .env
cd ../..
```

**⚠️ 중요 참고사항**:
- dify 첫 설치 시 **5-10분 소요** (Docker 이미지 다운로드)
- **최소 4GB RAM** 권장 (10개 컨테이너 실행)
- 포트 80 사용으로 **기존 웹서버와 충돌 가능**

### n8n 워크플로우 설치 (이미 설정됨)
```bash
# n8n 설정은 이미 프로젝트에 포함됨
ls n8n/docker-compose.yml  # 설정 파일 확인

# n8n 데이터 폴더 생성
mkdir -p n8n/data
```

## 🚀 3단계: Docker 서비스 시작

```bash
# 모든 서비스 한 번에 시작
chmod +x start-services.sh && ./start-services.sh

# 서비스 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(dx-ai-n8n|dify-)"
```

**예상 결과**: n8n(1개) + dify(10개) 컨테이너 모두 실행 중

### 설치 확인
```bash
# 컨테이너 실행 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 서비스 접속 테스트
curl -f http://localhost:5678 > /dev/null && echo "✅ n8n 정상 작동" || echo "❌ n8n 접속 실패"
curl -f http://localhost > /dev/null && echo "✅ dify 정상 작동" || echo "❌ dify 접속 실패"
```

### 개별 서비스 시작 (문제 발생 시)
```bash
# n8n만 시작
cd n8n && docker compose up -d && cd ..

# dify만 시작  
cd dify/docker && docker compose -p dify up -d && cd ../..

# 로그 확인
docker logs dx-ai-n8n-workflow  # n8n 로그
docker logs dify-api-1          # dify API 로그
```

## 🔧 4단계: 계정 및 API 키 설정

### n8n 설정
1. **http://localhost:5678** 접속
2. **계정 생성**: admin@company.com / Admin123!
3. **API 키 생성**: Settings → API Keys → Create API Key → **복사**

### Dify 설정  
1. **http://localhost** 접속
2. **계정 생성**: admin@company.com / Admin123!
3. **앱 생성**: Create New App → Chatbot → Manufacturing Copilot
4. **API 키 복사**: API 탭에서 API Key 복사

## 🖥️ 5단계: 백엔드/프론트엔드 실행

### 백엔드 설정 및 실행
```bash
cd backend

# Python 의존성 설치 (Poetry 사용)
# Poetry가 없다면: curl -sSL https://install.python-poetry.org | python3 -
poetry install

# 또는 pip 사용 시
# pip install -r requirements.txt  # requirements.txt가 있다면

# 환경 변수 설정 (.env 파일 생성)
cat > .env << EOF
DIFY_API_URL=http://localhost/console/api
DIFY_CONSOLE_API_KEY=app-xxxxxxxxxx  # Dify에서 복사한 키
N8N_API_URL=http://localhost:5678/api  
N8N_API_KEY=n8n_xxxxxxxxxx           # n8n에서 복사한 키
DEBUG=True
EOF

# 백엔드 실행
poetry run python main.py
# 또는 가상환경 활성화 후: python main.py
```

### 프론트엔드 실행
```bash
# 새 터미널에서
cd frontend && npm install && npm run dev
```

## ✅ 6단계: 연동 테스트

### 서비스 접속 확인
| 서비스 | URL | 상태 |
|--------|-----|------|
| **Frontend** | http://localhost:3000 | 메인 UI |
| **Backend** | http://localhost:8000/docs | API 문서 |
| **Dify Console** | http://localhost | AI 관리 |
| **n8n** | http://localhost:5678 | 워크플로우 |

### 기능 테스트
```bash
# n8n 웹훅 테스트
curl -X POST "http://localhost:5678/webhook/test-webhook" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "user": "Admin"}'

# Dify API 키 검증
curl -X POST "http://localhost:8000/api/v1/dify-agent/validate-key" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-dify-api-key"}'
```

## 🎯 7단계: 실제 사용하기

### AI 제조 상담 테스트
1. **Frontend**: http://localhost:3000
2. **AI Agent 페이지** 이동  
3. **Dify API 키 입력** 후 테스트 메시지 전송

### 제조 데이터 처리 테스트
```bash
curl -X POST "http://localhost:5678/webhook/manufacturing-data" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 250,
    "pressure": 3.5, 
    "quality": 85,
    "batchId": "BATCH001"
  }'
```

## 📊 시스템 구조

### 서비스 구성
```
Frontend (:3000) ←→ Backend (:8000) ←→ Dify (:80) + n8n (:5678)
```

### 주요 API
| 기능 | 엔드포인트 | 설명 |
|------|------------|------|
| **워크플로우 실행** | `POST /api/v1/workflow/workflows/{id}/execute` | n8n 연동 |
| **AI 메시지** | `POST /api/v1/dify-agent/send-message` | Dify 연동 |
| **API 키 검증** | `POST /api/v1/dify-agent/validate-key` | 설정 검증 |

### n8n 웹훅 URL
- **테스트**: http://localhost:5678/webhook/test-webhook
- **제조 데이터**: http://localhost:5678/webhook/manufacturing-data  
- **API 연동**: http://localhost:5678/webhook/api-test

## 🚨 문제 해결

### Docker 서비스 문제
```bash
# 모든 서비스 재시작
docker stop $(docker ps -q --filter "name=dify") $(docker ps -q --filter "name=dx-ai-n8n")
./start-services.sh
```

### API 키 관련 문제
- **Dify**: Console에서 새 API 키 재생성
- **n8n**: Settings → API Keys에서 재생성
- **백엔드**: .env 파일 내용 확인 후 재시작

### 포트 충돌
```bash
# 포트 사용 확인
lsof -i :80 -i :3000 -i :5678 -i :8000
# 충돌 프로세스 종료 후 재시작
```

### XGBoost 모델 문제
```bash
# OpenMP 라이브러리 오류 시
# macOS
brew install libomp

# Linux
sudo apt-get install libomp-dev

# Windows
pip uninstall xgboost && pip install xgboost

# XGBoost 로딩 테스트
python -c "import xgboost as xgb; print('XGBoost 정상 로딩:', xgb.__version__)"
```

### Python 패키지 문제
```bash
# Poetry 재설치
cd backend && poetry install --no-cache

# 가상환경 재생성
poetry env remove python && poetry install

# pip 사용 시
pip install --upgrade --force-reinstall xgboost scikit-learn pandas numpy
```

### 로그 확인
```bash
# Docker 로그
docker logs dx-ai-n8n-workflow
docker logs dify-api-1
# 백엔드/프론트엔드 로그는 터미널에서 확인
```

## 📋 완료 체크리스트

### 🔧 설치 단계
- [ ] **준비사항**: XGBoost 시스템 의존성 설치 (OpenMP: macOS=libomp, Linux=libomp-dev)
- [ ] **1단계**: 메인 프로젝트 클론 완료
- [ ] **2단계**: dify 공식 저장소 클론 완료 
- [ ] **2단계**: n8n 폴더 및 데이터 디렉토리 확인
- [ ] **3단계**: Docker 서비스 11개 모두 실행 중 (n8n 1개 + dify 10개)
- [ ] **3단계**: 서비스 접속 테스트 성공 (localhost, localhost:5678)

### ⚙️ 설정 단계  
- [ ] **4단계**: n8n 계정 생성 및 API 키 발급
- [ ] **4단계**: Dify 계정 생성 및 앱 API 키 발급
- [ ] **5단계**: Python 패키지 설치 (Poetry install) 및 XGBoost 로딩 테스트 성공
- [ ] **5단계**: 백엔드 .env 설정 및 서버 실행 (포트 8000)
- [ ] **5단계**: 프론트엔드 npm install 및 서버 실행 (포트 3000)

### ✅ 테스트 단계
- [ ] **6단계**: n8n 웹훅 테스트 성공
- [ ] **6단계**: Dify API 키 검증 성공  
- [ ] **7단계**: AI Agent에서 메시지 송수신 성공

## 🎉 완료!

축하합니다! 🎊 DX-AI Manufacturing Copilot이 완전히 설정되었습니다.

### 다음 단계
- **커스텀 워크플로우 개발** (n8n 웹 인터페이스 사용)
- **실제 제조 데이터 연동**
- **AI 에이전트 고도화** (Dify Console 사용)

### 고급 기능
- **n8n 워크플로우 편집**: http://localhost:5678에서 드래그앤드롭으로 복잡한 자동화 구축
- **Dify AI 에이전트**: http://localhost에서 대화형 AI 모델 관리 및 훈련
- **API 연동**: Backend API 문서(http://localhost:8000/docs)에서 모든 엔드포인트 확인

문제 발생 시 위의 문제 해결 섹션을 참고하세요! 🚀 