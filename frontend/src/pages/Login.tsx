import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';
import { Card, Input, Button, Icon } from '../components';
import { resetAllStores } from '../utils/resetStores';
import styles from './Login.module.css';

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [loginError, setLoginError] = useState('');
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const validateForm = () => {
    let isValid = true;

    if (!username.trim()) {
      setUsernameError('请输入用户名');
      isValid = false;
    } else {
      setUsernameError('');
    }

    if (!password.trim()) {
      setPasswordError('请输入密码');
      isValid = false;
    } else {
      setPasswordError('');
    }

    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    const maxRetries = 4;
    let retryCount = 0;
    let success = false;

    // 错误消息提取函数（复用原有逻辑）
    const extractErrorMessage = (error: unknown): string => {
      if (error instanceof Error) {
        return error.message;
      } else if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        return axiosError.response?.data?.detail || '登录失败，请检查用户名和密码';
      }
      return '登录失败，请检查用户名和密码';
    };

    while (retryCount <= maxRetries && !success) {
      try {
        const response = (await apiClient.login({ username, password })) as any;

        if (response) {
          // 登录成功逻辑（保持不变）
          const userInfo = response.user || response.user_info || { username };
          const token = response.token || response.access_token;

          setAuth(token, userInfo);
          resetAllStores();
          navigate('/');

          setTimeout(() => {
            if (window.location.pathname === '/login') {
              window.location.href = '/';
            }
          }, 1000);

          success = true;
        }
      } catch (error) {
        retryCount++;

        if (retryCount > maxRetries) {
          // 最终失败处理
          let errorMessage = '登录失败，请检查用户名和密码';

          // 检查是否为服务器错误
          if (error && typeof error === 'object') {
            const status = (error as any).response?.status;
            if (status === 503 || status === 502 || status === 504) {
              errorMessage = '服务器正在启动中，请稍后重试（已自动重试多次）';
            } else {
              errorMessage = extractErrorMessage(error);
            }
          }

          setLoginError(errorMessage);
        } else {
          // 固定间隔重试：25, 50, 75, 100秒（总等待时间250秒，约4.2分钟）
          const retryIntervals = [25, 50, 75, 100];
          const waitTime = retryIntervals[retryCount - 1] * 1000;
          console.log(
            `登录失败，${retryIntervals[retryCount - 1]}秒后重试 (${retryCount}/${maxRetries})`
          );
          await new Promise((resolve) => setTimeout(resolve, waitTime));
        }
      }
    }

    setLoading(false);
  };

  return (
    <div className={styles.loginContainer}>
      <Card variant="center" padding="large" className={styles.loginCard}>
        <div className={styles.loginHeader}>
          <div className={styles.headerLeft}>
            <img src="/logopic.svg" alt="Otium" className={styles.logoImage} />
          </div>
          <div className={styles.headerDivider}></div>
          <div className={styles.headerRight}>
            <h1 className={styles.loginTitle}>Otium</h1>
            <p className={styles.loginSubtitle}>拯救拖延症儿童的论文DDL</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className={styles.loginForm}>
          <Input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            error={usernameError}
            placeholder="请输入用户名"
            fullWidth
            disabled={loading}
          />

          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={passwordError}
            placeholder="请输入密码"
            fullWidth
            disabled={loading}
          />

          {loginError && (
            <div className={styles.errorMessage}>
              <Icon name="close" size="sm" variant="error" />
              <span>{loginError}</span>
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            size="large"
            loading={loading}
            fullWidth
            className={styles.loginButton}
          >
            {loading ? '登录中...' : '登录'}
          </Button>

          <div className={styles.authLinks}>
            <Link to="/register" className={styles.authLink}>
              还没有账户？立即注册
            </Link>
            <Link to="/forgot-password" className={styles.authLink}>
              忘记密码？
            </Link>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default Login;
