from flask import Flask, render_template
from routes import api  # `routes.py` の Blueprint をインポート
from scheduler import start_scheduler  # スケジューラーをインポート

app = Flask(__name__)
app.register_blueprint(api)  # `routes.py` を Blueprint として登録

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    start_scheduler()  # 定期処理を開始
    app.run(debug=True, threaded=True)  # `threaded=True` で並列実行
