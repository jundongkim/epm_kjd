'use client'

import { useState, useEffect } from 'react'
import { 
  Workflow, 
  Play, 
  Pause, 
  Plus, 
  Trash2, 
  Eye, 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle,
  Settings,
  Copy,
  ExternalLink,
  RefreshCw,
  Server,
  Target,
  GitBranch,
  ArrowRight,
  Circle,
  Diamond,
  Zap,
  Globe,
  Database,
  Mail,
  Code,
  Filter,
  MoreHorizontal
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { TabNavigation, Select } from '@/components/ui'
import WorkflowTester from '@/components/WorkflowTester'

// ============================
// StatusCard 컴포넌트 (다른 페이지와 동일)
// ============================

interface StatusCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: string
  color: string
}

function StatusCard({ title, value, icon, trend, color }: StatusCardProps) {
  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-muted-foreground text-sm mb-1">{title}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {trend && (
            <p className={`text-sm ${trend.includes('↑') ? 'text-accent-cyan' : trend.includes('↓') ? 'text-accent-orange' : 'text-muted-foreground'}`}>
              {trend}
            </p>
          )}
        </div>
        <div 
          className="p-3 rounded-lg"
          style={{ backgroundColor: color }}
        >
          {icon}
        </div>
      </div>
    </div>
  )
}

