export type UserRole = 'user' | 'doctor' | 'admin'

export interface AuthUser {
  _id: string
  email: string
  name: string
  role: UserRole
  surname?: string
  middlename?: string
  birthday?: string
  position?: string
  phone?: string
  avatar_url?: string
  clinic_id?: string
  clinic_name?: string
  created_at: string
  updated_at: string
}
