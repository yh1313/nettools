# nettools.py - NetTools 网络工程师工具箱 v1.0
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
    """NetTools 网络工程师工具箱"""

    def __init__(self, root):
        self.root = root
        self.root.title("NetTools - 网络工程师工具箱 v1.0")
        self.root.geometry("1280x900")

        # 初始化工具
        self.net = NetworkTools()
        self.sys = SystemTools()
        self.pwd = PasswordTools()
        self.switch = SwitchManager() if SWITCH_AVAILABLE else None

        # 设置样式
        if USE_BOOTSTRAP:
            self.style = ttkb.Style(theme="flatly")

        self.setup_ui()

    def setup_ui(self):
        """创建主界面"""
        # 标题栏
        title_frame = tk.Frame(self.root, bg="#1a1a2e")
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="NetTools",
                 font=("Segoe UI", 24, "bold"), fg="#e94560", bg="#1a1a2e").pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(title_frame, text="网络工程师工具箱",
                 font=("微软雅黑", 12), fg="#a0a0b0", bg="#1a1a2e").pack(side=tk.LEFT, pady=10)
        version_label = tk.Label(title_frame, text="v1.0  |  公共通用版",
                                 font=("Segoe UI", 9), fg="#555570", bg="#1a1a2e")
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
        self.create_quality_tab()
        self.create_ip_tab()
        self.create_password_tab()
        self.create_utility_tab()
        self.create_public_ip_tab()
        self.create_about_tab()

        # 状态栏
        status_text = "NetTools 就绪 | 网络测试 | DNS查询 | 端口扫描 | 密码生成 | 完全免费"
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
        self.ping_target.insert(0, "8.8.8.8")

        tk.Label(frame, text="发包数量:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.ping_count = tk.Spinbox(frame, from_=1, to=100, width=6, font=("Consolas", 10))
        self.ping_count.grid(row=0, column=3, padx=5)
        self.ping_count.delete(0, tk.END)
        self.ping_count.insert(0, "10")

        self.ping_btn = tk.Button(frame, text="开始 Ping", command=self.do_ping,
                                  bg="#e94560", fg="white", padx=20, font=("微软雅黑", 10))
        self.ping_btn.grid(row=0, column=4, padx=20)

        # 快速目标
        quick_frame = tk.Frame(frame)
        quick_frame.grid(row=1, column=0, columnspan=5, pady=(10, 0))
        for label, target in [("Google DNS", "8.8.8.8"), ("Cloudflare", "1.1.1.1"), ("百度", "www.baidu.com"),
                               ("阿里", "www.aliyun.com"), ("腾讯", "www.qq.com")]:
            tk.Button(quick_frame, text=label,
                      command=lambda t=target: self.set_ping_target(t),
                      bg="#f0f0f0", padx=8, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=3)

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
        self.tcping_host.insert(0, "8.8.8.8")

        tk.Label(frame, text="端口:").grid(row=0, column=2, sticky=tk.W, padx=(15, 0))
        self.tcping_port = tk.Entry(frame, width=7, font=("Consolas", 10))
        self.tcping_port.grid(row=0, column=3, padx=5)
        self.tcping_port.insert(0, "443")

        self.tcping_svc_label = tk.Label(frame, text="(HTTPS)", fg="#e94560", font=("微软雅黑", 9))
        self.tcping_svc_label.grid(row=0, column=4, padx=5)

        tk.Label(frame, text="发包数:").grid(row=0, column=5, sticky=tk.W, padx=(15, 0))
        self.tcping_count = tk.Spinbox(frame, from_=1, to=20, width=5, font=("Consolas", 10))
        self.tcping_count.grid(row=0, column=6, padx=5)
        self.tcping_count.delete(0, tk.END)
        self.tcping_count.insert(0, "4")

        self.tcping_btn = tk.Button(frame, text="开始 TCPing", command=self.do_tcping,
                                    bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
        self.tcping_btn.grid(row=0, column=7, padx=20)

        # 快速端口选择
        quick_frame = tk.Frame(frame)
        quick_frame.grid(row=1, column=0, columnspan=8, pady=(10, 0))
        for label, port in [("SSH(22)", 22), ("HTTP(80)", 80), ("HTTPS(443)", 443),
                            ("MySQL(3306)", 3306), ("RDP(3389)", 3389), ("Redis(6379)", 6379),
                            ("MongoDB(27017)", 27017)]:
            tk.Button(quick_frame, text=label, command=lambda p=port: self.set_tcping_port(p),
                      bg="#f0f0f0", padx=6, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=3)

        result_frame = tk.LabelFrame(tab, text="测试结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tcping_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.tcping_result.pack(fill=tk.BOTH, expand=True)

    def set_tcping_port(self, port):
        self.tcping_port.delete(0, tk.END)
        self.tcping_port.insert(0, str(port))
        svc = NetworkTools._get_port_service(port)
        self.tcping_svc_label.config(text=f"({svc})")

    def do_tcping(self):
        def task():
            self.tcping_btn.config(state=tk.DISABLED, text="测试中...")
            host = self.tcping_host.get().strip()
            try:
                port = int(self.tcping_port.get())
            except ValueError:
                self.root.after(0, lambda: self.tcping_result.insert(tk.END, "端口号无效\n"))
                self.root.after(0, lambda: self.tcping_btn.config(state=tk.NORMAL, text="开始 TCPing"))
                return
            count = int(self.tcping_count.get())
            res = self.net.tcping(host, port, count)

            out = f"TCPing 测试结果\n"
            out += "=" * 60 + "\n"
            out += f"目标: {res['host']}:{res['port']} [{res['service']}]\n"
            out += f"发送: {res['packets_sent']}  接收: {res['packets_received']}  丢包率: {res['packet_loss']}\n"
            out += f"最小延迟: {res['min_latency']}  最大延迟: {res['max_latency']}  平均延迟: {res['avg_latency']}\n"
            out += "=" * 60 + "\n\n"

            for d in res['details']:
                status_icon = "OK" if d['status'] == 'success' else "FAIL"
                out += f"  [{status_icon:4s}] 第{d['seq']}包: {d['latency']}\n"

            out += "\n说明: TCPing 测试 TCP 端口可达性，延迟为 TCP 握手时间\n"

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

        self.trace_btn = tk.Button(frame, text="开始追踪", command=self.do_traceroute,
                                   bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
        self.trace_btn.pack(side=tk.LEFT, padx=20)

        result_frame = tk.LabelFrame(tab, text="追踪结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.trace_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.trace_result.pack(fill=tk.BOTH, expand=True)

    def do_traceroute(self):
        def task():
            self.trace_btn.config(state=tk.DISABLED, text="追踪中...")
            target = self.trace_target.get().strip()
            res = self.net.traceroute(target)
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
                                  bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
        self.scan_btn.pack(pady=10)

        # 快捷端口
        quick_frame = tk.Frame(frame)
        quick_frame.pack(fill=tk.X)
        for label, ports in [("常用端口", "22,80,443,3306,3389,8080"), ("Web端口", "80,443,8080,8443,9090"),
                             ("数据库", "3306,5432,6379,27017,1433,1521"),
                             ("1-1024", "1-1024")]:
            tk.Button(quick_frame, text=label, command=lambda p=ports: self.set_scan_ports(p),
                      bg="#f0f0f0", padx=6, font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=3)

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
                        out += f"  [OPEN] 端口 {p['port']:5d}  {p['service']:15s}  延迟 {p['latency']}\n"
                else:
                    out += "未发现开放端口\n"

                self.root.after(0, lambda: self.scan_result.insert(tk.END, out))
            except Exception as e:
                self.root.after(0, lambda: self.scan_result.insert(tk.END, f"扫描错误: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL, text="开始扫描"))

        threading.Thread(target=task, daemon=True).start()

    # ==================== DNS 查询 ====================
    def create_dns_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="DNS 查询")

        frame = tk.LabelFrame(tab, text="查询参数", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="域名:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.dns_domain = tk.Entry(frame, width=30, font=("Consolas", 10))
        self.dns_domain.grid(row=0, column=1, padx=5)
        self.dns_domain.insert(0, "google.com")

        tk.Label(frame, text="记录类型:").grid(row=0, column=2, sticky=tk.W, padx=(15, 0))
        self.dns_type = ttk.Combobox(frame, values=["A", "AAAA", "MX", "CNAME", "NS", "TXT", "SOA"], width=8)
        self.dns_type.grid(row=0, column=3, padx=5)
        self.dns_type.set("A")

        self.dns_btn = tk.Button(frame, text="查询", command=self.do_dns,
                                 bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
        self.dns_btn.grid(row=0, column=4, padx=20)

        result_frame = tk.LabelFrame(tab, text="查询结果", padx=10, pady=10, font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.dns_result = scrolledtext.ScrolledText(result_frame, height=18, font=("Consolas", 10))
        self.dns_result.pack(fill=tk.BOTH, expand=True)

    def do_dns(self):
        def task():
            self.dns_btn.config(state=tk.DISABLED, text="查询中...")
            domain = self.dns_domain.get().strip()
            rtype = self.dns_type.get()
            res = self.net.dns_lookup(domain, rtype)

            out = f"DNS 查询结果\n"
            out += "=" * 60 + "\n"
            out += f"域名: {domain}\n记录类型: {rtype}\n\n"
            if res.get("success"):
                for r in res['records']:
                    out += f"  {r}\n"
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
                                  bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
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
                out += f"URL: {res['url']}\n"
                out += f"状态码: {res['status_code']}\n"
                out += f"响应时间: {res['response_time']}\n"
                out += f"服务器: {res['server']}\n"
                out += f"内容类型: {res['content_type']}\n"
                out += f"内容大小: {res['size']} 字节\n"
            else:
                out += f"错误: {res['error']}\n"

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

        tk.Label(frame, text="目标 IP:").pack(side=tk.LEFT, padx=5)
        self.quality_target = tk.Entry(frame, width=25, font=("Consolas", 10))
        self.quality_target.pack(side=tk.LEFT, padx=5)
        self.quality_target.insert(0, "8.8.8.8")

        self.quality_btn = tk.Button(frame, text="开始评估", command=self.do_quality,
                                     bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
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
                                     bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
        self.ip_calc_btn.pack(side=tk.LEFT, padx=10)

        # 快捷 CIDR
        quick_frame = tk.Frame(main_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        tk.Label(quick_frame, text="快捷:", font=("微软雅黑", 9), fg="gray").pack(side=tk.LEFT, padx=5)
        for cidr in [8, 16, 24, 26, 28, 30, 32]:
            tk.Button(quick_frame, text=f"/{cidr}", command=lambda c=cidr: self.set_cidr(c),
                      bg="#f0f0f0", padx=6, font=("Consolas", 9)).pack(side=tk.LEFT, padx=3)

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
                                     bg="#e94560", fg="white", font=("微软雅黑", 11), padx=20)
        self.gen_pwd_btn.pack(pady=15)

        result_frame = tk.LabelFrame(main_frame, text="生成的密码", padx=10, pady=10,
                                     font=("微软雅黑", 10, "bold"))
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.password_display = tk.Entry(result_frame, font=("Consolas", 16), justify="center", state="readonly",
                                         readonlybackground="white")
        self.password_display.pack(fill=tk.X, padx=10, pady=10)

        self.strength_label = tk.Label(result_frame, text="密码强度: ", font=("微软雅黑", 10), fg="gray")
        self.strength_label.pack(anchor=tk.W, padx=10)

        btn_frame = tk.Frame(result_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="复制密码", command=self.copy_password,
                  bg="#2ecc71", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="重新生成", command=self.generate_password,
                  bg="#f39c12", fg="white", padx=15, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)

        tip = tk.Label(main_frame,
                       text="建议: 密码长度 12 位以上，包含大小写、数字和特殊符号，强度更高",
                       fg="gray", font=("微软雅黑", 9))
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

    # ==================== 实用工具 ====================
    def create_utility_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="实用工具")

        # 左侧
        left_frame = tk.Frame(tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # DNS 刷新
        dns_frame = tk.LabelFrame(left_frame, text="DNS 缓存管理", padx=10, pady=10,
                                  font=("微软雅黑", 10, "bold"))
        dns_frame.pack(fill=tk.X, pady=5)
        self.flush_dns_btn = tk.Button(dns_frame, text="刷新 DNS 缓存", command=self.flush_dns,
                                       bg="#3498db", fg="white", font=("微软雅黑", 10))
        self.flush_dns_btn.pack(pady=5)
        self.dns_result_label = tk.Label(dns_frame, text="", fg="green", font=("微软雅黑", 9))
        self.dns_result_label.pack()

        # WiFi 密码
        wifi_frame = tk.LabelFrame(left_frame, text="已保存的 WiFi 密码", padx=10, pady=10,
                                   font=("微软雅黑", 10, "bold"))
        wifi_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.wifi_btn = tk.Button(wifi_frame, text="查看 WiFi 密码", command=self.show_wifi_passwords,
                                  bg="#9b59b6", fg="white", font=("微软雅黑", 10))
        self.wifi_btn.pack(pady=5)
        self.wifi_result_text = scrolledtext.ScrolledText(wifi_frame, height=10, font=("Consolas", 9))
        self.wifi_result_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 右侧 - 本机网络信息
        right_frame = tk.LabelFrame(tab, text="本机网络信息 (ipconfig /all)", padx=10, pady=10,
                                    font=("微软雅黑", 10, "bold"))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.local_info_text = scrolledtext.ScrolledText(right_frame, height=25, font=("Consolas", 9))
        self.local_info_text.pack(fill=tk.BOTH, expand=True)
        tk.Button(right_frame, text="刷新", command=self.refresh_local_info,
                  bg="#3498db", fg="white", font=("微软雅黑", 10)).pack(pady=5)

        self.refresh_local_info()

    def flush_dns(self):
        success, msg = self.sys.flush_dns()
        if success:
            self.dns_result_label.config(text=f"{msg}", fg="green")
        else:
            self.dns_result_label.config(text=f"{msg}", fg="red")
        self.root.after(3000, lambda: self.dns_result_label.config(text=""))

    def show_wifi_passwords(self):
        self.wifi_result_text.delete(1.0, tk.END)
        results = self.sys.get_wifi_passwords()
        if results and "error" in results[0]:
            self.wifi_result_text.insert(tk.END, f"获取失败: {results[0]['error']}\n\n可能需要以管理员身份运行")
        else:
            for item in results:
                self.wifi_result_text.insert(tk.END, f"SSID: {item['ssid']}\n密码: {item['password']}\n\n")
            if not results:
                self.wifi_result_text.insert(tk.END, "未找到已保存的 WiFi 配置文件")

    def refresh_local_info(self):
        info = self.sys.get_local_network_info()
        self.local_info_text.delete(1.0, tk.END)
        if info.get("success"):
            self.local_info_text.insert(tk.END, info["output"])
        else:
            self.local_info_text.insert(tk.END, f"获取失败: {info.get('error')}")

    # ==================== 公网 IP ====================
    def create_public_ip_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="公网 IP")

        main = tk.LabelFrame(tab, text="公网出口地址查询", padx=15, pady=15, font=("微软雅黑", 11, "bold"))
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        info = tk.Label(main, text="查询当前网络的公网出口 IP 地址", fg="gray", font=("微软雅黑", 10))
        info.pack(anchor=tk.W, pady=(0, 10))

        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=5)
        self.pub_btn = tk.Button(btn_frame, text="查询公网 IP", command=self.get_public_ip,
                                 bg="#e94560", fg="white", padx=15, font=("微软雅黑", 10))
        self.pub_btn.pack(side=tk.LEFT, padx=5)
        self.copy_pub_btn = tk.Button(btn_frame, text="复制 IP", command=self.copy_public_ip,
                                      bg="#2ecc71", fg="white", padx=15, font=("微软雅黑", 10), state=tk.DISABLED)
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
                self.root.after(0, lambda: self.ip_val_label.config(text="查询失败", fg="#e74c3c"))
                self.root.after(0, lambda: self.pub_result.insert(tk.END, "无法获取公网 IP，请检查网络连接"))

            self.root.after(0, lambda: self.pub_btn.config(state=tk.NORMAL, text="查询公网 IP"))

        threading.Thread(target=task, daemon=True).start()

    def copy_public_ip(self):
        ip = self.ip_val_label.cget("text")
        if ip and ip not in ["未查询", "查询中...", "查询失败"]:
            self.root.clipboard_clear()
            self.root.clipboard_append(ip)
            messagebox.showinfo("成功", f"已复制 IP: {ip}")

    # ==================== 关于 ====================
    def create_about_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="关于")

        main = tk.LabelFrame(tab, text="关于 NetTools", padx=20, pady=20, font=("微软雅黑", 12, "bold"))
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        about_text = """NetTools - 网络工程师工具箱
版本: v1.0 (公共通用版)

NetTools 是一款面向网络工程师和 IT 运维人员的免费工具集，
提供常用的网络测试、诊断和系统管理功能。

功能模块:
  • Ping 测试       - 高级 Ping 测试，统计丢包率和延迟分布
  • TCPing 测试     - TCP 端口连通性测试，支持常见服务端口
  • 路由追踪        - 显示数据包到达目标经过的路由节点
  • 端口扫描        - 多线程 TCP 端口扫描，支持自定义端口范围
  • DNS 查询        - 支持 A/AAAA/MX/CNAME/NS/TXT/SOA 等记录类型
  • HTTP 测试       - HTTP/HTTPS 接口响应时间和状态码测试
  • 网络质量评估    - 综合评估网络质量，给出评分和建议
  • IP 计算器       - CIDR 子网计算，快速得出网络/广播/可用IP
  • 密码生成器      - 生成高强度随机密码，支持自定义规则
  • 实用工具        - DNS 缓存刷新、WiFi 密码查看、本机网络信息
  • 公网 IP 查询    - 获取当前网络的公网出口 IP 地址

技术栈:
  Python 3 + tkinter + ttkbootstrap(可选)

依赖库:
  ping3, dnspython, requests

开源协议: MIT License
完全免费使用"""

        self.about_text = scrolledtext.ScrolledText(main, height=20, font=("微软雅黑", 10), wrap=tk.WORD)
        self.about_text.pack(fill=tk.BOTH, expand=True)
        self.about_text.insert(tk.END, about_text)
        self.about_text.config(state=tk.DISABLED)


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
