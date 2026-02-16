import { useState } from 'react'

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

    const tabs: ITabs[] = [
        { id: 'main', title: 'Главная' },
        { id: 'articles', title: 'База знаний' },
        { id: 'history', title: 'История' },
        { id: 'profile', title: 'Профиль' },
        // { id: 'auth', title: 'Вход' },
    ]

    return (
        <div className={cls.wrapper}>
            <div className={cls.tabs}>
                {tabs.map((tab) =>
                    (<div 
                        key={tab.id} 
                        className={activeTab === tab.id ? cls.activeTab : cls.tab} 
                        onClick={() => setActiveTab(tab.id)}>
                            <p className={cls.tabName}>{tab.title}</p>
                    </div>)
                )}
            </div>

            <div className={cls.content}>
                {activeTab === 'main' && <Main />}
                {/* {activeTab === 'articles' && <Articles />} */}
                {activeTab === 'history' && <History />}
                {activeTab === 'profile' && <Profile />}
                {/* {activeTab === 'auth' && <Auth />} */}
            </div>
        </div>
    )
} 