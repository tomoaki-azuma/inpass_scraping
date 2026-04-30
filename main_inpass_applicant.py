# from inpass_accessor_firefox import *
# from inpass_accessor_chrome import *
from inpass_accessor_edge import *
from inpass_accessor_common import *
from inpass_accessor_edge import *
from inpass_accessor_common import *
import concurrent.futures
import threading

# コンソールの入力（CAPTCHA）が混線しないためのロック（信号機）
input_lock = threading.Lock()

def scrape_for_year(year):
    url = "https://iprsearch.ipindia.gov.in/publicsearch"
    
    # 各スレッド（並列処理）ごとに独立したEdgeブラウザを立ち上げる
    driver = getInpassPageDriver(url)
    
    try:
        print(f"[{year}年] ブラウザを起動し、検索条件を入力中...")
        
        # ⚠️ searchInpassSite の中身は少し変更が必要です（後述）
        searchInpassSite(driver, type="applicant", year=year, input_lock=input_lock)
        
        # --- ここから先の重い処理（ページ遷移と詳細取得）は、すべてのブラウザが「同時」に走ります ---
        print(f"[{year}年] 検索開始。並列でデータを取得します。")
        getPatentUrls(driver)
        scrape_all_pages(driver, "applicant")
        print(f"✅ [{year}年] すべての取得が完了しました。")
        
    except Exception as e:
        print(f"❌ [{year}年] エラーが発生しました: {e}")
    finally:
        driver.quit()



if __name__ == "__main__":

    # 処理したい年のリストを作成します。必要に応じて年を追加してください。
    # コンソールで入力を促す
    years_input = input("検索したい年をカンマ区切りで入力してください（例: 2020, 2021, 2022） > ")
        
    # 入力された文字列をカンマ(,)で分割し、前後の空白を消す
    target_years = [y.strip() for y in years_input.split(',')]

    
    # 【重要】同時に立ち上げるブラウザの最大数
    # メモリ不足を防ぐため、最初は 2 か 3 くらいから試すことを強くお勧めします
    max_parallel_browsers = 3
    
    print(f"=== 最大 {max_parallel_browsers} 個のブラウザを同時に立ち上げて処理を開始します ===")
    
    # ThreadPoolExecutorを使って関数を並列実行
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel_browsers) as executor:
        # target_years の各要素を scrape_for_year に渡して並列実行
        executor.map(scrape_for_year, target_years)
        
    print("=== すべての年の処理が完了しました ===")

    # url = "https://iprsearch.ipindia.gov.in/publicsearch"
    # driver = getInpassPageDriver(url)
    # try:
    #     searchInpassSite(driver, "applicant") # "applicant" or "patent_number"
    #     getPatentUrls(driver)
    #     scrape_all_pages(driver, "applicant")
    # except Exception as e:
    #     print(f"エラーが発生しました: {e}")
    # finally:
    #     driver.quit()