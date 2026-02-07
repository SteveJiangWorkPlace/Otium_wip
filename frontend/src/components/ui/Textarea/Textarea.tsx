import React from 'react'
import styles from './Textarea.module.css'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  fullWidth?: boolean
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
  rows?: number
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      helperText,
      fullWidth = false,
      resize = 'vertical',
      rows = 4,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`
    const hasError = !!error

    const textareaClasses = [
      styles.textarea,
      hasError ? styles.error : '',
      styles[`resize-${resize}`],
      fullWidth ? styles.fullWidth : '',
      className
    ].filter(Boolean).join(' ')

    const wrapperClasses = [
      styles.wrapper,
      fullWidth ? styles.fullWidth : ''
    ].filter(Boolean).join(' ')

    return (
      <div className={wrapperClasses}>
        {label && (
          <label htmlFor={textareaId} className={styles.label}>
            {label}
          </label>
        )}

        <textarea
          ref={ref}
          id={textareaId}
          className={textareaClasses}
          rows={rows}
          aria-invalid={hasError}
          aria-describedby={
            hasError ? `${textareaId}-error` : helperText ? `${textareaId}-helper` : undefined
          }
          {...props}
        />

        {hasError && (
          <div id={`${textareaId}-error`} className={styles.errorText}>
            {error}
          </div>
        )}

        {!hasError && helperText && (
          <div id={`${textareaId}-helper`} className={styles.helperText}>
            {helperText}
          </div>
        )}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'

export default Textarea