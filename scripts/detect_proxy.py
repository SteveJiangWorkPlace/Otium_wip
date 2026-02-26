#!/usr/bin/env python3
"""
代理环境检测工具
检测所有可能的代理设置位置，提供清理建议

注意事项：
- Windows编码兼容性：避免使用Unicode字符，使用[成功]、[失败]、[警告]标记
- 安全考虑：仅检测配置，不修改系统设置
"""

import json
import os
import platform
import subprocess
import sys
import winreg  # Windows注册表访问
from datetime import datetime
from typing import Dict, Optional


def safe_print(message: str) -> None:
    """安全打印函数，处理Windows控制台编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 如果遇到编码问题，使用ASCII安全版本
        safe_message = message.encode("ascii", errors="replace").decode("ascii")
        print(safe_message)


def check_environment_proxies() -> Dict[str, Dict[str, Optional[str]]]:
    """检查环境变量中的代理设置"""
    safe_print("=" * 60)
    safe_print("检查环境变量代理设置")
    safe_print("=" * 60)

    proxy_vars = {
        "HTTP_PROXY": "HTTP代理",
        "HTTPS_PROXY": "HTTPS代理",
        "NO_PROXY": "代理排除列表",
        "http_proxy": "HTTP代理(小写)",
        "https_proxy": "HTTPS代理(小写)",
        "no_proxy": "代理排除列表(小写)",
        "ALL_PROXY": "通用代理",
        "all_proxy": "通用代理(小写)",
        "FTP_PROXY": "FTP代理",
        "ftp_proxy": "FTP代理(小写)",
    }

    results = {}
    for var, description in proxy_vars.items():
        value = os.environ.get(var)
        results[var] = {
            "value": value,
            "description": description,
            "exists": value is not None,
        }

        if value:
            safe_print(f"[警告] 检测到环境变量: {var}={value} ({description})")

    if not any(results[var]["exists"] for var in results):
        safe_print("[成功] 未在环境变量中检测到代理设置")

    safe_print("")
    return results


def check_windows_registry_proxies() -> Dict[str, Optional[str]]:
    """检查Windows注册表中的代理设置"""
    safe_print("=" * 60)
    safe_print("检查Windows注册表代理设置")
    safe_print("=" * 60)

    registry_proxies = {}
    registry_paths = [
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            "用户级代理设置",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
            "系统级代理设置",
        ),
    ]

    proxy_keys = ["ProxyServer", "ProxyEnable", "ProxyOverride"]

    try:
        for hive, path, description in registry_paths:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                safe_print(f"\n检查注册表: {description}")

                for proxy_key in proxy_keys:
                    try:
                        value, reg_type = winreg.QueryValueEx(key, proxy_key)
                        registry_proxies[f"{description}_{proxy_key}"] = str(value)

                        if proxy_key == "ProxyEnable" and value == 1:
                            safe_print(
                                f"[警告] 注册表代理已启用: {description}.{proxy_key} = {value}"
                            )
                        elif proxy_key == "ProxyServer" and value:
                            safe_print(
                                f"[警告] 注册表代理服务器: {description}.{proxy_key} = {value}"
                            )
                        elif proxy_key == "ProxyOverride" and value:
                            safe_print(
                                f"[信息] 注册表代理排除: {description}.{proxy_key} = {value}"
                            )
                    except FileNotFoundError:
                        # 键不存在是正常的
                        pass
                    except Exception as e:
                        safe_print(f"[错误] 读取注册表键 {proxy_key} 时出错: {e}")

                winreg.CloseKey(key)
            except FileNotFoundError:
                safe_print(f"[信息] 注册表路径不存在: {path}")
            except Exception as e:
                safe_print(f"[错误] 打开注册表路径 {path} 时出错: {e}")

    except Exception as e:
        safe_print(f"[错误] 检查注册表时发生异常: {e}")

    if not registry_proxies:
        safe_print("[成功] 未在注册表中检测到代理设置")

    safe_print("")
    return registry_proxies


def check_npm_proxy_config() -> Dict[str, Optional[str]]:
    """检查npm代理配置（全局和项目级）"""
    safe_print("=" * 60)
    safe_print("检查npm代理配置")
    safe_print("=" * 60)

    npm_configs = {}
    npm_commands = [
        ("proxy", "npm config get proxy"),
        ("https-proxy", "npm config get https-proxy"),
        ("noproxy", "npm config get noproxy"),
        ("registry", "npm config get registry"),
    ]

    try:
        for name, cmd in npm_commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            value = result.stdout.strip()
            npm_configs[f"npm_{name}"] = value if value and value != "null" else None

            if value and value != "null":
                safe_print(f"[警告] 检测到npm全局配置 {name}: {value}")
    except Exception as e:
        safe_print(f"[错误] 检查npm配置时出错: {e}")

    # 检查项目级.npmrc文件
    npmrc_paths = [os.path.join(os.getcwd(), ".npmrc"), os.path.expanduser("~/.npmrc")]

    for npmrc_path in npmrc_paths:
        if os.path.exists(npmrc_path):
            try:
                with open(npmrc_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "proxy" in content.lower() or "registry" in content.lower():
                        safe_print(f"[警告] 检测到项目级npm配置文件: {npmrc_path}")
                        npm_configs[f"npmrc_{os.path.basename(npmrc_path)}"] = (
                            content[:200] + "..." if len(content) > 200 else content
                        )
            except Exception as e:
                safe_print(f"[错误] 读取npmrc文件 {npmrc_path} 时出错: {e}")

    if not any(npm_configs.values()):
        safe_print("[成功] 未检测到npm代理配置")

    safe_print("")
    return npm_configs


def check_python_proxy_config() -> Dict[str, Optional[str]]:
    """检查Python/pip代理配置"""
    safe_print("=" * 60)
    safe_print("检查Python/pip代理配置")
    safe_print("=" * 60)

    python_configs = {}

    # 检查pip配置
    try:
        result = subprocess.run(
            "pip config list", shell=True, capture_output=True, text=True
        )
        pip_config = result.stdout.strip()
        if pip_config:
            python_configs["pip_config"] = pip_config
            if "proxy" in pip_config.lower():
                safe_print("[警告] 检测到pip代理配置")
                safe_print(f"pip配置:\n{pip_config}")
    except Exception as e:
        safe_print(f"[错误] 检查pip配置时出错: {e}")

    # 检查Python环境中的代理相关模块配置
    try:
        import urllib.request

        proxy_handler = urllib.request.getproxies()
        if proxy_handler:
            python_configs["urllib_proxies"] = json.dumps(proxy_handler)
            safe_print("[警告] 检测到urllib代理设置:")
            for key, value in proxy_handler.items():
                safe_print(f"  {key}: {value}")
    except Exception as e:
        safe_print(f"[信息] 检查urllib代理时出错: {e}")

    if not python_configs:
        safe_print("[成功] 未检测到Python/pip代理配置")

    safe_print("")
    return python_configs


def check_git_proxy_config() -> Dict[str, Optional[str]]:
    """检查Git代理配置"""
    safe_print("=" * 60)
    safe_print("检查Git代理配置")
    safe_print("=" * 60)

    git_configs = {}
    git_commands = [
        ("http.proxy", "git config --global http.proxy"),
        ("https.proxy", "git config --global https.proxy"),
        ("http.sslVerify", "git config --global http.sslVerify"),
    ]

    try:
        for name, cmd in git_commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            value = result.stdout.strip()
            if value:
                git_configs[f"git_{name}"] = value
                safe_print(f"[警告] 检测到Git配置 {name}: {value}")
    except Exception as e:
        safe_print(f"[错误] 检查Git配置时出错: {e}")

    if not git_configs:
        safe_print("[成功] 未检测到Git代理配置")

    safe_print("")
    return git_configs


def check_system_proxy_settings() -> Dict[str, Optional[str]]:
    """检查系统代理设置（通过netsh）"""
    safe_print("=" * 60)
    safe_print("检查系统代理设置（netsh）")
    safe_print("=" * 60)

    system_proxies = {}

    if platform.system() == "Windows":
        try:
            # 检查WinHTTP代理设置
            result = subprocess.run(
                "netsh winhttp show proxy", shell=True, capture_output=True, text=True
            )
            output = result.stdout.strip()
            if output and "Direct access" not in output:
                system_proxies["winhttp_proxy"] = output
                safe_print("[警告] 检测到WinHTTP代理设置:")
                safe_print(output)
            else:
                safe_print("[成功] 未检测到WinHTTP代理设置")
        except Exception as e:
            safe_print(f"[错误] 检查WinHTTP代理时出错: {e}")
    else:
        safe_print("[信息] 系统代理检查仅支持Windows平台")

    safe_print("")
    return system_proxies


def generate_proxy_report(
    env_proxies: Dict[str, Dict[str, Optional[str]]],
    registry_proxies: Dict[str, Optional[str]],
    npm_proxies: Dict[str, Optional[str]],
    python_proxies: Dict[str, Optional[str]],
    git_proxies: Dict[str, Optional[str]],
    system_proxies: Dict[str, Optional[str]],
) -> None:
    """生成代理检测报告"""
    safe_print("=" * 60)
    safe_print("代理检测报告")
    safe_print("=" * 60)

    # 统计检测结果
    env_count = sum(1 for var in env_proxies if env_proxies[var]["exists"])
    registry_count = len(registry_proxies)
    npm_count = sum(1 for v in npm_proxies.values() if v)
    python_count = sum(1 for v in python_proxies.values() if v)
    git_count = sum(1 for v in git_proxies.values() if v)
    system_count = sum(1 for v in system_proxies.values() if v)

    total_count = (
        env_count + registry_count + npm_count + python_count + git_count + system_count
    )

    safe_print("检测汇总:")
    safe_print(f"  环境变量代理: {env_count} 个")
    safe_print(f"  注册表代理: {registry_count} 个")
    safe_print(f"  npm代理: {npm_count} 个")
    safe_print(f"  Python/pip代理: {python_count} 个")
    safe_print(f"  Git代理: {git_count} 个")
    safe_print(f"  系统代理: {system_count} 个")
    safe_print(f"  总计: {total_count} 个代理设置")

    safe_print("\n" + "=" * 60)
    safe_print("清理建议")
    safe_print("=" * 60)

    if total_count == 0:
        safe_print("[成功] 未检测到代理设置，无需清理")
        return

    recommendations = []

    # 根据检测结果提供建议
    if env_count > 0:
        recommendations.append("清除环境变量代理:")
        for var in env_proxies:
            if env_proxies[var]["exists"]:
                recommendations.append(f"  - 删除环境变量: {var}")

    if registry_count > 0:
        recommendations.append("清理注册表代理设置:")
        recommendations.append("  1. 运行命令: regedit")
        recommendations.append(
            "  2. 导航到: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
        )
        recommendations.append("  3. 删除或修改 ProxyServer、ProxyEnable 值")
        recommendations.append("  注意: 修改注册表有风险，请先备份")

    if npm_count > 0:
        recommendations.append("清除npm代理配置:")
        recommendations.append("  - 运行: npm config delete proxy")
        recommendations.append("  - 运行: npm config delete https-proxy")
        recommendations.append("  - 检查项目级 .npmrc 文件并删除代理相关配置")

    if python_count > 0:
        recommendations.append("清除Python/pip代理:")
        recommendations.append("  - 运行: pip config unset global.proxy")
        recommendations.append("  - 运行: pip config unset global.https-proxy")
        recommendations.append("  - 检查环境变量中是否设置了代理")

    if git_count > 0:
        recommendations.append("清除Git代理配置:")
        recommendations.append("  - 运行: git config --global --unset http.proxy")
        recommendations.append("  - 运行: git config --global --unset https.proxy")

    if system_count > 0:
        recommendations.append("清除系统代理:")
        recommendations.append("  - 运行: netsh winhttp reset proxy")

    # 通用建议
    recommendations.append("\n通用建议:")
    recommendations.append("1. 仅在公司网络要求时才设置代理")
    recommendations.append("2. 开发时建议禁用所有代理，避免本地连接问题")
    recommendations.append(
        "3. 使用 NO_PROXY 环境变量排除本地地址（127.0.0.1, localhost）"
    )
    recommendations.append("4. 测试网络连接: curl -v http://localhost:8000/api/health")

    # 显示所有建议
    for rec in recommendations:
        safe_print(rec)

    safe_print("\n" + "=" * 60)
    safe_print("重要提示")
    safe_print("=" * 60)
    safe_print("1. 代理设置可能影响本地开发环境的网络连接")
    safe_print("2. 如果正在使用公司VPN或代理，可能需要保留某些设置")
    safe_print("3. 清除代理后，可能需要重启终端或IDE使更改生效")
    safe_print("4. 对于前端开发，代理可能影响npm包下载和API请求")
    safe_print("5. 对于后端开发，代理可能影响外部API调用（Gemini、GPTZero）")


def main():
    """主函数"""
    safe_print("Otium项目代理环境检测工具")
    safe_print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print(f"系统平台: {platform.platform()}")
    safe_print(f"当前目录: {os.getcwd()}")
    safe_print("")

    # 检查所有可能的代理设置位置
    env_proxies = check_environment_proxies()
    registry_proxies = check_windows_registry_proxies()
    npm_proxies = check_npm_proxy_config()
    python_proxies = check_python_proxy_config()
    git_proxies = check_git_proxy_config()
    system_proxies = check_system_proxy_settings()

    # 生成报告
    generate_proxy_report(
        env_proxies,
        registry_proxies,
        npm_proxies,
        python_proxies,
        git_proxies,
        system_proxies,
    )

    # 提供快速修复命令
    safe_print("\n" + "=" * 60)
    safe_print("快速修复命令")
    safe_print("=" * 60)
    safe_print("如果需要快速清除常见代理设置，可以运行以下命令:")
    safe_print("")
    safe_print("# 清除环境变量（当前会话）")
    safe_print("set HTTP_PROXY=")
    safe_print("set HTTPS_PROXY=")
    safe_print("")
    safe_print("# 清除npm代理")
    safe_print("npm config delete proxy")
    safe_print("npm config delete https-proxy")
    safe_print("")
    safe_print("# 清除Git代理")
    safe_print("git config --global --unset http.proxy")
    safe_print("git config --global --unset https.proxy")
    safe_print("")
    safe_print("# 重置WinHTTP代理")
    safe_print("netsh winhttp reset proxy")
    safe_print("")

    # 检查是否有代理设置
    total_proxies = (
        sum(1 for var in env_proxies if env_proxies[var]["exists"])
        + len(registry_proxies)
        + sum(1 for v in npm_proxies.values() if v)
        + sum(1 for v in python_proxies.values() if v)
        + sum(1 for v in git_proxies.values() if v)
        + sum(1 for v in system_proxies.values() if v)
    )

    if total_proxies > 0:
        safe_print(f"[警告] 检测到 {total_proxies} 个代理设置，可能会影响本地开发")
        sys.exit(1)
    else:
        safe_print("[成功] 未检测到代理设置，网络环境正常")
        sys.exit(0)


if __name__ == "__main__":
    main()
