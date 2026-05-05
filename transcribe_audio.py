#!/usr/bin/env python3
"""
Script para transcrever áudios usando Deepgram.
Suporta áudios longos nativamente (sem necessidade de dividir).

Uso:
    python transcribe_audio.py <caminho_do_audio>
    python transcribe_audio.py --folder <pasta_com_audios>

Requisitos:
    pip install deepgram-sdk pydub

Configuração:
    export DEEPGRAM_API_KEY="sua_chave_aqui"
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    from pydub import AudioSegment
except ImportError:
    print("Erro: pydub não instalado. Execute: pip install pydub")
    sys.exit(1)

try:
    from deepgram import DeepgramClient
except ImportError:
    print("Erro: deepgram-sdk não instalado. Execute: pip install deepgram-sdk")
    sys.exit(1)


OUTPUT_DIR = Path.home() / "Documentos" / "Transcricoes"
SUPPORTED_FORMATS = {'.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac'}


def setup_deepgram():
    api_key = os.environ.get('DEEPGRAM_API_KEY')
    if not api_key:
        print("Erro: DEEPGRAM_API_KEY não definida.")
        print("   Execute: export DEEPGRAM_API_KEY='sua_chave'")
        sys.exit(1)

    return DeepgramClient(api_key=api_key)


def get_audio_duration(audio_path: Path) -> float:
    suffix = audio_path.suffix.lower()
    if suffix == '.m4a':
        audio = AudioSegment.from_file(audio_path, format='m4a')
    elif suffix == '.mp3':
        audio = AudioSegment.from_mp3(audio_path)
    elif suffix == '.wav':
        audio = AudioSegment.from_wav(audio_path)
    elif suffix == '.ogg':
        audio = AudioSegment.from_ogg(audio_path)
    else:
        audio = AudioSegment.from_file(audio_path)

    return len(audio) / 1000 / 60


def transcribe_audio(client, audio_path: Path) -> str:
    print(f"Transcrevendo: {audio_path.name}")

    duration_min = get_audio_duration(audio_path)
    print(f"   Duração: {duration_min:.1f} minutos")

    with open(audio_path, "rb") as f:
        buffer_data = f.read()

    print("   Enviando para Deepgram...")
    response = client.listen.v1.media.transcribe_file(
        request=buffer_data,
        model="nova-2",
        language="pt-BR",
        smart_format=True,
        punctuate=True,
        diarize=True,
        utterances=True,
    )

    if response.results and response.results.utterances:
        lines = []
        for utt in response.results.utterances:
            speaker = utt.speaker + 1
            lines.append(f"Orador {speaker}: {utt.transcript}")
        return "\n".join(lines)

    if response.results and response.results.channels:
        alt = response.results.channels[0].alternatives[0]
        if alt and alt.transcript:
            return alt.transcript

    return "[Sem conteúdo audível]"


def extract_theme(transcript: str) -> str:
    lines = transcript[:2000].split('\n')
    words = []
    for line in lines[:5]:
        clean = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
        words.extend(clean.split()[:8])
        if len(words) >= 10:
            break

    if words:
        theme = ' '.join(words[:6])
        if len(theme) > 40:
            theme = theme[:37] + '...'
        return theme

    return "Reunião"


def save_transcription(audio_name: str, theme: str, transcription: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')
    safe_theme = "".join(c for c in theme if c.isalnum() or c in ' -_').strip()[:30]
    filename = f"{date_str} — {safe_theme}.md"

    output_path = OUTPUT_DIR / filename

    content = f"""# {theme}

**Arquivo original:** {audio_name}
**Data:** {date_str}

---

## Transcrição

{transcription}
"""

    output_path.write_text(content, encoding='utf-8')
    return output_path


def process_audio(audio_path: Path):
    print(f"\n{'='*50}")
    print(f"Processando: {audio_path.name}")
    print('='*50)

    client = setup_deepgram()
    transcription = transcribe_audio(client, audio_path)

    print(f"\nTranscrição completa: {len(transcription)} caracteres")

    theme = extract_theme(transcription)
    print(f"   Tema: {theme}")

    output_path = save_transcription(audio_path.name, theme, transcription)

    print(f"\nSUCESSO!")
    print(f"   Arquivo salvo em: {output_path}")

    return output_path


def process_folder(folder_path: Path):
    audio_files = [
        f for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]

    if not audio_files:
        print(f"Nenhum arquivo de áudio encontrado em: {folder_path}")
        return

    print(f"Encontrados {len(audio_files)} arquivos de áudio")

    for audio_file in sorted(audio_files):
        try:
            process_audio(audio_file)
        except Exception as e:
            print(f"Erro ao processar {audio_file.name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Transcreve áudios usando Deepgram',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python transcribe_audio.py audio.mp3
    python transcribe_audio.py --folder ~/Audios
        """
    )

    parser.add_argument('audio', nargs='?', help='Caminho do arquivo de áudio')
    parser.add_argument('--folder', '-f', help='Pasta com arquivos de áudio')
    parser.add_argument('--output', '-o', help='Pasta de saída para transcrições')

    args = parser.parse_args()

    if args.output:
        global OUTPUT_DIR
        OUTPUT_DIR = Path(args.output)

    if args.folder:
        folder_path = Path(args.folder).expanduser()
        if not folder_path.exists():
            print(f"Pasta não encontrada: {folder_path}")
            sys.exit(1)
        process_folder(folder_path)
    elif args.audio:
        audio_path = Path(args.audio).expanduser()
        if not audio_path.exists():
            print(f"Arquivo não encontrado: {audio_path}")
            sys.exit(1)
        process_audio(audio_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
