#!/usr/bin/env python3
"""
网络连接诊断工具
检查代理设置、API连接和端口占用情况

注意事项：
- Windows编码兼容性：避免使用Unicode字符（✓✗⚠），使用[成功]、[失败]、[警告]标记
- 安全考虑：不包含敏感信息，避免泄露API密钥
"""

import os
import sys
import json
import socket
import requests
import subprocess
import platform
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def safe_print(message: str) -> None:
    """安全打印函数，处理Windows控制台编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 如果遇到编码问题，使用ASCII安全版本
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)


def check_proxy_settings() -> Dict[str, Optional[str]]:
    """检查所有可能的代理环境变量"""
    safe_print("=" * 60)
    safe_print("检查代理环境变量")
    safe_print("=" * 60)

    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY',
        'http_proxy', 'https_proxy', 'no_proxy',
        'ALL_PROXY', 'all_proxy',
        'FTP_PROXY', 'ftp_proxy'
    ]

    proxy_settings = {}
    has_proxy = False

    for var in proxy_vars:
        value = os.environ.get(var)
        proxy_settings[var] = value
        if value:
            has_proxy = True
            safe_print(f"[警告] 检测到代理设置: {var}={value}")

    if not has_proxy:
        safe_print("[成功] 未检测到代理设置")

    safe_print("")
    return proxy_settings


def check_npm_proxy() -> Dict[str, Optional[str]]:
    """检查npm代理配置"""
    safe_print("=" * 60)
    safe_print("检查npm代理配置")
    safe_print("=" * 60)

    npm_configs = {}
    npm_commands = [
        ('proxy', 'npm config get proxy'),
        ('https-proxy', 'npm config get https-proxy'),
        ('noproxy', 'npm config get noproxy'),
        ('registry', 'npm config get registry')
    ]

    try:
        for name, cmd in npm_commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            value = result.stdout.strip()
            npm_configs[name] = value if value and value != 'null' else None

            if value and value != 'null':
                safe_print(f"[警告] 检测到npm配置 {name}: {value}")
    except Exception as e:
        safe_print(f"[错误] 检查npm配置时出错: {e}")

    if not any(npm_configs.values()):
        safe_print("[成功] 未检测到npm代理配置")

    safe_print("")
    return npm_configs


def check_backend_connection(url: str = "http://localhost:8000/api/health", timeout: int = 5) -> Tuple[bool, Optional[Dict]]:
    """检查后端API连接"""
    safe_print("=" * 60)
    safe_print("检查后端API连接")
    safe_print("=" * 60)
    safe_print(f"测试URL: {url}")

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            safe_print("[成功] 后端服务运行正常")
            try:
                data = response.json()
                safe_print(f"健康检查响应: {json.dumps(data, ensure_ascii=False)}")
                return True, data
            except:
                safe_print(f"健康检查响应(原始文本): {response.text}")
                return True, {"text": response.text}
        else:
            safe_print(f"[失败] 后端服务返回状态码: {response.status_code}")
            safe_print(f"响应内容: {response.text}")
            return False, {"status_code": response.status_code, "text": response.text}
    except requests.exceptions.ConnectionError:
        safe_print("[失败] 无法连接到后端服务")
        safe_print("可能原因: 1) 后端服务未启动 2) 端口错误 3) 防火墙阻止")
        return False, None
    except requests.exceptions.Timeout:
        safe_print("[失败] 连接超时")
        return False, None
    except Exception as e:
        safe_print(f"[失败] 连接时发生错误: {e}")
        return False, None

    safe_print("")


def check_frontend_connection(url: str = "http://localhost:3000", timeout: int = 5) -> bool:
    """检查前端开发服务器连接"""
    safe_print("=" * 60)
    safe_print("检查前端开发服务器连接")
    safe_print("=" * 60)
    safe_print(f"测试URL: {url}")

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code < 400:
            safe_print("[成功] 前端开发服务器运行正常")
            return True
        else:
            safe_print(f"[警告] 前端服务器返回状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        safe_print("[警告] 无法连接到前端开发服务器")
        safe_print("提示: 前端开发服务器可能未启动，这在仅测试后端时是正常的")
        return False
    except Exception as e:
        safe_print(f"[警告] 连接前端时发生错误: {e}")
        return False

    safe_print("")


def check_port_usage(ports: List[int] = [8000, 8001, 3000, 3001]) -> Dict[int, bool]:
    """检查端口占用情况"""
    safe_print("=" * 60)
    safe_print("检查端口占用情况")
    safe_print("=" * 60)

    port_status = {}
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            is_in_use = result == 0
            port_status[port] = is_in_use

            if is_in_use:
                safe_print(f"[警告] 端口 {port} 已被占用")
            else:
                safe_print(f"[成功] 端口 {port} 可用")
        except Exception as e:
            safe_print(f"[错误] 检查端口 {port} 时出错: {e}")
            port_status[port] = None

    safe_print("")
    return port_status


def check_environment_configs() -> Dict[str, str]:
    """检查关键环境配置"""
    safe_print("=" * 60)
    safe_print("检查环境配置")
    safe_print("=" * 60)

    configs = {}
    env_vars_to_check = [
        'REACT_APP_API_BASE_URL',
        'GEMINI_API_KEY',
        'GPTZERO_API_KEY',
        'DATABASE_TYPE',
        'CORS_ORIGINS',
        'EMAIL_PROVIDER'
    ]

    for var in env_vars_to_check:
        value = os.environ.get(var)
        configs[var] = value

        if var == 'GEMINI_API_KEY' or var == 'GPTZERO_API_KEY':
            # 安全地显示API密钥（仅显示是否存在）
            if value:
                masked = value[:4] + "***" + value[-4:] if len(value) > 8 else "***"
                safe_print(f"[信息] {var}: {masked}")
            else:
                safe_print(f"[警告] {var}: 未设置")
        elif var == 'REACT_APP_API_BASE_URL':
            if value:
                safe_print(f"[信息] {var}: {value}")
                if '8001' in value:
                    safe_print(f"[警告] 前端API基础URL包含8001端口，建议使用8000端口")
            else:
                safe_print(f"[警告] {var}: 未设置，前端将使用默认值")
        else:
            if value:
                safe_print(f"[信息] {var}: {value}")
            else:
                safe_print(f"[信息] {var}: 未设置（使用默认值）")

    safe_print("")
    return configs


def generate_summary_report(
    proxy_settings: Dict[str, Optional[str]],
    npm_configs: Dict[str, Optional[str]],
    backend_ok: bool,
    frontend_ok: bool,
    port_status: Dict[int, bool],
    configs: Dict[str, str]
) -> None:
    """生成诊断报告摘要"""
    safe_print("=" * 60)
    safe_print("诊断报告摘要")
    safe_print("=" * 60)

    # 代理状态
    has_proxy = any(proxy_settings.values())
    has_npm_proxy = any(v for v in npm_configs.values() if v)

    # 问题计数
    issues = []
    recommendations = []

    if has_proxy:
        issues.append("检测到系统代理设置")
        recommendations.append("如非必要，请清除HTTP_PROXY/HTTPS_PROXY环境变量")

    if has_npm_proxy:
        issues.append("检测到npm代理配置")
        recommendations.append("检查npm配置: npm config get proxy / npm config get https-proxy")

    if not backend_ok:
        issues.append("后端服务连接失败")
        recommendations.append("1. 确保后端服务已启动 (uvicorn main:app --reload)")
        recommendations.append("2. 检查端口8000是否被占用")
        recommendations.append("3. 检查防火墙设置")

    if 'REACT_APP_API_BASE_URL' in configs and configs['REACT_APP_API_BASE_URL']:
        if '8001' in configs['REACT_APP_API_BASE_URL']:
            issues.append("前端API基础URL配置使用8001端口")
            recommendations.append("修改REACT_APP_API_BASE_URL为http://localhost:8000")

    # 检查关键API密钥
    if not configs.get('GEMINI_API_KEY'):
        issues.append("GEMINI_API_KEY未设置")
        recommendations.append("设置GEMINI_API_KEY环境变量以使用AI功能")

    if not configs.get('GPTZERO_API_KEY'):
        issues.append("GPTZERO_API_KEY未设置")
        recommendations.append("设置GPTZERO_API_KEY环境变量以使用AI检测功能")

    # 显示摘要
    if not issues:
        safe_print("[成功] 未检测到严重问题")
        safe_print("建议: 可以正常进行开发")
    else:
        safe_print(f"[警告] 检测到 {len(issues)} 个潜在问题:")
        for i, issue in enumerate(issues, 1):
            safe_print(f"  {i}. {issue}")

        safe_print("\n建议操作:")
        for i, rec in enumerate(recommendations, 1):
            safe_print(f"  {i}. {rec}")

    # 显示基本连接状态
    safe_print(f"\n后端连接: {'[成功]' if backend_ok else '[失败]'}")
    safe_print(f"前端连接: {'[成功]' if frontend_ok else '[警告]'}")

    # 端口状态
    used_ports = [port for port, in_use in port_status.items() if in_use]
    if used_ports:
        safe_print(f"已占用端口: {used_ports}")

    safe_print("")


def main():
    """主函数"""
    safe_print("Otium项目网络诊断工具")
    safe_print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print(f"系统平台: {platform.platform()}")
    safe_print("")

    # 执行所有检查
    proxy_settings = check_proxy_settings()
    npm_configs = check_npm_proxy()
    backend_ok, backend_data = check_backend_connection()
    frontend_ok = check_frontend_connection()
    port_status = check_port_usage()
    configs = check_environment_configs()

    # 生成报告
    generate_summary_report(
        proxy_settings, npm_configs, backend_ok,
        frontend_ok, port_status, configs
    )

    # 返回退出码
    if not backend_ok:
        safe_print("[错误] 后端连接失败，请检查问题并重试")
        sys.exit(1)
    else:
        safe_print("[成功] 诊断完成")
        sys.exit(0)


if __name__ == "__main__":
    main()