import React, { forwardRef, useState } from 'react'

import cls from './Input.module.css'

export type InputVariant = 'primary' | 'secondary'
export type InputSize = 'small' | 'medium' | 'large'
export type InputType = 'text' | 'password' | 'email' | 'number' | 'tel' | 'search' | 'date' | 'time'

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: InputVariant // Вариант 
  size?: InputSize // Размер 
  type?: InputType // Тип
  label?: string // Label текст
  helperText?: string // Подсказка под инпутом
  error?: string // Текст ошибки
  disabled?: boolean // Флаг блокировки
  readOnly?: boolean // Флаг только для чтения
  startIcon?: React.ReactNode // Иконка слева
  endIcon?: React.ReactNode // Иконка справа
  clearable?: boolean // Кнопка очистки
  fullWidth?: boolean // Флаг полноширинного инпута
  maxLength?: number // Максимальное количество символов
  showCounter?: boolean // Показывать счетчик символов
  className?: string // Дополнительные классы для контейнера
  minDate?: string // Минимальная дата (для type="date")
  maxDate?: string // Максимальная дата (для type="date")
  onClear?: () => void // Callback при очистке
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  variant = 'primary',
  size = 'medium',
  type = 'text',
  label,
  helperText,
  error,
  disabled = false,
  readOnly = false,
  startIcon,
  endIcon,
  clearable = false,
  fullWidth = false,
  maxLength,
  showCounter = false,
  minDate,
  maxDate,
  className = '',
  value,
  onChange,
  onClear,
  ...rest
}, ref) => {
  const [showPassword, setShowPassword] = useState(false)
  const inputType = type === 'password' && showPassword ? 'text' : type

  const handleClear = () => {
    if (onClear) {
      onClear()
    } else if (onChange) {
      const event = {
        target: { value: '' },
      } as React.ChangeEvent<HTMLInputElement>
      onChange(event)
    }
  }

  const handleTogglePassword = () => {
    setShowPassword(!showPassword)
  }

  const getInputClasses = () => {
    const classes = [
      cls.input,
      cls[variant],
      cls[size],
      error ? cls.error : '',
      disabled ? cls.disabled : '',
      readOnly ? cls.readOnly : '',
      startIcon ? cls.withStartIcon : '',
      endIcon || clearable || type === 'password' ? cls.withEndIcon : '',
      fullWidth ? cls.fullWidth : '',
    ]
    return classes.filter(Boolean).join(' ')
  }

  const getWrapperClasses = () => {
    const classes = [
      cls.inputWrapper,
      fullWidth ? cls.fullWidth : '',
      className,
    ]
    return classes.filter(Boolean).join(' ')
  }

  const currentValue = typeof value === 'string' ? value : ''
  const charCount = currentValue.length

  // Форматирование значения для типа date
  const formatDateValue = (val: string) => {
    if (type === 'date' && val) {
      return val.split('T')[0] // Убираем время, если оно есть
    }
    return val
  }

  return (
    <div className={getWrapperClasses()}>
      {label && (
        <label className={cls.label}>
          {label}
          {maxLength && showCounter && (
            <span className={cls.counter}>
              {charCount}/{maxLength}
            </span>
          )}
        </label>
      )}
      
      <div className={cls.inputContainer}>
        {startIcon && (
          <span className={cls.startIcon}>
            {startIcon}
          </span>
        )}
        
        <input
          ref={ref}
          type={inputType}
          className={getInputClasses()}
          disabled={disabled}
          readOnly={readOnly}
          value={type === 'date' ? formatDateValue(currentValue) : currentValue}
          onChange={onChange}
          maxLength={maxLength}
          min={type === 'date' ? minDate : undefined}
          max={type === 'date' ? maxDate : undefined}
          aria-invalid={!!error}
          aria-describedby={error || helperText ? 'input-description' : undefined}
          {...rest}
        />
        
        {(endIcon || clearable || type === 'password') && (
          <span className={cls.endIcons}>
            {clearable && value && !disabled && !readOnly && (
              <button
                type="button"
                className={cls.clearButton}
                onClick={handleClear}
                aria-label="Очистить поле"
              >
                ✕
              </button>
            )}
            
            {type === 'password' && !disabled && (
              <button
                type="button"
                className={cls.passwordToggle}
                onClick={handleTogglePassword}
                aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            )}
            
            {type === 'date' && !endIcon && !disabled && !readOnly && (
              <span className={cls.dateIcon} aria-hidden="true">
                📅
              </span>
            )}
            
            {endIcon && (
              <span className={cls.endIcon}>
                {endIcon}
              </span>
            )}
          </span>
        )}
      </div>
      
      {(error || helperText || (maxLength && showCounter && !label)) && (
        <div className={cls.footer}>
          {error ? (
            <span className={cls.errorText} id="input-description">
              {error}
            </span>
          ) : helperText ? (
            <span className={cls.helperText} id="input-description">
              {helperText}
            </span>
          ) : null}
          
          {maxLength && showCounter && !label && (
            <span className={cls.counter}>
              {charCount}/{maxLength}
            </span>
          )}
        </div>
      )}
    </div>
  )
})

Input.displayName = 'Input'