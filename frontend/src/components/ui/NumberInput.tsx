'use client'

import { useState, useRef, useEffect } from 'react'
import { Plus, Minus } from 'lucide-react'

interface NumberInputProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
  label: string
  unit?: string
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function NumberInput({ 
  value, 
  onChange, 
  min = 0, 
  max = 999999, 
  step = 1,
  label, 
  unit = '',
  placeholder = '0',
  className = '', 
  disabled = false
}: NumberInputProps) {
  const [inputValue, setInputValue] = useState(value.toString())
  const inputRef = useRef<HTMLInputElement>(null)

  // value prop이 변경될 때 inputValue 동기화
  useEffect(() => {
    setInputValue(value.toString())
  }, [value])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    
    // 숫자와 소수점, 마이너스 기호만 허용
    const numericValue = newValue.replace(/[^0-9.-]/g, '')
    
    // 여러 소수점이나 마이너스 기호 방지
    const cleanValue = numericValue
      .replace(/\.(?=.*\.)/g, '') // 중복 소수점 제거
      .replace(/-(?=.*-)/g, '')   // 중복 마이너스 제거
      .replace(/(?!^)-/g, '')     // 처음이 아닌 위치의 마이너스 제거
    
    setInputValue(cleanValue)
    
    // 숫자 유효성 검사
    if (cleanValue === '' || cleanValue === '-' || cleanValue === '.') {
      return // 입력 중이면 기다림
    }
    
    const numValue = parseFloat(cleanValue)
    if (!isNaN(numValue) && numValue >= min && numValue <= max) {
      onChange(numValue)
    }
  }

  const handleInputBlur = () => {
    // 빈 값이면 최소값으로 설정
    if (inputValue === '' || inputValue === '-' || inputValue === '.') {
      const fallbackValue = Math.max(min, 0)
      setInputValue(fallbackValue.toString())
      onChange(fallbackValue)
      return
    }
    
    const numValue = parseFloat(inputValue)
    if (isNaN(numValue) || numValue < min || numValue > max) {
      // 유효하지 않은 값이면 이전 값으로 복원
      setInputValue(value.toString())
    } else {
      // 유효한 값이면 정규화
      const normalizedValue = Math.min(Math.max(numValue, min), max)
      setInputValue(normalizedValue.toString())
      if (normalizedValue !== value) {
        onChange(normalizedValue)
      }
    }
  }

  const handleIncrement = () => {
    if (disabled) return
    const newValue = Math.min(value + step, max)
    onChange(newValue)
  }

  const handleDecrement = () => {
    if (disabled) return
    const newValue = Math.max(value - step, min)
    onChange(newValue)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return
    
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      handleIncrement()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      handleDecrement()
    }
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-foreground">
        {label}
        {unit && <span className="text-muted-foreground ml-1">({unit})</span>}
      </label>
      <div className="relative w-full">
        {/* Input Field */}
        <input
          ref={inputRef}
          type="text"
          inputMode="decimal"
          pattern="[0-9]*\.?[0-9]*"
          value={inputValue}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full h-11 pl-10 pr-10 bg-card border border-border rounded-lg text-foreground text-sm text-center focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
        />

        {/* Decrement Button */}
        <button
          type="button"
          onClick={handleDecrement}
          disabled={disabled || value <= min}
          style={{ left: '8px' }}
          className="absolute top-1/2 transform -translate-y-1/2 h-8 w-8 bg-background border border-border hover:bg-gradient-to-r hover:from-accent-blue hover:to-accent-purple hover:text-white hover:border-transparent disabled:bg-muted/30 disabled:border-muted disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center group focus:outline-none focus:ring-1 focus:ring-accent-blue rounded-md z-10 shadow-sm hover:shadow-md"
        >
          <Minus className="w-4 h-4 text-foreground group-hover:text-white disabled:text-muted-foreground transition-all duration-200 group-hover:scale-110" />
        </button>

        {/* Increment Button */}
        <button
          type="button"
          onClick={handleIncrement}
          disabled={disabled || value >= max}
          style={{ right: '8px' }}
          className="absolute top-1/2 transform -translate-y-1/2 h-8 w-8 bg-background border border-border hover:bg-gradient-to-r hover:from-accent-blue hover:to-accent-purple hover:text-white hover:border-transparent disabled:bg-muted/30 disabled:border-muted disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center group focus:outline-none focus:ring-1 focus:ring-accent-blue rounded-md z-10 shadow-sm hover:shadow-md"
        >
          <Plus className="w-4 h-4 text-foreground group-hover:text-white disabled:text-muted-foreground transition-all duration-200 group-hover:scale-110" />
        </button>
      </div>
      
      {/* Range indicator */}
      <div className="text-xs text-muted-foreground">
        {min} - {max}
        {unit && ` ${unit}`}
      </div>
    </div>
  )
} 