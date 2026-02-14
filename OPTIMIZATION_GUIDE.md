# 优化修改指导手册

本手册记录每次对Otium项目进行优化和修改时的注意事项和工作流程，确保开发过程的一致性和质量。

## 基本原则

每次进行优化和修改时，请遵循以下基本原则：

### 1. 文档同步更新
- **CONTRIBUTING.md**：如果修改涉及开发流程、代码规范或贡献指南，必须更新此文件
- **README.md**：如果修改影响用户功能、安装步骤或项目介绍，必须更新此文件
- **CLAUDE.md**：如果修改涉及项目架构、技术栈或重要配置，必须更新此文件

### 2. 本地化部署测试
在推送到Render后端和Netlify前端之前，必须在本地进行完整测试：

**重要变更**：现在使用完全手动启动方式，不依赖启动脚本。详细步骤请参考 [MANUAL_STARTUP.md](./MANUAL_STARTUP.md)，包含端口占用检查、虚拟环境配置和热重载设置。

#### Windows PowerShell启动指令（使用UTF-8编码）
为避免Claude Code运行时出现乱码，请使用以下UTF-8编码的PowerShell命令：

**后端启动（已弃用，仅作参考）**：
```powershell
# 使用UTF-8编码启动后端
$OutputEncoding = [System.Text.Encoding]::UTF8
cd backend
.\start_backend.ps1
```

**前端启动（已弃用，仅作参考）**：
```powershell
# 使用UTF-8编码启动前端
$OutputEncoding = [System.Text.Encoding]::UTF8
cd frontend
.\start_frontend.ps1
```

**手动启动（主要方式）**：
详细完整指南请参考 [MANUAL_STARTUP.md](./MANUAL_STARTUP.md)，包含端口占用检查、备用端口选择等完整流程。
```powershell
# 后端手动启动
$OutputEncoding = [System.Text.Encoding]::UTF8
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端手动启动
$OutputEncoding = [System.Text.Encoding]::UTF8
cd frontend
npm install
npm start
```

### 3. 单元测试检查
**每次新增功能或修改现有功能后，必须检查是否有相应的单元测试**：

#### 前端测试检查
```bash
cd frontend
# 检查是否有对应的测试文件
find src -name "*.test.tsx" -o -name "*.test.ts" -o -name "*.spec.tsx" -o -name "*.spec.ts"
# 运行现有测试
npm test
```

#### 后端测试检查
```bash
cd backend
# 检查是否有对应的测试文件
find . -name "test_*.py" -o -name "*_test.py"
# 运行现有测试
pytest tests/
```

#### 测试覆盖率要求
- 新增功能必须包含至少基本的单元测试
- 关键业务逻辑测试覆盖率应≥80%
- 如果没有对应测试，应优先补充测试代码

### 4. 代码输出标准化（严格禁止卡通图标）

**严格禁止代码中出现任何卡通图标、表情符号或图形字符**：

根据用户明确要求，代码中绝对不允许出现任何卡通图标（emoji、表情符号、图形字符等）。Claude Code有时会自动生成带有表情符号的代码，然后再替换为文本标签，这种先写错再修改的过程会浪费token。请遵循以下严格规则：

#### 直接使用文本标签，避免表情符号
```python
# ❌ 错误：使用表情符号，Claude Code可能会先写入再替换
print("❌ AI优化模板的基础版本提示词未包含'Strictly Avoid'")

# ✅ 正确：直接使用文本标签
print("[FAIL] AI优化模板的基础版本提示词未包含'Strictly Avoid'")
```

#### 常用标签映射
- **❌** → **[FAIL]** 或 **[ERROR]**（失败/错误）
- **✅** → **[PASS]** 或 **[SUCCESS]**（通过/成功）
- **⚠️** → **[WARN]** 或 **[WARNING]**（警告）
- **🔍** → **[DEBUG]** 或 **[INFO]**（调试/信息）
- **🚀** → **[PERF]** 或 **[PERFORMANCE]**（性能）

