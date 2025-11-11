import os
import requests
import json

def notion_query(database_id, access_token):
    res = requests.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    if res.status_code != 200:
        return None, res.text

    return res.json(), None


def run_automation():
    NOTION_DB = os.getenv("NOTION_DB")
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")

    if not NOTION_DB or not NOTION_TOKEN:
        return "❌ NOTION_DB 또는 NOTION_TOKEN 없음."

    # ✅ DB 조회
    data, err = notion_query(NOTION_DB, NOTION_TOKEN)
    if err:
        return f"❌ Notion Error: {err}"

    entries = data.get("results", [])

    processed = len(entries)

    return f"✅ 자동화 처리됨: {processed}개 항목"
