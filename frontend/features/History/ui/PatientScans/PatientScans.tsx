import { useEffect, useState } from 'react'

import Link from 'next/link'
import { useRouter } from 'next/router'

import { PatientScansResponse, ScanItem } from '@features/History/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'
import { Pagination } from '@shared/ui/Pagination'

import cls from './PatientScans.module.css'

interface PatientScansProps {
  userId: string
}

export const PatientScans = ({ userId }: PatientScansProps) => {
  const router = useRouter()
  const [data, setData] = useState<PatientScansResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const limit = 10

  useEffect(() => {
    setError(null)
    setLoading(true)

    api
      .get<PatientScansResponse>(`/scans/patients/${userId}`, {
        params: { page: currentPage, limit },
      })
      .then(({ data: response }) => setData(response))
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [userId, currentPage])

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(dateString))
  }

  const getStatusText = (status: ScanItem['status']) => {
    switch (status) {
      case 'done':
        return 'Завершено'
      case 'processing':
        return 'В обработке'
      case 'queued':
        return 'Ожидание'
      case 'error':
        return 'Ошибка'
      default:
        return status
    }
  }

  const totalPages = data ? Math.ceil(data.pagination.total / limit) || 1 : 1

  return (
    <div className={cls.page}>
      <header className={cls.header}>
        <div>
          <Button onClick={() => router.push('/history')}>К каталогу</Button>
          <h1 className={cls.title}>{data?.patient.full_name || 'Пациент'}</h1>
        </div>
      </header>

      {error && <p className={cls.error}>{error}</p>}
      {loading && <PageLoader />}

      {data && (
        <>
          <section className={cls.profile}>
            <h2 className={cls.sectionTitle}>Профиль пациента</h2>
            <div className={cls.profileGrid}>
              <div>
                <span className={cls.label}>Email</span>
                <span>{data.patient.email}</span>
              </div>
              {data.patient.birthday && (
                <div>
                  <span className={cls.label}>Дата рождения</span>
                  <span>{new Date(data.patient.birthday).toLocaleDateString('ru-RU')}</span>
                </div>
              )}
              {data.patient.phone && (
                <div>
                  <span className={cls.label}>Телефон</span>
                  <span>{data.patient.phone}</span>
                </div>
              )}
            </div>
          </section>

          <section className={cls.scans}>
            <h2 className={cls.sectionTitle}>Анализы ({data.pagination.total})</h2>

            {data.items.length === 0 ? (
              <p>У пациента пока нет анализов</p>
            ) : (
              <div className={cls.scanList}>
                {data.items.map((scan) => (
                  <Link
                    key={scan._id}
                    href={`/history/${userId}/${scan._id}`}
                    className={cls.scanCard}
                  >
                    <div className={cls.scanHeader}>
                      <span>{formatDate(scan.created_at)}</span>
                      <span className={cls.status}>{getStatusText(scan.status)}</span>
                    </div>
                    <p className={cls.scanDesc}>
                      {scan.result_desc || scan.filename || 'Без описания'}
                    </p>
                    {scan.status === 'done' && (
                      <p className={cls.scanMeta}>
                        {scan.tumor_detected ? '⚠️ Аномалия' : '✅ Без аномалий'}
                        {scan.confidence != null && ` · ${Math.round(scan.confidence * 100)}%`}
                      </p>
                    )}
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
          </section>
        </>
      )}
    </div>
  )
}
