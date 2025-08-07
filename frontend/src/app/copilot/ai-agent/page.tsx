'use client'

import { useState, useEffect } from 'react'
import {
  Bot,
  Plus,
  Edit,
  Trash2,
  MessageCircle,
  Clock,
  XCircle,
  Copy,
  ExternalLink,
  RefreshCw,
  Server,
  Brain,
  ArrowRight,
  Key,
  Zap,
  FileText,
  MoreHorizontal,
  Activity,
  AlertCircle
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { TabNavigation, Select } from '@/components/ui'
import MarkdownRenderer from '@/components/MarkdownRenderer'

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

// ============================
// AI 에이전트 인터페이스
// ============================

interface Agent {
  id: string
  name: string
  description: string
  type: 'chatbot' | 'workflow' | 'agent' | 'completion'
  status: 'active' | 'inactive' | 'error'
  created_at: string
  last_used?: string
  conversation_count: number
  api_key: string
}

interface AgentTemplate {
  id: string
  name: string
  description: string
  category: string
  agent_type: string
  instructions: string
  opening_statement: string
  suggested_questions: string[]
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

// 에이전트별 대화 기록을 저장하는 전역 상태 (로컬 스토리지 연동)
const CHAT_HISTORY_KEY = 'dify_agent_chat_history'

// 로컬 스토리지에서 대화 기록 로드
const loadChatHistoryFromStorage = (): { [agentId: string]: { messages: ChatMessage[], conversationId: string } } => {
  try {
    const stored = localStorage.getItem(CHAT_HISTORY_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch (error) {
    console.error('Failed to load chat history from localStorage:', error)
    return {}
  }
}

// 로컬 스토리지에 대화 기록 저장
const saveChatHistoryToStorage = (history: { [agentId: string]: { messages: ChatMessage[], conversationId: string } }) => {
  try {
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history))
  } catch (error) {
    console.error('Failed to save chat history to localStorage:', error)
  }
}

// 초기 로드 시 로컬 스토리지에서 대화 기록 복원
const agentChatHistory: { [agentId: string]: { messages: ChatMessage[], conversationId: string } } = loadChatHistoryFromStorage()

// 특정 에이전트의 대화 기록 삭제
const clearAgentChatHistory = (agentId: string) => {
  if (agentChatHistory[agentId]) {
    agentChatHistory[agentId] = { messages: [], conversationId: '' }
    saveChatHistoryToStorage(agentChatHistory)
  }
}

// 모든 대화 기록 삭제
const clearAllChatHistory = () => {
  localStorage.removeItem(CHAT_HISTORY_KEY)
  Object.keys(agentChatHistory).forEach(agentId => {
    agentChatHistory[agentId] = { messages: [], conversationId: '' }
  })
}

// ============================
// AI 에이전트 카드 컴포넌트 (통일된 스타일)
// ============================

interface AgentCardProps {
  agent: Agent
  onEdit: (agent: Agent) => void
  onDelete: (agent: Agent) => void
  onChat: (agent: Agent) => void
  onSetApiKey: (agent: Agent) => void
}

const AgentCard: React.FC<AgentCardProps> = ({ agent, onEdit, onDelete, onChat, onSetApiKey }) => {
  const { t } = useTranslation()
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-accent-cyan bg-accent-cyan/10'
      case 'inactive': return 'text-muted-foreground bg-muted'
      case 'error': return 'text-accent-orange bg-accent-orange/10'
      default: return 'text-muted-foreground bg-muted'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'chatbot': return <MessageCircle className="w-4 h-4" />
      case 'workflow': return <ArrowRight className="w-4 h-4" />
      case 'agent': return <Brain className="w-4 h-4" />
      case 'completion': return <FileText className="w-4 h-4" />
      default: return <Bot className="w-4 h-4" />
    }
  }

  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 transition-all duration-300 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
            {getTypeIcon(agent.type)}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">{agent.name}</h3>
            <p className="text-sm text-muted-foreground">{agent.description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(agent.status)}`}>
            {agent.status}
          </span>
          <div className="relative">
            <button className="p-1 text-muted-foreground hover:text-foreground transition-colors">
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <MessageCircle className="w-4 h-4" />
            <span>{agent.conversation_count} {t('dashboard.aiAgent.agent.conversations') || '대화'}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Clock className="w-4 h-4" />
            <span>{agent.last_used ? new Date(agent.last_used).toLocaleDateString() : t('dashboard.aiAgent.status.notUsed')}</span>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <Key className="w-4 h-4" />
          <span className={
            agent.api_key && agent.api_key !== 'Not set' && agent.api_key.startsWith('app-')
              ? 'text-accent-cyan'
              : 'text-accent-orange'
          }>
            {agent.api_key && agent.api_key !== 'Not set' && agent.api_key.startsWith('app-')
              ? `${t('dashboard.aiAgent.status.configured')} ✓`
              : t('dashboard.aiAgent.status.notConfigured')}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onChat(agent)}
            disabled={agent.status !== 'active' || !agent.api_key || agent.api_key === 'Not set' || !agent.api_key.startsWith('app-')}
            className="flex items-center space-x-1 px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <MessageCircle className="w-4 h-4" />
            <span>{t('dashboard.aiAgent.buttons.chat')}</span>
          </button>
          <button
            onClick={() => onSetApiKey(agent)}
            className="flex items-center space-x-1 px-3 py-1.5 bg-muted text-muted-foreground rounded-md text-sm font-medium hover:bg-muted/80 transition-colors"
          >
            <Key className="w-4 h-4" />
            <span>{t('dashboard.aiAgent.form.apiKey')}</span>
          </button>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => onEdit(agent)}
            className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded-md"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(agent)}
            className="p-1.5 text-muted-foreground hover:text-accent-orange transition-colors rounded-md"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================
// 채팅 모달 컴포넌트
// ============================

interface ChatModalProps {
  agent: Agent | null
  isOpen: boolean
  onClose: () => void
  t: (key: string) => string
}

const ChatModal: React.FC<ChatModalProps> = ({ agent, isOpen, onClose, t }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string>('')
  const [userId] = useState(() => 'user_' + Date.now()) // 세션별 고정 user_id

  // 에이전트가 변경될 때 해당 에이전트의 대화 기록 로드
  useEffect(() => {
    if (isOpen && agent) {
      // 해당 에이전트의 기존 대화 기록이 있으면 복원
      if (agentChatHistory[agent.id]) {
        setMessages(agentChatHistory[agent.id].messages)
        setConversationId(agentChatHistory[agent.id].conversationId)
      } else {
        // 새 에이전트인 경우 초기화
        setMessages([])
        setConversationId('')
        agentChatHistory[agent.id] = { messages: [], conversationId: '' }
        saveChatHistoryToStorage(agentChatHistory) // 새 에이전트도 로컬 스토리지에 저장
      }

      // 항상 초기화해야 하는 상태들
      setInputValue('')    // 입력 필드 초기화
      setIsLoading(false)  // 로딩 상태 초기화
    }
  }, [isOpen, agent])

  const sendMessage = async () => {
    if (!inputValue.trim() || !agent) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInputValue('')
    setIsLoading(true)

    // 에이전트별 대화 기록 업데이트
    if (agent) {
      agentChatHistory[agent.id].messages = newMessages
      saveChatHistoryToStorage(agentChatHistory) // 로컬 스토리지에 저장
    }

    try {
      const response = await fetch(`/api/v1/dify/agents/${agent.id}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          conversation_id: conversationId,
          user_id: userId,
          streaming: false
        })
      })

      if (!response.ok) {
        throw new Error(t('dashboard.aiAgent.messages.chatRequestFailed'))
      }

      const data = await response.json()

      if (data.success && data.response) {
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: data.response.answer,
          timestamp: new Date().toISOString()
        }

        const updatedMessages = [...newMessages, assistantMessage]
        setMessages(updatedMessages)

        // conversation_id 업데이트
        if (data.response.conversation_id) {
          setConversationId(data.response.conversation_id)
        }

        // 에이전트별 대화 기록 업데이트 (AI 응답 포함)
        if (agent) {
          agentChatHistory[agent.id].messages = updatedMessages
          if (data.response.conversation_id) {
            agentChatHistory[agent.id].conversationId = data.response.conversation_id
          }
          saveChatHistoryToStorage(agentChatHistory) // 로컬 스토리지에 저장
        }
      }
    } catch (error) {
      console.error('채팅 오류:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: t('dashboard.aiAgent.messages.chatError'),
        timestamp: new Date().toISOString()
      }
      const errorMessages = [...newMessages, errorMessage]
      setMessages(errorMessages)

      // 에러 메시지도 대화 기록에 저장
      if (agent) {
        agentChatHistory[agent.id].messages = errorMessages
        saveChatHistoryToStorage(agentChatHistory) // 로컬 스토리지에 저장
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (!isOpen || !agent) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col shadow-xl">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{agent.name}</h3>
              <p className="text-sm text-muted-foreground">{t('dashboard.aiAgent.agent.assistant') || 'AI 어시스턴트'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-muted-foreground hover:text-foreground transition-colors rounded-md"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[400px]">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <Bot className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
              <p>{t('dashboard.aiAgent.messages.welcomeMessage') || '안녕하세요! 무엇을 도와드릴까요?'}</p>
            </div>
          )}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-lg ${message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                  }`}
              >
                {message.role === 'user' ? (
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div className="text-sm">
                    <MarkdownRenderer
                      content={message.content}
                      className="prose prose-sm max-w-none"
                    />
                  </div>
                )}
                <p className="text-xs opacity-70 mt-1">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted text-muted-foreground p-3 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 입력 영역 */}
        <div className="p-4 border-t border-border">
          <div className="flex items-end space-x-2">
            <div className="flex-1">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={t('dashboard.aiAgent.messages.inputPlaceholder') || '메시지를 입력하세요...'}
                className="w-full p-3 border border-border rounded-lg resize-none bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                rows={2}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="p-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================
// API 키 설정 모달
// ============================

interface ApiKeyModalProps {
  agent: Agent | null
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  t: (key: string) => string
}

const ApiKeyModal: React.FC<ApiKeyModalProps> = ({ agent, isOpen, onClose, onSuccess, t }) => {
  const [apiKey, setApiKey] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // 모달이 열릴 때마다 상태 초기화
  useEffect(() => {
    if (isOpen && agent) {
      setApiKey('') // API 키 입력 필드 초기화
      setError('')  // 에러 메시지 초기화
    }
  }, [isOpen, agent])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!agent || !apiKey.trim()) return

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch(`/api/v1/dify/agents/${agent.id}/api-key`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: apiKey.trim()
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'API 키 설정 실패')
      }

      onSuccess()
      onClose()
    } catch (error: any) {
      setError(error.message)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen || !agent) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-lg w-full max-w-md shadow-xl">
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <Key className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{t('dashboard.aiAgent.form.apiKey')}</h3>
              <p className="text-sm text-muted-foreground">{agent.name}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                {t('dashboard.aiAgent.form.difyApiKey') || 'Dify App API 키'}
              </label>
              <input
                type="text"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={t('dashboard.aiAgent.form.apiKeyPlaceholder') || 'app-xxxxxxxxxxxxxxxxx'}
                className="w-full p-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Dify 앱의 &quot;API 접근&quot; 페이지에서 발급받은 API 키를 입력하세요.
              </p>
            </div>

            {error && (
              <div className="p-4 bg-accent-orange/10 border border-accent-orange/20 rounded-lg">
                <p className="text-sm text-accent-orange whitespace-pre-line leading-relaxed">{error}</p>
              </div>
            )}

            <div className="flex items-center space-x-2 pt-4">
              <button
                type="submit"
                disabled={!apiKey.trim() || isLoading}
                className="flex-1 bg-primary text-primary-foreground rounded-lg py-2 px-4 font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? t('dashboard.aiAgent.buttons.saving') : t('dashboard.aiAgent.buttons.save')}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-muted text-muted-foreground rounded-lg py-2 px-4 font-medium hover:bg-muted/80 transition-colors"
              >
                {t('common.cancel')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// ============================
// 자동 에이전트 생성 함수
// ============================

const autoCreateAgent = async (templateId: string, name: string) => {
  try {
    const response = await fetch(`/api/v1/dify/agents/auto-create/${templateId}?name=${encodeURIComponent(name)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '자동 에이전트 생성 실패')
    }

    return data
  } catch (error: any) {
    throw new Error(error.message)
  }
}

