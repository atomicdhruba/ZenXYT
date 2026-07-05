import time
from pathlib import Path
from typing import Callable, Optional

from zenmetabot.config import CFG, log
from zenmetabot.models import VideoMeta
from zenmetabot.youtube import get_youtube_client
from zenmetabot.downloader import download_video
from zenmetabot.brain import extract_brain
from zenmetabot.ai_nvidia import generate_metadata_nvidia
from zenmetabot.ai_gemini import generate_metadata_gemini
from zenmetabot.debate import run_debate, get_seo_score
from zenmetabot.progress import progress

def process_single_video(
    video: VideoMeta, 
    index: int, 
    total: int, 
    skip_done: bool, 
    gui_callback: Optional[Callable] = None
) -> bool:
    
    def notify(msg):
        log.info(msg)
        if gui_callback:
            gui_callback(msg)

    if skip_done and progress.is_done(video.id):
        notify(f"[{index}/{total}] ⏭  {video.id} already done — skipping.")
        return True
    if not skip_done and progress.is_done(video.id):
        notify(f"[{index}/{total}] 🔄  {video.id} already done — reprocessing (skip-done OFF).")

    notify(f"[{index}/{total}] ▶  Processing {video.id} …")

    for attempt in range(1, CFG.MAX_RETRIES + 1):
        local_file = ""
        try:
            # 1. Download
            notify(f"  ⬇️ Downloading video...")
            local_file = download_video(video.id)
            
            # 2. Extract Brain
            notify(f"  🧠 Extracting brain intelligence...")
            brain_path = extract_brain(video.id, local_file)
            brain_text = Path(brain_path).read_text(encoding="utf-8")
            
            # 3. Generate Metadata based on Mode
            mode = CFG.GENERATION_MODE
            notify(f"  🎛️ Mode: {mode.upper()}")
            
            if mode == "nvidia":
                meta = generate_metadata_nvidia(video, brain_text)
            elif mode == "gemini":
                meta = generate_metadata_gemini(video, brain_text)
            elif mode == "debate":
                meta = run_debate(video, brain_text, gui_callback)
            else:
                notify(f"Unknown mode '{mode}'. Defaulting to debate.")
                meta = run_debate(video, brain_text, gui_callback)
                
            # Ensure keys are lowercase just in case the AI capitalized them
            meta = {k.lower(): v for k, v in meta.items()}
            
            video.new_title = meta.get("title", video.old_title)
            video.new_desc  = meta.get("description", video.old_desc)
            video.new_tags  = meta.get("tags", [])
            
            notify(f"  📝 New Title: {video.new_title}")
            notify(f"  🏷️ New Tags: {', '.join(video.new_tags[:5])}...")
            
            # 4. SEO Score
            notify("  📊 Calculating SEO Virality Score...")
            score = get_seo_score(meta)
            video.seo_score = score
            notify(f"  🏆 Score: {score.get('total_score', '?')}/100")

            # 5. Update YouTube
            notify("  ✅ Updating YouTube metadata...")
            get_youtube_client().update_video(video)
            
            # 6. Mark Done
            progress.mark_done(video.id)
            notify(f"[{index}/{total}] ✅  {video.id} fully updated.")
            return True

        except Exception as exc:
            notify(f"[{index}/{total}] ❌ Error on {video.id} (attempt {attempt}/{CFG.MAX_RETRIES}): {exc}")
        finally:
            if local_file and Path(local_file).exists():
                try:
                    Path(local_file).unlink()
                    log.debug(f"  Deleted temp file {local_file}")
                except Exception as e:
                    log.warning(f"  Could not delete temp file {local_file}: {e}")

        if attempt < CFG.MAX_RETRIES:
            wait = CFG.BACKOFF_BASE_S * (2 ** (attempt - 1))
            notify(f"  ⏳ Retrying in {wait}s …")
            time.sleep(wait)

    notify(f"[{index}/{total}] ❌  {video.id} failed after {CFG.MAX_RETRIES} attempts.")
    return False
