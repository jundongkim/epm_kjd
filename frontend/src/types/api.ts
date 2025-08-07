// API 응답 기본 타입
export interface ApiResponse<T = unknown> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: string;
}

// 헬스체크 응답
export interface HealthResponse {
  status: string;
  message: string;
  engines_status: Record<string, string>;
}

// 데이터 생성 관련 타입
export interface DataGenerationRequest {
  num_samples: number;
  product_type: string;
  parameters?: Record<string, unknown>;
}

export interface DataGenerationResponse {
  status: string;
  data: unknown;
}

// 프로세스 분석 관련 타입
export interface ProcessAnalysisRequest {
  process_data: Record<string, unknown>;
  analysis_type: string;
}

export interface ProcessAnalysisResponse {
  status: string;
  analysis: unknown;
}

// 실험 설계 관련 타입
export interface ExperimentRequest {
  factors: Array<Record<string, unknown>>;
  responses: string[];
  design_type: string;
}

export interface ExperimentResponse {
  status: string;
  design: unknown;
}

// 원가 분석 관련 타입
export interface CostAnalysisRequest {
  cost_data: Record<string, unknown>;
  analysis_type: string;
}

export interface CostAnalysisResponse {
  status: string;
  analysis: unknown;
}

// 원가 최적화 관련 타입
export interface CostOptimizationRequest {
  cost_data: Record<string, unknown>;
  optimization_params?: Record<string, unknown>;
}

export interface CostOptimizationResponse {
  status: string;
  optimization: unknown;
}

// AI 보고서 생성 관련 타입
export interface ReportGenerationRequest {
  report_type: string;
  data: Record<string, unknown>;
  parameters?: Record<string, unknown>;
}

export interface ReportGenerationResponse {
  status: string;
  report: unknown;
}

// 고급 최적화 관련 타입
export interface AdvancedOptimizationRequest {
  optimization_type: string;
  parameters: Record<string, unknown>;
  constraints?: Record<string, unknown>;
}

export interface AdvancedOptimizationResponse {
  status: string;
  optimization: unknown;
}

// 챗봇 관련 타입
export interface ChatRequest {
  message: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  status: string;
  response: string;
}

// 에러 타입
export interface ApiError {
  detail: string;
  status_code?: number;
} 