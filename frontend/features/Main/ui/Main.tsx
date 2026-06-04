import { useEffect, useMemo, useState } from 'react'

import Link from 'next/link'

import { SuggestedArticles } from '@features/Knowledge/ui/SuggestedArticles/SuggestedArticles'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { useAuth } from '@shared/lib/hooks/useAuth'
import { FileUploader } from '@shared/ui/FileUploader'
import { Loader } from '@shared/ui/Loader'

import cls from './Main.module.css'

const SOCKET = process.env.SOCKET

const UPLOAD_ENDPOINTS = {
  image: '/scans/upload',
  dicom: '/scans/upload-dicom',
  dicom_zip: '/scans/upload-dicom-zip',
} as const

const DICOM_ZIP_MAX_MB = 200

type UploadMode = keyof typeof UPLOAD_ENDPOINTS
type ResultView = 'mask' | 'original' | 'heatmap' | 'overlay' | 'sideBySide'
type ScanStatus = 'idle' | 'queued' | 'processing' | 'done' | 'error' | 'expired'

interface AnalysisResult {
  confidence: number
  tumor_detected: boolean
  result_desc?: string
}

export const Main = () => {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [fileId, setFileId] = useState('')
  const [uploadMode, setUploadMode] = useState<UploadMode>('image')
  const [resultView, setResultView] = useState<ResultView>('mask')
  const [status, setStatus] = useState<ScanStatus>('idle')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [images, setImages] = useState({
    mask: null as string | null,
    original: null as string | null,
    heatmap: null as string | null,
    overlay: null as string | null,
  })

  const resetResults = () => {
    setImages({ mask: null, original: null, heatmap: null, overlay: null })
    setAnalysis(null)
    setResultView('mask')
  }

  const uploadScan = (file: File | null) => {
    if (!file) return

    setError(null)
    resetResults()
    setIsLoading(true)

    const formData = new FormData()
    formData.append('file', file)

    api
      .post(UPLOAD_ENDPOINTS[uploadMode], formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      .then(({ data }) => {
        setFileId(data.id)
        setStatus('queued')
      })
      .catch((e) => {
        setError(getErrorMessage(e))
        setStatus('error')
      })
      .finally(() => setIsLoading(false))
  }

  const loadResultImages = async (scanId: string) => {
    const urls: Partial<Record<Exclude<ResultView, 'sideBySide'>, string>> = {}

    const fetchBlob = async (path: string) => {
      const response = await api.get(path, { responseType: 'blob' })
      return URL.createObjectURL(response.data)
    }

    try {
      urls.original = await fetchBlob(`/scans/input/${scanId}`)
      urls.mask = await fetchBlob(`/scans/result/${scanId}`)
    } catch {
      // optional images
    }

    try {
      urls.overlay = await fetchBlob(`/scans/heatmap/${scanId}?view=overlay`)
    } catch {
      // heatmap may be unavailable
    }

    try {
      urls.heatmap = await fetchBlob(`/scans/heatmap/${scanId}?view=raw`)
    } catch {
      // raw heatmap may be unavailable
    }

    setImages({
      mask: urls.mask || null,
      original: urls.original || null,
      heatmap: urls.heatmap || null,
      overlay: urls.overlay || null,
    })
  }

  useEffect(() => {
    if (!fileId) return

    const token = localStorage.getItem('access_token')
    const wsUrl = token
      ? `${SOCKET}/scans/ws/${fileId}?token=${encodeURIComponent(token)}`
      : `${SOCKET}/scans/ws/${fileId}`

    const socket = new WebSocket(wsUrl)

    socket.onopen = () => socket.send('connect')

    socket.onmessage = async (event) => {
      const data = JSON.parse(event.data)

      if (data.status === 'expired') {
        setError(data.message || 'Гостевой результат удалён. Войдите, чтобы сохранять анализы.')
        setStatus('expired')
        resetResults()
        setFileId('')
        setIsLoading(false)
        socket.close()
        return
      }

      setStatus(data.status)

      if (data.status === 'done') {
        setAnalysis({
          confidence: data.confidence,
          tumor_detected: data.tumor_detected,
          result_desc: data.result_desc,
        })
        await loadResultImages(fileId)
        setIsLoading(false)
        socket.close()
      }

      if (data.status === 'error') {
        const raw = (data.message || data.result_desc || '').trim()
        let msg = raw || 'Произошла ошибка во время обработки'
        if (raw.includes('Lambda layer') || raw.includes('safe_mode')) {
          msg =
            'Не удалось загрузить модель нейросети. Перезапустите API или переобучите модель (train_aa_unet).'
        }
        setError(msg)
        setAnalysis(null)
        setIsLoading(false)
        socket.close()
      }
    }

    socket.onerror = () => {
      setError('Ошибка websocket соединения')
      setIsLoading(false)
      setStatus('error')
    }

    return () => socket.close()
  }, [fileId])

  const activeImage = useMemo(() => {
    if (resultView === 'sideBySide') return null
    return images[resultView]
  }, [images, resultView])

  const showSideBySide =
    resultView === 'sideBySide' && Boolean(images.original && images.mask)

  const hasConfidence = analysis?.confidence !== undefined && analysis?.confidence !== null

  const isProcessing = isLoading || status === 'queued' || status === 'processing'

  const processingLabel = useMemo(() => {
    if (isLoading) return 'Загрузка файла...'
    if (status === 'queued') return 'Файл в очереди на обработку...'
    if (uploadMode === 'dicom_zip') return 'Нейросеть анализирует серию DICOM-срезов...'
    return 'Нейросеть анализирует изображение...'
  }, [isLoading, status, uploadMode])

  const renderUploader = () => {
    if (uploadMode === 'image') {
      return (
        <FileUploader
          key="image"
          acceptType="image"
          allowedExtensions={['.jpg', '.jpeg', '.png', '.gif', '.webp']}
          buttonText="Загрузить фото"
          onFileSelect={uploadScan}
          placeholder="Выберите изображение"
        />
      )
    }

    if (uploadMode === 'dicom') {
      return (
        <FileUploader
          key="dicom"
          acceptType="file"
          allowedExtensions={['.dcm']}
          buttonText="Загрузить DICOM"
          onFileSelect={uploadScan}
          placeholder="Выберите DICOM файл (.dcm)"
        />
      )
    }

    return (
      <FileUploader
        key="dicom_zip"
        acceptType="file"
        allowedExtensions={['.zip']}
        buttonText="Загрузить ZIP"
        onFileSelect={uploadScan}
        placeholder="Выберите ZIP-архив с DICOM (.dcm)"
      />
    )
  }

  return (
    <>
      {!authLoading && !isAuthenticated && (
        <div className={cls.guestBanner}>
          Результат будет удалён через 1 час.{' '}
          <Link href="/login" className={cls.guestLink}>
            Войдите
          </Link>
          , чтобы сохранить анализ в истории.
        </div>
      )}

      <div className={cls.top}>
        <div className={cls.block}>
          <h1 className={cls.white}>Анализ МРТ изображений</h1>

          <div className={cls.modeToggle}>
            <button
              type="button"
              className={uploadMode === 'image' ? cls.modeActive : cls.modeButton}
              onClick={() => setUploadMode('image')}
            >
              Изображение
            </button>
            <button
              type="button"
              className={uploadMode === 'dicom' ? cls.modeActive : cls.modeButton}
              onClick={() => setUploadMode('dicom')}
            >
              DICOM (.dcm)
            </button>
            <button
              type="button"
              className={uploadMode === 'dicom_zip' ? cls.modeActive : cls.modeButton}
              onClick={() => setUploadMode('dicom_zip')}
            >
              DICOM (ZIP)
            </button>
          </div>

          {renderUploader()}
        </div>

        <div className={cls.block}>
          <h1 className={cls.white}>Результат обработки</h1>

          {status === 'done' && (
            <div className={cls.viewToggle}>
              <button
                type="button"
                className={resultView === 'original' ? cls.viewActive : cls.viewButton}
                onClick={() => setResultView('original')}
                disabled={!images.original}
              >
                Исходник
              </button>
              <button
                type="button"
                className={resultView === 'mask' ? cls.viewActive : cls.viewButton}
                onClick={() => setResultView('mask')}
                disabled={!images.mask}
              >
                Маска
              </button>
              <button
                type="button"
                className={resultView === 'sideBySide' ? cls.viewActive : cls.viewButton}
                onClick={() => setResultView('sideBySide')}
                disabled={!images.original || !images.mask}
              >
                Сравнение
              </button>
              <button
                type="button"
                className={resultView === 'heatmap' ? cls.viewActive : cls.viewButton}
                onClick={() => setResultView('heatmap')}
                disabled={!images.heatmap}
              >
                Heatmap
              </button>
              <button
                type="button"
                className={resultView === 'overlay' ? cls.viewActive : cls.viewButton}
                onClick={() => setResultView('overlay')}
                disabled={!images.overlay}
              >
                Overlay
              </button>
            </div>
          )}

          <div className={cls.border}>
            {isProcessing && !showSideBySide && !activeImage && (
              <div className={cls.processingState}>
                <Loader size="lg" label={processingLabel} />
              </div>
            )}

            {showSideBySide && (
              <div className={cls.sideBySide}>
                <div className={cls.sideBySidePane}>
                  <span className={cls.sideBySideLabel}>Исходник</span>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img className={cls.resultImg} src={images.original!} alt="Исходное изображение" />
                </div>
                <div className={cls.sideBySidePane}>
                  <span className={cls.sideBySideLabel}>Маска сегментации</span>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img className={cls.resultImg} src={images.mask!} alt="Маска сегментации" />
                </div>
              </div>
            )}

            {!showSideBySide && activeImage && (
              // eslint-disable-next-line @next/next/no-img-element
              <img className={cls.resultImg} src={activeImage} alt="Результат обработки" />
            )}

            {!showSideBySide &&
              !activeImage &&
              !isProcessing && (
                <>
                  {status === 'error' && (
                    <p>Произошла ошибка во время обработки. Пожалуйста, попробуйте снова.</p>
                  )}
                  {status === 'expired' && (
                    <p className={cls.error}>
                      {error || 'Гостевой результат удалён. Войдите, чтобы сохранять анализы.'}
                    </p>
                  )}
                  {error && status !== 'expired' && <p className={cls.error}>{error}</p>}
                  {status === 'idle' && <p>Загрузите файл, чтобы получить результаты.</p>}
                </>
              )}
          </div>

          {status === 'error' && error && (
            <div className={cls.errorBox}>
              <p className={cls.error}>{error}</p>
            </div>
          )}

          {analysis && status === 'done' && (
            <div className={cls.analysisBox}>
              {hasConfidence && (
                <p className={cls.white}>Уверенность: {(analysis.confidence * 100).toFixed(1)}%</p>
              )}

              {analysis.result_desc ? (
                <p className={cls.white}>{analysis.result_desc}</p>
              ) : analysis.tumor_detected ? (
                <p className={cls.warning}>
                  Обнаружены признаки возможной аномалии. Результат носит вспомогательный характер и
                  не является медицинским диагнозом.
                </p>
              ) : (
                <p className={cls.success}>
                  Признаков аномалии не выявлено. Результат носит вспомогательный характер.
                </p>
              )}
            </div>
          )}

          {status === 'done' && fileId && (
            <SuggestedArticles scanId={fileId} className={cls.suggestedArticles} />
          )}
        </div>
      </div>

      <div className={cls.bottom}>
        <h2 className={cls.white}>
          Загрузите МРТ-снимок (изображение, DICOM или ZIP с серией) и получите автоматическую
          сегментацию подозрительных областей с Grad-CAM визуализацией.
        </h2>

        <h4>
          <p className={`${cls.warning} ${cls.white}`}>
            ⚠️ Результаты анализа носят вспомогательный характер и не заменяют медицинскую
            диагностику врача. Нейросеть не ставит диагноз.
          </p>
        </h4>

        <h3 className={cls.white}>Как это работает</h3>
        <h4 className={cls.white}>
          1. Загрузка — изображение (PNG/JPG), один DICOM (.dcm) или ZIP с папкой DICOM.
        </h4>
        <h4 className={cls.white}>
          2. Анализ нейросетью — модель сегментирует возможные отклонения.
        </h4>
        <h4 className={cls.white}>
          3. Grad-CAM — heatmap показывает области, повлиявшие на решение модели.
        </h4>
      </div>
    </>
  )
}
