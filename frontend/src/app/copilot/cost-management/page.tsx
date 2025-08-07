'use client'

import { useState } from 'react'
import { DollarSign, TrendingDown, TrendingUp, PieChart, BarChart3, Calculator, Database, Activity, Target } from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { NumberInput } from '@/components/ui'

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

export default function CostManagementPage() {
  const { t } = useTranslation()
  const [selectedPeriod, setSelectedPeriod] = useState('monthly')
  
  // 비용 계산기 state
  const [productionVolume, setProductionVolume] = useState(1000)
  const [materialCostPerUnit, setMaterialCostPerUnit] = useState(5.0)

  const periods = [
    { id: 'daily', name: t('dashboard.costManagement.periods.daily'), active: false },
    { id: 'weekly', name: t('dashboard.costManagement.periods.weekly'), active: false },
    { id: 'monthly', name: t('dashboard.costManagement.periods.monthly'), active: true },
    { id: 'yearly', name: t('dashboard.costManagement.periods.yearly'), active: false },
  ]

  const costCategories = [
    { name: t('dashboard.costManagement.categories.materialCosts'), amount: 45000, percentage: 45, trend: 'up', change: 5.2 },
    { name: t('dashboard.costManagement.categories.laborCosts'), amount: 30000, percentage: 30, trend: 'down', change: -2.1 },
    { name: t('dashboard.costManagement.categories.energyCosts'), amount: 15000, percentage: 15, trend: 'up', change: 8.4 },
    { name: t('dashboard.costManagement.categories.overhead'), amount: 10000, percentage: 10, trend: 'stable', change: 0.3 },
  ]

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-red-400" />
      case 'down': return <TrendingDown className="w-4 h-4 text-green-400" />
      default: return <span className="w-4 h-4 text-gray-400">-</span>
    }
  }

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-4 flex items-center">
          <DollarSign className="w-8 h-8 mr-3 text-accent-green" />
          {t('nav.costManagement')}
        </h1>
        <p className="text-muted-foreground text-lg">
          {t('dashboard.costManagement.subtitle')}
        </p>
      </div>

      {/* Period Selection */}
      <div className="flex flex-wrap gap-2">
        {periods.map((period) => (
          <button
            key={period.id}
            onClick={() => setSelectedPeriod(period.id)}
            className={`px-4 py-2 rounded-glass-lg transition-all duration-300 ${
              selectedPeriod === period.id
                ? 'bg-gradient-primary text-white shadow-glow'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:text-foreground'
            }`}
          >
            {period.name}
          </button>
        ))}
      </div>

      {/* 비용 관리 현황 대시보드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="총 분석 건수"
          value="1,248"
          icon={<Database className="w-6 h-6 text-white" />}
          color="#3b82f6"
        />
        <StatusCard
          title="진행 중인 분석"
          value="3"
          icon={<Activity className="w-6 h-6 text-white" />}
          color="#f97316"
        />
        <StatusCard
          title="평균 배치 비용"
          value="$12,543"
          icon={<DollarSign className="w-6 h-6 text-white" />}
          trend="↓ 5.2%"
          color="#22c55e"
        />
        <StatusCard
          title="예산 절약률"
          value="15.2%"
          icon={<Target className="w-6 h-6 text-white" />}
          trend="↑ 3.2%"
          color="#8b5cf6"
        />
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Cost Analysis */}
        <div className="lg:col-span-2">
          <div className="bg-card border border-border rounded-glass-2xl p-8 shadow-glass-lg">
            <h3 className="text-2xl font-bold text-foreground mb-6 flex items-center">
              <BarChart3 className="w-6 h-6 mr-2 text-accent-green" />
              {t('dashboard.costManagement.sections.costBreakdown')}
            </h3>
            
            <div className="space-y-4">
              {costCategories.map((category, index) => (
                <div key={index} className="bg-muted/50 rounded-glass-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-foreground font-medium">{category.name}</span>
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(category.trend)}
                      <span className="text-muted-foreground text-sm">
                        {category.change > 0 ? '+' : ''}{category.change}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-muted-foreground">${category.amount.toLocaleString()}</span>
                    <span className="text-muted-foreground">{category.percentage}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className="bg-gradient-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${category.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Control Panel */}
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-glass-2xl p-6 shadow-glass-lg">
            <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
              <Calculator className="w-5 h-5 mr-2 text-accent-blue" />
              {t('dashboard.costManagement.sections.costCalculator')}
            </h3>
            
            <div className="space-y-4">
              <NumberInput
                value={productionVolume}
                onChange={setProductionVolume}
                min={1}
                max={1000000}
                step={1}
                label={t('dashboard.costManagement.calculator.productionVolume')}
                unit="units"
              />
              
              <NumberInput
                value={materialCostPerUnit}
                onChange={setMaterialCostPerUnit}
                min={0.01}
                max={1000}
                step={0.01}
                label={t('dashboard.costManagement.calculator.materialCostPerUnit')}
                unit="$"
              />
              
              <button className="w-full bg-gradient-primary text-white py-2 px-4 rounded-glass-lg font-medium hover:scale-105 transition-all duration-300">
                {t('dashboard.costManagement.calculator.calculateCost')}
              </button>
            </div>
          </div>

          <div className="bg-card border border-border rounded-glass-2xl p-6 shadow-glass-lg">
            <h3 className="text-xl font-bold text-foreground mb-4 flex items-center">
              <PieChart className="w-5 h-5 mr-2 text-accent-purple" />
              {t('dashboard.costManagement.sections.costOptimization')}
            </h3>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">{t('dashboard.costManagement.optimization.materialWaste')}</span>
                <span className="text-red-400 font-medium">5.2%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">{t('dashboard.costManagement.optimization.energyEfficiency')}</span>
                <span className="text-green-400 font-medium">92.1%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">{t('dashboard.costManagement.optimization.laborUtilization')}</span>
                <span className="text-yellow-400 font-medium">78.5%</span>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-glass-2xl p-6 shadow-glass-lg">
            <h3 className="text-xl font-bold text-foreground mb-4">{t('dashboard.costManagement.sections.quickActions')}</h3>
            
            <div className="space-y-3">
              <button className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-2 px-4 rounded-glass-lg font-medium transition-all duration-300">
                {t('dashboard.costManagement.buttons.generateReport')}
              </button>
              <button className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-2 px-4 rounded-glass-lg font-medium transition-all duration-300">
                {t('dashboard.costManagement.buttons.exportData')}
              </button>
              <button className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-2 px-4 rounded-glass-lg font-medium transition-all duration-300">
                {t('dashboard.costManagement.buttons.setBudgetAlert')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 