import { useEffect, useState } from 'react'

import { AdminUser, AdminUserListResponse, ROLE_LABELS } from '@features/Admin/types'
import { AdminNav } from '@features/Admin/ui/AdminNav/AdminNav'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { UserRole } from '@shared/lib/auth/types'
import { PageLoader } from '@shared/ui/Loader'
import { Pagination } from '@shared/ui/Pagination'

import cls from './AdminUsers.module.css'

const ROLES: UserRole[] = ['user', 'doctor', 'admin']

export const AdminUsers = () => {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [roleError, setRoleError] = useState<string | null>(null)
  const [updatingId, setUpdatingId] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [total, setTotal] = useState(0)
  const limit = 10

  useEffect(() => {
    setLoading(true)
    setError(null)

    api
      .get<AdminUserListResponse>('/admin/users', {
        params: {
          page: currentPage,
          limit,
          search: search || undefined,
        },
      })
      .then(({ data }) => {
        setUsers(data.items)
        setTotal(data.pagination.total)
      })
      .catch((e) => setError(getErrorMessage(e)))
      .finally(() => setLoading(false))
  }, [currentPage, search])

  const totalPages = Math.ceil(total / limit) || 1

  const formatName = (user: AdminUser) => {
    const parts = [user.surname, user.name, user.middlename].filter(Boolean)
    return parts.join(' ') || '—'
  }

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(new Date(dateString))
  }

  const handleRoleChange = async (userId: string, role: UserRole) => {
    setRoleError(null)
    setUpdatingId(userId)

    try {
      const { data } = await api.patch<AdminUser>(`/admin/users/${userId}/role`, { role })
      setUsers((prev) => prev.map((user) => (user._id === userId ? data : user)))
    } catch (e) {
      setRoleError(getErrorMessage(e))
    } finally {
      setUpdatingId(null)
    }
  }

  return (
    <div className={cls.page}>
      <AdminNav />

      <header className={cls.header}>
        <h1 className={cls.title}>Управление пользователями</h1>
      </header>

      <div className={cls.toolbar}>
        <input
          type="text"
          placeholder="Поиск по email или ФИО..."
          className={cls.searchInput}
          value={search}
          onChange={(e) => {
            setCurrentPage(1)
            setSearch(e.target.value)
          }}
        />
      </div>

      {error && <p className={cls.error}>{error}</p>}
      {roleError && <p className={cls.error}>{roleError}</p>}
      {loading && <PageLoader />}

      {!loading && (
        <div className={cls.tableWrap}>
          <table className={cls.table}>
            <thead>
              <tr>
                <th>Email</th>
                <th>ФИО</th>
                <th>Роль</th>
                <th>Клиника</th>
                <th>Регистрация</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user._id}>
                  <td>{user.email}</td>
                  <td>{formatName(user)}</td>
                  <td>
                    <select
                      className={cls.roleSelect}
                      value={user.role}
                      disabled={updatingId === user._id}
                      onChange={(e) => handleRoleChange(user._id, e.target.value as UserRole)}
                    >
                      {ROLES.map((role) => (
                        <option key={role} value={role}>
                          {ROLE_LABELS[role]}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>{user.clinic_name || '—'}</td>
                  <td>{formatDate(user.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {users.length === 0 && <p className={cls.empty}>Пользователи не найдены</p>}
        </div>
      )}

      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  )
}
