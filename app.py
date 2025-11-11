from flask import Flask, request
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from automation_handler import run_automation

app = Flask(__name__)

# ✅ 환경변수 로딩
NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET")
NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KAKAO_ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN")

# ✅ OAuth Callback (NOTION → 서버)
@app.route('/', methods=['GET'])
def notion_oauth_callback():
    code = request.args.get("code")

    if not code:
        return "✅ Server is running.<br>OAuth code 없음.", 200

    # ✅ 토큰 교환
    token_res = requests.post(
        "https://api.notion.com/v1/oauth/token",
        auth=(NOTION_CLIENT_ID, NOTION_CLIENT_SECRET),
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": NOTION_REDIRECT_URI
        },
        headers={"Content-Type": "application/json"}
    )

    if token_res.status_code != 200:
        return f"❌ Token exchange failed:<br>{token_res.text}", 500

    data = token_res.json()
    access_token = data.get("access_token")

    return f"""
    ✅ Notion OAuth 성공!<br><br>
    Access Token:<br>{access_token}<br><br>
    👉 이 값을 Render 환경변수 NOTION_TOKEN 에 저장하세요.
    """

# ✅ 수동 실행
@app.route('/run_automation', methods=['GET'])
def run_now():
    result = run_automation()
    return f"✅ 실행 완료:<br>{result}", 200


# ✅ 자동 실행 스케줄러
scheduler = BackgroundScheduler()
scheduler.add_job(run_automation, 'interval', hours=1)
scheduler.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
