from flask import Flask, render_template
from routes import api  # `routes.py` の Blueprint をインポート
from scheduler import start_scheduler  # スケジューラーをインポート

app = Flask(__name__)
app.register_blueprint(api)  # `routes.py` を Blueprint として登録

# ★★★ スケジューラーをここで開始する ★★★
start_scheduler()

@app.route("/")
def index():
    return render_template("index.html")

# if __name__ == "__main__": のブロックは、
# Heroku(gunicorn)では使われないため、削除しても、そのままでもOKです。
# ローカルで python app.py と実行したい場合のために残しておいても良いでしょう。
if __name__ == "__main__":
    app.run(debug=True)