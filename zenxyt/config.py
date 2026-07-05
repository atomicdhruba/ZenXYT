import os
import logging
from dataclasses import dataclass
from pathlib import Path

# Try to load python-dotenv, but don't hard-crash if missing, we can load from env directly
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class Config:
    # ── NVIDIA API ──────────────────────────────────────
    NVIDIA_API_KEY: str = os.environ.get("NVIDIA_API_KEY", "")
    NVIDIA_MODEL: str = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
    NVIDIA_MAX_TOKENS: int = int(os.environ.get("NVIDIA_MAX_TOKENS", "4096"))
    NVIDIA_TEMPERATURE: float = float(os.environ.get("NVIDIA_TEMPERATURE", "0.3"))
    NVIDIA_FREQ_PENALTY: float = float(os.environ.get("NVIDIA_FREQ_PENALTY", "0.3"))
    NVIDIA_API_TIMEOUT: int = int(os.environ.get("NVIDIA_API_TIMEOUT", "120"))

    # ── GOOGLE GEMINI API ───────────────────────────────
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

    # ── YOUTUBE AUTH ────────────────────────────────────
    CLIENT_SECRETS: str = os.environ.get("GOOGLE_CLIENT_SECRETS_PATH", "client_secrets.json")
    TOKEN_PICKLE: str = os.environ.get("GOOGLE_TOKEN_PICKLE_PATH", "token.pickle")
    COOKIES_FILE: str = os.environ.get("COOKIES_FILE", "cookies.txt")

    # ── BEHAVIOR ────────────────────────────────────────
    GENERATION_MODE: str = os.environ.get("GENERATION_MODE", "debate").lower().strip()
    VIDEO_TYPE_FILTER: str = os.environ.get("VIDEO_TYPE_FILTER", "all").lower().strip()
    MAX_DURATION_S: int = int(os.environ.get("MAX_DURATION_SECONDS", "65"))
    VIDEO_FORMAT: str = os.environ.get("VIDEO_FORMAT", "worst[height<=360][ext=mp4]/worst[ext=mp4]/worst/best")
    SKIP_DONE: bool = os.environ.get("SKIP_DONE", "true").strip().lower() == "true"
    
    # ── PIPELINE & RETRY ────────────────────────────────
    MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", "3"))
    BACKOFF_BASE_S: int = int(os.environ.get("BACKOFF_BASE_SECONDS", "15"))
    INTER_VIDEO_S: int = int(os.environ.get("INTER_VIDEO_SECONDS", "45"))
    WORKERS: int = int(os.environ.get("WORKERS", "2"))

    # ── LOGGING & STORAGE ───────────────────────────────
    PROGRESS_LOG: str = os.environ.get("PROGRESS_LOG", "progress.json")
    LOG_FILE: str = os.environ.get("LOG_FILE", "bot.log")
    BRAIN_DIR: str = "brain"

    def __post_init__(self):
        Path(self.BRAIN_DIR).mkdir(exist_ok=True)
        # Setup logging configuration here to ensure it's available everywhere
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.LOG_FILE, encoding="utf-8"),
            ],
        )

CFG = Config()
log = logging.getLogger("zenxveda")
