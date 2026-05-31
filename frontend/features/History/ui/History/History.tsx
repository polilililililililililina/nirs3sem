import React, { useEffect, useState } from 'react'

import { useRouter } from 'next/router'

import { Pagination, ScanItem } from '@features/History/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'

import { HistoryList } from '../HistoryList/HistoryList'
import { RequestDetail } from '../RequestDetail/RequestDetail'

import cls from './History.module.css'

export const History: React.FC = () => {
  const router = useRouter()

  const [requests, setRequests] = useState<ScanItem[]>([])
  const [selectedRequest, setSelectedRequest] = useState<ScanItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState<'all' | 'queued' | 'processing' | 'done' | 'error'>('all')
  const [search, setSearch] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState<Pagination>()
  const [currentPage, setCurrentPage] = useState(1)

  const handleSelectRequest = (request: ScanItem) => {
    setSelectedRequest(request)
  }

  const handleDeleteRequest = async (requestId: string) => {
    if (!window.confirm('Удалить анализ?')) {
      return
    }

    api
      .delete(`/scans/${requestId}`)
      .then(() => {
        setRequests((prev) => prev.filter((req) => req._id !== requestId))

        if (selectedRequest?._id === requestId) {
          setSelectedRequest(null)
        }
      })
      .catch((e) => setError(getErrorMessage(e)))
  }

  useEffect(() => {
    setError(null)
    setLoading(true)

    api
      .get('/scans', {
        params: {
          page: currentPage,
          limit: 10,
          status: filter === 'all' ? undefined : filter,
          search: search || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
        },
      })
      .then(({ data }) => {
        setRequests(data.items)
        setPagination(data.pagination)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [currentPage, filter, search, dateFrom, dateTo])

  return (
    <>
      <header className={cls.pageHeader}>
        <h1 className={cls.pageTitle}>История анализов МРТ</h1>

        <Button variant="primary" onClick={() => router.push('/')} className={cls.btn}>
          Новый анализ
        </Button>
      </header>

      {error && <p className={cls.error}>{error}</p>}

      <div className={cls.filters}>
        <div className={cls.filterButtons}>
          <button
            className={`${cls.filterButton} ${filter === 'all' ? cls.active : ''}`}
            onClick={() => setFilter('all')}
          >
            Все
          </button>

          <button
            className={`${cls.filterButton} ${filter === 'done' ? cls.active : ''}`}
            onClick={() => setFilter('done')}
          >
            Завершённые
          </button>

          <button
            className={`${cls.filterButton} ${filter === 'processing' ? cls.active : ''}`}
            onClick={() => setFilter('processing')}
          >
            В обработке
          </button>

          <button
            className={`${cls.filterButton} ${filter === 'queued' ? cls.active : ''}`}
            onClick={() => setFilter('queued')}
          >
            В очереди
          </button>

          <button
            className={`${cls.filterButton} ${filter === 'error' ? cls.active : ''}`}
            onClick={() => setFilter('error')}
          >
            Ошибки
          </button>
        </div>

        <div className={cls.searchBox}>
          <input
            type="text"
            placeholder="Поиск..."
            className={cls.searchInput}
            value={search}
            onChange={(e) => {
              setCurrentPage(1)
              setSearch(e.target.value)
            }}
          />
        </div>

        <div className={cls.dateFilters}>
          <label className={cls.dateLabel}>
            С
            <input
              type="date"
              className={cls.dateInput}
              value={dateFrom}
              onChange={(e) => {
                setCurrentPage(1)
                setDateFrom(e.target.value)
              }}
            />
          </label>
          <label className={cls.dateLabel}>
            По
            <input
              type="date"
              className={cls.dateInput}
              value={dateTo}
              onChange={(e) => {
                setCurrentPage(1)
                setDateTo(e.target.value)
              }}
            />
          </label>
        </div>
      </div>

      {loading && requests.length === 0 && <PageLoader />}

      <div className={cls.contentLayout}>
        <div className={cls.listColumn}>
          <HistoryList
            requests={requests}
            onSelectRequest={handleSelectRequest}
            selectedRequestId={selectedRequest?._id}
            itemsPerPage={pagination?.limit}
            totalItems={pagination?.total}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
        </div>

        <div className={cls.detailColumn}>
          <RequestDetail request={selectedRequest} onNewAnalysis={() => router.push('/')} />

          {selectedRequest && (
            <div className={cls.detailActions}>
              <Button variant="secondary" onClick={() => handleDeleteRequest(selectedRequest._id)}>
                Удалить
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
