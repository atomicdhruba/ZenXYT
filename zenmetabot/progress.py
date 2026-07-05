import json
from pathlib import Path
from zenmetabot.config import CFG, log

class ProgressLog:
    def __init__(self, path: str):
        self.path  = Path(path)
        self._done: set = set()
        if self.path.exists():
            try:
                self._done = set(json.loads(self.path.read_text()))
                log.info(f"Resuming — {len(self._done)} videos already done.")
            except Exception:
                log.warning("Could not read progress log; starting fresh.")

    def mark_done(self, video_id: str) -> None:
        self._done.add(video_id)
        self.path.write_text(json.dumps(sorted(self._done), indent=2))

    def is_done(self, video_id: str) -> bool:
        return video_id in self._done

progress = ProgressLog(CFG.PROGRESS_LOG)
