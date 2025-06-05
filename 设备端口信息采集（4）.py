import requests
import pandas as pd
import urllib3
import pprint
import sys
import ast
import re
import time
import os
import json
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN_FILE = "token_cache.json"
TOKEN_EXPIRE_SECONDS = 60 * 50  # 50分钟后自动刷新

def get_token():
    # 如果有缓存且未过期，直接用
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            if time.time() - cache["time"] < TOKEN_EXPIRE_SECONDS:
                return cache["token"]
    # 否则重新登录获取
    login_url = "https://172.16.12.199/api/base/auth/token"
    login_headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Cookie": "sdnloginUser=%7B%22controller-ip%22%3A%22172.16.12.199%22%2C%22role%22%3A%5B%22admin%22%5D%2C%22username%22%3A%22mock_admin%22%2C%22rootDefault%22%3A0%7D; currentversion=sdn; sdntheme=white_skin_theme; sdncurrentlang=zh; ioncauthorize=%7B%22scAuthorize%22%3Atrue%2C%22actlAuthorize%22%3Atrue%2C%22pfolAuthorize%22%3Atrue%2C%22adsAuthorize%22%3Atrue%2C%22incAuthorize%22%3Afalse%7D",
        "Origin": "https://172.16.12.199",
        "Referer": "https://172.16.12.199/app/login",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    }
    login_data = {
        "userName": "admin",
        "password": "P5ewC0VQ4AbRgPDFEoFGdw==",
        "rememberPwd": None,
        "encrypt": True
    }
    resp = requests.post(login_url, headers=login_headers, json=login_data, verify=False)
    print("登录接口返回：", resp.text)
    token = resp.json().get("result", {}).get("token")
    if not token:
        print("登录失败，未获取到token！")
        sys.exit(1)
    # 写入缓存
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump({"token": token, "time": time.time()}, f)
    return token

class Logger(object):
    def __init__(self, filename="output.txt"):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal.flush()
        self.log.flush()
sys.stdout = Logger("output.txt")

def bytes_to_size(t):
    try:
        t = int(t)
    except Exception:
        return str(t)
    if t == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    n = int(math.floor(math.log(t, 1024)))
    return f"{t / (1024 ** n):.3f} {units[n]}"

# 1. 设置参数
device_ip = "10.0.0.1"  # 你的设备IP
token = get_token()
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Cookie": "sdnloginUser=%7B%22controller-ip%22%3A%22172.16.12.199%22%2C%22role%22%3A%5B%22admin%22%5D%2C%22username%22%3A%22mock_admin%22%2C%22rootDefault%22%3A0%7D; currentversion=sdn; sdntheme=white_skin_theme; sdncurrentlang=zh; ioncauthorize=%7B%22scAuthorize%22%3Atrue%2C%22actlAuthorize%22%3Atrue%2C%22pfolAuthorize%22%3Atrue%2C%22adsAuthorize%22%3Atrue%2C%22incAuthorize%22%3Afalse%7D",
    "Host": "172.16.12.199",
    "Referer": f"https://172.16.12.199/app/home/incProDeviceDetail?deviceIp={device_ip}&jumpfrom=incProDeviceManagement",
    "Sec-Ch-Ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "X-Authorization": token,
    "X-Lang": "zh"
}

# 2. 获取端口流量信息
url_port_traffic = f"https://172.16.12.199/api/devicemgr/v1/device/detail/ip?deviceIp={device_ip}"
resp_port_traffic = requests.get(url_port_traffic, headers=headers, verify=False)
port_data = resp_port_traffic.json()
pprint.pprint(port_data)  # 调试用，打印接口返回内容

# 将object下的所有内容写入object_dump.txt，便于查找端口信息实际存放位置
with open('output.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 匹配所有包含'agPorts': 'Gi1/3/25_Gi1/3/26'的字典
pattern = r"({[^{}]*'agPorts': 'Gi1/3/25_Gi1/3/26'[^{}]*})"
matches = re.findall(pattern, content)

print("匹配到的端口字典数量：", len(matches))
ag1_list = []
for m in matches:
    try:
        d = ast.literal_eval(m)
        ag1_list.append({k: str(v) for k, v in d.items()})
    except Exception as e:
        print("解析异常：", e)

# 先做流量转换
for port in ag1_list:
    if 'portInOctets' in port and port['portInOctets'] is not None:
        port['portInOctets'] = bytes_to_size(port['portInOctets'])
    if 'portOutOctets' in port and port['portOutOctets'] is not None:
        port['portOutOctets'] = bytes_to_size(port['portOutOctets'])
    if 'portInSpeed' in port and port['portInSpeed'] is not None:
        port['portInSpeed'] = bytes_to_size(port['portInSpeed']) if not str(port['portInSpeed']).isdigit() else bytes_to_size(int(port['portInSpeed']) // 8) + "/s"
    if 'portOutSpeed' in port and port['portOutSpeed'] is not None:
        port['portOutSpeed'] = bytes_to_size(port['portOutSpeed']) if not str(port['portOutSpeed']).isdigit() else bytes_to_size(int(port['portOutSpeed']) // 8) + "/s"

# 只保留需要的四个字段写入Excel
if ag1_list:
    df = pd.DataFrame(ag1_list)
    df = df[[col for col in ['portInOctets', 'portOutOctets', 'portInSpeed', 'portOutSpeed'] if col in df.columns]]
    df.to_excel('设备端口信息_Gi1-3-25_Gi1-3-26_from_txt.xlsx', index=False)

# 假设port_data['object']['ports']为端口列表
ports = []
if isinstance(port_data, dict):
    ports = port_data.get('object', {}).get('ports', [])

for port in ports:
    if 'portInOctets' in port and port['portInOctets'] is not None:
        port['portInOctets_fmt'] = bytes_to_size(port['portInOctets'])
    if 'portOutOctets' in port and port['portOutOctets'] is not None:
        port['portOutOctets_fmt'] = bytes_to_size(port['portOutOctets'])
    if 'portInSpeed' in port and port['portInSpeed'] is not None:
        port['portInSpeed_fmt'] = bytes_to_size(port['portInSpeed']) if not str(port['portInSpeed']).isdigit() else bytes_to_size(int(port['portInSpeed']) // 8) + "/s"
    if 'portOutSpeed' in port and port['portOutSpeed'] is not None:
        port['portOutSpeed_fmt'] = bytes_to_size(port['portOutSpeed']) if not str(port['portOutSpeed']).isdigit() else bytes_to_size(int(port['portOutSpeed']) // 8) + "/s"

# 输出带单位的流量信息（放在所有print之后，且只输出有流量/速率的端口）
if ports:
    print("\n=== 端口流量统计（带单位） ===")
    for port in ports:
        if any([
            port.get('portInOctets'),
            port.get('portOutOctets'),
            port.get('portInSpeed'),
            port.get('portOutSpeed')
        ]):
            print(f"端口: {port.get('portName', '')}")
            print(f"  入流量: {port.get('portInOctets_fmt', '')}")
            print(f"  出流量: {port.get('portOutOctets_fmt', '')}")
            print(f"  入速率: {port.get('portInSpeed_fmt', '')}")
            print(f"  出速率: {port.get('portOutSpeed_fmt', '')}")
