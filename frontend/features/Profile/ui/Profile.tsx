import React, { useState, useEffect, useMemo } from 'react'

import { ClinicItem } from '@features/History/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { useAuth } from '@shared/lib/hooks/useAuth'
import { Button } from '@shared/ui/Button'
import { FileUploader } from '@shared/ui/FileUploader'
import { Input } from '@shared/ui/Input'
import { InputType } from '@shared/ui/Input/Input'
import { PageLoader } from '@shared/ui/Loader'

import cls from './Profile.module.css'

export interface UserProfileData {
  name: string
  surname: string
  middlename?: string
  email: string
  birthday?: string
  position?: string
  phone?: string
  avatar_url?: string
  clinic_id?: string
  clinic_name?: string
}

export interface ProfileProps {
  loading?: boolean
  onCancel?: () => void
  readOnly?: boolean
  title?: string
  className?: string
}

const initData = {
  name: '',
  surname: '',
  middlename: '',
  email: '',
  birthday: '',
  position: '',
  phone: '',
  avatar_url: '',
  clinic_id: '',
  clinic_name: '',
}

export const Profile: React.FC<ProfileProps> = ({ title = 'Профиль пользователя' }) => {
  const { logout } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState<UserProfileData>(initData)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [initialData, setInitialData] = useState<UserProfileData>(initData)
  const [avatarImageUrl, setAvatarImageUrl] = useState<string | null>(null)
  const [clinics, setClinics] = useState<ClinicItem[]>([])

  const uploadAvatar = (file: File | null) => {
    if (!file) return

    const formDataData = new FormData()
    formDataData.append('file', file)

    api
      .post('/users/avatar', formDataData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      .then(({ data }) =>
        setFormData((prev) => ({
          ...prev,
          avatar_url: data.avatar_url,
        }))
      )
      .catch((e) => setError(getErrorMessage(e)))
  }

  const handleSave = () => {
    if (!validateForm()) return

    setError(null)
    setIsLoading(true)

    api
      .put('/users/me', {
        name: formData.name,
        surname: formData.surname,
        middlename: formData.middlename,
        birthday: formData.birthday,
        position: formData.position,
        phone: formData.phone,
        clinic_id: formData.clinic_id || null,
      })
      .then(({ data }) => {
        setFormData(data)
        setIsEditing(false)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setIsLoading(false))
  }

  // Обработчик изменения полей
  const handleChange = (field: keyof UserProfileData, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))

    // Убираем ошибку при изменении поля
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: '',
      }))
    }

    // Помечаем поле как touched
    setTouched((prev) => ({
      ...prev,
      [field]: true,
    }))
  }

  // Валидация формы
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    // Обязательные поля
    if (!formData.surname.trim()) {
      newErrors.lastName = 'Фамилия обязательна'
    }

    if (!formData.name.trim()) {
      newErrors.firstName = 'Имя обязательно'
    }

    // Email валидация
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Неверный формат email'
    }

    // Дата рождения - проверка что пользователь старше 16 лет
    if (formData.birthday) {
      const birthDate = new Date(formData.birthday)
      const today = new Date()
      const minDate = new Date()
      minDate.setFullYear(today.getFullYear() - 16)

      if (birthDate > minDate) {
        newErrors.birthDate = 'Возраст должен быть не менее 16 лет'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const exitFrom = () => {
    logout()
  }

  // Обработчик отмены
  const handleCancel = () => {
    setFormData(initialData)
    setErrors({})
    setIsEditing(false)
  }

  // Обработчик редактирования
  const handleEdit = () => {
    setIsEditing(true)
  }

  // Проверка была ли форма изменена
  const isFormChanged = useMemo(() => {
    return JSON.stringify(formData) !== JSON.stringify(initialData)
  }, [formData, initialData])

  useEffect(() => {
    if (!formData.avatar_url) {
      setAvatarImageUrl(null)
      return
    }

    let objectUrl: string | null = null
    let cancelled = false

    api
      .get(`/users/avatar/${formData.avatar_url}`, { responseType: 'blob' })
      .then(({ data }) => {
        if (!cancelled) {
          objectUrl = URL.createObjectURL(data)
          setAvatarImageUrl(objectUrl)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAvatarImageUrl(null)
        }
      })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [formData.avatar_url])

  useEffect(() => {
    api
      .get<{ items: ClinicItem[] }>('/clinics/')
      .then(({ data }) => setClinics(data.items))
      .catch(() => setClinics([]))
  }, [])

  useEffect(() => {
    setIsLoading(true)

    api
      .get('/users/me')
      .then(({ data }) => {
        setFormData(data)
        setInitialData(data)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setIsLoading(false))
  }, [])

  // Рендер поля
  const renderField = (
    label: string,
    field: keyof UserProfileData,
    type: InputType = 'text',
    placeholder = '',
    required = false
  ) => {
    return (
      <div className={cls.field}>
        <Input
          label={label}
          type={type}
          value={formData[field] || ''}
          onChange={(e) => handleChange(field, e.target.value)}
          placeholder={placeholder}
          error={errors[field]}
          disabled={!isEditing || !!(field === 'email' && formData.email)}
          readOnly={field === 'email' && !!formData.email}
          variant={isEditing ? 'primary' : 'secondary'}
          fullWidth
          required={required}
          helperText={touched[field] && !errors[field] ? '' : undefined}
        />
      </div>
    )
  }

  // Рендер информации только для просмотра
  const renderViewMode = () => {
    const formatValue = (value?: string) => value || ''

    return (
      <div className={cls.viewMode}>
        <div className={cls.viewSection}>
          <h3 className={cls.viewTitle}>Личные данные</h3>
          <div className={cls.viewGrid}>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>ФИО:</span>
              <span className={cls.viewValue}>
                {`${formatValue(formData.surname)} ${formatValue(formData.name)} ${formatValue(formData.middlename)}`}
              </span>
            </div>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>Email:</span>
              <span className={cls.viewValue}>{formatValue(formData.email)}</span>
            </div>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>Дата рождения:</span>
              <span className={cls.viewValue}>
                {formData.birthday
                  ? new Date(formData.birthday).toLocaleDateString('ru-RU')
                  : 'Не указано'}
              </span>
            </div>
          </div>
        </div>

        <div className={cls.viewSection}>
          <h3 className={cls.viewTitle}>Работа</h3>
          <div className={cls.viewGrid}>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>Клиника:</span>
              <span className={cls.viewValue}>
                {formatValue(formData.clinic_name) || 'Не указана'}
              </span>
            </div>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>Должность:</span>
              <span className={cls.viewValue}>{formatValue(formData.position)}</span>
            </div>
          </div>
        </div>

        {formData.phone && (
          <div className={cls.viewSection}>
            <h3 className={cls.viewTitle}>Контакты</h3>
            <div className={cls.viewGrid}>
              <div className={cls.viewItem}>
                <span className={cls.viewLabel}>Телефон:</span>
                <span className={cls.viewValue}>{formData.phone}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (isLoading && !formData.email) {
    return <PageLoader label="Загрузка профиля..." />
  }

  return (
    <div className={cls.profile}>
      <div className={cls.header}>
        <h2 className={cls.title}>{title}</h2>

        <div className={cls.actions}>
          {isEditing ? (
            <>
              <Button variant="primary" onClick={handleSave} disabled={!isFormChanged}>
                Сохранить
              </Button>
              <Button variant="secondary" onClick={handleCancel}>
                Отмена
              </Button>
            </>
          ) : (
            <Button variant="primary" onClick={handleEdit} icon="✏️">
              Редактировать
            </Button>
          )}
        </div>
      </div>

      <div className={cls.avatarBlock}>
        {avatarImageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatarImageUrl} alt="avatar" className={cls.avatar} />
        ) : (
          <div className={cls.emptyAvatar}>👤</div>
        )}

        {isEditing && (
          <FileUploader
            acceptType="image"
            allowedExtensions={['.jpg', '.jpeg', '.png', '.webp']}
            maxSizeMB={5}
            buttonText="Загрузить фото"
            onFileSelect={uploadAvatar}
            placeholder="Фото профиля"
          />
        )}
      </div>

      {isEditing ? (
        <form
          className={cls.form}
          onSubmit={(e) => {
            e.preventDefault()
            handleSave()
          }}
        >
          <div className={cls.section}>
            <h3 className={cls.sectionTitle}>Личные данные</h3>
            <div className={cls.fieldsGrid}>
              {renderField('Фамилия*', 'surname', 'text', 'Иванов', true)}
              {renderField('Имя*', 'name', 'text', 'Иван', true)}
              {renderField('Отчество', 'middlename', 'text', 'Иванович')}
            </div>
          </div>

          <div className={cls.section}>
            <h3 className={cls.sectionTitle}>Контактная информация</h3>
            <div className={cls.fieldsGrid}>
              {renderField('Email', 'email', 'email', 'ivanov@example.com')}
              {renderField('Телефон', 'phone', 'tel', '+7 (999) 123-45-67')}
              {renderField('Дата рождения', 'birthday', 'date')}
            </div>
          </div>

          <div className={cls.section}>
            <h3 className={cls.sectionTitle}>Работа</h3>
            <div className={cls.fieldsGrid}>
              {renderField('Должность', 'position', 'text', 'Менеджер')}
              <div className={cls.field}>
                <label className={cls.selectLabel}>Клиника</label>
                <select
                  className={cls.select}
                  value={formData.clinic_id || ''}
                  onChange={(e) => handleChange('clinic_id', e.target.value)}
                  disabled={!isEditing}
                >
                  <option value="">Не выбрана</option>
                  {clinics.map((clinic) => (
                    <option key={clinic._id} value={clinic._id}>
                      {clinic.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className={cls.formActions}>
            <Button type="submit" variant="primary" fullWidth disabled={!isFormChanged}>
              Сохранить изменения
            </Button>
            <Button type="button" variant="secondary" onClick={handleCancel} fullWidth>
              Отменить
            </Button>
          </div>
        </form>
      ) : (
        renderViewMode()
      )}

      <Button className={cls.exit} onClick={exitFrom}>
        Выйти
      </Button>

      {((isEditing && Object.keys(errors).some((key) => errors[key])) || error) && (
        <div className={cls.formErrors}>
          <h4 className={cls.errorsTitle}>Ошибки в форме:</h4>
          <ul className={cls.errorsList}>
            {error ? (
              <li className={cls.errorItem}>{error}</li>
            ) : (
              Object.entries(errors)
                .filter(([_, error]) => error)
                .map(([field, error]) => (
                  <li key={field} className={cls.errorItem}>
                    {error}
                  </li>
                ))
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
