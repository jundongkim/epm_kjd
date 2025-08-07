'use client'

import { useState } from 'react'
import { FileText, Download, Brain, TrendingUp, Calendar, Clock, Eye, Database, Activity, Target, BarChart3, Zap } from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { Checkbox, Select } from '@/components/ui'

// ============================
// StatusCard 컴포넌트 (공정분석 페이지와 동일)
// ============================

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

export default function AIReportPage() {
  const { t } = useTranslation()
  
  // 보고서 섹션 포함 상태
  const [includeSections, setIncludeSections] = useState({
    executiveSummary: true,
    dataAnalysis: true,
    trendsPatterns: true,
    recommendations: false,
    riskAssessment: false,
    appendices: false
  })
  
  const handleSectionToggle = (section: string) => {
    setIncludeSections(prev => ({
      ...prev,
      [section]: !prev[section as keyof typeof prev]
    }))
  }
  const [selectedReport, setSelectedReport] = useState('production_summary')
  const [selectedDateRange, setSelectedDateRange] = useState('last7Days')
  const [selectedFormat, setSelectedFormat] = useState('pdf')

  const reportTypes = [
          { 
        id: 'production_summary', 
        name: t('dashboard.aiReport.reportTypes.productionSummary'), 
        icon: BarChart3, 
        color: 'text-accent-blue' 
      },
    { 
      id: 'quality_analysis', 
      name: t('dashboard.aiReport.reportTypes.qualityAnalysis'), 
      icon: TrendingUp, 
      color: 'text-accent-green' 
    },
    { 
      id: 'cost_optimization', 
      name: t('dashboard.aiReport.reportTypes.costOptimization'), 
      icon: Brain, 
      color: 'text-accent-purple' 
    },
          { 
        id: 'predictive_insights', 
        name: t('dashboard.aiReport.reportTypes.predictiveInsights'), 
        icon: Zap, 
        color: 'text-accent-orange' 
      },
  ]

  const recentReports = [
    { name: 'Monthly Production Report', date: '2024-01-15', status: 'completed', size: '2.3 MB' },
    { name: 'Quality Control Analysis', date: '2024-01-14', status: 'completed', size: '1.8 MB' },
    { name: 'Cost Optimization Study', date: '2024-01-13', status: 'generating', size: '- MB' },
    { name: 'Predictive Maintenance', date: '2024-01-12', status: 'completed', size: '3.1 MB' },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400'
      case 'generating': return 'text-yellow-400'
      case 'failed': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusText = (status: string) => {
    return t(`dashboard.aiReport.status.${status}`)
  }

  const insights = Array.isArray(t('dashboard.aiReport.insights')) ? 
    t('dashboard.aiReport.insights') : 
    [
      "Production efficiency increased by 12% this month compared to the previous period.",
      "Quality defect rate shows a declining trend, suggesting improved process control.",
      "Cost optimization opportunities identified in material procurement processes."
    ]

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-4 flex items-center">
          <FileText className="w-8 h-8 mr-3 text-accent-cyan" />
          {t('nav.aiReport')}
        </h1>
        <p className="text-muted-foreground text-lg">
          {t('dashboard.aiReport.subtitle')}
        </p>
      </div>

      {/* AI 보고서 현황 대시보드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <StatusCard
            title="총 보고서 수"
            value="246"
            icon={<Database className="w-6 h-6 text-white" />}
            color="#3b82f6"
          />
          <StatusCard
            title="생성 중인 보고서"
            value="3"
            icon={<Activity className="w-6 h-6 text-white" />}
            color="#f97316"
          />
        <StatusCard
          title="평균 처리 시간"
          value="4.2분"
          icon={<Clock className="w-6 h-6 text-white" />}
          trend="↓ 12%"
          color="#22c55e"
        />
                  <StatusCard
            title="AI 정확도"
            value="94.7%"
            icon={<Target className="w-6 h-6 text-white" />}
            trend="↑ 2.1%"
            color="#8b5cf6"
        />
      </div>

      {/* Report Type Selection */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {reportTypes.map((report) => {
          const Icon = report.icon
          return (
            <div
              key={report.id}
              onClick={() => setSelectedReport(report.id)}
              className={`bg-card border border-border rounded-glass-2xl p-6 cursor-pointer transition-all duration-300 hover:bg-muted/50 ${
                selectedReport === report.id ? 'ring-2 ring-accent-cyan' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <Icon className={`w-6 h-6 ${report.color}`} />
                <span className="text-muted-foreground text-sm">AI</span>
              </div>
              <h3 className="text-foreground font-semibold">{report.name}</h3>
            </div>
          )
        })}
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-8">
          {/* Report Configuration */}
          <div className="lg:col-span-2">
            <div className="bg-card border border-border rounded-glass-2xl p-8 shadow-glass-lg">
              <h3 className="text-2xl font-bold text-foreground mb-6 flex items-center">
                <FileText className="w-6 h-6 mr-2 text-accent-cyan" />
                {t('dashboard.aiReport.sections.configuration')}
              </h3>
              
              <div className="space-y-6">
                <div className="bg-muted/50 rounded-glass-lg p-6">
                  <h4 className="text-lg font-semibold text-foreground mb-4">{t('dashboard.aiReport.parameters.dateRange')}</h4>
                  <div className="grid md:grid-cols-2 gap-4">
                    <Select
                      value={selectedDateRange}
                      onChange={setSelectedDateRange}
                      options={['last7Days', 'last30Days', 'last90Days', 'customRange']}
                      label={t('dashboard.aiReport.parameters.dateRange')}
                      placeholder="날짜 범위 선택"
                    />
                    <Select
                      value={selectedFormat}
                      onChange={setSelectedFormat}
                      options={['pdf', 'excel', 'powerpoint', 'html']}
                      label={t('dashboard.aiReport.parameters.reportFormat')}
                      placeholder="보고서 형식 선택"
                    />
                  </div>
                </div>

                <div className="bg-muted/50 rounded-glass-lg p-6">
                  <h4 className="text-lg font-semibold text-foreground mb-4">{t('dashboard.aiReport.parameters.includeSections')}</h4>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Checkbox
                        checked={includeSections.executiveSummary}
                        onChange={() => handleSectionToggle('executiveSummary')}
                        label={t('dashboard.aiReport.includeSections.executiveSummary')}
                      />
                      <Checkbox
                        checked={includeSections.dataAnalysis}
                        onChange={() => handleSectionToggle('dataAnalysis')}
                        label={t('dashboard.aiReport.includeSections.dataAnalysis')}
                      />
                      <Checkbox
                        checked={includeSections.trendsPatterns}
                        onChange={() => handleSectionToggle('trendsPatterns')}
                        label={t('dashboard.aiReport.includeSections.trendsPatterns')}
                      />
                    </div>
                    <div className="space-y-2">
                      <Checkbox
                        checked={includeSections.recommendations}
                        onChange={() => handleSectionToggle('recommendations')}
                        label={t('dashboard.aiReport.includeSections.recommendations')}
                      />
                      <Checkbox
                        checked={includeSections.riskAssessment}
                        onChange={() => handleSectionToggle('riskAssessment')}
                        label={t('dashboard.aiReport.includeSections.riskAssessment')}
                      />
                      <Checkbox
                        checked={includeSections.appendices}
                        onChange={() => handleSectionToggle('appendices')}
                        label={t('dashboard.aiReport.includeSections.appendices')}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-center pt-6">
                  <button className="bg-gradient-primary text-white px-8 py-3 rounded-glass-lg font-semibold hover:scale-105 transition-all duration-300 shadow-glow">
                    {t('dashboard.aiReport.buttons.generateAiReport')}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Report Library */}
          <div className="space-y-6">
            <div className="bg-card border border-border rounded-glass-2xl p-6 shadow-glass-lg">
              <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-accent-purple" />
                {t('dashboard.aiReport.sections.recentReports')}
              </h3>
              
              <div className="space-y-3">
                {recentReports.map((report, index) => (
                  <div key={index} className="bg-muted/50 rounded-glass-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-foreground font-medium text-sm">{report.name}</h4>
                      <span className={`text-xs ${getStatusColor(report.status)}`}>
                        {getStatusText(report.status)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-muted-foreground text-xs">
                      <span>{report.date}</span>
                      <span>{report.size}</span>
                    </div>
                    {report.status === 'completed' && (
                      <div className="flex space-x-2 mt-2">
                        <button className="flex items-center space-x-1 bg-secondary hover:bg-secondary/80 text-secondary-foreground px-2 py-1 rounded text-xs transition-all duration-300">
                          <Eye className="w-3 h-3" />
                          <span>{t('dashboard.aiReport.buttons.view')}</span>
                        </button>
                        <button className="flex items-center space-x-1 bg-secondary hover:bg-secondary/80 text-secondary-foreground px-2 py-1 rounded text-xs transition-all duration-300">
                          <Download className="w-3 h-3" />
                          <span>{t('dashboard.aiReport.buttons.download')}</span>
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card border border-border rounded-glass-2xl p-6 shadow-glass-lg">
              <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
                <Brain className="w-5 h-5 mr-2 text-accent-orange" />
                {t('dashboard.aiReport.sections.aiInsights')}
              </h3>
              
              <div className="space-y-3">
                {insights.map((insight: string, index: number) => (
                  <div key={index} className="bg-muted/50 rounded-glass-lg p-3">
                    <p className="text-muted-foreground text-sm">{insight}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card border border-border rounded-glass-2xl p-6 shadow-glass-lg">
              <h3 className="text-xl font-bold text-foreground mb-4">{t('dashboard.aiReport.sections.quickActions')}</h3>
              
              <div className="space-y-3">
                <button className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-2 px-4 rounded-glass-lg font-medium transition-all duration-300">
                  {t('dashboard.aiReport.buttons.scheduleReport')}
                </button>
                <button className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-2 px-4 rounded-glass-lg font-medium transition-all duration-300">
                  {t('dashboard.aiReport.buttons.templateLibrary')}
                </button>
                <button className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-2 px-4 rounded-glass-lg font-medium transition-all duration-300">
                  {t('dashboard.aiReport.buttons.exportSettings')}
                </button>
              </div>
            </div>
          </div>
        </div>
    </div>
  )
} 