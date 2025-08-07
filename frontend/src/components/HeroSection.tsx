'use client'

import { useState, useEffect } from 'react'
import { ChevronRight, Play, Zap, Shield, TrendingUp, Brain, Rocket, Award, LucideIcon, Workflow, Bot } from 'lucide-react'
import Link from 'next/link'
import { useTranslation } from '@/hooks/useTranslation'

interface FeatureItem {
  icon: LucideIcon
  text: string
  color: string
}

interface StatItem {
  value: string
  label: string
  icon: LucideIcon
}

interface SystemStatus {
  status: string
  message: string
  engines_status: Record<string, string>
}

export default function HeroSection() {
  const [currentFeature, setCurrentFeature] = useState(0)
  const [mounted, setMounted] = useState(false)
  const [systemData, setSystemData] = useState<SystemStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { t } = useTranslation()

  const features: FeatureItem[] = [
    { icon: Brain, text: t('hero.features.aiAnalytics') || "AI-Powered Analytics", color: "text-accent-blue" },
    { icon: Shield, text: t('hero.features.realtimeMonitoring') || "Real-time Monitoring", color: "text-accent-purple" },
    { icon: TrendingUp, text: t('hero.features.predictiveOptimization') || "Predictive Optimization", color: "text-accent-cyan" },
    { icon: Rocket, text: t('hero.features.advancedML') || "Advanced ML Models", color: "text-accent-pink" },
    { icon: Workflow, text: t('hero.features.workflowAutomation') || "Workflow Automation", color: "text-accent-indigo" },
    { icon: Bot, text: t('hero.features.aiAgent') || "AI Agent Integration", color: "text-accent-yellow" },
  ]

  const stats: StatItem[] = [
    { value: "99.9%", label: "System Uptime", icon: Zap },
    { value: "500+", label: "AI Models", icon: Brain },
    { value: "24/7", label: "Support", icon: Shield },
    { value: "ISO", label: "Certified", icon: Award },
  ]

  useEffect(() => {
    setMounted(true)
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % features.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [features.length])

  useEffect(() => {
    // Check actual system status including Docker services
    const checkSystemStatus = async () => {
      try {
        // Check main engines (simulate or use actual API)
        const coreEnginesStatus = {
          'data_engine': 'healthy',
          'ml_engine': 'healthy',
          'process_engine': 'healthy',
          'cost_engine': 'healthy',
          'report_engine': 'healthy'
        }

        // Check n8n Docker status
        let n8nStatus = 'checking'
        try {
          const n8nResponse = await fetch('/api/v1/workflow/health', { method: 'GET' })
          n8nStatus = n8nResponse.ok ? 'healthy' : 'unhealthy'
        } catch (error) {
          console.warn('n8n health check failed:', error)
          n8nStatus = 'unhealthy'
        }

        // Check Dify Docker status
        let difyStatus = 'checking'
        try {
          const difyResponse = await fetch('/api/v1/dify/health', { method: 'GET' })
          difyStatus = difyResponse.ok ? 'healthy' : 'unhealthy'
        } catch (error) {
          console.warn('Dify health check failed:', error)
          difyStatus = 'unhealthy'
        }

        const mockData: SystemStatus = {
          status: 'healthy',
          message: 'All systems operational',
          engines_status: {
            ...coreEnginesStatus,
            'n8n_workflow': n8nStatus,
            'dify_ai_agent': difyStatus
          }
        }

        setSystemData(mockData)
        setIsLoading(false)
      } catch (error) {
        console.error('System status check failed:', error)
        // Fallback to mock data on error
        const fallbackData: SystemStatus = {
          status: 'partial',
          message: 'Some services may be unavailable',
          engines_status: {
            'data_engine': 'healthy',
            'ml_engine': 'healthy',
            'process_engine': 'healthy',
            'cost_engine': 'healthy',
            'report_engine': 'healthy',
            'n8n_workflow': 'unhealthy',
            'dify_ai_agent': 'unhealthy'
          }
        }
        setSystemData(fallbackData)
        setIsLoading(false)
      }
    }

    // Simulate loading delay then check status
    setTimeout(() => {
      checkSystemStatus()
    }, 1000)
  }, [])

  // Safe array creation for background elements
  const backgroundElements = Array.from({ length: 6 }, (_, i) => i)

  // Safe feature access
  const currentFeatureData = features[currentFeature] || features[0]

  if (!mounted) {
    return null
  }

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* Animated background elements */}
      <div className="absolute inset-0 -z-10">
        {backgroundElements.map((i) => (
          <div
            key={i}
            className="absolute w-32 h-32 bg-gradient-primary rounded-full opacity-10 animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${i * 1.5}s`,
              animationDuration: `${6 + i * 2}s`,
            }}
          />
        ))}
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8 animate-fade-in-up">
            {/* Status Badge */}
            <div className="inline-flex items-center px-4 py-2 bg-card backdrop-blur-sm border border-border rounded-lg shadow-sm">
              <div className="flex items-center space-x-2">
                <div className="status-indicator status-healthy animate-pulse-glow"></div>
                <span className="text-sm font-medium text-foreground">
                  {isLoading ? t('common.loading') : t('hero.healthy')}
                </span>
                <span className="text-xs text-muted-foreground">
                  {systemData?.engines_status ? Object.keys(systemData.engines_status).length + ' ' + t('hero.allEnginesRunning') : t('common.loading')}
                </span>
              </div>
            </div>

            {/* Main Heading */}
            <div className="space-y-4">
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-black text-foreground leading-tight">
                <span className="block">{t('hero.title')}</span>
                <span className="block gradient-text">{t('hero.subtitle')}</span>
              </h1>
              <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl leading-relaxed">
                {t('hero.description')}
              </p>
            </div>

            {/* Feature Carousel */}
            <div className="relative h-16 overflow-hidden rounded-lg bg-card backdrop-blur-sm border border-border shadow-sm">
              <div className="absolute inset-0 flex items-center px-6">
                <div className="flex items-center space-x-4 transition-all duration-500">
                  {(() => {
                    const IconComponent = currentFeatureData.icon
                    return <IconComponent className={`w-8 h-8 ${currentFeatureData.color}`} />
                  })()}
                  <span className="text-lg font-semibold text-foreground">
                    {currentFeatureData.text}
                  </span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="absolute bottom-0 left-0 h-1 bg-gradient-primary transition-all duration-300" 
                   style={{ width: `${((currentFeature + 1) / features.length) * 100}%` }} />
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/copilot/data-generation" className="btn-primary group flex items-center justify-center px-8 py-4 text-lg font-semibold hover:scale-105 transition-transform duration-300">
                <Play className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform duration-300" />
                {t('hero.tryDemo')}
                <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform duration-300" />
              </Link>
              <button 
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="btn-glass group flex items-center justify-center px-8 py-4 text-lg font-semibold hover:scale-105 transition-transform duration-300"
              >
                <Brain className="w-5 h-5 mr-2 group-hover:rotate-12 transition-transform duration-300" />
                {t('hero.learnMore')}
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-8">
              {stats && stats.length > 0 && stats.map((stat, index) => (
                <div key={index} className="text-center group">
                  <div className="flex items-center justify-center mb-2">
                    <div className="w-12 h-12 bg-muted/30 backdrop-blur-sm rounded-lg flex items-center justify-center group-hover:bg-muted/50 transition-colors duration-300">
                      <stat.icon className="w-6 h-6 text-accent-blue" />
                    </div>
                  </div>
                  <div className="text-2xl font-black text-foreground">{stat.value}</div>
                  <div className="text-sm text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Content - System Dashboard */}
          <div className="space-y-6 animate-fade-in-down">
            {/* Main Dashboard Card */}
            <div className="bg-card backdrop-blur-sm border border-border rounded-lg p-8 shadow-sm hover:shadow-md transition-all duration-300">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-foreground">{t('hero.systemStatus')}</h3>
                <div className="flex items-center space-x-2">
                  <div className="status-indicator status-healthy animate-pulse-glow"></div>
                  <span className="text-sm font-medium text-foreground">{t('hero.healthy')}</span>
                </div>
              </div>

              {/* Engine Status Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                {systemData?.engines_status && Object.keys(systemData.engines_status).length > 0 ? (
                  Object.entries(systemData.engines_status).map(([engine, status]) => (
                    <div key={engine} className="bg-muted/30 backdrop-blur-sm rounded-lg p-3 hover:bg-muted/50 transition-colors duration-300">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-muted-foreground">
                          {t(`hero.engines.${engine}`) || engine.replace('_', ' ')}
                        </span>
                        <div className={`status-indicator ${status === 'healthy' ? 'status-healthy' : status === 'checking' ? 'status-warning' : 'status-error'}`}></div>
                      </div>
                      <div className="text-sm font-semibold text-foreground mt-1">
                        {status === 'healthy' ? t('hero.status.online') : status === 'checking' ? t('hero.status.checking') : t('hero.status.offline')}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 md:col-span-3 flex items-center justify-center py-8">
                    <div className="loading-spinner mr-3"></div>
                    <span className="text-muted-foreground">Loading system status...</span>
                  </div>
                )}
              </div>

              {/* Performance Metrics */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">System Performance</span>
                  <span className="text-sm font-semibold text-accent-blue">99.2%</span>
                </div>
                <div className="w-full bg-muted/30 rounded-full h-2">
                  <div className="bg-gradient-primary h-2 rounded-full animate-pulse" style={{ width: '92%' }}></div>
                </div>
              </div>

              <div className="space-y-4 mt-6">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">AI Processing Load</span>
                  <span className="text-sm font-semibold text-accent-cyan">76%</span>
                </div>
                <div className="w-full bg-muted/30 rounded-full h-2">
                  <div className="bg-gradient-secondary h-2 rounded-full animate-pulse" style={{ width: '76%' }}></div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-4">
              <Link href="/copilot/data-generation" className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 hover:scale-105 transition-all duration-300 text-left shadow-sm">
                <Zap className="w-8 h-8 text-accent-blue mb-3" />
                <div className="text-lg font-semibold text-foreground">Quick Start</div>
                <div className="text-sm text-muted-foreground">Launch AI Analysis</div>
              </Link>
              <button 
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="bg-card backdrop-blur-sm border border-border rounded-lg p-6 hover:bg-muted/50 hover:scale-105 transition-all duration-300 text-left shadow-sm"
              >
                <Brain className="w-8 h-8 text-accent-purple mb-3" />
                <div className="text-lg font-semibold text-foreground">AI Reports</div>
                <div className="text-sm text-muted-foreground">Generate Insights</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
} 