import { useRouter } from 'next/router'

import { ArticleEditor } from '@features/Knowledge'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'

const KnowledgeEditArticlePage = () => {
  const router = useRouter()
  const { id } = router.query
  const { isLoading } = useRequireAuth(['doctor'])

  if (isLoading || typeof id !== 'string') {
    return <p>Загрузка...</p>
  }

  return <ArticleEditor articleId={id} />
}

export default KnowledgeEditArticlePage
