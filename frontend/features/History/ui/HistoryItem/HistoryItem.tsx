import React from 'react'

import { ScanItem } from '@features/History/types'

import cls from './HistoryItem.module.css'

interface HistoryItemProps {
  request: ScanItem
  isSelected: boolean
  onClick: () => void
}

export const HistoryItem: React.FC<HistoryItemProps> = ({ request, isSelected, onClick }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }).format(date)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#28a745'
      case 'processing':
        return '#007bff'
      case 'pending':
        return '#6c757d'
      case 'failed':
        return '#dc3545'
      default:
        return '#6c757d'
    }
  }

  return (
    <div className={`${cls.historyItem} ${isSelected ? cls.selected : ''}`} onClick={onClick}>
      <div className={cls.itemHeader}>
        <div className={cls.date}>{formatDate(request.created_at)}</div>
        <div className={cls.status} style={{ backgroundColor: getStatusColor(request.status) }}>
          {request.status === 'done'
            ? '✓'
            : request.status === 'processing'
              ? '⟳'
              : request.status === 'queued'
                ? '⏱'
                : '✗'}
        </div>
      </div>

      <div className={cls.itemContent}>
        <div className={cls.previewText}>
          {request.result_desc ? (
            request.result_desc.substring(0, 80) + '...'
          ) : (
            <span className={cls.noData}>Нет описания</span>
          )}
        </div>

        <div className={cls.anomalies}>
          <span className={cls.anomaliesLabel}>Аномалии:</span>
          <span className={cls.anomaliesValue}>
            {request.tumor_detected ? 'Выявлены' : 'Не выявлены'}
          </span>
        </div>
      </div>
    </div>
  )
}
