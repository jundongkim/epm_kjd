'use client'

import { useState, useEffect, useCallback } from 'react'
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
    isLoading: false,
    error: null
  })

  // Load services from localStorage on mount
  useEffect(() => {
    const loadServices = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
          const parsed = JSON.parse(stored)
          if (Array.isArray(parsed)) {
            const services = parsed.map((service: any) => ({
              ...service,
              createdAt: new Date(service.createdAt),
              updatedAt: new Date(service.updatedAt)
            }))
            setState(prev => ({ 
              ...prev, 
              services,
              currentService: services.find((s: DifyServiceConfig) => s.isActive) || services[0] || null,
              error: null
            }))
          } else {
            // Invalid format, clear storage
            localStorage.removeItem(STORAGE_KEY)
          }
        }
      } catch (error) {
        console.error('Failed to load Dify services:', error)
        // Clear corrupted data
        localStorage.removeItem(STORAGE_KEY)
        setState(prev => ({ 
          ...prev, 
          error: {
            code: 'STORAGE_ERROR',
            message: 'Failed to load saved services. Starting fresh.',
            status: 500
          }
        }))
      }
    }
    loadServices()
  }, [])

  // Save services to localStorage
  const saveServices = useCallback((services: DifyServiceConfig[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(services))
    } catch (error) {
      console.error('Failed to save Dify services:', error)
    }
  }, [])

  // API call wrapper with error handling
  const apiCall = useCallback(async <T>(
    url: string, 
    options: RequestInit, 
    service?: DifyServiceConfig
  ): Promise<T> => {
    const currentSvc = service || state.currentService
    if (!currentSvc) {
      throw {
        code: 'NO_SERVICE',
        message: 'No Dify service configured',
        status: 400
      } as DifyApiError
    }

    try {
      // Create timeout controller for better browser compatibility
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch(`${currentSvc.apiUrl}${url}`, {
        ...options,
        headers: {
          'Authorization': `Bearer ${currentSvc.apiKey}`,
          'Content-Type': 'application/json',
          ...options.headers
        },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ 
          message: `HTTP ${response.status}: ${response.statusText}` 
        }))
        
        throw {
          code: errorData.code || `HTTP_${response.status}`,
          message: errorData.message || `Request failed with status ${response.status}`,
          status: response.status
        } as DifyApiError
      }

      return response.json()
    } catch (error: any) {
      // Handle network errors, CORS, timeouts, etc.
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        throw {
          code: 'TIMEOUT_ERROR',
          message: 'Request timed out. Please check your connection and try again.',
          status: 408
        } as DifyApiError
      }
      
      if (error.code && error.message && error.status) {
        throw error // Re-throw our custom errors
      }
      
      // Handle network/CORS errors
      throw {
        code: 'NETWORK_ERROR',
        message: error.message || 'Network error. Please check if the Dify service is running and accessible.',
        status: 0
      } as DifyApiError
    }
  }, [state.currentService])

  // Test service connection
  const testService = useCallback(async (
    serviceConfig: Omit<DifyServiceConfig, 'id' | 'isActive' | 'createdAt' | 'updatedAt'>
  ): Promise<DifyServiceTestResult> => {
    const startTime = Date.now()
    
    try {
      const testSvc: DifyServiceConfig = {
        ...serviceConfig,
        id: 'test',
        isActive: false,
        createdAt: new Date(),
        updatedAt: new Date()
      }

      const response = await apiCall<DifyAppsResponse>('/apps', { method: 'GET' }, testSvc)
      const latency = Date.now() - startTime

      return {
        success: true,
        latency,
        appsCount: response.total
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Connection failed'
      }
    }
  }, [apiCall])

  // Create new service
  const createService = useCallback(async (request: CreateDifyServiceRequest): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      // Test connection first
      const testResult = await testService(request)
      if (!testResult.success) {
        throw new Error(testResult.error || 'Service connection test failed')
      }

      const newService: DifyServiceConfig = {
        id: Date.now().toString(),
        ...request,
        isActive: state.services.length === 0, // First service becomes active
        createdAt: new Date(),
        updatedAt: new Date()
      }

      const updatedServices = [...state.services, newService]
      saveServices(updatedServices)

      setState(prev => ({
        ...prev,
        services: updatedServices,
        currentService: newService.isActive ? newService : prev.currentService,
        isLoading: false
      }))
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: {
          code: 'CREATE_SERVICE_ERROR',
          message: error.message || 'Failed to create service',
          status: 500
        }
      }))
      throw error
    }
  }, [state.services, testService, saveServices])

  // Update service
  const updateService = useCallback(async (request: UpdateDifyServiceRequest): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const existingService = state.services.find(s => s.id === request.id)
      if (!existingService) {
        throw new Error('Service not found')
      }

      // Test connection if API details changed
      if (request.apiUrl || request.apiKey) {
        const testConfig = {
          name: request.name || existingService.name,
          description: request.description || existingService.description,
          apiUrl: request.apiUrl || existingService.apiUrl,
          apiKey: request.apiKey || existingService.apiKey
        }
        
        const testResult = await testService(testConfig)
        if (!testResult.success) {
          throw new Error(testResult.error || 'Service connection test failed')
        }
      }

      const updatedService: DifyServiceConfig = {
        ...existingService,
        ...request,
        updatedAt: new Date()
      }

      const updatedServices = state.services.map(s => 
        s.id === request.id ? updatedService : s
      )
      saveServices(updatedServices)

      setState(prev => ({
        ...prev,
        services: updatedServices,
        currentService: prev.currentService?.id === request.id ? updatedService : prev.currentService,
        isLoading: false
      }))
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: {
          code: 'UPDATE_SERVICE_ERROR',
          message: error.message || 'Failed to update service',
          status: 500
        }
      }))
      throw error
    }
  }, [state.services, testService, saveServices])

  // Delete service
  const deleteService = useCallback(async (serviceId: string): Promise<void> => {
    const updatedServices = state.services.filter(s => s.id !== serviceId)
    saveServices(updatedServices)

    setState(prev => ({
      ...prev,
      services: updatedServices,
      currentService: prev.currentService?.id === serviceId 
        ? (updatedServices[0] || null) 
        : prev.currentService
    }))
  }, [state.services, saveServices])

  // Set active service
  const setActiveService = useCallback((serviceId: string) => {
    const service = state.services.find(s => s.id === serviceId)
    if (service) {
      const updatedServices = state.services.map(s => ({
        ...s,
        isActive: s.id === serviceId
      }))
      saveServices(updatedServices)

      setState(prev => ({
        ...prev,
        services: updatedServices,
        currentService: service
      }))
    }
  }, [state.services, saveServices])

  // Fetch apps from current service
  const fetchApps = useCallback(async (): Promise<void> => {
    if (!state.currentService) return

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const response = await apiCall<DifyAppsResponse>('/apps', { method: 'GET' })
      setState(prev => ({
        ...prev,
        apps: response.data,
        isLoading: false
      }))
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error
      }))
    }
  }, [state.currentService, apiCall])

  // Create new app
  const createApp = useCallback(async (request: DifyCreateAppRequest): Promise<DifyApp> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const newApp = await apiCall<DifyApp>('/apps', {
        method: 'POST',
        body: JSON.stringify(request)
      })

      setState(prev => ({
        ...prev,
        apps: [...prev.apps, newApp],
        isLoading: false
      }))

      return newApp
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error
      }))
      throw error
    }
  }, [apiCall])

  // Send chat message
  const sendChat = useCallback(async (
    appId: string, 
    request: DifyChatRequest
  ): Promise<DifyChatResponse> => {
    try {
      return await apiCall<DifyChatResponse>(`/chat-messages`, {
        method: 'POST',
        body: JSON.stringify(request),
        headers: {
          'Authorization': `Bearer ${state.currentService?.apiKey}`,
          'Content-Type': 'application/json'
        }
      })
    } catch (error: any) {
      setState(prev => ({ ...prev, error }))
      throw error
    }
  }, [apiCall, state.currentService])

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  return {
    // State
    ...state,
    
    // Service management
    createService,
    updateService,
    deleteService,
    setActiveService,
    testService,
    
    // App management
    fetchApps,
    createApp,
    
    // Chat
    sendChat,
    
    // Utilities
    clearError
  }
} 