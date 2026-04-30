from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# Chrome用のマネージャーを使用
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from get_data_object import *
import time
import re

def closeDriver(driver):
    driver.quit()

def searchInpassSite(driver, type, year=None, target_div=None, input_lock=None):
    if type == "applicant":
        target = getTargetApplicant()
    elif type == "patent_number":
        target = getTargetPatentNum(target_div=target_div)
        print(f"検索対象の特許番号: {target}")
    else:
        print("Invalid type. Please specify 'applicant' or 'patent_number'.")
        return

    wait = WebDriverWait(driver, 10)
    try:    
        # 要素がクリック可能になるまで待機
        pub_type = wait.until(EC.element_to_be_clickable((By.ID, 'Granted')))
        pub_type.click()
        
        try:    
            # ---------------------------------------------------
            # 【変更】CAPTCHA入力時にロック（信号機）をかける
            # ---------------------------------------------------
            if input_lock:
                with input_lock:
                    if year is not None:
                        from_date = f"01/01/{year}" # 1月1日
                        to_date = f"12/31/{year}"   # 12月31日
                        # JSを使って直接value属性を書き換える（カレンダーポップアップを回避）
                        driver.execute_script(f"document.getElementById('FromDate').value = '{from_date}';")
                        driver.execute_script(f"document.getElementById('ToDate').value = '{to_date}';")

                        # このブロックに入っている間は、他のブラウザはCAPTCHA入力を待たされます
                        print(f"\n=========================================")
                        print(f"🎯 【{year}年のブラウザ】の順番です！")
                        print("ブラウザ画面を見てCAPTCHAを入力してください。")
                    
                    else:
                        banner_script = f"""
                        var banner = document.createElement('div');
                        banner.id = 'thread-indicator-banner';
                        banner.innerHTML = '🚨 現在の入力対象: 【 検索番号 {target_div} 】 🚨';
                        banner.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; background-color: red; color: white; text-align: center; z-index: 99999; padding: 20px; font-size: 36px; font-weight: bold; border-bottom: 5px solid yellow; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);';
                        document.body.prepend(banner);
                        """
                        driver.execute_script(banner_script)
                        
                    input_captcha = input('コンソールに入力してEnter: ')

                    if type == "applicant":
                        setApplicant(driver, target)
                    elif type == "patent_number":
                        setPatentNum(driver, target)

                    captcha = driver.find_element(By.ID, 'CaptchaText')
                    captcha.send_keys(input_captcha)
                    
                    search_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.NAME, "submit"))
                    )
                    search_button.click()
                    print(f"=========================================\n")
            else:
                # 並列処理を使わない従来の単発実行用のフォールバック
                input_captcha = input('コンソールにCAPTCHAコードを入力してEnterを押してください: ')
                if type == "applicant":
                    setApplicant(driver, target)
                elif type == "patent_number":
                    setPatentNum(driver, target)

                captcha = driver.find_element(By.ID, 'CaptchaText')
                captcha.send_keys(input_captcha)
                
                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "submit"))
                )
                search_button.click()
                print(f"=========================================\n")
        
        except Exception as e:
            print("エラーがsearchInpassSiteで発生しました: " + str(e))
            driver.quit()
    except Exception as e:
        print("エラーがsearchInpassSiteの最初の部分で発生しました: " + str(e))
        driver.quit()

def setApplicant(driver, target):
    wait = WebDriverWait(driver, 10)
    for i in range(0, len(target)):
        select_el = wait.until(EC.presence_of_element_located((By.NAME, f'ItemField{i+1}')))
        select_obj = Select(select_el)
        select_obj.select_by_value('PA')

        select_lg = wait.until(EC.presence_of_element_located((By.NAME, f'LogicField{i+1}')))
        select_lgobj = Select(select_lg)
        select_lgobj.select_by_value('OR')
        
        input_el = driver.find_element(By.NAME, f'TextField{i+1}')
        input_el.send_keys(f'"{target[i]}"')

