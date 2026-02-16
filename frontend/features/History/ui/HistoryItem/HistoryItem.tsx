import React from 'react'

import { MriAnalysisRequest } from '@features/History/types'

import cls from './HistoryItem.module.css'


interface HistoryItemProps {
  request: MriAnalysisRequest
  isSelected: boolean
  onClick: () => void
}

export const HistoryItem: React.FC<HistoryItemProps> = ({
  request,
  isSelected,
  onClick
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }).format(date)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#28a745'
      case 'processing': return '#007bff'
      case 'pending': return '#6c757d'
      case 'failed': return '#dc3545'
      default: return '#6c757d'
    }
  }

  const getAnomaliesSummary = (anomalies: string[]) => {
    if (anomalies.length === 0) return 'Норма'
    if (anomalies.length === 1) return anomalies[0]
    return `${anomalies[0]} (+${anomalies.length - 1})`
  }

  return (
    <div 
      className={`${cls.historyItem} ${isSelected ? cls.selected : ''}`}
      onClick={onClick}
    >
      <div className={cls.itemHeader}>
        <div className={cls.date}>{formatDate(request.createdAt)}</div>
        <div 
          className={cls.status}
          style={{ backgroundColor: getStatusColor(request.status) }}
        >
          {request.status === 'completed' ? '✓' : 
           request.status === 'processing' ? '⟳' : 
           request.status === 'pending' ? '⏱' : '✗'}
        </div>
      </div>
      
      <div className={cls.itemContent}>
        <div className={cls.previewText}>
          {request.description ? (
            request.description.substring(0, 80) + '...'
          ) : (
            <span className={cls.noData}>Нет описания</span>
          )}
        </div>
        
        <div className={cls.anomalies}>
          <span className={cls.anomaliesLabel}>Аномалии:</span>
          <span className={cls.anomaliesValue}>
            {getAnomaliesSummary(request.anomalies || [])}
          </span>
        </div>
      </div>
    </div>
  )
}