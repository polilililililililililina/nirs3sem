import React, { useRef, useState, useCallback, ChangeEvent } from 'react'

import { Button } from '../Button'

import cls from './FileUploader.module.css'

export type FileType = 'image' | 'file' | 'document' | 'video' | 'audio'

export interface FileUploaderProps {
  /** Тип загружаемых файлов */
  acceptType: FileType
  /** Допустимые расширения файлов (например: ['.png', '.jpg', '.pdf']) */
  allowedExtensions: string[]
  /** Максимальный размер файла в мегабайтах */
  maxSizeMB: number
  /** Текст на кнопке загрузки */
  buttonText?: string
  /** Функция обратного вызова при успешной загрузке */
  onFileSelect: (file: File | null) => void
  /** Плейсхолдер текста */
  placeholder?: string
  /** Функция валидации файла (дополнительная к стандартной) */
  customValidator?: (file: File) => string | null
  /** Можно ли загружать несколько файлов */
  multiple?: boolean
  /** ID для тестирования */
  testId?: string
  /** Дополнительные классы для контейнера */
  className?: string
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  acceptType,
  allowedExtensions,
  maxSizeMB,
  buttonText = 'Выберите файл',
  onFileSelect,
  placeholder = 'Перетащите файл сюда или нажмите для выбора',
  customValidator,
  multiple = false,
  testId = 'file-uploader',
  className = ''
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | File[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  // Формируем accept строку для input
  const getAcceptString = useCallback(() => {
    return allowedExtensions.join(',')
  }, [allowedExtensions])

  // Валидация файла
  const validateFile = useCallback((file: File): string | null => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    const isValidExtension = allowedExtensions.some(ext => 
      ext.toLowerCase() === fileExtension
    )

    if (!isValidExtension) {
      return `Недопустимое расширение файла. Допустимые: ${allowedExtensions.join(', ')}`
    }

    const fileSizeMB = file.size / (1024 * 1024)
    if (fileSizeMB > maxSizeMB) {
      return `Файл слишком большой. Максимальный размер: ${maxSizeMB}MB`
    }

    if (customValidator) {
      return customValidator(file)
    }

    return null
  }, [allowedExtensions, maxSizeMB, customValidator])

