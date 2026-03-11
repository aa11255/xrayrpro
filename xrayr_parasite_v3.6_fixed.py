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
import subprocess

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

# --- 地区映射 ---
REGION_MAP = {
    'HK': ['HK', 'Hong Kong', '香港', 'HongKong'],
    'TW': ['TW', 'Taiwan', '台湾', 'TaiWan'],
    'JP': ['JP', 'Japan', '日本'],
    'SG': ['SG', 'Singapore', '新加坡'],
    'US': ['US', 'United States', '美国', 'USA']
}

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

def decode_base64(text):
    """尝试解码 Base64"""
    try:
        decoded = base64.b64decode(text).decode('utf-8')
        if decoded.startswith('vmess://') or decoded.startswith('trojan://') or decoded.startswith('ss://'):
            return decoded
    except:
        pass
    return text

def parse_vmess(uri):
    """解析 vmess:// 链接"""
    try:
        data = json.loads(base64.b64decode(uri.replace('vmess://', '')).decode('utf-8'))
        return {
            'type': 'vmess',
            'name': data.get('ps', 'Unknown'),
            'server': data.get('add', ''),
            'port': int(data.get('port', 443)),
            'uuid': data.get('id', ''),
            'alterId': int(data.get('aid', 0)),
            'network': data.get('net', 'tcp'),
            'tls': data.get('tls', '') == 'tls',
            'sni': data.get('sni', data.get('host', '')),
            'path': data.get('path', ''),
            'host': data.get('host', '')
        }
    except:
        return None

def parse_trojan(uri):
    """解析 trojan:// 链接"""
    try:
        # trojan://password@server:port?sni=xxx#name
        match = re.match(r'trojan://([^@]+)@([^:]+):(\d+)(\?[^#]*)?(#.*)?', uri)
        if not match:
            return None
        
        password, server, port, params, name = match.groups()
        sni = ''
        if params:
            sni_match = re.search(r'sni=([^&]+)', params)
            if sni_match:
                sni = sni_match.group(1)
        
        return {
            'type': 'trojan',
            'name': name.replace('#', '') if name else 'Unknown',
            'server': server,
            'port': int(port),
            'password': password,
            'sni': sni or server
        }
    except:
        return None

def parse_ss(uri):
    """解析 ss:// 链接"""
    try:
        # ss://base64(method:password)@server:port#name
        match = re.match(r'ss://([^@]+)@([^:]+):(\d+)(#.*)?', uri)
        if not match:
            return None
        
        encoded, server, port, name = match.groups()
        decoded = base64.b64decode(encoded).decode('utf-8')
        method, password = decoded.split(':', 1)
        
        return {
            'type': 'ss',
            'name': name.replace('#', '') if name else 'Unknown',
            'server': server,
            'port': int(port),
            'method': method,
            'password': password
        }
    except:
        return None

def parse_subscription(text):
    """解析订阅内容"""
    nodes = []
    
    # 尝试 Base64 解码
    text = decode_base64(text)
    
    # 按行分割
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        node = None
        if line.startswith('vmess://'):
            node = parse_vmess(line)
        elif line.startswith('trojan://'):
            node = parse_trojan(line)
        elif line.startswith('ss://'):
            node = parse_ss(line)
        
        if node:
            nodes.append(node)
    
    return nodes

def filter_nodes(nodes):
    """过滤广告节点"""
    filtered = []
    for node in nodes:
        name = node.get('name', '')
        if any(kw in name for kw in EXCLUDE_KEYWORDS):
            continue
        filtered.append(node)
    return filtered

def detect_region(name):
    """检测节点地区"""
    for region, keywords in REGION_MAP.items():
        if any(kw in name for kw in keywords):
            return region
    return 'OTHER'

def group_by_region(nodes):
    """按地区分组"""
    groups = {}
    for node in nodes:
        region = detect_region(node['name'])
        if region not in groups:
            groups[region] = []
        groups[region].append(node)
    return groups

