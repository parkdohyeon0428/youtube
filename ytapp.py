from flask import Flask, render_template, jsonify
import requests
import json
import os

app = Flask(__name__)

# JSON 파일 경로 설정 (현재 디렉토리에서 직접 로드)
JSON_FILE_PATH = "C:/Users/kccistc/Desktop/workspace/data/trending_videos.json"

# 1️⃣ index.html 렌더링
@app.route("/")
def home():
    return render_template("index.html")

# 2️⃣ JSON 데이터를 GitHub으로 부터 가져와서 API로 제공
owner = "parkdohyeon0428"
repo = "youtube"
GITHUB_JSON_URL = f"https://raw.githubusercontent.com/{owner}/{repo}/main/templates/trending_videos.json"
@app.route("/api/videos")
def get_videos():
    response = requests.get(GITHUB_JSON_URL)
    if response.status_code == 200:
        return jsonify(response.json())  # JSON 응답 반환
    else:
        return jsonify({"error": "Failed to fetch data"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
