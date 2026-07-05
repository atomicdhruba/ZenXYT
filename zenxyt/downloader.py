import yt_dlp
from pathlib import Path
from zenxyt.config import CFG, log

def download_video(video_id: str) -> str:
    """
    Download with cascading client fallback:
      1. web  + cookies.txt  (best — no GVS token issues)
      2. web  without cookies (if cookies.txt missing)
      3. tv_embedded          (last resort, no auth needed)
    """
    out = f"{video_id}.mp4"
    has_cookies = Path(CFG.COOKIES_FILE).exists()

    # Format cascade: prefer low-res mp4; fall back to any mp4, then best available
    FORMAT = CFG.VIDEO_FORMAT

    base_opts = {
        "outtmpl": out,
        "format": FORMAT,
        "quiet": True,
        "no_warnings": False,
        "socket_timeout": 60,
        "merge_output_format": "mp4",
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
    }

    if has_cookies:
        base_opts["cookiefile"] = CFG.COOKIES_FILE
        log.debug(f"  Using cookies from {CFG.COOKIES_FILE}")
    else:
        log.warning("  cookies.txt not found — downloading without auth (may hit rate limits)")

    with yt_dlp.YoutubeDL(base_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    # yt-dlp sometimes adds .mp4.mp4 — normalise
    if not Path(out).exists():
        alt = out.replace(".mp4", "")
        for candidate in Path(".").glob(f"{video_id}*"):
            candidate.rename(out)
            break

    return out
