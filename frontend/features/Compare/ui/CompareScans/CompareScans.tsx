import { useEffect, useMemo, useState } from 'react'

import { useRouter } from 'next/router'

import { ScanItem, ScanListResponse } from '@features/History/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'

import cls from './CompareScans.module.css'

const MAX_SELECTED = 4

export const CompareScans = () => {
  const router = useRouter()
  const scanId = typeof router.query.scan_id === 'string' ? router.query.scan_id : ''

  const [similarScans, setSimilarScans] = useState<ScanItem[]>([])
  const [allScans, setAllScans] = useState<ScanItem[]>([])
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [imageUrls, setImageUrls] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!scanId) return

    setLoading(true)
    setError(null)

    Promise.all([
      api.get<{ items: ScanItem[] }>('/scans/similar', { params: { scan_id: scanId, limit: 10 } }),
      api.get<ScanListResponse>('/scans', { params: { page: 1, limit: 50, status: 'done' } }),
      api.get<ScanItem>(`/scans/${scanId}`),
    ])
      .then(([similarRes, historyRes, baseScanRes]) => {
        const baseScan = baseScanRes.data
        const merged = [baseScan, ...similarRes.data.items]
        const unique = merged.filter(
          (scan, index, arr) => arr.findIndex((item) => item._id === scan._id) === index
        )

        setSimilarScans(similarRes.data.items)
        setAllScans(unique)
        setSelectedIds(unique.slice(0, Math.min(MAX_SELECTED, unique.length)).map((s) => s._id))
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [scanId])

  const selectedScans = useMemo(
    () =>
      selectedIds
        .map((id) => allScans.find((scan) => scan._id === id))
        .filter(Boolean) as ScanItem[],
    [selectedIds, allScans]
  )

  useEffect(() => {
    let cancelled = false
    const urls: Record<string, string> = {}

    const loadImages = async () => {
      for (const scan of selectedScans) {
        try {
          const response = await api.get(`/scans/input/${scan._id}`, { responseType: 'blob' })
          if (!cancelled) {
            urls[scan._id] = URL.createObjectURL(response.data)
          }
        } catch {
          //
        }
      }

      if (!cancelled) {
        setImageUrls((prev) => {
          Object.values(prev).forEach((url) => URL.revokeObjectURL(url))
          return urls
        })
      }
    }

    if (selectedScans.length > 0) {
      loadImages()
    } else {
      setImageUrls({})
    }

    return () => {
      cancelled = true
      Object.values(urls).forEach((url) => URL.revokeObjectURL(url))
    }
  }, [selectedScans])

  const toggleScan = (id: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id)
      }
      if (prev.length >= MAX_SELECTED) {
        return prev
      }
      return [...prev, id]
    })
  }

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(new Date(dateString))
  }

  return (
    <div className={cls.page}>
      <header className={cls.header}>
        <div>
          <h1 className={cls.title}>Сравнение анализов</h1>
          <p className={cls.subtitle}>Выберите от 2 до 4 завершённых анализов для сравнения</p>
        </div>
        <Button onClick={() => router.push('/history')}>К истории</Button>
      </header>

      {!scanId && (
        <div className={cls.notice}>Укажите scan_id в URL, например: /compare?scan_id=...</div>
      )}

      {error && <p className={cls.error}>{error}</p>}
      {loading && <PageLoader />}

      {allScans.length > 0 && (
        <>
          <section className={cls.selector}>
            <h2 className={cls.sectionTitle}>Доступные анализы</h2>
            <div className={cls.scanOptions}>
              {allScans.map((scan) => {
                const selected = selectedIds.includes(scan._id)
                const isSimilar = similarScans.some((item) => item._id === scan._id)

                return (
                  <button
                    key={scan._id}
                    type="button"
                    className={`${cls.option} ${selected ? cls.optionSelected : ''}`}
                    onClick={() => toggleScan(scan._id)}
                  >
                    <span>{formatDate(scan.created_at)}</span>
                    <span>{scan.tumor_detected ? '⚠️ Аномалия' : '✅ Норма'}</span>
                    {scan.confidence != null && <span>{Math.round(scan.confidence * 100)}%</span>}
                    {isSimilar && <span className={cls.similarTag}>Похожий</span>}
                  </button>
                )
              })}
            </div>
          </section>

          <section className={cls.compareGrid}>
            {selectedScans.map((scan) => (
              <div key={scan._id} className={cls.compareCard}>
                <h3>{formatDate(scan.created_at)}</h3>
                <div className={cls.imageWrap}>
                  {imageUrls[scan._id] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={imageUrls[scan._id]} alt="" className={cls.image} />
                  ) : (
                    <div className={cls.imagePlaceholder}>Нет превью</div>
                  )}
                </div>
                <p className={cls.meta}>
                  {scan.tumor_detected ? 'Обнаружена аномалия' : 'Без аномалий'}
                </p>
                {scan.confidence != null && (
                  <p className={cls.meta}>Уверенность: {Math.round(scan.confidence * 100)}%</p>
                )}
                <p className={cls.desc}>{scan.result_desc || 'Без описания'}</p>
              </div>
            ))}
          </section>
        </>
      )}
    </div>
  )
}
