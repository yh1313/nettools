# NetTools - 网络工程师工具箱

![Version](https://img.shields.io/badge/version-1.5-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

> 面向网络工程师和 IT 运维人员的免费工具集，提供常用的网络测试、诊断和管理功能。

## ✨ 功能特性

| 模块 | 功能说明 |
|------|----------|
| **Ping 测试** | 高级 ICMP Ping，统计丢包率、最小/最大/平均延迟 |
| **TCPing 测试** | TCP 端口连通性测试，支持 SSH/HTTP/MySQL/Redis 等常用端口 |
| **路由追踪** | 显示数据包到达目标经过的路由节点 (tracert/traceroute) |
| **端口扫描** | 多线程 TCP 端口扫描，支持自定义端口范围和深度扫描 |
| **DNS 查询** | 支持 A/AAAA/MX/CNAME/NS/TXT/SOA 等记录类型查询 |
| **HTTP 测试** | HTTP/HTTPS 接口响应时间、状态码测试 |
| **网络质量评估** | 综合评估网络质量（丢包率+延迟），给出评分和建议 |
| **IP 计算器** | CIDR 子网计算，快速得出网络地址、广播地址、可用 IP 范围 |
| **密码生成器** | 生成高强度随机密码，支持自定义长度和字符类型 |
| **实用工具** | DNS 缓存刷新、WiFi 密码查看、本机网络信息 (ipconfig /all) |
| **公网 IP 查询** | 获取当前网络的公网出口 IP 地址 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows / macOS / Linux

### 源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/nettools.git
cd nettools

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动程序
python nettools.py
```

### Windows 打包为 EXE

```bash
# 双击运行
build.bat

# 或手动执行
pip install pyinstaller
python build_exe.py

# 输出目录: dist/NetTools/
```

### 下载预编译版本

前往 [Releases](https://github.com/YOUR_USERNAME/nettools/releases) 页面下载最新的 `NetTools_v1.5.zip`，解压后双击 `NetTools.exe` 即可运行。

## 📦 依赖说明

### 核心依赖（必须）

| 包名 | 版本 | 用途 |
|------|------|------|
| `ping3` | >=4.0 | ICMP Ping 测试 |
| `dnspython` | >=2.4 | DNS 解析查询 |
| `requests` | >=2.31 | HTTP 请求 |

### 可选依赖

| 包名 | 用途 |
|------|------|
| `ttkbootstrap` | 现代化 UI 主题（不安装则使用原生 tkinter 样式） |

## 📁 项目结构

```
nettools/
├── nettools.py          # 主程序 (GUI 界面)
├── tools.py             # 核心工具模块
│   ├── NetworkTools     # 网络测试工具集
│   ├── SystemTools      # 系统工具集
│   └── PasswordTools    # 密码工具
├── requirements.txt     # Python 依赖
├── build_exe.py         # PyInstaller 打包配置
├── NetTools.spec        # PyInstaller spec 文件
├── build.bat            # 一键打包脚本 (Windows)
├── LICENSE              # MIT 开源协议
└── README.md            # 说明文档
```

## 🖥️ 界面预览

主界面采用标签页布局：

- **Ping 测试** | **TCPing 测试** | **路由追踪** | **端口扫描**
- **DNS 查询** | **HTTP 测试** | **网络质量** | **IP 计算器**
- **密码生成器** | **实用工具** | **公网 IP** | **关于**

每个标签页提供独立的功能区域，操作简单直观。

## 🛠️ 技术栈

- **语言**: Python 3
- **GUI**: tkinter + ttkbootstrap (可选)
- **网络**: ping3, dnspython, requests
- **打包**: PyInstaller

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

## 📄 License

MIT License - 完全免费使用，详见 [LICENSE](LICENSE) 文件。
