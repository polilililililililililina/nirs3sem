import { useEffect, useMemo, useState } from 'react'

import { Auth } from '@features/Auth'
import { History } from '@features/History'
import { Main } from '@features/Main'
import { Profile } from '@features/Profile'

import cls from './Home.module.css'

interface ITabs {
  id: string
  title: string
}

export const Home = () => {
  const [activeTab, setActiveTab] = useState<string>('main')
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const tabs: ITabs[] = useMemo(() => {
    const t = [{ id: 'main', title: 'Главная' }]

    if (isAuthorized) {
      t.push({ id: 'articles', title: 'База знаний' })
      t.push({ id: 'history', title: 'История' })
      t.push({ id: 'profile', title: 'Профиль' })
    }

    if (!isAuthorized) t.push({ id: 'auth', title: 'Вход' })

    return t
  }, [isAuthorized])

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsAuthorized(true)
    }
  }, [])

  return (
    <div className={cls.wrapper}>
      <div className={cls.burger} onClick={() => setIsMenuOpen(true)}>
        ☰
      </div>

      {isMenuOpen && <div className={cls.overlay} onClick={() => setIsMenuOpen(false)} />}

      <div className={`${cls.sidebar} ${isMenuOpen ? cls.open : ''}`}>
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className={activeTab === tab.id ? cls.activeTab : cls.tab}
            onClick={() => {
              setActiveTab(tab.id)
              setIsMenuOpen(false)
            }}
          >
            <p className={cls.tabName}>{tab.title}</p>
          </div>
        ))}
      </div>

      <div className={cls.content}>
        {activeTab === 'main' && <Main />}
        {/* {activeTab === 'articles' && <Articles />} */}
        {activeTab === 'history' && isAuthorized && <History setActiveTab={setActiveTab} />}
        {activeTab === 'profile' && isAuthorized && (
          <Profile setIsAuthorized={setIsAuthorized} setActiveTab={setActiveTab} />
        )}
        {activeTab === 'auth' && !isAuthorized && (
          <Auth setIsAuthorized={setIsAuthorized} setActiveTab={setActiveTab} />
        )}
      </div>
    </div>
  )
}
