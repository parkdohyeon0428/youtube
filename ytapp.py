from flask import Flask, render_template, request
import requests
import os
import time
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# GitHub JSON 데이터 URL
owner = "parkdohyeon0428"
repo = "youtube"
GITHUB_JSON_URL = f"https://raw.githubusercontent.com/{owner}/{repo}/main/data/trending_videos.json"

# 🔹 공통으로 사용할 JSON 데이터 로드 함수
def fetch_videos():
    response = requests.get(GITHUB_JSON_URL)
    if response.status_code == 200:
        return response.json()  # JSON 데이터를 리스트로 변환하여 반환
    return []  # 실패 시 빈 리스트 반환

videos = fetch_videos().get("videos",[])  # JSON 데이터 한 번만 호출

def conver_time(duration):
    parts = list(map(int, duration.split(":")))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]


@app.route("/")
def home():
    scraped_time = fetch_videos().get("scraped_time")
    month1 = scraped_time.split(" ")[0].split("-")[1]
    day1 = scraped_time.split(" ")[0].split("-")[2]
    hour1 = scraped_time.split(" ")[1].split(":")[0]

    duration_filter = request.args.get("duration", "")
    category_filter = request.args.get("category", "all")


    # 시간필터 적용 15분 미만, 15분~30분, 30분 초과
    filtered_videos = []

    for video in videos:
        vs = conver_time(video["duration"])

        if duration_filter == "under15" and vs < 900:
            filtered_videos.append(video)
        elif duration_filter == "15to30" and 900 <= vs <= 1800:
            filtered_videos.append(video)
        elif duration_filter == "over30" and vs > 1800:
            filtered_videos.append(video)
        if not duration_filter:
            filtered_videos = videos


        if category_filter and category_filter != "all":
            filtered_videos = [video for video in filtered_videos if video.get("category") == category_filter]
    
    # index.html 템플릿을 렌더링하고 특정 데이터를 템플릿으로 전달달
    return render_template("index.html", 
                           videos=filtered_videos, 
                           selected_filter=duration_filter, 
                           selected_category_filter=category_filter,
                           month1 = month1, 
                           day1 = day1,
                           hour1 = hour1)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CACHE = {}  # 캐싱된 댓글 저장
CACHE_EXPIRY = 60 * 60  # 1시간 캐싱 유지

def get_best_comments(video_id):
    """YouTube API에서 베스트 댓글을 가져오는 함수"""
    # 캐시된 데이터가 있으면 반환 (API 호출 최소화)
    if video_id in CACHE and time.time() - CACHE[video_id]["timestamp"] < CACHE_EXPIRY:
        print(f"[CACHE HIT] {video_id}의 댓글을 캐시에서 가져옴")
        return CACHE[video_id]["comments"]

    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": API_KEY,
        "order": "relevance",  # 인기순 정렬
        "maxResults": 5
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data:
        print(f"❌ YouTube API 오류 발생: {data['error']['message']}")
        return []

    comments = []
    for item in data.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "author": snippet["authorDisplayName"],
            "text": snippet["textDisplay"],
            "likes": snippet.get("likeCount", 0)  # 좋아요 수 추가
        })

    # 캐시에 저장
    CACHE[video_id] = {
        "comments": comments,
        "timestamp": time.time()
    }

    return comments

@app.route('/best_comments')
def best_comments():
    """index 페이지에서 요청한 후, best_comments.html에 댓글 전달"""
    video_id = request.args.get("video_id")
    video_title = request.args.get("title")

    if not video_id:
        return "잘못된 요청입니다. video_id가 필요합니다.", 400

    # YouTube API에서 베스트 댓글 가져오기
    comments = get_best_comments(video_id)
    video= next((video for video in videos if video["video_id"] == video_id), None)
    return render_template(
        "best_comments.html",
        title=video_title,
        url=f"https://www.youtube.com/watch?v={video_id}",
        comments=comments,
        video=video
    )

if __name__ == "__main__":
    app.run("0.0.0.0")
