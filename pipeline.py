#!/usr/bin/env python3
# ============================================================
# pipeline.py — Moteur ViralClip
# Usage : python3 pipeline.py "<lien_video>" "<chemin_sortie.mp4>"
#
# Ce script fait exactement ce qui a été validé sur Colab :
# télécharger -> transcrire -> générer sous-titres animés -> exporter
# Adapté pour tourner automatiquement sur un serveur (Railway).
# ============================================================

import sys
import subprocess
import whisper
import os

def ass_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 pipeline.py <lien_video> <sortie.mp4>")
        sys.exit(1)

    video_url = sys.argv[1]
    output_path = sys.argv[2]

    work_dir = os.path.dirname(output_path) or "."
    source_path = os.path.join(work_dir, "source_temp.mp4")
    ass_path = os.path.join(work_dir, "subs_temp.ass")

    # --- 1. Télécharger la vidéo ---
    print("Téléchargement...")
    result = subprocess.run(
        ["yt-dlp", "-f", "mp4", "-o", source_path, video_url],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Erreur téléchargement:", result.stderr)
        sys.exit(1)

    # --- 2. Transcrire avec timing mot par mot ---
    print("Transcription...")
    model = whisper.load_model("base")
    transcription = model.transcribe(source_path, word_timestamps=True)

    words = []
    for segment in transcription["segments"]:
        for w in segment.get("words", []):
            words.append({
                "text": w["word"].strip(),
                "start": w["start"],
                "end": w["end"]
            })

    if not words:
        print("Aucun mot détecté (vidéo sans son ?)")
        sys.exit(1)

    # --- 3. Générer le fichier .ass ---
    print("Génération des sous-titres...")
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Default,Arial Black,90,&H00FFFFFF,&H00000000,1,1,6,0,5,50,50,700

[Events]
Format: Layer, Start, End, Style, Text
"""
    HIGHLIGHT_COLOR = "&H0000FFFF"
    events = []
    for w in words:
        start = ass_timestamp(w["start"])
        end = ass_timestamp(w["end"])
        text = w["text"].upper()
        events.append(f"Dialogue: 0,{start},{end},Default,{{\\c{HIGHLIGHT_COLOR}}}{text}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write("\n".join(events))

    # --- 4. Incruster les sous-titres avec FFmpeg ---
    print("Export final...")
    result = subprocess.run([
        "ffmpeg", "-y", "-i", source_path,
        "-vf", f"ass={ass_path}",
        "-c:a", "copy", output_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("Erreur FFmpeg:", result.stderr)
        sys.exit(1)

    # --- 5. Nettoyage des fichiers temporaires ---
    for f in [source_path, ass_path]:
        if os.path.exists(f):
            os.remove(f)

    print(f"Terminé : {output_path}")

if __name__ == "__main__":
    main()
