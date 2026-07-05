from openai import OpenAI
from zenmetabot.config import CFG, log
from zenmetabot.utils import extract_json
from zenmetabot.models import VideoMeta

_NVIDIA_SYSTEM_PROMPT = """\
You are an expert YouTube strategist for the channel Zen MetaBot (Minecraft content).
Generate viral metadata based on the provided BRAIN file.

OUTPUT RULES:
1. You MUST output ONLY a valid JSON object.
2. Do not use markdown blocks or backticks.
3. Escape newlines as \\n within strings.

JSON schema (strict):
{
  "title": "<60-char punchy viral title with 1-2 emojis>",
  "description": "<sections joined by \\n\\n — see below>",
  "tags": ["word1", "word2", "word3", "word4", "word5", "word6", "word7", "word8", "word9", "word10"]
}

Description sections — join every section with \\n\\n:
1. Headline hook that matches the video's exact energy/mood
2. 1-2 sentences describing exactly what happened based on the BRAIN file
3. One highly specific comment-driving question
4. Subscribe for more epic Minecraft moments 🚀
5. 10-15 hashtags separated by spaces
6. | Zen MetaBot\\nFollow for daily Minecraft videos 👀
"""

def generate_metadata_nvidia(video: VideoMeta, brain_text: str) -> dict:
    log.info(f"  🟢 NVIDIA Nemotron is generating metadata for {video.id}...")
    
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=CFG.NVIDIA_API_KEY,
    )
    
    user_prompt = f"Original Title: {video.old_title}\n\nHere is the video BRAIN file:\n\n{brain_text}"

    response = client.chat.completions.create(
        model=CFG.NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": _NVIDIA_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=CFG.NVIDIA_MAX_TOKENS,
        temperature=CFG.NVIDIA_TEMPERATURE,
        frequency_penalty=CFG.NVIDIA_FREQ_PENALTY,
        timeout=CFG.NVIDIA_API_TIMEOUT,
    )

    raw = (response.choices[0].message.content or response.choices[0].message.reasoning_content)
    if not raw:
        raise RuntimeError("Nemotron returned empty content.")

    return extract_json(raw)
