#!/usr/bin/env python3
"""Video demo icaria 16:9 2:40 (160s) v3:
- Sin textos quemados (limpio, solo placas de logo)
- Zoom suave sin temblor: lienzo 7680px + recorrido corto (6%)
- Capturas reales con mas protagonismo (apertura, presentacion, recap, CTA)
"""
import os, subprocess, sys
import imageio_ffmpeg
from PIL import Image, ImageOps

BASE = "/home/user/arena.ai/video_icaria"
IMG = os.path.join(BASE, "img")
RAW = os.path.join(BASE, "raw")
SEG = os.path.join(BASE, "seg")
AUDIO = "/home/user/arena.ai/audio/icaria_reel_final_2m40s.mp3"
OUT = os.path.join(BASE, "icaria_reel_16x9_2m40s_v3.mp4")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 30
W, H = 1920, 1080
SW, SH = 7680, 4320   # lienzo grande => zoompan sin temblor
ZOOM = 0.06           # recorrido corto => movimiento elegante

os.makedirs(SEG, exist_ok=True)

# (fuente, duracion, zoom_in?/None=placa estatica)
SEGS = [
    (f"{RAW}/icaria1.jpg",          3.0, None),    # 0:00 logo
    (f"{RAW}/01.png",               4.5, True),    # Bombal
    (f"{RAW}/02.png",               4.5, False),   # Oliva
    (f"{IMG}/02_problema.jpg",     16.0, False),   # el problema
    (f"{RAW}/03.png",              10.0, True),    # Alkimia
    (f"{RAW}/04.png",              10.0, False),   # Smartphone
    (f"{IMG}/05_manual.jpg",       13.5, True),    # manual de marca
    (f"{IMG}/06_dispositivos.jpg", 13.5, False),   # dos tiendas
    (f"{IMG}/07_movil_tienda.jpg", 13.0, True),    # tienda funcionando
    (f"{IMG}/08_dashboard.jpg",    12.0, False),   # panel admin
    (f"{IMG}/09_conversacion.jpg", 13.0, True),    # personas
    (f"{IMG}/10_equipo.jpg",       12.0, False),   # persona a persona
    (f"{RAW}/01.png",               5.0, True),    # recap Bombal
    (f"{RAW}/02.png",               5.0, False),   # recap Oliva
    (f"{RAW}/03.png",               5.0, True),    # recap Alkimia
    (f"{RAW}/04.png",               5.0, False),   # recap Smartphone
    (f"{RAW}/02.png",              10.0, True),    # CTA: como quedaria tu marca
    (f"{RAW}/icaria2.jpg",          5.0, None),    # cierre logo 3D
]

def bake(src, dst):
    ImageOps.fit(Image.open(src).convert("RGB"), (SW, SH), Image.LANCZOS).save(dst, quality=88)
    print("seg:", dst, os.path.getsize(dst) // 1024, "KB")

seg_files = []
for i, (src, dur, zin) in enumerate(SEGS):
    outp = os.path.join(SEG, f"v3_{i:02d}.jpg")
    bake(src, outp)
    seg_files.append(outp)

cmd = [FFMPEG, "-y"]
for i, (src, dur, zin) in enumerate(SEGS):
    if zin is None:
        cmd += ["-loop", "1", "-t", str(dur), "-i", seg_files[i]]
    else:
        cmd += ["-i", seg_files[i]]
audio_idx = len(SEGS)
cmd += ["-i", AUDIO]

fc = []
for i, (src, dur, zin) in enumerate(SEGS):
    frames = int(round(dur * FPS))
    if zin is None:
        fc.append(
            f"[{i}:v]scale={W}:{H},fps={FPS},"
            f"fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4:.2f}:d=0.4,"
            f"setsar=1,format=yuv420p[v{i}]"
        )
    else:
        z = f"1+{ZOOM}*on/{frames-1}" if zin else f"1+{ZOOM}-({ZOOM}*on/{frames-1})"
        fc.append(
            f"[{i}:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={W}x{H}:fps={FPS},"
            f"fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4:.2f}:d=0.4,"
            f"setsar=1,format=yuv420p[v{i}]"
        )
fc.append("".join(f"[v{i}]" for i in range(len(SEGS))) + f"concat=n={len(SEGS)}:v=1:a=0[vout]")

cmd += ["-filter_complex", ";".join(fc),
        "-map", "[vout]", "-map", f"{audio_idx}:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart", "-t", "160", OUT]

total = sum(d for _, d, _ in SEGS)
print("total video: %.1fs | corriendo ffmpeg..." % total)
p = subprocess.run(cmd, capture_output=True, text=True)
print("\n".join((p.stdout + "\n" + p.stderr).strip().splitlines()[-4:]))
if p.returncode != 0:
    sys.exit("ffmpeg fallo")
print("OK:", OUT, os.path.getsize(OUT) // 1024, "KB")
