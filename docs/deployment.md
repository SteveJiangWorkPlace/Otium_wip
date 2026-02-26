# 部署指南

本指南介绍如何将 Otium 项目部署到生产环境。当前部署架构为：
- **前端**：Netlify（静态网站托管）
- **后端**：Render（云服务）

## [部署概述]

### 部署架构
```
用户 → Netlify（前端） → Render（后端API） → 外部服务（Gemini AI, GPTZero）
```

### 环境要求
- **前端**：Netlify账户（免费层足够）
- **后端**：Render账户（免费层足够，但注意限制）
- **域名**：可选，可以使用Netlify和Render提供的免费子域名

## [Netlify 前端部署]

### 1. 准备工作
1. 注册 [Netlify](https://www.netlify.com/) 账户
2. 连接GitHub账户，授权访问仓库

### 2. 自动部署（推荐）
1. 在Netlify控制台点击 "New site from Git"
2. 选择GitHub和仓库
3. 配置构建设置：
   - **构建命令**：`cd frontend && npm run build`
   - **发布目录**：`frontend/build`
   - **环境变量**：添加 `REACT_APP_API_BASE_URL`（指向Render后端）

### 3. 环境变量配置
在Netlify控制台的 "Site settings" > "Environment variables" 中添加：
```
REACT_APP_API_BASE_URL=https://your-render-backend.onrender.com
```

### 4. 自定义域名（可选）
1. 在 "Domain settings" 中添加自定义域名
2. 配置DNS记录指向Netlify
3. 启用HTTPS（Netlify自动提供）

### 5. 部署预览
- 每个Pull Request自动生成预览部署
- 便于测试和代码审查

## [Render 后端部署]

### 1. 准备工作
1. 注册 [Render](https://render.com/) 账户
2. 连接GitHub账户

### 2. 创建Web服务
1. 在Render控制台点击 "New +" > "Web Service"
2. 选择GitHub仓库
3. 配置服务设置：
   - **名称**：`otium-backend`（或其他有意义的名称）
   - **环境**：`Python 3`
   - **构建命令**：`pip install -r backend/requirements.txt`
   - **启动命令**：`cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **计划**：Free（免费层）

### 3. 环境变量配置
在Render控制台的 "Environment" 标签页添加：
```
# API密钥
GEMINI_API_KEY=your-gemini-api-key
GPTZERO_API_KEY=your-gptzero-api-key

# JWT配置
JWT_SECRET_KEY=your-strong-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置（允许Netlify前端访问）
CORS_ORIGINS=https://your-netlify-app.netlify.app,http://localhost:3000

# 邮件服务配置（必需，用于用户注册和密码重置）
# 首先设置邮件提供商（resend 或 smtp）
EMAIL_PROVIDER=resend

# 选项1：Resend API（推荐，HTTP API方式，更可靠）
RESEND_API_KEY=你的Resend_API密钥
RESEND_FROM=你的已验证邮箱（如onboarding@resend.dev或自定义域名邮箱）

# 选项2：SendGrid（SMTP方式，与Render集成良好）
# EMAIL_PROVIDER=smtp
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_USERNAME=apikey
# SMTP_PASSWORD=你的SendGrid_API密钥
# SMTP_FROM=你的已验证邮箱
# SMTP_TIMEOUT=30
# SMTP_TLS=true
# SMTP_SSL=false

# 选项3：QQ邮箱（需要授权码，不是登录密码）
# EMAIL_PROVIDER=smtp
# SMTP_HOST=smtp.qq.com
# SMTP_PORT=465
# SMTP_USERNAME=你的QQ邮箱（如123456789@qq.com）
# SMTP_PASSWORD=QQ邮箱授权码（16位字符串）
# SMTP_FROM=发件人邮箱（与SMTP_USERNAME相同）
# SMTP_TIMEOUT=30
# SMTP_SSL=true
# SMTP_TLS=false

# 数据库配置（如果使用数据库）
DATABASE_URL=postgresql://user:password@host:port/database
```

### 4. Render特定注意事项
1. **免费层限制**：
   - 服务在15分钟无活动后休眠
   - 唤醒需要几秒钟
   - 每月750小时运行时间

2. **文件系统限制**：
   - Render文件系统是临时的
   - 不适合JSON文件存储
   - 建议使用数据库（见下文）

3. **健康检查**：
   - Render要求健康检查端点
   - 项目已提供 `/api/health` 端点

### 5. 自动部署
- 连接GitHub仓库后，每次推送自动部署
- 支持回滚到之前的版本

## [数据库配置]

### Render PostgreSQL（推荐）
1. 在Render控制台创建 "PostgreSQL" 数据库
2. 选择Free计划
3. 连接Web服务到数据库
4. 更新环境变量 `DATABASE_URL`

### 外部数据库服务
备选方案（如果Render PostgreSQL不可用）：
1. **Supabase**：免费的PostgreSQL托管
2. **Neon**：无服务器PostgreSQL
3. **Railway**：综合部署平台

### 数据迁移
如果从JSON文件迁移到数据库，运行迁移脚本：
```bash
cd backend
python scripts/migrate_json_to_database.py
```

## [CI/CD 配置（可选）]

### GitHub Actions
项目包含基本的CI/CD配置（计划中），可以：
1. 自动运行测试
2. 检查代码质量
3. 部署到Netlify和Render

### 本地部署脚本
创建本地部署脚本简化流程：
```bash
# deploy.sh
npm run build
netlify deploy --prod
```

## [安全部署检查清单]

### 生产环境必做
- [ ] 修改默认管理员密码
- [ ] 使用强JWT密钥
- [ ] 启用HTTPS（Netlify和Render自动提供）
- [ ] 限制CORS源
- [ ] 设置API速率限制
- [ ] 定期备份数据库

### 监控和日志
- [ ] 设置错误监控（Sentry等）
- [ ] 配置日志聚合
- [ ] 设置性能监控
- [ ] 创建警报机制

## [常见部署问题]

### 问题1：CORS错误
**症状**：前端无法访问后端API
**解决方案**：
1. 检查CORS_ORIGINS配置
2. 确保包含前端域名
3. 验证HTTPS配置

### 问题2：数据库连接失败
**症状**：后端无法连接数据库
**解决方案**：
1. 检查DATABASE_URL格式
2. 验证数据库访问权限
3. 检查网络连接

### 问题3：服务休眠后响应慢
**症状**：Render免费层服务休眠后第一次请求慢
**解决方案**：
1. 使用监控服务定期ping（保持活跃）
2. 升级到付费计划
3. 优化冷启动时间

### 问题4：API密钥限制
**症状**：Gemini或GPTZero API调用失败
**解决方案**：
1. 检查API密钥是否正确
2. 验证API配额
3. 配置适当的重试机制

### 问题5：邮件发送失败
**症状**：用户注册或密码重置时显示"验证码已生成，如果未收到邮件请检查邮箱或联系管理员"
**解决方案**：
1. 检查SMTP环境变量配置是否正确（参考环境变量配置部分）
2. 验证邮件服务账户是否激活（QQ邮箱需要开启SMTP服务并获取授权码）
3. 测试SMTP连接：运行 `python backend/test_smtp_connection.py`
4. 考虑使用SendGrid替代QQ邮箱（Render集成更好）
5. 检查Render日志中的SMTP错误信息

## [性能优化]

### 前端优化
1. **代码分割**：React.lazy动态导入
2. **资源优化**：压缩图片，使用CDN
3. **缓存策略**：合理设置HTTP缓存头

### 后端优化
1. **数据库连接池**：管理数据库连接
2. **缓存机制**：实现API响应缓存
3. **异步处理**：长时间任务异步执行

## [多环境部署]

### 环境分类
1. **开发环境**：本地开发
2. **测试环境**：预览部署
3. **生产环境**：正式服务

### 环境变量管理
```bash
# 开发环境 (.env.local)
REACT_APP_API_BASE_URL=http://localhost:8000

# 生产环境 (Netlify环境变量)
REACT_APP_API_BASE_URL=https://otium-backend.onrender.com
```

## 🆘 故障排除

### 部署失败检查清单
1. **构建失败**：检查构建日志，依赖是否正确
2. **启动失败**：检查启动命令，端口配置
3. **运行时错误**：查看应用日志，环境变量
4. **网络问题**：检查防火墙，DNS解析

### 获取帮助
1. 查看 [常见问题](./faq.md)
2. 查阅平台文档（Netlify、Render）
3. 创建GitHub Issue
4. 联系维护者

---

**最后更新**：2026-02-15
**部署状态**：Netlify + Render 已验证
**注意事项**：免费层有使用限制，生产环境建议升级到付费计划