import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import apiClient from '@/lib/api'
import { HealthResponse } from '@/types/api'

interface NavigationState {
  activeSection: string
  isMenuOpen: boolean
  setActiveSection: (section: string) => void
  setMenuOpen: (isOpen: boolean) => void
}

interface UIState {
  isLoading: boolean
  theme: 'light' | 'dark' | 'system'
  setLoading: (loading: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
}

interface ApiState {
  systemStatus: HealthResponse | null
  isConnected: boolean
  lastError: string | null
  
  // API 액션들
  checkSystemStatus: () => Promise<void>
  healthCheck: () => Promise<boolean>
  setError: (error: string | null) => void
  clearError: () => void
}

interface ModelingDataState {
  // 전처리된 데이터
  trainData: any[] | null
  testData: any[] | null
  originalData: any[] | null
  
  // 전처리 설정 정보
  preprocessingConfig: {
    targetColumn: string
    trainTestSplit: number
    missingValueMethod: string
    outlierMethod: string
    scalingMethod: string
    randomState: number
  } | null
  
  // 데이터 정보
  dataInfo: {
    originalRows: number
    processedRows: number
    columns: string[]
    numericColumns: string[]
    categoricalColumns: string[]
  } | null
  
  // 액션들
  setModelingData: (data: {
    trainData: any[]
    testData: any[]
    originalData: any[]
    preprocessingConfig: any
    dataInfo: any
  }) => void
  clearModelingData: () => void
}

interface AppState extends NavigationState, UIState, ApiState, ModelingDataState {}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Navigation state
      activeSection: 'home',
      isMenuOpen: false,
      setActiveSection: (section) => set({ activeSection: section }),
      setMenuOpen: (isOpen) => set({ isMenuOpen: isOpen }),

      // UI state
      isLoading: false,
      theme: 'system',
      setLoading: (loading) => set({ isLoading: loading }),
      setTheme: (theme) => set({ theme: theme }),

      // API state
      systemStatus: null,
      isConnected: false,
      lastError: null,

      // Modeling data state
      trainData: null,
      testData: null,
      originalData: null,
      preprocessingConfig: null,
      dataInfo: null,

      // API actions
      checkSystemStatus: async () => {
        try {
          set({ isLoading: true, lastError: null });
          const status = await apiClient.getSystemStatus();
          set({ 
            systemStatus: status, 
            isConnected: true,
            isLoading: false 
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          set({ 
            lastError: errorMessage, 
            isConnected: false,
            isLoading: false 
          });
        }
      },

      healthCheck: async () => {
        try {
          await apiClient.healthCheck();
          set({ isConnected: true, lastError: null });
          return true;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Health check failed';
          set({ 
            lastError: errorMessage, 
            isConnected: false 
          });
          return false;
        }
      },

      setError: (error) => set({ lastError: error }),
      clearError: () => set({ lastError: null }),

      // Modeling data actions
      setModelingData: (data) => set({
        trainData: data.trainData,
        testData: data.testData,
        originalData: data.originalData,
        preprocessingConfig: data.preprocessingConfig,
        dataInfo: data.dataInfo,
      }),
      clearModelingData: () => set({
        trainData: null,
        testData: null,
        originalData: null,
        preprocessingConfig: null,
        dataInfo: null,
      }),
    }),
    {
      name: 'app-store',
    }
  )
) 