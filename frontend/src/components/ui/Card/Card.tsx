import React from 'react'
import styles from './Card.module.css'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'elevated' | 'outlined' | 'filled'
  padding?: 'none' | 'small' | 'medium' | 'large'
  fullWidth?: boolean
}

const Card: React.FC<CardProps> = ({
  children,
  variant = 'elevated',
  padding = 'medium',
  fullWidth = false,
  className = '',
  ...props
}) => {
  const cardClasses = [
    styles.card,
    styles[`variant-${variant}`],
    styles[`padding-${padding}`],
    fullWidth ? styles.fullWidth : '',
    className
  ].filter(Boolean).join(' ')

  return (
    <div className={cardClasses} {...props}>
      {children}
    </div>
  )
}

export default Card