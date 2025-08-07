'use client'


import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Database,
  Factory,
  Beaker,
  Calculator,
  DollarSign,
  FileText,
  Workflow,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Home,
  Settings,
  BarChart3,
  Bot,
  ChartSpline,
  Brain
} from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { useLanguageStore } from '@/stores/useLanguageStore'
import SettingsDropdown from './SettingsDropdown'
import { LanguageCode } from '@/types/settings'

interface MenuItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  translationKey: string
}

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const pathname = usePathname()
  const { t } = useTranslation()
  const { setLanguage } = useLanguageStore()

  const menuItems: MenuItem[] = [
    {
      name: 'Data Generation',
      href: '/copilot/data-generation',
      icon: Database,
      translationKey: 'nav.dataGeneration'
    },
    {
      name: 'Experiment Design',
      href: '/copilot/experiment-design',
      icon: Beaker,
      translationKey: 'nav.experimentDesign'
    },
    {
      name: 'Product Data Analysis',
      href: '/copilot/product-data-analysis',
      icon: BarChart3,
      translationKey: 'nav.productDataAnalysis'
    },
    {
      name: 'Data Analysis Workflow',
      href: '/copilot/data-analysis-workflow',
      icon: Brain,
      translationKey: 'nav.dataAnalysisWorkflow'
    },
    {
      name: 'Product Modeling',
      href: '/copilot/product-modeling',
      icon: Calculator,
      translationKey: 'nav.productModeling'
    },
    {
      name: 'Process Analysis',
      href: '/copilot/process-analysis',
      icon: Factory,
      translationKey: 'nav.processAnalysis'
    },
    {
      name: 'Cost Management',
      href: '/copilot/cost-management',
      icon: DollarSign,
      translationKey: 'nav.costManagement'
    },
    {
      name: 'Workflow',
      href: '/copilot/workflow',
      icon: Workflow,
      translationKey: 'nav.workflow'
    },
    {
      name: 'AI Agent',
      href: '/copilot/ai-agent',
      icon: Bot,
      translationKey: 'nav.aiAgent'
    },
    {
      name: 'AI Report',
      href: '/copilot/ai-report',
      icon: FileText,
      translationKey: 'nav.aiReport'
    },
    {
      name: 'IoT Prism',
      href: '/copilot/iot-prism-demo',
      icon: ChartSpline,
      translationKey: 'nav.iotPrismDemo'
    },
    {
      name: 'AI Advisor',
      href: '/aiadvisor',
      icon: Brain,
      translationKey: 'AI Advisor'
    }
  ]

  const isActive = (href: string) => pathname === href

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-glass bg-glass-200 hover:bg-glass-300 transition-all duration-300"
      >
        {isMobileOpen ? (
          <X className="w-6 h-6 text-foreground" />
        ) : (
          <Menu className="w-6 h-6 text-foreground" />
        )}
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-40
        ${isCollapsed ? 'w-16' : 'w-64'}
        ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        bg-glass-100 backdrop-blur-glass-xl border-r border-glass-border
        transition-all duration-300 ease-in-out
        flex flex-col h-full
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-glass-border">
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Database className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className="text-foreground font-bold text-sm">DX-AI</h2>
                <p className="text-muted-foreground text-xs">Dashboard</p>
              </div>
            </div>
          )}

          {/* Header Actions */}
          <div className="flex items-center space-x-1">
            {/* Home Button */}
            <Link
              href="/"
              className="p-1.5 rounded-glass bg-glass-200 hover:bg-glass-300 transition-all duration-300 group"
              title={t('dashboard.sidebar.backToHome')}
            >
              <Home className="w-4 h-4 text-muted-foreground group-hover:text-foreground" />
            </Link>

            {/* Settings Button */}
            <button
              onClick={() => setIsSettingsOpen(!isSettingsOpen)}
              className="p-1.5 rounded-glass bg-glass-200 hover:bg-glass-300 transition-all duration-300 group relative"
              title={isSettingsOpen ? t('dashboard.sidebar.closeSettings') : t('dashboard.sidebar.openSettings')}
            >
              <Settings className="w-4 h-4 text-muted-foreground group-hover:text-foreground" />
            </button>

            {/* Collapse Toggle - Desktop Only */}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden lg:flex p-1.5 rounded-glass bg-glass-200 hover:bg-glass-300 transition-all duration-300"
              title={isCollapsed ? t('dashboard.sidebar.expand') : t('dashboard.sidebar.collapse')}
            >
              {isCollapsed ? (
                <ChevronRight className="w-4 h-4 text-foreground" />
              ) : (
                <ChevronLeft className="w-4 h-4 text-foreground" />
              )}
            </button>
          </div>
        </div>

        {/* Settings Dropdown */}
        <SettingsDropdown
          isOpen={isSettingsOpen}
          isCollapsed={isCollapsed}
          onClose={() => setIsSettingsOpen(false)}
          onLanguageChange={(lang: LanguageCode) => setLanguage(lang)}
          onMobileClose={() => setIsMobileOpen(false)}
        />

        {/* Settings Dropdown Overlay */}
        {isSettingsOpen && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsSettingsOpen(false)}
          />
        )}

        {/* Navigation Menu */}
        <div className="flex-1 flex flex-col">
          <nav className="flex-1 p-4 space-y-2" role="navigation" aria-label={t('dashboard.sidebar.navigation')}>
            {menuItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileOpen(false)}
                  className={`
                    flex items-center space-x-3 px-3 py-3 rounded-glass transition-all duration-300
                    min-h-[44px] w-full
                    ${active
                      ? 'bg-gradient-primary text-white shadow-glow'
                      : 'text-muted-foreground hover:text-foreground hover:bg-glass-200'
                    }
                    ${isCollapsed ? 'justify-center' : ''}
                  `}
                  aria-current={active ? 'page' : undefined}
                  title={isCollapsed ? t(item.translationKey) : undefined}
                >
                  <Icon className={`${isCollapsed ? 'w-5 h-5' : 'w-5 h-5'} flex-shrink-0`} />
                  {!isCollapsed && (
                    <span className="font-medium text-base truncate">{t(item.translationKey)}</span>
                  )}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Footer */}
        <div className="mt-auto">
          {!isCollapsed && (
            <div className="p-4 border-t border-glass-border">
              <div className="text-center space-y-1">
                <p className="text-muted-foreground text-xs">
                  {t('dashboard.footer.copyright')}
                </p>
                <div className="flex justify-center items-center space-x-2 text-xs">
                  <span className="text-muted-foreground">{t('dashboard.footer.version')} 1.0.0</span>
                  <span className="text-muted-foreground">•</span>
                  <span className="text-accent-cyan">{t('dashboard.footer.status')}: {t('hero.healthy')}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}