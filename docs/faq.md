# 常见问题（FAQ）

## 📋 一般问题

### Q: Otium是什么？
A: Otium是一个全栈学术文本处理平台，专注于提供智能文本检查、AI检测、文本润色和翻译指令管理功能。

### Q: 项目的主要功能有哪些？
A:
1. **文本处理**：AI检测、文本检查、文本润色
2. **用户管理**：多用户系统、使用限制、管理员面板
3. **部署特性**：云原生部署、实时处理、API集成

### Q: 项目使用什么技术栈？
A:
- **前端**：React 18 + TypeScript + Zustand + Tailwind CSS
- **后端**：FastAPI + Pydantic + JWT
- **外部服务**：Gemini AI + GPTZero API

## 🚀 安装和运行

### Q: 如何快速启动项目？
A: 参考 [QUICK_START.md](../QUICK_START.md) 文档，使用项目提供的启动脚本：
- 后端：`backend/start_backend.bat` (Windows) 或 `backend/start_backend.ps1` (PowerShell)
- 前端：`frontend/start_frontend.bat` (Windows) 或 `frontend/start_frontend.ps1` (PowerShell)

### Q: 需要配置哪些环境变量？
A:
- **后端**：复制 `backend/.env.example` 为 `backend/.env`，配置：
  - `GEMINI_API_KEY`: Google Gemini API密钥
  - `GPTZERO_API_KEY`: GPTZero API密钥
  - `JWT_SECRET_KEY`: JWT令牌密钥
- **前端**：通常不需要特殊配置，如有需要参考前端目录的 `.env.example`

### Q: 启动时遇到端口占用怎么办？
A:
- **后端默认端口8000**：修改启动脚本中的端口参数
- **前端默认端口3000**：修改前端 `package.json` 中的 `start` 脚本

## 🔧 故障排除

### Q: 后端启动失败，提示依赖错误
A:
1. 确保Python版本为3.9+
2. 检查虚拟环境是否正确激活
3. 重新安装依赖：`pip install -r requirements.txt`
4. 查看详细的错误信息进行调试

### Q: 前端启动失败，npm安装错误
A:
1. 确保Node.js版本为18+
2. 清除缓存：删除 `node_modules` 和 `package-lock.json`
3. 重新安装：`npm install`
4. 检查网络连接

### Q: API调用返回错误
A:
1. 检查后端服务是否正常运行（访问 `http://localhost:8000/docs`）
2. 验证API密钥是否正确配置
3. 查看后端日志获取详细错误信息

## 🌐 部署问题

### Q: 项目当前如何部署？
A:
- **前端**：部署在Netlify（静态托管）
- **后端**：部署在Render（云服务）

### Q: 如何部署到生产环境？
A: 参考项目文档中的部署指南（计划中），或直接使用：
- Netlify：连接GitHub仓库自动部署
- Render：配置 `render.yaml` 文件或通过Web界面部署

### Q: Render部署时数据库存储有问题？
A: Render的文件系统是临时的，不适合JSON文件存储。建议：
1. 使用Render PostgreSQL插件（免费层可用）
2. 使用外部数据库服务（如Supabase、Neon）
3. 实现数据备份和恢复机制

## 📊 使用问题

### Q: 默认管理员账户是什么？
A: 用户名：`admin`，密码：`admin123`

### Q: 如何管理用户和权限？
A: 通过管理员面板（需管理员登录）管理用户、查看统计、设置使用限制。

### Q: API调用限制是多少？
A: 默认配置：
- 普通用户：每小时50次API调用
- 管理员用户：每小时200次API调用
- 可在 `UserLimitManager` 中调整限制

## 🔐 安全性问题

### Q: 如何保护API密钥？
A:
1. 永远不要将API密钥提交到版本控制
2. 使用环境变量管理密钥
3. 定期轮换密钥
4. 限制API密钥的权限范围

### Q: 如何增强系统安全性？
A:
1. 使用强密码策略
2. 启用HTTPS
3. 实施API速率限制
4. 定期更新依赖包
5. 进行安全扫描和代码审查

## 💻 开发问题

### Q: 如何贡献代码？
A: 参考 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解完整的贡献流程。

### Q: 代码规范是什么？
A:
- **前端**：ESLint + Prettier，TypeScript严格模式
- **后端**：PEP 8，Google风格文档字符串
- **提交消息**：约定式提交（Conventional Commits）

### Q: 如何运行测试？
A:
- **后端**：`cd backend && pytest`
- **前端**：`cd frontend && npm test`

## 📈 改进和扩展

### Q: 项目有哪些改进计划？
A: 参考 [IMPROVEMENT_PLAN.md](../IMPROVEMENT_PLAN.md) 查看完整的四阶段改进计划。

### Q: 可以添加新功能吗？
A: 当然可以！欢迎通过GitHub Issue提交功能请求，或直接创建Pull Request。

### Q: 如何扩展AI服务集成？
A: 在 `backend/services.py` 中添加新的服务类，遵循现有的模式（如GeminiService、GPTZeroService）。

---

**最后更新**：2026-02-08
**更多问题**：请创建 [GitHub Issue](https://github.com/yourusername/Otium_wip/issues) 或联系维护者