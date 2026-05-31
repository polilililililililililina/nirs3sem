import cls from './Loader.module.css'

type LoaderSize = 'sm' | 'md' | 'lg'

interface LoaderProps {
  size?: LoaderSize
  label?: string
  className?: string
}

export const Loader = ({ size = 'md', label, className }: LoaderProps) => {
  return (
    <div className={`${cls.loader} ${cls[size]} ${className || ''}`} role="status" aria-live="polite">
      <div className={cls.scanner}>
        <div className={cls.ring} />
        <div className={cls.core} />
        <div className={cls.beam} />
      </div>
      {label && <span className={cls.label}>{label}</span>}
    </div>
  )
}
