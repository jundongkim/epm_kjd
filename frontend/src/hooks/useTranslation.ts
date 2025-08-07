import { useEffect, useState } from 'react'
import { useLanguageStore } from '@/stores/useLanguageStore'
import { translations } from '@/locales'

export const useTranslation = () => {
  const [isHydrated, setIsHydrated] = useState(false)
  const language = useLanguageStore(state => state.language)
  
  // Wait for hydration to complete
  useEffect(() => {
    setIsHydrated(true)
  }, [])
  
  const t = (key: string): any => {
    const keys = key.split('.')
    // Use 'ko' as default during SSR to prevent hydration mismatch
    const currentLanguage = isHydrated ? language : 'ko'
    let value: any = translations[currentLanguage]
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k]
      } else {
        // Fallback to English if key not found
        let fallbackValue: any = translations.en
        for (const k of keys) {
          if (fallbackValue && typeof fallbackValue === 'object' && k in fallbackValue) {
            fallbackValue = fallbackValue[k]
          } else {
            return key // Return key if not found in any language
          }
        }
        return fallbackValue
      }
    }
    
    return value || key
  }

  const tArray = (key: string): string[] => {
    const result = t(key)
    return Array.isArray(result) ? result : []
  }

  return { t, tArray, language: isHydrated ? language : 'ko' }
} 