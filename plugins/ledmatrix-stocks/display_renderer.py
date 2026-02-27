"""
Display Renderer for Stock Ticker Plugin

Handles all display creation, layout, and rendering logic for both
scrolling and static display modes.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Import common utilities
from src.common import ScrollHelper, LogoHelper, TextHelper


class StockDisplayRenderer:
    """Handles rendering of stock and cryptocurrency displays."""

    # Class-level font cache keyed by (font_path, font_size) to avoid redundant
    # disk I/O when the same font is loaded multiple times across instances or
    # after config changes.
    _font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}

    def __init__(self, config: Dict[str, Any], display_width: int, display_height: int, logger):
        """Initialize the display renderer."""
        self.config = config
        self.display_width = display_width
        self.display_height = display_height
        self.logger = logger

        # Display configuration - support both new nested format (display.toggle_chart)
        # and old top-level format for backward compatibility
        display_config = config.get('display', {})
        self.toggle_chart = display_config.get('toggle_chart', config.get('toggle_chart', False))
        self.layout_preset = display_config.get('layout_preset', 'single')

        # Load colors from customization structure (organized by element: symbol, price, price_delta)
        # Support both new format (customization.stocks.*) and old format (top-level) for backwards compatibility
        customization = config.get('customization', {})
        stocks_custom = customization.get('stocks', {})
        crypto_custom = customization.get('crypto', {})

        # Stock colors - new format: customization.stocks.symbol/price/price_delta
        # Old format fallback: top-level text_color, positive_color, negative_color
        # Ensure all color values are integers (RGB values from config might be floats)
        if stocks_custom.get('symbol') and 'text_color' in stocks_custom['symbol']:
            symbol_color_list = stocks_custom['symbol'].get('text_color', [255, 255, 255])
            price_color_list = stocks_custom.get('price', {}).get('text_color', [255, 255, 255])
            self.symbol_text_color = tuple(int(c) for c in symbol_color_list)
            self.price_text_color = tuple(int(c) for c in price_color_list)
        else:
            old_text_color_list = config.get('text_color', [255, 255, 255])
            old_text_color = tuple(int(c) for c in old_text_color_list)
            self.symbol_text_color = old_text_color
            self.price_text_color = old_text_color

        price_delta_custom = stocks_custom.get('price_delta', {})
        if price_delta_custom:
            positive_color_list = price_delta_custom.get('positive_color', [0, 255, 0])
            negative_color_list = price_delta_custom.get('negative_color', [255, 0, 0])
            self.positive_color = tuple(int(c) for c in positive_color_list)
            self.negative_color = tuple(int(c) for c in negative_color_list)
        else:
            positive_color_list = config.get('positive_color', [0, 255, 0])
            negative_color_list = config.get('negative_color', [255, 0, 0])
            self.positive_color = tuple(int(c) for c in positive_color_list)
            self.negative_color = tuple(int(c) for c in negative_color_list)

        # Crypto colors
        if crypto_custom.get('symbol') and 'text_color' in crypto_custom['symbol']:
            crypto_symbol_color_list = crypto_custom['symbol'].get('text_color', [255, 215, 0])
            crypto_price_color_list = crypto_custom.get('price', {}).get('text_color', [255, 215, 0])
            self.crypto_symbol_text_color = tuple(int(c) for c in crypto_symbol_color_list)
            self.crypto_price_text_color = tuple(int(c) for c in crypto_price_color_list)
        else:
            old_crypto_text_color_list = crypto_custom.get('text_color', [255, 215, 0])
            old_crypto_text_color = tuple(int(c) for c in old_crypto_text_color_list)
            self.crypto_symbol_text_color = old_crypto_text_color
            self.crypto_price_text_color = old_crypto_text_color

        crypto_price_delta_custom = crypto_custom.get('price_delta', {})
        if crypto_price_delta_custom:
            crypto_positive_color_list = crypto_price_delta_custom.get('positive_color', [0, 255, 0])
            crypto_negative_color_list = crypto_price_delta_custom.get('negative_color', [255, 0, 0])
            self.crypto_positive_color = tuple(int(c) for c in crypto_positive_color_list)
            self.crypto_negative_color = tuple(int(c) for c in crypto_negative_color_list)
        else:
            crypto_positive_color_list = crypto_custom.get('positive_color', [0, 255, 0])
            crypto_negative_color_list = crypto_custom.get('negative_color', [255, 0, 0])
            self.crypto_positive_color = tuple(int(c) for c in crypto_positive_color_list)
            self.crypto_negative_color = tuple(int(c) for c in crypto_negative_color_list)

        # Initialize helpers
        self.logo_helper = LogoHelper(display_width, display_height, logger=logger)
        self.text_helper = TextHelper(logger=self.logger)

        # Initialize scroll helper
        self.scroll_helper = ScrollHelper(display_width, display_height, logger)

        # Load custom fonts from config
        fonts_config = customization.get('fonts', {})
        if fonts_config:
            self.symbol_font = self._load_custom_font_from_element_config(fonts_config.get('symbol', {}))
            self.price_font = self._load_custom_font_from_element_config(fonts_config.get('price', {}))
            self.price_delta_font = self._load_custom_font_from_element_config(fonts_config.get('price_delta', {}))
        else:
            self.symbol_font = self._load_custom_font_from_element_config(stocks_custom.get('symbol', {}))
            self.price_font = self._load_custom_font_from_element_config(stocks_custom.get('price', {}))
            self.price_delta_font = self._load_custom_font_from_element_config(stocks_custom.get('price_delta', {}))

        # Compact font for quad layout cells (2 lines fit in half the display height)
        self.compact_font = self._load_custom_font_from_element_config(
            {'font': '4x6-font.ttf', 'font_size': 6}
        )

        # Dual layout: slightly smaller price font creates more breathing room
        # for the 3-row text block (symbol / price / change) in the half-column.
        _price_cfg = fonts_config.get('price', {}) if fonts_config else stocks_custom.get('price', {})
        _dual_price_size = max(6, int(_price_cfg.get('font_size', 8)) - 1)
        self.dual_price_font = self._load_custom_font_from_element_config({
            'font': _price_cfg.get('font', 'PressStart2P-Regular.ttf'),
            'font_size': _dual_price_size,
        })

    def _load_custom_font_from_element_config(self, element_config: Dict[str, Any]) -> ImageFont.FreeTypeFont:
        """
        Load a custom font from an element configuration dictionary.

        Uses a class-level cache keyed by (font_path, font_size) so that
        repeated requests for the same font avoid redundant disk I/O.

        Args:
            element_config: Configuration dict for a single element (symbol, price, or price_delta)
                           containing 'font' and 'font_size' keys

        Returns:
            PIL ImageFont object
        """
        font_name = element_config.get('font', 'PressStart2P-Regular.ttf')
        font_size = int(element_config.get('font_size', 8))

        font_path = os.path.join('assets', 'fonts', font_name)
        cache_key = (font_path, font_size)

        # Return cached font if available
        if cache_key in StockDisplayRenderer._font_cache:
            self.logger.debug("Using cached font: %s at size %d", font_name, font_size)
            return StockDisplayRenderer._font_cache[cache_key]

        try:
            if os.path.exists(font_path):
                if font_path.lower().endswith('.ttf'):
                    font = ImageFont.truetype(font_path, font_size)
                    self.logger.debug("Loaded font: %s at size %d", font_name, font_size)
                    StockDisplayRenderer._font_cache[cache_key] = font
                    return font
                elif font_path.lower().endswith('.bdf'):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        self.logger.debug("Loaded BDF font: %s at size %d", font_name, font_size)
                        StockDisplayRenderer._font_cache[cache_key] = font
                        return font
                    except OSError:
                        self.logger.warning("Could not load BDF font %s with PIL, using default", font_name)
                else:
                    self.logger.warning("Unknown font file type: %s, using default", font_name)
            else:
                self.logger.warning("Font file not found: %s, using default", font_path)
        except OSError:
            self.logger.exception("Error loading font %s, using default", font_name)

        default_font_path = os.path.join('assets', 'fonts', 'PressStart2P-Regular.ttf')
        default_cache_key = (default_font_path, font_size)

        # Check cache for default font too
        if default_cache_key in StockDisplayRenderer._font_cache:
            return StockDisplayRenderer._font_cache[default_cache_key]

        try:
            if os.path.exists(default_font_path):
                font = ImageFont.truetype(default_font_path, font_size)
                StockDisplayRenderer._font_cache[default_cache_key] = font
                return font
            else:
                self.logger.warning("Default font not found, using PIL default")
                return ImageFont.load_default()
        except OSError:
            self.logger.exception("Error loading default font")
            return ImageFont.load_default()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert a value to float, returning default on failure.

        Handles None, non-numeric strings, and other unexpected types that
        may arrive from upstream API responses.
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _get_change_text(self, data: Dict[str, Any], is_crypto: bool) -> str:
        """Build the change/percentage display string from stock data."""
        if is_crypto:
            show_change = self.config.get('crypto', {}).get('show_change', True)
            show_percentage = self.config.get('crypto', {}).get('show_percentage', True)
        else:
            show_change = self.config.get('show_change', True)
            show_percentage = self.config.get('show_percentage', True)

        change_val = self._safe_float(data.get('change', 0.0))
        change_parts: List[str] = []
        try:
            if show_change:
                change_parts.append(f"{change_val:+.2f}")
            if show_percentage:
                change_pct = data.get('change_percent')
                open_val = self._safe_float(data.get('open', 0))
                if change_pct is not None:
                    change_parts.append(f"({self._safe_float(change_pct):+.1f}%)")
                elif open_val > 0:
                    change_percent = (change_val / open_val) * 100
                    change_parts.append(f"({change_percent:+.1f}%)")
        except (TypeError, ValueError, ZeroDivisionError):
            pass

        return " ".join(change_parts) if change_parts else ""

    def _get_change_color(self, data: Dict[str, Any], is_crypto: bool) -> Tuple[int, int, int]:
        """Return the positive or negative color based on the stock's change value."""
        change_val = self._safe_float(data.get('change', 0.0))
        if change_val >= 0:
            return self.positive_color if not is_crypto else self.crypto_positive_color
        return self.negative_color if not is_crypto else self.crypto_negative_color

    def _get_compact_change_text(self, data: Dict[str, Any]) -> str:
        """Return a compact percentage-only change string for space-constrained layouts."""
        try:
            change_val = self._safe_float(data.get('change', 0.0))
            if 'change_percent' in data:
                pct = self._safe_float(data['change_percent'])
            else:
                open_val = self._safe_float(data.get('open', 0))
                if open_val > 0:
                    pct = (change_val / open_val) * 100
                else:
                    return ""
            return f"{pct:+.1f}%"
        except (TypeError, ValueError, ZeroDivisionError):
            return ""

    def _draw_change_arrow(self, draw: ImageDraw.Draw, x: int, y: int,
                           positive: bool, color: Tuple[int, int, int]) -> None:
        """Draw a small filled triangle indicating price direction.

        The triangle is 5px wide and 4px tall.
        Upward (▲) for positive movement, downward (▼) for negative.
        """
        if positive:
            # Tip at top-centre, base at bottom
            points = [(x + 2, y), (x, y + 3), (x + 4, y + 3)]
        else:
            # Base at top, tip at bottom-centre
            points = [(x, y), (x + 4, y), (x + 2, y + 3)]
        draw.polygon(points, fill=color)

    def _get_stock_logo(self, symbol: str, is_crypto: bool = False,
                        max_px: Optional[int] = None) -> Optional[Image.Image]:
        """Get stock or crypto logo image.

        Args:
            symbol:    Ticker symbol.
            is_crypto: Whether this is a cryptocurrency.
            max_px:    Maximum pixel size (square). Defaults to
                       int(display_height * 0.65) — tighter than the old 1/1.2 ratio.
        """
        if max_px is None:
            max_px = int(self.display_height * 0.65)
        try:
            if is_crypto:
                logo_path = f"assets/stocks/crypto_icons/{symbol}.png"
            else:
                logo_path = f"assets/stocks/ticker_icons/{symbol}.png"
            # Include max_px in the abbr so different sizes get separate cache entries
            return self.logo_helper.load_logo(f"{symbol}_{max_px}", logo_path, max_px, max_px)
        except (OSError, IOError) as e:
            self.logger.warning("Error loading logo for %s: %s", symbol, e)
            return None

    def _draw_mini_chart(self, draw: ImageDraw.Draw, price_history: List[Dict],
                         width: int, height: int, color: Tuple[int, int, int]) -> None:
        """Draw a mini price chart on the right side of the display."""
        if len(price_history) < 2:
            return

        chart_width = int(width / 2.5)
        chart_height = int(height / 1.5)
        chart_x = int(width - chart_width - 4)
        chart_y = int((height - chart_height) / 2)

        prices = [point['price'] for point in price_history if 'price' in point]
        if len(prices) < 2:
            return

        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price

        if price_range == 0:
            y = int(chart_y + chart_height / 2)
            draw.line([(chart_x, y), (chart_x + chart_width, y)], fill=color, width=1)
            return

        if price_range < 0.01:
            min_price -= 0.01
            max_price += 0.01
            price_range = 0.02

        points = []
        for i, price in enumerate(prices):
            x = int(chart_x + (i * chart_width) / (len(prices) - 1))
            y = int(chart_y + chart_height - int(((price - min_price) / price_range) * chart_height))
            points.append((x, y))

        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=color, width=1)

    # ------------------------------------------------------------------
    # Layout renderers
    # ------------------------------------------------------------------

    def create_stock_display(self, symbol: str, data: Dict[str, Any]) -> Image.Image:
        """Create a display image for a single stock (single layout, tightened).

        Panel width is 1.8× display width with chart, 1.2× without — tighter than
        the original 2× / 1.5×. Logo is ~65% of display height. Text column is
        dynamically centred in the space between logo and chart area.
        """
        width = int(self.display_width * (1.8 if self.toggle_chart else 1.2))
        height = int(self.display_height)
        image = Image.new('RGB', (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        is_crypto = data.get('is_crypto', False)

        # Logo — tighter default size via _get_stock_logo default (~65% of height)
        logo = self._get_stock_logo(symbol, is_crypto)
        logo_right = 4
        if logo:
            logo_x = 2
            logo_y = int((height - logo.height) // 2)
            image.paste(logo, (logo_x, logo_y), logo)
            logo_right = logo_x + logo.width + 4

        symbol_font = self.symbol_font
        price_font = self.price_font
        change_font = self.price_delta_font

        display_symbol = symbol.replace('-USD', '') if is_crypto else symbol
        price = self._safe_float(data.get('price', 0.0))
        price_text = f"${price:.2f}"
        change_text = self._get_change_text(data, is_crypto)
        change_color = self._get_change_color(data, is_crypto)
        symbol_color = self.symbol_text_color if not is_crypto else self.crypto_symbol_text_color
        price_color = self.price_text_color if not is_crypto else self.crypto_price_text_color

        symbol_bbox = draw.textbbox((0, 0), display_symbol, font=symbol_font)
        price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
        symbol_height = int(symbol_bbox[3] - symbol_bbox[1])
        price_height = int(price_bbox[3] - price_bbox[1])

        if change_text:
            change_bbox = draw.textbbox((0, 0), change_text, font=change_font)
            change_height = int(change_bbox[3] - change_bbox[1])
        else:
            change_bbox = (0, 0, 0, 0)
            change_height = 0

        text_gap = 2 if self.toggle_chart else 1
        change_gap = text_gap if change_text else 0
        total_text_height = symbol_height + price_height + change_height + text_gap + change_gap
        start_y = int((height - total_text_height) // 2)

        # Dynamic column_x: centre text in the space between logo right-edge and chart left-edge
        if self.toggle_chart:
            chart_width_px = int(width / 2.5)
            chart_left = width - chart_width_px - 6
        else:
            chart_left = width - 4
        available = chart_left - logo_right
        column_x = logo_right + available // 2

        # Draw symbol
        sym_w = int(symbol_bbox[2] - symbol_bbox[0])
        draw.text((column_x - sym_w // 2, start_y), display_symbol,
                  font=symbol_font, fill=symbol_color)

        # Draw price
        prc_w = int(price_bbox[2] - price_bbox[0])
        price_y = start_y + symbol_height + text_gap
        draw.text((column_x - prc_w // 2, price_y), price_text,
                  font=price_font, fill=price_color)

        # Draw change
        if change_text:
            chg_w = int(change_bbox[2] - change_bbox[0])
            change_y = price_y + price_height + text_gap
            draw.text((column_x - chg_w // 2, change_y), change_text,
                      font=change_font, fill=change_color)

        # Mini chart
        if self.toggle_chart and 'price_history' in data and len(data['price_history']) >= 2:
            self._draw_mini_chart(draw, data['price_history'], width, height, change_color)

        return image

    def create_dual_panel(self, stocks_items: List[Tuple[str, Dict[str, Any]]]) -> Image.Image:
        """Create a full-display panel showing up to 2 stocks side-by-side.

        Each stock occupies half the display width. Uses the user's configured
        fonts with the same dynamic vertical-centering as create_stock_display().
        A dim grey vertical separator is drawn at the midpoint.

        Args:
            stocks_items: List of (symbol, data) tuples, maximum 2.

        Returns:
            PIL Image of size (display_width × display_height).
        """
        width = int(self.display_width)
        height = int(self.display_height)
        col_w = width // 2
        logo_size = height  # full panel height, maximum logo size

        image = Image.new('RGB', (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        for col, (symbol, data) in enumerate(stocks_items[:2]):
            x_offset = col * col_w
            is_crypto = data.get('is_crypto', False)

            # Logo — sized to fill the panel height
            logo = self._get_stock_logo(symbol, is_crypto, max_px=logo_size)
            logo_right = x_offset + 4
            if logo:
                logo_x = x_offset + 2
                logo_y = (height - logo.height) // 2
                image.paste(logo, (logo_x, logo_y), logo)
                logo_right = logo_x + logo.width + 3

            # Data
            display_symbol = symbol.replace('-USD', '') if is_crypto else symbol
            price = self._safe_float(data.get('price', 0.0))
            price_text = f"${price:.2f}"
            change_val = self._safe_float(data.get('change', 0.0))
            positive = change_val >= 0
            change_color = self._get_change_color(data, is_crypto)
            symbol_color = self.symbol_text_color if not is_crypto else self.crypto_symbol_text_color
            price_color = self.price_text_color if not is_crypto else self.crypto_price_text_color

            # Fonts — price uses slightly smaller dual variant for better vertical fit
            symbol_font = self.symbol_font
            price_font = self.dual_price_font
            change_font = self.price_delta_font

            # Available horizontal space for the text column (right of logo)
            col_right = x_offset + col_w
            available = col_right - logo_right
            column_x = logo_right + available // 2

            # Change row: compute pct and determine if change data exists
            try:
                if 'change_percent' in data:
                    pct = self._safe_float(data['change_percent'])
                    has_change = True
                else:
                    open_val = self._safe_float(data.get('open', 0))
                    if open_val > 0:
                        pct = (change_val / open_val) * 100
                        has_change = True
                    else:
                        pct = 0.0
                        has_change = False
            except (TypeError, ValueError, ZeroDivisionError):
                pct = 0.0
                has_change = False

            if has_change:
                # Arrow shows direction — no +/- prefix on either value.
                # Dollar uses compact_font (small) so the row always fits;
                # pct uses full price_delta_font so the decimal stays legible.
                dollar_str = f"{abs(change_val):.2f}"
                pct_str = f"{abs(pct):.1f}%"
                dol_bbox = draw.textbbox((0, 0), dollar_str, font=self.compact_font)
                pct_bbox = draw.textbbox((0, 0), pct_str, font=change_font)
                dol_w = int(dol_bbox[2] - dol_bbox[0])
                dol_h = int(dol_bbox[3] - dol_bbox[1])
                pct_w = int(pct_bbox[2] - pct_bbox[0])
                h_gap = 2
                arrow_w = 5
                chg_h = dol_h  # row height governed by the dollar font
            else:
                chg_h = 0

            # Measure symbol and price for vertical centering
            sym_bbox = draw.textbbox((0, 0), display_symbol, font=symbol_font)
            prc_bbox = draw.textbbox((0, 0), price_text, font=price_font)
            sym_h = int(sym_bbox[3] - sym_bbox[1])
            prc_h = int(prc_bbox[3] - prc_bbox[1])

            v_gap = 1
            n_gaps = 2 if has_change else 1
            total_h = sym_h + prc_h + chg_h + v_gap * n_gaps
            start_y = (height - total_h) // 2

            # Draw symbol
            sym_w = int(sym_bbox[2] - sym_bbox[0])
            draw.text((column_x - sym_w // 2, start_y), display_symbol,
                      font=symbol_font, fill=symbol_color)

            # Draw price
            prc_w = int(prc_bbox[2] - prc_bbox[0])
            price_y = start_y + sym_h + v_gap
            draw.text((column_x - prc_w // 2, price_y), price_text,
                      font=price_font, fill=price_color)

            # Draw change row: [dollar_str] [▲/▼] [pct_str]
            if has_change:
                change_y = price_y + prc_h + v_gap
                total_row_w = dol_w + h_gap + arrow_w + h_gap + pct_w
                row_x = column_x - total_row_w // 2
                arrow_y = change_y + max(0, (dol_h - 4) // 2)
                draw.text((row_x, change_y), dollar_str,
                          font=self.compact_font, fill=change_color)
                self._draw_change_arrow(draw, row_x + dol_w + h_gap, arrow_y,
                                        positive, change_color)
                draw.text((row_x + dol_w + h_gap + arrow_w + h_gap, change_y),
                          pct_str, font=change_font, fill=change_color)

        # Vertical separator between the two halves
        draw.line([(col_w, 0), (col_w, height - 1)], fill=(160, 160, 160), width=1)
        # Right-edge separator — becomes divider between adjacent panels in the strip
        draw.line([(width - 1, 0), (width - 1, height - 1)], fill=(160, 160, 160), width=1)

        return image

    def create_quad_panel(self, stocks_items: List[Tuple[str, Dict[str, Any]]]) -> Image.Image:
        """Create a full-display panel showing up to 4 stocks in a 2×2 grid.

        Each cell is (display_width//2) × (display_height//2).
        Row 1: small logo + symbol (left) + price (right)
        Row 2: ▲/▼ arrow + dollar change + percentage change, centred

        Args:
            stocks_items: List of (symbol, data) tuples, maximum 4.

        Returns:
            PIL Image of size (display_width × display_height).
        """
        width = int(self.display_width)
        height = int(self.display_height)
        cell_w = width // 2
        cell_h = height // 2
        logo_size = int(cell_h * 0.65)  # ~10px on a 16px-tall cell

        image = Image.new('RGB', (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        font = self.compact_font

        for idx, (symbol, data) in enumerate(stocks_items[:4]):
            col = idx % 2
            row = idx // 2
            cell_x = col * cell_w
            cell_y = row * cell_h

            is_crypto = data.get('is_crypto', False)
            display_symbol = symbol.replace('-USD', '') if is_crypto else symbol
            price = self._safe_float(data.get('price', 0.0))
            change_val = self._safe_float(data.get('change', 0.0))
            change_color = self._get_change_color(data, is_crypto)
            positive = change_val >= 0

            # Compact price: omit cents for large values to save horizontal space
            if price >= 1000:
                price_str = f"${price:.0f}"
            elif price >= 100:
                price_str = f"${price:.1f}"
            else:
                price_str = f"${price:.2f}"

            # Row 2 content: dollar change + percentage
            try:
                if 'change_percent' in data:
                    pct = self._safe_float(data['change_percent'])
                else:
                    open_val = self._safe_float(data.get('open', 0))
                    if open_val > 0:
                        pct = (change_val / open_val) * 100
                    else:
                        pct = 0.0
            except (TypeError, ValueError, ZeroDivisionError):
                pct = 0.0
            # --- Row 1: small logo + symbol (left) + price (right) ---
            row1_y = cell_y + 1

            # Try to load and draw a small logo
            logo = self._get_stock_logo(symbol, is_crypto, max_px=logo_size)
            if logo:
                logo_x = cell_x + 1
                logo_y = cell_y + (cell_h - logo.height) // 2
                image.paste(logo, (logo_x, logo_y), logo)
                text_x = cell_x + logo_size + 3
            else:
                text_x = cell_x + 2

            draw.text((text_x, row1_y), display_symbol,
                      font=font, fill=self.symbol_text_color)

            prc_bbox = draw.textbbox((0, 0), price_str, font=font)
            prc_w = int(prc_bbox[2] - prc_bbox[0])
            draw.text((cell_x + cell_w - prc_w - 2, row1_y), price_str,
                      font=font, fill=self.price_text_color)

            # --- Row 2: dollar change ▲/▼ pct% — arrow acts as separator ---
            row2_y = cell_y + cell_h // 2 + 1

            # Arrow shows direction — no +/- prefix on either value
            dollar_str = f"{abs(change_val):.2f}"
            pct_str = f"{abs(pct):.1f}%"

            dol_bbox = draw.textbbox((0, 0), dollar_str, font=font)
            pct_bbox = draw.textbbox((0, 0), pct_str, font=font)
            dol_w = int(dol_bbox[2] - dol_bbox[0])
            pct_w = int(pct_bbox[2] - pct_bbox[0])
            dol_h = int(dol_bbox[3] - dol_bbox[1])

            # Layout: [dollar_str] [gap] [▲/▼ arrow] [gap] [pct_str]
            arrow_w = 5
            gap = 2
            total_row2_w = dol_w + gap + arrow_w + gap + pct_w
            row2_x = cell_x + (cell_w - total_row2_w) // 2

            # Vertically centre the 4px arrow within the text row height
            arrow_y = row2_y + max(0, (dol_h - 4) // 2)

            draw.text((row2_x, row2_y), dollar_str, font=font, fill=change_color)
            self._draw_change_arrow(draw, row2_x + dol_w + gap, arrow_y, positive, change_color)
            draw.text((row2_x + dol_w + gap + arrow_w + gap, row2_y), pct_str,
                      font=font, fill=change_color)

        # Grid separator lines — drawn last so they appear over cell content
        sep = (160, 160, 160)
        draw.line([(cell_w, 0), (cell_w, height - 1)], fill=sep, width=1)
        draw.line([(0, cell_h), (width - 1, cell_h)], fill=sep, width=1)
        # Right-edge separator: creates a divider between adjacent panels in the scroll strip
        draw.line([(width - 1, 0), (width - 1, height - 1)], fill=sep, width=1)

        return image

    def create_static_display(self, symbol: str, data: Dict[str, Any]) -> Image.Image:
        """Create a static display for one stock/crypto (no scrolling)."""
        image = Image.new('RGB', (int(self.display_width), int(self.display_height)), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        is_crypto = data.get('is_crypto', False)

        logo = self._get_stock_logo(symbol, is_crypto)
        if logo:
            logo_x = 5
            logo_y = int((int(self.display_height) - logo.height) // 2)
            image.paste(logo, (int(logo_x), int(logo_y)), logo)

        symbol_font = self.symbol_font
        price_font = self.price_font
        change_font = self.price_delta_font

        display_symbol = symbol.replace('-USD', '') if is_crypto else symbol
        price = self._safe_float(data.get('price', 0.0))
        price_text = f"${price:.2f}"
        change_text = self._get_change_text(data, is_crypto)
        change_color = self._get_change_color(data, is_crypto)
        symbol_color = self.symbol_text_color if not is_crypto else self.crypto_symbol_text_color
        price_color = self.price_text_color if not is_crypto else self.crypto_price_text_color

        symbol_bbox = draw.textbbox((0, 0), display_symbol, font=symbol_font)
        price_bbox = draw.textbbox((0, 0), price_text, font=price_font)

        center_x = int(self.display_width) // 2
        spacing = 1
        symbol_h = int(symbol_bbox[3] - symbol_bbox[1])
        price_h = int(price_bbox[3] - price_bbox[1])

        lines = [symbol_h, price_h]
        if change_text:
            change_bbox = draw.textbbox((0, 0), change_text, font=change_font)
            change_h = int(change_bbox[3] - change_bbox[1])
            lines.append(change_h)
        else:
            change_bbox = (0, 0, 0, 0)
            change_h = 0

        total_h = sum(lines) + spacing * (len(lines) - 1)
        start_y = (int(self.display_height) - total_h) // 2

        sym_w = int(symbol_bbox[2] - symbol_bbox[0])
        draw.text((center_x - sym_w // 2, start_y), display_symbol,
                  font=symbol_font, fill=symbol_color)

        prc_w = int(price_bbox[2] - price_bbox[0])
        price_y = start_y + symbol_h + spacing
        draw.text((center_x - prc_w // 2, price_y), price_text,
                  font=price_font, fill=price_color)

        if change_text:
            chg_w = int(change_bbox[2] - change_bbox[0])
            change_y = price_y + price_h + spacing
            draw.text((center_x - chg_w // 2, change_y), change_text,
                      font=change_font, fill=change_color)

        return image

    def create_scrolling_display(self, all_data: Dict[str, Any]) -> Image.Image:
        """Create a wide scrolling strip with all stocks/crypto.

        Routes to the appropriate layout based on self.layout_preset:
          'single' — one stock per slot, original scrolling behaviour (tightened)
          'dual'   — two stocks side-by-side per panel, panels concatenated
          'quad'   — four stocks in a 2×2 grid per panel, panels concatenated
        """
        if not all_data:
            return self.create_error_display()

        if self.layout_preset == 'dual':
            return self._create_panel_strip(all_data, group_size=2,
                                            panel_fn=self.create_dual_panel)
        if self.layout_preset == 'quad':
            return self._create_panel_strip(all_data, group_size=4,
                                            panel_fn=self.create_quad_panel)

        # --- 'single' layout (original behaviour, tighter sizing) ---
        width = int(self.display_width)
        height = int(self.display_height)

        stock_displays = []
        for symbol, data in all_data.items():
            stock_displays.append(self.create_stock_display(symbol, data))

        stock_gap = int(width // 6)
        element_gap = int(width // 8)

        total_width = int(width)  # Leading offset so first stock scrolls in from the right
        total_width += sum(int(d.width) for d in stock_displays)
        total_width += stock_gap * (len(stock_displays) - 1)
        total_width += element_gap * (len(stock_displays) - 1)

        scrolling_image = Image.new('RGB', (int(total_width), height), (0, 0, 0))

        # Start pasting after the leading offset
        current_x = int(width)
        for i, display in enumerate(stock_displays):
            scrolling_image.paste(display, (int(current_x), 0))
            current_x += int(display.width) + int(element_gap)
            if i < len(stock_displays) - 1:
                current_x += int(stock_gap)

        return scrolling_image

    def _create_panel_strip(self, all_data: Dict[str, Any], group_size: int,
                            panel_fn) -> Image.Image:
        """Concatenate full-display panels for dual/quad layouts.

        Stocks are chunked into groups of group_size. Each chunk is rendered
        as one full-display panel by panel_fn. Panels are concatenated
        horizontally with a display_width-wide initial blank gap (matching the
        single-layout strip) so that ScrollHelper fires is_scroll_complete()
        correctly and the display controller can rotate to the next plugin.

        Args:
            all_data:   Ordered dict of symbol→data.
            group_size: Stocks per panel (2 for dual, 4 for quad).
            panel_fn:   Callable(list[(symbol, data)]) → PIL Image.

        Returns:
            Horizontally concatenated strip of panels.
        """
        stocks_list = list(all_data.items())
        groups = [stocks_list[i:i + group_size]
                  for i in range(0, len(stocks_list), group_size)]

        panels = [panel_fn(group) for group in groups]

        # Add the same initial blank gap as the single-layout strip so that
        # ScrollHelper's is_scroll_complete() fires correctly and the display
        # controller can rotate to the next plugin.  Without this gap the strip
        # width equals the content width and the wrap-around logic triggers
        # before total_distance_scrolled reaches total_scroll_width.
        initial_gap = int(self.display_width)
        total_width = sum(p.width for p in panels) + initial_gap
        strip = Image.new('RGB', (total_width, int(self.display_height)), (0, 0, 0))
        x = initial_gap
        for panel in panels:
            strip.paste(panel, (x, 0))
            x += panel.width

        return strip

    # ------------------------------------------------------------------
    # Public setters / accessors
    # ------------------------------------------------------------------

    def set_toggle_chart(self, enabled: bool) -> None:
        """Set whether to show mini charts."""
        self.toggle_chart = enabled
        self.logger.debug("Chart toggle set to: %s", enabled)

    def set_layout_preset(self, preset: str) -> None:
        """Set the display layout preset (single, dual, quad)."""
        self.layout_preset = preset
        self.logger.debug("Layout preset set to: %s", preset)

    def create_error_display(self) -> Image.Image:
        """Create an error display when no data is available."""
        image = Image.new('RGB', (int(self.display_width), int(self.display_height)), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        error_font = self.symbol_font
        error_text = "No Data Available"
        bbox = draw.textbbox((0, 0), error_text, font=error_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (int(self.display_width) - text_width) // 2
        y = (int(self.display_height) - text_height) // 2

        draw.text((x, y), error_text, font=error_font, fill=(255, 0, 0))

        return image

    def get_scroll_helper(self) -> ScrollHelper:
        """Get the scroll helper instance."""
        return self.scroll_helper
