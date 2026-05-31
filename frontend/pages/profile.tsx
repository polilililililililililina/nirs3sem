import { Profile } from '@features/Profile'

import { useRequireAuth } from '@shared/lib/hooks/useAuth'

const ProfilePage = () => {
  const { isLoading } = useRequireAuth()

  if (isLoading) {
    return <p>Загрузка...</p>
  }

  return <Profile />
}

export default ProfilePage
