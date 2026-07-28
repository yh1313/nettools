# tools.py - 网络小助手 核心工具模块
import os
import re
import time
import socket
import subprocess
import threading
import json
import string
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import dns.resolver
from ping3 import ping


def _get_hidden_startupinfo():
    """获取隐藏控制台窗口的 startupinfo（Windows 专用）"""
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


def run_hidden_cmd(command, capture=True, text=True, encoding=None, timeout=None, check=False):
    """执行命令并隐藏控制台窗口，返回 CompletedProcess"""
    kwargs = {
        "shell": True,
        "startupinfo": _get_hidden_startupinfo(),
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
    }
    if capture:
        kwargs["capture_output"] = True
    if text:
        kwargs["text"] = True
    if encoding:
        kwargs["encoding"] = encoding
    if timeout:
        kwargs["timeout"] = timeout
    if check:
        kwargs["check"] = True
    return subprocess.run(command, **kwargs)


def run_hidden_cmd_output(command, encoding='utf-8', timeout=30):
    """执行命令，隐藏窗口，返回 stdout 字符串"""
    result = run_hidden_cmd(command, encoding=encoding, timeout=timeout)
    return result.stdout or ""


class NetworkTools:
    """网络测试工具集"""

    def __init__(self):
        self.results_dir = "test_results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    # ==================== Ping 测试 ====================
    def ping_test(self, target, count=10, timeout=2):
        """高级 Ping 测试"""
        results = []
        successful = 0
        total_time = 0.0
        min_time = float('inf')
        max_time = 0.0

        for i in range(count):
            try:
                response = ping(target, timeout=timeout)
                if response:
                    latency = response * 1000
                    successful += 1
                    total_time += latency
                    min_time = min(min_time, latency)
                    max_time = max(max_time, latency)
                    results.append({"seq": i + 1, "status": "success", "latency": f"{latency:.2f}ms"})
                else:
                    results.append({"seq": i + 1, "status": "timeout", "latency": "N/A"})
            except Exception:
                results.append({"seq": i + 1, "status": "error", "latency": "N/A"})
            time.sleep(1)

        loss_rate = ((count - successful) / count) * 100 if count > 0 else 0
        avg_latency = total_time / successful if successful > 0 else 0

        return {
            "target": target,
            "packets_sent": count,
            "packets_received": successful,
            "packet_loss": f"{loss_rate:.1f}%",
            "min_latency": f"{min_time:.2f}ms" if min_time != float('inf') else "N/A",
            "max_latency": f"{max_time:.2f}ms" if max_time > 0 else "N/A",
            "avg_latency": f"{avg_latency:.2f}ms" if avg_latency > 0 else "N/A",
            "details": results
        }

    def batch_ping(self, targets, count=4):
        """批量 Ping 测试"""
        results = {}
        for target in targets:
            target = target.strip()
            if target:
                results[target] = self.ping_test(target, count=count)
        return results

    # ==================== TCPing 测试 ====================
    def tcping(self, host, port, count=4, timeout=3):
        """TCP 端口连通性测试"""
        results = []
        successful = 0
        total_time = 0.0
        min_time = float('inf')
        max_time = 0.0

        for i in range(count):
            try:
                start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                ret = sock.connect_ex((host, port))
                elapsed = (time.time() - start) * 1000
                if ret == 0:
                    successful += 1
                    total_time += elapsed
                    min_time = min(min_time, elapsed)
                    max_time = max(max_time, elapsed)
                    results.append({"seq": i + 1, "status": "success", "latency": f"{elapsed:.2f}ms"})
                else:
                    results.append({"seq": i + 1, "status": "failed", "latency": "连接失败"})
                sock.close()
            except socket.timeout:
                results.append({"seq": i + 1, "status": "timeout", "latency": f">{timeout * 1000}ms"})
            except socket.gaierror:
                results.append({"seq": i + 1, "status": "error", "latency": "DNS解析失败"})
            except Exception as e:
                results.append({"seq": i + 1, "status": "error", "latency": str(e)})
            time.sleep(0.5)

        loss_rate = ((count - successful) / count) * 100 if count > 0 else 0
        avg_latency = total_time / successful if successful > 0 else 0

        return {
            "host": host,
            "port": port,
            "service": self._get_port_service(port),
            "packets_sent": count,
            "packets_received": successful,
            "packet_loss": f"{loss_rate:.1f}%",
            "min_latency": f"{min_time:.2f}ms" if min_time != float('inf') else "N/A",
            "max_latency": f"{max_time:.2f}ms" if max_time > 0 else "N/A",
            "avg_latency": f"{avg_latency:.2f}ms" if avg_latency > 0 else "N/A",
            "details": results
        }

    # ==================== 路由追踪 ====================
    def traceroute(self, target, max_hops=15, no_dns=True, timeout=30):
        """路由追踪（隐藏CMD窗口，默认15跳，每跳超时1.5秒）"""
        try:
            if os.name == 'nt':
                dns_opt = "-d " if no_dns else ""
                cmd = f"tracert {dns_opt}-h {max_hops} -w 1500 {target}"
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk',
                                        timeout=timeout, startupinfo=startupinfo,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                cmd = f"traceroute -m {max_hops} {target}"
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"success": True, "output": result.stdout}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "路由追踪超时，请尝试减少跳数或使用 -d 选项"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"命令执行失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 端口扫描 ====================
    def port_scan(self, ip, ports=None, timeout=1.5, max_threads=200, deep_scan=False):
        """TCP 端口扫描（加速版）"""
        if ports is None:
            port_list = [21, 22, 23, 25, 53, 80, 110, 143, 161, 443, 3389, 8080, 8443, 3306, 5432, 6379, 27017]
        elif isinstance(ports, str):
            port_list = []
            for part in ports.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    if end - start > 1000:
                        end = start + 1000  # 限制范围
                    port_list.extend(range(start, end + 1))
                else:
                    port_list.append(int(part))
        else:
            port_list = ports

        if deep_scan:
            timeout = max(timeout, 2.0)

        open_ports = []
        details = []

        def scan_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                start = time.time()
                ret = sock.connect_ex((ip, port))
                elapsed = (time.time() - start) * 1000
                sock.close()
                if ret == 0:
                    svc = self._get_port_service(port)
                    display = f"{svc} ({port})" if svc != f"Port {port}" else str(port)
                    return {"port": port, "status": "open", "latency": f"{elapsed:.0f}ms",
                            "service": svc, "display": display}
                return {"port": port, "status": "closed"}
            except socket.timeout:
                return {"port": port, "status": "timeout"}
            except Exception as e:
                return {"port": port, "status": "error", "reason": str(e)}

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_map = {executor.submit(scan_port, p): p for p in port_list}
            for future in as_completed(future_map):
                port = future_map[future]
                try:
                    detail = future.result()
                    details.append(detail)
                    if detail["status"] == "open":
                        open_ports.append(detail)
                except Exception as e:
                    details.append({"port": port, "status": "error", "reason": str(e)})

        details.sort(key=lambda x: x["port"])
        open_ports.sort(key=lambda x: x["port"])

        return {
            "target_ip": ip,
            "total_ports_scanned": len(port_list),
            "open_ports": open_ports,
            "details": details,
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "deep_scan": deep_scan
        }

    # ==================== DNS 查询 ====================
    def dns_lookup(self, domain, record_type="A"):
        """DNS 解析查询"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8', '114.114.114.114']
            answers = resolver.resolve(domain, record_type)
            records = [str(a) for a in answers]
            return {"success": True, "domain": domain, "record_type": record_type, "records": records}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== HTTP 测试 ====================
    def http_test(self, url, timeout=10):
        """HTTP 接口测试"""
        try:
            start = time.time()
            response = requests.get(url, timeout=timeout, headers={"User-Agent": "NetTools/1.3"})
            elapsed = (time.time() - start) * 1000
            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "response_time": f"{elapsed:.2f}ms",
                "server": response.headers.get('Server', 'Unknown'),
                "content_type": response.headers.get('Content-Type', 'Unknown'),
                "size": len(response.content)
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "连接超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "连接失败"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 网络质量评估 ====================
    def network_quality(self, target=None, packets=10):
        """综合网络质量评估（多目标检测，更准确）"""
        if target is None:
            targets = ["baidu.com", "114.114.114.114", "8.8.8.8"]
            results = []
            for t in targets:
                r = self.ping_test(t, count=3)
                if float(r['packet_loss'].replace('%', '')) < 100:
                    results.append(r)
            if not results:
                return {
                    "quality_score": 0,
                    "quality_level": "无法连接",
                    "packet_loss": "100%",
                    "avg_latency": "N/A",
                    "min_latency": "N/A",
                    "max_latency": "N/A",
                    "total_score": 0,
                    "suggestion": "所有目标都无法连接，请检查网络设备和网线",
                    "target": "多目标检测"
                }
            # 取结果最好的
            best = max(results, key=lambda x: float(x['avg_latency'].replace('ms', '99')) if x['avg_latency'] != 'N/A' else 999)
            ping_result = best
            target = best['target']
        else:
            ping_result = self.ping_test(target, count=packets)

        loss_rate = float(ping_result['packet_loss'].replace('%', ''))
        avg_latency = float(ping_result['avg_latency'].replace('ms', '')) if ping_result['avg_latency'] != 'N/A' else 999

        # 综合评分：丢包权重60%，延迟权重40%
        loss_score = max(0, 60 - loss_rate * 6)
        if avg_latency >= 999:
            latency_score = 0
        elif avg_latency <= 10:
            latency_score = 40
        elif avg_latency <= 30:
            latency_score = 35
        elif avg_latency <= 60:
            latency_score = 28
        elif avg_latency <= 100:
            latency_score = 20
        elif avg_latency <= 200:
            latency_score = 10
        else:
            latency_score = 5

        quality_score = int(loss_score + latency_score)
        quality_score = max(0, min(100, quality_score))

        if quality_score >= 85:
            quality_level = "🏆 优秀"
        elif quality_score >= 70:
            quality_level = "👍 良好"
        elif quality_score >= 50:
            quality_level = "⚠️ 一般"
        else:
            quality_level = "❌ 较差"

        # 详细建议
        suggestions = []
        if loss_rate > 10:
            suggestions.append("⚠️ 丢包率严重({:.1f}%)，请检查网线/路由器/交换机".format(loss_rate))
        elif loss_rate > 3:
            suggestions.append("⚠️ 存在丢包({:.1f}%)，建议检查网络稳定性".format(loss_rate))
        if avg_latency > 200:
            suggestions.append("🐢 延迟过高({:.0f}ms)，可能有带宽占用或路由问题".format(avg_latency))
        elif avg_latency > 100:
            suggestions.append("🔶 延迟偏高({:.0f}ms)，建议检查网络占用".format(avg_latency))
        if loss_rate <= 3 and avg_latency <= 60:
            suggestions.append("✅ 网络状态良好，各项指标正常")

        return {
            "target": target,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "packet_loss": ping_result['packet_loss'],
            "avg_latency": ping_result['avg_latency'],
            "min_latency": ping_result['min_latency'],
            "max_latency": ping_result['max_latency'],
            "suggestion": '\n'.join(suggestions) if suggestions else "网络状态正常"
        }

    # ==================== 公网 IP 查询 ====================
    def get_public_ip(self):
        """获取公网出口 IP"""
        services = [
            ('https://myip.ipip.net/', r'\d+\.\d+\.\d+\.\d+'),
            ('https://ifconfig.me/ip', None),
            ('https://api.ipify.org', None),
        ]
        for url, pattern in services:
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    if pattern:
                        m = re.search(pattern, r.text)
                        if m:
                            return {"success": True, "ip": m.group(), "source": url}
                    else:
                        ip = r.text.strip()
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                            return {"success": True, "ip": ip, "source": url}
            except Exception:
                continue
        return {"success": False, "error": "无法获取公网IP"}

    # ==================== MAC 地址厂商查询 ====================
    def mac_lookup(self, mac_address):
        """MAC 地址厂商查询"""
        try:
            mac_clean = mac_address.replace(':', '').replace('-', '').upper()
            response = requests.get(f"https://api.macvendors.com/{mac_clean}", timeout=5)
            if response.status_code == 200:
                return {"mac": mac_address, "vendor": response.text, "oui": mac_clean[:6]}
            return {"mac": mac_address, "vendor": "未知厂商", "oui": mac_clean[:6]}
        except Exception:
            return {"mac": mac_address, "vendor": "查询失败"}

    @staticmethod
    def _get_port_service(port):
        """获取端口对应服务名"""
        services = {
            7: "Echo", 9: "Discard", 13: "Daytime", 19: "Chargen",
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 67: "DHCP", 68: "DHCP", 69: "TFTP",
            80: "HTTP", 81: "HTTP-Alt", 88: "Kerberos",
            110: "POP3", 123: "NTP", 135: "RPC", 137: "NetBIOS", 138: "NetBIOS", 139: "SMB",
            143: "IMAP", 161: "SNMP", 162: "SNMP-Trap", 179: "BGP",
            389: "LDAP", 443: "HTTPS", 445: "SMB", 464: "Kerberos",
            465: "SMTPS", 500: "IPSEC", 514: "Syslog", 587: "SMTP-Sub",
            593: "RPC", 636: "LDAPS", 873: "Rsync",
            993: "IMAPS", 995: "POP3S", 1080: "Proxy", 1194: "OpenVPN",
            1352: "Lotus", 1433: "MSSQL", 1521: "Oracle",
            1723: "PPTP", 2049: "NFS", 2082: "cPanel", 2083: "cPanel-SSL",
            2375: "Docker", 2376: "Docker-SSL", 3128: "Squid",
            3306: "MySQL", 3389: "RDP", 3690: "SVN", 4333: "SQLite",
            4848: "GlassFish", 5000: "Flask", 5432: "PostgreSQL",
            5555: "ADB", 5632: "PCAnywhere", 5800: "VNC-HTTP",
            5900: "VNC", 5984: "CouchDB", 5985: "WinRM-HTTP", 5986: "WinRM-HTTPS",
            6379: "Redis", 6443: "K8s-API", 7077: "Spark", 8000: "HTTP-Alt",
            8080: "HTTP-Alt", 8443: "HTTPS-Alt", 8444: "HTTPS-Alt",
            8530: "Jenkins", 8888: "HTTP-Alt", 9000: "WebDev",
            9090: "Prometheus", 9100: "NodeExporter", 9200: "Elasticsearch",
            9300: "Elasticsearch", 9418: "Git", 9999: "HTTP-Alt",
            11211: "Memcached", 11214: "Memcached", 11215: "Memcached",
            15672: "RabbitMQ", 16010: "HBase", 20000: "DNP3",
            25565: "Minecraft", 27017: "MongoDB", 28017: "MongoDB-Web",
            50000: "SAP", 50070: "Hadoop-Web", 61616: "ActiveMQ"
        }
        return services.get(port, f"Port-{port}")


class SystemTools:
    """系统工具集"""

    # 常用公共 DNS 服务器
    PUBLIC_DNS = {
        "阿里 DNS": ("223.5.5.5", "223.6.6.6"),
        "腾讯 DNS": ("119.29.29.29", "182.254.116.116"),
        "百度 DNS": ("180.76.76.76", ""),
        "Google DNS": ("8.8.8.8", "8.8.4.4"),
        "Cloudflare DNS": ("1.1.1.1", "1.0.0.1"),
        "114 DNS": ("114.114.114.114", "114.114.115.115"),
        "OpenDNS": ("208.67.222.222", "208.67.220.220"),
        "DNSPod": ("119.29.29.29", "182.254.118.118"),
        "自动获取 (DHCP)": ("", ""),
    }

    def __init__(self):
        pass

    # ==================== DNS 修改 ====================
    def get_dns_servers(self):
        """获取当前所有网络适配器的 DNS 配置"""
        adapters = []
        try:
            import tempfile
            tmpfile = os.path.join(tempfile.gettempdir(), 'nettools_dns_output.txt')
            run_hidden_cmd(f'chcp 65001 > nul && netsh interface ip show dnsservers > "{tmpfile}"')
            with open(tmpfile, 'r', encoding='utf-8', errors='replace') as f:
                output = f.read()
            try:
                os.remove(tmpfile)
            except Exception:
                pass

            current_adapter = None
            dns_servers = []
            for line in output.split('\n'):
                stripped = line.strip()
                if not stripped:
                    continue

                # 匹配适配器名称行: "Configuration for interface \"xxx\""
                if 'Configuration for interface' in stripped:
                    if current_adapter and dns_servers:
                        adapters.append({
                            "adapter": current_adapter,
                            "dns_servers": dns_servers.copy()
                        })
                    # 提取适配器名称
                    match = re.search(r'"([^"]*)"', stripped)
                    if match:
                        current_adapter = match.group(1)
                    else:
                        # 没有引号的情况
                        parts = stripped.split('"')
                        if len(parts) >= 2:
                            current_adapter = parts[1]
                        else:
                            current_adapter = stripped.split('interface')[-1].strip()
                    dns_servers = []
                elif current_adapter:
                    # DNS 服务器行
                    if 'Statically Configured DNS Servers' in stripped:
                        val = stripped.split(':', 1)[-1].strip()
                        if val and val.lower() != 'none':
                            dns_servers.append(val)
                    elif 'DNS servers configured through DHCP' in stripped:
                        val = stripped.split(':', 1)[-1].strip()
                        if val and val.lower() != 'none':
                            dns_servers.append(f"DHCP: {val}")
                        else:
                            dns_servers.append("DHCP (自动获取)")
                    # 续行（多行 DNS）
                    elif dns_servers and re.match(r'^\d+\.\d+\.\d+\.\d+$', stripped):
                        # 检查上一行是否已经有这个 IP
                        last = dns_servers[-1]
                        if 'DHCP:' in last:
                            dns_servers.append(stripped)
                        else:
                            dns_servers.append(stripped)
                    elif 'Register with which suffix' in stripped:
                        pass  # 忽略

            # 保存最后一个适配器
            if current_adapter and dns_servers:
                adapters.append({
                    "adapter": current_adapter,
                    "dns_servers": dns_servers.copy()
                })

            # 过滤掉环回适配器
            adapters = [a for a in adapters if 'Loopback' not in a['adapter'] and '环回' not in a['adapter']]

            if not adapters:
                adapters.append({"adapter": "未检测到适配器", "dns_servers": ["请检查网络连接"]})

        except Exception as e:
            adapters.append({"adapter": "错误", "dns_servers": [str(e)]})

        return adapters

    def set_dns(self, adapter_name, primary_dns, secondary_dns=""):
        """修改指定网络适配器的 DNS 服务器"""
        try:
            if not adapter_name:
                return False, "请选择网络适配器"

            if not primary_dns:
                # 设为自动获取
                cmd = f'netsh interface ip set dnsservers name="{adapter_name}" source=dhcp'
                result = run_hidden_cmd(cmd, encoding='gbk')
                if result.returncode == 0:
                    return True, f"已为 [{adapter_name}] 设为自动获取 DNS"
                else:
                    return False, result.stdout.strip() or result.stderr.strip()

            # 设置首选 DNS
            cmd = f'netsh interface ip set dnsservers name="{adapter_name}" source=static address={primary_dns} register=primary validate=no'
            result = run_hidden_cmd(cmd, encoding='gbk')
            if result.returncode != 0:
                return False, f"设置首选 DNS 失败: {result.stdout.strip() or result.stderr.strip()}"

            # 设置备用 DNS
            if secondary_dns:
                cmd2 = f'netsh interface ip add dnsservers name="{adapter_name}" address={secondary_dns} index=2 validate=no'
                result2 = run_hidden_cmd(cmd2, encoding='gbk')
                if result2.returncode != 0:
                    # 备用 DNS 设置失败不算致命错误
                    return True, f"已为 [{adapter_name}] 设置 DNS: {primary_dns} (备用 DNS 设置失败)"

            return True, f"已为 [{adapter_name}] 设置 DNS: {primary_dns}" + (
                f", 备用: {secondary_dns}" if secondary_dns else "")

        except Exception as e:
            return False, f"设置 DNS 失败: {str(e)}\n提示: 请以管理员身份运行"

    def flush_dns_cache(self):
        """刷新 DNS 缓存"""
        try:
            run_hidden_cmd('ipconfig /flushdns')
            return True, "DNS 缓存已刷新"
        except Exception as e:
            return False, str(e)

    # ==================== IP 计算器 ====================
    def ip_calculator(self, ip_cidr):
        """IP 子网计算器 (CIDR)"""
        try:
            if '/' in ip_cidr:
                ip_str, cidr_str = ip_cidr.split('/')
                cidr = int(cidr_str)
            else:
                ip_str = ip_cidr
                cidr = 24

            ip_int = sum(int(octet) << (24 - 8 * i) for i, octet in enumerate(ip_str.split('.')))
            mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
            network_int = ip_int & mask_int
            broadcast_int = network_int | (~mask_int & 0xFFFFFFFF)
            first_host = network_int + 1 if network_int != broadcast_int else network_int
            last_host = broadcast_int - 1 if network_int != broadcast_int else broadcast_int
            total_hosts = 2 ** (32 - cidr)
            usable_hosts = total_hosts - 2 if total_hosts > 2 else total_hosts

            def int_to_ip(x):
                return '.'.join(str((x >> (24 - 8 * i)) & 0xFF) for i in range(4))

            return {
                "ip": ip_str, "cidr": cidr,
                "subnet_mask": int_to_ip(mask_int),
                "network": int_to_ip(network_int),
                "broadcast": int_to_ip(broadcast_int),
                "first_host": int_to_ip(first_host) if first_host != network_int else "N/A",
                "last_host": int_to_ip(last_host) if last_host != broadcast_int else "N/A",
                "total_hosts": total_hosts,
                "usable_hosts": usable_hosts
            }
        except Exception as e:
            return {"error": str(e)}

    # ==================== DNS 刷新 ====================
    def flush_dns(self):
        """刷新 DNS 缓存"""
        try:
            run_hidden_cmd('ipconfig /flushdns')
            return True, "DNS缓存已刷新"
        except Exception as e:
            return False, str(e)

    # ==================== WiFi 密码查看 ====================
    def get_wifi_passwords(self):
        """查看已保存的 WiFi 密码 (Windows)"""
        results = []
        try:
            output = run_hidden_cmd('netsh wlan show profiles').stdout
            profiles = re.findall(r'所有用户配置文件 : (.*)', output)
            if not profiles:
                # 英文系统
                profiles = re.findall(r'All User Profile\s*:\s*(.*)', output)
            for profile in profiles:
                profile = profile.strip()
                info = run_hidden_cmd(f'netsh wlan show profile name="{profile}" key=clear').stdout
                password_match = re.search(r'关键内容\s*:\s*(.*)', info)
                if not password_match:
                    password_match = re.search(r'Key Content\s*:\s*(.*)', info)
                password = password_match.group(1).strip() if password_match else "(无密码)"
                results.append({"ssid": profile, "password": password})
        except Exception as e:
            results.append({"error": str(e)})
        return results

    # ==================== 网络适配器 ====================
    def get_network_adapters(self):
        """获取网络适配器列表"""
        adapters = []
        try:
            result = run_hidden_cmd('netsh interface show interface')
            for line in result.stdout.split('\n'):
                if '已启用' in line or 'Enabled' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        name = parts[-1]
                        if name and name not in ['环回', 'Loopback', 'Npcap', 'Bluetooth']:
                            adapters.append(name)
        except Exception:
            pass
        return adapters

    # ==================== 本机网络信息 ====================
    def get_local_network_info(self):
        """获取本机网络配置信息"""
        try:
            result = run_hidden_cmd('ipconfig /all', encoding='gbk')
            return {"success": True, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== Hosts 文件管理 ====================
    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"

    def get_hosts_content(self):
        """读取 hosts 文件内容"""
        try:
            with open(self.HOSTS_PATH, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return {"success": True, "content": content}
        except PermissionError:
            return {"success": False, "error": "权限不足，请以管理员身份运行"}
        except FileNotFoundError:
            return {"success": False, "error": f"hosts 文件不存在: {self.HOSTS_PATH}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_hosts_content(self, content):
        """保存 hosts 文件内容"""
        try:
            with open(self.HOSTS_PATH, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            return True, "hosts 文件已保存"
        except PermissionError:
            return False, "权限不足，请以管理员身份运行"
        except Exception as e:
            return False, f"保存失败: {str(e)}"

    def backup_hosts(self):
        """备份 hosts 文件"""
        import shutil
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.HOSTS_PATH}.backup_{timestamp}"
            shutil.copy2(self.HOSTS_PATH, backup_path)
            return True, f"已备份到: {backup_path}"
        except PermissionError:
            return False, "权限不足，请以管理员身份运行"
        except Exception as e:
            return False, f"备份失败: {str(e)}"

    def restore_hosts(self, backup_path):
        """恢复 hosts 文件备份"""
        import shutil
        try:
            if not os.path.exists(backup_path):
                return False, f"备份文件不存在: {backup_path}"
            shutil.copy2(backup_path, self.HOSTS_PATH)
            return True, "hosts 文件已恢复"
        except PermissionError:
            return False, "权限不足，请以管理员身份运行"
        except Exception as e:
            return False, f"恢复失败: {str(e)}"

    def list_hosts_backups(self):
        """列出所有 hosts 备份文件"""
        backups = []
        try:
            backup_dir = os.path.dirname(self.HOSTS_PATH)
            for f in os.listdir(backup_dir):
                if f.startswith("hosts.backup_"):
                    full_path = os.path.join(backup_dir, f)
                    mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                    size = os.path.getsize(full_path)
                    backups.append({
                        "filename": f,
                        "path": full_path,
                        "time": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                        "size": f"{size:,} 字节"
                    })
            backups.sort(key=lambda x: x['time'], reverse=True)
        except Exception:
            pass
        return backups

    # ==================== 路由表查看 ====================
    def get_route_table(self):
        """获取路由表"""
        try:
            import tempfile
            tmpfile = os.path.join(tempfile.gettempdir(), 'nettools_route_output.txt')
            run_hidden_cmd(f'chcp 65001 > nul && route print > "{tmpfile}"')
            with open(tmpfile, 'r', encoding='utf-8', errors='replace') as f:
                output = f.read()
            try:
                os.remove(tmpfile)
            except Exception:
                pass
            return {"success": True, "output": output}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== ARP 表查看 ====================
    def get_arp_table(self):
        """获取 ARP 表"""
        try:
            import tempfile
            tmpfile = os.path.join(tempfile.gettempdir(), 'nettools_arp_output.txt')
            run_hidden_cmd(f'chcp 65001 > nul && arp -a > "{tmpfile}"')
            with open(tmpfile, 'r', encoding='utf-8', errors='replace') as f:
                output = f.read()
            try:
                os.remove(tmpfile)
            except Exception:
                pass

            # 解析 ARP 表
            entries = []
            current_iface = ""
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if 'Interface:' in line or '接口:' in line:
                    current_iface = line.split(':', 1)[-1].strip()
                    continue
                # 匹配 IP - MAC - 类型
                parts = line.split()
                if len(parts) >= 3:
                    ip = parts[0]
                    mac = parts[1]
                    if re.match(r'^[\da-fA-F]{1,2}-[\da-fA-F]{1,2}-[\da-fA-F]{1,2}-[\da-fA-F]{1,2}-[\da-fA-F]{1,2}-[\da-fA-F]{1,2}$', mac):
                        arp_type = ' '.join(parts[2:])
                        entries.append({
                            "interface": current_iface,
                            "ip": ip,
                            "mac": mac,
                            "type": arp_type
                        })

            return {"success": True, "output": output, "entries": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 网卡流量统计 ====================
    def get_network_stats(self):
        """获取网卡流量统计信息"""
        try:
            import tempfile
            tmpfile = os.path.join(tempfile.gettempdir(), 'nettools_netstat_output.txt')
            run_hidden_cmd(f'chcp 65001 > nul && netstat -e > "{tmpfile}"')
            with open(tmpfile, 'r', encoding='utf-8', errors='replace') as f:
                netstat_output = f.read()
            try:
                os.remove(tmpfile)
            except Exception:
                pass

            # 解析接口统计
            bytes_received = 0
            bytes_sent = 0
            for line in netstat_output.split('\n'):
                if 'Bytes' in line or '字节' in line:
                    parts = line.split()
                    nums = [int(p.replace(',', '')) for p in parts if p.replace(',', '').isdigit()]
                    if len(nums) >= 2:
                        bytes_received = nums[0]
                        bytes_sent = nums[1]

            # 获取各网卡详细信息
            import tempfile as tmp2
            tmpfile2 = os.path.join(tmp2.gettempdir(), 'nettools_if_output.txt')
            run_hidden_cmd(f'chcp 65001 > nul && netsh interface ip show interfaces > "{tmpfile2}"')
            with open(tmpfile2, 'r', encoding='utf-8', errors='replace') as f:
                if_output = f.read()
            try:
                os.remove(tmpfile2)
            except Exception:
                pass

            return {
                "success": True,
                "total_bytes_received": bytes_received,
                "total_bytes_sent": bytes_sent,
                "netstat_raw": netstat_output,
                "interfaces_raw": if_output
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 网络诊断 ====================
    def network_diagnostic(self):
        """一键网络诊断：检测网关连通性、外网连通性、DNS 解析（HTTP方式更可靠）"""
        result = {"gateway": None, "internet": None, "dns": None, "ping": None, "details": {}}

        try:
            # 1. 获取默认网关
            gw = run_hidden_cmd('ipconfig', encoding='gbk')
            gw_ip = None
            for line in gw.stdout.split('\n'):
                if '默认网关' in line or 'Default Gateway' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        gw_ip = parts[1].strip()
                        if gw_ip and gw_ip != '':
                            break
            result["details"]["gateway_ip"] = gw_ip or "未找到"

            # 2. Ping 网关
            if gw_ip:
                try:
                    r = ping(gw_ip, timeout=3)
                    result["gateway"] = f"{r * 1000:.1f}ms" if r else "超时"
                except Exception:
                    result["gateway"] = "超时"
            else:
                result["gateway"] = "未找到"

            # 3. 外网连通性（HTTP方式，更准确）
            try:
                r = requests.get("https://www.baidu.com", timeout=5)
                result["internet"] = f"正常 ({r.status_code})" if r.status_code == 200 else f"异常({r.status_code})"
            except requests.exceptions.Timeout:
                result["internet"] = "超时"
            except requests.exceptions.ConnectionError:
                result["internet"] = "连接失败"
            except Exception:
                result["internet"] = "异常"

            # 4. Ping 百度
            try:
                r = ping("baidu.com", timeout=4)
                result["ping"] = f"{r * 1000:.1f}ms" if r else "超时"
            except Exception:
                result["ping"] = "超时"

            # 5. DNS 解析测试
            try:
                resolver = dns.resolver.Resolver()
                resolver.timeout = 3
                resolver.lifetime = 3
                answers = resolver.resolve('baidu.com', 'A')
                result["dns"] = f"正常 ({answers[0].address})"
            except Exception as e:
                try:
                    socket.gethostbyname('baidu.com')
                    result["dns"] = "正常"
                except Exception:
                    result["dns"] = "异常"

            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 系统信息查询 ====================
    def get_system_info(self):
        """获取 Windows 系统信息（版本/激活状态/工作组或域）"""
        info = {
            "os_name": "",
            "os_version": "",
            "os_build": "",
            "activation_status": "未知",
            "domain_or_workgroup": "未知",
            "domain_type": "未知",
            "hostname": "",
            "raw_systeminfo": ""
        }
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # 1. 使用 systeminfo 命令获取详细信息
            si = subprocess.run('systeminfo', capture_output=True, text=True,
                                encoding='gbk', timeout=30,
                                startupinfo=startupinfo,
                                creationflags=subprocess.CREATE_NO_WINDOW)
            raw = si.stdout
            info["raw_systeminfo"] = raw

            # 解析 OS 名称和版本
            for line in raw.split('\n'):
                line_stripped = line.strip()
                if 'OS 名称' in line_stripped or 'OS Name' in line_stripped:
                    parts = line_stripped.split(':', 1)
                    if len(parts) > 1:
                        info["os_name"] = parts[1].strip()
                if 'OS 版本' in line_stripped or 'OS Version' in line_stripped:
                    parts = line_stripped.split(':', 1)
                    if len(parts) > 1:
                        info["os_version"] = parts[1].strip()
                if '系统类型' in line_stripped or 'System Type' in line_stripped:
                    parts = line_stripped.split(':', 1)
                    if len(parts) > 1:
                        info["os_build"] = parts[1].strip()

            # 2. 检查激活状态（优先使用 systeminfo，备用 slmgr）
            try:
                # 方法1: 从 systeminfo 中解析激活状态
                if '已激活' in raw or 'Licensed' in raw:
                    info["activation_status"] = "已激活"
                else:
                    # 方法2: 使用 slmgr.vbs
                    try:
                        slmgr_paths = [
                            os.path.expandvars(r'%windir%\system32\slmgr.vbs'),
                            os.path.expandvars(r'%windir%\SysWOW64\slmgr.vbs'),
                            r'C:\Windows\system32\slmgr.vbs',
                        ]
                        slmgr_path = None
                        for p in slmgr_paths:
                            if os.path.exists(p):
                                slmgr_path = p
                                break

                        if slmgr_path:
                            slmgr = subprocess.run(
                                f'cscript //Nologo "{slmgr_path}" /dli',
                                capture_output=True, text=True, encoding='gbk', timeout=15,
                                startupinfo=startupinfo,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            slmgr_out = slmgr.stdout + slmgr.stderr
                            if 'Licensed' in slmgr_out or '已授权' in slmgr_out or '许可证状态: 已授权' in slmgr_out:
                                info["activation_status"] = "已激活"
                            elif 'Notification' in slmgr_out or '通知' in slmgr_out:
                                info["activation_status"] = "已激活（通知模式）"
                            elif 'Initial grace' in slmgr_out or '初始宽限' in slmgr_out:
                                info["activation_status"] = "未激活（宽限期）"
                            elif 'Unlicensed' in slmgr_out or '未授权' in slmgr_out:
                                info["activation_status"] = "未激活"
                            else:
                                # 方法3: 检查注册表
                                import winreg
                                try:
                                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                        r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
                                    try:
                                        val, _ = winreg.QueryValueEx(key, 'DigitalProductId')
                                        if val:
                                            info["activation_status"] = "已激活"
                                        else:
                                            info["activation_status"] = "未激活"
                                    except Exception:
                                        info["activation_status"] = "状态未知"
                                    winreg.CloseKey(key)
                                except Exception:
                                    info["activation_status"] = "状态未知"
                        else:
                            info["activation_status"] = "无法检测（slmgr.vbs 未找到）"
                    except Exception:
                        info["activation_status"] = "无法检测"
            except Exception:
                info["activation_status"] = "无法检测"

            # 3. 检查工作组或域
            try:
                domain_cmd = subprocess.run(
                    'wmic computersystem get domain /format:list',
                    capture_output=True, text=True, encoding='gbk', timeout=10,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in domain_cmd.stdout.split('\n'):
                    if 'Domain=' in line or 'domain=' in line:
                        val = line.split('=', 1)[1].strip()
                        if val.upper() == 'WORKGROUP':
                            info["domain_or_workgroup"] = "WORKGROUP（工作组）"
                            info["domain_type"] = "工作组模式"
                        else:
                            info["domain_or_workgroup"] = val
                            info["domain_type"] = "域环境"
                        break
            except Exception:
                # 备用方法
                try:
                    env_domain = os.environ.get('USERDOMAIN', '')
                    env_logon = os.environ.get('LOGONSERVER', '')
                    if env_domain and env_logon and env_logon.startswith('\\\\'):
                        info["domain_or_workgroup"] = env_domain
                        info["domain_type"] = "域环境"
                    elif env_domain:
                        info["domain_or_workgroup"] = env_domain
                        info["domain_type"] = "工作组模式" if env_domain.upper() != os.environ.get('COMPUTERNAME', '').upper() else "工作组模式"
                except Exception:
                    pass

            info["hostname"] = os.environ.get('COMPUTERNAME', socket.gethostname())
            return {"success": True, **info}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 诊断向导辅助方法 ====================
    def get_ip_info(self):
        """获取本机 IP 信息"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return {"local_ip": local_ip, "hostname": hostname}
        except Exception:
            return {"local_ip": "", "hostname": ""}

    def ping_gateway(self):
        """Ping 默认网关"""
        result = {"gateway_ip": "", "result": "未找到", "latency": ""}
        try:
            gw = subprocess.run('ipconfig', capture_output=True, text=True, shell=True,
                                encoding='gbk',
                                creationflags=subprocess.CREATE_NO_WINDOW)
            gw_ip = None
            for line in gw.stdout.split('\n'):
                if '默认网关' in line or 'Default Gateway' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        ip = parts[1].strip()
                        if ip and ip != '' and '.' in ip:
                            gw_ip = ip
                            break
            if gw_ip:
                result["gateway_ip"] = gw_ip
                try:
                    r = ping(gw_ip, timeout=3)
                    if r:
                        result["result"] = "通畅"
                        result["latency"] = f"{r * 1000:.1f}ms"
                    else:
                        result["result"] = "超时"
                except Exception:
                    result["result"] = "超时"
        except Exception as e:
            result["result"] = f"异常: {e}"
        return result

    def test_dns(self):
        """测试 DNS 解析"""
        result = {"status": "未知", "latency": ""}
        try:
            import time
            start = time.time()
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 3
            answers = resolver.resolve('baidu.com', 'A')
            elapsed = (time.time() - start) * 1000
            result["status"] = "正常"
            result["latency"] = f"{elapsed:.0f}ms"
            result["ip"] = str(answers[0].address)
        except Exception:
            try:
                start = time.time()
                socket.gethostbyname('baidu.com')
                elapsed = (time.time() - start) * 1000
                result["status"] = "正常"
                result["latency"] = f"{elapsed:.0f}ms"
            except Exception:
                result["status"] = "异常"
        return result

    def test_internet(self):
        """测试外网连通性"""
        result = {"result": "未知", "latency": ""}
        try:
            import time
            start = time.time()
            r = requests.get("https://www.baidu.com", timeout=5)
            elapsed = (time.time() - start) * 1000
            if r.status_code == 200:
                result["result"] = "通畅"
                result["latency"] = f"{elapsed:.0f}ms"
            else:
                result["result"] = f"异常 (HTTP {r.status_code})"
        except requests.exceptions.Timeout:
            result["result"] = "超时"
            result["error"] = "连接超时"
        except requests.exceptions.ConnectionError:
            result["result"] = "不通"
            result["error"] = "无法连接"
        except Exception as e:
            result["result"] = "异常"
            result["error"] = str(e)
        return result

    def ping_host(self, host, count=2):
        """Ping 指定主机"""
        result = {"host": host, "latency": "超时"}
        try:
            r = ping(host, timeout=3)
            if r:
                result["latency"] = f"{r * 1000:.1f}ms"
        except Exception:
            pass
        return result

    # ==================== 域账号查询 ====================
    def domain_user_query(self, username=""):
        """查询域账号信息（通过 net user /domain）"""
        if not username:
            # 自动获取当前登录用户名
            username = os.environ.get('USERNAME', '')
            if not username:
                return {"success": False, "error": "无法获取当前用户名"}

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cmd = f'net user "{username}" /domain'
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk',
                                    timeout=15, startupinfo=startupinfo,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            raw_output = result.stdout

            if result.returncode != 0 or not raw_output.strip():
                # 尝试不带 /domain 参数
                cmd2 = f'net user "{username}"'
                result2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='gbk',
                                         timeout=10, startupinfo=startupinfo,
                                         creationflags=subprocess.CREATE_NO_WINDOW)
                if result2.returncode == 0 and result2.stdout.strip():
                    raw_output = result2.stdout
                else:
                    return {"success": False, "error": f"未找到域账号 '{username}'，请确认用户名正确且已加入域环境",
                            "raw": raw_output}

            # 解析 net user 输出
            info = self._parse_domain_user(raw_output)
            info["success"] = True
            info["raw"] = raw_output
            info["username"] = username
            return info

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "查询超时，请检查域网络连接"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_domain_user(self, output):
        """解析 net user 输出为结构化数据"""
        info = {}

        # 中英文映射
        key_map = {
            "User name": "username", "用户名": "username",
            "Full Name": "full_name", "全名": "full_name",
            "Comment": "comment", "注释": "comment",
            "User's comment": "user_comment", "用户的注释": "user_comment",
            "Country/region code": "country_code", "国家/地区代码": "country_code",
            "Account active": "account_active", "帐户启用": "account_active",
            "Account expires": "account_expires", "帐户到期": "account_expires",
            "Password last set": "password_last_set", "上次设置密码": "password_last_set",
            "Password expires": "password_expires", "密码到期": "password_expires",
            "Password changeable": "password_changeable", "密码可更改": "password_changeable",
            "Password required": "password_required", "需要密码": "password_required",
            "User may change password": "user_may_change_pwd", "用户可以更改密码": "user_may_change_pwd",
            "Workstations allowed": "workstations", "允许的工作站": "workstations",
            "Logon script": "logon_script", "登录脚本": "logon_script",
            "User profile": "user_profile", "用户配置文件": "user_profile",
            "Home directory": "home_directory", "主目录": "home_directory",
            "Last logon": "last_logon", "上次登录": "last_logon",
            "Logon hours allowed": "logon_hours", "可允许的登录小时": "logon_hours",
            "Local Group Memberships": "local_groups", "本地组成员": "local_groups",
            "Global Group memberships": "global_groups", "全局组成员": "global_groups",
            "The command completed successfully": "status", "命令成功完成": "status",
        }

        current_key = None
        current_value = []
        groups = []

        for line in output.split('\n'):
            stripped = line.strip()
            if not stripped:
                if current_key and current_value:
                    val = ' '.join(current_value).strip()
                    mapped = key_map.get(current_key, current_key)
                    info[mapped] = val
                    current_key = None
                    current_value = []
                continue

            # 检测组信息
            if stripped.startswith('*') and current_key and 'group' in current_key.lower():
                groups.append(stripped.lstrip('*').strip())
                continue

            # 尝试匹配键值对
            found_key = False
            for key, mapped in key_map.items():
                if stripped.startswith(key):
                    if current_key and current_value:
                        val = ' '.join(current_value).strip()
                        info[key_map.get(current_key, current_key)] = val
                    current_key = key
                    # 提取值部分
                    val_part = stripped[len(key):].strip()
                    current_value = [val_part] if val_part else []
                    found_key = True
                    break

            if not found_key and current_key:
                current_value.append(stripped)

        # 保存最后一项
        if current_key and current_value:
            val = ' '.join(current_value).strip()
            info[key_map.get(current_key, current_key)] = val

        # 保存组信息
        if groups:
            info["domain_groups"] = groups

        return info

    # ==================== DNS 重置 ====================
    def reset_dns(self):
        """重置 DNS 缓存和网络配置"""
        results = []
        try:
            r = run_hidden_cmd('ipconfig /flushdns', encoding='gbk')
            results.append(f"[DNS 缓存刷新] {'成功' if '成功' in r.stdout or 'successfully' in r.stdout else r.stdout.strip() or r.stderr.strip()}")
        except Exception as e:
            results.append(f"[DNS 缓存刷新] 失败: {e}")

        try:
            r = run_hidden_cmd('ipconfig /registerdns', encoding='gbk')
            results.append(f"[DNS 重新注册] {'完成' if r.returncode == 0 else r.stdout.strip() or '执行完成'}")
        except Exception as e:
            results.append(f"[DNS 重新注册] 失败: {e}")

        try:
            r = run_hidden_cmd('nbtstat -R', encoding='gbk')
            results.append(f"[NetBIOS 名称缓存] {'已清除' if r.returncode == 0 else '执行完成'}")
        except Exception as e:
            results.append(f"[NetBIOS 名称缓存] 失败: {e}")

        return "\n".join(results)


class PasswordTools:
    """密码工具"""

    @staticmethod
    def generate(length=12, use_upper=True, use_lower=True, use_digits=True, use_symbols=True):
        """生成随机密码"""
        char_pools = []
        if use_upper:
            char_pools.append(string.ascii_uppercase)
        if use_lower:
            char_pools.append(string.ascii_lowercase)
        if use_digits:
            char_pools.append(string.digits)
        if use_symbols:
            char_pools.append("!@#$%^&*()_+-=[]{}|;:,.<>?")

        if not char_pools:
            return None, "请至少选择一种字符类型"

        all_chars = ''.join(char_pools)
        password_chars = [random.choice(pool) for pool in char_pools]
        for _ in range(length - len(password_chars)):
            password_chars.append(random.choice(all_chars))
        random.shuffle(password_chars)
        return ''.join(password_chars), None

    @staticmethod
    def check_strength(password):
        """检查密码强度"""
        score = 0
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[^A-Za-z0-9]', password):
            score += 1

        if score >= 6:
            return "非常强", "green"
        elif score >= 5:
            return "强", "green"
        elif score >= 3:
            return "中等", "orange"
        else:
            return "弱", "red"
