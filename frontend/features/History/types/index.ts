export type ScanStatus = 'queued' | 'processing' | 'done' | 'error'

export interface ScanItem {
  _id: string
  filename: string
  file_path: string
  status: ScanStatus
  user_id?: string | null
  is_guest: boolean
  result?: string | null
  result_desc?: string | null
  source_type?: string
  heatmap_path?: string | null
  heatmap_raw_path?: string | null
  doctor_verified?: boolean | null
  created_at: string
  updated_at?: string | null
  confidence?: number | null
  tumor_detected?: boolean | null
  n_slices?: number | null
  representative_slice_idx?: number | null
}

export interface Pagination {
  page: number
  limit: number
  total: number
}

export interface ScanListResponse {
  items: ScanItem[]
  pagination: Pagination
}

export interface PatientItem {
  _id: string
  email: string
  name?: string
  surname?: string
  middlename?: string
  full_name: string
  birthday?: string
  phone?: string
  clinic_id?: string
  scan_count: number
  last_scan_at: string
}

export interface PatientListResponse {
  items: PatientItem[]
  pagination: Pagination
}

export interface PatientScansResponse {
  patient: Omit<PatientItem, 'scan_count' | 'last_scan_at'>
  items: ScanItem[]
  pagination: Pagination
}

export interface ScanComment {
  _id: string
  scan_id: string
  author_id: string
  author_name: string
  message: string
  created_at: string
}

export interface ExpertConclusion {
  _id: string
  scan_id: string
  doctor_id: string
  doctor_name: string
  text: string
  created_at: string
}

export interface ClinicItem {
  _id: string
  name: string
  address?: string
}
