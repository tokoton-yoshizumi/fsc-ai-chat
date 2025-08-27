from flask import Blueprint, request, jsonify
from utils import load_existing_data # 既存の関数を流用
from openai_api import chat_with_openai

api = Blueprint("api", __name__)

print("🔄 サイトのコンテンツデータを読み込んでいます...")
ALL_PAGES_DATA = load_existing_data("site_content.json")
if ALL_PAGES_DATA:
    print(f"✅ 全{len(ALL_PAGES_DATA)}ページのデータをメモリに読み込みました。")
else:
    print("⚠️ コンテンツデータが見つからないか、空です。")

# --- 簡易的なキーワード検索機能 ---
# --- 軽量なキーワード検索機能 ---
def search_content(question):
    all_pages = ALL_PAGES_DATA
    if not all_pages:
        return []

    # Janomeの代わりに、不要な単語（ストップワード）を削除する方式に変更
    stop_words = [
        "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ", "ある", "いる", "も", 
        "する", "から", "な", "こと", "もの", "へ", "より", "です", "ます", "でした", "ました",
        "ください", "よう", "について", "における", "に関して", "対して", "どの", "どのくらい",
        "何", "なぜ", "いつ", "どこ", "だれ", "どうして", "教えて"
    ]
    
    # 質問文からストップワードを空文字に置換して削除
    temp_question = question
    for word in stop_words:
        temp_question = temp_question.replace(word, " ")

    # 連続する空白を一つにまとめ、キーワードリストを作成
    keywords = [kw for kw in temp_question.split() if kw]

    # もしキーワードが抽出できなかった場合は、元の質問をそのまま使う
    if not keywords:
        keywords = [question]
    
    print(f"抽出されたキーワード: {keywords}")

    scored_pages = []
    for page in all_pages:
        score = 0
        for keyword in keywords:
            # タイトルに含まれていたら高スコア
            if keyword.lower() in page['title'].lower():
                score += 10
            # 本文に含まれる回数をスコアに加算
            score += page['content'].lower().count(keyword.lower())

        if score > 0:
            scored_pages.append({"score": score, "page": page})

    scored_pages.sort(key=lambda x: x['score'], reverse=True)
    
    return [item['page'] for item in scored_pages[:3]]
# --- 新しいAPIエンドポイント ---
@api.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "質問が空です"}), 400

    # 1. 最も関連性の高いページを1つだけ取得
    relevant_pages = search_content(question)

    if not relevant_pages:
        return jsonify({"bot_response": "申し訳ありません、関連する情報が見つかりませんでした。"})
    
    # ★★★ AIに渡すのは「最初の1ページだけ」に絞る ★★★
    main_page = relevant_pages[0]

    # 2. AIに渡す参考ページは、最も関連性の高い最初の1ページに限定
    main_page = relevant_pages[0]

    # 3. AIに渡すコンテキストを「main_page」からのみ作成
    context = ""
    stop_words = [
        "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ", "ある", "いる", "も", 
        "する", "から", "な", "こと", "もの", "へ", "より", "です", "ます", "でした", "ました",
        "ください", "よう", "について", "における", "に関して", "対して", "どの", "どのくらい",
        "何", "なぜ", "いつ", "どこ", "だれ", "どうして", "教えて"
    ]
    temp_question = question
    for word in stop_words:
        temp_question = temp_question.replace(word, " ")
    keywords = [kw for kw in temp_question.split() if kw]
    if not keywords:
        keywords = question.split()

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

    context += f"--- ページタイトル: {main_page['title']} ---\n"
    context += f"{snippet}\n\n"

    # 4. ユーザーに見せるソース情報は、見つかった全ページ（最大3件）から作成
    sources_data = []
    for page in relevant_pages:
        sources_data.append({
            "title": page['title'],
            "url": page['url']
        })

    # 5. AIへのプロンプトを作成
    prompt = (
        "あなたは藤原産業株式会社の製品について回答する、親切なアシスタントです。\n"
        "以下の参考情報だけを元にして、ユーザーからの質問に日本語で分かりやすく回答してください。\n"
        "参考情報から答えが推測できる場合は、その内容をまとめて回答を作成してください。\n"
        "もし参考情報にまったく関連する記述が一切ない場合にのみ、「申し訳ありませんが、ご質問に関する情報は見つかりませんでした。」と回答してください。\n\n"
        "--- 参考情報 ---\n"
        f"{context}"
        "--- ユーザーの質問 ---\n"
        f"{question}"
    )

    # 6. AIに質問して回答を取得
    answer = chat_with_openai(prompt)

    return jsonify({
        "bot_response": answer,
        "sources": sources_data
    })
