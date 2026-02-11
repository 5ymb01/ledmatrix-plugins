#!/usr/bin/env python3
"""
Generate simple sport icons for the Olympics plugin.

Creates 12x12 pixel icons for winter sports, suitable for LED matrix display.
"""

from pathlib import Path
from PIL import Image, ImageDraw

# Output directory
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "assets" / "sport_icons"

# Icon size
ICON_SIZE = (12, 12)

# Colors
WHITE = (255, 255, 255)
CYAN = (0, 200, 255)
BLUE = (50, 100, 200)
SILVER = (180, 180, 180)
BROWN = (139, 90, 43)
ORANGE = (255, 140, 0)
RED = (255, 50, 50)
GREEN = (50, 200, 50)
YELLOW = (255, 215, 0)
BLACK = (0, 0, 0)


def create_icon(name: str, draw_func) -> None:
    """Create and save an icon."""
    img = Image.new('RGB', ICON_SIZE, BLACK)
    draw = ImageDraw.Draw(img)
    draw_func(draw)

    output_path = OUTPUT_DIR / f"{name}.png"
    img.save(output_path, 'PNG')
    print(f"  Created {name}.png")


def draw_alpine_skiing(draw):
    """Downhill skier silhouette."""
    # Skier body (diagonal pose)
    draw.line([(3, 2), (8, 7)], fill=CYAN, width=1)  # Body
    draw.line([(6, 4), (9, 2)], fill=CYAN, width=1)  # Arm
    draw.line([(7, 6), (10, 9)], fill=CYAN, width=1)  # Leg
    draw.line([(7, 6), (4, 9)], fill=CYAN, width=1)  # Other leg
    # Skis
    draw.line([(2, 10), (11, 10)], fill=WHITE, width=1)
    # Head
    draw.ellipse([(2, 1), (4, 3)], fill=CYAN)


def draw_cross_country(draw):
    """Cross-country skier."""
    # Skier (upright pose)
    draw.ellipse([(5, 1), (7, 3)], fill=CYAN)  # Head
    draw.line([(6, 3), (6, 7)], fill=CYAN, width=1)  # Body
    draw.line([(6, 5), (3, 3)], fill=CYAN, width=1)  # Arm back
    draw.line([(6, 5), (9, 3)], fill=CYAN, width=1)  # Arm front
    draw.line([(6, 7), (4, 10)], fill=CYAN, width=1)  # Leg
    draw.line([(6, 7), (8, 10)], fill=CYAN, width=1)  # Other leg
    # Skis
    draw.line([(1, 11), (6, 11)], fill=WHITE, width=1)
    draw.line([(6, 11), (11, 11)], fill=WHITE, width=1)


def draw_biathlon(draw):
    """Biathlon - skier with rifle."""
    # Similar to cross-country but with target
    draw.ellipse([(4, 1), (6, 3)], fill=CYAN)  # Head
    draw.line([(5, 3), (5, 6)], fill=CYAN, width=1)  # Body
    # Target circles
    draw.ellipse([(8, 3), (11, 6)], outline=WHITE)
    draw.ellipse([(9, 4), (10, 5)], fill=RED)
    # Skis
    draw.line([(2, 10), (8, 10)], fill=WHITE, width=1)


def draw_ski_jumping(draw):
    """Ski jumper in flight."""
    # V-style jumper
    draw.line([(2, 5), (6, 3)], fill=CYAN, width=1)  # Body
    draw.ellipse([(1, 4), (3, 6)], fill=CYAN)  # Head
    # Skis in V
    draw.line([(5, 2), (10, 1)], fill=WHITE, width=1)
    draw.line([(5, 4), (10, 5)], fill=WHITE, width=1)


def draw_nordic_combined(draw):
    """Nordic combined - jump + ski."""
    # Combine elements
    draw.line([(1, 3), (5, 1)], fill=WHITE, width=1)  # Jump hill
    draw.ellipse([(5, 1), (7, 3)], fill=CYAN)  # Jumper
    # Ski trail
    draw.line([(2, 8), (10, 8)], fill=WHITE, width=1)
    draw.ellipse([(8, 6), (10, 8)], fill=CYAN)  # Skier


def draw_freestyle_skiing(draw):
    """Freestyle skier doing trick."""
    # Skier upside down
    draw.ellipse([(5, 7), (7, 9)], fill=CYAN)  # Head (bottom)
    draw.line([(6, 5), (6, 7)], fill=CYAN, width=1)  # Body
    draw.line([(6, 3), (4, 1)], fill=WHITE, width=1)  # Ski
    draw.line([(6, 3), (8, 1)], fill=WHITE, width=1)  # Other ski
    # Action lines
    draw.line([(2, 4), (4, 4)], fill=YELLOW, width=1)


def draw_snowboard(draw):
    """Snowboarder."""
    # Rider
    draw.ellipse([(4, 2), (6, 4)], fill=CYAN)  # Head
    draw.line([(5, 4), (5, 7)], fill=CYAN, width=1)  # Body
    # Board
    draw.rectangle([(2, 8), (9, 10)], fill=ORANGE)


