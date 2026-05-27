import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

export const api = axios.create({
  baseURL: process.env.API_HOST,
})

// REQUEST INTERCEPTOR
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')

  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

// RESPONSE INTERCEPTOR
api.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // access token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refresh_token = localStorage.getItem('refresh_token')

        if (!refresh_token) {
          throw new Error('No refresh token')
        }

        const response = await axios.post(`${process.env.API_HOST}/auth/refresh`, {
          refresh_token,
        })

        const newAccessToken = response.data.access_token

        localStorage.setItem('access_token', newAccessToken)

        // повторяем запрос
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`

        return api(originalRequest)
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')

        window.location.reload()

        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export const isApiError = (error: any): error is AxiosError => axios.isAxiosError(error)
