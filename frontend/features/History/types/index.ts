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
  created_at: string
  confidence: number
  tumor_detected: boolean
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
