import Link from 'next/link'
import { useRouter } from 'next/router'

import cls from './AdminNav.module.css'

export const AdminNav = () => {
  const router = useRouter()

  return (
    <nav className={cls.nav}>
      <Link
        href="/admin"
        className={router.pathname === '/admin' ? cls.linkActive : cls.link}
      >
        Пользователи
      </Link>
      <Link
        href="/admin/clinics"
        className={router.pathname === '/admin/clinics' ? cls.linkActive : cls.link}
      >
        Клиники
      </Link>
    </nav>
  )
}
