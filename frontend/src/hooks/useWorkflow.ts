import { useState, useCallback } from 'react'

export interface WorkflowItem {
  id: string
  name: string
  description: string
  active: boolean
  created_at: string
  updated_at: string
  tags: string[]
  nodes: any[]
  connections: any
}

export interface Execution {
  id: string
  workflow_id: string
  status: string
  started_at: string
  finished_at?: string
  data: any
}

export interface Template {
  id: string
  name: string
  description: string
  category: string
  nodes: any[]
  connections: any
}

export interface WorkflowCreateRequest {
  name: string
  description?: string
  nodes: any[]
  connections: any
  tags?: string[]
}

export interface WorkflowUpdateRequest {
  name?: string
  description?: string
  nodes?: any[]
  connections?: any
  tags?: string[]
  active?: boolean
}

export const useWorkflow = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const apiCall = useCallback(async (url: string, options?: RequestInit) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // n8n 서비스 상태 확인
  const checkHealth = useCallback(async () => {
    try {
      const data = await apiCall('/api/v1/workflow/health')
      return data.status === 'healthy'
    } catch {
      return false
    }
  }, [apiCall])

  // 워크플로우 목록 조회
  const getWorkflows = useCallback(async (): Promise<WorkflowItem[]> => {
    const data = await apiCall('/api/v1/workflow/workflows')
    return data
  }, [apiCall])

  // 워크플로우 상세 조회
  const getWorkflow = useCallback(async (workflowId: string): Promise<WorkflowItem> => {
    const data = await apiCall(`/api/v1/workflow/workflows/${workflowId}`)
    return data
  }, [apiCall])

  // 워크플로우 생성
  const createWorkflow = useCallback(async (workflow: WorkflowCreateRequest): Promise<WorkflowItem> => {
    const data = await apiCall('/api/v1/workflow/workflows', {
      method: 'POST',
      body: JSON.stringify(workflow),
    })
    return data
  }, [apiCall])

  // 워크플로우 업데이트
  const updateWorkflow = useCallback(async (workflowId: string, updates: WorkflowUpdateRequest): Promise<WorkflowItem> => {
    const data = await apiCall(`/api/v1/workflow/workflows/${workflowId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
    return data
  }, [apiCall])

  // 워크플로우 삭제
  const deleteWorkflow = useCallback(async (workflowId: string): Promise<void> => {
    await apiCall(`/api/v1/workflow/workflows/${workflowId}`, {
      method: 'DELETE',
    })
  }, [apiCall])

  // 워크플로우 실행
  const executeWorkflow = useCallback(async (workflowId: string, inputData: any = {}): Promise<Execution> => {
    const data = await apiCall(`/api/v1/workflow/workflows/${workflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify({
        workflow_id: workflowId,
        input_data: inputData,
      }),
    })
    return data
  }, [apiCall])

  // 워크플로우 활성화
  const activateWorkflow = useCallback(async (workflowId: string): Promise<void> => {
    await apiCall(`/api/v1/workflow/workflows/${workflowId}/activate`, {
      method: 'POST',
    })
  }, [apiCall])

  // 워크플로우 비활성화
  const deactivateWorkflow = useCallback(async (workflowId: string): Promise<void> => {
    await apiCall(`/api/v1/workflow/workflows/${workflowId}/deactivate`, {
      method: 'POST',
    })
  }, [apiCall])

  // 실행 기록 조회
  const getExecutions = useCallback(async (limit: number = 20, workflowId?: string): Promise<Execution[]> => {
    let url = `/api/v1/workflow/executions?limit=${limit}`
    if (workflowId) {
      url += `&workflow_id=${workflowId}`
    }
    
    const data = await apiCall(url)
    return data.data || []
  }, [apiCall])

  // 특정 실행 결과 조회
  const getExecution = useCallback(async (executionId: string): Promise<Execution> => {
    const data = await apiCall(`/api/v1/workflow/executions/${executionId}`)
    return data
  }, [apiCall])

  // 템플릿 목록 조회
  const getTemplates = useCallback(async (): Promise<Template[]> => {
    const data = await apiCall('/api/v1/workflow/workflow-templates')
    return data.templates || []
  }, [apiCall])

  // 템플릿에서 워크플로우 생성
  const createFromTemplate = useCallback(async (templateId: string, name: string): Promise<WorkflowItem> => {
    const data = await apiCall(`/api/v1/workflow/workflows/from-template/${templateId}?name=${encodeURIComponent(name)}`, {
      method: 'POST',
    })
    return data
  }, [apiCall])

  return {
    loading,
    error,
    checkHealth,
    getWorkflows,
    getWorkflow,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    executeWorkflow,
    activateWorkflow,
    deactivateWorkflow,
    getExecutions,
    getExecution,
    getTemplates,
    createFromTemplate,
  }
}

export default useWorkflow 