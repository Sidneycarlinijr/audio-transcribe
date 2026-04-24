# CLAUDE.md

## WHY - Purpose

CLI tools for transcribing audio files using Google Gemini AI. Splits long recordings into segments, transcribes each with speaker identification, extracts a theme, and saves as Markdown.

## WHAT - Architecture

```
├── transcribe_audio.py      # Main script: split + transcribe + join → .md
├── split_audio.py            # Utility: split long audio into segments
├── transcribe_segment.py     # Lightweight: single file transcription with retry
├── .claude/skills/transcribe/ # Claude Code skill for auto-discovery
├── docs.html                 # Visual documentation (open in browser)
└── README.md
```

**Stack:** Python 3.12+, google-generativeai SDK, pydub, ffmpeg

**Flow:**
```
audio.mp3 → split_audio.py → segments/
audio.mp3 → transcribe_audio.py → Gemini API (per segment) → Markdown
segment.mp3 → transcribe_segment.py → stdout
```

## HOW - Usage

```bash
# Setup (one-time)
python3 -m venv ~/venvs/transcribe
source ~/venvs/transcribe/bin/activate
pip install google-generativeai pydub
sudo apt install ffmpeg
export GEMINI_API_KEY="your_key"  # add to ~/.zshrc

# Transcribe
python transcribe_audio.py audio.mp3
python transcribe_audio.py --folder ~/Audios
python transcribe_audio.py audio.mp3 --segment-duration 5
python transcribe_audio.py audio.mp3 --output ~/Transcricoes
```

## Key Constraints

- `GEMINI_API_KEY` env var required (get from https://aistudio.google.com/app/apikey)
- Free tier: 10 req/min, 250 req/day — sufficient for daily use
- ffmpeg must be installed system-wide
- Supported formats: mp3, m4a, wav, ogg, aac, flac
- Output default: `~/Documentos/Transcricoes/YYYY-MM-DD — Theme.md`

## Coding Guidelines

1. No code comments
2. Minimize logging and console output
3. Keep scripts standalone — no shared imports between them
4. Simplicity first — YAGNI
