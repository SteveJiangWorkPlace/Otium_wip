# 数据库迁移快速启动指南

## 5分钟快速迁移

### 步骤1: 安装依赖
```bash
cd backend
pip install sqlalchemy psycopg2-binary alembic
```

### 步骤2: 配置环境
编辑 `.env` 文件，添加：
```
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/otium.db
PASSWORD_HASH_ALGORITHM=sha256
```

### 步骤3: 运行迁移
```bash
python scripts/migrate_to_database.py
```

### 步骤4: 启动服务器
```bash
uvicorn main:app --reload
```

### 步骤5: 验证功能
1. 访问 `http://localhost:8000/docs`
2. 测试登录
3. 测试文本处理

## 命令速查

### 迁移相关
```bash
# 完整迁移
python scripts/migrate_to_database.py

# 测试迁移
python scripts/test_migration.py

# 回滚迁移
python scripts/rollback_migration.py

# 初始化数据库
python -c "from models.database import init_database; init_database()"
```

### 数据库操作
```bash
# 查看SQLite数据库
sqlite3 ./data/otium.db

# 常用SQLite命令
.tables                 # 查看所有表
.schema users           # 查看表结构
SELECT * FROM users;    # 查看用户数据
.exit                   # 退出
```

### 服务器管理
```bash
# 开发模式
uvicorn main:app --reload

# 生产模式
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Windows脚本
.\start_backend.ps1
.\start_backend.bat
```

## 常见问题快速解决

### 1. "数据库连接失败"
```bash
# 检查SQLite文件
ls -la ./data/otium.db

# 修复权限
chmod 755 ./data
chmod 644 ./data/otium.db
```

### 2. "迁移脚本失败"
```bash
# 查看日志
cat migration.log

# 手动备份
cp usage_data.json usage_data.json.backup
```

### 3. "密码验证失败"
```python
# 手动验证密码
from models.database import hash_password, verify_password
print(verify_password("用户密码", "数据库中的哈希值"))
```

### 4. "服务器启动失败"
```bash
# 检查端口占用
netstat -ano | findstr :8000

# 使用其他端口
uvicorn main:app --reload --port 8001
```

## 紧急回滚

如果迁移后出现问题，立即回滚：

```bash
# 1. 停止服务器
# 2. 运行回滚脚本
python scripts/rollback_migration.py

# 3. 恢复main.py中的UserLimitManager
# 编辑main.py，将user_service改回user_manager

# 4. 重启服务器
uvicorn main:app --reload
```

## 验证清单

迁移完成后，验证以下功能：

- [ ] 管理员登录
- [ ] 普通用户登录
- [ ] 文本纠错功能
- [ ] 文本翻译功能
- [ ] AI检测功能
- [ ] 聊天功能
- [ ] 管理员用户管理
- [ ] 使用次数记录

## 下一步

1. **测试生产环境** - 使用PostgreSQL测试
2. **性能优化** - 添加数据库索引
3. **监控设置** - 添加健康检查端点
4. **备份策略** - 设置定期备份

## 获取帮助

- 查看完整文档: `DATABASE_MIGRATION_README.md`
- 检查日志文件: `migration.log`, `rollback.log`
- 查看错误信息: 服务器控制台输出