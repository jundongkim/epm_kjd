"use client"

import { useState, useEffect } from 'react'
import { Check, Zap, Brain, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface AnalysisModeStatus {
  mode: 'standard' | 'advanced' | 'expert'
  model_name: string
  streaming: boolean
  analysis_config: {
    search_k: number
    context_limit: number
    depth: string
  }
}

interface SystemStatus {
  ollama: {
    available: boolean
    error?: string
  }
  analysis_ready: boolean
}

interface AnalysisModeSelectorProps {
  onModeChange?: (mode: 'standard' | 'advanced' | 'expert') => void
  currentMode?: 'standard' | 'advanced' | 'expert'
}

export default function AnalysisModeSelector({ onModeChange, currentMode = 'standard' }: AnalysisModeSelectorProps) {
  const [selectedMode, setSelectedMode] = useState<'standard' | 'advanced' | 'expert'>(currentMode)
  const [isLoading, setIsLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)

  const checkSystemStatus = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/aiadvisor/status')
      if (response.ok) {
        const status = await response.json()
        setSystemStatus(status)
      }
    } catch (error) {
      console.error('시스템 상태 확인 실패:', error)
      setSystemStatus({
        ollama: { available: false, error: '연결 실패' },
        analysis_ready: false
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleModeSwitch = async (mode: 'standard' | 'advanced' | 'expert') => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/aiadvisor/mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode }),
      })

      if (response.ok) {
        setSelectedMode(mode)
        onModeChange?.(mode)
      } else {
        console.error('모드 전환 실패')
      }
    } catch (error) {
      console.error('모드 전환 오류:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getModeIcon = (mode: 'standard' | 'advanced' | 'expert') => {
    switch (mode) {
      case 'standard':
        return <Zap className="w-5 h-5" />
      case 'advanced':
        return <Brain className="w-5 h-5" />
      case 'expert':
        return <Settings className="w-5 h-5" />
      default:
        return <Zap className="w-5 h-5" />
    }
  }

  const getModeColor = (mode: 'standard' | 'advanced' | 'expert') => {
    const isSelected = selectedMode === mode
    const isAvailable = systemStatus?.ollama.available

    if (!isAvailable) {
      return 'border-gray-300 bg-gray-50 text-gray-400'
    }

    switch (mode) {
      case 'standard':
        return isSelected 
          ? 'border-blue-500 bg-blue-50 text-blue-700' 
          : 'border-gray-300 bg-white hover:border-blue-300 hover:bg-blue-50'
      case 'advanced':
        return isSelected 
          ? 'border-purple-500 bg-purple-50 text-purple-700' 
          : 'border-gray-300 bg-white hover:border-purple-300 hover:bg-purple-50'
      case 'expert':
        return isSelected 
          ? 'border-orange-500 bg-orange-50 text-orange-700' 
          : 'border-gray-300 bg-white hover:border-orange-300 hover:bg-orange-50'
      default:
        return 'border-gray-300 bg-white'
    }
  }

  const isAvailable = (mode: 'standard' | 'advanced' | 'expert') => {
    return systemStatus?.ollama.available ?? false
  }

  const getModeDescription = (mode: 'standard' | 'advanced' | 'expert') => {
    switch (mode) {
      case 'standard':
        return '기본 분석 모드'
      case 'advanced':
        return '고급 분석 모드'
      case 'expert':
        return '전문가 분석 모드'
      default:
        return ''
    }
  }

  const getModeFeatures = (mode: 'standard' | 'advanced' | 'expert') => {
    switch (mode) {
      case 'standard':
        return [
          '✓ 기본 문서 검색 (5개)',
          '✓ 핵심 컨텍스트 (3개)',
          '✓ 기본 분석 깊이'
        ]
      case 'advanced':
        return [
          '✓ 확장 문서 검색 (10개)',
          '✓ 상세 컨텍스트 (5개)',
          '✓ 심화 분석 깊이'
        ]
      case 'expert':
        return [
          '✓ 종합 문서 검색 (15개)',
          '✓ 전체 컨텍스트 (8개)',
          '✓ 전문가 분석 깊이'
        ]
      default:
        return []
    }
  }

  useEffect(() => {
    checkSystemStatus()
  }, [])

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-foreground">제조업 특화 분석 모드</h3>
        <p className="text-sm text-muted-foreground mt-1">
          질문의 복잡도와 요구사항에 맞는 분석 모드를 선택하세요
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Standard 모드 */}
        <button
          onClick={() => handleModeSwitch('standard')}
          disabled={isLoading || !isAvailable('standard')}
          className={`
            relative p-4 border-2 rounded-lg transition-all duration-200 text-left
            ${getModeColor('standard')}
            ${!isAvailable('standard') ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${isLoading ? 'cursor-wait' : ''}
          `}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {getModeIcon('standard')}
              <div>
                <h4 className="font-medium">Standard</h4>
                <p className="text-sm opacity-80 mt-1">{getModeDescription('standard')}</p>
              </div>
            </div>
            {selectedMode === 'standard' && (
              <Check className="w-5 h-5 text-green-500" />
            )}
          </div>
          
          {/* 상태 표시 */}
          <div className="mt-3 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isAvailable('standard') ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs opacity-75">
              {isAvailable('standard') ? '사용 가능' : '연결 실패'}
            </span>
          </div>
          
          {/* 기능 */}
          <div className="mt-3 space-y-1">
            {getModeFeatures('standard').map((feature, index) => (
              <div key={index} className="text-xs opacity-75">{feature}</div>
            ))}
          </div>
        </button>

        {/* Advanced 모드 */}
        <button
          onClick={() => handleModeSwitch('advanced')}
          disabled={isLoading || !isAvailable('advanced')}
          className={`
            relative p-4 border-2 rounded-lg transition-all duration-200 text-left
            ${getModeColor('advanced')}
            ${!isAvailable('advanced') ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${isLoading ? 'cursor-wait' : ''}
          `}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {getModeIcon('advanced')}
              <div>
                <h4 className="font-medium">Advanced</h4>
                <p className="text-sm opacity-80 mt-1">{getModeDescription('advanced')}</p>
              </div>
            </div>
            {selectedMode === 'advanced' && (
              <Check className="w-5 h-5 text-green-500" />
            )}
          </div>
          
          {/* 상태 표시 */}
          <div className="mt-3 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isAvailable('advanced') ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs opacity-75">
              {isAvailable('advanced') ? '사용 가능' : '연결 실패'}
            </span>
          </div>
          
          {/* 기능 */}
          <div className="mt-3 space-y-1">
            {getModeFeatures('advanced').map((feature, index) => (
              <div key={index} className="text-xs opacity-75">{feature}</div>
            ))}
          </div>
        </button>

        {/* Expert 모드 */}
        <button
          onClick={() => handleModeSwitch('expert')}
          disabled={isLoading || !isAvailable('expert')}
          className={`
            relative p-4 border-2 rounded-lg transition-all duration-200 text-left
            ${getModeColor('expert')}
            ${!isAvailable('expert') ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${isLoading ? 'cursor-wait' : ''}
          `}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {getModeIcon('expert')}
              <div>
                <h4 className="font-medium">Expert</h4>
                <p className="text-sm opacity-80 mt-1">{getModeDescription('expert')}</p>
              </div>
            </div>
            {selectedMode === 'expert' && (
              <Check className="w-5 h-5 text-green-500" />
            )}
          </div>
          
          {/* 상태 표시 */}
          <div className="mt-3 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isAvailable('expert') ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs opacity-75">
              {isAvailable('expert') ? '사용 가능' : '연결 실패'}
            </span>
          </div>
          
          {/* 기능 */}
          <div className="mt-3 space-y-1">
            {getModeFeatures('expert').map((feature, index) => (
              <div key={index} className="text-xs opacity-75">{feature}</div>
            ))}
          </div>
        </button>
      </div>

      {/* 현재 상태 정보 */}
      {systemStatus && (
        <div className="bg-muted/30 rounded-lg p-4">
          <h4 className="text-sm font-medium text-foreground mb-3">시스템 상태</h4>
          <div className="grid grid-cols-1 gap-4 text-sm">
            
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
          </div>

          {/* 오류 세부 정보 */}
          {systemStatus.ollama.error && (
            <div className="mt-4 space-y-2">
              <div className="text-xs text-red-600">
                <span className="font-medium">Ollama 오류:</span> {systemStatus.ollama.error}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 새로고침 버튼 */}
      <div className="mt-4 flex justify-end">
        <Button
          onClick={checkSystemStatus}
          disabled={isLoading}
          variant="outline"
          size="sm"
        >
          {isLoading ? '확인 중...' : '상태 새로고침'}
        </Button>
      </div>
    </div>
  )
}