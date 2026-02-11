#!/usr/bin/env python3
"""Explore Olympics.com data structure for medal winners."""

import json
import requests
from lxml import html

URL = "https://www.olympics.com/en/milano-cortina-2026/medals"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def main():
    """Fetch and explore medal data structure from Olympics.com."""
    response = requests.get(URL, headers=HEADERS, timeout=15)
    print(f"Status: {response.status_code}")

    tree = html.fromstring(response.content)
    scripts = tree.xpath("//script/text()")

    for script in scripts:
        if "result_medals_data" in script and len(script) > 1000:
            data = json.loads(script)
            medals_data = data["result_medals_data"]

            print("Top-level keys:", list(medals_data.keys()))

            initial = medals_data.get("initialMedals", {})
            print("initialMedals keys:", list(initial.keys()))

            standings = initial.get("medalStandings", {})
            table = standings.get("medalsTable", [])

            if table:
                first = table[0]
                org = first.get("organisation")
                print(f"\nFirst country: {org}")

                discs = first.get("disciplines", [])
                if discs:
                    d = discs[0]
                    print(f"First discipline: {d.get('name')}")

                    winners = d.get("medalWinners", [])
                    print(f"Medal winners: {len(winners)}")

                    if winners:
                        print("\nFirst winner structure:")
                        print(json.dumps(winners[0], indent=2))

                        print("\n\nAll recent medal winners (first 5):")
                        all_winners = []
                        for country in table[:10]:
                            for disc in country.get("disciplines", []):
                                for w in disc.get("medalWinners", []):
                                    all_winners.append(w)

                        # Sort by date
                        all_winners.sort(key=lambda x: x.get("date", ""), reverse=True)
                        for w in all_winners[:5]:
                            medal = w.get("medalType", "").replace("ME_", "")
                            name = w.get("competitorDisplayName", "Unknown")
                            event_desc = w.get("eventDescription", "")
                            winner_org = w.get("organisation", "")
                            print(f"  {medal}: {name} ({winner_org}) - {event_desc}")
            break


if __name__ == "__main__":
    main()