// ============================
// 에이전트 생성 모달
// ============================

interface CreateAgentModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  templates: AgentTemplate[]
  t: (key: string) => string
}

const CreateAgentModal: React.FC<CreateAgentModalProps> = ({ isOpen, onClose, onSuccess, templates, t }) => {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [agentData, setAgentData] = useState({
    name: '',
    description: '',
    agent_type: 'chatbot'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isAutoCreating, setIsAutoCreating] = useState(false)
  const [error, setError] = useState('')

  // 모달이 열릴 때마다 폼 상태 초기화
  useEffect(() => {
    if (isOpen) {
      setSelectedTemplate('')  // 템플릿 선택 초기화
      setAgentData({          // 에이전트 데이터 초기화
        name: '',
        description: '',
        agent_type: 'chatbot'
      })
      setError('')            // 에러 메시지 초기화
      setIsLoading(false)     // 로딩 상태 초기화
      setIsAutoCreating(false) // 자동 생성 상태 초기화
    }
  }, [isOpen])

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId)
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setAgentData({
        name: template.name,
        description: template.description,
        agent_type: template.agent_type
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('/api/v1/dify/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(agentData)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || '에이전트 생성 실패')
      }

      onSuccess()
      onClose()
    } catch (error: any) {
      setError(error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAutoCreate = async (templateId: string, templateName: string) => {
    setIsAutoCreating(true)
    setError('')

    try {
      const customName = agentData.name || templateName
      const result = await autoCreateAgent(templateId, customName)

      if (result.success) {
        if (result.ready_to_use && result.auto_created) {
          // 완전 자동 생성 성공
          onSuccess()
          onClose()
          alert(`🎉 ${result.message}`)
        } else if (result.fallback_mode && result.setup_required) {
          // 폴백 모드 - 수동 설정 필요
          onSuccess()
          onClose()

          // 상세한 설정 안내 모달 표시
          const instructions = result.setup_instructions?.join('\n') || ''
          const message = `⚠️ ${result.message}\n\n📋 설정 방법:\n${instructions}`

          if (confirm(message + '\n\n지금 Dify 콘솔을 열어보시겠습니까?')) {
            window.open('http://localhost:3001', '_blank')
          }
        } else {
          // 기타 성공 케이스
          onSuccess()
          onClose()
          alert(`✅ ${result.message}`)
        }
      } else {
        throw new Error(result.message || '자동 생성에 실패했습니다.')
      }
    } catch (error: any) {
      // 에러 메시지 개선
      let errorMessage = error.message

      if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
        errorMessage = '⚠️ Dify 인증 오류\n\nDIFY_CONSOLE_API_KEY 환경변수가 설정되지 않았거나 잘못되었습니다.\n\n해결 방법:\n1. Dify 콘솔(http://localhost:3001)에서 Console API 키 생성\n2. 환경변수 설정 후 백엔드 재시작\n3. 또는 수동으로 에이전트를 생성하세요'
      } else if (errorMessage.includes('connection') || errorMessage.includes('timeout')) {
        errorMessage = '🔌 연결 오류\n\nDify 서비스에 연결할 수 없습니다.\n\n해결 방법:\n1. Dify 서비스가 실행 중인지 확인\n2. Docker 컨테이너 상태 확인: docker-compose ps\n3. 서비스 재시작: docker-compose restart'
      }

      setError(errorMessage)
    } finally {
      setIsAutoCreating(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-lg w-full max-w-lg max-h-[80vh] overflow-y-auto shadow-xl">
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <Plus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{t('dashboard.aiAgent.buttons.create')}</h3>
              <p className="text-sm text-muted-foreground">{t('dashboard.aiAgent.template.description')}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 템플릿 선택 */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">{t('dashboard.aiAgent.template.selectTemplate')}</label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    onClick={() => handleTemplateSelect(template.id)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${selectedTemplate === template.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:bg-muted/50'
                      }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                        <Bot className="w-4 h-4" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-foreground text-sm">{template.name}</h4>
                        <p className="text-xs text-muted-foreground mt-1">{template.description}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="px-2 py-1 bg-muted rounded text-xs text-muted-foreground">
                            {template.category}
                          </span>
                          <div className="flex items-center space-x-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleAutoCreate(template.id, template.name)
                              }}
                              disabled={isAutoCreating}
                              className="flex items-center space-x-1 px-2 py-1 bg-gradient-primary hover:opacity-90 text-white text-xs font-medium rounded transition-all duration-300 disabled:opacity-50"
                              title="Dify 앱까지 자동 생성하여 즉시 사용 가능"
                            >
                              <Zap className="w-3 h-3" />
                              <span>{isAutoCreating ? '생성중...' : '즉시 사용'}</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 기본 정보 */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">{t('dashboard.aiAgent.form.name')}</label>
                <input
                  type="text"
                  value={agentData.name}
                  onChange={(e) => setAgentData({ ...agentData, name: e.target.value })}
                  className="w-full p-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">{t('dashboard.aiAgent.form.description')}</label>
                <textarea
                  value={agentData.description}
                  onChange={(e) => setAgentData({ ...agentData, description: e.target.value })}
                  className="w-full p-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">{t('dashboard.aiAgent.agent.type')}</label>
                <select
                  value={agentData.agent_type}
                  onChange={(e) => setAgentData({ ...agentData, agent_type: e.target.value })}
                  className="w-full p-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="chatbot">ChatBot</option>
                  <option value="workflow">Workflow</option>
                  <option value="agent">Agent</option>
                  <option value="completion">Completion</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="p-4 bg-accent-orange/10 border border-accent-orange/20 rounded-lg">
                <p className="text-sm text-accent-orange whitespace-pre-line leading-relaxed">{error}</p>
              </div>
            )}

            <div className="flex items-center space-x-2 pt-4">
              <button
                type="submit"
                disabled={!agentData.name.trim() || isLoading}
                className="flex-1 bg-primary text-primary-foreground rounded-lg py-2 px-4 font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? t('dashboard.aiAgent.buttons.creating') : t('dashboard.aiAgent.buttons.create')}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-muted text-muted-foreground rounded-lg py-2 px-4 font-medium hover:bg-muted/80 transition-colors"
              >
                {t('common.cancel')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// ============================
// 메인 페이지 컴포넌트
// ============================

export default function AIAgentPage() {
  const { t } = useTranslation()
  const [agents, setAgents] = useState<Agent[]>([])
  const [templates, setTemplates] = useState<AgentTemplate[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [difyHealth, setDifyHealth] = useState<'healthy' | 'unhealthy' | 'checking'>('checking')

  // 모달 상태
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showChatModal, setShowChatModal] = useState(false)
  const [showApiKeyModal, setShowApiKeyModal] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)

  // 필터 상태
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterType, setFilterType] = useState<string>('all')

  // iframe 상태 추가
  const [iframeUrl, setIframeUrl] = useState<string>('http://localhost/explore/apps')
  const [showIframe, setShowIframe] = useState<boolean>(false)

  // ============================
  // API 호출 함수들
  // ============================

  const fetchHealthStatus = async () => {
    try {
      setDifyHealth('checking')
      const response = await fetch('/api/v1/dify/health')
      const data = await response.json()
      setDifyHealth(data.status === 'healthy' ? 'healthy' : 'unhealthy')
    } catch (error) {
      console.error('Dify health check failed:', error)
      setDifyHealth('unhealthy')
    }
  }

  const fetchAgents = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/dify/agents')
      const data = await response.json()

      if (data.success) {
        setAgents(data.agents)
      }
    } catch {
      setError('에이전트 목록을 불러오는데 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/dify/templates')
      const data = await response.json()

      if (data.success) {
        setTemplates(data.templates)
      }
    } catch (error) {
      console.error('템플릿 로드 실패:', error)
    }
  }

  const deleteAgent = async (agent: Agent) => {
    if (!confirm(`'${agent.name}' 에이전트를 삭제하시겠습니까?`)) return

    try {
      const response = await fetch(`/api/v1/dify/agents/${agent.id}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        await fetchAgents()
      }
    } catch (error) {
      console.error('에이전트 삭제 실패:', error)
    }
  }

  // Dify 웹 인터페이스 열기
  const openDifyInterface = () => {
    window.open('http://localhost', '_blank')
  }

  // 데이터 새로고침
  const refreshData = async () => {
    setIsLoading(true)
    await Promise.all([
      fetchAgents(),
      fetchHealthStatus(),
      fetchTemplates()
    ])
    setIsLoading(false)
  }

  // ============================
  // 초기화
  // ============================

  useEffect(() => {
    fetchHealthStatus()
    fetchAgents()
    fetchTemplates()
  }, [])

  // ============================
  // 필터 값 변환 함수들
  // ============================

  const getStatusDisplayValue = (value: string) => {
    const statusMap: { [key: string]: string } = {
      'all': t('dashboard.aiAgent.status.all'),
      'active': t('dashboard.aiAgent.status.active'),
      'inactive': t('dashboard.aiAgent.status.inactive'),
      'error': t('dashboard.aiAgent.status.error')
    }
    return statusMap[value] || t('dashboard.aiAgent.status.all')
  }

  const getStatusValue = (displayValue: string) => {
    const reverseStatusMap: { [key: string]: string } = {
      [t('dashboard.aiAgent.status.all')]: 'all',
      [t('dashboard.aiAgent.status.active')]: 'active',
      [t('dashboard.aiAgent.status.inactive')]: 'inactive',
      [t('dashboard.aiAgent.status.error')]: 'error'
    }
    return reverseStatusMap[displayValue] || 'all'
  }

  const getTypeDisplayValue = (value: string) => {
    const typeMap: { [key: string]: string } = {
      'all': t('dashboard.aiAgent.types.all'),
      'chatbot': 'ChatBot',
      'workflow': 'Workflow',
      'agent': 'Agent',
      'completion': 'Completion'
    }
    return typeMap[value] || t('dashboard.aiAgent.types.all')
  }

  const getTypeValue = (displayValue: string) => {
    const reverseTypeMap: { [key: string]: string } = {
      [t('dashboard.aiAgent.types.all')]: 'all',
      'ChatBot': 'chatbot',
      'Workflow': 'workflow',
      'Agent': 'agent',
      'Completion': 'completion'
    }
    return reverseTypeMap[displayValue] || 'all'
  }

  // ============================
  // 필터링된 에이전트
  // ============================

  const filteredAgents = agents.filter(agent => {
    if (filterStatus !== 'all' && agent.status !== filterStatus) return false
    if (filterType !== 'all' && agent.type !== filterType) return false
    return true
  })

  // ============================
  // 통계 계산
  // ============================

  const stats = {
    total: agents.length,
    active: agents.filter(a => a.status === 'active').length
  }

  // ============================
  // 탭 구성
  // ============================

  const tabs = [
    { id: 'overview', name: t('dashboard.aiAgent.tabs.overview'), icon: Activity },
    { id: 'agents', name: t('dashboard.aiAgent.tabs.agents'), icon: Bot },
    { id: 'templates', name: t('dashboard.aiAgent.tabs.templates'), icon: FileText }
  ]

  const [activeTab, setActiveTab] = useState('overview')

  // ============================
  // 렌더링
  // ============================

  return (
    <div className="p-6 space-y-6 bg-background min-h-screen">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center">
            <Bot className="w-8 h-8 mr-3 text-accent-cyan" />
            {t('nav.aiAgent') || t('dashboard.aiAgent.aiAgent.title')}
          </h1>
          <p className="text-muted-foreground text-lg">{t('dashboard.aiAgent.subtitle')}</p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Dify 상태 표시 */}
          <div className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-card backdrop-blur-sm border border-border">
            <div className={`w-3 h-3 rounded-full ${difyHealth === 'healthy' ? 'bg-green-500' :
                difyHealth === 'unhealthy' ? 'bg-red-500' : 'bg-yellow-500'
              }`} />
            <span className="text-sm text-foreground">
              Dify {difyHealth === 'healthy' ? t('dashboard.aiAgent.status.healthy') : difyHealth === 'unhealthy' ? t('dashboard.aiAgent.status.unhealthy') : t('dashboard.aiAgent.status.checking')}
            </span>
          </div>

          {/* Dify 인터페이스 열기 */}
          <button
            onClick={openDifyInterface}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
          >
            <ExternalLink className="w-5 h-5" />
            <span>{t('dashboard.aiAgent.buttons.openDify') || 'Dify 열기'}</span>
          </button>

          {/* 새로고침 */}
          <button
            onClick={refreshData}
            disabled={isLoading}
            className="p-3 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-300 disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 상태 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title={t('dashboard.aiAgent.statusCards.totalAgents')}
          value={stats.total}
          icon={<Bot className="w-6 h-6 text-white" />}
          color="#3b82f6"
        />
        <StatusCard
          title={t('dashboard.aiAgent.statusCards.activeAgents')}
          value={stats.active}
          icon={<Activity className="w-6 h-6 text-white" />}
          color="#22c55e"
        />
        <StatusCard
          title={t('dashboard.aiAgent.statusCards.totalTemplates')}
          value={templates.length}
          icon={<Copy className="w-6 h-6 text-white" />}
          color="#f97316"
        />
        <StatusCard
          title={t('dashboard.aiAgent.statusCards.difyStatus')}
          value={difyHealth === 'healthy' ? t('dashboard.aiAgent.status.healthy') : difyHealth === 'unhealthy' ? t('dashboard.aiAgent.status.unhealthy') : t('dashboard.aiAgent.status.checking')}
          icon={<Server className="w-6 h-6 text-white" />}
          color={difyHealth === 'healthy' ? '#22c55e' : difyHealth === 'unhealthy' ? '#ef4444' : '#f97316'}
        />
      </div>

      {/* 탭 네비게이션 */}
      <TabNavigation
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(tabId) => setActiveTab(String(tabId))}
      />

      {/* 탭 컨텐츠 */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">{t('dashboard.aiAgent.tabs.overview')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-foreground mb-2">{t('dashboard.aiAgent.overview.typeDistribution') || '에이전트 유형별 분포'}</h4>
                <div className="space-y-2">
                  {['chatbot', 'workflow', 'agent', 'completion'].map(type => {
                    const count = agents.filter(a => a.type === type).length
                    return (
                      <div key={type} className="flex items-center justify-between">
                        <span className="text-muted-foreground capitalize">{type}</span>
                        <span className="font-medium text-foreground">{count}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div>
                <h4 className="font-medium text-foreground mb-2">{t('dashboard.aiAgent.overview.recentActivity') || '최근 활동'}</h4>
                <div className="space-y-2">
                  {agents
                    .filter(a => a.last_used)
                    .sort((a, b) => new Date(b.last_used!).getTime() - new Date(a.last_used!).getTime())
                    .slice(0, 3)
                    .map(agent => (
                      <div key={agent.id} className="flex items-center justify-between">
                        <span className="text-muted-foreground">{agent.name}</span>
                        <span className="text-sm text-muted-foreground">
                          {new Date(agent.last_used!).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'agents' && (
        <div className="space-y-6">
          {/* 필터 및 액션 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="min-w-[140px]">
                <Select
                  value={getStatusDisplayValue(filterStatus)}
                  onChange={(value) => setFilterStatus(getStatusValue(value))}
                  options={[t('dashboard.aiAgent.status.all'), t('dashboard.aiAgent.status.active'), t('dashboard.aiAgent.status.inactive'), t('dashboard.aiAgent.status.error')]}
                  label={t('dashboard.aiAgent.filter.status')}
                  placeholder={t('dashboard.aiAgent.filter.status')}
                />
              </div>
              <div className="min-w-[140px]">
                <Select
                  value={getTypeDisplayValue(filterType)}
                  onChange={(value) => setFilterType(getTypeValue(value))}
                  options={[t('dashboard.aiAgent.types.all'), 'ChatBot', 'Workflow', 'Agent', 'Completion']}
                  label={t('dashboard.aiAgent.filter.type')}
                  placeholder={t('dashboard.aiAgent.filter.type')}
                />
              </div>
              <button
                onClick={fetchAgents}
                className="flex items-center space-x-2 px-3 py-2 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>{t('dashboard.aiAgent.buttons.refresh')}</span>
              </button>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm"
            >
              <Plus className="w-5 h-5" />
              <span>{t('dashboard.aiAgent.buttons.create')}</span>
            </button>
          </div>

          {/* 에이전트 목록 */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <RefreshCw className="w-8 h-8 mx-auto mb-4 text-muted-foreground animate-spin" />
                <p className="text-muted-foreground">{t('dashboard.aiAgent.messages.loadingAgents') || '에이전트를 불러오는 중...'}</p>
              </div>
            </div>
          ) : error ? (
            <div className="bg-accent-orange/10 border border-accent-orange/20 rounded-lg p-6 text-center">
              <AlertCircle className="w-8 h-8 mx-auto mb-4 text-accent-orange" />
              <p className="text-accent-orange">{error}</p>
              <button
                onClick={fetchAgents}
                className="mt-4 px-4 py-2 bg-accent-orange text-white rounded-lg hover:bg-accent-orange/90 transition-colors"
              >
                {t('dashboard.aiAgent.buttons.retry') || '다시 시도'}
              </button>
            </div>
          ) : filteredAgents.length === 0 ? (
            <div className="bg-card border border-border rounded-lg p-12 text-center">
              <Bot className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium text-foreground mb-2">{t('dashboard.aiAgent.emptyState.noAgents')}</h3>
              <p className="text-muted-foreground mb-6">{t('dashboard.aiAgent.emptyState.createFirst')}</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-primary text-primary-foreground px-6 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors"
              >
                {t('dashboard.aiAgent.emptyState.createFirst')}
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredAgents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onEdit={(agent) => {
                      setSelectedAgent(agent)
                      // 편집 모달 구현 가능
                    }}
                    onDelete={deleteAgent}
                    onChat={(agent) => {
                      setSelectedAgent(agent)
                      setShowChatModal(true)
                    }}
                    onSetApiKey={(agent) => {
                      setSelectedAgent(agent)
                      setShowApiKeyModal(true)
                    }}
                  />
                ))}
              </div>

              {/* iframe 섹션 */}
              <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                      <ExternalLink className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-foreground">Dify</h3>
                      <p className="text-sm text-muted-foreground">{t('dashboard.aiAgent.iframe.description')}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setShowIframe(!showIframe)
                    }}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      showIframe
                        ? 'bg-accent-orange text-white hover:bg-accent-orange/90'
                        : 'bg-primary text-primary-foreground hover:bg-primary/90'
                    }`}
                  >
                    {showIframe ? t('dashboard.aiAgent.iframe.button.close') : t('dashboard.aiAgent.iframe.button.open')}
                  </button>
                </div>

                {showIframe && iframeUrl && (
                  <div className="space-y-4">
                      <div className="border border-border rounded-lg overflow-hidden bg-background">
                        <iframe
                          src={iframeUrl}
                          title="Embedded Website"
                          className="w-full h-[800px] border-0"
                          sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
                          loading="lazy"
                        />
                      </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">{t('dashboard.aiAgent.tabs.templates')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="border border-border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start space-x-3 mb-4">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                      <Bot className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-foreground">{template.name}</h4>
                      <p className="text-sm text-muted-foreground mt-1">{template.description}</p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="px-2 py-1 bg-muted rounded text-xs text-muted-foreground">
                          {template.category}
                        </span>
                        <span className="px-2 py-1 bg-primary/10 text-primary rounded text-xs">
                          {template.agent_type}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col space-y-2">
                    <button
                      onClick={async () => {
                        try {
                          setIsLoading(true)
                          const result = await autoCreateAgent(template.id, template.name)
                          if (result.success) {
                            await fetchAgents()
                            alert(`🎉 ${result.message}`)
                          }
                        } catch (error: any) {
                          alert(`❌ ${error.message}`)
                        } finally {
                          setIsLoading(false)
                        }
                      }}
                      disabled={isLoading}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-lg transition-all duration-300 shadow-sm disabled:opacity-50"
                    >
                      <Zap className="w-4 h-4" />
                      <span>{isLoading ? t('dashboard.aiAgent.buttons.generating') : t('dashboard.aiAgent.messages.instantCreateAgent')}</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowCreateModal(true)
                      }}
                      className="w-full flex items-center justify-center space-x-2 px-4 py-3 border border-border text-foreground hover:bg-muted/50 rounded-lg transition-all duration-300"
                    >
                      <Plus className="w-4 h-4" />
                      <span>{t('dashboard.aiAgent.buttons.manualCreate') || '수동 설정으로 생성'}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 모달들 */}
      <CreateAgentModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          fetchAgents()
          setShowCreateModal(false)
        }}
        templates={templates}
        t={t}
      />

      <ChatModal
        agent={selectedAgent}
        isOpen={showChatModal}
        onClose={() => {
          setShowChatModal(false)
          setSelectedAgent(null)
        }}
        t={t}
      />

      <ApiKeyModal
        agent={selectedAgent}
        isOpen={showApiKeyModal}
        onClose={() => {
          setShowApiKeyModal(false)
          setSelectedAgent(null)
        }}
        onSuccess={() => {
          fetchAgents()
          setShowApiKeyModal(false)
          setSelectedAgent(null)
        }}
        t={t}
      />
    </div>
  )
}