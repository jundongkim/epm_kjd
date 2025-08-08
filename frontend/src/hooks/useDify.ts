// Dify Service Hook - AI Advisor 외부 기능용
// AI Advisor에서는 사용하지 않음

import { useState, useCallback, useEffect } from 'react'
import {
  DifyServiceConfig,
  DifyApp,
  DifyAppsResponse,
  CreateDifyServiceRequest,
  UpdateDifyServiceRequest,
  DifyApiError,
  UseDifyState,
  DifyCreateAppRequest,
  DifyChatRequest,
  DifyChatResponse,
  DifyServiceTestResult
} from '@/types/dify'

const STORAGE_KEY = 'dify-services'

export function useDify() {
  const [state, setState] = useState<UseDifyState>({
    services: [],
    currentService: null,
    apps: [],
    conversations: [],
    loading: false,
    error: null
  })

  // Load services from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const services: DifyServiceConfig[] = JSON.parse(stored)
        setState(prev => ({
          ...prev,
          services,
          currentService: services.find((s: DifyServiceConfig) => s.isActive) || services[0] || null
        }))
      }
    } catch (error) {
      console.error('Failed to load Dify services:', error)
    }
  }, [])

  const saveServices = useCallback((services: DifyServiceConfig[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(services))
    } catch (error) {
      console.error('Failed to save Dify services:', error)
    }
  }, [])

  const apiCall = async <T>(
    endpoint: string,
    options: RequestInit = {},
    service?: DifyServiceConfig
  ): Promise<T> => {
    const targetService = service || state.currentService

    if (!targetService) {
      throw {
        code: 'NO_SERVICE',
        message: 'No Dify service configured',
        details: 'Please configure a Dify service first'
      } as DifyApiError
    }

    const url = `${targetService.baseUrl}/v1${endpoint}`
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${targetService.apiKey}`,
      ...options.headers
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw {
          code: response.status.toString(),
          message: errorData.message || `HTTP ${response.status}`,
          details: errorData.details || response.statusText
        } as DifyApiError
      }

      return await response.json()
    } catch (error) {
      if (error instanceof TypeError) {
        throw {
          code: 'NETWORK_ERROR',
          message: error.message || 'Network error. Please check if the Dify service is running and accessible.',
          details: 'Failed to connect to Dify service'
        } as DifyApiError
      }
      throw error
    }
  }

  const testService = useCallback(async (
    serviceConfig: Omit<DifyServiceConfig, 'id' | 'isActive' | 'createdAt' | 'updatedAt'>
  ): Promise<DifyServiceTestResult> => {
    try {
      const testSvc: DifyServiceConfig = {
        ...serviceConfig,
        id: 'test',
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }

      const response = await apiCall<DifyAppsResponse>('/apps', { method: 'GET' }, testSvc)
      
      return {
        success: true,
        message: 'Service connection successful',
        appsCount: response.data?.length || 0
      }
    } catch (error) {
      return {
        success: false,
        message: (error as DifyApiError).message || 'Connection failed',
        error: error as DifyApiError
      }
    }
  }, [])

  const createService = useCallback(async (request: CreateDifyServiceRequest): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      // Test the service first
      const testResult = await testService(request)
      if (!testResult.success) {
        throw testResult.error
      }

      const newService: DifyServiceConfig = {
        id: Date.now().toString(),
        ...request,
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }

      const updatedServices = [...state.services, newService]
      saveServices(updatedServices)

      setState(prev => ({
        ...prev,
        services: updatedServices,
        currentService: newService,
        loading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error as DifyApiError
      }))
      throw error
    }
  }, [state.services, testService, saveServices])

  const updateService = useCallback(async (request: UpdateDifyServiceRequest): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const { id, ...updateData } = request
      const serviceIndex = state.services.findIndex(s => s.id === id)
      
      if (serviceIndex === -1) {
        throw {
          code: 'NOT_FOUND',
          message: 'Service not found',
          details: `Service with ID ${id} does not exist`
        } as DifyApiError
      }

      const updatedService: DifyServiceConfig = {
        ...state.services[serviceIndex],
        ...updateData,
        updatedAt: new Date().toISOString()
      }

      const updatedServices = [...state.services]
      updatedServices[serviceIndex] = updatedService
      saveServices(updatedServices)

      setState(prev => ({
        ...prev,
        services: updatedServices,
        currentService: prev.currentService?.id === id ? updatedService : prev.currentService,
        loading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error as DifyApiError
      }))
      throw error
    }
  }, [state.services, saveServices])

  const deleteService = useCallback(async (id: string): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const updatedServices = state.services.filter(s => s.id !== id)
      saveServices(updatedServices)

      setState(prev => ({
        ...prev,
        services: updatedServices,
        currentService: prev.currentService?.id === id ? (updatedServices[0] || null) : prev.currentService,
        loading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error as DifyApiError
      }))
      throw error
    }
  }, [state.services, saveServices])

  const setActiveService = useCallback(async (id: string): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const updatedServices = state.services.map(s => ({
        ...s,
        isActive: s.id === id
      }))
      saveServices(updatedServices)

      const newCurrentService = updatedServices.find(s => s.id === id) || null

      setState(prev => ({
        ...prev,
        services: updatedServices,
        currentService: newCurrentService,
        loading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error as DifyApiError
      }))
      throw error
    }
  }, [state.services, saveServices])

  const loadApps = useCallback(async (): Promise<void> => {
    if (!state.currentService) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const response = await apiCall<DifyAppsResponse>('/apps', { method: 'GET' })
      
      setState(prev => ({
        ...prev,
        apps: response.data || [],
        loading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error as DifyApiError
      }))
    }
  }, [state.currentService])

  const createApp = useCallback(async (request: DifyCreateAppRequest): Promise<DifyApp> => {
    if (!state.currentService) {
      throw {
        code: 'NO_SERVICE',
        message: 'No active Dify service',
        details: 'Please select an active Dify service'
      } as DifyApiError
    }

    const newApp = await apiCall<DifyApp>('/apps', {
      method: 'POST',
      body: JSON.stringify(request)
    })

    // Refresh apps list
    await loadApps()

    return newApp
  }, [state.currentService, loadApps])

  const deleteApp = useCallback(async (appId: string): Promise<void> => {
    if (!state.currentService) {
      throw {
        code: 'NO_SERVICE',
        message: 'No active Dify service',
        details: 'Please select an active Dify service'
      } as DifyApiError
    }

    await apiCall(`/apps/${appId}`, { method: 'DELETE' })

    // Refresh apps list
    await loadApps()
  }, [state.currentService, loadApps])

  const sendChatMessage = useCallback(async (
    request: DifyChatRequest
  ): Promise<DifyChatResponse> => {
    if (!state.currentService) {
      throw {
        code: 'NO_SERVICE',
        message: 'No active Dify service',
        details: 'Please select an active Dify service'
      } as DifyApiError
    }

    return await apiCall<DifyChatResponse>(`/chat-messages`, {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }, [state.currentService])

  return {
    ...state,
    testService,
    createService,
    updateService,
    deleteService,
    setActiveService,
    loadApps,
    createApp,
    deleteApp,
    sendChatMessage
  }
}
