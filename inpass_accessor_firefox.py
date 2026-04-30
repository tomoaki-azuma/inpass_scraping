from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# webdriver_managerを使うと、ドライバーの不整合がほぼ解消されます
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from get_data_object import *
import time
import re

def getInpassPageDriver(url):
    # Firefox用のオプション設定
    options = Options()
    # options.add_argument('--headless') # 画面を見たい場合はコメントアウトのまま

    # Windows環境での起動エラー（Status code 1等）を防ぐための追加設定
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    # 重要：GeckoDriverManagerを使って、確実にFirefox用ドライバーを指定する
    service = Service(GeckoDriverManager().install())
    
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    print("Accessing URL: " + url)
    return driver