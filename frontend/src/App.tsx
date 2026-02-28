import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useAuthStore } from './store/useAuthStore';
import { apiClient } from './api/client';
import { Card, Input, Button, Form, FormItem, Icon, ToastProvider } from './components/ui';
import { debugLog } from './utils/logger';
import './App.css';

const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const Admin = lazy(() => import('./pages/Admin'));
const TextCorrection = lazy(() => import('./pages/TextCorrection'));
const TextTranslation = lazy(() => import('./pages/TextTranslation'));
const AIDetectionPage = lazy(() => import('./pages/AIDetectionPage'));
const TextModification = lazy(() => import('./pages/TextModification'));
const AppLayout = lazy(() => import('./components/layout/AppLayout/AppLayout'));

const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" />;
};

const AdminRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const isAdmin = useAuthStore((state) => state.isAdmin);
  return isAdmin ? children : <Navigate to="/admin/login" />;
};

const App: React.FC = () => {
  // 应用启动时验证token
  useEffect(() => {
    const validateStoredToken = async () => {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('admin_token');
      if (token) {
        try {
          await apiClient.getCurrentUser();
          debugLog('应用启动：token验证成功');
        } catch (error) {
          debugLog('应用启动：token已失效，清除登录状态');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('admin_token');
          localStorage.removeItem('token');
          useAuthStore.getState().logout();
        }
      }
    };

    validateStoredToken();
  }, []);

  return (
    <ToastProvider>
      <Router>
        <Suspense
          fallback={
            <div className="appRouteSkeleton" aria-live="polite" aria-busy="true">
              <div className="appRouteSkeletonSidebar" />
              <div className="appRouteSkeletonMain">
                <div className="appRouteSkeletonLine appRouteSkeletonLineLg" />
                <div className="appRouteSkeletonLine appRouteSkeletonLineMd" />
                <div className="appRouteSkeletonLine appRouteSkeletonLineSm" />
              </div>
            </div>
          }
        >
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ForgotPassword />} />
            <Route path="/" element={<Navigate to="/correction" />} />
            <Route
              path="/correction"
              element={
                <PrivateRoute>
                  <AppLayout>
                    <TextCorrection />
                  </AppLayout>
                </PrivateRoute>
              }
            />
            <Route
              path="/translation"
              element={
                <PrivateRoute>
                  <AppLayout>
                    <TextTranslation />
                  </AppLayout>
                </PrivateRoute>
              }
            />
            <Route
              path="/ai-detection"
              element={
                <PrivateRoute>
                  <AppLayout>
                    <AIDetectionPage />
                  </AppLayout>
                </PrivateRoute>
              }
            />
            <Route
              path="/modification"
              element={
                <PrivateRoute>
                  <AppLayout>
                    <TextModification />
                  </AppLayout>
                </PrivateRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AppLayout>
                    <Admin />
                  </AppLayout>
                </AdminRoute>
              }
            />
            <Route path="/admin/login" element={<AdminLogin />} />
          </Routes>
        </Suspense>
      </Router>
    </ToastProvider>
  );
};

// 管理员登录组件
const AdminLogin: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const setAdminAuth = useAuthStore((state) => state.setAdminAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!password.trim()) {
      setError('请输入管理员密码');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await apiClient.adminLogin({ password });
      if (response.success) {
        setAdminAuth(response.token);
        // 成功时不显示提醒
        navigate('/admin');
      } else {
        setError('密码错误');
      }
    } catch (error) {
      setError('登录失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-background)',
      }}
    >
      <Card variant="elevated" padding="large" style={{ width: 400 }}>
        <h3
          style={{
            textAlign: 'center',
            color: 'var(--color-primary)',
            fontSize: 'var(--font-size-xl)',
            fontWeight: 'var(--font-weight-semibold)',
            margin: '0 0 var(--spacing-6) 0',
          }}
        >
          管理员登录
        </h3>
        <Form onSubmit={handleSubmit}>
          <FormItem label="管理员密码" required error={error}>
            <Input
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (error) setError('');
              }}
              placeholder="请输入管理员密码"
              startIcon={<Icon name="lock" size="sm" />}
            />
          </FormItem>
          <div style={{ marginTop: 'var(--spacing-6)' }}>
            <Button variant="primary" type="submit" loading={loading} fullWidth>
              登录
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default App;
