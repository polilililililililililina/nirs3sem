import React from 'react'

import { MriAnalysisRequest } from '@features/History/types'


import { Button } from '@shared/ui/Button'

import cls from './RequestDetail.module.css'


interface RequestDetailProps {
  request: MriAnalysisRequest | null
  onDownloadReport?: (request: MriAnalysisRequest) => void
  onNewAnalysis?: () => void
}

export const RequestDetail: React.FC<RequestDetailProps> = ({
  request,
  onDownloadReport,
  onNewAnalysis
}) => {
  if (!request) {
    return (
      <div className={cls.emptyDetail}>
        <div className={cls.emptyIcon}>👈</div>
        <h3 className={cls.emptyTitle}>Выберите запрос</h3>
        <p className={cls.emptyText}>
          Выберите запрос из списка слева, чтобы просмотреть детальную информацию
        </p>
        {onNewAnalysis && (
          <Button
            variant="primary"
            onClick={onNewAnalysis}
            className={cls.newAnalysisButton}
          >
            Новый анализ МРТ
          </Button>
        )}
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Анализ завершен'
      case 'processing': return 'В процессе обработки'
      case 'pending': return 'Ожидает обработки'
      case 'failed': return 'Ошибка обработки'
      default: return status
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅'
      case 'processing': return '🔄'
      case 'pending': return '⏳'
      case 'failed': return '❌'
      default: return '📋'
    }
  }

  return (
    <div className={cls.requestDetail}>
      <div className={cls.detailHeader}>
        <div>
          <h3 className={cls.detailTitle}>Детали анализа</h3>
          <div className={cls.headerMeta}>
            <span className={cls.date}>{formatDate(request.createdAt)}</span>
            <span className={`${cls.status} ${cls[`status${request.status}`]}`}>
              {getStatusIcon(request.status)} {getStatusText(request.status)}
            </span>
          </div>
        </div>
        
        <div className={cls.headerActions}>
          {request.status === 'completed' && onDownloadReport && (
            <Button
              variant="primary"
              size="small"
              onClick={() => onDownloadReport(request)}
              icon="📥"
            >
              Отчёт
            </Button>
          )}
          {onNewAnalysis && (
            <Button
              variant="secondary"
              size="small"
              onClick={onNewAnalysis}
              icon="➕"
            >
              Новый
            </Button>
          )}
        </div>
      </div>

      <div className={cls.imagesSection}>
        <h4 className={cls.sectionTitle}>МРТ изображения</h4>
        <div className={cls.imagesGrid}>
          <div className={cls.imageContainer}>
            <div className={cls.imageLabel}>Исходное изображение</div>
            <div className={cls.imageWrapper}>
              {request.inputImage ? (
                <img 
                  src={request.inputImage} 
                  alt="Исходное МРТ" 
                  className={cls.image}
                />
              ) : (
                <div className={cls.imagePlaceholder}>
                  <span>Изображение недоступно</span>
                </div>
              )}
            </div>
          </div>
          
          <div className={cls.imageContainer}>
            <div className={cls.imageLabel}>Обработанное изображение</div>
            <div className={cls.imageWrapper}>
              {request.outputImage ? (
                <img 
                  src={request.outputImage} 
                  alt="Обработанное МРТ" 
                  className={cls.image}
                />
              ) : (
                <div className={cls.imagePlaceholder}>
                  <span>{request.status === 'processing' ? 'Обработка...' : 'Недоступно'}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {request.status === 'completed' && (
        <>
          <div className={cls.analysisResults}>
            <h4 className={cls.sectionTitle}>Результаты анализа</h4>
            
            {request.confidence && (
              <div className={cls.confidenceSection}>
                <div className={cls.confidenceHeader}>
                  <span className={cls.confidenceLabel}>Уверенность анализа:</span>
                  <span className={cls.confidenceValue}>{request.confidence}%</span>
                </div>
                <div className={cls.confidenceBar}>
                  <div 
                    className={cls.confidenceFill}
                    style={{ width: `${request.confidence}%` }}
                  />
                </div>
                <div className={cls.confidenceScale}>
                  <span>Низкая</span>
                  <span>Средняя</span>
                  <span>Высокая</span>
                </div>
              </div>
            )}
            
            {request.anomalies && request.anomalies.length > 0 ? (
              <div className={cls.anomaliesSection}>
                <h5 className={cls.subtitle}>Обнаруженные аномалии:</h5>
                <div className={cls.anomaliesList}>
                  {request.anomalies.map((anomaly, index) => (
                    <div key={index} className={cls.anomalyItem}>
                      <span className={cls.anomalyIcon}>⚠️</span>
                      <span className={cls.anomalyText}>{anomaly}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className={cls.noAnomalies}>
                <span className={cls.noAnomaliesIcon}>✅</span>
                <span className={cls.noAnomaliesText}>
                  Аномалий не обнаружено. МРТ картина в пределах нормы.
                </span>
              </div>
            )}
          </div>
          
          <div className={cls.descriptionSection}>
            <h4 className={cls.sectionTitle}>Заключение</h4>
            <div className={cls.descriptionContent}>
              {request.description.split('\n').map((paragraph, index) => (
                <p key={index} className={cls.descriptionParagraph}>
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
          
          {request.recommendations && request.recommendations.length > 0 && (
            <div className={cls.recommendationsSection}>
              <h4 className={cls.sectionTitle}>Рекомендации</h4>
              <div className={cls.recommendationsList}>
                {request.recommendations.map((recommendation, index) => (
                  <div key={index} className={cls.recommendationItem}>
                    <span className={cls.recommendationNumber}>{index + 1}.</span>
                    <span className={cls.recommendationText}>{recommendation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
      
      {request.status === 'processing' && (
        <div className={cls.processingState}>
          <div className={cls.processingIcon}>🔄</div>
          <h4 className={cls.processingTitle}>Обработка изображения</h4>
          <p className={cls.processingText}>
            ИИ анализирует МРТ изображение. Это может занять несколько минут.
          </p>
          <div className={cls.processingProgress}>
            <div className={cls.progressBar}>
              <div className={cls.progressFill} />
            </div>
          </div>
        </div>
      )}
      
      {request.status === 'pending' && (
        <div className={cls.pendingState}>
          <div className={cls.pendingIcon}>⏳</div>
          <h4 className={cls.pendingTitle}>В очереди на обработку</h4>
          <p className={cls.pendingText}>
            Ваш запрос добавлен в очередь. Обработка начнётся в ближайшее время.
          </p>
        </div>
      )}
      
      {request.status === 'failed' && (
        <div className={cls.failedState}>
          <div className={cls.failedIcon}>❌</div>
          <h4 className={cls.failedTitle}>Ошибка обработки</h4>
          <p className={cls.failedText}>
            При обработке изображения произошла ошибка. Попробуйте загрузить изображение снова.
          </p>
        </div>
      )}
    </div>
  )
}