# Audio Transcribe

Transcreve audios usando Gemini AI com identificacao de oradores e extracao de tema.

## Setup

```bash
# 1. Criar venv e instalar dependencias
python3 -m venv ~/venvs/transcribe
source ~/venvs/transcribe/bin/activate
pip install google-generativeai pydub

# 2. Instalar ffmpeg (se nao tiver)
sudo apt install ffmpeg

# 3. Configurar API key
export GEMINI_API_KEY="sua_chave_aqui"
# Gere em: https://aistudio.google.com/app/apikey
# Adicione ao ~/.zshrc para persistir

# 4. Alias (opcional)
alias transcribe="~/venvs/transcribe/bin/python ~/caminho/para/transcribe_audio.py"
```

### API Key — Free Tier

Funciona sem cartao de credito. Limites: 10 req/min, 250 req/dia, 250k tokens/min.

> **Privacidade:** No free tier, dados podem ser usados para treinamento do modelo.

## Uso

```bash
# Arquivo unico
transcribe audio.mp3

# Pasta inteira
transcribe --folder ~/Downloads/Audios

# Segmentos menores (se der rate limit)
transcribe audio.mp3 --segment-duration 5

# Pasta de saida customizada
transcribe audio.mp3 --output ~/Transcricoes
```

### Via Claude Code

O Claude Code roda o script direto na conversa — basta pedir:

```
"transcreve o audio ~/Downloads/reuniao.m4a"
```

Como o `GEMINI_API_KEY` ja esta no `~/.zshrc`, funciona sem configuracao adicional.

### Como Skill no Claude Code

Crie `~/.claude/skills/transcribe-audio/SKILL.md`:

```markdown
---
name: transcribe-audio
description: Transcribe audio files using Gemini AI. Use when
  the user asks to transcribe, convert audio to text, or process
  meeting recordings.
---

Run the transcription script on the audio file provided.

## Steps

1. Identify the audio file path from the user's message
2. Run: `~/venvs/transcribe/bin/python ~/path/to/transcribe_audio.py <audio_file>`
3. Read the output from ~/Documentos/Transcricoes/
4. Show a summary to the user

## Notes
- Supported: mp3, m4a, wav, ogg, aac, flac
- Long audios: use --segment-duration 5 if rate limited
- GEMINI_API_KEY must be set in the environment
```

## Scripts

| Script | Descricao |
|--------|-----------|
| `transcribe_audio.py` | Transcreve audios usando Gemini (divide, transcreve, junta) |
| `split_audio.py` | Divide audios longos em partes de 30 min |
| `transcribe_segment.py` | Transcreve um unico segmento com retry automatico |

## Saida

Arquivos `.md` em `~/Documentos/Transcricoes/`:
```
2026-04-02 — Tema da Reuniao.md
```

## Formatos suportados

mp3, m4a, wav, ogg, aac, flac

## Troubleshooting

| Erro | Solucao |
|------|---------|
| `GEMINI_API_KEY nao definida` | `export GEMINI_API_KEY="key"` no `~/.zshrc` |
| `pydub nao instalado` | `pip install pydub` no venv |
| `ffmpeg nao encontrado` | `sudo apt install ffmpeg` |
| Rate limit / 429 | Use `--segment-duration 5` |
