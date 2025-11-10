from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Server is running.", 200

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/debug")
def debug():
    cwd = os.getcwd()
    files = os.listdir(cwd)
    return jsonify({
        "cwd": cwd,
        "files": files
    }), 200

# ❌ app.run() 제거! (Render에서는 사용 금지)
# 절대 넣지 말 것
