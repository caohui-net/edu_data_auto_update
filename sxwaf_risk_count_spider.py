from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import re
import os
import shutil
import pandas as pd

# 自动检测Chrome浏览器路径
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

# Selenium配置
chrome_options = Options()
chrome_options.add_argument('--headless')  # 如需可视化可注释掉
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-insecure-localhost')
chrome_options.binary_location = chrome_path

# 显式指定 chromedriver 路径
chromedriver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
if not os.path.exists(chromedriver_path):
    raise FileNotFoundError(f"未找到chromedriver.exe: {chromedriver_path}")
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

url_login = "https://10.0.0.5/login.php"
url_home = "https://10.0.0.5/framework.php"
username = "admin"
password = "AF@hnrpc.com"

result_file = "sxwaf_risk_count_history.xlsx"

def handle_cert_warning(driver):
    """自动处理证书警告页面"""
    time.sleep(2)
    page_source = driver.page_source
    if '您的连接不是私密连接' in page_source or 'NET::ERR_CERT_AUTHORITY_INVALID' in page_source:
        try:
            # 点击"高级"按钮
            advanced_btn = driver.find_element(By.ID, 'details-button')
            advanced_btn.click()
            time.sleep(1)
            # 点击"继续前往"按钮
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

    # 智能等待查找用户名输入框
    user_input = None
    for i in range(10):
        try:
            user_input = driver.find_element(By.NAME, "user")
            break
        except Exception:
            time.sleep(1)
    if not user_input:
        driver.quit()
        exit(1)

    user_input.send_keys(username)

    # 智能等待查找密码输入框
    pwd_input = None
    for i in range(10):
        try:
            pwd_input = driver.find_element(By.NAME, "password")
            break
        except Exception:
            time.sleep(1)
    if not pwd_input:
        driver.quit()
        exit(1)

    pwd_input.send_keys(password)
    pwd_input.send_keys(Keys.RETURN)
    time.sleep(5)
    driver.get(url_home)
    handle_cert_warning(driver)
    time.sleep(5)

    while True:
        page_text = driver.page_source
        big_numbers = re.findall(r'>\s*(\d{4,})\s*<', page_text)
        if big_numbers:
            risk_count = big_numbers[0]
            row = {"采集时间": time.strftime('%Y-%m-%d %H:%M:%S'), "业务风险数分析": risk_count}
            if os.path.exists(result_file):
                df = pd.read_excel(result_file)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_excel(result_file, index=False)
            else:
                pd.DataFrame([row]).to_excel(result_file, index=False)
        time.sleep(3600)
except KeyboardInterrupt:
    print("程序已手动终止，退出采集。")
finally:
    driver.quit() 