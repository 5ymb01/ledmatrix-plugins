#!/usr/bin/env python3
"""
Script to convert flight_manager_original.py to plugin format
"""

import re
import os

# Read original file
with open('flight_manager_original.py', 'r') as f:
    content = f.read()

# Add plugin header
header = '''"""
Flight Tracker Plugin for LEDMatrix

Real-time aircraft tracking with ADS-B data, map backgrounds, flight plans, and proximity alerts.
Migrated from feature/flight-tracker-manager branch with flattened configuration structure for plugin compatibility.
"""

import logging
import math
import time
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# Import base plugin class
import sys
# Add parent directory to path to find base plugin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.plugin_system.base_plugin import BasePlugin

# Import aircraft database
from aircraft_database import AircraftDatabase

logger = logging.getLogger(__name__)

'''

# Replace imports section
content = re.sub(r'^import logging.*?^logger = logging\.getLogger\(__name__\)', '', content, flags=re.MULTILINE | re.DOTALL)
content = header + content

# Replace class definition
content = content.replace('class BaseFlightManager:', 'class FlightTrackerPlugin(BasePlugin):')
content = content.replace('    """Base class for flight tracking with common functionality."""', 
                         '    """Flight tracker plugin for LEDMatrix."""')

# Replace __init__ signature
old_init_pattern = r'    def __init__\(self, config: Dict\[str, Any\], display_manager: DisplayManager, cache_manager: CacheManager\):'
new_init = '    def __init__(self, plugin_id: str, config: Dict[str, Any], display_manager, cache_manager, plugin_manager):'
content = re.sub(old_init_pattern, new_init, content)

# Add super().__init__ and update config access
init_replacement = r'''        super().__init__(plugin_id, config, display_manager, cache_manager, plugin_manager)
        self.plugin_manager = plugin_manager
        
        # Config is already flattened (no flight_tracker wrapper)
        # Flight tracker configuration
        self.enabled = self.config.get('enabled', False)
        self.update_interval = self.config.get('update_interval', 5)'''

content = re.sub(
    r'        self\.config = config\n        self\.display_manager = display_manager\n        self\.cache_manager = cache_manager\n        \n        # Flight tracker configuration\n        self\.flight_config = config\.get\(\'flight_tracker\', \{\}\)\n        self\.enabled = self\.flight_config\.get\(\'enabled\', False\)\n        self\.update_interval = self\.flight_config\.get\(\'update_interval\', 5\)',
    init_replacement,
    content
)

# Replace all self.flight_config.get() with self.config.get()
content = re.sub(r'self\.flight_config\.get\(', 'self.config.get(', content)

# Replace flight_config references
content = re.sub(r'self\.flight_config\.get\(', 'self.config.get(', content)

# Update font paths - handle both relative and absolute paths
def fix_font_path(match):
    path = match.group(1)
    # Check if path exists, if not try relative to parent
    if not os.path.exists(path):
        parent_path = os.path.join('..', '..', path)
        if os.path.exists(parent_path):
            return f"ImageFont.truetype('{parent_path}'"
    return match.group(0)

content = re.sub(r"ImageFont\.truetype\('assets/fonts/([^']+)'", fix_font_path, content)

# Remove the three separate manager classes and merge their display methods
# We'll keep BaseFlightManager's display as abstract and merge all three into one

# Find and remove the subclass definitions
content = re.sub(r'class FlightMapManager\(BaseFlightManager\):.*?        self\.display_manager\.update_display\(\)\n\n', 
                '', content, flags=re.DOTALL)

content = re.sub(r'class FlightOverheadManager\(BaseFlightManager\):.*?        self\.display_manager\.update_display\(\)\n\n', 
                '', content, flags=re.DOTALL)

content = re.sub(r'class FlightStatsManager\(BaseFlightManager\):.*?        self\.display_manager\.update_display\(\)\n\n', 
                '', content, flags=re.DOTALL)

# Replace the abstract display method with a unified one
# We'll need to manually merge the three display methods based on display_mode config

# Save converted file
with open('manager.py', 'w') as f:
    f.write(content)

print("Conversion complete. Manual review needed for display() method merging.")

