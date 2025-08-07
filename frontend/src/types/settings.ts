export interface SettingsSection {
  id: string
  title: string
  subtitle?: string
  icon?: React.ComponentType<{ className?: string }>
  items: SettingItem[]
}

export interface SettingItem {
  id: string
  type: 'toggle' | 'select' | 'input' | 'button' | 'divider'
  title: string
  subtitle?: string
  icon?: React.ComponentType<{ className?: string }>
  value?: unknown
  options?: SettingOption[]
  onClick?: () => void
  onChange?: (value: unknown) => void
  disabled?: boolean
  visible?: boolean
}

export interface SettingOption {
  label: string
  value: unknown
  icon?: React.ComponentType<{ className?: string }>
  disabled?: boolean
}

export interface SettingsConfig {
  sections: SettingsSection[]
  collapsed?: boolean
  onClose?: () => void
}

export type LanguageCode = 'ko' | 'en'
export type ThemeMode = 'light' | 'dark' | 'system'

export interface UserSettings {
  language: LanguageCode
  theme: ThemeMode
  notifications: {
    enabled: boolean
    sound: boolean
    email: boolean
    push: boolean
  }
  privacy: {
    dataCollection: boolean
    analytics: boolean
    cookies: boolean
  }
  advanced: {
    debug: boolean
    apiUrl?: string
    cacheEnabled: boolean
  }
} 