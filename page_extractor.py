import requests
from bs4 import BeautifulSoup

def clean_text(text):
    # 各行の前後の空白を削除し、空行を取り除く
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    cleaned_text = "\n".join(cleaned_lines)
    return cleaned_text

def get_page_content(url, output_file="page_content.txt"):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ページ内のテキストを取得
        text = soup.get_text()

        # テキストを整形して不要な空白や改行を削除
        cleaned_text = clean_text(text)

        # テキストファイルに保存
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(cleaned_text)

        return cleaned_text
    except Exception as e:
        return f"Error: {str(e)}"

# 直接実行された場合の動作
if __name__ == "__main__":
    url = input("ページのURLを入力してください: ")
    output_file = "page_content.txt"  # 出力ファイル名
    page_content = get_page_content(url, output_file)
    print(f"ページ内容が {output_file} に保存されました。")
