# 贡献指南

感谢您考虑为 Otium 项目做出贡献！本指南将帮助您了解如何参与项目开发。

## 开始之前

### 行为准则
请遵守以下行为准则：
- 尊重所有贡献者
- 建设性讨论，避免负面评论
- 专注于技术问题，而非个人

### 需要帮助？
如果您是第一次贡献开源项目：
1. 查看 [GitHub 第一次贡献指南](https://github.com/firstcontributions/first-contributions)
2. 阅读项目的 README.md
3. 如有疑问，请创建 Issue 询问

## 开发流程

### 1. 设置开发环境
请参考 [README.md](./README.md) 中的"快速开始"部分设置本地开发环境。

### 2. 选择任务
查看以下位置寻找可贡献的任务：
- [GitHub Issues](https://github.com/yourusername/Otium_wip/issues)
- [改进计划](./IMPROVEMENT_PLAN.md) 中的待办事项
- 功能请求或 Bug 报告

### 3. 创建分支
1. Fork 本仓库
2. 克隆您的 Fork：
   ```bash
   git clone https://github.com/your-username/Otium_wip.git
   cd Otium_wip
   ```

3. 创建功能分支：
   ```bash
   git checkout -b feature/your-feature-name
   # 或修复 Bug：
   git checkout -b fix/issue-number-description
   ```

### 4. 进行更改
#### 前端开发（React/TypeScript）
```bash
cd frontend
npm install          # 安装依赖
npm start           # 启动开发服务器
npm run lint        # 检查代码规范
npm run build       # 构建检查
```

#### 后端开发（FastAPI/Python）
```bash
cd backend
python -m venv venv  # 创建虚拟环境
# 激活虚拟环境
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

pip install -r requirements.txt  # 安装依赖
uvicorn main:app --reload       # 启动开发服务器
pytest tests/                   # 运行测试
```

### 5. 提交更改
使用约定式提交（Conventional Commits）格式：
```bash
git add .
git commit -m "feat: 添加新的文本处理功能"
git commit -m "fix: 修复登录页面的样式问题"
git commit -m "docs: 更新API文档"
git commit -m "refactor: 重构用户认证模块"
```

**提交类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变更

### 6. 推送到远程
```bash
git push origin feature/your-feature-name
```

### 7. 创建 Pull Request
1. 访问您的 Fork 仓库
2. 点击 "Compare & pull request"
3. 填写 PR 模板：
   - **标题**：简洁描述更改
   - **描述**：
     - 更改的目的
     - 测试方法
     - 相关 Issue（使用 #号码）
   - **检查清单**：
     - [ ] 代码遵循项目规范
     - [ ] 添加/更新了测试
     - [ ] 更新了文档
     - [ ] 本地测试通过

## 代码规范

### 前端规范
- **TypeScript**：使用严格模式
- **React**：使用函数组件和 Hooks
- **命名约定**：
  - 组件：`PascalCase` (如 `TextProcessor.tsx`)
  - 函数/变量：`camelCase`
  - 常量：`UPPER_SNAKE_CASE`
- **导入顺序**：
  1. React 和第三方库
  2. 绝对路径导入
  3. 相对路径导入
  4. 样式文件

### 后端规范
- **Python**：遵循 PEP 8
- **FastAPI**：使用类型提示
- **命名约定**：
  - 函数/变量：`snake_case`
  - 类：`PascalCase`
  - 常量：`UPPER_SNAKE_CASE`
- **文档字符串**：使用 Google 风格
  ```python
  def process_text(text: str) -> str:
      """处理文本并返回结果。

      Args:
          text: 要处理的文本

      Returns:
          处理后的文本

      Raises:
          ValidationError: 文本格式无效时
      """
  ```
- **提示词开发规范**：
  - 提示词模板应定义在 `prompt_templates.py` 中
  - 保持原始提示词在注释中完整备份
  - 使用模板版本常量管理不同版本
  - 所有提示词构建应通过 `prompts.py` 中的函数进行
  - 新功能应集成缓存和监控系统

### 提交前检查
运行以下命令确保代码质量：
```bash
# 前端
cd frontend
npm run lint    # ESLint 检查
npm run build   # 构建检查

# 后端
cd backend
pytest tests/   # 运行测试
black .         # 代码格式化（如果配置了）
isort .         # 导入排序（如果配置了）
```

## 测试

### 测试策略
- **单元测试**：测试单个函数/方法
- **集成测试**：测试模块间交互
- **API 测试**：测试端点功能

### 编写测试
#### 前端测试（Jest + React Testing Library）
```typescript
// __tests__/TextProcessor.test.tsx
import { render, screen } from '@testing-library/react';
import TextProcessor from '../TextProcessor';

describe('TextProcessor', () => {
  it('渲染文本输入框', () => {
    render(<TextProcessor />);
    expect(screen.getByPlaceholderText('输入文本')).toBeInTheDocument();
  });
});
```

#### 后端测试（pytest）
```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/api/login", json={
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "token" in response.json()
```

### 测试覆盖率目标
- 总体覆盖率：≥ 80%
- 关键业务逻辑：≥ 90%

## 文档

### 文档要求
所有主要更改都应包含文档更新：

1. **代码注释**：复杂逻辑需要注释
2. **API 文档**：FastAPI 自动生成，但需要添加描述
3. **用户文档**：README.md 和相关指南
4. **开发文档**：本文件和架构文档

### 文档更新流程
1. 代码更改和文档更新在同一 PR 中
2. 确保文档与实际代码一致
3. 添加必要的示例和截图

## 代码审查

### 审查标准
所有 PR 都需要通过代码审查：
- **功能性**：代码是否正确实现功能
- **可读性**：代码是否易于理解
- **可维护性**：是否遵循项目架构
- **测试**：是否有足够的测试覆盖
- **文档**：是否更新了相关文档

### 审查流程
1. 至少需要一位核心贡献者批准
2. 解决所有审查意见
3. 确保 CI/CD 通过
4. 合并到主分支

## 报告问题

### Bug 报告模板
创建 Issue 时请提供：
```markdown
## 问题描述
清晰描述问题

## 重现步骤
1. 第一步
2. 第二步
3. 第三步

## 预期行为
期望发生什么

## 实际行为
实际发生了什么

## 环境信息
- 操作系统：
- 浏览器：
- 版本：
- 其他相关环境信息

## 截图/日志
如果有，请提供
```

### 功能请求模板
```markdown
## 功能描述
清晰描述需要的功能

## 使用场景
为什么需要这个功能

## 可能的解决方案
如果有想法，请描述

## 替代方案
考虑过的其他方案
```

## 贡献者等级

根据贡献程度，贡献者分为：

### 初级贡献者
- 提交第一个成功的 PR
- 报告有价值的 Bug
- 改进文档

### 活跃贡献者
- 提交多个 PR
- 参与 Issue 讨论
- 帮助审查代码

### 核心贡献者
- 对项目有深入理解
- 负责重要功能开发
- 参与项目决策

## 许可证

贡献即表示您同意您的贡献将在项目的 MIT 许可证下发布。

## 致谢

感谢所有贡献者的时间和努力！您的贡献使项目变得更好。

---

**最后更新**：2026-02-14
**维护者**：项目维护团队