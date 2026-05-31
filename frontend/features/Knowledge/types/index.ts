export interface KnowledgeArticle {
  _id: string
  title: string
  body: string
  tags: string[]
  pathology_type?: string | null
  source?: 'manual' | 'external'
  source_url?: string | null
  is_external?: boolean
  author_id?: string | null
  created_at: string
  updated_at?: string | null
}

export interface KnowledgePagination {
  page: number
  limit: number
  total: number
}

export interface KnowledgeListResponse {
  items: KnowledgeArticle[]
  pagination: KnowledgePagination
}

export const KNOWLEDGE_TAGS = [
  'МРТ',
  'Нейрохирургия',
  'Опухоль головного мозга',
  'Диагностика',
] as const

export const PATHOLOGY_TAG = 'опухоль головного мозга'
