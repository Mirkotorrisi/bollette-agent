import os
from typing import Any, Dict, Optional

import requests

from logger_config import setup_logger

logger = setup_logger(__name__)

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"
# A Choice question accepts up to 255 options (TypeSafe docs).
MAX_CHOICE_OPTIONS = 255


class JevError(Exception):
    """Raised when the OpenRouter Decisions API returns an error or an unexpected payload."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def decide(state: Any, questions: Dict[str, Dict[str, Any]], session_id: Optional[str] = None,
           timeout: float = 30.0) -> Dict[str, Any]:
    """
    Ask Jev a set of independent typed questions about the same state.

    Args:
        state: Plain string, JSON object or JSON array describing the situation.
        questions: Map of question id -> question object (noul / choice / score).
        session_id: Optional id used by OpenRouter to group related requests in logs.

    Returns:
        The full Decisions response; typed answers are under `answers`, keyed by question id.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise JevError("OPENROUTER_API_KEY is not set")

    body: Dict[str, Any] = {
        "model": os.environ.get("JEV_MODEL", DEFAULT_MODEL),
        "state": state,
        "questions": questions,
    }
    if session_id:
        body["session_id"] = session_id[:256]

    try:
        response = requests.post(
            DECISIONS_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise JevError(f"Jev request failed: {e}") from e

    if response.status_code != 200:
        try:
            message = response.json().get("error", {}).get("message") or response.text
        except ValueError:
            message = response.text
        raise JevError(f"Jev API error: {message}", status_code=response.status_code)

    payload = response.json()
    answers = payload.get("answers")
    if not isinstance(answers, dict):
        raise JevError("Jev response has no answers")

    logger.info(f"Jev answered {len(answers)} questions with {payload.get('model')}, usage: {payload.get('usage')}")
    return payload
