'use client'

import { Globe, Settings, Check, Sun } from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import { LanguageCode } from '@/types/settings'
import ThemeToggle from './ThemeToggle'

interface SettingsDropdownProps {
  isOpen: boolean
  isCollapsed: boolean
  onClose: () => void
  onLanguageChange: (lang: LanguageCode) => void
  onMobileClose: () => void
}

interface LanguageButtonProps {
  language: LanguageCode
  currentLanguage: LanguageCode
  isCollapsed: boolean
  label: string
  onClick: () => void
}

export default function SettingsDropdown({
  isOpen,
  isCollapsed,
  onClose,
  onLanguageChange,
  onMobileClose
}: SettingsDropdownProps) {
  const { t, language } = useTranslation()

  const handleLanguageChange = (lang: LanguageCode) => {
    onLanguageChange(lang)
  }

  if (!isOpen) return null

  return (
    <>
      {/* Settings Dropdown */}
      <div 
        className={`absolute top-16 z-50 bg-card backdrop-blur-glass-xl border border-border rounded-glass-lg p-4 shadow-glass-lg ${
          isCollapsed 
            ? 'w-52' 
            : 'w-56'
        } max-w-sm`} 
        style={{
          backgroundColor: 'var(--card)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px var(--border)',
          left: isCollapsed ? '72px' : '16px', // 축소: 사이드바 밖, 확장: 사이드바 안쪽 여유공간
        }}>
        {/* Settings Header */}
        {!isCollapsed && (
          <div className="mb-4">
            <h3 className="text-card-foreground font-semibold text-sm mb-1 flex items-center">
              <Settings className="w-4 h-4 mr-2" />
              {t('settings.title')}
            </h3>
            <p className="text-muted-foreground text-xs">{t('settings.subtitle')}</p>
          </div>
        )}
        
        {/* Language Settings Section */}
        <div className="mb-4">
          <h4 className="text-card-foreground text-xs font-medium mb-2 flex items-center">
            <Globe className="w-3 h-3 mr-1" />
            {t('settings.language.title')}
          </h4>
          {!isCollapsed && (
            <p className="text-muted-foreground text-xs mb-3">{t('settings.language.subtitle')}</p>
          )}
          
          <div className="space-y-1">
            <LanguageButton
              language="ko"
              currentLanguage={language}
              isCollapsed={isCollapsed}
              label={t('settings.language.korean')}
              onClick={() => handleLanguageChange('ko')}
            />
            <LanguageButton
              language="en"
              currentLanguage={language}
              isCollapsed={isCollapsed}
              label={t('settings.language.english')}
              onClick={() => handleLanguageChange('en')}
            />
          </div>
        </div>

        {/* Theme Settings Section */}
        {!isCollapsed && (
          <div className="pt-3 border-t border-border">
            <ThemeToggle 
              variant="dropdown" 
              showLabels={true}
              className="w-full"
            />
          </div>
        )}

        {/* Notification Settings - Coming Soon */}
        {!isCollapsed && (
          <div className="mt-4 pt-3 border-t border-border">
            <div className="opacity-50">
              <h4 className="text-muted-foreground text-xs font-medium mb-1 flex items-center">
                <Sun className="w-3 h-3 mr-1" />
                {t('settings.notifications.title')}
              </h4>
              <p className="text-muted-foreground text-xs mb-2">{t('settings.notifications.subtitle')}</p>
              <div className="text-xs text-muted-foreground italic">Coming Soon...</div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function LanguageButton({
  language,
  currentLanguage,
  isCollapsed,
  label,
  onClick
}: LanguageButtonProps) {
  const isActive = currentLanguage === language

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-glass text-sm transition-all duration-300 ${
        isActive
          ? 'bg-gradient-primary text-white shadow-glow' 
          : 'text-muted-foreground hover:text-card-foreground hover:bg-glass-300'
      }`}
    >
      <span className="flex items-center">
        <Globe className="w-4 h-4 mr-2 flex-shrink-0" />
        <span className="truncate text-current">{label}</span>
      </span>
      {isActive && <Check className="w-4 h-4 flex-shrink-0 text-white" />}
    </button>
  )
} 