# LEDMatrix Official Plugins Registry

> Official plugin registry for [LEDMatrix](https://github.com/ChuckBuilds/LEDMatrix) · [Installation](#-installation) · [Documentation](#-documentation) · [Support](#-support)

---

## 🚀 Quick Install

**Web Interface (Recommended):**
1. Open `http://your-pi-ip:5000`
2. Go to **Plugin Store** tab
3. Browse & click **Install**

**API:**
```bash
curl -X POST http://your-pi-ip:5050/api/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"plugin_id": "football-scoreboard"}'
```

---

## 📦 Available Plugins

### 🏆 Sports (7)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Football Scoreboard](https://github.com/ChuckBuilds/ledmatrix-football-scoreboard)** | NFL & NCAA Football | NFL, NCAA FB |
| **[Hockey Scoreboard](https://github.com/ChuckBuilds/ledmatrix-hockey-scoreboard)** | NHL & NCAA Hockey | NHL, NCAA M/W |
| **[Basketball Scoreboard](https://github.com/ChuckBuilds/ledmatrix-basketball-scoreboard)** | NBA & NCAA Basketball | NBA, NCAA M/W, WNBA |
| **[Baseball Scoreboard](https://github.com/ChuckBuilds/ledmatrix-baseball-scoreboard)** | MLB & NCAA Baseball | MLB, MiLB, NCAA |
| **[Soccer Scoreboard](https://github.com/ChuckBuilds/ledmatrix-soccer-scoreboard)** | Global Soccer Leagues | Premier League, La Liga, Bundesliga, Serie A, Ligue 1, MLS |
| **[Odds Ticker](https://github.com/ChuckBuilds/ledmatrix-odds-ticker)** | Betting Odds & Lines | NFL, NBA, MLB, NCAA |
| **[Sports Leaderboard](https://github.com/ChuckBuilds/ledmatrix-leaderboard)** | League Standings | Rankings, records, conference standings |

### 💰 Financial (2)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Stocks Ticker](https://github.com/ChuckBuilds/ledmatrix-stocks)** | Stock & Crypto Prices | Real-time prices, charts, volume |
| **[Stock News](https://github.com/ChuckBuilds/ledmatrix-stock-news)** | Financial Headlines | Stock-specific news, RSS feeds |

### ⏰ Time & Calendar (2)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Simple Clock](https://github.com/ChuckBuilds/ledmatrix-clock-simple)** | Time and date display | Basic clock display |
| **[Google Calendar](https://github.com/ChuckBuilds/ledmatrix-calendar)** | Event calendar display | Google Calendar integration |

### 🌤️ Weather (1)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Weather Display](https://github.com/ChuckBuilds/ledmatrix-weather)** | Weather forecasts and conditions | Current, hourly, daily forecasts |

### 📱 Media (2)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Music Player](https://github.com/ChuckBuilds/ledmatrix-music)** | Now playing with album art | Music player integration |
| **[Static Image Display](https://github.com/ChuckBuilds/ledmatrix-static-image)** | Image slideshow with effects | Image display with transitions |

### 📝 Text & Content (4)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Scrolling Text Display](https://github.com/ChuckBuilds/ledmatrix-text-display)** | Custom text and messages | Custom text scrolling |
| **[News Ticker](https://github.com/ChuckBuilds/ledmatrix-news)** | RSS news headlines | RSS feed integration |
| **[Of The Day](https://github.com/ChuckBuilds/ledmatrix-of-the-day)** | Daily quotes and verses | Daily inspirational content |
| **[Flights](https://github.com/ChuckBuilds/ledmatrix-flights)** | ADSB Flight Map & Stats | Flight tracking display |

### 🎄 Holiday (1)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Christmas Countdown](https://github.com/ChuckBuilds/ledmatrix-christmas-countdown)** | Festive Christmas countdown with tree | Holiday countdown timer |

### 🎮 Development (1)

| Plugin | Description | Details |
|--------|-------------|---------|
| **[Hello World](https://github.com/ChuckBuilds/ledmatrix-hello-world)** | Plugin development example | Template for plugin development |

---

## 📖 Installation & Usage


### Plugin Store (Recommended)

The **Plugin Store** in the LEDMatrix web interface automatically fetches the latest plugins from this registry:
- Browse and search plugins
- One-click installation
- Automatic updates
- Configuration management

### Manual Installation

Clone plugin repositories directly:

```bash
git clone https://github.com/ChuckBuilds/ledmatrix-football-scoreboard.git
cp -r ledmatrix-football-scoreboard /path/to/LEDMatrix/plugins/
```

> **Note:** See individual plugin repositories for detailed setup instructions and configuration.

---

## 🔌 Installing 3rd Party Plugins

LEDMatrix supports installing plugins from any GitHub repository, not just the official registry. This allows you to use community plugins or your own custom plugins.

### Via Plugin Manager Tab

1. Open the LEDMatrix web interface (`http://your-pi-ip:5000`)
2. Navigate to **Plugin Manager** tab
3. Scroll to **"Install from GitHub"** section

### Single Plugin Installation

Install a plugin directly from its GitHub repository:

1. Enter the GitHub repository URL (e.g., `https://github.com/user/ledmatrix-my-plugin`)
2. Optionally specify a branch (defaults to `main` if not provided)
3. Click **Install**

The plugin will be downloaded, installed, and automatically discovered by LEDMatrix.

### Registry/Monorepo Installation

Browse and install plugins from registry-style repositories (like this one):

1. Enter a registry repository URL (e.g., `https://github.com/user/ledmatrix-plugins`)
2. Click **Load Registry** to browse available plugins
3. Click **Install** on any plugin you want
4. Optionally **Save Repository** for automatic loading on future visits

### Post-Installation

After installation:
- Plugin appears in the installed plugins list
- Enable via toggle switch in Plugin Manager
- Configure via Plugin Settings tab
- May require restarting LEDMatrix service: `sudo systemctl restart ledmatrix`

### Important Notes

- **Custom Badge**: 3rd party plugins show a "Custom" badge to indicate they're not from the official registry
- **Code Review**: Review plugin code before installing from untrusted sources
- **Not Tracked**: Plugins installed via URL are not tracked in the official registry
- **Updates**: Manual updates required unless you use a saved repository

---

## 🔧 For Maintainers

### Registry Structure

- `plugins.json` - Plugin metadata and download URLs
- `update_registry.py` - Automated version checker
- `config_secrets.template.json` - GitHub API token template

### Updating Plugin Versions

```bash
python update_registry.py
```

**GitHub API Token (Recommended):**

Avoid rate limits (60 → 5,000 requests/hour):

1. Copy template: `cp config_secrets.template.json config_secrets.json`
2. Add token to `config_secrets.json`
3. Get token: [Create token](https://github.com/settings/tokens/new) (no scopes needed)

**Alternatives:**
- Environment: `$env:GITHUB_TOKEN = "your_token"`
- CLI: `python update_registry.py --token your_token`

---

## 🎯 Key Features

- **Plugin System**: All plugins inherit from `BasePlugin` for consistent behavior
- **Configuration**: JSON schema validation, web UI config, environment variable support
- **Display Modes**: Live, Recent, Upcoming, Ticker
- **Background Services**: Non-blocking API calls, intelligent caching, retry logic
- **Web Integration**: Full UI support for installation, configuration, and management

---

## 📚 Documentation

- **[Plugin Registry Setup Guide](docs/PLUGIN_REGISTRY_SETUP_GUIDE.md)** - Maintaining the registry
- **[Plugin Store User Guide](docs/PLUGIN_STORE_USER_GUIDE.md)** - Using the plugin store
- **[Plugin Store Implementation](docs/PLUGIN_STORE_IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[Quick Reference](docs/PLUGIN_STORE_QUICK_REFERENCE.md)** - Command reference

---

## 🤝 Contributing

### Submit a Plugin
See [SUBMISSION.md](SUBMISSION.md) for guidelines and [VERIFICATION.md](VERIFICATION.md) for the review process.

### Create a Plugin
- **[Plugin Developer Guide](https://github.com/ChuckBuilds/LEDMatrix/wiki/Plugin-Development)** - Complete development guide
- **[Hello World Plugin](https://github.com/ChuckBuilds/ledmatrix-hello-world)** - Starter template

---

## 🛠️ 3rd Party Plugin Development

Want to create your own plugin for LEDMatrix? Here's what you need to know for your plugin to be discovered and loaded by the system.

### Required Files

Your plugin repository must contain:

- **`manifest.json`** - Plugin metadata and configuration (required)
- **Entry point file** - Python file containing your plugin class (default: `manager.py`)
- **Plugin class** - Must inherit from `BasePlugin` and implement required methods

Optional but recommended:
- `requirements.txt` - Python dependencies
- `config_schema.json` - Configuration validation schema
- `README.md` - Documentation for users

### Plugin Discovery

LEDMatrix automatically discovers plugins by:

1. Scanning the `plugins/` directory for subdirectories
2. Looking for `manifest.json` in each subdirectory
3. Reading the manifest to get plugin metadata
4. Loading plugins that are enabled in configuration

**Directory naming:** The plugin directory name should match the `id` field in your manifest.json.

### Manifest Requirements

Your `manifest.json` must include these required fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique plugin identifier (used as directory name) |
| `name` | string | Human-readable plugin name |
| `class_name` | string | Name of your plugin class (must match class in entry point) |
| `compatible_versions` | array | LEDMatrix version compatibility (e.g., `[">=2.0.0"]`) |

**Common optional fields:**
- `version` - Plugin version (semver format)
- `author` - Plugin author name
- `description` - Brief description
- `entry_point` - Entry point file (default: `manager.py`)
- `display_modes` - Array of display mode names

See the [manifest schema](https://github.com/ChuckBuilds/LEDMatrix/blob/main/schema/manifest_schema.json) for the complete field reference and validation rules.

### Base Plugin Requirements

Your plugin class must:

1. **Inherit from `BasePlugin`**:
   ```python
   from src.plugin_system.base_plugin import BasePlugin
   
   class MyPlugin(BasePlugin):
       pass
   ```

2. **Implement required methods**:
   - `update()` - Fetch/update plugin data (called based on `update_interval`)
   - `display(force_clear=False)` - Render plugin content to display

3. **Match class name**: The class name must exactly match the `class_name` in your manifest.json

### Repository Structure

Recommended plugin repository structure:

```
my-plugin/
├── manifest.json          # Plugin metadata (required)
├── manager.py             # Plugin class (required)
├── requirements.txt       # Python dependencies (optional)
├── config_schema.json     # Config validation (optional)
├── README.md              # Documentation (recommended)
└── assets/                # Plugin assets (optional)
    └── logos/
```

**Repository types:**
- **Standalone plugin repo**: Repository contains a single plugin (manifest.json at root)
- **Monorepo**: Repository contains multiple plugins (specify `plugin_path` during installation)

### Getting Started

1. Review the [Plugin Developer Guide](https://github.com/ChuckBuilds/LEDMatrix/wiki/Plugin-Development) for detailed documentation
2. Check out the [Hello World plugin](https://github.com/ChuckBuilds/ledmatrix-hello-world) as a starter template
3. See existing plugins in this registry for real-world examples

---

## 📄 License

GNU General Public License v3.0 - see [LICENSE](LICENSE) for details.

---

## 💬 Support & Community

- **Discord**: [Join the community](https://discord.gg/uW36dVAtcT)
- **Issues**: [Report plugin issues](https://github.com/ChuckBuilds/ledmatrix-plugins/issues)
- **LEDMatrix**: [Main repository](https://github.com/ChuckBuilds/LEDMatrix)

### Connect with ChuckBuilds

- **YouTube**: [@ChuckBuilds](https://www.youtube.com/@ChuckBuilds)
- **Instagram**: [@ChuckBuilds](https://www.instagram.com/ChuckBuilds/)
- **Support the Project**:
  - [GitHub Sponsorship](https://github.com/sponsors/ChuckBuilds)
  - [Buy Me a Coffee](https://buymeacoffee.com/chuckbuilds)
  - [Ko-fi](https://ko-fi.com/chuckbuilds/)

---

> **Note**: Plugins are actively developed. Report bugs or feature requests on individual plugin repositories.
