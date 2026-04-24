---
name: transcribe
description: Transcribe audio files using Gemini AI. Use when the user asks to transcribe audio, convert recordings to text, or process meeting files.
type: workflow
---

## Purpose

Transcribe audio files into text using the project's Python scripts powered by Gemini AI. Handles speaker identification, automatic segmentation of long files, and theme extraction.

## When to Use

- User asks to transcribe an audio file
- User wants to convert a recording to text
- User mentions processing meeting audio
- User provides a path to an mp3, m4a, wav, ogg, aac, or flac file

## Steps

1. **Identify the audio file** from the user's message. If no file path given, ask for it.

2. **Check prerequisites** before running:
   ```bash
   # Verify GEMINI_API_KEY is set
   echo $GEMINI_API_KEY | head -c 4
   # Should print "AIza" — if empty, tell user to set it
   ```

3. **Run transcription** using the venv:
   ```bash
   ~/venvs/transcribe/bin/python transcribe_audio.py <audio_file>
   ```
   If venv doesn't exist, set it up first:
   ```bash
   python3 -m venv ~/venvs/transcribe
   ~/venvs/transcribe/bin/pip install google-generativeai pydub
   ```

4. **Find the output** in `~/Documentos/Transcricoes/` — the most recently created `.md` file.

5. **Read and summarize** the transcription for the user. Include:
   - Theme extracted
   - Number of speakers identified
   - Key topics discussed (brief summary)
   - Full file path for reference

## Options

| Flag | Effect |
|------|--------|
| `--folder <path>` | Transcribe all audio files in a directory |
| `--segment-duration <min>` | Change segment length (default: 10 min, use 5 if rate limited) |
| `--output <path>` | Change output directory |

## Splitting Only

If the user just wants to split audio without transcribing:
```bash
~/venvs/transcribe/bin/python split_audio.py <audio_file>
```

## Single Segment

For transcribing one segment with retry logic (output to stdout):
```bash
~/venvs/transcribe/bin/python transcribe_segment.py <audio_file>
```

## Troubleshooting

- **Rate limit (429):** Use `--segment-duration 5` to send smaller chunks
- **Missing ffmpeg:** `sudo apt install ffmpeg`
- **Missing deps:** `~/venvs/transcribe/bin/pip install google-generativeai pydub`
