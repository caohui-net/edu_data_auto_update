import requests
import pandas as pd

# 1. 设置参数
device_ip = "10.0.0.1"  # 你的设备IP
cookie = "你的cookie内容"  # 用F12复制浏览器里的cookie
headers = {
    "Cookie": cookie,
    "User-Agent": "Mozilla/5.0"
}

# 2. 获取端口流量信息
url_port_traffic = f"https://172.16.12.199/api/devicemgr/v1/port/traffic?deviceIp={device_ip}"
resp_port_traffic = requests.get(url_port_traffic, headers=headers, verify=False)
port_data = resp_port_traffic.json()

# 3. 只保留需要的字段，并做状态转换
fields = [
    ("portName", "端口"),
    ("portState", "状态"),
    ("portInOctets", "入端口流量"),
    ("portOutOctets", "出端口流量"),
    ("portInSpeed", "上行流量速率"),
    ("portOutSpeed", "下行流量速率"),
    ("portAllPkts", "包统计"),
    ("portAllDrops", "丢包数"),
    ("portReceiveFrameError", "错帧数")
]

rows = []
for item in port_data:
    row = {}
    for key, label in fields:
        value = item.get(key, "")
        # 状态字段转换
        if key == "portState":
            value = "关闭" if value == 2 else ("开启" if value == 3 else value)
        row[label] = value
    rows.append(row)

# 4. 保存为Excel
pd.DataFrame(rows).to_excel("设备端口信息.xlsx", index=False)
print("数据已保存到 设备端口信息.xlsx") 