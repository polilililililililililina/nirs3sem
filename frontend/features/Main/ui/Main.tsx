import { useEffect, useState } from 'react'

import { api } from '@shared/api/api'
import { getErrorMessage } from '@shared/api/getErrorMessage'
import { FileUploader } from '@shared/ui/FileUploader'

import cls from './Main.module.css'

export const Main = () => {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [fileId, setFileId] = useState('')
  const [resultImage, setResultImage] = useState<string | null>(null)
  const [status, setStatus] = useState<'idle' | 'queued' | 'processing' | 'done' | 'error'>('idle')

  const uploadScan = (file: File | null) => {
    if (!file) return

    setError(null)
    setResultImage(null)
    setIsLoading(true)

    const formData = new FormData()
    formData.append('file', file)

    api
      .post('/scans/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      .then(({ data }) => {
        setFileId(data.id)
        setStatus('queued')
      })
      .catch((e) => {
        setError(getErrorMessage(e))
        setStatus('error')
      })
      .finally(() => setIsLoading(false))
  }

  useEffect(() => {
    if (!fileId) return

    const socket = new WebSocket(`ws://localhost:8000/scans/ws/${fileId}`)

    socket.onopen = () => socket.send('connect')

    socket.onmessage = async (event) => {
      const data = JSON.parse(event.data)

      setStatus(data.status)

      if (data.status === 'done') {
        const result = await api.get(`/scans/result/${fileId}`, {
          responseType: 'blob',
        })

        const imageUrl = URL.createObjectURL(result.data)
        setResultImage(imageUrl)
        setIsLoading(false)
        socket.close()
      }
    }

    socket.onerror = () => {
      setError('Ошибка websocket соединения')
      setIsLoading(false)
    }

    return () => socket.close()
  }, [fileId])

  return (
    <>
      {isLoading && <p>Загрузка...</p>}

      <div className={cls.top}>
        <div className={cls.block}>
          <h1>Анализ МРТ изображений</h1>
          <FileUploader
            acceptType="image"
            allowedExtensions={['.jpg', '.jpeg', '.png', '.gif', '.webp']}
            maxSizeMB={5}
            buttonText="Загрузить фото"
            onFileSelect={uploadScan}
            placeholder="Выберите изображение"
          />
        </div>
        <div className={cls.block}>
          <h1>Результат обработки</h1>
          <div className={cls.border}>
            {resultImage ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img className={cls.resultImg} src={resultImage} alt="Результат обработки" />
            ) : (
              <>
                {status === 'error' && (
                  <p>Произошла ошибка во время обработки. Пожалуйста, попробуйте снова.</p>
                )}
                {error && <p className={cls.error}>{error}</p>}
                {status === 'queued' && <p>Изображение ожидает обработки...</p>}
                {status === 'processing' && <p>Нейросеть анализирует изображение...</p>}
                {status === 'idle' && <p>Загрузите изображение, чтобы получить результаты.</p>}
              </>
            )}
          </div>
        </div>
      </div>

      <div className={cls.bottom}>
        <h2>
          Загрузите МРТ-снимок и получите автоматическую сегментацию подозрительных областей. Наш
          алгоритм помогает врачам принимать решения быстрее и увереннее.
        </h2>
        <h3>Как это работает</h3>
        <p>
          1. Загрузка изображения - Вы добавляете МРТ-снимок в формате изображения прямо в браузере.
        </p>
        <p>
          2. Анализ нейросетью - модель машинного обучения обрабатывает данные и находит возможные
          отклонения.
        </p>
        <p>3. Визуальный результат - Вы получаете изображение с подсвеченными зонами риска.</p>
        <h3>Преимущества</h3>
        <ul>
          <li>Поддержка медицинских MRI изображений</li>
          <li>Автоматическая сегментация опухолей</li>
          <li>Быстрая обработка</li>
          <li>Удобный веб-интерфейс</li>
          <li>Подходит для вспомогательной диагностики</li>
        </ul>
        <p className={cls.bold}>
          Результаты анализа носят вспомогательный характер и не заменяют медицинскую диагностику
          врача.
        </p>
        <p>
          Современные технологии — в помощь медицинским решениям. Используйте искусственный
          интеллект для более точной и быстрой оценки МРТ-снимков.
        </p>
      </div>
    </>
  )
}
