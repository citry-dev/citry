from dataclasses import dataclass


@dataclass
class ThemeData:
    accent: str
    """Accent color for the board, used for highlighting and buttons."""
