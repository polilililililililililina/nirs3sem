export interface MriAnalysisRequest {
  id: string
  inputImage: string // Входное МРТ изображение (URL или base64)
  outputImage: string // Обработанное изображение с выделенными областями (URL или base64)
  description: string // Текст-описание результатов анализа
  createdAt: string // Дата создания запроса
  status: 'pending' | 'processing' | 'completed' | 'failed' // Статус обработки
  anomalies?: string[] // Тип обнаруженных аномалий
  confidence?: number // Уровень уверенности (0-100)
  recommendations?: string[] // Рекомендации
}

export interface PaginationMeta {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
}