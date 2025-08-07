'use client'

import { Check } from 'lucide-react'

interface CheckboxProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  disabled?: boolean
  className?: string
}

export function Checkbox({ 
  checked, 
  onChange, 
  label, 
  disabled = false,
  className = '' 
}: CheckboxProps) {
  return (
    <label className={`flex items-center space-x-3 cursor-pointer group ${disabled ? 'cursor-not-allowed opacity-50' : ''} ${className}`}>
      <div className="relative flex-shrink-0">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => !disabled && onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        <div className={`
          w-5 h-5 rounded border-2 transition-all duration-200 flex items-center justify-center
          ${checked 
            ? 'bg-gradient-to-r from-accent-blue to-accent-purple border-transparent shadow-md' 
            : 'bg-background border-border hover:border-accent-blue'
          }
          ${disabled ? '' : 'group-hover:shadow-sm'}
        `}>
          {checked && (
            <Check className="w-3 h-3 text-white font-bold" strokeWidth={3} />
          )}
        </div>
      </div>
      <span className={`text-sm select-none ${checked ? 'text-foreground font-medium' : 'text-muted-foreground'} transition-colors duration-200`}>
        {label}
      </span>
    </label>
  )
} 