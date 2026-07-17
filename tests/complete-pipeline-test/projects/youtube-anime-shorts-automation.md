# YouTube Anime Shorts Automator

An automated desktop application designed to scrape, download, trim, and format video clips from `animexin.dev` into vertical 9:16 YouTube Shorts with customizable audio controls.

---

## 🎨 Design & Preview
The application is built using **PySide6 (Qt6)** and features a modern, premium **Cyberpunk Dark Mode** interface:
* **Left Panel**: Configure inputs, trim durations, audio options, and target export path.
* **Right Panel**: Real-time FFmpeg log monitor, status messages, progress bar, and execution control buttons.
* Visual design mockup is stored in: [ui_design/anime_shorts_gui_final.jpg](ui_design/anime_shorts_gui_final.jpg)

---

## ✨ Features
1. **Automated Scraping & Extraction**: Fetches and parses Animexin pages to locate player iframe sources and resolve Dailymotion video IDs.
2. **High-Quality Stream Resolution**: Resolves separate high-quality video and audio stream links using `yt-dlp`.
3. **Fast Selective Download**: Trims and downloads only the specified time-range using FFmpeg fast seek (`-ss` and `-t` applied to HLS input), eliminating the need to download the full episode.
4. **YouTube Shorts Formatting**: Scales and adds vertical black bars to center landscape video into a vertical 9:16 (`1080x1920`) aspect ratio.
5. **Audio Customization**:
   * Option to **Mute Original Sound**.
   * Option to **Add Custom Background Music** (audio file picker supporting `.mp3`, `.wav`, `.m4a`, etc.).
   * Dual audio modes: **Replace** (completely overrides original audio) or **Mix** (blends custom music with original voices/SFX).
6. **Smart Output Naming**: Automatically parses the Animexin URL slug to extract the anime name and episode number (e.g., `https://animexin.dev/renegade-immortal-episode-83...` automatically sets the file name to `renegade-immortal_ep83_short.mp4`).
7. **Real-Time Progress Tracking**: Parses standard output from FFmpeg to dynamically update the progress bar percentage during rendering.
8. **Settings Persistence**: Saves your configurations locally so that they are automatically restored when you restart the application.

---

## ⚙️ Prerequisites
Before running the application, make sure you have the following installed:
* **Python 3.10+**
* **FFmpeg**: Must be installed and added to your system's `PATH` variables. To verify, run `ffmpeg -version` in your terminal.

---

## 🚀 Installation & Setup
1. **Activate Virtual Environment** (or create one first):
   ```powershell
   # If venv doesn't exist, create it:
   python -m venv venv

   # Activate on Windows:
   .\venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```bash
   pip install PySide6 yt-dlp beautifulsoup4 requests
   ```
3. **Run the Application**:
   ```bash
   python main.py
   ```

---

## 🧪 Running Tests
To run the automated integration tests that verify the full pipeline:
```bash
python tests/test_integration.py
```
This script runs the following test specs:
1. **Dynamic Naming**: Verifies that the helper correctly parses the anime name and episode from an Animexin URL to suggest output filenames (e.g. `{anime_name}_ep{number}_short.mp4`).
2. **Local Page Scraper**: Parses the Dailymotion ID from a cached Animexin HTML file (`scripts/page_renegade.html`) to verify BeautifulSoup parser rules without triggering Cloudflare blocks.
3. **Stream Resolution**: Contacts Dailymotion to resolve separate high-quality video and audio stream links using `yt-dlp`.
4. **FFmpeg Processing engine**: Trims the resolved streams from `8:30` to `9:00` (510s to 540s), applies 9:16 vertical padding (centered landscape video inside a `1080x1920` black canvas), muxes the original audio, parses progress in real-time, and exports the final file in the `tests/` folder.

---

## 📂 Project Structure
* `main.py`: Primary application entry point (launches the PySide6 Cyberpunk GUI).
* `config.py`: Settings manager for loading/saving configurations to `config.json`.
* `core/`: Core modules for scraping, stream resolving, and video rendering.
* `gui/`: UI components (main window design, styles, and background worker threads).
* `utils/`: Common utilities (timestamp conversions and URL details parser).
* `tests/`: Test suite for automated verification.
  * `test_integration.py`: End-to-end integration test runner.
* `scripts/`: Dev sandboxes, scraper logs, and HTML/media sample files.
* `ui_design/`: High-fidelity user interface design mockups.
* `prd.md` & `progress.md`: Requirements and progress tracking logs.
