import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import { useAuthStore } from '../store/useAuthStore'
import { Card, Input, Button, Icon } from '../components'
import { resetAllStores } from '../utils/resetStores'
import styles from './Register.module.css'

const Register: React.FC = () => {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)

  // 注册流程步骤
  const [step, setStep] = useState<'email' | 'verify' | 'complete'>('email')

  // 表单状态
  const [email, setEmail] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // 验证令牌（后端返回）
  const [verificationToken, setVerificationToken] = useState<string>('')

  // 加载状态
  const [loading, setLoading] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)

  // 倒计时状态
  const [countdown, setCountdown] = useState(0)

  // 错误状态
  const [emailError, setEmailError] = useState('')
  const [codeError, setCodeError] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [confirmPasswordError, setConfirmPasswordError] = useState('')
  const [formError, setFormError] = useState('')

  // 用户名验证状态
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(null)
  const [checkingUsername, setCheckingUsername] = useState(false)

  // 邮箱验证状态
  const [checkingEmail, setCheckingEmail] = useState(false)

  // 已认证用户重定向
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  // 倒计时效果
  useEffect(() => {
    let timer: NodeJS.Timeout
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown(countdown - 1), 1000)
    }
    return () => {
      if (timer) clearTimeout(timer)
    }
  }, [countdown])

  // 验证邮箱格式
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  // 验证用户名格式
  const validateUsername = (username: string): boolean => {
    // 用户名格式：字母开头，允许字母、数字、下划线，3-20位
    const usernameRegex = /^[a-zA-Z][a-zA-Z0-9_]{2,19}$/
    return usernameRegex.test(username)
  }

  // 验证密码强度
  const validatePassword = (password: string): boolean => {
    return password.length >= 6
  }

  // 发送验证码
  const handleSendCode = async () => {
    if (!email.trim()) {
      setEmailError('请输入邮箱地址')
      return
    }

    if (!validateEmail(email)) {
      setEmailError('请输入有效的邮箱地址')
      return
    }

    setSendingCode(true)
    setEmailError('')
    setFormError('')

    try {
      // 先检查邮箱是否可用
      setCheckingEmail(true)
      const emailCheck = await apiClient.checkEmail(email)

      if (!emailCheck.available) {
        setEmailError('该邮箱已被注册')
        setCheckingEmail(false)
        setSendingCode(false)
        return
      }

      // 发送验证码
      const response = await apiClient.sendVerificationCode(email)
      if (response.success) {
        setFormError('')
        setCountdown(60) // 60秒倒计时
        setStep('verify')
      } else {
        setFormError(response.message || '发送验证码失败')
      }
    } catch (error: any) {
      console.error('发送验证码出错:', error)
      let errorMessage = '发送验证码失败，请稍后重试'
      if (error?.message) {
        errorMessage = error.message
      }
      setFormError(errorMessage)
    } finally {
      setSendingCode(false)
      setCheckingEmail(false)
    }
  }

  // 验证邮箱验证码
  const handleVerifyCode = async () => {
    if (!verificationCode.trim()) {
      setCodeError('请输入验证码')
      return
    }

    if (verificationCode.length !== 6) {
      setCodeError('验证码应为6位数字')
      return
    }

    setLoading(true)
    setCodeError('')
    setFormError('')

    try {
      const response = await apiClient.verifyEmail(email, verificationCode)
      if (response.success && response.verification_token) {
        setVerificationToken(response.verification_token)
        setStep('complete')
        setFormError('')
      } else {
        setFormError(response.message || '验证码错误或已过期')
      }
    } catch (error: any) {
      console.error('验证验证码出错:', error)
      let errorMessage = '验证失败，请稍后重试'
      if (error?.message) {
        errorMessage = error.message
      }
      setFormError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 检查用户名是否可用
  const handleCheckUsername = async () => {
    if (!username.trim()) {
      setUsernameError('请输入用户名')
      return
    }

    if (!validateUsername(username)) {
      setUsernameError('用户名格式不正确（字母开头，3-20位，允许字母、数字、下划线）')
      return
    }

    setCheckingUsername(true)
    setUsernameError('')
    setUsernameAvailable(null)

    try {
      const response = await apiClient.checkUsername(username)
      if (response.available) {
        setUsernameAvailable(true)
      } else {
        setUsernameAvailable(false)
        setUsernameError(response.message || '用户名已被使用')
      }
    } catch (error: any) {
      console.error('检查用户名出错:', error)
      setUsernameError('检查用户名失败，请稍后重试')
    } finally {
      setCheckingUsername(false)
    }
  }

  // 提交注册
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // 验证所有字段
    let isValid = true

    if (!username.trim()) {
      setUsernameError('请输入用户名')
      isValid = false
    } else if (!validateUsername(username)) {
      setUsernameError('用户名格式不正确（字母开头，3-20位，允许字母、数字、下划线）')
      isValid = false
    } else if (usernameAvailable === false) {
      setUsernameError('用户名已被使用，请更换')
      isValid = false
    } else if (usernameAvailable === null) {
      setUsernameError('请先检查用户名是否可用')
      isValid = false
    } else {
      setUsernameError('')
    }

    if (!password.trim()) {
      setPasswordError('请输入密码')
      isValid = false
    } else if (!validatePassword(password)) {
      setPasswordError('密码至少需要6位')
      isValid = false
    } else {
      setPasswordError('')
    }

    if (!confirmPassword.trim()) {
      setConfirmPasswordError('请确认密码')
      isValid = false
    } else if (password !== confirmPassword) {
      setConfirmPasswordError('两次输入的密码不一致')
      isValid = false
    } else {
      setConfirmPasswordError('')
    }

    if (!isValid) {
      return
    }

    setLoading(true)
    setFormError('')

    try {
      const response = await apiClient.register(username, email, password, verificationToken)
      if (response.success) {
        const userInfo = response.user_info || {
          username,
          daily_translation_limit: 100,
          daily_ai_detection_limit: 50,
          daily_translation_used: 0,
          daily_ai_detection_used: 0,
          is_admin: false,
          is_active: true
        }
        const token = response.token

        setAuth(token, userInfo as any)
        resetAllStores()

        // 显示成功消息并跳转
        setFormError('注册成功！正在跳转到首页...')
        setTimeout(() => {
          navigate('/')
        }, 2000)
      } else {
        setFormError(response.message || '注册失败')
      }
    } catch (error: any) {
      console.error('注册过程出错:', error)
      let errorMessage = '注册失败，请稍后重试'
      if (error?.message) {
        errorMessage = error.message
      }
      setFormError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 返回上一步
  const handleBack = () => {
    if (step === 'verify') {
      setStep('email')
      setVerificationCode('')
      setCountdown(0)
    } else if (step === 'complete') {
      setStep('verify')
    }
    setFormError('')
  }

  return (
    <div className={styles.registerContainer}>
      <Card variant="center" padding="large" className={styles.registerCard}>
        <div className={styles.registerHeader}>
          <div className={styles.headerLeft}>
            <img
              src="/logopic.svg"
              alt="Otium"
              className={styles.logoImage}
            />
          </div>
          <div className={styles.headerDivider}></div>
          <div className={styles.headerRight}>
            <h1 className={styles.registerTitle}>注册新账户</h1>
            <p className={styles.registerSubtitle}>加入Otium，拯救你的论文DDL</p>
          </div>
        </div>

        {/* 步骤指示器 */}
        <div className={styles.stepsContainer}>
          <div className={`${styles.step} ${step === 'email' ? styles.active : ''} ${step === 'verify' || step === 'complete' ? styles.completed : ''}`}>
            <div className={styles.stepNumber}>1</div>
            <div className={styles.stepLabel}>验证邮箱</div>
          </div>
          <div className={styles.stepLine}></div>
          <div className={`${styles.step} ${step === 'verify' ? styles.active : ''} ${step === 'complete' ? styles.completed : ''}`}>
            <div className={styles.stepNumber}>2</div>
            <div className={styles.stepLabel}>输入验证码</div>
          </div>
          <div className={styles.stepLine}></div>
          <div className={`${styles.step} ${step === 'complete' ? styles.active : ''}`}>
            <div className={styles.stepNumber}>3</div>
            <div className={styles.stepLabel}>填写信息</div>
          </div>
        </div>

        {formError && (
          <div className={`${styles.message} ${formError.includes('成功') ? styles.successMessage : styles.errorMessage}`}>
            <Icon name={formError.includes('成功') ? 'check' : 'close'} size="sm" variant={formError.includes('成功') ? 'success' : 'error'} />
            <span>{formError}</span>
          </div>
        )}

        {/* 第一步：输入邮箱 */}
        {step === 'email' && (
          <div className={styles.stepContent}>
            <p className={styles.stepDescription}>请输入您的邮箱地址，我们将发送验证码</p>

            <div className={styles.formGroup}>
              <Input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  setEmailError('')
                  setFormError('')
                }}
                error={emailError}
                placeholder="请输入邮箱地址"
                fullWidth
                disabled={sendingCode || checkingEmail}
                startIcon={<Icon name="info" size="sm" />}
              />
              {checkingEmail && (
                <div className={styles.checkingIndicator}>
                  <span>检查邮箱中...</span>
                </div>
              )}
            </div>

            <div className={styles.buttonGroup}>
              <Button
                type="button"
                variant="primary"
                onClick={handleSendCode}
                loading={sendingCode || checkingEmail}
                fullWidth
              >
                {sendingCode ? '发送中...' : '发送验证码'}
              </Button>
            </div>

            <div className={styles.authLinks}>
              <Link to="/login" className={styles.authLink}>
                已有账户？立即登录
              </Link>
            </div>
          </div>
        )}

        {/* 第二步：验证邮箱验证码 */}
        {step === 'verify' && (
          <div className={styles.stepContent}>
            <p className={styles.stepDescription}>
              验证码已发送至 <strong>{email}</strong>，请查收邮件并输入6位验证码
            </p>

            <div className={styles.formGroup}>
              <Input
                type="text"
                value={verificationCode}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '') // 只允许数字
                  setVerificationCode(value.slice(0, 6))
                  setCodeError('')
                  setFormError('')
                }}
                error={codeError}
                placeholder="请输入6位验证码"
                fullWidth
                disabled={loading}
                startIcon={<Icon name="lock" size="sm" />}
              />
              <div className={styles.codeActions}>
                <span className={styles.countdownText}>
                  {countdown > 0 ? `${countdown}秒后可重新发送` : '未收到验证码？'}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="small"
                  onClick={handleSendCode}
                  disabled={countdown > 0 || sendingCode}
                >
                  {sendingCode ? '发送中...' : '重新发送'}
                </Button>
              </div>
            </div>

            <div className={styles.buttonGroup}>
              <Button
                type="button"
                variant="secondary"
                onClick={handleBack}
                disabled={loading}
              >
                返回
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={handleVerifyCode}
                loading={loading}
              >
                {loading ? '验证中...' : '验证'}
              </Button>
            </div>
          </div>
        )}

        {/* 第三步：填写用户名和密码 */}
        {step === 'complete' && (
          <div className={styles.stepContent}>
            <p className={styles.stepDescription}>请设置您的用户名和密码</p>

            <form onSubmit={handleSubmit} className={styles.completeForm}>
              <div className={styles.formGroup}>
                <Input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    const value = e.target.value
                    setUsername(value)
                    setUsernameError('')
                    setUsernameAvailable(null)
                    setFormError('')
                  }}
                  onBlur={handleCheckUsername}
                  error={usernameError}
                  placeholder="请输入用户名"
                  fullWidth
                  disabled={loading}
                  startIcon={<Icon name="info" size="sm" />}
                />
                {checkingUsername && (
                  <div className={styles.checkingIndicator}>
                    <span>检查用户名中...</span>
                  </div>
                )}
                {usernameAvailable === true && (
                  <div className={styles.availableIndicator}>
                    <Icon name="check" size="sm" variant="success" />
                    <span>用户名可用</span>
                  </div>
                )}
                {usernameAvailable === false && !usernameError && (
                  <div className={styles.unavailableIndicator}>
                    <Icon name="close" size="sm" variant="error" />
                    <span>用户名已被使用</span>
                  </div>
                )}
              </div>

              <div className={styles.formGroup}>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setPasswordError('')
                    setFormError('')
                  }}
                  error={passwordError}
                  placeholder="请输入密码（至少6位）"
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
                    setConfirmPassword(e.target.value)
                    setConfirmPasswordError('')
                    setFormError('')
                  }}
                  error={confirmPasswordError}
                  placeholder="请确认密码"
                  fullWidth
                  disabled={loading}
                  startIcon={<Icon name="lock" size="sm" />}
                />
              </div>

              <div className={styles.buttonGroup}>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleBack}
                  disabled={loading}
                >
                  返回
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  loading={loading}
                >
                  {loading ? '注册中...' : '完成注册'}
                </Button>
              </div>

              <div className={styles.authLinks}>
                <Link to="/login" className={styles.authLink}>
                  已有账户？立即登录
                </Link>
              </div>
            </form>
          </div>
        )}
      </Card>
    </div>
  )
}

export default Register