import { ReactNode, useMemo, useState } from 'react'

import Link from 'next/link'
import { useRouter } from 'next/router'

import { useAuth } from '@shared/lib/hooks/useAuth'
import { PageLoader } from '@shared/ui/Loader'

import cls from './Layout.module.css'

interface NavItem {
  href: string
  label: string
}

interface LayoutProps {
  children: ReactNode
}

export const Layout = ({ children }: LayoutProps) => {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useAuth()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const visibleItems = useMemo(() => {
    const items = [
      { href: '/', label: 'Главная' },
      { href: '/knowledge', label: 'База знаний' },
    ]

    if (isAuthenticated) {
      items.push({ href: '/history', label: 'История' })
      items.push({ href: '/compare', label: 'Сравнение' })
      items.push({ href: '/profile', label: 'Профиль' })
    }

    if (isAuthenticated && user && user.role === 'doctor') {
      items.push({ href: '/knowledge/edit', label: 'Редактор статей' })
    }

    if (isAuthenticated && user && user.role === 'admin') {
      items.push({ href: '/admin', label: 'Админ' })
    }

    if (!isAuthenticated) items.push({ href: '/login', label: 'Вход' })

    return items
  }, [isAuthenticated, user])

  const isActive = (href: string) => {
    if (href === '/') {
      return router.pathname === '/'
    }

    return router.pathname === href || router.pathname.startsWith(`${href}/`)
  }

  const renderLink = (item: NavItem, mobile = false) => {
    const active = isActive(item.href)
    const className = mobile
      ? active
        ? cls.sidebarLinkActive
        : cls.sidebarLink
      : active
        ? cls.navLinkActive
        : cls.navLink

    return (
      <Link
        key={item.href}
        href={item.href}
        className={className}
        onClick={() => setIsMenuOpen(false)}
      >
        {item.label}
      </Link>
    )
  }

  if (isLoading) {
    return (
      <div className={cls.wrapper}>
        <PageLoader />
      </div>
    )
  }

  return (
    <div className={cls.wrapper}>
      <div className={cls.burger} onClick={() => setIsMenuOpen(true)}>
        ☰
      </div>

      {isMenuOpen && <div className={cls.overlay} onClick={() => setIsMenuOpen(false)} />}

      <div className={`${cls.sidebar} ${isMenuOpen ? cls.sidebarOpen : ''}`}>
        {visibleItems.map((item) => renderLink(item, true))}
      </div>

      <nav className={cls.nav}>{visibleItems.map((item) => renderLink(item))}</nav>

      <main className={cls.content}>{children}</main>
    </div>
  )
}
