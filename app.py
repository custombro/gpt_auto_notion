from flask import Flask, request, jsonify, redirect
import os
import requests

app = Flask(__name__)

# ✅ 환경 변수
CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI")

TOKEN_URL = "https://api.notion.com/v1/oauth/token"

@app.route("/")
def home():
    return "✅ GPT Auto Notion Server Running"

# ✅ OAuth Redirect handler
@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "❌ Missing OAuth code", 400

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    res = requests.post(TOKEN_URL, json=data)
    if res.status_code != 200:
        return f"❌ Token exchange failed: {res.text}", 500

    token_data = res.json()
    access_token = token_data.get("access_token")

    return f"✅ OAuth Success!<br><br>Access Token:<br>{access_token}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
