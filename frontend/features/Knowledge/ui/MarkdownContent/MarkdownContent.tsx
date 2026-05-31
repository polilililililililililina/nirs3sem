import ReactMarkdown from 'react-markdown'

import cls from './MarkdownContent.module.css'

interface MarkdownContentProps {
  content: string
  className?: string
}

export const MarkdownContent = ({ content, className }: MarkdownContentProps) => {
  return (
    <div className={`${cls.markdown} ${className || ''}`}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  )
}
