import React, { useState, useEffect } from 'react';
import { Table } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { apiClient } from '../api/client';
import { UserInfo } from '../types';
import { Button, Card, Input, Modal, Form, FormItem, Icon } from '../components/ui';

const Admin: React.FC = () => {
  const navigate = useNavigate();
  const { isAdmin } = useAuthStore();
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<UserInfo | null>(null);
  // 表单状态
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    daily_translation_limit: 3,
    daily_ai_detection_limit: 3,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!isAdmin) {
      navigate('/admin/login');
    } else {
      fetchUsers();
    }
  }, [isAdmin, navigate]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getAllUsers();
      setUsers(response.users);
    } catch (error) {
      alert('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (user: UserInfo) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '',
      daily_translation_limit: user.daily_translation_limit,
      daily_ai_detection_limit: user.daily_ai_detection_limit,
    });
    setFormErrors({});
    setModalVisible(true);
  };

  const handleAdd = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      daily_translation_limit: 3,
      daily_ai_detection_limit: 3,
    });
    setFormErrors({});
    setModalVisible(true);
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.username.trim()) {
      errors.username = '请输入用户名';
    }

    if (!editingUser && !formData.password.trim()) {
      errors.password = '请输入密码';
    }

    // 验证每日限制字段
    if (formData.daily_translation_limit <= 0) {
      errors.daily_translation_limit = '每日翻译限制必须大于0';
    }

    if (formData.daily_ai_detection_limit <= 0) {
      errors.daily_ai_detection_limit = '每日AI检测限制必须大于0';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      const data = {
        username: formData.username,
        password: formData.password || undefined,
        daily_translation_limit: formData.daily_translation_limit,
        daily_ai_detection_limit: formData.daily_ai_detection_limit,
      };

      if (editingUser) {
        await apiClient.updateUser(data);
        // 成功时不显示提醒
      } else {
        await apiClient.addUser(data);
        // 成功时不显示提醒
      }

      setModalVisible(false);
      fetchUsers();
    } catch (error) {
      alert('操作失败，请稍后重试');
    }
  };

  const handleFormChange = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    // 清除该字段的错误
    if (formErrors[field]) {
      setFormErrors((prev) => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => (
        <span style={{ color: value ? '#52c41a' : '#ff4d4f' }}>{value ? '激活' : '禁用'}</span>
      ),
    },
    {
      title: '今日翻译',
      key: 'daily_translation',
      render: (_: any, record: UserInfo) => (
        <span>
          {record.daily_translation_used}/{record.daily_translation_limit}
        </span>
      ),
    },
    {
      title: '今日AI检测',
      key: 'daily_ai_detection',
      render: (_: any, record: UserInfo) => (
        <span>
          {record.daily_ai_detection_used}/{record.daily_ai_detection_limit}
        </span>
      ),
    },
    {
      title: '管理员',
      dataIndex: 'is_admin',
      key: 'is_admin',
      render: (value: boolean) => <span>{value ? '是' : '否'}</span>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: UserInfo) => (
        <Button variant="ghost" size="small" onClick={() => handleEdit(record)}>
          编辑
        </Button>
      ),
    },
  ];

  // 由于Table和DatePicker是复杂组件，暂时保留Ant Design版本
  // 但通过CSS覆盖使其样式匹配设计系统

  return (
    <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
      <Card variant="elevated" padding="medium">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 'var(--spacing-4)',
          }}
        >
          <h3
            style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 'var(--font-weight-semibold)',
              color: 'var(--color-text-primary)',
              margin: 0,
            }}
          >
            用户列表
          </h3>
          <Button variant="primary" onClick={handleAdd} icon={<Icon name="add" size="sm" />}>
            添加用户
          </Button>
        </div>
        <Table columns={columns} dataSource={users} rowKey="username" loading={loading} />
      </Card>

      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={modalVisible}
        onClose={() => setModalVisible(false)}
        onConfirm={handleSubmit}
        confirmText={editingUser ? '更新' : '添加'}
        cancelText="取消"
      >
        <Form layout="vertical">
          <FormItem label="用户名" required error={formErrors.username}>
            <Input
              name="username"
              value={formData.username}
              onChange={(e) => handleFormChange('username', e.target.value)}
              disabled={!!editingUser}
              placeholder="请输入用户名"
            />
          </FormItem>

          <FormItem
            label="密码"
            required={!editingUser}
            help={editingUser ? '留空表示不修改' : ''}
            error={formErrors.password}
          >
            <Input
              type="password"
              name="password"
              value={formData.password}
              onChange={(e) => handleFormChange('password', e.target.value)}
              placeholder={editingUser ? '留空表示不修改' : '请输入密码'}
            />
          </FormItem>

          <FormItem label="每日翻译限制" required error={formErrors.daily_translation_limit}>
            <Input
              type="number"
              name="daily_translation_limit"
              value={formData.daily_translation_limit}
              onChange={(e) =>
                handleFormChange('daily_translation_limit', parseInt(e.target.value) || 0)
              }
              placeholder="请输入每日翻译限制"
              min="1"
            />
          </FormItem>

          <FormItem label="每日AI检测限制" required error={formErrors.daily_ai_detection_limit}>
            <Input
              type="number"
              name="daily_ai_detection_limit"
              value={formData.daily_ai_detection_limit}
              onChange={(e) =>
                handleFormChange('daily_ai_detection_limit', parseInt(e.target.value) || 0)
              }
              placeholder="请输入每日AI检测限制"
              min="1"
            />
          </FormItem>
        </Form>
      </Modal>
    </div>
  );
};

export default Admin;
