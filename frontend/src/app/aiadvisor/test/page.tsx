'use client'

import { useState } from 'react'
import { aiAdvisorService } from '@/services/aiadvisor'

export default function AITestPage() {
  const [testResult, setTestResult] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  const testHealthCheck = async () => {
    setIsLoading(true)
    try {
      const result = await aiAdvisorService.healthCheck()
      setTestResult(`Health check result: ${result}`)
    } catch (error) {
      setTestResult(`Health check failed: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  const testSystemStatus = async () => {
    setIsLoading(true)
    try {
      const result = await aiAdvisorService.getSystemStatus()
      setTestResult(`System status: ${JSON.stringify(result, null, 2)}`)
    } catch (error) {
      setTestResult(`System status failed: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  const testQueryAgent = async () => {
    setIsLoading(true)
    try {
      const result = await aiAdvisorService.queryAgent({
        query: '안녕하세요',
        use_workflow: false,
        k: 5
      })
      setTestResult(`Query result: ${JSON.stringify(result, null, 2)}`)
    } catch (error) {
      setTestResult(`Query failed: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">AI Advisor API Test</h1>
      
      <div className="space-y-4">
        <button
          onClick={testHealthCheck}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
        >
          Test Health Check
        </button>
        
        <button
          onClick={testSystemStatus}
          disabled={isLoading}
          className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
        >
          Test System Status
        </button>
        
        <button
          onClick={testQueryAgent}
          disabled={isLoading}
          className="px-4 py-2 bg-purple-500 text-white rounded disabled:opacity-50"
        >
          Test Query Agent
        </button>
      </div>
      
      {isLoading && <p className="mt-4">Loading...</p>}
      
      {testResult && (
        <div className="mt-4">
          <h2 className="text-lg font-semibold mb-2">Test Result:</h2>
          <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96">
            {testResult}
          </pre>
        </div>
      )}
    </div>
  )
} 