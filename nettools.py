# nettools.py - 网络小助手 v1.5
# 公共通用版本 | 纯网络工具 | MIT License
import sys
import os

# 确保工作目录正确
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import subprocess
import re
import socket
from datetime import datetime

from tools import NetworkTools, SystemTools, PasswordTools

# 尝试使用 ttkbootstrap 美化界面
try:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *

    USE_BOOTSTRAP = True
except ImportError:
    USE_BOOTSTRAP = False

# 尝试导入交换机管理模块（可选）
try:
    from switch_manager import SwitchManager

    SWITCH_AVAILABLE = True
except ImportError:
    SWITCH_AVAILABLE = False


class NetToolsApp:
    """网络小助手"""

    def __init__(self, root):
        self.root = root
        self.root.title("网络小助手 v1.5")
        self.root.geometry("1280x900")

        # 初始化工具
        self.net = NetworkTools()
        self.sys = SystemTools()
        self.pwd = PasswordTools()
        self.switch = SwitchManager() if SWITCH_AVAILABLE else None
        self._last_dns_backup = None  # 记录 DNS 修改前的配置
        self._dns_adapters_cache = []  # DNS 适配器缓存

        # 设置样式
        if USE_BOOTSTRAP:
            self.style = ttkb.Style(theme="cosmo")
            # cosmo 主题：现代清爽风格，背景适中不刺眼
            self._bg = "#e8ecf1"          # 主背景（浅蓝灰，不刺眼）
            self._bg2 = "#ffffff"         # 内容区白色
            self._bg_header = "#d5dce6"   # 头部区（稍深蓝灰）
            self._accent = "#2780e3"      # 主色调蓝
            self._danger = "#e74c3c"      # 危险/操作色红
            self._success = "#27ae60"     # 成功绿
            self._warning = "#f0ad4e"     # 警告橙
            self._text = "#222222"        # 主文字色（深色，清晰）
            self._text_light = "#555555"  # 次要文字色（够深，可读）

            # 全局配置 tk 默认颜色
            root.option_add('*Frame.background', self._bg)
            root.option_add('*LabelFrame.background', self._bg)
            root.option_add('*Label.background', self._bg)
            root.option_add('*Label.foreground', self._text)
            root.option_add('*Button.background', self._bg_header)
            root.option_add('*Button.foreground', self._text)
            root.option_add('*Entry.background', self._bg2)
            root.option_add('*Text.background', self._bg2)
            root.option_add('*Text.foreground', self._text)

            # 配置 ttkbootstrap 自定义样式
            self.style.configure('danger.TButton', font=('微软雅黑', 10))
            self.style.configure('primary.TButton', font=('微软雅黑', 10))
            self.style.configure('success.TButton', font=('微软雅黑', 10))
            self.style.configure('warning.TButton', font=('微软雅黑', 10))
            self.style.configure('info.TButton', font=('微软雅黑', 10))
            self.style.configure('secondary.TButton', font=('微软雅黑', 10))

        self.setup_ui()

    def setup_ui(self):
        """创建主界面"""
        # 标题栏
        title_frame = tk.Frame(self.root, bg="#e8ecf1")
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="网络小助手",
                 font=("Segoe UI", 24, "bold"), fg="#e74c3c", bg="#e8ecf1").pack(side=tk.LEFT, padx=20, pady=10)
        version_label = tk.Label(title_frame, text="v1.5  |  公共通用版",
                                 font=("Segoe UI", 9), fg="#555555", bg="#e8ecf1")
        version_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # 标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=8, pady=5)

        # 创建各功能标签页
        self.create_ping_tab()
        self.create_tcping_tab()
        self.create_traceroute_tab()
        self.create_portscan_tab()
        self.create_dns_tab()
        self.create_http_tab()
        self.create_ip_tab()
        self.create_hosts_tab()
        self.create_route_tab()
        self.create_arp_tab()
        self.create_netstat_tab()
        self.create_password_tab()
        self.create_utility_tab()
        self.create_public_ip_tab()
        self.create_diagnostic_tab()
        self.create_quality_tab()
        self.create_domain_user_tab()
        self.create_system_info_tab()
        self.create_about_tab()

        # 状态栏
        status_text = "网络小助手 就绪 | 网络测试 | DNS查询 | Hosts管理 | 端口扫描 | 网络诊断 | 完全免费"
        self.status = tk.Label(self.root, text=status_text, bd=1, relief=tk.SUNKEN,
                               anchor=tk.W, font=("微软雅黑", 9))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ==================== Ping 测试 ====================
    def create_ping_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Ping 测试")

        # 参数区
        frame = tk.LabelFrame(tab, text="测试参数", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="目标 IP/域名:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ping_target = tk.Entry(frame, width=30, font=("Consolas", 10))
        self.ping_target.grid(row=0, column=1, padx=5)
        self.ping_target.insert(0, "www.baidu.com")

        tk.Label(frame, text="发包数量:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.ping_count = tk.Spinbox(frame, from_=1, to=100, width=6, font=("Consolas", 10))
        self.ping_count.grid(row=0, column=3, padx=5)
        self.ping_count.delete(0, tk.END)
        self.ping_count.insert(0, "4")

        self.ping_btn = tk.Button(frame, text="开始 Ping", command=self.do_ping,
                                  bg="#e74c3c", fg="white", padx=20, font=("微软雅黑", 10))
        self.ping_btn.grid(row=0, column=4, padx=20)

        # 快速目标
        quick_frame = tk.Frame(frame)
        quick_frame.grid(row=1, column=0, columnspan=5, pady=(10, 0))
        for label, target in [("百度", "www.baidu.com"), ("Google DNS", "8.8.8.8"),
                               ("阿里", "www.aliyun.com"), ("腾讯", "www.qq.com")]:
            tk.Button(quick_frame, text=label,
                      command=lambda t=target: self.set_ping_target(t),
                      bg="#d5dce6", padx=8, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=3)

        # 结果区
        result_frame = tk.LabelFrame(tab, text="测试结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.ping_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.ping_result.pack(fill=tk.BOTH, expand=True)

    def set_ping_target(self, target):
        self.ping_target.delete(0, tk.END)
        self.ping_target.insert(0, target)

    def do_ping(self):
        def task():
            self.ping_btn.config(state=tk.DISABLED, text="测试中...")
            target = self.ping_target.get().strip()
            count = int(self.ping_count.get())
            res = self.net.ping_test(target, count)

            out = f"Ping 测试结果 - {target}\n"
            out += "=" * 60 + "\n"
            out += f"发送: {res['packets_sent']}  接收: {res['packets_received']}  丢包率: {res['packet_loss']}\n"
            out += f"最小延迟: {res['min_latency']}  最大延迟: {res['max_latency']}  平均延迟: {res['avg_latency']}\n"
            out += "=" * 60 + "\n\n"

            for d in res['details']:
                if d['status'] == 'success':
                    out += f"  [第{d['seq']:2d}包]  {d['latency']}\n"
                else:
                    out += f"  [第{d['seq']:2d}包]  超时\n"

            self.root.after(0, lambda: self.ping_result.delete(1.0, tk.END))
            self.root.after(0, lambda: self.ping_result.insert(tk.END, out))
            self.root.after(0, lambda: self.ping_btn.config(state=tk.NORMAL, text="开始 Ping"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== TCPing 测试 ====================
    def create_tcping_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="TCPing 测试")

        frame = tk.LabelFrame(tab, text="测试参数", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="目标主机:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.tcping_host = tk.Entry(frame, width=25, font=("Consolas", 10))
        self.tcping_host.grid(row=0, column=1, padx=5)
        self.tcping_host.insert(0, "223.5.5.5")

        tk.Label(frame, text="端口:").grid(row=0, column=2, sticky=tk.W, padx=(15, 0))
        self.tcping_port = tk.Entry(frame, width=20, font=("Consolas", 10))
        self.tcping_port.grid(row=0, column=3, padx=5)
        self.tcping_port.insert(0, "53,443")
        tk.Label(frame, text="(多个端口用逗号隔开)", fg="#555555", font=("微软雅黑", 8)).grid(row=0, column=4, padx=2)

        tk.Label(frame, text="发包数:").grid(row=0, column=5, sticky=tk.W, padx=(15, 0))
        self.tcping_count = tk.Spinbox(frame, from_=1, to=10, width=5, font=("Consolas", 10))
        self.tcping_count.grid(row=0, column=6, padx=5)
        self.tcping_count.delete(0, tk.END)
        self.tcping_count.insert(0, "2")

        self.tcping_btn = tk.Button(frame, text="开始 TCPing", command=self.do_tcping,
                                    bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.tcping_btn.grid(row=0, column=7, padx=20)

        # 快速端口选择
        quick_frame = tk.Frame(frame)
        quick_frame.grid(row=1, column=0, columnspan=8, pady=(10, 0))
        for label, port in [("SSH(22)", "22"), ("HTTP(80)", "80"), ("HTTPS(443)", "443"),
                            ("MySQL(3306)", "3306"), ("RDP(3389)", "3389"), ("Redis(6379)", "6379"),
                            ("DNS(53)", "53"), ("DNS+HTTPS", "53,443")]:
            tk.Button(quick_frame, text=label, command=lambda p=port: self.set_tcping_port(p),
                      bg="#d5dce6", padx=6, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=3)

        result_frame = tk.LabelFrame(tab, text="测试结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tcping_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.tcping_result.pack(fill=tk.BOTH, expand=True)

    def set_tcping_port(self, ports):
        self.tcping_port.delete(0, tk.END)
        self.tcping_port.insert(0, ports)

    def do_tcping(self):
        def task():
            self.tcping_btn.config(state=tk.DISABLED, text="测试中...")
            host = self.tcping_host.get().strip()
            port_str = self.tcping_port.get().strip()
            count = int(self.tcping_count.get())

            # 解析端口列表
            ports = []
            for p in port_str.replace('，', ',').split(','):
                p = p.strip()
                if p:
                    try:
                        ports.append(int(p))
                    except ValueError:
                        pass

            if not ports:
                self.root.after(0, lambda: self.tcping_result.insert(tk.END, "请输入有效的端口号\n"))
                self.root.after(0, lambda: self.tcping_btn.config(state=tk.NORMAL, text="开始 TCPing"))
                return

            out = f"TCPing 测试结果\n"
            out += "=" * 60 + "\n"
            out += f"目标: {host}\n"
            out += f"端口: {', '.join(map(str, ports))}\n"
            out += "-" * 60 + "\n\n"

            for port in ports:
                for i in range(count):
                    try:
                        start = time.time()
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(3)
                        ret = sock.connect_ex((host, port))
                        elapsed = (time.time() - start) * 1000
                        sock.close()
                        svc = NetworkTools._get_port_service(port)
                        if ret == 0:
                            out += f"  [✓ 开放] 端口 {port:5d}  {svc:12s}  {elapsed:.1f}ms\n"
                        else:
                            out += f"  [✗ 关闭] 端口 {port:5d}  {svc:12s}  拒绝连接\n"
                    except socket.gaierror:
                        out += f"  [✗ 错误] 端口 {port:5d}  DNS解析失败\n"
                    except Exception as e:
                        out += f"  [✗ 错误] 端口 {port:5d}  {str(e)}\n"

            out += "\n说明: [✓] 表示端口开放可访问，[✗] 表示端口关闭或不可达\n"

            self.root.after(0, lambda: self.tcping_result.delete(1.0, tk.END))
            self.root.after(0, lambda: self.tcping_result.insert(tk.END, out))
            self.root.after(0, lambda: self.tcping_btn.config(state=tk.NORMAL, text="开始 TCPing"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== 路由追踪 ====================
    def create_traceroute_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="路由追踪")

        frame = tk.LabelFrame(tab, text="测试参数", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="目标 IP/域名:").pack(side=tk.LEFT, padx=5)
        self.trace_target = tk.Entry(frame, width=30, font=("Consolas", 10))
        self.trace_target.pack(side=tk.LEFT, padx=5)
        self.trace_target.insert(0, "8.8.8.8")

        self.trace_no_dns = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="不解析为域名 (-d)", variable=self.trace_no_dns,
                       font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)

        self.trace_btn = tk.Button(frame, text="开始追踪", command=self.do_traceroute,
                                   bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.trace_btn.pack(side=tk.LEFT, padx=5)

        result_frame = tk.LabelFrame(tab, text="追踪结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.trace_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.trace_result.pack(fill=tk.BOTH, expand=True)

    def do_traceroute(self):
        def task():
            self.trace_btn.config(state=tk.DISABLED, text="追踪中...")
            target = self.trace_target.get().strip()
            no_dns = self.trace_no_dns.get()
            res = self.net.traceroute(target, no_dns=no_dns, timeout=60)
            self.root.after(0, lambda: self.trace_result.delete(1.0, tk.END))
            if res.get("success"):
                self.root.after(0, lambda: self.trace_result.insert(tk.END, res["output"]))
            else:
                self.root.after(0, lambda: self.trace_result.insert(tk.END, f"错误: {res['error']}"))
            self.root.after(0, lambda: self.trace_btn.config(state=tk.NORMAL, text="开始追踪"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== 端口扫描 ====================
    def create_portscan_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="端口扫描")

        frame = tk.LabelFrame(tab, text="扫描参数", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        frame.pack(fill=tk.X, padx=10, pady=10)

        row1 = tk.Frame(frame)
        row1.pack(fill=tk.X, pady=5)
        tk.Label(row1, text="目标 IP:", width=8).pack(side=tk.LEFT)
        self.scan_ip = tk.Entry(row1, width=20, font=("Consolas", 10))
        self.scan_ip.pack(side=tk.LEFT, padx=5)
        self.scan_ip.insert(0, "127.0.0.1")

        tk.Label(row1, text="端口范围:", width=8).pack(side=tk.LEFT, padx=(20, 0))
        self.scan_ports = tk.Entry(row1, width=30, font=("Consolas", 10))
        self.scan_ports.pack(side=tk.LEFT, padx=5)
        self.scan_ports.insert(0, "22,80,443,3306,3389,8080,8443")

        row2 = tk.Frame(frame)
        row2.pack(fill=tk.X, pady=5)
        tk.Label(row2, text="并发线程:", width=8).pack(side=tk.LEFT)
        self.scan_threads = tk.Spinbox(row2, from_=10, to=200, width=6)
        self.scan_threads.pack(side=tk.LEFT, padx=5)
        self.scan_threads.delete(0, tk.END)
        self.scan_threads.insert(0, "100")

        self.deep_scan_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row2, text="深度扫描 (更慢但更准确)", variable=self.deep_scan_var,
                       font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(20, 0))

        self.scan_btn = tk.Button(frame, text="开始扫描", command=self.do_portscan,
                                  bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.scan_btn.pack(pady=10)

        # 快捷端口
        quick_frame = tk.Frame(frame)
        quick_frame.pack(fill=tk.X)
        for label, ports in [("常用端口", "22,80,443,3306,3389,8080"), ("Web端口", "80,443,8080,8443,9090"),
                             ("数据库", "3306,5432,6379,27017,1433,1521"),
                             ("1-1024", "1-1024")]:
            tk.Button(quick_frame, text=label, command=lambda p=ports: self.set_scan_ports(p),
                      bg="#d5dce6", padx=6, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=3)

        result_frame = tk.LabelFrame(tab, text="扫描结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.scan_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.scan_result.pack(fill=tk.BOTH, expand=True)

    def set_scan_ports(self, ports):
        self.scan_ports.delete(0, tk.END)
        self.scan_ports.insert(0, ports)

    def do_portscan(self):
        def task():
            self.scan_btn.config(state=tk.DISABLED, text="扫描中...")
            self.scan_result.delete(1.0, tk.END)
            ip = self.scan_ip.get().strip()
            ports_str = self.scan_ports.get().strip()
            max_threads = int(self.scan_threads.get())
            deep = self.deep_scan_var.get()

            try:
                res = self.net.port_scan(ip, ports=ports_str, max_threads=max_threads, deep_scan=deep)
                out = f"端口扫描结果 - {ip}\n"
                out += "=" * 60 + "\n"
                out += f"扫描时间: {res['scan_time']}\n"
                out += f"扫描端口: {res['total_ports_scanned']} 个\n"
                out += f"开放端口: {len(res['open_ports'])} 个\n"
                out += f"扫描模式: {'深度扫描' if deep else '普通扫描'}\n"
                out += "-" * 60 + "\n\n"

                if res['open_ports']:
                    out += "开放端口列表:\n"
                    for p in res['open_ports']:
                        svc_name = p.get('display', p.get('service', ''))
                        out += f"  [✓] 端口 {p['port']:5d}  {svc_name:20s}  延迟 {p['latency']}\n"
                else:
                    out += "未发现开放端口\n"

                self.root.after(0, lambda: self.scan_result.insert(tk.END, out))
            except Exception as e:
                self.root.after(0, lambda: self.scan_result.insert(tk.END, f"扫描错误: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL, text="开始扫描"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== DNS 管理（查询+设置+重置） ====================
    def create_dns_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="DNS 管理")

        # ===== 查询区 =====
        query_frame = tk.LabelFrame(tab, text="DNS 查询", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        query_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        q_row = tk.Frame(query_frame)
        q_row.pack(fill=tk.X, pady=3)
        tk.Label(q_row, text="域名:").pack(side=tk.LEFT, padx=5)
        self.dns_domain = tk.Entry(q_row, width=28, font=("Consolas", 10))
        self.dns_domain.pack(side=tk.LEFT, padx=5)
        self.dns_domain.insert(0, "www.baidu.com")

        tk.Label(q_row, text="类型:").pack(side=tk.LEFT, padx=(10, 0))
        self.dns_type = ttk.Combobox(q_row, values=["A", "AAAA", "MX", "CNAME", "NS", "TXT", "SOA"], width=7)
        self.dns_type.pack(side=tk.LEFT, padx=5)
        self.dns_type.set("A")

        self.dns_btn = tk.Button(q_row, text="查询", command=self.do_dns,
                                 bg="#2780e3", fg="white", padx=15, font=("微软雅黑", 10))
        self.dns_btn.pack(side=tk.LEFT, padx=5)

        self.dns_result = scrolledtext.ScrolledText(query_frame, height=4, font=("Consolas", 9))
        self.dns_result.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # ===== 设置区 =====
        setup_frame = tk.LabelFrame(tab, text="DNS 切换 / 重置", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        setup_frame.pack(fill=tk.X, padx=10, pady=5)

        s_row1 = tk.Frame(setup_frame)
        s_row1.pack(fill=tk.X, pady=3)
        tk.Label(s_row1, text="网卡:").pack(side=tk.LEFT, padx=5)
        self.dns_adapter_combo = ttk.Combobox(s_row1, width=30, state="readonly", font=("微软雅黑", 9))
        self.dns_adapter_combo.pack(side=tk.LEFT, padx=5)
        tk.Button(s_row1, text="刷新", command=self.refresh_dns_adapters,
                  bg="#2780e3", fg="white", font=("微软雅黑", 9), padx=8).pack(side=tk.LEFT, padx=5)
        self.dns_current_label = tk.Label(s_row1, text="点击刷新查看", fg="#555555", font=("Consolas", 9))
        self.dns_current_label.pack(side=tk.LEFT, padx=10)

        s_row2 = tk.Frame(setup_frame)
        s_row2.pack(fill=tk.X, pady=3)
        dns_presets = list(SystemTools.PUBLIC_DNS.keys())
        for i, name in enumerate(dns_presets):
            if name == "自动获取 (DHCP)":
                continue
            tk.Button(s_row2, text=name, command=lambda n=name: self.apply_dns_preset(n),
                      bg="#d5dce6", padx=6, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=2)

        s_row3 = tk.Frame(setup_frame)
        s_row3.pack(fill=tk.X, pady=4)
        tk.Label(s_row3, text="主 DNS:").pack(side=tk.LEFT, padx=5)
        self.dns_primary = tk.Entry(s_row3, width=15, font=("Consolas", 10))
        self.dns_primary.pack(side=tk.LEFT, padx=3)
        self.dns_primary.insert(0, "223.5.5.5")
        tk.Label(s_row3, text="备 DNS:").pack(side=tk.LEFT, padx=5)
        self.dns_secondary = tk.Entry(s_row3, width=15, font=("Consolas", 10))
        self.dns_secondary.pack(side=tk.LEFT, padx=3)
        self.dns_secondary.insert(0, "223.6.6.6")

        self.dns_apply_btn = tk.Button(s_row3, text="应用", command=self.apply_dns_manual,
                                       bg="#e74c3c", fg="white", padx=10, font=("微软雅黑", 9))
        self.dns_apply_btn.pack(side=tk.LEFT, padx=3)
        self.dns_dhcp_btn = tk.Button(s_row3, text="自动获取 (DHCP)", command=self.apply_dns_dhcp,
                                      bg="#f39c12", fg="white", padx=10, font=("微软雅黑", 9))
        self.dns_dhcp_btn.pack(side=tk.LEFT, padx=3)
        self.dns_backup_btn = tk.Button(s_row3, text="恢复之前", command=self.apply_dns_backup,
                                        bg="#8e44ad", fg="white", padx=10, font=("微软雅黑", 9))
        self.dns_backup_btn.pack(side=tk.LEFT, padx=3)
        self.dns_flush_btn = tk.Button(s_row3, text="刷新缓存", command=self.do_flush_dns_cache,
                                       bg="#27ae60", fg="white", padx=10, font=("微软雅黑", 9))
        self.dns_flush_btn.pack(side=tk.LEFT, padx=3)

        # 日志
        log_frame = tk.LabelFrame(tab, text="操作日志", padx=10, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.dns_log = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9))
        self.dns_log.pack(fill=tk.BOTH, expand=True)

        tip = tk.Label(tab, text="提示: 修改 DNS 需要管理员权限", fg="#c0392b", font=("微软雅黑", 9))
        tip.pack(pady=2)

        self.refresh_dns_adapters()

    def do_dns(self):
        def task():
            self.dns_btn.config(state=tk.DISABLED, text="查询中...")
            domain = self.dns_domain.get().strip()
            rtype = self.dns_type.get()
            res = self.net.dns_lookup(domain, rtype)

            out = f"DNS {rtype} 查询 - {domain}\n"
            out += "=" * 60 + "\n"
            if res.get("success"):
                for r in res['records']:
                    out += f"  {r}\n"
                out += f"\n共 {len(res['records'])} 条记录"
            else:
                out += f"查询失败: {res['error']}\n"

            self.root.after(0, lambda: self.dns_result.delete(1.0, tk.END))
            self.root.after(0, lambda: self.dns_result.insert(tk.END, out))
            self.root.after(0, lambda: self.dns_btn.config(state=tk.NORMAL, text="查询"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== HTTP 测试 ====================
    def create_http_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="HTTP 测试")

        frame = tk.LabelFrame(tab, text="测试参数", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="URL:").pack(side=tk.LEFT, padx=5)
        self.http_url = tk.Entry(frame, width=50, font=("Consolas", 10))
        self.http_url.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.http_url.insert(0, "https://www.baidu.com")

        self.http_btn = tk.Button(frame, text="测试", command=self.do_http,
                                  bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.http_btn.pack(side=tk.LEFT, padx=10)

        result_frame = tk.LabelFrame(tab, text="测试结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.http_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.http_result.pack(fill=tk.BOTH, expand=True)

    def do_http(self):
        def task():
            self.http_btn.config(state=tk.DISABLED, text="测试中...")
            url = self.http_url.get().strip()
            res = self.net.http_test(url)

            out = f"HTTP 测试结果\n"
            out += "=" * 60 + "\n"
            if res.get("success"):
                status = res['status_code']
                if 200 <= status < 300:
                    access = "✅ 可以访问"
                elif 300 <= status < 400:
                    access = "⚠️ 已重定向"
                elif 400 <= status < 500:
                    access = "❌ 访问被拒绝"
                else:
                    access = "❌ 服务器错误"
                out += f"URL: {res['url']}\n"
                out += f"状态: {access} (HTTP {status})\n"
                out += f"响应时间: {res['response_time']}\n"
                out += f"服务器: {res['server']}\n"
                out += f"内容类型: {res['content_type']}\n"
                out += f"内容大小: {res['size']}\n"
            else:
                access = "❌ 不能访问"
                out += f"URL: {url}\n"
                out += f"状态: {access}\n"
                out += f"错误: {res['error']}\n\n"
                # 自动触发网络诊断
                out += "=" * 60 + "\n"
                out += "⚠️ 访问失败，正在自动进行网络诊断...\n"
                diag = self.sys.network_diagnostic()
                if diag.get("success"):
                    out += f"  网关: {diag.get('gateway', '未知')}\n"
                    out += f"  外网: {diag.get('internet', '未知')}\n"
                    out += f"  DNS: {diag.get('dns', '未知')}\n"
                    out += f"  百度: {diag.get('ping', '未知')}\n"
                    if '超时' in str(diag.get('gateway', '')):
                        out += "\n  → 建议: 网关不通，请检查网络连接\n"
                    elif '超时' in str(diag.get('internet', '')):
                        out += "\n  → 建议: 外网不通，请检查宽带/路由器\n"
                    elif '异常' in str(diag.get('dns', '')):
                        out += "\n  → 建议: DNS 解析异常，请尝试切换 DNS 服务器\n"
                else:
                    out += f"  诊断失败: {diag.get('error', '未知')}\n"

            self.root.after(0, lambda: self.http_result.delete(1.0, tk.END))
            self.root.after(0, lambda: self.http_result.insert(tk.END, out))
            self.root.after(0, lambda: self.http_btn.config(state=tk.NORMAL, text="测试"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== 网络质量 ====================
    def create_quality_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="网络质量")

        frame = tk.LabelFrame(tab, text="测试参数", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="目标 IP/域名:").pack(side=tk.LEFT, padx=5)
        self.quality_target = tk.Entry(frame, width=25, font=("Consolas", 10))
        self.quality_target.pack(side=tk.LEFT, padx=5)
        self.quality_target.insert(0, "8.8.8.8")

        self.quality_btn = tk.Button(frame, text="开始评估", command=self.do_quality,
                                     bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.quality_btn.pack(side=tk.LEFT, padx=20)

        result_frame = tk.LabelFrame(tab, text="评估报告", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.quality_result = scrolledtext.ScrolledText(result_frame, height=18, font=("微软雅黑", 11))
        self.quality_result.pack(fill=tk.BOTH, expand=True)

    def do_quality(self):
        def task():
            self.quality_btn.config(state=tk.DISABLED, text="评估中...")
            target = self.quality_target.get().strip()
            res = self.net.network_quality(target, packets=15)

            grade_icon = "A" if res['quality_score'] >= 80 else "B" if res['quality_score'] >= 60 else "C"
            out = f"网络质量评估报告\n"
            out += "=" * 60 + "\n"
            out += f"目标: {res['target']}\n\n"
            out += f"质量评分: {res['quality_score']}/100  等级: {grade_icon} ({res['quality_level']})\n\n"
            out += f"丢包率: {res['packet_loss']}\n"
            out += f"平均延迟: {res['avg_latency']}\n"
            out += f"最小延迟: {res['min_latency']}\n"
            out += f"最大延迟: {res['max_latency']}\n\n"
            out += f"建议: {res['suggestion']}\n"

            self.root.after(0, lambda: self.quality_result.delete(1.0, tk.END))
            self.root.after(0, lambda: self.quality_result.insert(tk.END, out))
            self.root.after(0, lambda: self.quality_btn.config(state=tk.NORMAL, text="开始评估"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== IP 计算器 ====================
    def create_ip_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="IP 计算器")

        main_frame = tk.LabelFrame(tab, text="IP 子网计算器 (CIDR)", padx=15, pady=15, font=("微软雅黑", 11, "bold"))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        tk.Label(input_frame, text="输入 IP/CIDR:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        self.ip_cidr_entry = tk.Entry(input_frame, width=25, font=("Consolas", 11))
        self.ip_cidr_entry.pack(side=tk.LEFT, padx=5)
        self.ip_cidr_entry.insert(0, "192.168.1.100/24")

        self.ip_calc_btn = tk.Button(input_frame, text="计算", command=self.calc_ip,
                                     bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.ip_calc_btn.pack(side=tk.LEFT, padx=10)

        # 快捷 CIDR
        quick_frame = tk.Frame(main_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        tk.Label(quick_frame, text="快捷:", font=("微软雅黑", 9), fg="#555555").pack(side=tk.LEFT, padx=5)
        for cidr in [8, 16, 24, 26, 28, 30, 32]:
            tk.Button(quick_frame, text=f"/{cidr}", command=lambda c=cidr: self.set_cidr(c),
                      bg="#d5dce6", padx=6, font=("Consolas", 9)).pack(side=tk.LEFT, padx=3)

        self.ip_result_text = scrolledtext.ScrolledText(main_frame, height=15, font=("Consolas", 10))
        self.ip_result_text.pack(fill=tk.BOTH, expand=True, pady=10)

        self.calc_ip()

    def set_cidr(self, cidr):
        current = self.ip_cidr_entry.get().strip()
        if '/' in current:
            ip = current.split('/')[0]
        else:
            ip = current
        self.ip_cidr_entry.delete(0, tk.END)
        self.ip_cidr_entry.insert(0, f"{ip}/{cidr}")

    def calc_ip(self):
        ip_cidr = self.ip_cidr_entry.get().strip()
        if not ip_cidr:
            return
        result = self.sys.ip_calculator(ip_cidr)
        self.ip_result_text.delete(1.0, tk.END)
        if "error" in result:
            self.ip_result_text.insert(tk.END, f"错误: {result['error']}")
        else:
            out = f"IP 地址:      {result['ip']}\n"
            out += f"CIDR 前缀:    /{result['cidr']}\n"
            out += f"子网掩码:     {result['subnet_mask']}\n"
            out += f"网络地址:     {result['network']}\n"
            out += f"广播地址:     {result['broadcast']}\n"
            out += f"第一个可用IP: {result['first_host']}\n"
            out += f"最后一个可用IP: {result['last_host']}\n"
            out += f"总地址数:     {result['total_hosts']}\n"
            out += f"可用主机数:   {result['usable_hosts']}\n"
            self.ip_result_text.insert(tk.END, out)

    # ==================== DNS 设置 ====================
    def refresh_dns_adapters(self):
        """刷新网络适配器列表"""
        adapters = self.sys.get_dns_servers()
        adapter_names = [a['adapter'] for a in adapters if a.get('adapter')]
        self.dns_adapter_combo['values'] = adapter_names
        if adapter_names:
            self.dns_adapter_combo.current(0)
            self._update_current_dns_info(adapters[0] if adapters else None)
        self.dns_adapter_combo.bind('<<ComboboxSelected>>',
                                    lambda e: self._on_adapter_select(adapters))
        self._dns_adapters_cache = adapters

    def _on_adapter_select(self, adapters):
        idx = self.dns_adapter_combo.current()
        if 0 <= idx < len(adapters):
            self._update_current_dns_info(adapters[idx])

    def _update_current_dns_info(self, adapter_info):
        if adapter_info:
            dns_str = "\n".join(adapter_info.get('dns_servers', ['未知']))
            self.dns_current_label.config(
                text=f"当前 DNS:\n{dns_str}", fg="#2c3e50"
            )
        else:
            self.dns_current_label.config(text="当前 DNS: 未获取", fg="#555555")

    def apply_dns_preset(self, name):
        """选择预设 DNS（仅填充输入框，需点击应用后生效）"""
        dns_info = SystemTools.PUBLIC_DNS.get(name)
        if dns_info is None:
            return
        primary, secondary = dns_info
        self.dns_primary.delete(0, tk.END)
        self.dns_primary.insert(0, primary)
        self.dns_secondary.delete(0, tk.END)
        self.dns_secondary.insert(0, secondary)

    def apply_dns_manual(self):
        """应用当前输入框中的 DNS 设置"""
        primary = self.dns_primary.get().strip()
        secondary = self.dns_secondary.get().strip()
        if not primary and not secondary:
            # 主备均为空时，使用 DHCP 自动获取
            self._set_dns("", "")
        elif not primary:
            self.dns_log.insert(tk.END, "[错误] 请填写首选 DNS 地址，或清空两项使用 DHCP\n")
            self.dns_log.see(tk.END)
            return
        else:
            self._set_dns(primary, secondary)

    def apply_dns_dhcp(self):
        """直接切换为 DHCP 自动获取 DNS"""
        self._set_dns("", "")

    def apply_dns_backup(self):
        """恢复上一次的 DNS 配置（仅填充输入框，需点击应用后生效）"""
        if not self._last_dns_backup:
            self.dns_log.insert(tk.END, "[提示] 没有可恢复的 DNS 配置\n")
            self.dns_log.see(tk.END)
            return
        dns_servers, adapter = self._last_dns_backup
        # 如果当前适配器与备份不一致，尝试切换
        current_adapter = self.dns_adapter_combo.get().strip()
        if adapter and adapter != current_adapter:
            values = list(self.dns_adapter_combo['values'])
            if adapter in values:
                self.dns_adapter_combo.set(adapter)
                self.refresh_dns_adapters()
        self.dns_primary.delete(0, tk.END)
        self.dns_secondary.delete(0, tk.END)
        if dns_servers:
            self.dns_primary.insert(0, dns_servers[0])
            if len(dns_servers) > 1:
                self.dns_secondary.insert(0, dns_servers[1])
        self.dns_log.insert(tk.END, "[提示] 已恢复上次 DNS 配置，点击“应用”后生效\n")
        self.dns_log.see(tk.END)

    def _set_dns(self, primary, secondary):
        """执行 DNS 设置"""
        adapter = self.dns_adapter_combo.get().strip()
        if not adapter:
            self.dns_log.insert(tk.END, "[错误] 请选择网络适配器\n")
            self.dns_log.see(tk.END)
            return

        # 记录当前配置，用于“恢复之前”
        if self._dns_adapters_cache:
            for a in self._dns_adapters_cache:
                if a.get('adapter') == adapter:
                    self._last_dns_backup = (a.get('dns_servers', []), adapter)
                    break

        self.dns_apply_btn.config(state=tk.DISABLED, text="设置中...")
        self.dns_dhcp_btn.config(state=tk.DISABLED)
        self.dns_backup_btn.config(state=tk.DISABLED)
        self.dns_flush_btn.config(state=tk.DISABLED)

        def task():
            mode = "DHCP 自动获取" if not primary and not secondary else "静态 DNS"
            self.root.after(0, lambda: self.dns_log.insert(
                tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] 正在设置 {mode}...\n"))
            self.root.after(0, lambda: self.dns_log.see(tk.END))

            success, msg = self.sys.set_dns(adapter, primary, secondary)

            prefix = "[成功]" if success else "[失败]"
            self.root.after(0, lambda: self.dns_log.insert(tk.END, f"{prefix} {msg}\n"))
            self.root.after(0, lambda: self.dns_log.see(tk.END))

            if success:
                # 自动刷新 DNS 缓存
                s2, m2 = self.sys.flush_dns_cache()
                self.root.after(0, lambda: self.dns_log.insert(
                    tk.END, f"[{'成功' if s2 else '提示'}] {m2}\n\n"))
                self.root.after(0, lambda: self.dns_log.see(tk.END))
                # 刷新适配器信息
                self.root.after(500, self.refresh_dns_adapters)

            self.root.after(0, lambda: self.dns_apply_btn.config(
                state=tk.NORMAL, text="应用"))
            self.root.after(0, lambda: self.dns_dhcp_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.dns_backup_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.dns_flush_btn.config(state=tk.NORMAL))

        threading.Thread(target=task, daemon=True).start()

    def do_flush_dns_cache(self):
        """刷新 DNS 缓存"""
        self.dns_flush_btn.config(state=tk.DISABLED, text="刷新中...")
        success, msg = self.sys.flush_dns_cache()
        self.dns_log.insert(tk.END, f"[{'成功' if success else '失败'}] {msg}\n")
        self.dns_log.see(tk.END)
        self.dns_flush_btn.config(state=tk.NORMAL, text="刷新 DNS 缓存")

    # ==================== 密码生成器 ====================
    def create_password_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="密码生成器")

        main_frame = tk.LabelFrame(tab, text="随机密码生成", padx=15, pady=15, font=("微软雅黑", 11, "bold"))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        len_frame = tk.Frame(main_frame)
        len_frame.pack(fill=tk.X, pady=10)
        tk.Label(len_frame, text="密码长度:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        self.pwd_length = tk.Spinbox(len_frame, from_=8, to=32, width=5, font=("微软雅黑", 10))
        self.pwd_length.pack(side=tk.LEFT, padx=5)
        self.pwd_length.delete(0, tk.END)
        self.pwd_length.insert(0, "16")

        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)

        opt_frame = tk.Frame(main_frame)
        opt_frame.pack(fill=tk.X, pady=10)
        tk.Checkbutton(opt_frame, text="大写字母 (A-Z)", variable=self.use_upper,
                       font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(opt_frame, text="小写字母 (a-z)", variable=self.use_lower,
                       font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(opt_frame, text="数字 (0-9)", variable=self.use_digits,
                       font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(opt_frame, text="特殊符号 (!@#...)", variable=self.use_symbols,
                       font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)

        self.gen_pwd_btn = tk.Button(main_frame, text="生成随机密码", command=self.generate_password,
                                     bg="#e74c3c", fg="white", font=("微软雅黑", 11), padx=20)
        self.gen_pwd_btn.pack(pady=15)

        result_frame = tk.LabelFrame(main_frame, text="生成的密码", padx=10, pady=10,
                                     font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.password_display = tk.Entry(result_frame, font=("Consolas", 16), justify="center", state="readonly",
                                         readonlybackground="white")
        self.password_display.pack(fill=tk.X, padx=10, pady=10)

        self.strength_label = tk.Label(result_frame, text="密码强度: ", font=("微软雅黑", 10), fg="#555555")
        self.strength_label.pack(anchor=tk.W, padx=10)

        btn_frame = tk.Frame(result_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="复制密码", command=self.copy_password,
                  bg="#27ae60", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="重新生成", command=self.generate_password,
                  bg="#f39c12", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)

        tip = tk.Label(main_frame,
                       text="建议: 密码长度 12 位以上，包含大小写、数字和特殊符号，强度更高",
                       fg="#555555", font=("微软雅黑", 9))
        tip.pack(pady=5)

    def generate_password(self):
        length = int(self.pwd_length.get())
        use_upper = self.use_upper.get()
        use_lower = self.use_lower.get()
        use_digits = self.use_digits.get()
        use_symbols = self.use_symbols.get()

        if not (use_upper or use_lower or use_digits or use_symbols):
            messagebox.showwarning("提示", "请至少选择一种字符类型")
            return

        pwd, err = PasswordTools.generate(length, use_upper, use_lower, use_digits, use_symbols)
        if err:
            messagebox.showerror("错误", err)
            return

        self.password_display.config(state="normal")
        self.password_display.delete(0, tk.END)
        self.password_display.insert(0, pwd)
        self.password_display.config(state="readonly")

        strength, color = PasswordTools.check_strength(pwd)
        self.strength_label.config(text=f"密码强度: {strength}", fg=color)

    def copy_password(self):
        pwd = self.password_display.get()
        if pwd:
            self.root.clipboard_clear()
            self.root.clipboard_append(pwd)
            messagebox.showinfo("成功", "密码已复制到剪贴板")

    # ==================== Hosts 文件管理 ====================
    def create_hosts_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Hosts 管理")

        # 顶部工具栏
        toolbar = tk.Frame(tab)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(toolbar, text=f"Hosts 文件: {SystemTools.HOSTS_PATH}", font=("Consolas", 9), fg="#555555").pack(
            side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(toolbar)
        btn_frame.pack(side=tk.RIGHT)

        self.hosts_save_btn = tk.Button(btn_frame, text="保存修改", command=self.save_hosts,
                                        bg="#e74c3c", fg="white", padx=12, font=("微软雅黑", 9))
        self.hosts_save_btn.pack(side=tk.LEFT, padx=3)

        self.hosts_backup_btn = tk.Button(btn_frame, text="备份 Hosts", command=self.backup_hosts,
                                          bg="#2780e3", fg="white", padx=12, font=("微软雅黑", 9))
        self.hosts_backup_btn.pack(side=tk.LEFT, padx=3)

        self.hosts_refresh_btn = tk.Button(btn_frame, text="刷新", command=self.load_hosts,
                                           bg="#d5dce6", padx=12, font=("微软雅黑", 9))
        self.hosts_refresh_btn.pack(side=tk.LEFT, padx=3)

        # 快速添加
        quick_frame = tk.LabelFrame(tab, text="快速添加记录", padx=10, pady=5, font=("微软雅黑", 10, "bold"))
        quick_frame.pack(fill=tk.X, padx=10, pady=5)

        qf = tk.Frame(quick_frame)
        qf.pack(fill=tk.X, pady=5)
        tk.Label(qf, text="IP 地址:", font=("微软雅黑", 9), width=7).pack(side=tk.LEFT, padx=3)
        self.hosts_ip = tk.Entry(qf, width=18, font=("Consolas", 10))
        self.hosts_ip.pack(side=tk.LEFT, padx=3)
        self.hosts_ip.insert(0, "127.0.0.1")

        tk.Label(qf, text="域名:", font=("微软雅黑", 9), width=5).pack(side=tk.LEFT, padx=(10, 3))
        self.hosts_domain = tk.Entry(qf, width=30, font=("Consolas", 10))
        self.hosts_domain.pack(side=tk.LEFT, padx=3)
        self.hosts_domain.insert(0, "example.local")

        tk.Label(qf, text="注释:", font=("微软雅黑", 9), width=5).pack(side=tk.LEFT, padx=(10, 3))
        self.hosts_comment = tk.Entry(qf, width=20, font=("微软雅黑", 10))
        self.hosts_comment.pack(side=tk.LEFT, padx=3)

        tk.Button(qf, text="添加", command=self.add_hosts_entry,
                  bg="#27ae60", fg="white", padx=10, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)

        # 编辑区
        edit_frame = tk.LabelFrame(tab, text="Hosts 文件内容 (可直接编辑)", padx=10, pady=10,
                                   font=("微软雅黑", 10, "bold"))
        edit_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.hosts_text = scrolledtext.ScrolledText(edit_frame, height=20, font=("Consolas", 10))
        self.hosts_text.pack(fill=tk.BOTH, expand=True)

        # 备份管理
        backup_frame = tk.LabelFrame(tab, text="备份管理", padx=10, pady=5, font=("微软雅黑", 10, "bold"))
        backup_frame.pack(fill=tk.X, padx=10, pady=5)

        self.hosts_backup_combo = ttk.Combobox(backup_frame, width=60, state="readonly", font=("Consolas", 9))
        self.hosts_backup_combo.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(backup_frame, text="恢复选中备份", command=self.restore_hosts,
                  bg="#f39c12", fg="white", padx=10, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(backup_frame, text="刷新列表", command=self.refresh_hosts_backups,
                  bg="#d5dce6", padx=10, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)

        self.hosts_status = tk.Label(backup_frame, text="", fg="#555555", font=("微软雅黑", 9))
        self.hosts_status.pack(side=tk.RIGHT, padx=10)

        tip = tk.Label(tab, text="提示: 修改 hosts 文件需要管理员权限。保存后可能需要刷新 DNS 缓存才能生效。",
                       fg="#c0392b", font=("微软雅黑", 9))
        tip.pack(pady=5)

        self.load_hosts()
        self.refresh_hosts_backups()

    def load_hosts(self):
        """加载 hosts 文件内容"""
        res = self.sys.get_hosts_content()
        self.hosts_text.delete(1.0, tk.END)
        if res.get("success"):
            self.hosts_text.insert(tk.END, res["content"])
            self.hosts_status.config(text="已加载", fg="green")
        else:
            self.hosts_text.insert(tk.END, f"加载失败: {res.get('error', '未知错误')}")
            self.hosts_status.config(text="加载失败", fg="red")

    def save_hosts(self):
        """保存 hosts 文件"""
        content = self.hosts_text.get(1.0, tk.END).rstrip('\n') + '\n'
        self.hosts_save_btn.config(state=tk.DISABLED, text="保存中...")
        success, msg = self.sys.save_hosts_content(content)
        self.hosts_status.config(text=msg, fg="green" if success else "red")
        self.hosts_save_btn.config(state=tk.NORMAL, text="保存修改")
        if not success:
            messagebox.showerror("保存失败", msg)
        else:
            self.load_hosts()

    def backup_hosts(self):
        """备份 hosts 文件"""
        self.hosts_backup_btn.config(state=tk.DISABLED, text="备份中...")
        success, msg = self.sys.backup_hosts()
        self.hosts_backup_btn.config(state=tk.NORMAL, text="备份 Hosts")
        if success:
            self.refresh_hosts_backups()
        self.hosts_status.config(text=msg, fg="green" if success else "red")

    def restore_hosts(self):
        """恢复 hosts 备份"""
        selection = self.hosts_backup_combo.get()
        if not selection:
            messagebox.showwarning("提示", "请选择一个备份文件")
            return
        backup_path = self._hosts_backup_map.get(selection, "")
        if not backup_path:
            messagebox.showerror("错误", "未找到备份文件路径")
            return
        if not messagebox.askyesno("确认恢复", f"确定要恢复到备份:\n{selection}\n\n当前 hosts 文件将被覆盖!"):
            return
        success, msg = self.sys.restore_hosts(backup_path)
        self.hosts_status.config(text=msg, fg="green" if success else "red")
        if success:
            self.load_hosts()

    def refresh_hosts_backups(self):
        """刷新备份列表"""
        backups = self.sys.list_hosts_backups()
        self._hosts_backup_map = {}
        items = []
        for b in backups:
            label = f"{b['time']}  |  {b['size']}  |  {b['filename']}"
            items.append(label)
            self._hosts_backup_map[label] = b['path']
        self.hosts_backup_combo['values'] = items
        if items:
            self.hosts_backup_combo.current(0)

    def add_hosts_entry(self):
        """快速添加 hosts 记录"""
        ip = self.hosts_ip.get().strip()
        domain = self.hosts_domain.get().strip()
        comment = self.hosts_comment.get().strip()
        if not ip or not domain:
            messagebox.showwarning("提示", "请填写 IP 地址和域名")
            return

        entry = f"{ip} {domain}"
        if comment:
            entry += f"  # {comment}"

        current = self.hosts_text.get(1.0, tk.END)
        if not current.endswith('\n'):
            current += '\n'
        current += entry + '\n'
        self.hosts_text.delete(1.0, tk.END)
        self.hosts_text.insert(tk.END, current)
        self.hosts_status.config(text=f"已添加: {entry}", fg="blue")

    # ==================== MAC 地址厂商查询 ====================
    def create_mac_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="MAC 查询")

        main_frame = tk.LabelFrame(tab, text="MAC 地址厂商查询", padx=15, pady=15,
                                   font=("微软雅黑", 11, "bold"))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        tk.Label(input_frame, text="MAC 地址:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        self.mac_entry = tk.Entry(input_frame, width=25, font=("Consolas", 11))
        self.mac_entry.pack(side=tk.LEFT, padx=5)
        self.mac_entry.insert(0, "00:1A:79:xx:xx:xx")
        self.mac_entry.bind('<Return>', lambda e: self.do_mac_lookup())

        self.mac_btn = tk.Button(input_frame, text="查询厂商", command=self.do_mac_lookup,
                                 bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.mac_btn.pack(side=tk.LEFT, padx=10)

        # 快捷 MAC 示例
        quick_frame = tk.Frame(main_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        tk.Label(quick_frame, text="示例:", font=("微软雅黑", 9), fg="#555555").pack(side=tk.LEFT, padx=5)
        for label, mac in [("Cisco", "00:1A:79:00:00:00"), ("华为", "00:E0:FC:00:00:00"),
                           ("Intel", "00:1C:C0:00:00:00"), ("Apple", "00:03:93:00:00:00"),
                           ("TP-Link", "14:CC:20:00:00:00"), ("小米", "8C:BE:BE:00:00:00")]:
            tk.Button(quick_frame, text=label, command=lambda m=mac: self.set_mac_entry(m),
                      bg="#d5dce6", padx=6, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=2)

        # 批量查询
        batch_frame = tk.LabelFrame(main_frame, text="批量查询 (每行一个 MAC 地址)", padx=10, pady=10,
                                    font=("微软雅黑", 10, "bold"))
        batch_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.mac_batch_text = scrolledtext.ScrolledText(batch_frame, height=8, font=("Consolas", 10))
        self.mac_batch_text.pack(fill=tk.BOTH, expand=True)

        batch_btn_frame = tk.Frame(batch_frame)
        batch_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(batch_btn_frame, text="批量查询", command=self.do_mac_batch,
                  bg="#2780e3", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(batch_btn_frame, text="清空", command=lambda: self.mac_batch_text.delete(1.0, tk.END),
                  bg="#d5dce6", padx=10, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)

        # 查询结果
        result_frame = tk.LabelFrame(main_frame, text="查询结果", padx=10, pady=10,
                                     font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.mac_result = scrolledtext.ScrolledText(result_frame, height=10, font=("Consolas", 10))
        self.mac_result.pack(fill=tk.BOTH, expand=True)

        tip = tk.Label(main_frame, text="提示: MAC 地址格式如 00:1A:79:AB:CD:EF 或 00-1A-79-AB-CD-EF，查询前6位(OUI)即可识别厂商",
                       fg="#555555", font=("微软雅黑", 9))
        tip.pack(pady=5)

    def set_mac_entry(self, mac):
        self.mac_entry.delete(0, tk.END)
        self.mac_entry.insert(0, mac)

    def do_mac_lookup(self):
        """单个 MAC 查询"""
        mac = self.mac_entry.get().strip()
        if not mac:
            return
        self.mac_btn.config(state=tk.DISABLED, text="查询中...")
        self.mac_result.delete(1.0, tk.END)

        def task():
            res = self.net.mac_lookup(mac)
            out = f"MAC 地址: {res['mac']}\n"
            out += f"OUI (厂商码): {res.get('oui', 'N/A')}\n"
            out += f"厂商: {res.get('vendor', '未知')}\n"
            out += "-" * 50 + "\n"
            self.root.after(0, lambda: self.mac_result.insert(tk.END, out))
            self.root.after(0, lambda: self.mac_btn.config(state=tk.NORMAL, text="查询厂商"))

        threading.Thread(target=task, daemon=True).start()

    def do_mac_batch(self):
        """批量 MAC 查询"""
        lines = self.mac_batch_text.get(1.0, tk.END).strip().split('\n')
        macs = [l.strip() for l in lines if l.strip()]
        if not macs:
            return

        self.mac_result.delete(1.0, tk.END)
        self.mac_result.insert(tk.END, f"批量查询 {len(macs)} 个 MAC 地址...\n")
        self.mac_result.insert(tk.END, "=" * 60 + "\n\n")

        def task():
            for mac in macs:
                res = self.net.mac_lookup(mac)
                line = f"{res['mac']:25s}  OUI: {res.get('oui', 'N/A'):6s}  厂商: {res.get('vendor', '未知')}\n"
                self.root.after(0, lambda l=line: self.mac_result.insert(tk.END, l))
            self.root.after(0, lambda: self.mac_result.insert(tk.END, "\n批量查询完成\n"))
            self.root.after(0, lambda: self.mac_result.see(tk.END))

        threading.Thread(target=task, daemon=True).start()

    # ==================== 路由表查看 ====================
    def create_route_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="路由表")

        frame = tk.LabelFrame(tab, text="系统路由表 (route print)", padx=10, pady=10,
                              font=("微软雅黑", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="刷新路由表", command=self.load_route_table,
                  bg="#2780e3", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)

        # 过滤输入
        tk.Label(btn_frame, text="过滤:", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(20, 5))
        self.route_filter = tk.Entry(btn_frame, width=20, font=("Consolas", 10))
        self.route_filter.pack(side=tk.LEFT, padx=5)
        self.route_filter.bind('<KeyRelease>', lambda e: self.filter_route_table())

        self.route_btn = tk.Button(btn_frame, text="应用过滤", command=self.filter_route_table,
                                   bg="#d5dce6", padx=10, font=("微软雅黑", 9))
        self.route_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(btn_frame, text="支持目标网络/IP 过滤", fg="#555555", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)

        self.route_text = scrolledtext.ScrolledText(frame, height=22, font=("Consolas", 10))
        self.route_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.route_text.insert(tk.END, "点击“刷新路由表”加载数据\n")

        self._route_full_output = ""

    def load_route_table(self):
        """加载路由表"""
        self.route_text.delete(1.0, tk.END)
        self.route_text.insert(tk.END, "正在加载路由表...\n")
        self._route_full_output = ""

        def task():
            res = self.sys.get_route_table()
            if res.get("success"):
                self._route_full_output = res["output"]
                self.root.after(0, lambda: self.display_route(res["output"]))
            else:
                self.root.after(0, lambda: self.route_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.route_text.insert(tk.END,
                                                                  f"获取路由表失败: {res.get('error', '未知错误')}"))

        threading.Thread(target=task, daemon=True).start()

    def display_route(self, output):
        self.route_text.delete(1.0, tk.END)
        self.route_text.insert(tk.END, output)

    def filter_route_table(self):
        """过滤路由表"""
        if not self._route_full_output:
            return
        keyword = self.route_filter.get().strip()
        if not keyword:
            self.display_route(self._route_full_output)
            return

        lines = self._route_full_output.split('\n')
        filtered = []
        header_section = True
        for line in lines:
            if header_section or keyword in line:
                filtered.append(line)
            if line.strip().startswith('IPv4 Route Table') or line.strip().startswith('IPv4 路由表'):
                header_section = True
            elif '====' in line or '---' in line or 'Persistent Routes' in line or '永久路由' in line:
                header_section = True
            elif line.strip() and not line.strip().startswith('=') and not line.strip().startswith('-'):
                header_section = False

        self.route_text.delete(1.0, tk.END)
        self.route_text.insert(tk.END, '\n'.join(filtered))
        self.route_text.insert(tk.END, f"\n\n--- 过滤条件: '{keyword}' (显示 {len(filtered)} 行) ---")

    # ==================== ARP 表查看 ====================
    def create_arp_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="ARP 表")

        # 顶部操作栏
        top_frame = tk.LabelFrame(tab, text="ARP 缓存表 (arp -a)", padx=10, pady=10,
                                  font=("微软雅黑", 11, "bold"))
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="刷新 ARP 表", command=self.load_arp_table,
                  bg="#2780e3", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)

        # 搜索过滤
        tk.Label(btn_frame, text="搜索:", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(20, 5))
        self.arp_filter = tk.Entry(btn_frame, width=20, font=("Consolas", 10))
        self.arp_filter.pack(side=tk.LEFT, padx=5)
        self.arp_filter.bind('<KeyRelease>', lambda e: self.filter_arp_table())

        tk.Button(btn_frame, text="搜索", command=self.filter_arp_table,
                  bg="#d5dce6", padx=10, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=5)

        # 统计信息
        self.arp_stats = tk.Label(btn_frame, text="", fg="#555555", font=("微软雅黑", 9))
        self.arp_stats.pack(side=tk.RIGHT, padx=10)

        # 表格化显示
        columns = ("接口", "IP 地址", "MAC 地址", "类型")
        self.arp_tree = ttk.Treeview(top_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.arp_tree.heading(col, text=col)
        self.arp_tree.column("接口", width=200)
        self.arp_tree.column("IP 地址", width=150)
        self.arp_tree.column("MAC 地址", width=180)
        self.arp_tree.column("类型", width=100)

        scrollbar = ttk.Scrollbar(top_frame, orient=tk.VERTICAL, command=self.arp_tree.yview)
        self.arp_tree.configure(yscrollcommand=scrollbar.set)

        self.arp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # 原始输出（可切换）
        raw_frame = tk.LabelFrame(top_frame, text="原始输出 (arp -a)", padx=5, pady=5, font=("微软雅黑", 9))
        raw_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.arp_raw_text = scrolledtext.ScrolledText(raw_frame, height=10, font=("Consolas", 9))
        self.arp_raw_text.pack(fill=tk.BOTH, expand=True)
        self.arp_raw_text.insert(tk.END, "点击“刷新 ARP 表”加载数据\n")

        self._arp_entries = []

    def load_arp_table(self):
        """加载 ARP 表"""
        for item in self.arp_tree.get_children():
            self.arp_tree.delete(item)

        self.arp_tree.insert("", tk.END, values=("加载中...", "", "", ""))

        def task():
            res = self.sys.get_arp_table()
            if res.get("success"):
                self._arp_entries = res.get("entries", [])
                self.root.after(0, lambda: self._display_arp_table())
                self.root.after(0, lambda: self.arp_raw_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.arp_raw_text.insert(tk.END, res.get("output", "")))
            else:
                self.root.after(0, lambda: self.arp_tree.delete(
                    *self.arp_tree.get_children()))
                self.root.after(0, lambda: self.arp_tree.insert(
                    "", tk.END, values=("获取失败", res.get("error", ""), "", "")))

        threading.Thread(target=task, daemon=True).start()

    def _display_arp_table(self, entries=None):
        """显示 ARP 表格"""
        for item in self.arp_tree.get_children():
            self.arp_tree.delete(item)
        entries = entries or self._arp_entries
        for e in entries:
            self.arp_tree.insert("", tk.END, values=(
                e.get("interface", ""),
                e.get("ip", ""),
                e.get("mac", ""),
                e.get("type", "")
            ))
        self.arp_stats.config(
            text=f"共 {len(entries)} 条记录" + (f" (已过滤)" if entries is not self._arp_entries else ""))

    def filter_arp_table(self):
        """过滤 ARP 表"""
        keyword = self.arp_filter.get().strip().lower()
        if not keyword:
            self._display_arp_table()
            return
        filtered = [e for e in self._arp_entries
                    if keyword in e.get("ip", "").lower()
                    or keyword in e.get("mac", "").lower()
                    or keyword in e.get("interface", "").lower()
                    or keyword in e.get("type", "").lower()]
        self._display_arp_table(filtered)

    # ==================== 网卡信息/流量统计 ====================
    def create_netstat_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="网卡信息")

        # 上半部分：流量统计
        stat_frame = tk.LabelFrame(tab, text="网络流量统计", padx=10, pady=10,
                                   font=("微软雅黑", 11, "bold"))
        stat_frame.pack(fill=tk.X, padx=10, pady=10)

        btn_frame = tk.Frame(stat_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="刷新统计", command=self.load_netstat,
                  bg="#2780e3", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)

        self.netstat_refresh_var = tk.BooleanVar(value=False)
        tk.Checkbutton(btn_frame, text="自动刷新 (每3秒)", variable=self.netstat_refresh_var,
                       command=self.toggle_netstat_auto, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=15)

        # 流量数字显示
        cards_frame = tk.Frame(stat_frame)
        cards_frame.pack(fill=tk.X, pady=10)

        # 统计周期说明
        self.netstat_period_label = tk.Label(stat_frame,
                                             text="数据统计周期: 开机至今的累计值 (netstat -e)",
                                             fg="#888", font=("微软雅黑", 8))
        self.netstat_period_label.pack(anchor=tk.W, pady=(0, 5))

        # 接收流量卡片
        rx_card = tk.LabelFrame(cards_frame, text="总接收 (Download)", padx=20, pady=15,
                                font=("微软雅黑", 10, "bold"), fg="#27ae60")
        rx_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.netstat_rx_bytes = tk.Label(rx_card, text="--", font=("Consolas", 22, "bold"), fg="#27ae60")
        self.netstat_rx_bytes.pack()
        self.netstat_rx_label = tk.Label(rx_card, text="MB", font=("微软雅黑", 9), fg="#555555")
        self.netstat_rx_label.pack()

        # 发送流量卡片
        tx_card = tk.LabelFrame(cards_frame, text="总发送 (Upload)", padx=20, pady=15,
                                font=("微软雅黑", 10, "bold"), fg="#e74c3c")
        tx_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.netstat_tx_bytes = tk.Label(tx_card, text="--", font=("Consolas", 22, "bold"), fg="#e74c3c")
        self.netstat_tx_bytes.pack()
        self.netstat_tx_label = tk.Label(tx_card, text="MB", font=("微软雅黑", 9), fg="#555555")
        self.netstat_tx_label.pack()

        # 合计卡片
        total_card = tk.LabelFrame(cards_frame, text="总流量", padx=20, pady=15,
                                   font=("微软雅黑", 10, "bold"), fg="#2780e3")
        total_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.netstat_total_bytes = tk.Label(total_card, text="--", font=("Consolas", 22, "bold"), fg="#2780e3")
        self.netstat_total_bytes.pack()
        self.netstat_total_label = tk.Label(total_card, text="MB", font=("微软雅黑", 9), fg="#555555")
        self.netstat_total_label.pack()

        # 速率卡片（需要两次采样计算）
        self.netstat_rate_label = tk.Label(stat_frame,
                                           text="实时速率: 点击刷新后再次刷新可查看速率 (Mbps)",
                                           fg="#555555", font=("微软雅黑", 9))
        self.netstat_rate_label.pack(anchor=tk.W, pady=5)

        # 下半部分：网卡详细信息
        detail_frame = tk.LabelFrame(tab, text="网卡接口信息", padx=10, pady=10,
                                     font=("微软雅黑", 11, "bold"))
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.netstat_detail = scrolledtext.ScrolledText(detail_frame, height=12, font=("Consolas", 10))
        self.netstat_detail.pack(fill=tk.BOTH, expand=True, pady=5)
        self.netstat_detail.insert(tk.END, "点击“刷新统计”加载数据\n")

        tk.Button(detail_frame, text="刷新网卡信息", command=self.load_netstat,
                  bg="#2780e3", fg="white", padx=15, font=("微软雅黑", 10)).pack(pady=5)

        self._netstat_prev = None  # 用于速率计算
        self._netstat_auto_id = None

    def load_netstat(self):
        """加载网卡流量统计"""
        def task():
            res = self.sys.get_network_stats()
            if res.get("success"):
                rx = res.get("total_bytes_received", 0)
                tx = res.get("total_bytes_sent", 0)

                # 计算速率 (bps -> Mbps)
                now = time.time()
                if self._netstat_prev:
                    prev_rx, prev_tx, prev_time = self._netstat_prev
                    elapsed = now - prev_time
                    if elapsed > 0:
                        rx_rate_bps = (rx - prev_rx) * 8 / elapsed
                        tx_rate_bps = (tx - prev_tx) * 8 / elapsed
                        rate_text = (f"接收: {self._format_speed_mbps(rx_rate_bps)}  |  "
                                     f"发送: {self._format_speed_mbps(tx_rate_bps)}"
                                     f"  (采样间隔 {elapsed:.1f}s)")
                        self.root.after(0, lambda: self.netstat_rate_label.config(
                            text=f"实时速率: {rate_text}", fg="#2c3e50"))
                self._netstat_prev = (rx, tx, now)

                total = rx + tx

                self.root.after(0, lambda: self.netstat_rx_bytes.config(text=self._format_mb(rx)))
                self.root.after(0, lambda: self.netstat_tx_bytes.config(text=self._format_mb(tx)))
                self.root.after(0, lambda: self.netstat_total_bytes.config(text=self._format_mb(total)))

                # 显示网卡详细信息
                iface_info = res.get("interfaces_raw", "")
                self.root.after(0, lambda: self.netstat_detail.delete(1.0, tk.END))
                self.root.after(0, lambda: self.netstat_detail.insert(tk.END, iface_info))

                # 显示 netstat 原始输出
                ns_raw = res.get("netstat_raw", "")
                if ns_raw:
                    self.root.after(0, lambda: self.netstat_detail.insert(tk.END,
                                                                          "\n" + "=" * 60 + "\n网络统计 (netstat -e):\n" + "=" * 60 + "\n"))
                    self.root.after(0, lambda: self.netstat_detail.insert(tk.END, ns_raw))
            else:
                self.root.after(0, lambda: self.netstat_rx_bytes.config(text="错误"))
                self.root.after(0, lambda: self.netstat_tx_bytes.config(text="错误"))

        threading.Thread(target=task, daemon=True).start()

    def toggle_netstat_auto(self):
        """切换自动刷新"""
        if self.netstat_refresh_var.get():
            self._start_netstat_auto()
        else:
            self._stop_netstat_auto()

    def _start_netstat_auto(self):
        """启动自动刷新"""
        self.load_netstat()
        self._netstat_auto_id = self.root.after(3000, self._start_netstat_auto)

    def _stop_netstat_auto(self):
        """停止自动刷新"""
        if self._netstat_auto_id:
            self.root.after_cancel(self._netstat_auto_id)
            self._netstat_auto_id = None

    @staticmethod
    def _format_mb(b):
        """格式化字节数为 MB/GB/TB"""
        if b >= 1024 ** 4:
            return f"{b / 1024 ** 4:.2f} TB"
        elif b >= 1024 ** 3:
            return f"{b / 1024 ** 3:.2f} GB"
        elif b >= 1024 ** 2:
            return f"{b / 1024 ** 2:.2f} MB"
        elif b >= 1024:
            return f"{b / 1024:.2f} KB"
        else:
            return f"{b} B"

    @staticmethod
    def _format_speed_mbps(bps):
        """格式化速率为 Mbps"""
        if bps >= 1000 ** 3:
            return f"{bps / 1000 ** 3:.2f} Gbps"
        elif bps >= 1000 ** 2:
            return f"{bps / 1000 ** 2:.2f} Mbps"
        elif bps >= 1000:
            return f"{bps / 1000:.1f} Kbps"
        else:
            return f"{bps:.0f} bps"

    # ==================== WiFi 密码 ====================
    def create_utility_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="WiFi 密码")

        wifi_frame = tk.LabelFrame(tab, text="已保存的 WiFi 密码查看", padx=15, pady=15,
                                   font=("微软雅黑", 11, "bold"))
        wifi_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        info = tk.Label(wifi_frame, text="查看本机已连接过的所有 WiFi 密码（需要管理员权限）",
                        fg="#555555", font=("微软雅黑", 9))
        info.pack(anchor=tk.W, pady=(0, 10))

        btn_frame = tk.Frame(wifi_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        self.wifi_btn = tk.Button(btn_frame, text="查看 WiFi 密码", command=self.show_wifi_passwords,
                                  bg="#8e44ad", fg="white", padx=20, font=("微软雅黑", 10))
        self.wifi_btn.pack(side=tk.LEFT, padx=5)

        self.wifi_result_text = scrolledtext.ScrolledText(wifi_frame, height=25, font=("Consolas", 10))
        self.wifi_result_text.pack(fill=tk.BOTH, expand=True, pady=10)

    def show_wifi_passwords(self):
        self.wifi_result_text.delete(1.0, tk.END)
        results = self.sys.get_wifi_passwords()
        if results and "error" in results[0]:
            err = results[0].get("error", "未知错误")
            self.wifi_result_text.insert(tk.END, "获取失败: " + err + "\n\n提示: 需要以管理员身份运行")
        else:
            for item in results:
                ssid = item.get("ssid", "未知")
                pwd = item.get("password", "未知")
                self.wifi_result_text.insert(tk.END, "SSID: " + ssid + "\n密码: " + pwd + "\n\n")
            if not results:
                self.wifi_result_text.insert(tk.END, "未找到已保存的 WiFi 信息")

    # ==================== 公网 IP ====================
    def create_public_ip_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="公网 IP")

        main = tk.LabelFrame(tab, text="公网出口地址查询", padx=15, pady=15, font=("微软雅黑", 11, "bold"))
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        info = tk.Label(main, text="查询当前网络的公网出口 IP 地址", fg="#555555", font=("微软雅黑", 10))
        info.pack(anchor=tk.W, pady=(0, 10))

        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=5)
        self.pub_btn = tk.Button(btn_frame, text="查询公网 IP", command=self.get_public_ip,
                                 bg="#e74c3c", fg="white", padx=15, font=("微软雅黑", 10))
        self.pub_btn.pack(side=tk.LEFT, padx=5)
        self.copy_pub_btn = tk.Button(btn_frame, text="复制 IP", command=self.copy_public_ip,
                                      bg="#27ae60", fg="white", padx=15, font=("微软雅黑", 10), state=tk.DISABLED)
        self.copy_pub_btn.pack(side=tk.LEFT, padx=5)

        res_frame = tk.LabelFrame(main, text="查询结果", padx=10, pady=10)
        res_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.ip_val_label = tk.Label(res_frame, text="未查询", font=("Consolas", 28, "bold"), fg="#2c3e50")
        self.ip_val_label.pack(pady=15)
        self.pub_result = scrolledtext.ScrolledText(res_frame, height=5, font=("Consolas", 10))
        self.pub_result.pack(fill=tk.BOTH, expand=True)

    def get_public_ip(self):
        def task():
            self.pub_btn.config(state=tk.DISABLED, text="查询中...")
            self.copy_pub_btn.config(state=tk.DISABLED)
            self.pub_result.delete(1.0, tk.END)
            self.ip_val_label.config(text="查询中...", fg="#f39c12")

            res = self.net.get_public_ip()

            if res.get("success"):
                self.root.after(0, lambda: self.ip_val_label.config(text=res["ip"], fg="#27ae60"))
                self.root.after(0, lambda: self.pub_result.insert(tk.END,
                                                                  f"公网 IP: {res['ip']}\n来源: {res['source']}\n查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
                self.root.after(0, lambda: self.copy_pub_btn.config(state=tk.NORMAL))
            else:
                self.root.after(0, lambda: self.ip_val_label.config(text="查询失败", fg="#c0392b"))
                self.root.after(0, lambda: self.pub_result.insert(tk.END, "无法获取公网 IP，请检查网络连接"))

            self.root.after(0, lambda: self.pub_btn.config(state=tk.NORMAL, text="查询公网 IP"))

        threading.Thread(target=task, daemon=True).start()

    def copy_public_ip(self):
        ip = self.ip_val_label.cget("text")
        if ip and ip not in ["未查询", "查询中...", "查询失败"]:
            self.root.clipboard_clear()
            self.root.clipboard_append(ip)
            messagebox.showinfo("成功", f"已复制 IP: {ip}")

    # ==================== 网络诊断 ====================
    def create_diagnostic_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="网络诊断")

        # 使用 Notebook 分两个子页
        diag_notebook = ttk.Notebook(tab)
        diag_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ==================== 子页1：一键诊断向导 ====================
        wizard_frame = tk.Frame(diag_notebook, bg="#e8ecf1")
        diag_notebook.add(wizard_frame, text="一键诊断向导")

        # 顶部横幅区域
        banner = tk.Frame(wizard_frame, bg="#d5dce6", height=70)
        banner.pack(fill=tk.X, padx=10, pady=(10, 8))
        banner.pack_propagate(False)

        banner_left = tk.Frame(banner, bg="#d5dce6")
        banner_left.pack(side=tk.LEFT, padx=20, pady=12)

        tk.Label(banner_left, text="🔍", font=("Segoe UI Emoji", 22), bg="#d5dce6").pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(banner_left, text="一键网络诊断向导", font=("微软雅黑", 16, "bold"),
                 fg="#2c3e50", bg="#d5dce6").pack(side=tk.LEFT)

        tk.Label(banner_left, text="  |  自动检测网卡 → IP → 网关 → DNS → 外网 → 常用网站，快速定位问题",
                 font=("微软雅黑", 9), fg="#555555", bg="#d5dce6").pack(side=tk.LEFT, padx=(10, 0))

        banner_right = tk.Frame(banner, bg="#d5dce6")
        banner_right.pack(side=tk.RIGHT, padx=15, pady=14)
        self.wizard_btn = tk.Button(banner_right, text="🚀  开始诊断", command=self.do_wizard_diagnostic,
                                    bg="#e74c3c", fg="white", padx=20, font=("微软雅黑", 11, "bold"),
                                    cursor="hand2", activebackground="#c0392b", activeforeground="white",
                                    relief=tk.FLAT, bd=0)
        self.wizard_btn.pack(side=tk.LEFT, padx=3)
        self.wizard_stop_btn = tk.Button(banner_right, text="⏹ 停止", command=self.stop_wizard,
                                         bg="#7f8c8d", fg="white", padx=12, font=("微软雅黑", 10),
                                         state=tk.DISABLED, cursor="hand2", relief=tk.FLAT, bd=0)
        self.wizard_stop_btn.pack(side=tk.LEFT, padx=3)

        # 主体区域：左右分栏
        main_paned = tk.PanedWindow(wizard_frame, orient=tk.HORIZONTAL, bg="#e8ecf1",
                                    sashwidth=3, sashrelief=tk.GROOVE)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 左侧：检测步骤列表（卡片式）
        left_frame = tk.Frame(main_paned, bg="#e8ecf1", width=350)
        main_paned.add(left_frame)

        tk.Label(left_frame, text="检测步骤", font=("微软雅黑", 11, "bold"),
                 fg="#e74c3c", bg="#e8ecf1").pack(anchor=tk.W, pady=(5, 8))

        self.wizard_steps = {}
        step_configs = [
            ("nic", "1", "网卡状态", "检查本地网络连接是否正常"),
            ("ip", "2", "IP 地址", "是否获取到有效 IP 地址"),
            ("gateway", "3", "默认网关", "是否能连通路由器/网关"),
            ("dns", "4", "DNS 解析", "DNS 服务器是否正常响应"),
            ("internet", "5", "外网连通", "能否访问互联网"),
            ("websites", "6", "常用网站", "百度、腾讯等访问速度"),
        ]

        for key, num, title, desc in step_configs:
            card = tk.Frame(left_frame, bg="#ffffff", bd=1, relief=tk.GROOVE)
            card.pack(fill=tk.X, pady=3)

            card_inner = tk.Frame(card, bg="#ffffff")
            card_inner.pack(fill=tk.X, padx=10, pady=8)

            # 左侧：步骤编号圆圈
            dot = tk.Label(card_inner, text=num, font=("Consolas", 12, "bold"),
                           fg="#555555", bg="#e8ecf1", width=3, height=1,
                           relief=tk.GROOVE, bd=1)
            dot.pack(side=tk.LEFT, padx=(0, 10))

            # 右侧：标题和描述
            text_col = tk.Frame(card_inner, bg="#ffffff")
            text_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

            title_label = tk.Label(text_col, text=title, font=("微软雅黑", 11, "bold"),
                                   fg="#333333", bg="#ffffff", anchor=tk.W)
            title_label.pack(anchor=tk.W)
            result_label = tk.Label(text_col, text=desc, font=("微软雅黑", 8),
                                    fg="#555555", bg="#ffffff", anchor=tk.W)
            result_label.pack(anchor=tk.W)

            # 状态图标（右侧）
            status_icon = tk.Label(card_inner, text="", font=("Segoe UI Emoji", 14),
                                   bg="#ffffff", width=2)
            status_icon.pack(side=tk.RIGHT)

            self.wizard_steps[key] = {"dot": dot, "title": title_label, "desc": result_label,
                                      "icon": status_icon, "card": card}

        # 右侧：结果输出区
        right_frame = tk.Frame(main_paned, bg="#e8ecf1")
        main_paned.add(right_frame)

        result_header = tk.Frame(right_frame, bg="#e8ecf1")
        result_header.pack(fill=tk.X, pady=(5, 5))
        tk.Label(result_header, text="诊断结果与建议", font=("微软雅黑", 11, "bold"),
                 fg="#27ae60", bg="#e8ecf1").pack(side=tk.LEFT)

        # 诊断进度条
        self.wizard_progress = ttk.Progressbar(right_frame, mode='indeterminate', length=300)
        self.wizard_progress.pack(fill=tk.X, pady=(0, 5))
        self.wizard_progress.pack_forget()

        self.wizard_suggestion = scrolledtext.ScrolledText(right_frame,
                                                           font=("微软雅黑", 10), bg="#ffffff",
                                                           fg="#333333", wrap=tk.WORD,
                                                           insertbackground="#e94560")
        self.wizard_suggestion.pack(fill=tk.BOTH, expand=True)

        # 初始提示
        self.wizard_suggestion.insert(tk.END,
            "欢迎使用一键网络诊断向导！\n\n"
            "📋 使用方法：\n"
            "  点击左上角「🚀 开始诊断」按钮，系统将自动依次检测\n"
            "  您的网络状态，并在右侧显示详细结果。\n\n"
            "⏱ 诊断过程约需 10-20 秒\n"
            "💡 检测结束后会给出针对性的修复建议\n"
            "🛑 如需中途停止，点击「⏹ 停止」按钮\n\n"
            "请确保您已连接网络后开始检测。"
        )

        # ==================== 子页2：单项检测工具 ====================
        tool_frame = ttk.Frame(diag_notebook)
        diag_notebook.add(tool_frame, text="单项检测")

        # --- 自定义 Ping 测试 ---
        ping_frame = tk.LabelFrame(tool_frame, text="Ping 测试", padx=10, pady=10,
                                   font=("微软雅黑", 10, "bold"))
        ping_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ping_input = tk.Frame(ping_frame)
        ping_input.pack(fill=tk.X, pady=5)
        tk.Label(ping_input, text="目标 IP/域名:").pack(side=tk.LEFT, padx=5)
        self.custom_ping_target = tk.Entry(ping_input, width=25, font=("Consolas", 10))
        self.custom_ping_target.pack(side=tk.LEFT, padx=5)
        self.custom_ping_target.insert(0, "www.baidu.com")

        tk.Label(ping_input, text="次数:").pack(side=tk.LEFT, padx=(15, 5))
        self.custom_ping_count = ttk.Combobox(ping_input, values=["2", "4", "8", "16", "32"],
                                              width=4, font=("Consolas", 10), state="readonly")
        self.custom_ping_count.pack(side=tk.LEFT, padx=5)
        self.custom_ping_count.current(1)

        self.custom_ping_btn = tk.Button(ping_input, text="Ping", command=self.do_custom_ping,
                                         bg="#2780e3", fg="white", padx=15, font=("微软雅黑", 10))
        self.custom_ping_btn.pack(side=tk.LEFT, padx=15)

        self.custom_ping_result = scrolledtext.ScrolledText(ping_frame, height=4,
                                                            font=("Consolas", 9))
        self.custom_ping_result.pack(fill=tk.X, pady=5)

        # --- DNS 重置 ---
        dns_frame = tk.LabelFrame(tool_frame, text="DNS 重置", padx=10, pady=10,
                                  font=("微软雅黑", 10, "bold"))
        dns_frame.pack(fill=tk.X, padx=10, pady=5)

        btn2_frame = tk.Frame(dns_frame)
        btn2_frame.pack(fill=tk.X)
        self.dns_reset_btn = tk.Button(btn2_frame, text="重置 DNS 缓存", command=self.do_reset_dns,
                                       bg="#e67e22", fg="white", padx=15, font=("微软雅黑", 10))
        self.dns_reset_btn.pack(side=tk.LEFT, padx=5)
        tk.Label(btn2_frame, text="刷新 DNS 缓存、重新注册 DNS、清除 NetBIOS 缓存",
                 fg="#555555", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=10)

        self.dns_reset_result = scrolledtext.ScrolledText(dns_frame, height=4, font=("Consolas", 9))
        self.dns_reset_result.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # --- 本机信息 ---
        info_frame = tk.LabelFrame(tool_frame, text="本机网络信息", padx=10, pady=10,
                                   font=("微软雅黑", 10, "bold"))
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        btn3_frame = tk.Frame(info_frame)
        btn3_frame.pack(fill=tk.X, pady=(0, 5))
        self.local_info_btn = tk.Button(btn3_frame, text="查看本机信息", command=self.do_local_info,
                                        bg="#27ae60", fg="white", padx=15, font=("微软雅黑", 10))
        self.local_info_btn.pack(side=tk.LEFT, padx=5)

        self.diag_local_info = scrolledtext.ScrolledText(info_frame, height=8, font=("Consolas", 9))
        self.diag_local_info.pack(fill=tk.BOTH, expand=True)

        # 诊断取消标志
        self._wizard_cancel = False

    def stop_wizard(self):
        """停止向导诊断"""
        self._wizard_cancel = True
        self.wizard_stop_btn.config(state=tk.DISABLED)
        self.wizard_progress.stop()
        self.wizard_progress.pack_forget()
        self.wizard_btn.config(state=tk.NORMAL, text="🔄  重新诊断")

    def do_wizard_diagnostic(self):
        """一键诊断向导"""
        self._wizard_cancel = False
        self.wizard_btn.config(state=tk.DISABLED, text="⏳ 诊断中...")
        self.wizard_stop_btn.config(state=tk.NORMAL)
        self.wizard_suggestion.delete(1.0, tk.END)
        self.wizard_suggestion.insert(tk.END, "🔄 正在执行网络诊断，请稍候...\n\n")

        # 显示进度条
        self.wizard_progress.pack(fill=tk.X, pady=(0, 5))
        self.wizard_progress.start(15)

        # 重置所有步骤状态为卡片样式
        for key in self.wizard_steps:
            sd = self.wizard_steps[key]
            sd["dot"].config(text=sd["dot"].cget("text").split("\n")[0] if "\n" in (sd["dot"].cget("text") or "") else sd["dot"].cget("text"),
                           fg="#555555", bg="#e8ecf1")
            sd["title"].config(fg="#333333")
            sd["desc"].config(text="等待检测", fg="#555555")
            sd["icon"].config(text="")
            sd["card"].config(bg="#ffffff")
            # 恢复步骤编号
            step_nums = {"nic": "1", "ip": "2", "gateway": "3", "dns": "4",
                        "internet": "5", "websites": "6"}
            sd["dot"].config(text=step_nums.get(key, "?"))

        def task():
            import time

            def update_step(key, status, result_text, detail_color="#333333"):
                """更新步骤状态: status = 'running'|'pass'|'fail'|'warn'"""
                if self._wizard_cancel:
                    return
                sd = self.wizard_steps[key]
                icons_map = {
                    "running": ("⏳", "#f39c12"),
                    "pass": ("✅", "#27ae60"),
                    "fail": ("❌", "#e74c3c"),
                    "warn": ("⚠️", "#f39c12")
                }
                icon_char, icon_color = icons_map.get(status, ("⬜", "#555"))
                bg_colors = {
                    "running": "#fff3cd",
                    "pass": "#d4edda",
                    "fail": "#f8d7da",
                    "warn": "#fff3cd"
                }

                def apply():
                    sd["icon"].config(text=icon_char)
                    sd["desc"].config(text=result_text, fg=detail_color)
                    sd["card"].config(bg=bg_colors.get(status, "#ffffff"))
                    if status == "running":
                        sd["dot"].config(text="...", fg="#f39c12", bg="#f39c12")
                        sd["title"].config(fg="#f39c12")
                    elif status == "pass":
                        sd["dot"].config(text="✓", fg="#27ae60", bg="#e8ecf1")
                        sd["title"].config(fg="#27ae60")
                    elif status == "fail":
                        sd["dot"].config(text="✗", fg="#c0392b", bg="#e8ecf1")
                        sd["title"].config(fg="#c0392b")
                    elif status == "warn":
                        sd["dot"].config(text="!", fg="#f39c12", bg="#e8ecf1")
                        sd["title"].config(fg="#f39c12")
                self.root.after(0, apply)

            # 步骤1: 检查网卡状态
            update_step("nic", "running", "检测中...")
            time.sleep(0.5)
            if self._wizard_cancel:
                self.root.after(0, self._wizard_finish)
                return
            nic_info = self.sys.get_local_network_info()
            if nic_info.get("success"):
                update_step("nic", "pass", "网卡正常", "#27ae60")
            else:
                update_step("nic", "fail", "网卡异常，请检查网络连接", "#e74c3c")
                update_step("ip", "fail", "跳过（网卡异常）", "#e74c3c")
                update_step("gateway", "fail", "跳过（网卡异常）", "#e74c3c")
                update_step("dns", "fail", "跳过（网卡异常）", "#e74c3c")
                update_step("internet", "fail", "跳过（网卡异常）", "#e74c3c")
                update_step("websites", "fail", "跳过（网卡异常）", "#e74c3c")
                self.root.after(0, lambda: self.wizard_suggestion.insert(
                    tk.END,
                    "⚠ 诊断结果：网卡未正常工作\n\n"
                    "修复建议：\n"
                    "  1. 检查网线是否插好或 WiFi 是否已连接\n"
                    "  2. 尝试禁用再启用网卡\n"
                    "  3. 重启电脑试试\n"
                    "  4. 如果仍无法解决，请联系 IT 支持"))
                self.root.after(0, self._wizard_finish)
                return

            # 步骤2: 检查 IP 地址
            update_step("ip", "running", "检测中...")
            time.sleep(0.5)
            if self._wizard_cancel:
                self.root.after(0, self._wizard_finish)
                return
            ip_info = self.sys.get_ip_info()
            local_ip = ip_info.get("local_ip", "")
            if local_ip and not local_ip.startswith("169.254"):
                update_step("ip", "pass", f"IP: {local_ip}", "#27ae60")
            elif local_ip.startswith("169.254"):
                update_step("ip", "warn",
                            f"IP: {local_ip} (未获取到有效IP，DHCP可能异常)", "#f39c12")
            else:
                update_step("ip", "fail", "未获取到IP地址", "#e74c3c")

            # 步骤3: 检查网关
            update_step("gateway", "running", "检测中...")
            time.sleep(0.5)
            if self._wizard_cancel:
                self.root.after(0, self._wizard_finish)
                return
            gateway_info = self.sys.ping_gateway()
            gateway_ip = gateway_info.get("gateway_ip", "")
            gateway_result = gateway_info.get("result", "")
            if gateway_result == "通畅":
                update_step("gateway", "pass",
                            f"网关 {gateway_ip} 连通 ({gateway_info.get('latency', '')})",
                            "#27ae60")
            elif gateway_ip:
                update_step("gateway", "fail",
                            f"网关 {gateway_ip} 不通，请检查路由器/交换机", "#e74c3c")
            else:
                update_step("gateway", "fail", "未找到默认网关", "#e74c3c")

            # 步骤4: 检查 DNS
            update_step("dns", "running", "检测中...")
            time.sleep(0.5)
            if self._wizard_cancel:
                self.root.after(0, self._wizard_finish)
                return
            dns_info = self.sys.test_dns()
            dns_status = dns_info.get("status", "")
            if dns_status == "正常":
                update_step("dns", "pass", f"DNS 正常 ({dns_info.get('latency', '')})",
                            "#27ae60")
            else:
                update_step("dns", "fail", f"DNS 异常: {dns_status}", "#e74c3c")

            # 步骤5: 检查外网
            update_step("internet", "running", "检测中...")
            time.sleep(0.5)
            if self._wizard_cancel:
                self.root.after(0, self._wizard_finish)
                return
            net_info = self.sys.test_internet()
            net_result = net_info.get("result", "")
            if net_result == "通畅":
                update_step("internet", "pass",
                            f"外网连通 ({net_info.get('latency', '')})", "#27ae60")
            else:
                update_step("internet", "fail",
                            f"外网不通: {net_info.get('error', '')}", "#e74c3c")

            # 步骤6: 常用网站检测
            update_step("websites", "running", "检测中...")
            time.sleep(0.5)
            if self._wizard_cancel:
                self.root.after(0, self._wizard_finish)
                return
            websites = {
                "百度": "www.baidu.com",
                "腾讯": "www.qq.com",
                "阿里": "www.aliyun.com",
            }
            web_results = []
            for name, host in websites.items():
                if self._wizard_cancel:
                    break
                r = self.sys.ping_host(host, count=2)
                latency = r.get("latency", "超时")
                web_results.append(f"{name}({host}): {latency}")

            all_ok = all("超时" not in w for w in web_results)
            if all_ok:
                update_step("websites", "pass",
                            " | ".join(web_results), "#27ae60")
            elif any("超时" not in w for w in web_results):
                update_step("websites", "warn",
                            " | ".join(web_results), "#f39c12")
            else:
                update_step("websites", "fail",
                            "所有网站均无法访问", "#e74c3c")

            # 输出结果摘要
            summary = "✅ 网络诊断完成！\n\n"
            for key in ["nic", "ip", "gateway", "dns", "internet", "websites"]:
                desc_text = self.wizard_steps[key]["desc"].cget("text")
                summary += f"  {desc_text}\n"

            summary += "\n💡 提示：如需详细修复建议，请查看「单项检测」标签页中的各项工具。"
            self.root.after(0, lambda: self.wizard_suggestion.insert(tk.END, summary))
            self.root.after(0, self._wizard_finish)

        threading.Thread(target=task, daemon=True).start()

    def _wizard_finish(self):
        """诊断向导完成"""
        self.wizard_btn.config(state=tk.NORMAL, text="🔄  重新诊断")
        self.wizard_stop_btn.config(state=tk.DISABLED)
        self.wizard_progress.stop()
        self.wizard_progress.pack_forget()
        self.status.config(text="一键诊断完成")

    def do_custom_ping(self):
        """自定义 Ping 测试"""
        target = self.custom_ping_target.get().strip()
        if not target:
            self.custom_ping_result.delete(1.0, tk.END)
            self.custom_ping_result.insert(tk.END, "请输入目标 IP 或域名")
            return

        try:
            count = int(self.custom_ping_count.get())
        except Exception:
            count = 4

        self.custom_ping_btn.config(state=tk.DISABLED, text="Ping 中...")

        def task():
            result = self.sys.ping_host(target, count=count)
            self.root.after(0, lambda: self.custom_ping_result.delete(1.0, tk.END))
            out = f"Ping {target} ({count} 次)\n"
            out += f"延迟: {result.get('latency', '超时')}\n"
            out += f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.root.after(0, lambda: self.custom_ping_result.insert(tk.END, out))
            self.root.after(0, lambda: self.custom_ping_btn.config(
                state=tk.NORMAL, text="Ping"))

        threading.Thread(target=task, daemon=True).start()

    def do_reset_dns(self):
        def task():
            self.dns_reset_btn.config(state=tk.DISABLED, text="重置中...")
            result = self.sys.reset_dns()
            self.root.after(0, lambda: self.dns_reset_result.delete(1.0, tk.END))
            self.root.after(0, lambda: self.dns_reset_result.insert(tk.END, result))
            self.root.after(0, lambda: self.dns_reset_btn.config(
                state=tk.NORMAL, text="重置 DNS 缓存"))

        threading.Thread(target=task, daemon=True).start()

    def do_local_info(self):
        def task():
            self.local_info_btn.config(state=tk.DISABLED, text="查询中...")
            res = self.sys.get_local_network_info()
            self.root.after(0, lambda: self.diag_local_info.delete(1.0, tk.END))
            if res.get("success"):
                self.root.after(0, lambda: self.diag_local_info.insert(tk.END, res["output"]))
            else:
                self.root.after(0, lambda: self.diag_local_info.insert(
                    tk.END, f"错误: {res.get('error', '未知')}"))
            self.root.after(0, lambda: self.local_info_btn.config(
                state=tk.NORMAL, text="查看本机信息"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== 域账号查询 ====================
    def create_domain_user_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="域账号查询")

        # 输入区
        input_frame = tk.LabelFrame(tab, text="域账号查询", padx=10, pady=10,
                                    font=("微软雅黑", 10, "bold"))
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(input_frame, text="用户名:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        self.domain_user_entry = tk.Entry(input_frame, width=30, font=("Consolas", 10))
        self.domain_user_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.domain_user_btn = tk.Button(input_frame, text="查询", command=self.do_domain_user_query,
                                         bg="#e74c3c", fg="white", font=("微软雅黑", 10), padx=20)
        self.domain_user_btn.pack(side=tk.LEFT, padx=10)

        tk.Label(input_frame, text="（留空则查询当前用户）", fg="#555555",
                 font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=5)

        # 结果展示区
        result_frame = tk.LabelFrame(tab, text="查询结果", padx=10, pady=10,
                                     font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 使用 Canvas + Scrollbar 展示结果
        canvas_container = tk.Frame(result_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.domain_result_canvas = tk.Canvas(canvas_container, bg="#e8ecf1", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical",
                                  command=self.domain_result_canvas.yview)
        self.domain_result_frame = tk.Frame(self.domain_result_canvas, bg="#e8ecf1")

        self.domain_result_frame.bind("<Configure>",
                                      lambda e: self.domain_result_canvas.configure(
                                          scrollregion=self.domain_result_canvas.bbox("all")))

        self.domain_result_canvas.create_window((0, 0), window=self.domain_result_frame, anchor="nw",
                                                tags="result_frame")
        self.domain_result_canvas.configure(yscrollcommand=scrollbar.set)

        self.domain_result_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            self.domain_result_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.domain_result_canvas.bind("<Enter>",
                                       lambda e: self.domain_result_canvas.bind_all(
                                           "<MouseWheel>", _on_mousewheel))
        self.domain_result_canvas.bind("<Leave>",
                                       lambda e: self.domain_result_canvas.unbind_all("<MouseWheel>"))

        # 提示
        tip_frame = tk.Frame(tab, bg="#e8ecf1")
        tip_frame.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(tip_frame,
                 text="提示：仅支持在已加入域环境的电脑上查询域账号，需要域网络连通。",
                 fg="#f39c12", font=("微软雅黑", 8), bg="#e8ecf1").pack(side=tk.LEFT)

    def do_domain_user_query(self):
        """执行域账号查询"""
        username = self.domain_user_entry.get().strip()
        if not username:
            username = os.environ.get('USERNAME', '')

        # 清除旧结果
        for widget in self.domain_result_frame.winfo_children():
            widget.destroy()

        self.domain_user_btn.config(text="查询中...", state="disabled")
        self.status.config(text="正在查询域账号信息...")
        self.root.update()

        def task():
            try:
                result = self.sys.domain_user_query(username)
            except Exception as e:
                result = {"success": False, "error": str(e)}

            self.root.after(0, lambda: self._show_domain_user_result(result))

        threading.Thread(target=task, daemon=True).start()

    def _show_domain_user_result(self, result):
        """展示域账号查询结果"""
        self.domain_user_btn.config(text="查询", state="normal")

        if not result.get("success"):
            tk.Label(self.domain_result_frame, text=f"查询失败: {result.get('error', '未知错误')}",
                     fg="#c0392b", font=("微软雅黑", 11, "bold"), bg="#e8ecf1",
                     wraplength=600, justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=10)
            self.status.config(text="域账号查询失败")
            return

        # 关键字段展示
        key_fields = [
            ("username", "用户名"),
            ("full_name", "全名"),
            ("comment", "注释"),
            ("account_active", "帐户状态"),
            ("account_expires", "帐户到期"),
            ("password_last_set", "上次设置密码"),
            ("password_expires", "密码到期"),
            ("password_changeable", "密码可更改"),
            ("password_required", "需要密码"),
            ("user_may_change_pwd", "用户可更改密码"),
            ("last_logon", "上次登录"),
            ("logon_hours", "登录时段"),
            ("workstations", "允许的工作站"),
            ("logon_script", "登录脚本"),
            ("user_profile", "用户配置文件"),
            ("home_directory", "主目录"),
            ("country_code", "国家/地区代码"),
        ]

        # 标题
        tk.Label(self.domain_result_frame,
                 text=f"域账号: {result.get('username', '')}",
                 fg="#27ae60", font=("微软雅黑", 13, "bold"), bg="#e8ecf1").pack(
            anchor=tk.W, padx=15, pady=(15, 10))

        # 分隔线
        tk.Frame(self.domain_result_frame, height=1, bg="#aeb6bf").pack(fill=tk.X, padx=15)

        # 详细信息
        info_frame = tk.Frame(self.domain_result_frame, bg="#e8ecf1")
        info_frame.pack(fill=tk.X, padx=15, pady=5)

        for i, (key, label) in enumerate(key_fields):
            value = result.get(key, "")
            if not value:
                continue

            row_frame = tk.Frame(info_frame, bg="#e8ecf1")
            row_frame.pack(fill=tk.X, pady=2)

            tk.Label(row_frame, text=f"{label}:", width=14, anchor=tk.E,
                     fg="#444444", font=("微软雅黑", 9, "bold"), bg="#e8ecf1").pack(
                side=tk.LEFT, padx=(0, 10))

            # 高亮关键信息
            color = "#222222"  # 默认深色，确保可读
            if key == "account_active" and "no" in str(value).lower():
                color = "#c0392b"
            elif key == "account_active" and "yes" in str(value).lower():
                color = "#27ae60"
            elif key == "password_expires" and "never" not in str(value).lower():
                color = "#d35400"

            tk.Label(row_frame, text=str(value), fg=color,
                     font=("Consolas", 10), bg="#e8ecf1", wraplength=500,
                     justify=tk.LEFT).pack(side=tk.LEFT)

        # 组信息
        groups = result.get("domain_groups", [])
        if groups:
            tk.Frame(self.domain_result_frame, height=1, bg="#aeb6bf").pack(fill=tk.X, padx=15, pady=(15, 0))
            tk.Label(self.domain_result_frame, text="所属域组:",
                     fg="#444444", font=("微软雅黑", 9, "bold"), bg="#e8ecf1").pack(
                anchor=tk.W, padx=15, pady=(10, 5))

            group_frame = tk.Frame(self.domain_result_frame, bg="#e8ecf1")
            group_frame.pack(fill=tk.X, padx=15, pady=5)

            for g in groups:
                tk.Label(group_frame, text=f"  ● {g}", fg="#2780e3",
                         font=("Consolas", 9), bg="#e8ecf1",
                         anchor=tk.W).pack(fill=tk.X, pady=1)

        # 原始输出
        raw = result.get("raw", "")
        if raw:
            tk.Frame(self.domain_result_frame, height=1, bg="#aeb6bf").pack(fill=tk.X, padx=15, pady=(15, 0))
            tk.Label(self.domain_result_frame, text="原始输出:",
                     fg="#444444", font=("微软雅黑", 9, "bold"), bg="#e8ecf1").pack(
                anchor=tk.W, padx=15, pady=(10, 5))

            raw_text = tk.Text(self.domain_result_frame, height=12, font=("Consolas", 9),
                               bg="#ffffff", fg="#444444", wrap=tk.WORD, bd=1, relief=tk.SOLID)
            raw_text.pack(fill=tk.X, padx=15, pady=(0, 15))
            raw_text.insert("1.0", raw)
            raw_text.config(state="disabled")

        self.status.config(text=f"域账号 {result.get('username', '')} 查询完成")

    # ==================== 系统信息 ====================
    def create_system_info_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="系统信息")

        # 顶部操作栏
        top_frame = tk.Frame(tab, bg="#e8ecf1")
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(top_frame, text="系统信息", font=("微软雅黑", 14, "bold"),
                 fg="#e74c3c", bg="#e8ecf1").pack(side=tk.LEFT, padx=5)

        self.sysinfo_btn = tk.Button(top_frame, text="刷新信息", command=self.do_system_info,
                                     bg="#2780e3", fg="white", padx=20, font=("微软雅黑", 10))
        self.sysinfo_btn.pack(side=tk.RIGHT, padx=10)

        # 主信息面板（使用 Canvas + Scrollbar 支持滚动）
        canvas_frame = tk.Frame(tab)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.sysinfo_canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.sysinfo_canvas.yview)
        self.sysinfo_inner = tk.Frame(self.sysinfo_canvas, bg="#ffffff")

        self.sysinfo_inner.bind("<Configure>",
                                lambda e: self.sysinfo_canvas.configure(scrollregion=self.sysinfo_canvas.bbox("all")))
        self.sysinfo_canvas.create_window((0, 0), window=self.sysinfo_inner, anchor=tk.NW, tags="inner")

        self.sysinfo_canvas.configure(yscrollcommand=scrollbar.set)
        self.sysinfo_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮
        def on_mousewheel(event):
            self.sysinfo_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.sysinfo_canvas.bind("<Enter>", lambda e: self.sysinfo_canvas.bind_all("<MouseWheel>", on_mousewheel))
        self.sysinfo_canvas.bind("<Leave>", lambda e: self.sysinfo_canvas.unbind_all("<MouseWheel>"))

        # 初始提示
        self.sysinfo_placeholder = tk.Label(
            self.sysinfo_inner,
            text='点击右上角「刷新信息」按钮查看系统详情',
            font=("微软雅黑", 12), fg="#555555", bg="#ffffff", pady=40
        )
        self.sysinfo_placeholder.pack()

        # 自动加载一次
        self.root.after(500, self.do_system_info)

    def do_system_info(self):
        """查询系统信息"""
        self.sysinfo_btn.config(state=tk.DISABLED, text="查询中...")

        def task():
            info = self.sys.get_system_info()

            def update_ui():
                # 清除旧内容
                for w in self.sysinfo_inner.winfo_children():
                    w.destroy()

                if not info.get("success"):
                    tk.Label(self.sysinfo_inner, text=f"查询失败: {info.get('error', '未知错误')}",
                             font=("微软雅黑", 11), fg="#c0392b", bg="#ffffff", pady=30).pack()
                    self.sysinfo_btn.config(state=tk.NORMAL, text="刷新信息")
                    return

                # 定义信息卡片样式
                def add_card(title, icon, items, accent_color="#e94560"):
                    """添加信息卡片"""
                    card = tk.Frame(self.sysinfo_inner, bg="#e8ecf1", bd=1, relief=tk.GROOVE)
                    card.pack(fill=tk.X, padx=5, pady=6)

                    # 标题栏
                    header = tk.Frame(card, bg="#d5dce6")
                    header.pack(fill=tk.X)
                    tk.Label(header, text=f"{icon}  {title}", font=("微软雅黑", 11, "bold"),
                             fg=accent_color, bg="#d5dce6").pack(side=tk.LEFT, padx=12, pady=6)

                    # 内容
                    content = tk.Frame(card, bg="#e8ecf1")
                    content.pack(fill=tk.X, padx=15, pady=(5, 10))

                    for i, (label, value) in enumerate(items):
                        row_frame = tk.Frame(content, bg="#e8ecf1")
                        row_frame.pack(fill=tk.X, pady=2)
                        tk.Label(row_frame, text=label, font=("微软雅黑", 10),
                                 fg="#555555", bg="#e8ecf1", width=14, anchor=tk.W).pack(side=tk.LEFT)
                        val_color = "#27ae60" if ("已激活" in str(value) or "域" in str(value)) else "#333333"
                        tk.Label(row_frame, text=str(value), font=("微软雅黑", 10, "bold"),
                                 fg=val_color, bg="#e8ecf1", anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

                # 卡片1: 操作系统信息
                os_name = info.get("os_name", "未知")
                if not os_name:
                    # 备用方案：从 platform 获取
                    import platform
                    os_name = f"Microsoft {platform.system()} {platform.release()}"
                add_card("操作系统", "💻", [
                    ("系统名称:", os_name),
                    ("系统版本:", info.get("os_version", "未知")),
                    ("系统架构:", info.get("os_build", "未知")),
                    ("计算机名:", info.get("hostname", "未知")),
                ], "#2780e3")

                # 卡片2: 激活状态
                activation = info.get("activation_status", "未知")
                act_color = "#27ae60" if "已激活" in activation else "#e74c3c"
                add_card("激活状态", "🔑", [
                    ("激活状态:", activation),
                ], act_color)

                # 卡片3: 域/工作组信息
                domain = info.get("domain_or_workgroup", "未知")
                domain_type = info.get("domain_type", "未知")
                add_card("网络环境", "🌐", [
                    ("所属域/组:", domain),
                    ("环境类型:", domain_type),
                ], "#9b59b6")

                # 更新画布滚动区域
                self.sysinfo_inner.update_idletasks()
                self.sysinfo_canvas.configure(scrollregion=self.sysinfo_canvas.bbox("all"))

                self.sysinfo_btn.config(state=tk.NORMAL, text="刷新信息")
                self.status.config(text="系统信息查询完成")

            self.root.after(0, update_ui)

        threading.Thread(target=task, daemon=True).start()

    # ==================== 关于 ====================
    def create_about_tab(self):
        tab = tk.Frame(self.notebook, bg="#e8ecf1")
        self.notebook.add(tab, text="关于")

        # 顶部大标题
        header = tk.Frame(tab, bg="#d5dce6")
        header.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(header, text="🛠", font=("Segoe UI Emoji", 36), bg="#d5dce6").pack(pady=(10, 0))
        tk.Label(header, text="网络小助手", font=("微软雅黑", 20, "bold"),
                 fg="#e74c3c", bg="#d5dce6").pack()
        tk.Label(header, text=f"版本 v1.5  |  免费网络工具集", font=("微软雅黑", 11),
                 fg="#555555", bg="#d5dce6").pack(pady=(2, 12))

        # 中间内容区域
        content = tk.Frame(tab, bg="#e8ecf1")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 简介卡片
        intro = tk.Frame(content, bg="#ffffff", bd=1, relief=tk.GROOVE)
        intro.pack(fill=tk.X, pady=(0, 10))

        tk.Label(intro, text="💡 这是什么？", font=("微软雅黑", 12, "bold"),
                 fg="#e74c3c", bg="#ffffff", anchor=tk.W).pack(padx=15, pady=(10, 5))
        tk.Label(intro, text=(
            "网络小助手是一款免费、绿色、无需安装的 Windows 网络工具箱。\n"
            "无论您是 IT 工程师还是普通办公人员，当遇到网络问题时，\n"
            "都可以用它快速检测、诊断并找到解决办法。"
        ), font=("微软雅黑", 10), fg="#333333", bg="#ffffff", justify=tk.LEFT).pack(padx=15, pady=(0, 10))

        # 功能模块卡片
        features = tk.Frame(content, bg="#ffffff", bd=1, relief=tk.GROOVE)
        features.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Label(features, text="📦 主要功能", font=("微软雅黑", 12, "bold"),
                 fg="#2780e3", bg="#ffffff", anchor=tk.W).pack(padx=15, pady=(10, 5))

        # 功能网格（3列）
        func_grid = tk.Frame(features, bg="#ffffff")
        func_grid.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        func_items = [
            ("📡", "Ping 测试", "检测网络连通性"),
            ("🔌", "端口检测", "检查服务端口状态"),
            ("🗺", "路由追踪", "查看数据经过的节点"),
            ("🔍", "端口扫描", "扫描目标开放端口"),
            ("🌐", "DNS 管理", "查询/切换 DNS 服务器"),
            ("📊", "HTTP 测试", "网站访问速度测试"),
            ("📈", "网络质量", "综合评估网络状况"),
            ("🧮", "IP 计算器", "子网划分与计算"),
            ("📁", "Hosts 管理", "管理 hosts 文件"),
            ("🗄", "路由/ARP", "查看路由表与ARP缓存"),
            ("🖥", "网卡信息", "流量统计与速率"),
            ("🔧", "网络诊断", "一键检测+修复向导"),
            ("🔑", "密码工具", "生成随机强密码"),
            ("📶", "WiFi 密码", "查看已保存的密码"),
            ("🌍", "公网 IP", "查询外网出口 IP"),
            ("📋", "域账号查询", "查询域账号详细信息"),
            ("💻", "系统信息", "版本/激活/域环境"),
        ]

        for i, (icon, title, desc) in enumerate(func_items):
            row, col = divmod(i, 3)
            cell = tk.Frame(func_grid, bg="#ffffff")
            cell.grid(row=row, column=col, sticky="w", padx=5, pady=4)

            tk.Label(cell, text=f"{icon} {title}", font=("微软雅黑", 10, "bold"),
                     fg="#333333", bg="#ffffff").pack(anchor=tk.W)
            tk.Label(cell, text=desc, font=("微软雅黑", 8),
                     fg="#555555", bg="#ffffff").pack(anchor=tk.W)

        # 底部信息
        footer = tk.Frame(content, bg="#ffffff", bd=1, relief=tk.GROOVE)
        footer.pack(fill=tk.X)

        tk.Label(footer, text="📋 使用须知", font=("微软雅黑", 12, "bold"),
                 fg="#27ae60", bg="#ffffff", anchor=tk.W).pack(padx=15, pady=(10, 5))

        tips_text = (
            "• 本工具完全免费，无需安装，解压即用\n"
            "• 部分功能需要管理员权限（如 Hosts 编辑、DNS 重置等）\n"
            "• 所有检测均在本地执行，不会上传您的任何数据\n"
            "• 如遇到问题，可联系 IT 部门或网络管理员协助\n\n"
            "技术栈：Python 3 + tkinter  |  开源协议：MIT License"
        )
        tk.Label(footer, text=tips_text, font=("微软雅黑", 9), fg="#555555",
                 bg="#ffffff", justify=tk.LEFT).pack(padx=15, pady=(0, 10))


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default='')
    except Exception:
        pass
    app = NetToolsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
