#!/usr/bin/env python3
"""Video demo icaria 16:9 2:40 (160s) v2: capturas reales + logos oficiales + conceptos IA.
Titulos quemados con PIL (contraste automatico) + Ken Burns + audio final."""
import os, subprocess, sys
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat

BASE = "/home/user/arena.ai/video_icaria"
IMG = os.path.join(BASE, "img")       # visuales IA (conceptos)
RAW = os.path.join(BASE, "raw")       # capturas reales + logos
SEG = os.path.join(BASE, "seg")
AUDIO = "/home/user/arena.ai/audio/icaria_reel_final_2m40s.mp3"
OUT = os.path.join(BASE, "icaria_reel_16x9_2m40s.mp4")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FPS = 30
W, H = 1920, 1080
SW, SH = 2560, 1440

INK = (17, 17, 17)        # #111111 Negro Profundo
CARBON = (42, 42, 42)     # #2A2A2A Gris Carbon
WHITE = (255, 255, 255)

os.makedirs(SEG, exist_ok=True)

# (fuente, duracion, zoom_in?/None=placa, titulo|None, marca_agua?, subtitulo_placa|None)
SEGS = [
    (f"{RAW}/icaria1.jpg",          3.0, None,  None, False, None),   # apertura logo real
    (f"{RAW}/01.png",               4.5, True,  "Ni largo, ni caro, ni complicado", True, None),
    (f"{RAW}/02.png",               4.5, False, "Todas corriendo sobre la misma base", True, None),
    (f"{IMG}/02_problema.jpg",     16.0, False, "O te adapt\u00e1s vos\u2026 o pag\u00e1s de m\u00e1s", True, None),
    (f"{RAW}/03.png",              10.0, True,  "icaria nace para resolver eso", True, None),
    (f"{RAW}/04.png",              10.0, False, "Adaptable a cualquier rubro", True, None),
    (f"{IMG}/05_manual.jpg",       13.5, True,  "Se moldea a la identidad de tu marca", True, None),
    (f"{IMG}/06_dispositivos.jpg", 13.5, False, "Tu est\u00e9tica, tu tono, tu forma de vender", True, None),
    (f"{IMG}/07_movil_tienda.jpg", 13.0, True,  "Hablamos de horas", True, None),
    (f"{IMG}/08_dashboard.jpg",    12.0, False, "Un panel claro para gestionar todo", True, None),
    (f"{IMG}/09_conversacion.jpg", 13.0, True,  "Hablamos con personas", True, None),
    (f"{IMG}/10_equipo.jpg",       12.0, False, "De persona a persona", True, None),
    (f"{RAW}/01.png",               5.0, True,  "R\u00e1pida, flexible y humana", True, None),  # recap cierre
    (f"{RAW}/02.png",               5.0, False, None, True, None),
    (f"{RAW}/03.png",               5.0, True,  None, True, None),
    (f"{RAW}/04.png",               5.0, False, None, True, None),
    (f"{IMG}/07_movil_tienda.jpg", 10.0, False, "Escribinos", True, None),
    (f"{RAW}/icaria2.jpg",          5.0, None,  None, False, "En pocas horas, tu tienda online funcionando."),
]

F_TITLE = ImageFont.truetype(FONT, 64)
F_WM = ImageFont.truetype(FONT, 44)
F_SUB = ImageFont.truetype(FONT, 58)

def luminance(im, box):
    return ImageStat.Stat(im.crop(box).convert("L")).mean[0]

def scheme_for(lum):
    # fondo claro -> texto tinta con borde blanco ; fondo oscuro -> blanco con borde negro
    return (INK, WHITE) if lum > 150 else (WHITE, INK)

def bake_photo(src, dst, title, wm):
    im = ImageOps.fit(Image.open(src).convert("RGB"), (SW, SH), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    if wm:
        fill, stroke = scheme_for(luminance(im, (150, 80, 760, 230)))
        d.text((200, 130), "icaria", font=F_WM, fill=fill,
               stroke_width=1, stroke_fill=stroke)
    if title:
        fill, stroke = scheme_for(luminance(im, (150, SH - 460, 1750, SH - 120)))
        d.text((200, SH - 280), title, font=F_TITLE, fill=fill,
               stroke_width=3, stroke_fill=stroke)
    im.save(dst, quality=92)
    print("seg:", dst)

def bake_card(src, dst, subtitle):
    im = ImageOps.fit(Image.open(src).convert("RGB"), (SW, SH), Image.LANCZOS)
    if subtitle:
        d = ImageDraw.Draw(im)
        d.text((SW // 2, 1230), subtitle, font=F_SUB, fill=CARBON, anchor="mm")
    im.save(dst, quality=92)
    print("card:", dst)

seg_files = []
for i, (src, dur, zin, title, wm, sub) in enumerate(SEGS):
    outp = os.path.join(SEG, f"seg{i:02d}.jpg")
    if zin is None:
        bake_card(src, outp, sub)
    else:
        bake_photo(src, outp, title, wm)
    seg_files.append(outp)

# ---- ffmpeg ----
cmd = [FFMPEG, "-y"]
for i, (src, dur, zin, title, wm, sub) in enumerate(SEGS):
    if zin is None:
        cmd += ["-loop", "1", "-t", str(dur), "-i", seg_files[i]]
    else:
        cmd += ["-i", seg_files[i]]
audio_idx = len(SEGS)
cmd += ["-i", AUDIO]

fc = []
for i, (src, dur, zin, title, wm, sub) in enumerate(SEGS):
    frames = int(round(dur * FPS))
    if zin is None:
        fc.append(
            f"[{i}:v]scale={W}:{H},fps={FPS},"
            f"fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4:.2f}:d=0.4,"
            f"setsar=1,format=yuv420p[v{i}]"
        )
    else:
        z = f"1+0.10*on/{frames-1}" if zin else f"1.10-0.10*on/{frames-1}"
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

total = sum(d for _, d, _, _, _, _ in SEGS)
print("total video: %.1fs | corriendo ffmpeg..." % total)
p = subprocess.run(cmd, capture_output=True, text=True)
print("\n".join((p.stdout + "\n" + p.stderr).strip().splitlines()[-4:]))
if p.returncode != 0:
    sys.exit("ffmpeg fallo")
print("OK:", OUT, os.path.getsize(OUT) // 1024, "KB")
