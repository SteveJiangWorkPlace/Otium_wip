import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../../store/useAuthStore';
import Sidebar from '../Sidebar/Sidebar';
import styles from './AppLayout.module.css';

export interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeMenu, setActiveMenu] = useState('home');
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);

  // 根据当前路径设置活动菜单
  useEffect(() => {
    const path = location.pathname;
    if (path === '/' || path.includes('correction')) {
      setActiveMenu('correction');
    } else if (path.includes('translation')) {
      setActiveMenu('translation');
    } else if (path.includes('ai-detection')) {
      setActiveMenu('ai-detection');
    } else if (path.includes('modification')) {
      setActiveMenu('modification');
    } else if (path === '/admin') {
      setActiveMenu('admin');
    }
  }, [location.pathname]);

  const handleMenuSelect = useCallback(
    (menu: string) => {
      setActiveMenu(menu);
      switch (menu) {
        case 'correction':
          navigate('/correction');
          break;
        case 'translation':
          navigate('/translation');
          break;
        case 'ai-detection':
          navigate('/ai-detection');
          break;
        case 'modification':
          navigate('/modification');
          break;
        case 'admin':
          navigate('/admin');
          break;
      }
    },
    [navigate]
  );

  // 获取用户是否为管理员
  const isAdmin = useAuthStore((state) => state.isAdmin);

  // 键盘导航处理
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // 检查是否按下了上下箭头键
      if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        event.preventDefault(); // 防止页面滚动

        // 定义菜单项顺序（与Sidebar中的顺序一致）
        const menuOrder = ['correction', 'translation', 'ai-detection', 'modification', 'admin'];

        // 过滤可见的菜单项（管理员权限检查）
        const visibleMenus = menuOrder.filter((menu) => {
          if (menu === 'admin') {
            return isAdmin;
          }
          return true;
        });

        // 查找当前活动菜单在列表中的索引
        const currentIndex = visibleMenus.indexOf(activeMenu);
        if (currentIndex === -1) return;

        let newIndex;
        if (event.key === 'ArrowUp') {
          // 向上：移动到上一个菜单项，如果是第一个则循环到最后
          newIndex = currentIndex > 0 ? currentIndex - 1 : visibleMenus.length - 1;
        } else {
          // 向下：移动到下一个菜单项，如果是最后一个则循环到第一个
          newIndex = currentIndex < visibleMenus.length - 1 ? currentIndex + 1 : 0;
        }

        const nextMenu = visibleMenus[newIndex];
        if (nextMenu) {
          handleMenuSelect(nextMenu);
        }
      }
    };

    // 添加键盘事件监听
    window.addEventListener('keydown', handleKeyDown);

    // 清理函数
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [activeMenu, navigate, isAdmin, handleMenuSelect]); // 依赖项：activeMenu、navigate、isAdmin和handleMenuSelect

  const handleSidebarToggle = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={styles.appLayout}>
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        activeMenu={activeMenu}
        onMenuSelect={handleMenuSelect}
        onToggle={handleSidebarToggle}
        onLogout={handleLogout}
      />
      <main
        className={`${styles.content} ${
          isSidebarCollapsed ? styles.withCollapsedSidebar : styles.withSidebar
        }`}
      >
        {children}
      </main>
    </div>
  );
};

export default AppLayout;
