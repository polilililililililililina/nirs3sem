import { useState } from 'react'

import { useRouter } from 'next/router'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'
import { Input } from '@shared/ui/Input'

import cls from './ResetPassword.module.css'

export const ResetPasswordForm = () => {
  const router = useRouter()

  const token = router.query.token

  const [password, setPassword] = useState('')
  const [repeatPassword, setRepeatPassword] = useState('')

  const [error, setError] = useState<string | null>(null)

  const [success, setSuccess] = useState(false)

  const [isLoading, setIsLoading] = useState(false)

  const resetPassword = () => {
    setError(null)

    if (!password.trim()) {
      return setError('Введите пароль')
    }

    if (password.length < 8) {
      return setError('Пароль должен содержать минимум 8 символов')
    }

    if (password !== repeatPassword) {
      return setError('Пароли не совпадают')
    }

    if (!token || typeof token !== 'string') {
      return setError('Неверный токен')
    }

    setIsLoading(true)

    api
      .post('/auth/reset-password', {
        token,
        new_password: password,
      })
      .then(() => {
        setSuccess(true)

        setTimeout(() => {
          router.push('/')
        }, 2000)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setIsLoading(false))
  }

  return (
    <div className={cls.container}>
      <h1 className={cls.title}>Сброс пароля</h1>

      {!success && (
        <>
          <Input
            placeholder="Новый пароль"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <Input
            placeholder="Повторите пароль"
            type="password"
            value={repeatPassword}
            onChange={(e) => setRepeatPassword(e.target.value)}
          />

          <Button onClick={resetPassword}>Сменить пароль</Button>
        </>
      )}

      {success && <p className={cls.success}>Пароль успешно изменён</p>}

      {error && <p className={cls.error}>{error}</p>}

      {isLoading && <p className={cls.loading}>Загрузка...</p>}
    </div>
  )
}
