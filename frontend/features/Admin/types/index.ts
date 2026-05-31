import { UserRole } from '@shared/lib/auth/types'

export interface AdminUser {
  _id: string
  email: string
  name?: string
  surname?: string
  middlename?: string
  role: UserRole
  clinic_id?: string
  clinic_name?: string
  created_at: string
}

export interface AdminUserListResponse {
  items: AdminUser[]
  pagination: {
    page: number
    limit: number
    total: number
  }
}

export interface Clinic {
  _id: string
  name: string
  address?: string
  description?: string
  created_at: string
}

export interface ClinicListResponse {
  items: Clinic[]
}

export const ROLE_LABELS: Record<UserRole, string> = {
  user: 'Пользователь',
  doctor: 'Врач',
  admin: 'Администратор',
}
