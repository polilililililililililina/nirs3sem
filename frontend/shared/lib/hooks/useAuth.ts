import { useCallback, useEffect, useState } from 'react'

import { useRouter } from 'next/router'

import { api } from '@shared/api/api'
import { AuthUser, UserRole } from '@shared/lib/auth/types'

interface UseAuthResult {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  logout: () => void
  refreshUser: () => Promise<void>
}

export const useAuth = (): UseAuthResult => {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const { data } = await api.get<AuthUser>('/users/me')
      setUser(data)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    router.reload()
    router.push('/login')
  }, [router])

  return {
    user,
    isLoading,
    isAuthenticated: Boolean(user),
    logout,
    refreshUser,
  }
}

export const useRequireAuth = (roles?: UserRole[]): UseAuthResult => {
  const auth = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (auth.isLoading) return

    if (!auth.isAuthenticated) {
      const redirect = encodeURIComponent(router.asPath)
      router.replace(`/login?redirect=${redirect}`)
      return
    }

    if (roles && auth.user && !roles.includes(auth.user.role)) {
      router.replace('/403')
    }
  }, [auth.isLoading, auth.isAuthenticated, auth.user, roles, router])

  return auth
}
