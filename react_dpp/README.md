# 현대제철 DPP 공정 스케줄표 웹 애플리케이션

현대제철 DPP 공정 스케줄표를 웹 애플리케이션으로 구현한 프로젝트입니다. 기존 Excel 형식의 스케줄표와 완전히 동일한 UI를 제공하며, 직관적인 키보드 조작을 통해 효율적인 스케줄 관리가 가능합니다.

## 🚀 주요 기능

### ⌨️ 키보드 조작
- **클릭 선택**: 스케줄 바를 클릭하여 선택 (파란색 테두리 표시)
- **Shift + ← / →**: startTime 1시간 단위 이동 (날짜 경계 자동 처리)
- **Shift + ↑ / ↓**: 공정라인 이동 (No.1 ↔ No.2)
- **← / →**: 지속시간 1시간 단위 조정 (최소 1시간)
- **ESC**: 선택 해제
- **정밀 제어**: 1시간 단위로 정확한 시간 관리

### 📅 스케줄 관리
- **다양한 뷰모드**: 1주~4주 단위 스케줄 표시
- **날짜 경계 처리**: 0시 이전 → 전날 23시, 24시 이후 → 다음날 0시 자동 이동
- **범위 제한**: 설정된 날짜 범위를 벗어나지 않도록 제한
- **실시간 업데이트**: 키보드 조작 시 즉시 화면 반영
- **시각적 피드백**: 선택된 아이템에 파란색 테두리 및 그림자 효과

### 💾 데이터 관리
- **수동 저장**: 저장 버튼을 통한 명시적 저장
- **초기화 기능**: 변경사항을 초기 상태로 되돌리기
- **저장 상태 표시**: "변경사항 있음", "저장됨" 상태 실시간 표시
- **데이터베이스 기반**: PostgreSQL 데이터베이스에 모든 데이터 영구 저장

### 📝 생산 정보 편집
- **압연일정**: 날짜별 실시간 편집 가능
- **미교정**: 품질 관리 정보 입력
- **당진이관재**: 이관 정보 관리
- **빌렛**: 원료 정보 관리

### 🎨 사용자 경험
- **반응형 디자인**: 화면 크기에 따른 동적 셀 너비 조정
- **한국어 지원**: 요일 표시 (일, 월, 화, 수, 목, 금, 토)
- **주말 하이라이트**: 토요일, 일요일 배경색 구분
- **인쇄 최적화**: A4 가로 인쇄에 최적화된 레이아웃
- **로컬 폰트**: Paperlogy 폰트 사용으로 일관된 디자인

## 🛠 기술 스택

### Frontend
- **프레임워크**: Next.js 15.3.3 (App Router)
- **언어**: TypeScript 5.x
- **React**: React 19.0.0 (최신 안정 버전)
- **스타일링**: Tailwind CSS 4.x (PostCSS 통합)
- **상태 관리**: Zustand 5.x (persist middleware)
- **UI 컴포넌트**: Radix UI (Headless 컴포넌트 라이브러리)
- **아이콘**: Heroicons 2.x, Lucide React
- **테마**: next-themes (다크/라이트 모드)

### Backend & Database
- **API**: Next.js API Routes (서버리스 함수)
- **데이터베이스**: PostgreSQL 13 (Docker 컨테이너)
- **ORM**: Prisma 6.9.0 (타입 안전 데이터베이스 클라이언트)
- **마이그레이션**: Prisma Migrate (자동 스키마 마이그레이션)
- **HTTP 클라이언트**: Axios 1.9.0

### Database Infrastructure
- **컨테이너화**: Docker Compose (개발 환경)
- **데이터베이스 이미지**: postgres:13
- **포트 매핑**: 5434:5432 (호스트:컨테이너)
- **데이터 영속성**: Docker Volume (postgres_data)
- **환경 변수**: DATABASE_URL 기반 연결 관리

### Data Management
- **테이블 구조**: TanStack Table 8.x (정렬, 필터링)
- **파일 업로드**: CSV 파일 처리 (PapaParse)
- **실시간 상태**: 로컬 상태 + 서버 동기화
- **데이터 검증**: Prisma Schema 기반 타입 안전성

### Development & Build
- **패키지 매니저**: npm
- **개발 서버**: Next.js Dev (Turbopack 지원)
- **린터**: ESLint 9.x (Next.js 설정)
- **타입 체킹**: TypeScript strict mode
- **빌드 도구**: Next.js built-in bundler
- **CSS 처리**: PostCSS with Tailwind CSS

### UI/UX Framework
- **디자인 시스템**: shadcn/ui (Radix UI 기반)
- **알림**: Sonner (토스트 알림)
- **스타일 유틸리티**: clsx, tailwind-merge, class-variance-authority
- **애니메이션**: tw-animate-css

