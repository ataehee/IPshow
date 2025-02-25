import requests
import socket
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import time
import threading
import logging
import sys
from datetime import datetime
import os

# 配置日志
logging.basicConfig(
    filename='ip_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# IP 查询服务列表
IP_APIS = [
    'https://api64.ipify.org?format=json',
    'https://api.ipify.org?format=json',
    'http://ip-api.com/json',
    'https://api.ip.sb/jsonip',
    'https://api.myip.com',
]

class IPMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('IP 监控客户端')
        self.root.geometry('400x250')  # 调整窗口宽度为400
        
        # 初始化监控状态
        self.is_monitoring = True
        
        self.server_url = self.load_latest_url()
        self.init_ui()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_ip, daemon=True)
        self.monitor_thread.start()

    def init_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        
        # 配置主框架的网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 状态标签和指示灯框架
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.N+tk.EW)
        status_frame.grid_columnconfigure(0, weight=1)
        
        # 创建内部框架来包含状态标签和指示灯
        inner_status_frame = ttk.Frame(status_frame)
        inner_status_frame.grid(row=0, column=0)
        
        # 状态标签
        self.status_label = ttk.Label(inner_status_frame, text="正常监控中...")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 监控状态指示灯
        self.indicator = ttk.Label(inner_status_frame, text="●", font=('TkDefaultFont', 18), foreground="green")
        self.indicator.pack(side=tk.LEFT)
        
        # URL输入框和更新按钮框架
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        # URL输入框
        self.url_entry = ttk.Entry(url_frame, width=35)
        self.url_entry.insert(0, self.server_url)
        self.url_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 更新URL按钮
        self.update_url_button = ttk.Button(url_frame, text="更新URL", command=self.update_server_url)
        self.update_url_button.pack(side=tk.LEFT)
        
        # 显示最新的SERVER_URL（只读）
        url_display_frame = ttk.Frame(main_frame)
        url_display_frame.grid(row=2, column=0, columnspan=2, pady=3, sticky=tk.W)
        
        self.url_display = ttk.Entry(url_display_frame, width=35, state='readonly')
        self.url_display.insert(0, self.server_url)
        self.url_display.pack(side=tk.LEFT, padx=(23, 0))
        
        # IP显示标签
        self.ip_label = ttk.Label(main_frame, text="当前IP: 未知", anchor="center")
        self.ip_label.grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        # 最后更新时间标签
        self.time_label = ttk.Label(main_frame, text="最后更新: --", anchor="center")
        self.time_label.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.EW)
        
        # 开始/停止按钮
        self.start_button = ttk.Button(main_frame, text="停止监控", command=self.toggle_monitoring)
        self.start_button.grid(row=5, column=0, columnspan=2, pady=5)
        
        # 手动发送按钮
        self.send_button = ttk.Button(main_frame, text="手动发送IP", command=self.send_ip_manually)
        self.send_button.grid(row=6, column=0, columnspan=2, pady=5)
        
        # 设置窗口图标
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # 更新初始状态
        self.update_status("开始监控...")

        # 监控状态
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_ip, daemon=True)
        self.monitor_thread.start()  # 自动启动监控线程

        # 设置窗口图标
        try:
            self.root.iconbitmap('icon.ico')  # 如果有图标文件的话
        except:
            pass

        # 更新初始状态
        self.update_status("开始监控...")

    def get_public_ip(self):
        """获取公网IP地址"""
        # 使用 Python 请求获取 IP
        for api_url in IP_APIS:
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if "ip" in data:
                        return data["ip"]
                    elif "query" in data:
                        return data["query"]
            except Exception as e:
                logging.error(f"API {api_url} 请求失败: {str(e)}")
                continue
        return None

    def get_ip_from_router(self):
        try:
            # 访问本地路由器获取公网 IP
            response = requests.get('http://192.168.1.1', timeout=5)  # 根据实际路由器地址修改
            if response.status_code == 200:
                # 解析返回的 HTML 或 JSON 数据以获取 IP
                # 这里需要根据路由器的具体返回格式进行解析
                # 假设返回的内容中包含 "Your IP is: xxx.xxx.xxx.xxx"
                # 需要根据实际情况进行调整
                return self.parse_router_response(response.text)
        except Exception as e:
            logging.error(f"从路由器获取IP失败: {str(e)}")
        return None

    def parse_router_response(self, response_text):
        # 解析路由器返回的内容以提取 IP 地址
        # 这里需要根据实际情况进行实现
        # 例如，使用正则表达式或字符串操作
        return None  # 返回提取到的 IP 地址

    def update_status(self, message, ip=None, error=False):
        self.status_label.configure(text=message, foreground="red" if error else "black")
        
        if ip:
            self.ip_label.configure(text=f"当前IP: {ip}")
            self.time_label.configure(text=f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 更新指示灯颜色
        self.indicator.configure(foreground="green" if self.is_monitoring else "red")

    def send_ip_to_server(self, ip):
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            response = requests.post(self.server_url, json={
                'ip': ip,
                'timestamp': timestamp
            }, timeout=5)
            if response.status_code == 200:
                logging.info(f"成功发送IP到服务器: {ip}")
                self.limit_log_file()
                return True
            else:
                logging.error(f"发送IP失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"发送IP到服务器时出错: {str(e)}")
            return False

    def limit_log_file(self):
        # 限制日志文件最多保存20条数据
        with open('ip_monitor.log', 'r+') as log_file:
            lines = log_file.readlines()
            if len(lines) > 20:
                log_file.seek(0)
                log_file.writelines(lines[-20:])  # 保留最后20条记录
                log_file.truncate()  # 截断文件

    def monitor_ip(self):
        while self.is_monitoring:
            ip = self.get_public_ip()
            if ip:
                self.update_status("正常监控中...", ip)
                self.send_ip_to_server(ip)
            else:
                self.update_status("获取IP失败，等待下次尝试...", error=True)
            
            # 等待5分钟
            for _ in range(300):  # 5分钟 = 300秒
                if not self.is_monitoring:
                    break
                time.sleep(1)

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.start_button.configure(text="停止监控")
            self.update_status("开始监控...")
            self.monitor_thread = threading.Thread(target=self.monitor_ip, daemon=True)
            self.monitor_thread.start()
        else:
            self.is_monitoring = False
            self.start_button.configure(text="开始监控")
            self.update_status("监控已停止")

    def send_ip_manually(self):
        ip = self.get_public_ip()  # 获取当前公网 IP
        if ip:
            success = self.send_ip_to_server(ip)  # 发送 IP 到服务器
            if success:
                self.update_status("手动发送成功", ip)
                # 3秒后恢复原来的状态提示
                threading.Timer(3.0, self.restore_status).start()
            else:
                self.update_status("手动发送失败", error=True)
                # 3秒后恢复原来的状态提示
                threading.Timer(3.0, self.restore_status).start()
        else:
            self.update_status("获取IP失败，无法发送", error=True)
            # 3秒后恢复原来的状态提示
            threading.Timer(3.0, self.restore_status).start()

    def update_server_url(self):
        """更新服务器URL并保存到文件"""
        new_url = self.url_entry.get().strip()
        print(f"Attempting to update URL to: {new_url}")  # 调试信息
        if new_url:
            # 保存URL到文件
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.save_url_to_file(new_url, timestamp)
            
            # 更新当前使用的URL
            self.server_url = new_url
            # 更新只读文本框显示
            self.url_display.configure(state='normal')
            self.url_display.delete(0, tk.END)
            self.url_display.insert(0, new_url)
            self.url_display.configure(state='readonly')
            
            self.update_status(f"服务器URL已更新: {new_url}")
            print(f"Updated SERVER_URL: {new_url}")  # 调试信息
            threading.Timer(3.0, self.restore_status).start()
        else:
            self.update_status("URL不能为空", error=True)
            threading.Timer(3.0, self.restore_status).start()

    def save_url_to_file(self, url, timestamp):
        """保存URL到文件，最多保存10条记录"""
        url_file = 'url_records.txt'
        try:
            # 读取现有记录
            records = []
            if os.path.exists(url_file):
                with open(url_file, 'r') as f:
                    records = [line.strip().split(',') for line in f.readlines()]
            
            # 添加新记录
            records.append([url, timestamp])
            
            # 按时间戳排序并保留最新的10条记录
            records.sort(key=lambda x: x[1], reverse=True)
            records = records[:10]
            
            # 写入文件
            with open(url_file, 'w') as f:
                for record in records:
                    f.write(f"{record[0]},{record[1]}\n")
            
            print(f"URL saved to file: {url}")
        except Exception as e:
            print(f"Error saving URL to file: {str(e)}")

    def load_latest_url(self):
        """从文件加载最新的URL"""
        url_file = 'url_records.txt'
        default_url = 'http://localhost/IPShowServer/index.php'  # 默认URL
        
        try:
            print(f"Checking for URL file: {url_file}")  # 调试信息
            if os.path.exists(url_file):
                print(f"URL file found: {url_file}")  # 调试信息
                with open(url_file, 'r') as f:
                    records = [line.strip().split(',') for line in f.readlines()]
                    print(f"Records found in file: {records}")  # 调试信息
                    if records:
                        # 按时间戳排序并获取最新的记录
                        records.sort(key=lambda x: x[1], reverse=True)
                        latest_url = records[0][0]
                        print(f"Latest URL loaded from file: {latest_url}")  # 调试信息
                        
                        # 确保URL不为空且格式正确
                        if latest_url and latest_url.strip():
                            return latest_url
                        else:
                            print("Latest URL is empty or invalid")  # 调试信息
                    else:
                        print("No records found in file")  # 调试信息
            else:
                print(f"URL file not found: {url_file}")  # 调试信息
        except Exception as e:
            print(f"Error loading URL from file: {str(e)}")
        
        print(f"Using default URL: {default_url}")  # 调试信息
        return default_url

    def restore_status(self):
        """恢复原来的状态提示"""
        if self.is_monitoring:
            self.update_status("正常监控中...")
        else:
            self.update_status("监控已停止")

    def run(self):
        # 设置窗口在屏幕中央
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # 设置窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # 启动主循环
        self.root.mainloop()

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要退出程序吗?"):
            self.is_monitoring = False
            self.root.destroy()
            sys.exit()

if __name__ == "__main__":
    # 隐藏控制台窗口
    try:
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except Exception as e:
        pass  # 忽略任何隐藏控制台的错误
    
    monitor = IPMonitor()
    monitor.run()