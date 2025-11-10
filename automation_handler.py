import os, json, csv, io, datetime, re
import requests
from urllib.parse import urlparse
from PIL import Image
from openai import OpenAI

# =========================
# 환경변수 (Render → Environment)
# =========================
NOTION_TOKEN   = os.getenv("NOTION_TOKEN", "")
NOTION_DB      = os.getenv("NOTION_DB", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# (선택) 주문 피드 URL: CSV/TSV/구글시트-CSV 링크 등
ORDERS_FEED_URL = os.getenv("ORDERS_FEED_URL", "")

# (선택) 카카오톡 나에게 보내기용 사용자 액세스 토큰
# https://developers.kakao.com > 내 애플리케이션 > 동의항목/토큰 발급 필요
KAKAO_ACCESS_TOKEN = os.getenv("KAKAO_ACCESS_TOKEN", "")

# Notion 공통 헤더
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# OpenAI 클라이언트
def _openai():
    client = OpenAI(api_key=OPENAI_API_KEY)
    return client

# Notion DB 쿼리
def notion_query_db(db_id, filter_json=None):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload = {}
    if filter_json:
        payload["filter"] = filter_json
    r = requests.post(url, headers=NOTION_HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

# Notion 페이지 속성 업데이트
def notion_update_page(page_id, properties):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": properties}
    r = requests.patch(url, headers=NOTION_HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

# Notion 페이지 생성
def notion_create_page(db_id, properties):
    url = "https://api.notion.com/v1/pages"
    payload = {"parent": {"database_id": db_id}, "properties": properties}
    r = requests.post(url, headers=NOTION_HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

# Notion 블록 텍스트 추출 (간단)
def notion_extract_plain_text(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    r = requests.get(url, headers=NOTION_HEADERS, timeout=60)
    if r.status_code != 200:
        return ""
    data = r.json()
    text = []
    for b in data.get("results", []):
        if "paragraph" in b and "rich_text" in b["paragraph"]:
            for t in b["paragraph"]["rich_text"]:
                text.append(t.get("plain_text", ""))
    return "\n".join(text).strip()

# GPT 요약
def summarize_text(text):
    if not text.strip():
        return ""
    client = _openai()
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role":"system","content":"너는 한국어 요약을 정확히 작성하는 도우미다."},
            {"role":"user","content":f"아래 내용을 한 단락(3~5문장)으로 핵심만 명확히 요약해줘.\n\n{text}"}
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

# GPT 상세페이지 문구 생성
def generate_detail_from_props(name, attributes):
    client = _openai()
    prompt = f"""
제품명: {name}
주요 속성: {json.dumps(attributes, ensure_ascii=False)}

상세페이지용 소개문(제목 1줄 + 본문 4~6문장)과 핵심 포인트 3가지를 한국어로 만들어줘.
"""
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role":"system","content":"이커머스 상세페이지 카피라이터"},
            {"role":"user","content":prompt}
        ],
        temperature=0.6
    )
    return resp.choices[0].message.content.strip()

# 간단 이미지 카테고리 태깅 (URL만 보고 파일명/경로 키워드로 분류)
def tag_image_url(url):
    path = urlparse(url).path.lower()
    if any(k in path for k in ["forklift","지게차","fork"]):
        return "지게차/안전"
    if any(k in path for k in ["acrylic","아크릴","sign","간판"]):
        return "자재/간판"
    return "기타"

# 카카오톡 나에게 보내기
def kakao_me_send(text):
    if not KAKAO_ACCESS_TOKEN:
        return {"ok": False, "msg": "KAKAO_ACCESS_TOKEN missing"}
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {KAKAO_ACCESS_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
    }
    # 텍스트 템플릿
    template_object = {
        "object_type": "text",
        "text": text,
        "link": {"web_url":"https://notion.so"}
    }
    data = {"template_object": json.dumps(template_object, ensure_ascii=False)}
    r = requests.post(url, headers=headers, data=data, timeout=30)
    try:
        r.raise_for_status()
        return {"ok": True}
    except:
        return {"ok": False, "status": r.status_code, "resp": r.text}

# ─────────────────────────────────────────
# 1) 매시간 자동 실행 루틴
#    - Notion DB에서 특정 조건만 요약/업데이트
#      (예: 속성 '작업상태' = '요약필요' 인 페이지만)
# ─────────────────────────────────────────
def run_automation():
    if not (NOTION_TOKEN and NOTION_DB and OPENAI_API_KEY):
        return {"status": "error", "msg": "Missing env vars"}
    # 필터: select 속성 '작업상태' 가 '요약필요'
    filter_json = {
        "property": "작업상태",
        "select": {"equals": "요약필요"}
    }
    data = notion_query_db(NOTION_DB, {"and":[filter_json]})
    count_updated = 0
    for page in data.get("results", []):
        pid = page["id"]
        src_text = notion_extract_plain_text(pid)
        summary = summarize_text(src_text)
        if not summary:
            continue
        # Summary(리치텍스트) + 작업상태를 '완료'로
        properties = {
            "Summary": {
                "rich_text": [{"text":{"content": summary[:2000]}}]
            },
            "작업상태": {
                "select": {"name":"완료"}
            }
        }
        notion_update_page(pid, properties)
        count_updated += 1
    return {"status":"done","updated_pages":count_updated}

# ─────────────────────────────────────────
# 2) 주문 자동 수집 → Notion DB 저장
#    - CSV 피드 가정: 컬럼(name, qty, price)
#    - Notion DB의 속성: Name(Title), 수량(Number), 금액(Number), 작업상태(Select)
# ─────────────────────────────────────────
def pull_orders_and_save():
    if not (NOTION_TOKEN and NOTION_DB):
        return {"status":"error","msg":"Missing Notion env"}
    if not ORDERS_FEED_URL:
        return {"status":"error","msg":"ORDERS_FEED_URL missing"}

    r = requests.get(ORDERS_FEED_URL, timeout=60)
    r.raise_for_status()
    content = r.content.decode("utf-8", errors="ignore")
    rows = list(csv.DictReader(io.StringIO(content)))
    created = 0
    for row in rows:
        name  = row.get("name") or row.get("상품명") or "주문"
        qty   = int((row.get("qty") or row.get("수량") or "1").strip())
        price = int(re.sub(r"[^0-9]","", (row.get("price") or row.get("금액") or "0")))
        props = {
            "Name": {"title":[{"text":{"content": name}}]},
            "수량": {"number": qty},
            "금액": {"number": price},
            "작업상태": {"select":{"name":"신규"}}
        }
        notion_create_page(NOTION_DB, props)
        created += 1
    return {"status":"done","created":created}

# ─────────────────────────────────────────
# 3) 상세페이지 자동 생성 Pipeline
#    - 조건: 작업상태 = '상세필요'
#    - 결과: 상세페이지(리치텍스트) 작성, 작업상태='상세완료'
# ─────────────────────────────────────────
def generate_details_pipeline():
    filter_json = {"property":"작업상태","select":{"equals":"상세필요"}}
    data = notion_query_db(NOTION_DB, {"and":[filter_json]})
    updated = 0
    for page in data.get("results", []):
        pid = page["id"]
        props = page.get("properties", {})
        name = ""
        if "Name" in props and "title" in props["Name"]:
            title_arr = props["Name"]["title"]
            if title_arr:
                name = title_arr[0].get("plain_text","")
        # 임의로 몇 속성 추출 예시(없으면 빈값)
        attributes = {
            "수량": props.get("수량",{}).get("number"),
            "금액": props.get("금액",{}).get("number")
        }
        detail = generate_detail_from_props(name, attributes)
        properties = {
            "상세페이지": {"rich_text":[{"text":{"content":detail[:2000]}}]},
            "작업상태": {"select":{"name":"상세완료"}}
        }
        notion_update_page(pid, properties)
        updated += 1
    return {"status":"done","updated":updated}

# ─────────────────────────────────────────
# 4) 이미지 기반 자동 정리
#    - 조건: 작업상태='이미지정리'
#    - 속성 '이미지' (files/url) 을 보고 카테고리 속성에 태그 입력
# ─────────────────────────────────────────
def image_sort_pipeline():
    filter_json = {"property":"작업상태","select":{"equals":"이미지정리"}}
    data = notion_query_db(NOTION_DB, {"and":[filter_json]})
    updated = 0
    for page in data.get("results", []):
        pid = page["id"]
        props = page.get("properties", {})
        urls = []
        if "이미지" in props and props["이미지"].get("files"):
            for f in props["이미지"]["files"]:
                if f.get("type")=="external":
                    urls.append(f["external"]["url"])
                elif f.get("type")=="file":
                    urls.append(f["file"]["url"])
        tags = list({tag_image_url(u) for u in urls}) or ["기타"]
        properties = {
            "카테고리": {
                "multi_select": [{"name": t} for t in tags]
            },
            "작업상태": {"select":{"name":"정리완료"}}
        }
        notion_update_page(pid, properties)
        updated += 1
    return {"status":"done","updated":updated}

# ─────────────────────────────────────────
# 5) 매일 자동 보고서 → 카카오톡 전송
#    - 오늘 생성/갱신 건수 요약
# ─────────────────────────────────────────
def send_daily_report():
    today = datetime.date.today().isoformat()
    # 간단히 전체 조회 후 created_time/last_edited_time로 집계
    data = notion_query_db(NOTION_DB)
    created_today = 0
    updated_today = 0
    for page in data.get("results", []):
        c = page.get("created_time","")[:10]
        u = page.get("last_edited_time","")[:10]
        if c == today: created_today += 1
        if u == today: updated_today += 1
    msg = f"""[Daily Report]
날짜: {today}
신규 생성: {created_today}건
수정/완료: {updated_today}건

- 자동 요약(요약필요→완료)
- 주문 수집(신규)
- 상세페이지(상세필요→상세완료)
- 이미지 정리(이미지정리→정리완료)
"""
    send_res = kakao_me_send(msg)
    return {"status":"done","kakao":send_res}
