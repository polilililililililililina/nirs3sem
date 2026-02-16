import React, { useState, useEffect } from 'react'

import { Button } from '@shared/ui/Button'
import { Input } from '@shared/ui/Input'
import { InputType } from '@shared/ui/Input/Input'

import cls from './Profile.module.css'

export interface UserProfileData {
  lastName: string
  firstName: string
  middleName?: string
  email: string
  organization?: string
  birthDate?: string
  position?: string
  phone?: string
}

export interface ProfileProps {
  loading?: boolean
  onSave?: (data: UserProfileData) => void
  onCancel?: () => void
  readOnly?: boolean
  title?: string
  className?: string
}

const userData = {
    lastName: 'Иванов',
    firstName: 'Иван',
    middleName: 'Иванович',
    email: 'ivanov@example.com',
    organization: 'ООО "Больница"',
    position: 'Главный врач',
    birthDate: '1990-05-15',
    phone: '+7 (999) 123-45-67'
  }

export const Profile: React.FC<ProfileProps> = ({
  loading = false,
  onSave,
  onCancel,
  readOnly = false,
  title = 'Профиль пользователя',
  className = ''
}) => {
  const [isEditing, setIsEditing] = useState(!readOnly)
  const [formData, setFormData] = useState<UserProfileData>(userData)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  // Обновляем форму при изменении userData
  useEffect(() => {
    setFormData(userData)
  }, [userData])

  // Обработчик изменения полей
  const handleChange = (field: keyof UserProfileData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))

    // Убираем ошибку при изменении поля
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }))
    }

    // Помечаем поле как touched
    setTouched(prev => ({
      ...prev,
      [field]: true
    }))
  }

  // Валидация формы
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    // Обязательные поля
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Фамилия обязательна'
    }

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'Имя обязательно'
    }

    // Email валидация
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Неверный формат email'
    }

    // Дата рождения - проверка что пользователь старше 16 лет
    if (formData.birthDate) {
      const birthDate = new Date(formData.birthDate)
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

  // Обработчик сохранения
  const handleSave = () => {
    if (validateForm()) {
      if (onSave) {
        onSave(formData)
      }
      setIsEditing(false)
    }
  }

  // Обработчик отмены
  const handleCancel = () => {
    setFormData(userData)
    setErrors({})
    setIsEditing(false)
    
    if (onCancel) {
      onCancel()
    }
  }

  // Обработчик редактирования
  const handleEdit = () => {
    setIsEditing(true)
  }

  // Форматирование даты для input type="date"
  const formatDateForInput = (dateString?: string) => {
    if (!dateString) return ''
    
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return ''
    
    return date.toISOString().split('T')[0]
  }

  // Проверка была ли форма изменена
  const isFormChanged = () => {
    return JSON.stringify(formData) !== JSON.stringify(userData)
  }

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
          disabled={!isEditing || !!(field === 'email' && userData.email)}
          readOnly={field === 'email' && !!userData.email}
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
    const formatValue = (value?: string) => value || 'Не указано'

    return (
      <div className={cls.viewMode}>
        <div className={cls.viewSection}>
          <h3 className={cls.viewTitle}>Личные данные</h3>
          <div className={cls.viewGrid}>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>ФИО:</span>
              <span className={cls.viewValue}>
                {`${formatValue(formData.lastName)} ${formatValue(formData.firstName)} ${formatValue(formData.middleName)}`}
              </span>
            </div>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>Email:</span>
              <span className={cls.viewValue}>{formatValue(formData.email)}</span>
            </div>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>Дата рождения:</span>
              <span className={cls.viewValue}>
                {formData.birthDate 
                  ? new Date(formData.birthDate).toLocaleDateString('ru-RU')
                  : 'Не указано'
                }
              </span>
            </div>
          </div>
        </div>

        <div className={cls.viewSection}>
          <h3 className={cls.viewTitle}>Работа</h3>
          <div className={cls.viewGrid}>
            <div className={cls.viewItem}>
              <span className={cls.viewLabel}>Организация:</span>
              <span className={cls.viewValue}>{formatValue(formData.organization)}</span>
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

  return (
    <div className={`${cls.profile} ${className}`}>
      <div className={cls.header}>
        <h2 className={cls.title}>{title}</h2>
        
        {!readOnly && (
          <div className={cls.actions}>
            {isEditing ? (
              <>
                <Button
                  variant="primary"
                  onClick={handleSave}
                  loading={loading}
                  disabled={loading || !isFormChanged()}
                >
                  Сохранить
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleCancel}
                  disabled={loading}
                >
                  Отмена
                </Button>
              </>
            ) : (
              <Button
                variant="primary"
                onClick={handleEdit}
                icon="✏️"
              >
                Редактировать
              </Button>
            )}
          </div>
        )}
      </div>

      {isEditing ? (
        <form className={cls.form} onSubmit={(e) => { e.preventDefault(); handleSave() }}>
          <div className={cls.section}>
            <h3 className={cls.sectionTitle}>Личные данные</h3>
            <div className={cls.fieldsGrid}>
              {renderField('Фамилия*', 'lastName', 'text', 'Иванов', true)}
              {renderField('Имя*', 'firstName', 'text', 'Иван', true)}
              {renderField('Отчество', 'middleName', 'text', 'Иванович')}
            </div>
          </div>

          <div className={cls.section}>
            <h3 className={cls.sectionTitle}>Контактная информация</h3>
            <div className={cls.fieldsGrid}>
              {renderField('Email', 'email', 'email', 'ivanov@example.com')}
              {renderField('Телефон', 'phone', 'tel', '+7 (999) 123-45-67')}
              {renderField('Дата рождения', 'birthDate', 'date')}
            </div>
          </div>

          <div className={cls.section}>
            <h3 className={cls.sectionTitle}>Работа</h3>
            <div className={cls.fieldsGrid}>
              {renderField('Организация', 'organization', 'text', 'ООО "Компания"')}
              {renderField('Должность', 'position', 'text', 'Менеджер')}
            </div>
          </div>

          <div className={cls.formActions}>
            <Button
              type="submit"
              variant="primary"
              loading={loading}
              disabled={loading || !isFormChanged()}
              fullWidth
            >
              Сохранить изменения
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleCancel}
              disabled={loading}
              fullWidth
            >
              Отменить
            </Button>
          </div>
        </form>
      ) : (
        renderViewMode()
      )}

      {isEditing && Object.keys(errors).some(key => errors[key]) && (
        <div className={cls.formErrors}>
          <h4 className={cls.errorsTitle}>Ошибки в форме:</h4>
          <ul className={cls.errorsList}>
            {Object.entries(errors)
              .filter(([_, error]) => error)
              .map(([field, error]) => (
                <li key={field} className={cls.errorItem}>
                  {error}
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  )
}