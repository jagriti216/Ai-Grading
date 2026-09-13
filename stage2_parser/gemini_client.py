import json
import os
import random
import re
import time
from typing import Callable, List, Optional

import requests
from dotenv import load_dotenv

from gemini_shared import clear_gemini_disabled, disable_gemini, gemini_disabled_reason

# Try loading from the root .env first
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(root_env)
else:
    # Fallback to stage1_extraction/.env
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "stage1_extraction", ".env"))
    # Generic load_dotenv searching current & parent directories
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _gemini_url() -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to the root .env file.")
    return (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )


def _extract_retry_delay_seconds(response: requests.Response, response_text: str) -> Optional[float]:
    header_delay = response.headers.get("Retry-After")
    if header_delay:
        try:
            return max(float(header_delay), 1.0)
        except ValueError:
            pass

    try:
        payload = response.json()
        details = payload.get("error", {}).get("details", [])
        for item in details:
            delay = item.get("retryDelay")
            if delay:
                match = re.search(r"(\d+(?:\.\d+)?)s", delay)
                if match:
                    return max(float(match.group(1)), 1.0)
    except Exception:
        pass

    match = re.search(r"retry in\s+(\d+(?:\.\d+)?)s", response_text, flags=re.IGNORECASE)
    if match:
        return max(float(match.group(1)), 1.0)
    return None


def _is_hard_quota_exhausted(response_text: str) -> bool:
    lowered = response_text.lower()
    return "quota exceeded" in lowered and ("perday" in lowered or "limit: 0" in lowered)


def call_gemini_json_array(
    prompt: str,
    fallback_builder: Optional[Callable[[], List[dict]]] = None,
    max_retries: int = 4,
    timeout_seconds: int = 90,
) -> List[dict]:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    last_error = None

    disabled_reason = gemini_disabled_reason()
    if disabled_reason is not None:
        if fallback_builder is not None:
            return fallback_builder()
        raise RuntimeError(f"Gemini disabled: {disabled_reason}")

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(_gemini_url(), json=payload, timeout=timeout_seconds)
        except requests.RequestException as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            time.sleep(min(2 ** attempt, 10) + random.uniform(0.1, 0.6))
            continue

        if response.status_code == 200:
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = re.sub(r"```json|```", "", text).strip()
            return json.loads(text)

        response_text = response.text
        transient = response.status_code in {429, 500, 502, 503, 504}
        hard_quota = response.status_code == 429 and _is_hard_quota_exhausted(response_text)

        if response.status_code in {401, 403} or hard_quota:
            retry_after = _extract_retry_delay_seconds(response, response_text)
            disable_gemini(
                reason=f"HTTP {response.status_code}: {response_text[:200]}",
                permanent=True,
                retry_after_seconds=int(retry_after) if retry_after else None,
            )
            if fallback_builder is not None:
                return fallback_builder()
            raise RuntimeError(f"Gemini disabled after hard failure: HTTP {response.status_code}")

        if transient and not hard_quota and attempt < max_retries:
            delay = _extract_retry_delay_seconds(response, response_text)
            if delay is None:
                delay = min(2 ** attempt, 20) + random.uniform(0.1, 0.7)
            time.sleep(delay)
            continue

        last_error = RuntimeError(f"Gemini error {response.status_code}: {response_text}")
        break

    if fallback_builder is not None:
        return fallback_builder()

    if last_error:
        raise last_error
    raise RuntimeError("Gemini request failed with unknown error")


def split_blocks_by_question(text: str) -> List[tuple[int, str]]:
    pattern = re.compile(r"(?im)^\s*(?:q\s*)?(\d{1,3})\s*[\).:-]\s*(.*)$")
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    blocks: List[tuple[int, str]] = []
    for idx, match in enumerate(matches):
        q_num = int(match.group(1))
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        blocks.append((q_num, block))
    return blocks


def parse_marks_from_text(text: str) -> Optional[int]:
    expr = re.search(r"(\d+(?:\s*\+\s*\d+)+)\s*marks?", text, flags=re.IGNORECASE)
    if expr:
        numbers = [int(n) for n in re.findall(r"\d+", expr.group(1))]
        return sum(numbers)

    single = re.search(r"\((\d+)\s*marks?\)", text, flags=re.IGNORECASE)
    if single:
        return int(single.group(1))

    fallback = re.search(r"\b(\d+)\s*marks?\b", text, flags=re.IGNORECASE)
    if fallback:
        return int(fallback.group(1))
    return None