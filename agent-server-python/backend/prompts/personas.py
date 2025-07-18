"""
prompts/personas.py
===================

Reads persona definitions from personas.yaml and exposes the same public
symbols as the original hard-coded version:

    RESPONSE_STYLE
    MENTAL_PROMPT,  PHYSICAL_PROMPT,  SPIRITUAL_PROMPT,  VOCATIONAL_PROMPT,
    ENVIRONMENTAL_PROMPT,  FINANCIAL_PROMPT,  SOCIAL_PROMPT,  INTELLECTUAL_PROMPT
    MENTAL_FULL,    PHYSICAL_FULL,    … (eight *_FULL variables)
    PERSONA_PROMPTS   – dict with persona keys plus "main"

"""

from __future__ import annotations
from pathlib import Path
from textwrap import dedent
import yaml

# ---------------------------------------------------------------------------
# Locate & load YAML
# ---------------------------------------------------------------------------

_YAML_PATH = Path(__file__).with_name("personas.yaml")

_DATA: dict
try:
    _DATA = yaml.safe_load(_YAML_PATH.read_text(encoding="utf-8"))
except FileNotFoundError as err:
    raise FileNotFoundError(
        f"[personas] Could not find {_YAML_PATH}. "
        "Make sure personas.yaml lives beside personas.py."
    ) from err

# ---------------------------------------------------------------------------
# Shared guidance blocks
# ---------------------------------------------------------------------------

RESPONSE_STYLE: str = dedent(_DATA["response_style"]).strip()
_BOUNDARIES_COMMON: str = dedent(_DATA["boundaries_common"]).strip()
_PROFESSIONAL_BOUNDARIES: str = dedent(_DATA["professional_boundaries"]).strip()
_USER_CONTEXT_HANDLING: str = dedent(_DATA["user_context_handling"]).strip()
_CONVERSATION_CONTINUITY: str = dedent(_DATA["conversation_continuity"]).strip()
_PERSONA_SWITCHING: str = dedent(_DATA["persona_switching"]).strip()
_SAFETY_ESCALATION: str = dedent(_DATA["safety_escalation"]).strip()
_CRISIS_RESOURCES: str = dedent(_DATA["crisis_resources"]).strip()

# Combine all style/guidance sections into one for easy persona prompt merging
FULL_RESPONSE_STYLE = "\n\n".join([
    RESPONSE_STYLE,
    "**Boundaries Common**\n" + _BOUNDARIES_COMMON,
    "**Professional Boundaries**\n" + _PROFESSIONAL_BOUNDARIES,
    "**User Context Handling**\n" + _USER_CONTEXT_HANDLING,
    "**Conversation Continuity**\n" + _CONVERSATION_CONTINUITY,
    "**Persona Switching**\n" + _PERSONA_SWITCHING,
    "**Safety Escalation**\n" + _SAFETY_ESCALATION,
    "**Crisis Resources**\n" + _CRISIS_RESOURCES,
])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Whether a persona should number its focus list (customize here as needed)
_NUMBERED_FOCUS = {"mental"}

def _build_focus_lines(key: str, items: list[str]) -> list[str]:
    """Return formatted primary-focus lines – numbered or bulleted."""
    if key in _NUMBERED_FOCUS:
        return [f"{i + 1}. {item}" for i, item in enumerate(items)]
    return [f"• {item}" for item in items]

def _compose_prompt(key: str, p: dict) -> str:
    """Compose the persona prompt text (without full response style)."""
    sections: list[str] = [
        f"You are the {p['display_name']}.",
        "",
        f"**Mission** – {p['mission']}",
        f"**Tone & Voice**\n{dedent(p['tone_voice']).strip()}",
        "**Primary Focus Areas**",
        *_build_focus_lines(key, p["primary_focus"]),
    ]
    # Persona-specific boundary additions (if any)
    if p.get("extra_boundaries"):
        sections.append(dedent(p["extra_boundaries"]).strip())
    # Join with blank lines, remove empties
    return "\n\n".join(filter(None, sections))

