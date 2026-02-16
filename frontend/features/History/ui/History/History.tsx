import React, { useState } from 'react'


import { mockMriRequests } from '@features/History/modules/mockData'
import { MriAnalysisRequest } from '@features/History/types'

import { Button } from '@shared/ui/Button'

import { HistoryList } from '../HistoryList/HistoryList'
import { RequestDetail } from '../RequestDetail/RequestDetail'

import cls from './History.module.css'


export const History: React.FC = () => {
  const [selectedRequest, setSelectedRequest] = useState<MriAnalysisRequest | null>(null)
  const [requests, setRequests] = useState<MriAnalysisRequest[]>(mockMriRequests)

  const handleSelectRequest = (request: MriAnalysisRequest) => {
    setSelectedRequest(request)
  }

  const handleDownloadReport = (request: MriAnalysisRequest) => {
    // Здесь будет логика скачивания отчёта
    console.log('Download report for:', request.id)
    alert(`Отчёт по анализу ${request.id} будет скачан`)
  }

  const handleNewAnalysis = () => {
    // Навигация на страницу нового анализа
    console.log('Navigate to new analysis')
  }

  const handleDeleteRequest = (requestId: string) => {
    if (window.confirm('Вы уверены, что хотите удалить этот запрос?')) {
      setRequests(prev => prev.filter(req => req.id !== requestId))
      if (selectedRequest?.id === requestId) {
        setSelectedRequest(null)
      }
    }
  }

  const handleRetryRequest = (request: MriAnalysisRequest) => {
    // Логика повторной обработки
    console.log('Retry request:', request.id)
  }

  // Фильтрация по статусу
  const [filter, setFilter] = useState<'all' | 'completed' | 'processing' | 'failed'>('all')
  
  const filteredRequests = requests.filter(request => {
    if (filter === 'all') return true
    return request.status === filter
  })

  return (
    <div className={cls.historyPage}>
      <header className={cls.pageHeader}>
        <h1 className={cls.pageTitle}>История анализов МРТ</h1>
        <div className={cls.headerActions}>
          <Button
            variant="primary"
            onClick={handleNewAnalysis}
            icon="➕"
          >
            Новый анализ МРТ
          </Button>
        </div>
      </header>

      <div className={cls.filters}>
        <div className={cls.filterButtons}>
          <button
            className={`${cls.filterButton} ${filter === 'all' ? cls.active : ''}`}
            onClick={() => setFilter('all')}
          >
            Все ({requests.length})
          </button>
          <button
            className={`${cls.filterButton} ${filter === 'completed' ? cls.active : ''}`}
            onClick={() => setFilter('completed')}
          >
            Завершённые ({requests.filter(r => r.status === 'completed').length})
          </button>
          <button
            className={`${cls.filterButton} ${filter === 'processing' ? cls.active : ''}`}
            onClick={() => setFilter('processing')}
          >
            В обработке ({requests.filter(r => r.status === 'processing').length})
          </button>
          <button
            className={`${cls.filterButton} ${filter === 'failed' ? cls.active : ''}`}
            onClick={() => setFilter('failed')}
          >
            Ошибки ({requests.filter(r => r.status === 'failed').length})
          </button>
        </div>
        
        <div className={cls.searchBox}>
          <input
            type="text"
            placeholder="Поиск по описанию..."
            className={cls.searchInput}
          />
          <button className={cls.searchButton}>🔍</button>
        </div>
      </div>

      <div className={cls.contentLayout}>
        <div className={cls.listColumn}>
          <HistoryList
            requests={filteredRequests}
            onSelectRequest={handleSelectRequest}
            selectedRequestId={selectedRequest?.id}
          />
        </div>
        
        <div className={cls.detailColumn}>
          <RequestDetail
            request={selectedRequest}
            onDownloadReport={handleDownloadReport}
            onNewAnalysis={handleNewAnalysis}
          />
          
          {selectedRequest && (
            <div className={cls.detailActions}>
              {selectedRequest.status === 'failed' && (
                <Button
                  variant="secondary"
                  onClick={() => handleRetryRequest(selectedRequest)}
                  icon="🔄"
                >
                  Повторить обработку
                </Button>
              )}
              <Button
                variant="secondary"
                onClick={() => handleDeleteRequest(selectedRequest.id)}
                icon="🗑️"
              >
                Удалить запрос
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}