import requests
import pandas as pd
import urllib3
import pprint
import sys
import ast
import re

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

# 1. 设置参数
device_ip = "10.0.0.1"  # 你的设备IP
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Cookie": "sdnloginUser=%7B%22controller-ip%22%3A%22172.16.12.199%22%2C%22role%22%3A%5B%22admin%22%5D%2C%22username%22%3A%22mock_admin%22%2C%22rootDefault%22%3A0%7D; currentversion=sdn; sdntheme=white_skin_theme; sdncurrentlang=zh; ioncauthorize=%7B%22scAuthorize%22%3Atrue%2C%22actlAuthorize%22%3Atrue%2C%22pfolAuthorize%22%3Atrue%2C%22adsAuthorize%22%3Atrue%2C%22incAuthorize%22%3Afalse%7D",
    "Host": "172.16.12.199",
    "Referer": "https://172.16.12.199/app/home/incProDeviceDetail?deviceIp=10.0.0.1&jumpfrom=incProDeviceManagement",
    "Sec-Ch-Ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "X-Authorization": "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYWRtaW4iLCJhcmVhSWQiOiIwIiwiZGF0YVJ1bGUiOiJ7fSIsIm5hbWUiOiLnrqHnkIblkZgiLCJ1c2VySWQiOiIxIiwiaWF0IjoxNzQ3NDI0NDQwLCJpc3MiOiJhZG1pbiIsImV4cCI6MTc0NzQyODA0MH0.WWk5Us8Ees6xC066VOn8-idd2ObB7K6-L4xDLsLN5qA",
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

if ag1_list:
    pd.DataFrame(ag1_list).to_excel('设备端口信息_Gi1-3-25_Gi1-3-26_from_txt.xlsx', index=False)
print("提取到的Gi1/3/25_Gi1/3/26端口数量：", len(ag1_list))

