import asyncio
import logging
import subprocess
import shutil
import sqlite3
import json
import requests
import os
import httpx
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, WebSocket, Request, Response, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
import yt_dlp
import uvicorn

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InfinityCore")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_NAME = "infinity_max.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS videos (id TEXT PRIMARY KEY, title TEXT, duration INTEGER, thumbnail TEXT, channel TEXT, ai_reason TEXT, added_at TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_setting(key, default=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def save_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

class ConfigRequest(BaseModel):
    provider: str
    api_key: str
    model: str
    base_url: str = None
    proxy: str = None

def create_http_client(proxy_url: str = None):
    if proxy_url and proxy_url.strip():
        return httpx.Client(proxies=proxy_url, verify=False, timeout=30.0)
    return httpx.Client(trust_env=False, timeout=30.0)

# --- API Config ---
@app.get("/api/config")
def get_config():
    key = get_setting("api_key", "")
    return {
        "is_configured": bool(key),
        "provider": get_setting("provider", "nvidia"),
        "model": get_setting("model", "meta/llama-3.1-70b-instruct"),
        "base_url": get_setting("base_url", "https://integrate.api.nvidia.com/v1"),
        "proxy": get_setting("proxy", "")
    }

@app.post("/api/config")
def update_config(config: ConfigRequest):
    base_url = config.base_url
    if not base_url:
        if config.provider == "openai": base_url = "https://api.openai.com/v1"
        elif config.provider == "deepseek": base_url = "https://api.deepseek.com"
        elif config.provider == "nvidia": base_url = "https://integrate.api.nvidia.com/v1"
        elif config.provider == "siliconflow": base_url = "https://api.siliconflow.cn/v1"

    try:
        http_client = create_http_client(config.proxy)
        client = OpenAI(api_key=config.api_key, base_url=base_url, http_client=http_client)
        client.chat.completions.create(model=config.model, messages=[{"role": "user", "content": "Hi"}], max_tokens=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    save_setting("provider", config.provider)
    save_setting("api_key", config.api_key)
    save_setting("model", config.model)
    save_setting("base_url", base_url)
    save_setting("proxy", config.proxy or "")
    return {"status": "success"}

# --- AI Logic ---
def verify_with_ai(video_metadata, query_person):
    api_key = get_setting("api_key")
    if not api_key: return True, "AI Skipped"
    
    client = OpenAI(api_key=api_key, base_url=get_setting("base_url"), http_client=create_http_client(get_setting("proxy")))
    prompt = f"""
    Role: Content Curator.
    Target: PRIMARY SOURCE of "{query_person}".
    Video: "{video_metadata['title']}" by "{video_metadata['channel']}" ({int(video_metadata['duration']/60)} mins).
    Task: Return JSON: {{"valid": true/false, "reason": "brief reason"}}
    Ignore reactions/commentary.
    """
    try:
        completion = client.chat.completions.create(
            model=get_setting("model"), messages=[{"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=60, response_format={"type": "json_object"}
        )
        res = json.loads(completion.choices[0].message.content)
        return res.get('valid', False), res.get('reason', 'Verified')
    except: return True, "AI Error"

# --- New Feature: AI Insight ---
@app.post("/api/insight")
async def generate_insight(request: Request):
    """
    生成视频深度洞察
    """
    data = await request.json()
    title = data.get("title")
    channel = data.get("channel")
    
    api_key = get_setting("api_key")
    if not api_key: return {"insight": "AI Not Configured."}

    client = OpenAI(api_key=api_key, base_url=get_setting("base_url"), http_client=create_http_client(get_setting("proxy")))
    
    prompt = f"""
    Analyze this video context:
    Title: "{title}"
    Channel: "{channel}"
    
    Generate a 3-bullet point "Viewing Guide" for a researcher:
    1. Context (What is this?)
    2. Key Topics (What do they discuss?)
    3. Target Audience (Who should watch?)
    
    Keep it concise. HTML format (use <ul><li>).
    """
    
    try:
        completion = client.chat.completions.create(
            model=get_setting("model"), messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=150
        )
        return {"insight": completion.choices[0].message.content}
    except Exception as e:
        return {"insight": f"Analysis Failed: {str(e)}"}

# --- Scraping ---
def get_scraper_opts():
    return {'quiet': True, 'extract_flat': True, 'ignoreerrors': True, 'no_warnings': True, 'socket_timeout': 15}

def heuristic_filter(entry, query_parts):
    title = entry.get('title', '').lower()
    if not any(part in title for part in query_parts): return False
    banned = ["reaction", "react", "gameplay", "short", "#shorts", "tiktok"]
    if any(b in title for b in banned): return False
    if (entry.get('duration') or 0) < 300: return False
    return True

async def fetch_process(websocket, query):
    if not get_setting("api_key"):
        await websocket.send_json({"status": "error", "msg": "⚠️ Configure API Key first."})
        return

    current_year = datetime.now().year
    years = range(current_year, current_year - 5, -1)
    search_matrix = []
    for t in ["full interview", "keynote speech", "documentary", "lecture"]:
        search_matrix.append(f"{query} {t}")
        for y in years: search_matrix.append(f"{query} {t} {y}")

    await websocket.send_json({"status": "log", "msg": f"🌐 Launching Matrix Scan: {len(search_matrix)} probes..."})
    
    semaphore = asyncio.Semaphore(5)
    async def worker(term):
        async with semaphore:
            return await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(get_scraper_opts()).extract_info(f"ytsearch40:{term}", download=False).get('entries', []))

    results = await asyncio.gather(*[worker(t) for t in search_matrix])
    
    raw_candidates = []
    seen = set()
    parts = query.lower().split()
    
    for batch in results:
        if not batch: continue
        for entry in batch:
            if not entry: continue
            vid = entry['id']
            if vid in seen: continue
            if heuristic_filter(entry, parts):
                seen.add(vid)
                raw_candidates.append({
                    'id': vid, 'title': entry['title'], 'channel': entry.get('uploader'),
                    'duration': entry.get('duration'), 'thumbnail': entry.get('thumbnail')
                })

    await websocket.send_json({"status": "log", "msg": f"⚡ Pre-filter: {len(raw_candidates)} candidates found..."})
    
    ai_candidates = raw_candidates[:60]
    final_list = []
    
    await websocket.send_json({"status": "log", "msg": f"🧠 AI Verifying {len(ai_candidates)} items..."})

    for vid in ai_candidates:
        valid, reason = verify_with_ai(vid, query)
        if valid:
            vid['ai_reason'] = reason
            if not vid.get('thumbnail'): vid['thumbnail'] = f"https://img.youtube.com/vi/{vid['id']}/hqdefault.jpg"
            save_video_to_db(vid)
            final_list.append(vid)

    await websocket.send_json({"status": "done", "msg": f"✅ Indexed {len(final_list)} Primary Sources", "data": final_list})

def save_video_to_db(v):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO videos (id, title, duration, thumbnail, channel, ai_reason, added_at) VALUES (?,?,?,?,?,?,?)', 
              (v['id'], v['title'], v['duration'], v['thumbnail'], v['channel'], v['ai_reason'], datetime.now()))
    conn.commit()
    conn.close()

# --- Streaming & Download ---
def get_real_url(vid):
    try:
        cmd = ["yt-dlp", "-g", "-f", "best[ext=mp4]", f"https://www.youtube.com/watch?v={vid}"]
        return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    except: return None

@app.get("/api/stream/{vid}")
async def proxy_stream(vid: str, request: Request):
    url = get_real_url(vid)
    if not url: return Response(status_code=404)
    headers = {"User-Agent": "Mozilla/5.0"}
    if request.headers.get("range"): headers["Range"] = request.headers.get("range")
    try:
        r = requests.get(url, headers=headers, stream=True, timeout=20)
        resp_h = {"Accept-Ranges": "bytes", "Content-Type": "video/mp4"}
        for k in ["Content-Length", "Content-Range"]: 
            if k in r.headers: resp_h[k] = r.headers[k]
        return StreamingResponse(r.iter_content(chunk_size=1024*1024), status_code=r.status_code, headers=resp_h, media_type="video/mp4")
    except: return Response(status_code=502)

# --- New Feature: Download ---
@app.get("/api/download/{vid}")
async def download_video(vid: str):
    """直接下载视频文件"""
    url = get_real_url(vid)
    if not url: return Response(status_code=404)
    
    try:
        r = requests.get(url, stream=True, timeout=20)
        # 设置 header 让浏览器触发下载
        headers = {
            "Content-Disposition": f'attachment; filename="infinity_{vid}.mp4"',
            "Content-Type": "video/mp4"
        }
        return StreamingResponse(r.iter_content(chunk_size=1024*1024), headers=headers)
    except: return Response(status_code=502)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        await fetch_process(websocket, data.get("query"))
    except: await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
