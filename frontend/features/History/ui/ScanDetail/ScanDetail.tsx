import { useCallback, useEffect, useState } from 'react'

import { useRouter } from 'next/router'

import { ExpertConclusion, ScanComment, ScanItem } from '@features/History/types'
import { RequestDetail } from '@features/History/ui/RequestDetail/RequestDetail'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { useAuth } from '@shared/lib/hooks/useAuth'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'

import cls from './ScanDetail.module.css'

interface ScanDetailProps {
  userId: string
  scanId: string
}

export const ScanDetail = ({ userId, scanId }: ScanDetailProps) => {
  const router = useRouter()
  const { user } = useAuth()

  const [scan, setScan] = useState<ScanItem | null>(null)
  const [comments, setComments] = useState<ScanComment[]>([])
  const [conclusion, setConclusion] = useState<ExpertConclusion | null>(null)
  const [commentText, setCommentText] = useState('')
  const [conclusionText, setConclusionText] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const isDoctor = user?.role === 'doctor' || user?.role === 'admin'

  const loadData = useCallback(async () => {
    setError(null)
    setLoading(true)

    try {
      const [scanRes, commentsRes, conclusionRes] = await Promise.all([
        api.get<ScanItem>(`/scans/${scanId}`),
        api.get<{ items: ScanComment[] }>(`/scans/${scanId}/comments`),
        api.get<{ conclusion: ExpertConclusion | null }>(`/scans/${scanId}/conclusion`),
      ])

      setScan(scanRes.data)
      setComments(commentsRes.data.items)
      setConclusion(conclusionRes.data.conclusion)
      setConclusionText(conclusionRes.data.conclusion?.text || '')
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }, [scanId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleAddComment = async () => {
    const message = commentText.trim()
    if (!message) return

    setActionLoading(true)
    setError(null)

    try {
      const { data } = await api.post<ScanComment>(`/scans/${scanId}/comments`, { message })
      setComments((prev) => [...prev, data])
      setCommentText('')
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  const handleSaveConclusion = async () => {
    const text = conclusionText.trim()
    if (!text) return

    setActionLoading(true)
    setError(null)

    try {
      const { data } = await api.post<ExpertConclusion>(`/scans/${scanId}/conclusion`, { text })
      setConclusion(data)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  const handleVerify = async (verified: boolean) => {
    setActionLoading(true)
    setError(null)

    try {
      const { data } = await api.put<ScanItem>(`/scans/${scanId}/verify`, { verified })
      setScan(data)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(dateString))
  }

  if (loading) {
    return <PageLoader />
  }

  if (!scan) {
    return (
      <div className={cls.page}>
        <p className={cls.error}>{error || 'Анализ не найден'}</p>
        <Button onClick={() => router.push(`/history/${userId}`)}>К пациенту</Button>
      </div>
    )
  }

  return (
    <div className={cls.page}>
      <header className={cls.header}>
        <Button onClick={() => router.push(`/history/${userId}`)}>К пациенту</Button>
        <Button variant="primary" onClick={() => router.push(`/compare?scan_id=${scanId}`)}>
          Похожие случаи
        </Button>
      </header>

      {error && <p className={cls.error}>{error}</p>}

      <RequestDetail request={scan} />

      {isDoctor && (
        <section className={cls.doctorPanel}>
          <h2 className={cls.sectionTitle}>Верификация результата ИИ</h2>
          <div className={cls.verifyRow}>
            {scan.doctor_verified === true && (
              <span className={cls.verifiedBadge}>✅ Подтверждено врачом</span>
            )}
            {scan.doctor_verified === false && (
              <span className={cls.rejectedBadge}>❌ Не согласен с результатом</span>
            )}
            {scan.doctor_verified == null && (
              <span className={cls.pendingBadge}>Ожидает проверки</span>
            )}
            <div className={cls.verifyActions}>
              <Button
                variant="primary"
                size="small"
                disabled={actionLoading}
                onClick={() => handleVerify(true)}
              >
                Подтвердить
              </Button>
              <Button
                variant="secondary"
                size="small"
                disabled={actionLoading}
                onClick={() => handleVerify(false)}
              >
                Не согласен
              </Button>
            </div>
          </div>

          <h2 className={cls.sectionTitle}>Комментарии</h2>
          {comments.length === 0 ? (
            <p className={cls.emptyText}>Комментариев пока нет</p>
          ) : (
            <ul className={cls.commentList}>
              {comments.map((comment) => (
                <li key={comment._id} className={cls.commentItem}>
                  <div className={cls.commentMeta}>
                    <strong>{comment.author_name}</strong>
                    <span>{formatDate(comment.created_at)}</span>
                  </div>
                  <p>{comment.message}</p>
                </li>
              ))}
            </ul>
          )}

          <div className={cls.form}>
            <textarea
              className={cls.textarea}
              placeholder="Добавить комментарий..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              rows={3}
            />
            <Button
              variant="primary"
              disabled={actionLoading || !commentText.trim()}
              onClick={handleAddComment}
            >
              Отправить
            </Button>
          </div>

          <h2 className={cls.sectionTitle}>Экспертное заключение</h2>
          {conclusion && (
            <div className={cls.conclusionBox}>
              <div className={cls.commentMeta}>
                <strong>{conclusion.doctor_name}</strong>
                <span>{formatDate(conclusion.created_at)}</span>
              </div>
              <p>{conclusion.text}</p>
            </div>
          )}

          <div className={cls.form}>
            <textarea
              className={cls.textarea}
              placeholder="Текст экспертного заключения..."
              value={conclusionText}
              onChange={(e) => setConclusionText(e.target.value)}
              rows={5}
            />
            <Button
              variant="primary"
              disabled={actionLoading || !conclusionText.trim()}
              onClick={handleSaveConclusion}
            >
              {conclusion ? 'Обновить заключение' : 'Сохранить заключение'}
            </Button>
          </div>
        </section>
      )}
    </div>
  )
}
