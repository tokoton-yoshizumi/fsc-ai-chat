import os
import json
import requests
from bs4 import BeautifulSoup
import re


# ユーザーエージェント設定
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def load_existing_data(filename):
    """既存のタイトルデータをロード"""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def fetch_page_headings(url):
    """指定したページの h2 見出しを取得する"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        headings = [h.get_text().strip() for h in soup.find_all("h2")]

        return headings if headings else []
    except requests.exceptions.RequestException as e:
        print(f"❌ 見出し取得失敗 ({url}): {e}")
        return []


def fetch_section_content(url, heading):
    """指定した `h2` の下にあるコンテンツを取得し、ファイルに保存"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        headings = soup.find_all("h2")  # h2 のみを取得

        safe_heading = re.sub(r'[^a-zA-Z0-9_]', '', heading.replace(' ', '_'))
        filename = f"output_{safe_heading}.txt"

        if not safe_heading:
            filename = "output_default.txt" # もしファイル名が空になった場合の対策

        print(f"🔍 {url} の h2 見出しリスト:")
        for h in headings:
            print(f" - {h.get_text().strip()}")

        for h in headings:
            h_text = h.get_text().strip()
            
            # **大文字小文字を無視し、完全一致を確認**
            if heading.lower().strip() == h_text.lower():
                print(f"✅ 一致した見出し: {h_text}")

                content = []
                next_elements = h.find_all_next()  # h2 以降のすべての要素を取得

                for elem in next_elements:
                    if elem.name == "h2":  # 次の h2 で終了
                        break
                    if elem.name in ["p", "ul", "li", "table"]:
                        content.append(elem.get_text().strip())

                result = "\n".join(content) if content else "該当する情報が見つかりませんでした。"
                print(f"🔹 取得したコンテンツ: {result[:100]}...")  # 100文字だけ表示

                # **ファイルに出力**
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"【{heading}】\n{result}")

                print(f"✅ 出力完了: {filename}")  # 出力したファイル名を表示

                return result

        print("❌ 一致する見出しが見つかりませんでした。")
        return "該当する情報が見つかりませんでした。"
    except requests.exceptions.RequestException as e:
        print(f"❌ セクション取得失敗 ({url}): {e}")
        return "エラーが発生しました"

def get_page_title(url):
    """指定した URL のタイトルを取得"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "No Title"

        return title
    except requests.exceptions.RequestException as e:
        print(f"❌ タイトル取得失敗 ({url}): {e}")
        return None
