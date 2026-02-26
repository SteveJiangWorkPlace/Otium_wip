import React, { useEffect, useState } from 'react';
import styles from './Toast.module.css';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: () => void;
  isVisible?: boolean;
}

const Toast: React.FC<ToastProps> = ({
  message,
  type = 'info',
  duration = 3000,
  onClose,
  isVisible = true,
}) => {
  const [visible, setVisible] = useState(isVisible);

  useEffect(() => {
    setVisible(isVisible);
  }, [isVisible]);

  useEffect(() => {
    if (duration > 0 && visible) {
      const timer = setTimeout(() => {
        setVisible(false);
        if (onClose) onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, visible, onClose]);

  if (!visible) return null;

  const typeStyles = {
    success: styles.toastSuccess,
    error: styles.toastError,
    info: styles.toastInfo,
    warning: styles.toastWarning,
  };

  const iconMap = {
    success: '+',
    error: 'x',
    info: 'i',
    warning: '!',
  };

  return (
    <div className={`${styles.toast} ${typeStyles[type]}`}>
      <span className={styles.toastIcon}>{iconMap[type]}</span>
      <span className={styles.toastMessage}>{message}</span>
    </div>
  );
};

export default Toast;
