# Audio Transcribe

Transcreve audios usando Gemini AI com identificacao de oradores e extracao de tema.

## Setup rapido

```bash
# 1. Criar venv e instalar dependencias
python3 -m venv ~/venvs/transcribe
source ~/venvs/transcribe/bin/activate
pip install google-generativeai pydub

# 2. Instalar ffmpeg (se nao tiver)
sudo apt-get install ffmpeg

# 3. Configurar API key no ~/.zshrc
export GEMINI_API_KEY="sua_chave_aqui"
# Gere a chave em: https://aistudio.google.com/apikey

# 4. Adicionar alias no ~/.zshrc (opcional, evita ativar venv toda vez)
alias transcribe="~/venvs/transcribe/bin/python ~/Documentos/Projetos/career-growth/scripts/transcribe_audio.py"

# 5. Recarregar shell
source ~/.zshrc
```

## Uso

```bash
# Arquivo unico
transcribe /caminho/do/audio.mp3

# Pasta inteira
transcribe --folder ~/Downloads/Audios

# Segmentos menores (padrao: 10 min)
transcribe audio.mp3 --segment-duration 5

# Pasta de saida customizada
transcribe audio.mp3 --output ~/Meus/Transcricoes
```

## Saida

Arquivos `.md` salvos em `~/Documentos/Transcricoes/` com formato:
```
2026-04-02 — Tema da Reuniao.md
```

## Formatos suportados

mp3, m4a, wav, ogg, aac, flac

## Scripts disponiveis

| Script | Descricao |
|--------|-----------|
| `transcribe_audio.py` | Transcreve audios usando Gemini (divide, transcreve, junta) |
| `split_audio.py` | Apenas divide audios longos em partes de 30 min |
| `transcribe_segment.py` | Transcreve um unico segmento com retry automatico |

## Troubleshooting

| Erro | Solucao |
|------|---------|
| `GEMINI_API_KEY nao definida` | `export GEMINI_API_KEY="key"` no `~/.zshrc` |
| `pydub nao instalado` | `~/venvs/transcribe/bin/pip install pydub` |
| `ffmpeg nao encontrado` | `sudo apt install ffmpeg` |
| Timeout em audios longos | Use `--segment-duration 5` |