#### 重要原则
1. **严格禁止卡通图标**：代码中绝对不允许出现任何卡通图标、表情符号或图形字符
2. **一次性写入正确文本**：不要依赖Claude Code的自动替换功能，直接从一开始就写入文本标签
3. **保持一致性**：在整个项目中统一使用相同的文本标签格式
4. **跨平台兼容**：文本标签在所有终端和环境下都能正确显示，而图标可能在部分环境中显示异常
5. **可搜索性**：文本标签便于在日志中搜索和过滤，图标无法通过文本搜索
6. **避免token浪费**：先写图标再替换为文本会浪费token，必须直接从开始就使用文本

#### 检查点
- **严格禁止**：代码中任何地方都不允许出现卡通图标、表情符号或图形字符
- **文档要求**：Markdown文档中应尽量避免使用图标，如必须使用应保持最小化
- **代码适用范围**：包括日志输出、调试信息、测试结果、注释、字符串常量等所有代码位置
- **统一格式**：使用方括号`[]`包裹标签以增强可读性
- **标签设计**：保持标签简洁明了，语义清晰
- **代码审查**：在代码审查时特别检查是否有违规的图标使用

## 标准工作流程

### 步骤1：分析修改影响
1. 确定修改会影响哪些模块
2. 检查相关文档是否需要更新
3. 评估测试覆盖情况

### 步骤2：实施修改
1. 按照项目代码规范进行修改
2. 保持代码风格一致
3. 添加必要的注释

### 步骤3：本地测试
1. 使用UTF-8编码的PowerShell启动前后端
2. 测试所有相关功能
3. 检查控制台是否有错误或警告
4. 验证API端点是否正常工作

### 步骤4：单元测试
1. **检查是否有对应功能的单元测试**
2. 如果没有，创建测试文件并编写测试用例
3. 运行现有测试确保没有破坏现有功能
4. 确保测试通过率达到要求

### 步骤5：文档更新
1. 更新CONTRIBUTING.md（如果影响开发流程）
2. 更新README.md（如果影响用户功能）
3. 更新CLAUDE.md（如果影响项目架构）
4. 确保文档与实际代码一致

### 步骤6：最终验证
1. 重新启动应用验证所有功能
2. 检查控制台输出是否有乱码（使用UTF-8编码避免此问题）
3. 确认文档链接和示例代码正确

## 常见问题处理

### 乱码问题
如果在Claude Code运行时看到乱码：
1. 确保使用UTF-8编码启动PowerShell：`$OutputEncoding = [System.Text.Encoding]::UTF8`
2. 检查系统区域设置是否支持UTF-8
3. 在PowerShell中执行：`chcp 65001`（将控制台代码页设置为UTF-8）

### 端口占用问题
如果端口被占用：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 终止进程（谨慎操作）
taskkill /PID [PID] /F
```

### 依赖问题
如果遇到依赖问题：
```powershell
# 后端依赖
cd backend
pip install -r requirements.txt --upgrade

# 前端依赖
cd frontend
npm install
npm audit fix
```

## 提交前检查清单

在提交修改前，请确认以下事项：

- [ ] 所有功能在本地测试通过
- [ ] 使用UTF-8编码的PowerShell启动，无乱码问题
- [ ] **检查并补充了相应的单元测试**
- [ ] 现有测试全部通过
- [ ] CONTRIBUTING.md已更新（如需要）
- [ ] README.md已更新（如需要）
- [ ] CLAUDE.md已更新（如需要）
- [ ] 代码符合项目规范
- [ ] 无控制台错误或警告
- [ ] API文档仍然准确

## 版本记录

### 2026-02-14
- 创建优化修改指导手册
- 添加文档同步更新要求
- 添加UTF-8编码的PowerShell启动指令
- **添加单元测试检查要求**
- **添加代码输出标准化规则**：严格禁止卡通图标，避免token浪费

---

**维护提示**：本手册应随着项目发展而更新，反映最新的最佳实践和工作流程。