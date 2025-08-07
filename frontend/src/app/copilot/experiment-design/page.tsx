'use client'

import React, { useState, useEffect } from 'react'
import { RangeSlider, Select, NumberInput, Checkbox, RadioGroup, TabNavigation, Slider } from '@/components/ui'
import { 
  Beaker, 
  Settings, 
  Target, 
  CheckCircle, 
  TrendingUp, 
  Activity, 
  Download,
  AlertCircle,
  BarChart3,
  FileText,
  Zap,
  RefreshCw,
  Lightbulb,
  BookOpen
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { useExperimentDesign } from '@/hooks/useExperimentDesign'
import { FloatingChatbot } from '@/components/FloatingChatbot'
import MarkdownRenderer from '@/components/MarkdownRenderer'

// StatusCard 컴포넌트
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

// 실험 설계 탭 컴포넌트
interface ExperimentDesignTabProps {
  experimentTypes: any[]
  parameters: any
  onGenerateExperimentPlan: (params: any) => void
  experimentPlan: any
  loading: boolean
  error: string | null
}

function ExperimentDesignTab({ 
  experimentTypes, 
  parameters, 
  onGenerateExperimentPlan, 
  experimentPlan, 
  loading, 
  error 
}: ExperimentDesignTabProps) {
  const { t } = useTranslation()
  const [experimentParams, setExperimentParams] = useState({
    experiment_type: 'Full Factorial',
    factors: ['온도', '압력', 'pH'],
    num_runs: 25,
    replications: 2,
    target_purity: 97.5,
    target_yield: 92.0,
    optimization_goal: '순도 최대화'
  })

  const [showAllResults, setShowAllResults] = useState(false)

  const availableFactors = Object.keys(parameters)

  const handleParameterChange = (field: string, value: any) => {
    setExperimentParams(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleFactorToggle = (factor: string) => {
    setExperimentParams(prev => ({
      ...prev,
      factors: prev.factors.includes(factor)
        ? prev.factors.filter(f => f !== factor)
        : [...prev.factors, factor]
    }))
  }

  const handleGenerateExperiment = () => {
    onGenerateExperimentPlan(experimentParams)
  }

  return (
    <div className="space-y-6">
      <div className="grid lg:grid-cols-3 gap-6">
        {/* 실험 파라미터 설정 */}
        <div className="lg:col-span-2">
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
              <Settings className="w-5 h-5 mr-2 text-accent-orange" />
              {t('dashboard.experimentDesign.experimentTab.parameterSettings')}
            </h3>
            
            <div className="space-y-6">
              {/* DoE 설정 */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.experimentTab.doeSettings')}</h4>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Select
                      value={(() => {
                        switch (experimentParams.experiment_type) {
                          case 'Full Factorial': return t('dashboard.experimentDesign.experimentTab.experimentTypes.fullFactorial')
                          case 'Fractional Factorial': return t('dashboard.experimentDesign.experimentTab.experimentTypes.fractionalFactorial')
                          case 'Central Composite': return t('dashboard.experimentDesign.experimentTab.experimentTypes.centralComposite')
                          case 'Box-Behnken': return t('dashboard.experimentDesign.experimentTab.experimentTypes.boxBehnken')
                          default: return experimentParams.experiment_type
                        }
                      })()}
                      onChange={(value) => {
                        // Find the original key for the selected translated value
                        const types = ['Full Factorial', 'Fractional Factorial', 'Central Composite', 'Box-Behnken']
                        const getTypeKey = (translatedValue: string) => {
                          return types.find(type => {
                            switch (type) {
                              case 'Full Factorial': return t('dashboard.experimentDesign.experimentTab.experimentTypes.fullFactorial') === translatedValue
                              case 'Fractional Factorial': return t('dashboard.experimentDesign.experimentTab.experimentTypes.fractionalFactorial') === translatedValue
                              case 'Central Composite': return t('dashboard.experimentDesign.experimentTab.experimentTypes.centralComposite') === translatedValue
                              case 'Box-Behnken': return t('dashboard.experimentDesign.experimentTab.experimentTypes.boxBehnken') === translatedValue
                              default: return false
                            }
                          }) || value
                        }
                        handleParameterChange('experiment_type', getTypeKey(value))
                      }}
                      options={[
                        t('dashboard.experimentDesign.experimentTab.experimentTypes.fullFactorial'),
                        t('dashboard.experimentDesign.experimentTab.experimentTypes.fractionalFactorial'),
                        t('dashboard.experimentDesign.experimentTab.experimentTypes.centralComposite'),
                        t('dashboard.experimentDesign.experimentTab.experimentTypes.boxBehnken')
                      ]}
                      label={t('dashboard.experimentDesign.experimentTab.parameters.experimentType')}
                    />
                  </div>
                  
                  <NumberInput
                    value={experimentParams.num_runs}
                    onChange={(value) => handleParameterChange('num_runs', value)}
                    min={10}
                    max={100}
                    step={1}
                    label={t('dashboard.experimentDesign.experimentTab.parameters.numberOfRuns')}
                    unit="회"
                  />
                  
                  <NumberInput
                    value={experimentParams.replications}
                    onChange={(value) => handleParameterChange('replications', value)}
                    min={1}
                    max={5}
                    step={1}
                    label={t('dashboard.experimentDesign.experimentTab.parameters.replications')}
                    unit="회"
                  />
                  
                  <div>
                                          <Select
                        value={(() => {
                          switch (experimentParams.optimization_goal) {
                            case '순도 최대화': return t('dashboard.experimentDesign.experimentTab.goals.purityMaximization')
                            case '수율 최대화': return t('dashboard.experimentDesign.experimentTab.goals.yieldMaximization')
                            case '비용 최소화': return t('dashboard.experimentDesign.experimentTab.goals.costMinimization')
                            case '시간 최소화': return t('dashboard.experimentDesign.experimentTab.goals.timeMinimization')
                            default: return experimentParams.optimization_goal
                          }
                        })()}
                        onChange={(value) => {
                          // Find the original key for the selected translated value
                          const goals = ['순도 최대화', '수율 최대화', '비용 최소화', '시간 최소화']
                          const getGoalKey = (translatedValue: string) => {
                            return goals.find(goal => {
                              switch (goal) {
                                case '순도 최대화': return t('dashboard.experimentDesign.experimentTab.goals.purityMaximization') === translatedValue
                                case '수율 최대화': return t('dashboard.experimentDesign.experimentTab.goals.yieldMaximization') === translatedValue
                                case '비용 최소화': return t('dashboard.experimentDesign.experimentTab.goals.costMinimization') === translatedValue
                                case '시간 최소화': return t('dashboard.experimentDesign.experimentTab.goals.timeMinimization') === translatedValue
                                default: return false
                              }
                            }) || value
                          }
                          handleParameterChange('optimization_goal', getGoalKey(value))
                        }}
                        options={[
                          t('dashboard.experimentDesign.experimentTab.goals.purityMaximization'),
                          t('dashboard.experimentDesign.experimentTab.goals.yieldMaximization'),
                          t('dashboard.experimentDesign.experimentTab.goals.costMinimization'),
                          t('dashboard.experimentDesign.experimentTab.goals.timeMinimization')
                        ]}
                        label={t('dashboard.experimentDesign.experimentTab.parameters.optimizationGoal')}
                      />
                  </div>
                </div>
              </div>

              {/* 실험 인자 선택 */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.experimentTab.factorSelectionTitle')}</h4>
                <div className="grid md:grid-cols-3 gap-3">
                  {availableFactors.map(factor => (
                    <Checkbox
                      key={factor}
                      checked={experimentParams.factors.includes(factor)}
                      onChange={() => handleFactorToggle(factor)}
                      label={factor}
                    />
                  ))}
                </div>
              </div>

              {/* 목표 설정 */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.experimentTab.targetSettingsTitle')}</h4>
                <div className="grid md:grid-cols-2 gap-4">
                  <Slider
                    min={95}
                    max={99}
                    step={0.1}
                    value={experimentParams.target_purity}
                    onChange={(value) => handleParameterChange('target_purity', value)}
                    label={t('dashboard.experimentDesign.experimentTab.parameters.targetPurity')}
                    unit="%"
                  />
                  
                  <Slider
                    min={85}
                    max={98}
                    step={0.1}
                    value={experimentParams.target_yield}
                    onChange={(value) => handleParameterChange('target_yield', value)}
                    label={t('dashboard.experimentDesign.experimentTab.parameters.targetYield')}
                    unit="%"
                  />
                </div>
              </div>

              {/* 실험 계획 생성 버튼 */}
              <button
                onClick={handleGenerateExperiment}
                disabled={loading || experimentParams.factors.length < 2}
                className="w-full bg-gradient-primary text-white py-3 px-6 rounded-lg font-medium hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    {t('dashboard.experimentDesign.experimentTab.buttons.generating')}
                  </>
                ) : (
                  <>
                    <Beaker className="w-4 h-4 mr-2" />
                    {t('dashboard.experimentDesign.experimentTab.buttons.generateExperimentPlan')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 실험 설계 가이드 */}
        <div className="space-y-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center">
              <BookOpen className="w-5 h-5 mr-2 text-accent-purple" />
              {t('dashboard.experimentDesign.experimentTab.experimentPlanSummary')}
            </h3>
            
            {experimentPlan ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">실험 유형</span>
                  <span className="text-sm font-medium">{experimentPlan.metadata?.experiment_type || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">실험 횟수</span>
                  <span className="text-sm font-medium">{experimentPlan.metadata?.num_runs || 0}회</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">인자 수</span>
                  <span className="text-sm font-medium">{experimentPlan.metadata?.factors?.length || 0}개</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">목표 순도</span>
                  <span className="text-sm font-medium">{experimentPlan.metadata?.target_purity || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">목표 수율</span>
                  <span className="text-sm font-medium">{experimentPlan.metadata?.target_yield || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">설계 효율성</span>
                  <span className="text-sm font-medium">{experimentPlan.metadata?.design_efficiency || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">검정력</span>
                  <span className="text-sm font-medium">{experimentPlan.metadata?.power_analysis?.statistical_power || 0}</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">실험 계획을 생성하면 여기에 요약이 표시됩니다.</p>
            )}
          </div>

          {/* 실험 설계 방법론 가이드 */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center">
              <Lightbulb className="w-5 h-5 mr-2 text-accent-green" />
              {t('dashboard.experimentDesign.experimentTab.methodologyGuideTitle')}
            </h3>
            
            <div className="space-y-3 text-sm">
              <div>
                <strong>Full Factorial:</strong> 모든 인자 조합을 실험하여 완전한 정보 확보
              </div>
              <div>
                <strong>Fractional Factorial:</strong> 실험 횟수를 줄인 효율적인 스크리닝
              </div>
              <div>
                <strong>Central Composite:</strong> 2차 곡선 모델링이 가능한 RSM 설계
              </div>
              <div>
                <strong>Box-Behnken:</strong> 안전한 3수준 설계로 극단조건 회피
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* 실험 계획 결과 */}
      {experimentPlan && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-accent-blue" />
            {t('dashboard.experimentDesign.common.experimentPlanResults')}
          </h3>
          
          {/* 실험 계획 분석 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatusCard
              title={t('dashboard.experimentDesign.experimentTab.status.totalExperiments')}
              value={`${experimentPlan.metadata?.num_runs || 0}${t('dashboard.experimentDesign.common.times')}`}
              icon={<Beaker className="w-6 h-6 text-white" />}
              color="#3b82f6"
            />
            <StatusCard
              title={t('dashboard.experimentDesign.experimentTab.status.factorsAnalyzed')}
              value={`${experimentPlan.metadata?.factors?.length || 0}${t('dashboard.experimentDesign.common.count')}`}
              icon={<Settings className="w-6 h-6 text-white" />}
              color="#f97316"
            />
            <StatusCard
              title={t('dashboard.experimentDesign.experimentTab.status.designEfficiency')}
              value={`${experimentPlan.metadata?.design_efficiency || 0}%`}
              icon={<TrendingUp className="w-6 h-6 text-white" />}
              color="#22c55e"
              trend={`${experimentPlan.metadata?.design_efficiency >= 80 ? t('dashboard.experimentDesign.common.status.excellent') : experimentPlan.metadata?.design_efficiency >= 60 ? t('dashboard.experimentDesign.common.status.good') : t('dashboard.experimentDesign.common.status.needsImprovement')}`}
            />
            <StatusCard
              title={t('dashboard.experimentDesign.experimentTab.status.statisticalPower')}
              value={(experimentPlan.metadata?.power_analysis?.statistical_power || 0).toFixed(3)}
              icon={<Target className="w-6 h-6 text-white" />}
              color="#8b5cf6"
              trend={`${(experimentPlan.metadata?.power_analysis?.statistical_power || 0) >= 0.8 ? t('dashboard.experimentDesign.common.status.sufficient') : t('dashboard.experimentDesign.common.status.moderate')}`}
            />
          </div>

          {/* 분석 결과 및 권장사항 */}
          {experimentPlan.analysis && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold text-foreground mb-3">{t('dashboard.experimentDesign.common.analysisResults')}</h4>
              {experimentPlan.analysis.recommendations && (
                <div className="space-y-2">
                  {experimentPlan.analysis.recommendations.map((rec: string, index: number) => (
                    <div key={index} className="flex items-start">
                      <Lightbulb className="w-4 h-4 text-accent-orange mt-0.5 mr-2 flex-shrink-0" />
                      <span className="text-sm text-muted-foreground">{rec}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gradient-to-r from-muted/80 to-muted/50">
                  <tr>
                    <th className="px-3 py-3 text-center text-sm font-semibold text-foreground border-b border-border">
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center">
                          <span className="text-xs font-bold text-primary">#</span>
                        </div>
                        <span>{t('dashboard.experimentDesign.common.run')}</span>
                      </div>
                    </th>
                    {experimentPlan.metadata?.factors?.map((factor: string) => (
                      <th key={factor} className="px-3 py-3 text-center text-sm font-semibold text-foreground border-b border-border">
                        <div className="flex items-center justify-center space-x-2">
                          <Settings className="w-4 h-4 text-accent-orange" />
                          <span>{factor}</span>
                          <span className="text-xs text-muted-foreground">
                            ({parameters[factor]?.unit || ''})
                          </span>
                        </div>
                      </th>
                    ))}
                    <th className="px-3 py-3 text-center text-sm font-semibold text-foreground border-b border-border">
                      <div className="flex items-center justify-center space-x-2">
                        <TrendingUp className="w-4 h-4 text-accent-green" />
                        <span>예상순도</span>
                        <span className="text-xs text-muted-foreground">(%)</span>
                      </div>
                    </th>
                    <th className="px-3 py-3 text-center text-sm font-semibold text-foreground border-b border-border">
                      <div className="flex items-center justify-center space-x-2">
                        <BarChart3 className="w-4 h-4 text-accent-blue" />
                        <span>예상수율</span>
                        <span className="text-xs text-muted-foreground">(%)</span>
                      </div>
                    </th>
                  </tr>
                </thead>
                                 <tbody className="divide-y divide-border">
                   {(experimentPlan.experiment_plan || []).slice(0, showAllResults ? undefined : 10).map((run: any, index: number) => (
                     <tr 
                       key={index}
                       className={`hover:bg-muted/30 transition-colors duration-150 ${
                         index % 2 === 0 ? 'bg-background' : 'bg-muted/10'
                       }`}
                     >
                       <td className="px-3 py-2 text-center">
                         <div className="flex items-center justify-center space-x-2">
                           <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center">
                             <span className="text-xs font-medium text-primary">{run.Run || index + 1}</span>
                           </div>
                         </div>
                       </td>
                      {experimentPlan.metadata?.factors?.map((factor: string) => {
                        // 가능한 모든 컬럼 이름 패턴을 시도
                        const possibleKeys = [
                          `${factor}(${parameters[factor]?.unit || ''})`,
                          `${factor}()`,
                          factor,
                          `${factor}(°C)`,
                          `${factor}(bar)`,
                          `${factor}(min)`,
                          `${factor}(M)`,
                          `${factor}(rpm)`
                        ];
                        
                        let value = 'N/A';
                        for (const key of possibleKeys) {
                          if (run[key] !== undefined) {
                            value = run[key];
                            break;
                          }
                        }
                        
                                                 return (
                           <td key={factor} className="px-3 py-2 text-center">
                             <div className="flex items-center justify-center">
                               <span className="text-sm font-medium text-foreground">
                                 {value !== 'N/A' ? value : (
                                   <span className="text-muted-foreground italic">N/A</span>
                                 )}
                               </span>
                             </div>
                           </td>
                         );
                       })}
                       <td className="px-3 py-2 text-center">
                         <div className="flex items-center justify-center space-x-2">
                           {run['예상순도(%)'] !== 'N/A' && run['예상순도(%)'] ? (
                             <>
                               <div className={`w-2 h-2 rounded-full ${
                                 parseFloat(run['예상순도(%)']) >= 98 ? 'bg-green-500' :
                                 parseFloat(run['예상순도(%)']) >= 96 ? 'bg-yellow-500' : 'bg-red-500'
                               }`}></div>
                               <span className="text-sm font-medium text-foreground">
                                 {run['예상순도(%)']}%
                               </span>
                             </>
                           ) : (
                             <span className="text-sm text-muted-foreground italic">N/A</span>
                           )}
                         </div>
                       </td>
                       <td className="px-3 py-2 text-center">
                         <div className="flex items-center justify-center space-x-2">
                           {run['예상수율(%)'] !== 'N/A' && run['예상수율(%)'] ? (
                             <>
                               <div className={`w-2 h-2 rounded-full ${
                                 parseFloat(run['예상수율(%)']) >= 95 ? 'bg-green-500' :
                                 parseFloat(run['예상수율(%)']) >= 90 ? 'bg-yellow-500' : 'bg-red-500'
                               }`}></div>
                               <span className="text-sm font-medium text-foreground">
                                 {run['예상수율(%)']}%
                               </span>
                             </>
                           ) : (
                             <span className="text-sm text-muted-foreground italic">N/A</span>
                           )}
                         </div>
                       </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
                    {(experimentPlan.experiment_plan || []).length > 10 && (
            <div className="mt-4 px-4 py-3 bg-muted/30 rounded-lg flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-accent-orange" />
                <span className="text-sm text-muted-foreground">
                  {showAllResults 
                    ? `전체 ${experimentPlan.experiment_plan.length}개 실험을 표시하고 있습니다.`
                    : `처음 10개 실험만 표시됩니다. 전체 ${experimentPlan.experiment_plan.length}개 실험`
                  }
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {!showAllResults && (
                  <span className="text-xs text-muted-foreground">
                    {(experimentPlan.experiment_plan || []).length - 10}개 더 보기
                  </span>
                )}
                <button 
                  onClick={() => setShowAllResults(!showAllResults)}
                  className="text-xs text-primary hover:underline"
                >
                  {showAllResults ? t('dashboard.experimentDesign.experimentTab.buttons.collapse') : t('dashboard.experimentDesign.experimentTab.buttons.showAll')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}





// 최적화 탭 컴포넌트
interface OptimizationTabProps {
  experimentPlan: any
  parameters: any
  onRunOptimization: (params: any) => void
  optimizationResult: any
  loading: boolean
  error: string | null
}

function OptimizationTab({
  experimentPlan,
  parameters,
  onRunOptimization,
  optimizationResult,
  loading,
  error
}: OptimizationTabProps) {
    const { t } = useTranslation()
  const [optimizationParams, setOptimizationParams] = useState({
    objectives: ['순도 최대화', '수율 최대화'],
    constraints: {} as Record<string, { min: number; max: number }>,
    optimizer: 'Gaussian Process',
    max_iterations: 50,
    acquisition_function: 'Expected Improvement'
  })

  const [enabledConstraints, setEnabledConstraints] = useState<Record<string, boolean>>({})

  // 실험 계획에서 설정한 인자들을 기반으로 제약조건 초기화
  useEffect(() => {
    if (experimentPlan?.metadata?.factors) {
      const factors = experimentPlan.metadata.factors
      const initialConstraints: Record<string, { min: number; max: number }> = {}
      const initialEnabled: Record<string, boolean> = {}

      factors.forEach((factor: string) => {
        const paramInfo = parameters[factor]
        if (paramInfo) {
          initialConstraints[factor.toLowerCase().replace(' ', '_')] = {
            min: paramInfo.min_value,
            max: paramInfo.max_value
          }
          initialEnabled[factor] = true
        }
      })

      setOptimizationParams(prev => ({
        ...prev,
        constraints: initialConstraints
      }))
      setEnabledConstraints(initialEnabled)
    }
  }, [experimentPlan, parameters])

  const handleConstraintToggle = (factor: string) => {
    setEnabledConstraints(prev => ({
      ...prev,
      [factor]: !prev[factor]
    }))
  }

  const handleConstraintChange = (factor: string, range: [number, number]) => {
    const constraintKey = factor.toLowerCase().replace(' ', '_')
    
    setOptimizationParams(prev => ({
      ...prev,
      constraints: {
        ...prev.constraints,
        [constraintKey]: {
          min: range[0],
          max: range[1]
        }
      }
    }))
  }

  const handleRunOptimization = () => {
    // 활성화된 제약조건만 전송
    const activeConstraints: Record<string, { min: number; max: number }> = {}
    Object.entries(enabledConstraints).forEach(([factor, enabled]) => {
      if (enabled) {
        const constraintKey = factor.toLowerCase().replace(' ', '_')
        if (optimizationParams.constraints[constraintKey]) {
          activeConstraints[constraintKey] = optimizationParams.constraints[constraintKey]
        }
      }
    })

    onRunOptimization({
      ...optimizationParams,
      constraints: activeConstraints
    })
  }

  // Get translated labels for options
  const getOptimizerLabel = (optimizer: string) => {
    switch (optimizer) {
      case 'Gaussian Process': return t('dashboard.experimentDesign.optimizationTab.algorithms.gaussianProcess')
      case 'Tree-structured Parzen Estimator': return t('dashboard.experimentDesign.optimizationTab.algorithms.tpe')
      case 'Random Search': return t('dashboard.experimentDesign.optimizationTab.algorithms.randomSearch')
      default: return optimizer
    }
  }

  const getAcquisitionFunctionLabel = (func: string) => {
    switch (func) {
      case 'Expected Improvement': return t('dashboard.experimentDesign.optimizationTab.acquisitionFunctions.expectedImprovement')
      case 'Upper Confidence Bound': return t('dashboard.experimentDesign.optimizationTab.acquisitionFunctions.upperConfidenceBound')
      case 'Probability of Improvement': return t('dashboard.experimentDesign.optimizationTab.acquisitionFunctions.probabilityOfImprovement')
      default: return func
    }
  }

  const optimizers = ['Gaussian Process', 'Tree-structured Parzen Estimator', 'Random Search']
  const acquisitionFunctions = ['Expected Improvement', 'Upper Confidence Bound', 'Probability of Improvement']

  return (
    <div className="space-y-6">
      {!experimentPlan && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-yellow-500 mr-2" />
          <span className="text-yellow-700">{t('dashboard.experimentDesign.optimizationTab.warnings.generateExperimentFirst')}</span>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* 최적화 설정 */}
        <div className="lg:col-span-2">
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
              <Zap className="w-5 h-5 mr-2 text-accent-orange" />
              {t('dashboard.experimentDesign.optimizationTab.settings')}
            </h3>

            <div className="space-y-6">
              {/* 목표 함수 설정 */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.optimizationTab.objectiveFunctionTitle')}</h4>
                <div className="grid md:grid-cols-2 gap-3">
                  {['순도 최대화', '수율 최대화', '비용 최소화', '시간 최소화'].map(objective => {
          const getGoalLabel = (goal: string) => {
            switch (goal) {
              case '순도 최대화': return t('dashboard.experimentDesign.experimentTab.goals.purityMaximization')
              case '수율 최대화': return t('dashboard.experimentDesign.experimentTab.goals.yieldMaximization')
              case '비용 최소화': return t('dashboard.experimentDesign.experimentTab.goals.costMinimization')
              case '시간 최소화': return t('dashboard.experimentDesign.experimentTab.goals.timeMinimization')
              default: return goal
            }
          }
          return (
                    <Checkbox
                      key={objective}
                      checked={optimizationParams.objectives.includes(objective)}
                      onChange={(checked) => {
                        if (checked) {
                          setOptimizationParams(prev => ({
                            ...prev,
                            objectives: [...prev.objectives, objective]
                          }))
                        } else {
                          setOptimizationParams(prev => ({
                            ...prev,
                            objectives: prev.objectives.filter(obj => obj !== objective)
                          }))
                        }
                      }}
                      label={getGoalLabel(objective)}
                    />
                  )
                  })}
                </div>
              </div>

              {/* 제약 조건 */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.optimizationTab.constraintsTitle')}</h4>
                {experimentPlan?.metadata?.factors ? (
                  <div className="grid md:grid-cols-2 gap-4">
                    {experimentPlan.metadata.factors.map((factor: string) => (
                      <div key={factor} className="border border-border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <Checkbox
                            checked={enabledConstraints[factor] || false}
                            onChange={() => handleConstraintToggle(factor)}
                            label={factor}
                          />
                          <span className="text-sm text-muted-foreground">
                            {parameters[factor]?.unit || ''}
                          </span>
                        </div>
                        
                        {enabledConstraints[factor] && (
                          <div className="mt-3">
                            <RangeSlider
                              min={parameters[factor]?.min_value || 0}
                              max={parameters[factor]?.max_value || 100}
                              step={factor === '촉매농도' ? 0.1 : factor === '압력' ? 0.1 : 1}
                              value={[
                                optimizationParams.constraints[factor.toLowerCase().replace(' ', '_')]?.min || parameters[factor]?.min_value || 0,
                                optimizationParams.constraints[factor.toLowerCase().replace(' ', '_')]?.max || parameters[factor]?.max_value || 100
                              ]}
                              onChange={(range) => handleConstraintChange(factor, range)}
                              label={`${factor} ${t('experimentDesign.common.range')}`}
                              unit={parameters[factor]?.unit || ''}
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {t('dashboard.experimentDesign.optimizationTab.constraintAutoSetting')}
                  </p>
                )}
              </div>

              {/* 알고리즘 설정 */}
              <div className="bg-muted/50 rounded-lg p-4">
                <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.optimizationTab.algorithmSettingsTitle')}</h4>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Select
                      value={getOptimizerLabel(optimizationParams.optimizer)}
                      onChange={(value) => {
                        // Find the original key for the selected translated value
                        const originalKey = optimizers.find(opt => getOptimizerLabel(opt) === value) || value
                        setOptimizationParams(prev => ({
                          ...prev,
                          optimizer: originalKey
                        }))
                      }}
                      options={optimizers.map(opt => getOptimizerLabel(opt))}
                      label={t('dashboard.experimentDesign.optimizationTab.parameters.optimizer')}
                    />
                  </div>

                  <div>
                                        <Select
                      value={getAcquisitionFunctionLabel(optimizationParams.acquisition_function)}
                      onChange={(value) => {
                        // Find the original key for the selected translated value
                        const originalKey = acquisitionFunctions.find(func => getAcquisitionFunctionLabel(func) === value) || value
                        setOptimizationParams(prev => ({
                          ...prev,
                          acquisition_function: originalKey
                        }))
                      }}
                      options={acquisitionFunctions.map(func => getAcquisitionFunctionLabel(func))}
                      label={t('dashboard.experimentDesign.optimizationTab.parameters.acquisitionFunction')}
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium mb-2">{t('dashboard.experimentDesign.optimizationTab.maxIterationsLabel')}</label>
                    <input
                      type="range"
                      min="10"
                      max="100"
                      value={optimizationParams.max_iterations}
                      onChange={(e) => setOptimizationParams(prev => ({
                        ...prev,
                        max_iterations: parseInt(e.target.value)
                      }))}
                      className="w-full"
                    />
                    <div className="text-sm text-muted-foreground">{optimizationParams.max_iterations}회</div>
                  </div>
                </div>
              </div>

              {/* 최적화 실행 버튼 */}
              <button
                onClick={handleRunOptimization}
                disabled={loading || !experimentPlan || optimizationParams.objectives.length === 0}
                className="w-full bg-gradient-primary text-white py-3 px-6 rounded-lg font-medium hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    {t('dashboard.experimentDesign.optimizationTab.buttons.running')}
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    {t('dashboard.experimentDesign.optimizationTab.buttons.runOptimization')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 최적화 가이드 */}
        <div className="space-y-4">
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center">
              <Target className="w-5 h-5 mr-2 text-accent-purple" />
              {t('dashboard.experimentDesign.optimizationTab.optimizationGuideTitle')}
            </h3>

            {optimizationResult ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">{t('dashboard.experimentDesign.optimizationTab.results.convergenceRate')}</span>
                  <span className="text-sm font-medium">{optimizationResult.convergence_info?.convergence_rate || 0}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">{t('dashboard.experimentDesign.optimizationTab.results.iterationsUsed')}</span>
                  <span className="text-sm font-medium">{optimizationResult.convergence_info?.iterations_used || 0}{t('experimentDesign.common.times')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">{t('dashboard.experimentDesign.optimizationTab.results.improvementRate')}</span>
                  <span className="text-sm font-medium">{optimizationResult.improvement_rate || 0}%</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t('dashboard.experimentDesign.optimizationTab.results.afterExecution')}</p>
            )}
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center">
              <Lightbulb className="w-5 h-5 mr-2 text-accent-green" />
              {t('dashboard.experimentDesign.optimizationTab.methodologyTitle')}
            </h3>

            <div className="space-y-3 text-sm">
              <div>
                <strong>{t('dashboard.experimentDesign.optimizationTab.guide.gaussianProcess.title')}:</strong> {t('dashboard.experimentDesign.optimizationTab.guide.gaussianProcess.features').split('\\n')[0]}
              </div>
              <div>
                <strong>{t('dashboard.experimentDesign.optimizationTab.guide.tpe.title')}:</strong> {t('dashboard.experimentDesign.optimizationTab.guide.tpe.features').split('\\n')[0]}
              </div>
              <div>
                <strong>Random Search:</strong> {t('dashboard.experimentDesign.optimizationTab.algorithms.randomSearch')}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* 최적화 결과 */}
      {optimizationResult && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-accent-blue" />
            {t('dashboard.experimentDesign.optimizationTab.results.title')}
          </h3>

          <div className="grid md:grid-cols-2 gap-6">
            {/* 최적 조건 */}
            <div>
              <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.optimizationTab.results.optimalConditions')}</h4>
              <div className="space-y-2">
                                 {Object.entries(optimizationResult.optimal_parameters || {}).map(([param, value]) => (
                   <div key={param} className="flex justify-between items-center p-2 bg-muted/50 rounded">
                     <span className="text-sm font-medium">{param}</span>
                     <span className="text-sm">{String(value)}</span>
                   </div>
                 ))}
               </div>
             </div>

             {/* 예측 성능 */}
             <div>
               <h4 className="font-semibold mb-3">{t('dashboard.experimentDesign.optimizationTab.results.predictedPerformance')}</h4>
               <div className="space-y-2">
                 {Object.entries(optimizationResult.predicted_performance || {}).map(([metric, value]) => {
                   let displayValue = String(value);
                   
                   // 값에 따라 포맷팅
                   if (metric.includes('순도') || metric.includes('수율')) {
                     displayValue = `${value}%`;
                   } else if (metric.includes('비용')) {
                     displayValue = `₩${Number(value).toLocaleString()}`;
                   } else if (metric.includes('시간')) {
                     displayValue = `${value}분`;
                   }
                   
                   return (
                     <div key={metric} className="flex justify-between items-center p-2 bg-muted/50 rounded">
                       <span className="text-sm font-medium">{metric}</span>
                       <span className="text-sm">{displayValue}</span>
                     </div>
                   );
                 })}
              </div>
            </div>
          </div>

          {/* 개선 정보 */}
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center">
              <TrendingUp className="w-5 h-5 text-green-500 mr-2" />
              <span className="font-medium text-green-700">
                {t('dashboard.experimentDesign.optimizationTab.results.improvementRate')}: {optimizationResult.improvement_rate || 0}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// 보고서 탭 컴포넌트
interface ReportTabProps {
  experimentPlan: any
  optimizationResult: any
  onGenerateReport: (params: any) => void
  generatedReport: any
  onDownloadReport: (reportType: string, content: string) => void
  loading: boolean
  error: string | null
}

function ReportTab({
  experimentPlan,
  optimizationResult,
  onGenerateReport,
  generatedReport,
  onDownloadReport,
  loading,
  error
}: ReportTabProps) {
  const { t } = useTranslation()
  const [reportSettings, setReportSettings] = useState({
    report_type: '실험 계획 요약',
    include_sections: ['실행 요약', '실험 설계', '최적화 결과'],
    report_length: '표준 (3-5페이지)',
    experiment_data: null,
    optimization_data: null
  })



  const reportTypes = ['실험 계획 요약', '최적화 결과', 'DoE 분석', '종합 보고서']
  const availableSections = ['실행 요약', '실험 설계', '최적화 결과', '결과 해석', '개선 제안', '다음 단계']
  const reportLengths = ['간단 (1-2페이지)', '표준 (3-5페이지)', '상세 (5-10페이지)']

  const handleSectionToggle = (section: string) => {
    setReportSettings(prev => ({
      ...prev,
      include_sections: prev.include_sections.includes(section)
        ? prev.include_sections.filter(s => s !== section)
        : [...prev.include_sections, section]
    }))
  }

  const handleGenerateReport = () => {
    const reportData = {
      ...reportSettings,
      experiment_data: experimentPlan?.metadata || null,
      optimization_data: optimizationResult ? {
        optimal_parameters: optimizationResult.optimal_parameters,
        predicted_performance: optimizationResult.predicted_performance,
        improvement_rate: optimizationResult.improvement_rate,
        convergence_info: optimizationResult.convergence_info
      } : null
    }

    onGenerateReport(reportData)
  }

  const handleDownloadReport = () => {
    if (generatedReport?.content) {
      onDownloadReport(reportSettings.report_type, generatedReport.content)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid lg:grid-cols-3 gap-4">
        {/* 보고서 설정 */}
        <div className="lg:col-span-2">
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-lg font-bold text-foreground mb-3 flex items-center">
              <FileText className="w-5 h-5 mr-2 text-accent-purple" />
              {t('dashboard.experimentDesign.reportTab.title')}
            </h3>

            <div className="space-y-4">
              {/* 보고서 유형 */}
              <div className="bg-muted/50 rounded-lg p-3">
                <h4 className="font-medium mb-2">{t('dashboard.experimentDesign.reportTab.reportTypeTitle')}</h4>
                <div className="grid md:grid-cols-2 gap-3">
                  {reportTypes.map(type => (
                    <label key={type} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="radio"
                        name="report_type"
                        value={type}
                        checked={reportSettings.report_type === type}
                        onChange={(e) => setReportSettings(prev => ({
                          ...prev,
                          report_type: e.target.value
                        }))}
                        className="rounded"
                      />
                      <span className="text-sm">{type}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* 포함할 섹션 */}
              <div className="bg-muted/50 rounded-lg p-3">
                <h4 className="font-medium mb-2">{t('dashboard.experimentDesign.reportTab.includeSectionsTitle')}</h4>
                <div className="grid md:grid-cols-2 gap-3">
                  {availableSections.map(section => (
                    <Checkbox
                      key={section}
                      checked={reportSettings.include_sections.includes(section)}
                      onChange={() => handleSectionToggle(section)}
                      label={section}
                    />
                  ))}
                </div>
              </div>

              {/* 보고서 길이 */}
              <div className="bg-muted/50 rounded-lg p-3">
                <h4 className="font-medium mb-2">{t('dashboard.experimentDesign.reportTab.reportLengthTitle')}</h4>
                <RadioGroup
                  value={reportSettings.report_length}
                  onChange={(value) => setReportSettings(prev => ({
                    ...prev,
                    report_length: value
                  }))}
                  name="report_length"
                  options={reportLengths.map(length => ({ value: length, label: length }))}
                />
              </div>

              {/* 데이터 포함 정보 */}
              <div className="bg-muted/50 rounded-lg p-3">
                <h4 className="font-medium mb-2">{t('dashboard.experimentDesign.reportTab.dataInclusionTitle')}</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">실험 계획 데이터</span>
                    <span className={`text-sm font-medium ${experimentPlan ? 'text-green-600' : 'text-red-600'}`}>
                      {experimentPlan ? '포함됨' : '없음'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">최적화 결과</span>
                    <span className={`text-sm font-medium ${optimizationResult ? 'text-green-600' : 'text-red-600'}`}>
                      {optimizationResult ? '포함됨' : '없음'}
                    </span>
                  </div>
                </div>
              </div>

              {/* 보고서 생성 버튼 */}
              <button
                onClick={handleGenerateReport}
                disabled={loading || reportSettings.include_sections.length === 0}
                className="w-full bg-gradient-primary text-white py-2 px-4 rounded-lg font-medium hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    {t('dashboard.experimentDesign.reportTab.buttons.generating')}
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    {t('dashboard.experimentDesign.reportTab.buttons.generate')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 보고서 가이드 */}
        <div className="space-y-3">
          <div className="bg-card border border-border rounded-lg p-3">
            <h3 className="text-base font-bold text-foreground mb-2 flex items-center">
              <BookOpen className="w-5 h-5 mr-2 text-accent-purple" />
              {t('dashboard.experimentDesign.reportTab.reportGuideTitle')}
            </h3>

            {generatedReport ? (
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">보고서 유형</span>
                  <span className="text-sm font-medium">{generatedReport.metadata?.report_type || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">생성 시간</span>
                  <span className="text-sm font-medium">{generatedReport.metadata?.generation_time || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">단어 수</span>
                  <span className="text-sm font-medium">
                    {generatedReport.metadata?.word_count || 
                     (generatedReport.content ? generatedReport.content.split(' ').length : 0)}개
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">예상 읽기 시간</span>
                  <span className="text-sm font-medium">
                    {generatedReport.metadata?.estimated_read_time || 
                     Math.max(1, Math.ceil((generatedReport.content ? generatedReport.content.split(' ').length : 0) / 200))}분
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">보고서 생성 후 가이드가 표시됩니다.</p>
            )}
          </div>

          <div className="bg-card border border-border rounded-lg p-3">
            <h3 className="text-base font-bold text-foreground mb-2 flex items-center">
              <Lightbulb className="w-5 h-5 mr-2 text-accent-green" />
              {t('dashboard.experimentDesign.reportTab.characteristicsTitle')}
            </h3>

            <div className="space-y-2 text-sm">
              <div>
                <strong>실험 계획 요약:</strong> 실험 설계 개요 및 인자 정보
              </div>
              <div>
                <strong>최적화 결과:</strong> 최적 조건 및 성능 개선 정도
              </div>
              <div>
                <strong>DoE 분석:</strong> 설계 방법론 및 통계적 특성 분석
              </div>
              <div>
                <strong>종합 보고서:</strong> 모든 섹션을 포함한 완전한 보고서
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* 생성된 보고서 */}
      {generatedReport && (
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-foreground flex items-center">
              <FileText className="w-5 h-5 mr-2 text-accent-purple" />
              {t('dashboard.experimentDesign.reportTab.generatedReportTitle')}
            </h3>
            
            <button
              onClick={handleDownloadReport}
              className="flex items-center px-4 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              {t('dashboard.experimentDesign.reportTab.buttons.download')}
            </button>
          </div>

          {/* 보고서 메타데이터 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-sm text-muted-foreground">단어 수</div>
              <div className="text-lg font-semibold">
                {generatedReport.metadata?.word_count || 
                 (generatedReport.content ? generatedReport.content.split(' ').length : 0)}개
              </div>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-sm text-muted-foreground">예상 읽기 시간</div>
              <div className="text-lg font-semibold">
                {generatedReport.metadata?.estimated_read_time || 
                 Math.max(1, Math.ceil((generatedReport.content ? generatedReport.content.split(' ').length : 0) / 200))}분
              </div>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-sm text-muted-foreground">예상 페이지 수</div>
              <div className="text-lg font-semibold">
                {generatedReport.metadata?.estimated_pages || 
                 Math.max(1, Math.ceil((generatedReport.content ? generatedReport.content.split(' ').length : 0) / 250))}페이지
              </div>
            </div>
          </div>

          {/* 보고서 내용 */}
          <div className="bg-muted/50 rounded-lg p-3 max-h-96 overflow-y-auto">
            <MarkdownRenderer content={generatedReport.content} />
          </div>
        </div>
      )}
    </div>
  )
}

// 메인 컴포넌트
export default function ExperimentDesignPage() {
  const { t } = useTranslation()
  const {
    experimentPlan,
    optimizationResult,
    generatedReport,
    parameters,
    experimentTypes,
    loading,
    error,
    generateExperimentPlan,
    runOptimization,
    generateReport,
    fetchParameters,
    fetchExperimentTypes,
    fetchOptimizationGoals,
    downloadReport
  } = useExperimentDesign()

  const [activeTab, setActiveTab] = useState<'experiment' | 'optimization' | 'report'>('experiment')

  // 초기 데이터 로드
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        await Promise.all([
          fetchParameters(),
          fetchExperimentTypes(),
          fetchOptimizationGoals()
        ])
      } catch (error) {
        console.error('초기 데이터 로드 실패:', error)
      }
    }
    
    loadInitialData()
  }, [fetchParameters, fetchExperimentTypes, fetchOptimizationGoals])

  // 실험 통계 데이터 (임시)
  const experimentStats = {
    totalExperiments: 156,
    runningExperiments: 8,
    completedExperiments: 142,
    successfulExperiments: 128
  }

  const tabs = [
    { id: 'experiment', label: t('experimentDesign.tabs.experiment'), icon: Beaker },
    { id: 'optimization', label: t('experimentDesign.tabs.optimization'), icon: Zap },
    { id: 'report', label: t('experimentDesign.tabs.report'), icon: FileText }
  ]

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-4 flex items-center">
          <Beaker className="w-8 h-8 mr-3 text-accent-orange" />
          {t('nav.experimentDesign')}
        </h1>
        <p className="text-muted-foreground text-lg">
          {t('experimentDesign.subtitle')}
        </p>
      </div>

      {/* 실험 현황 대시보드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title={t('dashboard.experimentDesign.experimentTab.status.totalExperiments')}
          value={experimentStats.totalExperiments}
          icon={<Beaker className="w-6 h-6 text-white" />}
          color="#3b82f6"
        />
        <StatusCard
          title={t('dashboard.experimentDesign.common.running')}
          value={experimentStats.runningExperiments}
          icon={<Activity className="w-6 h-6 text-white" />}
          color="#f97316"
        />
        <StatusCard
          title={t('dashboard.experimentDesign.common.completed')}
          value={experimentStats.completedExperiments}
          icon={<CheckCircle className="w-6 h-6 text-white" />}
          color="#22c55e"
        />
        <StatusCard
          title={t('dashboard.experimentDesign.common.successful')}
          value={experimentStats.successfulExperiments}
          icon={<TrendingUp className="w-6 h-6 text-white" />}
          color="#8b5cf6"
          trend={`${((experimentStats.successfulExperiments / experimentStats.completedExperiments) * 100).toFixed(1)}%`}
        />
      </div>

      {/* 탭 네비게이션 */}
      <TabNavigation
        tabs={tabs.map(tab => ({
          id: tab.id,
          name: tab.label,
          icon: tab.icon
        }))}
        activeTab={activeTab}
        onTabChange={(tabId) => setActiveTab(tabId as 'experiment' | 'optimization' | 'report')}
      />

      {/* 탭 컨텐츠 */}
      <div className="bg-card border border-border rounded-lg p-6">
        {activeTab === 'experiment' && (
          <ExperimentDesignTab
            experimentTypes={experimentTypes}
            parameters={parameters}
            onGenerateExperimentPlan={generateExperimentPlan}
            experimentPlan={experimentPlan}
            loading={loading}
            error={error}
          />
        )}

        {activeTab === 'optimization' && (
          <OptimizationTab
            experimentPlan={experimentPlan}
            parameters={parameters}
            onRunOptimization={runOptimization}
            optimizationResult={optimizationResult}
            loading={loading}
            error={error}
          />
        )}

        {activeTab === 'report' && (
          <ReportTab
            experimentPlan={experimentPlan}
            optimizationResult={optimizationResult}
            onGenerateReport={generateReport}
            generatedReport={generatedReport}
            onDownloadReport={downloadReport}
            loading={loading}
            error={error}
          />
        )}
      </div>

      {/* 플로팅 챗봇 위젯 */}
      <FloatingChatbot
        topic="experimental_design"
        sessionId="experiment_design_session"
        enableStreaming={true}
        simulationParams={{
          activeTab: activeTab,
          currentPhase: activeTab === 'experiment' ? 'design' : activeTab === 'optimization' ? 'optimization' : 'reporting',
          experimentStats: {
            total: experimentStats.totalExperiments,
            running: experimentStats.runningExperiments,
            completed: experimentStats.completedExperiments,
            successful: experimentStats.successfulExperiments,
            successRate: ((experimentStats.successfulExperiments / experimentStats.completedExperiments) * 100).toFixed(1)
          },
          experimentPlan: experimentPlan ? {
            experimentType: experimentPlan.metadata?.experiment_type,
            numberOfRuns: experimentPlan.metadata?.num_runs,
            factorsCount: experimentPlan.metadata?.factors?.length || 0,
            factors: experimentPlan.metadata?.factors || [],
            targetPurity: experimentPlan.metadata?.target_purity,
            targetYield: experimentPlan.metadata?.target_yield,
            designEfficiency: experimentPlan.metadata?.design_efficiency,
            statisticalPower: experimentPlan.metadata?.power_analysis?.statistical_power,
            optimizationGoal: experimentPlan.metadata?.optimization_goal,
            hasResults: !!(experimentPlan.experiment_plan && experimentPlan.experiment_plan.length > 0)
          } : null,
          optimization: optimizationResult ? {
            convergenceRate: optimizationResult.convergence_info?.convergence_rate,
            iterationsUsed: optimizationResult.convergence_info?.iterations_used,
            improvementRate: optimizationResult.improvement_rate,
            optimalParameters: Object.keys(optimizationResult.optimal_parameters || {}).length,
            predictedPerformance: optimizationResult.predicted_performance,
            hasOptimalConditions: !!(optimizationResult.optimal_parameters && Object.keys(optimizationResult.optimal_parameters).length > 0)
          } : null,
          report: generatedReport ? {
            reportType: generatedReport.metadata?.report_type,
            wordCount: generatedReport.metadata?.word_count,
            estimatedReadTime: Math.ceil((generatedReport.metadata?.word_count || 0) / 200),
            generationTime: generatedReport.metadata?.generation_time,
            hasContent: !!(generatedReport.content && generatedReport.content.length > 0)
          } : null,
          availableParameters: parameters ? Object.keys(parameters).length : 0,
          availableExperimentTypes: experimentTypes ? experimentTypes.length : 0,
          loading: loading,
          hasError: !!error,
          errorMessage: error || null
        }}
        position="bottom-right"
        theme="dark"
        accentColor="orange"
        minimizedText="AI 실험설계 전문가"
        placeholder="실험 설계에 대해 질문하세요..."
        maxHeight={800}
        width={600}
        showSessionInfo={false}
        onToggle={(isOpen) => {
          // 챗봇이 열리거나 닫힐 때의 로직 (선택사항)
          console.log('Experiment Design Chatbot toggle:', isOpen);
        }}
      />
    </div>
  )
} 