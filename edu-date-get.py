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
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN_FILE = "token_cache.json"
TOKEN_EXPIRE_SECONDS = 60 * 50  # 50分钟后自动刷新

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 只显示ERROR及以上的TensorFlow日志

import warnings
warnings.filterwarnings('ignore')  # 忽略所有Python警告

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            if time.time() - cache["time"] < TOKEN_EXPIRE_SECONDS:
                return cache["token"]
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
    device_ip = "10.0.0.1"
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
    url_port_traffic = f"https://172.16.12.199/api/devicemgr/v1/device/detail/ip?deviceIp={device_ip}"
    resp_port_traffic = requests.get(url_port_traffic, headers=headers, verify=False)
    port_data = resp_port_traffic.json()
    with open('output.txt', 'w', encoding='utf-8') as f:
        pprint.pprint(port_data, stream=f)
    with open('output.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r"({[^{}]*'agPorts': 'Gi1/3/25_Gi1/3/26'[^{}]*})"
    matches = re.findall(pattern, content)
    ag1_list = []
    collect_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if matches:
        try:
            d = ast.literal_eval(matches[0])
            record = dict(d)
            record['collect_time'] = collect_time
            ag1_list.append(record)
        except Exception as e:
            print("解析异常：", e)
    print("提取到的端口数量：", len(ag1_list))
    file_path = '设备端口信息_Gi1-3-25_Gi1-3-26_from_txt.xlsx'
    if ag1_list:
        if os.path.exists(file_path):
            old_df = pd.read_excel(file_path)
            new_df = pd.DataFrame(ag1_list)
            all_df = pd.concat([old_df, new_df], ignore_index=True)
            all_df.to_excel(file_path, index=False)
        else:
            pd.DataFrame(ag1_list).to_excel(file_path, index=False)
        df = pd.read_excel(file_path)
        if len(df) > 1:
            try:
                df['portInOctets'] = pd.to_numeric(df['portInOctets'], errors='coerce')
                df['portOutOctets'] = pd.to_numeric(df['portOutOctets'], errors='coerce')
                last = df.iloc[-1]
                prev = df.iloc[-2]
                diff_in = last['portInOctets'] - prev['portInOctets'] if pd.notnull(last['portInOctets']) and pd.notnull(prev['portInOctets']) else None
                diff_out = last['portOutOctets'] - prev['portOutOctets'] if pd.notnull(last['portOutOctets']) and pd.notnull(prev['portOutOctets']) else None
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

def port_info_task():
    try:
        while True:
            try:
                open("output.txt", "w").close()
                collect_and_save()
                print(f"采集完成，等待1小时后再次采集...\n")
            except Exception as e:
                print(f"采集异常: {e}")
            time.sleep(600)
    except KeyboardInterrupt:
        print("端口信息采集已手动终止。")

def sxwaf_risk_count_task():
    possible_chrome_paths = [
        r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        r"C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
        r"D:\\Chrome\\App\\chrome.exe"
    ]
    chrome_path = None
    for path in possible_chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    if not chrome_path:
        print("未检测到Chrome浏览器，请手动指定chrome.exe路径！")
        chrome_path = input("请输入chrome.exe的完整路径：").strip()
        if not os.path.exists(chrome_path):
            raise FileNotFoundError(f"未找到指定的chrome.exe: {chrome_path}")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.binary_location = chrome_path
    chromedriver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    if not os.path.exists(chromedriver_path):
        raise FileNotFoundError(f"未找到chromedriver.exe: {chromedriver_path}")
    service = Service(executable_path=chromedriver_path, log_path=os.devnull)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    url_login = "https://10.0.0.5/login.php"
    url_home = "https://10.0.0.5/framework.php"
    username = "admin"
    password = "AF@hnrpc.com"
    result_file = "sxwaf_risk_count_history.xlsx"
    def handle_cert_warning(driver):
        time.sleep(2)
        page_source = driver.page_source
        if '您的连接不是私密连接' in page_source or 'NET::ERR_CERT_AUTHORITY_INVALID' in page_source:
            try:
                advanced_btn = driver.find_element(By.ID, 'details-button')
                advanced_btn.click()
                time.sleep(1)
                proceed_btn = driver.find_element(By.ID, 'proceed-link')
                proceed_btn.click()
                print("已自动跳过证书警告页面")
                time.sleep(2)
            except Exception as e:
                print("自动跳过证书警告页面失败：", e)
                driver.save_screenshot("cert_warning.png")
                print("已保存证书警告页面截图: cert_warning.png")
                with open("cert_warning.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("已保存证书警告页面HTML: cert_warning.html")
                driver.quit()
                exit(1)
    try:
        driver.get(url_login)
        handle_cert_warning(driver)
        time.sleep(2)
        user_input = None
        for i in range(10):
            try:
                user_input = driver.find_element(By.NAME, "user")
                break
            except Exception:
                time.sleep(1)
        if not user_input:
            driver.quit()
            return
        user_input.send_keys(username)
        pwd_input = None
        for i in range(10):
            try:
                pwd_input = driver.find_element(By.NAME, "password")
                break
            except Exception:
                time.sleep(1)
        if not pwd_input:
            driver.quit()
            return
        pwd_input.send_keys(password)
        pwd_input.send_keys(Keys.RETURN)
        time.sleep(5)
        driver.get(url_home)
        handle_cert_warning(driver)
        time.sleep(5)
        def wait_for_risk_text(driver, timeout=20):
            try:
                WebDriverWait(driver, timeout).until(
                    lambda d: any(
                        div.text.strip() == '风险业务数'
                        for div in d.find_elements(By.CLASS_NAME, 'legend-subtitle-text')
                    )
                )
                return True
            except TimeoutException:
                return False
        while True:
            try:
                print("开始采集风险业务数...")
                # 滚动页面到底部，等待内容加载
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                found = wait_for_risk_text(driver, timeout=20)
                driver.save_screenshot('current_page.png')
                if not found:
                    print("等待页面出现'风险业务数'超时，已保存current_page.png供排查。")
                    page_text = driver.page_source
                    with open("debug.html", "w", encoding="utf-8") as f:
                        f.write(page_text)
                    time.sleep(600)
                    continue
                page_text = driver.page_source
                soup = BeautifulSoup(page_text, 'html.parser')
                risk_business_num = None
                for txt_div in soup.find_all('div', class_='legend-subtitle-text'):
                    if txt_div.get_text(strip=True) == '风险业务数':
                        # 先尝试前一个兄弟节点
                        prev_div = txt_div.find_previous_sibling('div')
                        if prev_div and prev_div.get('class') and 'legend-total-num' in ' '.join(prev_div.get('class')):
                            risk_business_num = prev_div.get_text(strip=True)
                        # 如果还没找到，再尝试父节点下的所有div
                        if not risk_business_num:
                            parent = txt_div.parent
                            for sib in parent.find_all('div', recursive=False):
                                if sib is not txt_div and sib.get('class') and 'legend-total-num' in ' '.join(sib.get('class')):
                                    risk_business_num = sib.get_text(strip=True)
                                    break
                        break
                if risk_business_num is not None:
                    collect_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    row = {"采集时间": collect_time, "风险业务数": risk_business_num}
                    print(f"准备写入：{row}")
                    try:
                        if os.path.exists(result_file):
                            df = pd.read_excel(result_file)
                            # 保证列顺序
                            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                            # 只保留这两列，且顺序为采集时间、风险业务数
                            df = df[["采集时间", "风险业务数"]]
                            df.to_excel(result_file, index=False)
                        else:
                            pd.DataFrame([row], columns=["采集时间", "风险业务数"]).to_excel(result_file, index=False)
                        print(f"已写入：{row}")
                    except Exception as e:
                        print("写入Excel异常：", e)
                else:
                    print("未采集到风险业务数！已保存debug.html供排查。")
                    with open("debug.html", "w", encoding="utf-8") as f:
                        f.write(page_text)
            except Exception as e:
                print("采集流程异常：", e)
            time.sleep(600)
    except KeyboardInterrupt:
        print("风险数采集已手动终止。")
    finally:
        driver.quit()

if __name__ == "__main__":
    sys.stdout = Logger("output.txt")
    t1 = threading.Thread(target=sxwaf_risk_count_task, daemon=True)
    t2 = threading.Thread(target=port_info_task, daemon=True)
    t1.start()
    t2.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("程序已手动终止，退出采集。") 