"""
Icon loader utility for Olympics plugin.

Provides functions to load sport icons and Olympics branding
for use in renderers.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)

# Asset paths
ASSETS_DIR = Path(__file__).parent.parent / "assets"
SPORT_ICONS_DIR = ASSETS_DIR / "sport_icons"
BRANDING_DIR = ASSETS_DIR / "branding"

# Icon cache
_icon_cache: Dict[str, Image.Image] = {}
_branding_cache: Dict[str, Image.Image] = {}

# Sport name normalization map
SPORT_NAME_MAP = {
    # Official names to icon names
    "alpine skiing": "alpine_skiing",
    "cross-country skiing": "cross_country_skiing",
    "cross country skiing": "cross_country_skiing",
    "biathlon": "biathlon",
    "ski jumping": "ski_jumping",
    "nordic combined": "nordic_combined",
    "freestyle skiing": "freestyle_skiing",
    "snowboard": "snowboard",
    "snowboarding": "snowboard",
    "figure skating": "figure_skating",
    "speed skating": "speed_skating",
    "short track speed skating": "short_track_speed_skating",
    "short track": "short_track_speed_skating",
    "ice hockey": "ice_hockey",
    "hockey": "ice_hockey",
    "curling": "curling",
    "bobsleigh": "bobsleigh",
    "bobsled": "bobsleigh",
    "luge": "luge",
    "skeleton": "skeleton",
}


def normalize_sport_name(sport: str) -> str:
    """Convert sport name to icon filename."""
    sport_lower = sport.lower().strip()
    return SPORT_NAME_MAP.get(sport_lower, "default")


def get_sport_icon(sport: str, size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
    """
    Get icon for a sport.

    Args:
        sport: Sport name (e.g., "Alpine Skiing", "Ice Hockey")
        size: Optional target size (width, height) to resize icon

    Returns:
        PIL Image of the icon, or None if not found
    """
    icon_name = normalize_sport_name(sport)
    cache_key = f"{icon_name}_{size}" if size else icon_name

    # Check cache
    if cache_key in _icon_cache:
        return _icon_cache[cache_key].copy()

    # Try to load icon
    icon_path = SPORT_ICONS_DIR / f"{icon_name}.png"
    if not icon_path.exists():
        # Fall back to default
        icon_path = SPORT_ICONS_DIR / "default.png"
        if not icon_path.exists():
            return None

    try:
        with Image.open(icon_path) as img:
            icon = img.convert("RGB")
            if size and size != icon.size:
                icon = icon.resize(size, Image.Resampling.NEAREST)
            icon.load()  # Force read all pixel data into memory

        _icon_cache[cache_key] = icon
        return icon.copy()

    except Exception as e:
        logger.debug(f"Error loading sport icon {icon_name}: {e}")
        return None


def get_olympics_rings(size: Tuple[int, int] = (24, 12)) -> Image.Image:
    """
    Get the Olympic rings logo.

    Args:
        size: Target size (width, height)

    Returns:
        PIL Image of the Olympic rings
    """
    cache_key = f"rings_{size}"

    if cache_key in _branding_cache:
        return _branding_cache[cache_key].copy()

    # Try to load from file first
    rings_path = BRANDING_DIR / "olympic_rings.png"
    if rings_path.exists():
        try:
            with Image.open(rings_path) as img:
                rings = img.convert("RGB")
                if size != rings.size:
                    rings = rings.resize(size, Image.Resampling.LANCZOS)
                rings.load()  # Force read all pixel data into memory
            _branding_cache[cache_key] = rings
            return rings.copy()
        except Exception as e:
            logger.debug(f"Error loading rings from file: {e}")

    # Generate programmatically
    rings = _generate_olympic_rings(size)
    _branding_cache[cache_key] = rings
    return rings.copy()


def _generate_olympic_rings(size: Tuple[int, int]) -> Image.Image:
    """Generate Olympic rings programmatically."""
    from PIL import ImageDraw

    width, height = size
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Ring colors (top: blue, black, red; bottom: yellow, green)
    colors = [
        (0, 129, 188),    # Blue
        (0, 0, 0),        # Black (will use white for visibility)
        (238, 51, 78),    # Red
        (252, 177, 49),   # Yellow
        (0, 157, 87),     # Green
    ]

    # For LED display, use white instead of black for visibility
    colors[1] = (200, 200, 200)

    # Calculate ring dimensions based on size
    ring_diameter = min(width // 4, height // 2)
    ring_radius = ring_diameter // 2
    line_width = max(1, ring_radius // 3)

    # Ring positions (5 interlocking rings)
    # Top row: 3 rings, bottom row: 2 rings offset
    y_top = height // 4
    y_bottom = height * 3 // 5

    spacing = width // 5

    positions = [
        (spacing, y_top),           # Blue
        (spacing * 2, y_top),       # White (black)
        (spacing * 3, y_top),       # Red
        (spacing + spacing // 2, y_bottom),      # Yellow
        (spacing * 2 + spacing // 2, y_bottom),  # Green
    ]

    # Draw rings
    for i, (cx, cy) in enumerate(positions):
        color = colors[i]
        bbox = [
            cx - ring_radius,
            cy - ring_radius,
            cx + ring_radius,
            cy + ring_radius
        ]
        draw.arc(bbox, 0, 360, fill=color, width=line_width)

    return img


# Medal icon cache
_medal_icon_cache: Dict[str, Image.Image] = {}


def get_medal_icon(medal_type: str, size: Tuple[int, int] = (10, 10)) -> Image.Image:
    """
    Get a medal icon (gold, silver, bronze).

    Args:
        medal_type: "gold", "silver", or "bronze"
        size: Target size

    Returns:
        PIL Image of the medal
    """
    cache_key = f"{medal_type.lower()}_{size}"
    if cache_key in _medal_icon_cache:
        return _medal_icon_cache[cache_key].copy()

    from PIL import ImageDraw

    colors = {
        "gold": (255, 215, 0),
        "silver": (192, 192, 192),
        "bronze": (205, 127, 50),
    }

    color = colors.get(medal_type.lower(), colors["gold"])

    img = Image.new("RGB", size, (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw medal as circle
    margin = 1
    draw.ellipse(
        [margin, margin, size[0] - margin - 1, size[1] - margin - 1],
        fill=color
    )

    # Add shine effect
    highlight = tuple(min(255, c + 50) for c in color)
    draw.arc(
        [margin + 1, margin + 1, size[0] - margin - 2, size[1] - margin - 2],
        200, 340,
        fill=highlight
    )

    _medal_icon_cache[cache_key] = img
    return img.copy()


def load_olympics_logo(size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
    """
    Load the Olympics logo image.

    Args:
        size: Optional target size (width, height) to resize logo

    Returns:
        PIL Image of the Olympics logo, or None if not found
    """
    cache_key = f"olympics_logo_{size}" if size else "olympics_logo"

    if cache_key in _branding_cache:
        return _branding_cache[cache_key].copy()

    # Try common logo paths
    # Note: ASSETS_DIR.parent == Path(__file__).parent.parent (plugin root)
    logo_paths = [
        BRANDING_DIR / "olympics_logo.png",
        ASSETS_DIR.parent / "olympics-logo.png",
    ]

    for logo_path in logo_paths:
        if logo_path.exists():
            try:
                with Image.open(logo_path) as img:
                    logo = img.convert("RGB")
                    if size and size != logo.size:
                        logo = logo.resize(size, Image.Resampling.LANCZOS)
                    logo.load()  # Force read all pixel data into memory
                _branding_cache[cache_key] = logo
                return logo.copy()
            except Exception as e:
                logger.debug(f"Error loading Olympics logo from {logo_path}: {e}")

    # Fall back to Olympic rings if logo not found
    logger.debug("Olympics logo not found, falling back to rings")
    return get_olympics_rings(size or (24, 12))


def clear_cache() -> None:
    """Clear all cached icons."""
    _icon_cache.clear()
    _branding_cache.clear()
    _medal_icon_cache.clear()
