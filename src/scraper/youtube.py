import yt_dlp
from ..database import add_content

def fetch_youtube_metadata(keywords, max_results=5):
    """使用 yt-dlp 搜索并获取元数据"""
    print(f"🔍 正在搜索 YouTube: {keywords}...")
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True, # 只获取列表信息，不深入解析（速度快）
        'default_search': 'ytsearch',
    }

    results = []
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # 搜索 videos
            search_query = f"ytsearch{max_results}:{keywords}"
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    item = {
                        'id': entry.get('id'),
                        'source': 'youtube',
                        'title': entry.get('title'),
                        'url': entry.get('url'), # 或者是 https://www.youtube.com/watch?v=ID
                        'thumbnail': f"https://img.youtube.com/vi/{entry.get('id')}/mqdefault.jpg",
                        'duration': entry.get('duration', 0)
                    }
                    if add_content(item):
                        print(f"   [+] 新增: {item['title'][:30]}...")
                        results.append(item)
                    else:
                        print(f"   [.] 已存在: {item['title'][:30]}...")
        except Exception as e:
            print(f"❌ 抓取出错: {e}")
            
    return results

def get_stream_url(video_url):
    """获取实际播放流地址（用于播放器）"""
    ydl_opts = {
        'format': 'bestaudio/best', # 优先获取音频，或者最佳格式
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('url') # 这是真实的 CDN 播放地址
