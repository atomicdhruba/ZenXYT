import json
import re
import time
from zenmetabot.config import log

def call_gemini_with_retry(func, *args, **kwargs):
    """
    Wraps a Gemini API call to automatically catch 429 Quota Exceeded errors
    and sleep/retry, allowing the free tier to cool down without crashing.
    """
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "exhausted" in error_str or "503" in error_str:
                sleep_time = 30 * (attempt + 1)
                log.warning(f"  ⏳ Gemini API Quota/Limit hit! Sleeping {sleep_time}s before retrying (Attempt {attempt+1}/{max_retries})...")
                time.sleep(sleep_time)
            else:
                raise e
    raise RuntimeError("Exceeded maximum retries for Gemini API due to quota limits.")

def _sanitise_json_string(raw: str) -> str:
    """
    Fix common AI JSON mistakes:
    - Literal backslash-n (\n) inside string values that are not valid escapes
    - Stray control characters
    """
    VALID_ESCAPES = set('"\\bfnrtu')
    out, i, in_str = [], 0, False
    while i < len(raw):
        ch = raw[i]
        if ch == '"'  and (i == 0 or raw[i-1] != '\\'):
            in_str = not in_str
            out.append(ch)
        elif in_str and ch == '\\' and i + 1 < len(raw):
            nxt = raw[i + 1]
            if nxt in VALID_ESCAPES:
                out.append(ch)          # keep valid escape
            else:
                out.append(' ')        # replace bad backslash with space
                i += 1
        else:
            out.append(ch)
        i += 1
    return ''.join(out)

def extract_json(text: str) -> dict:
    """
    Robustly extract the first complete JSON object from raw AI output.
    """
    text = text.replace("```json", "").replace("```", "").strip()

    start = text.rfind('{')          
    if start == -1:
        start = text.find('{')
    if start == -1:
        raise ValueError(f"No JSON object found in AI response.\nRaw (first 300 chars):\n{text[:300]}")

    depth = end_idx = 0
    for i, ch in enumerate(text[start:], start):
        if   ch == '{': depth += 1
        elif ch == '}': depth -= 1
        if depth == 0:
            end_idx = i + 1
            break

    if not end_idx:
        raise ValueError("Unbalanced braces in AI response.")

    candidate = text[start:end_idx]
    candidate = _sanitise_json_string(candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        candidate2 = re.sub(r'(?<!\\)\n', ' ', candidate)
        # Fallback for Nemotron missing quotes around keys (e.g., {title:" -> {"title":")
        candidate2 = re.sub(r'{\s*([a-zA-Z0-9_]+)\s*:', r'{"\1":', candidate2)
        candidate2 = re.sub(r',\s*([a-zA-Z0-9_]+)\s*:', r',"\1":', candidate2)
        
        try:
            return json.loads(candidate2)
        except json.JSONDecodeError:
            raise ValueError(
                f"JSON parse failed: {e}\n"
                f"Sanitised candidate (first 400 chars):\n{candidate[:400]}"
            )
