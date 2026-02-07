import React from 'react'
import styles from './Input.module.css'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  fullWidth?: boolean
  startIcon?: React.ReactNode
  endIcon?: React.ReactNode
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      fullWidth = false,
      startIcon,
      endIcon,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
    const hasError = !!error

    const inputClasses = [
      styles.input,
      hasError ? styles.error : '',
      startIcon ? styles.withStartIcon : '',
      endIcon ? styles.withEndIcon : '',
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
          <label htmlFor={inputId} className={styles.label}>
            {label}
          </label>
        )}

        <div className={styles.inputContainer}>
          {startIcon && (
            <span className={styles.startIcon} aria-hidden="true">
              {startIcon}
            </span>
          )}

          <input
            ref={ref}
            id={inputId}
            className={inputClasses}
            aria-invalid={hasError}
            aria-describedby={
              hasError ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            {...props}
          />

          {endIcon && (
            <span className={styles.endIcon} aria-hidden="true">
              {endIcon}
            </span>
          )}
        </div>

        {hasError && (
          <div id={`${inputId}-error`} className={styles.errorText}>
            {error}
          </div>
        )}

        {!hasError && helperText && (
          <div id={`${inputId}-helper`} className={styles.helperText}>
            {helperText}
          </div>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input