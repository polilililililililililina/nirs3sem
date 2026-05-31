import { useState } from 'react'

import { useRouter } from 'next/router'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'
import { Input } from '@shared/ui/Input'

import cls from './AuthForm.module.css'

interface IResponse {
  access_token: string
  refresh_token: string
}

export const AuthForm = () => {
  const router = useRouter()

  const [type, setType] = useState<'login' | 'register' | 'forgot'>('login')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const login = () => {
    setError(null)

    if (!email.trim()) return setError('Введите email!')
    if (!password.trim()) return setError('Введите пароль!')

    setIsLoading(true)

    api
      .post('/auth/login', { email: email.trim(), password: password.trim() })
      .then(({ data }: { data: IResponse }) => {
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)

        setEmail('')
        setName('')
        setPassword('')

        router.reload()
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setIsLoading(false))
  }

  const register = () => {
    setError(null)

    if (!email.trim()) return setError('Введите email!')
    if (!password.trim()) return setError('Введите пароль!')
    if (!name.trim()) return setError('Введите имя!')

    setIsLoading(true)

    api
      .post('/auth/register', { email: email.trim(), password: password.trim(), name: name.trim() })
      .then(() => {
        setType('login')
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setIsLoading(false))
  }

  const forgotPassword = () => {
    setError(null)

    if (!email.trim()) return setError('Введите email!')

    setIsLoading(true)

    api
      .post('/auth/forgot-password', {
        email: email.trim(),
      })
      .then(() => {
        alert('Если аккаунт существует, письмо отправлено на почту')
        setType('login')
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setIsLoading(false))
  }

  return (
    <div className={cls.container}>
      <h2 className={cls.title}>
        {type === 'login' ? 'Вход' : type === 'register' ? 'Регистрация' : 'Восстановление пароля'}
      </h2>

      {type === 'register' && (
        <Input placeholder="Имя" value={name} onChange={(v) => setName(v.target.value)} />
      )}

      <Input placeholder="Email" value={email} onChange={(v) => setEmail(v.target.value)} />

      {type !== 'forgot' && (
        <Input
          placeholder="Пароль"
          type="password"
          value={password}
          onChange={(v) => setPassword(v.target.value)}
        />
      )}

      <Button
        onClick={() => {
          if (type === 'login') return login()
          if (type === 'register') return register()
          return forgotPassword()
        }}
      >
        {type === 'login' ? 'Войти' : type === 'register' ? 'Создать аккаунт' : 'Отправить ссылку'}
      </Button>

      {type === 'login' && (
        <>
          <p className={cls.link}>
            Нет аккаунта? <span onClick={() => setType('register')}>Зарегистрироваться</span>
          </p>
          <p className={cls.link} onClick={() => setType('forgot')}>
            <span>Забыли пароль?</span>
          </p>
        </>
      )}

      {type === 'register' && (
        <p className={cls.link}>
          Уже зарегистрированы? <span onClick={() => setType('login')}>Войти</span>
        </p>
      )}

      {type === 'forgot' && (
        <p className={cls.link}>
          Вспомнили пароль? <span onClick={() => setType('login')}>Войти</span>
        </p>
      )}

      {error && <p className={cls.error}>{error}</p>}
      {isLoading && <p className={cls.link}>Загрузка...</p>}
    </div>
  )
}
