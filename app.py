from flask import Flask, redirect, request, jsonify
import requests
import os

app = Flask(__name__)

KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

# 카카오 로그인 URL
@app.route("/kakao/login")
def kakao_login():
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize?"
        f"client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        "&response_type=code"
    )
    return redirect(kakao_auth_url)

# 카카오 로그인 후 Redirect 되는 URL
@app.route("/kakao/callback")
def kakao_callback():
    code = request.args.get("code")

    # Access Token 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI",
        "code": code,
        "client_secret": KAKAO_CLIENT_SECRET
    }

    res = requests.post(token_url, data=data)
    token_json = res.json()

    return jsonify(token_json)

@app.route("/")
def home():
    return "Kakao login server is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
