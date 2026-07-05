import sys
import argparse

def run_cli():
    from zenmetabot.config import CFG, log
    from zenmetabot.youtube import get_youtube_client
    from zenmetabot.orchestrator import process_single_video

    print(f"\n{'─'*60}")
    print(f"  Zen MetaBot Bot v2.0  —  CLI Mode")
    print(f"{'─'*60}")

    if not CFG.NVIDIA_API_KEY and not CFG.GEMINI_API_KEY:
        print("❌ API Keys missing. Please copy .env.example to .env and fill in your keys.")
        sys.exit(1)

    yt = get_youtube_client()
    log.info("Fetching videos...")
    videos = yt.get_videos()
    total = len(videos)
    
    if total == 0:
        log.info("No videos matched the current filters.")
        sys.exit(0)
        
    start_raw = input(f"Start at video # (1–{total})  [Enter = 1]: ").strip()
    end_raw   = input(f"End at video #   (1–{total})  [Enter = all]: ").strip()

    start_idx = (int(start_raw) - 1) if start_raw.isdigit() else 0
    end_idx   = int(end_raw)          if end_raw.isdigit()   else total

    selected = videos[start_idx:end_idx]
    log.info(f"Queued {len(selected)} videos.")
    
    successes = failures = 0

    for i, v in enumerate(selected, start=start_idx + 1):
        if process_single_video(v, i, total, skip_done=CFG.SKIP_DONE):
            successes += 1
        else:
            failures += 1

    print(f"\n{'─'*60}")
    print(f"  Batch complete — ✅ {successes} succeeded  ❌ {failures} failed")
    print(f"{'─'*60}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zen MetaBot Video Intelligence Bot")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line mode without GUI")
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        from zenmetabot.gui import launch_gui
        launch_gui()
