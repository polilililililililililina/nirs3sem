import { ButtonHTMLAttributes, FC } from 'react'

import cls from './Button.module.css'

export type ButtonVariant = 'primary' | 'secondary'
export type ButtonSize = 'small' | 'medium' | 'large'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant // Вариант кнопки
  size?: ButtonSize // Размер кнопки
  loading?: boolean // Флаг загрузки
  disabled?: boolean // Флаг блокировки
  children: React.ReactNode // Текст кнопки
  className?: string // Дополнительные классы
  icon?: React.ReactNode // Иконка перед текстом
  fullWidth?: boolean // Флаг полноширинной кнопки
}

export const Button: FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled = false,
  children,
  className = '',
  icon,
  fullWidth = false,
  type = 'button',
  onClick,
  ...rest
}) => {
  const buttonClasses = [
    cls.button,
    cls[variant],
    cls[size],
    fullWidth ? cls.fullWidth : '',
    loading ? cls.loading : '',
    className
  ]
    .filter(Boolean)
    .join(' ')

  const isDisabled = disabled || loading

  return (
    <button
      type={type}
      className={buttonClasses}
      disabled={isDisabled}
      onClick={onClick}
      {...rest}
    >
      {loading && <span className={cls.loader} />}
      {icon && !loading && <span className={cls.icon}>{icon}</span>}
      <span className={cls.content}>{children}</span>
    </button>
  )
}