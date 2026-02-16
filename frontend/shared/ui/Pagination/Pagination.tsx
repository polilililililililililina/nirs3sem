import React from 'react'

import cls from './Pagination.module.css'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
  maxVisiblePages?: number
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  maxVisiblePages = 5
}) => {
  if (totalPages <= 1) return null

  const getPageNumbers = () => {
    const half = Math.floor(maxVisiblePages / 2)
    let start = Math.max(1, currentPage - half)
    const end = Math.min(totalPages, start + maxVisiblePages - 1)

    if (end - start + 1 < maxVisiblePages) {
      start = Math.max(1, end - maxVisiblePages + 1)
    }

    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }

  const pageNumbers = getPageNumbers()

  return (
    <div className={cls.pagination}>
      <button
        className={`${cls.pageButton} ${cls.prevButton}`}
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        ← Назад
      </button>
      
      <div className={cls.pageNumbers}>
        {pageNumbers[0] && pageNumbers[0] > 1 && (
          <>
            <button
              className={`${cls.pageButton} ${currentPage === 1 ? cls.active : ''}`}
              onClick={() => onPageChange(1)}
            >
              1
            </button>
            {pageNumbers[0] > 2 && <span className={cls.dots}>...</span>}
          </>
        )}
        
        {pageNumbers.map(page => (
          <button
            key={page}
            className={`${cls.pageButton} ${currentPage === page ? cls.active : ''}`}
            onClick={() => onPageChange(page)}
          >
            {page}
          </button>
        ))}
        
        {pageNumbers[pageNumbers.length - 1] < totalPages && (
          <>
            {pageNumbers[pageNumbers.length - 1] < totalPages - 1 && (
              <span className={cls.dots}>...</span>
            )}
            <button
              className={`${cls.pageButton} ${currentPage === totalPages ? cls.active : ''}`}
              onClick={() => onPageChange(totalPages)}
            >
              {totalPages}
            </button>
          </>
        )}
      </div>
      
      <button
        className={`${cls.pageButton} ${cls.nextButton}`}
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        Вперед →
      </button>
    </div>
  )
}