def generate_xrayr_node(node, panel_index, node_id, tag):
    """生成 XrayR 节点配置"""
    config = {
        'PanelType': PANEL_TYPES[panel_index],
        'ApiConfig': {
            'ApiHost': f"https://panel{panel_index+1}.example.com",
            'ApiKey': "your_api_key",
            'NodeID': node_id,
            'NodeType': NODE_TYPES.get('1', 'V2ray'),
            'Timeout': 30,
            'EnableVless': False,
            'EnableXTLS': False,
            'SpeedLimit': 0,
            'DeviceLimit': 0,
            'RuleListPath': ''
        },
        'ControllerConfig': {
            'ListenIP': '0.0.0.0',
            'SendIP': '0.0.0.0',
            'UpdatePeriodic': 60,
            'EnableDNS': False,
            'DNSType': 'AsIs',
            'EnableProxyProtocol': False,
            'EnableFallback': False,
            'FallBackConfigs': [],
            'DisableLocalREALITYConfig': False,
            'EnableREALITY': False,
            'REALITYConfigs': {
                'Show': True
            },
            'CertConfig': {
                'CertMode': 'none',
                'CertDomain': node.get('sni', node.get('server', '')),
                'CertFile': '',
                'KeyFile': '',
                'Provider': 'cloudflare',
                'Email': '',
                'DNSEnv': {}
            }
        }
    }
    
    return config

def input_panels():
    """输入面板信息"""
    panels = []
    num = int(get_input("请输入面板数量", "1"))
    
    for i in range(num):
        print(f"\n{CYAN}=== 面板 {i+1} ==={PLAIN}")
        panel_type_idx = int(get_input(f"面板类型 (0={PANEL_TYPES[0]}, 1={PANEL_TYPES[1]}, 2={PANEL_TYPES[2]}, 3={PANEL_TYPES[3]})", "0"))
        domain = get_input("面板域名 (如: panel.example.com)")
        api_key = get_input("API Key")
        node_id = int(get_input("Node ID", "1"))
        
        panels.append({
            'type_idx': panel_type_idx,
            'type': PANEL_TYPES[panel_type_idx],
            'domain': domain,
            'api_key': api_key,
            'node_id': node_id
        })
    
    return panels

