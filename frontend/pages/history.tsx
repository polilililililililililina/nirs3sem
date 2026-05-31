import { History } from '@features/History'
import { DoctorHistory } from '@features/History/ui/DoctorHistory/DoctorHistory'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'
import { PageLoader } from '@shared/ui/Loader'

const HistoryPage = () => {
  const { user, isLoading } = useRequireAuth()

  if (isLoading) {
    return <PageLoader />
  }

  if (user?.role === 'doctor' || user?.role === 'admin') {
    return <DoctorHistory />
  }

  return <History />
}

export default HistoryPage
