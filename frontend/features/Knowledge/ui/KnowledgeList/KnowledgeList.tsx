import { useEffect, useState } from 'react'

import Link from 'next/link'

import { KNOWLEDGE_TAGS, KnowledgeArticle, KnowledgeListResponse } from '@features/Knowledge/types'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { useAuth } from '@shared/lib/hooks/useAuth'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'
import { Pagination } from '@shared/ui/Pagination'

import cls from './KnowledgeList.module.css'

export const KnowledgeList = () => {
  const { user } = useAuth()

  const [articles, setArticles] = useState<KnowledgeArticle[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeTag, setActiveTag] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [total, setTotal] = useState(0)
  const limit = 10

  const isDoctor = user?.role === 'doctor' || user?.role === 'admin'

  useEffect(() => {
    setLoading(true)
    setError(null)

    api
      .get<KnowledgeListResponse>('/knowledge/', {
        params: {
          page: currentPage,
          limit,
          tag: activeTag || undefined,
          search: search || undefined,
        },
      })
      .then(({ data }) => {
        setArticles(data.items)
        setTotal(data.pagination.total)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [currentPage, activeTag, search])

  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className={cls.page}>
      <div className={cls.header}>
        <h1 className={cls.title}>База знаний</h1>
        {isDoctor && (
          <Link href="/knowledge/edit">
            <Button variant="primary">Создать статью</Button>
          </Link>
        )}
      </div>

      <div className={cls.toolbar}>
        <input
          type="text"
          placeholder="Поиск по заголовку и тексту..."
          className={cls.searchInput}
          value={search}
          onChange={(e) => {
            setCurrentPage(1)
            setSearch(e.target.value)
          }}
        />
      </div>

      <div className={cls.tags}>
        <button
          type="button"
          className={`${cls.tag} ${activeTag === null ? cls.tagActive : ''}`}
          onClick={() => {
            setCurrentPage(1)
            setActiveTag(null)
          }}
        >
          Все
        </button>
        {KNOWLEDGE_TAGS.map((tag) => (
          <button
            key={tag}
            type="button"
            className={`${cls.tag} ${activeTag === tag ? cls.tagActive : ''}`}
            onClick={() => {
              setCurrentPage(1)
              setActiveTag(tag)
            }}
          >
            {tag}
          </button>
        ))}
      </div>

      {loading && <PageLoader />}
      {error && <p className={cls.error}>{error}</p>}

      <div className={cls.list}>
        {articles.map((article) => (
          <Link key={article._id} href={`/knowledge/${article._id}`} className={cls.item}>
            <div className={cls.itemTitle}>{article.title}</div>
            {article.tags.length > 0 && (
              <div className={cls.itemTags}>
                {article.tags.map((tag) => (
                  <span key={tag} className={cls.itemTag}>
                    {tag}
                  </span>
                ))}
              </div>
            )}
            {article.is_external && article.source_url && (
              <div className={cls.itemMeta}>Источник: neurosurgeru.org</div>
            )}
          </Link>
        ))}
      </div>

      {!loading && articles.length === 0 && !error && <p>Статьи пока не добавлены.</p>}

      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  )
}