# 検索対象のpatent numberを入力
def setPatentNum(driver, target, div=None):
    wait = WebDriverWait(driver, 10)
    if div:
        target = target + [div]
    for i in range(0,len(target)):

        # 検索フィールドの指定
        select_el = wait.until(EC.presence_of_element_located((By.NAME, f'ItemField{i+1}')))
        select_obj = Select(select_el)
        select_obj.select_by_value('patent-number')

        # 各行間の論理和積の指定
        select_lg = wait.until(EC.presence_of_element_located((By.NAME, f'LogicField{i+1}')))
        select_lgobj = Select(select_lg)
        select_lgobj.select_by_value('OR')
        
        # テキスト入力 (TextField1, 2, 3...)
        input_el = driver.find_element(By.NAME, f'TextField{i+1}')
        input_el.send_keys(f'{target[i]}') # ここに検索したい値を入れる

def getPatentUrls(driver):
    # INPASSは検索結果が出るまで遅いことがあるため、長めの20秒待機に設定
    wait = WebDriverWait(driver, 20)
    print("accessing results page...")
    
    try:
        # 【修正箇所】いきなり探すのではなく、要素が出現するまで待機する
        element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Total Document(s)')]"))
        )
        element_text = element.text
        
        match = re.search(r'\d+', element_text)
        if match:
            total_count = match.group()
            print(f"取得した件数: {total_count}")
            
    except TimeoutException:
        # 20秒待っても見つからなかった場合のエラー処理
        print("❌ 検索結果の件数が取得できませんでした。")
        print("考えられる原因: ")
        print(" 1. CAPTCHA（画像認証）の入力ミス")
        print(" 2. 検索結果が0件だった")
        print(" 3. サーバーの応答が遅すぎた")
        
        # もし必要であれば、現在開いているページのスクショを撮るなどして原因究明に役立てることも可能です
        # driver.save_screenshot("error_screenshot.png")
        
    time.sleep(5) # ページの安定のために少し待機

def scrape_all_pages(driver, type="patent_number"):
    page_num = 1
    wait = WebDriverWait(driver, 10)
    
    while True:
        print(f"--- {page_num}ページ目を処理中 ---")
        
        # 1. 現在のページの特許詳細をすべて取得する
        click_all_e_registers(driver, type)
        
        try:
            # 2. 「次へ（>>）」ボタンを探す
            # クラス名 'next' と name属性 'page' を持つボタンを指定
            next_button = driver.find_element(By.CSS_SELECTOR, "button.next[name='page']")
            
            # 3. 終了判定: 最後のページに到達したか
            # disabled属性が付与されている場合は、クリックできないので終了する
            if next_button.get_attribute("disabled"):
                print("最後のページに到達しました（Nextボタンが無効です）。")
                break
            
            # 遷移後のページ番号を取得しておく（待機処理に使うため）
            next_page_value = next_button.get_attribute("value")
            
            # 4. 次のページへ遷移
            # JavaScriptを使って確実にクリックさせる（ヘッダー被りなどを防ぐ）
            driver.execute_script("arguments[0].click();", next_button)
            print(f"次のページ（{next_page_value}）へ遷移します...")
            
            # 5. ページのロード完了を待つ（超重要）
            try:
                # 待機時間を「30秒」に延長して、確実に切り替わるのを待つ
                WebDriverWait(driver, 30).until(EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, "span.Selected"), str(next_page_value)
                ))
            except Exception as wait_error:
                # 💡 【追加】親画面が真っ白になった、または激重になった場合の蘇生処理
                print(f"⚠️ 親画面が応答しません（白紙化の可能性）。リロードして蘇生を試みます...")
                try:
                    # 画面を強制リフレッシュ（F5キーと同じ効果）
                    driver.refresh()
                    
                    # リフレッシュ後にページが再読み込みされるのを待つ
                    WebDriverWait(driver, 15).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                    print("蘇生に成功しました。次の処理へ進みます。")

                    time.sleep(3)
                    
                except Exception as e:
                    print(f"❌ リロードしても蘇生できませんでした。ここでスクレイピングを終了します: {e}")
                    break # これ以上進めないので安全にループを抜ける
            
            # サーバーへの負荷軽減とDOM安定のため少しだけ待つ
            time.sleep(10) 
            
        except NoSuchElementException:
            # 万が一ボタン自体が存在しなくなった場合もループを抜ける
            print("「次へ」ボタンが見つからないため終了します。")
            break
        except Exception as e:
            print(f"ページ遷移中にエラーが発生しました: {e}")
            break

