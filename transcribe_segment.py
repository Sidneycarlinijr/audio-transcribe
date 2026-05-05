#!/usr/bin/env python3
import sys
import os
import warnings
warnings.filterwarnings("ignore")

try:
    from deepgram import DeepgramClient
except ImportError:
    print("ERROR: deepgram-sdk não instalado. Execute: pip install deepgram-sdk", file=sys.stderr)
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Uso: transcribe_segment.py <caminho_do_audio>", file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]
    api_key = os.environ.get('DEEPGRAM_API_KEY')

    if not api_key:
        print("ERROR: DEEPGRAM_API_KEY não definida", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"ERROR: Arquivo não encontrado: {audio_path}", file=sys.stderr)
        sys.exit(1)

    client = DeepgramClient(api_key=api_key)

    with open(audio_path, "rb") as f:
        buffer_data = f.read()

    try:
        response = client.listen.v1.media.transcribe_file(
            request=buffer_data,
            model="nova-2",
            language="pt-BR",
            smart_format=True,
            punctuate=True,
            diarize=True,
            utterances=True,
        )
    except Exception as e:
        print(f"ERROR: Falha na transcrição: {e}", file=sys.stderr)
        sys.exit(1)

    if response.results and response.results.utterances:
        lines = []
        for utt in response.results.utterances:
            speaker = utt.speaker + 1
            lines.append(f"Orador {speaker}: {utt.transcript}")
        print("\n".join(lines))
        return

    if response.results and response.results.channels:
        alt = response.results.channels[0].alternatives[0]
        if alt and alt.transcript:
            print(alt.transcript)
            return

    print("[Sem conteúdo audível neste segmento]")

if __name__ == '__main__':
    main()
