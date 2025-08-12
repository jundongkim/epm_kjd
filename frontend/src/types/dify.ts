// Dify Service Configuration
export interface DifyServiceConfig {
  id: string
  name: string
  description?: string
  apiUrl: string
  apiKey: string
  isActive: boolean
  createdAt: Date
  updatedAt: Date
}

// Dify App Types
export type DifyAppType = 'chatbot' | 'agent' | 'workflow'

export interface DifyApp {
  id: string
  name: string
  description?: string
  mode: DifyAppType
  enable_site: boolean
  enable_api: boolean
  api_rpm_limit: number
  api_tpm_limit: number
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
}

// Dify API Responses
export interface DifyAppsResponse {
  data: DifyApp[]
  has_more: boolean
  limit: number
  total: number
  page: number
}

// Chat/Conversation Types
export interface DifyMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  created_at: string
  files?: any[]
}

export interface DifyConversation {
  id: string
  name: string
  inputs: Record<string, any>
  status: string
  introduction: string
  created_at: string
}

// Service Creation/Update
export interface CreateDifyServiceRequest {
  name: string
  description?: string
  apiUrl: string
  apiKey: string
}

export interface UpdateDifyServiceRequest extends Partial<CreateDifyServiceRequest> {
  id: string
  isActive?: boolean
}

// Error Types
export interface DifyApiError {
  code: string
  message: string
  status: number
}

// Hook State Types
export interface UseDifyState {
  services: DifyServiceConfig[]
  currentService: DifyServiceConfig | null
  apps: DifyApp[]
  conversations: DifyConversation[]
  isLoading: boolean
  error: DifyApiError | null
}

// API Parameters
export interface DifyCreateAppRequest {
  name: string
  description?: string
  mode: DifyAppType
  icon?: string
  icon_background?: string
}

export interface DifyChatRequest {
  query: string
  inputs?: Record<string, any>
  response_mode?: 'streaming' | 'blocking'
  conversation_id?: string
  user: string
  files?: any[]
}

export interface DifyChatResponse {
  message_id: string
  conversation_id: string
  mode: string
  answer: string
  metadata: {
    usage: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
    retriever_resources?: any[]
  }
  created_at: number
}

// Service Test Result
export interface DifyServiceTestResult {
  success: boolean
  latency?: number
  appsCount?: number
  error?: string
} 