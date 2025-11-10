from flask import Flask, jsonify, request
import os
from automation_handler import (
    run_automation,
    pull_orders_and_save,
    generate_details_pipeline,
    image_sort_pipeline,
    send_daily_report
)

app = Flask(__name__)

@app.route("/")
def home():
    return "Server is running.", 200

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/debug")
def debug():
    import os
    cwd = os.getcwd()
    files = os.listdir(cwd)
    return jsonify({"cwd": cwd, "files": files}), 200

# 1) 매시간 자동 실행(핵심 루틴)
@app.route("/run_automation")
def run_automation_route():
    result = run_automation()
    return jsonify(result), 200

# 2) 주문 수집 → DB 저장 (수동 트리거용)
@app.route("/orders/pull")
def pull_orders_route():
    result = pull_orders_and_save()
    return jsonify(result), 200

# 3) 상세페이지 자동 생성 파이프라인
@app.route("/pipeline/generate")
def pipeline_generate_route():
    result = generate_details_pipeline()
    return jsonify(result), 200

# 4) 이미지 URL 자동 분류/정리
@app.route("/images/sort")
def images_sort_route():
    result = image_sort_pipeline()
    return jsonify(result), 200

# 5) 매일 자동 보고서 (수동 트리거)
@app.route("/report/daily")
def report_daily_route():
    result = send_daily_report()
    return jsonify(result), 200


if __name__ == "__main__":
    # 로컬 테스트용
    app.run(host="0.0.0.0", port=5000)
