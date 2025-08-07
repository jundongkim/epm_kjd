// API 설정
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// 환경 설정
export const CONFIG = {
  api: {
    baseUrl: API_BASE_URL,
    timeout: 30000,
  },
  features: {
    enableStreaming: true,
    enableRealTimeUpdates: true,
  },
  ui: {
    theme: 'auto' as 'light' | 'dark' | 'auto',
    language: 'ko' as 'ko' | 'en',
  },
} as const

// 환경 변수 타입 정의
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      NEXT_PUBLIC_API_URL?: string
      NODE_ENV: 'development' | 'production' | 'test'
    }
  }
} 