// 실행 결과 모달 컴포넌트
function ExecutionResultModal({ 
  workflowId, 
  result, 
  isOpen, 
  onClose,
  t
}: { 
  workflowId: string | null
  result: any
  isOpen: boolean
  onClose: () => void
  t: (key: string) => string
}) {
  if (!isOpen || !result) return null

  const formatJsonData = (data: any) => {
    try {
      return JSON.stringify(data, null, 2)
    } catch {
      return String(data)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col shadow-xl">
        {/* 모달 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-border flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${result.success ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}>
              {result.success ? 
                <CheckCircle className="w-5 h-5 text-green-600" /> : 
                <XCircle className="w-5 h-5 text-red-600" />
              }
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">{t('dashboard.workflow.sections.executionResult')}</h3>
              <p className="text-sm text-muted-foreground">{result.workflowName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-300"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        {/* 모달 내용 */}
        <div className="p-6 overflow-auto flex-1 min-h-0">
          {/* 실행 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-muted/30 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="w-4 h-4 text-accent-cyan" />
                <span className="text-sm font-medium text-foreground">상태</span>
              </div>
              <span className={`text-sm font-medium ${result.success ? 'text-green-600' : 'text-red-600'}`}>
                {result.success ? '성공' : '실패'} (HTTP {result.status})
              </span>
            </div>
            <div className="bg-muted/30 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-4 h-4 text-accent-cyan" />
                <span className="text-sm font-medium text-foreground">실행 시간</span>
              </div>
              <span className="text-sm text-muted-foreground">
                {new Date(result.timestamp).toLocaleString('ko-KR')}
              </span>
            </div>
            <div className="bg-muted/30 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Workflow className="w-4 h-4 text-accent-cyan" />
                <span className="text-sm font-medium text-foreground">워크플로우</span>
              </div>
              <span className="text-sm text-muted-foreground">{workflowId}</span>
            </div>
          </div>

          {/* 응답 데이터 */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-foreground flex items-center space-x-2">
              <Target className="w-5 h-5" />
              <span>응답 데이터</span>
            </h4>
            
            {result.success ? (
              <div className="space-y-4">
                {result.data && (
                  <>
                    {/* 성공 메시지 */}
                    {result.data.message && (
                      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="font-medium text-green-800 dark:text-green-200">메시지</span>
                        </div>
                        <p className="text-green-700 dark:text-green-300">{result.data.message}</p>
                      </div>
                    )}

                    {/* 웹훅 응답 데이터 */}
                    {result.data.webhook_response && (
                      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Activity className="w-4 h-4 text-blue-600" />
                          <span className="font-medium text-blue-800 dark:text-blue-200">웹훅 응답</span>
                        </div>
                        <div className="relative">
                          <pre className="text-sm text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-950/50 p-3 rounded-lg overflow-auto max-h-96 scrollbar-thin scrollbar-thumb-blue-400 scrollbar-track-blue-100 dark:scrollbar-thumb-blue-600 dark:scrollbar-track-blue-900">
                            {formatJsonData(result.data.webhook_response)}
                          </pre>
                          <button
                            onClick={() => navigator.clipboard.writeText(formatJsonData(result.data.webhook_response))}
                            className="absolute top-2 right-2 p-1 bg-blue-200 dark:bg-blue-800 hover:bg-blue-300 dark:hover:bg-blue-700 rounded text-blue-800 dark:text-blue-200 transition-colors opacity-75 hover:opacity-100"
                            title="응답 데이터 복사"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    )}

                    {/* 전체 응답 데이터 */}
                    <div className="bg-muted/30 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <GitBranch className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium text-foreground">전체 응답</span>
                      </div>
                      <div className="relative">
                        <pre className="text-sm text-muted-foreground bg-background p-3 rounded-lg overflow-auto border border-border max-h-96 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100 dark:scrollbar-thumb-gray-600 dark:scrollbar-track-gray-800">
                          {formatJsonData(result.data)}
                        </pre>
                        <button
                          onClick={() => navigator.clipboard.writeText(formatJsonData(result.data))}
                          className="absolute top-2 right-2 p-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded text-gray-800 dark:text-gray-200 transition-colors opacity-75 hover:opacity-100"
                          title="전체 응답 복사"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <XCircle className="w-4 h-4 text-red-600" />
                  <span className="font-medium text-red-800 dark:text-red-200">오류 정보</span>
                </div>
                <div className="relative">
                  <pre className="text-sm text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-950/50 p-3 rounded-lg overflow-auto max-h-96 scrollbar-thin scrollbar-thumb-red-400 scrollbar-track-red-100 dark:scrollbar-thumb-red-600 dark:scrollbar-track-red-900">
                    {formatJsonData(result.data)}
                  </pre>
                  <button
                    onClick={() => navigator.clipboard.writeText(formatJsonData(result.data))}
                    className="absolute top-2 right-2 p-1 bg-red-200 dark:bg-red-800 hover:bg-red-300 dark:hover:bg-red-700 rounded text-red-800 dark:text-red-200 transition-colors opacity-75 hover:opacity-100"
                    title="오류 정보 복사"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 모달 푸터 */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-border flex-shrink-0">
          <button
            onClick={() => navigator.clipboard.writeText(formatJsonData(result.data))}
            className="flex items-center space-x-2 px-4 py-2 border border-border rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-300"
          >
            <Copy className="w-4 h-4" />
            <span>복사</span>
          </button>
          <button
            onClick={onClose}
            className="flex items-center space-x-2 px-6 py-2 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300"
          >
            <span>닫기</span>
          </button>
        </div>
      </div>
    </div>
  )
}

// 미니 플로우 차트 컴포넌트
function MiniWorkflowChart({ 
  nodes, 
  className = "",
  t 
}: { 
  nodes: any[]
  className?: string
  t: (key: string) => string
}) {
  // 노드 타입에 따른 아이콘 매핑
  const getNodeIcon = (nodeType: string, nodeName: string) => {
    const type = nodeType?.toLowerCase() || ''
    const name = nodeName?.toLowerCase() || ''
    
    if (type.includes('webhook') || name.includes('webhook')) {
      return <Globe className="w-3 h-3" />
    }
    if (type.includes('function') || name.includes('function')) {
      return <Code className="w-3 h-3" />
    }
    if (type.includes('http') || name.includes('http')) {
      return <Zap className="w-3 h-3" />
    }
    if (type.includes('email') || name.includes('email')) {
      return <Mail className="w-3 h-3" />
    }
    if (type.includes('database') || type.includes('sql')) {
      return <Database className="w-3 h-3" />
    }
    if (type.includes('condition') || type.includes('if')) {
      return <Diamond className="w-3 h-3" />
    }
    if (type.includes('response') || name.includes('response')) {
      return <CheckCircle className="w-3 h-3" />
    }
    if (type.includes('filter') || name.includes('filter')) {
      return <Filter className="w-3 h-3" />
    }
    if (type.includes('set') || type.includes('edit')) {
      return <Settings className="w-3 h-3" />
    }
    
    return <Circle className="w-3 h-3" />
  }

  // 노드 타입에 따른 색상 매핑
  const getNodeColor = (nodeType: string, nodeName: string) => {
    const type = nodeType?.toLowerCase() || ''
    const name = nodeName?.toLowerCase() || ''
    
    if (type.includes('webhook') || name.includes('webhook')) {
      return 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 border-blue-200 dark:border-blue-800'
    }
    if (type.includes('function') || name.includes('function')) {
      return 'bg-purple-100 dark:bg-purple-900/20 text-purple-600 border-purple-200 dark:border-purple-800'
    }
    if (type.includes('http') || name.includes('http')) {
      return 'bg-orange-100 dark:bg-orange-900/20 text-orange-600 border-orange-200 dark:border-orange-800'
    }
    if (type.includes('response') || name.includes('response')) {
      return 'bg-green-100 dark:bg-green-900/20 text-green-600 border-green-200 dark:border-green-800'
    }
    if (type.includes('condition') || type.includes('if')) {
      return 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-600 border-yellow-200 dark:border-yellow-800'
    }
    
    return 'bg-gray-100 dark:bg-gray-900/20 text-gray-600 border-gray-200 dark:border-gray-800'
  }

  const displayNodes = nodes?.slice(0, 6) || [] // 최대 6개 노드만 표시
  const hasMoreNodes = (nodes?.length || 0) > 6

  return (
    <div className={`space-y-2 ${className}`}>
      {/* 플로우 차트 제목 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <GitBranch className="w-4 h-4 text-accent-cyan" />
          <span className="text-sm font-medium text-foreground">{t('dashboard.workflow.workflow.workflowChart')}</span>
        </div>
        {hasMoreNodes && (
          <span className="text-xs text-muted-foreground">+{(nodes?.length || 0) - 6}{t('dashboard.workflow.miniFlow.moreNodes')}</span>
        )}
      </div>
      
      {/* 플로우 차트 */}
      <div className="flex items-center space-x-1 overflow-x-auto pb-1">
        {displayNodes.map((node, index) => (
          <div key={node.id || index} className="flex items-center space-x-1 flex-shrink-0">
            {/* 노드 */}
            <div 
              className={`flex items-center space-x-1 px-2 py-1 rounded text-xs border transition-all duration-200 hover:scale-105 ${
                getNodeColor(node.type, node.name)
              }`}
              title={`${node.name || node.type || 'Unknown'} (${node.type || 'unknown'})`}
            >
              {getNodeIcon(node.type, node.name)}
              <span className="max-w-16 truncate">
                {node.name || node.type || 'Node'}
              </span>
            </div>
            
            {/* 연결 화살표 */}
            {index < displayNodes.length - 1 && (
              <ArrowRight className="w-3 h-3 text-muted-foreground flex-shrink-0" />
            )}
          </div>
        ))}
        
        {/* 더 많은 노드가 있을 때 */}
        {hasMoreNodes && (
          <div className="flex items-center space-x-1 flex-shrink-0">
            <ArrowRight className="w-3 h-3 text-muted-foreground" />
            <div className="flex items-center space-x-1 px-2 py-1 rounded text-xs border bg-muted/30 text-muted-foreground border-border">
              <MoreHorizontal className="w-3 h-3" />
              <span>더보기</span>
            </div>
          </div>
        )}
      </div>
      
      {/* 워크플로우 요약 */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center space-x-2">
          <Play className="w-3 h-3" />
          <ArrowRight className="w-3 h-3" />
          <Settings className="w-3 h-3" />
          <ArrowRight className="w-3 h-3" />
          <CheckCircle className="w-3 h-3" />
        </div>
        <span>{nodes?.length || 0}개 노드</span>
      </div>
    </div>
  )
}

interface WorkflowItem {
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

interface Execution {
  id: string
  workflow_id: string
  status: string
  started_at: string
  finished_at?: string
  data: any
}

interface Template {
  id: string
  name: string
  description: string
  category: string
  nodes: any[]
  connections: any
}

export default function WorkflowPage() {
  const { t } = useTranslation()
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([])
  const [executions, setExecutions] = useState<Execution[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'workflows' | 'executions' | 'templates' | 'test'>('workflows')
  const [n8nHealth, setN8nHealth] = useState<'healthy' | 'unhealthy' | 'checking'>('checking')
  
  // 템플릿 필터링 및 정렬 상태
  const [selectedCategory, setSelectedCategory] = useState<string>(t('dashboard.workflow.form.allCategories'))
  const [sortBy, setSortBy] = useState<string>(t('dashboard.workflow.form.sortByName'))

  // 워크플로우 실행 결과 상태
  const [executionResults, setExecutionResults] = useState<{ [key: string]: any }>({})
  const [executingWorkflows, setExecutingWorkflows] = useState<Set<string>>(new Set())
  const [showExecutionResult, setShowExecutionResult] = useState<string | null>(null)

  // 템플릿 카테고리 목록 생성
  const getTemplateCategories = () => {
    if (!templates || templates.length === 0) return [t('dashboard.workflow.form.allCategories')]
    const categories = [...new Set(templates.map(t => t.category))]
    return [t('dashboard.workflow.form.allCategories'), ...categories.sort()]
  }

  // 템플릿 필터링 및 정렬
  const getFilteredAndSortedTemplates = () => {
    if (!templates) return []
    
    let filtered = templates
    
    // 카테고리 필터링
    if (selectedCategory !== t('dashboard.workflow.form.allCategories')) {
      filtered = filtered.filter(template => template.category === selectedCategory)
    }
    
    // 정렬
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case t('dashboard.workflow.form.sortByName'):
          return a.name.localeCompare(b.name)
        case t('dashboard.workflow.form.sortByCategory'):
          return a.category.localeCompare(b.category)
        case t('dashboard.workflow.form.sortByNodesDesc'):
          return (b.nodes?.length || 0) - (a.nodes?.length || 0)
        case t('dashboard.workflow.form.sortByNodesAsc'):
          return (a.nodes?.length || 0) - (b.nodes?.length || 0)
        default:
          return 0
      }
    })
    
    return sorted
  }

  // n8n 서비스 상태 확인
  const checkN8nHealth = async () => {
    try {
      // 캐시를 무시하고 새로 요청
      const response = await fetch('http://localhost:8000/api/v1/workflow/health', {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('Health check response:', data) // 디버깅용 로그
      
      setN8nHealth(data.status === 'healthy' ? 'healthy' : 'unhealthy')
    } catch (error) {
      console.error('n8n health check failed:', error)
      setN8nHealth('unhealthy')
    }
  }

  // 워크플로우 목록 조회
  const fetchWorkflows = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/workflow/workflows', {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setWorkflows(data)
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
    }
  }

  // 실행 기록 조회
  const fetchExecutions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/workflow/executions?limit=10', {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setExecutions(data.data || [])
      }
    } catch (error) {
      console.error('Failed to fetch executions:', error)
    }
  }

  // 템플릿 목록 조회
  const fetchTemplates = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/workflow/workflow-templates', {
        cache: 'no-cache',
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
      console.error('Failed to fetch templates:', error)
    }
  }

  // 워크플로우 활성화/비활성화
  const toggleWorkflow = async (workflowId: string, active: boolean) => {
    try {
      const endpoint = active ? 'deactivate' : 'activate'
      const response = await fetch(`/api/v1/workflow/workflows/${workflowId}/${endpoint}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        await fetchWorkflows()
      }
    } catch (error) {
      console.error('Failed to toggle workflow:', error)
    }
  }

  // 워크플로우 실행
  const executeWorkflow = async (workflowId: string) => {
    // 실행 시작 상태로 설정
    setExecutingWorkflows(prev => new Set([...prev, workflowId]))
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/workflow/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          workflow_id: workflowId,
          input_data: {}
        })
      })
      
      const result = await response.json()
      
      // 실행 결과 저장
      setExecutionResults(prev => ({
        ...prev,
        [workflowId]: {
          success: response.ok,
          status: response.status,
          data: result,
          timestamp: new Date().toISOString(),
          workflowName: workflows.find(w => w.id === workflowId)?.name || 'Unknown'
        }
      }))
      
      // 결과 팝업 표시
      setShowExecutionResult(workflowId)
      
      if (response.ok) {
        await fetchExecutions()
      }
    } catch (error) {
      console.error('Failed to execute workflow:', error)
      
      // 에러 결과 저장
      setExecutionResults(prev => ({
        ...prev,
        [workflowId]: {
          success: false,
          status: 0,
          data: { error: error instanceof Error ? error.message : 'Unknown error' },
          timestamp: new Date().toISOString(),
          workflowName: workflows.find(w => w.id === workflowId)?.name || 'Unknown'
        }
      }))
      
      setShowExecutionResult(workflowId)
    } finally {
      // 실행 완료 상태로 설정
      setExecutingWorkflows(prev => {
        const newSet = new Set(prev)
        newSet.delete(workflowId)
        return newSet
      })
    }
  }

  // 워크플로우 삭제
  const deleteWorkflow = async (workflowId: string) => {
    if (!confirm(t('dashboard.workflow.messages.deleteConfirm'))) return
    
    try {
      const response = await fetch(`/api/v1/workflow/workflows/${workflowId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        await fetchWorkflows()
      }
    } catch (error) {
      console.error('Failed to delete workflow:', error)
    }
  }

  // 템플릿에서 워크플로우 생성
  const createFromTemplate = async (templateId: string) => {
    const name = prompt(t('dashboard.workflow.messages.promptWorkflowName'))
    if (!name) return

    try {
      const response = await fetch(`/api/v1/workflow/workflows/from-template/${templateId}?name=${encodeURIComponent(name)}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        await fetchWorkflows()
        setActiveTab('workflows')
      }
    } catch (error) {
      console.error('Failed to create workflow from template:', error)
    }
  }

  // 모든 템플릿 워크플로우를 n8n에 생성
  const createAllTemplateWorkflows = async () => {
    if (!confirm(t('dashboard.workflow.messages.createAllConfirm'))) return

    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/v1/workflow/workflow-templates/create-all', {
        method: 'POST'
      })
      
      const result = await response.json()
      
      if (response.ok) {
        alert(`🎉 성공!\n\n생성된 워크플로우: ${result.created_workflows.length}개\n실패한 워크플로우: ${result.failed_workflows.length}개\n\n성공률: ${result.success_rate}`)
        await fetchWorkflows()
        setActiveTab('workflows')
      } else {
        alert(`❌ 실패: ${result.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('Failed to create all template workflows:', error)
      alert('❌ 템플릿 워크플로우 생성 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // 특정 템플릿 워크플로우를 n8n에 생성
  const createSingleTemplateWorkflow = async (templateId: string) => {
    if (!confirm(t('dashboard.workflow.messages.createTemplateConfirm'))) return

    setLoading(true)
    try {
      const response = await fetch(`/api/v1/workflow/workflow-templates/${templateId}/create`, {
        method: 'POST'
      })
      
      const result = await response.json()
      
      if (response.ok) {
        const workflow = result.workflow
        let message = `🎉 워크플로우 생성 성공!\n\n이름: ${workflow.template_name}\nn8n ID: ${workflow.n8n_workflow_id}`
        
        if (workflow.webhook_url) {
          message += `\n\n웹훅 URL:\n📤 프로덕션: ${workflow.webhook_url}\n🧪 테스트: ${workflow.test_webhook_url}`
        }
        
        alert(message)
        await fetchWorkflows()
        setActiveTab('workflows')
      } else {
        alert(`❌ 실패: ${result.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('Failed to create template workflow:', error)
      alert('❌ 템플릿 워크플로우 생성 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // n8n 웹 인터페이스 열기
  const openN8nInterface = () => {
    window.open('http://localhost:5678', '_blank')
  }

  // 데이터 새로고침
  const refreshData = async () => {
    setLoading(true)
    await Promise.all([
      checkN8nHealth(),
      fetchWorkflows(),
      fetchExecutions(),
      fetchTemplates()
    ])
    setLoading(false)
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([
        checkN8nHealth(),
        fetchWorkflows(),
        fetchExecutions(),
        fetchTemplates()
      ])
      setLoading(false)
    }

    loadData()
  }, [])

  const getStatusIcon = (status: string) => {
    // null/undefined 체크 추가
    if (!status) {
      return <Clock className="w-4 h-4 text-gray-500" />
    }
    
    switch (status.toLowerCase()) {
      case 'success':
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('ko-KR')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="text-center bg-card backdrop-blur-sm border border-border rounded-lg p-12">
          <div className="w-16 h-16 bg-accent-cyan/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <RefreshCw className="w-8 h-8 animate-spin text-accent-cyan" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">Loading Workflows</h3>
          <p className="text-muted-foreground">{t('dashboard.workflow.messages.loadingWorkflows')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
        {/* 헤더 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center">
                <Workflow className="w-8 h-8 mr-3 text-accent-cyan" />
                {t('nav.workflow') || t('dashboard.workflow.header.title')}
              </h1>
              <p className="text-muted-foreground text-lg">{t('dashboard.workflow.header.subtitle')}</p>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* n8n 상태 표시 */}
              <div className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-card backdrop-blur-sm border border-border">
                <div className={`w-3 h-3 rounded-full ${
                  n8nHealth === 'healthy' ? 'bg-green-500' : 
                  n8nHealth === 'unhealthy' ? 'bg-red-500' : 'bg-yellow-500'
                }`} />
                <span className="text-sm text-foreground">
                  n8n {n8nHealth === 'healthy' ? t('dashboard.workflow.status.healthy') : n8nHealth === 'unhealthy' ? t('dashboard.workflow.status.unhealthy') : t('dashboard.workflow.status.checking')}
                </span>
              </div>
              
              {/* n8n 인터페이스 열기 */}
              <button
                onClick={openN8nInterface}
                className="flex items-center space-x-2 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
              >
                <ExternalLink className="w-5 h-5" />
                <span>{t('dashboard.workflow.buttons.openN8n')}</span>
              </button>
              
              {/* 새로고침 */}
              <button
                onClick={refreshData}
                disabled={loading}
                className="p-3 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-300 disabled:opacity-50"
                title={t('dashboard.workflow.buttons.refresh')}
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Status Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title={t('dashboard.workflow.statusCards.totalWorkflows')}
            value={workflows?.length || 0}
            icon={<Workflow className="w-6 h-6 text-white" />}
            color="#3b82f6"
          />
          <StatusCard
            title={t('dashboard.workflow.statusCards.activeWorkflows')}
            value={workflows?.filter(w => w.active).length || 0}
            icon={<Activity className="w-6 h-6 text-white" />}
            color="#22c55e"
          />
          <StatusCard
            title={t('dashboard.workflow.statusCards.totalTemplates')}
            value={templates?.length || 0}
            icon={<Copy className="w-6 h-6 text-white" />}
            color="#f97316"
          />
          <StatusCard
            title={t('dashboard.workflow.statusCards.n8nStatus')}
            value={n8nHealth === 'healthy' ? t('dashboard.workflow.status.healthy') : n8nHealth === 'unhealthy' ? t('dashboard.workflow.status.unhealthy') : t('dashboard.workflow.status.checking')}
            icon={<Server className="w-6 h-6 text-white" />}
            color={n8nHealth === 'healthy' ? '#22c55e' : n8nHealth === 'unhealthy' ? '#ef4444' : '#f97316'}
          />
        </div>

        {/* 탭 네비게이션 */}
        <TabNavigation
          tabs={[
            { id: 'workflows', name: t('dashboard.workflow.tabs.workflows'), icon: Workflow },
            { id: 'executions', name: t('dashboard.workflow.tabs.executions'), icon: Activity },
            { id: 'templates', name: t('dashboard.workflow.tabs.templates'), icon: Copy },
            { id: 'test', name: t('dashboard.workflow.tabs.test'), icon: Play }
          ]}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as 'workflows' | 'executions' | 'templates' | 'test')}
        />

        {/* 워크플로우 탭 */}
        {activeTab === 'workflows' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-accent-cyan" />
                {t('dashboard.workflow.sections.workflowList')}
              </h2>
              <div className="text-sm text-muted-foreground bg-muted/30 px-3 py-1 rounded-lg">
                {t('dashboard.workflow.stats.total')} {workflows?.length || 0}{t('dashboard.workflow.stats.workflows')}
              </div>
            </div>
            
            {!workflows || workflows.length === 0 ? (
              <div className="text-center py-16 bg-card backdrop-blur-sm border border-border rounded-lg">
                <div className="mb-6">
                  <div className="w-20 h-20 bg-accent-cyan/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Workflow className="w-10 h-10 text-accent-cyan" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">{t('dashboard.workflow.emptyState.noWorkflows.title')}</h3>
                <p className="text-muted-foreground mb-2">{t('dashboard.workflow.emptyState.noWorkflows.subtitle')}</p>
                <p className="text-sm text-muted-foreground mb-6">{t('dashboard.workflow.emptyState.noWorkflows.description')}</p>
                <button
                  onClick={() => setActiveTab('templates')}
                  className="px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
                >
                  <Plus className="w-4 h-4 inline mr-2" />
                  {t('dashboard.workflow.buttons.showTemplates')}
                </button>
              </div>
            ) : (
              <div className="grid gap-6">
                {(workflows || []).map((workflow) => (
                  <div key={workflow.id} className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 shadow-sm group">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-3">
                          <h3 className="text-lg font-semibold text-foreground group-hover:text-accent-cyan transition-colors">{workflow.name}</h3>
                          <div className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all duration-300 ${
                            workflow.active 
                              ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800' 
                              : 'bg-gray-100 dark:bg-gray-900/20 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-800'
                          }`}>
                            {workflow.active ? t('dashboard.workflow.status.active') : t('dashboard.workflow.status.inactive')}
                          </div>
                          
                          {/* 실행 상태 인디케이터 */}
                          {executingWorkflows.has(workflow.id) && (
                            <div className="flex items-center space-x-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 text-xs rounded-lg border border-blue-200 dark:border-blue-800">
                              <RefreshCw className="w-3 h-3 animate-spin" />
                              <span>{t('dashboard.workflow.buttons.executing')}</span>
                            </div>
                          )}
                          
                          {/* 최근 실행 결과 인디케이터 */}
                          {!executingWorkflows.has(workflow.id) && executionResults[workflow.id] && (
                            <div className={`flex items-center space-x-1 px-2 py-1 text-xs rounded-lg border ${
                              executionResults[workflow.id].success
                                ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800'
                                : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800'
                            }`}>
                              {executionResults[workflow.id].success ? (
                                <CheckCircle className="w-3 h-3" />
                              ) : (
                                <XCircle className="w-3 h-3" />
                              )}
                              <span>{executionResults[workflow.id].success ? t('dashboard.workflow.messages.executionSuccess') : t('dashboard.workflow.messages.executionFailed')}</span>
                            </div>
                          )}
                          {(workflow.tags || []).map((tag) => (
                            <span key={tag} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 text-xs rounded-lg border border-blue-200 dark:border-blue-800">
                              {tag}
                            </span>
                          ))}
                        </div>
                        <p className="text-muted-foreground mb-4">{workflow.description || t('dashboard.workflow.messages.noDescription')}</p>
                        
                        {/* 미니 플로우 차트 */}
                        {workflow.nodes && workflow.nodes.length > 0 && (
                          <div className="mb-4 p-4 bg-muted/20 rounded-lg border border-border/50">
                            <MiniWorkflowChart 
                              nodes={workflow.nodes} 
                              t={t}
                            />
                          </div>
                        )}
                        
                        <div className="flex items-center space-x-6 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Settings className="w-4 h-4" />
                            <span>{t('dashboard.workflow.workflow.nodes')}: {workflow.nodes?.length || 0}{t('dashboard.workflow.stats.nodes')}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            <span>{t('dashboard.workflow.workflow.created')}: {formatDate(workflow.created_at)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <RefreshCw className="w-4 h-4" />
                            <span>{t('dashboard.workflow.workflow.updated')}: {formatDate(workflow.updated_at)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => executeWorkflow(workflow.id)}
                          disabled={executingWorkflows.has(workflow.id)}
                          className={`p-2 rounded-lg border border-border transition-all duration-300 group/btn ${
                            executingWorkflows.has(workflow.id)
                              ? 'text-blue-600 bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 cursor-not-allowed'
                              : 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20 hover:border-green-300 dark:hover:border-green-700'
                          }`}
                          title={executingWorkflows.has(workflow.id) ? t('dashboard.workflow.buttons.executing') : t('dashboard.workflow.buttons.execute')}
                        >
                          {executingWorkflows.has(workflow.id) ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <Play className="w-4 h-4 group-hover/btn:scale-110 transition-transform" />
                          )}
                        </button>
                        
                        {/* 실행 결과 보기 버튼 */}
                        {executionResults[workflow.id] && (
                          <button
                            onClick={() => setShowExecutionResult(workflow.id)}
                            className={`p-2 rounded-lg border border-border transition-all duration-300 group/btn ${
                              executionResults[workflow.id].success
                                ? 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20 hover:border-green-300 dark:hover:border-green-700'
                                : 'text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-300 dark:hover:border-red-700'
                            }`}
                            title={t('dashboard.workflow.buttons.viewResult')}
                          >
                            <Eye className="w-4 h-4 group-hover/btn:scale-110 transition-transform" />
                          </button>
                        )}
                        
                        <button
                          onClick={() => toggleWorkflow(workflow.id, workflow.active)}
                          className={`p-2 rounded-lg border border-border transition-all duration-300 group/btn ${
                            workflow.active
                              ? 'text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 hover:border-yellow-300 dark:hover:border-yellow-700'
                              : 'text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-700'
                          }`}
                          title={workflow.active ? t('dashboard.workflow.buttons.deactivate') : t('dashboard.workflow.buttons.activate')}
                        >
                          {workflow.active ? 
                            <Pause className="w-4 h-4 group-hover/btn:scale-110 transition-transform" /> : 
                            <Play className="w-4 h-4 group-hover/btn:scale-110 transition-transform" />
                          }
                        </button>
                        
                        <button
                          onClick={() => deleteWorkflow(workflow.id)}
                          className="p-2 rounded-lg border border-border text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-300 dark:hover:border-red-700 transition-all duration-300 group/btn"
                          title={t('dashboard.workflow.buttons.delete')}
                        >
                          <Trash2 className="w-4 h-4 group-hover/btn:scale-110 transition-transform" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 실행 기록 탭 */}
        {activeTab === 'executions' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <Activity className="w-5 h-5 text-accent-green" />
                {t('dashboard.workflow.sections.executionHistory')}
              </h2>
              <div className="text-sm text-muted-foreground bg-muted/30 px-3 py-1 rounded-lg">
                {t('dashboard.workflow.stats.recent')} {executions?.length || 0}{t('dashboard.workflow.stats.executions')}
              </div>
            </div>
            
            {!executions || executions.length === 0 ? (
              <div className="text-center py-16 bg-card backdrop-blur-sm border border-border rounded-lg">
                <div className="mb-6">
                  <div className="w-20 h-20 bg-accent-green/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Activity className="w-10 h-10 text-accent-green" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">{t('dashboard.workflow.emptyState.noExecutions.title')}</h3>
                <p className="text-muted-foreground mb-6">{t('dashboard.workflow.emptyState.noExecutions.subtitle')}</p>
                <button
                  onClick={() => setActiveTab('workflows')}
                  className="px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
                >
                  <Play className="w-4 h-4 inline mr-2" />
                  {t('dashboard.workflow.buttons.runWorkflow')}
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {(executions || []).map((execution) => (
                  <div key={execution.id} className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 shadow-sm group">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="p-2 rounded-lg bg-muted/30">
                          {getStatusIcon(execution.status || 'unknown')}
                        </div>
                        <div>
                          <div className="font-semibold text-foreground group-hover:text-accent-green transition-colors">
                            실행 ID: {execution.id}
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            워크플로우: {execution.workflow_id}
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right text-sm text-muted-foreground">
                        <div className="flex items-center gap-1 justify-end">
                          <Clock className="w-3 h-3" />
                          <span>시작: {formatDate(execution.started_at)}</span>
                        </div>
                        {execution.finished_at && (
                          <div className="flex items-center gap-1 justify-end mt-1">
                            <CheckCircle className="w-3 h-3" />
                            <span>완료: {formatDate(execution.finished_at)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 템플릿 탭 */}
        {activeTab === 'templates' && (
          <div className="space-y-6">
            {/* 헤더 및 필터 */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
                  <Copy className="w-5 h-5 text-accent-purple" />
                  {t('dashboard.workflow.sections.workflowTemplates')}
                </h2>
                <button
                  onClick={createAllTemplateWorkflows}
                  disabled={loading || !templates || templates.length === 0}
                  className="flex items-center space-x-2 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Plus className="w-5 h-5" />
                  <span>{t('dashboard.workflow.buttons.createAllTemplates')}</span>
                </button>
              </div>
              
              {/* 필터링 및 정렬 옵션 */}
              <div className="flex items-center justify-between bg-card backdrop-blur-sm border border-border rounded-lg p-4">
                <div className="flex items-center space-x-4">
                  <Select
                    value={selectedCategory}
                    onChange={setSelectedCategory}
                    options={getTemplateCategories()}
                    label={t('dashboard.workflow.form.category')}
                    className="min-w-[140px]"
                  />
                  <Select
                    value={sortBy}
                    onChange={setSortBy}
                    options={[
                      t('dashboard.workflow.form.sortByName'), 
                      t('dashboard.workflow.form.sortByCategory'), 
                      t('dashboard.workflow.form.sortByNodesDesc'), 
                      t('dashboard.workflow.form.sortByNodesAsc')
                    ]}
                    label={t('dashboard.workflow.form.sortBy')}
                    className="min-w-[120px]"
                  />
                </div>
                <div className="text-sm text-muted-foreground bg-muted/30 px-3 py-1 rounded-lg">
                  {getFilteredAndSortedTemplates().length} / {templates?.length || 0}{t('dashboard.workflow.stats.templates')}
                </div>
              </div>
            </div>
            
            {/* 템플릿 목록 */}
            {!templates || templates.length === 0 ? (
              <div className="text-center py-16 bg-card backdrop-blur-sm border border-border rounded-lg">
                <div className="mb-6">
                  <div className="w-20 h-20 bg-accent-purple/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Copy className="w-10 h-10 text-accent-purple" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">Loading Templates</h3>
                <p className="text-muted-foreground mb-6">템플릿을 로드하는 중...</p>
                <button
                  onClick={fetchTemplates}
                  className="px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
                >
                  <RefreshCw className="w-4 h-4 inline mr-2" />
                  템플릿 새로고침
                </button>
              </div>
            ) : getFilteredAndSortedTemplates().length === 0 ? (
              <div className="text-center py-16 bg-card backdrop-blur-sm border border-border rounded-lg">
                <div className="mb-6">
                  <div className="w-20 h-20 bg-accent-purple/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Copy className="w-10 h-10 text-accent-purple" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">No Templates Found</h3>
                <p className="text-muted-foreground mb-6">선택한 조건에 맞는 템플릿이 없습니다.</p>
                <button
                  onClick={() => {
                    setSelectedCategory(t('dashboard.workflow.form.allCategories'))
                    setSortBy(t('dashboard.workflow.form.sortByName'))
                  }}
                  className="px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
                >
                  <RefreshCw className="w-4 h-4 inline mr-2" />
                  {t('dashboard.workflow.buttons.resetFilter')}
                </button>
              </div>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {getFilteredAndSortedTemplates().map((template) => (
                <div key={template.id} className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 shadow-sm group">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-foreground group-hover:text-accent-purple transition-colors mb-3">
                        {template.name}
                      </h3>
                      <span className="inline-block px-3 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 text-xs rounded-lg border border-blue-200 dark:border-blue-800">
                        {template.category}
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-muted-foreground text-sm mb-4 line-clamp-2">{template.description}</p>
                  
                  <div className="flex items-center gap-1 text-xs text-muted-foreground mb-6">
                    <Settings className="w-3 h-3" />
                    <span>{t('dashboard.workflow.workflow.nodes')}: {template.nodes?.length || 0}{t('dashboard.workflow.stats.nodes')}</span>
                  </div>
                  
                  <div className="space-y-3">
                    <button
                      onClick={() => createSingleTemplateWorkflow(template.id)}
                      disabled={loading}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg bg-gradient-primary hover:opacity-90 text-white font-semibold disabled:opacity-50 transition-all duration-300 shadow-sm"
                    >
                      <Plus className="w-4 h-4" />
                      <span>{t('dashboard.workflow.buttons.createInN8n')}</span>
                    </button>
                    
                    <button
                      onClick={() => createFromTemplate(template.id)}
                      disabled={loading}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg border border-border text-foreground hover:bg-muted/50 disabled:opacity-50 transition-all duration-300"
                    >
                      <Copy className="w-4 h-4" />
                      <span>{t('dashboard.workflow.buttons.templateCopy')}</span>
                    </button>
                  </div>
                </div>
              ))}
              </div>
            )}
          </div>
        )}

        {/* 테스트 탭 */}
        {activeTab === 'test' && (
          <WorkflowTester />
        )}

        {/* 실행 결과 모달 */}
        <ExecutionResultModal
          workflowId={showExecutionResult}
          result={showExecutionResult ? executionResults[showExecutionResult] : null}
          isOpen={!!showExecutionResult}
          onClose={() => setShowExecutionResult(null)}
          t={t}
        />
    </div>
  )
} 