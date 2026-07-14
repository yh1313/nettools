# tools.py - NetTools 核心工具模块
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
    def traceroute(self, target, max_hops=30):
        """路由追踪"""
        try:
            if os.name == 'nt':
                cmd = f"tracert -d -h {max_hops} {target}"
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk', timeout=120)
            else:
                cmd = f"traceroute -m {max_hops} {target}"
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return {"success": True, "output": result.stdout}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "路由追踪超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== 端口扫描 ====================
    def port_scan(self, ip, ports=None, timeout=2, max_threads=100, deep_scan=False):
        """TCP 端口扫描"""
        if ports is None:
            port_list = [21, 22, 23, 25, 53, 80, 110, 143, 161, 443, 3389, 8080, 8443, 3306, 5432, 6379, 27017]
        elif isinstance(ports, str):
            port_list = []
            for part in ports.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    port_list.extend(range(start, end + 1))
                else:
                    port_list.append(int(part))
        else:
            port_list = ports

        if deep_scan:
            timeout = max(timeout, 3.0)
            retries = 2
        else:
            retries = 1

        open_ports = []
        details = []

        def scan_port(port):
            for attempt in range(retries + 1):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    start = time.time()
                    ret = sock.connect_ex((ip, port))
                    elapsed = (time.time() - start) * 1000
                    sock.close()
                    if ret == 0:
                        return {"port": port, "status": "open", "latency": f"{elapsed:.2f}ms",
                                "service": self._get_port_service(port)}
                    else:
                        if attempt < retries:
                            time.sleep(0.2)
                            continue
                        return {"port": port, "status": "closed"}
                except socket.timeout:
                    if attempt < retries:
                        time.sleep(0.2)
                        continue
                    return {"port": port, "status": "timeout"}
                except Exception as e:
                    return {"port": port, "status": "error", "reason": str(e)}
            return {"port": port, "status": "closed"}

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_map = {executor.submit(scan_port, p): p for p in port_list}
            for future in as_completed(future_map):
                port = future_map[future]
                try:
                    detail = future.result()
                    details.append(detail)
                    if detail["status"] == "open":
                        open_ports.append({"port": detail["port"], "service": detail["service"],
                                           "latency": detail.get("latency", "N/A")})
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
            response = requests.get(url, timeout=timeout, headers={"User-Agent": "NetTools/1.0"})
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
    def network_quality(self, target="8.8.8.8", packets=15):
        """综合网络质量评估"""
        ping_result = self.ping_test(target, count=packets)
        loss_rate = float(ping_result['packet_loss'].replace('%', ''))
        avg_latency = float(ping_result['avg_latency'].replace('ms', '')) if ping_result['avg_latency'] != 'N/A' else 0

        quality_score = 100
        if loss_rate > 10:
            quality_score -= 30
        elif loss_rate > 5:
            quality_score -= 15
        elif loss_rate > 1:
            quality_score -= 5

        if avg_latency > 100:
            quality_score -= 20
        elif avg_latency > 50:
            quality_score -= 10

        quality_score = max(0, min(100, quality_score))

        if quality_score >= 80:
            quality_level = "优秀"
        elif quality_score >= 60:
            quality_level = "良好"
        else:
            quality_level = "较差"

        # 建议
        if loss_rate > 5:
            suggestion = "丢包率过高，建议检查物理链路和交换机端口"
        elif avg_latency > 100:
            suggestion = "延迟过高，建议检查路由路径和链路带宽"
        elif loss_rate > 0:
            suggestion = "存在少量丢包，可能需要检查网络稳定性"
        else:
            suggestion = "网络质量良好"

        return {
            "target": target,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "packet_loss": ping_result['packet_loss'],
            "avg_latency": ping_result['avg_latency'],
            "min_latency": ping_result['min_latency'],
            "max_latency": ping_result['max_latency'],
            "suggestion": suggestion
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
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 67: "DHCP", 68: "DHCP", 69: "TFTP",
            80: "HTTP", 110: "POP3", 123: "NTP", 143: "IMAP",
            161: "SNMP", 162: "SNMP-Trap", 179: "BGP",
            443: "HTTPS", 465: "SMTPS", 514: "Syslog", 587: "SMTP",
            993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
            3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
            6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
            27017: "MongoDB", 9090: "Prometheus", 9100: "NodeExporter"
        }
        return services.get(port, f"Port-{port}")


class SystemTools:
    """系统工具集"""

    def __init__(self):
        pass

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
            subprocess.run('ipconfig /flushdns', capture_output=True, text=True, shell=True)
            return True, "DNS缓存已刷新"
        except Exception as e:
            return False, str(e)

    # ==================== WiFi 密码查看 ====================
    def get_wifi_passwords(self):
        """查看已保存的 WiFi 密码 (Windows)"""
        results = []
        try:
            output = subprocess.run('netsh wlan show profiles', capture_output=True, text=True, shell=True).stdout
            profiles = re.findall(r'所有用户配置文件 : (.*)', output)
            if not profiles:
                # 英文系统
                profiles = re.findall(r'All User Profile\s*:\s*(.*)', output)
            for profile in profiles:
                profile = profile.strip()
                info = subprocess.run(f'netsh wlan show profile name="{profile}" key=clear',
                                      capture_output=True, text=True, shell=True).stdout
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
            result = subprocess.run('netsh interface show interface', capture_output=True, text=True, shell=True)
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
            result = subprocess.run('ipconfig /all', capture_output=True, text=True, shell=True, encoding='gbk')
            return {"success": True, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}


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
