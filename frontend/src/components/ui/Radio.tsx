'use client'

interface RadioProps {
  checked: boolean
  onChange: (value: string) => void
  value: string
  name: string
  label: string
  disabled?: boolean
  className?: string
}

export function Radio({ 
  checked, 
  onChange, 
  value,
  name,
  label, 
  disabled = false,
  className = '' 
}: RadioProps) {
  return (
    <label className={`flex items-center space-x-3 cursor-pointer group ${disabled ? 'cursor-not-allowed opacity-50' : ''} ${className}`}>
      <div className="relative flex-shrink-0">
        <input
          type="radio"
          name={name}
          value={value}
          checked={checked}
          onChange={(e) => !disabled && onChange(e.target.value)}
          disabled={disabled}
          className="sr-only"
        />
        <div className={`
          w-5 h-5 rounded-full border-2 transition-all duration-200 flex items-center justify-center
          ${checked 
            ? 'bg-gradient-to-r from-accent-blue to-accent-purple border-transparent shadow-md' 
            : 'bg-background border-border hover:border-accent-blue'
          }
          ${disabled ? '' : 'group-hover:shadow-sm'}
        `}>
          {checked && (
            <div className="w-2 h-2 bg-white rounded-full" />
          )}
        </div>
      </div>
      <span className={`text-sm select-none ${checked ? 'text-foreground font-medium' : 'text-muted-foreground'} transition-colors duration-200`}>
        {label}
      </span>
    </label>
  )
}

interface RadioGroupProps {
  value: string
  onChange: (value: string) => void
  name: string
  options: { value: string; label: string; disabled?: boolean }[]
  className?: string
}

export function RadioGroup({ 
  value, 
  onChange, 
  name, 
  options, 
  className = '' 
}: RadioGroupProps) {
  return (
    <div className={`space-y-2 ${className}`}>
      {options.map((option) => (
        <Radio
          key={option.value}
          checked={value === option.value}
          onChange={onChange}
          value={option.value}
          name={name}
          label={option.label}
          disabled={option.disabled}
        />
      ))}
    </div>
  )
} 