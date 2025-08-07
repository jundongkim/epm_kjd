'use client'

import { useState, useEffect } from 'react'
import { Settings, Zap, Bot, Workflow, Check, AlertCircle, Loader } from 'lucide-react'

interface ModeStatus {
  mode: 'ollama' | 'dify'
  model_name: string
  streaming: boolean
  dify_available: boolean
  ollama_available: boolean
}

interface SystemStatus {
  dify: {
    available: boolean
    error?: string
  }
  ollama: {
    available: boolean
    error?: string
  }
  hybrid_ready: boolean
}

interface HybridModeSelectorProps {
  onModeChange?: (mode: 'ollama' | 'dify') => void
  currentMode?: 'ollama' | 'dify'
}

export default function HybridModeSelector({ onModeChange, currentMode = 'ollama' }: HybridModeSelectorProps) {
  const [selectedMode, setSelectedMode] = useState<'ollama' | 'dify'>(currentMode)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkSystemStatus()
  }, [])

  const checkSystemStatus = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/v1/aiadvisor/hybrid/status')
      
      if (response.ok) {
        const data = await response.json()
        setSystemStatus(data)
      } else {
        setError('시스템 상태를 확인할 수 없습니다.')
      }
    } catch (err) {
      setError('시스템 상태 확인 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleModeSwitch = async (mode: 'ollama' | 'dify') => {
    if (mode === selectedMode) return

    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch('/api/v1/aiadvisor/hybrid/switch-mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: 'default',
          use_dify: mode === 'dify'
        })
      })

      if (response.ok) {
        const result = await response.json()
        setSelectedMode(mode)
        onModeChange?.(mode)
        
        // 상태 업데이트
        await checkSystemStatus()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || '모드 전환에 실패했습니다.')
      }
    } catch (err) {
      setError('모드 전환 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const getModeIcon = (mode: 'ollama' | 'dify') => {
    if (mode === 'dify') {
      return <Bot className="w-5 h-5" />
    }
    return <Zap className="w-5 h-5" />
  }

  const getModeColor = (mode: 'ollama' | 'dify') => {
    if (mode === 'dify') {
      return selectedMode === mode 
        ? 'bg-purple-500 border-purple-500 text-white' 
        : 'bg-white border-purple-200 text-purple-700 hover:border-purple-300'
    }
    return selectedMode === mode 
      ? 'bg-blue-500 border-blue-500 text-white' 
      : 'bg-white border-blue-200 text-blue-700 hover:border-blue-300'
  }

  const isAvailable = (mode: 'ollama' | 'dify') => {
    if (!systemStatus) return false
    return mode === 'dify' ? systemStatus.dify.available : systemStatus.ollama.available
  }

  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-5 h-5 text-muted-foreground" />
        <h3 className="text-lg font-semibold text-foreground">AI 모드 선택</h3>
        {isLoading && <Loader className="w-4 h-4 animate-spin text-muted-foreground" />}
      </div>

      {/* 오류 메시지 */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* 모드 선택 버튼들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        
        {/* Ollama 모드 */}
        <button
          onClick={() => handleModeSwitch('ollama')}
          disabled={isLoading || !isAvailable('ollama')}
          className={`
            relative p-4 border-2 rounded-lg transition-all duration-200 text-left
            ${getModeColor('ollama')}
            ${!isAvailable('ollama') ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${isLoading ? 'cursor-wait' : ''}
          `}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {getModeIcon('ollama')}
              <div>
                <h4 className="font-medium">Ollama 모드</h4>
                <p className="text-sm opacity-80 mt-1">로컬 LLM 직접 사용</p>
              </div>
            </div>
            {selectedMode === 'ollama' && (
              <Check className="w-5 h-5 text-green-500" />
            )}
          </div>
          
          {/* 상태 표시 */}
          <div className="mt-3 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isAvailable('ollama') ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs opacity-75">
              {isAvailable('ollama') ? '사용 가능' : '연결 실패'}
            </span>
          </div>
          
          {/* 장점 */}
          <div className="mt-3 space-y-1">
            <div className="text-xs opacity-75">✓ 빠른 응답 속도</div>
            <div className="text-xs opacity-75">✓ 오프라인 사용 가능</div>
            <div className="text-xs opacity-75">✓ 데이터 보안</div>
          </div>
        </button>

        {/* Dify 모드 */}
        <button
          onClick={() => handleModeSwitch('dify')}
          disabled={isLoading || !isAvailable('dify')}
          className={`
            relative p-4 border-2 rounded-lg transition-all duration-200 text-left
            ${getModeColor('dify')}
            ${!isAvailable('dify') ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${isLoading ? 'cursor-wait' : ''}
          `}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {getModeIcon('dify')}
              <div>
                <h4 className="font-medium">Dify 하이브리드</h4>
                <p className="text-sm opacity-80 mt-1">고급 AI 플랫폼 연동</p>
              </div>
            </div>
            {selectedMode === 'dify' && (
              <Check className="w-5 h-5 text-green-500" />
            )}
          </div>
          
          {/* 상태 표시 */}
          <div className="mt-3 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isAvailable('dify') ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs opacity-75">
              {isAvailable('dify') ? '사용 가능' : '연결 실패'}
            </span>
          </div>
          
          {/* 장점 */}
          <div className="mt-3 space-y-1">
            <div className="text-xs opacity-75">✓ 멀티 모델 지원</div>
            <div className="text-xs opacity-75">✓ 고급 추론 능력</div>
            <div className="text-xs opacity-75">✓ GUI 프롬프트 편집</div>
          </div>
        </button>
      </div>

      {/* 현재 상태 정보 */}
      {systemStatus && (
        <div className="bg-muted/30 rounded-lg p-4">
          <h4 className="text-sm font-medium text-foreground mb-3">시스템 상태</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            
            {/* Ollama 상태 */}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Ollama:</span>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${systemStatus.ollama.available ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className={systemStatus.ollama.available ? 'text-green-600' : 'text-red-600'}>
                  {systemStatus.ollama.available ? '연결됨' : '연결 실패'}
                </span>
              </div>
            </div>

            {/* Dify 상태 */}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Dify:</span>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${systemStatus.dify.available ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className={systemStatus.dify.available ? 'text-green-600' : 'text-red-600'}>
                  {systemStatus.dify.available ? '연결됨' : '연결 실패'}
                </span>
              </div>
            </div>
          </div>

          {/* 오류 세부 정보 */}
          {(systemStatus.dify.error || systemStatus.ollama.error) && (
            <div className="mt-4 space-y-2">
              {systemStatus.ollama.error && (
                <div className="text-xs text-red-600">
                  <span className="font-medium">Ollama 오류:</span> {systemStatus.ollama.error}
                </div>
              )}
              {systemStatus.dify.error && (
                <div className="text-xs text-red-600">
                  <span className="font-medium">Dify 오류:</span> {systemStatus.dify.error}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 새로고침 버튼 */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={checkSystemStatus}
          disabled={isLoading}
          className="px-3 py-1 text-sm text-muted-foreground hover:text-foreground transition-colors disabled:cursor-wait"
        >
          {isLoading ? '확인 중...' : '상태 새로고침'}
        </button>
      </div>
    </div>
  )
}