import sqlite3
DB_NAME = "inpass.db"

#処理対象のapplicantを取得
def getTargetApplicant():
    SELECT_QUERY = "SELECT * FROM source_applicants where is_checked = 0 order by count desc limit 1"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(SELECT_QUERY)
        return list(map(lambda m: m[0], cursor.fetchall()))
    except Exception as e:
        print(e)
        return []
    finally:
        conn.close()

def getTargetPatentNum(target_div=None):
    SELECT_QUERY = f"SELECT * FROM origin_source where status = 0 order by register_number limit 14"
    if target_div is not None:
        SELECT_QUERY = f"SELECT register_number FROM origin_source where status = 0 and register_number % 10 = {target_div} order by register_number limit 14"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(SELECT_QUERY)
        return list(map(lambda m: m[0], cursor.fetchall()))
    except Exception as e:
        print(e)
        return []
    finally:
        conn.close()
    

def insertFullHtml(patent_number, full_html):

    INSERT_QUERY = "INSERT INTO full_html (register_number, full_html) VALUES (?, ?)"
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if not check_exist_patent_number(patent_number, cursor):
            print(f"特許番号 {patent_number} は取得データに存在しません。")
            return

        if check_exist_full_html(patent_number, cursor):
            print(f"特許番号 {patent_number} はすでに存在しています。スキップします。")
            return

        cursor.execute(INSERT_QUERY, (patent_number, full_html))
        updateStatus(patent_number, 1, cursor, conn)  # ステータスを1に更新
        print(f"特許番号 {patent_number} のfull_htmlを保存しました。")
    except Exception as e:
        print(f"特許番号 {patent_number} のfull_htmlの保存に失敗しました: {e}")
        updateStatus(patent_number, -1, cursor, conn)  # ステータスを-1に更新
        print(e)
    finally:
        if conn:
            conn.close()

def check_exist_patent_number(patent_number, cursor):
    SELECT_QUERY = "SELECT COUNT(*) FROM origin_source WHERE register_number = ?"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(SELECT_QUERY, (patent_number,))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        return False
    finally:
        if conn:
            conn.close()

def check_exist_full_html(patent_number, cursor):
    SELECT_QUERY = "SELECT COUNT(*) FROM full_html WHERE register_number = ?"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(SELECT_QUERY, (patent_number,))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        return False
    finally:
        if conn:
            conn.close()    

def updateStatus(patent_number, status, cursor, conn):
    UPDATE_QUERY = "UPDATE origin_source SET status = ? WHERE register_number = ?"
    try:
        cursor.execute(UPDATE_QUERY, (status, patent_number))
        conn.commit()
    except Exception as e:
        print(f"特許番号 {patent_number} のステータスの更新に失敗しました: {e}")

def check_exist_application_number(application_number):
    SELECT_QUERY = "SELECT COUNT(*) FROM origin_source WHERE application_number = ?"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(SELECT_QUERY, (application_number,))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        return False
    finally:
        if conn:
            conn.close()

def check_already_scraped_application_number(application_number):
    SELECT_QUERY = "SELECT COUNT(*) FROM origin_source WHERE application_number = ? AND status = 1"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(SELECT_QUERY, (application_number,))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        return False
    finally:
        if conn:
            conn.close()
