#!/usr/bin/env python3
"""
SMTP连接测试脚本

用于诊断邮件服务SMTP连接问题，特别是在Render部署环境中的问题。
测试QQ邮箱SMTP连接是否正常工作。

使用方法：
1. 在本地测试：python test_smtp_connection.py
2. 在Render环境测试：设置好环境变量后运行
"""

import logging
import os
import smtplib
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_smtp_connection():
    """测试SMTP连接"""
    print("\n" + "=" * 70)
    print("SMTP连接测试")
    print("=" * 70)

    # 从环境变量读取配置
    smtp_host = os.environ.get("SMTP_HOST", "smtp.qq.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_username = os.environ.get("SMTP_USERNAME", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    smtp_from = os.environ.get("SMTP_FROM", "")
    smtp_timeout = int(os.environ.get("SMTP_TIMEOUT", "30"))
    smtp_ssl = os.environ.get("SMTP_SSL", "true").lower() in ("true", "1", "yes")
    smtp_tls = os.environ.get("SMTP_TLS", "false").lower() in ("true", "1", "yes")

    # 显示当前配置（隐藏密码）
    print("\n当前SMTP配置:")
    print(f"  SMTP_HOST: {smtp_host}")
    print(f"  SMTP_PORT: {smtp_port}")
    print(f"  SMTP_USERNAME: {smtp_username}")
    print(f"  SMTP_PASSWORD: {'*' * len(smtp_password) if smtp_password else '未设置'}")
    print(f"  SMTP_FROM: {smtp_from}")
    print(f"  SMTP_TIMEOUT: {smtp_timeout}秒")
    print(f"  SMTP_SSL: {smtp_ssl}")
    print(f"  SMTP_TLS: {smtp_tls}")

    # 检查必要配置
    if not smtp_host:
        print("\n[错误] SMTP_HOST 未设置")
        return False

    if not smtp_username:
        print("\n[错误] SMTP_USERNAME 未设置")
        return False

    if not smtp_password:
        print("\n[错误] SMTP_PASSWORD 未设置")
        return False

    if not smtp_from:
        print("\n[警告] SMTP_FROM 未设置，将使用SMTP_USERNAME")
        smtp_from = smtp_username

    print("\n" + "-" * 70)
    print("测试1: 基础连接测试")
    print("-" * 70)

    smtp = None
    try:
        if smtp_ssl:
            print(f"尝试SSL连接: {smtp_host}:{smtp_port} (超时: {smtp_timeout}秒)")
            smtp = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=smtp_timeout)
            print("[成功] SSL连接建立")
        else:
            print(f"尝试普通连接: {smtp_host}:{smtp_port} (超时: {smtp_timeout}秒)")
            smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout)
            print("[成功] 普通连接建立")

            if smtp_tls:
                print("尝试STARTTLS加密...")
                smtp.starttls()
                print("[成功] STARTTLS加密启用")

        # 测试登录
        print(f"尝试登录: {smtp_username}")
        smtp.login(smtp_username, smtp_password)
        print("[成功] 登录成功")

        print("\n" + "-" * 70)
        print("测试2: 发送测试邮件")
        print("-" * 70)

        # 创建测试邮件
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        test_subject = f"Otium SMTP测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        test_body = f"""
        这是一封测试邮件，用于验证Otium应用的邮件服务配置。

        发送时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        SMTP服务器: {smtp_host}:{smtp_port}
        发件人: {smtp_from}

        如果收到此邮件，说明邮件服务配置正确。
        """

        # 发送给自己
        msg = MIMEMultipart("alternative")
        msg["Subject"] = test_subject
        msg["From"] = smtp_from
        msg["To"] = smtp_from  # 发送给自己

        text_part = MIMEText(test_body, "plain", "utf-8")
        msg.attach(text_part)

        print(f"发送测试邮件到: {smtp_from}")
        smtp.send_message(msg)
        print("[成功] 测试邮件发送完成")

        print("\n" + "-" * 70)
        print("测试总结")
        print("-" * 70)
        print("[成功] 所有SMTP测试通过！")
        print(f"  • 成功连接到 {smtp_host}:{smtp_port}")
        print(f"  • 成功登录账号 {smtp_username}")
        print(f"  • 成功发送测试邮件到 {smtp_from}")
        print("\n建议: 请检查您的邮箱（包括垃圾邮件文件夹）是否收到测试邮件。")

        return True

    except smtplib.SMTPConnectError as e:
        print(f"[错误] SMTP连接失败: {e}")
        print("可能原因:")
        print("  1. SMTP服务器地址或端口错误")
        print("  2. 网络连接问题")
        print("  3. 防火墙阻止了连接")
        print("  4. Render环境可能阻止出站SMTP连接")
        return False

    except smtplib.SMTPAuthenticationError as e:
        print(f"[错误] SMTP认证失败: {e}")
        print("可能原因:")
        print("  1. 用户名或密码错误")
        print("  2. QQ邮箱需要授权码而非登录密码")
        print("  3. 邮箱未开启SMTP服务")
        return False

    except smtplib.SMTPSenderRefused as e:
        print(f"[错误] 发件人被拒绝: {e}")
        print("可能原因:")
        print("  1. SMTP_FROM地址与登录账号不匹配")
        print("  2. 邮箱服务器限制")
        return False

    except smtplib.SMTPRecipientsRefused as e:
        print(f"[错误] 收件人被拒绝: {e}")
        print("可能原因:")
        print("  1. 收件人邮箱地址无效")
        print("  2. 邮箱服务器限制")
        return False

    except smtplib.SMTPDataError as e:
        print(f"[错误] 邮件数据错误: {e}")
        print("可能原因:")
        print("  1. 邮件内容格式问题")
        print("  2. 邮箱服务器限制")
        return False

    except smtplib.SMTPException as e:
        print(f"[错误] SMTP通用错误: {e}")
        return False

    except TimeoutError as e:
        print(f"[错误] 连接超时: {e}")
        print("可能原因:")
        print("  1. SMTP服务器响应缓慢")
        print("  2. 网络延迟")
        print("  3. SMTP_TIMEOUT设置过短")
        return False

    except Exception as e:
        print(f"[错误] 未知错误: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if smtp:
            try:
                smtp.quit()
                print("[信息] 已关闭SMTP连接")
            except Exception:
                pass


def check_render_environment():
    """检查Render环境配置"""
    print("\n" + "=" * 70)
    print("Render环境检查")
    print("=" * 70)

    is_render = os.environ.get("RENDER", "").lower() == "true"
    print(f"是否在Render环境: {is_render}")

    # 检查关键环境变量
    required_vars = [
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM",
        "SMTP_TIMEOUT",
    ]

    print("\n环境变量检查:")
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # 隐藏密码显示
            if "PASSWORD" in var:
                display_value = "*" * len(value)
            else:
                display_value = value
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: 未设置")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n[警告] 缺少{len(missing_vars)}个必需环境变量: {', '.join(missing_vars)}")
        print("\n在Render面板中设置环境变量的步骤:")
        print("1. 登录Render控制台 (https://dashboard.render.com/)")
        print("2. 选择你的Otium服务")
        print("3. 点击左侧的'Environment'标签")
        print("4. 添加或修改以下环境变量:")
        print("   - SMTP_HOST: smtp.qq.com")
        print("   - SMTP_PORT: 465")
        print("   - SMTP_USERNAME: 你的QQ邮箱（如123456789@qq.com）")
        print("   - SMTP_PASSWORD: QQ邮箱授权码（不是登录密码）")
        print("   - SMTP_FROM: 发件人邮箱（与SMTP_USERNAME相同）")
        print("   - SMTP_TIMEOUT: 30")
        print("   - SMTP_SSL: true")
        print("   - SMTP_TLS: false")
        return False
    else:
        print("\n[成功] 所有必需环境变量已设置")
        return True


def qq_email_specific_checks():
    """QQ邮箱特定检查"""
    print("\n" + "=" * 70)
    print("QQ邮箱配置检查")
    print("=" * 70)

    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = os.environ.get("SMTP_PORT", "")
    smtp_username = os.environ.get("SMTP_USERNAME", "")

    issues = []

    # 检查主机名
    if smtp_host and "qq.com" not in smtp_host.lower():
        issues.append(f"SMTP_HOST应为QQ邮箱服务器 (smtp.qq.com)，当前为: {smtp_host}")

    # 检查端口
    if smtp_port and smtp_port not in ["465", "587"]:
        issues.append(f"QQ邮箱SMTP端口应为465(SSL)或587(TLS)，当前为: {smtp_port}")

    # 检查用户名格式
    if smtp_username and not smtp_username.endswith("@qq.com"):
        issues.append(f"QQ邮箱用户名应以@qq.com结尾，当前为: {smtp_username}")

    # QQ邮箱SMTP服务启用说明
    print("\nQQ邮箱SMTP服务启用步骤:")
    print("1. 登录QQ邮箱网页版")
    print("2. 点击'设置' → '账户'")
    print("3. 找到'POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务'")
    print("4. 开启'POP3/SMTP服务'或'IMAP/SMTP服务'")
    print("5. 生成授权码（16位字符串，不是邮箱密码）")
    print("6. 使用授权码作为SMTP_PASSWORD")

    if issues:
        print("\n[问题] 发现配置问题:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("\n[成功] QQ邮箱配置检查通过")
        return True


def main():
    """主函数"""
    print("=" * 70)
    print("Otium 邮件服务诊断工具")
    print("=" * 70)

    # 检查Render环境
    if not check_render_environment():
        print("\n[警告] 环境变量不完整，SMTP测试可能失败")
        response = input("\n是否继续测试SMTP连接? (y/n): ")
        if response.lower() != "y":
            return

    # QQ邮箱特定检查
    qq_email_specific_checks()

    # 测试SMTP连接
    success = test_smtp_connection()

    # 总结
    print("\n" + "=" * 70)
    print("诊断总结")
    print("=" * 70)

    if success:
        print("[成功] 邮件服务配置正确")
        print("\n下一步:")
        print("1. 检查您的QQ邮箱是否收到测试邮件")
        print("2. 如果没有收到，请检查垃圾邮件文件夹")
        print("3. 如果问题仍然存在，可能是Render网络限制")
    else:
        print("[失败] 邮件服务配置有问题")
        print("\n常见问题解决方案:")
        print("1. 确保QQ邮箱已开启SMTP服务")
        print("2. 确保使用授权码而不是登录密码")
        print("3. 检查Render环境变量是否正确设置")
        print("4. Render可能阻止出站SMTP连接，考虑使用:")
        print("   - SendGrid (推荐，与Render集成更好)")
        print("   - Mailgun")
        print("   - AWS SES")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n[错误] 测试过程中发生异常: {e}")
        import traceback

        traceback.print_exc()
