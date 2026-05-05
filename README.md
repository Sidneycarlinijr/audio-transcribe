# Audio Transcribe

Transcribe audio files using Deepgram with native speaker diarization and automatic theme extraction.

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

# Custom output directory
python transcribe_audio.py audio.mp3 --output ~/Transcriptions
```

## Setup

```bash
# 1. Create venv and install dependencies
python3 -m venv ~/venvs/transcribe
source ~/venvs/transcribe/bin/activate
pip install deepgram-sdk pydub

# 2. Install ffmpeg
sudo apt install ffmpeg

# 3. Configure API key
export DEEPGRAM_API_KEY="your_key_here"
# Get one at: https://console.deepgram.com (free $200 credit, no credit card)
# Add to ~/.zshrc to persist

# 4. Alias (optional)
alias transcribe="~/venvs/transcribe/bin/python ~/path/to/transcribe_audio.py"
```

### API Key — Free Tier

$200 in free credits on signup. No credit card required. No expiration.

At ~$0.0043/min, that's roughly **770 hours** of audio transcription.

## Scripts

| Script | Description |
|--------|-------------|
| `transcribe_audio.py` | Full pipeline: transcribe + theme extraction → Markdown |
| `split_audio.py` | Split long audio into 30-min segments (no AI, standalone utility) |
| `transcribe_segment.py` | Transcribe a single file, output to stdout |

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
| `DEEPGRAM_API_KEY not set` | `export DEEPGRAM_API_KEY="key"` in `~/.zshrc` |
| `deepgram-sdk not installed` | `pip install deepgram-sdk` in the venv |
| `pydub not installed` | `pip install pydub` in the venv |
| `ffmpeg not found` | `sudo apt install ffmpeg` |
