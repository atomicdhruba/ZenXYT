import google.generativeai as genai
from zenmetabot.config import CFG, log
from zenmetabot.utils import extract_json, call_gemini_with_retry
from zenmetabot.models import VideoMeta

_GEMINI_SYSTEM_PROMPT = """\
You are an expert YouTube strategist for the channel Zen MetaBot (Minecraft content).
I am providing you with the BRAIN file of a video, containing every detail you need.

OUTPUT RULES — follow every one, no exceptions:
1. Output ONLY a single raw JSON object. No markdown, no backticks, no commentary before or after.
2. Start your reply with { and end with }. Nothing else outside the braces.
3. Use \\n (backslash + n) for line-breaks inside JSON string values. NEVER embed a real newline inside a string.
4. Only these backslash escapes are allowed inside strings: \\\\ \\n \\t \\r \\" — no others.

JSON schema (strict):
{
  "title":       "<60-char punchy viral title with 1-2 emojis>",
  "description": "<sections joined by \\n\\n — see below>",
  "tags":        ["word1", "word2", ...]   // exactly 10-15 plain words, no # symbols
}

Description sections — join every section with \\n\\n:
1. Headline hook that matches the video's exact energy/mood
2. 1-2 sentences describing exactly what happened based on the BRAIN file
3. One highly specific comment-driving question
4. Subscribe for more epic Minecraft moments 🚀
5. 10-15 hashtags separated by spaces
6. | Zen MetaBot\\nFollow for daily Minecraft videos 👀
"""

def generate_metadata_gemini(video: VideoMeta, brain_text: str) -> dict:
    log.info(f"  🔵 Gemini is generating metadata for {video.id}...")
    
    genai.configure(api_key=CFG.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=CFG.GEMINI_MODEL,
        system_instruction=_GEMINI_SYSTEM_PROMPT
    )
    
    user_prompt = f"Original Title: {video.old_title}\n\nHere is the video BRAIN file:\n\n{brain_text}"

    response = call_gemini_with_retry(
        model.generate_content,
        user_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json"
        ),
        request_options={"timeout": 120}
    )

    if not response.text:
        raise RuntimeError("Gemini returned empty content.")

    return extract_json(response.text)
