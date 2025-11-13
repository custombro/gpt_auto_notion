from flask import Flask, redirect, request, jsonify
import os
import requests

app = Flask(__name__)

# 환경 변수 불러오기
KAKAO_CLIENT_ID = os.getenv("KAKAO_REST_API_KEY")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")


# 카카오 로그인 URL (사용자가 최초로 접속할 곳)
@app.route("/kakao/login")
def kakao_login():
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize?"
        f"client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        "&response_type=code"
    )
    return redirect(kakao_auth_url)


# 카카오 인가코드 수신 → Access Token 요청
@app.route("/kakao/callback")
def kakao_callback():
    code = request.args.get("code")

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
        "client_secret": KAKAO_CLIENT_SECRET,
    }

    res = requests.post(token_url, data=data)
    token_json = res.json()

    return jsonify(token_json)


@app.route("/")
def home():
    return "Kakao login server is running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
