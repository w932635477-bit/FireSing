#!/usr/bin/env python3
"""Download atmosphere stock photos from Unsplash for video production.

Usage:
  source docs/content/.env
  python3 unsplash-downloader.py --query "empty warehouse" --output ../assets/unsplash/test.jpg
  python3 unsplash-downloader.py --config unsplash-manifest.json
  python3 unsplash-downloader.py --config unsplash-manifest.json --list-only
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import urllib.request


def search_photos(
    query: str,
    access_key: str,
    per_page: int = 10,
    orientation: str = "portrait",
) -> list[dict]:
    """Search Unsplash for photos matching query."""
    url = (
        f"https://api.unsplash.com/search/photos?"
        f"query={query}&per_page={per_page}&orientation={orientation}"
    )
    req = urllib.request.Request(url, headers={
        "Authorization": f"Client-ID {access_key}",
        "Accept-Version": "v1",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get("results", [])


def download_photo(photo_url: str, output_path: Path) -> bool:
    """Download photo from URL to local file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(photo_url)
    with urllib.request.urlopen(req) as resp:
        output_path.write_bytes(resp.read())
    return output_path.exists()


def pick_best(photos: list[dict], prefer_no_people: bool = True) -> dict | None:
    """Pick best photo: prefer no people, high likes."""
    scored: list[tuple[int, dict]] = []
    for p in photos:
        score = p.get("likes", 0)
        if prefer_no_people:
            desc = (p.get("description") or "").lower()
            alt = (p.get("alt_description") or "").lower()
            people_words = ["person", "people", "man", "woman", "face", "portrait"]
            if any(w in desc or w in alt for w in people_words):
                score -= 100
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Unsplash stock photos")
    parser.add_argument("--query", type=str, help="Search query (English)")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--config", type=str, help="Manifest JSON with batch downloads")
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument(
        "--list-only", action="store_true",
        help="Show search results without downloading",
    )
    args = parser.parse_args()

    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        print("ERROR: UNSPLASH_ACCESS_KEY not set. Run: source docs/content/.env")
        sys.exit(1)

    if args.config:
        with open(args.config) as f:
            manifest = json.load(f)
        for item in manifest.get("downloads", []):
            query = item["query"]
            output = Path(item["output"])
            print(f"\n--- {query} -> {output.name} ---")
            photos = search_photos(query, access_key, args.per_page)
            if args.list_only:
                for i, p in enumerate(photos[:5]):
                    desc = (p.get("alt_description") or "?")[:60]
                    print(f"  {i+1}. {desc} | {p['likes']} likes | {p['urls']['regular']}")
                continue
            best = pick_best(photos)
            if best:
                url = best["urls"]["regular"]
                ok = download_photo(url, output)
                print(f"  -> {output} ({'OK' if ok else 'FAIL'})")
            else:
                print("  -> No suitable photo found")
            time.sleep(1)
        return

    if args.query and args.output:
        photos = search_photos(query := args.query, access_key, args.per_page)
        if args.list_only:
            for i, p in enumerate(photos[:5]):
                desc = (p.get("alt_description") or "?")[:60]
                print(f"  {i+1}. {desc} | {p['likes']} likes | {p['urls']['regular']}")
            return
        best = pick_best(photos)
        if best:
            url = best["urls"]["regular"]
            ok = download_photo(url, Path(args.output))
            print(f"{'OK' if ok else 'FAIL'}: {args.output}")
        else:
            print("No suitable photo found")
            sys.exit(1)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
