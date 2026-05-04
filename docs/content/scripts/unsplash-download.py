#!/usr/bin/env python3
"""
Download atmosphere images from Unsplash based on config JSON.
Reads the 'atmosphere' array, skips existing files, downloads missing ones.

Usage:
  source docs/content/.env
  python3 unsplash-download.py --config config/unemploy-story-04-zhangwei-v3.json
  python3 unsplash-download.py --config config/xxx.json --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent


def download_atmosphere(config_path: Path, dry_run: bool = False) -> None:
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    atmosphere = config.get("atmosphere", [])
    if not atmosphere:
        print("No atmosphere entries in config.")
        return

    out_dir = BASE / "assets" / "unsplash" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        print("ERROR: UNSPLASH_ACCESS_KEY not set. Run: source docs/content/.env")
        sys.exit(1)

    for entry in atmosphere:
        entry_id = entry["id"]
        query = entry["query"]
        output = entry["output"]
        out_path = out_dir / output

        if out_path.exists():
            print(f"  SKIP {entry_id}: {output} already exists")
            continue

        if dry_run:
            print(f"  WOULD DOWNLOAD {entry_id}: query='{query}' -> {out_path}")
            continue

        print(f"  DOWNLOAD {entry_id}: query='{query}' -> {output}")
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1, "orientation": "portrait"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            print(f"    WARNING: no results for '{query}'")
            continue

        image_url = results[0]["urls"]["regular"]
        img_resp = requests.get(image_url, timeout=30)
        img_resp.raise_for_status()
        out_path.write_bytes(img_resp.content)
        print(f"    OK: {len(img_resp.content) // 1024}KB")

    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Unsplash atmosphere images")
    parser.add_argument("--config", type=str, required=True, help="v3 config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = BASE / "config" / config_path.name
    if not config_path.exists():
        config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(f"ERROR: config not found: {args.config}")
        sys.exit(1)

    download_atmosphere(config_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
