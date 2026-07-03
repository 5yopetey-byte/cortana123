# Cortana Local (prototype)

Lightweight offline voice assistant prototype for Linux (target: ASUS Chromebook CM3001 Crostini).  
Focus: speed, low RAM, modular architecture.

This repo contains a minimal working core:
- Wakeword (stub / OpenWakeWord if installed)
- Offline STT: Vosk (if model present) with a text-input fallback
- TTS: Piper CLI if available, else pyttsx3 fallback
- Simple rule-based intent parser and executor
- Pygame CE avatar window (idle / listening / speaking)
- Plugin system for adding features

Quick start (development):
1. Create and activate a Python 3.11+ venv:
   python3 -m venv .venv
   source .venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Edit config/settings.json (model paths, dry_run flag, etc).

4. Initialize databases:
   python3 database/init_db.py

5. Run:
   python3 main.py

Notes:
- Vosk models and Piper voice models are not bundled. Put Vosk model in `assets/models/vosk` or set the path in `config/settings.json`.
- On Chromebook Crostini, ensure audio devices are forwarded and pulseaudio/pipewire is installed.
- The default behavior is safe: destructive system commands are dry-run unless you set `"dry_run": false` in `config/settings.json`.

Project structure: matches the spec you provided.

License: MIT
