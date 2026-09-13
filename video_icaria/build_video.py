#!/usr/bin/env python3
"""Arma el video demo icaria 16:9 2:40 (160s).
Titulos quemados con PIL (el ffmpeg disponible no trae drawtext) + Ken Burns + audio final."""
import os, subprocess, sys
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = "/home/user/arena.ai/video_icaria"
IMG = os.path.join(BASE, "img")
SEG = os.path.join(BASE, "seg")
AUDIO = "/home/user/arena.ai/audio/icaria_reel_final_2m40s.mp3"
OUT = os.path.join(BASE, "icaria_reel_16x9_2m40s.mp4")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FPS = 30
W, H = 1920, 1080
SW, SH = 2560, 1440  # lienzo de trabajo para zoompan

os.makedirs(SEG, exist_ok=True)

# (fuente, duracion_seg, zoom_in?, titulo o None) ; zoom None = placa estatica
SEGS = [
    ("card_open.png",       3.0, None,  None),
    ("01_alimentos.jpg",    9.0, True,  "Ni largo, ni caro, ni complicado"),
    ("02_problema.jpg",    16.0, False, "O te adapt\u00e1s vos\u2026 o pag\u00e1s de m\u00e1s"),
    ("03_vinos.jpg",       10.0, True,  "icaria nace para resolver eso"),
    ("04_velas_tech.jpg",  10.0, False, "Adaptable a cualquier rubro"),
    ("05_manual.jpg",      13.5, True,  "Se moldea a la identidad de tu marca"),
    ("06_dispositivos.jpg", 13.5, False, "Tu est\u00e9tica, tu tono, tu forma de vender"),
    ("07_movil_tienda.jpg", 13.0, True,  "Hablamos de horas"),
    ("08_dashboard.jpg",   12.0, False, "Un panel claro para gestionar todo"),
    ("09_conversacion.jpg", 13.0, True,  "Hablamos con personas"),
    ("10_equipo.jpg",      12.0, False, "De persona a persona"),
    ("03_vinos.jpg",       20.0, False, "R\u00e1pida, flexible y humana"),
    ("07_movil_tienda.jpg", 10.0, False, "Escribinos"),
    ("card_end.png",        5.0, None,  None),
]

def draw_tracked(draw, cx, y_center, text, font, fill, tracking):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y_center), ch, font=font, fill=fill, anchor="lm")
        x += w + tracking

def make_card(path, wordmark_size, wm_y, subtitle=None, sub_size=54, sub_y=700):
    im = Image.new("RGB", (W, H), (244, 241, 234))
    d = ImageDraw.Draw(im)
    f_wm = ImageFont.truetype(FONT, wordmark_size)
    draw_tracked(d, W // 2, wm_y, "icaria", f_wm, (17, 17, 17), tracking=int(wordmark_size * 0.12))
    if subtitle:
        f_sub = ImageFont.truetype(FONT, sub_size)
        d.text((W // 2, sub_y), subtitle, font=f_sub, fill=(90, 88, 84), anchor="mm")
    im.save(path)
    print("card:", path)

make_card(os.path.join(SEG, "card_open.png"), 230, 500,
          subtitle="Tu e-commerce, listo para vender", sub_size=56, sub_y=720)
make_card(os.path.join(SEG, "card_end.png"), 170, 420,
          subtitle="En pocas horas, tu tienda online funcionando.", sub_size=52, sub_y=620)

F_TITLE = ImageFont.truetype(FONT, 62)
F_WM = ImageFont.truetype(FONT, 44)

def bake(photo_path, out_path, title):
    im = ImageOps.fit(Image.open(photo_path).convert("RGB"), (SW, SH), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    # marca de agua
    d.text((203, 133), "icaria", font=F_WM, fill=(0, 0, 0, 170))
    d.text((200, 130), "icaria", font=F_WM, fill=(255, 255, 255, 235))
    # titulo inferior (margenes seguros para zoom 1.10)
    x, yb = 200, SH - 260
    d.text((x + 4, yb + 4), title, font=F_TITLE, fill=(0, 0, 0, 190))
    d.text((x, yb), title, font=F_TITLE, fill=(255, 255, 255, 255),
           stroke_width=2, stroke_fill=(0, 0, 0, 160))
    im.save(out_path, quality=92)
    print("seg:", out_path)

seg_files = []
for i, (fname, dur, zin, title) in enumerate(SEGS):
    if zin is None:
        seg_files.append(os.path.join(SEG, fname))
    else:
        outp = os.path.join(SEG, f"seg{i:02d}.jpg")
        bake(os.path.join(IMG, fname), outp, title)
        seg_files.append(outp)

# ---- ffmpeg ----
cmd = [FFMPEG, "-y"]
for i, (fname, dur, zin, title) in enumerate(SEGS):
    if zin is None:
        cmd += ["-loop", "1", "-t", str(dur), "-i", seg_files[i]]
    else:
        cmd += ["-i", seg_files[i]]
audio_idx = len(SEGS)
cmd += ["-i", AUDIO]

fc = []
for i, (fname, dur, zin, title) in enumerate(SEGS):
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

total = sum(d for _, d, _, _ in SEGS)
print("total video: %.1fs | corriendo ffmpeg..." % total)
p = subprocess.run(cmd, capture_output=True, text=True)
print("\n".join((p.stdout + "\n" + p.stderr).strip().splitlines()[-5:]))
if p.returncode != 0:
    sys.exit("ffmpeg fallo")
print("OK:", OUT, os.path.getsize(OUT) // 1024, "KB")
