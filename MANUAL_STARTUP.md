# 手动启动指导手册

本指南提供Otium项目前后端的完全手动启动方法，不依赖任何启动脚本。所有操作均在虚拟环境中进行，支持热重载，启动时会检查端口占用情况并自动寻找空闲端口。

## 基本原则

- **完全手动**：不使用任何启动脚本，每个步骤手动执行
- **虚拟环境**：后端必须在Python虚拟环境中运行
- **热重载**：开发服务器支持代码修改后自动重载
- **端口管理**：启动前检查端口占用，自动寻找空闲端口
- **UTF-8编码**：避免Claude Code运行时乱码问题

## 环境要求

### 后端要求
- Python 3.9+
- pip (Python包管理器)

### 前端要求
- Node.js 18+
- npm (Node包管理器)

## 端口占用检查（启动前必须执行）

在启动前后端之前，先检查默认端口是否被占用：

### 检查8000端口（后端默认）
```powershell
# 使用UTF-8编码避免乱码
$OutputEncoding = [System.Text.Encoding]::UTF8

# 检查8000端口占用情况
netstat -ano | findstr :8000

# 如果端口被占用，显示进程信息
# 示例输出：TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       1234
# 进程ID为1234，可以通过以下命令终止（谨慎操作）：
# taskkill /PID 1234 /F
```

### 检查3000端口（前端默认）
```powershell
# 检查3000端口占用情况
netstat -ano | findstr :3000
```

### 寻找空闲端口
如果默认端口被占用，可以选择以下备用端口：
- **后端备用端口**：8001、8002、8003、8080、8888
- **前端备用端口**：3001、3002、3003、3004、3005

## 后端手动启动

### 步骤1：创建和激活虚拟环境
```powershell
# 使用UTF-8编码
$OutputEncoding = [System.Text.Encoding]::UTF8

# 进入后端目录
cd backend

# 创建虚拟环境（如果不存在）
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 验证虚拟环境激活
# 命令行提示符前应显示 (venv)
```

### 步骤2：安装依赖
```powershell
# 确保在虚拟环境中
# 安装所有依赖
pip install -r requirements.txt

# 如果需要升级pip
python -m pip install --upgrade pip
```

### 步骤3：配置环境变量
```powershell
# 复制环境变量模板
copy .env.example .env

# 编辑.env文件，配置以下必需变量：
# GEMINI_API_KEY=your-gemini-api-key
# GPTZERO_API_KEY=your-gptzero-api-key
# SECRET_KEY=your-strong-secret-key-change-in-production
```

### 步骤4：启动后端开发服务器（热重载）
```powershell
# 使用uvicorn启动，支持热重载
# 默认端口8000，如果被占用使用备用端口
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 如果8000端口被占用，使用备用端口：
# uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

**关键参数说明**：
- `--host 0.0.0.0`：允许所有网络接口访问
- `--port XXXX`：指定端口号
- `--reload`：启用热重载，代码修改后自动重启

## 前端手动启动

### 步骤1：进入前端目录
```powershell
# 使用UTF-8编码
$OutputEncoding = [System.Text.Encoding]::UTF8

# 进入前端目录
cd frontend
```

### 步骤2：安装依赖
```powershell
# 安装Node.js依赖
npm install

# 如果安装失败，尝试清理缓存
npm cache clean --force
```

### 步骤3：配置前端环境变量
```powershell
# 复制环境变量模板
copy .env.example .env.local

# 编辑.env.local，配置API基础URL
# 如果后端使用非8000端口，需要相应修改
# REACT_APP_API_BASE_URL=http://localhost:8000
# 如果后端使用8001端口：
# REACT_APP_API_BASE_URL=http://localhost:8001
```

### 步骤4：启动前端开发服务器（热重载）
```powershell
# 使用npm启动开发服务器
# 默认端口3000，如果被占用使用备用端口
npm start

# React会自动处理端口冲突，如果3000被占用会询问是否使用3001
# 也可以手动指定端口：
# set PORT=3001 && npm start
```

## 访问应用

启动成功后，通过以下地址访问：

### 后端API
- **默认地址**：http://localhost:8000
- **备用地址**（如果使用其他端口）：http://localhost:8001、http://localhost:8002等
- **API文档**：http://localhost:8000/docs（或相应端口）
- **健康检查**：http://localhost:8000/api/health

### 前端应用
- **默认地址**：http://localhost:3000
- **备用地址**：http://localhost:3001、http://localhost:3002等

## 热重载功能

### 后端热重载
- Uvicorn的`--reload`参数启用热重载
- 修改Python代码后自动重启服务器
- 无需手动停止和重启

### 前端热重载
- React开发服务器默认支持热重载
- 修改代码后浏览器自动刷新
- 保持应用状态（使用React Fast Refresh）

## 完整启动示例

### 场景：默认端口均被占用
```powershell
# 设置UTF-8编码
$OutputEncoding = [System.Text.Encoding]::UTF8

# 1. 检查端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 2. 启动后端（假设8000被占用，使用8001）
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 3. 新终端窗口启动前端（假设3000被占用，使用3001）
cd frontend
npm install
set PORT=3001 && npm start

# 4. 访问地址
# 后端：http://localhost:8001
# 前端：http://localhost:3001
# 需要修改前端.env.local中的REACT_APP_API_BASE_URL为http://localhost:8001
```

## 故障排除

### 常见问题1：端口占用
**症状**：启动时提示"Address already in use"
**解决方案**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 终止进程（谨慎操作）
taskkill /PID [进程ID] /F

# 或使用备用端口
```

### 常见问题2：虚拟环境激活失败
**症状**：执行命令提示"venv\Scripts\activate不是可执行的脚本"
**解决方案**：
```powershell
# 重新创建虚拟环境
cd backend
rmdir /s venv  # 删除旧虚拟环境
python -m venv venv
venv\Scripts\activate
```

### 常见问题3：依赖安装失败
**症状**：pip install或npm install失败
**解决方案**：
```powershell
# 后端：使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 前端：清理缓存
npm cache clean --force
npm install
```

### 常见问题4：乱码显示
**症状**：PowerShell输出中文乱码
**解决方案**：
```powershell
# 在每条命令前设置UTF-8编码
$OutputEncoding = [System.Text.Encoding]::UTF8

# 或设置控制台代码页
chcp 65001
```

## 开发命令参考

### 后端开发命令
```powershell
# 运行测试
pytest

# 代码格式化（如配置了black）
black .

# 检查代码规范
flake8 .
```

### 前端开发命令
```powershell
# 运行测试
npm test

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

## 重要提示

1. **始终使用虚拟环境**：避免系统Python环境污染
2. **先检查端口**：启动前务必检查端口占用情况
3. **保持热重载**：开发时务必使用`--reload`参数
4. **注意端口对应**：如果修改后端端口，前端环境变量需要同步更新
5. **UTF-8编码**：所有PowerShell命令前加上`$OutputEncoding = [System.Text.Encoding]::UTF8`

## 版本记录

### 2026-02-14
- 创建手动启动指导手册
- 强调完全手动操作，不使用脚本
- 添加端口占用检查和空闲端口寻找
- 包含UTF-8编码设置避免乱码
- 提供完整故障排除方案

---

**注意**：本手册适用于需要完全控制启动过程的开发场景。如需快速启动，可参考QUICK_START.md中的脚本启动方式。