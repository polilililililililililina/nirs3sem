import React, { Dispatch, SetStateAction } from 'react'

import { ScanItem } from '@features/History/types'

import { Pagination } from '@shared/ui/Pagination'

import cls from './HistoryList.module.css'

interface HistoryListProps {
  requests: ScanItem[]
  onSelectRequest: (request: ScanItem) => void
  selectedRequestId?: string
  itemsPerPage?: number
  totalItems?: number
  currentPage?: number
  onPageChange: Dispatch<SetStateAction<number>>
}

export const HistoryList: React.FC<HistoryListProps> = ({
  requests,
  onSelectRequest,
  selectedRequestId,
  itemsPerPage = 10,
  totalItems,
  currentPage,
  onPageChange,
}) => {
  // Вычисляем пагинацию
  const totalPages = Math.ceil((totalItems || 0) / itemsPerPage)

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done':
        return cls.statusCompleted
      case 'processing':
        return cls.statusProcessing
      case 'queued':
        return cls.statusPending
      case 'error':
        return cls.statusFailed
      default:
        return ''
    }
  }

  const getStatusText = (status: string) => {
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

  return (
    <div className={cls.historyList}>
      <div className={cls.listHeader}>
        <h3 className={cls.title}>История запросов</h3>
        <div className={cls.stats}>
          <span className={cls.totalCount}>Всего: {totalItems}</span>
          <span className={cls.pageInfo}>
            Страница {currentPage} из {totalPages}
          </span>
        </div>
      </div>

      <div className={cls.listContainer}>
        {requests.length === 0 ? (
          <div className={cls.emptyState}>
            <div className={cls.emptyIcon}>📋</div>
            <p className={cls.emptyText}>Запросы не найдены</p>
            <p className={cls.emptySubtext}>Начните анализ МРТ изображений</p>
          </div>
        ) : (
          <>
            <div className={cls.requestsGrid}>
              {requests.map((request) => (
                <div
                  key={request._id}
                  className={`${cls.listItem} ${
                    selectedRequestId === request._id ? cls.selected : ''
                  }`}
                  onClick={() => onSelectRequest(request)}
                >
                  <div className={cls.itemHeader}>
                    <span className={cls.requestDate}>{formatDate(request.created_at)}</span>
                    <span className={`${cls.requestStatus} ${getStatusColor(request.status)}`}>
                      {getStatusText(request.status)}
                    </span>
                  </div>

                  <div className={cls.itemContent}>
                    <div className={cls.descriptionPreview}>
                      {request.result_desc ? (
                        <>
                          <p className={cls.descriptionText}>
                            {request.result_desc.length > 100
                              ? `${request.result_desc.substring(0, 100)}...`
                              : request.result_desc}
                          </p>
                        </>
                      ) : (
                        <p className={cls.noDescription}>Описание отсутствует</p>
                      )}
                    </div>
                  </div>

                  <div className={cls.itemFooter}>
                    <span className={cls.viewDetails}>Подробнее</span>
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <Pagination
                currentPage={currentPage || 1}
                totalPages={totalPages}
                onPageChange={onPageChange}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}