def draw_figure_skating(draw):
    """Figure skater."""
    # Dancer pose
    draw.ellipse([(5, 1), (7, 3)], fill=CYAN)  # Head
    draw.line([(6, 3), (6, 6)], fill=CYAN, width=1)  # Body
    draw.line([(6, 4), (3, 2)], fill=CYAN, width=1)  # Arm up
    draw.line([(6, 4), (9, 4)], fill=CYAN, width=1)  # Arm out
    draw.line([(6, 6), (4, 9)], fill=CYAN, width=1)  # Leg
    draw.line([(6, 6), (9, 8)], fill=CYAN, width=1)  # Leg extended
    # Sparkle
    draw.point((2, 3), fill=YELLOW)
    draw.point((10, 2), fill=YELLOW)


def draw_speed_skating(draw):
    """Speed skater."""
    # Crouched position
    draw.ellipse([(2, 3), (4, 5)], fill=CYAN)  # Head
    draw.line([(4, 4), (8, 6)], fill=CYAN, width=2)  # Body (horizontal)
    draw.line([(8, 6), (10, 4)], fill=CYAN, width=1)  # Arm back
    draw.line([(7, 6), (4, 9)], fill=CYAN, width=1)  # Leg
    # Ice
    draw.line([(1, 10), (11, 10)], fill=WHITE, width=1)


def draw_short_track(draw):
    """Short track skater."""
    # Similar to speed skating, more compact
    draw.ellipse([(3, 3), (5, 5)], fill=ORANGE)  # Head with helmet
    draw.line([(5, 4), (8, 5)], fill=CYAN, width=2)  # Body
    draw.line([(7, 5), (5, 8)], fill=CYAN, width=1)  # Leg
    # Curve indicator
    draw.arc([(1, 6), (11, 11)], 180, 270, fill=WHITE)


def draw_ice_hockey(draw):
    """Hockey player."""
    # Player with stick
    draw.ellipse([(4, 2), (6, 4)], fill=CYAN)  # Head
    draw.line([(5, 4), (5, 7)], fill=CYAN, width=2)  # Body
    draw.line([(5, 5), (8, 4)], fill=CYAN, width=1)  # Arm
    # Stick
    draw.line([(8, 4), (10, 8)], fill=BROWN, width=1)
    draw.line([(9, 8), (11, 8)], fill=BROWN, width=1)
    # Puck
    draw.ellipse([(1, 9), (3, 10)], fill=WHITE)


def draw_curling(draw):
    """Curling stone."""
    # Stone
    draw.ellipse([(3, 4), (9, 9)], fill=RED)
    draw.ellipse([(4, 5), (8, 8)], fill=SILVER)
    # Handle
    draw.rectangle([(5, 2), (7, 5)], fill=SILVER)
    # Broom lines
    draw.line([(1, 10), (3, 8)], fill=YELLOW, width=1)


def draw_bobsleigh(draw):
    """Bobsled."""
    # Sled body
    draw.polygon([(1, 6), (10, 6), (11, 8), (2, 8)], fill=RED)
    # Runners
    draw.line([(2, 9), (11, 9)], fill=SILVER, width=1)
    # Crew (dots)
    draw.ellipse([(3, 4), (5, 6)], fill=CYAN)
    draw.ellipse([(6, 4), (8, 6)], fill=CYAN)


def draw_luge(draw):
    """Luge slider."""
    # Slider on back
    draw.ellipse([(8, 3), (10, 5)], fill=CYAN)  # Head
    draw.line([(3, 5), (8, 4)], fill=CYAN, width=2)  # Body
    # Sled
    draw.line([(2, 7), (10, 7)], fill=RED, width=2)
    # Runners
    draw.line([(2, 8), (10, 8)], fill=SILVER, width=1)


def draw_skeleton(draw):
    """Skeleton slider."""
    # Slider head-first
    draw.ellipse([(2, 3), (4, 5)], fill=CYAN)  # Head
    draw.line([(4, 4), (10, 5)], fill=CYAN, width=2)  # Body
    # Sled
    draw.line([(2, 7), (10, 7)], fill=BLUE, width=2)


def draw_default(draw):
    """Default Olympic rings."""
    # Simplified rings
    draw.arc([(1, 3), (5, 7)], 0, 360, fill=BLUE)
    draw.arc([(4, 3), (8, 7)], 0, 360, fill=WHITE)
    draw.arc([(7, 3), (11, 7)], 0, 360, fill=RED)


# Sport name to icon function mapping
SPORTS = {
    "alpine_skiing": draw_alpine_skiing,
    "cross_country_skiing": draw_cross_country,
    "biathlon": draw_biathlon,
    "ski_jumping": draw_ski_jumping,
    "nordic_combined": draw_nordic_combined,
    "freestyle_skiing": draw_freestyle_skiing,
    "snowboard": draw_snowboard,
    "figure_skating": draw_figure_skating,
    "speed_skating": draw_speed_skating,
    "short_track_speed_skating": draw_short_track,
    "ice_hockey": draw_ice_hockey,
    "curling": draw_curling,
    "bobsleigh": draw_bobsleigh,
    "luge": draw_luge,
    "skeleton": draw_skeleton,
    "default": draw_default,
}


def main():
    print("=" * 50)
    print("Olympics Sport Icons Generator")
    print("=" * 50)
    print(f"Icon size: {ICON_SIZE[0]}x{ICON_SIZE[1]} pixels")
    print(f"Output: {OUTPUT_DIR}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate all icons
    print("Generating icons:")
    for name, draw_func in SPORTS.items():
        create_icon(name, draw_func)

    print()
    print(f"Created {len(SPORTS)} sport icons")


if __name__ == "__main__":
    main()
