import requests
import json
import xml.etree.ElementTree as ET
import schedule
import time
from threading import Thread
from utils import load_existing_data, get_page_title

PAGE_SITEMAP_URL = "https://fujiwarasangyo.jp/page-sitemap.xml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_page_urls(sitemap_url):
    """Sitemap から固定ページの URL を取得"""
    try:
        response = requests.get(sitemap_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
        return urls
    except requests.exceptions.RequestException as e:
        print(f"❌ Sitemap の取得に失敗しました: {e}")
        return []

def update_sitemap():
    """週に1回 sitemap を取得して JSON を更新"""
    print("🔄 Sitemap から最新のデータを取得中...")
    
    fixed_page_urls = get_page_urls(PAGE_SITEMAP_URL)
    existing_page_data = load_existing_data("fixed_page_titles.json")
    existing_urls = {entry["url"] for entry in existing_page_data}

    new_page_data = []
    total_pages = len(fixed_page_urls)
    print(f"📌 取得対象の固定ページ数: {total_pages}")

    for index, url in enumerate(fixed_page_urls, start=1):
        if url in existing_urls:
            print(f"[{index}/{total_pages}] {url} は取得済み ✅ スキップ")
            continue

        print(f"[{index}/{total_pages}] {url} を処理中...", end=" ")
        title = get_page_title(url)
        if title:
            new_page_data.append({"url": url, "title": title})
            print("✅ 取得成功")
        else:
            print("❌ 取得失敗")

    # 既存データに新しいデータを追加
    updated_page_data = existing_page_data + new_page_data

    # JSON に保存
    with open("fixed_page_titles.json", "w", encoding="utf-8") as f:
        json.dump(updated_page_data, f, ensure_ascii=False, indent=4)

    print("✅ 最新のデータに更新しました！")

# **スケジューラーの設定**
schedule.every().week.do(update_sitemap)

def start_scheduler():
    """バックグラウンドでスケジュールを実行"""
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    Thread(target=run_scheduler, daemon=True).start()
