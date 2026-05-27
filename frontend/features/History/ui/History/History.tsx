import React, { Dispatch, SetStateAction, useEffect, useState } from 'react'

import { Pagination, ScanItem } from '@features/History/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'

import { HistoryList } from '../HistoryList/HistoryList'
import { RequestDetail } from '../RequestDetail/RequestDetail'

import cls from './History.module.css'

interface IProps {
  setActiveTab: Dispatch<SetStateAction<string>>
}

export const History: React.FC<IProps> = (props) => {
  const { setActiveTab } = props

  const [requests, setRequests] = useState<ScanItem[]>([])
  const [selectedRequest, setSelectedRequest] = useState<ScanItem | null>(null)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState<'all' | 'queued' | 'processing' | 'done' | 'error'>('all')
  const [search, setSearch] = useState('')
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
        },
      })
      .then(({ data }) => {
        setRequests(data.items)
        setPagination(data.pagination)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [currentPage, filter, search])

  return (
    <>
      <header className={cls.pageHeader}>
        <h1 className={cls.pageTitle}>История анализов МРТ</h1>

        <Button variant="primary" onClick={() => setActiveTab('main')} className={cls.btn}>
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
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

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
          <RequestDetail request={selectedRequest} />

          {selectedRequest && (
            <div className={cls.detailActions}>
              <Button variant="secondary" onClick={() => handleDeleteRequest(selectedRequest._id)}>
                Удалить
              </Button>
            </div>
          )}
        </div>
      </div>

      {loading && <p>Загрузка...</p>}
    </>
  )
}
