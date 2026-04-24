#!/usr/bin/env python3
"""
Script para dividir áudios longos em partes de 30 minutos.

Uso:
    python split_audio.py <caminho_do_audio>
    python split_audio.py --folder <pasta_com_audios>

Requisitos:
    pip install pydub
    sudo apt-get install ffmpeg
"""

import sys
import argparse
from pathlib import Path

try:
    from pydub import AudioSegment
except ImportError:
    print("❌ Erro: pydub não instalado. Execute: pip install pydub")
    sys.exit(1)


SEGMENT_DURATION_MS = 30 * 60 * 1000  # 30 minutos em milissegundos
SUPPORTED_FORMATS = {'.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac'}


def split_audio(audio_path: Path, output_dir: Path = None, segment_duration_ms: int = SEGMENT_DURATION_MS):
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

    if output_dir is None:
        output_dir = audio_path.parent / f"{audio_path.stem}_partes"

    output_dir.mkdir(parents=True, exist_ok=True)

    if duration_ms <= segment_duration_ms:
        print("   Áudio curto, copiando sem dividir...")
        output_path = output_dir / f"{audio_path.stem}_parte_01.mp3"
        audio.export(output_path, format='mp3')
        print(f"   ✓ Salvo: {output_path.name}")
        return [output_path]

    num_segments = (duration_ms + segment_duration_ms - 1) // segment_duration_ms
    print(f"   Dividindo em {num_segments} partes...")

    segments = []

    for i in range(num_segments):
        start = i * segment_duration_ms
        end = min((i + 1) * segment_duration_ms, duration_ms)

        segment = audio[start:end]
        segment_path = output_dir / f"{audio_path.stem}_parte_{i+1:02d}.mp3"
        segment.export(segment_path, format='mp3')
        segments.append(segment_path)

        start_min = start / 1000 / 60
        end_min = end / 1000 / 60
        print(f"   ✓ Parte {i+1}/{num_segments}: {start_min:.0f}-{end_min:.0f} min → {segment_path.name}")

    print(f"\n🎉 Concluído! {len(segments)} arquivos salvos em: {output_dir}")
    return segments


def process_folder(folder_path: Path, output_dir: Path = None):
    audio_files = [
        f for f in folder_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS
    ]

    if not audio_files:
        print(f"❌ Nenhum arquivo de áudio encontrado em: {folder_path}")
        return

    print(f"📁 Encontrados {len(audio_files)} arquivos de áudio\n")

    for audio_file in sorted(audio_files):
        try:
            split_audio(audio_file, output_dir)
            print()
        except Exception as e:
            print(f"❌ Erro ao processar {audio_file.name}: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Divide áudios longos em partes de 30 minutos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python split_audio.py audio.mp3
    python split_audio.py --folder ~/Audios
    python split_audio.py audio.mp3 --output ~/Saida
    python split_audio.py audio.mp3 --segment-duration 15
        """
    )

    parser.add_argument('audio', nargs='?', help='Caminho do arquivo de áudio')
    parser.add_argument('--folder', '-f', help='Pasta com arquivos de áudio')
    parser.add_argument('--output', '-o', help='Pasta de saída')
    parser.add_argument('--segment-duration', '-s', type=int, default=30,
                        help='Duração de cada segmento em minutos (padrão: 30)')

    args = parser.parse_args()

    segment_duration_ms = args.segment_duration * 60 * 1000
    output_dir = Path(args.output) if args.output else None

    if args.folder:
        folder_path = Path(args.folder).expanduser()
        if not folder_path.exists():
            print(f"❌ Pasta não encontrada: {folder_path}")
            sys.exit(1)
        process_folder(folder_path, output_dir)
    elif args.audio:
        audio_path = Path(args.audio).expanduser()
        if not audio_path.exists():
            print(f"❌ Arquivo não encontrado: {audio_path}")
            sys.exit(1)
        split_audio(audio_path, output_dir, segment_duration_ms)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
