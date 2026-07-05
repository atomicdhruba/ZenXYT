import time
import os
from pathlib import Path
import google.generativeai as genai

from zenmetabot.config import CFG, log

BRAIN_PROMPT = """
You are a highly advanced Video Intelligence AI. 
I am providing you with a video file. Your task is to extract a "Brain File" that describes absolutely EVERYTHING about this video. 
Imagine another AI will read your output and needs to understand the video perfectly without ever seeing the video itself.

Provide your output EXACTLY in this format, with these sections. Be exhaustive and use timestamps (MM:SS) everywhere.

═══════════════════════════════════════════════
 ZENXYT BRAIN FILE
═══════════════════════════════════════════════

[OVERVIEW]
- Video Type: (Short or Long)
- Duration: (Length)
- Overall Tone: (e.g., Funny meme / Epic cinematic / Fail compilation / Spooky)
- Energy Level: (1-10)
- Target Audience: (e.g., Casual gamers, Hardcore Minecraft, Kids)

[FRAME-BY-FRAME TIMELINE]
(Describe what happens visually at every significant moment or scene change. Use format: MM:SS - MM:SS | Description)

[AUDIO & SFX TIMELINE]
(Describe the dialogue, music, and specific Sound Effects. Use format: MM:SS - MM:SS | Description)

[VISUAL ELEMENTS]
- Color Palette: 
- Text Overlays: (Quote any text that appears on screen and at what time)
- Memes/Effects: (e.g., Zoom effect, screen shake, green screen elements)
- Skin/Character: (Describe the main characters or skins)

[EMOTIONAL ARC]
(Map the emotions of the video across time, e.g. 00:00-00:05: Curiosity)

[KEY MOMENTS FOR METADATA]
- Hook moment: (The most engaging moment)
- Viral potential: (Why would this go viral?)
- Comparable trending formats: (What trend does this fit?)

[RAW TRANSCRIPT]
(If there is any speech or important on-screen text, list it here with timestamps. Otherwise, write 'None')
"""

def extract_brain(video_id: str, video_path: str) -> str:
    """
    Uploads the video to Gemini, waits for processing, extracts the brain, 
    saves to disk, and returns the path to the brain.txt.
    """
    brain_file = Path(CFG.BRAIN_DIR) / f"{video_id}_brain.txt"
    
    if not CFG.FORCE_REWATCH and brain_file.exists():
        log.info(f"  🧠 Brain file already exists for {video_id}. Skipping extraction.")
        return str(brain_file)

    if not CFG.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Cannot extract brain.")

    genai.configure(api_key=CFG.GEMINI_API_KEY)

    log.info(f"  📤 Uploading {video_path} to Gemini for brain extraction...")
    video_file = genai.upload_file(path=video_path)
    
    log.info(f"  ⏳ Waiting for Gemini to process the video (URI: {video_file.uri})...")
    # Wait for the video to be processed
    while video_file.state.name == "PROCESSING":
        time.sleep(5)
        video_file = genai.get_file(video_file.name)
        
    if video_file.state.name == "FAILED":
        raise RuntimeError("Gemini failed to process the video.")
        
    log.info(f"  🧠 Generating deep brain analysis for {video_id}...")
    model = genai.GenerativeModel(model_name=CFG.GEMINI_MODEL)
    
    response = model.generate_content([video_file, BRAIN_PROMPT], request_options={"timeout": 600})
    
    brain_text = response.text
    brain_file.write_text(brain_text, encoding="utf-8")
    
    log.info(f"  ✅ Brain file saved to {brain_file}")
    
    # Cleanup uploaded file to save quota
    try:
        genai.delete_file(video_file.name)
        log.debug(f"  Deleted remote file {video_file.name}")
    except Exception as e:
        log.warning(f"  Failed to delete remote file: {e}")
        
    return str(brain_file)
