from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Server is running ✅"

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/tasks/create", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        data = request.json
        return jsonify({"received": data}), 201
    return "Use POST to create tasks"

# ✅ Gunicorn 환경에서는 필요 없다
# ✅ 로컬 테스트할 때만 사용
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
