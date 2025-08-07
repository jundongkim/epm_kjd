'use client'

import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { ChevronDown, X, Check } from 'lucide-react'

// ============================
// 단일 선택 Select 컴포넌트
// ============================

type SelectOption = {
  value: string
  label: string
}

interface SelectProps {
  value: string
  onChange: (value: string) => void
  options: string[] | SelectOption[]
  label: string
  placeholder?: string
  className?: string
}

export function Select({
  value,
  onChange,
  options,
  label,
  placeholder = "선택하세요",
  className = ''
}: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 4,
        left: rect.left + window.scrollX,
        width: rect.width
      })
    }
  }, [isOpen])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (buttonRef.current && !buttonRef.current.contains(target)) {
        // 드롭다운 메뉴 클릭이 아닌 경우에만 닫기
        const dropdown = document.querySelector('[data-dropdown-portal="true"]')
        if (!dropdown || !dropdown.contains(target)) {
          setIsOpen(false)
        }
      }
    }

    const handleScroll = () => {
      if (isOpen && buttonRef.current) {
        const rect = buttonRef.current.getBoundingClientRect()
        setDropdownPosition({
          top: rect.bottom + window.scrollY + 4,
          left: rect.left + window.scrollX,
          width: rect.width
        })
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      window.addEventListener('scroll', handleScroll, true)
      window.addEventListener('resize', handleScroll)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
        window.removeEventListener('scroll', handleScroll, true)
        window.removeEventListener('resize', handleScroll)
      }
    }
  }, [isOpen])

  const DropdownPortal = () => {
    if (!mounted || !isOpen) return null

    return createPortal(
      <>
        {/* 투명한 오버레이 - 외부 클릭 감지 */}
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm"
          style={{ zIndex: 99999998 }}
          onClick={() => setIsOpen(false)}
        />

        {/* 드롭다운 메뉴 */}
        <div
          data-dropdown-portal="true"
          className="fixed bg-card border border-border rounded-lg shadow-lg backdrop-blur-sm overflow-y-auto"
          style={{
            top: dropdownPosition.top,
            left: dropdownPosition.left,
            width: dropdownPosition.width,
            maxHeight: 'min(400px, calc(100vh - 200px))',
            zIndex: 99999999,
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(148, 163, 184, 0.5) transparent'
          } as React.CSSProperties & { scrollbarWidth?: string; scrollbarColor?: string }}
          onClick={(e) => e.stopPropagation()}
        >
          {options.map((option, index) => (
            typeof option === 'string' ? (
            <button
              key={option}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onChange(option)
                setIsOpen(false)
              }}
              className="w-full px-4 py-2.5 text-left text-foreground text-sm transition-all duration-200 border-b border-border last:border-b-0 hover:bg-gradient-primary hover:text-white flex items-center justify-between"
              style={{
                backgroundColor: 'transparent',
                borderRadius: index === 0 ? '8px 8px 0 0' : index === options.length - 1 ? '0 0 8px 8px' : '0'
              }}
            >
              <span>{option}</span>
              {value === option && <Check className="w-4 h-4 text-accent-blue" />}
            </button>
            ) : (
              <button
                key={option.value}
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  onChange(option.value)
                  setIsOpen(false)
                }}
                className="w-full px-4 py-2.5 text-left text-foreground text-sm transition-all duration-200 border-b border-border last:border-b-0 hover:bg-gradient-primary hover:text-white flex items-center justify-between"
                style={{
                  backgroundColor: 'transparent',
                  borderRadius: index === 0 ? '8px 8px 0 0' : index === options.length - 1 ? '0 0 8px 8px' : '0'
                }}
              >
                <span>{option.label}</span>
                {value === option.value && <Check className="w-4 h-4 text-accent-blue" />}
              </button>
            )
          ))}
        </div>
      </>,
      document.body
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <div className="relative">
        <button
          ref={buttonRef}
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm hover:bg-muted/50 hover:border-border transition-all duration-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
        >
          <span className={value ? 'text-foreground' : 'text-muted-foreground'}>
            {(() => {
              if (!value) return placeholder
              
              // options가 SelectOption[]인 경우 label 찾기
              if (Array.isArray(options) && options.length > 0 && typeof options[0] === 'object') {
                const option = (options as SelectOption[]).find(opt => opt.value === value)
                return option ? option.label : value
              }
              
              // options가 string[]인 경우 그대로 표시
              return value
            })()}
          </span>
          <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180 text-accent-blue' : 'text-muted-foreground'}`} />
        </button>
        <DropdownPortal />
      </div>
    </div>
  )
}

// ============================
// 다중 선택 MultiSelect 컴포넌트
// ============================

