'use client'

import { useState, useEffect, useRef } from 'react'
import { Brain, MessageSquare, FileText, TrendingUp, Settings, Send, Download, Search, AlertCircle, Upload, Trash2, File, Database } from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { aiAdvisorService, Message, QueryRequest, ReportGenerationRequest } from '@/services/aiadvisor'
import DocumentManager from '@/components/aiadvisor/DocumentManager'

export default function AIAdvisorPage() {
  const { t } = useTranslation()
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '안녕하세요! AI Advisor입니다. 제조업 최적화에 대해 어떤 도움이 필요하신가요?\n\n문서를 업로드하시면 해당 내용을 바탕으로 더 정확한 답변을 드릴 수 있습니다.',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState<any>(null)
  const [reportTypes, setReportTypes] = useState<any[]>([])
  const [agents, setAgents] = useState<any[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'settings'>('chat')
  // AI 모드는 Ollama로 고정
  const currentAIMode = 'ollama'
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    initializeSystem()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const initializeSystem = async () => {
    try {
      console.log('Initializing AI Advisor system...')
      
      // 시스템 상태 확인
      const status = await aiAdvisorService.getSystemStatus()
      console.log('System status:', status)
      setSystemStatus(status)

      // 리포트 타입 가져오기
      const types = await aiAdvisorService.getReportTypes()
      console.log('Report types:', types)
      setReportTypes(types)

      // 에이전트 목록 가져오기
      const agentList = await aiAdvisorService.listAgents()
      console.log('Available agents:', agentList)
      setAgents(agentList)
      if (agentList.length > 0) {
        setSelectedAgent(agentList[0].id)
      }


      
      console.log('System initialization completed successfully')
    } catch (error) {
      console.error('System initialization failed:', error)
      // 백엔드 연결 실패 시 기본 메시지 추가
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `백엔드 서버에 연결할 수 없습니다. 오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}. 서버가 실행 중인지 확인해주세요.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = inputMessage
    setInputMessage('')
    setIsLoading(true)

    // 스트리밍 응답을 위한 초기 메시지 생성
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      type: 'assistant',
      content: '',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, assistantMessage])

    try {
      // 하이브리드 모드 스트리밍 응답 받기
      const response = await fetch('/api/v1/aiadvisor/hybrid/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: currentInput,
          agent_id: selectedAgent || 'default',
          use_dify: currentAIMode === 'dify',
          conversation_id: undefined
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to get streaming response')
      }

      // 스트리밍 응답 처리 (최적화된 버전)
      if (response.body) {
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let accumulatedContent = ''
        let buffer = ''
        let updateScheduled = false

        // 렌더링 최적화를 위한 debounce 함수
        const scheduleUpdate = () => {
          if (!updateScheduled) {
            updateScheduled = true
            requestAnimationFrame(() => {
              setMessages(prev => prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: accumulatedContent }
                  : msg
              ))
              updateScheduled = false
            })
          }
        }

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          buffer += chunk

          // SSE 형식 파싱 (data: 접두사 제거)
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 마지막 불완전한 라인은 버퍼에 유지

          let hasNewContent = false

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6) // 'data: ' 제거
              if (data.trim() && data !== '[DONE]') {
                try {
                  // JSON 파싱 시도
                  const parsed = JSON.parse(data)
                  if (parsed.done) {
                    // 스트리밍 완료
                    break
                  } else if (parsed.chunk) {
                    // 백엔드에서 보내는 chunk 형태
                    accumulatedContent += parsed.chunk
                    hasNewContent = true
                  } else if (typeof parsed === 'string') {
                    accumulatedContent += parsed
                    hasNewContent = true
                  } else if (parsed.content) {
                    accumulatedContent += parsed.content
                    hasNewContent = true
                  }
                } catch {
                  // JSON이 아닌 경우 그대로 사용
                  accumulatedContent += data
                  hasNewContent = true
                }
              }
            }
          }

          // 새 컨텐츠가 있을 때만 업데이트 스케줄링
          if (hasNewContent) {
            scheduleUpdate()
          }
        }

        // 최종 업데이트 보장
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: accumulatedContent }
            : msg
        ))
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: assistantMessageId,
        type: 'assistant',
        content: `오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
        timestamp: new Date()
      }
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId ? errorMessage : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleQuickAction = async (action: string) => {
    const actions = {
      performance: '제조 공정의 성능을 분석하고 개선 방안을 제시해주세요.',
      quality: '품질 관리 시스템을 개선하고 품질 향상 방안을 제시해주세요.',
      cost: '생산 비용을 절감할 수 있는 전략과 방안을 제시해주세요.',
      report: '현재 상황에 대한 종합 분석 리포트를 생성해주세요.'
    }

    const query = actions[action as keyof typeof actions] || action
    setInputMessage(query)
  }





  const generateReport = async () => {
    try {
      const request: ReportGenerationRequest = {
        topic: '제조업 최적화 종합 분석',
        report_type: 'analysis',
        sections: ['executive_summary', 'situation_analysis', 'recommendations']
      }

      const result = await aiAdvisorService.generateReport(request)
      
      if (result.generation_status === 'success') {
        // 리포트 다운로드
        await aiAdvisorService.downloadReport(result.report_filename)
        
        const successMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: `리포트가 성공적으로 생성되었습니다. 파일명: ${result.report_filename}`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])
      }
    } catch (error) {
      console.error('Report generation error:', error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `리포트 생성 중 오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-border bg-card">
        <div className="flex items-center space-x-4">
          <div className="p-2 rounded-lg bg-gradient-primary">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">AI Advisor</h1>
            <p className="text-muted-foreground">제조업 최적화 전문 AI 어드바이저</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {systemStatus && (
            <div className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-muted">
              <div className={`w-2 h-2 rounded-full ${
                systemStatus.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="text-sm text-muted-foreground">
                {systemStatus.status === 'healthy' ? '시스템 정상' : '시스템 오류'}
              </span>
            </div>
          )}
          <button className="p-2 rounded-lg bg-muted hover:bg-muted/80 transition-colors">
            <Settings className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Tab Navigation */}
          <div className="flex border-b border-border bg-card">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'chat'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-4 h-4" />
                <span>채팅</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'documents'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="flex items-center space-x-2">
                <File className="w-4 h-4" />
                <span>문서 관리</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'settings'
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Settings className="w-4 h-4" />
                <span>AI 모드</span>
              </div>
            </button>
          </div>

          {activeTab === 'chat' ? (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] p-4 rounded-lg ${
                        message.type === 'user'
                          ? 'bg-gradient-primary text-white'
                          : 'bg-card border border-border'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      
                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border/20">
                          <p className="text-xs text-muted-foreground mb-2">참고 문서:</p>
                          <div className="space-y-1">
                            {message.sources.slice(0, 3).map((source: any, index: number) => (
                              <div key={`${message.id}-source-${index}`} className="text-xs bg-muted/50 px-2 py-1 rounded">
                                {source.metadata?.filename || `문서 ${index + 1}`}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <p className={`text-xs mt-2 ${
                        message.type === 'user' ? 'text-white/70' : 'text-muted-foreground'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-card border border-border p-4 rounded-lg">
                      <div className="flex space-x-2">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-6 border-t border-border bg-card">
                <div className="flex space-x-3">
                  <div className="flex-1 relative">
                    <textarea
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="제조업 최적화에 대해 질문하세요..."
                      className="w-full p-3 pr-12 border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary bg-background text-foreground"
                      rows={1}
                      disabled={isLoading}
                    />
                  </div>
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    className="px-4 py-3 bg-gradient-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          ) : activeTab === 'documents' ? (
            /* Documents Tab */
            <div className="flex-1 p-6">
              <DocumentManager onDocumentChange={() => {
                // 문서 변경 시 채팅 메시지에 알림 추가
                const notificationMessage: Message = {
                  id: Date.now().toString(),
                  type: 'assistant',
                  content: '문서가 업데이트되었습니다. 이제 업데이트된 문서 내용을 바탕으로 답변을 드릴 수 있습니다.',
                  timestamp: new Date()
                }
                setMessages(prev => [...prev, notificationMessage])
              }} />
            </div>
          ) : (
            /* Settings Tab - System Configuration */
            <div className="flex-1 p-6">
              <div className="max-w-4xl mx-auto space-y-6">
                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-foreground mb-2">시스템 설정</h2>
                  <p className="text-muted-foreground">
                    AI Advisor 시스템의 설정을 확인하고 관리할 수 있습니다.
                  </p>
                </div>
                
                {/* AI 모드 정보 (고정) */}
                <div className="bg-card border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-foreground mb-4">AI 모드</h3>
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <div>
                      <p className="text-sm font-medium text-foreground">Ollama 로컬 모드</p>
                      <p className="text-xs text-muted-foreground">빠른 로컬 AI 처리로 응답을 생성합니다</p>
                    </div>
                  </div>
                </div>

                {/* 시스템 정보 */}
                {systemStatus && (
                  <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-4">시스템 상태</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">상태</span>
                        <span className={`text-sm font-medium ${
                          systemStatus.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {systemStatus.status === 'healthy' ? '정상' : '오류'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">마지막 확인</span>
                        <span className="text-sm text-foreground">
                          {new Date(systemStatus.timestamp).toLocaleString('ko-KR')}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="w-80 border-l border-border bg-card p-6">
          <div className="space-y-6">
            {/* System Status */}
            {systemStatus && (
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-3">시스템 상태</h3>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      systemStatus.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm text-foreground">
                      {systemStatus.status === 'healthy' ? '정상' : '오류'}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    업데이트: {new Date(systemStatus.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            )}

            {/* Agent Selection */}
            {agents.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-3">AI 에이전트</h3>
                <select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="w-full p-2 border border-border rounded-lg bg-background text-foreground text-sm"
                >
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name || agent.id}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Quick Actions */}
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-3">빠른 액션</h3>
              <div className="space-y-2">
                <button 
                  onClick={() => handleQuickAction('performance')}
                  className="w-full p-3 text-left bg-muted hover:bg-muted/80 rounded-lg transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">성능 분석 요청</span>
                  </div>
                </button>
                <button 
                  onClick={() => handleQuickAction('quality')}
                  className="w-full p-3 text-left bg-muted hover:bg-muted/80 rounded-lg transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <Search className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">품질 관리 개선</span>
                  </div>
                </button>
                <button 
                  onClick={() => handleQuickAction('cost')}
                  className="w-full p-3 text-left bg-muted hover:bg-muted/80 rounded-lg transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">비용 절감 전략</span>
                  </div>
                </button>
                <button 
                  onClick={() => handleQuickAction('report')}
                  className="w-full p-3 text-left bg-muted hover:bg-muted/80 rounded-lg transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">리포트 생성</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Report Types */}
            {reportTypes.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-3">리포트 타입</h3>
                <div className="space-y-2">
                  {reportTypes.map((type) => (
                    <div key={type.type} className="p-2 bg-muted/50 rounded-lg">
                      <p className="text-sm font-medium text-foreground">{type.name}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Statistics */}
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-3">통계</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">총 대화</span>
                  <span className="text-sm font-medium text-foreground">{messages.length}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">사용 가능한 에이전트</span>
                  <span className="text-sm font-medium text-foreground">{agents.length}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">리포트 타입</span>
                  <span className="text-sm font-medium text-foreground">{reportTypes.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 