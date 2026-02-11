"""
Baseball Scorebug Renderer

Handles all drawing logic for live, recent, and upcoming baseball games.
Replicates functionality from BaseballLive, SportsRecent, and SportsUpcoming.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pytz
from PIL import Image, ImageDraw, ImageFont
import freetype

from logo_manager import BaseballLogoManager
from odds_manager import BaseballOddsManager
from rankings_manager import BaseballRankingsManager


class BaseballScorebugRenderer:
    """Renders scorebugs for all baseball game modes."""

    def __init__(self, display_manager, logo_manager: BaseballLogoManager,
                 odds_manager: BaseballOddsManager,
                 rankings_manager: BaseballRankingsManager,
                 logger: logging.Logger):
        """
        Initialize the scorebug renderer.

        Args:
            display_manager: Display manager instance
            logo_manager: Logo manager instance
            odds_manager: Odds manager instance
            rankings_manager: Rankings manager instance
            logger: Logger instance
        """
        self.display_manager = display_manager
        self.logo_manager = logo_manager
        self.odds_manager = odds_manager
        self.rankings_manager = rankings_manager
        self.logger = logger

        # Get display dimensions
        if display_manager and hasattr(display_manager, 'matrix') and display_manager.matrix is not None:
            self.display_width = display_manager.matrix.width
            self.display_height = display_manager.matrix.height
        elif display_manager:
            # Fallback to width/height properties (which also check matrix)
            self.display_width = getattr(display_manager, "width", 128)
            self.display_height = getattr(display_manager, "height", 32)
        else:
            self.display_width = 128
            self.display_height = 32

        # Load fonts
        self.fonts = self._load_fonts()

    def _load_fonts(self) -> Dict:
        """
        Load fonts used by the scoreboard.

        Returns:
            Dictionary of font objects
        """
        fonts = {}
        try:
            fonts['score'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 10)
            fonts['time'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8)
            fonts['team'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8)
            fonts['status'] = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
            fonts['detail'] = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
            fonts['rank'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 10)
            self.logger.info("Successfully loaded fonts")
        except IOError:
            self.logger.warning("Fonts not found, using default PIL font.")
            fonts['score'] = ImageFont.load_default()
            fonts['time'] = ImageFont.load_default()
            fonts['team'] = ImageFont.load_default()
            fonts['status'] = ImageFont.load_default()
            fonts['detail'] = ImageFont.load_default()
            fonts['rank'] = ImageFont.load_default()
        return fonts

    def _draw_text_with_outline(self, draw: ImageDraw.Draw, text: str, position: tuple,
                                font, fill=(255, 255, 255), outline_color=(0, 0, 0)) -> None:
        """
        Draw text with a black outline for better readability.

        Args:
            draw: ImageDraw instance
            text: Text to draw
            position: (x, y) position tuple
            font: Font to use
            fill: Text color (default: white)
            outline_color: Outline color (default: black)
        """
        x, y = position
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw.text((x, y), text, font=font, fill=fill)

    def render_live_scorebug(self, game: Dict, league_config: Dict, league_key: str = None) -> None:
        """
        Render a live game scorebug.

        Replicates BaseballLive._draw_scorebug_layout() logic.

        Args:
            game: Game dictionary with all game details
            league_config: League-specific configuration
            league_key: League identifier (for MiLB-specific handling)
        """
        try:
            # MiLB uses different rendering
            if league_key == 'milb':
                self._render_milb_live_scorebug(game, league_config)
                return

            main_img = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            # Load logos
            home_abbr = game.get('home_abbr', '')
            away_abbr = game.get('away_abbr', '')
            home_id = game.get('home_id', '')
            away_id = game.get('away_id', '')
            home_logo_path = game.get('home_logo_path')
            away_logo_path = game.get('away_logo_path')
            home_logo_url = game.get('home_logo_url')
            away_logo_url = game.get('away_logo_url')

            sport_key = league_key or 'baseball'
            home_logo = self.logo_manager.load_logo(
                home_id, home_abbr, home_logo_path, home_logo_url, sport_key
            )
            away_logo = self.logo_manager.load_logo(
                away_id, away_abbr, away_logo_path, away_logo_url, sport_key
            )

            if not home_logo or not away_logo:
                self.logger.error(f"Failed to load logos for live game: {game.get('id')}")
                draw_final = ImageDraw.Draw(main_img.convert('RGB'))
                self._draw_text_with_outline(draw_final, "Logo Error", (5, 5), self.fonts['status'])
                self.display_manager.image.paste(main_img.convert('RGB'), (0, 0))
                self.display_manager.update_display()
                return

            center_y = self.display_height // 2

            # Draw logos (shifted slightly inward)
            home_x = self.display_width - home_logo.width + 10
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -10
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Live Game Specific Elements
            text_color = (255, 255, 255)

            # Draw Inning (Top Center)
            inning_half = game.get('inning_half', 'top')
            inning_num = game.get('inning', 1)

            if game.get('is_final', False):
                inning_text = "FINAL"
            else:
                inning_half_indicator = "▲" if inning_half.lower() == "top" else "▼"
                inning_text = f"{inning_half_indicator}{inning_num}"

            # Use display_manager font for inning
            inning_font = getattr(self.display_manager, 'font', self.fonts['time'])
            try:
                inning_bbox = draw_overlay.textbbox((0, 0), inning_text, font=inning_font)
                inning_width = inning_bbox[2] - inning_bbox[0]
            except AttributeError:
                # Fallback for older PIL
                inning_width = len(inning_text) * 8
            inning_x = (self.display_width - inning_width) // 2
            inning_y = 1
            self._draw_text_with_outline(draw_overlay, inning_text, (inning_x, inning_y), inning_font)

            # Draw bases and outs
            bases_occupied = game.get('bases_occupied', [False, False, False])
            outs = game.get('outs', 0)

            # Define geometry
            base_diamond_size = 7
            out_circle_diameter = 3
            out_vertical_spacing = 2
            spacing_between_bases_outs = 3
            base_vert_spacing = 1
            base_horiz_spacing = 1

            base_cluster_height = base_diamond_size + base_vert_spacing + base_diamond_size
            base_cluster_width = base_diamond_size + base_horiz_spacing + base_diamond_size
            out_cluster_height = 3 * out_circle_diameter + 2 * out_vertical_spacing
            out_cluster_width = out_circle_diameter

            overall_start_y = inning_bbox[3] if 'inning_bbox' in locals() else 9

            # Center the BASE cluster horizontally
            bases_origin_x = (self.display_width - base_cluster_width) // 2

            # Determine relative positions for outs based on inning half
            if inning_half == "top":
                outs_column_x = bases_origin_x - spacing_between_bases_outs - out_cluster_width
            else:
                outs_column_x = bases_origin_x + base_cluster_width + spacing_between_bases_outs

            outs_column_start_y = overall_start_y + (base_cluster_height // 2) - (out_cluster_height // 2)

            # Draw Bases (Diamonds)
            base_color_occupied = (255, 255, 255)
            base_color_empty = (255, 255, 255)
            h_d = base_diamond_size // 2

            # 2nd Base (Top center)
            c2x = bases_origin_x + base_cluster_width // 2
            c2y = overall_start_y + h_d
            poly2 = [(c2x, overall_start_y), (c2x + h_d, c2y), (c2x, c2y + h_d), (c2x - h_d, c2y)]
            if bases_occupied[1]:
                draw_overlay.polygon(poly2, fill=base_color_occupied)
            else:
                draw_overlay.polygon(poly2, outline=base_color_empty)

            base_bottom_y = c2y + h_d

            # 3rd Base (Bottom left)
            c3x = bases_origin_x + h_d
            c3y = base_bottom_y + base_vert_spacing + h_d
            poly3 = [(c3x, base_bottom_y + base_vert_spacing), (c3x + h_d, c3y), (c3x, c3y + h_d), (c3x - h_d, c3y)]
            if bases_occupied[2]:
                draw_overlay.polygon(poly3, fill=base_color_occupied)
            else:
                draw_overlay.polygon(poly3, outline=base_color_empty)

            # 1st Base (Bottom right)
            c1x = bases_origin_x + base_cluster_width - h_d
            c1y = base_bottom_y + base_vert_spacing + h_d
            poly1 = [(c1x, base_bottom_y + base_vert_spacing), (c1x + h_d, c1y), (c1x, c1y + h_d), (c1x - h_d, c1y)]
            if bases_occupied[0]:
                draw_overlay.polygon(poly1, fill=base_color_occupied)
            else:
                draw_overlay.polygon(poly1, outline=base_color_empty)

            # Draw Outs (Vertical Circles)
            circle_color_out = (255, 255, 255)
            circle_color_empty_outline = (100, 100, 100)

            for i in range(3):
                cx = outs_column_x
                cy = outs_column_start_y + i * (out_circle_diameter + out_vertical_spacing)
                coords = [cx, cy, cx + out_circle_diameter, cy + out_circle_diameter]
                if i < outs:
                    draw_overlay.ellipse(coords, fill=circle_color_out)
                else:
                    draw_overlay.ellipse(coords, outline=circle_color_empty_outline)

            # Draw Balls-Strikes Count
            balls = game.get('balls', 0)
            strikes = game.get('strikes', 0)
            count_text = f"{balls}-{strikes}"

            # Try to use BDF font if available, otherwise fallback to TTF
            bdf_font = getattr(self.display_manager, 'calendar_font', None)
            if bdf_font and isinstance(bdf_font, freetype.Face):
                try:
                    bdf_font.set_char_size(height=7 * 64)
                    count_text_width = self.display_manager.get_text_width(count_text, bdf_font)
                    using_bdf = True
                except Exception:
                    count_text_width = draw_overlay.textlength(count_text, font=self.fonts['detail'])
                    using_bdf = False
            else:
                count_text_width = draw_overlay.textlength(count_text, font=self.fonts['detail'])
                using_bdf = False

            cluster_bottom_y = overall_start_y + base_cluster_height
            count_y = cluster_bottom_y + 2
            count_x = bases_origin_x + (base_cluster_width - count_text_width) // 2

            if using_bdf:
                self.display_manager.draw = draw_overlay
                outline_color_for_bdf = (0, 0, 0)
                for dx_offset, dy_offset in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                    self.display_manager._draw_bdf_text(
                        count_text, count_x + dx_offset, count_y + dy_offset,
                        color=outline_color_for_bdf, font=bdf_font
                    )
                self.display_manager._draw_bdf_text(count_text, count_x, count_y, color=text_color, font=bdf_font)
            else:
                self._draw_text_with_outline(draw_overlay, count_text, (count_x, count_y), self.fonts['detail'])

            # Draw Team:Score at the bottom
            score_font = getattr(self.display_manager, 'font', self.fonts['score'])
            score_text_color = (255, 255, 255)
            outline_color = (0, 0, 0)

            away_score_str = str(game.get('away_score', '0'))
            home_score_str = str(game.get('home_score', '0'))
            away_text = f"{away_abbr}:{away_score_str}"
            home_text = f"{home_abbr}:{home_score_str}"

            try:
                font_height = score_font.getbbox("A")[3] - score_font.getbbox("A")[1]
            except AttributeError:
                font_height = 8
            score_y = self.display_height - font_height - 2

            # Away Team:Score (Bottom Left)
            away_score_x = 2
            self._draw_text_with_outline(draw_overlay, away_text, (away_score_x, score_y), score_font, fill=score_text_color, outline_color=outline_color)

            # Home Team:Score (Bottom Right)
            try:
                home_text_bbox = draw_overlay.textbbox((0, 0), home_text, font=score_font)
                home_text_width = home_text_bbox[2] - home_text_bbox[0]
            except AttributeError:
                home_text_width = len(home_text) * 8
            home_score_x = self.display_width - home_text_width - 2
            self._draw_text_with_outline(draw_overlay, home_text, (home_score_x, score_y), score_font, fill=score_text_color, outline_color=outline_color)

            # Draw odds if available
            if 'odds' in game and game['odds']:
                self.odds_manager.render_odds(draw_overlay, game['odds'], self.display_width, self.display_height, self.fonts)

            # Composite and display
            main_img = Image.alpha_composite(main_img, overlay)
            main_img = main_img.convert('RGB')
            self.display_manager.image.paste(main_img, (0, 0))
            self.display_manager.update_display()

        except Exception as e:
            self.logger.error(f"Error rendering live scorebug: {e}", exc_info=True)

    def render_recent_scorebug(self, game: Dict, league_config: Dict, league_key: str = None) -> None:
        """
        Render a recent (final) game scorebug.

        Replicates SportsRecent._draw_scorebug_layout() logic.

        Args:
            game: Game dictionary
            league_config: League-specific configuration
            league_key: League identifier
        """
        try:
            # MiLB uses different rendering
            if league_key == 'milb':
                self._render_milb_recent_scorebug(game, league_config)
                return

            main_img = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            # Load logos
            home_abbr = game.get('home_abbr', '')
            away_abbr = game.get('away_abbr', '')
            home_id = game.get('home_id', '')
            away_id = game.get('away_id', '')
            home_logo_path = game.get('home_logo_path')
            away_logo_path = game.get('away_logo_path')
            home_logo_url = game.get('home_logo_url')
            away_logo_url = game.get('away_logo_url')

            sport_key = league_key or 'baseball'
            home_logo = self.logo_manager.load_logo(
                home_id, home_abbr, home_logo_path, home_logo_url, sport_key
            )
            away_logo = self.logo_manager.load_logo(
                away_id, away_abbr, away_logo_path, away_logo_url, sport_key
            )

            if not home_logo or not away_logo:
                self.logger.error(f"Failed to load logos for recent game: {game.get('id')}")
                draw_final = ImageDraw.Draw(main_img.convert('RGB'))
                self._draw_text_with_outline(draw_final, "Logo Error", (5, 5), self.fonts['status'])
                self.display_manager.image.paste(main_img.convert('RGB'), (0, 0))
                self.display_manager.update_display()
                return

            center_y = self.display_height // 2

            # MLB-style logo positioning
            home_x = self.display_width - home_logo.width + 2
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -2
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Final Scores (Centered)
            home_score = str(game.get("home_score", "0"))
            away_score = str(game.get("away_score", "0"))
            score_text = f"{away_score}-{home_score}"
            score_width = draw_overlay.textlength(score_text, font=self.fonts['score'])
            score_x = (self.display_width - score_width) // 2
            score_y = self.display_height - 14
            self._draw_text_with_outline(draw_overlay, score_text, (score_x, score_y), self.fonts['score'])

            # "Final" text (Top center)
            status_text = game.get("period_text", "Final")
            status_width = draw_overlay.textlength(status_text, font=self.fonts['time'])
            status_x = (self.display_width - status_width) // 2
            status_y = 1
            self._draw_text_with_outline(draw_overlay, status_text, (status_x, status_y), self.fonts['time'])

            # Draw odds if available
            if 'odds' in game and game['odds']:
                self.odds_manager.render_odds(draw_overlay, game['odds'], self.display_width, self.display_height, self.fonts)

            # Draw records or rankings if enabled
            show_records = league_config.get('show_records', False)
            show_ranking = league_config.get('show_ranking', False)

            if show_records or show_ranking:
                try:
                    record_font = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
                except IOError:
                    record_font = ImageFont.load_default()

                record_bbox = draw_overlay.textbbox((0, 0), "0-0", font=record_font)
                record_height = record_bbox[3] - record_bbox[1]
                record_y = self.display_height - record_height

                # Display away team info
                if away_abbr:
                    away_text = self._get_team_display_text(
                        away_abbr, game, league_config, league_key, show_records, show_ranking
                    )
                    if away_text:
                        away_record_x = 0
                        self._draw_text_with_outline(draw_overlay, away_text, (away_record_x, record_y), record_font)

                # Display home team info
                if home_abbr:
                    home_text = self._get_team_display_text(
                        home_abbr, game, league_config, league_key, show_records, show_ranking
                    )
                    if home_text:
                        home_record_bbox = draw_overlay.textbbox((0, 0), home_text, font=record_font)
                        home_record_width = home_record_bbox[2] - home_record_bbox[0]
                        home_record_x = self.display_width - home_record_width
                        self._draw_text_with_outline(draw_overlay, home_text, (home_record_x, record_y), record_font)

            # Draw series summary if enabled (replicates BaseballRecent.display_series_summary)
            show_series_summary = league_config.get('show_series_summary', False)
            if show_series_summary:
                series_summary = game.get("series_summary", "")
                if series_summary:
                    try:
                        series_font = self.fonts['time']
                        series_bbox = draw_overlay.textbbox((0, 0), series_summary, font=series_font)
                        series_height = series_bbox[3] - series_bbox[1]
                        series_y = (self.display_height - series_height) // 2
                        series_width = draw_overlay.textlength(series_summary, font=series_font)
                        series_x = (self.display_width - series_width) // 2
                        self._draw_text_with_outline(draw_overlay, series_summary, (series_x, series_y), series_font)
                    except Exception as e:
                        self.logger.warning(f"Error drawing series summary: {e}")

            # Composite and display
            main_img = Image.alpha_composite(main_img, overlay)
            main_img = main_img.convert('RGB')
            self.display_manager.image.paste(main_img, (0, 0))
            self.display_manager.update_display()

        except Exception as e:
            self.logger.error(f"Error rendering recent scorebug: {e}", exc_info=True)

    def render_upcoming_scorebug(self, game: Dict, league_config: Dict, league_key: str = None) -> None:
        """
        Render an upcoming game scorebug.

        Replicates SportsUpcoming._draw_scorebug_layout() logic.

        Args:
            game: Game dictionary
            league_config: League-specific configuration
            league_key: League identifier
        """
        try:
            # MiLB uses different rendering
            if league_key == 'milb':
                self._render_milb_upcoming_scorebug(game, league_config)
                return

            main_img = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            # Load logos
            home_abbr = game.get('home_abbr', '')
            away_abbr = game.get('away_abbr', '')
            home_id = game.get('home_id', '')
            away_id = game.get('away_id', '')
            home_logo_path = game.get('home_logo_path')
            away_logo_path = game.get('away_logo_path')
            home_logo_url = game.get('home_logo_url')
            away_logo_url = game.get('away_logo_url')

            sport_key = league_key or 'baseball'
            home_logo = self.logo_manager.load_logo(
                home_id, home_abbr, home_logo_path, home_logo_url, sport_key
            )
            away_logo = self.logo_manager.load_logo(
                away_id, away_abbr, away_logo_path, away_logo_url, sport_key
            )

            if not home_logo or not away_logo:
                self.logger.error(f"Failed to load logos for upcoming game: {game.get('id')}")
                draw_final = ImageDraw.Draw(main_img.convert('RGB'))
                self._draw_text_with_outline(draw_final, "Logo Error", (5, 5), self.fonts['status'])
                self.display_manager.image.paste(main_img.convert('RGB'), (0, 0))
                self.display_manager.update_display()
                return

            center_y = self.display_height // 2

            # MLB-style logo positions
            home_x = self.display_width - home_logo.width + 2
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -2
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Draw Text Elements on Overlay
            game_date = game.get("game_date", "")
            game_time = game.get("game_time", "")

            # "Next Game" at the top
            status_font = self.fonts['status']
            if self.display_width > 128:
                status_font = self.fonts['time']
            status_text = "Next Game"
            status_width = draw_overlay.textlength(status_text, font=status_font)
            status_x = (self.display_width - status_width) // 2
            status_y = 1
            self._draw_text_with_outline(draw_overlay, status_text, (status_x, status_y), status_font)

            # Date text (centered, below "Next Game")
            date_width = draw_overlay.textlength(game_date, font=self.fonts['time'])
            date_x = (self.display_width - date_width) // 2
            date_y = center_y - 7
            self._draw_text_with_outline(draw_overlay, game_date, (date_x, date_y), self.fonts['time'])

            # Time text (centered, below Date)
            time_width = draw_overlay.textlength(game_time, font=self.fonts['time'])
            time_x = (self.display_width - time_width) // 2
            time_y = date_y + 9
            self._draw_text_with_outline(draw_overlay, game_time, (time_x, time_y), self.fonts['time'])

            # Draw odds if available
            if 'odds' in game and game['odds']:
                self.odds_manager.render_odds(draw_overlay, game['odds'], self.display_width, self.display_height, self.fonts)

            # Draw records or rankings if enabled
            show_records = league_config.get('show_records', False)
            show_ranking = league_config.get('show_ranking', False)

            if show_records or show_ranking:
                try:
                    record_font = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
                except IOError:
                    record_font = ImageFont.load_default()

                record_bbox = draw_overlay.textbbox((0, 0), "0-0", font=record_font)
                record_height = record_bbox[3] - record_bbox[1]
                record_y = self.display_height - record_height

                # Display away team info
                if away_abbr:
                    away_text = self._get_team_display_text(
                        away_abbr, game, league_config, league_key, show_records, show_ranking
                    )
                    if away_text:
                        away_record_x = 0
                        self._draw_text_with_outline(draw_overlay, away_text, (away_record_x, record_y), record_font)

                # Display home team info
                if home_abbr:
                    home_text = self._get_team_display_text(
                        home_abbr, game, league_config, league_key, show_records, show_ranking
                    )
                    if home_text:
                        home_record_bbox = draw_overlay.textbbox((0, 0), home_text, font=record_font)
                        home_record_width = home_record_bbox[2] - home_record_bbox[0]
                        home_record_x = self.display_width - home_record_width
                        self._draw_text_with_outline(draw_overlay, home_text, (home_record_x, record_y), record_font)

            # Composite and display
            main_img = Image.alpha_composite(main_img, overlay)
            main_img = main_img.convert('RGB')
            self.display_manager.image.paste(main_img, (0, 0))
            self.display_manager.update_display()

        except Exception as e:
            self.logger.error(f"Error rendering upcoming scorebug: {e}", exc_info=True)

    def _get_team_display_text(self, team_abbr: str, game: Dict, league_config: Dict,
                               league_key: str, show_records: bool, show_ranking: bool) -> str:
        """
        Get display text for team (ranking or record).

        Args:
            team_abbr: Team abbreviation
            game: Game dictionary
            league_config: League-specific configuration
            league_key: League identifier
            show_records: Whether to show records
            show_ranking: Whether to show rankings

        Returns:
            Display text string
        """
        if show_ranking and show_records:
            # When both rankings and records are enabled, rankings replace records completely
            team_rank = self.rankings_manager.get_team_rank(team_abbr, league_key or 'baseball')
            if team_rank > 0:
                return f"#{team_rank}"
            return ''
        elif show_ranking:
            # Show ranking only if available
            team_rank = self.rankings_manager.get_team_rank(team_abbr, league_key or 'baseball')
            if team_rank > 0:
                return f"#{team_rank}"
            return ''
        elif show_records:
            # Show record only when rankings are disabled
            if team_abbr == game.get('away_abbr', ''):
                return game.get('away_record', '')
            elif team_abbr == game.get('home_abbr', ''):
                return game.get('home_record', '')
            return ''
        return ''

    def _render_milb_live_scorebug(self, game: Dict, league_config: Dict) -> None:
        """
        Render MiLB live game scorebug (replicates MiLBLiveManager._create_live_game_display).

        Args:
            game: Game dictionary
            league_config: League-specific configuration
        """
        try:
            from src.old_managers.milb_manager import MiLBLiveManager

            # For now, use a simplified version that matches ESPN format
            # Full MiLB rendering would require MiLB-specific logic from milb_manager.py
            # This is a placeholder that renders in ESPN format
            self.render_live_scorebug(game, league_config, league_key='milb')

        except Exception as e:
            self.logger.error(f"Error rendering MiLB live scorebug: {e}", exc_info=True)

    def _render_milb_recent_scorebug(self, game: Dict, league_config: Dict) -> None:
        """
        Render MiLB recent game scorebug.

        Args:
            game: Game dictionary
            league_config: League-specific configuration
        """
        try:
            # Simplified version - full implementation would match MiLB manager
            self.render_recent_scorebug(game, league_config, league_key='milb')
        except Exception as e:
            self.logger.error(f"Error rendering MiLB recent scorebug: {e}", exc_info=True)

    def _render_milb_upcoming_scorebug(self, game: Dict, league_config: Dict) -> None:
        """
        Render MiLB upcoming game scorebug.

        Args:
            game: Game dictionary
            league_config: League-specific configuration
        """
        try:
            # Simplified version - full implementation would match MiLB manager
            self.render_upcoming_scorebug(game, league_config, league_key='milb')
        except Exception as e:
            self.logger.error(f"Error rendering MiLB upcoming scorebug: {e}", exc_info=True)

