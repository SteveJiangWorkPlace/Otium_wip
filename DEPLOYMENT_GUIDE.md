# Otium 部署指南 - Render & Netlify

本文档详细说明如何将 Otium 应用部署到 Render（后端 + PostgreSQL）和 Netlify（前端）。

## 部署架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Netlify      │────▶│    Render       │────▶│   PostgreSQL    │
│   (前端 React)  │     │  (后端 FastAPI) │     │    (数据库)     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 第一部分：Render 后端部署

### 1.1 准备工作

1. **注册 Render 账号**：访问 [render.com](https://render.com) 注册
2. **连接 GitHub**：在 Render 控制台连接你的 GitHub 账号
3. **准备 API 密钥**：
   - **Gemini API 密钥**：[Google AI Studio](https://makersuite.google.com/app/apikey)
   - **GPTZero API 密钥**：[GPTZero.me](https://gptzero.me/)

### 1.2 部署步骤

#### 方法 A：使用 Blueprint（推荐）

1. 在 GitHub 上确保以下文件存在：
   - `render.yaml` - Render 蓝图配置
   - `Dockerfile` - 容器配置
   - `backend/requirements.txt` - Python 依赖

2. 在 Render 控制台：
   - 点击 "New +" → "Blueprint"
   - 选择你的 GitHub 仓库
   - Render 会自动检测 `render.yaml` 文件

3. 点击 "Apply" 开始部署

#### 方法 B：手动创建服务

1. **创建 PostgreSQL 数据库**：
   - 点击 "New +" → "PostgreSQL"
   - 名称：`otium-database`
   - 数据库名称：`otium`
   - 用户：`otium_admin`
   - 地区：选择离你最近的（如 Oregon）
   - Plan：免费版（或根据需求选择）
   - 点击 "Create Database"

2. **创建 Web 服务**：
   - 点击 "New +" → "Web Service"
   - 选择你的 GitHub 仓库
   - 名称：`otium-backend`
   - 地区：与数据库相同
   - Branch：`main`
   - Root Directory：留空（使用根目录）
   - Runtime：`Python 3`
   - Build Command：`pip install -r backend/requirements.txt`
   - Start Command：`gunicorn --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120 main:app`
   - Plan：免费版（或根据需求选择）
   - 点击 "Advanced" → 添加环境变量（见下文）
   - 点击 "Create Web Service"

### 1.3 Render 环境变量配置

在 Render Dashboard → 你的服务 → "Environment" 标签页中添加以下变量：

#### 必需变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DATABASE_TYPE` | `postgresql` | 数据库类型 |
| `ENVIRONMENT` | `production` | 环境类型 |
| `DEBUG` | `false` | 关闭调试模式 |
| `CORS_ORIGINS` | `https://your-netlify-app.netlify.app,http://localhost:3000` | CORS 允许的源 |
| `ENABLE_HTTPS_REDIRECT` | `true` | 启用 HTTPS 重定向 |

#### API 密钥（必须手动设置）：

| 变量名 | 获取方式 | 说明 |
|--------|----------|------|
| `GEMINI_API_KEY` | Google AI Studio | Gemini API 密钥 |
| `GPTZERO_API_KEY` | GPTZero.me | GPTZero API 密钥 |

#### 安全相关（建议生成）：

| 变量名 | 建议值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | 自动生成 | JWT 签名密钥 |
| `ADMIN_PASSWORD` | 自动生成 | 管理员密码 |

**生成 SECRET_KEY 的方法**：
```bash
# Linux/Mac
openssl rand -hex 32

# Windows (PowerShell)
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

#### 数据库变量（自动设置）：
- `DATABASE_URL`：Render 会自动从 PostgreSQL 服务获取

### 1.4 数据库初始化

部署完成后，需要初始化数据库：

1. 获取 Render 数据库的 **外部连接字符串**：
   - 进入 `otium-database` 服务
   - 点击 "Connect" → "External Connection"
   - 复制连接字符串

2. 运行数据库迁移：
   ```bash
   # 本地执行（需要安装 psql）
   psql "你的连接字符串"
   # 在 psql 中执行：
   \i backend/models/database.py 中的 SQL 语句
   ```

   或者通过 Python 脚本：
   ```bash
   # 在本地设置 DATABASE_URL 环境变量后运行
   cd backend
   python -c "
   import sys
   sys.path.insert(0, '.')
   from models.database import init_database
   init_database()
   print('Database initialized')
   "
   ```

### 1.5 验证后端部署

1. **健康检查**：
   ```
   GET https://your-otium-backend.onrender.com/api/health
   ```
   应返回：`{"status": "healthy", ...}`

2. **API 测试**：
   ```
   POST https://your-otium-backend.onrender.com/api/login
   Content-Type: application/json

   {
     "username": "admin",
     "password": "你的ADMIN_PASSWORD"
   }
   ```
   应返回 JWT 令牌。

## 第二部分：Netlify 前端部署

### 2.1 准备工作

1. **注册 Netlify 账号**：访问 [netlify.com](https://netlify.com)
2. **连接 GitHub**：在 Netlify 控制台连接 GitHub 账号

### 2.2 部署步骤

1. **导入仓库**：
   - 点击 "Add new site" → "Import an existing project"
   - 选择 "GitHub"
   - 选择你的 Otium 仓库

2. **配置构建设置**：
   - Build command: `npm run build`
   - Publish directory: `frontend/build`
   - Base directory: `.` (根目录)

3. **环境变量设置**：
   - Site settings → Build & deploy → Environment → Environment variables
   - 添加：`REACT_APP_API_BASE_URL` = `https://your-otium-backend.onrender.com`

4. **点击 "Deploy site"**

### 2.3 Netlify 环境变量

在 Netlify Dashboard → Site settings → Build & deploy → Environment variables：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `REACT_APP_API_BASE_URL` | `https://your-otium-backend.onrender.com` | 后端 API 地址 |
| `NODE_VERSION` | `18` | Node.js 版本 |

### 2.4 自定义域名（可选）

1. 在 Netlify Dashboard → Site settings → Domain management
2. 点击 "Add custom domain"
3. 输入你的域名
4. 按照提示配置 DNS 记录

## 第三部分：环境变量详细说明

### 3.1 后端环境变量（Render）

```env
# ==================== 应用配置 ====================
ENVIRONMENT=production          # 环境：production, development
DEBUG=false                     # 生产环境关闭调试
APP_NAME=Otium                  # 应用名称
APP_VERSION=1.0.0              # 应用版本

# ==================== 服务器配置 ====================
HOST=0.0.0.0                   # 监听所有地址
# PORT 由 Render 自动设置
CORS_ORIGINS=https://your-otium-app.netlify.app,http://localhost:3000

# ==================== JWT 认证配置 ====================
SECRET_KEY=你的安全密钥         # 用于 JWT 签名
ALGORITHM=HS256                # JWT 算法
ACCESS_TOKEN_EXPIRE_MINUTES=30 # 普通令牌过期时间
ADMIN_TOKEN_EXPIRE_MINUTES=1440 # 管理员令牌过期时间（24小时）

# ==================== API 密钥配置 ====================
GEMINI_API_KEY=你的_Gemini_API密钥
GPTZERO_API_KEY=你的_GPTZero_API密钥

# ==================== 数据库配置 ====================
DATABASE_TYPE=postgresql       # 数据库类型
# DATABASE_URL 由 Render 自动设置
PASSWORD_HASH_ALGORITHM=sha256 # 密码哈希算法

# ==================== 管理员配置 ====================
ADMIN_USERNAME=admin           # 管理员用户名
ADMIN_PASSWORD=安全密码        # 管理员密码

# ==================== 速率限制配置 ====================
RATE_LIMIT_PER_MINUTE=60       # 每分钟请求限制
DAILY_TEXT_LIMIT=1000          # 每日文本处理限制

# ==================== 日志配置 ====================
LOG_LEVEL=INFO                 # 日志级别
LOG_TO_CONSOLE=true            # 输出到控制台

# ==================== 安全配置 ====================
ENABLE_HTTPS_REDIRECT=true     # 启用 HTTPS 重定向

# ==================== 功能开关 ====================
ENABLE_AI_DETECTION=true       # 启用 AI 检测
ENABLE_TEXT_REFINEMENT=true    # 启用文本润色
ENABLE_TRANSLATION_DIRECTIVES=true # 启用翻译指令
```

### 3.2 前端环境变量（Netlify）

```env
REACT_APP_API_BASE_URL=https://your-otium-backend.onrender.com
# 注意：这是最重要的变量，必须正确设置后端 URL
```

## 第四部分：故障排除

### 4.1 常见问题

#### 问题1：后端无法连接数据库
**症状**：`sqlalchemy.exc.OperationalError` 或类似错误
**解决**：
1. 检查 `DATABASE_URL` 环境变量是否正确
2. 确认 PostgreSQL 服务正在运行
3. 检查防火墙设置（Render 数据库默认只允许 Render 内部访问）

#### 问题2：CORS 错误
**症状**：前端控制台显示 CORS 错误
**解决**：
1. 检查 `CORS_ORIGINS` 环境变量
2. 确保包含前端 URL（包括 http/https）
3. 重启后端服务

#### 问题3：API 密钥错误
**症状**：Gemini 或 GPTZero API 返回错误
**解决**：
1. 检查 `GEMINI_API_KEY` 和 `GPTZERO_API_KEY` 是否正确
2. 确认 API 密钥有足够的额度
3. 检查 API 密钥的权限

#### 问题4：管理员无法登录
**症状**：管理员密码错误
**解决**：
1. 检查 `ADMIN_PASSWORD` 环境变量
2. 数据库中的管理员密码哈希可能不匹配
3. 重置管理员密码（见下文）

### 4.2 重置管理员密码

如果需要重置管理员密码：

1. **通过环境变量**：
   - 在 Render 中更新 `ADMIN_PASSWORD` 变量
   - 重启服务

2. **通过数据库**：
   ```sql
   -- 连接到 PostgreSQL 数据库
   UPDATE users
   SET password_hash = SHA256('新密码')
   WHERE username = 'admin';
   ```

### 4.3 查看日志

- **Render 日志**：Dashboard → 服务 → "Logs" 标签页
- **Netlify 日志**：Dashboard → 站点 → "Deploys" → 点击部署 → "Deploy log"

## 第五部分：生产环境优化建议

### 5.1 安全性
1. **定期轮换密钥**：每 3-6 个月更换 `SECRET_KEY`
2. **使用强密码**：管理员密码至少 16 位，包含大小写、数字、特殊字符
3. **限制访问**：配置 IP 白名单（如果需要）
4. **启用监控**：Render 和 Netlify 都提供基本监控

### 5.2 性能
1. **升级计划**：根据用户量升级 Render 和 PostgreSQL 计划
2. **CDN**：Netlify 自动提供 CDN
3. **缓存策略**：考虑添加 Redis 缓存

### 5.3 备份
1. **数据库备份**：Render PostgreSQL 提供自动备份
2. **代码备份**：GitHub 作为代码备份
3. **环境备份**：导出环境变量备份

## 第六部分：更新部署

### 6.1 更新后端
1. 推送代码到 GitHub
2. Render 会自动重新部署
3. 检查部署日志

### 6.2 更新前端
1. 推送代码到 GitHub
2. Netlify 会自动重新构建和部署
3. 检查部署状态

### 6.3 数据库迁移
如果有数据库结构变更：
1. 更新 `models/database.py`
2. 创建迁移脚本
3. 手动执行迁移

## 附录

### A. 本地开发环境变量
创建 `backend/.env` 文件：
```env
ENVIRONMENT=development
DEBUG=True
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/otium.db
GEMINI_API_KEY=你的测试密钥
GPTZERO_API_KEY=你的测试密钥
SECRET_KEY=本地开发密钥
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### B. 有用的命令

```bash
# 本地开发
cd backend
python main.py

# 运行测试
cd backend
python test_backend.py
python test_auth_flow.py

# 数据库迁移
cd backend
python scripts/migrate_to_database.py

# 前端开发
cd frontend
npm start
```

### C. 联系支持

- **Render 支持**：Dashboard → "Support"
- **Netlify 支持**：Dashboard → "Help"
- **项目 Issues**：GitHub Issues

---

**部署完成 Checklist**：
- [ ] Render 后端服务运行正常
- [ ] PostgreSQL 数据库已初始化
- [ ] Netlify 前端部署完成
- [ ] CORS 配置正确
- [ ] API 密钥已设置
- [ ] 管理员可以登录
- [ ] 基本功能测试通过

祝您部署顺利！