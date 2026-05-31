import { ArticleEditor } from '@features/Knowledge'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'

const KnowledgeEditPage = () => {
  const { isLoading } = useRequireAuth(['doctor'])

  if (isLoading) {
    return <p>Загрузка...</p>
  }

  return <ArticleEditor />
}

export default KnowledgeEditPage
