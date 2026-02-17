import React, { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '../../../store/useAuthStore';
import styles from './UserInfoIcon.module.css';

const UserInfoIcon: React.FC = () => {
  const { userInfo } = useAuthStore();
  const [isPopupVisible, setIsPopupVisible] = useState(false);
  const iconRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭弹出框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (iconRef.current && !iconRef.current.contains(event.target as Node)) {
        setIsPopupVisible(false);
      }
    };

    if (isPopupVisible) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isPopupVisible]);

  if (!userInfo) {
    return null;
  }

  // 获取用户名的前两个字母并大写
  const getInitials = () => {
    if (!userInfo.username) return 'U';
    const initials = userInfo.username.slice(0, 2).toUpperCase();
    return initials;
  };

  const handleIconClick = () => {
    setIsPopupVisible(!isPopupVisible);
  };

  return (
    <div className={styles.userInfoIconContainer} ref={iconRef}>
      <button
        className={styles.userIconButton}
        onClick={handleIconClick}
        aria-label="用户信息"
        title="点击查看用户信息"
      >
        <span className={styles.userInitials}>{getInitials()}</span>
      </button>

      {isPopupVisible && (
        <div className={styles.userInfoPopup}>
          <div className={styles.popupHeader}>
            <span className={styles.popupTitle}>用户信息</span>
          </div>
          <div className={styles.popupContent}>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>用户名:</span>
              <span className={styles.infoValue}>{userInfo.username}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>角色:</span>
              <span className={styles.infoValue}>{userInfo.is_admin ? '管理员' : '普通用户'}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>今日翻译次数:</span>
              <span className={styles.infoValue}>
                {userInfo.daily_translation_used || 0}/{userInfo.daily_translation_limit || 0}
              </span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>今日AI检测次数:</span>
              <span className={styles.infoValue}>
                {userInfo.daily_ai_detection_used || 0}/{userInfo.daily_ai_detection_limit || 0}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserInfoIcon;
