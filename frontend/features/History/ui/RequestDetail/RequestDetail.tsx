import React, { useEffect, useMemo, useState } from 'react'

import { useRouter } from 'next/router'

import { ScanItem } from '@features/History/types'
import { SuggestedArticles } from '@features/Knowledge/ui/SuggestedArticles/SuggestedArticles'

import { api } from '@shared/api/api'
import { Button } from '@shared/ui/Button'

import cls from './RequestDetail.module.css'

interface RequestDetailProps {
  request: ScanItem | null
  onDownloadReport?: (request: ScanItem) => void
  onNewAnalysis?: () => void
}

type ResultView = 'mask' | 'heatmap' | 'overlay'
type ImageLayoutMode = 'split' | 'sideBySide'

export const RequestDetail: React.FC<RequestDetailProps> = ({
  request,
  onDownloadReport,
  onNewAnalysis,
}) => {
  const router = useRouter()
  const [inputImageUrl, setInputImageUrl] = useState<string | null>(null)
  const [resultView, setResultView] = useState<ResultView>('mask')
  const [imageLayout, setImageLayout] = useState<ImageLayoutMode>('split')
  const [images, setImages] = useState({
    mask: null as string | null,
    heatmap: null as string | null,
    overlay: null as string | null,
  })

  useEffect(() => {
    if (!request?._id) {
      setInputImageUrl(null)
      setImages({ mask: null, heatmap: null, overlay: null })
      setImageLayout('split')
      return
    }

    let inputUrl: string | null = null
    const resultUrls = {
      mask: null as string | null,
      heatmap: null as string | null,
      overlay: null as string | null,
    }
    let cancelled = false

    const loadImages = async () => {
      try {
        const inputResponse = await api.get(`/scans/input/${request._id}`, {
          responseType: 'blob',
        })

        if (!cancelled) {
          inputUrl = URL.createObjectURL(inputResponse.data)
          setInputImageUrl(inputUrl)
        }
      } catch {
        if (!cancelled) setInputImageUrl(null)
      }

      if (request.status === 'done' && request.result) {
        try {
          const maskResponse = await api.get(`/scans/result/${request._id}`, {
            responseType: 'blob',
          })
          if (!cancelled) {
            resultUrls.mask = URL.createObjectURL(maskResponse.data)
          }
        } catch {
          //
        }

        try {
          const overlayResponse = await api.get(`/scans/heatmap/${request._id}?view=overlay`, {
            responseType: 'blob',
          })
          if (!cancelled) {
            resultUrls.overlay = URL.createObjectURL(overlayResponse.data)
          }
        } catch {
          //
        }

        try {
          const heatmapResponse = await api.get(`/scans/heatmap/${request._id}?view=raw`, {
            responseType: 'blob',
          })
          if (!cancelled) {
            resultUrls.heatmap = URL.createObjectURL(heatmapResponse.data)
          }
        } catch {
          //
        }

        if (!cancelled) {
          setImages(resultUrls)
        }
      } else if (!cancelled) {
        setImages({ mask: null, heatmap: null, overlay: null })
      }
    }

    loadImages()

    return () => {
      cancelled = true
      if (inputUrl) URL.revokeObjectURL(inputUrl)
      Object.values(resultUrls).forEach((url) => {
        if (url) URL.revokeObjectURL(url)
      })
    }
  }, [request?._id, request?.status, request?.result])

  const activeResultImage = useMemo(() => images[resultView], [images, resultView])

  if (!request) {
    return (
      <div className={cls.emptyDetail}>
        <div className={cls.emptyIcon}>👈</div>
        <h3 className={cls.emptyTitle}>Выберите запрос</h3>
        <p className={cls.emptyText}>
          Выберите запрос из списка слева, чтобы просмотреть детальную информацию
        </p>
        {onNewAnalysis && (
          <Button variant="primary" onClick={onNewAnalysis} className={cls.newAnalysisButton}>
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
      minute: '2-digit',
    }).format(date)
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'done':
        return 'Анализ завершен'
      case 'processing':
        return 'В процессе обработки'
      case 'queued':
        return 'Ожидает обработки'
      case 'error':
        return 'Ошибка обработки'
      default:
        return status
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return '✅'
      case 'processing':
        return '🔄'
      case 'queued':
        return '⏳'
      case 'error':
        return '❌'
      default:
        return '📋'
    }
  }

  const hasConfidence = request.confidence !== undefined && request.confidence !== null

  return (
    <div className={cls.requestDetail}>
      <div className={cls.detailHeader}>
        <div>
          <h3 className={cls.detailTitle}>Детали анализа</h3>
          <div className={cls.headerMeta}>
            <span className={cls.date}>{formatDate(request.created_at)}</span>
            <span className={`${cls.status} ${cls[`status${request.status}`]}`}>
              {getStatusIcon(request.status)} {getStatusText(request.status)}
            </span>
          </div>
        </div>

        <div className={cls.headerActions}>
          {request.status === 'done' && (
            <Button
              variant="secondary"
              size="small"
              onClick={() => router.push(`/compare?scan_id=${request._id}`)}
              icon="🔍"
            >
              Похожие случаи
            </Button>
          )}
          {request.status === 'done' && onDownloadReport && (
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
            <Button variant="secondary" size="small" onClick={onNewAnalysis} icon="➕">
              Новый
            </Button>
          )}
        </div>
      </div>

      <div className={cls.imagesSection}>
        <h4 className={cls.sectionTitle}>МРТ изображения</h4>

        {request.source_type === 'dicom_zip' && request.n_slices != null && (
          <p className={cls.volumeMeta}>
            Проанализировано срезов: {request.n_slices}
            {request.representative_slice_idx != null &&
              ` · для просмотра выбран срез №${request.representative_slice_idx + 1}`}
          </p>
        )}

        {request.status === 'done' && (
          <div className={cls.viewToggle}>
            <button
              type="button"
              className={imageLayout === 'sideBySide' ? cls.viewActive : cls.viewButton}
              onClick={() => setImageLayout('sideBySide')}
              disabled={!inputImageUrl || !images.mask}
            >
              Сравнение
            </button>
            <button
              type="button"
              className={imageLayout === 'split' && resultView === 'mask' ? cls.viewActive : cls.viewButton}
              onClick={() => {
                setImageLayout('split')
                setResultView('mask')
              }}
              disabled={!images.mask}
            >
              Маска
            </button>
            <button
              type="button"
              className={
                imageLayout === 'split' && resultView === 'heatmap' ? cls.viewActive : cls.viewButton
              }
              onClick={() => {
                setImageLayout('split')
                setResultView('heatmap')
              }}
              disabled={!images.heatmap}
            >
              Heatmap
            </button>
            <button
              type="button"
              className={
                imageLayout === 'split' && resultView === 'overlay' ? cls.viewActive : cls.viewButton
              }
              onClick={() => {
                setImageLayout('split')
                setResultView('overlay')
              }}
              disabled={!images.overlay}
            >
              Overlay
            </button>
          </div>
        )}

        {imageLayout === 'sideBySide' && inputImageUrl && images.mask ? (
          <div className={cls.sideBySide}>
            <div className={cls.sideBySidePane}>
              <div className={cls.imageLabel}>Исходное изображение</div>
              <div className={cls.imageWrapper}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={inputImageUrl} alt="" className={cls.image} />
              </div>
            </div>
            <div className={cls.sideBySidePane}>
              <div className={cls.imageLabel}>Маска сегментации</div>
              <div className={cls.imageWrapper}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={images.mask} alt="" className={cls.image} />
              </div>
            </div>
          </div>
        ) : (
          <div className={cls.imagesGrid}>
            <div className={cls.imageContainer}>
              <div className={cls.imageLabel}>Исходное изображение</div>
              <div className={cls.imageWrapper}>
                {inputImageUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={inputImageUrl} alt="" className={cls.image} />
                ) : (
                  <div className={cls.imagePlaceholder}>
                    <span>Изображение недоступно</span>
                  </div>
                )}
              </div>
            </div>

            <div className={cls.imageContainer}>
              <div className={cls.imageLabel}>Результат / Grad-CAM</div>
              <div className={cls.imageWrapper}>
                {activeResultImage ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={activeResultImage} alt="" className={cls.image} />
                ) : (
                  <div className={cls.imagePlaceholder}>
                    <span>{request.status === 'processing' ? 'Обработка...' : 'Недоступно'}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {request.status === 'done' && (
        <>
          <div className={cls.analysisResults}>
            <h4 className={cls.sectionTitle}>Результаты анализа</h4>

            {hasConfidence && (
              <div className={cls.confidenceSection}>
                <div className={cls.confidenceHeader}>
                  <span className={cls.confidenceLabel}>Уверенность анализа:</span>
                  <span className={cls.confidenceValue}>{request.confidence! * 100}%</span>
                </div>
                <div className={cls.confidenceBar}>
                  <div
                    className={cls.confidenceFill}
                    style={{ width: `${request.confidence! * 100}%` }}
                  />
                </div>
                <div className={cls.confidenceScale}>
                  <span>Низкая</span>
                  <span>Средняя</span>
                  <span>Высокая</span>
                </div>
              </div>
            )}

            {request.tumor_detected ? (
              <div className={cls.anomalies}>
                <span className={cls.noAnomaliesIcon}>⚠️</span>
                <h5 className={cls.anomalyText}>Обнаружены признаки возможной аномалии</h5>
              </div>
            ) : (
              <div className={cls.noAnomalies}>
                <span className={cls.noAnomaliesIcon}>✅</span>
                <span className={cls.noAnomaliesText}>
                  Признаков аномалии не выявлено. Результат носит вспомогательный характер.
                </span>
              </div>
            )}

            <p className={cls.disclaimer}>
              ⚠️ Результат носит вспомогательный характер и не является медицинским диагнозом.
            </p>
          </div>

          <div className={cls.descriptionSection}>
            <h4 className={cls.sectionTitle}>Заключение</h4>
            <div className={cls.descriptionContent}>
              {request.result_desc?.split('\n').map((paragraph, index) => (
                <p key={index} className={cls.descriptionParagraph}>
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
        </>
      )}

      {request.status === 'done' && (
        <SuggestedArticles scanId={request._id} className={cls.suggestedArticles} />
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

      {request.status === 'queued' && (
        <div className={cls.pendingState}>
          <div className={cls.pendingIcon}>⏳</div>
          <h4 className={cls.pendingTitle}>В очереди на обработку</h4>
          <p className={cls.pendingText}>
            Ваш запрос добавлен в очередь. Обработка начнётся в ближайшее время.
          </p>
        </div>
      )}

      {request.status === 'error' && (
        <div className={cls.failedState}>
          <div className={cls.failedIcon}>❌</div>
          <h4 className={cls.failedTitle}>Ошибка обработки</h4>
          <p className={cls.failedText}>
            {request.result_desc ||
              'При обработке изображения произошла ошибка. Попробуйте загрузить изображение снова.'}
          </p>
        </div>
      )}
    </div>
  )
}
