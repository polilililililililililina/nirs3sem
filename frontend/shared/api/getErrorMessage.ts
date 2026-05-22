import axios from 'axios'

interface IValidationError {
  msg: string
}

interface IApiErrorResponse {
  detail?: string | IValidationError[]
}

export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as IApiErrorResponse | undefined

    const detail = data?.detail

    // Обычная ошибка
    if (typeof detail === 'string') {
      return detail
    }

    // Ошибки валидации FastAPI
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((item) => item.msg).join('\n')
    }

    return error.message || 'Ошибка запроса'
  }

  return 'Неизвестная ошибка'
}