# ---------------------------------------------------------------------------
# Build all personas
# ---------------------------------------------------------------------------

_PERSONA_PROMPTS_RAW: dict[str, str] = {
    k: _compose_prompt(k, v) for k, v in _DATA["personas"].items()
}

# Expose individual raw-prompt constants
MENTAL_PROMPT        = _PERSONA_PROMPTS_RAW["mental"]
PHYSICAL_PROMPT      = _PERSONA_PROMPTS_RAW["physical"]
SPIRITUAL_PROMPT     = _PERSONA_PROMPTS_RAW["spiritual"]
VOCATIONAL_PROMPT    = _PERSONA_PROMPTS_RAW["vocational"]
ENVIRONMENTAL_PROMPT = _PERSONA_PROMPTS_RAW["environmental"]
FINANCIAL_PROMPT     = _PERSONA_PROMPTS_RAW["financial"]
SOCIAL_PROMPT        = _PERSONA_PROMPTS_RAW["social"]
INTELLECTUAL_PROMPT  = _PERSONA_PROMPTS_RAW["intellectual"]

# Combine with FULL_RESPONSE_STYLE for final persona prompts
MENTAL_FULL        = f"{MENTAL_PROMPT}\n{FULL_RESPONSE_STYLE}"
PHYSICAL_FULL      = f"{PHYSICAL_PROMPT}\n{FULL_RESPONSE_STYLE}"
SPIRITUAL_FULL     = f"{SPIRITUAL_PROMPT}\n{FULL_RESPONSE_STYLE}"
VOCATIONAL_FULL    = f"{VOCATIONAL_PROMPT}\n{FULL_RESPONSE_STYLE}"
ENVIRONMENTAL_FULL = f"{ENVIRONMENTAL_PROMPT}\n{FULL_RESPONSE_STYLE}"
FINANCIAL_FULL     = f"{FINANCIAL_PROMPT}\n{FULL_RESPONSE_STYLE}"
SOCIAL_FULL        = f"{SOCIAL_PROMPT}\n{FULL_RESPONSE_STYLE}"
INTELLECTUAL_FULL  = f"{INTELLECTUAL_PROMPT}\n{FULL_RESPONSE_STYLE}"

# Public dict identical to the original
PERSONA_PROMPTS: dict[str, str] = {
    "mental": MENTAL_FULL,
    "physical": PHYSICAL_FULL,
    "spiritual": SPIRITUAL_FULL,
    "vocational": VOCATIONAL_FULL,
    "environmental": ENVIRONMENTAL_FULL,
    "financial": FINANCIAL_FULL,
    "social": SOCIAL_FULL,
    "intellectual": INTELLECTUAL_FULL,
    "main": (
        "You are **Tabi**, a compassionate, holistic wellness companion.\n"
        "Listen closely, determine which of the eight wellness dimensions (mental, physical, spiritual, vocational, environmental, financial, social, intellectual) best fits the user's needs, and respond naturally using that coach’s empathetic style.\n"
        "If the dimension is unclear, kindly ask a clarifying question first.\n"
        "Always reply warmly, practically, and conversationally, just like a caring friend would.\n\n"
        f"{FULL_RESPONSE_STYLE}"
    ),
}

# ---------------------------------------------------------------------------
# Clean up internal names from module namespace
# ---------------------------------------------------------------------------

del yaml, Path, dedent, _DATA, _YAML_PATH, _compose_prompt, _build_focus_lines
del _PERSONA_PROMPTS_RAW, _BOUNDARIES_COMMON, _PROFESSIONAL_BOUNDARIES
del _USER_CONTEXT_HANDLING, _CONVERSATION_CONTINUITY, _PERSONA_SWITCHING
del _SAFETY_ESCALATION, _CRISIS_RESOURCES, _NUMBERED_FOCUS
