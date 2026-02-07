import React from 'react'
import styles from './Button.module.css'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'small' | 'medium' | 'large'
export type ButtonIconPosition = 'left' | 'right'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: React.ReactNode
  iconPosition?: ButtonIconPosition
  loading?: boolean
  fullWidth?: boolean
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  icon,
  iconPosition = 'left',
  loading = false,
  fullWidth = false,
  disabled,
  className = '',
  ...props
}) => {
  const buttonClasses = [
    styles.button,
    styles[`variant-${variant}`],
    styles[`size-${size}`],
    loading ? styles.loading : '',
    fullWidth ? styles.fullWidth : '',
    className
  ].filter(Boolean).join(' ')

  const isDisabled = disabled || loading

  return (
    <button
      className={buttonClasses}
      disabled={isDisabled}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <span className={styles.loader} aria-hidden="true">
          <div className={styles.spinner} />
        </span>
      )}

      {!loading && icon && iconPosition === 'left' && (
        <span className={styles.iconLeft}>{icon}</span>
      )}

      <span className={styles.content}>{children}</span>

      {!loading && icon && iconPosition === 'right' && (
        <span className={styles.iconRight}>{icon}</span>
      )}
    </button>
  )
}

export default Button