## 프로젝트 개요

현대제철 공정 스케줄표 PDF와 **완전히 동일한** UI를 웹 애플리케이션으로 구현하기 위한 제품 요구 사항 문서(Product Requirements Document, PRD)입니다. 이 애플리케이션은 **TypeScript**와 최신 웹 프레임워크(Next.js 15.x, React 19.x) 기반으로 개발되며, 현재 **v0.1.0** 단계로 진행 중입니다.

---

## 목표

1. **완전 일치성**: 기존 PDF 형식의 공정표 디자인·레이아웃·데이터 표현 방식을 그대로 재현
2. **인터랙티브 기능**: 웹 환경에서 드래그·드롭, 텍스트 편집, 실시간 저장·불러오기
3. **반응형 A4 출력**: 브라우저에서 A4 사이즈(1주~4주 단위) 인쇄 지원
4. **유지보수성**: TypeScript + 컴포넌트 기반 구조로 손쉬운 확장·수정
5. **실시간 협업**: 다중 사용자 환경에서의 동시 편집 지원

---

## 대상 사용자

* 생산 스케줄러, 설비 관리자, 야드 운영자
* 사내 ERP/SCM 시스템과 연계하여 일정 관리 및 커뮤니케이션을 수행하는 실무자
* 현장 관리자 및 품질 관리 담당자

---

## 범위 및 현재 구현 상태

### ✅ 구현 완료
* **다중 뷰 모드**: 1주, 2주, 3주, 4주 단위 스케줄 그리드
* **동적 셀 크기**: 뷰 모드에 따른 자동 셀 폭 조정
* **드래그앤드롭 스케줄바**: `DraggableScheduleBar` 컴포넌트
* **실시간 데이터 편집**: 생산 정보 실시간 입력 및 저장
* **Zustand 상태 관리**: 스케줄 및 설정 상태 중앙 관리
* **API 엔드포인트**: `/api/schedule-data`, `/api/production-data`
* **TypeScript 타입 시스템**: 완전한 타입 안전성

### 🚧 개발 진행 중
* **비조업/비가동 표시**: 셀 배경 색상 및 오버레이
* **공정별 막대 시각화**: TON → 생산시간 역산 로직
* **인쇄 최적화**: A4 브레이크포인트 및 페이지네이션
* **키보드 내비게이션**: 접근성 향상

### 📝 계획 중
* **야드 운영 노트**: 사이드바 메모 기능
* **데이터 내보내기**: Excel/PDF 익스포트
* **사용자 권한 관리**: 역할 기반 접근 제어

---

## 주요 기능 상세

| 구분             | 기능 설명                                                                                                                                              | 구현 상태 |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| **스케줄 그리드**    | - X축: 월/일(date) 표시 (예: 5/21 ~ 5/31)<br>- Y축: 공정번호(No.1, No.2, 5A-15 등)<br>- 동적 셀 크기 조정                                                         | ✅     |
| **시간 단위**      | - 24시간 운영, 한 칸 = 2시간<br>- 뷰 모드별 셀 폭: 1주(40px), 2주(35px), 3주(30px), 4주(25px)                                                                      | ✅     |
| **막대 표시**      | - 생산량(Ton)을 기반으로 계산된 생산시간 → SVG 막대<br>- 드래그앤드롭 리사이징<br>- 공정별 색상 구분                                                                              | 🚧     |
| **비조업/비가동 표시** | - 셀 배경 또는 오버레이로 "비조업""비가동" 텍스트 표시<br>- 주말/공휴일 자동 표시                                                                                              | 🚧     |
| **텍스트 입력**     | - 인라인 편집: rolling, uncorrected, transfer, billet<br>- 실시간 저장 (디바운싱)                                                                               | ✅     |
| **야드 운영 노트**   | - 우측 사이드바 메모 영역<br>- CRUD 지원, 타임스탬프                                                                                                               | 📝     |
| **프린트 스타일**    | - A4 용지 가로 모드<br>- 뷰 모드별 최적화된 레이아웃<br>- 자동 페이지 번호                                                                                                | 🚧     |
| **데이터 관리**     | - REST API 완전 구현<br>- 로컬 스토리지 백업<br>- 변경 사항 추적                                                                                                    | ✅     |

---

## 화면 구성도 (컴포넌트 아키텍처)

