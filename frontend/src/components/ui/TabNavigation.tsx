import React from 'react'
import { LucideIcon } from 'lucide-react'

interface TabItem {
  id: string | number
  name: string
  icon: LucideIcon
}

interface TabNavigationProps {
  tabs: TabItem[]
  activeTab: string | number
  onTabChange: (tabId: string | number) => void
  className?: string
}

export function TabNavigation({ tabs, activeTab, onTabChange, className = "" }: TabNavigationProps) {
  return (
    <div className={`flex flex-wrap gap-2 bg-card backdrop-blur-sm border border-border rounded-lg p-2 ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`flex-1 min-w-fit flex items-center justify-center px-4 py-3 rounded-lg text-base font-semibold transition-all duration-300 ${
            activeTab === tab.id
              ? 'bg-gradient-primary text-white shadow-glow'
              : 'text-foreground/80 hover:text-foreground hover:bg-muted/50'
          }`}
        >
          <tab.icon className="w-4 h-4 mr-2" />
          {tab.name}
        </button>
      ))}
    </div>
  )
} 