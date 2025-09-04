# scheduler.py (新しい完成版コード)

import requests
import json
import re
from bs4 import BeautifulSoup
import schedule
import time
from threading import Thread

# --- create_database.py から持ってきたロジック ---

PAGES_API_URL = "https://fujiwarasangyo.jp/wp-json/wp/v2/pages?per_page=100"
POSTS_API_URL = "https://fujiwarasangyo.jp/wp-json/wp/v2/posts?per_page=100"


EXCLUDE_URLS = [
    "https://fujiwarasangyo.jp/", # トップページ
    "https://fujiwarasangyo.jp/form-contact/",
    "https://fujiwarasangyo.jp/order/",
    "https://fujiwarasangyo.jp/rockbolt-form/",
    "https://fujiwarasangyo.jp/form-rental/",
    "https://fujiwarasangyo.jp/calibratio-repair/",
    "https://fujiwarasangyo.jp/number-view/"
    "https://fujiwarasangyo.jp/%e3%83%88%e3%83%83%e3%83%97%e3%83%9a%e3%83%bc%e3%82%b8/"
    
    # 他にも除外したいページがあればここに追加
]
def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()
    text = re.sub(r'\s{2,}', '\n', text).strip()
    return text

def fetch_all_content(api_url):
    all_items = []
    page = 1
    while True:
        try:
            response = requests.get(f"{api_url}&page={page}", timeout=20)
            response.raise_for_status()
            items = response.json()
            if not items:
                break
            all_items.extend(items)
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ APIからのデータ取得に失敗しました: {e}")
            break
    return all_items

def update_database():
    """サイトの全コンテンツを取得してJSONファイルを更新する"""
    print("🔄 [スケジューラー] データベースの定期更新を開始します...")
    
    pages = fetch_all_content(PAGES_API_URL)
    posts = fetch_all_content(POSTS_API_URL)
    all_content = pages + posts
    
    site_data = []
    for item in all_content:
        url = item.get('link', '')
        if url in EXCLUDE_URLS:
            print(f"🚫 スキップ (除外リスト): {item.get('title', {}).get('rendered', '')}")
            continue
        if 'content' in item and 'rendered' in item['content'] and item['content']['rendered']:
            title = item.get('title', {}).get('rendered', 'No Title')
            html_content = item['content']['rendered']
            cleaned_content = clean_html(html_content)
            site_data.append({"title": title, "url": url, "content": cleaned_content})

    with open("site_content.json", "w", encoding="utf-8") as f:
        json.dump(site_data, f, ensure_ascii=False, indent=2)

    print(f"✅ [スケジューラー] 全{len(site_data)}ページのデータで `site_content.json` を更新しました。")

# --- ここまでが create_database.py のロジック ---


# **スケジューラーの設定**
# 毎週月曜日の早朝3時にデータベースを更新するように設定
schedule.every().monday.at("03:00").do(update_database)


def start_scheduler():
    """バックグラウンドでスケジュールを実行"""
    # ★ サーバー起動時に一度だけ即時実行する
    # print("🚀 [初回実行] データベースを最新の状態に更新します...")
    # update_database()
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1) # 1秒ごとに次のスケジュールを確認

    Thread(target=run_scheduler, daemon=True).start()