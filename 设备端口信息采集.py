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
import threading
from datetime import datetime

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

def speed_to_str(val):
    try:
        val = float(val) / 8  # bit/s转为Byte/s
    except Exception:
        return str(val)
    if val == 0:
        return "0 B/s"
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    n = int(math.floor(math.log(val, 1024)))
    return f"{val / (1024 ** n):.3f} {units[n]}/s"

def collect_and_save():
# 1. 设置参数
device_ip = "10.0.0.1"  # 你的设备IP
    token = get_token()
headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Cookie": "...",
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
    # 只保留本次内容，覆盖output.txt
    with open('output.txt', 'w', encoding='utf-8') as f:
        pprint.pprint(port_data, stream=f)

    # 用正则从output.txt中提取端口字典，只取第一条
    with open('output.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r"({[^{}]*'agPorts': 'Gi1/3/25_Gi1/3/26'[^{}]*})"
    matches = re.findall(pattern, content)
    ag1_list = []
    collect_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if matches:
        try:
            d = ast.literal_eval(matches[0])
            record = dict(d)  # 保持原始类型
            record['collect_time'] = collect_time
            ag1_list.append(record)
        except Exception as e:
            print("解析异常：", e)
    print("提取到的端口数量：", len(ag1_list))
    # 追加写入Excel（保留全部字段和原始类型）
    file_path = '设备端口信息_Gi1-3-25_Gi1-3-26_from_txt.xlsx'
    if ag1_list:
        if os.path.exists(file_path):
            old_df = pd.read_excel(file_path)
            new_df = pd.DataFrame(ag1_list)
            all_df = pd.concat([old_df, new_df], ignore_index=True)
            all_df.to_excel(file_path, index=False)
        else:
            pd.DataFrame(ag1_list).to_excel(file_path, index=False)

        # 差值统计：只有数据行数大于1时才进行
        df = pd.read_excel(file_path)
        if len(df) > 1:
            try:
                df['portInOctets'] = pd.to_numeric(df['portInOctets'], errors='coerce')
                df['portOutOctets'] = pd.to_numeric(df['portOutOctets'], errors='coerce')
                last = df.iloc[-1]
                prev = df.iloc[-2]
                diff_in = last['portInOctets'] - prev['portInOctets'] if pd.notnull(last['portInOctets']) and pd.notnull(prev['portInOctets']) else None
                diff_out = last['portOutOctets'] - prev['portOutOctets'] if pd.notnull(last['portOutOctets']) and pd.notnull(prev['portOutOctets']) else None
                # 新增速率字段
                portInSpeed = speed_to_str(last.get('portInSpeed', 0))
                portOutSpeed = speed_to_str(last.get('portOutSpeed', 0))
                diff = {
                    'collect_time': last.get('collect_time', ''),
                    'portInOctets_diff': bytes_to_size(diff_in) if diff_in is not None else '',
                    'portOutOctets_diff': bytes_to_size(diff_out) if diff_out is not None else '',
                    'portInSpeed': portInSpeed,
                    'portOutSpeed': portOutSpeed
                }
                diff_path = '端口流量统计表.xlsx'
                if os.path.exists(diff_path):
                    diff_df = pd.read_excel(diff_path)
                    diff_df = pd.concat([diff_df, pd.DataFrame([diff])], ignore_index=True)
                    diff_df.to_excel(diff_path, index=False)
                else:
                    pd.DataFrame([diff]).to_excel(diff_path, index=False)
            except Exception as e:
                print("差值统计异常：", e)

if __name__ == "__main__":
    sys.stdout = Logger("output.txt")  # 确保所有print都重定向
    try:
        while True:
            try:
                open("output.txt", "w").close()  # 每次采集前清空output.txt
                collect_and_save()
                print(f"采集完成，等待1小时后再次采集...\n")
            except Exception as e:
                print(f"采集异常: {e}")
            time.sleep(3600)
    except KeyboardInterrupt:
        print("程序已手动终止，退出采集。")
