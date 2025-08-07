'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  actualTheme: 'light' | 'dark'
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('system')
  const [actualTheme, setActualTheme] = useState<'light' | 'dark'>('dark')
  const [mounted, setMounted] = useState(false)

  // Get the actual theme based on preference and system setting
  const getActualTheme = (themePreference: Theme): 'light' | 'dark' => {
    if (themePreference === 'system') {
      // Check if window exists (to prevent SSR issues)
      if (typeof window !== 'undefined') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      }
      // Default to dark theme during SSR
      return 'dark'
    }
    return themePreference
  }

  // Update the actual theme when preference changes
  useEffect(() => {
    if (!mounted) return
    
    const newActualTheme = getActualTheme(theme)
    setActualTheme(newActualTheme)
    
    // Apply theme to document
    const root = document.documentElement
    if (newActualTheme === 'dark') {
      root.classList.add('dark')
      root.classList.remove('light')
    } else {
      root.classList.add('light')
      root.classList.remove('dark')
    }
  }, [theme, mounted])

  // Listen for system theme changes when using 'system' preference
  useEffect(() => {
    if (!mounted) return
    
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      
      const handleChange = (e: MediaQueryListEvent) => {
        const newActualTheme = e.matches ? 'dark' : 'light'
        setActualTheme(newActualTheme)
        
        const root = document.documentElement
        if (newActualTheme === 'dark') {
          root.classList.add('dark')
          root.classList.remove('light')
        } else {
          root.classList.add('light')
          root.classList.remove('dark')
        }
      }
      
      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme, mounted])

  // Initialize theme on mount
  useEffect(() => {
    setMounted(true)
    
    // Get initial theme from localStorage or default to system
    const savedTheme = typeof window !== 'undefined' 
      ? localStorage.getItem('theme') as Theme | null 
      : null
    const initialTheme = savedTheme || 'system'
    
    // Update local state
    setThemeState(initialTheme)
    
    const newActualTheme = getActualTheme(initialTheme)
    setActualTheme(newActualTheme)
    
    // Apply initial theme to document
    const root = document.documentElement
    if (newActualTheme === 'dark') {
      root.classList.add('dark')
      root.classList.remove('light')
    } else {
      root.classList.add('light')
      root.classList.remove('dark')
    }
  }, [])

  // Save theme preference to localStorage
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', newTheme)
    }
    
    // If not mounted yet, update actualTheme immediately for initial render
    if (!mounted) {
      const newActualTheme = getActualTheme(newTheme)
      setActualTheme(newActualTheme)
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, actualTheme }}>
      {/* Prevent hydration mismatch by showing loading state until mounted */}
      {!mounted ? (
        <div className="min-h-screen bg-background text-foreground">
          {children}
        </div>
      ) : (
        children
      )}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
} 