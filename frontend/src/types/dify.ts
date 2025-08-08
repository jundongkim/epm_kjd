// Dify Service Configuration - AI Advisor 외부 기능용
// AI Advisor에서는 사용하지 않음

export interface DifyServiceConfig {
  id: string
  name: string
  baseUrl: string
  apiKey: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

// Dify App Types
export type DifyAppType = 'chatbot' | 'agent' | 'workflow'

export interface DifyApp {
  id: string
  name: string
  mode: DifyAppType
  icon: string
  color: string
  description?: string
  created_at: string
  updated_at: string
}

// Dify API Responses
export interface DifyAppsResponse {
  data: DifyApp[]
  total: number
  page: number
  limit: number
}

export interface DifyMessage {
  id: string
  conversation_id: string
  inputs: Record<string, any>
  query: string
  message: string
  answer: string
  feedback: any
  created_at: string
}

export interface DifyConversation {
  id: string
  name: string
  inputs: Record<string, any>
  status: string
  created_at: string
  updated_at: string
}

export interface CreateDifyServiceRequest {
  name: string
  baseUrl: string
  apiKey: string
}

export interface UpdateDifyServiceRequest extends Partial<CreateDifyServiceRequest> {
  id: string
}

export interface DifyApiError {
  code: string
  message: string
  details?: string
}

export interface UseDifyState {
  services: DifyServiceConfig[]
  currentService: DifyServiceConfig | null
  apps: DifyApp[]
  conversations: DifyConversation[]
  loading: boolean
  error: DifyApiError | null
}

export interface DifyCreateAppRequest {
  name: string
  mode: DifyAppType
  icon?: string
  color?: string
  description?: string
}

export interface DifyChatRequest {
  inputs: Record<string, any>
  query: string
  response_mode: 'blocking' | 'streaming'
  user: string
  conversation_id?: string
  files?: any[]
}

export interface DifyChatResponse {
  answer: string
  conversation_id: string
  message_id: string
  metadata: {
    usage: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
  }
}

export interface DifyServiceTestResult {
  success: boolean
  message: string
  appsCount?: number
  error?: DifyApiError
}
