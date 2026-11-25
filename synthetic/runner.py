"""
Standalone CLI tool to run synthetic scenarios against the Project 07 Ingestion API.
Usage:
    python -m synthetic.runner --url http://127.0.0.1:8000 --scenario normal --campaign demo-01
"""

import argparse
import sys
from typing import List
import httpx

from .scenarios import generate_normal_scenario, generate_stalled_scenario


def run_scenario(api_url: str, scenario_name: str, campaign_id: str, run_id: str, api_key: str | None = None):
    print(f"[*] Initializing scenario '{scenario_name}' for Campaign='{campaign_id}', Run='{run_id}'...")

    if scenario_name == "normal":
        events = generate_normal_scenario(campaign_id=campaign_id, run_id=run_id)
    elif scenario_name == "stalled":
        events = generate_stalled_scenario(campaign_id=campaign_id, run_id=run_id)
    else:
        print(f"[!] Unknown scenario '{scenario_name}'. Available: normal, stalled")
        sys.exit(1)

    print(f"[*] Submitting {len(events)} events via batch endpoint to {api_url}...")
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        resp = httpx.post(
            f"{api_url.rstrip('/')}/api/v1/events/batch",
            json={"events": events},
            headers=headers,
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"[+] Ingestion complete! Submitted: {data['total_submitted']}, Accepted: {data['accepted_count']}, Deduplicated: {data['deduplicated_count']}, Failed: {data['failed_count']}")
        else:
            print(f"[!] Ingestion failed with status {resp.status_code}: {resp.text}")
    except Exception as exc:
        print(f"[!] Error connecting to API: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project 07 Synthetic Scenario Runner")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of Ingestion API")
    parser.add_argument("--scenario", default="normal", choices=["normal", "stalled"], help="Scenario to execute")
    parser.add_argument("--campaign", default="campaign-demo-alpha", help="Campaign ID")
    parser.add_argument("--run", default="run-01", help="Run ID")
    parser.add_argument("--api-key", default=None, help="Optional API Key")

    args = parser.parse_args()
    run_scenario(
        api_url=args.url,
        scenario_name=args.scenario,
        campaign_id=args.campaign,
        run_id=args.run,
        api_key=args.api_key,
    )
