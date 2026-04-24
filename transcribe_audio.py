#!/usr/bin/env python3
"""
Script para transcrever áudios longos usando Gemini.
Divide áudios em partes menores, transcreve cada parte e junta o resultado.

Uso:
    python transcribe_audio.py <caminho_do_audio>
    python transcribe_audio.py --folder <pasta_com_audios>

Requisitos:
    pip install google-generativeai pydub

Configuração:
    export GEMINI_API_KEY="sua_chave_aqui"
"""

import os
import sys
import argparse
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

try:
    from pydub import AudioSegment
except ImportError:
    print("❌ Erro: pydub não instalado. Execute: pip install pydub")
    sys.exit(1)

try:
    import google.generativeai as genai
except ImportError:
    print("❌ Erro: google-generativeai não instalado. Execute: pip install google-generativeai")
    sys.exit(1)


SEGMENT_DURATION_MS = 30 * 60 * 1000  # 30 minutos em milissegundos
OUTPUT_DIR = Path.home() / "Documentos" / "Transcricoes"
SUPPORTED_FORMATS = {'.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac'}


def setup_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ Erro: GEMINI_API_KEY não definida.")
        print("   Execute: export GEMINI_API_KEY='sua_chave'")
        sys.exit(1)

    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')


def split_audio(audio_path: Path, segment_duration_ms: int = SEGMENT_DURATION_MS) -> list[Path]:
    print(f"📂 Carregando áudio: {audio_path.name}")

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

    duration_ms = len(audio)
    duration_min = duration_ms / 1000 / 60
    print(f"   Duração: {duration_min:.1f} minutos")

    if duration_ms <= segment_duration_ms:
        print("   Áudio curto, não precisa dividir.")
        return [audio_path]

    num_segments = (duration_ms + segment_duration_ms - 1) // segment_duration_ms
    print(f"   Dividindo em {num_segments} partes...")

    temp_dir = Path(tempfile.mkdtemp(prefix='audio_segments_'))
    segments = []

    for i in range(num_segments):
        start = i * segment_duration_ms
        end = min((i + 1) * segment_duration_ms, duration_ms)

        segment = audio[start:end]
        segment_path = temp_dir / f"segment_{i+1:03d}.mp3"
        segment.export(segment_path, format='mp3')
        segments.append(segment_path)

        print(f"   ✓ Parte {i+1}/{num_segments} criada")

    return segments


def transcribe_segment(model, audio_path: Path, segment_num: int, total_segments: int) -> str:
    print(f"🎙️ Transcrevendo parte {segment_num}/{total_segments}...")

    audio_file = genai.upload_file(audio_path)

    while audio_file.state.name == "PROCESSING":
        import time
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)

    if audio_file.state.name == "FAILED":
        raise Exception(f"Falha no upload do arquivo: {audio_file.name}")

    prompt = """Transcreva este áudio integralmente em português do Brasil.
Identifique os diferentes oradores (ex: Orador 1, Orador 2) sempre que a voz mudar.
Formate como: "Orador X: [fala]".
Retorne APENAS a transcrição, sem comentários ou análises."""

    response = model.generate_content([prompt, audio_file])

    try:
        genai.delete_file(audio_file.name)
    except:
        pass

    return response.text


def extract_theme(model, transcription: str) -> str:
    print("🧠 Extraindo tema...")

    prompt = f"""Analise esta transcrição e retorne APENAS um título curto (máximo 40 caracteres)
que descreva o tema principal da conversa. Sem aspas, sem explicações, apenas o título.

TRANSCRIÇÃO (primeiros 2000 chars):
{transcription[:2000]}"""

    try:
        response = model.generate_content(prompt)
        theme = response.text.strip().replace('"', '').replace('\n', '')[:40]
        return theme
    except:
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
    print(f"🚀 Processando: {audio_path.name}")
    print('='*50)

    model = setup_gemini()
    segments = split_audio(audio_path)
    temp_dir = segments[0].parent if len(segments) > 1 else None

    transcriptions = []

    try:
        for i, segment_path in enumerate(segments, 1):
            text = transcribe_segment(model, segment_path, i, len(segments))
            transcriptions.append(text)
            print(f"   ✓ Parte {i} transcrita ({len(text)} caracteres)")
    finally:
        if temp_dir and temp_dir.exists() and 'audio_segments_' in str(temp_dir):
            shutil.rmtree(temp_dir)

    full_transcription = "\n\n".join(transcriptions)
    print(f"\n📝 Transcrição completa: {len(full_transcription)} caracteres")

    theme = extract_theme(model, full_transcription)
    print(f"   Tema: {theme}")

    output_path = save_transcription(audio_path.name, theme, full_transcription)

    print(f"\n🎉 SUCESSO!")
    print(f"   Arquivo salvo em: {output_path}")

    return output_path


def process_folder(folder_path: Path):
    audio_files = [
        f for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]

    if not audio_files:
        print(f"❌ Nenhum arquivo de áudio encontrado em: {folder_path}")
        return

    print(f"📁 Encontrados {len(audio_files)} arquivos de áudio")

    for audio_file in sorted(audio_files):
        try:
            process_audio(audio_file)
        except Exception as e:
            print(f"❌ Erro ao processar {audio_file.name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Transcreve áudios usando Gemini AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python transcribe_audio.py audio.mp3
    python transcribe_audio.py --folder ~/Audios
    python transcribe_audio.py --folder ~/Audios --segment-duration 5
        """
    )

    parser.add_argument('audio', nargs='?', help='Caminho do arquivo de áudio')
    parser.add_argument('--folder', '-f', help='Pasta com arquivos de áudio')
    parser.add_argument('--segment-duration', '-s', type=int, default=10,
                        help='Duração de cada segmento em minutos (padrão: 10)')
    parser.add_argument('--output', '-o', help='Pasta de saída para transcrições')

    args = parser.parse_args()

    if args.segment_duration:
        global SEGMENT_DURATION_MS
        SEGMENT_DURATION_MS = args.segment_duration * 60 * 1000

    if args.output:
        global OUTPUT_DIR
        OUTPUT_DIR = Path(args.output)

    if args.folder:
        folder_path = Path(args.folder).expanduser()
        if not folder_path.exists():
            print(f"❌ Pasta não encontrada: {folder_path}")
            sys.exit(1)
        process_folder(folder_path)
    elif args.audio:
        audio_path = Path(args.audio).expanduser()
        if not audio_path.exists():
            print(f"❌ Arquivo não encontrado: {audio_path}")
            sys.exit(1)
        process_audio(audio_path)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
