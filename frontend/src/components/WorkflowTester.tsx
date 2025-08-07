'use client'

import { useState, useEffect } from 'react'
import { Play, Send, RefreshCw, Plus, Copy } from 'lucide-react'
import { Select } from './ui'

interface TestResult {
  success: boolean
  data?: any
  error?: string
  timestamp: string
  duration?: number
}

interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  workflow?: any
}

export default function WorkflowTester() {
  const [loading, setLoading] = useState(false)
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [workflowName, setWorkflowName] = useState('')
  const [testData, setTestData] = useState(`{
  "temperature": 175,
  "pressure": 2.5,
  "quality": 95.2,
  "batchId": "BATCH-001"
}`)
  const [result, setResult] = useState<TestResult | null>(null)

  // 컴포넌트 마운트 시 템플릿 로드
  useEffect(() => {
    loadTemplates()
  }, [])

  // 템플릿 옵션 생성 (Select 컴포넌트용)
  const getTemplateOptions = () => {
    if (!templates || templates.length === 0) return ['템플릿이 없습니다']
    return templates.map(template => `${template.name} (${template.category})`)
  }

  // 선택된 템플릿 이름으로부터 템플릿 객체 찾기
  const getSelectedTemplateName = () => {
    if (!selectedTemplate || !templates) return ''
    const template = templates.find(t => t.id === selectedTemplate)
    return template ? `${template.name} (${template.category})` : ''
  }

  // 템플릿 이름으로부터 ID 찾기
  const getTemplateIdByName = (templateName: string) => {
    if (!templates) return ''
    const template = templates.find(t => `${t.name} (${t.category})` === templateName)
    return template?.id || ''
  }

  // 선택된 템플릿 객체 가져오기
  const getSelectedTemplateObject = () => {
    if (!selectedTemplate || !templates) return null
    return templates.find(t => t.id === selectedTemplate) || null
  }

  // 템플릿 목록 로드
  const loadTemplates = async () => {
    try {
              const response = await fetch('http://localhost:8000/api/v1/workflow/workflow-templates', {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setTemplates(data.templates || [])
      }
    } catch (error) {
      console.error('템플릿 로드 실패:', error)
    }
  }

  // 워크플로우 생성
  const createWorkflow = async () => {
    if (!selectedTemplate || !workflowName.trim()) {
      setResult({
        success: false,
        error: '템플릿과 워크플로우 이름을 선택/입력하세요.',
        timestamp: new Date().toISOString()
      })
      return
    }

    setLoading(true)
    const startTime = Date.now()
    
    try {
      const response = await fetch(`/api/v1/workflow/workflows/from-template/${selectedTemplate}?name=${encodeURIComponent(workflowName)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })

      const responseData = await response.json()
      const endTime = Date.now()

      setResult({
        success: response.ok,
        data: responseData,
        timestamp: new Date().toISOString(),
        duration: endTime - startTime
      })
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류',
        timestamp: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  // n8n Health Check 테스트
  const testWebhook = async () => {
    setLoading(true)
    const startTime = Date.now()
    
    try {
      // n8n 연결 상태 테스트
              const response = await fetch('http://localhost:8000/api/v1/workflow/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      const responseData = await response.json()
      const endTime = Date.now()

      setResult({
        success: response.ok && responseData.status === 'healthy',
        data: responseData,
        timestamp: new Date().toISOString(),
        duration: endTime - startTime
      })
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류',
        timestamp: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  // Backend API를 통한 워크플로우 API 테스트
  const testWorkflowAPI = async () => {
    setLoading(true)
    const startTime = Date.now()
    
    try {
      const data = JSON.parse(testData)
      
      // 워크플로우 목록 조회 테스트
                const workflowsResponse = await fetch('http://localhost:8000/api/v1/workflow/workflows', {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!workflowsResponse.ok) {
        throw new Error(`워크플로우 목록 조회 실패: ${workflowsResponse.status}`)
      }
      
      const workflows = await workflowsResponse.json()
      
      // 템플릿 목록 조회 테스트
                const templatesResponse = await fetch('http://localhost:8000/api/v1/workflow/workflow-templates', {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!templatesResponse.ok) {
        throw new Error(`템플릿 목록 조회 실패: ${templatesResponse.status}`)
      }
      
      const templates = await templatesResponse.json()
      
      // 실제 존재하는 워크플로우가 있는 경우 실행 테스트도 수행
      let executionResult = null
      let executionError = null
      
      // sample-1 같은 더미 워크플로우는 제외하고 실제 워크플로우만 찾기
      const realWorkflows = workflows.filter((w: any) => 
        w.id !== 'sample-1' && 
        w.name !== '🚀 n8n 워크플로우 시작하기' &&
        w.nodes && 
        w.nodes.length > 0
      )
      
      if (realWorkflows.length > 0) {
        // 첫 번째 실제 워크플로우로 테스트 시도
        const testWorkflowId = realWorkflows[0].id
        try {
          const executeResponse = await fetch(`http://localhost:8000/api/v1/workflow/workflows/${testWorkflowId}/execute`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            },
            body: JSON.stringify({
              workflow_id: testWorkflowId,
              input_data: data
            })
          })
          
          if (executeResponse.ok) {
            executionResult = await executeResponse.json()
          } else {
            const errorData = await executeResponse.json()
            executionError = errorData.detail || `HTTP ${executeResponse.status}`
          }
        } catch (execError) {
          executionError = execError instanceof Error ? execError.message : '실행 테스트 오류'
        }
      }

      const endTime = Date.now()

      setResult({
        success: true,
        data: {
          api_status: "성공",
          workflows_count: workflows.length,
          workflows: workflows.slice(0, 3), // 처음 3개만 표시
          templates_count: templates.templates?.length || 0,
          execution_test: executionResult ? "성공" : executionError ? "실패" : "건너뜀",
          execution_result: executionResult,
          execution_error: executionError,
          tested_workflow_id: realWorkflows.length > 0 ? realWorkflows[0].id : null,
          test_summary: {
            workflow_api: "✅ 작동",
            template_api: "✅ 작동", 
            execution_api: executionResult ? "✅ 작동" : executionError ? `❌ 실패: ${executionError}` : "⏭️ 건너뜀 (워크플로우 없음)"
          }
        },
        timestamp: new Date().toISOString(),
        duration: endTime - startTime
      })
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류',
        timestamp: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  const formatJson = (obj: any) => {
    return JSON.stringify(obj, null, 2)
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* 워크플로우 생성 섹션 */}
      <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-8 shadow-sm">
        <h2 className="text-2xl font-bold text-foreground mb-4 flex items-center">
          <Plus className="w-6 h-6 mr-3 text-accent-cyan" />
          실제 워크플로우 생성
        </h2>
        
        <p className="text-muted-foreground mb-8">
          템플릿을 선택해서 n8n에 실제 워크플로우를 생성하세요.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 템플릿 선택 */}
          <div>
            <Select
              value={getSelectedTemplateName()}
              onChange={(templateName) => {
                if (templateName === '템플릿이 없습니다') return
                setSelectedTemplate(getTemplateIdByName(templateName))
              }}
              options={getTemplateOptions()}
              label="워크플로우 템플릿 선택"
              placeholder="템플릿을 선택하세요"
            />
            {selectedTemplate && (
              <p className="text-sm text-muted-foreground mt-2">
                {getSelectedTemplateObject()?.description}
              </p>
            )}
          </div>

          {/* 워크플로우 이름 */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              워크플로우 이름
            </label>
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="예: 제조데이터 모니터링 v1"
              className="w-full px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm hover:bg-muted/50 hover:border-border transition-all duration-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
            />
          </div>
        </div>

        <div className="mt-8">
          <button
            onClick={createWorkflow}
            disabled={loading || !selectedTemplate || !workflowName.trim()}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Plus className="w-5 h-5" />
            )}
            <span>워크플로우 생성</span>
          </button>
        </div>
      </div>

      {/* 기존 테스트 섹션 */}
      <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-8 shadow-sm">
        <h2 className="text-2xl font-bold text-foreground mb-4 flex items-center">
          <Play className="w-6 h-6 mr-3 text-accent-blue" />
          n8n 워크플로우 테스터
        </h2>
        
        <p className="text-muted-foreground mb-8">
          n8n 워크플로우의 연동을 테스트할 수 있습니다. 연결 상태 확인 또는 API를 통해 워크플로우를 실행해보세요.
        </p>

        {/* 입력 데이터 */}
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              테스트 데이터 (JSON)
            </label>
            <textarea
              value={testData}
              onChange={(e) => setTestData(e.target.value)}
              className="w-full h-32 px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground font-mono text-sm resize-none hover:bg-muted/50 hover:border-border transition-all duration-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
              placeholder="JSON 형태의 테스트 데이터를 입력하세요"
            />
          </div>

          {/* 버튼들 */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={testWebhook}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-accent-cyan text-white rounded-lg hover:bg-accent-cyan/90 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span>연결 테스트</span>
            </button>

            <button
              onClick={testWorkflowAPI}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-accent-purple text-white rounded-lg hover:bg-accent-purple/90 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>API 종합 테스트</span>
            </button>

            <a
              href="http://localhost:5678"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 px-4 py-2 bg-muted/20 text-foreground rounded-lg border border-border hover:bg-muted/50 transition-all duration-300"
            >
              <span>n8n 열기</span>
            </a>
          </div>
        </div>
      </div>

      {/* 결과 표시 */}
      {result && (
        <div className="bg-card border border-border rounded-lg p-6 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100">
          <h3 className="text-lg font-semibold text-foreground mb-4 sticky top-0 bg-card pb-2 z-10 border-b border-border/50">
            실행 결과
            <span className="text-xs text-muted-foreground font-normal ml-2">
              (결과가 길면 스크롤하세요)
            </span>
          </h3>
          
          <div className="space-y-4">
            {/* 상태 */}
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                result.success ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="font-medium">
                {result.success ? '성공' : '실패'}
              </span>
              <span className="text-sm text-muted-foreground">
                {result.timestamp}
              </span>
              {result.duration && (
                <span className="text-sm text-muted-foreground">
                  ({result.duration}ms)
                </span>
              )}
            </div>

            {/* 워크플로우 생성 가이드 특별 표시 */}
            {result.data?.manual_creation && (
              <div className="bg-blue-50 border border-blue-200 rounded-glass p-6 space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-500 rounded-glass flex items-center justify-center">
                    <Plus className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-blue-900">{result.data.message}</h4>
                    <p className="text-sm text-blue-700">
                      예상 소요시간: {result.data.estimated_time}
                    </p>
                  </div>
                </div>

                {/* 단계별 가이드 */}
                <div className="bg-white rounded-glass p-4 border border-blue-200 relative">
                  <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-auto scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100">
                    {result.data.instructions}
                  </pre>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(result.data.instructions)
                      alert('가이드가 클립보드에 복사되었습니다!')
                    }}
                    className="absolute top-2 right-2 p-1 bg-blue-200 hover:bg-blue-300 rounded text-blue-800 transition-colors opacity-75 hover:opacity-100"
                    title="가이드 복사"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                </div>

                {/* 빠른 액션 버튼들 */}
                <div className="flex flex-wrap gap-3 pt-2">
                  <a
                    href={result.data.n8n_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-glass hover:bg-blue-600 transition-all duration-300"
                  >
                    <span>🚀 n8n 열기</span>
                  </a>
                  
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(result.data.instructions)
                      alert('가이드가 클립보드에 복사되었습니다!')
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-500 text-white rounded-glass hover:bg-gray-600 transition-all duration-300"
                  >
                    <span>📋 가이드 복사</span>
                  </button>

                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(result.data.workflow_json, null, 2))
                      alert('워크플로우 JSON이 클립보드에 복사되었습니다!')
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-purple-500 text-white rounded-glass hover:bg-purple-600 transition-all duration-300"
                  >
                    <span>💾 JSON 복사</span>
                  </button>
                </div>

                {/* 템플릿 정보 */}
                <div className="border-t border-blue-200 pt-4">
                  <h5 className="font-medium text-blue-900 mb-2">템플릿 정보:</h5>
                  <div className="text-sm text-blue-700 space-y-1">
                    <p><strong>이름:</strong> {result.data.template.name}</p>
                    <p><strong>설명:</strong> {result.data.template.description}</p>
                    <p><strong>카테고리:</strong> {result.data.template.category}</p>
                    <p><strong>노드 수:</strong> {result.data.workflow_json.nodes.length}개</p>
                  </div>
                </div>
              </div>
            )}

            {/* 일반 응답 데이터 (워크플로우 생성이 아닌 경우) */}
            {result.data && !result.data?.manual_creation && (
              <div>
                <h4 className="text-sm font-medium text-foreground mb-2">응답 데이터:</h4>
                <div className="relative">
                  <pre className="bg-background border border-glass-border rounded-glass p-4 text-sm overflow-auto max-h-64 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100">
                  {formatJson(result.data)}
                </pre>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(formatJson(result.data))
                      alert('응답 데이터가 클립보드에 복사되었습니다!')
                    }}
                    className="absolute top-2 right-2 p-1 bg-gray-200 hover:bg-gray-300 rounded text-gray-800 transition-colors opacity-75 hover:opacity-100"
                    title="응답 데이터 복사"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}

            {/* 에러 */}
            {result.error && (
              <div>
                <h4 className="text-sm font-medium text-red-600 mb-2">오류:</h4>
                <div className="relative bg-red-50 border border-red-200 rounded-glass p-4 text-sm text-red-700 max-h-32 overflow-auto scrollbar-thin scrollbar-thumb-red-400 scrollbar-track-red-100">
                  {result.error}
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(result.error || '')
                      alert('오류 정보가 클립보드에 복사되었습니다!')
                    }}
                    className="absolute top-2 right-2 p-1 bg-red-200 hover:bg-red-300 rounded text-red-800 transition-colors opacity-75 hover:opacity-100"
                    title="오류 정보 복사"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 사용법 안내 */}
      <div className="bg-glass-100 rounded-glass p-6 border border-glass-border">
        <h3 className="text-lg font-semibold text-foreground mb-4">사용법 안내</h3>
        
        <div className="space-y-4 text-sm text-muted-foreground">
          <div>
            <h4 className="font-medium text-foreground mb-2">1. 워크플로우 생성</h4>
            <p>템플릿을 선택하고 이름을 입력한 후 &apos;워크플로우 생성&apos; 버튼을 클릭하세요.</p>
            <p className="text-xs mt-1">
              n8n API 연결이 실패하면 수동 생성 가이드가 제공됩니다.
            </p>
          </div>

          <div>
            <h4 className="font-medium text-foreground mb-2">2. 연결 테스트</h4>
            <p>n8n 서비스의 연결 상태를 확인합니다.</p>
            <code className="bg-background px-2 py-1 rounded border">
              GET /api/v1/workflow/health
            </code>
          </div>

          <div>
            <h4 className="font-medium text-foreground mb-2">3. API 종합 테스트</h4>
            <p>Backend API의 전반적인 기능을 테스트합니다:</p>
            <ul className="text-sm mt-1 space-y-1">
              <li>• 워크플로우 목록 조회</li>
              <li>• 템플릿 목록 조회</li>
              <li>• 샘플 워크플로우 실행</li>
            </ul>
          </div>

          <div>
            <h4 className="font-medium text-foreground mb-2">4. 실제 워크플로우 테스트</h4>
            <p>생성된 워크플로우는 n8n 웹 인터페이스에서 확인하고 활성화할 수 있습니다.</p>
            <p>
              <strong>웹훅 URL 예시:</strong> http://localhost:5678/webhook/test-webhook
            </p>
          </div>
        </div>
      </div>
    </div>
  )
} 