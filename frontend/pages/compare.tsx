import { CompareScans } from '@features/Compare'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'
import { PageLoader } from '@shared/ui/Loader'

const ComparePage = () => {
  const { isLoading } = useRequireAuth()

  if (isLoading) {
    return <PageLoader />
  }

  return <CompareScans />
}

export default ComparePage
