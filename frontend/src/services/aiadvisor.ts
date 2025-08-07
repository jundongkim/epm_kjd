import { API_BASE_URL } from '@/lib/config'

export interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: any[]
  ontologyContext?: any
}

export interface QueryRequest {
  query: string
  agent_id?: string
  use_workflow?: boolean
  k?: number
}

export interface QueryResponse {
  response: string
  sources?: any[]
  ontology_context?: any
  timestamp: string
}

export interface ReportGenerationRequest {
  topic: string
  report_type: string
  sections: string[]
}

export interface DocumentUploadResponse {
  status: string
  document_id: string
  filename: string
  processed_sections: number
  extracted_entities: number
  timestamp: string
}

export interface DocumentListResponse {
  documents: any[]
  total_count: number
  timestamp: string
}

export interface ReportGenerationResponse {
  generation_status: string
  report_metadata: any
  report_filename: string
  sections: any[]
}

export interface SystemStatus {
  status: string
  components: {
    [key: string]: {
      status: string
      message?: string
    }
  }
  timestamp: string
}

class AIAdvisorService {
  private baseUrl: string

  constructor() {
    this.baseUrl = API_BASE_URL
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/health`)
      return await response.json()
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }

  async getSystemStatus(): Promise<any> {
    try {
      console.log('Fetching system status from:', `${this.baseUrl}/api/v1/aiadvisor/status`)
      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/status`)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('System status response not ok:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }
      
      const data = await response.json()
      console.log('System status response:', data)
      return data
    } catch (error) {
      console.error('Failed to get system status:', error)
      throw error
    }
  }

  async queryAgent(request: QueryRequest): Promise<QueryResponse> {
    try {
      console.log('Querying agent with request:', request)
      
      const formData = new FormData()
      formData.append('query', request.query)
      if (request.agent_id) formData.append('agent_id', request.agent_id)
      formData.append('use_workflow', request.use_workflow?.toString() || 'true')
      formData.append('k', request.k?.toString() || '5')

      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/query`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Query response not ok:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      console.log('Query response:', data)
      return data
    } catch (error) {
      console.error('Failed to query agent:', error)
      throw error
    }
  }

  async queryAgentStream(request: QueryRequest): Promise<Response> {
    try {
      const formData = new FormData()
      formData.append('query', request.query)
      if (request.agent_id) formData.append('agent_id', request.agent_id)
      formData.append('use_workflow', request.use_workflow?.toString() || 'true')
      formData.append('k', request.k?.toString() || '5')

      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/query/stream`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`)
      }

      return response
    } catch (error) {
      console.error('Failed to stream agent response:', error)
      throw error
    }
  }

  async streamAgentResponse(request: QueryRequest): Promise<ReadableStream<Uint8Array> | null> {
    try {
      const formData = new FormData()
      formData.append('query', request.query)
      if (request.agent_id) formData.append('agent_id', request.agent_id)
      formData.append('use_workflow', request.use_workflow?.toString() || 'true')
      formData.append('k', request.k?.toString() || '5')

      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/query/stream`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`)
      }

      return response.body
    } catch (error) {
      console.error('Failed to stream agent response:', error)
      throw error
    }
  }

  async generateReport(request: ReportGenerationRequest): Promise<ReportGenerationResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/reports/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error('Failed to generate report')
    }

    return response.json()
  }

  async getReportTypes(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/reports/types`)
    if (!response.ok) {
      throw new Error('Failed to get report types')
    }
    const data = await response.json()
    return data.report_types || []
  }

  async getReportSections(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/reports/sections`)
    if (!response.ok) {
      throw new Error('Failed to get report sections')
    }
    const data = await response.json()
    return data.sections || []
  }

  async downloadReport(filename: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/reports/download/${filename}`)
    if (!response.ok) {
      throw new Error('Failed to download report')
    }
    return response.blob()
  }

  async uploadDocument(formData: FormData): Promise<DocumentUploadResponse> {
    try {
      console.log('Uploading document...')
      
      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/documents/upload`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Document upload response not ok:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      console.log('Document upload response:', data)
      return data
    } catch (error) {
      console.error('Failed to upload document:', error)
      throw error
    }
  }

  async listDocuments(category?: string, limit: number = 50, offset: number = 0): Promise<DocumentListResponse> {
    try {
      console.log('Listing documents...')
      
      const params = new URLSearchParams()
      if (category) params.append('category', category)
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/documents?${params}`)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Document list response not ok:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      console.log('Document list response:', data)
      return data
    } catch (error) {
      console.error('Failed to list documents:', error)
      throw error
    }
  }

  async getDocument(documentId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/documents/${documentId}`)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to get document:', error)
      throw error
    }
  }

  async deleteDocument(documentId: string): Promise<any> {
    try {
      console.log('Deleting document:', documentId)
      
      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/documents/${documentId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Document deletion response not ok:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      console.log('Document deletion response:', data)
      return data
    } catch (error) {
      console.error('Failed to delete document:', error)
      throw error
    }
  }

  async downloadDocument(documentId: string): Promise<Blob> {
    try {
      console.log('Downloading document:', documentId)
      
      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/documents/${documentId}/download`)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Document download response not ok:', response.status, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const blob = await response.blob()
      console.log('Document download completed')
      return blob
    } catch (error) {
      console.error('Failed to download document:', error)
      throw error
    }
  }

  async searchDocuments(query: string, k: number = 5, category?: string): Promise<any> {
    try {
      const formData = new FormData()
      formData.append('query', query)
      formData.append('k', k.toString())
      if (category) formData.append('category', category)

      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/documents/search`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      return {
        documents: data.results || [],
        total_count: data.total_found || 0,
        query: data.query,
        timestamp: data.timestamp
      }
    } catch (error) {
      console.error('Failed to search documents:', error)
      throw error
    }
  }

  async getOntologyEntities(entityType?: string, limit: number = 50): Promise<any> {
    try {
      const params = new URLSearchParams()
      if (entityType) params.append('entity_type', entityType)
      params.append('limit', limit.toString())

      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/ontology/entities?${params}`)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to get ontology entities:', error)
      throw error
    }
  }

  async searchOntology(query: string): Promise<any> {
    try {
      const formData = new FormData()
      formData.append('query', query)

      const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/ontology/search`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to search ontology:', error)
      throw error
    }
  }

  async listAgents(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/agent/list`)
    if (!response.ok) {
      throw new Error('Failed to list agents')
    }
    const data = await response.json()
    return data.agents || []
  }

  async getSystemConfig(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/aiadvisor/config`)
    if (!response.ok) {
      throw new Error('Failed to get system config')
    }
    return response.json()
  }
}

export const aiAdvisorService = new AIAdvisorService() 