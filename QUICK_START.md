# Otium_wip 快速启动指南

本指南帮助您快速启动Otium_wip项目的本地开发环境。

## 环境要求

### 后端要求
- Python 3.8+
- pip (Python包管理器)

### 前端要求
- Node.js 16+
- npm (Node包管理器)

## 快速启动方式

### 选项一：使用启动脚本（推荐）

#### 后端启动
1. 进入后端目录：
   ```
   cd backend
   ```
2. 运行启动脚本：
   - **Windows命令提示符**：双击 `start_backend.bat` 或命令行运行：
     ```
     start_backend.bat
     ```
   - **PowerShell**：右键点击 `start_backend.ps1` 选择"使用PowerShell运行"，或命令行运行：
     ```
     .\start_backend.ps1
     ```
   - 如果遇到PowerScript执行策略错误，先运行：
     ```
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```

#### 前端启动
1. 进入前端目录：
   ```
   cd frontend
   ```
2. 运行启动脚本：
   - **Windows命令提示符**：双击 `start_frontend.bat` 或命令行运行：
     ```
     start_frontend.bat
     ```
   - **PowerShell**：右键点击 `start_frontend.ps1` 选择"使用PowerShell运行"，或命令行运行：
     ```
     .\start_frontend.ps1
     ```

### 选项二：手动启动

#### 后端手动启动
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（热重载）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端手动启动
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

## 访问应用

启动成功后，可以通过以下地址访问：

- **后端API**：http://localhost:8000
  - API文档：http://localhost:8000/docs
  - 健康检查：http://localhost:8000/api/health

- **前端应用**：http://localhost:3000

## 环境变量配置

### 后端环境变量
1. 复制后端 `.env.example` 为 `.env`：
   ```bash
   cd backend
   copy .env.example .env
   ```
2. 编辑 `.env` 文件，配置以下变量：
   - `GEMINI_API_KEY`: Google Gemini API密钥
   - `GPTZERO_API_KEY`: GPTZero API密钥
   - `JWT_SECRET_KEY`: JWT令牌密钥（生产环境必须修改）
   - `ADMIN_USERNAME`: 管理员用户名
   - `ADMIN_PASSWORD`: 管理员密码

### 前端环境变量
前端通常不需要额外环境变量，但如果有需要，可以参考前端目录的 `.env.example`（如有）。

## 开发说明

### 热重载功能
- **后端**：使用 `--reload` 参数，代码修改后自动重启
- **前端**：React默认支持热重载，代码修改后自动刷新

### 常用命令

#### 后端
```bash
# 运行测试
cd backend
pytest

# 代码格式化（如配置了black）
black .
```

#### 前端
```bash
# 运行测试
cd frontend
npm test

# 构建生产版本
npm run build
```

## 故障排除

### 后端常见问题
1. **端口占用**：如果8000端口被占用，修改启动脚本中的端口号
2. **依赖安装失败**：检查Python版本和网络连接
3. **虚拟环境问题**：脚本会自动检测虚拟环境，如需手动创建：
   ```bash
   python -m venv venv
   # Windows激活
   venv\Scripts\activate
   ```

### 前端常见问题
1. **端口占用**：如果3000端口被占用，修改 `package.json` 中的 `start` 脚本
2. **npm安装失败**：检查Node.js版本和网络连接
3. **依赖冲突**：删除 `node_modules` 和 `package-lock.json` 后重新安装

## 部署说明

### 生产环境部署
- **前端**：部署到Netlify（当前部署方式）
- **后端**：部署到Render（当前部署方式）

详细部署指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)（如有）或项目文档。

---

**提示**：启动脚本会自动处理依赖安装和环境检查，是本地开发的最便捷方式。