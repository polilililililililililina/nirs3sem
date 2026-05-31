import { FormEvent, useEffect, useState } from 'react'

import { Clinic, ClinicListResponse } from '@features/Admin/types'
import { AdminNav } from '@features/Admin/ui/AdminNav/AdminNav'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'

import cls from './AdminClinics.module.css'

interface ClinicForm {
  name: string
  address: string
  description: string
}

const emptyForm: ClinicForm = {
  name: '',
  address: '',
  description: '',
}

export const AdminClinics = () => {
  const [clinics, setClinics] = useState<Clinic[]>([])
  const [form, setForm] = useState<ClinicForm>(emptyForm)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadClinics = () => {
    setLoading(true)
    setError(null)

    api
      .get<ClinicListResponse>('/admin/clinics')
      .then(({ data }) => setClinics(data.items))
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadClinics()
  }, [])

  const resetForm = () => {
    setForm(emptyForm)
    setEditingId(null)
  }

  const startEdit = (clinic: Clinic) => {
    setEditingId(clinic._id)
    setForm({
      name: clinic.name,
      address: clinic.address || '',
      description: clinic.description || '',
    })
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()

    const name = form.name.trim()
    if (!name) {
      setError('Название клиники обязательно')
      return
    }

    setSaving(true)
    setError(null)

    const payload = {
      name,
      address: form.address.trim() || undefined,
      description: form.description.trim() || undefined,
    }

    try {
      if (editingId) {
        const { data } = await api.put<Clinic>(`/admin/clinics/${editingId}`, payload)
        setClinics((prev) => prev.map((clinic) => (clinic._id === editingId ? data : clinic)))
      } else {
        const { data } = await api.post<Clinic>('/admin/clinics', payload)
        setClinics((prev) => [...prev, data].sort((a, b) => a.name.localeCompare(b.name)))
      }
      resetForm()
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (clinicId: string) => {
    if (!window.confirm('Удалить клинику?')) return

    setError(null)

    try {
      await api.delete(`/admin/clinics/${clinicId}`)
      setClinics((prev) => prev.filter((clinic) => clinic._id !== clinicId))
      if (editingId === clinicId) {
        resetForm()
      }
    } catch (e) {
      setError(getErrorMessage(e))
    }
  }

  return (
    <div className={cls.page}>
      <AdminNav />

      <header className={cls.header}>
        <h1 className={cls.title}>Управление клиниками</h1>
      </header>

      {error && <p className={cls.error}>{error}</p>}

      <form className={cls.form} onSubmit={handleSubmit}>
        <h2 className={cls.formTitle}>{editingId ? 'Редактирование' : 'Новая клиника'}</h2>

        <div className={cls.fields}>
          <label className={cls.label}>
            Название *
            <input
              className={cls.input}
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Городская клиника №1"
              required
            />
          </label>

          <label className={cls.label}>
            Адрес
            <input
              className={cls.input}
              value={form.address}
              onChange={(e) => setForm((prev) => ({ ...prev, address: e.target.value }))}
              placeholder="г. Москва, ул. Примерная, 1"
            />
          </label>

          <label className={cls.label}>
            Описание
            <textarea
              className={cls.textarea}
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Краткое описание"
              rows={3}
            />
          </label>
        </div>

        <div className={cls.formActions}>
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? 'Сохранение...' : editingId ? 'Сохранить' : 'Создать'}
          </Button>
          {editingId && (
            <Button type="button" variant="secondary" onClick={resetForm}>
              Отмена
            </Button>
          )}
        </div>
      </form>

      {loading && <PageLoader />}

      {!loading && (
        <div className={cls.list}>
          {clinics.length === 0 ? (
            <p className={cls.empty}>Клиники пока не добавлены</p>
          ) : (
            clinics.map((clinic) => (
              <div key={clinic._id} className={cls.card}>
                <div>
                  <h3 className={cls.cardTitle}>{clinic.name}</h3>
                  {clinic.address && <p className={cls.cardMeta}>{clinic.address}</p>}
                  {clinic.description && <p className={cls.cardDesc}>{clinic.description}</p>}
                </div>
                <div className={cls.cardActions}>
                  <Button variant="secondary" size="small" onClick={() => startEdit(clinic)}>
                    Редактировать
                  </Button>
                  <Button variant="secondary" size="small" onClick={() => handleDelete(clinic._id)}>
                    Удалить
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
