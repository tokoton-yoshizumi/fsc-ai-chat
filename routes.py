from flask import Blueprint, request, jsonify
from utils import fetch_page_headings, fetch_section_content, load_existing_data
from openai_api import chat_with_openai  # 追加


api = Blueprint("api", __name__)  # `api` という Blueprint を作成

# **製品情報を取得**
@api.route("/get_product_info", methods=["POST"])
def get_product_info():
    data = request.get_json()
    product_name = data.get("product_name")

    if not product_name:
        return jsonify({"bot_response": "製品名が指定されていません。"})

    # `fixed_page_titles.json` から該当する製品ページのURLを探す
    page_data = load_existing_data("fixed_page_titles.json")
    matched_pages = [entry for entry in page_data if entry["title"] == product_name]

    if not matched_pages:
        return jsonify({"bot_response": "該当する製品ページが見つかりませんでした。"})

    selected_page = matched_pages[0]
    page_url = selected_page["url"]

    # ページの `h2`, `h3` 見出しを取得
    headings = fetch_page_headings(page_url)

    return jsonify({
        "bot_response": f"「{product_name}」についてですね！<br>ご質問はなんですか？",
        "choices": headings,
        "source_url": page_url
    })

# **見出しに対する詳細情報を取得**
@api.route("/get_answer", methods=["POST"])
def get_answer():
    data = request.json
    url = data.get("url")
    TRUSTED_DOMAIN = "https://fujiwarasangyo.jp/"
    heading = data.get("heading")
    question = data.get("question")

    if not url or not heading or not question:
        return jsonify({"error": "無効なリクエスト"}), 400
    
    if not url or not url.startswith(TRUSTED_DOMAIN):
        return jsonify({"error": "無効なURLです"}), 400

    # 指定された見出し以下のコンテンツを取得
    section_content = fetch_section_content(url, heading)
    print("🔹 取得したコンテンツ:", section_content)

    # プロンプトに「不足時」の条件を明示する
    prompt = (
        f"以下は製品の情報の一部です:\n{section_content}\n\n"
        f"ユーザーの質問: {question}\n\n"
        "上記の情報を踏まえて、適切な回答を生成してください。"
        "もし、質問に必要な情報が上記に含まれていない場合は、"
        "『申し訳ありません、私ではお答えできない質問のため、以下よりお問い合わせください。』と回答してください。"
    )

    answer = chat_with_openai(prompt)
    print("🔹 ChatGPT からの回答:", answer)

    # fallback_message が回答に含まれている場合はお問い合わせを促す
    fallback_message = "申し訳ありません、私ではお答えできない質問のため、以下よりお問い合わせください。"
    if fallback_message in answer:
        return jsonify({"bot_response": fallback_message, "show_contact": True})
    else:
        return jsonify({"bot_response": answer})

# **ユーザーの質問に対して応答を生成**
@api.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("user_input")

    print("🔹 ユーザーからの質問:", user_input)  # デバッグ用

    if not user_input:
        return jsonify({"error": "質問が空です"}), 400

    # ここで適切なレスポンスを生成する（仮の応答）
    response_text = f"あなたの質問: {user_input} に関する情報です。"

    return jsonify({"bot_response": response_text})