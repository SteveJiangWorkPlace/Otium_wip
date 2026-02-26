# 测试脚本使用说明

本项目包含前端和后端的健康检查测试脚本，用于验证系统是否可以正常工作。

## 脚本列表

### Python测试脚本
1. **test_backend.py** - 后端健康检查测试
   - 测试后端服务是否运行
   - 测试健康端点
   - 测试数据库连接
   - 测试基本API功能
   - 检查后端依赖

2. **test_frontend.py** - 前端健康检查测试
   - 检查前端项目结构
   - 检查npm依赖安装
   - 检查TypeScript配置
   - 测试npm测试配置
   - 检查构建配置
   - 检查API配置

### 便捷启动脚本

#### Windows批处理文件 (.bat)
- `run_backend_test.bat` - 运行后端测试
- `run_frontend_test.bat` - 运行前端测试

#### PowerShell脚本 (.ps1)
- `run_backend_test.ps1` - 运行后端测试（PowerShell）
- `run_frontend_test.ps1` - 运行前端测试（PowerShell）

## 使用方法

### 1. 使用Python脚本直接运行

```bash
# 后端测试
python scripts/test_backend.py

# 前端测试
python scripts/test_frontend.py
```

### 2. 使用批处理文件（Windows命令提示符）

```cmd
# 后端测试
scripts\run_backend_test.bat

# 前端测试
scripts\run_frontend_test.bat
```

### 3. 使用PowerShell脚本

```powershell
# 后端测试
.\scripts\run_backend_test.ps1

# 前端测试
.\scripts\run_frontend_test.ps1
```

## 测试要求

### 后端测试要求
1. Python 3.7+ 已安装
2. requests库已安装（脚本会自动检查并安装）
3. 后端服务正在运行（默认端口8000）
4. 管理员账户存在（默认：admin/admin123）

### 前端测试要求
1. Python 3.7+ 已安装
2. Node.js 14.0.0+ 已安装（可选，但推荐）
3. npm依赖已安装（`cd frontend && npm install`）

## 测试输出说明

测试脚本会显示详细的测试结果，包括：

1. **通过测试** - 系统功能正常
2. **失败测试** - 需要修复的问题
3. **警告** - 需要注意但不影响基本功能的问题

测试脚本遵循Windows编码兼容性规范：
- 避免使用Unicode字符（如[成功]、[失败]、[警告]）
- 使用ASCII兼容标记如[成功]、[失败]、[警告]
- 支持Windows命令行（GBK编码）

## 故障排除

### 后端测试失败
1. **无法连接到后端服务**
   - 确保后端正在运行：`cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
   - 检查端口8000是否被占用

2. **数据库连接失败**
   - 检查数据库配置
   - 确保管理员账户存在：运行 `python -c "from models.database import ensure_admin_user_exists; ensure_admin_user_exists()"`

3. **依赖检查失败**
   - 安装缺少的依赖：`pip install -r backend/requirements.txt`

### 前端测试失败
1. **Node.js未安装**
   - 安装Node.js 14.0.0+版本
   - 将Node.js添加到PATH环境变量

2. **npm依赖未安装**
   - 运行：`cd frontend && npm install`

3. **项目结构不完整**
   - 检查关键文件是否缺失
   - 确保前端项目目录结构正确

## 集成到工作流

### 开发环境检查
在开始开发前，可以运行测试脚本确保环境正常：

```bash
# 检查后端环境
python scripts/test_backend.py

# 检查前端环境
python scripts/test_frontend.py
```

### CI/CD集成
测试脚本可以集成到CI/CD流程中，作为健康检查步骤：

```yaml
# 示例GitHub Actions配置
jobs:
  health-check:
    runs-on: windows-latest
    steps:
      - name: 后端健康检查
        run: python scripts/test_backend.py

      - name: 前端健康检查
        run: python scripts/test_frontend.py
```

## 扩展测试

现有的测试脚本提供基本健康检查。对于更全面的测试，请参考：

1. **后端系统测试**：`backend/scripts/run_system_test.py`
2. **最终系统测试**：`backend/scripts/final_system_test.py`
3. **代码质量检查**：`scripts/run_quality_checks.py`

## 更新日志

- **2026-02-25**：创建基础测试脚本
  - 后端健康检查脚本
  - 前端健康检查脚本
  - Windows批处理文件
  - PowerShell脚本
  - 完整文档