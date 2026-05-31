import { useEffect } from 'react'

import { useRouter } from 'next/router'

import { AuthForm } from '@features/Auth/AuthForm/AuthForm'

import { useAuth } from '@shared/lib/hooks/useAuth'

const LoginPage = () => {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      const redirect = typeof router.query.redirect === 'string' ? router.query.redirect : '/'
      router.replace(redirect)
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading || isAuthenticated) {
    return <div>Загрузка...</div>
  }

  return (
    <div>
      <AuthForm />
    </div>
  )
}

export default LoginPage
