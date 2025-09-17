#!/usr/bin/env python3
"""
Interactive YouTube playlist downloader using yt-dlp.

What it does:
- Prompts for playlist URL
- Prompts for quality (default = max). Options: max, 2160p, 1440p, 1080p, 720p, 480p, custom
- Creates a folder named exactly like the playlist (sanitized)
- Downloads multiple videos in parallel (thread pool)
- Skips already-downloaded items via an archive file
- Merges into MP4 when possible (fallback note in summary)

Tip: Re-run the script any time; finished items are skipped.

Respect the content provider’s Terms of Service and local laws.
"""

import concurrent.futures
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from yt_dlp import YoutubeDL

# ---------- Utilities ----------

def sanitize_folder_name(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]+', " ", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name or "playlist"

def check_binary(name: str) -> bool:
    return shutil.which(name) is not None

def prompt(text: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{text}{suffix}: ").strip()
    return val or (default or "")

def parse_quality_to_fmt(q: str) -> str:
    """
    Convert a human-friendly quality like 'max', '1080p', '720', or 'custom:900'
    into a yt-dlp format selector.
    """
    q = q.strip().lower()
    if q in ("", "max", "best", "highest"):
        # truly highest available
        return "bv*+ba/b"

    # Common fixed tiers
    match_map = {
        "2160p": 2160, "2160": 2160, "4k": 2160,
        "1440p": 1440, "1440": 1440, "2k": 1440,
        "1080p": 1080, "1080": 1080,
        "720p": 720,   "720": 720,
        "480p": 480,   "480": 480,
        "360p": 360,   "360": 360,
    }
    if q in match_map:
        h = match_map[q]
        return f"bv*[height<={h}]+ba/b[height<={h}]"

    # Custom like "custom:900" or "900"
    m = re.match(r"(custom:)?(\d{3,4})p?$", q)
    if m:
        h = int(m.group(2))
        return f"bv*[height<={h}]+ba/b[height<={h}]"

    # Fallback to max if unrecognized
    print("Unrecognized quality; defaulting to max.")
    return "bv*+ba/b"

def fetch_playlist_index(url: str) -> Tuple[str, List[Tuple[int, str]]]:
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,   # fast list; we’ll do real extraction per video later
        "skip_download": True,
        "noplaylist": False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise RuntimeError("Could not extract playlist info.")

    # Handle single video gracefully
    if info.get("_type") != "playlist":
        title = sanitize_folder_name(info.get("title") or "single_video")
        return title, [(1, info.get("webpage_url") or url)]

    title = sanitize_folder_name(info.get("title") or "playlist")
    tasks: List[Tuple[int, str]] = []
    for idx, e in enumerate(info.get("entries") or [], start=1):
        vid_url = e.get("url")
        if not vid_url and e.get("id"):
            vid_url = f"https://www.youtube.com/watch?v={e['id']}"
        if vid_url:
            tasks.append((idx, vid_url))
    if not tasks:
        raise RuntimeError("No entries found in playlist.")
    return title, tasks

def download_one(task: Tuple[int, str], playlist_dir: Path, fmt: str,
                 concurrent_frags: int, retries: int) -> Tuple[int, bool, str]:
    index, url = task
    outtmpl = str(playlist_dir / f"{index:03d} - %(title).200B.%(ext)s")
    archive = str(playlist_dir / "_archive.txt")

    ydl_opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "noplaylist": True,
        "retries": retries,
        "fragment_retries": retries,
        "concurrent_fragment_downloads": concurrent_frags,
        "download_archive": archive,        # skip completed
        # Prefer MP4 for compatibility; yt-dlp may fallback to mkv if needed.
        "merge_output_format": "mp4",
        "windowsfilenames": True,
        "outtmpl_na_placeholder": "NA",
        "quiet": False,
        "newline": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return index, True, "ok"
    except Exception as e:
        return index, False, str(e)

# ---------- Main flow ----------

def main():
    print("=== YouTube Playlist Downloader (yt-dlp, friendly) ===\n")

    # Basic checks
    if not check_binary("ffmpeg"):
        print("⚠️  ffmpeg not found in PATH. Merging audio+video will fail.")
        print("    Install ffmpeg and ensure it's in PATH, then re-run.\n")

    playlist_url = prompt("Paste YouTube playlist URL", "")
    if not playlist_url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    print("\nQuality options:")
    print("  - max (default)   → highest available")
    print("  - 2160p / 1440p / 1080p / 720p / 480p / 360p")
    print("  - custom:N        → e.g., custom:900 caps at ≤900p")
    quality_in = prompt("Choose quality", "max")
    fmt = parse_quality_to_fmt(quality_in)

    # Parallelism
    try:
        default_workers = max(4, os.cpu_count() or 4)
    except Exception:
        default_workers = 4
    workers_str = prompt("Parallel video downloads (workers)", str(default_workers))
    try:
        workers = max(1, int(workers_str))
    except ValueError:
        workers = default_workers

    # Fragments per video
    frag_str = prompt("Concurrent fragments per video", "4")
    try:
        concurrent_frags = max(1, int(frag_str))
    except ValueError:
        concurrent_frags = 4

    # Output location
    output_root_str = prompt("Output root folder (blank = current)", "")
    output_root = Path(output_root_str).expanduser().resolve() if output_root_str else Path.cwd()

    print("\nFetching playlist info...")
    title, tasks = fetch_playlist_index(playlist_url)
    playlist_dir = output_root / title
    playlist_dir.mkdir(parents=True, exist_ok=True)

    print("\nSummary:")
    print(f"  Playlist : {title}")
    print(f"  Items    : {len(tasks)}")
    print(f"  Save to  : {playlist_dir}")
    print(f"  Quality  : {quality_in}  →  {fmt}")
    print(f"  Workers  : {workers}")
    print(f"  Frags    : {concurrent_frags}\n")

    # Confirm start
    _ = prompt("Press Enter to start (or Ctrl+C to cancel)")

    successes, failures = 0, 0
    failed_items: List[Tuple[int, str, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [
            ex.submit(
                download_one, t, playlist_dir, fmt, concurrent_frags, retries=10
            ) for t in tasks
        ]
        for fut in concurrent.futures.as_completed(futs):
            idx, ok, msg = fut.result()
            if ok:
                successes += 1
                print(f"[{idx:03d}] ✅ done")
            else:
                failures += 1
                failed_items.append((idx, tasks[idx-1][1], msg))
                print(f"[{idx:03d}] ❌ {msg}")

    print("\n=== Finished ===")
    print(f"Downloaded successfully: {successes}")
    print(f"Failed               : {failures}")
    if failures:
        print("\nFailed items:")
        for idx, url, msg in sorted(failed_items):
            print(f"  - #{idx:03d} {url}\n    ↳ {msg}")
        print("\nTip: Re-run the script; completed videos are skipped (_archive.txt).")
        print("If some merges fail with MP4, consider switching container to MKV by")
        print("removing 'merge_output_format' or setting it to 'mkv' in the code.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
