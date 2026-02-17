import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import Icon from '../Icon/Icon';
import Button from '../Button/Button';
import styles from './Modal.module.css';

interface ModalProps {
  title?: string;
  open: boolean;
  onClose?: () => void;
  onConfirm?: () => void;
  confirmText?: string;
  cancelText?: string;
  children: React.ReactNode;
  showFooter?: boolean;
  loading?: boolean;
}

const Modal: React.FC<ModalProps> = ({
  title,
  open,
  onClose,
  onConfirm,
  confirmText = '确定',
  cancelText = '取消',
  children,
  showFooter = true,
  loading = false,
}) => {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [open]);

  if (!open) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && onClose) {
      onClose();
    }
  };

  const modalContent = (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.modal}>
        <div className={styles.header}>
          {title && <h3 className={styles.title}>{title}</h3>}
          {onClose && (
            <Button variant="ghost" size="small" onClick={onClose} className={styles.closeButton}>
              <Icon name="close" size="sm" />
            </Button>
          )}
        </div>
        <div className={styles.content}>{children}</div>
        {showFooter && (
          <div className={styles.footer}>
            {onClose && (
              <Button variant="ghost" onClick={onClose} disabled={loading}>
                {cancelText}
              </Button>
            )}
            {onConfirm && (
              <Button
                variant="primary"
                onClick={onConfirm}
                loading={loading}
                style={{ marginLeft: 'var(--spacing-2)' }}
              >
                {confirmText}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default Modal;
export type { ModalProps };
