# XrayR 寄生模式配置生成器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

自动化生成 XrayR 寄生模式配置的工具，支持从订阅链接批量导入节点并生成完整的 XrayR 配置文件。

## ✨ 特性

### v3.6 Fixed 版本
- ✅ **双路由模式**
  - 负载均衡模式：自动分配节点到面板
  - 固定映射模式：精确控制 proxy-node 对应关系
- ✅ **修复关键问题**
  - proxy-node 映射关系准确性
  - 地区分类识别优化
- ✅ **多面板支持**
  - NewV2board / V2board / SSpanel / PMpanel
- ✅ **Base64 订阅解析**
  - 自动识别并解码 Base64 订阅
- ✅ **自动部署**
  - 一键生成配置并重启 XrayR 服务

## 📋 系统要求

- Python 3.6+
- Linux 虚拟机环境
- 已安装 XrayR（路径：`/etc/XrayR`）

## 🚀 快速开始

### 1. 下载脚本

```bash
wget https://raw.githubusercontent.com/aa11255/xrayrpro/main/xrayr_parasite_v3.6_fixed.py
chmod +x xrayr_parasite_v3.6_fixed.py
```

### 2. 运行脚本

```bash
python3 xrayr_parasite_v3.6_fixed.py
```

### 3. 按提示输入配置

脚本会引导你完成以下配置：

1. **面板信息**
   - 面板类型（NewV2board/V2board/SSpanel/PMpanel）
   - 面板域名
   - API Key
   - Node ID

2. **订阅链接**
   - 支持多个订阅链接（逗号分隔）
   - 自动解析 Base64 编码

3. **路由模式选择**
   - **负载均衡模式**：自动分配节点到面板
   - **固定映射模式**：手动指定每个节点对应的面板

4. **节点筛选**
   - 自动过滤广告节点（包含"到期"、"流量"等关键词）
   - 支持地区分类（香港/台湾/日本/新加坡/美国/其他）

## 📖 使用示例

### 负载均衡模式

```
请选择路由模式:
1. 负载均衡 (自动分配节点到面板)
2. 固定映射 (手动指定每个节点对应的面板)
选择 [1]: 1

✓ 已生成 15 个节点配置
✓ 配置已保存到 /etc/XrayR/config.yml
✓ XrayR 服务已重启
```

### 固定映射模式

```
请选择路由模式:
1. 负载均衡 (自动分配节点到面板)
2. 固定映射 (手动指定每个节点对应的面板)
选择 [1]: 2

节点 1: 香港-HKT [HK]
  请选择对应的面板 (1-3): 1

节点 2: 台湾-Hinet [TW]
  请选择对应的面板 (1-3): 2

✓ 已生成 15 个节点配置（固定映射）
✓ 配置已保存到 /etc/XrayR/config.yml
✓ XrayR 服务已重启
```

## 🔧 配置说明

### 支持的节点类型

- V2ray (VMess)
- Trojan
- Shadowsocks
- Shadowsocks-Plugin

### 自动过滤关键词

脚本会自动过滤包含以下关键词的节点：
- 到期、流量、网站、重置、剩余、过期
- 官网、群、订阅、套餐、客服、TG

### 地区识别

支持自动识别以下地区：
- 🇭🇰 香港 (HK/Hong Kong/香港)
- 🇹🇼 台湾 (TW/Taiwan/台湾)
- 🇯🇵 日本 (JP/Japan/日本)
- 🇸🇬 新加坡 (SG/Singapore/新加坡)
- 🇺🇸 美国 (US/United States/美国)

## ⚠️ 注意事项

1. **备份配置**：脚本会自动备份原有配置到 `config.yml.bak`
2. **权限要求**：需要 root 权限或对 `/etc/XrayR` 有写权限
3. **服务重启**：配置生成后会自动重启 XrayR 服务
4. **订阅有效性**：确保订阅链接可访问且返回有效节点

## 🐛 故障排查

### 订阅获取失败
```bash
❌ 获取失败 (重试3次): https://...
```
**解决方案**：
- 检查订阅链接是否有效
- 确认网络连接正常
- 尝试更换订阅链接

### 配置写入失败
```bash
❌ 配置写入失败: Permission denied
```
**解决方案**：
- 使用 `sudo` 运行脚本
- 检查 `/etc/XrayR` 目录权限

### 服务重启失败
```bash
❌ XrayR 重启失败
```
**解决方案**：
- 手动检查配置：`xrayr config`
- 查看日志：`journalctl -u xrayr -f`

## 📝 更新日志

### v3.6 Fixed (2026-03-12)
- 🔧 修复 proxy-node 映射关系准确性
- 🔧 优化地区分类识别逻辑
- ✨ 新增固定映射模式
- ✨ 改进节点标签生成算法

### v3.5
- ✨ 支持多面板配置
- ✨ Base64 订阅自动解码
- 🔧 优化节点过滤逻辑

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

- GitHub: [@aa11255](https://github.com/aa11255)
- 项目地址: https://github.com/aa11255/xrayrpro

---

**免责声明**：本工具仅供学习交流使用，请遵守当地法律法规。
