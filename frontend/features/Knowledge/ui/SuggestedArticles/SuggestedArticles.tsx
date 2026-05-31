import { useEffect, useState } from 'react'

import Link from 'next/link'

import { KnowledgeArticle } from '@features/Knowledge/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'

import cls from './SuggestedArticles.module.css'

interface SuggestedArticlesProps {
  scanId: string
  title?: string
  className?: string
}

export const SuggestedArticles = ({
  scanId,
  title = 'Рекомендуемые статьи',
  className,
}: SuggestedArticlesProps) => {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!scanId) return

    setLoading(true)
    setError(null)

    api
      .get<{ items: KnowledgeArticle[] }>('/knowledge/suggest', {
        params: { scan_id: scanId, limit: 5 },
      })
      .then(({ data }) => setArticles(data.items))
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [scanId])

  if (loading) {
    return <p className={className}>Загрузка статей...</p>
  }

  if (error || articles.length === 0) {
    return null
  }

  return (
    <section className={`${cls.section} ${className || ''}`}>
      <h3 className={cls.title}>{title}</h3>
      <div className={cls.list}>
        {articles.map((article) => (
          <Link key={article._id} href={`/knowledge/${article._id}`} className={cls.item}>
            <span className={cls.itemTitle}>{article.title}</span>
            {article.tags.length > 0 && (
              <span className={cls.itemTags}>{article.tags.slice(0, 2).join(', ')}</span>
            )}
          </Link>
        ))}
      </div>
    </section>
  )
}
