import os
import sys
import shutil
from pathlib import Path

# ---- Minimal ANSI styling ----
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"

def box(title):
    bar = "─" * (len(title) + 2)
    print(f"{CYAN}┌{bar}┐{RESET}")
    print(f"{CYAN}│ {BOLD}{title}{RESET}{CYAN} │{RESET}")
    print(f"{CYAN}└{bar}┘{RESET}")

# --- yt-dlp import check ---
try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Run: pip install -U yt-dlp")
    sys.exit(1)

STD_HEIGHTS = [4320, 2160, 1440, 1080, 720, 480, 360, 240, 144]

def pick_format_for_height(h: int) -> str:
    """
    Build a yt-dlp format string that picks the best available <= h.
    Falls back to best <= h if split streams aren't available.
    """
    return f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"

def best_format() -> str:
    # best video + best audio; fallback to best single stream
    return "bv*+ba/b"

def detect_single_video_heights(info) -> list[int]:
    """Return sorted available heights for a single video info dict."""
    heights = set()
    for f in (info.get("formats") or []):
        # count any format that has video
        if f.get("vcodec") and f["vcodec"] != "none":
            h = f.get("height")
            if isinstance(h, int):
                heights.add(h)
    return sorted(heights, reverse=True)

def probe_url(url: str):
    """
    Extract info without downloading. Return (info, is_playlist_like).
    is_playlist_like = True when entries exist (playlist/channel/mix).
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": False,  # allow playlist expansion
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    is_playlist_like = bool(info.get("entries"))
    return info, is_playlist_like

def nicer_outtmpl(base_dir: Path) -> str:
    # Use playlist title if present, else channel/uploader, else a generic folder
    return str(base_dir / "%(playlist_title|channel|uploader|uploader_id|extractor)s/%(title)s.%(ext)s")

def ask_url_and_folder():
    box("YouTube Downloader")
    url = input(f"{BOLD}Paste YouTube video / playlist / channel link:{RESET} ").strip()
    if not url:
        print("No URL provided.")
        sys.exit(1)

    base_dir_input = input(f"{BOLD}Download to folder{RESET} (default: ./downloads): ").strip()
    base_dir = Path(base_dir_input) if base_dir_input else Path("./downloads")
    base_dir.mkdir(parents=True, exist_ok=True)

    return url, base_dir

def ask_resolution_menu_single(heights: list[int]) -> str:
    """
    For a single video: present only the heights that actually exist,
    plus option 1 = Best available.
    """
    print()
    box("Choose Resolution")
    print(f"{GREEN}  1){RESET} Best available (auto)")
    mapping = {}
    idx = 2
    for h in heights:
        print(f"{GREEN}{idx:3d}){RESET} Best ≤ {h}p")
        mapping[str(idx)] = h
        idx += 1
    print(f"{GREEN}{idx:3d}){RESET} Custom cap (enter number like 900)")

    while True:
        choice = input(f"{BOLD}Select 1-{idx}:{RESET} ").strip()
        if choice == "1":
            return best_format()
        if choice == str(idx):
            cap = input("Enter custom height cap (e.g., 900): ").strip()
            if cap.isdigit():
                return pick_format_for_height(int(cap))
            print("Invalid number.")
            continue
        if choice in mapping:
            return pick_format_for_height(mapping[choice])
        print("Invalid choice.")

def ask_resolution_menu_playlist() -> str:
    """
    For playlist/channel: show standard heights as auto caps; per item it will
    pick the best available ≤ your choice. Also offer 'Best available'.
    """
    print()
    box("Choose Resolution (Auto per item)")
    print(f"{GREEN}  1){RESET} Best available per item (auto)")
    mapping = {}
    idx = 2
    for h in STD_HEIGHTS:
        print(f"{GREEN}{idx:3d}){RESET} Best ≤ {h}p (auto cap)")
        mapping[str(idx)] = h
        idx += 1
    print(f"{GREEN}{idx:3d}){RESET} Custom cap (enter number like 900)")

    while True:
        choice = input(f"{BOLD}Select 1-{idx}:{RESET} ").strip()
        if choice == "1":
            return best_format()
        if choice == str(idx):
            cap = input("Enter custom height cap (e.g., 900): ").strip()
            if cap.isdigit():
                return pick_format_for_height(int(cap))
            print("Invalid number.")
            continue
        if choice in mapping:
            return pick_format_for_height(mapping[choice])
        print("Invalid choice.")

def print_ffmpeg_hint():
    if shutil.which("ffmpeg") is None:
        print(f"{YELLOW}Warning:{RESET} ffmpeg not found on PATH. Install ffmpeg so yt-dlp can merge audio+video properly.")

def progress_hook(d):
    status = d.get("status")
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        speed = d.get("speed") or 0
        eta = d.get("eta")
        if total:
            pct = downloaded / total * 100
            sys.stdout.write(f"\r{DIM}Downloading:{RESET} {pct:5.1f}%  {DIM}Speed:{RESET} {int(speed/1024)} KiB/s  {DIM}ETA:{RESET} {eta or '?'}s   ")
            sys.stdout.flush()
    elif status == "finished":
        print(f"\n{DIM}Post-processing (merge/convert)...{RESET}")

def main():
    url, base_dir = ask_url_and_folder()
    print_ffmpeg_hint()

    # Probe URL to decide menu style and (if single video) real heights
    try:
        info, is_playlist_like = probe_url(url)
    except yt_dlp.utils.DownloadError as e:
        print(f"Failed to read metadata: {e}")
        sys.exit(1)

    if is_playlist_like:
        fmt_selector = ask_resolution_menu_playlist()
    else:
        heights = detect_single_video_heights(info)
        if not heights:
            # If no heights detected, fall back to generic menu (rare)
            fmt_selector = ask_resolution_menu_playlist()
        else:
            fmt_selector = ask_resolution_menu_single(heights)

    outtmpl = nicer_outtmpl(base_dir)

    ydl_opts = {
        "outtmpl": {"default": outtmpl},
        "format": fmt_selector,
        "merge_output_format": "mp4",
        "ignoreerrors": True,
        "noplaylist": False,   # allow full playlist downloads
        "retries": 5,
        "fragment_retries": 5,
        "continuedl": True,
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
        ],
        # Nice logging (less noisy)
        "quiet": False,
        "no_warnings": True,
    }

    print()
    box("Downloading")
    print(f"{DIM}Format selector:{RESET} {fmt_selector}")
    print(f"{DIM}Output folder  :{RESET} {base_dir.resolve()}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            print(f"Download error: {e}")
            sys.exit(1)

    print(f"\n{GREEN}✅ Done!{RESET} Saved under: {BOLD}{base_dir.resolve()}{RESET}")
    print(f"{DIM}Folders are named by playlist (or channel/uploader if no playlist).{RESET}")

if __name__ == "__main__":
    main()
