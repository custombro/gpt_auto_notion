from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Server is running ✅"

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/tasks/create", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        data = request.json
        return jsonify({"received": data}), 201
    return "Use POST to create tasks"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
