#!/usr/bin/env python3
"""
Generate static schedule data for the Olympics plugin.

Fetches the complete event schedule from Olympics.com and saves it
as a compact JSON file. This eliminates the need to fetch the 3MB
schedule page during normal operation.

Usage:
    python scripts/generate_schedule.py

The output file (data/static_schedule.json) should be committed to
the repository and updated periodically before/during the Olympics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
    from lxml import html
except ImportError:
    print("Required packages not installed. Run:")
    print("  pip install requests lxml")
    sys.exit(1)

# Olympics configuration
OLYMPICS_URL = "https://www.olympics.com/en/milano-cortina-2026/schedule"
OLYMPICS_NAME = "Milano Cortina 2026"
OLYMPICS_START = "2026-02-06"
OLYMPICS_END = "2026-02-22"

# Output paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR.parent / "data" / "static_schedule.json"

USER_AGENT = "LEDMatrix-Olympics/2.0 (Schedule Generator)"


def fetch_schedule_page() -> str:
    """Fetch the schedule page from Olympics.com."""
    print(f"Fetching schedule from {OLYMPICS_URL}...")

    response = requests.get(
        OLYMPICS_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=30
    )
    response.raise_for_status()

    print(f"  Downloaded {len(response.content):,} bytes")
    return response.text


def extract_schedule_data(page_content: str) -> dict:
    """Extract schedule data from embedded JSON in the page."""
    tree = html.fromstring(page_content)
    scripts = tree.xpath("//script/text()")

    for script in scripts:
        if "result_schedule_data" not in script:
            continue
        if len(script) < 10000:
            continue

        try:
            data = json.loads(script)
            if "result_schedule_data" not in data:
                continue
            return data["result_schedule_data"]
        except json.JSONDecodeError:
            continue

    raise ValueError("Could not find schedule data in page")


def parse_events(schedule_data: dict) -> list:
    """Parse all events from schedule data."""
    events = []

    # Get all day keys
    day_keys = [k for k in schedule_data.keys() if k.startswith("initialSchedule_")]
    print(f"  Found {len(day_keys)} days of events")

    for day_key in sorted(day_keys):
        day_schedule = schedule_data.get(day_key, {})
        units = day_schedule.get("units", [])

        for unit in units:
            event = parse_event(unit)
            if event:
                events.append(event)

    # Sort by start time
    events.sort(key=lambda e: e["start"])

    return events


def parse_event(unit: dict) -> Optional[dict]:
    """Parse a single event unit into a compact format."""
    event_id = unit.get("id", "")
    sport = unit.get("disciplineName", "")
    event_name = unit.get("eventUnitName", "") or unit.get("eventName", "")

    if not sport and not event_name:
        return None

    start_time = unit.get("startDate", "")
    end_time = unit.get("endDate", "")
    venue = unit.get("venueDescription", "") or unit.get("venueLongDescription", "")
    round_name = unit.get("phaseName", "")
    medal_event = unit.get("medalFlag", 0) == 1

    # Mark as final if it's a medal event with no round name
    # Don't append "Final" to existing round names (e.g., single-run medal events)
    if medal_event and not round_name:
        round_name = "Final"

    return {
        "id": event_id,
        "sport": sport,
        "name": event_name,
        "start": start_time,
        "end": end_time,
        "venue": venue,
        "round": round_name,
        "medal": medal_event
    }


def generate_schedule():
    """Main function to generate the static schedule file."""
    print("=" * 60)
    print("Olympics Schedule Generator")
    print("=" * 60)
    print()

    # Fetch and parse
    page_content = fetch_schedule_page()
    schedule_data = extract_schedule_data(page_content)
    events = parse_events(schedule_data)

    print(f"  Parsed {len(events)} total events")

    # Count by sport
    sports = {}
    for event in events:
        sport = event["sport"]
        sports[sport] = sports.get(sport, 0) + 1

    print("\nEvents by sport:")
    for sport, count in sorted(sports.items(), key=lambda x: -x[1])[:10]:
        print(f"  {sport}: {count}")

    # Build output structure
    output = {
        "meta": {
            "games_name": OLYMPICS_NAME,
            "games_start": OLYMPICS_START,
            "games_end": OLYMPICS_END,
            "generated_at": datetime.now().astimezone().isoformat(),
            "event_count": len(events),
            "sport_count": len(sports)
        },
        "events": events
    }

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))  # Compact JSON

    file_size = OUTPUT_FILE.stat().st_size
    print(f"\nOutput written to: {OUTPUT_FILE}")
    print(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print()
    print("This file should be committed to the repository.")


if __name__ == "__main__":
    generate_schedule()
