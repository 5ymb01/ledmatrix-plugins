#!/bin/bash
#
# Archive individual plugin repositories on GitHub.
#
# This script:
# 1. Prepends a redirect notice to each repo's README
# 2. Updates the repo description
# 3. Archives the repo (makes it read-only)
#
# Prerequisites: gh CLI authenticated with repo access
#
# Usage:
#   ./scripts/archive_old_repos.sh          # Dry run (default)
#   ./scripts/archive_old_repos.sh --apply  # Actually archive repos
#

set -euo pipefail

OWNER="ChuckBuilds"
MONOREPO_URL="https://github.com/ChuckBuilds/ledmatrix-plugins"
DRY_RUN=true

if [[ "${1:-}" == "--apply" ]]; then
    DRY_RUN=false
    echo "=== LIVE MODE: Changes will be applied ==="
else
    echo "=== DRY RUN: No changes will be made (use --apply to execute) ==="
fi
echo

# Map: repo name -> plugin directory in monorepo
declare -A REPOS
REPOS=(
    ["ledmatrix-hello-world"]="plugins/hello-world"
    ["ledmatrix-clock-simple"]="plugins/clock-simple"
    ["ledmatrix-weather"]="plugins/ledmatrix-weather"
    ["ledmatrix-static-image"]="plugins/static-image"
    ["ledmatrix-text-display"]="plugins/text-display"
    ["ledmatrix-of-the-day"]="plugins/of-the-day"
    ["ledmatrix-music"]="plugins/ledmatrix-music"
    ["ledmatrix-calendar"]="plugins/calendar"
    ["ledmatrix-hockey-scoreboard"]="plugins/hockey-scoreboard"
    ["ledmatrix-football-scoreboard"]="plugins/football-scoreboard"
    ["ledmatrix-basketball-scoreboard"]="plugins/basketball-scoreboard"
    ["ledmatrix-baseball-scoreboard"]="plugins/baseball-scoreboard"
    ["ledmatrix-soccer-scoreboard"]="plugins/soccer-scoreboard"
    ["ledmatrix-odds-ticker"]="plugins/odds-ticker"
    ["ledmatrix-leaderboard"]="plugins/ledmatrix-leaderboard"
    ["ledmatrix-news"]="plugins/news"
    ["ledmatrix-stock-news"]="plugins/stock-news"
    ["ledmatrix-stocks"]="plugins/ledmatrix-stocks"
    ["ledmatrix-flights"]="plugins/ledmatrix-flights"
    ["ledmatrix-christmas-countdown"]="plugins/christmas-countdown"
    ["ledmatrix-olympics-countdown"]="plugins/olympics"
    ["ledmatrix-youtube-stats"]="plugins/youtube-stats"
    ["ledmatrix-7-segment-clock"]="plugins/7-segment-clock"
    ["ledmatrix-countdown"]="plugins/countdown"
    ["ledmatrix-mqtt-notifications"]="plugins/mqtt-notifications"
)

for repo in $(echo "${!REPOS[@]}" | tr ' ' '\n' | sort); do
    plugin_path="${REPOS[$repo]}"
    monorepo_link="${MONOREPO_URL}/tree/main/${plugin_path}"

    echo "Processing: ${repo}"
    echo "  -> ${monorepo_link}"

    if $DRY_RUN; then
        echo "  [dry-run] Would update README, description, and archive"
        echo
        continue
    fi

    # 1. Update README with redirect notice
    # Fetch current README
    current_readme=$(gh api "repos/${OWNER}/${repo}/contents/README.md" \
        --jq '.content' 2>/dev/null | base64 -d 2>/dev/null || echo "")
    readme_sha=$(gh api "repos/${OWNER}/${repo}/contents/README.md" \
        --jq '.sha' 2>/dev/null || echo "")

    notice="> **This repository has been archived.** This plugin has moved to the [LEDMatrix Plugins monorepo](${MONOREPO_URL}).
> Find it at [\`${plugin_path}/\`](${monorepo_link}).
>
> Existing installations will automatically update from the new location.

---

"

    if [[ -n "$readme_sha" ]]; then
        new_readme="${notice}${current_readme}"
        encoded=$(echo -n "$new_readme" | base64 -w 0)

        gh api -X PUT "repos/${OWNER}/${repo}/contents/README.md" \
            -f message="Add redirect notice to monorepo" \
            -f content="$encoded" \
            -f sha="$readme_sha" \
            --silent 2>/dev/null && echo "  Updated README" || echo "  Failed to update README"
    else
        echo "  No README found, skipping README update"
    fi

    # 2. Update repo description
    gh api -X PATCH "repos/${OWNER}/${repo}" \
        -f description="[ARCHIVED] Moved to ${MONOREPO_URL}" \
        --silent 2>/dev/null && echo "  Updated description" || echo "  Failed to update description"

    # 3. Archive the repo
    gh api -X PATCH "repos/${OWNER}/${repo}" \
        -F archived=true \
        --silent 2>/dev/null && echo "  Archived" || echo "  Failed to archive"

    echo
done

echo "Done!"
if $DRY_RUN; then
    echo "This was a dry run. Use --apply to execute."
fi
