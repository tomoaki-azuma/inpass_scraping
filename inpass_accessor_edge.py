from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager

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
    options.page_load_strategy = 'eager'
    # EdgeChromiumDriverManagerを使用してドライバーを自動インストール・設定
    # service = Service(EdgeChromiumDriverManager().install())
    
    # webdriver.Edge を使用
    driver = webdriver.Edge(options=options)
    
    driver.get(url)
    return driver