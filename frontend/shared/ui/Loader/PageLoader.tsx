import { Loader } from './Loader'
import cls from './PageLoader.module.css'

interface PageLoaderProps {
  label?: string
}

export const PageLoader = ({ label = 'Загрузка...' }: PageLoaderProps) => {
  return (
    <div className={cls.overlay}>
      <Loader size="lg" label={label} />
    </div>
  )
}
