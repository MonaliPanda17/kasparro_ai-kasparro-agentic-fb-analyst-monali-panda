from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

from openai import OpenAI


def _build_prompt(overview: Dict[str, Any], segments: Dict[str, Any], plan: Dict[str, Any]) -> str:
    return (
        "You are a performance marketing analyst.\n"
        "Summarize the current vs baseline performance and the top segment movers.\n"
        "Constraints: Only use numbers present in the provided JSON.\n"
        "Return a short narrative (<= 180 words) with 3 bullet points of key takeaways.\n\n"
        f"PLAN:\n{json.dumps(plan, indent=2)}\n\n"
        f"OVERVIEW:\n{json.dumps(overview, indent=2)}\n\n"
        f"SEGMENTS (truncated):\n{json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ['top_gainers','top_losers']} for k, v in segments.items()}, indent=2)}\n\n"
        "Write the narrative now."
    )


def generate_narrative(
    overview: Dict[str, Any],
    segments: Dict[str, Any],
    plan: Dict[str, Any],
    model: str = "gpt-4o-mini",
    timeout_s: int = 30,
) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    client = OpenAI(api_key=api_key, timeout=timeout_s)
    prompt = _build_prompt(overview, segments, plan)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise, concise marketing analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=350,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return None


