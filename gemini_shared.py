import json
import time
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent
DISABLED_FILE = PROJECT_ROOT / "outputs" / ".gemini_disabled.json"


def _read_disabled_state() -> Optional[dict]:
    if not DISABLED_FILE.exists():
        return None

    try:
        return json.loads(DISABLED_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"reason": "disabled"}


def gemini_disabled_reason() -> Optional[str]:
    state = _read_disabled_state()
    if not state:
        return None

    disabled_until = state.get("disabled_until")
    if disabled_until and time.time() > float(disabled_until):
        clear_gemini_disabled()
        return None

    return state.get("reason") or "disabled"


def disable_gemini(reason: str, permanent: bool = True, retry_after_seconds: Optional[int] = None) -> None:
    DISABLED_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "reason": reason,
        "permanent": permanent,
        "disabled_at": time.time(),
    }
    if retry_after_seconds is not None:
        state["disabled_until"] = time.time() + retry_after_seconds

    DISABLED_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def clear_gemini_disabled() -> None:
    if DISABLED_FILE.exists():
        try:
            DISABLED_FILE.unlink()
        except Exception:
            pass