"""
邮件服务模块

提供邮件发送功能，包括验证码邮件和密码重置邮件。
支持SMTP协议，兼容SendGrid、Gmail等邮件服务。
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

from config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务类"""

    def __init__(self):
        """初始化邮件服务"""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.smtp_tls = settings.SMTP_TLS
        self.smtp_ssl = settings.SMTP_SSL

        # 前端URL用于重置密码链接
        self.frontend_base_url = settings.FRONTEND_BASE_URL

        logger.info(f"邮件服务初始化: {self.smtp_host}:{self.smtp_port}")

    def _get_logo_base64(self) -> str:
        """读取SVG logo文件，设置fill为黑色，返回base64编码

        Returns:
            str: base64编码的SVG数据
        """
        try:
            import os
            import re
            import base64

            # 前端logo文件路径（使用绝对路径）
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(base_dir, "frontend", "logopic.svg")

            logger.info(f"尝试读取logo文件: {logo_path}")

            # 检查文件是否存在
            if not os.path.exists(logo_path):
                logger.error(f"Logo文件不存在: {logo_path}")
                raise FileNotFoundError(f"Logo文件不存在: {logo_path}")

            # 读取SVG文件
            with open(logo_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()

            logger.info(f"成功读取SVG文件，大小: {len(svg_content)} 字符")

            # 检查SVG中是否有fill属性
            fill_matches = re.findall(r'fill=["\'](#?\w+)["\']', svg_content)
            logger.info(f"找到fill属性: {fill_matches}")

            # 将fill颜色替换为黑色 (#000000)
            # 更健壮的正则表达式，匹配各种fill颜色格式
            svg_content = re.sub(r'fill=["\']#?[a-fA-F0-9]{3,8}["\']', 'fill="#000000"', svg_content)

            # 再次检查替换后的fill属性
            fill_after = re.findall(r'fill=["\'](#?\w+)["\']', svg_content)
            logger.info(f"替换后fill属性: {fill_after}")

            # 将SVG内容转换为base64
            base64_data = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

            logger.info(f"成功生成base64数据，长度: {len(base64_data)}")

            # 返回data URL格式
            return f"data:image/svg+xml;base64,{base64_data}"

        except Exception as e:
            logger.error(f"读取logo文件失败，使用默认logo: {e}")
            # 返回默认的base64 logo（黑色填充版本）
            # 这里使用硬编码的base64数据，但已修改fill为黑色
            return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2ODQgNjc1IiBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJ4TWlkWU1pZCBtZWV0IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZlcnNpb249IjEuMSI+CiA8ZyBpZD0iTGF5ZXJfMSI+CiAgPHRpdGxlPkxheWVyIDE8L3RpdGxlPgogIDxwYXRoIGlkPSJzdmdfNCIgZD0ibTQ1MC4xNzYwMiw1MzcuNzU5MzFhMC4yLDAuMTkgLTU5LjUgMCAwIC0wLjM0LDAuMDlxLTguMTIsNDAuOCAtMjkuNDQsNzcuMjhxLTEzLjA5LDIyLjQgLTMwLjMzLDQzLjI1cS02LjA5LDcuMzcgLTE0LjA2LDExLjYzYy0zMi4yNywxNy4yNiAtNjQuOTMsLTQ3LjM4IC03NC43MywtNjguNDFjLTkuMjgsLTE5Ljk0IC0xNy41NiwtNDAuMTQgLTI0LjUxLC02MS4ycS0wLjc4LC0yLjM2IC0xLjI3LDAuMDhxLTYuOTQsMzQuNTEgLTIyLjk0LDY0LjEycS05LjMxLDE3LjIxIC0xOC42NiwzMi45NHEtNy40OCwxMi41OCAtMTUuNzEsMjEuNjFxLTMuNDIsMy43NSAtNy43Niw2LjY1Yy04LjczLDUuODQgLTIwLjEyLDQuNDIgLTI4LjgxLC0xLjIxYy00LjczLC0zLjA3IC05LjE1LC02Ljc1IC0xMi45NSwtMTAuOTFjLTE1LjMzLC0xNi43NyAtMjcuMzMsLTM4LjE3IC0zNy42LC01OC4zNGMtNy41NiwtMTQuODYgLTE1LjEyLC0zMC4xNSAtMjEuOTgsLTQ1LjQ4cS0xNC44OCwtMzMuMjUgLTI5LjcyLC02Ni4xNGMtMTIuMTcsLTI2Ljk2IC0yNS4xMSwtNTQuMTYgLTM5LjM5LC04MC42NHEtMTEuMTgsLTIwLjc1IC0yMy4zOCwtMzcuNjFxLTcuMywtMTAuMSAtMTAuMzQsLTE2LjM1cS0xNC4xNiwtMjkuMTIgMy43MywtNTkuNDNjNC4zMywtNy4zMyA4Ljk2LC0xNC4zNSAxMy45NCwtMjAuODRxMTMuOTksLTE4LjI5IDI2LjU1LC0zNS45N3E1LjcsLTguMDIgMTEuOTEsLTE2LjFxMjEuMSwtMjcuNDMgNDEuNzksLTUzLjk2cTIyLjg1LC0yOS4zMSAzMy44MiwtNDYuMTVxMTAuMzksLTE1Ljk0IDIxLjgsLTM1LjQ3cTYuODEsLTExLjY0IDExLjc5LC0yMi4xMWM3LjQ4LC0xNS43MiAxNi4zLC0yOS4yMSAzMC4zMSwtMzkuMXExNi4zOSwtMTEuNTkgMzYuMjgsLTEyLjc3YzMwLC0xLjc3IDU5Ljg1LDE1LjM3IDc2LjAxLDQwLjAyYTAuNzQsMC43NCAwIDAgMCAxLjIyLDAuMDNxMjQuNCwtMzMuNDggNjUuMzcsLTQ0LjE1cTguNDgsLTIuMjEgMTguMzcsLTIuODZxMzAuMzMsLTIuMDEgNTUuODcsMTEuNTZxMTUuMTEsOC4wMyAyNi4yOCwxOS4yNnEzLjc4LDMuNzkgNi40NCw4LjM4cTQ1LjU3LDc4LjczIDkxLjUyLDE1Ni43MnE1LjAyLDguNTEgMTAuMDcsMTcuMzRxNDMsNzUuMTggNzkuMDQsMTM1LjA3YzEwLjE3LDE2LjkxIDE2LjQ1LDM3Ljk1IDE1LjUzLDU3LjdjLTAuODgsMTguOCAtNS40NywzNi43NCAtMTEuNTYsNTUuMjlxLTIuODMsOC42IC03LjA4LDE4LjUzcS0xMC4xOCwyMy43NSAtMjAuODMsNDcuM3EtMTEuMDksMjQuNTMgLTIxLjM2LDQyLjI1cS05Ljk3LDE3LjIyIC0yMi4yLDM1LjkzYy0xMS4xMiwxNi45OSAtMjEuODIsMzQuMTQgLTM0LjgzLDUwLjM2Yy02LjMxLDcuODUgLTE0LjYyLDE2LjMyIC0yNC4zNSwxOC43OGMtMTEuNTIsMi45MiAtMjMuODgsLTQuNSAtMzIuMzIsLTEyLjgyYy0xMi41MSwtMTIuMzUgLTIyLjA0LC0yOC4zMSAtMjkuODksLTQ0LjM4Yy0xMi4yLC0yNC45OCAtMjEuNTEsLTUxLjU0IC0yOC43OCwtNzguNzZxLTAuMTUsLTAuNTYgLTAuNTIsLTEuMDF6bS0zODAuMDIsLTI2NC40OWMtOC43OCw4LjEyIC0xOC4yNCwxNi4zOSAtMjIuNTEsMjguMDdjLTUuMzUsMTQuNjMgLTQuMSwyOC4zOSAyLjMsNDIuMjNjNS44NSwxMi42NSAxMy4xNywyNC4wOCAyMC45LDM2LjI1YzE0Ljk1LDIzLjU1IDI5LjksNDguNjMgNDAuNTgsNjYuOTRjMTguNDgsMzEuNjYgMzMuOTMsNjEuNjIgNDkuNzQsOTIuNDhxNC40Nyw4LjczIDkuOTYsMTcuNTdjNC42Niw3LjUgMTAuNTYsMTUuMTQgMjAuMzQsMTMuMzZjMTMuMjcsLTIuNDEgMjMuODgsLTE5LjkgMjkuOTUsLTMwLjc5cTcuODEsLTE0LjAyIDEzLjgzLC0yNy4xNXEyNC45NCwtNTQuMzQgNDMuOTMsLTkzLjI2cTkuOTMsLTIwLjM1IDIyLjkzLC00NC4zNHE3LjUsLTEzLjgyIDE0LjYzLC0yNS42NHE4LjIyLC0xMy42MSAyMS4wOSwtMjUuM2MyNS43NSwtMjMuMzkgNTguNTEsLTI5LjcxIDkyLjU1LC0yNC45NGEwLjQ1LDAuNDUgMCAwIDAgMC40NiwtMC42N2MtMjQuNjEsLTQ0LjI2IC01MC44NCwtOTAuMjIgLTc2Ljc2LC0xMzYuNjFxLTQuNjQsLTguMzEgLTkuOSwtMTcuMzZxLTE3LjM0LC0yOS44NyAtMzQuMzEsLTYwLjQxYy0wLjczLC0xLjMzIC0xLjcxLC0yLjUzIC0yLjg3LC0zLjUxYy0yMC44MiwtMTcuNDUgLTUyLjU2LC0zNS40OSAtODAuMzcsLTIzLjUyYy0xNS45Miw2Ljg0IC0yNy4wNywyMS43MiAtMzYuNTQsMzcuMXEtNC42Miw3LjUxIC0xMC4wOCwxNy4ycS0xOC41NCwzMi44OSAtMzUuNTgsNjUuNjFxLTUuMTMsOS44NSAtOS41OCwxNy4zOXEtMjIuMjUsMzcuNjMgLTUzLjE3LDY4LjQ5cS0yLjIxLDIuMiAtMTEuNTIsMTAuODF6bTQ5NC4wNiwyNS42NHEyLjYyLC0wLjQgMS4zNiwtMi43M3EtMTMuODQsLTI1Ljc0IC0yNy4zOCwtNTAuMzlxLTQuNDgsLTguMTUgLTkuNDYsLTE3LjU5cS0xMi4yMSwtMjMuMTIgLTI7Ljk0LDk5LjE1YzcuMTgsMTIuNDggMTQuOTksMjUuMTkgMjEuODUsMzcuODRxNS4xMyw5LjQ4IDkuNjksMTcuNDlxMjQuMjIsNDIuNiA0OC40Miw4NC40NGEwLjM4LDAuMzggMCAwIDAgMC42NSwwLjAycTIwLjg4LC0zMS42OSA1Ny4zNCwtNDEuMzdjNS4yOCwtMS4zOSAxMC44NywtMS45MSAxNi4yOCwtMi43M3ptLTI4Ljk2LDI2Ny43OXExMi4wOCwtMTEuMzUgMjEuNSwtMjIuODRxNDAuMzEsLTQ5LjIzIDU3LjY5LC0xMDguODVxMi45OCwtMTAuMTkgNS43NiwtMjEuMzJxMi41MSwtMTAuMDQgMC45OCwtMTkuNDVjLTEuODksLTExLjYyIC04LjQsLTI0Ljc2IC0xOC4wNywtMzIuMTVjLTE4LjI4LC0xMy45NiAtNDIuMywtOS42MSAtNTcuODMsNS44NWMtMC45NiwwLjk3IC0xLjYsMi4xIC0yLjI4LDMuMjdjLTE4LjU5LDMxLjg2IC0zNy4xNCw2My4wMiAtNTUuOSw5NS4wMmMtMS45LDMuMjUgLTQuMDEsNi40MiAtNS42Miw5Ljc0YTEuOSwxLjg5IDQzLjEgMCAwIDAuMDYsMS43OWMxNC43NywyNS45IDI5LjQ1LDUzLjA3IDQ0Ljc1LDc3LjU5YzIuNTcsNC4xMiA0LjEsOC4zNyA4LjAzLDExLjRhMC43MywwLjcxIC00Ny42IDAgMCAwLjkzLC0wLjA1em0tMTc0LjM1LC0xLjc5YTAuNTMsMC41MyAwIDAgMCAwLjc5LDAuMDNjMS42OSwtMS43NyAzLjYzLC0zLjIgNS4zNywtNC45OXExNywtMTcuNTggMzEuMTMsLTM5LjA1YzE5LjI3LC0yOS4yNiAzNC4wOCwtNjAuMzkgNDMuOTEsLTkzLjE3YzEuMTMsLTMuNzQgMy40NSwtNy4xMiA1LjAyLC0xMC43NHE3LjU0LC0xNy40NiAtMC41LC0zNS4yNmMtOS42MiwtMjEuMzMgLTMxLjksLTMyLjU4IC01NC44MSwtMjUuMzFjLTYuMzIsMiAtMTYuOTcsNi41NyAtMjAuNDIsMTIuNjdjLTguMDIsMTQuMTYgLTIxLjEzLDM3Ljk3IC0zMi43LDU4LjIzcS0xMS44MywyMC43MSAtMjMuMjUsNDEuNjVjLTEuNjIsMi45OCAtMy41Miw1LjgxIC00LjkzLDguODdxLTAuMjYsMC41NyAwLjA0LDEuMWMxLjg1LDMuMjYgMy45Nyw2LjQ0IDUuOCw5Ljc1cTE3LjAzLDMwLjY5IDM0Ljk2LDYwLjI0YzEuODcsMy4wOCA0LjA0LDUuNzMgNS40Myw5LjA2cTEuNTcsMy43OCA0LjIsNi45MnoiIGZpbGw9IiNGRkZGRkYiLz4KIDwvZz4KPC9zdmc+"

    def _create_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """创建SMTP连接"""
        try:
            if self.smtp_ssl:
                # SSL连接
                smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                # 普通连接
                smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.smtp_tls and not self.smtp_ssl:
                # STARTTLS加密
                smtp.starttls()

            # 登录
            if self.smtp_username and self.smtp_password:
                smtp.login(self.smtp_username, self.smtp_password)

            return smtp

        except Exception as e:
            logger.error(f"创建SMTP连接失败: {e}")
            return None

    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """发送邮件（内部方法）"""
        if not self.smtp_password:
            logger.warning("SMTP密码未配置，邮件发送功能不可用")
            return False

        smtp = self._create_smtp_connection()
        if not smtp:
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email

            # 添加纯文本版本
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)

            # 添加HTML版本
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 发送邮件
            smtp.send_message(msg)
            logger.info(f"邮件发送成功: {to_email}, 主题: {subject}")
            return True

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

        finally:
            try:
                smtp.quit()
            except:
                pass

    def send_verification_code(self, email: str, code: str) -> bool:
        """发送验证码邮件

        Args:
            email: 收件人邮箱
            code: 6位验证码

        Returns:
            bool: 是否发送成功
        """
        subject = f"Otium验证码：{code}"

        # HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #333333; color: white; padding: 20px; text-align: center; border-radius: 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0; }}
                .code {{ font-size: 32px; font-weight: bold; color: #333333; text-align: center; margin: 30px 0; padding: 15px; background-color: #f0f0f0; border-radius: 0; letter-spacing: 5px; }}
                .note {{ font-size: 14px; color: #666; margin-top: 20px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #999; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="font-size: 28px; font-weight: bold; color: white; margin: 0; padding: 10px 0;">Otium - 专业的学术文本处理平台</h1>
                </div>
                <div class="content">
                    <h2>邮箱验证码</h2>
                    <p>您好，您正在注册Otium账户，请输入以下验证码完成邮箱验证：</p>

                    <div class="code">{code}</div>

                    <p>验证码有效期10分钟，请尽快使用。</p>

                    <div class="note">
                        <p><strong>注意：</strong></p>
                        <p>• 如果您没有注册Otium账户，请忽略此邮件</p>
                        <p>• 请勿将验证码分享给他人</p>
                        <p>• 此验证码仅用于邮箱验证，不会用于其他用途</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} Otium学术文本处理平台. 保留所有权利.</p>
                    <p>此邮件为系统自动发送，请勿回复</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 纯文本内容
        text_content = f"""
        Otium学术文本处理平台 - 邮箱验证码

        您好，您正在注册Otium账户，请输入以下验证码完成邮箱验证：

        验证码：{code}

        验证码有效期10分钟，请尽快使用。

        注意：
        • 如果您没有注册Otium账户，请忽略此邮件
        • 请勿将验证码分享给他人
        • 此验证码仅用于邮箱验证，不会用于其他用途

        © {datetime.now().year} Otium学术文本处理平台. 保留所有权利.
        此邮件为系统自动发送，请勿回复
        """

        return self._send_email(email, subject, html_content, text_content)

    def send_password_reset_link(self, email: str, reset_token: str) -> bool:
        """发送密码重置链接邮件

        Args:
            email: 收件人邮箱
            reset_token: 重置令牌

        Returns:
            bool: 是否发送成功
        """
        reset_url = f"{self.frontend_base_url}/reset-password/{reset_token}"
        subject = "Otium密码重置"

        # HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #333333; color: white; padding: 20px; text-align: center; border-radius: 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0; }}
                .button {{ display: inline-block; background-color: #333333; color: white; padding: 12px 24px; text-decoration: none; border-radius: 0; font-weight: bold; margin: 20px 0; }}
                .button:hover {{ background-color: #000000; }}
                .url {{ font-family: monospace; background-color: #f0f0f0; padding: 10px; border-radius: 0; word-break: break-all; margin: 20px 0; }}
                .note {{ font-size: 14px; color: #666; margin-top: 20px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #999; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="font-size: 28px; font-weight: bold; color: white; margin: 0; padding: 10px 0;">Otium - 专业的学术文本处理平台</h1>
                </div>
                <div class="content">
                    <h2>重置密码</h2>
                    <p>您好，我们收到了您重置Otium账户密码的请求。</p>

                    <p>请点击以下按钮重置密码：</p>

                    <p>
                        <a href="{reset_url}" class="button">重置密码</a>
                    </p>

                    <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>

                    <div class="url">{reset_url}</div>

                    <p>此链接24小时内有效，过期后需要重新申请。</p>

                    <div class="note">
                        <p><strong>注意：</strong></p>
                        <p>• 如果您没有申请重置密码，请忽略此邮件</p>
                        <p>• 请勿将此链接分享给他人</p>
                        <p>• 重置链接只能使用一次</p>
                    </div>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} Otium学术文本处理平台. 保留所有权利.</p>
                    <p>此邮件为系统自动发送，请勿回复</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 纯文本内容
        text_content = f"""
        Otium学术文本处理平台 - 重置密码

        您好，我们收到了您重置Otium账户密码的请求。

        请点击以下链接重置密码：
        {reset_url}

        此链接24小时内有效，过期后需要重新申请。

        注意：
        • 如果您没有申请重置密码，请忽略此邮件
        • 请勿将此链接分享给他人
        • 重置链接只能使用一次

        © {datetime.now().year} Otium学术文本处理平台. 保留所有权利.
        此邮件为系统自动发送，请勿回复
        """

        return self._send_email(email, subject, html_content, text_content)

    def send_welcome_email(self, email: str, username: str) -> bool:
        """发送欢迎邮件（注册成功）

        Args:
            email: 收件人邮箱
            username: 用户名

        Returns:
            bool: 是否发送成功
        """
        subject = "欢迎加入Otium学术文本处理平台"

        # HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #333333; color: white; padding: 20px; text-align: center; border-radius: 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0; }}
                .welcome {{ font-size: 24px; color: #333333; text-align: center; margin: 20px 0; }}
                .features {{ margin: 30px 0; }}
                .feature {{ display: flex; align-items: center; margin-bottom: 15px; }}
                .feature-icon {{ background-color: #333333; color: white; width: 30px; height: 30px; border-radius: 0; display: flex; align-items: center; justify-content: center; margin-right: 15px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #999; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="font-size: 28px; font-weight: bold; color: white; margin: 0; padding: 10px 0;">Otium - 专业的学术文本处理平台</h1>
                </div>
                <div class="content">
                    <div class="welcome">欢迎加入Otium！</div>

                    <p>您好 <strong>{username}</strong>，</p>

                    <p>感谢您注册Otium学术文本处理平台！您的账户已成功创建，邮箱已验证。</p>

                    <div class="features">
                        <h3>开始使用以下功能：</h3>

                        <div class="feature">
                            <div class="feature-icon">✓</div>
                            <div><strong>文本纠错</strong> - 识别原文语法、拼写和标点错误</div>
                        </div>

                        <div class="feature">
                            <div class="feature-icon">✓</div>
                            <div><strong>学术翻译</strong> - 论文标准的去AI化中英文翻译</div>
                        </div>

                        <div class="feature">
                            <div class="feature-icon">✓</div>
                            <div><strong>文本修改</strong> - 内置详细的语法规则降低AI率</div>
                        </div>

                        <div class="feature">
                            <div class="feature-icon">✓</div>
                            <div><strong>AI内容检测</strong> - 即时检测并识别AI生成内容</div>
                        </div>
                    </div>

                    <p>立即登录开始使用：</p>
                    <p><a href="{self.frontend_base_url}" style="color: #333333; font-weight: bold;">{self.frontend_base_url}</a></p>

                    <p>如果您有任何问题或建议，请随时联系我们。</p>

                    <p>祝您使用愉快！</p>
                    <p>Otium团队</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} Otium学术文本处理平台. 保留所有权利.</p>
                    <p>此邮件为系统自动发送，请勿回复</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 纯文本内容
        text_content = f"""
        Otium学术文本处理平台 - 欢迎加入

        您好 {username}，

        感谢您注册Otium学术文本处理平台！您的账户已成功创建，邮箱已验证。

        开始使用以下功能：
        • 文本纠错 - 识别原文语法、拼写和标点错误
        • 学术翻译 - 论文标准的去AI化中英文翻译
        • 文本修改 - 内置详细的语法规则降低AI率
        • AI内容检测 - 即时检测并识别AI生成内容

        立即登录开始使用：
        {self.frontend_base_url}

        如果您有任何问题或建议，请随时联系我们。

        祝您使用愉快！
        Otium团队

        © {datetime.now().year} Otium学术文本处理平台. 保留所有权利.
        此邮件为系统自动发送，请勿回复
        """

        return self._send_email(email, subject, html_content, text_content)


# 全局邮件服务实例
email_service = EmailService()