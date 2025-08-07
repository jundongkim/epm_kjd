'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Zap, Menu, X } from 'lucide-react'
import { useTranslation } from '@/hooks/useTranslation'
import LanguageSwitcher from './LanguageSwitcher'
import ThemeToggle from './ThemeToggle'

export default function Navigation() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { t } = useTranslation()

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navItems = [
    { name: t('nav.home'), href: '/' },
    { name: t('nav.aiAdvisor'), href: '/aiadvisor' },
    { name: t('nav.features'), href: '#features' },
    { name: t('nav.techStack'), href: '#tech' },
    { name: t('nav.contact'), href: '#contact' },
  ]

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled 
        ? 'glass-nav backdrop-blur-glass-xl shadow-glass-lg' 
        : 'bg-glass-50 backdrop-blur-glass-sm'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-primary rounded-full blur-md opacity-60"></div>
              <div className="relative w-10 h-10 bg-gradient-primary rounded-full flex items-center justify-center shadow-glow">
                <Zap className="w-5 h-5 text-white" />
              </div>
            </div>
            <div className="flex flex-col">
              <h1 className="text-lg font-black text-foreground tracking-tight">
                DX-AI <span className="gradient-text">Manufacturing</span>
              </h1>
              <p className="text-xs text-muted-foreground font-medium">Copilot</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4 lg:space-x-6 xl:space-x-8">
            {navItems.map((item) => (
              item.href.startsWith('/') ? (
                <Link
                  key={item.name}
                  href={item.href}
                  className="relative text-muted-foreground hover:text-foreground transition-all duration-300 font-medium group whitespace-nowrap"
                >
                  {item.name}
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-primary transition-all duration-300 group-hover:w-full"></span>
                </Link>
              ) : (
                <a
                  key={item.name}
                  href={item.href}
                  className="relative text-muted-foreground hover:text-foreground transition-all duration-300 font-medium group whitespace-nowrap"
                >
                  {item.name}
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-primary transition-all duration-300 group-hover:w-full"></span>
                </a>
              )
            ))}
          </div>

          {/* CTA Button, Theme Toggle & Language Switcher */}
          <div className="hidden md:flex items-center space-x-2 lg:space-x-3 xl:space-x-4">
            <ThemeToggle variant="compact" showLabels={false} />
            <LanguageSwitcher />
            <Link href="/copilot/data-generation" className="btn-primary hover:scale-105 transition-transform duration-300 text-sm lg:text-base px-3 lg:px-4">
              {t('nav.getStarted')}
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-glass bg-glass-200 hover:bg-glass-300 transition-all duration-300"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6 text-foreground" />
            ) : (
              <Menu className="w-6 h-6 text-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <div className={`md:hidden transition-all duration-300 overflow-hidden ${
        isMobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="px-4 pt-2 pb-6 space-y-1 bg-glass-100 backdrop-blur-glass-md border-t border-glass-border">
          {navItems.map((item) => (
            item.href.startsWith('/') ? (
              <Link
                key={item.name}
                href={item.href}
                className="block px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-glass-200 rounded-glass-sm transition-all duration-300"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {item.name}
              </Link>
            ) : (
              <a
                key={item.name}
                href={item.href}
                className="block px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-glass-200 rounded-glass-sm transition-all duration-300"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {item.name}
              </a>
            )
          ))}
          <div className="flex flex-col space-y-3 pt-4">
            <div className="flex justify-center space-x-4">
              <ThemeToggle variant="button" showLabels={false} className="flex-1" />
            </div>
            <div className="flex justify-center pb-2">
              <LanguageSwitcher />
            </div>
            <Link href="/copilot/data-generation" className="btn-primary w-full justify-center flex items-center">
              {t('nav.getStarted')}
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
} 