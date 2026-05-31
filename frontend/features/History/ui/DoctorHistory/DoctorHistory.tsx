import { useEffect, useState } from 'react'

import Link from 'next/link'
import { useRouter } from 'next/router'

import { PatientItem, PatientListResponse } from '@features/History/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { useAuth } from '@shared/lib/hooks/useAuth'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'
import { Pagination } from '@shared/ui/Pagination'

import cls from './DoctorHistory.module.css'

export const DoctorHistory = () => {
  const router = useRouter()
  const { user } = useAuth()

  const [patients, setPatients] = useState<PatientItem[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [total, setTotal] = useState(0)
  const limit = 12

  useEffect(() => {
    setError(null)
    setLoading(true)

    api
      .get<PatientListResponse>('/scans/patients', {
        params: {
          page: currentPage,
          limit,
          search: search || undefined,
        },
      })
      .then(({ data }) => {
        setPatients(data.items)
        setTotal(data.pagination.total)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [currentPage, search])

  const totalPages = Math.ceil(total / limit) || 1

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(new Date(dateString))
  }

  return (
    <div className={cls.page}>
      <header className={cls.header}>
        <div>
          <h1 className={cls.title}>Каталог пациентов</h1>
          {user?.clinic_name && <p className={cls.subtitle}>Клиника: {user.clinic_name}</p>}
        </div>
        <Button variant="primary" onClick={() => router.push('/')}>
          Новый анализ
        </Button>
      </header>

      {user?.role === 'doctor' && !user.clinic_id && (
        <div className={cls.warning}>
          Укажите клинику в профиле, чтобы видеть пациентов своей клиники.
        </div>
      )}

      {error && <p className={cls.error}>{error}</p>}

      <div className={cls.toolbar}>
        <input
          type="text"
          placeholder="Поиск по ФИО или email..."
          className={cls.searchInput}
          value={search}
          onChange={(e) => {
            setCurrentPage(1)
            setSearch(e.target.value)
          }}
        />
      </div>

      {loading && <PageLoader />}

      {!loading && patients.length === 0 ? (
        <div className={cls.empty}>
          <p>Пациенты с анализами не найдены</p>
        </div>
      ) : (
        <div className={cls.grid}>
          {patients.map((patient) => (
            <Link key={patient._id} href={`/history/${patient._id}`} className={cls.card}>
              <div className={cls.cardIcon}>📁</div>
              <h3 className={cls.cardTitle}>{patient.full_name}</h3>
              <p className={cls.cardEmail}>{patient.email}</p>
              <div className={cls.cardMeta}>
                <span>Анализов: {patient.scan_count}</span>
                <span>Последний: {formatDate(patient.last_scan_at)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  )
}