def click_all_e_registers(driver, type="patent_number"):
    wait = WebDriverWait(driver, 60)
    buttons = driver.find_elements(By.XPATH, "//table[@id='tableData']//button[@name='eRegister']")
    ap_buttons = driver.find_elements(By.NAME, "ApplicationNumber")  # 出願番号の列を取得
    main_window = driver.current_window_handle

    for i in range(len(buttons)):
        try:
            opened_successfully = False
            raw_value = ap_buttons[i].get_attribute("value")
            application_number = raw_value.strip()
            if type == "applicant":
                if not check_exist_application_number(application_number):
                    print(f"出願番号 {application_number} は取得データに存在しないためスキップします。")
                    continue
                if check_already_scraped_application_number(application_number):
                    print(f"出願番号 {application_number} はすでにスクレイピング済みのためスキップします。")
                    continue

            for retry in range(2):
                current_buttons = driver.find_elements(By.XPATH, "//table[@id='tableData']//button[@name='eRegister']")
                btn = current_buttons[i]

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                
                try:
                    btn.click()
                except:
                    driver.execute_script("arguments[0].click();", btn)
                
                try:
                    WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
                except:
                    print(f"[{i+1}行目] タブが開きません。再クリックします ({retry+1}/3)")
                    continue
                
                new_window = [h for h in driver.window_handles if h != main_window][0]
                driver.switch_to.window(new_window)
                
                try:
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "Content")))
                    opened_successfully = True
                    break
                except:
                    print(f"[{i+1}行目] ページが真っ白（タイムアウト）です。タブを閉じてやり直します。")
                    if len(driver.window_handles) > 1:
                        driver.close()
                    driver.switch_to.window(main_window)
                    time.sleep(2)
            
            if not opened_successfully:
                print(f"❌ [{i+1}行目] 2回試行しましたが取得できませんでした。スキップします。")
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    if len(driver.window_handles) > 1:
                        driver.close()
                driver.switch_to.window(main_window)
                continue
            
            getPatentDetails(driver) 
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(main_window)
            time.sleep(1)

        except Exception as e:
            print(f"{i+1}行目でエラーが発生しました: {e}")
            if len(driver.window_handles) > 1:
                driver.close()
            driver.switch_to.window(main_window)
            continue

def getPatentDetails(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Legal Status')]")))
    print(f"開いたページ: {driver.title}")
    register_number = get_patent_number(driver)
    try:
        if register_number:
            print(f"Register Number: {register_number}")
            full_html = driver.page_source
            insertFullHtml(register_number, full_html)
    except Exception as e:    
        print(f"特許の詳細情報の取得に失敗しました: {e}")
    
def get_patent_number(driver):
    wait = WebDriverWait(driver, 10)
    try:
        xpath_selector = "//td[contains(text(), 'Patent Number')]/following-sibling::td[2]"
        target_element = wait.until(
            EC.visibility_of_element_located((By.XPATH, xpath_selector))
        )
        patent_number = target_element.text.strip()
        print(f"取得したPatent Number: {patent_number}")
        return patent_number
    except Exception as e:
        print(f"Patent Numberの取得に失敗しました: {e}")
        return None