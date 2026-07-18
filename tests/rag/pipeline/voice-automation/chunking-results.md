# Chunking results — voice-automation

## Summary
- Parents: 24
- Boundary units: 104
- Child chunks: 24
- README chars: 15288

## Parents
- `Voice Automation` — 202 tokens
- `Voice Automation > License` — 15 tokens
- `Voice Automation > Why This Exists` — 215 tokens
- `Voice Automation > Features` — 188 tokens
- `Voice Automation > Engineering Highlights` — 266 tokens
- `Voice Automation > Inference & Performance Trade-offs` — 164 tokens
- `Voice Automation > System Design` — 214 tokens
- `Voice Automation > System Design > Latency Strategy` — 76 tokens
- `Voice Automation > Backend Modes > Deepgram API Mode` — 239 tokens
- `Voice Automation > Backend Modes > Moonshine Local Mode` — 227 tokens
- `Voice Automation > Installation` — 116 tokens
- `Voice Automation > Configuration` — 135 tokens
- `Voice Automation > Configuration > Deepgram Configuration` — 65 tokens
- `Voice Automation > Configuration > Moonshine Configuration` — 53 tokens
- `Voice Automation > Usage` — 123 tokens
- `Voice Automation > Desktop App` — 152 tokens
- `Voice Automation > Desktop App > Desktop Home Screen` — 135 tokens
- `Voice Automation > Desktop App > Desktop Settings` — 206 tokens
- `Voice Automation > Desktop App > Desktop Deepgram Setup` — 128 tokens
- `Voice Automation > Desktop App > Desktop Moonshine Setup` — 122 tokens
- `Voice Automation > Desktop App > Building The Desktop Executable` — 111 tokens
- `Voice Automation > Project Structure` — 173 tokens
- `Voice Automation > Engineering Notes` — 169 tokens
- `Voice Automation > Current Status` — 168 tokens

## Child chunks
### Voice Automation (chunk 0, 202 tokens, readme_section)
A Windows push-to-talk voice dictation tool I built to reduce typing friction in AI engineering workflows.  It runs in the background, listens only while a hotkey is held, transcribes speech, cleans the transcript, and inserts the result into the currently focused application. The design is intentionally lightweight: short recording windows, background processing, and explicit backend choice betwe...

### Voice Automation > License (chunk 1, 15 tokens, readme_section)
This project is open source under the [MIT License](LICENSE).

### Voice Automation > Why This Exists (chunk 2, 215 tokens, readme_section)
Modern technical work involves constant context switching: coding in Cursor, writing prompts, using terminals, searching documentation, messaging, and testing ideas in browsers. Voice input can remove a lot of small typing overhead, but most dictation tools are either app-specific, always listening, or awkward to use inside developer workflows.  Voice Automation is designed as a lightweight system...

### Voice Automation > Features (chunk 3, 188 tokens, readme_section)
- Global push-to-talk hotkey. - Records only while the hotkey is held. - Works across normal Windows text fields. - Supports Deepgram cloud transcription. - Supports Moonshine local transcription. - Tray-first Windows desktop app with Home and Settings screens. - Secure Deepgram API key storage with the Windows credential store. - Moonshine model selection, download, and verification from the desk...

