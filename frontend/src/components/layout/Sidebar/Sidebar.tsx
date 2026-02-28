import React from 'react';
import { useAuthStore } from '../../../store/useAuthStore';
import UserInfoIcon from '../../ui/UserInfoIcon/UserInfoIcon';
import styles from './Sidebar.module.css';

export interface SidebarProps {
  isCollapsed: boolean;
  activeMenu: string;
  onMenuSelect: (menu: string) => void;
  onToggle: () => void;
  onLogout: () => void;
}

interface MenuItem {
  id: string;
  label: string;
  visible: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  activeMenu,
  onMenuSelect,
  onToggle,
  onLogout,
}) => {
  const isAdmin = useAuthStore((state) => state.isAdmin);

  // 菜单项定义 - 适配Otium项目
  const menuItems: MenuItem[] = [
    {
      id: 'correction',
      label: '智能纠错',
      visible: true,
    },
    {
      id: 'translation',
      label: '文本翻译',
      visible: true,
    },
    {
      id: 'ai-detection',
      label: 'AI率检测',
      visible: true,
    },
    {
      id: 'modification',
      label: '文本修改',
      visible: true,
    },
    {
      id: 'admin',
      label: '管理员',
      visible: isAdmin,
    },
  ];

  // 过滤可见的菜单项
  const visibleMenuItems = menuItems.filter((item) => item.visible);

  return (
    <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}>
      <div className={styles.header}>
        {!isCollapsed && (
          <>
            <div className={styles.logo}>
              <img src="/logopic.svg" alt="Otium" className={styles.logoImage} />
              <div className={styles.logoTexts}>
                <span className={styles.logoText}>Otium</span>
              </div>
            </div>
            <UserInfoIcon />
          </>
        )}
      </div>

      {/* 侧边栏隐藏/显示按钮 */}
      <button
        className={styles.toggleButton}
        onClick={onToggle}
        aria-label={isCollapsed ? '展开侧边栏' : '折叠侧边栏'}
        title={isCollapsed ? '展开侧边栏' : '折叠侧边栏'}
      >
        {isCollapsed ? '>' : '<'}
      </button>

      <nav className={styles.nav}>
        <ul className={styles.menuList}>
          {visibleMenuItems.map((item) => {
            const isActive = activeMenu === item.id;
            return (
              <li key={item.id} className={styles.menuItem}>
                <button
                  className={`${styles.menuButton} ${isActive ? styles.active : ''}`}
                  onClick={() => onMenuSelect(item.id)}
                  aria-label={item.label}
                  title={item.label}
                >
                  {!isCollapsed && <span className={styles.menuLabel}>{item.label}</span>}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className={styles.footer}>
        {/* 底部按钮：退出登录 */}
        <div className={styles.bottomButtons}>
          <button className={styles.logoutButton} onClick={onLogout} title="退出登录">
            <img src="/logout.svg" alt="退出登录" className={styles.logoutIcon} />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
