import { useEffect, useState } from 'react'

import Link from 'next/link'
import { useRouter } from 'next/router'

import { KnowledgeArticle as KnowledgeArticleType } from '@features/Knowledge/types'
import { MarkdownContent } from '@features/Knowledge/ui/MarkdownContent/MarkdownContent'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { useAuth } from '@shared/lib/hooks/useAuth'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'

import cls from './KnowledgeArticle.module.css'

interface KnowledgeArticleProps {
  id: string
}

export const KnowledgeArticle = ({ id }: KnowledgeArticleProps) => {
  const router = useRouter()
  const { user } = useAuth()

  const [article, setArticle] = useState<KnowledgeArticleType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  const canEdit =
    user && (user.role === 'admin' || (user.role === 'doctor' && article?.author_id === user._id))

  useEffect(() => {
    api
      .get<KnowledgeArticleType>(`/knowledge/${id}`)
      .then(({ data }) => setArticle(data))
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [id])

  const handleDelete = async () => {
    if (!window.confirm('Удалить статью?')) return

    setDeleting(true)
    setError(null)

    try {
      await api.delete(`/knowledge/${id}`)
      router.push('/knowledge')
    } catch (e) {
      setError(getErrorMessage(e))
      setDeleting(false)
    }
  }

  if (loading) {
    return <PageLoader />
  }

  if (error || !article) {
    return <p className={cls.error}>{error || 'Статья не найдена'}</p>
  }

  return (
    <div className={cls.page}>
      <div className={cls.topBar}>
        <Button onClick={() => router.push('/knowledge')}>К списку статей</Button>

        {canEdit && (
          <div className={cls.actions}>
            <Link href={`/knowledge/edit/${article._id}`}>
              <Button variant="secondary" size="small">
                Редактировать
              </Button>
            </Link>
            <Button variant="secondary" size="small" disabled={deleting} onClick={handleDelete}>
              Удалить
            </Button>
          </div>
        )}
      </div>

      <h1 className={cls.title}>{article.title}</h1>

      {article.tags.length > 0 && (
        <div className={cls.tags}>
          {article.tags.map((tag) => (
            <span key={tag} className={cls.tag}>
              {tag}
            </span>
          ))}
        </div>
      )}

      {article.source_url && (
        <a href={article.source_url} target="_blank" rel="noreferrer" className={cls.sourceLink}>
          Оригинал на neurosurgeru.org
        </a>
      )}

      <MarkdownContent content={article.body} className={cls.body} />
    </div>
  )
}