### Voice Automation > Engineering Highlights (chunk 4, 266 tokens, readme_section)
* **Asynchronous Multi-Threaded Pipeline**: Engineered a non-blocking execution flow using Python threading and global thread pools (`QThreadPool`) to prevent OS hotkey lag and GUI freezes during concurrent microphone capture and STT processing. * **Quantized Local CPU Inference**: Integrated the **Moonshine** model family, optimizing inference latency on resource-constrained host machines (CPU-on...

### Voice Automation > Inference & Performance Trade-offs (chunk 5, 164 tokens, readme_section)
The engine is profiled to run on CPU-only hosts alongside CPU-heavy IDEs (such as Cursor/VS Code) and terminals.  | Model / Provider | Parameter Count | Mode | Typical RTF (Real-Time Factor) | Best Use Case | | :--- | :---: | :---: | :---: | :--- | | **Deepgram API** | *N/A (Cloud)* | Cloud Streaming | < 0.1 | High-accuracy technical prompt dictation (requires network) | | **Moonshine Tiny** | 26M...

### Voice Automation > System Design (chunk 6, 214 tokens, readme_section)
```mermaid graph TD     classDef default fill:#1a1a1e,stroke:#2d2d34,stroke-width:1px,color:#e4e4e7;     classDef active fill:#10b981,stroke:#059669,stroke-width:2px,color:#ffffff;     classDef process fill:#27272a,stroke:#3f3f46,stroke-width:1px,color:#f4f4f5;      Hotkey["Global Hotkey<br>(right_ctrl / F8)"]:::active     Audio["Audio Capture<br>(sounddevice / mono chunks)"]:::process     STT["Sp...

### Voice Automation > System Design > Latency Strategy (chunk 7, 76 tokens, readme_section)
- Push-to-talk only, not always listening. - Short audio chunks so the recording loop stays responsive. - Background transcription so the UI and hotkey listener stay usable. - Direct typing fallback when clipboard paste is not suitable. - Offline Moonshine mode when network latency or privacy is a concern.

### Voice Automation > Backend Modes > Deepgram API Mode (chunk 8, 239 tokens, readme_section)
Deepgram is the recommended cloud mode in this project because it provides stronger transcription accuracy for real usage. This is useful when dictating technical language, prompts, commands, or longer natural speech.  Deepgram also provides generous free credits, which makes it practical for personal productivity automation.  To use Deepgram mode:  1. Create a Deepgram account. 2. Generate an API...

### Voice Automation > Backend Modes > Moonshine Local Mode (chunk 9, 227 tokens, readme_section)
Moonshine is included for local/offline transcription. It is useful when you want the system to run without sending audio to a cloud API.  Example config:  ```json {     "model_provider": "moonshine",     "model_arch": 5,     "sample_rate": 16000 } ```  Available Moonshine model architecture values:  | Model | `model_arch` | |---|---:| | Tiny | `0` | | Base | `1` | | Tiny Streaming | `2` | | Base ...

### Voice Automation > Installation (chunk 10, 116 tokens, readme_section)
Requirements:  - Windows - Python 3.11 or newer - Microphone access  Create and activate a virtual environment:  ```bat python -m venv .venv call .venv\Scripts\activate.bat ```  Install the project:  ```bat pip install -e . ```  Or run the setup script:  ```bat setup.bat ```  If you are using Deepgram, create your `.env` file after installation:  ```bat copy .env.example .env ```  Then edit `.env`...

### Voice Automation > Configuration (chunk 11, 135 tokens, readme_section)
The app uses:  ```text voice_automation_config.json ```  Current important settings:  | Setting | Purpose | |---|---| | `hotkey` | Key used for push-to-talk | | `model_provider` | `deepgram` or `moonshine` | | `deepgram_api_key` | API key for Deepgram mode | | `model_arch` | Moonshine model architecture | | `sample_rate` | Audio sample rate | | `paste_mode` | `clipboard` or `type` | | `max_record_...

### Voice Automation > Configuration > Deepgram Configuration (chunk 12, 65 tokens, readme_section)
For cloud transcription, use:  ```json {     "model_provider": "deepgram",     "sample_rate": 8000,     "deepgram_api_key": "" } ```  The recommended approach is to keep `deepgram_api_key` empty in `voice_automation_config.json` and store the real key in `.env`.

### Voice Automation > Configuration > Moonshine Configuration (chunk 13, 53 tokens, readme_section)
For local transcription, use:  ```json {     "model_provider": "moonshine",     "model_arch": 5,     "sample_rate": 16000 } ```  Then download the local model:  ```bat python -m voice_automation download-model ```

### Voice Automation > Usage (chunk 14, 123 tokens, readme_section)
Run the application:  ```bat python -m voice_automation run ```  Or:  ```bat run.bat ```  Then:  1. Focus any text field. 2. Hold the configured hotkey. 3. Speak. 4. Release the hotkey. 5. The transcript is pasted into the focused app.  Run environment checks:  ```bat python -m voice_automation check ```  Download a Moonshine model:  ```bat python -m voice_automation download-model ```  Note: mode...

### Voice Automation > Desktop App (chunk 15, 152 tokens, readme_section)
The desktop app is the V1 Windows-first interface for Voice Automation. It is tray-first and opens to a simple Home screen with Start and Stop controls. Settings handles backend selection, Deepgram key storage, Moonshine model management, hotkey choice, and recording limits.  Run the desktop app from source:  ```bat python -m voice_automation.desktop ```  If the project is installed with console s...

### Voice Automation > Desktop App > Desktop Home Screen (chunk 16, 135 tokens, readme_section)
The Home screen shows the current dictation status, backend readiness, the primary Start and Stop buttons, and quick access to Settings, Check Environment, and Diagnostics. Use Settings when you need to change the speech backend, Deepgram API key, Moonshine model, hotkey, or maximum recording time.  The desktop app uses direct typing mode by default and does not expose a paste-mode selector. The p...

### Voice Automation > Desktop App > Desktop Settings (chunk 17, 206 tokens, readme_section)
The Settings screen is where desktop users configure:  | Setting | Purpose | |---|---| | Backend | Choose online Deepgram API or offline Moonshine Local | | Deepgram API key | Save the cloud transcription key through the OS credential store | | Moonshine model | Select and download the offline model | | Hotkey | Choose the push-to-talk key | | Max recording seconds | Safety cap for one recording |...

### Voice Automation > Desktop App > Desktop Deepgram Setup (chunk 18, 128 tokens, readme_section)
In the desktop Settings screen:  1. Select `Deepgram API` as the backend. 2. Paste your Deepgram API key into the API key field. 3. Save the key. 4. Save or apply the settings.  The desktop app stores the Deepgram API key in the operating system credential store through `keyring`, not in the JSON config file. The CLI still supports `.env` and JSON-based keys for development compatibility, but the ...

### Voice Automation > Desktop App > Desktop Moonshine Setup (chunk 19, 122 tokens, readme_section)
In the desktop Settings screen:  1. Select `Moonshine Local` as the backend. 2. Choose a Moonshine model:    - Tiny `0`    - Base `1`    - Tiny Streaming `2`    - Base Streaming `3`    - Small Streaming `4`    - Medium Streaming `5` 3. Click the Moonshine download button. 4. Save or apply the settings.  Moonshine runs locally after the selected model is downloaded. For the best local accuracy, use...

### Voice Automation > Desktop App > Building The Desktop Executable (chunk 20, 111 tokens, readme_section)
The V1 package target is a Windows PyInstaller one-folder build. From an activated virtual environment with the project dependencies installed, build with the provided PyInstaller spec or build script:  ```bat pyinstaller voice_automation_desktop.spec ```  If a build script is present in your checkout, use it as the wrapper around the same PyInstaller build:  ```bat build_desktop.bat ```  Build ou...

### Voice Automation > Project Structure (chunk 21, 173 tokens, readme_section)
```text voice_automation/ +-- __main__.py        CLI entrypoint +-- orchestrator.py    Main runtime pipeline +-- service.py         Engine daemon lifecycle manager +-- audio.py           Microphone recording +-- hotkey.py          Global push-to-talk listener +-- stt.py             Deepgram and Moonshine adapters +-- paste.py           Clipboard/direct text insertion +-- cleanup.py         Transcr...

### Voice Automation > Engineering Notes (chunk 22, 169 tokens, readme_section)
- The app is intentionally push-to-talk, not always listening. - STT providers are hidden behind a common adapter interface. - Audio capture and transcription run through background threads to keep the hotkey loop responsive. - Clipboard insertion is preferred because it is faster and more reliable than typing character by character. - Direct typing remains available as a fallback for apps where c...

### Voice Automation > Current Status (chunk 23, 168 tokens, readme_section)
This is a working personal automation project focused on Windows productivity workflows. It is useful to me as an AI engineer because it reduces repetitive typing and keeps dictation close to the apps I already use.  The current desktop implementation includes:  - Tray-first Home and Settings UI - Deepgram API key storage through the OS credential store - Moonshine model download and readiness che...
