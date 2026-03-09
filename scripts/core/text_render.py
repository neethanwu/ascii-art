"""FIGlet text-to-ASCII rendering."""

import pyfiglet

AVAILABLE_FONTS = [
    "standard", "doom", "banner", "slant", "big", "small",
    "block", "lean", "mini", "script", "shadow", "speed",
    "ansi_shadow", "ansi_regular",
]

MAX_TEXT_LENGTH = 100


def render_text(text: str, font: str = "standard") -> str:
    """
    Render text as ASCII art banner using FIGlet.

    Args:
        text: Input text (max 100 chars)
        font: FIGlet font name

    Returns:
        Multi-line ASCII art string
    """
    if not text:
        raise ValueError("No text provided")

    # Truncate long text
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    # Validate font
    if font not in AVAILABLE_FONTS:
        font = "standard"

    try:
        result = pyfiglet.figlet_format(text, font=font)
    except pyfiglet.FontNotFound:
        result = pyfiglet.figlet_format(text, font="standard")

    return result.rstrip("\n")
