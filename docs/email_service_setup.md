# 邮件服务配置指南

## 问题描述
在Render和Netlify部署的Otium应用中，用户报告：
- 注册功能显示"验证码已生成，如果未收到邮件请检查邮箱或联系管理员"
- 密码重置邮件也无法收到
- API调用成功，但实际邮件发送失败

## 问题根源
邮件发送失败但API返回成功是安全设计（防止邮箱枚举攻击）。问题可能包括：

1. **Render环境变量配置不正确**
2. **QQ邮箱SMTP服务在云环境中的限制**
3. **Render网络策略阻止出站SMTP连接**

## 解决方案

### 方案1：配置QQ邮箱SMTP（如已在使用）

#### 步骤1：检查当前Render环境变量
登录Render控制台 (https://dashboard.render.com/)，选择你的Otium后端服务，进入"Environment"标签页，检查以下变量：

```
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=你的QQ邮箱（如123456789@qq.com）
SMTP_PASSWORD=QQ邮箱授权码（不是登录密码！）
SMTP_FROM=发件人邮箱（与SMTP_USERNAME相同）
SMTP_TIMEOUT=30
SMTP_SSL=true
SMTP_TLS=false
```

#### 步骤2：获取QQ邮箱授权码
1. 登录QQ邮箱网页版
2. 点击"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"或"IMAP/SMTP服务"
5. 生成授权码（16位字符串）
6. 使用授权码作为`SMTP_PASSWORD`

#### 步骤3：测试SMTP连接
在Render服务中运行测试脚本：

1. 在Render控制台的"Shell"标签页打开终端
2. 运行：
```bash
cd backend
python test_smtp_connection.py
```

或通过SSH连接到Render实例：
```bash
ssh <service-name>@ssh.render.com
cd backend
python test_smtp_connection.py
```

### 方案2：切换到SendGrid（推荐，与Render集成更好）

SendGrid是专业的邮件服务，与Render平台集成良好，可靠性更高。

#### 步骤1：注册SendGrid账户
1. 访问 [SendGrid官网](https://sendgrid.com/)
2. 注册免费账户（每月100封邮件）
3. 验证邮箱地址

#### 步骤2：创建API密钥
1. 登录SendGrid控制台
2. 进入"Settings" → "API Keys"
3. 点击"Create API Key"
4. 选择"Restricted Access"，至少赋予"Mail Send"权限
5. 复制生成的API密钥

#### 步骤3：配置Render环境变量
在Render控制台更新以下环境变量：

```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=你的SendGrid_API密钥
SMTP_FROM=你的已验证邮箱（如noreply@yourdomain.com）
SMTP_TIMEOUT=30
SMTP_TLS=true
SMTP_SSL=false
```

**注意：** `SMTP_USERNAME`必须为`apikey`（固定值）

#### 步骤4：在SendGrid验证发件人
1. 在SendGrid控制台进入"Settings" → "Sender Authentication"
2. 验证"Single Sender Verification"或"Domain Authentication"
3. 使用已验证的邮箱作为`SMTP_FROM`

### 方案3：使用Resend API（推荐，HTTP API方式）

Resend是现代化的邮件API服务，使用HTTP API而非SMTP，在云环境中更可靠，避免了SMTP连接问题。

#### 步骤1：注册Resend账户
1. 访问 [Resend官网](https://resend.com/)
2. 注册免费账户
3. 验证邮箱地址

#### 步骤2：创建API密钥
1. 登录Resend控制台
2. 进入"API Keys"页面
3. 点击"Create API Key"
4. 选择权限（邮件发送权限）
5. 复制生成的API密钥（以 `re_` 开头）

#### 步骤3：验证发件人域名或邮箱
1. 在Resend控制台进入"Domains"页面
2. 添加并验证你的域名（推荐）
3. 或者使用Resend提供的测试域名（如 `onboarding@resend.dev`）

#### 步骤4：配置Render环境变量
在Render控制台更新以下环境变量：

```
EMAIL_PROVIDER=resend
RESEND_API_KEY=你的Resend_API密钥（以re_开头）
RESEND_FROM=你的已验证邮箱（如noreply@yourdomain.com或onboarding@resend.dev）
```

**注意：** 使用Resend时不需要SMTP相关的环境变量。

#### 步骤5：重启服务
在Render控制台点击"Manual Deploy" → "Clear Cache and Deploy"

### 方案4：使用其他邮件服务

如果以上方案都不适用，考虑以下替代方案：

#### Mailgun
```
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=你的Mailgun_SMTP密码
```

#### AWS SES（需要AWS账户）
```
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=你的SES_SMTP用户名
SMTP_PASSWORD=你的SES_SMTP密码
```

## 诊断工具使用

### 使用测试脚本
项目提供了诊断脚本，帮助识别问题：

1. **本地测试**：
```bash
cd backend
# 设置环境变量或编辑脚本中的配置
python test_smtp_connection.py
```

2. **在Render环境测试**：
- 通过Render Shell运行测试
- 或临时添加测试端点到应用

### 检查应用日志
在Render控制台的"Logs"标签页查看应用日志，搜索以下关键词：
- "邮件发送成功"
- "发送邮件失败"
- "SMTP连接失败"
- "SMTP认证失败"

## 常见问题解决

### 问题1：SMTP连接超时
**症状**：连接长时间无响应
**解决方案**：
- 增加`SMTP_TIMEOUT`到60秒
- 检查防火墙规则
- 使用更可靠的邮件服务（如SendGrid）

### 问题2：认证失败
**症状**：`SMTPAuthenticationError`
**解决方案**：
- 确保使用正确的授权码/API密钥
- 检查用户名格式（QQ邮箱需完整邮箱地址）
- 验证邮件服务账户是否激活

### 问题3：Render网络限制
**症状**：连接被拒绝或超时
**解决方案**：
- Render免费层可能限制出站SMTP连接
- 升级到付费计划
- 使用Render官方集成的邮件服务（SendGrid）

### 问题4：邮件进入垃圾箱
**症状**：邮件发送成功但进入垃圾箱
**解决方案**：
- 配置SPF、DKIM、DMARC记录
- 使用专业邮件服务
- 避免垃圾邮件关键词

## 配置验证

### 验证配置是否正确
运行部署配置测试：
```bash
cd backend
python ../scripts/run_tests.py --deployment
```

### 检查邮件服务状态
手动调用API测试邮件发送：

```bash
# 使用curl测试（替换为你的Render域名）
curl -X POST https://otium.onrender.com/api/register/send-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "你的测试邮箱"}'
```

## 安全考虑

1. **不要将敏感信息提交到Git**：
   - `.env`文件应加入`.gitignore`
   - API密钥通过环境变量传递

2. **使用强密码/密钥**：
   - 定期轮换API密钥
   - 限制邮件服务权限

3. **监控邮件发送**：
   - 设置发送失败警报
   - 监控邮件服务配额

## 紧急解决方案

如果急需恢复邮件功能，可以：

### 临时禁用邮件验证
在Render环境变量中设置：
```
EMAIL_VERIFICATION_REQUIRED=false
```

这样用户注册时不需要邮箱验证，但会降低安全性。

### 使用控制台输出验证码
修改代码，将验证码输出到日志而不是发送邮件（仅限开发环境）。

## 联系支持

如果所有方案都失败：
1. 检查Render状态页面：https://status.render.com/
2. 联系Render支持
3. 创建GitHub Issue描述详细问题

## 最佳实践总结

1. **生产环境使用专业邮件服务**：SendGrid、Mailgun等
2. **配置正确的SPF/DKIM**：提高邮件送达率
3. **监控邮件发送指标**：成功率、退信率等
4. **设置备用邮件服务**：主服务故障时自动切换
5. **定期测试邮件功能**：确保始终可用

---
**最后更新**：2026-02-15
**适用版本**：Otium 1.0.0
**相关文件**：`backend/test_smtp_connection.py`, `backend/config.py`, `backend/services/email_service.py`