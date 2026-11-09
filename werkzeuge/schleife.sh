#!/usr/bin/env bash
# Macht aus einem KI-Clip eine nahtlose Web-Schleife:
# Die letzten Sekunden werden weich in den Anfang überblendet, dann wird auf 720 px Breite
# verkleinert, der Ton entfernt und für schnelles Laden gespeichert (H.264, faststart).
# Aufruf: bash schleife.sh <eingabe.mp4> <ausgabe.mp4> [ueberblendung_sekunden=0.6]
set -euo pipefail
IN=$1; OUT=$2; D=${3:-0.6}
L=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
OFF=$(python3 -c "print(round($L - 2*$D, 3))")
ffmpeg -loglevel error -y -i "$IN" -filter_complex "
  [0:v]fps=30,scale=720:-2:flags=lanczos,setsar=1,split[a][b];
  [a]trim=start=$D,setpts=PTS-STARTPTS[main];
  [b]trim=end=$D,setpts=PTS-STARTPTS[head];
  [main][head]xfade=transition=fade:duration=$D:offset=$OFF,format=yuv420p[v]" \
  -map "[v]" -an -c:v libx264 -preset slow -crf 24 -profile:v high -movflags +faststart "$OUT"
echo "fertig: $OUT ($(du -h "$OUT" | cut -f1))"
