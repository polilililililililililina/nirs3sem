import { AdminClinics } from '@features/Admin'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'
import { PageLoader } from '@shared/ui/Loader'

const AdminClinicsPage = () => {
  const { isLoading } = useRequireAuth(['admin'])

  if (isLoading) {
    return <PageLoader />
  }

  return <AdminClinics />
}

export default AdminClinicsPage
