#!/usr/bin/env python
# coding: utf-8

# -*- coding: utf-8 -*-
import os
import re
import csv
import sys
import sqlite3
from time import sleep
from bs4 import BeautifulSoup
import unicodedata

DB_NAME = "inpass.db"

# 💡 【追加】テキストを綺麗にする専用の便利関数
def clean_text(text):
    if not text:
        return ""
        
    # 1. \xa0 などの特殊な空白や全角英数を、すべて通常の半角文字に正規化する
    text = unicodedata.normalize('NFKC', text)
    
    # 2. 改行コード (\n や \r) を単なるスペースに置き換える
    text = text.replace('\n', ' ').replace('\r', '')
    
    # 3. 連続する複数のスペースを、1つのスペースにギュッとまとめる（お好みで）
    text = re.sub(r'\s+', ' ', text)
    
    # 前後の空白を削って返す
    return text.strip()

def insert_all_results(results):

    # 2. データベース接続
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 3. SQL文の準備 (14個のカラムに対応する14個の「?」)
    sql = '''
    INSERT INTO result_data (
        application_number, 
        patent_number, 
        serial_no, 
        patentee_name, 
        patentee_address, 
        legal_event, 
        date_of_event, 
        remark1, 
        remark2, 
        remark3, 
        remark4, 
        renewal_year, 
        renewal_from, 
        renewal_to
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    try:
        # 4. executemany で一括インサート
        # これが SQLite において最も高速な登録方法です
        cursor.executemany(sql, results)
        
        # 5. コミットして確定
        conn.commit()
        print(f"✅ 正常に {len(results)} 件のデータを一括登録しました。")
        
    except Exception as e:
        # エラーが起きた場合はロールバック（登録を白紙に戻す）
        conn.rollback()
        print(f"❌ 登録中にエラーが発生しました: {e}")
        
    finally:
        # 接続を閉じる
        conn.close()

def get_full_html():
    SELECT_QUERY = "SELECT * FROM full_html order by register_number"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(SELECT_QUERY)
        return list(map(lambda m: m, cursor.fetchall()))
    except Exception as e:
        print(e)
        return []
    finally:
        conn.close()

def get_detail_data_bs4(register_number, html_content):
    patentee_data = []
    remark_data = []
    renewal_data = []
    application_number = ""
    legal_status_info = ("", "")
    
    try:
        # 1. HTMLをBeautifulSoupで解析
        soup = BeautifulSoup(html_content, 'lxml') # 'html.parser' でも可
        
        # 'Content' IDを持つ大枠を取得
        content_area = soup.find(id="Content")
        if not content_area:
            print(f"[{application_number}] Contentエリアが見つかりません。")
            return []

        # Content内のすべてのテーブルを取得
        tables = content_area.find_all('table')
        
        # 💡【新規追加】出願番号(Application Number)の取得
        app_num_td = soup.find('td', string=re.compile(r'Application Number', re.IGNORECASE))
        if app_num_td:
            app_val_td = app_num_td.find_next_sibling('td').find_next_sibling('td')
            if app_val_td:
                application_number = app_val_td.get_text(strip=True)

        # -----------------------------------------------------
        # Patentee Data: 元の table[4]
        # -----------------------------------------------------
        if len(tables) > 3:
            patentee_trs = tables[3].find_all('tr')
            for i, tr in enumerate(patentee_trs):
                if i == 0:
                    ths = tr.find_all('th')
                    if len(ths) > 1 and ths[1].get_text(strip=True) != 'Name of Patentee':
                        break
                    else:
                        continue

                tds = tr.find_all('td')
                if len(tds) >= 4:
                    patentee_sl = tds[0].get_text(strip=True)
                    patentee_name = tds[1].get_text(strip=True)
                    patentee_address = tds[3].get_text(strip=True)
                    patentee_data.append((patentee_sl, patentee_name, patentee_address))

        # -----------------------------------------------------
        # Remark Data: 元の table[7]
        # -----------------------------------------------------
        if len(tables) > 6:
            remark_trs = tables[6].find_all('tr')
            for i, tr in enumerate(remark_trs):
                if i == 0:
                    ths = tr.find_all('th')
                    if len(ths) > 0 and ths[0].get_text(strip=True) != 'Sl No':
                        break
                    else:
                        continue

                tds = tr.find_all('td')
                if len(tds) >= 3:
                    serial = tds[0].get_text(strip=True)
                    date_of_entry = tds[1].get_text(strip=True)
                    remarks = tds[2].get_text(strip=True)
                    remark_data.append(remarks)

        while len(remark_data) < 4:
            remark_data.append("")
        remark_data = remark_data[:4]

        # -----------------------------------------------------
        # Renewal Data: 元の id="renual"
        # -----------------------------------------------------
        renual_table = soup.find(id="renual")
        if renual_table:
            renewal_trs = renual_table.find_all('tr')
            temp_renewal = []
            for i, tr in enumerate(renewal_trs):
                tds = tr.find_all('td')
                if not tds: # ヘッダー行(th)をスキップ
                    continue
                
                if i < 2:
                    continue
                if i == 2:
                    temp_renewal = [td.get_text(strip=True) for td in tds]
                else:
                    if len(tds) > 1 and tds[1].get_text(strip=True) != "--":
                        temp_renewal = [td.get_text(strip=True) for td in tds]
            
            if temp_renewal:
                renewal_data = temp_renewal

        # -----------------------------------------------------
        # Legal Status: 元の table[1]/tr[2]/td[1] & td[2]
        # -----------------------------------------------------
        legal_status = ""
        status_date = ""
        if len(tables) > 0:
            legal_status_trs = tables[0].find_all('tr')
            if len(legal_status_trs) > 1:
                legal_tds = legal_status_trs[1].find_all('td')
                if len(legal_tds) > 0:
                    legal_status = legal_tds[0].get_text(strip=True)
                if len(legal_tds) > 1 and legal_status != "":
                    status_date = legal_tds[1].get_text(strip=True)
                    
        legal_status_info = (legal_status, status_date)

        return {"application_number": application_number, 
                "register_number": register_number,
                "patentee_data": patentee_data,
                "remark_data": remark_data,
                "renewal_data": renewal_data,
                "legal_status_info": legal_status_info}

    except Exception as e:
        print(f"エラー発生 ({register_number}): {e}")
        return []
    
if __name__ == '__main__':
    full_html_list = get_full_html()

    all_results = []

    for html in full_html_list:
        result = get_detail_data_bs4(html[0], html[1])
        
        application_number = result["application_number"]
        register_number = result["register_number"]
        patentee_data = result["patentee_data"]

        renewal_data = result["renewal_data"]
        # 💡【修正】年金データが無い、または要素が足りない場合にエラーで落ちるのを防ぐ
        if renewal_data and len(renewal_data) >= 3:
            date_info = [renewal_data[0], renewal_data[-2], renewal_data[-1]]
        else:
            date_info = ["", "", ""] # 年金データが取れなかった場合は空文字で3枠埋める

        legal_status_info = result["legal_status_info"]
        remark_data = result["remark_data"]
        date_info = [renewal_data[0], renewal_data[-2], renewal_data[-1]]

        for i in range(len(patentee_data)):
            record = [application_number, register_number, *patentee_data[i], *legal_status_info, *remark_data, *date_info]
            cleaned_record = list(map(clean_text, record))
            all_results.append(cleaned_record)
    
    insert_all_results(all_results)