### 📁 `/src/components/`
```
components/
├── schedule/
│   ├── SchedulePage.tsx          # 메인 스케줄 페이지 (1,036 lines)
│   ├── ScheduleBar.tsx           # 정적 스케줄 막대
│   └── DraggableScheduleBar.tsx  # 드래그 가능한 스케줄 막대
├── layout/
│   └── Sidebar.tsx               # 사이드바 레이아웃
├── pages/                        # 페이지별 컴포넌트
└── ui/                          # shadcn/ui 컴포넌트 (예정)
```

### 🗂️ 상태 관리 (`/src/stores/`)
```
stores/
├── scheduleStore.ts    # 스케줄 데이터, 뷰 모드, 네비게이션
└── settingsStore.ts    # 사용자 설정, 테마, 공정 색상
```

### 🔌 API Routes (`/src/app/api/`)
```
api/
├── schedule-data/
│   └── route.ts       # 스케줄 아이템 CRUD
└── production-data/
    └── route.ts       # 생산 정보 CRUD
```

---

## 데이터 모델 (TypeScript 인터페이스)

### 현재 구현된 타입들

```typescript
// /src/types/schedule.ts
interface ScheduleItem {
  id: string;
  processNo: string;           // e.g., "5A-15"
  startTime: string;           // ISO DateTime
  durationHours: number;       // 생산시간 (시간 단위)
  quantityTon: number;         // 생산량
  description?: string;        // SIZE·톤수 등
  processLine?: string;        // 공정라인 (No.1, No.2)
}

interface YardNote {
  id: string;
  content: string;
  updatedAt: string;
}

interface ScheduleDateCell {
  date: string;                // YYYY-MM-DD
  isNonWorking: boolean;       // 비조업 여부
  isIdle: boolean;             // 비가동 여부
  items: ScheduleItem[];
}

interface ProcessInfo {
  id: string;
  name: string;                // e.g., "No.1", "No.2", "5A-15"
  color: string;               // 막대 색상
}
```

### 스토어 인터페이스

```typescript
// Zustand 스케줄 스토어
interface ScheduleStore {
  // State
  currentStartDate: string;
  scheduleData: ScheduleDateCell[];
  yardNotes: YardNote[];
  processes: ProcessInfo[];
  selectedItem: ScheduleItem | null;
  viewMode: 'week' | '2weeks' | '3weeks' | '4weeks';
  cellWidth: number;
  
  // Actions (15+ 메서드)
  setCurrentStartDate: (date: string) => void;
  moveToNextPeriod: () => void;
  moveToPrevPeriod: () => void;
  // ... 기타 CRUD 메서드들
}
```

---

## 기술 스택 (현재 구현 버전)

### 🚀 프론트엔드
* **프레임워크**: Next.js 15.3.3 (App Router, Turbopack)
* **언어**: TypeScript 5.x
* **UI 라이브러리**: React 19.x
* **스타일링**: Tailwind CSS 4.x + tw-animate-css
* **상태 관리**: Zustand 5.0.5
* **UI 컴포넌트**: shadcn/ui (new-york style)
* **아이콘**: Lucide React 0.511.0, Heroicons 2.2.0
* **HTTP 클라이언트**: Axios 1.9.0
* **유틸리티**: class-variance-authority, clsx, tailwind-merge

### 🛠️ 개발 도구
* **린터**: ESLint 9.x + Next.js config
* **PostCSS**: @tailwindcss/postcss 4.x
* **타입 검사**: TypeScript strict mode
* **패키지 관리**: npm (package-lock.json 6,314 lines)

### 🏗️ 빌드 및 배포
* **개발 서버**: `next dev --turbopack` (고성능 번들러)
* **빌드**: `next build` (정적 최적화)
* **배포**: Vercel 권장 (계획)

---

## API 명세 (현재 구현)

### 기본 엔드포인트

| 메서드 | 경로 | 설명 | 구현 상태 |
|--------|------|------|----------|
| `GET` | `/api/schedule-data` | 스케줄 데이터 조회 | ✅ |
| `POST` | `/api/schedule-data` | 스케줄 데이터 저장 | ✅ |
| `GET` | `/api/production-data` | 생산 정보 조회 | ✅ |
| `POST` | `/api/production-data` | 생산 정보 저장 | ✅ |

### 요청/응답 예시

