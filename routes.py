from flask import Blueprint, request, jsonify
from utils import load_existing_data
from openai_api import chat_with_openai
import re

api = Blueprint("api", __name__)

print("🔄 サイトのコンテンツデータを読み込んでいます...")
ALL_PAGES_DATA = load_existing_data("site_content.json")
if ALL_PAGES_DATA:
    print(f"✅ 全{len(ALL_PAGES_DATA)}ページのデータをメモリに読み込みました。")
else:
    print("⚠️ コンテンツデータが見つからないか、空です。")

# --- 軽量なキーワード検索機能 ---
def search_content(question):
    all_pages = ALL_PAGES_DATA
    if not all_pages:
        return [], []

    question_cleaned = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', question)

    stop_words = [
        "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ", "ある", "いる", "も", "する", "から", "な", "へ", "より", "です", "ます", "でした", "ました",
        "こと", "もの", "これ", "それ", "あれ", "どれ", "この", "その", "あの", "どの", "ここ", "そこ", "あそこ", "どこ",
        "ください", "よう", "について", "における", "に関して", "対して", "どのくらい", "何", "なぜ", "いつ", "だれ", "どうして", "教えて", "思います", "どう", "いう",
        "また", "および", "しかし", "そして"
    ]

    temp_question = question_cleaned
    for word in stop_words:
        temp_question = temp_question.replace(word, " ")

    keywords = [kw for kw in temp_question.split() if kw]

    if not keywords:
        keywords = [question_cleaned]
    
    print(f"抽出されたキーワード: {keywords}")

    scored_pages = []
    for page in all_pages:
        score = 0
        for keyword in keywords:
            if keyword.lower() in page['title'].lower():
                score += 10
            score += page['content'].lower().count(keyword.lower())

        if score > 0:
            scored_pages.append({"score": score, "page": page})

    scored_pages.sort(key=lambda x: x['score'], reverse=True)
    
    return [item['page'] for item in scored_pages[:3]], keywords

# --- 新しいAPIエンドポイント ---
@api.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "質問が空です"}), 400

    # 1. 関連性の高いページとキーワードを取得
    relevant_pages, keywords = search_content(question)

    # 2. HP内に情報が見つかった場合の処理
    if relevant_pages:
        main_page = relevant_pages[0]
        full_content = main_page['content']
        best_pos = -1
        for keyword in keywords:
            pos = full_content.lower().find(keyword.lower())
            if pos != -1:
                best_pos = pos
                break
        
        snippet = ""
        if best_pos != -1:
            start_index = max(0, best_pos - 750)
            end_index = start_index + 1500
            snippet = full_content[start_index:end_index]
        else:
            snippet = full_content[:1500]

        context = f"--- ページタイトル: {main_page['title']} ---\n{snippet}\n\n"

        sources_data = [{"title": page['title'], "url": page['url']} for page in relevant_pages]

        # AIへの最初のプロンプト（HP情報ベース）
        prompt1 = (
            "あなたは藤原産業株式会社の製品について回答する、親切なアシスタントです。\n"
            "以下の参考情報だけを元にして、ユーザーからの質問に日本語で分かりやすく回答してください。\n"
            "参考情報から答えが推測できる場合は、その内容をまとめて回答を作成してください。\n"
            "もし参考情報にまったく関連する記述がない場合にのみ、「情報なし」という単語だけを返してください。\n\n"
            "--- 参考情報 ---\n"
            f"{context}"
            "--- ユーザーの質問 ---\n"
            f"{question}"
        )

        answer1 = chat_with_openai(prompt1)

        # AIがHP情報から回答を生成できた場合
        if "情報なし" not in answer1:
            return jsonify({
                "bot_response": answer1,
                "sources": sources_data
            })

    # 3. HP内に情報がなかった場合、またはAIが回答を生成できなかった場合のフォールバック処理
    print("⚠️ HP内に情報が見つからなかったため、GPTの一般知識で回答します。")
    
    # AIへの2番目のプロンプト（一般知識ベース）
    prompt2 = (
        "あなたは、親切で優秀なAIアシスタントです。\n"
        "藤原産業株式会社のウェブサイト内では、以下の質問に関する情報が見つかりませんでした。\n"
        "あなたの一般的な知識を元にして、この質問に回答してください。\n"
        "ただし、回答の一番最初に、以下の注意書きを必ず改行を挟んで含めてください。\n\n"
        "**※ご注意：** この回答はAIの一般的な知識に基づくもので、藤原産業の公式情報ではありません。参考としてご活用ください。\n\n"
        "--- ユーザーの質問 ---\n"
        f"{question}"
    )
    
    answer2 = chat_with_openai(prompt2)

    return jsonify({
        "bot_response": answer2,
        "sources": []  # 一般知識からの回答なのでソースはなし
    })