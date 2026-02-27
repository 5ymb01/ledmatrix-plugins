"""
Stock News Ticker Plugin for LEDMatrix

Displays scrolling stock-specific news headlines and financial updates from RSS feeds.
Shows market news, company announcements, and financial updates for tracked stocks.

Features:
- Stock-specific RSS feeds and news aggregation
- Symbol tracking and filtering
- Smooth horizontal scrolling headline display via ScrollHelper
- Custom RSS feed support
- Configurable scroll speed and colors
- Background data fetching
- Dynamic duration based on content width

API Version: 1.2.0
"""

import time
import requests
import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from src.plugin_system.base_plugin import BasePlugin
from src.common.scroll_helper import ScrollHelper
from src.logging_config import get_logger

logger = get_logger(__name__)


class StockNewsTickerPlugin(BasePlugin):
    """
    Stock news ticker plugin for displaying financial headlines.

    Tracks specific stock symbols and displays relevant news headlines
    from financial RSS feeds with configurable display options.

    Uses ScrollHelper for smooth horizontal scrolling at high FPS.

    Configuration options:
        feeds: Stock symbols to track and custom RSS feeds
        display_options: Scroll speed, duration, colors
        background_service: Data fetching configuration
    """

    def __init__(self, plugin_id: str, config: Dict[str, Any],
                 display_manager, cache_manager, plugin_manager):
        """Initialize the stock news ticker plugin."""
        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)

        # Configuration
        self.feeds_config = config.get('feeds', {})
        self.global_config = config.get('global', {})

        # Display settings
        self.display_duration = self.global_config.get('display_duration', 30)
        self.scroll_speed = self.global_config.get('scroll_speed', 1)
        self.scroll_delay = self.global_config.get('scroll_delay', 0.01)
        self.dynamic_duration = self.global_config.get('dynamic_duration', True)
        self.min_duration = self.global_config.get('min_duration', 30)
        self.max_duration = self.global_config.get('max_duration', 300)
        self.max_headlines_per_symbol = self.global_config.get('max_headlines_per_symbol', 1)
        self.headlines_per_rotation = self.global_config.get('headlines_per_rotation', 2)
        self.font_size = self.global_config.get('font_size', 10)

        # Colors
        self.text_color = tuple(self.feeds_config.get('text_color', [0, 255, 0]))
        self.symbol_color = tuple(self.feeds_config.get('symbol_color', [255, 255, 0]))
        self.separator_color = tuple(self.feeds_config.get('separator_color', [255, 0, 0]))

        # Background service configuration
        self.background_config = self.global_config.get('background_service', {
            'enabled': True,
            'request_timeout': 30,
            'max_retries': 5,
            'priority': 2
        })

        # State
        self.all_news_items: List[Dict] = []
        self.last_update = 0
        self.initialized = True

        # Display dimensions
        self.display_width = display_manager.width
        self.display_height = display_manager.height

        # Initialize ScrollHelper for smooth pixel-by-pixel scrolling
        self.scroll_helper = ScrollHelper(self.display_width, self.display_height, logger=self.logger)

        # Enable scrolling — display controller checks this to enter high-FPS mode (125 FPS)
        self.enable_scrolling = True
        self._cycle_complete = False

        # Additional scroll config
        self.scroll_pixels_per_second = self.global_config.get('scroll_pixels_per_second', 25.0)
        self.target_fps = self.global_config.get('scroll_target_fps', 100)

        # Register fonts and load font objects for rendering
        self._register_fonts()
        self.fonts = self._load_fonts()

        # Configure scroll helper with current settings
        self._configure_scroll_settings()

        # Log configuration
        stock_symbols = self.feeds_config.get('stock_symbols', [])
        custom_feeds = list(self.feeds_config.get('custom_feeds', {}).keys())

        self.logger.info("Stock news ticker plugin initialized")
        self.logger.info(f"Tracking symbols: {stock_symbols}")
        self.logger.info(f"Custom feeds: {custom_feeds}")

    def _register_fonts(self):
        """Register fonts with the font manager."""
        try:
            if not hasattr(self.plugin_manager, 'font_manager'):
                return

            font_manager = self.plugin_manager.font_manager

            # Headline font
            font_manager.register_manager_font(
                manager_id=self.plugin_id,
                element_key=f"{self.plugin_id}.headline",
                family="press_start",
                size_px=self.font_size,
                color=self.text_color
            )

            # Symbol font
            font_manager.register_manager_font(
                manager_id=self.plugin_id,
                element_key=f"{self.plugin_id}.symbol",
                family="press_start",
                size_px=self.font_size,
                color=self.symbol_color
            )

            # Separator font
            font_manager.register_manager_font(
                manager_id=self.plugin_id,
                element_key=f"{self.plugin_id}.separator",
                family="press_start",
                size_px=self.font_size,
                color=self.separator_color
            )

            # Info font (source, time)
            font_manager.register_manager_font(
                manager_id=self.plugin_id,
                element_key=f"{self.plugin_id}.info",
                family="four_by_six",
                size_px=6,
                color=(150, 150, 150)
            )

            self.logger.info("Stock news ticker fonts registered")
        except Exception as e:
            self.logger.warning(f"Error registering fonts: {e}")

    def _load_fonts(self) -> Dict:
        """Load PIL font objects for rendering."""
        fonts = {}
        try:
            fonts['symbol'] = ImageFont.truetype('assets/fonts/PressStart2P-Regular.ttf', 8)
            fonts['headline'] = ImageFont.truetype('assets/fonts/4x6-font.ttf', 8)
            fonts['info'] = ImageFont.truetype('assets/fonts/4x6-font.ttf', 6)
            self.logger.info("Stock news display fonts loaded")
        except Exception as e:
            self.logger.warning(f"Font loading error: {e}, using defaults")
            default = ImageFont.load_default()
            fonts = {'symbol': default, 'headline': default, 'info': default}
        return fonts

    def _configure_scroll_settings(self) -> None:
        """Configure scroll helper with current settings."""
        if not hasattr(self, 'scroll_helper') or not self.scroll_helper:
            return

        # Use frame-based scrolling (scroll_speed = pixels per frame, scroll_delay = seconds per frame)
        self.scroll_helper.set_frame_based_scrolling(True)
        self.scroll_helper.set_scroll_speed(self.scroll_speed)
        self.scroll_helper.set_scroll_delay(self.scroll_delay)
        self.scroll_helper.set_target_fps(self.target_fps)

        # Configure dynamic duration
        self.scroll_helper.set_dynamic_duration_settings(
            enabled=self.dynamic_duration,
            min_duration=self.min_duration,
            max_duration=self.max_duration,
            buffer=self.global_config.get('duration_buffer', 0.1)
        )

        self.logger.debug(
            "Scroll settings: speed=%.1f px/frame, delay=%.3fs, target_fps=%d, dynamic_duration=%s",
            self.scroll_speed, self.scroll_delay, self.target_fps, self.dynamic_duration
        )

    def update(self) -> None:
        """Update stock news headlines for all tracked symbols."""
        if not self.initialized:
            return

        try:
            self.all_news_items = []

            # Get stock symbols to track
            stock_symbols = self.feeds_config.get('stock_symbols', [])

            # Fetch news for each symbol
            for symbol in stock_symbols:
                symbol_news = self._fetch_stock_news(symbol)
                if symbol_news:
                    self.all_news_items.extend(symbol_news)

            # Fetch from custom feeds
            custom_feeds = self.feeds_config.get('custom_feeds', {})
            for feed_name, feed_url in custom_feeds.items():
                custom_news = self._fetch_feed_headlines(feed_name, feed_url)
                if custom_news:
                    self.all_news_items.extend(custom_news)

            # Limit total news items
            max_items = len(stock_symbols) * self.max_headlines_per_symbol + len(custom_feeds) * self.headlines_per_rotation
            if len(self.all_news_items) > max_items:
                self.all_news_items = self.all_news_items[:max_items]

            # Clear scroll cache so scrolling image is rebuilt with new data
            if hasattr(self, 'scroll_helper'):
                self.scroll_helper.clear_cache()

            self.last_update = time.time()
            self.logger.debug(f"Updated stock news: {len(self.all_news_items)} total items")

        except Exception as e:
            self.logger.error(f"Error updating stock news: {e}")

    def _fetch_stock_news(self, symbol: str) -> List[Dict]:
        """Fetch news for a specific stock symbol from Yahoo Finance RSS."""
        cache_key = f"stock_news_{symbol}_{datetime.now().strftime('%Y%m%d%H')}"
        update_interval = self.global_config.get('update_interval', 300)

        # Check cache first
        cached_data = self.cache_manager.get(cache_key, max_age=update_interval)
        if cached_data:
            self.logger.debug(f"Using cached news for {symbol}")
            return cached_data

        try:
            feed_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
            self.logger.info(f"Fetching stock news for {symbol}...")
            headers = {
                'User-Agent': 'LEDMatrix-StockNewsPlugin/1.0 (RSS Reader)'
            }
            response = requests.get(
                feed_url,
                timeout=self.background_config.get('request_timeout', 30),
                headers=headers
            )
            response.raise_for_status()

            root = ET.fromstring(response.content)
            news_items = []

            for item in root.findall('.//item')[:self.max_headlines_per_symbol]:
                title = item.find('title')
                description = item.find('description')
                pub_date = item.find('pubDate')
                link = item.find('link')

                if title is not None and title.text:
                    news_item = {
                        'symbol': symbol,
                        'title': self._clean_headline(html.unescape(title.text).strip()),
                        'summary': html.unescape(description.text).strip() if description is not None and description.text else '',
                        'source': 'Yahoo Finance',
                        'published': pub_date.text if pub_date is not None else '',
                        'url': link.text if link is not None else '',
                    }
                    news_items.append(news_item)

            # Cache the results
            self.cache_manager.set(cache_key, news_items, ttl=update_interval * 2)
            self.logger.debug(f"Fetched {len(news_items)} news items for {symbol}")
            return news_items

        except requests.RequestException as e:
            self.logger.error(f"Error fetching news for {symbol}: {e}")
        except ET.ParseError as e:
            self.logger.error(f"Error parsing RSS feed for {symbol}: {e}")
        except Exception as e:
            self.logger.error(f"Error processing news for {symbol}: {e}")

        # Stale cache fallback on failure
        stale_data = self.cache_manager.get(cache_key, max_age=86400)
        if stale_data:
            self.logger.info(f"Using stale cached news for {symbol}")
            return stale_data
        return []

    def _fetch_feed_headlines(self, feed_name: str, feed_url: str) -> List[Dict]:
        """Fetch headlines from a custom RSS feed."""
        cache_key = f"stock_feed_{feed_name}_{datetime.now().strftime('%Y%m%d%H')}"
        update_interval = self.global_config.get('update_interval', 300)

        # Check cache first
        cached_data = self.cache_manager.get(cache_key, max_age=update_interval)
        if cached_data:
            self.logger.debug(f"Using cached headlines for {feed_name}")
            return cached_data

        try:
            self.logger.info(f"Fetching stock headlines from {feed_name}...")
            response = requests.get(feed_url, timeout=self.background_config.get('request_timeout', 30))
            response.raise_for_status()

            # Parse RSS XML
            root = ET.fromstring(response.content)
            headlines = []

            # Extract headlines from RSS items
            for item in root.findall('.//item')[:self.headlines_per_rotation]:
                title = item.find('title')
                description = item.find('description')
                pub_date = item.find('pubDate')
                link = item.find('link')

                if title is not None and title.text:
                    headline = {
                        'feed_name': feed_name,
                        'title': html.unescape(title.text).strip(),
                        'description': html.unescape(description.text).strip() if description is not None else '',
                        'published': pub_date.text if pub_date is not None else '',
                        'link': link.text if link is not None else '',
                        'timestamp': datetime.now().isoformat()
                    }

                    # Clean up the title
                    headline['title'] = self._clean_headline(headline['title'])
                    headlines.append(headline)

            # Cache the results
            self.cache_manager.set(cache_key, headlines, ttl=update_interval * 2)

            return headlines

        except requests.RequestException as e:
            self.logger.error(f"Error fetching RSS feed {feed_name}: {e}")
            return []
        except ET.ParseError as e:
            self.logger.error(f"Error parsing RSS feed {feed_name}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error processing RSS feed {feed_name}: {e}")
            return []

    def _clean_headline(self, headline: str) -> str:
        """Clean and format headline text."""
        if not headline:
            return ""

        # Remove extra whitespace
        headline = re.sub(r'\s+', ' ', headline.strip())

        # Remove common artifacts
        headline = re.sub(r'^\s*-\s*', '', headline)  # Remove leading dashes
        headline = re.sub(r'\s+', ' ', headline)  # Normalize whitespace

        return headline

    # ---- Scrolling Display Pipeline ----

    def _render_headline(self, news_item: Dict[str, Any]) -> Optional[Image.Image]:
        """
        Render a single stock news headline as a horizontal strip PIL Image.

        Format: "SYMBOL: headline text"
        - Symbol in self.symbol_color using symbol font
        - Separator ": " in self.separator_color
        - Title in self.text_color using headline font
        - Height = display height, text vertically centered
        - Width = calculated from actual text measurements

        Args:
            news_item: Dict with 'symbol'/'feed_name' and 'title' keys

        Returns:
            PIL Image for this headline, or None on error
        """
        try:
            symbol = news_item.get('symbol', news_item.get('feed_name', ''))
            title = news_item.get('title', 'No title')
            separator = ": "

            symbol_font = self.fonts.get('symbol', ImageFont.load_default())
            headline_font = self.fonts.get('headline', ImageFont.load_default())

            # Measure text dimensions using a temporary draw context
            temp_img = Image.new('RGB', (1, 1))
            draw_temp = ImageDraw.Draw(temp_img)

            symbol_bbox = draw_temp.textbbox((0, 0), symbol, font=symbol_font)
            symbol_width = symbol_bbox[2] - symbol_bbox[0]
            symbol_height = symbol_bbox[3] - symbol_bbox[1]

            sep_bbox = draw_temp.textbbox((0, 0), separator, font=symbol_font)
            sep_width = sep_bbox[2] - sep_bbox[0]

            title_bbox = draw_temp.textbbox((0, 0), title, font=headline_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]

            # Total width with trailing padding
            padding = 8
            total_width = symbol_width + sep_width + title_width + padding
            total_height = self.display_height

            # Create the headline strip image
            headline_img = Image.new('RGB', (total_width, total_height), (0, 0, 0))
            draw = ImageDraw.Draw(headline_img)

            current_x = 0

            # Vertically center text using the taller of the two fonts
            max_text_height = max(symbol_height, title_height)
            base_y = (total_height - max_text_height) // 2

            # Draw symbol
            draw.text((current_x, base_y), symbol, font=symbol_font, fill=self.symbol_color)
            current_x += symbol_width

            # Draw separator
            draw.text((current_x, base_y), separator, font=symbol_font, fill=self.separator_color)
            current_x += sep_width

            # Draw title
            draw.text((current_x, base_y), title, font=headline_font, fill=self.text_color)

            return headline_img

        except Exception as e:
            self.logger.error(f"Error rendering stock headline: {e}")
            return None

    def _create_scrolling_image(self) -> None:
        """Create the wide scrolling image from all stock news headlines."""
        try:
            headline_images = []
            for item in self.all_news_items:
                headline_img = self._render_headline(item)
                if headline_img:
                    headline_images.append(headline_img)

            if not headline_images:
                self.logger.warning("No headline images created")
                self.scroll_helper.clear_cache()
                return

            # Use ScrollHelper to create the composite scrolling image
            # ScrollHelper adds display_width padding at the start so content scrolls in from right
            self.scroll_helper.create_scrolling_image(
                headline_images,
                item_gap=32,     # Gap between different headlines
                element_gap=16   # Gap within headline elements
            )
            self._cycle_complete = False

            self.logger.info(
                "Created stock news scrolling image: %d headlines, total_scroll_width=%dpx, dynamic_duration=%ds",
                len(headline_images),
                self.scroll_helper.total_scroll_width,
                self.scroll_helper.get_dynamic_duration()
            )

        except Exception as e:
            self.logger.error(f"Error creating stock news scrolling image: {e}")
            self.scroll_helper.clear_cache()

    def display(self, display_mode: str = None, force_clear: bool = False) -> None:
        """
        Display scrolling stock news headlines.

        Called ~125 times/sec by the display controller in high-FPS mode.
        Each call: update scroll position, extract visible portion, render.

        Args:
            display_mode: Should be 'stock_news_ticker'
            force_clear: If True, clear display and reset scroll
        """
        if not self.initialized:
            self._display_error("Stock news ticker plugin not initialized")
            return

        if not self.all_news_items:
            self._display_no_news()
            return

        # Create scrolling image on first call or after data update
        if not self.scroll_helper.cached_image or force_clear:
            self.logger.info("Creating stock news scrolling image...")
            self._create_scrolling_image()
            if not self.scroll_helper.cached_image:
                self.logger.error("Failed to create scrolling image, showing fallback")
                self._display_no_news()
                return
            self.logger.info("Stock news scrolling image created successfully")
            self._cycle_complete = False

        if force_clear:
            self.scroll_helper.reset_scroll()
            self._cycle_complete = False

        # Signal scrolling state to display manager
        self.display_manager.set_scrolling_state(True)
        self.display_manager.process_deferred_updates()

        # Advance scroll position by scroll_speed pixels per frame
        self.scroll_helper.update_scroll_position()

        # Check cycle completion for dynamic duration
        if self.dynamic_duration and self.scroll_helper.is_scroll_complete():
            if not self._cycle_complete:
                scroll_info = self.scroll_helper.get_scroll_info()
                elapsed_time = scroll_info.get('elapsed_time')
                self.logger.info(
                    "Stock news scroll cycle completed (elapsed=%.2fs, target=%.2fs)",
                    elapsed_time if elapsed_time is not None else -1.0,
                    scroll_info.get('dynamic_duration'),
                )
            self._cycle_complete = True

        # Extract the currently visible portion and render to display
        visible_portion = self.scroll_helper.get_visible_portion()
        if visible_portion:
            self.display_manager.image.paste(visible_portion, (0, 0))
            self.display_manager.update_display()

        # Log frame rate for performance monitoring
        self.scroll_helper.log_frame_rate()

    def _display_no_news(self):
        """Display message when no news is available."""
        img = Image.new('RGB', (self.display_width, self.display_height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self.fonts.get('headline', ImageFont.load_default())
        draw.text((5, 12), "No Stock News", font=font, fill=(150, 150, 150))

        self.display_manager.image = img.copy()
        self.display_manager.update_display()

    def _display_error(self, message: str):
        """Display error message."""
        img = Image.new('RGB', (self.display_width, self.display_height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self.fonts.get('headline', ImageFont.load_default())
        draw.text((5, 12), message, font=font, fill=(255, 0, 0))

        self.display_manager.image = img.copy()
        self.display_manager.update_display()

    # ---- Cycle Tracking & Duration ----

    def is_cycle_complete(self) -> bool:
        """
        Check if the stock news scroll cycle is complete.

        Called by the display controller to determine when to switch
        to the next plugin. Returns True only after all headlines have
        scrolled completely through.

        Returns:
            bool: True if scroll cycle is complete, False otherwise
        """
        return self._cycle_complete

    def reset_cycle_state(self) -> None:
        """
        Reset cycle tracking state for a new display session.

        Called by the display controller before beginning a new
        dynamic-duration session.
        """
        self._cycle_complete = False
        if hasattr(self, 'scroll_helper'):
            self.scroll_helper.reset_scroll()
        self.logger.debug("Stock news cycle state reset")

    def get_display_duration(self) -> float:
        """Get display duration, using dynamic duration if enabled."""
        if self.dynamic_duration and hasattr(self, 'scroll_helper'):
            duration = self.scroll_helper.get_dynamic_duration()
            if duration > 0:
                return float(duration)
        return float(self.display_duration)

    # ---- Config Hot-Reload ----

    def on_config_change(self, new_config: Dict[str, Any]) -> None:
        """Handle configuration changes at runtime (e.g. from web UI)."""
        super().on_config_change(new_config)

        # Update config sections
        self.feeds_config = new_config.get('feeds', {})
        self.global_config = new_config.get('global', {})

        # Update display settings
        self.display_duration = self.global_config.get('display_duration', 30)
        self.scroll_speed = self.global_config.get('scroll_speed', 1)
        self.scroll_delay = self.global_config.get('scroll_delay', 0.01)
        self.dynamic_duration = self.global_config.get('dynamic_duration', True)
        self.min_duration = self.global_config.get('min_duration', 30)
        self.max_duration = self.global_config.get('max_duration', 300)
        self.max_headlines_per_symbol = self.global_config.get('max_headlines_per_symbol', 1)
        self.headlines_per_rotation = self.global_config.get('headlines_per_rotation', 2)
        self.scroll_pixels_per_second = self.global_config.get('scroll_pixels_per_second', 25.0)
        self.target_fps = self.global_config.get('scroll_target_fps', 100)

        # Update colors
        self.text_color = tuple(self.feeds_config.get('text_color', [0, 255, 0]))
        self.symbol_color = tuple(self.feeds_config.get('symbol_color', [255, 255, 0]))
        self.separator_color = tuple(self.feeds_config.get('separator_color', [255, 0, 0]))

        # Apply scroll settings to scroll helper
        self._configure_scroll_settings()

        # Clear scroll cache to force recreation with new settings
        if hasattr(self, 'scroll_helper'):
            self.scroll_helper.clear_cache()

        self.logger.info("Stock news ticker config updated, scroll cache cleared")

    # ---- Plugin Info & Cleanup ----

    def get_info(self) -> Dict[str, Any]:
        """Return plugin info for web UI."""
        info = super().get_info()
        info.update({
            'total_news_items': len(self.all_news_items),
            'stock_symbols': self.feeds_config.get('stock_symbols', []),
            'custom_feeds': list(self.feeds_config.get('custom_feeds', {}).keys()),
            'last_update': self.last_update,
            'display_duration': self.get_display_duration(),
            'scroll_speed': self.scroll_speed,
            'scroll_delay': self.scroll_delay,
            'max_headlines_per_symbol': self.max_headlines_per_symbol,
            'headlines_per_rotation': self.headlines_per_rotation,
            'font_size': self.font_size,
            'text_color': self.text_color,
            'symbol_color': self.symbol_color,
            'separator_color': self.separator_color
        })
        return info

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.all_news_items = []
        if hasattr(self, 'scroll_helper'):
            self.scroll_helper.clear_cache()
        self.logger.info("Stock news ticker plugin cleaned up")
