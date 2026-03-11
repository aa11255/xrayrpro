#!/usr/bin/env python3
"""
XrayR 脚本诊断工具
检查运行环境和依赖
"""
import sys

print("=" * 60)
print("XrayR 脚本环境诊断")
print("=" * 60)

# 1. Python 版本
print(f"\n1. Python 版本: {sys.version}")
print(f"   版本号: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

if sys.version_info < (3, 6):
    print("   ❌ Python 版本过低，需要 3.6+")
else:
    print("   ✓ Python 版本符合要求")

# 2. 检查依赖
print("\n2. 依赖检查:")

deps = {
    'requests': 'HTTP 请求库',
    'yaml': 'YAML 解析库 (PyYAML)',
    'json': 'JSON 解析库 (内置)',
    'base64': 'Base64 编解码 (内置)',
    'hashlib': '哈希库 (内置)',
    're': '正则表达式 (内置)',
    'os': '系统操作 (内置)',
    'subprocess': '进程管理 (内置)',
    'shutil': '文件操作 (内置)'
}

missing = []
for module, desc in deps.items():
    try:
        __import__(module)
        print(f"   ✓ {module:15s} - {desc}")
    except ImportError:
        print(f"   ❌ {module:15s} - {desc} (缺失)")
        missing.append(module)

# 3. 安装建议
if missing:
    print("\n3. 缺少依赖，请运行以下命令安装:")
    if 'requests' in missing or 'yaml' in missing:
        install_cmd = []
        if 'requests' in missing:
            install_cmd.append('requests')
        if 'yaml' in missing:
            install_cmd.append('pyyaml')
        print(f"   pip3 install {' '.join(install_cmd)}")
else:
    print("\n3. ✓ 所有依赖已安装")

# 4. XrayR 路径检查
print("\n4. XrayR 路径检查:")
import os
xrayr_path = "/etc/XrayR"
if os.path.exists(xrayr_path):
    print(f"   ✓ {xrayr_path} 存在")
    config_path = os.path.join(xrayr_path, "config.yml")
    if os.path.exists(config_path):
        print(f"   ✓ {config_path} 存在")
    else:
        print(f"   ⚠ {config_path} 不存在")
else:
    print(f"   ❌ {xrayr_path} 不存在")

# 5. 权限检查
print("\n5. 权限检查:")
if os.access(xrayr_path, os.W_OK):
    print(f"   ✓ 对 {xrayr_path} 有写权限")
else:
    print(f"   ❌ 对 {xrayr_path} 无写权限，需要 sudo")

print("\n" + "=" * 60)
if missing:
    print("状态: ❌ 环境不完整，请安装缺失的依赖")
    sys.exit(1)
else:
    print("状态: ✓ 环境检查通过，可以运行主脚本")
    sys.exit(0)
