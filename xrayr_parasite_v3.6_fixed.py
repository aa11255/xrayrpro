#!/usr/bin/env python3
"""
XrayR 寄生模式配置生成器 (v3.6 Fixed)
优化: 负载均衡 + 固定映射双模式 / 多面板支持 / Base64订阅 / 自动部署
修复: proxy-node 映射关系 / 地区分类准确性
适用于: Linux 虚拟机环境
"""
import requests
import yaml
import json
import re
import os
import base64
import ipaddress
import hashlib
import random
import shutil

# --- 颜色常量 ---
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
PLAIN = '\033[0m'

# --- 配置 ---
EXCLUDE_KEYWORDS = ["到期", "流量", "网站", "重置", "剩余", "过期", "官网", "群", "订阅", "套餐", "客服", "TG"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "ClashforWindows/0.20.39"
]
NODE_TYPES = {'1': 'V2ray', '2': 'Trojan', '3': 'Shadowsocks', '4': 'Shadowsocks-Plugin'}
PANEL_TYPES = ['NewV2board', 'V2board', 'SSpanel', 'PMpanel']
XRAYR_PATH = "/etc/XrayR"

def get_input(prompt, default=""):
    text = f"{prompt} [{default}]: " if default else f"{prompt}: "
    value = input(text).strip()
    return value if value else default

def get_unique_tag(index, name):
    clean = re.sub(r'[^\w]', '', name)[:10]
    h = hashlib.md5(f"{index}{name}".encode()).hexdigest()[:6]
    return f"p_{index}_{clean}_{h}"

def is_ip(s):
    try:
        ipaddress.ip_address(s)
        return True
    except:
        return False

def get_sni(p):
    for key in ['sni', 'servername', 'server']:
        val = p.get(key, '')
        if val and not is_ip(val):
            return val
    return p.get('server', '')

def fetch_sub(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=20)
            if r.ok:
                return r.text
        except:
            pass
    print(f"{RED}❌ 获取失败 (重试{retries}次): {url[:50]}...{PLAIN}")
    return None