def main():
    print(f"{CYAN}{'='*60}{PLAIN}")
    print(f"{CYAN}XrayR 寄生模式配置生成器 v3.6 Fixed{PLAIN}")
    print(f"{CYAN}{'='*60}{PLAIN}\n")
    
    # 1. 输入面板信息
    panels = input_panels()
    
    # 2. 输入订阅链接
    print(f"\n{CYAN}=== 订阅链接 ==={PLAIN}")
    sub_urls = get_input("订阅链接 (多个用逗号分隔)").split(',')
    
    # 3. 获取并解析订阅
    all_nodes = []
    for url in sub_urls:
        url = url.strip()
        if not url:
            continue
        print(f"{BLUE}正在获取: {url[:50]}...{PLAIN}")
        content = fetch_sub(url)
        if content:
            nodes = parse_subscription(content)
            all_nodes.extend(nodes)
            print(f"{GREEN}✓ 获取到 {len(nodes)} 个节点{PLAIN}")
    
    if not all_nodes:
        print(f"{RED}❌ 未获取到任何节点{PLAIN}")
        return
    
    # 4. 过滤节点
    all_nodes = filter_nodes(all_nodes)
    print(f"\n{GREEN}✓ 过滤后剩余 {len(all_nodes)} 个节点{PLAIN}")
    
    # 5. 选择路由模式
    print(f"\n{CYAN}=== 路由模式 ==={PLAIN}")
    print("1. 负载均衡 (自动分配节点到面板)")
    print("2. 固定映射 (手动指定每个节点对应的面板)")
    mode = get_input("选择", "1")
    
    # 6. 生成配置
    xrayr_nodes = []
    
    if mode == "1":
        # 负载均衡模式
        for idx, node in enumerate(all_nodes):
            panel_idx = idx % len(panels)
            panel = panels[panel_idx]
            tag = get_unique_tag(idx, node['name'])
            
            config = generate_xrayr_node(node, panel['type_idx'], panel['node_id'], tag)
            config['ApiConfig']['ApiHost'] = f"https://{panel['domain']}"
            config['ApiConfig']['ApiKey'] = panel['api_key']
            config['ApiConfig']['NodeID'] = panel['node_id']
            
            xrayr_nodes.append(config)
        
        print(f"\n{GREEN}✓ 已生成 {len(xrayr_nodes)} 个节点配置{PLAIN}")
    
    else:
        # 固定映射模式
        groups = group_by_region(all_nodes)
        
        print(f"\n{CYAN}节点分组:{PLAIN}")
        for region, nodes in groups.items():
            print(f"  {region}: {len(nodes)} 个节点")
        
        print(f"\n{YELLOW}请为每个节点指定面板:{PLAIN}")
        for idx, node in enumerate(all_nodes):
            region = detect_region(node['name'])
            print(f"\n节点 {idx+1}: {node['name']} [{region}]")
            
            for i, panel in enumerate(panels):
                print(f"  {i+1}. {panel['domain']} ({panel['type']})")
            
            panel_choice = int(get_input(f"  请选择对应的面板 (1-{len(panels)})", "1")) - 1
            panel = panels[panel_choice]
            tag = get_unique_tag(idx, node['name'])
            
            config = generate_xrayr_node(node, panel['type_idx'], panel['node_id'], tag)
            config['ApiConfig']['ApiHost'] = f"https://{panel['domain']}"
            config['ApiConfig']['ApiKey'] = panel['api_key']
            config['ApiConfig']['NodeID'] = panel['node_id']
            
            xrayr_nodes.append(config)
        
        print(f"\n{GREEN}✓ 已生成 {len(xrayr_nodes)} 个节点配置（固定映射）{PLAIN}")
    
    # 7. 保存配置
    config_path = os.path.join(XRAYR_PATH, 'config.yml')
    
    # 备份原配置
    if os.path.exists(config_path):
        backup_path = config_path + '.bak'
        shutil.copy2(config_path, backup_path)
        print(f"{YELLOW}已备份原配置到: {backup_path}{PLAIN}")
    
    # 写入新配置
    final_config = {
        'Log': {
            'Level': 'warning',
            'AccessPath': '',
            'ErrorPath': ''
        },
        'DnsConfigPath': '',
        'RouteConfigPath': '',
        'InboundConfigPath': '',
        'OutboundConfigPath': '',
        'ConnectionConfig': {
            'Handshake': 4,
            'ConnIdle': 30,
            'UplinkOnly': 2,
            'DownlinkOnly': 4,
            'BufferSize': 64
        },
        'Nodes': xrayr_nodes
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(final_config, f, allow_unicode=True, default_flow_style=False)
        print(f"{GREEN}✓ 配置已保存到 {config_path}{PLAIN}")
    except Exception as e:
        print(f"{RED}❌ 配置写入失败: {e}{PLAIN}")
        return
    
    # 8. 重启服务
    restart = get_input("\n是否重启 XrayR 服务? (y/n)", "y")
    if restart.lower() == 'y':
        try:
            subprocess.run(['systemctl', 'restart', 'xrayr'], check=True)
            print(f"{GREEN}✓ XrayR 服务已重启{PLAIN}")
        except:
            print(f"{RED}❌ XrayR 重启失败，请手动执行: systemctl restart xrayr{PLAIN}")
    
    print(f"\n{CYAN}{'='*60}{PLAIN}")
    print(f"{GREEN}配置生成完成！{PLAIN}")
    print(f"{CYAN}{'='*60}{PLAIN}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}用户中断{PLAIN}")
    except Exception as e:
        print(f"\n{RED}错误: {e}{PLAIN}")
        import traceback
        traceback.print_exc()
