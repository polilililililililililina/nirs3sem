import { useEffect, useState } from 'react'

import { useRouter } from 'next/router'

import { KNOWLEDGE_TAGS, KnowledgeArticle, PATHOLOGY_TAG } from '@features/Knowledge/types'
import { MarkdownContent } from '@features/Knowledge/ui/MarkdownContent/MarkdownContent'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { Button } from '@shared/ui/Button'
import { PageLoader } from '@shared/ui/Loader'

import cls from './ArticleEditor.module.css'

interface ArticleEditorProps {
  articleId?: string
}

export const ArticleEditor = ({ articleId }: ArticleEditorProps) => {
  const router = useRouter()
  const isEdit = Boolean(articleId)

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [customTag, setCustomTag] = useState('')
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!articleId) return

    api
      .get<KnowledgeArticle>(`/knowledge/${articleId}`)
      .then(({ data }) => {
        setTitle(data.title)
        setBody(data.body)
        setSelectedTags(data.tags || [])
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [articleId])

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((item) => item !== tag) : [...prev, tag]
    )
  }

  const addCustomTag = () => {
    const tag = customTag.trim()
    if (!tag || selectedTags.includes(tag)) return
    setSelectedTags((prev) => [...prev, tag])
    setCustomTag('')
  }

  const handleSave = async () => {
    const trimmedTitle = title.trim()
    const trimmedBody = body.trim()

    if (!trimmedTitle || !trimmedBody) {
      setError('Заполните заголовок и текст статьи')
      return
    }

    setSaving(true)
    setError(null)

    const payload = {
      title: trimmedTitle,
      body: trimmedBody,
      tags: selectedTags,
      pathology_type: selectedTags.includes(PATHOLOGY_TAG) ? PATHOLOGY_TAG : null,
    }

    try {
      if (isEdit && articleId) {
        await api.put(`/knowledge/${articleId}`, payload)
        router.push(`/knowledge/${articleId}`)
      } else {
        const { data } = await api.post<KnowledgeArticle>('/knowledge/', payload)
        router.push(`/knowledge/${data._id}`)
      }
    } catch (e) {
      setError(getErrorMessage(e))
      setSaving(false)
    }
  }

  if (loading) {
    return <PageLoader />
  }

  return (
    <div className={cls.page}>
      <div className={cls.header}>
        <h1 className={cls.title}>{isEdit ? 'Редактирование статьи' : 'Создание статьи'}</h1>
        <Button onClick={() => router.push('/knowledge')}>К базе знаний</Button>
      </div>

      {error && <p className={cls.error}>{error}</p>}

      <div className={cls.form}>
        <label className={cls.label}>
          Заголовок
          <input
            className={cls.input}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Название статьи"
          />
        </label>

        <div className={cls.tagsSection}>
          <span className={cls.label}>Теги</span>
          <div className={cls.tagList}>
            {KNOWLEDGE_TAGS.map((tag) => (
              <label key={tag} className={cls.tagOption}>
                <input
                  type="checkbox"
                  checked={selectedTags.includes(tag)}
                  onChange={() => toggleTag(tag)}
                />
                {tag}
              </label>
            ))}
          </div>
          <div className={cls.customTagRow}>
            <input
              className={cls.input}
              value={customTag}
              onChange={(e) => setCustomTag(e.target.value)}
              placeholder="Свой тег"
            />
            <Button variant="secondary" size="small" onClick={addCustomTag}>
              Добавить
            </Button>
          </div>
          {selectedTags.length > 0 && (
            <div className={cls.selectedTags}>
              {selectedTags.map((tag) => (
                <span key={tag} className={cls.selectedTag}>
                  {tag}
                  <button type="button" onClick={() => toggleTag(tag)} aria-label="Удалить тег">
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className={cls.editorGrid}>
          <label className={cls.label}>
            Markdown
            <textarea
              className={cls.textarea}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Текст статьи в формате Markdown..."
              rows={18}
            />
          </label>

          <div className={cls.previewBlock}>
            <span className={cls.label}>Предпросмотр</span>
            <div className={cls.preview}>
              {body.trim() ? (
                <MarkdownContent content={body} />
              ) : (
                <p className={cls.previewEmpty}>Предпросмотр появится здесь</p>
              )}
            </div>
          </div>
        </div>

        <div className={cls.actions}>
          <Button variant="primary" disabled={saving} onClick={handleSave}>
            {saving ? 'Сохранение...' : 'Сохранить'}
          </Button>
          <Button variant="secondary" onClick={() => router.push('/knowledge')}>
            Отмена
          </Button>
        </div>
      </div>
    </div>
  )
}
