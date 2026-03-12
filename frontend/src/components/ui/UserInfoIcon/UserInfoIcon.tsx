import React from 'react';
import { useAuthStore } from '../../../store/useAuthStore';
import styles from './UserInfoIcon.module.css';

const UserInfoIcon: React.FC = () => {
  const { userInfo } = useAuthStore();

  if (!userInfo) {
    return null;
  }

  // 获取用户名的前两个字母并大写
  const getInitials = () => {
    if (!userInfo.username) return 'U';
    const initials = userInfo.username.slice(0, 2).toUpperCase();
    return initials;
  };

  return (
    <div className={styles.userInfoIconContainer}>
      <button className={styles.userIconButton} aria-label="用户信息" title="用户信息">
        <span className={styles.userInitials}>{getInitials()}</span>
      </button>
    </div>
  );
};

export default UserInfoIcon;
