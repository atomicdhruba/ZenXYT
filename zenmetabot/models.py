from dataclasses import dataclass, field

@dataclass
class VideoMeta:
    id: str
    old_title: str
    old_desc: str
    duration_s: int
    new_title: str = ""
    new_desc: str = ""
    new_tags: list = field(default_factory=list)
    seo_score: dict = field(default_factory=dict)
    
    draft_nvidia: dict = field(default_factory=dict)
    draft_gemini: dict = field(default_factory=dict)
    draft_debate: dict = field(default_factory=dict)
