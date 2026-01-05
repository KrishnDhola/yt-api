from fastapi import FastAPI, HTTPException
import yt_dlp
from datetime import datetime

app = FastAPI(title="YT-DLP Data Hunter API", version="2.0")

# --- Helper: Convert Bytes to Human Readable (MB/GB) ---
def get_size(bytes_val):
    if not bytes_val: return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0

@app.get("/")
def home():
    return {
        "system_status": "ONLINE",
        "mode": "RECONNAISSANCE",
        "usage": "/analyze?url=YOUR_LINK"
    }

@app.get("/analyze")
async def analyze_video(url: str):
    print(f"[*] Hunting data for: {url}")
    
    # 1. Configure yt-dlp to extraction mode (No Download)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True, # CRITICAL: Only fetch metadata
        'geo_bypass': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract all raw info
            info = ydl.extract_info(url, download=False)

            # 2. Filter and Sort Formats
            formats_video_audio = [] # Ready to play (720p/360p)
            formats_video_only = []  # High res (1080p/4k) - needs merging
            formats_audio_only = []  # mp3/m4a
            
            for f in info.get('formats', []):
                # Skip m3u8/manifests (usually useless for direct download)
                if 'manifest' in f.get('protocol', ''): continue
                
                # Create a clean "Hunter" data object for this format
                format_data = {
                    "format_id": f.get('format_id'),
                    "ext": f.get('ext'),
                    "resolution": f.get('resolution', 'N/A'),
                    "filesize": get_size(f.get('filesize') or f.get('filesize_approx')),
                    "fps": f.get('fps'),
                    "vcodec": f.get('vcodec'),
                    "acodec": f.get('acodec'),
                    "url": f.get('url') # <--- THE DIRECT LINK
                }

                # Categorize
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats_video_audio.append(format_data)
                elif f.get('vcodec') != 'none':
                    formats_video_only.append(format_data)
                elif f.get('acodec') != 'none':
                    formats_audio_only.append(format_data)

            # 3. Construct the "Beautiful" JSON Response
            return {
                "status": "SUCCESS",
                "extracted_at": datetime.now().isoformat(),
                "hunter_signature": "GHOST-V1",
                "meta": {
                    "title": info.get('title'),
                    "channel": info.get('uploader'),
                    "views": info.get('view_count'),
                    "duration_seconds": info.get('duration'),
                    "upload_date": info.get('upload_date'),
                    "age_limit": info.get('age_limit'),
                },
                "assets": {
                    "thumbnail": info.get('thumbnail'),
                    "description": info.get('description'),
                    "tags": info.get('tags', []),
                    "categories": info.get('categories', []),
                },
                "captions": list(info.get('subtitles', {}).keys()) if info.get('subtitles') else "None",
                "direct_links": {
                    "best_muxed (720p/360p with audio)": formats_video_audio,
                    "audio_streams": formats_audio_only,
                    "high_definition_video_only": formats_video_only
                }
            }

    except Exception as e:
        return {
            "status": "FAILURE",
            "error": str(e),
            "hint": "Check if URL is valid or if YouTube is blocking the server IP."
        }
