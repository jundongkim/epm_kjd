'use client'

import React from 'react'
import { Sun, Moon, Monitor } from 'lucide-react'
import { useTheme } from './ThemeProvider'
import { useTranslation } from '@/hooks/useTranslation'

interface ThemeToggleProps {
  variant?: 'button' | 'dropdown' | 'compact'
  showLabels?: boolean
  className?: string
}

export function ThemeToggle({ 
  variant = 'button', 
  showLabels = true, 
  className = '' 
}: ThemeToggleProps) {
  const { theme, setTheme, actualTheme } = useTheme()
  const { t } = useTranslation()

  const themes = [
    {
      id: 'light' as const,
      name: t('settings.theme.light'),
      icon: Sun,
      description: t('settings.theme.light')
    },
    {
      id: 'dark' as const,
      name: t('settings.theme.dark'),
      icon: Moon,
      description: t('settings.theme.dark')
    },
    {
      id: 'system' as const,
      name: t('settings.theme.system'),
      icon: Monitor,
      description: t('settings.theme.system')
    }
  ]

  const currentTheme = themes.find(t => t.id === theme)

  if (variant === 'compact') {
    return (
      <button
        onClick={() => {
          const nextTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light'
          setTheme(nextTheme)
        }}
        className={`
          p-2 rounded-glass bg-glass-200 hover:bg-glass-300 
          transition-all duration-300 group relative
          ${className}
        `}
        title={currentTheme?.description}
      >
        {currentTheme && (
          <currentTheme.icon className="w-4 h-4 text-muted-foreground group-hover:text-foreground" />
        )}
      </button>
    )
  }

  if (variant === 'dropdown') {
    return (
      <div className={`relative ${className}`}>
        <div className="space-y-1">
          {showLabels && (
            <div className="mb-3">
              <h4 className="text-card-foreground text-sm font-medium mb-1 flex items-center">
                <Sun className="w-4 h-4 mr-2" />
                {t('settings.theme.title')}
              </h4>
              <p className="text-muted-foreground text-xs">{t('settings.theme.subtitle')}</p>
            </div>
          )}
          
          <div className="space-y-2">
            {themes.map((themeOption) => {
              const Icon = themeOption.icon
              const isActive = theme === themeOption.id
              
              return (
                <button
                  key={themeOption.id}
                  onClick={() => setTheme(themeOption.id)}
                  className={`
                    w-full flex items-center justify-between px-3 py-2.5 rounded-glass text-sm 
                    transition-all duration-300 group
                    ${isActive
                      ? 'bg-gradient-primary text-white shadow-glow' 
                      : 'text-muted-foreground hover:text-card-foreground hover:bg-glass-300'
                    }
                  `}
                >
                  <span className="flex items-center">
                    <Icon className="w-4 h-4 mr-2 flex-shrink-0" />
                    <span className={`truncate ${isActive ? 'text-white' : 'text-current'}`}>{themeOption.name}</span>
                    {themeOption.id === 'system' && (
                      <span className={`ml-2 text-xs ${isActive ? 'text-white/60' : 'text-muted-foreground'}`}>
                        ({actualTheme === 'dark' ? '🌙' : '☀️'})
                      </span>
                    )}
                  </span>
                  {isActive && (
                    <div className="w-2 h-2 bg-white rounded-full flex-shrink-0" />
                  )}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  // Default button variant
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {showLabels && (
        <span className="text-muted-foreground text-sm font-medium">
          {t('settings.theme.title')}
        </span>
      )}
      <div className="flex bg-glass-100 backdrop-blur-glass rounded-full p-1 border border-white/20">
        {themes.map((themeOption) => {
          const Icon = themeOption.icon
          const isActive = theme === themeOption.id
          
          return (
            <button
              key={themeOption.id}
              onClick={() => setTheme(themeOption.id)}
              className={`
                px-3 py-1.5 text-sm font-medium rounded-full transition-all duration-300
                flex items-center space-x-1.5
                ${isActive
                  ? 'bg-gradient-primary text-white shadow-glow' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-glass-200'
                }
              `}
              title={themeOption.description}
            >
              <Icon className="w-3 h-3" />
              {showLabels && (
                <span className="hidden sm:inline whitespace-nowrap">
                  {themeOption.name}
                </span>
              )}
              {themeOption.id === 'system' && !showLabels && (
                <span className="text-xs">
                  {actualTheme === 'dark' ? '🌙' : '☀️'}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default ThemeToggle 