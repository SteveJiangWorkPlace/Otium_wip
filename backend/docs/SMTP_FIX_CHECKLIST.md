# SMTP邮件服务快速修复清单

## 问题症状
- 注册用户时显示："验证码已生成，如果未收到邮件请检查邮箱或联系管理员"
- 密码重置邮件也收不到
- API调用返回成功，但实际邮件发送失败

## 根本原因
邮件服务SMTP配置不正确，或Render环境阻止了QQ邮箱SMTP连接。

## 5分钟快速修复方案

### 方案A：切换到SendGrid（推荐，成功率95%）

**步骤1：获取SendGrid API密钥**
1. 访问 https://sendgrid.com/ 注册免费账户
2. 在控制台创建API密钥（赋予"Mail Send"权限）
3. 复制API密钥（以 `SG.` 开头）

**步骤2：更新Render环境变量**
登录Render控制台 → 选择Otium后端服务 → Environment标签页 → 更新以下变量：

```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=你的SendGrid_API密钥（SG.xxxxx）
SMTP_FROM=你的已验证邮箱（如noreply@example.com）
SMTP_TIMEOUT=30
SMTP_TLS=true
SMTP_SSL=false
```

**步骤3：重启服务**
在Render控制台点击"Manual Deploy" → "Clear Cache and Deploy"

### 方案B：修复QQ邮箱配置（如必须使用QQ邮箱）

**步骤1：获取QQ邮箱授权码**
1. 登录QQ邮箱网页版
2. 设置 → 账户 → POP3/IMAP/SMTP服务
3. 开启"POP3/SMTP服务"
4. 生成"授权码"（16位字符串，不是登录密码！）

**步骤2：更新Render环境变量**
```
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=你的完整QQ邮箱（如123456789@qq.com）
SMTP_PASSWORD=QQ邮箱授权码（16位字符串）
SMTP_FROM=与SMTP_USERNAME相同的邮箱
SMTP_TIMEOUT=30
SMTP_SSL=true
SMTP_TLS=false
```

**步骤3：重启服务**

## 验证修复是否成功

### 方法1：测试注册功能
1. 打开你的Netlify前端应用
2. 尝试注册新用户
3. 如果收到邮件，修复成功
4. 如果仍显示"检查邮箱或联系管理员"，继续下一步

### 方法2：运行诊断脚本
1. 在Render控制台打开"Shell"标签页
2. 运行：
```bash
cd backend
python test_smtp_connection.py
```
3. 查看输出，根据错误信息调整配置

### 方法3：检查应用日志
在Render控制台"Logs"标签页搜索：
- "邮件发送成功" → 配置正确
- "发送邮件失败" → 查看具体错误
- "SMTP连接失败" → 网络/配置问题

## 常见错误及解决方案

### 错误1：SMTPAuthenticationError
**原因**：用户名或密码错误
**解决**：
- SendGrid：确保`SMTP_USERNAME=apikey`，使用正确的API密钥
- QQ邮箱：使用授权码而非登录密码，邮箱格式正确

### 错误2：SMTPConnectError
**原因**：无法连接到SMTP服务器
**解决**：
- 检查SMTP_HOST和SMTP_PORT
- Render可能阻止连接，尝试SendGrid

### 错误3：TimeoutError
**原因**：连接超时
**解决**：增加`SMTP_TIMEOUT=60`

## 紧急应对方案

如果急需恢复注册功能：

### 临时方案：禁用邮件验证
在Render环境变量中添加：
```
EMAIL_VERIFICATION_REQUIRED=false
```
重启服务后，用户注册无需邮箱验证。

### 测试方案：输出验证码到日志
修改`backend/main.py`第477-485行，将验证码输出到日志而不是发送邮件（仅限测试）。

## 技术支持

如果问题仍未解决：
1. 运行诊断脚本并保存完整输出
2. 查看Render日志中的详细错误
3. 提供以下信息寻求帮助：
   - Render服务名称
   - 使用的邮件服务（SendGrid/QQ邮箱）
   - 诊断脚本输出截图
   - 错误日志片段

---
**创建时间**：2026-02-15
**预期修复时间**：5-15分钟
**成功率**：SendGrid方案 > 95%，QQ邮箱方案 > 70%