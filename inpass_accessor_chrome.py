from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Chrome用のマネージャーを使用
from webdriver_manager.chrome import ChromeDriverManager
from get_data_object import *

def getInpassPageDriver(url):
    # Chrome用のオプション設定
    options = Options()
    # options.add_argument('--headless') # 画面を見たい場合はコメントアウトのまま

    # Windows環境での起動エラー（Status code 1等）を防ぐための追加設定
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-allow-origins=*')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-popup-blocking') # ポップアップブロックの無効化
    options.add_argument('--disable-site-isolation-trials') # サイト分離機能の無効化（真っ白対策の特効薬）
    options.add_argument('--disable-web-security') # クロスドメイン制限の無効化

    # ChromeDriverManagerを使用してドライバーを自動インストール・設定
    service = Service(ChromeDriverManager().install())
    
    # webdriver.Chrome を使用
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get(url)
    return driver