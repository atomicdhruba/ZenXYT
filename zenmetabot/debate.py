import json
from zenmetabot.config import CFG, log
from zenmetabot.models import VideoMeta
from zenmetabot.ai_nvidia import generate_metadata_nvidia
from zenmetabot.ai_gemini import generate_metadata_gemini
import google.generativeai as genai
from zenmetabot.utils import extract_json

_JUDGE_PROMPT = """\
You are the Ultimate SEO Judge for the Zen MetaBot YouTube channel (Minecraft content).
You will receive:
1. The original video title.
2. A Draft from NVIDIA.
3. A Draft from Gemini.
4. (Optional) Critiques from both.

Your job is to merge the absolute BEST parts of both drafts into the ultimate viral metadata.
Follow the exact same JSON schema and rules as before:
{
  "title":       "<60-char punchy viral title with 1-2 emojis>",
  "description": "<sections joined by \\n\\n>",
  "tags":        ["word1", "word2", ...]
}
"""

_SCORE_PROMPT = """\
You are an SEO Analyst. Rate this metadata on a scale of 0-100 for virality and reach.
Output ONLY a JSON object:
{
  "total_score": 87,
  "title_power": 9,
  "description_seo": 8,
  "tag_coverage": 9,
  "emotional_hook": 8,
  "global_reach": 9
}
"""

def get_seo_score(metadata: dict) -> dict:
    genai.configure(api_key=CFG.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=CFG.GEMINI_MODEL, system_instruction=_SCORE_PROMPT)
    prompt = f"Metadata to score:\nTitle: {metadata.get('title')}\nDescription: {metadata.get('description')}\nTags: {metadata.get('tags')}"
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.1, response_mime_type="application/json")
    )
    try:
        return extract_json(response.text)
    except:
        return {"total_score": 0}

def run_debate(video: VideoMeta, brain_text: str, gui_callback=None) -> dict:
    def notify(msg):
        log.info(msg)
        if gui_callback:
            gui_callback(msg)

    notify(f"  ⚔️ DEBATE MODE INITIATED for {video.id}")
    
    notify("  Round 1: Drafting...")
    nvidia_draft = generate_metadata_nvidia(video, brain_text)
    notify("  🟢 NVIDIA Draft Completed.")
    
    gemini_draft = generate_metadata_gemini(video, brain_text)
    notify("  🔵 Gemini Draft Completed.")
    
    notify("  Round 2: Skipping direct cross-critique to save time, jumping to Final Merge...")
    # To save time and API costs, we pass both drafts directly to the Judge.
    # In a fully expanded version, we would do the cross-critique step here.
    
    notify("  Round 3: Final Merge (Judge Gemini)...")
    genai.configure(api_key=CFG.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=CFG.GEMINI_MODEL, system_instruction=_JUDGE_PROMPT)
    
    user_prompt = f"Original Title: {video.old_title}\n\nNVIDIA Draft:\n{json.dumps(nvidia_draft, indent=2)}\n\nGemini Draft:\n{json.dumps(gemini_draft, indent=2)}"
    
    response = model.generate_content(
        user_prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.3, response_mime_type="application/json")
    )
    
    final_meta = extract_json(response.text)
    notify("  🏆 Final Merge Completed.")
    
    return final_meta
