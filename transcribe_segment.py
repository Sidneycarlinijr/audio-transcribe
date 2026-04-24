#!/usr/bin/env python3
import sys
import os
import time

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: google-generativeai não instalado", file=sys.stderr)
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Uso: transcribe_segment.py <caminho_do_audio>", file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]
    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        print("ERROR: GEMINI_API_KEY não definida", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(audio_path):
        print(f"ERROR: Arquivo não encontrado: {audio_path}", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    audio_file = genai.upload_file(audio_path)

    while audio_file.state.name == "PROCESSING":
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)

    if audio_file.state.name == "FAILED":
        print("ERROR: Upload falhou", file=sys.stderr)
        sys.exit(1)

    prompt = """Transcreva este áudio integralmente em português do Brasil.
Identifique os diferentes oradores (ex: Orador 1, Orador 2) sempre que a voz mudar.
Formate como: "Orador X: [fala]".
Retorne APENAS a transcrição, sem comentários ou análises."""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt, audio_file])
            break
        except Exception as e:
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                wait = 40 * (attempt + 1)
                print(f"Rate limit atingido, aguardando {wait}s... (tentativa {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(wait)
                if attempt == max_retries - 1:
                    raise
            else:
                raise

    try:
        genai.delete_file(audio_file.name)
    except:
        pass

    if response.candidates and response.candidates[0].content.parts:
        print(response.text)
    else:
        print("[Sem conteúdo audível neste segmento]")

if __name__ == '__main__':
    main()
