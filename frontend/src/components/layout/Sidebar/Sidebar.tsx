import React, { useState } from 'react'
import { Icon } from '../../ui'
import { useAuthStore } from '../../../store/useAuthStore'
import { useApiKeys } from '../../../hooks/useApiKeys'
import styles from './Sidebar.module.css'

export interface SidebarProps {
  isCollapsed: boolean
  activeMenu: string
  onMenuSelect: (menu: string) => void
  onToggle: () => void
  onLogout: () => void
}

const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  activeMenu,
  onMenuSelect,
  onToggle,
  onLogout
}) => {
  const isAdmin = useAuthStore((state) => state.isAdmin)
  const userInfo = useAuthStore((state) => state.userInfo)
  const { apiKeys, updateApiKey } = useApiKeys()
  const [showApiKeys, setShowApiKeys] = useState(false)

  // 处理API密钥输入变化并立即保存
  const handleApiKeyChange = (key: 'geminiApiKey' | 'gptzeroApiKey', value: string) => {
    console.log('Sidebar - API密钥输入变化:', { key, valueLength: value.length, valuePreview: value.substring(0, Math.min(5, value.length)) + '...' })
    const success = updateApiKey(key, value)
    console.log('Sidebar - updateApiKey结果:', success ? '成功' : '失败')
  }

  // 菜单项定义 - 适配Otium项目
  const menuItems = [
    {
      id: 'correction',
      label: '智能纠错',
      icon: '' as const,
      visible: true
    },
    {
      id: 'translation',
      label: '文本翻译',
      icon: '' as const,
      visible: true
    },
    {
      id: 'ai-detection',
      label: 'AI率检测',
      icon: '' as const,
      visible: true
    },
    {
      id: 'modification',
      label: '文本修改',
      icon: '' as const,
      visible: true
    },
    {
      id: 'admin',
      label: '管理员',
      icon: '' as const,
      visible: isAdmin
    }
  ]

  // 过滤可见的菜单项
  const visibleMenuItems = menuItems.filter(item => item.visible)

  return (
    <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}>
      <div className={styles.header}>
        {!isCollapsed && (
          <div className={styles.logo}>
            <img
              src="/logopic.svg"
              alt="Otium"
              className={styles.logoImage}
            />
            <div className={styles.logoTexts}>
              <span className={styles.logoText}>Otium</span>
            </div>
          </div>
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
            const isActive = activeMenu === item.id
            return (
              <li key={item.id} className={styles.menuItem}>
                <button
                  className={`${styles.menuButton} ${isActive ? styles.active : ''}`}
                  onClick={() => onMenuSelect(item.id)}
                  aria-label={item.label}
                  title={item.label}
                >
                  {item.icon && (
                    <span className={styles.menuIcon}>
                      <Icon
                        name={item.icon}
                        size="md"
                        variant="default"
                      />
                    </span>
                  )}
                  {!isCollapsed && (
                    <span className={styles.menuLabel}>{item.label}</span>
                  )}
                </button>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className={styles.footer}>
        {!isCollapsed && userInfo && (
          <div className={styles.userInfo}>
            <div className={styles.username}>{userInfo.username}</div>
            <div className={styles.userStats}>
              <div className={styles.userStatItem}>
                <span className={styles.userStatLabel}>今日翻译：</span>
                <span className={styles.userStatValue}>
                  {userInfo.daily_translation_used}/{userInfo.daily_translation_limit}
                </span>
              </div>
              <div className={styles.userStatItem}>
                <span className={styles.userStatLabel}>今日AI检测：</span>
                <span className={styles.userStatValue}>
                  {userInfo.daily_ai_detection_used}/{userInfo.daily_ai_detection_limit}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* 简化的底部按钮：API密钥管理和退出登录 */}
        <div className={styles.bottomButtons}>
          <button
            className={styles.apiKeyButton}
            onClick={() => setShowApiKeys(!showApiKeys)}
            title="管理API密钥"
          >
            <span className={styles.apiKeyButtonIcon}>
              <Icon name="lock" size="sm" variant="default" />
            </span>
          </button>

          <button
            className={styles.logoutButton}
            onClick={onLogout}
            title="退出登录"
          >
            <span className={styles.logoutButtonIcon}>
              <Icon name="close" size="sm" variant="default" />
            </span>
          </button>
        </div>

        {/* API密钥管理面板（展开状态） */}
        {showApiKeys && !isCollapsed && (
          <div className={styles.apiKeysPanel}>
            <div className={styles.apiKeyInputGroup}>
              <label className={styles.apiKeyLabel}>
                <span>Gemini API Key</span>
              </label>
              <input
                type="password"
                className={styles.apiKeyInput}
                value={apiKeys.geminiApiKey}
                onChange={(e) => handleApiKeyChange('geminiApiKey', e.target.value)}
                placeholder="输入Google Gemini API密钥"
              />
            </div>

            <div className={styles.apiKeyInputGroup}>
              <label className={styles.apiKeyLabel}>
                <span>GPTZero API Key</span>
              </label>
              <input
                type="password"
                className={styles.apiKeyInput}
                value={apiKeys.gptzeroApiKey}
                onChange={(e) => handleApiKeyChange('gptzeroApiKey', e.target.value)}
                placeholder="输入GPTZero API密钥"
              />
            </div>

            <div className={styles.apiKeysStatus}>
              <div className={styles.apiKeyStatusItem}>
                <span>Gemini API: {apiKeys.geminiApiKey ? '已配置' : '未配置'}</span>
              </div>
              <div className={styles.apiKeyStatusItem}>
                <span>GPTZero API: {apiKeys.gptzeroApiKey ? '已配置' : '未配置'}</span>
              </div>
            </div>
          </div>
        )}

      </div>
    </aside>
  )
}

export default Sidebar