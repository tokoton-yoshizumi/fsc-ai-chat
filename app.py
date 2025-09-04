from flask import Flask, render_template
from flask_cors import CORS
from routes import api  # `routes.py` の Blueprint をインポート

app = Flask(__name__)
CORS(app)

app.register_blueprint(api)  # `routes.py` を Blueprint として登録


@app.route("/")
def index():
    return render_template("index.html")

# if __name__ == "__main__": のブロックは、
# Heroku(gunicorn)では使われないため、削除しても、そのままでもOKです。
# ローカルで python app.py と実行したい場合のために残しておいても良いでしょう。
if __name__ == "__main__":
    app.run(debug=True)