# 数据库迁移指南

## 概述

本指南说明如何将Otium项目从环境变量和JSON文件存储迁移到数据库存储。

## 迁移前准备

### 1. 备份当前数据
```bash
# 备份usage_data.json
cp usage_data.json usage_data.json.backup.$(date +%Y%m%d)

# 记录ALLOWED_USERS环境变量值
echo "ALLOWED_USERS=$ALLOWED_USERS" > allowed_users_backup.txt
```

### 2. 检查当前配置
确保`.env`文件包含以下数据库配置：
```
# 数据库类型：sqlite（开发）或 postgresql（生产）
DATABASE_TYPE=sqlite

# SQLite数据库路径
DATABASE_PATH=./data/otium.db

# PostgreSQL连接字符串（生产环境）
# DATABASE_URL=postgresql://user:password@localhost/otium

# 密码哈希算法
PASSWORD_HASH_ALGORITHM=sha256
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

## 迁移步骤

### 步骤1: 运行迁移脚本
```bash
cd backend
python scripts/migrate_to_database.py
```

迁移脚本会：
1. 备份原始文件
2. 初始化数据库
3. 迁移用户数据
4. 迁移使用数据
5. 验证迁移结果

### 步骤2: 测试迁移结果
```bash
# 运行测试脚本
python scripts/test_migration.py
```

测试脚本会验证：
- 用户认证功能
- 密码哈希
- 使用记录
- 用户管理功能

### 步骤3: 启动服务器测试
```bash
# 启动开发服务器
uvicorn main:app --reload

# 或使用提供的脚本
./start_backend.ps1  # Windows PowerShell
./start_backend.bat  # Windows CMD
```

### 步骤4: 功能验证
1. 访问 `http://localhost:8000/docs` 查看API文档
2. 测试登录功能
3. 测试文本处理功能
4. 测试管理员功能

## 回滚步骤

如果迁移出现问题，可以回滚到原始文件存储：

### 步骤1: 运行回滚脚本
```bash
cd backend
python scripts/rollback_migration.py
```

### 步骤2: 恢复配置
1. 将 `restored_env_vars.txt` 中的 `ALLOWED_USERS` 值设置到环境变量
2. 更新 `main.py`，恢复使用 `UserLimitManager`
3. 重启服务器

## 生产环境部署

### Render平台部署
1. 在Render Dashboard中设置环境变量：
   - `DATABASE_TYPE=postgresql`
   - `DATABASE_URL`（Render会自动提供）
   - `PASSWORD_HASH_ALGORITHM=sha256`

2. 确保Render的PostgreSQL插件已安装

3. 部署后运行迁移：
   ```bash
   # 通过Render的Shell或使用初始化脚本
   python scripts/migrate_to_database.py
   ```

### 其他平台
根据平台文档配置PostgreSQL连接。

## 故障排除

### 常见问题

#### 1. 数据库连接失败
- 检查 `DATABASE_URL` 格式
- 验证数据库服务是否运行
- 检查网络连接和防火墙设置

#### 2. 迁移脚本失败
- 检查日志文件 `migration.log`
- 验证原始数据格式
- 确保有足够的磁盘空间

#### 3. 密码验证失败
- 确保使用相同的哈希算法
- 检查密码是否包含特殊字符
- 验证数据库中的密码哈希

#### 4. 性能问题
- 检查数据库索引
- 优化查询语句
- 考虑使用连接池

### 日志文件
- `migration.log` - 迁移过程日志
- `rollback.log` - 回滚过程日志
- `test_migration.log` - 测试日志

## 新功能

### UserService新增功能
1. **密码哈希** - 使用SHA256存储密码哈希
2. **详细记录** - 记录每次操作的详细信息
3. **用户状态管理** - 启用/禁用用户
4. **使用统计** - 更详细的使用数据分析
5. **数据库备份** - 支持数据导出和备份

### 数据库表结构
```
users
  ├── id (主键)
  ├── username (唯一)
  ├── password_hash (SHA256)
  ├── expiry_date
  ├── max_translations
  ├── is_admin
  ├── is_active
  └── 时间戳字段

user_usage
  ├── id (主键)
  ├── user_id (外键)
  ├── translations_count
  ├── last_translation_at
  └── 时间戳字段

translation_records
  ├── id (主键)
  ├── user_id (外键)
  ├── operation_type
  ├── text_length
  ├── metadata (JSON)
  └── created_at
```

## 维护建议

### 定期备份
```bash
# 导出数据库数据
python scripts/rollback_migration.py
# 这会创建 database_backup_YYYYMMDD_HHMMSS.json 文件
```

### 监控
- 监控数据库连接数
- 监控磁盘空间使用
- 定期检查日志文件

### 升级
- 定期更新数据库依赖
- 测试新版本兼容性
- 备份数据后再进行升级

## 支持

如有问题，请检查：
1. 日志文件中的错误信息
2. 数据库连接配置
3. 环境变量设置
4. 文件权限

如需进一步帮助，请提供：
- 相关日志文件
- 错误信息截图
- 环境配置信息