from flask import Blueprint, request, jsonify
from utils import load_existing_data
from openai_api import chat_with_openai
import re
from sudachipy import tokenizer
from sudachipy import dictionary

api = Blueprint("api", __name__)

ALL_PAGES_DATA = None
tokenizer_obj = None

def initialize_data():
    global ALL_PAGES_DATA, tokenizer_obj
    if ALL_PAGES_DATA is None:
        print("🔄 初回リクエスト：サイトのコンテンツデータを読み込んでいます...")
        ALL_PAGES_DATA = load_existing_data("site_content.json")
        if ALL_PAGES_DATA:
            print(f"✅ 全{len(ALL_PAGES_DATA)}ページのデータをメモリに読み込みました。")
        else:
            print("⚠️ コンテンツデータが見つからないか、空です。")
    
    if tokenizer_obj is None:
        print("🔄 初回リクエスト：SudachiPy Tokenizerを初期化しています...")
        tokenizer_obj = dictionary.Dictionary().create()
        print("✅ Tokenizerの初期化が完了しました。")

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
    
    mode = tokenizer.Tokenizer.SplitMode.C
    tokens = tokenizer_obj.tokenize(question_synonymized, mode)
    keywords = [m.normalized_form() for m in tokens if m.part_of_speech()[0] == '名詞']
    
    if not keywords:
        keywords = [question_cleaned]
    
    print(f"抽出されたキーワード（最終）: {keywords}")

    scored_pages = []
    for page in all_pages:
        score = 0
        page_title_lower = page['title'].lower()
        page_content_lower = page['content'].lower()

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
    initialize_data()

    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "質問が空です"}), 400

    relevant_pages, keywords = search_content(question)

    if relevant_pages:
        main_page = relevant_pages[0]
        full_content = main_page['content']
        best_snippet = ""
        max_keyword_count = 0
        
        for i in range(0, len(full_content), 300):
            snippet_candidate = full_content[i:i+1500]
            keyword_count = sum(snippet_candidate.lower().count(kw.lower()) for kw in keywords)
            
            if keyword_count > max_keyword_count:
                max_keyword_count = keyword_count
                best_snippet = snippet_candidate

        if not best_snippet:
            best_snippet = full_content[:1500]

        context = f"--- ページタイトル: {main_page['title']} ---\n{best_snippet}\n\n"
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

    # ▼▼▼【ここを修正】 "--- 注意書き ---" の行を削除 ▼▼▼
    prompt2 = (
        "あなたは、親切で優秀なAIアシスタントです。\n"
        "藤原産業株式会社のウェブサイト内では、以下の質問に関する情報が見つかりませんでした。\n"
        "あなたの一般的な知識を元にして、この質問に回答してください。\n"
        "ただし、回答の一番最初に、以下のHTMLブロック形式の注意書きを改行などを一切挟まずにそのまま含めてください。\n"
        "注意書きのHTMLブロックの直後から、すぐに回答本文を始めてください。\n\n"
        f"{caution_message}\n\n"
        "--- ユーザーの質問 ---\n"
        f"{question}"
    )
    # ▲▲▲【ここまで修正】▲▲▲
    
    answer2 = chat_with_openai(prompt2)

    return jsonify({
        "bot_response": answer2,
        "sources": []
    })