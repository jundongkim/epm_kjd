import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  ApiResponse,
  HealthResponse,
  DataGenerationRequest,
  DataGenerationResponse,
  ProcessAnalysisRequest,
  ProcessAnalysisResponse,
  ExperimentRequest,
  ExperimentResponse,
  CostAnalysisRequest,
  CostAnalysisResponse,
  CostOptimizationRequest,
  CostOptimizationResponse,
  ReportGenerationRequest,
  ReportGenerationResponse,
  AdvancedOptimizationRequest,
  AdvancedOptimizationResponse,
  ChatRequest,
  ChatResponse,
} from '@/types/api';

// API 클라이언트 인스턴스
const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터 (에러 처리)
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
);

// API 클라이언트 클래스
class ApiClient {
  // 헬스체크
  async healthCheck(): Promise<HealthResponse> {
    const response = await api.get('/health');
    return response.data;
  }

  // 전체 시스템 상태 확인
  async getSystemStatus(): Promise<HealthResponse> {
    const response = await api.get('/');
    return response.data;
  }

  // 데이터 생성
  async generateData(request: DataGenerationRequest): Promise<DataGenerationResponse> {
    const response = await api.post('/api/data/generate', request);
    return response.data;
  }

  // 프로세스 분석
  async analyzeProcess(request: ProcessAnalysisRequest): Promise<ProcessAnalysisResponse> {
    const response = await api.post('/api/process/analyze', request);
    return response.data;
  }

  // 제품 데이터 분석
  async analyzeProductData(data: Record<string, any>): Promise<ApiResponse> {
    const response = await api.post('/api/product/analyze', data);
    return response.data;
  }

  // 실험 설계
  async designExperiment(request: ExperimentRequest): Promise<ExperimentResponse> {
    const response = await api.post('/api/experiment/design', request);
    return response.data;
  }

  // 원가 분석
  async analyzeCost(request: CostAnalysisRequest): Promise<CostAnalysisResponse> {
    const response = await api.post('/api/cost/analyze', request);
    return response.data;
  }

  // 원가 최적화
  async optimizeCost(request: CostOptimizationRequest): Promise<CostOptimizationResponse> {
    const response = await api.post('/api/cost/optimize', request);
    return response.data;
  }

  // AI 보고서 생성
  async generateReport(request: ReportGenerationRequest): Promise<ReportGenerationResponse> {
    const response = await api.post('/api/report/generate', request);
    return response.data;
  }

  // 고급 최적화
  async advancedOptimize(request: AdvancedOptimizationRequest): Promise<AdvancedOptimizationResponse> {
    const response = await api.post('/api/optimization/advanced', request);
    return response.data;
  }

  // 챗봇 대화
  async chat(moduleName: string, request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post(`/api/chat/${moduleName}`, request);
    return response.data;
  }

  // 실험 설계 API
  async generateExperimentPlan(request: any): Promise<any> {
    const response = await api.post('/api/v1/experimental-design/experiment-plan', request);
    return response.data;
  }

  async runOptimization(request: any): Promise<any> {
    const response = await api.post('/api/v1/experimental-design/optimization', request);
    return response.data;
  }

  async generateExperimentReport(request: any): Promise<any> {
    const response = await api.post('/api/v1/experimental-design/report', request);
    return response.data;
  }

  async getExperimentParameters(): Promise<any> {
    const response = await api.get('/api/v1/experimental-design/parameters');
    return response.data;
  }

  async getExperimentTypes(): Promise<any> {
    const response = await api.get('/api/v1/experimental-design/experiment-types');
    return response.data;
  }

  async getOptimizationGoals(): Promise<any> {
    const response = await api.get('/api/v1/experimental-design/optimization-goals');
    return response.data;
  }

  async validateExperimentSetup(request: any): Promise<any> {
    const response = await api.post('/api/v1/experimental-design/validate-setup', request);
    return response.data;
  }

  // 파일 업로드 (추후 구현)
  async uploadFile(file: File, endpoint: string): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/api/upload/${endpoint}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }
}

// 싱글톤 인스턴스
const apiClient = new ApiClient();

export default apiClient;

// 개별 API 함수들 (편의성을 위한 export)
export const healthCheck = () => apiClient.healthCheck();
export const getSystemStatus = () => apiClient.getSystemStatus();
export const generateData = (request: DataGenerationRequest) => apiClient.generateData(request);
export const analyzeProcess = (request: ProcessAnalysisRequest) => apiClient.analyzeProcess(request);
export const analyzeProductData = (data: Record<string, any>) => apiClient.analyzeProductData(data);
export const designExperiment = (request: ExperimentRequest) => apiClient.designExperiment(request);
export const analyzeCost = (request: CostAnalysisRequest) => apiClient.analyzeCost(request);
export const optimizeCost = (request: CostOptimizationRequest) => apiClient.optimizeCost(request);
export const generateReport = (request: ReportGenerationRequest) => apiClient.generateReport(request);
export const advancedOptimize = (request: AdvancedOptimizationRequest) => apiClient.advancedOptimize(request);
export const chat = (moduleName: string, request: ChatRequest) => apiClient.chat(moduleName, request);

// 실험 설계 API exports
export const generateExperimentPlan = (request: any) => apiClient.generateExperimentPlan(request);
export const runOptimization = (request: any) => apiClient.runOptimization(request);
export const generateExperimentReport = (request: any) => apiClient.generateExperimentReport(request);
export const getExperimentParameters = () => apiClient.getExperimentParameters();
export const getExperimentTypes = () => apiClient.getExperimentTypes();
export const getOptimizationGoals = () => apiClient.getOptimizationGoals();
export const validateExperimentSetup = (request: any) => apiClient.validateExperimentSetup(request);

// 에러 핸들러
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
}; 