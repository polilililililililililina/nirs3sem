import { useRouter } from 'next/router'

import { PatientScans } from '@features/History/ui/PatientScans/PatientScans'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'

const PatientHistoryPage = () => {
  const router = useRouter()
  const { userId } = router.query
  const { isLoading } = useRequireAuth(['doctor', 'admin'])

  if (isLoading || typeof userId !== 'string') {
    return <p>Загрузка...</p>
  }

  return <PatientScans userId={userId} />
}

export default PatientHistoryPage
