import requests
import json
import re
from bs4 import BeautifulSoup

# WordPressサイトのAPIエンドポイント
# NOTE: per_page=100 とすることで、一度に100件のデータを取得し、リクエスト回数を減らします。
# ページ数が100を超える場合は、ループ処理で全ページを取得する必要があります。
PAGES_API_URL = "https://fujiwarasangyo.jp/wp-json/wp/v2/pages?per_page=100"
POSTS_API_URL = "https://fujiwarasangyo.jp/wp-json/wp/v2/posts?per_page=100"

EXCLUDE_URLS = [
    "https://fujiwarasangyo.jp/", # トップページ
    "https://fujiwarasangyo.jp/form-contact/",
    "https://fujiwarasangyo.jp/order/",
    "https://fujiwarasangyo.jp/rockbolt-form/",
    "https://fujiwarasangyo.jp/form-rental/",
    "https://fujiwarasangyo.jp/calibratio-repair/",
    


    # 他にも除外したいページがあればここに追加
]

def clean_html(html_content):
    """HTMLタグを除去し、テキストをクリーンにする"""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text()
    # 連続する改行や空白を整理
    text = re.sub(r'\s{2,}', '\n', text).strip()
    return text

def fetch_all_content(api_url):
    """指定されたAPIからコンテンツを取得する"""
    all_items = []
    page = 1
    while True:
        try:
            response = requests.get(f"{api_url}&page={page}", timeout=20)
            response.raise_for_status()
            items = response.json()
            if not items:
                break # データがなくなったらループを抜ける
            all_items.extend(items)
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ APIからのデータ取得に失敗しました: {e}")
            break
    return all_items

def create_content_database():
    """サイトの全コンテンツを取得してJSONファイルに保存する"""
    print("🔄 サイトコンテンツの取得を開始します...")

    pages = fetch_all_content(PAGES_API_URL)
    posts = fetch_all_content(POSTS_API_URL)
    
    all_content = pages + posts
    
    site_data = []

    for item in all_content:
        url = item.get('link', '')
        
        # ★★★ 除外リストに含まれるURLはスキップする処理を追加 ★★★
        if url in EXCLUDE_URLS:
            print(f"🚫 スキップ (除外リスト): {item.get('title', {}).get('rendered', '')}")
            continue

        if 'content' in item and 'rendered' in item['content'] and item['content']['rendered']:
            title = item.get('title', {}).get('rendered', 'No Title')
            html_content = item['content']['rendered']
            cleaned_content = clean_html(html_content)

            site_data.append({
                "title": title,
                "url": url,
                "content": cleaned_content
            })
            print(f"✅ 取得完了: {title}")

    # JSONファイルに保存
    with open("site_content.json", "w", encoding="utf-8") as f:
        json.dump(site_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 全{len(site_data)}ページのデータを `site_content.json` に保存しました。")

if __name__ == "__main__":
    create_content_database()
