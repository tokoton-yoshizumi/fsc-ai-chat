from flask import Blueprint, request, jsonify, render_template, abort
from utils import load_existing_data
from openai_api import chat_with_openai
import re
import os
from datetime import datetime
import pytz

api = Blueprint("api", __name__)

ALL_PAGES_DATA = None

def initialize_data():
    global ALL_PAGES_DATA
    if ALL_PAGES_DATA is None:
        print("🔄 初回リクエスト：サイトのコンテンツデータを読み込んでいます...")
        ALL_PAGES_DATA = load_existing_data("site_content.json")
        if ALL_PAGES_DATA:
            print(f"✅ 全{len(ALL_PAGES_DATA)}ページのデータをメモリに読み込みました。")
        else:
            print("⚠️ コンテンツデータが見つからないか、空です。")

SYNONYM_MAP = {
    "重さ": "重量", "値段": "価格", "金額": "価格", "費用": "価格",
    "大きさ": "寸法", "サイズ": "寸法", "長さ": "全長", "高さ": "全長",
    "耐荷重": "最大荷重", "出力": "最大荷重", "能力": "最大荷重",
    "穴径": "ホール径", "伸び": "ストローク", "オイル量": "油量",
    "オイル容量": "油量", "タンク容量": "有効油量", "流量": "吐出量", "いつ届く": "発送", "納期": "発送",
}

def search_content(question):
    initialize_data()
    
    all_pages = ALL_PAGES_DATA
    if not all_pages:
        return [], []

    question_cleaned = re.sub(r'[。「」、？！（）『』【】・]', ' ', question)
    
    question_synonymized = question_cleaned
    for key, value in SYNONYM_MAP.items():
        question_synonymized = question_synonymized.replace(key, value)
    
    stop_words = [
        "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "ある", "いる", "も", "する", "から", "な", "へ", "より", "です", "ます", "でした", "ました",
        "こと", "もの", "これ", "それ", "あれ", "どれ", "この", "その", "あの", "どの", "ここ", "そこ", "あそこ", "どこ",
        "ください", "よう", "について", "における", "に関して", "対して", "どのくらい", "何", "なぜ", "いつ", "だれ", "どうして", "教えて", "思います", "どう", "いう",
        "また", "および", "しかし", "そして"
    ]

    temp_question = question_synonymized
    for word in stop_words:
        temp_question = temp_question.replace(word, " ")
    
    keywords = [kw for kw in temp_question.split() if kw]

    if not keywords:
        keywords = [question_synonymized.strip()]
    
    print(f"抽出されたキーワード（最終）: {keywords}")

    scored_pages = []
    for page in all_pages:
        score = 0
        page_title_lower = page['title'].lower()
        page_content_lower = page['content'].lower()
        page_full_text = page_title_lower + " " + page_content_lower

        all_keywords_found = True
        for keyword in keywords:
            if keyword.lower() not in page_full_text:
                all_keywords_found = False
                break
        
        if all_keywords_found:
            score += 1000

        for keyword in keywords:
            kw_lower = keyword.lower()
            if kw_lower in page_title_lower:
                score += 100
            score += page_content_lower.count(kw_lower)
            
        if score > 0:
            scored_pages.append({"score": score, "page": page})

    scored_pages.sort(key=lambda x: x['score'], reverse=True)
    
    return [item['page'] for item in scored_pages[:3]], keywords

@api.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "質問が空です"}), 400

    # ▼▼▼【ここから追加】質問をログファイルに記録する処理 ▼▼▼
    jst = pytz.timezone('Asia/Tokyo')
    timestamp = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
    with open("question_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {question}\n")
    # ▲▲▲【ここまで追加】▲▲▲

    relevant_pages, keywords = search_content(question)

    if relevant_pages:
        context = ""
        for page in relevant_pages:
            context += f"--- ページタイトル: {page['title']} ---\n{page['content']}\n\n"
        
        sources_data = [{"title": page['title'], "url": page['url']} for page in relevant_pages]

        question_for_ai = question
        for key, value in SYNONYM_MAP.items():
            question_for_ai = question_for_ai.replace(key, value)

        prompt1 = (
            "あなたは藤原産業株式会社の製品に関するアシスタントです。\n"
            "以下の『参考情報』だけを使って、ユーザーの『質問』に答えてください。\n"
            "答えが『参考情報』に含まれている場合は、その情報だけを基に、尋ねられている点について簡潔に回答を作成してください。\n"
            "答えが『参考情報』に書かれていない場合は、他の知識を使わずに、ただ「情報なし」とだけ答えてください。\n\n"
            "--- 参考情報 ---\n"
            f"{context}"
            "--- 質問 ---\n"
            f"{question_for_ai}"
        )

        answer1 = chat_with_openai(prompt1)
        
        if "情報なし" not in answer1:
            return jsonify({
                "bot_response": answer1,
                "sources": sources_data
            })

    print("⚠️ HP内に情報が見つからなかったため、GPTの一般知識で回答します。")
    
    caution_message = (
        '<div class="disclaimer-ai">'
        "申し訳ありませんが、ご質問に関する情報は見つかりませんでした。<br>"
        "<b>⚠️ご注意ください⚠️</b><br>"
        "以下の回答は、AIが持つ一般的な知識や公開されている情報に基づいた参考内容です。<br>"
        "そのため、藤原産業の公式な仕様・データではありません。<br>"
        "実際に使用される際は、必ずカタログ、藤原産業の公式資料をご確認ください。"
        '</div>'
    )

    prompt2 = (
        "あなたは、親切で優秀なAIアシスタントです。\n"
        "藤原産業株式会社のウェブサイト内では、以下の質問に関する情報が見つかりませんでした。\n"
        "あなたの一般的な知識を元にして、この質問に回答してください。\n"
        "ただし、回答の一番最初に、以下のHTMLブロック形式の注意書きを改行などを一切挟まずにそのまま含めてください。\n"
        "注意書きのHTMLブロックの直後から、すぐに回答本文を始めてください。"
        f"{caution_message}"
        "--- ユーザーの質問 ---\n"
        f"{question}"
    )
    
    answer2 = chat_with_openai(prompt2)

    return jsonify({
        "bot_response": answer2,
        "sources": []
    })

# ▼▼▼【ここから追加】ログ閲覧ページ用の新しいルート ▼▼▼
@api.route("/view-log/<password>", methods=["GET"])
def view_log(password):
    correct_password = os.environ.get("LOG_DOWNLOAD_PASSWORD")
    if not correct_password or password != correct_password:
        abort(404)

    logs = []
    try:
        with open("question_log.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("] ")
                if len(parts) == 2:
                    timestamp = parts[0].strip("[")
                    question = parts[1]
                    logs.append({"timestamp": timestamp, "question": question})
        logs.reverse()
    except FileNotFoundError:
        print("ログファイルが見つかりません。")

    return render_template("log_viewer.html", logs=logs)
# ▲▲▲【ここまで追加】▲▲▲