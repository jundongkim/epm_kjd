/**
 * 제품 예측 모델링 서비스
 */

// 기본 API URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 타입 정의
export interface TrainingDataUploadRequest {
  file: File
}

export interface TrainingDataSetRequest {
  data: Array<Record<string, any>>
  preprocessing_info?: Record<string, any>
}

export interface ModelConfigRequest {
  model_type: string
  model_name: string
  target_variable: string
  hyperparameters: Record<string, any>
  task_type?: string
  test_size?: number
  random_state?: number
}

export interface PredictionRequest {
  model_name: string
  input_data: Record<string, number>
  confidence_interval?: boolean
}

export interface ReportRequest {
  report_type: string
  include_sections: string[]
  report_length?: string
  model_name?: string
  additional_data?: Record<string, any>
}

export interface TrainingResult {
  model_name: string
  model_type: string
  target_variable: string
  feature_names: string[]
  metrics: Record<string, number>
  training_time: number
  data_shape: [number, number]
  feature_importance?: Array<Record<string, any>>
  predictions: {
    test_actual: number[]
    test_predictions: number[]
  }
}

export interface PredictionResult {
  prediction: number
  confidence_interval?: [number, number]
  model_name: string
  timestamp: string
}

export interface ModelInfo {
  name: string
  type: string
  task_type: string
  created_at?: string
  last_trained?: string
  trained: boolean
}

export interface ModelRecommendation {
  model_type: string
  reason: string
  priority: number
}

// API 클래스
export class ProductModelingService {
  private baseURL: string

  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1/product-modeling`
  }

  /**
   * 헬스 체크
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${this.baseURL}/health`)
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 훈련 데이터 파일 업로드
   */
  async uploadTrainingData(file: File): Promise<{
    success: boolean
    message: string
    data_info?: {
      filename: string
      shape: [number, number]
      numeric_columns: string[]
      categorical_columns: string[]
    }
  }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseURL}/data/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 훈련 데이터 설정 (JSON 형태)
   */
  async setTrainingData(request: TrainingDataSetRequest): Promise<{
    success: boolean
    data_shape: [number, number]
    numeric_columns: string[]
    categorical_columns: string[]
    preprocessing_applied: boolean
    message: string
  }> {
    const response = await fetch(`${this.baseURL}/data/set`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Set training data failed: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 예시 데이터 가져오기
   */
  async getSampleData(): Promise<{
    success: boolean
    data: Array<Record<string, any>>
    columns: string[]
    shape: [number, number]
    message: string
  }> {
    const response = await fetch(`${this.baseURL}/data/sample`)
    if (!response.ok) {
      throw new Error(`Get sample data failed: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 모델 생성
   */
  async createModel(request: ModelConfigRequest): Promise<{
    success: boolean
    model_name: string
    model_type: string
    message: string
  }> {
    const response = await fetch(`${this.baseURL}/models/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Create model failed: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 모델 훈련
   */
  async trainModel(request: ModelConfigRequest): Promise<{
    success: boolean
    message: string
    training_result: TrainingResult
  }> {
    const response = await fetch(`${this.baseURL}/models/train`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Train model failed: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 예측 수행
   */
  async predict(request: PredictionRequest): Promise<{
    success: boolean
    message: string
    prediction: number
    confidence_interval?: [number, number]
    model_name: string
    timestamp: string
  }> {
    const response = await fetch(`${this.baseURL}/models/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * AI 보고서 생성
   */
  async generateReport(request: ReportRequest): Promise<{
    success: boolean
    message: string
    report_content: string
    report_metadata: Record<string, any>
  }> {
    const response = await fetch(`${this.baseURL}/reports/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Generate report failed: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * 등록된 모델 목록 조회
   */
  async getModels(): Promise<{
    success: boolean
    models: ModelInfo[]
    count: number
  }> {
    const response = await fetch(`${this.baseURL}/models`)
    if (!response.ok) {
      throw new Error(`Get models failed: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 특정 모델 정보 조회
   */
  async getModelInfo(modelName: string): Promise<{
    success: boolean
    model_info: Record<string, any>
    training_result?: Partial<TrainingResult>
  }> {
    const response = await fetch(`${this.baseURL}/models/${encodeURIComponent(modelName)}`)
    if (!response.ok) {
      throw new Error(`Get model info failed: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 모델 추천
   */
  async getModelRecommendations(targetVariable: string): Promise<{
    success: boolean
    recommendations: ModelRecommendation[]
    target_variable: string
  }> {
    const response = await fetch(`${this.baseURL}/models/recommendations/${encodeURIComponent(targetVariable)}`)
    if (!response.ok) {
      throw new Error(`Get model recommendations failed: ${response.statusText}`)
    }
    return response.json()
  }
}

// 싱글톤 인스턴스
export const productModelingService = new ProductModelingService()

// 편의 함수들
export async function uploadTrainingDataFile(file: File) {
  return productModelingService.uploadTrainingData(file)
}

export async function getSampleModelingData() {
  return productModelingService.getSampleData()
}

export async function trainMLModel(config: ModelConfigRequest) {
  return productModelingService.trainModel(config)
}

export async function predictWithModel(request: PredictionRequest) {
  return productModelingService.predict(request)
}

export async function generateAIReport(request: ReportRequest) {
  return productModelingService.generateReport(request)
}

export async function getAvailableModels() {
  return productModelingService.getModels()
}

export async function getModelRecommendations(targetVariable: string) {
  return productModelingService.getModelRecommendations(targetVariable)
} 