# Audio Transcribe

Transcribe audio files using Gemini AI with speaker identification and automatic theme extraction.

## How to Use

### With Claude Code (recommended)

```bash
git clone https://github.com/Sidneycarlinijr/audio-transcribe.git
cd audio-transcribe
# open Claude Code here
```

Then ask:

```
"transcribe the audio ~/Downloads/meeting.m4a"
```

The repo includes `CLAUDE.md` and a built-in skill (`.claude/skills/transcribe/`) — Claude Code discovers it automatically, handles setup if needed, and delivers the transcription.

### From the terminal

```bash
# Single file
python transcribe_audio.py audio.mp3

# Entire folder
python transcribe_audio.py --folder ~/Audios

# Shorter segments (if rate limited)
python transcribe_audio.py audio.mp3 --segment-duration 5

# Custom output directory
python transcribe_audio.py audio.mp3 --output ~/Transcriptions
```

## Setup

```bash
# 1. Create venv and install dependencies
python3 -m venv ~/venvs/transcribe
source ~/venvs/transcribe/bin/activate
pip install google-generativeai pydub

# 2. Install ffmpeg
sudo apt install ffmpeg

# 3. Configure API key
export GEMINI_API_KEY="your_key_here"
# Get one at: https://aistudio.google.com/app/apikey
# Add to ~/.zshrc to persist

# 4. Alias (optional)
alias transcribe="~/venvs/transcribe/bin/python ~/path/to/transcribe_audio.py"
```

### API Key — Free Tier

Works without a credit card. Limits: 10 req/min, 250 req/day, 250k tokens/min.

> **Privacy:** On the free tier, your data may be used for model training.

## Scripts

| Script | Description |
|--------|-------------|
| `transcribe_audio.py` | Full pipeline: split + transcribe + join → Markdown |
| `split_audio.py` | Split long audio into 30-min segments (no AI) |
| `transcribe_segment.py` | Transcribe a single file with automatic retry |

## Output

Markdown files saved to `~/Documentos/Transcricoes/`:
```
2026-04-02 — Meeting Theme.md
```

## Supported Formats

mp3, m4a, wav, ogg, aac, flac

## Troubleshooting

| Error | Fix |
|-------|-----|
| `GEMINI_API_KEY not set` | `export GEMINI_API_KEY="key"` in `~/.zshrc` |
| `pydub not installed` | `pip install pydub` in the venv |
| `ffmpeg not found` | `sudo apt install ffmpeg` |
| Rate limit / 429 | Use `--segment-duration 5` |
