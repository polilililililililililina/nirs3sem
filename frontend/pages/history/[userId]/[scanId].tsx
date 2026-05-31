import { useRouter } from 'next/router'

import { ScanDetail } from '@features/History/ui/ScanDetail/ScanDetail'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'

const ScanDetailPage = () => {
  const router = useRouter()
  const { userId, scanId } = router.query
  const { isLoading } = useRequireAuth(['doctor', 'admin'])

  if (isLoading || typeof userId !== 'string' || typeof scanId !== 'string') {
    return <p>Загрузка...</p>
  }

  return <ScanDetail userId={userId} scanId={scanId} />
}

export default ScanDetailPage
