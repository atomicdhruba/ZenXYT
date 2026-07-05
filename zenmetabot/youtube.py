import pickle
import re
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from zenmetabot.config import CFG, log
from zenmetabot.models import VideoMeta

def _iso_duration_to_seconds(duration: str) -> int:
    parts = {"H": 3600, "M": 60, "S": 1}
    total = 0
    for unit, mult in parts.items():
        m = re.search(rf"(\d+){unit}", duration)
        if m:
            total += int(m.group(1)) * mult
    return total

class YouTubeClient:
    def __init__(self):
        self.youtube = self._build_youtube()

    def _build_youtube(self):
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        creds = None
        token_path = Path(CFG.TOKEN_PICKLE)

        if token_path.exists():
            creds = pickle.loads(token_path.read_bytes())

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    log.warning("Refresh token expired. Re-authenticating...")
                    token_path.unlink(missing_ok=True)
                    flow = InstalledAppFlow.from_client_secrets_file(CFG.CLIENT_SECRETS, scopes)
                    creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CFG.CLIENT_SECRETS, scopes)
                creds = flow.run_local_server(port=0)
            token_path.write_bytes(pickle.dumps(creds))

        log.info("YouTube authenticated ✓")
        return build("youtube", "v3", credentials=creds)

    def get_videos(self) -> List[VideoMeta]:
        log.info("Fetching uploads playlist …")
        ch = self.youtube.channels().list(mine=True, part="contentDetails").execute()
        playlist_id = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        raw, token = [], None
        while True:
            page = self.youtube.playlistItems().list(
                playlistId=playlist_id,
                part="contentDetails,snippet",
                maxResults=50,
                pageToken=token,
            ).execute()
            for item in page["items"]:
                raw.append(VideoMeta(
                    id=item["contentDetails"]["videoId"],
                    old_title=item["snippet"]["title"],
                    old_desc=item["snippet"]["description"],
                    duration_s=0
                ))
            token = page.get("nextPageToken")
            if not token:
                break

        log.info(f"Total uploads: {len(raw)} — checking durations …")
        
        # Batch fetch durations
        ids = [v.id for v in raw]
        for i in range(0, len(ids), 50):
            batch = ids[i : i + 50]
            resp = self.youtube.videos().list(id=",".join(batch), part="contentDetails").execute()
            dur_map = {v["id"]: v["contentDetails"]["duration"] for v in resp["items"]}

            for v in raw[i : i + 50]:
                v.duration_s = _iso_duration_to_seconds(dur_map.get(v.id, "PT0S"))

        filtered = []
        for v in raw:
            is_short = v.duration_s <= CFG.MAX_DURATION_S
            if CFG.VIDEO_TYPE_FILTER == "shorts" and not is_short:
                continue
            if CFG.VIDEO_TYPE_FILTER == "longs" and is_short:
                continue
            filtered.append(v)

        log.info(f"Videos matching filter ({CFG.VIDEO_TYPE_FILTER}): {len(filtered)}")
        return filtered

    def update_video(self, video: VideoMeta) -> None:
        resp = self.youtube.videos().list(part="snippet", id=video.id).execute()
        snippet = resp["items"][0]["snippet"]

        snippet["title"] = video.new_title
        snippet["description"] = video.new_desc
        snippet["tags"] = [t.strip().lstrip("#") for t in video.new_tags][:15]

        self.youtube.videos().update(
            part="snippet",
            body={"id": video.id, "snippet": snippet},
        ).execute()

# Lazy singleton — only created when first accessed, not at import time.
_client = None

def get_youtube_client() -> YouTubeClient:
    global _client
    if _client is None:
        _client = YouTubeClient()
    return _client
