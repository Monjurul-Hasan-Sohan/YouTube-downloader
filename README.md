# 📥 yt-dlp-menu-downloader

Menu-driven YouTube downloader (video / playlist / channel) powered by **yt-dlp** + **ffmpeg**.
Pick resolutions from a **numbered menu**, auto-adapt to each video’s available qualities, and save files into a folder named after the **playlist / channel**.

> ⚠️ Download content only where you have rights to do so. Respect YouTube’s Terms and local laws.

---

## ✨ Features

* **One script, friendly UI** — paste a link, pick a number, done.
* **Video / Playlist / Channel** — handles them all.
* **Smart quality selection**

  * Single video: lists only **actually available** heights (e.g., 360p/720p/1080p).
  * Playlist/Channel: choose a **cap** (4K→144p) and it auto-picks the best ≤ cap per item.
* **Organized output** — saves into `downloads/<Playlist or Channel>/<Title>.mp4`.
* **Cross-platform** — Windows, macOS, Linux.

---

## 🧰 Requirements

* **Python** 3.8+
* **ffmpeg** on your system `PATH` (yt-dlp uses it to merge audio + video)
* **yt-dlp** (Python package)

---

## 🚀 Quick Start

### 1) Install Python (if you don’t have it)

**Windows**

* Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
  ✅ Check **“Add Python to PATH”** during install.
* Verify:

  ```powershell
  py --version
  ```

  (If `py` fails, try `python --version`)

**macOS**

```bash
# Install Homebrew (if needed)
 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
python3 --version
```

**Ubuntu/Debian Linux**

```bash
sudo apt update
sudo apt install -y python3 python3-pip
python3 --version
```

---

### 2) Install ffmpeg

**Windows (choose one)**

```powershell
# Scoop (recommended)
scoop install ffmpeg
# or Chocolatey
choco install ffmpeg
```

**macOS**

```bash
brew install ffmpeg
```

**Ubuntu/Debian Linux**

```bash
sudo apt install -y ffmpeg
```

Verify:

```bash
ffmpeg -version
```

---

### 3) Install yt-dlp

```bash
# Any OS
python -m pip install -U yt-dlp
# or
pip3 install -U yt-dlp

# Optional (isolated install)
pipx install yt-dlp
```

> Tip: If you prefer, `brew install yt-dlp` (macOS) or `sudo apt install yt-dlp` (Ubuntu 24.04+) also works.

---

### 4) Download this repo & run the script

```bash
git clone https://github.com/<your-username>/yt-dlp-menu-downloader.git
cd yt-dlp-menu-downloader
```

**Run:**

* **Windows**

  ```powershell
  py yt_dl_menu.py
  # or
  python yt_dl_menu.py
  ```

* **macOS / Linux**

  ```bash
  python3 yt_dl_menu.py
  ```

Then:

1. Paste a **YouTube video / playlist / channel** URL.
2. Choose the **download folder** (or accept the default `./downloads`).
3. Pick a **numbered** resolution option.

---

## 👀 What it looks like

```
┌───────────────────────────┐
│ Choose Resolution         │
└───────────────────────────┘
  1) Best available (auto)
  2) Best ≤ 2160p (auto cap)
  3) Best ≤ 1440p (auto cap)
  4) Best ≤ 1080p (auto cap)
  5) Best ≤ 720p  (auto cap)
  ...
Select 1-...:
```

* **Single video**: menu shows **only** available heights + “Best”.
* **Playlist/Channel**: menu shows **standard caps** (4K→144p).
  The script **automatically picks the best available ≤ your cap for each item** (great for mixed-quality playlists).

---

## 📂 Output location

Default:

```
./downloads/<Playlist Title or Channel>/<Video Title>.mp4
```

You can change the base folder at the prompt every time you run the script.

---

## 📦 Project structure

```
yt-dlp-menu-downloader/
├─ yt_dl_menu.py          # The script (interactive)
├─ README.md              # This file
└─ requirements.txt       # Optional: pinned dependency list
```

`requirements.txt`:

```
yt-dlp
```

Install via:

```bash
pip install -r requirements.txt
```

---

## 🔧 Troubleshooting

* **`ffmpeg` not found**

  * Install it (see steps above) and ensure `ffmpeg` runs from your terminal.
* **Windows: `py` not recognized**

  * Use `python` instead: `python yt_dl_menu.py`
* **Permission errors / cannot write**

  * Choose a folder you own (e.g., in your user profile). On Windows, you can run Terminal as Administrator if necessary.
* **Age-restricted / private videos**

  * You may need to pass cookies/auth to yt-dlp. See yt-dlp docs for `--cookies` usage.
* **Rate limiting / network hiccups**

  * Try again; the script enables retries. A stable connection helps.

---

## ❓ FAQ

**Can it download audio-only (MP3/M4A)?**
Not by default, but easy to add. Open an issue/PR and we’ll include a menu option for audio-only.

**Can I skip the prompts and pass arguments?**
This version is interactive. If you want headless flags like `--url`, `--res`, `--out`, open an issue and we’ll add them.

**Where do merged MP4s come from?**
yt-dlp downloads separate video/audio when needed and **ffmpeg** merges them into MP4.

---

## 🤝 Contributing

PRs welcome!

* Add audio-only, subtitles, thumbnails options
* Add command-line flags for automation
* Improve progress display / error handling

---

## 🧾 License

MIT

---

## 🙏 Credits

* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [ffmpeg](https://ffmpeg.org/)

---

## ⚖️ Legal

This tool is for personal/educational use. You are responsible for ensuring you have rights to download the content and for complying with YouTube’s Terms and all applicable laws.
