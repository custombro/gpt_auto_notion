from flask import Flask, request, jsonify

app = Flask(__name__)

# ----------------------
# 기본 홈 경로
# ----------------------
@app.route("/")
def home():
    return "Server is running ✅"

# ----------------------
# Render Health Check
# ----------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# ✅ Render 기본 헬스 체크는 /healthz 이므로 추가
@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

# ----------------------
# Task 생성 엔드포인트
# ----------------------
@app.route("/tasks/create", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        data = request.json
        return jsonify({"received": data}), 201

    return "Use POST to create tasks"
