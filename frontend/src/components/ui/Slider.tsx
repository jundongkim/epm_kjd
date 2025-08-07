'use client'

import { useState, useRef, useEffect, useCallback } from 'react'

// ============================
// 단일 값 슬라이더 (Slider)
// ============================

interface SliderProps {
  min: number
  max: number
  step?: number
  value: number
  onChange: (value: number) => void
  label: string
  unit?: string
  className?: string
}

export function Slider({ 
  min, 
  max, 
  step = 1, 
  value, 
  onChange, 
  label, 
  unit = '', 
  className = '' 
}: SliderProps) {
  const sliderRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const percentage = ((value - min) / (max - min)) * 100

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    updateValue(e)
  }

  const updateValue = useCallback((e: MouseEvent | React.MouseEvent) => {
    if (!sliderRef.current) return

    const rect = sliderRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const width = rect.width
    const newPercentage = Math.max(0, Math.min(100, (x / width) * 100))
    const newValue = min + (newPercentage / 100) * (max - min)
    const steppedValue = Math.round(newValue / step) * step
    
    onChange(Math.max(min, Math.min(max, steppedValue)))
  }, [min, max, step, onChange])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      updateValue(e)
    }
  }, [isDragging, updateValue])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <div className="px-3">
        <div 
          ref={sliderRef}
          className="relative h-6 cursor-pointer"
          onMouseDown={handleMouseDown}
        >
          {/* Track */}
          <div className="absolute top-1/2 transform -translate-y-1/2 w-full h-2 bg-muted rounded-full border border-border" />
          
          {/* Fill */}
          <div 
            className="absolute top-1/2 transform -translate-y-1/2 h-2 bg-gradient-to-r from-accent-blue to-accent-purple rounded-full"
            style={{ width: `${percentage}%` }}
          />
          
          {/* Thumb */}
          <div 
            className="absolute top-1/2 transform -translate-y-1/2 w-5 h-5 bg-gradient-to-r from-accent-blue to-accent-purple rounded-full border-2 border-background cursor-pointer shadow-lg"
            style={{ left: `calc(${percentage}% - 10px)` }}
          />
        </div>
        
        <div className="flex justify-between text-sm text-muted-foreground mt-2">
          <span>{min} {unit}</span>
          <span className="font-medium text-foreground">{value.toFixed(step < 1 ? 1 : 0)} {unit}</span>
          <span>{max} {unit}</span>
        </div>
      </div>
    </div>
  )
}

// ============================
// 범위 슬라이더 (RangeSlider)
// ============================

interface RangeSliderProps {
  min: number
  max: number
  step?: number
  value: [number, number]
  onChange: (value: [number, number]) => void
  label: string
  unit?: string
  className?: string
}

export function RangeSlider({ 
  min, 
  max, 
  step = 1, 
  value, 
  onChange, 
  label, 
  unit = '', 
  className = '' 
}: RangeSliderProps) {
  const sliderRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState<'min' | 'max' | null>(null)

  const [minVal, maxVal] = value
  const minPercentage = ((minVal - min) / (max - min)) * 100
  const maxPercentage = ((maxVal - min) / (max - min)) * 100

  const handleMouseDown = (type: 'min' | 'max') => (e: React.MouseEvent) => {
    setIsDragging(type)
    updateValue(e, type)
  }

  const updateValue = (e: MouseEvent | React.MouseEvent, type: 'min' | 'max') => {
    if (!sliderRef.current) return

    const rect = sliderRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const width = rect.width
    const newPercentage = Math.max(0, Math.min(100, (x / width) * 100))
    const newValue = min + (newPercentage / 100) * (max - min)
    const steppedValue = Math.round(newValue / step) * step

    if (type === 'min') {
      onChange([Math.max(min, Math.min(steppedValue, maxVal - step)), maxVal])
    } else {
      onChange([minVal, Math.max(minVal + step, Math.min(max, steppedValue))])
    }
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      updateValue(e, isDragging)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(null)
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-foreground">{label}</label>
      <div className="px-3">
        <div 
          ref={sliderRef}
          className="relative h-6 cursor-pointer"
        >
          {/* Track */}
          <div className="absolute top-1/2 transform -translate-y-1/2 w-full h-2 bg-muted rounded-full border border-border" />
          
          {/* Fill */}
          <div 
            className="absolute top-1/2 transform -translate-y-1/2 h-2 bg-gradient-to-r from-accent-blue to-accent-purple rounded-full"
            style={{
              left: `${minPercentage}%`,
              right: `${100 - maxPercentage}%`,
            }}
          />
          
          {/* Min Thumb */}
          <div 
            className="absolute top-1/2 transform -translate-y-1/2 w-5 h-5 bg-gradient-to-r from-accent-blue to-accent-purple rounded-full border-2 border-background cursor-pointer shadow-lg"
            style={{ left: `calc(${minPercentage}% - 10px)` }}
            onMouseDown={handleMouseDown('min')}
          />
          
          {/* Max Thumb */}
          <div 
            className="absolute top-1/2 transform -translate-y-1/2 w-5 h-5 bg-gradient-to-r from-accent-blue to-accent-purple rounded-full border-2 border-background cursor-pointer shadow-lg"
            style={{ left: `calc(${maxPercentage}% - 10px)` }}
            onMouseDown={handleMouseDown('max')}
          />
        </div>
        
        <div className="flex justify-between text-sm text-muted-foreground mt-2">
          <span>{minVal.toFixed(step < 1 ? 1 : 0)} {unit}</span>
          <span>{maxVal.toFixed(step < 1 ? 1 : 0)} {unit}</span>
        </div>
      </div>
    </div>
  )
} 