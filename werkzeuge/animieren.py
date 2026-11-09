"""Animiert Tobis Foto ohne KI, als nahtlose Schleife (MP4, 720 x 900, ohne Ton).

  zoom    Idee 10: langsamer Zoom mit Tiefe (Person und Wand bewegen sich gegeneinander)
  formen  Idee 8:  diagonale RANG + KLUR-Formen gleiten hinter Tobi durchs Bild

Aufruf: python animieren.py zoom|formen <ausgabe.mp4>
Braucht numpy, Pillow und ffmpeg. Eingaben: ../quelle/tobias-4x5-voll.jpg und ../quelle/maske.png
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HIER = Path(__file__).resolve().parent
QUELLE = HIER.parent / "quelle"
W, H, FPS = 720, 900, 30


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255


SLATE, SKY, BERRY, ROSE = map(hex2rgb, ("#647887", "#B8D7E9", "#B35667", "#C8838F"))


def laden():
    foto = Image.open(QUELLE / "tobias-4x5-voll.jpg").convert("RGB").resize((W, H), Image.LANCZOS)
    maske = Image.open(QUELLE / "maske.png").convert("L").resize((W, H), Image.LANCZOS)
    # kleine Löcher schließen, Kante 1 px nach innen ziehen und weich machen (gegen hellen Rand)
    maske = maske.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    maske = maske.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    # Randzeilen der Vision-Maske sind manchmal nicht ganz schwarz: oben, links, rechts nullen
    m = np.asarray(maske, dtype=np.float32) / 255
    m[:6, :] = 0; m[:, :6] = 0; m[:, -6:] = 0
    rgb = np.asarray(foto, dtype=np.float32) / 255
    a = m[..., None]
    # Für die Wand die Maske großzügig erweitern, damit kein Kantenlicht der Person in der Wand bleibt
    gross = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(4))
    inv = (1 - np.asarray(gross, dtype=np.float32) / 255)[..., None]
    num = Image.fromarray((rgb * inv * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(60))
    den = Image.fromarray((inv[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(60))
    wand = np.asarray(num, dtype=np.float32) / 255 / np.maximum(np.asarray(den, dtype=np.float32)[..., None] / 255, 1e-3)
    wand = np.clip(wand, 0, 1)
    wand = rgb * inv + wand * (1 - inv)
    return rgb, a, wand


def transform(arr, scale, dx, dy, cx=0.5, cy=0.35):
    """Skaliert um den Punkt (cx, cy) und verschiebt (in Pixeln). Bilinear."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    px, py = cx * W, cy * H
    sx = (xs - px - dx) / scale + px
    sy = (ys - py - dy) / scale + py
    sx = np.clip(sx, 0, W - 1.001); sy = np.clip(sy, 0, H - 1.001)
    x0 = sx.astype(np.int32); y0 = sy.astype(np.int32)
    fx = (sx - x0)[..., None]; fy = (sy - y0)[..., None]
    a = arr if arr.ndim == 3 else arr[..., None]
    out = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy)
           + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)
    return out


def ease(t):
    """0 → 1 → 0 über eine Schleife, weich an beiden Enden."""
    return (1 - math.cos(2 * math.pi * t)) / 2


def frames_zoom(rgb, a, wand, dauer=6):
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    n = dauer * FPS
    for i in range(n):
        s = ease(i / n)
        # Person kommt näher, Wand weicht leicht zurück und verschiebt sich gegenläufig
        p_rgb = transform(rgb, 1 + 0.055 * s, -6 * s, 4 * s)
        p_a = transform(a, 1 + 0.055 * s, -6 * s, 4 * s)
        w = transform(wand, 1 + 0.012 * s, 14 * s, -4 * s)
        # weicher Studio-Lichtkegel auf der Wand, wandert gegenläufig → Tiefe sichtbar
        lx, ly = W * (0.70 + 0.06 * s), H * (0.28 - 0.02 * s)
        licht = np.exp(-(((xs - lx) / (W * 0.42)) ** 2 + ((ys - ly) / (H * 0.38)) ** 2))[..., None]
        w = np.clip(w * (0.95 + 0.09 * licht), 0, 1)
        # leichte Vignette, die mit dem Zoom etwas dichter wird
        vig = 1 - (0.06 + 0.03 * s) * (((xs / W - 0.5) * 2) ** 2 + ((ys / H - 0.45) * 1.6) ** 2)[..., None]
        bild = (w * (1 - p_a) + p_rgb * p_a) * vig
        yield bild


def frames_formen(rgb, a, wand, dauer=8):
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    n = dauer * FPS
    diag = xs + (H - ys)          # wächst nach rechts oben → Formen wandern diagonal nach rechts oben
    span = W + H + 900            # Weg, nach dem eine Form wieder an derselben Stelle ist
    # (Farbe, Breite in px, Startversatz, Umläufe pro Schleife, Deckkraft)
    baender = [
        (SKY, 150, 0, 1, 0.95),
        (SLATE, 230, 520, 1, 1.0),
        (BERRY, 26, 860, 1, 1.0),
        (SKY, 60, 1180, 1, 0.75),
        (SLATE, 90, 1500, 1, 0.55),
    ]
    schatten_a = np.asarray(
        Image.fromarray((a[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14)),
        dtype=np.float32)[..., None] / 255
    for i in range(n):
        t = i / n
        bild = wand.copy()
        for farbe, breite, start, k, deck in baender:
            c = ((start + k * t * span) % span) - 450       # Mittellinie des Bands
            d = np.abs(diag - c) - breite / 2
            m = np.clip(0.5 - d / 1.2, 0, 1)[..., None] * deck  # weiche 1-px-Kante
            bild = bild * (1 - m) + farbe * m
        # zarter Schatten der Person auf den Formen, leicht nach rechts unten versetzt
        sh = np.zeros_like(schatten_a); sh[10:, 8:] = schatten_a[:-10, :-8]   # verschieben ohne Umlauf
        bild = bild * (1 - 0.18 * sh)
        s = ease(t)
        p_rgb = transform(rgb, 1 + 0.012 * s, 0, 0)
        p_a = transform(a, 1 + 0.012 * s, 0, 0)
        yield bild * (1 - p_a) + p_rgb * p_a


def schreiben(frames, ziel):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
           "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-movflags", "+faststart", str(ziel)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        sys.exit("ffmpeg-Fehler")


if __name__ == "__main__":
    art, ziel = sys.argv[1], Path(sys.argv[2])
    rgb, a, wand = laden()
    schreiben(frames_zoom(rgb, a, wand) if art == "zoom" else frames_formen(rgb, a, wand), ziel)
    print("fertig:", ziel)
