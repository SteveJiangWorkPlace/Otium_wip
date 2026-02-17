import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useParams } from 'react-router-dom';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';
import { Card, Input, Button, Icon } from '../components';
import styles from './ForgotPassword.module.css';

const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();

  // 判断当前模式：请求重置链接还是重置密码
  const isResetMode = !!token;

  // 表单状态
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // 加载状态
  const [loading, setLoading] = useState(false);
  const [sendingRequest, setSendingRequest] = useState(false);
  const [verifyingToken, setVerifyingToken] = useState(false);

  // 错误状态
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [formError, setFormError] = useState('');

  // 成功状态
  const [success, setSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // 令牌验证状态
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);

  // 已认证用户重定向
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // 重置模式下验证令牌
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) return;

      setVerifyingToken(true);
      setFormError('');

      try {
        // 前端验证令牌格式（基本格式检查）
        // 后端会在实际重置时进行完整验证
        if (token.length < 10) {
          setTokenValid(false);
          setFormError('无效的重置令牌');
          return;
        }

        // 令牌格式看起来有效
        setTokenValid(true);
      } catch (error) {
        console.error('验证令牌出错:', error);
        setTokenValid(false);
        setFormError('令牌验证失败');
      } finally {
        setVerifyingToken(false);
      }
    };

    if (isResetMode && token) {
      verifyToken();
    }
  }, [isResetMode, token]);

  // 验证邮箱格式
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // 验证密码强度
  const validatePassword = (password: string): boolean => {
    return password.length >= 6;
  };

  // 请求重置链接
  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim()) {
      setEmailError('请输入邮箱地址');
      return;
    }

    if (!validateEmail(email)) {
      setEmailError('请输入有效的邮箱地址');
      return;
    }

    setSendingRequest(true);
    setEmailError('');
    setFormError('');

    try {
      const response = await apiClient.requestPasswordReset(email);
      if (response.success) {
        setSuccess(true);
        setSuccessMessage(`重置链接已发送至 ${email}，请查收邮件并按照说明操作`);
        setEmail('');
      } else {
        setFormError(response.message || '请求重置失败');
      }
    } catch (error: any) {
      console.error('请求密码重置出错:', error);
      let errorMessage = '请求失败，请稍后重试';
      if (error?.message) {
        errorMessage = error.message;
      }
      setFormError(errorMessage);
    } finally {
      setSendingRequest(false);
    }
  };

  // 重置密码
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    // 验证所有字段
    let isValid = true;

    if (!newPassword.trim()) {
      setPasswordError('请输入新密码');
      isValid = false;
    } else if (!validatePassword(newPassword)) {
      setPasswordError('密码至少需要6位');
      isValid = false;
    } else {
      setPasswordError('');
    }

    if (!confirmPassword.trim()) {
      setConfirmPasswordError('请确认新密码');
      isValid = false;
    } else if (newPassword !== confirmPassword) {
      setConfirmPasswordError('两次输入的密码不一致');
      isValid = false;
    } else {
      setConfirmPasswordError('');
    }

    if (!isValid || !token) {
      return;
    }

    setLoading(true);
    setFormError('');

    try {
      const response = await apiClient.resetPassword(token, newPassword);
      if (response.success) {
        setSuccess(true);
        setSuccessMessage('密码重置成功！您可以立即使用新密码登录');
        setNewPassword('');
        setConfirmPassword('');

        // 3秒后跳转到登录页面
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        setFormError(response.message || '密码重置失败');
      }
    } catch (error: any) {
      console.error('重置密码出错:', error);
      let errorMessage = '重置失败，请稍后重试';
      if (error?.message) {
        errorMessage = error.message;
      }
      setFormError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.forgotPasswordContainer}>
      <Card variant="center" padding="large" className={styles.forgotPasswordCard}>
        <div className={styles.forgotPasswordHeader}>
          <div className={styles.headerLeft}>
            <img src="/logopic.svg" alt="Otium" className={styles.logoImage} />
          </div>
          <div className={styles.headerDivider}></div>
          <div className={styles.headerRight}>
            <h1 className={styles.forgotPasswordTitle}>{isResetMode ? '重置密码' : '忘记密码'}</h1>
            <p className={styles.forgotPasswordSubtitle}>
              {isResetMode ? '请设置您的新密码' : '我们将向您的邮箱发送重置链接'}
            </p>
          </div>
        </div>

        {formError && (
          <div className={styles.errorMessage}>
            <Icon name="close" size="sm" variant="error" />
            <span>{formError}</span>
          </div>
        )}

        {success && (
          <div className={styles.successMessage}>
            <Icon name="check" size="sm" variant="success" />
            <span>{successMessage}</span>
          </div>
        )}

        {isResetMode && tokenValid === false && (
          <div className={styles.errorMessage}>
            <Icon name="close" size="sm" variant="error" />
            <span>重置链接无效或已过期，请重新申请</span>
            <div style={{ marginTop: 'var(--spacing-3)' }}>
              <Link to="/forgot-password" className={styles.authLink}>
                重新申请重置链接
              </Link>
            </div>
          </div>
        )}

        {isResetMode && tokenValid === null && verifyingToken && (
          <div className={styles.loadingMessage}>
            <Icon name="info" size="sm" />
            <span>验证重置链接中...</span>
          </div>
        )}

        {/* 请求重置链接模式 */}
        {!isResetMode && !success && (
          <form onSubmit={handleRequestReset} className={styles.forgotPasswordForm}>
            <p className={styles.formDescription}>
              请输入您注册时使用的邮箱地址，我们将发送密码重置链接
            </p>

            <div className={styles.formGroup}>
              <Input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setEmailError('');
                  setFormError('');
                }}
                error={emailError}
                placeholder="请输入邮箱地址"
                fullWidth
                disabled={sendingRequest}
                startIcon={<Icon name="info" size="sm" />}
              />
            </div>

            <div className={styles.buttonGroup}>
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate('/login')}
                disabled={sendingRequest}
              >
                返回登录
              </Button>
              <Button type="submit" variant="primary" loading={sendingRequest}>
                {sendingRequest ? '发送中...' : '发送重置链接'}
              </Button>
            </div>
          </form>
        )}

        {/* 重置密码模式 */}
        {isResetMode && tokenValid === true && !success && (
          <form onSubmit={handleResetPassword} className={styles.resetPasswordForm}>
            <p className={styles.formDescription}>请设置您的新密码</p>

            <div className={styles.formGroup}>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => {
                  setNewPassword(e.target.value);
                  setPasswordError('');
                  setFormError('');
                }}
                error={passwordError}
                placeholder="请输入新密码（至少6位）"
                fullWidth
                disabled={loading}
                startIcon={<Icon name="lock" size="sm" />}
              />
            </div>

            <div className={styles.formGroup}>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  setConfirmPasswordError('');
                  setFormError('');
                }}
                error={confirmPasswordError}
                placeholder="请确认新密码"
                fullWidth
                disabled={loading}
                startIcon={<Icon name="lock" size="sm" />}
              />
            </div>

            <div className={styles.buttonGroup}>
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate('/login')}
                disabled={loading}
              >
                返回登录
              </Button>
              <Button type="submit" variant="primary" loading={loading}>
                {loading ? '重置中...' : '重置密码'}
              </Button>
            </div>
          </form>
        )}

        {/* 成功状态 */}
        {success && (
          <div className={styles.successActions}>
            <Button type="button" variant="primary" onClick={() => navigate('/login')} fullWidth>
              立即登录
            </Button>
          </div>
        )}

        {/* 认证链接 */}
        {!success && !isResetMode && (
          <div className={styles.authLinks}>
            <Link to="/login" className={styles.authLink}>
              返回登录
            </Link>
            <span className={styles.authLinkDivider}>·</span>
            <Link to="/register" className={styles.authLink}>
              注册新账户
            </Link>
          </div>
        )}

        {!success && isResetMode && tokenValid === true && (
          <div className={styles.authLinks}>
            <Link to="/forgot-password" className={styles.authLink}>
              重新申请重置链接
            </Link>
            <span className={styles.authLinkDivider}>·</span>
            <Link to="/login" className={styles.authLink}>
              返回登录
            </Link>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ForgotPassword;
