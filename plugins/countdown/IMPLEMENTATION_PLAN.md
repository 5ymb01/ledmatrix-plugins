# Countdown Plugin Implementation Plan

## Overview
Custom countdown plugin for LEDMatrix that allows users to create and manage multiple countdowns with custom images, dates, names, and configurable display settings.

## Plugin Specifications

### Plugin Metadata
- **ID**: `countdown`
- **Name**: "Countdown Display"
- **Category**: `custom`
- **Entry Point**: `manager.py`
- **Class Name**: `CountdownPlugin`

### Core Features
1. Multiple countdown entries with individual enable/disable controls
2. Each countdown includes:
   - Target date (date picker)
   - Display name (text field)
   - Custom uploadable image (PNG, JPG, GIF, BMP)
   - Enable/disable toggle
3. Configurable font settings (size, color, family)
4. Web UI management interface
5. Automatic rotation through enabled countdowns

## File Structure
```
ledmatrix-videoexample/
├── manifest.json              # Plugin metadata
├── config_schema.json         # Configuration schema with file upload
├── manager.py                 # Main plugin implementation
├── requirements.txt           # Python dependencies (if needed)
└── README.md                  # Documentation
```

## Configuration Schema Design

### Image Upload Configuration
Reusing the static-image plugin's approach:
```json
{
  "x-widget": "file-upload",
  "x-upload-config": {
    "endpoint": "/api/v3/plugins/assets/upload",
    "plugin_id": "countdown",
    "max_files": 1,
    "allowed_types": ["image/png", "image/jpeg", "image/bmp", "image/gif"],
    "max_size_mb": 5
  }
}
```

### Countdown Entry Structure
Each countdown entry will have:
```json
{
  "id": "unique-uuid",
  "enabled": true,
  "name": "Birthday",
  "target_date": "2026-06-15",
  "image": {
    "id": "image-uuid",
    "path": "assets/plugins/countdown/uploads/...",
    "uploaded_at": "2026-01-20T..."
  }
}
```

### Font Configuration
```json
{
  "font_family": "press_start",
  "font_size": 8,
  "font_color": [255, 255, 255]
}
```

## Plugin Implementation

### Key Methods

#### `__init__()`
- Initialize countdown list from config
- Set up font configuration
- Register fonts with font manager
- Calculate initial countdown values
- Sort countdowns by display order

#### `update()`
- Recalculate days/hours/minutes remaining for each enabled countdown
- Check if any countdowns have expired
- Update rotation state if needed

#### `display(force_clear=False)`
- Display current countdown with:
  - Background image (scaled and centered)
  - Countdown name at top
  - Time remaining (e.g., "15 Days" or "2h 30m")
- Rotate through enabled countdowns based on display_duration
- Handle countdown expiration (show "Today!" or similar)

#### `_calculate_time_remaining(target_date)`
- Calculate days/hours/minutes from now to target
- Return formatted string and raw values
- Handle past dates gracefully

#### `_load_and_scale_image(image_path)`
- Reuse static-image plugin's image loading logic
- Scale to display size
- Handle transparency
- Preserve aspect ratio
- Center on display

#### `_render_countdown_display()`
- Composite image + text overlay
- Position name at top
- Position countdown value prominently
- Use configured fonts and colors

#### `on_config_change(new_config)`
- Reload countdown list
- Update font settings
- Reload images if changed

#### `validate_config()`
- Validate date formats
- Check image paths exist
- Validate font settings
- Ensure at least one countdown exists

### Display Format Options

**Days Remaining (>24 hours):**
```
┌─────────────────┐
│   [IMAGE]       │
│                 │
│  Birthday       │
│   15 Days       │
└─────────────────┘
```

**Hours Remaining (<24 hours):**
```
┌─────────────────┐
│   [IMAGE]       │
│                 │
│  Birthday       │
│  23h 45m        │
└─────────────────┘
```

**Event Day:**
```
┌─────────────────┐
│   [IMAGE]       │
│                 │
│  Birthday       │
│   TODAY!        │
└─────────────────┘
```

## Integration Points

### From LEDMatrix Base Plugin
- Inherit from `BasePlugin` at path: `src/plugin_system/base_plugin.py`
- Use `display_manager` for rendering
- Use `cache_manager` for caching countdown calculations
- Use `plugin_manager.font_manager` for fonts

### From Static-Image Plugin
- Image upload schema structure (lines 12-139 of config_schema.json)
- Image loading and scaling methods (lines 344-591 of manager.py)
- Image path resolution (lines 344-377)
- Aspect ratio preservation (lines 776-796)
- Background color handling (lines 52-74)

