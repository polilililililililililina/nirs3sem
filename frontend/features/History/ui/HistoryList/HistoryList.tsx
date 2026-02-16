import React, { useState } from 'react'

import { MriAnalysisRequest } from '@features/History/types'

import { Pagination } from '@shared/ui/Pagination'

import cls from './HistoryList.module.css'


interface HistoryListProps {
  requests: MriAnalysisRequest[]
  onSelectRequest: (request: MriAnalysisRequest) => void
  selectedRequestId?: string
  itemsPerPage?: number
}

export const HistoryList: React.FC<HistoryListProps> = ({
  requests,
  onSelectRequest,
  selectedRequestId,
  itemsPerPage = 10
}) => {
  const [currentPage, setCurrentPage] = useState(1)

  // Сортируем по дате (новые первые)
  const sortedRequests = [...requests].sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )

  // Вычисляем пагинацию
  const totalItems = sortedRequests.length
  const totalPages = Math.ceil(totalItems / itemsPerPage)
  
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentRequests = sortedRequests.slice(startIndex, endIndex)

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return cls.statusCompleted
      case 'processing': return cls.statusProcessing
      case 'pending': return cls.statusPending
      case 'failed': return cls.statusFailed
      default: return ''
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Завершено'
      case 'processing': return 'В обработке'
      case 'pending': return 'Ожидание'
      case 'failed': return 'Ошибка'
      default: return status
    }
  }

  const getAnomaliesSummary = (anomalies: string[]) => {
    if (anomalies.length === 0) return 'Аномалий не обнаружено'
    if (anomalies.length === 1) return anomalies[0]
    return `${anomalies[0]} +${anomalies.length - 1}`
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
        {currentRequests.length === 0 ? (
          <div className={cls.emptyState}>
            <div className={cls.emptyIcon}>📋</div>
            <p className={cls.emptyText}>Запросы не найдены</p>
            <p className={cls.emptySubtext}>Начните анализ МРТ изображений</p>
          </div>
        ) : (
          <>
            <div className={cls.requestsGrid}>
              {currentRequests.map((request) => (
                <div
                  key={request.id}
                  className={`${cls.listItem} ${
                    selectedRequestId === request.id ? cls.selected : ''
                  }`}
                  onClick={() => onSelectRequest(request)}
                >
                  <div className={cls.itemHeader}>
                    <span className={cls.requestDate}>
                      {formatDate(request.createdAt)}
                    </span>
                    <span className={`${cls.requestStatus} ${getStatusColor(request.status)}`}>
                      {getStatusText(request.status)}
                    </span>
                  </div>
                  
                  <div className={cls.itemContent}>
                    <div className={cls.descriptionPreview}>
                      {request.description ? (
                        <>
                          <p className={cls.descriptionText}>
                            {request.description.length > 100
                              ? `${request.description.substring(0, 100)}...`
                              : request.description}
                          </p>
                          {request.anomalies && request.anomalies.length > 0 && (
                            <div className={cls.anomaliesPreview}>
                              <span className={cls.anomaliesLabel}>Обнаружено:</span>
                              <span className={cls.anomaliesValue}>
                                {getAnomaliesSummary(request.anomalies)}
                              </span>
                            </div>
                          )}
                        </>
                      ) : (
                        <p className={cls.noDescription}>Описание отсутствует</p>
                      )}
                    </div>
                    
                    {request.confidence && (
                      <div className={cls.confidenceIndicator}>
                        <div className={cls.confidenceLabel}>Уверенность:</div>
                        <div className={cls.confidenceBar}>
                          <div 
                            className={cls.confidenceFill}
                            style={{ width: `${request.confidence}%` }}
                          />
                        </div>
                        <div className={cls.confidenceValue}>{request.confidence}%</div>
                      </div>
                    )}
                  </div>
                  
                  <div className={cls.itemFooter}>
                    <span className={cls.viewDetails}>Подробнее →</span>
                  </div>
                </div>
              ))}
            </div>
            
            {totalPages > 1 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}