import os
import requests

NOTION_VERSION = "2022-06-28"
NOTION_DB = os.getenv("NOTION_DB")

def notion_request(method, url, payload=None, token=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

    if method == "POST":
        res = requests.post(url, json=payload, headers=headers)
    elif method == "GET":
        res = requests.get(url, headers=headers)
    else:
        return None

    return res.json()
