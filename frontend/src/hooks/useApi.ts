import React, { useState, useCallback } from 'react';
import { 
  handleApiError,
  healthCheck, 
  getSystemStatus, 
  generateData, 
  analyzeProcess, 
  analyzeProductData, 
  designExperiment, 
  analyzeCost, 
  optimizeCost, 
  generateReport, 
  advancedOptimize, 
  chat 
} from '@/lib/api';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

// 제네릭 API Hook
export function useApi<T>(
  apiFunction: (...args: any[]) => Promise<T>
): UseApiResult<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: any[]): Promise<T | null> => {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      try {
        const result = await apiFunction(...args);
        setState(prev => ({ ...prev, data: result, loading: false }));
        return result;
      } catch (error) {
        const errorMessage = handleApiError(error);
        setState(prev => ({ ...prev, error: errorMessage, loading: false }));
        return null;
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    execute,
    reset,
  };
}

// 자동 실행 API Hook
export function useApiWithAutoExecution<T>(
  apiFunction: (...args: any[]) => Promise<T>,
  dependencies: any[] = []
): UseApiResult<T> {
  const apiHook = useApi(apiFunction);
  
  // 의존성 배열이 변경될 때마다 자동 실행
  React.useEffect(() => {
    apiHook.execute(...dependencies);
  }, dependencies);

  return apiHook;
}

// 특정 API용 Hook들
export function useHealthCheck() {
  return useApi(healthCheck);
}

export function useSystemStatus() {
  return useApi(getSystemStatus);
}

export function useDataGeneration() {
  return useApi(generateData);
}

export function useProcessAnalysis() {
  return useApi(analyzeProcess);
}

export function useProductAnalysis() {
  return useApi(analyzeProductData);
}

export function useExperimentDesign() {
  return useApi(designExperiment);
}

export function useCostAnalysis() {
  return useApi(analyzeCost);
}

export function useCostOptimization() {
  return useApi(optimizeCost);
}

export function useReportGeneration() {
  return useApi(generateReport);
}

export function useAdvancedOptimization() {
  return useApi(advancedOptimize);
}

export function useChat() {
  return useApi(chat);
}

// 다중 API 호출 Hook
export function useMultipleApi<T extends Record<string, any>>(
  apiCalls: T
): {
  [K in keyof T]: UseApiResult<any>;
} {
  const results = {} as any;
  
  for (const [key, apiFunction] of Object.entries(apiCalls)) {
    results[key] = useApi(apiFunction);
  }
  
  return results;
} 