```typescript
// GET /api/production-data 응답
{
  "2025-05-21": {
    "rolling": "1200",
    "uncorrected": "150",
    "transfer": "1050",
    "billet": "900"
  },
  // ... 날짜별 데이터
}

// POST /api/schedule-data 요청
[
  {
    "id": "schedule-001",
    "processNo": "5A-15",
    "startTime": "2025-05-21T08:00:00Z",
    "durationHours": 4,
    "quantityTon": 500,
    "processLine": "No.1"
  }
]
```

---

## 성능 최적화 및 기술적 고려사항

### 🎯 최적화 전략
* **메모이제이션**: `useCallback`, `useMemo`로 불필요한 리렌더링 방지
* **가상화**: 대용량 스케줄 데이터 처리를 위한 윈도잉 (계획)
* **디바운싱**: 입력 필드 자동 저장 (300ms 지연)
* **코드 스플리팅**: Next.js 자동 번들 분할
* **이미지 최적화**: Next.js Image 컴포넌트

### 🔒 보안 및 접근성
* **CSP**: Content Security Policy 적용 예정
* **ARIA**: 키보드 내비게이션 및 스크린 리더 지원
* **HTTPS**: 프로덕션 환경 필수
* **데이터 검증**: Zod 스키마 검증 (계획)

### 📱 반응형 지원
* **뷰포트**: 1200px+ 데스크톱 최적화
* **터치**: 모바일 드래그앤드롭 지원
* **프린트**: `@media print` 스타일 최적화

---

## 마일스톤 및 개발 일정 (업데이트)

| 단계 | 기간 | 주요 산출물 | 진행 상태 |
|------|------|-------------|-----------|
| **Phase 1: 핵심 기능** | 2주 | 스케줄 그리드, 기본 CRUD | ✅ 완료 |
| **Phase 2: 고급 기능** | 2주 | 드래그앤드롭, 막대 시각화 | 🚧 진행중 |
| **Phase 3: UI/UX 개선** | 1주 | 인쇄 최적화, 접근성 | 📝 대기 |
| **Phase 4: 통합 테스트** | 1주 | E2E 테스트, 성능 최적화 | 📝 대기 |
| **Phase 5: 배포 준비** | 3일 | 프로덕션 배포, 문서화 | 📝 대기 |

### 🎯 현재 우선순위
1. **막대 시각화 완성**: TON → 시간 변환 로직
2. **인쇄 레이아웃**: A4 브레이크포인트 구현
3. **야드 노트**: 사이드바 메모 기능
4. **성능 최적화**: 대용량 데이터 처리

---

## 품질 보증 및 테스트 전략

### 🧪 테스트 계획
* **단위 테스트**: Jest + React Testing Library (계획)
* **통합 테스트**: API 엔드포인트 검증
* **E2E 테스트**: Playwright 또는 Cypress (계획)
* **시각적 회귀**: Storybook + Chromatic (계획)

### 📊 품질 지표
* **코드 커버리지**: ≥ 80% 목표
* **번들 크기**: < 500KB (First Load JS)
* **성능**: Lighthouse 90+ 스코어
* **접근성**: WCAG 2.1 AA 준수

---

## 배포 및 운영

### 🌐 배포 환경
* **개발**: `localhost:3000` (Turbopack)
* **스테이징**: Vercel Preview 브랜치
* **프로덕션**: Vercel 프로덕션 도메인

### 📈 모니터링 (계획)
* **에러 추적**: Sentry 연동
* **성능 모니터링**: Vercel Analytics
* **사용자 피드백**: Hotjar 또는 LogRocket

---

## 검토 및 승인 기준

### ✅ 완료 기준
* ✅ PDF 레이아웃 95% 일치 (현재 달성)
* ✅ CRUD 기능 정상 동작 (현재 달성)
* 🚧 크로스 브라우저 호환성 (Chrome, Edge, Safari)
* 📝 코드 커버리지 ≥ 80%
* 📝 성능 벤치마크 통과
* 📝 사용자 수용 테스트 완료

### 📋 릴리스 체크리스트
- [x] TypeScript 엄격 모드 통과
- [x] ESLint 규칙 준수
- [x] 반응형 레이아웃 구현
- [ ] A4 인쇄 최적화
- [ ] 접근성 검증 (WAVE, axe)
- [ ] 보안 스캔 (npm audit)
- [ ] 성능 프로파일링

---

**최종 업데이트**: 2024년 12월 (v0.1.0 기준)  
**다음 마일스톤**: Phase 2 완료 - 막대 시각화 및 인쇄 최적화