interface MultiSelectProps {
  value: string[]
  onChange: (value: string[]) => void
  options: string[]
  label: string
  placeholder?: string
  className?: string
  maxDisplay?: number
}

export function MultiSelect({
  value,
  onChange,
  options,
  label,
  placeholder = "선택하세요",
  className = '',
  maxDisplay = 3
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 4,
        left: rect.left + window.scrollX,
        width: rect.width
      })
    }
  }, [isOpen])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (buttonRef.current && !buttonRef.current.contains(target)) {
        // 드롭다운 메뉴 클릭이 아닌 경우에만 닫기
        const dropdown = document.querySelector('[data-dropdown-portal="true"]')
        if (!dropdown || !dropdown.contains(target)) {
          setIsOpen(false)
        }
      }
    }

    const handleScroll = () => {
      if (isOpen && buttonRef.current) {
        const rect = buttonRef.current.getBoundingClientRect()
        setDropdownPosition({
          top: rect.bottom + window.scrollY + 4,
          left: rect.left + window.scrollX,
          width: rect.width
        })
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      window.addEventListener('scroll', handleScroll, true)
      window.addEventListener('resize', handleScroll)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
        window.removeEventListener('scroll', handleScroll, true)
        window.removeEventListener('resize', handleScroll)
      }
    }
  }, [isOpen])

  const toggleOption = (option: string) => {
    if (value.includes(option)) {
      onChange(value.filter(item => item !== option))
    } else {
      onChange([...value, option])
    }
  }

  const removeOption = (option: string) => {
    onChange(value.filter(item => item !== option))
  }

  const getDisplayText = () => {
    if (value.length === 0) return placeholder
    if (value.length <= maxDisplay) {
      return value.join(', ')
    }
    return `${value.slice(0, maxDisplay).join(', ')} +${value.length - maxDisplay}개`
  }

  const DropdownPortal = () => {
    if (!mounted || !isOpen) return null

    return createPortal(
      <>
        {/* 투명한 오버레이 - 외부 클릭 감지 */}
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm"
          style={{ zIndex: 99999998 }}
          onClick={() => setIsOpen(false)}
        />

        {/* 드롭다운 메뉴 */}
        <div
          data-dropdown-portal="true"
          className="fixed bg-card border border-border rounded-lg shadow-lg backdrop-blur-sm overflow-y-auto"
          style={{
            top: dropdownPosition.top,
            left: dropdownPosition.left,
            width: dropdownPosition.width,
            maxHeight: 'min(400px, calc(100vh - 200px))',
            zIndex: 99999999,
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(148, 163, 184, 0.5) transparent'
          } as React.CSSProperties & { scrollbarWidth?: string; scrollbarColor?: string }}
          onClick={(e) => e.stopPropagation()}
        >
          {options.map((option, index) => {
            const isSelected = value.includes(option)
            return (
              <button
                key={option}
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  toggleOption(option)
                }}
                className={`w-full px-4 py-2.5 text-left text-sm transition-all duration-200 border-b border-border last:border-b-0 flex items-center justify-between ${
                  isSelected
                    ? 'bg-gradient-primary text-white'
                    : 'text-foreground hover:bg-muted/50'
                }`}
                style={{
                  borderRadius: index === 0 ? '8px 8px 0 0' : index === options.length - 1 ? '0 0 8px 8px' : '0'
                }}
              >
                <span>{option}</span>
                {isSelected && <Check className="w-4 h-4" />}
              </button>
            )
          })}
        </div>
      </>,
      document.body
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <div className="relative">
        <button
          ref={buttonRef}
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between px-4 py-2.5 bg-card backdrop-blur-sm border border-border rounded-lg text-foreground text-sm hover:bg-muted/50 hover:border-border transition-all duration-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
        >
          <span className={value.length > 0 ? 'text-foreground' : 'text-muted-foreground'}>
            {getDisplayText()}
          </span>
          <div className="flex items-center gap-2">
            {value.length > 0 && (
              <span className="text-xs bg-accent-blue text-white px-2 py-1 rounded-full">
                {value.length}
              </span>
            )}
            <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180 text-accent-blue' : 'text-muted-foreground'}`} />
          </div>
        </button>
        <DropdownPortal />
      </div>

      {/* 선택된 아이템들 표시 */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {value.map(item => (
            <div
              key={item}
              className="inline-flex items-center gap-1 px-3 py-1 bg-accent-blue/10 text-accent-blue rounded-full text-sm"
            >
              <span>{item}</span>
              <button
                onClick={() => removeOption(item)}
                className="hover:bg-accent-blue/20 rounded-full p-1 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}