### Font Manager Integration
Reference: web-ui-info plugin (lines 314-342 of static-image/manager.py)
```python
font_manager.register_manager_font(
    manager_id=self.plugin_id,
    element_key=f"{self.plugin_id}.countdown_name",
    family=self.config.get('font_family', 'press_start'),
    size_px=self.config.get('font_size', 8),
    color=tuple(self.config.get('font_color', [255, 255, 255]))
)
```

## Configuration Options

### Top-Level Settings
- `enabled`: bool - Plugin enabled state
- `display_duration`: number - Seconds to show each countdown
- `countdowns`: array - List of countdown entries
- `font_family`: string - Font family name
- `font_size`: number - Font size in pixels
- `font_color`: array [R, G, B] - Text color
- `fit_to_display`: bool - Auto-scale images
- `preserve_aspect_ratio`: bool - Preserve image aspect ratio
- `background_color`: array [R, G, B] - Background color

### Per-Countdown Settings
- `id`: string - Unique identifier
- `enabled`: bool - Show this countdown
- `name`: string - Display name
- `target_date`: string (ISO 8601 date)
- `image`: object - Image upload info
- `display_order`: number - Sort order

## Web UI Integration

### Display Features
- List all countdowns with enable/disable toggles
- Add new countdown button
- Edit/delete countdown buttons
- Real-time preview of countdown calculations
- Image upload per countdown

### API Endpoints Used
- `/api/v3/plugins/assets/upload` - Image uploads (provided by LEDMatrix)
- Standard plugin config endpoints for CRUD operations

## Dependencies

### Python Packages (requirements.txt)
```
Pillow>=9.0.0
python-dateutil>=2.8.0
```

### LEDMatrix Version
- Compatible with: `>=2.0.0`

## Implementation Steps

1. **Create manifest.json**
   - Define plugin metadata
   - Set compatible versions
   - Define display modes

2. **Create config_schema.json**
   - Define countdown array with file upload widgets
   - Define font configuration options
   - Set validation rules

3. **Create manager.py**
   - Implement CountdownPlugin class
   - Inherit from BasePlugin
   - Implement required methods (update, display)
   - Reuse image loading from static-image pattern
   - Implement countdown calculation logic
   - Handle multi-countdown rotation

4. **Create requirements.txt**
   - List Python dependencies

5. **Create README.md**
   - Document usage
   - Provide configuration examples
   - Include screenshots

6. **Testing**
   - Test with single countdown
   - Test with multiple countdowns
   - Test enable/disable functionality
   - Test date calculations (future, today, past)
   - Test image uploads
   - Test font customization

## Edge Cases to Handle

1. **No Enabled Countdowns**: Display message "No active countdowns"
2. **Past Dates**: Show "Expired" or count days since
3. **Invalid Images**: Show placeholder or text-only countdown
4. **Missing Images**: Graceful fallback to text-only
5. **Date Format Errors**: Validate and provide error messages
6. **Very Long Names**: Truncate or wrap text
7. **Very Large/Small Images**: Scale appropriately

## Performance Considerations

1. **Image Caching**: Load images once, cache in memory
2. **Calculation Frequency**: Only recalculate on update() calls
3. **Rotation State**: Track current countdown index efficiently
4. **Font Loading**: Register fonts once at initialization

## Reference Files from LEDMatrix Project

### Core Plugin System
- Base class: `c:\Users\Charles\Documents\LEDmatrix Development folder\LEDMatrix\src\plugin_system\base_plugin.py`
- Plugin manager: `c:\Users\Charles\Documents\LEDmatrix Development folder\LEDMatrix\src\plugin_system\plugin_manager.py`

### Example Plugins
- Static image: `C:/Users/Charles/AppData/Local/Temp/ledmatrix-static-image/manager.py`
- Web UI info: `c:\Users\Charles\Documents\LEDmatrix Development folder\LEDMatrix\plugin-repos\web-ui-info\`

### Schemas
- Manifest schema: `c:\Users\Charles\Documents\LEDmatrix Development folder\LEDMatrix\schema\manifest_schema.json`
- Static-image config: `C:/Users/Charles/AppData/Local/Temp/ledmatrix-static-image/config_schema.json`

## Next Steps

1. Review and approve this plan
2. Begin implementation with manifest.json
3. Create config_schema.json with countdown array structure
4. Implement CountdownPlugin class
5. Test locally on Raspberry Pi
6. Create GitHub repository
7. Test loading as external plugin in LEDMatrix

---

**Ready to proceed with implementation?**