  // Обработчик выбора файла через input
  const handleFileSelect = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) {
      onFileSelect(null)
      return
    }

    const selectedFiles = multiple ? Array.from(files) : files[0]
    
    if (multiple) {
      const filesArray = selectedFiles as File[]
      const errors: string[] = []
      
      filesArray.forEach(file => {
        const validationError = validateFile(file)
        if (validationError) {
          errors.push(`${file.name}: ${validationError}`)
        }
      })

      if (errors.length > 0) {
        setError(errors.join('\n'))
        onFileSelect(null)
        return
      }

      if (acceptType === 'image' && filesArray[0]) {
        const reader = new FileReader()
        reader.onload = (e) => {
          setPreview(e.target?.result as string)
        }
        reader.readAsDataURL(filesArray[0])
      }
      
      setSelectedFile(filesArray)
      onFileSelect(filesArray[0] || null)
    } else {
      const file = selectedFiles as File
      const validationError = validateFile(file)
      
      if (validationError) {
        setError(validationError)
        onFileSelect(null)
        return
      }

      if (acceptType === 'image') {
        const reader = new FileReader()
        reader.onload = (e) => {
          setPreview(e.target?.result as string)
        }
        reader.readAsDataURL(file)
      } else {
        setPreview(null)
      }

      setSelectedFile(file)
      setError(null)
      onFileSelect(file)
    }
  }, [acceptType, multiple, onFileSelect, validateFile])

  // Обработчик drag and drop
  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    
    const files = event.dataTransfer.files
    if (!files || files.length === 0) return

    const dataTransfer = new DataTransfer()
    const validFiles: File[] = []
    
    Array.from(files).forEach(file => {
      const validationError = validateFile(file)
      if (!validationError) {
        validFiles.push(file)
        dataTransfer.items.add(file)
      } else {
        setError(validationError)
      }
    })

    if (validFiles.length > 0 && fileInputRef.current) {
      fileInputRef.current.files = dataTransfer.files
      
      if (multiple) {
        setSelectedFile(validFiles)
        onFileSelect(validFiles[0] || null)
      } else {
        const file = validFiles[0]
        setSelectedFile(file || null)
        onFileSelect(file || null)
        
        if (acceptType === 'image' && file) {
          const reader = new FileReader()
          reader.onload = (e) => {
            setPreview(e.target?.result as string)
          }
          reader.readAsDataURL(file)
        }
      }
      
      setError(null)
    }
  }, [acceptType, multiple, onFileSelect, validateFile])

  // Обработчик клика по кнопке
  const handleButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  // Очистка выбранного файла
  const handleClear = useCallback(() => {
    setSelectedFile(null)
    setPreview(null)
    setError(null)
    onFileSelect(null)
    
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [onFileSelect])

  // Форматирование размера файла
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }, [])

  // Получение иконки для типа файла
  const getFileIcon = useCallback(() => {
    switch (acceptType) {
      case 'image':
        return '🖼️'
      case 'document':
        return '📄'
      case 'video':
        return '🎬'
      case 'audio':
        return '🎵'
      default:
        return '📎'
    }
  }, [acceptType])

  // Рендер информации о выбранном файле
  const renderFileInfo = useCallback(() => {
    if (!selectedFile) return null

    if (multiple && Array.isArray(selectedFile)) {
      return (
        <div className={cls.filesList}>
          {selectedFile.map((file, index) => (
            <div className={cls.fileItem} key={`${file.name}-${index}`}>
              <span>{getFileIcon()}</span>
              <div>
                <div className={cls.fileName}>{file.name}</div>
                <div className={cls.fileSize}>{formatFileSize(file.size)}</div>
              </div>
            </div>
          ))}
        </div>
      )
    }

    const file = selectedFile as File
    return (
      <div className={cls.fileInfo}>
        {preview && acceptType === 'image' ? (
          <img className={cls.imagePreview} src={preview} alt="Превью" />
        ) : (
          <div className={cls.fileIcon}>{getFileIcon()}</div>
        )}
        <div>
          <div className={cls.fileName}>{file.name}</div>
          <div className={cls.fileSize}>{formatFileSize(file.size)}</div>
          <div className={cls.fileType}>{file.type || 'Неизвестный тип'}</div>
        </div>
      </div>
    )
  }, [selectedFile, preview, acceptType, multiple, getFileIcon, formatFileSize])

  return (
    <div className={`${cls.wrapper} ${className}`} data-testid={testId}>
      <input
        ref={fileInputRef}
        type="file"
        accept={getAcceptString()}
        onChange={handleFileSelect}
        multiple={multiple}
        style={{ display: 'none' }}
      />
      
      <div 
        className={`${cls.dropZone} ${isDragging ? cls.dragging : ''} ${error ? cls.error : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        {!selectedFile ? (
          <>
            <div className={cls.uploadIcon}>📤</div>
            <p className={cls.placeholder}>{placeholder}</p>
            <small className={cls.hint}>
              Максимальный размер: {maxSizeMB}MB
              <br />
              Допустимые форматы: {allowedExtensions.join(', ')}
            </small>
          </>
        ) : (
          renderFileInfo()
        )}
      </div>

      {error && (
        <div className={cls.errorMessage}>
          <span className={cls.errorIcon}>⚠️</span>
          {error}
        </div>
      )}

      <div className={cls.buttonsContainer}>
        <Button
        variant="primary"
        size="medium"
        onClick={handleButtonClick}
        fullWidth
      >
        {buttonText}
      </Button>
        
        {selectedFile && (
          <Button
          variant="secondary"
          size="medium"
          onClick={handleClear}
          fullWidth
        >
          Очистить
        </Button>
        )}
      </div>
    </div>
  )
}