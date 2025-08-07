'use client'

import { useState, useEffect } from 'react'
import { 
  Brain, Target, TrendingUp, BarChart3, Activity, Settings, 
  CheckCircle, AlertCircle, Play, Download, Eye, Info,
  Database, Zap, Award, FileText
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { TabNavigation, Select, Slider, Checkbox } from '@/components/ui'
import { FloatingChatbot } from '@/components/FloatingChatbot'
import { useAppStore } from '@/store/useAppStore'

// 인터페이스 정의
interface ModelConfig {
  modelType: string
  taskType: 'regression' | 'classification'
  hyperparameters: { [key: string]: any }
}

interface TrainingResult {
  modelId: string
  metrics: { [key: string]: number }
  trainingTime: number
  featureImportance: { [key: string]: number }
}

interface EvaluationResult {
  testMetrics: { [key: string]: number }
  predictions: number[]
  actualValues: number[]
  confusionMatrix?: number[][]
}

interface SimulationResult {
  predictedValue: number
  actualValue: number
  difference: number
  percentageError: number
}

export default function ProductModelingPage() {
  const { t } = useTranslation()
  const { trainData, testData, originalData, preprocessingConfig, dataInfo } = useAppStore()
  
  // 상태 관리
  const [activeTab, setActiveTab] = useState<'overview' | 'modeling' | 'evaluation' | 'interpretation'>('overview')
  const [isLoading, setIsLoading] = useState(false)
  
  // 모델 설정
  const [modelConfig, setModelConfig] = useState<ModelConfig>({
    modelType: 'random_forest',
    taskType: 'regression',
    hyperparameters: {}
  })
  
  // 결과 상태
  const [trainingResult, setTrainingResult] = useState<TrainingResult | null>(null)
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult | null>(null)
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([])
  
  // 시뮬레이션 상태
  const [simulationInputs, setSimulationInputs] = useState<{ [key: string]: number }>({})
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null)
  
  // 초기화
  useEffect(() => {
    if (dataInfo?.numericColumns) {
      setSelectedFeatures(dataInfo.numericColumns.filter(col => col !== preprocessingConfig?.targetColumn))
    }
    
    // 타겟 변수 타입에 따라 태스크 타입 자동 결정
    if (trainData && preprocessingConfig?.targetColumn) {
      const targetValues = trainData.map(row => row[preprocessingConfig.targetColumn])
      const uniqueValues = new Set(targetValues)
      setModelConfig(prev => ({
        ...prev,
        taskType: uniqueValues.size <= 10 ? 'classification' : 'regression'
      }))
    }
  }, [trainData, testData, preprocessingConfig, dataInfo])

  // 모델 학습 함수
  const handleTrainModel = async () => {
    if (!trainData || !preprocessingConfig?.targetColumn) {
      alert('훈련 데이터가 없습니다. 먼저 데이터 분석에서 전처리를 완료해주세요.')
      return
    }

    setIsLoading(true)
    try {
      // 실제 백엔드 API 호출 대신 시뮬레이션
      const mockResult: TrainingResult = {
        modelId: `${modelConfig.modelType}_${Date.now()}`,
        metrics: modelConfig.taskType === 'regression' 
          ? {
              r2_score: 0.85 + Math.random() * 0.1,
              mse: 0.15 + Math.random() * 0.1,
              mae: 0.12 + Math.random() * 0.08,
              rmse: 0.38 + Math.random() * 0.1
            }
          : {
              accuracy: 0.88 + Math.random() * 0.1,
              precision: 0.86 + Math.random() * 0.1,
              recall: 0.84 + Math.random() * 0.1,
              f1_score: 0.85 + Math.random() * 0.1
            },
        trainingTime: 2.5 + Math.random() * 3,
        featureImportance: selectedFeatures.reduce((acc, feature, idx) => {
          acc[feature] = Math.random()
          return acc
        }, {} as { [key: string]: number })
      }

      // 2초 지연
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      setTrainingResult(mockResult)
      alert('모델 학습이 완료되었습니다!')
      
    } catch (error) {
      console.error('모델 학습 오류:', error)
      alert('모델 학습 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  // 모델 평가 함수
  const handleEvaluateModel = async () => {
    if (!trainingResult || !testData) {
      alert('먼저 모델을 학습해주세요.')
      return
    }

    setIsLoading(true)
    try {
      // 테스트 데이터로 평가 시뮬레이션
      const mockEvaluation: EvaluationResult = {
        testMetrics: modelConfig.taskType === 'regression'
          ? {
              r2_score: trainingResult.metrics.r2_score * (0.9 + Math.random() * 0.1),
              mse: trainingResult.metrics.mse * (1 + Math.random() * 0.2),
              mae: trainingResult.metrics.mae * (1 + Math.random() * 0.15),
              rmse: trainingResult.metrics.rmse * (1 + Math.random() * 0.15)
            }
          : {
              accuracy: trainingResult.metrics.accuracy * (0.92 + Math.random() * 0.08),
              precision: trainingResult.metrics.precision * (0.9 + Math.random() * 0.1),
              recall: trainingResult.metrics.recall * (0.91 + Math.random() * 0.09),
              f1_score: trainingResult.metrics.f1_score * (0.9 + Math.random() * 0.1)
            },
        predictions: Array.from({ length: testData.length }, () => Math.random() * 100),
        actualValues: testData.map(row => row[preprocessingConfig?.targetColumn || ''])
      }

      await new Promise(resolve => setTimeout(resolve, 1000))
      setEvaluationResult(mockEvaluation)
      
    } catch (error) {
      console.error('모델 평가 오류:', error)
      alert('모델 평가 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  // 시뮬레이션 함수
  const handleSimulation = async (actualValue: number) => {
    if (!trainingResult || Object.keys(simulationInputs).length === 0) {
      alert('모든 특성 값을 입력해주세요.')
      return
    }

    setIsLoading(true)
    try {
      // 모델 기반 예측값 계산 (시뮬레이션)
      const features = selectedFeatures.map(feature => simulationInputs[feature] || 0)
      
      // 간단한 선형 예측 시뮬레이션 (실제로는 백엔드 API 호출)
      let predictedValue = 0
      features.forEach((value, idx) => {
        const importance = Object.values(trainingResult.featureImportance)[idx] || 0.1
        predictedValue += value * importance * (Math.random() * 2 + 0.5)
      })
      
      // 회귀의 경우 타겟 변수 범위에 맞게 조정
      if (modelConfig.taskType === 'regression' && trainData) {
        const targetValues = trainData.map(row => row[preprocessingConfig?.targetColumn || ''])
        const minTarget = Math.min(...targetValues)
        const maxTarget = Math.max(...targetValues)
        predictedValue = Math.max(minTarget, Math.min(maxTarget, predictedValue))
      }

      const difference = Math.abs(predictedValue - actualValue)
      const percentageError = actualValue !== 0 ? (difference / Math.abs(actualValue)) * 100 : 0

      const result: SimulationResult = {
        predictedValue,
        actualValue,
        difference,
        percentageError
      }

      await new Promise(resolve => setTimeout(resolve, 1000))
      setSimulationResult(result)
      
    } catch (error) {
      console.error('시뮬레이션 오류:', error)
      alert('시뮬레이션 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      {/* 헤더 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2 flex items-center">
          <Brain className="w-8 h-8 mr-3 text-accent-purple" />
          모델링
        </h1>
        <p className="text-muted-foreground">
          전처리된 데이터를 활용하여 머신러닝 모델을 학습하고 성능을 평가합니다.
        </p>
      </div>

      {/* 데이터 연동 상태 표시 */}
      {trainData && testData ? (
        <div className="bg-gradient-to-r from-accent-green/10 to-accent-blue/10 border border-accent-green/30 rounded-lg p-4 mb-6">
          <div className="flex items-center mb-3">
            <CheckCircle className="w-5 h-5 mr-2 text-accent-green" />
            <h3 className="text-lg font-semibold text-foreground">데이터 분석 연동 완료</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-lg font-bold text-foreground">{trainData.length.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">훈련 데이터</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-accent-orange">{testData.length.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">테스트 데이터</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-accent-purple">{dataInfo?.numericColumns.length || 0}</div>
              <div className="text-xs text-muted-foreground">수치형 특성</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-accent-blue">
                {preprocessingConfig?.targetColumn || 'None'}
              </div>
              <div className="text-xs text-muted-foreground">타겟 변수</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-lg p-6 text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
          <h3 className="text-lg font-semibold text-foreground mb-2">데이터 분석 연동 필요</h3>
          <p className="text-muted-foreground mb-4">
            먼저 <strong>데이터 분석</strong> 탭에서 데이터를 선택하고 전처리를 완료해주세요.
          </p>
          <button
            onClick={() => window.location.href = '/copilot/product-data-analysis'}
            className="bg-gradient-primary text-white px-4 py-2 rounded-lg hover:scale-105 transition-transform"
          >
            데이터 분석 탭으로 이동
          </button>
        </div>
      )}

      {/* 탭 메뉴 */}
      <TabNavigation
        tabs={[
          { id: 'overview', name: '모델 개요', icon: Info },
          { id: 'modeling', name: '모델 학습', icon: Brain },
          { id: 'evaluation', name: '시뮬레이션', icon: BarChart3 },
          { id: 'interpretation', name: '모델 해석', icon: Eye }
        ]}
        activeTab={activeTab}
        onTabChange={(tabId) => setActiveTab(tabId as any)}
        className="mb-6"
      />

      {/* 탭 컨텐츠 */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 모델링 워크플로우 개요 */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
              <Target className="w-5 h-5 mr-2 text-accent-blue" />
              머신러닝 워크플로우
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-muted/30 rounded-lg p-4 text-center">
                <div className="w-12 h-12 bg-accent-blue/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Database className="w-6 h-6 text-accent-blue" />
                </div>
                <h4 className="font-semibold text-foreground mb-2">1. 데이터 준비</h4>
                <p className="text-sm text-muted-foreground">전처리된 데이터를 훈련/테스트로 분할</p>
                <div className="mt-2">
                  {trainData ? (
                    <span className="text-xs bg-accent-green/20 text-accent-green px-2 py-1 rounded">완료</span>
                  ) : (
                    <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded">대기</span>
                  )}
                </div>
              </div>

              <div className="bg-muted/30 rounded-lg p-4 text-center">
                <div className="w-12 h-12 bg-accent-purple/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Brain className="w-6 h-6 text-accent-purple" />
                </div>
                <h4 className="font-semibold text-foreground mb-2">2. 모델 학습</h4>
                <p className="text-sm text-muted-foreground">알고리즘 선택 및 하이퍼파라미터 튜닝</p>
                <div className="mt-2">
                  {trainingResult ? (
                    <span className="text-xs bg-accent-green/20 text-accent-green px-2 py-1 rounded">완료</span>
                  ) : (
                    <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded">대기</span>
                  )}
                </div>
              </div>

              <div className="bg-muted/30 rounded-lg p-4 text-center">
                <div className="w-12 h-12 bg-accent-orange/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <BarChart3 className="w-6 h-6 text-accent-orange" />
                </div>
                <h4 className="font-semibold text-foreground mb-2">3. 시뮬레이션</h4>
                <p className="text-sm text-muted-foreground">실제 값으로 예측 테스트</p>
                <div className="mt-2">
                  {simulationResult ? (
                    <span className="text-xs bg-accent-green/20 text-accent-green px-2 py-1 rounded">완료</span>
                  ) : (
                    <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded">대기</span>
                  )}
                </div>
              </div>

              <div className="bg-muted/30 rounded-lg p-4 text-center">
                <div className="w-12 h-12 bg-accent-green/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Eye className="w-6 h-6 text-accent-green" />
                </div>
                <h4 className="font-semibold text-foreground mb-2">4. 모델 해석</h4>
                <p className="text-sm text-muted-foreground">특성 중요도 및 예측 설명</p>
                <div className="mt-2">
                  {trainingResult ? (
                    <span className="text-xs bg-accent-green/20 text-accent-green px-2 py-1 rounded">가능</span>
                  ) : (
                    <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded">대기</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 데이터 정보 카드 */}
          {trainData && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-card border border-border rounded-lg p-6">
                <h4 className="font-semibold text-foreground mb-3 flex items-center">
                  <Database className="w-4 h-4 mr-2" />
                  데이터 분할 정보
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">훈련 데이터:</span>
                    <span className="text-foreground font-medium">{trainData.length}행</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">테스트 데이터:</span>
                    <span className="text-foreground font-medium">{testData?.length}행</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">분할 비율:</span>
                    <span className="text-foreground font-medium">
                      {((preprocessingConfig?.trainTestSplit || 0.8) * 100).toFixed(0)}% : {(100 - (preprocessingConfig?.trainTestSplit || 0.8) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-6">
                <h4 className="font-semibold text-foreground mb-3 flex items-center">
                  <Target className="w-4 h-4 mr-2" />
                  타겟 변수 정보
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">타겟 변수:</span>
                    <span className="text-foreground font-medium">{preprocessingConfig?.targetColumn}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">문제 유형:</span>
                    <span className="text-foreground font-medium">
                      {modelConfig.taskType === 'regression' ? '회귀' : '분류'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">특성 개수:</span>
                    <span className="text-foreground font-medium">{dataInfo?.numericColumns.length}</span>
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-6">
                <h4 className="font-semibold text-foreground mb-3 flex items-center">
                  <Settings className="w-4 h-4 mr-2" />
                  전처리 정보
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">결측치 처리:</span>
                    <span className="text-foreground font-medium text-xs">
                      {preprocessingConfig?.missingValueMethod}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">이상치 처리:</span>
                    <span className="text-foreground font-medium text-xs">
                      {preprocessingConfig?.outlierMethod}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">스케일링:</span>
                    <span className="text-foreground font-medium text-xs">
                      {preprocessingConfig?.scalingMethod}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 모델 학습 탭 */}
      {activeTab === 'modeling' && trainData && (
        <div className="space-y-6">
          {/* 모델 선택 및 설정 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 모델 선택 */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <Brain className="w-5 h-5 mr-2 text-accent-purple" />
                모델 선택
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    알고리즘 선택
                  </label>
                  <Select
                    label=""
                    value={modelConfig.modelType}
                    onChange={(value) => setModelConfig(prev => ({ ...prev, modelType: value }))}
                    options={modelConfig.taskType === 'regression' ? [
                      { value: 'linear_regression', label: '선형 회귀 (Linear Regression)' },
                      { value: 'ridge_regression', label: '릿지 회귀 (Ridge)' },
                      { value: 'lasso_regression', label: '라쏘 회귀 (Lasso)' },
                      { value: 'random_forest', label: '랜덤 포레스트 (Random Forest)' },
                      { value: 'gradient_boosting', label: '그래디언트 부스팅 (XGBoost)' },
                      { value: 'svr', label: '서포트 벡터 회귀 (SVR)' },
                      { value: 'neural_network', label: '신경망 (Neural Network)' }
                    ] : [
                      { value: 'logistic_regression', label: '로지스틱 회귀' },
                      { value: 'svm', label: '서포트 벡터 머신 (SVM)' },
                      { value: 'random_forest', label: '랜덤 포레스트' },
                      { value: 'gradient_boosting', label: '그래디언트 부스팅' },
                      { value: 'knn', label: 'K-최근접 이웃 (K-NN)' },
                      { value: 'naive_bayes', label: '나이브 베이즈' },
                      { value: 'neural_network', label: '신경망' }
                    ]}
                  />
                </div>

                <div className="bg-muted/30 rounded-lg p-3">
                  <div className="text-sm font-medium text-foreground mb-2">
                    {modelConfig.modelType === 'random_forest' && '랜덤 포레스트'}
                    {modelConfig.modelType === 'gradient_boosting' && '그래디언트 부스팅'}
                    {modelConfig.modelType === 'linear_regression' && '선형 회귀'}
                    {modelConfig.modelType === 'neural_network' && '신경망'}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {modelConfig.modelType === 'random_forest' && '여러 결정 트리를 결합하여 높은 정확도와 안정성을 제공합니다. 특성 중요도 해석이 용이합니다.'}
                    {modelConfig.modelType === 'gradient_boosting' && '순차적으로 약한 학습기를 결합하여 강력한 예측 성능을 제공합니다.'}
                    {modelConfig.modelType === 'linear_regression' && '선형 관계를 모델링하는 기본적이지만 해석하기 쉬운 알고리즘입니다.'}
                    {modelConfig.modelType === 'neural_network' && '복잡한 비선형 패턴을 학습할 수 있는 강력한 알고리즘입니다.'}
                  </div>
                </div>
              </div>
            </div>

            {/* 특성 선택 */}
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <Target className="w-5 h-5 mr-2 text-accent-green" />
                특성 선택
              </h3>
              
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {dataInfo?.numericColumns
                  .filter(col => col !== preprocessingConfig?.targetColumn)
                  .map(feature => (
                    <div key={feature} className="flex items-center space-x-3">
                      <Checkbox
                        checked={selectedFeatures.includes(feature)}
                        onChange={(checked: boolean) => {
                          if (checked) {
                            setSelectedFeatures(prev => [...prev, feature])
                          } else {
                            setSelectedFeatures(prev => prev.filter(f => f !== feature))
                          }
                        }}
                        label={feature}
                      />
                    </div>
                  ))}
              </div>
              
              <div className="mt-4 text-sm text-muted-foreground">
                선택된 특성: {selectedFeatures.length}개
              </div>
            </div>
          </div>

          {/* 모델 학습 실행 */}
          <div className="bg-card border border-border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground flex items-center">
                <Play className="w-5 h-5 mr-2 text-accent-blue" />
                모델 학습 실행
              </h3>
              
              {trainingResult && (
                <span className="text-sm bg-accent-green/20 text-accent-green px-3 py-1 rounded-full">
                  학습 완료
                </span>
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {selectedFeatures.length}개 특성으로 {modelConfig.modelType} 모델을 학습합니다.
              </div>
              
              <button
                onClick={handleTrainModel}
                disabled={isLoading || selectedFeatures.length === 0}
                className="flex items-center px-6 py-3 bg-gradient-primary text-white font-medium rounded-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    학습 중...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    모델 학습 시작
                  </>
                )}
              </button>
            </div>

            {/* 학습 결과 요약 */}
            {trainingResult && (
              <div className="mt-6 pt-4 border-t border-border">
                <h4 className="font-semibold text-foreground mb-3">학습 결과</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(trainingResult.metrics).map(([metric, value]) => (
                    <div key={metric} className="bg-muted/30 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-foreground">{value.toFixed(3)}</div>
                      <div className="text-xs text-muted-foreground">{metric.toUpperCase()}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 text-sm text-muted-foreground">
                  학습 시간: {trainingResult.trainingTime.toFixed(1)}초
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 시뮬레이션 탭 */}
      {activeTab === 'evaluation' && (
        <div className="space-y-6">
          {!trainingResult ? (
            <div className="bg-card border border-border rounded-lg p-6 text-center">
              <Brain className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold text-foreground mb-2">모델 학습 필요</h3>
              <p className="text-muted-foreground">먼저 모델링 탭에서 모델을 학습해주세요.</p>
            </div>
          ) : (
            <>
              {/* 시뮬레이션 입력 */}
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-foreground flex items-center">
                    <BarChart3 className="w-5 h-5 mr-2 text-accent-orange" />
                    모델 시뮬레이션
                  </h3>
                  
                  {simulationResult && (
                    <span className="text-sm bg-accent-green/20 text-accent-green px-3 py-1 rounded-full">
                      예측 완료
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* 특성 값 입력 */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-foreground mb-4">특성 값 입력</h4>
                    {selectedFeatures.map((feature) => (
                      <div key={feature} className="space-y-2">
                        <label className="text-sm font-medium text-foreground">{feature}</label>
                        <input
                          type="number"
                          step="any"
                          placeholder={`${feature} 값을 입력하세요`}
                          value={simulationInputs[feature] || ''}
                          onChange={(e) => setSimulationInputs(prev => ({
                            ...prev,
                            [feature]: parseFloat(e.target.value) || 0
                          }))}
                          className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-accent-blue focus:border-transparent"
                        />
                      </div>
                    ))}
                  </div>

                  {/* 실제 값 입력 및 시뮬레이션 실행 */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-foreground mb-4">실제 값 및 예측</h4>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-foreground">
                        실제 {preprocessingConfig?.targetColumn} 값
                      </label>
                      <input
                        type="number"
                        step="any"
                        placeholder="비교할 실제 값을 입력하세요"
                        id="actualValue"
                        className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:ring-2 focus:ring-accent-blue focus:border-transparent"
                      />
                    </div>
                    
                    <button
                      onClick={() => {
                        const actualValueInput = document.getElementById('actualValue') as HTMLInputElement
                        const actualValue = parseFloat(actualValueInput.value)
                        if (actualValue) {
                          handleSimulation(actualValue)
                        } else {
                          alert('실제 값을 입력해주세요.')
                        }
                      }}
                      disabled={isLoading || selectedFeatures.length === 0}
                      className="w-full flex items-center justify-center px-6 py-3 bg-accent-orange text-white font-medium rounded-lg hover:scale-105 transition-transform disabled:opacity-50"
                    >
                      {isLoading ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                          예측 중...
                        </>
                      ) : (
                        <>
                          <BarChart3 className="w-5 h-5 mr-2" />
                          예측 시작
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* 시뮬레이션 결과 */}
              {simulationResult && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* 예측 결과 */}
                  <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                      <Award className="w-5 h-5 mr-2 text-accent-green" />
                      예측 결과
                    </h3>
                    
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-accent-blue/10 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-accent-blue mb-2">
                            {simulationResult.predictedValue.toFixed(3)}
                          </div>
                          <div className="text-sm text-muted-foreground">예측값</div>
                        </div>
                        
                        <div className="bg-accent-green/10 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-accent-green mb-2">
                            {simulationResult.actualValue.toFixed(3)}
                          </div>
                          <div className="text-sm text-muted-foreground">실제값</div>
                        </div>
                      </div>

                      <div className="bg-muted/20 rounded-lg p-4">
                        <div className="text-sm font-medium text-foreground mb-3">오차 분석</div>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">절대 오차:</span>
                            <span className="text-foreground font-medium">
                              {simulationResult.difference.toFixed(3)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">백분율 오차:</span>
                            <span className="text-foreground font-medium">
                              {simulationResult.percentageError.toFixed(2)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 오차 시각화 */}
                  <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                      <TrendingUp className="w-5 h-5 mr-2 text-accent-purple" />
                      오차 분석
                    </h3>
                    
                    {/* 오차 바 차트 시뮬레이션 */}
                    <div className="bg-muted/20 rounded-lg p-4 h-64 flex items-center justify-center">
                      <div className="w-full max-w-xs">
                        <div className="text-center mb-4">
                          <div className="text-sm text-muted-foreground">예측 정확도</div>
                          <div className="text-lg font-bold text-foreground">
                            {(100 - simulationResult.percentageError).toFixed(1)}%
                          </div>
                        </div>
                        
                        <div className="w-full h-6 bg-muted rounded-lg overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-accent-green to-accent-blue transition-all duration-1000"
                            style={{ width: `${Math.max(0, 100 - simulationResult.percentageError)}%` }}
                          />
                        </div>
                        
                        <div className="flex justify-between text-xs text-muted-foreground mt-2">
                          <span>0%</span>
                          <span>100%</span>
                        </div>
                      </div>
                    </div>

                    {/* 성능 평가 */}
                    <div className="mt-4 p-3 rounded-lg text-sm text-center">
                      <div className={`font-medium ${
                        simulationResult.percentageError < 5 ? 'text-accent-green bg-accent-green/10' : 
                        simulationResult.percentageError < 15 ? 'text-accent-orange bg-accent-orange/10' : 
                        'text-red-500 bg-red-500/10'
                      } px-3 py-2 rounded-lg`}>
                        {simulationResult.percentageError < 5 ? '매우 정확한 예측' : 
                         simulationResult.percentageError < 15 ? '보통 정확도' : 
                         '낮은 정확도'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* 모델 해석 탭 */}
      {activeTab === 'interpretation' && (
        <div className="space-y-6">
          {!trainingResult ? (
            <div className="bg-card border border-border rounded-lg p-6 text-center">
              <Eye className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold text-foreground mb-2">모델 학습 필요</h3>
              <p className="text-muted-foreground">먼저 모델링 탭에서 모델을 학습해주세요.</p>
            </div>
          ) : (
            <>
              {/* 특성 중요도 */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-accent-green" />
                  특성 중요도 (Feature Importance)
                </h3>
                
                <div className="space-y-3">
                  {Object.entries(trainingResult.featureImportance)
                    .sort(([,a], [,b]) => b - a)
                    .map(([feature, importance], idx) => (
                      <div key={feature} className="flex items-center space-x-3">
                        <div className="w-24 text-right">
                          <span className="text-sm font-medium text-foreground">
                            {feature.length > 10 ? feature.substring(0, 10) + '...' : feature}
                          </span>
                        </div>
                        
                        <div className="flex-1 relative">
                          <div className="w-full h-6 bg-muted rounded-lg overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-accent-green to-accent-blue transition-all duration-500"
                              style={{ width: `${importance * 100}%` }}
                            />
                          </div>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xs font-bold text-foreground">
                              {(importance * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="w-8 text-center">
                          <span className="text-xs text-muted-foreground">#{idx + 1}</span>
                        </div>
                      </div>
                    ))}
                </div>

                <div className="mt-4 p-3 bg-muted/20 rounded-lg">
                  <div className="text-sm font-medium text-foreground mb-2">해석</div>
                  <div className="text-xs text-muted-foreground">
                    특성 중요도가 높을수록 모델의 예측에 더 큰 영향을 미칩니다. 
                    상위 3개 특성이 전체 예측의 대부분을 설명하는 경우가 많습니다.
                  </div>
                </div>
              </div>

              {/* 모델 성능 요약 */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-accent-purple" />
                  모델 성능 요약 리포트
                </h3>
                
                <div className="prose prose-sm max-w-none">
                  <div className="bg-muted/20 rounded-lg p-4 space-y-3">
                    <div>
                      <span className="font-medium text-foreground">모델 유형:</span>
                      <span className="text-muted-foreground ml-2">
                        {modelConfig.modelType} ({modelConfig.taskType === 'regression' ? '회귀' : '분류'})
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-medium text-foreground">데이터 규모:</span>
                      <span className="text-muted-foreground ml-2">
                        훈련 {trainData?.length}행, 테스트 {testData?.length}행, 특성 {selectedFeatures.length}개
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-medium text-foreground">주요 성능 지표:</span>
                      <span className="text-muted-foreground ml-2">
                        {modelConfig.taskType === 'regression' ? (
                          `R² Score: ${trainingResult.metrics.r2_score?.toFixed(3)}, RMSE: ${trainingResult.metrics.rmse?.toFixed(3)}`
                        ) : (
                          `Accuracy: ${(trainingResult.metrics.accuracy * 100).toFixed(1)}%, F1-Score: ${trainingResult.metrics.f1_score?.toFixed(3)}`
                        )}
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-medium text-foreground">가장 중요한 특성:</span>
                      <span className="text-muted-foreground ml-2">
                        {Object.entries(trainingResult.featureImportance)
                          .sort(([,a], [,b]) => b - a)
                          .slice(0, 3)
                          .map(([feature, importance]) => `${feature} (${(importance * 100).toFixed(1)}%)`)
                          .join(', ')
                        }
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-medium text-foreground">권장사항:</span>
                      <span className="text-muted-foreground ml-2">
                        {evaluationResult ? (
                          modelConfig.taskType === 'regression' ? (
                            evaluationResult.testMetrics.r2_score > 0.8 ? 
                              '모델 성능이 우수합니다. 실제 운영에 적용 가능합니다.' :
                              '모델 성능 개선을 위해 더 많은 데이터나 특성 엔지니어링을 고려해보세요.'
                          ) : (
                            evaluationResult.testMetrics.accuracy > 0.85 ?
                              '모델 성능이 우수합니다. 실제 운영에 적용 가능합니다.' :
                              '모델 성능 개선을 위해 하이퍼파라미터 튜닝이나 앙상블 방법을 고려해보세요.'
                          )
                        ) : '먼저 모델 평가를 수행해주세요.'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 모델 저장/내보내기 */}
                <div className="mt-4 pt-4 border-t border-border">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      학습된 모델을 저장하거나 리포트를 내보낼 수 있습니다.
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => alert('모델 저장 기능은 곧 구현됩니다.')}
                        className="flex items-center px-4 py-2 text-sm bg-accent-blue text-white rounded-lg hover:bg-accent-blue/80 transition-colors"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        모델 저장
                      </button>
                      <button
                        onClick={() => alert('리포트 내보내기 기능은 곧 구현됩니다.')}
                        className="flex items-center px-4 py-2 text-sm bg-accent-green text-white rounded-lg hover:bg-accent-green/80 transition-colors"
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        리포트 내보내기
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* 플로팅 챗봇 */}
      <FloatingChatbot
        topic="product_modeling"
        sessionId="product_modeling_session"
        enableStreaming={true}
        simulationParams={{
          activeTab,
          hasTrainData: !!trainData,
          hasTestData: !!testData,
          modelType: modelConfig.modelType,
          taskType: modelConfig.taskType,
          isModelTrained: !!trainingResult,
          isModelEvaluated: !!evaluationResult,
          selectedFeatures: selectedFeatures.length,
          targetColumn: preprocessingConfig?.targetColumn
        }}
        position="bottom-right"
        theme="dark"
        accentColor="purple"
        minimizedText="AI 모델링 전문가"
        placeholder="모델링에 대해 질문하세요..."
        maxHeight={800}
        width={600}
        showSessionInfo={false}
      />
    </div>
  )
} 