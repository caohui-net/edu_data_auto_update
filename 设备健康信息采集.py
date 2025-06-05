import requests
import pandas as pd
import time

# 1. 设置参数
device_ip = "10.0.0.1"  # 你的设备IP
cookie = "你的cookie内容"  # 用F12复制浏览器里的cookie
headers = {
    "Cookie": cookie,
    "User-Agent": "Mozilla/5.0"
}

# 2. 获取槽位信息
url_slot = f"https://172.16.12.199/api/devicemgr/v1/health/latest/device?deviceIp={device_ip}"
resp_slot = requests.get(url_slot, headers=headers, verify=False)
slot_data = resp_slot.json()
slot_list = slot_data.get("perSlot", [])
if not slot_list:
    print("未获取到槽位信息")
    exit()
slot_id = slot_list[0]["slotId"]  # 取第一个槽位

# 3. 设置时间范围（最近7天）
end_time = int(time.time() * 1000)
start_time = end_time - 7 * 24 * 60 * 60 * 1000

# 4. 获取槽位健康历史（CPU、内存）
url_health_slot = f"https://172.16.12.199/api/devicemgr/v1/health/history/slot?deviceIp={device_ip}&slotId={slot_id}&startTime={start_time}&endTime={end_time}"
resp_health_slot = requests.get(url_health_slot, headers=headers, verify=False)
health_slot_data = resp_health_slot.json()

# 5. 获取设备健康历史（ARP、MAC）
url_health_device = f"https://172.16.12.199/api/devicemgr/v1/health/history/device?deviceIp={device_ip}&startTime={start_time}&endTime={end_time}"
resp_health_device = requests.get(url_health_device, headers=headers, verify=False)
health_device_data = resp_health_device.json()

# 6. 保存为Excel
with pd.ExcelWriter("设备健康信息.xlsx") as writer:
    pd.DataFrame(slot_list).to_excel(writer, sheet_name="槽位信息", index=False)
    pd.DataFrame(health_slot_data.get("cpuRecord", [])).to_excel(writer, sheet_name="CPU历史", index=False)
    pd.DataFrame(health_slot_data.get("memoryRecord", [])).to_excel(writer, sheet_name="内存历史", index=False)
    pd.DataFrame(health_device_data.get("arpRecord", [])).to_excel(writer, sheet_name="ARP历史", index=False)
    pd.DataFrame(health_device_data.get("macRecord", [])).to_excel(writer, sheet_name="MAC历史", index=False)

print("数据已保存到 设备健康信息.xlsx") 