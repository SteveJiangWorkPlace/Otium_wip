import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Admin from './pages/Admin';
import TextCorrection from './pages/TextCorrection';
import TextTranslation from './pages/TextTranslation';
import AIDetectionPage from './pages/AIDetectionPage';
import TextModification from './pages/TextModification';
import AppLayout from './components/layout/AppLayout/AppLayout';
import { useAuthStore } from './store/useAuthStore';
import { apiClient } from './api/client';
import { Card, Input, Button, Form, FormItem, Icon, ToastProvider } from './components/ui';
import './App.css';

const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" />;
};

const AdminRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const isAdmin = useAuthStore((state) => state.isAdmin);
  return isAdmin ? children : <Navigate to="/admin/login" />;
};

const App: React.FC = () => {
  return (
    <ToastProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
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
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-background)',
    }}>
      <Card variant="elevated" padding="large" style={{ width: 400 }}>
        <h3 style={{
          textAlign: 'center',
          color: 'var(--color-primary)',
          fontSize: 'var(--font-size-xl)',
          fontWeight: 'var(--font-weight-semibold)',
          margin: '0 0 var(--spacing-6) 0'
        }}>
          管理员登录
        </h3>
        <Form onSubmit={handleSubmit}>
          <FormItem
            label="管理员密码"
            required
            error={error}
          >
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
            <Button
              variant="primary"
              type="submit"
              loading={loading}
              fullWidth
            >
              登录
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default App;