### 커스텀 구현
- **키보드 조작**: 커스텀 이벤트 리스너 기반 스케줄 제어
- **상태 관리**: Zustand persist로 설정 데이터 브라우저 저장
- **그리드 시스템**: HTML table 기반 완벽 정렬 및 인쇄 최적화
- **드래그 앤 드롭**: 직관적인 스케줄 바 조작 인터페이스

## 🎯 데이터 모델

데이터 모델은 `prisma/schema.prisma` 파일에 정의되어 있으며, 데이터베이스 스키마의 실제 소스입니다.

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Order {
  id              Int            @id @default(autoincrement())
  processOrder    String
  startTime       DateTime
  durationHours   Int
  quantityTon     Float
  description     String
  processLine     String // "No.1" or "No.2"
  grade           String
  period          String
  quantity        Int
  orderVersions   OrderVersion[]
}

model OrderVersion {
  id              Int      @id @default(autoincrement())
  orderId         Int
  order           Order    @relation(fields: [orderId], references: [id])
  version         Int
  changes         Json
  createdAt       DateTime @default(now())
}

model ProductionInfo {
  id            String   @id @default(uuid())
  date          DateTime @unique
  rolling       String
  uncorrected   String
  transfer      String
  billet        String
}
```

## 🚀 시작하기

### A) Docker 사용 (권장)

1.  **Docker 실행**: Docker Desktop을 실행합니다.
2.  **컨테이너 실행**: 프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 PostgreSQL 컨테이너를 시작합니다.
    ```bash
    docker-compose up -d
    ```
3.  **환경 변수 설정**: 프로젝트 루트에 `.env` 파일을 생성하고, Docker 컨테이너에 맞는 데이터베이스 연결 정보를 추가합니다.
    ```
    # .env
    DATABASE_URL="postgresql://kenny:securepass@localhost:5434/my_project_db?schema=public"
    ```
4.  **데이터베이스 동기화**: 다음 명령어를 실행하여 Prisma 스키마를 데이터베이스에 적용합니다.
    ```bash
    npx prisma db push
    ```
5.  **애플리케이션 설치 및 실행**:
    ```bash
    npm install
    npm run dev
    ```

### B) 로컬 데이터베이스 직접 설치

1.  **PostgreSQL 설치**: 로컬 환경에 PostgreSQL을 설치하고 실행합니다.
2.  **데이터베이스 생성**: `my_project_db` 이름의 데이터베이스와 `kenny` 사용자(비밀번호: `securepass`)를 생성합니다.
3.  **환경 변수 설정**: 프로젝트 루트에 `.env` 파일을 생성하고, 로컬 데이터베이스 연결 정보를 추가합니다. (포트 등은 로컬 환경에 맞게 수정)
    ```
    # .env
    DATABASE_URL="postgresql://kenny:securepass@localhost:5432/my_project_db?schema=public"
    ```
4.  **데이터베이스 동기화 및 실행**: 위 Docker 설정의 4, 5번 단계를 동일하게 진행합니다.

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

## 📁 프로젝트 구조

```
.
├── app/
│   ├── api/
│   ├── globals.css
│   └── page.tsx
├── components/
│   ├── layout/
│   ├── pages/
│   └── schedule/
├── prisma/
│   └── schema.prisma         # Prisma 데이터베이스 스키마
├── public/
│   └── fonts/
├── stores/
│   ├── scheduleStore.ts
│   └── settingsStore.ts
├── .env.example              # 환경 변수 예제 파일
├── docker-compose.yml        # Docker 설정 파일
├── package.json              # 프로젝트 의존성
└── README.md
```

## 📖 사용법

### 기본 조작
1. **아이템 선택**: No.1, No.2 스케줄 바를 클릭하여 선택 (파란색 테두리 표시)
2. **시간 이동**: `Shift + ← / →`로 1시간 단위 시간 이동
3. **라인 이동**: `Shift + ↑ / ↓`로 No.1 ↔ No.2 공정라인 이동  
4. **지속시간 조정**: `← / →`로 1시간 단위 지속시간 증감
5. **선택 해제**: `ESC`키로 선택 해제
6. **생산 정보 편집**: 하단의 압연일정, 미교정, 당진이관재, 빌렛 섹션에서 직접 편집

### 저장 및 관리
- **수동 저장**: "저장" 버튼 클릭으로 즉시 저장
- **초기화**: "초기화" 버튼으로 변경사항을 초기 상태로 되돌리기
- **저장 상태**: 우상단에서 저장 상태 실시간 확인
