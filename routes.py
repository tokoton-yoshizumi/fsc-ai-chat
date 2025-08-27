from flask import Blueprint, request, jsonify
from utils import load_existing_data # 既存の関数を流用
from openai_api import chat_with_openai
from janome.tokenizer import Tokenizer

api = Blueprint("api", __name__)

print("🔄 サイトのコンテンツデータを読み込んでいます...")
ALL_PAGES_DATA = load_existing_data("site_content.json")
if ALL_PAGES_DATA:
    print(f"✅ 全{len(ALL_PAGES_DATA)}ページのデータをメモリに読み込みました。")
else:
    print("⚠️ コンテンツデータが見つからないか、空です。")

# --- 簡易的なキーワード検索機能 ---
def search_content(question):
    all_pages = ALL_PAGES_DATA
    if not all_pages:
        return []

    t = Tokenizer()
    keywords = []
    for token in t.tokenize(question):
        part_of_speech = token.part_of_speech.split(',')[0]
        if part_of_speech == '名詞':
            keywords.append(token.surface)
    
    if not keywords:
        keywords = [question]
    
    print(f"抽出されたキーワード: {keywords}")

    scored_pages = []
    for page in all_pages:
        score = 0
        # ★★★ 新しいスコアリングロジック ★★★
        for keyword in keywords:
            # 1. タイトルに含まれていたら、非常に高い点数を加算
            if keyword.lower() in page['title'].lower():
                score += 10
            
            # 2. 本文に含まれている回数も点数として加算
            score += page['content'].lower().count(keyword.lower())

        if score > 0:
            scored_pages.append({"score": score, "page": page})

    scored_pages.sort(key=lambda x: x['score'], reverse=True)
    
    # ★★★ ユーザーに見せるために、上位3件のページを返すように変更 ★★★
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
    t = Tokenizer()
    keywords = [token.surface for token in t.tokenize(question) if token.part_of_speech.split(',')[0] == '名詞']
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
        "もし参考情報にまったく関連する記述がない場合にのみ、「申し訳ありませんが、ご質問に関する情報は見つかりませんでした。」と回答してください。\n\n"
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
