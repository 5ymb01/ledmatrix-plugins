-----------------------------------------------------------------------------------
### Connect with ChuckBuilds

- Show support on Youtube: https://www.youtube.com/@ChuckBuilds
- Stay in touch on Instagram: https://www.instagram.com/ChuckBuilds/
- Want to chat or need support? Reach out on the ChuckBuilds Discord: https://discord.com/invite/uW36dVAtcT
- Feeling Generous? Support the project:
  - Github Sponsorship: https://github.com/sponsors/ChuckBuilds
  - Buy Me a Coffee: https://buymeacoffee.com/chuckbuilds
  - Ko-fi: https://ko-fi.com/chuckbuilds/ 

-----------------------------------------------------------------------------------

# YouTube Stats Plugin

Display YouTube channel statistics on your LED matrix, including channel name, subscriber count, and total views. Perfect for showcasing your YouTube channel metrics or tracking channel growth.

## Features

- **Channel Statistics**: Display subscriber count, total views, and channel name
- **YouTube Logo**: Shows the official YouTube logo alongside statistics
- **Auto-refresh**: Automatically updates channel statistics at configurable intervals
- **Caching**: Efficient API usage with built-in caching
- **Clean Layout**: Organized display with logo on left and stats on right

## Configuration

### Setup

1. **Get YouTube API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the YouTube Data API v3
   - Create credentials (API Key)
   - Copy your API key

2. **Find Your Channel ID**:
   - Go to [YouTube Account Advanced Settings](https://www.youtube.com/account_advanced)
   - Your Channel ID is displayed (format: UCxxxxx...)
   - Or use [this tool](https://commentpicker.com/youtube-channel-id.php)

3. **Configure Plugin**:
   - Add configuration to `config/config.json`
   - Add API key to `config/config_secrets.json`

### Example Configuration

**Main Configuration** (`config/config.json`):
```json
{
  "youtube-stats": {
    "enabled": true,
    "channel_id": "UCxxxxx...",
    "update_interval": 300,
    "display_duration": 15
  }
}
```

**Secrets Configuration** (`config/config_secrets.json`):
```json
{
  "youtube-stats": {
    "api_key": "YOUR_YOUTUBE_API_KEY_HERE"
  }
}
```

### Configuration Options

- `enabled` (boolean): Enable/disable the plugin (default: false)
- `channel_id` (string, required): YouTube channel ID (e.g., UCxxxxx...)
- `update_interval` (integer): Update interval in seconds (60-3600, default: 300)
- `display_duration` (number): Display duration in seconds (5-60, default: 15)
- `api_key` (string, required, in secrets): YouTube Data API v3 key

## Usage

### Basic Setup

Minimum configuration to get started:
```json
{
  "enabled": true,
  "channel_id": "UCxxxxx..."
}
```

With API key in `config/config_secrets.json`:
```json
{
  "youtube-stats": {
    "api_key": "YOUR_API_KEY"
  }
}
```

### Custom Update Frequency

Update channel stats every 5 minutes (300 seconds):
```json
{
  "enabled": true,
  "channel_id": "UCxxxxx...",
  "update_interval": 300
}
```

Update every hour (3600 seconds):
```json
{
  "enabled": true,
  "channel_id": "UCxxxxx...",
  "update_interval": 3600
}
```

### Display Duration

Show stats for 20 seconds:
```json
{
  "enabled": true,
  "channel_id": "UCxxxxx...",
  "display_duration": 20
}
```

## Display Format

The plugin displays:
- **Left side**: YouTube logo (scaled to 60% of display height)
- **Right side**: Three lines of text:
  - Channel name (top)
  - Subscriber count (middle, formatted with commas)
  - Total views (bottom, formatted with commas)

Example display:
```
[YouTube Logo]  ChuckBuilds
                 1,234 subs
                 567,890 views
```

## API Quota

The YouTube Data API v3 has a default quota of 10,000 units per day. Each channel statistics request uses 1 unit. With the default update interval of 300 seconds (5 minutes), you'll make approximately 288 requests per day, well within the free quota.

**Quota Management Tips**:
- Use longer update intervals (600+ seconds) to reduce API calls
- The plugin uses caching to avoid redundant API calls
- Monitor your API usage in the Google Cloud Console

## Troubleshooting

**Plugin not displaying:**
- Verify `enabled` is set to `true` in config
- Check that `channel_id` is correct
- Ensure API key is configured in `config/config_secrets.json`
- Check logs for error messages

**API key errors:**
- Verify API key is correct and not expired
- Ensure YouTube Data API v3 is enabled in Google Cloud Console
- Check API key restrictions in Google Cloud Console
- Verify API key has proper permissions

**Channel ID not found:**
- Double-check channel ID format (should start with UC)
- Verify channel ID at https://www.youtube.com/account_advanced
- Ensure channel is public (private channels may not be accessible)

**Logo not displaying:**
- Verify `assets/youtube_logo.png` exists in project root
- Check file permissions on logo file
- Logo should be in PNG format

**Statistics not updating:**
- Check `update_interval` setting (minimum 60 seconds)
- Verify API quota hasn't been exceeded
- Check network connectivity
- Review logs for API errors

**Display formatting issues:**
- Channel names longer than available space are automatically truncated
- Subscriber and view counts are formatted with commas for readability
- Display adapts to different matrix sizes

## Performance Notes

- Statistics are cached to reduce API calls
- Cache duration matches `update_interval` setting
- Font and logo are loaded once at initialization
- API requests have a 10-second timeout
- Plugin uses efficient image rendering for smooth display

## License

GPL-3.0 License - see main LEDMatrix repository for details.
