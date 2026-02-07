import React, { useState, useEffect } from 'react';
import { Table, DatePicker, InputNumber } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { apiClient } from '../api/client';
import { UserInfo } from '../types';
import dayjs from 'dayjs';
import {
  Button,
  Card,
  Input,
  Modal,
  Form,
  FormItem,
  Icon,
} from '../components/ui';

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
    expiry_date: null as dayjs.Dayjs | null,
    max_translations: 1,
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
      expiry_date: dayjs(user.expiry_date),
      max_translations: user.max_translations,
    });
    setFormErrors({});
    setModalVisible(true);
  };

  const handleAdd = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      expiry_date: null,
      max_translations: 1,
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

    if (!formData.expiry_date) {
      errors.expiry_date = '请选择过期日期';
    }

    if (!formData.max_translations || formData.max_translations < 1) {
      errors.max_translations = '请输入有效的最大翻译次数';
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
        expiry_date: formData.expiry_date ? formData.expiry_date.format('YYYY-MM-DD') : '',
        max_translations: formData.max_translations,
      };

      if (editingUser) {
        await apiClient.updateUser(data);
        alert('更新成功');
      } else {
        await apiClient.addUser(data);
        alert('添加成功');
      }

      setModalVisible(false);
      fetchUsers();
    } catch (error) {
      alert('操作失败，请稍后重试');
    }
  };

  const handleFormChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    // 清除该字段的错误
    if (formErrors[field]) {
      setFormErrors(prev => ({
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
      title: '过期日期',
      dataIndex: 'expiry_date',
      key: 'expiry_date',
    },
    {
      title: '已用次数',
      dataIndex: 'used_translations',
      key: 'used_translations',
    },
    {
      title: '总次数',
      dataIndex: 'max_translations',
      key: 'max_translations',
    },
    {
      title: '剩余次数',
      dataIndex: 'remaining_translations',
      key: 'remaining_translations',
      render: (value: number) => (
        <span style={{ color: value <= 5 ? '#ff4d4f' : 'inherit' }}>
          {value}
        </span>
      ),
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
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--spacing-4)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: 'var(--font-weight-semibold)',
            color: 'var(--color-text-primary)',
            margin: 0
          }}>
            用户列表
          </h3>
          <Button
            variant="primary"
            onClick={handleAdd}
            icon={<Icon name="add" size="sm" />}
          >
            添加用户
          </Button>
        </div>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="username"
          loading={loading}
        />
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
          <FormItem
            label="用户名"
            required
            error={formErrors.username}
          >
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

          <FormItem
            label="过期日期"
            required
            error={formErrors.expiry_date}
          >
            <DatePicker
              style={{ width: '100%' }}
              value={formData.expiry_date}
              onChange={(date) => handleFormChange('expiry_date', date)}
            />
          </FormItem>

          <FormItem
            label="最大翻译次数"
            required
            error={formErrors.max_translations}
          >
            <InputNumber
              min={1}
              style={{ width: '100%' }}
              value={formData.max_translations}
              onChange={(value) => handleFormChange('max_translations', value)}
            />
          </FormItem>
        </Form>
      </Modal>
    </div>
  );
};

export default Admin;