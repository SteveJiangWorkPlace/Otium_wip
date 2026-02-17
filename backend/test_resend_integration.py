#!/usr/bin/env python3
"""
Resend API集成测试脚本

用于测试Resend API邮件服务配置是否正确。
使用方法：
1. 设置环境变量：
   - EMAIL_PROVIDER=resend
   - RESEND_API_KEY=你的Resend_API密钥
   - RESEND_FROM=发件人邮箱
2. 运行：python test_resend_integration.py
"""

import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_resend_config():
    """测试Resend配置"""
    print("\n" + "=" * 70)
    print("Resend API集成测试")
    print("=" * 70)

    # 检查环境变量
    email_provider = os.environ.get("EMAIL_PROVIDER", "")
    resend_api_key = os.environ.get("RESEND_API_KEY", "")
    resend_from = os.environ.get("RESEND_FROM", "")

    print("\n当前Resend配置:")
    print(f"  EMAIL_PROVIDER: {email_provider}")
    print(f"  RESEND_API_KEY: {'*' * len(resend_api_key) if resend_api_key else '未设置'}")
    print(f"  RESEND_FROM: {resend_from}")

    # 检查配置
    if email_provider != "resend":
        print(f"\n[错误] EMAIL_PROVIDER应为'resend'，当前为: {email_provider}")
        return False

    if not resend_api_key:
        print("\n[错误] RESEND_API_KEY 未设置")
        return False

    if not resend_from:
        print("\n[警告] RESEND_FROM 未设置，使用默认值: onboarding@resend.dev")
        resend_from = "onboarding@resend.dev"

    if not resend_api_key.startswith("re_"):
        print("\n[警告] RESEND_API_KEY 通常以 're_' 开头，请确保使用正确的API密钥")

    print("\n[OK] Resend基础配置检查通过")

    # 尝试导入Resend库
    try:
        import resend

        print("[OK] resend库导入成功")
    except ImportError as e:
        print(f"[错误] 无法导入resend库: {e}")
        print("请安装resend: pip install resend>=1.0.0")
        return False

    # 测试发送邮件（可选）
    test_send = input("\n是否发送测试邮件? (y/n): ").lower()
    if test_send == "y":
        return test_resend_send_email(resend_api_key, resend_from)

    return True


def test_resend_send_email(api_key: str, from_email: str):
    """测试发送邮件"""
    try:
        import resend

        resend.api_key = api_key

        # 发送测试邮件到发件人自己
        test_to = from_email
        test_subject = "Resend API测试邮件"
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #333333; color: white; padding: 20px; text-align: center; }
                .content { background-color: #f9f9f9; padding: 30px; }
                .footer { margin-top: 30px; font-size: 12px; color: #999; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Resend API测试</h1>
                </div>
                <div class="content">
                    <p>这是一封测试邮件，用于验证Resend API配置是否正确。</p>
                    <p>如果您收到此邮件，说明Resend API集成成功！</p>
                </div>
                <div class="footer">
                    <p>© 2026 Otium学术文本处理平台. 保留所有权利.</p>
                </div>
            </div>
        </body>
        </html>
        """

        params = {"from": from_email, "to": test_to, "subject": test_subject, "html": test_html}

        print(f"\n发送测试邮件到: {test_to}")
        print(f"主题: {test_subject}")

        response = resend.Emails.send(params)
        print(f"[成功] 邮件发送成功! 响应ID: {response.get('id', 'N/A')}")
        print("\n请注意：邮件可能需要几秒钟才能到达收件箱。")
        print("如果未收到，请检查垃圾邮件文件夹。")
        return True

    except Exception as e:
        print(f"[错误] 发送测试邮件失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("Otium Resend API集成测试工具")
    print("=" * 70)

    try:
        success = test_resend_config()

        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)

        if success:
            print("[成功] Resend API配置测试通过")
            print("\n下一步:")
            print("1. 检查Render环境变量是否正确设置")
            print("2. 在Render控制台重启服务")
            print("3. 测试注册功能是否正常工作")
        else:
            print("[失败] Resend API配置测试未通过")
            print("\n解决方案:")
            print("1. 确保已安装resend库: pip install resend>=1.0.0")
            print("2. 检查RESEND_API_KEY是否正确")
            print("3. 确保RESEND_FROM邮箱已在Resend验证")
            print("4. 检查网络连接（Resend API需要外网访问）")

        print("\n" + "=" * 70)

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n[错误] 测试过程中发生异常: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
