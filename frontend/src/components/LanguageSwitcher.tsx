'use client'

import { useLanguageStore, Language } from '@/stores/useLanguageStore'
import { Globe } from 'lucide-react'

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguageStore()

  const languages = [
    { code: 'ko' as Language, label: 'KOR', flag: '🇰🇷' },
    { code: 'en' as Language, label: 'ENG', flag: '🇺🇸' }
  ]

  return (
    <div className="flex items-center space-x-2">
      <Globe className="w-4 h-4 text-muted-foreground" />
      <div className="flex bg-glass-100 backdrop-blur-glass rounded-full p-1 border border-white/20">
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => setLanguage(lang.code)}
            className={`
              px-3 py-1 text-sm font-medium rounded-full transition-all duration-300
              ${language === lang.code 
                ? 'bg-gradient-primary text-white shadow-glow' 
                : 'text-muted-foreground hover:text-foreground hover:bg-glass-200'
              }
            `}
          >
            <span className="flex items-center space-x-1">
              <span className="text-xs">{lang.flag}</span>
              <span>{lang.label}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  )
} 