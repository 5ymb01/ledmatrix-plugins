"""
Game Card Renderer for Baseball Scoreboard Plugin

Renders individual baseball game cards as PIL Images for use in scroll mode.
Adapted from scorebug_renderer.py but returns images instead of updating display directly.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from PIL import Image, ImageDraw, ImageFont

# Pillow compatibility: Image.Resampling.LANCZOS is available in Pillow >= 9.1
# Fall back to Image.LANCZOS for older versions
try:
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_FILTER = Image.LANCZOS


class GameRenderer:
    """Renders individual baseball game cards as PIL Images."""

    def __init__(
        self,
        display_width: int,
        display_height: int,
        config: Dict,
        logo_cache: Optional[Dict[str, Image.Image]] = None,
        custom_logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the game renderer.

        Args:
            display_width: Display width in pixels
            display_height: Display height in pixels
            config: Plugin configuration dictionary
            logo_cache: Optional shared logo cache
            custom_logger: Optional custom logger
        """
        self.display_width = display_width
        self.display_height = display_height
        self.config = config
        self.logger = custom_logger or logging.getLogger(__name__)

        # Use provided logo cache or create new one
        self._logo_cache = logo_cache if logo_cache is not None else {}

        # Load fonts
        self.fonts = self._load_fonts()

    def _load_fonts(self):
        """Load fonts used by the renderer."""
        fonts = {}
        try:
            fonts['score'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 10)
            fonts['time'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8)
            fonts['team'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8)
            fonts['status'] = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
            fonts['detail'] = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
            fonts['rank'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 10)
            self.logger.debug("Successfully loaded fonts")
        except IOError:
            self.logger.warning("Fonts not found, using default PIL font.")
            fonts['score'] = ImageFont.load_default()
            fonts['time'] = ImageFont.load_default()
            fonts['team'] = ImageFont.load_default()
            fonts['status'] = ImageFont.load_default()
            fonts['detail'] = ImageFont.load_default()
            fonts['rank'] = ImageFont.load_default()
        return fonts

    def _get_logo_path(self, league: str, team_abbrev: str) -> Path:
        """Get the logo path for a team based on league."""
        if league == 'mlb':
            return Path("assets/sports/mlb_logos") / f"{team_abbrev}.png"
        elif league == 'milb':
            return Path("assets/sports/milb_logos") / f"{team_abbrev}.png"
        elif league == 'ncaa_baseball':
            return Path("assets/sports/ncaa_logos") / f"{team_abbrev}.png"
        else:
            return Path("assets/sports/mlb_logos") / f"{team_abbrev}.png"

    def _load_and_resize_logo(self, league: str, team_abbrev: str) -> Optional[Image.Image]:
        """Load and resize a team logo, with caching."""
        cache_key = f"{league}_{team_abbrev}"
        if cache_key in self._logo_cache:
            return self._logo_cache[cache_key]

        logo_path = self._get_logo_path(league, team_abbrev)

        if not logo_path.exists():
            self.logger.warning(f"Logo not found for {team_abbrev} at {logo_path}")
            return None

        try:
            with Image.open(logo_path) as logo:
                if logo.mode != 'RGBA':
                    logo = logo.convert('RGBA')

                # Resize logo to fit display
                max_width = int(self.display_width * 1.5)
                max_height = int(self.display_height * 1.5)
                logo.thumbnail((max_width, max_height), RESAMPLE_FILTER)

                # Copy before exiting context manager
                cached_logo = logo.copy()

            self._logo_cache[cache_key] = cached_logo
            return cached_logo

        except OSError:
            self.logger.exception(f"Error loading logo for {team_abbrev}")
            return None

    def _draw_text_with_outline(self, draw, text, position, font,
                               fill=(255, 255, 255), outline_color=(0, 0, 0)):
        """Draw text with a black outline for better readability."""
        x, y = position
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw.text((x, y), text, font=font, fill=fill)

    def render_game_card(self, game: Dict, game_type: str) -> Image.Image:
        """
        Render a game card as a PIL Image.

        Args:
            game: Game dictionary
            game_type: Type of game ('live', 'recent', 'upcoming')

        Returns:
            PIL Image of the rendered game card
        """
        if game_type == 'live':
            return self._render_live_game(game)
        elif game_type == 'recent':
            return self._render_recent_game(game)
        elif game_type == 'upcoming':
            return self._render_upcoming_game(game)
        else:
            self.logger.error(f"Unknown game type: {game_type}")
            return self._render_error_card("Unknown type")

    def _render_live_game(self, game: Dict) -> Image.Image:
        """Render a live baseball game card."""
        try:
            # Create main image with transparency
            main_img = Image.new("RGBA", (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new("RGBA", (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            # Get team info and league
            home_team = game.get('home_team', {})
            away_team = game.get('away_team', {})
            league = game.get('league', 'mlb')

            # Load team logos
            home_logo = self._load_and_resize_logo(league, home_team.get('abbrev', ''))
            away_logo = self._load_and_resize_logo(league, away_team.get('abbrev', ''))

            if not home_logo or not away_logo:
                return self._render_error_card("Logo Error")

            center_y = self.display_height // 2

            # Draw logos
            home_x = self.display_width - home_logo.width + 10
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -10
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Draw inning and status
            inning_info = game.get('inning_info', {})
            inning = inning_info.get('inning', 1)
            inning_half = inning_info.get('half', 'top')
            inning_symbol = "▲" if inning_half == 'top' else "▼"
            inning_text = f"{inning_symbol}{inning}"

            status_width = draw_overlay.textlength(inning_text, font=self.fonts['time'])
            status_x = (self.display_width - status_width) // 2
            status_y = 1
            self._draw_text_with_outline(draw_overlay, inning_text, (status_x, status_y), self.fonts['time'])

            # Draw scores
            home_score = str(home_team.get("score", "0"))
            away_score = str(away_team.get("score", "0"))
            score_text = f"{away_score}-{home_score}"
            score_width = draw_overlay.textlength(score_text, font=self.fonts['score'])
            score_x = (self.display_width - score_width) // 2
            score_y = (self.display_height // 2) - 3
            self._draw_text_with_outline(draw_overlay, score_text, (score_x, score_y), self.fonts['score'])

            # Composite and convert to RGB
            main_img = Image.alpha_composite(main_img, overlay)
            return main_img.convert("RGB")

        except Exception:
            self.logger.exception("Error rendering live game")
            return self._render_error_card("Display error")

    def _render_recent_game(self, game: Dict) -> Image.Image:
        """Render a recent baseball game card."""
        try:
            # Create main image with transparency
            main_img = Image.new("RGBA", (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new("RGBA", (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            # Get team info and league
            home_team = game.get('home_team', {})
            away_team = game.get('away_team', {})
            league = game.get('league', 'mlb')

            # Load team logos
            home_logo = self._load_and_resize_logo(league, home_team.get('abbrev', ''))
            away_logo = self._load_and_resize_logo(league, away_team.get('abbrev', ''))

            if not home_logo or not away_logo:
                return self._render_error_card("Logo Error")

            center_y = self.display_height // 2

            # Draw logos
            home_x = self.display_width - home_logo.width + 10
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -10
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Draw "Final" status
            status_text = "Final"
            status_width = draw_overlay.textlength(status_text, font=self.fonts['time'])
            status_x = (self.display_width - status_width) // 2
            status_y = 1
            self._draw_text_with_outline(draw_overlay, status_text, (status_x, status_y), self.fonts['time'])

            # Draw scores
            home_score = str(home_team.get("score", "0"))
            away_score = str(away_team.get("score", "0"))
            score_text = f"{away_score}-{home_score}"
            score_width = draw_overlay.textlength(score_text, font=self.fonts['score'])
            score_x = (self.display_width - score_width) // 2
            score_y = (self.display_height // 2) - 3
            self._draw_text_with_outline(draw_overlay, score_text, (score_x, score_y), self.fonts['score'])

            # Composite and convert to RGB
            main_img = Image.alpha_composite(main_img, overlay)
            return main_img.convert("RGB")

        except Exception:
            self.logger.exception("Error rendering recent game")
            return self._render_error_card("Display error")

    def _render_upcoming_game(self, game: Dict) -> Image.Image:
        """Render an upcoming baseball game card."""
        try:
            # Create main image with transparency
            main_img = Image.new("RGBA", (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new("RGBA", (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            # Get team info and league
            home_team = game.get('home_team', {})
            away_team = game.get('away_team', {})
            league = game.get('league', 'mlb')

            # Load team logos
            home_logo = self._load_and_resize_logo(league, home_team.get('abbrev', ''))
            away_logo = self._load_and_resize_logo(league, away_team.get('abbrev', ''))

            if not home_logo or not away_logo:
                return self._render_error_card("Logo Error")

            center_y = self.display_height // 2

            # Draw logos
            home_x = self.display_width - home_logo.width + 10
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -10
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Draw game time
            game_time = game.get('start_time_short', 'TBD')
            time_width = draw_overlay.textlength(game_time, font=self.fonts['time'])
            time_x = (self.display_width - time_width) // 2
            time_y = 1
            self._draw_text_with_outline(draw_overlay, game_time, (time_x, time_y), self.fonts['time'])

            # Draw "vs" in center
            vs_text = "VS"
            vs_width = draw_overlay.textlength(vs_text, font=self.fonts['score'])
            vs_x = (self.display_width - vs_width) // 2
            vs_y = (self.display_height // 2) - 3
            self._draw_text_with_outline(draw_overlay, vs_text, (vs_x, vs_y), self.fonts['score'])

            # Composite and convert to RGB
            main_img = Image.alpha_composite(main_img, overlay)
            return main_img.convert("RGB")

        except Exception:
            self.logger.exception("Error rendering upcoming game")
            return self._render_error_card("Display error")

    def _render_error_card(self, message: str) -> Image.Image:
        """Render an error message card."""
        img = Image.new('RGB', (self.display_width, self.display_height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        self._draw_text_with_outline(draw, message, (5, 5), self.fonts['status'])
        return img
