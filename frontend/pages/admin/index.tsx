import { AdminUsers } from '@features/Admin'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'
import { PageLoader } from '@shared/ui/Loader'

const AdminPage = () => {
  const { isLoading } = useRequireAuth(['admin'])

  if (isLoading) {
    return <PageLoader />
  }

  return <AdminUsers />
}

export default AdminPage
