# CLAUDE.md

## WHY - Purpose

CLI tools for transcribing audio files using Deepgram. Sends audio directly to Deepgram's nova-2 model with native speaker diarization, extracts a theme, and saves as Markdown.

## WHAT - Architecture

```
├── transcribe_audio.py      # Main script: transcribe → .md
├── split_audio.py            # Utility: split long audio into segments
├── transcribe_segment.py     # Lightweight: single file transcription
├── .claude/skills/transcribe/ # Claude Code skill for auto-discovery
├── docs.html                 # Visual documentation (open in browser)
└── README.md
```

**Stack:** Python 3.12+, deepgram-sdk, pydub, ffmpeg

**Flow:**
```
audio.mp3 → transcribe_audio.py → Deepgram API → Markdown
segment.mp3 → transcribe_segment.py → stdout
audio.mp3 → split_audio.py → segments/ (standalone utility)
```

## HOW - Usage

```bash
# Setup (one-time)
python3 -m venv ~/venvs/transcribe
source ~/venvs/transcribe/bin/activate
pip install deepgram-sdk pydub
sudo apt install ffmpeg
export DEEPGRAM_API_KEY="your_key"  # add to ~/.zshrc

# Transcribe
python transcribe_audio.py audio.mp3
python transcribe_audio.py --folder ~/Audios
python transcribe_audio.py audio.mp3 --output ~/Transcricoes
```

## Key Constraints

- `DEEPGRAM_API_KEY` env var required (get from https://console.deepgram.com)
- Free tier: $200 credit (~770 hours of audio), no credit card required
- ffmpeg must be installed system-wide
- Supported formats: mp3, m4a, wav, ogg, aac, flac
- Output default: `~/Documentos/Transcricoes/YYYY-MM-DD — Theme.md`

## Coding Guidelines

1. No code comments
2. Minimize logging and console output
3. Keep scripts standalone — no shared imports between them
4. Simplicity first — YAGNI
