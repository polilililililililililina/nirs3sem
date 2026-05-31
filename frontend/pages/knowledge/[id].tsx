import { useRouter } from 'next/router'

import { KnowledgeArticle } from '@features/Knowledge'

const KnowledgeArticlePage = () => {
  const router = useRouter()
  const { id } = router.query

  if (typeof id !== 'string') {
    return <p>Загрузка...</p>
  }

  return <KnowledgeArticle id={id} />
}

export default KnowledgeArticlePage
