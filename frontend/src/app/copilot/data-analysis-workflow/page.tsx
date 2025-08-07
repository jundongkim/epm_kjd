'use client'

import { useState, useEffect } from 'react'
import { 
  Brain, Target, Database, Wrench, BarChart3, TestTube, 
  Settings, Download, Play, AlertCircle, CheckCircle,
  Calendar, Clock, Sliders, TrendingUp, Zap, Beaker,
  ChevronDown, ChevronUp, X, Info, RefreshCw, Activity,
  Upload, FileText, BarChart, LineChart, PieChart,
  Filter, Search, Eye, ArrowRight, Lightbulb, Bell,
  Factory, FlaskConical, DollarSign
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { Slider, RangeSlider, Select, MultiSelect, NumberInput, Checkbox, TabNavigation } from '@/components/ui'
import MarkdownRenderer from '@/components/MarkdownRenderer'

// ============================
// API 호출 함수들
// ============================

// 데이터 분석 워크플로우 API 호출
const runAnalysisStepAPI = async (step: string, config: unknown) => {
  try {
    const response = await fetch(`/api/analysis/workflow/${step}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config)
    })
    
    if (!response.ok) {
      console.error(`분석 단계 실행 실패: ${response.status} ${response.statusText}`)
      throw new Error(`분석 실행 실패: ${response.status} ${response.statusText}`)
    }
    
    const data = await response.json()
    console.log('분석 단계 실행 결과:', data)
    return data
  } catch (error) {
    console.error('분석 단계 실행 오류:', error)
    throw error
  }
}

// 데이터 파일 목록 조회 API
const getAvailableDataAPI = async () => {
  try {
    const response = await fetch('/api/analysis/data/available', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      console.error(`API 응답 오류: ${response.status} ${response.statusText}`)
      throw new Error(`데이터 목록 조회 실패: ${response.status} ${response.statusText}`)
    }
    
    const data = await response.json()
    console.log('API 응답 데이터:', data)
    return data
  } catch (error) {
    console.error('API 호출 오류:', error)
    throw error
  }
}

// 엔진 설정 조회/저장 API
const getEngineConfigAPI = async (engineType: string) => {
  try {
    const response = await fetch(`/api/analysis/engines/${engineType}/config`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      console.error(`엔진 설정 조회 실패: ${response.status} ${response.statusText}`)
      throw new Error(`엔진 설정 조회 실패: ${response.status} ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('엔진 설정 조회 오류:', error)
    throw error
  }
}

const saveEngineConfigAPI = async (engineType: string, config: unknown) => {
  try {
    const response = await fetch(`/api/analysis/engines/${engineType}/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config)
    })
    
    if (!response.ok) {
      console.error(`엔진 설정 저장 실패: ${response.status} ${response.statusText}`)
      throw new Error(`엔진 설정 저장 실패: ${response.status} ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('엔진 설정 저장 오류:', error)
    throw error
  }
}

// ============================
// StatusCard 컴포넌트
// ============================

interface StatusCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: string
  color: string
  clickable?: boolean
  onClick?: () => void
}

function StatusCard({ title, value, icon, trend, color, clickable = false, onClick }: StatusCardProps) {
  return (
    <div 
      className={`bg-card backdrop-blur-sm border border-border rounded-lg p-6 transition-all duration-300 shadow-sm ${
        clickable ? 'hover:bg-muted/50 cursor-pointer' : 'hover:bg-muted/50'
      }`}
      onClick={onClick}
    >
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
// 타입 정의
// ============================

interface AnalysisStep {
  id: number
  nameKey: string
  descriptionKey: string
  icon: React.ReactNode
  status: 'pending' | 'running' | 'completed' | 'error'
  result?: any
  config?: any
}

interface DataFile {
  filepath: string
  dataType: string
  filename: string
  createTime: Date
  fileSizeKb: number
  rowCount?: number
  colCount?: number
  previewData?: any[]
}

interface AnalysisResult {
  step: number
  success: boolean
  data?: any
  message: string
  timestamp: Date
  duration?: number
  artifacts?: {
    reports?: string[]
    charts?: string[]
    files?: string[]
  }
}

interface EngineConfig {
  preprocessing: {
    enabled: boolean
    cleaningRules: string[]
    featureEngineering: string[]
    metadataTagging: boolean
  }
  eda: {
    enabled: boolean
    autoReports: boolean
    pandasProfiling: boolean
    sweetviz: boolean
    customCharts: string[]
  }
  hypothesis: {
    enabled: boolean
    statisticalTests: string[]
    alertRules: string[]
    notifications: boolean
  }
}

// ============================
// Expander 컴포넌트
// ============================

interface ExpanderProps {
  title: string
  children: React.ReactNode
  defaultExpanded?: boolean
  icon?: React.ReactNode
}

function Expander({ title, children, defaultExpanded = false, icon }: ExpanderProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 bg-muted/30 hover:bg-muted/50 transition-colors duration-200 flex items-center justify-between text-left"
      >
        <div className="flex items-center">
          {icon && <span className="mr-3">{icon}</span>}
          <span className="font-medium text-foreground">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-5 h-5 text-muted-foreground" />
        )}
      </button>
      {isExpanded && (
        <div className="p-6 bg-card">
          {children}
        </div>
      )}
    </div>
  )
}

// ============================
// 메인 컴포넌트
// ============================

export default function DataAnalysisWorkflowPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedData, setSelectedData] = useState<string[]>([])
  const [availableData, setAvailableData] = useState<DataFile[]>([])
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>([
    {
      id: 0,
      nameKey: 'dataAnalysisWorkflow.steps.objectives.name',
      descriptionKey: 'dataAnalysisWorkflow.steps.objectives.description',
      icon: <Target className="w-6 h-6 text-white" />,
      status: 'pending'
    },
    {
      id: 1,
      nameKey: 'dataAnalysisWorkflow.steps.dataAcquisition.name',
      descriptionKey: 'dataAnalysisWorkflow.steps.dataAcquisition.description',
      icon: <Database className="w-6 h-6 text-white" />,
      status: 'pending'
    },
    {
      id: 2,
      nameKey: 'dataAnalysisWorkflow.steps.dataCleaning.name',
      descriptionKey: 'dataAnalysisWorkflow.steps.dataCleaning.description',
      icon: <Wrench className="w-6 h-6 text-white" />,
      status: 'pending'
    },
    {
      id: 3,
      nameKey: 'dataAnalysisWorkflow.steps.eda.name',
      descriptionKey: 'dataAnalysisWorkflow.steps.eda.description',
      icon: <BarChart3 className="w-6 h-6 text-white" />,
      status: 'pending'
    },
    {
      id: 4,
      nameKey: 'dataAnalysisWorkflow.steps.hypothesis.name',
      descriptionKey: 'dataAnalysisWorkflow.steps.hypothesis.description',
      icon: <TestTube className="w-6 h-6 text-white" />,
      status: 'pending'
    }
  ])
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [engineConfig, setEngineConfig] = useState<EngineConfig>({
    preprocessing: {
      enabled: true,
      cleaningRules: ['중복 제거', '결측값 처리'],
      featureEngineering: ['정규화', '피처 선택'],
      metadataTagging: true
    },
    eda: {
      enabled: true,
      autoReports: true,
      pandasProfiling: true,
      sweetviz: true,
      customCharts: ['상관관계 매트릭스', '분포 플롯']
    },
    hypothesis: {
      enabled: true,
      statisticalTests: ['T-검정', '카이제곱 검정', 'ANOVA'],
      alertRules: ['이상값 탐지', '트렌드 분석'],
      notifications: true
    }
  })
  const [isLoading, setIsLoading] = useState(false)
  const { t } = useTranslation()



  // 분석 현황 통계
  const analysisStats = {
    totalSteps: analysisSteps.length,
    completedSteps: analysisSteps.filter(step => step.status === 'completed').length,
    currentProgress: Math.round((analysisSteps.filter(step => step.status === 'completed').length / analysisSteps.length) * 100),
    selectedDataCount: selectedData.length
  }

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    loadAvailableData()
    loadEngineConfigs()
  }, [])

  const loadAvailableData = async () => {
    setIsLoading(true)
    try {
      const response = await getAvailableDataAPI()
      setAvailableData(response.files || [])
    } catch (error) {
      console.error('데이터 목록 로드 실패:', error)
      // Mock 데이터 사용 (백엔드 서버가 실행되지 않았을 때)
      setAvailableData([
        {
          filepath: '/data/production/manufacturing_data.csv',
          dataType: 'production',
          filename: 'manufacturing_data.csv',
          createTime: new Date('2024-12-01T10:30:00'),
          fileSizeKb: 125.4,
          rowCount: 1000,
          colCount: 15
        },
        {
          filepath: '/data/sensors/sensor_readings.csv',
          dataType: 'sensor',
          filename: 'sensor_readings.csv',
          createTime: new Date('2024-12-01T09:15:00'),
          fileSizeKb: 87.2,
          rowCount: 5000,
          colCount: 8
        },
        {
          filepath: '/data/quality/quality_metrics.csv',
          dataType: 'quality',
          filename: 'quality_metrics.csv',
          createTime: new Date('2024-12-01T08:45:00'),
          fileSizeKb: 43.8,
          rowCount: 500,
          colCount: 12
        },
        {
          filepath: '/data/experimental/experiment_results.csv',
          dataType: 'experimental',
          filename: 'experiment_results.csv',
          createTime: new Date('2024-12-01T11:00:00'),
          fileSizeKb: 67.3,
          rowCount: 300,
          colCount: 10
        },
        {
          filepath: '/data/cost/cost_analysis.csv',
          dataType: 'cost',
          filename: 'cost_analysis.csv',
          createTime: new Date('2024-12-01T12:30:00'),
          fileSizeKb: 89.1,
          rowCount: 800,
          colCount: 14
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const loadEngineConfigs = async () => {
    try {
      // 각 엔진 설정 로드 (실제 구현 시)
      // const preprocessingConfig = await getEngineConfigAPI('preprocessing')
      // const edaConfig = await getEngineConfigAPI('eda')
      // const hypothesisConfig = await getEngineConfigAPI('hypothesis')
    } catch (error) {
      console.error('엔진 설정 로드 실패:', error)
    }
  }

  const runAnalysisStep = async (stepId: number) => {
    const step = analysisSteps[stepId]
    if (!step) return

    // 단계 상태를 running으로 설정
    setAnalysisSteps(prev => prev.map(s => 
      s.id === stepId ? { ...s, status: 'running' } : s
    ))

    setIsLoading(true)
    const startTime = new Date()

    try {
      const config = {
        selectedData,
        engineConfig,
        stepConfig: step.config || {}
      }

      // 단계별 엔드포인트 매핑
      const stepEndpoints = [
        'define_objectives_&_hypotheses',
        'data_acquisition_&_ingestion', 
        'data_cleaning_&_feature_engineering',
        'exploratory_data_analysis_(eda)',
        'hypothesis_testing_&_alerting'
      ]
      
      const response = await runAnalysisStepAPI(stepEndpoints[stepId], config)
      
      const result: AnalysisResult = {
        step: stepId,
        success: true,
        data: response.data,
        message: response.message || `${t(step.nameKey)} 단계가 성공적으로 완료되었습니다.`,
        timestamp: new Date(),
        duration: Date.now() - startTime.getTime(),
        artifacts: response.artifacts
      }

      setAnalysisResults(prev => [...prev, result])
      
      // 단계 상태를 completed로 설정
      setAnalysisSteps(prev => prev.map(s => 
        s.id === stepId ? { ...s, status: 'completed', result: response } : s
      ))

      // 다음 단계로 자동 진행
      if (stepId < analysisSteps.length - 1) {
        setCurrentStep(stepId + 1)
      }

    } catch (error) {
      console.error(`분석 단계 ${stepId} 실행 실패:`, error)
      
      const result: AnalysisResult = {
        step: stepId,
        success: false,
        message: `${t(step.nameKey)} 단계 실행 중 오류가 발생했습니다: ${error}`,
        timestamp: new Date(),
        duration: Date.now() - startTime.getTime()
      }

      setAnalysisResults(prev => [...prev, result])
      
      // 단계 상태를 error로 설정
      setAnalysisSteps(prev => prev.map(s => 
        s.id === stepId ? { ...s, status: 'error' } : s
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const resetWorkflow = () => {
    setCurrentStep(0)
    setSelectedData([])
    setAnalysisResults([])
    setAnalysisSteps(prev => prev.map(step => ({ ...step, status: 'pending', result: undefined })))
  }

  const getStepStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return '#6b7280'
      case 'running': return '#f97316'
      case 'completed': return '#22c55e'
      case 'error': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getStepStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4" />
      case 'running': return <RefreshCw className="w-4 h-4 animate-spin" />
      case 'completed': return <CheckCircle className="w-4 h-4" />
      case 'error': return <AlertCircle className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="w-full">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-4 flex items-center">
            <Brain className="w-8 h-8 mr-3 text-accent-blue" />
            {t('dataAnalysisWorkflow.title')}
          </h1>
          <p className="text-muted-foreground text-lg">
            {t('dataAnalysisWorkflow.subtitle')}
          </p>
        </div>

        {/* 분석 현황 대시보드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title={t('dataAnalysisWorkflow.statusCards.totalSteps')}
            value={analysisStats.totalSteps}
            icon={<Brain className="w-6 h-6 text-white" />}
            color="#3b82f6"
          />
          <StatusCard
            title={t('dataAnalysisWorkflow.statusCards.completedSteps')}
            value={analysisStats.completedSteps}
            icon={<CheckCircle className="w-6 h-6 text-white" />}
            color="#22c55e"
          />
          <StatusCard
            title={t('dataAnalysisWorkflow.statusCards.progress')}
            value={`${analysisStats.currentProgress}%`}
            icon={<TrendingUp className="w-6 h-6 text-white" />}
            color="#8b5cf6"
          />
          <StatusCard
            title={t('dataAnalysisWorkflow.statusCards.selectedData')}
            value={analysisStats.selectedDataCount}
            icon={<Database className="w-6 h-6 text-white" />}
            color="#f97316"
          />
        </div>

        {/* 워크플로우 진행 상황 */}
        <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-8 mb-8 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-foreground">{t('dataAnalysisWorkflow.workflow.title')}</h2>
            <button
              onClick={resetWorkflow}
              className="px-4 py-2 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 transition-colors duration-200 flex items-center"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              {t('dataAnalysisWorkflow.workflow.reset')}
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {analysisSteps.map((step, index) => (
              <div
                key={step.id}
                className={`relative p-4 rounded-lg border transition-all duration-300 ${
                  currentStep === index ? 'border-accent-blue bg-accent-blue/10' : 
                  step.status === 'completed' ? 'border-green-500 bg-green-500/10' :
                  step.status === 'error' ? 'border-red-500 bg-red-500/10' :
                  'border-border bg-muted/30'
                }`}
              >
                <div className="flex items-center mb-2">
                  <div 
                    className="p-2 rounded-lg mr-3"
                    style={{ backgroundColor: getStepStatusColor(step.status) }}
                  >
                    {step.icon}
                  </div>
                  {getStepStatusIcon(step.status)}
                </div>
                <h3 className="font-medium text-sm text-foreground mb-1">{t(step.nameKey)}</h3>
                <p className="text-xs text-muted-foreground">{t(step.descriptionKey)}</p>
                
                {/* 다음 단계 화살표 */}
                {index < analysisSteps.length - 1 && (
                  <ArrowRight className="absolute -right-6 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground hidden md:block" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* 단계별 설정 패널 */}
          <div className="lg:col-span-2">
            <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-8 shadow-sm">
              {currentStep === 0 && <ObjectivesDefinitionPanel />}
              {currentStep === 1 && (
                <DataAcquisitionPanel 
                  availableData={availableData}
                  selectedData={selectedData}
                  onDataSelect={setSelectedData}
                />
              )}
              {currentStep === 2 && (
                <DataCleaningPanel 
                  config={engineConfig.preprocessing}
                  onConfigChange={(config) => setEngineConfig(prev => ({ ...prev, preprocessing: config }))}
                />
              )}
              {currentStep === 3 && (
                <EDAPanel 
                  config={engineConfig.eda}
                  onConfigChange={(config) => setEngineConfig(prev => ({ ...prev, eda: config }))}
                />
              )}
              {currentStep === 4 && (
                <HypothesisTestingPanel 
                  config={engineConfig.hypothesis}
                  onConfigChange={(config) => setEngineConfig(prev => ({ ...prev, hypothesis: config }))}
                />
              )}

              {/* 실행 버튼 */}
              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                  disabled={currentStep === 0}
                  className="px-6 py-3 bg-muted text-muted-foreground rounded-lg hover:bg-muted/80 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {t('dataAnalysisWorkflow.workflow.previousStep')}
                </button>
                
                <button
                  onClick={() => runAnalysisStep(currentStep)}
                  disabled={isLoading || (currentStep === 1 && selectedData.length === 0)}
                  className="px-6 py-3 bg-accent-blue text-white rounded-lg hover:bg-accent-blue/80 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      {t('dataAnalysisWorkflow.workflow.running')}
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      {t('dataAnalysisWorkflow.workflow.runStep')}
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 결과 및 정보 패널 */}
          <div className="space-y-6">
            <EngineStatusPanel engineConfig={engineConfig} />
            <AnalysisResultsPanel results={analysisResults} />
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================
// 단계별 패널 컴포넌트들
// ============================

function ObjectivesDefinitionPanel() {
  const { t } = useTranslation()
  const [objectives, setObjectives] = useState<string[]>(['부적합 (이상)', '설비 점검', '품질 이상'])
  const [hypotheses, setHypotheses] = useState('')
  const [analysisTheme, setAnalysisTheme] = useState('manufacturing_quality')

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-foreground mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2 text-accent-blue" />
          {t('dataAnalysisWorkflow.steps.objectives.title')}
        </h3>
        <p className="text-muted-foreground mb-6">
          {t('dataAnalysisWorkflow.steps.objectives.subtitle')}
        </p>
      </div>

      <Expander title={t('dataAnalysisWorkflow.objectives.analysisGoals')} defaultExpanded={true} icon={<Target className="w-4 h-4" />}>
        <div className="space-y-4">
          <div>
            <Select
              value={analysisTheme}
              onChange={setAnalysisTheme}
              options={[
                { value: 'manufacturing_quality', label: t('dataAnalysisWorkflow.objectives.themes.manufacturingQuality') },
                { value: 'equipment_performance', label: t('dataAnalysisWorkflow.objectives.themes.equipmentPerformance') },
                { value: 'process_optimization', label: t('dataAnalysisWorkflow.objectives.themes.processOptimization') },
                { value: 'predictive_maintenance', label: t('dataAnalysisWorkflow.objectives.themes.predictiveMaintenance') }
              ]}
              label={t('dataAnalysisWorkflow.objectives.analysisTheme')}
            />
          </div>
          
          <div>
            <MultiSelect
              value={objectives}
              onChange={setObjectives}
              options={[
                t('dataAnalysisWorkflow.objectives.goals.nonConformance'),
                t('dataAnalysisWorkflow.objectives.goals.equipmentInspection'),
                t('dataAnalysisWorkflow.objectives.goals.qualityIssues'),
                t('dataAnalysisWorkflow.objectives.goals.costOptimization'),
                t('dataAnalysisWorkflow.objectives.goals.yieldImprovement')
              ]}
              label={t('dataAnalysisWorkflow.objectives.analysisGoal')}
              placeholder={t('dataAnalysisWorkflow.objectives.selectDataPlaceholder')}
            />
          </div>
        </div>
      </Expander>

      <Expander title={t('dataAnalysisWorkflow.objectives.hypothesisDefinition')} icon={<Lightbulb className="w-4 h-4" />}>
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">{t('dataAnalysisWorkflow.objectives.hypothesisToTest')}</label>
          <textarea
            value={hypotheses}
            onChange={(e) => setHypotheses(e.target.value)}
            placeholder={t('dataAnalysisWorkflow.objectives.placeholder')}
            className="w-full p-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
            rows={4}
          />
        </div>
      </Expander>
    </div>
  )
}

function DataAcquisitionPanel({ 
  availableData, 
  selectedData, 
  onDataSelect 
}: { 
  availableData: DataFile[]
  selectedData: string[]
  onDataSelect: (data: string[]) => void
}) {
  const dataTypes = ['production', 'sensor', 'quality', 'experimental', 'cost']
  
  const getDataTypeIcon = (type: string) => {
    switch (type) {
      case 'production': return <Factory className="w-4 h-4" />
      case 'sensor': return <Activity className="w-4 h-4" />
      case 'quality': return <CheckCircle className="w-4 h-4" />
      case 'experimental': return <FlaskConical className="w-4 h-4" />
      case 'cost': return <DollarSign className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getDataTypeLabel = (type: string) => {
    switch (type) {
      case 'production': return '생산 데이터'
      case 'sensor': return '센서 데이터'  
      case 'quality': return '품질 데이터'
      case 'experimental': return '실험 데이터'
      case 'cost': return '비용 데이터'
      default: return type
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-foreground mb-4 flex items-center">
          <Database className="w-5 h-5 mr-2 text-accent-blue" />
          데이터 수집 및 선택
        </h3>
        <p className="text-muted-foreground mb-6">
          분석에 사용할 데이터를 선택합니다. 관련 IoT 데이터와 관련 데이터를 포함합니다.
        </p>
      </div>

      <Expander title="사용 가능한 데이터" defaultExpanded={true} icon={<Database className="w-4 h-4" />}>
        <div className="space-y-4">
          {dataTypes.map(dataType => {
            const typeData = availableData.filter(file => file.dataType === dataType)
            if (typeData.length === 0) return null

            return (
              <div key={dataType} className="border border-border rounded-lg p-4">
                <div className="flex items-center mb-3">
                  {getDataTypeIcon(dataType)}
                  <span className="ml-2 font-medium text-foreground">{getDataTypeLabel(dataType)}</span>
                  <span className="ml-auto text-sm text-muted-foreground">{typeData.length}개 파일</span>
                </div>
                
                <div className="space-y-2">
                  {typeData.map(file => (
                    <label key={file.filepath} className="flex items-center p-3 rounded-lg border border-border hover:bg-muted/30 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedData.includes(file.filepath)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            onDataSelect([...selectedData, file.filepath])
                          } else {
                            onDataSelect(selectedData.filter(path => path !== file.filepath))
                          }
                        }}
                        className="mr-3"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-foreground">{file.filename}</div>
                        <div className="text-sm text-muted-foreground">
                          {file.rowCount?.toLocaleString()} 행 × {file.colCount} 열 | {file.fileSizeKb} KB
                        </div>
                      </div>
                      <Eye className="w-4 h-4 text-muted-foreground ml-2" />
                    </label>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </Expander>

      {selectedData.length > 0 && (
        <div className="bg-accent-blue/10 border border-accent-blue/20 rounded-lg p-4">
          <h4 className="font-medium text-foreground mb-2">선택된 데이터 ({selectedData.length}개)</h4>
          <div className="space-y-1">
            {selectedData.map(filepath => {
              const file = availableData.find(f => f.filepath === filepath)
              return (
                <div key={filepath} className="text-sm text-muted-foreground">
                  • {file?.filename || filepath}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function DataCleaningPanel({ 
  config, 
  onConfigChange 
}: { 
  config: EngineConfig['preprocessing']
  onConfigChange: (config: EngineConfig['preprocessing']) => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-foreground mb-4 flex items-center">
          <Wrench className="w-5 h-5 mr-2 text-accent-blue" />
          데이터 정제 및 피처 엔지니어링
        </h3>
        <p className="text-muted-foreground mb-6">
          전처리 엔진을 사용하여 데이터 정제, 피처 생성, 메타데이터 태깅을 수행합니다.
        </p>
      </div>

      <Expander title="전처리 엔진 설정" defaultExpanded={true} icon={<Settings className="w-4 h-4" />}>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.enabled}
              onChange={(checked: boolean) => onConfigChange({ ...config, enabled: checked })}
              label="전처리 엔진 활성화"
            />
          </div>

          <div>
            <MultiSelect
              value={config.cleaningRules}
              onChange={(rules: string[]) => onConfigChange({ ...config, cleaningRules: rules })}
              options={[
                '중복 제거',
                '결측값 처리',
                '이상값 탐지',
                '데이터 검증',
                '형식 표준화'
              ]}
              label="정제 규칙"
              placeholder="정제 규칙 선택"
            />
          </div>

          <div>
            <MultiSelect
              value={config.featureEngineering}
              onChange={(features: string[]) => onConfigChange({ ...config, featureEngineering: features })}
              options={[
                '정규화',
                '피처 선택',
                '차원 축소',
                '상호작용 피처',
                '시계열 피처'
              ]}
              label="피처 엔지니어링"
              placeholder="피처 엔지니어링 방법 선택"
            />
          </div>

          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.metadataTagging}
              onChange={(checked: boolean) => onConfigChange({ ...config, metadataTagging: checked })}
              label="메타데이터 태깅"
            />
          </div>
        </div>
      </Expander>
    </div>
  )
}

function EDAPanel({ 
  config, 
  onConfigChange 
}: { 
  config: EngineConfig['eda']
  onConfigChange: (config: EngineConfig['eda']) => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-foreground mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2 text-accent-blue" />
          탐색적 데이터 분석 (EDA)
        </h3>
        <p className="text-muted-foreground mb-6">
          EDA 엔진을 통해 자동화된 리포트 생성 및 시각화를 수행합니다.
        </p>
      </div>

      <Expander title="EDA 엔진 설정" defaultExpanded={true} icon={<BarChart3 className="w-4 h-4" />}>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.enabled}
              onChange={(checked: boolean) => onConfigChange({ ...config, enabled: checked })}
              label="EDA 엔진 활성화"
            />
          </div>

          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.autoReports}
              onChange={(checked: boolean) => onConfigChange({ ...config, autoReports: checked })}
              label="자동 리포트 생성"
            />
          </div>

          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.pandasProfiling}
              onChange={(checked: boolean) => onConfigChange({ ...config, pandasProfiling: checked })}
              label="Pandas Profiling"
            />
          </div>

          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.sweetviz}
              onChange={(checked: boolean) => onConfigChange({ ...config, sweetviz: checked })}
              label="Sweetviz"
            />
          </div>

          <div>
            <MultiSelect
              value={config.customCharts}
              onChange={(charts: string[]) => onConfigChange({ ...config, customCharts: charts })}
              options={[
                '상관관계 매트릭스',
                '분포 플롯',
                '박스 플롯',
                '산점도 매트릭스',
                '시계열 플롯'
              ]}
              label="커스텀 차트"
              placeholder="차트 유형 선택"
            />
          </div>
        </div>
      </Expander>
    </div>
  )
}

function HypothesisTestingPanel({ 
  config, 
  onConfigChange 
}: { 
  config: EngineConfig['hypothesis']
  onConfigChange: (config: EngineConfig['hypothesis']) => void
}) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-bold text-foreground mb-4 flex items-center">
          <TestTube className="w-5 h-5 mr-2 text-accent-blue" />
          가설 검정 및 알림
        </h3>
        <p className="text-muted-foreground mb-6">
          가설 엔진을 사용하여 통계적 검정, 알림 규칙, 알림 시스템을 구성합니다.
        </p>
      </div>

      <Expander title="가설 엔진 설정" defaultExpanded={true} icon={<TestTube className="w-4 h-4" />}>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.enabled}
              onChange={(checked: boolean) => onConfigChange({ ...config, enabled: checked })}
              label="가설 엔진 활성화"
            />
          </div>

          <div>
            <MultiSelect
              value={config.statisticalTests}
              onChange={(tests: string[]) => onConfigChange({ ...config, statisticalTests: tests })}
              options={[
                'T-검정',
                '카이제곱 검정',
                'ANOVA',
                'Mann-Whitney U 검정',
                'Kruskal-Wallis 검정'
              ]}
              label="통계적 검정"
              placeholder="통계적 검정 방법 선택"
            />
          </div>

          <div>
            <MultiSelect
              value={config.alertRules}
              onChange={(rules: string[]) => onConfigChange({ ...config, alertRules: rules })}
              options={[
                '이상값 탐지',
                '트렌드 분석',
                '임계값 모니터링',
                '패턴 인식',
                '통계적 유의성'
              ]}
              label="알림 규칙"
              placeholder="알림 규칙 선택"
            />
          </div>

          <div className="flex items-center justify-between">
            <Checkbox
              checked={config.notifications}
              onChange={(checked: boolean) => onConfigChange({ ...config, notifications: checked })}
              label="알림 시스템"
            />
          </div>
        </div>
      </Expander>
    </div>
  )
}

// ============================
// 결과 및 상태 패널 컴포넌트들
// ============================

function EngineStatusPanel({ engineConfig }: { engineConfig: EngineConfig }) {
  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
      <h3 className="text-lg font-bold text-foreground mb-4 flex items-center">
        <Settings className="w-5 h-5 mr-2 text-accent-blue" />
        엔진 상태
      </h3>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-foreground">Preprocessing Engine</span>
          <div className={`px-2 py-1 rounded text-xs ${
            engineConfig.preprocessing.enabled 
              ? 'bg-green-500/20 text-green-600' 
              : 'bg-gray-500/20 text-gray-600'
          }`}>
            {engineConfig.preprocessing.enabled ? '활성화' : '비활성화'}
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-foreground">EDA Engine</span>
          <div className={`px-2 py-1 rounded text-xs ${
            engineConfig.eda.enabled 
              ? 'bg-green-500/20 text-green-600' 
              : 'bg-gray-500/20 text-gray-600'
          }`}>
            {engineConfig.eda.enabled ? '활성화' : '비활성화'}
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-foreground">Hypothesis Engine</span>
          <div className={`px-2 py-1 rounded text-xs ${
            engineConfig.hypothesis.enabled 
              ? 'bg-green-500/20 text-green-600' 
              : 'bg-gray-500/20 text-gray-600'
          }`}>
            {engineConfig.hypothesis.enabled ? '활성화' : '비활성화'}
          </div>
        </div>
      </div>
    </div>
  )
}

function AnalysisResultsPanel({ results }: { results: AnalysisResult[] }) {
  return (
    <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 shadow-sm">
      <h3 className="text-lg font-bold text-foreground mb-4 flex items-center">
        <BarChart className="w-5 h-5 mr-2 text-accent-blue" />
        분석 결과
      </h3>
      
      {results.length === 0 ? (
        <p className="text-muted-foreground text-sm">아직 실행된 단계가 없습니다.</p>
      ) : (
        <div className="space-y-4">
          {results.slice(-3).map((result, index) => (
            <div 
              key={`${result.step}-${result.timestamp.getTime()}`} 
              className={`p-4 rounded-lg border ${
                result.success 
                  ? 'border-green-500/20 bg-green-500/10' 
                  : 'border-red-500/20 bg-red-500/10'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-foreground">
                  단계 {result.step + 1}
                </span>
                <span className="text-xs text-muted-foreground">
                  {result.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">{result.message}</p>
              {result.duration && (
                <p className="text-xs text-muted-foreground mt-1">
                  실행 시간: {(result.duration / 1000).toFixed(1)}초
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}