import { useState, useCallback } from 'react'
import {
  generateExperimentPlan as apiGenerateExperimentPlan,
  runOptimization as apiRunOptimization,
  generateExperimentReport as apiGenerateExperimentReport,
  getExperimentParameters as apiGetExperimentParameters,
  getExperimentTypes as apiGetExperimentTypes,
  getOptimizationGoals as apiGetOptimizationGoals,
  validateExperimentSetup as apiValidateExperimentSetup,
  handleApiError
} from '@/lib/api'

// Types
interface ExperimentPlanRequest {
  experiment_type: string
  factors: string[]
  num_runs: number
  replications: number
  target_purity: number
  target_yield: number
  optimization_goal: string
}

interface ExperimentPlanResponse {
  experiment_plan: any
  metadata: any
  analysis: any
  validation: any
}

interface OptimizationRequest {
  objectives: string[]
  constraints: Record<string, { min: number; max: number }>
  optimizer: string
  max_iterations: number
  acquisition_function: string
}

interface OptimizationResponse {
  optimal_parameters: Record<string, number>
  predicted_performance: Record<string, string>
  confidence_levels: Record<string, number>
  improvement_rate: number
  convergence_info: any
  analysis: any
}

interface ReportRequest {
  report_type: string
  include_sections: string[]
  report_length: string
  experiment_data?: any
  optimization_data?: any
}

interface ReportResponse {
  content: string
  metadata: any
}

interface Parameter {
  name: string
  min_value: number
  max_value: number
  levels: number
  unit: string
}

interface ExperimentType {
  id: string
  name: string
  description: string
}

interface OptimizationGoal {
  id: string
  name: string
  description: string
}

export const useExperimentDesign = () => {
  const [experimentPlan, setExperimentPlan] = useState<ExperimentPlanResponse | null>(null)
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResponse | null>(null)
  const [generatedReport, setGeneratedReport] = useState<ReportResponse | null>(null)
  const [parameters, setParameters] = useState<Record<string, Parameter>>({})
  const [experimentTypes, setExperimentTypes] = useState<ExperimentType[]>([])
  const [optimizationGoals, setOptimizationGoals] = useState<OptimizationGoal[]>([])
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 실험 계획 생성
  const generateExperimentPlan = useCallback(async (request: ExperimentPlanRequest) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await apiGenerateExperimentPlan(request)
      setExperimentPlan(response)
      return response
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // 베이지안 최적화 실행
  const runOptimization = useCallback(async (request: OptimizationRequest) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await apiRunOptimization(request)
      setOptimizationResult(response)
      return response
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // 보고서 생성
  const generateReport = useCallback(async (request: ReportRequest) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await apiGenerateExperimentReport(request)
      setGeneratedReport(response)
      return response
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // 파라미터 정보 조회
  const fetchParameters = useCallback(async () => {
    try {
      const response = await apiGetExperimentParameters()
      setParameters(response.parameters)
      return response.parameters
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      throw err
    }
  }, [])

  // 실험 유형 조회
  const fetchExperimentTypes = useCallback(async () => {
    try {
      const response = await apiGetExperimentTypes()
      setExperimentTypes(response.experiment_types)
      return response.experiment_types
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      throw err
    }
  }, [])

  // 최적화 목표 조회
  const fetchOptimizationGoals = useCallback(async () => {
    try {
      const response = await apiGetOptimizationGoals()
      setOptimizationGoals(response.optimization_goals)
      return response.optimization_goals
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      throw err
    }
  }, [])

  // 실험 설정 검증
  const validateExperimentSetup = useCallback(async (request: ExperimentPlanRequest) => {
    try {
      const response = await apiValidateExperimentSetup(request)
      return response
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      throw err
    }
  }, [])

  // 보고서 다운로드
  const downloadReport = useCallback(async (reportType: string, content: string) => {
    try {
      // 파일 이름 생성
      const timestamp = new Date().toISOString().slice(0, 10);
      const filename = `실험설계_보고서_${reportType}_${timestamp}.md`;
      
      // Blob 생성
      const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      
      // 다운로드 실행
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      // 정리
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    }
  }, [])

  // 상태 리셋
  const resetState = useCallback(() => {
    setExperimentPlan(null)
    setOptimizationResult(null)
    setGeneratedReport(null)
    setError(null)
  }, [])

  return {
    // State
    experimentPlan,
    optimizationResult,
    generatedReport,
    parameters,
    experimentTypes,
    optimizationGoals,
    loading,
    error,
    
    // Actions
    generateExperimentPlan,
    runOptimization,
    generateReport,
    fetchParameters,
    fetchExperimentTypes,
    fetchOptimizationGoals,
    validateExperimentSetup,
    downloadReport,
    resetState,
  }
} 