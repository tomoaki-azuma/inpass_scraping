# from inpass_accessor_firefox import *
# from inpass_accessor_chrome import *
from inpass_accessor_edge import *
from inpass_accessor_common import *
import concurrent.futures
import threading

# コンソールの入力（CAPTCHA）が混線しないためのロック（信号機）
input_lock = threading.Lock()

# 【追加】引数に「barrier（待ち合わせオブジェクト）」を追加
def scrape_for_year(div, barrier):
    url = "https://iprsearch.ipindia.gov.in/publicsearch"
    driver = getInpassPageDriver(url)
    
    try:
        print(f"[検索番号 {div}] ブラウザを起動し、検索条件を入力中...")
        
        # 1. CAPTCHA入力までの処理（ロックにより1つずつ順番に入力）
        searchInpassSite(driver, type="patent_number", target_div=div, input_lock=input_lock)
        
        # 💡 【重要ポイント】CAPTCHA入力が終わったら、ここで他のブラウザを待つ！
        print(f"⏳ [検索番号 {div}] CAPTCHA入力完了。同じグループの全ブラウザの入力を待機しています...")
        barrier.wait() 
        # ↑ グループ内の全員がこの行に到達した瞬間、一斉に次の行へ進みます
        
        # 2. 全員揃ったら、重いスクレイピング処理を一斉に開始
        print(f"🚀 [検索番号 {div}] 全ブラウザの入力完了！スクレイピングを開始します。")
        getPatentUrls(driver)
        scrape_all_pages(driver, "patent_number")
        print(f"✅ [検索番号 {div}] すべての取得が完了しました。")
        
    except threading.BrokenBarrierError:
        print(f"⚠️ [検索番号 {div}] 他のブラウザでエラーが発生したため、待機をキャンセルして終了します。")
    except Exception as e:
        print(f"❌ [検索番号 {div}] エラーが発生しました: {e}")
        # 万が一このブラウザがエラーで落ちた場合、待機中の他のブラウザを永遠に待たせないようにバリアを破壊（キャンセル）する
        barrier.abort() 
    finally:
        driver.quit()

if __name__ == "__main__":

    target_divs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # 検索番号のリスト
    max_parallel_browsers = 5 # 1セット（バッチ）あたり同時に動かすブラウザ数
    
    # 💡 リストを「max_parallel_browsers」個ずつのグループに分割する
    # 例: [0,1], [2,3], [4,5], [6,7], [8,9]
    chunks = [target_divs[i:i + max_parallel_browsers] for i in range(0, len(target_divs), max_parallel_browsers)]
    
    print(f"=== 全 {len(chunks)} セットに分けて処理を開始します ===")
    
    # 分割したグループ（バッチ）ごとに順番に処理
    for batch_num, chunk in enumerate(chunks, 1):
        print(f"\n=======================================================")
        print(f"🎬 第 {batch_num} グループの処理を開始します (対象: 検索番号 {chunk})")
        print(f"=======================================================")
        
        # このグループで動くブラウザの数に合わせて「待ち合わせ場所（Barrier）」を作る
        # ※最後のグループで数が半端になった時（残り1個など）でもフリーズしないための工夫
        current_barrier = threading.Barrier(len(chunk))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunk)) as executor:
            # chunk内の検索番号ごとにスレッドを立ち上げ、current_barrier を渡す
            futures = [executor.submit(scrape_for_year, div, current_barrier) for div in chunk]
            
            # エラー監視用（すべてのスレッドが終わるまで待つ）
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass # エラーは関数内で表示されているのでここではスルー
                    
        print(f"🏁 第 {batch_num} グループのスクレイピングが完了しました。")
        time.sleep(3) # 次のグループを開く前にメモリを落ち着かせる
        
    print("\n🎉 すべての検索番号の処理が完了しました！")

# if __name__ == "__main__":
#     url = "https://iprsearch.ipindia.gov.in/publicsearch"
#     driver = getInpassPageDriver(url)
#     try:
#         searchInpassSite(driver, "patent_number")
#         getPatentUrls(driver)
#         scrape_all_pages(driver, "patent_number")
#     except Exception as e:
#         print(f"エラーが発生しました: {e}")
#     finally:
#         driver.quit()