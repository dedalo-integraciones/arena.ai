#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un sello redondo antiguo ("TU MARCA") en blanco y en negro.

CONVENCIÓN DE UNIDADES
  Todas las funciones de dibujo reciben medidas en "unidades finales" (0..BASE).
  La conversión a píxeles del lienzo supersampleado (x SS) la hace cada helper.
  Esto evita mezclar escalas y es el origen del bug que tenía la v1.

Salidas (en esta carpeta):
  sello-<variante>-<tinta>-fondo-<fondo>.png    cuadrado con fondo
  sello-<variante>-<tinta>-fondo-<fondo>.jpg    idem en JPEG
  sello-<variante>-<tinta>-transparente.png     sin fondo (para superponer)
  web/sello-<tinta>-<px>.png                    tamaños listos para web
  demo-portadas.jpg                             cómo se ve sobre las portadas
"""

import math
import os
import subprocess
import sys
import zipfile

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# ----------------------------------------------------------------------------
BASE = 1200                       # tamaño final del sello (px)
SS   = 3                          # supersampling (se dibuja x3 y se reduce)
W    = BASE * SS
HERE = os.path.dirname(os.path.abspath(__file__))
WEB  = os.path.join(HERE, "web")
FONTS = os.path.join(HERE, "fonts")

INK = {"blanco": (255, 255, 255), "negro": (12, 12, 12)}
BG  = {"negro": (0, 0, 0), "blanco": (255, 255, 255)}

# Geometría, en unidades finales sobre un lienzo de 1200x1200
# Proporciones tomadas de sellos clásicos: anillo grueso de borde, banda de texto
# de ~85 unidades de altura, aro fino y medallón central.
R_OUTER, W_OUTER = 556, 15        # anillo exterior (548..564)
R_BAND           = 507            # radio del texto en arco (~467..547 de banda útil)
F_TOP, F_BOTTOM  = 118, 80        # cuerpos de fuente (alto de mayúscula ~80 y ~54)
R_RING1, R_RING2 = 430, 422       # aro doble que encierra el medallón central
MED_DOTS_R, MED_DOTS_N, MED_DOT = 280, 16, 6.0     # guirnalda del medallón


def u(v):
    """unidades finales -> píxeles del lienzo supersampleado"""
    return v * SS


# ----------------------------------------------------------------------------
# Tipografías
# ----------------------------------------------------------------------------
FONT_FILES = {
    "serif_bold": "STIXGeneralBol.ttf",     # serif clásica, estética Times
    "serif":      "STIXGeneral.ttf",
}
FALLBACK = {
    "serif_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "serif":      "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
}


def ensure_fonts():
    os.makedirs(FONTS, exist_ok=True)
    missing = [f for f in FONT_FILES.values() if not os.path.exists(os.path.join(FONTS, f))]
    if missing:
        print("· Provisionando tipografías desde PyPI (matplotlib)…")
        tmp = os.path.join(HERE, ".cache")
        os.makedirs(tmp, exist_ok=True)
        subprocess.run([sys.executable, "-m", "pip", "download", "--no-deps", "--quiet",
                        "-d", tmp, "matplotlib"], check=False)
        for whl in os.listdir(tmp):
            if whl.startswith("matplotlib") and whl.endswith(".whl"):
                with zipfile.ZipFile(os.path.join(tmp, whl)) as z:
                    for src in z.namelist():
                        base = src.split("/")[-1]
                        if "/mpl-data/fonts/ttf/" in src and base in missing:
                            with z.open(src) as fi, open(os.path.join(FONTS, base), "wb") as fo:
                                fo.write(fi.read())
    return {k: (os.path.join(FONTS, n) if os.path.exists(os.path.join(FONTS, n))
                else FALLBACK[k]) for k, n in FONT_FILES.items()}


def fnt(fonts, key, size):
    """size = altura de caja en unidades finales"""
    return ImageFont.truetype(fonts[key], max(8, int(round(u(size)))))


# ----------------------------------------------------------------------------
# Helpers de dibujo (entradas en unidades finales)
# ----------------------------------------------------------------------------
def ring(draw, cx, cy, r, width):
    draw.ellipse([u(cx - r), u(cy - r), u(cx + r), u(cy + r)],
                 outline=255, width=max(2, int(round(u(width)))))


def dots(draw, cx, cy, r, n, dot_r, phase=0.0):
    for i in range(n):
        a = math.radians(phase + i * 360.0 / n)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        draw.ellipse([u(x - dot_r), u(y - dot_r), u(x + dot_r), u(y + dot_r)], fill=255)


def star_pts(cx, cy, R, n=5, rot=-90.0, ratio=0.382):
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + i * 180.0 / n)
        rad = R if i % 2 == 0 else R * ratio
        pts.append((u(cx + rad * math.cos(a)), u(cy + rad * math.sin(a))))
    return pts


def text_centered(draw, cx, cy, txt, f, dy=0.0, tracking=0.0):
    """Texto centrado (óptico) en (cx, cy). tracking en unidades finales."""
    if tracking:
        total = sum(f.getlength(c) for c in txt) + u(tracking) * (len(txt) - 1)
        x = u(cx) - total / 2.0
        asc, desc = f.getmetrics()
        y = u(cy + dy) - (asc + desc) / 2.0
        for c in txt:
            draw.text((x, y), c, font=f, fill=255)
            x += f.getlength(c) + u(tracking)
    else:
        box = draw.textbbox((0, 0), txt, font=f)
        asc, desc = f.getmetrics()
        draw.text((u(cx) - (box[2] + box[0]) / 2.0, u(cy + dy) - (asc + desc) / 2.0),
                  txt, font=f, fill=255)


def _stamp(mask, cx, cy, radius, angle, char, f, flip=False):
    """Estampa un carácter rotado sobre la tangente del círculo (radio/centro en u.f.).

    flip=True (arco inferior): el glifo gira 180° para que quede derecho y se lea
    natural; el orden de los caracteres lo invierte quien llama.
    """
    box = f.getbbox(char)
    if box[2] - box[0] <= 0:
        return
    cw, ch = box[2] - box[0], box[3] - box[1]
    pad = 4 * SS
    tile = Image.new("L", (cw + pad * 2, ch + pad * 2), 0)
    ImageDraw.Draw(tile).text((pad - box[0], pad - box[1]), char, font=f, fill=255)
    # Orientación: con el ángulo polar θ (0=este, +90=sur), la dirección "hacia
    # afuera" es -(θ+90) en grados CCW respecto del tope del glifo. En el arco
    # inferior (flip) se suman 180° para que las letras queden derechas.
    deg = -(math.degrees(angle) + 90.0) + (180.0 if flip else 0.0)
    rot = tile.rotate(deg, resample=Image.BICUBIC, expand=True)
    X = u(cx + radius * math.cos(angle)) - rot.width / 2.0
    Y = u(cy + radius * math.sin(angle)) - rot.height / 2.0
    mask.paste(255, (int(round(X)), int(round(Y))), rot)


def arc_text(mask, cx, cy, radius, txt, f, tracking=0.0, flip=False, max_span_deg=196):
    """Reparte el texto sobre el arco. flip=True -> arco inferior, texto derecho."""
    spans = [(f.getlength(c) / SS) / radius + math.radians(tracking) for c in txt]
    total = sum(spans)
    if total > math.radians(max_span_deg):
        raise ValueError(f"El texto '{txt}' ocupa {math.degrees(total):.0f}°, "
                         f"máximo {max_span_deg}°. Bajá el cuerpo o el tracking.")
    if not flip:
        ang = -math.pi / 2 - total / 2.0
        for c, s in zip(txt, spans):
            _stamp(mask, cx, cy, radius, ang + s / 2.0, c, f)
            ang += s
    else:
        ang = math.pi / 2 + total / 2.0
        for c, s in zip(txt, spans):
            _stamp(mask, cx, cy, radius, ang - s / 2.0, c, f, flip=True)
            ang -= s


# ----------------------------------------------------------------------------
# Composición del sello
# ----------------------------------------------------------------------------
def build_mask(variant, fonts):
    m = Image.new("L", (W, W), 0)
    d = ImageDraw.Draw(m)
    C = BASE / 2.0                                              # centro, unidades finales

    ring(d, C, C, R_OUTER, W_OUTER)
    ring(d, C, C, R_RING1, 3.5)
    ring(d, C, C, R_RING2, 1.8)

    f_top, f_bot = fnt(fonts, "serif_bold", F_TOP), fnt(fonts, "serif_bold", F_BOTTOM)

    if variant == "clasico":
        # nombre en el arco superior, rubro/claim abajo, estrella de medallón
        arc_text(m, C, C, R_BAND, "TU MARCA", f_top, tracking=1.0, max_span_deg=150)
        arc_text(m, C, C, R_BAND, "CALIDAD ARTESANAL", f_bot, tracking=1.0, flip=True,
                 max_span_deg=150)
        d.polygon(star_pts(C, C + 5, 168), fill=255)
        dots(d, C, C, MED_DOTS_R, MED_DOTS_N, MED_DOT, phase=-90)
    else:
        # nombre grande al centro, datos en los arcos
        arc_text(m, C, C, R_BAND, "CALIDAD ARTESANAL", f_bot, tracking=1.0, max_span_deg=150)
        arc_text(m, C, C, R_BAND, "EST. 2026", f_bot, tracking=1.0, flip=True,
                 max_span_deg=120)
        f_center = fnt(fonts, "serif_bold", 138)
        txt_c = "TU MARCA"
        ancho = (sum(f_center.getlength(c) for c in txt_c) / SS
                 + 6.0 * (len(txt_c) - 1))                 # ancho en unidades finales
        text_centered(d, C, C - 34, txt_c, f_center, tracking=6)
        rl = ancho * 0.46                                  # semilargo del filete
        d.line([u(C - rl), u(C + 62), u(C + rl), u(C + 62)],
               fill=255, width=max(2, int(round(u(2.8)))))
        text_centered(d, C, C + 126, "· DESDE SIEMPRE ·",
                      fnt(fonts, "serif_bold", 44), tracking=8)

    for ang in (0, 180):                       # estrellitas separadoras del arco
        a = math.radians(ang)
        d.polygon(star_pts(C + R_BAND * math.cos(a), C + R_BAND * math.sin(a),
                           20, rot=ang + 90), fill=255)

    return m


def apply_distress(mask, seed=1957, wear=1.0):
    """Estampado a goma: la tinta se corta por zonas y queda polvillo fino."""
    rng = np.random.default_rng(seed)

    def noise(mean, sigma, blur):
        n = rng.normal(mean, sigma, (W, W)).clip(0, 255).astype(np.uint8)
        return Image.fromarray(n, "L").filter(ImageFilter.GaussianBlur(blur))

    # manchas: agujeros grandes y suaves que comen los bordes de los trazos
    holes_big = noise(234, 26, 4.0).point(lambda v: 0 if v < 209 else 255)
    # polvillo: micro-agujeros que dan el grano de la goma
    holes_fine = noise(240, 20, 0.7).point(lambda v: 0 if v < 210 else 255)
    # Unión de agujeros (min): el desgaste es donde falla CUALQUIERA de los dos.
    # (Con multiply casi nunca coincidían y el sello salía limpio.)
    holes = ImageChops.darker(holes_big, holes_fine)
    if wear < 1.0:
        holes = Image.blend(Image.new("L", (W, W), 255), holes, wear)

    out = ImageChops.multiply(mask, holes)
    # densidad de tinta despareja (impresión a mano)
    dens = noise(236, 12, 22).point(lambda v: int(228 + v * 27 / 255))
    return ImageChops.multiply(out, dens)


def build_seal(variant, ink, bg, fonts, distressed=True, seed=1957, wear=1.0):
    mask = build_mask(variant, fonts)
    if distressed:
        mask = apply_distress(mask, seed=seed, wear=wear)
    mask = mask.resize((BASE, BASE), Image.LANCZOS)

    layer = Image.new("RGBA", (BASE, BASE), INK[ink] + (0,))
    layer.putalpha(mask)
    if bg is None:
        return layer
    canvas = Image.new("RGB", (BASE, BASE), BG[bg])
    canvas.paste(layer, (0, 0), layer)
    return canvas


def stamp_covers(covers_dir, seal_png, out_dir, size=150, angle=-9, margin=16):
    """Aplica el sello (transparente) sobre cada portada y guarda los JPG finales."""
    os.makedirs(out_dir, exist_ok=True)
    seal = Image.open(seal_png).convert("RGBA")
    seal = seal.resize((size, size), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC,
                                                          expand=True)
    n = 0
    for name in ("hamburgueseria", "pizzeria", "minutas", "sushi", "cafeteria"):
        p = os.path.join(covers_dir, name + ".jpg")
        if not os.path.exists(p):
            continue
        base = Image.open(p).convert("RGBA")
        base.alpha_composite(seal, (base.width - seal.width - margin,
                                    base.height - seal.height - margin))
        base.convert("RGB").save(os.path.join(out_dir, name + ".jpg"),
                                 quality=90, subsampling=1, optimize=True)
        n += 1
    print(f"   ↳ {n} portadas con sello en {os.path.basename(out_dir)}/")


def demo(covers_dir, seal_png, out_path, size=150, angle=-9, margin=16):
    seal = Image.open(seal_png).convert("RGBA")
    seal = seal.resize((size, size), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC,
                                                           expand=True)
    tiles = []
    for name in ("hamburgueseria", "pizzeria", "minutas", "sushi", "cafeteria"):
        p = os.path.join(covers_dir, name + ".jpg")
        if not os.path.exists(p):
            continue
        base = Image.open(p).convert("RGBA")
        base.alpha_composite(seal, (base.width - seal.width - margin,
                                    base.height - seal.height - margin))
        tiles.append(base.convert("RGB"))
    if not tiles:
        print("· (sin portadas para el demo)")
        return
    sheet = Image.new("RGB", (tiles[0].width, sum(t.height for t in tiles) + 8 * (len(tiles) - 1)),
                      (15, 15, 15))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height + 8
    sheet.save(out_path, quality=92, subsampling=1)


def main():
    fonts = ensure_fonts()
    os.makedirs(WEB, exist_ok=True)

    # (variante, tinta, fondo). "clasico" = diseño principal -> sin sufijo de variante.
    for variant, ink, bg in [("clasico", "blanco", "negro"), ("clasico", "negro", "blanco"),
                             ("wordmark", "blanco", "negro"), ("wordmark", "negro", "blanco")]:
        stem = "sello" if variant == "clasico" else f"sello-{variant}"
        build_seal(variant, ink, bg, fonts).save(
            os.path.join(HERE, f"{stem}-{ink}-fondo-{bg}.png"))
        build_seal(variant, ink, bg, fonts).save(
            os.path.join(HERE, f"{stem}-{ink}-fondo-{bg}.jpg"), quality=95, subsampling=0)

        tr = build_seal(variant, ink, None, fonts)
        tr.save(os.path.join(HERE, f"{stem}-{ink}-transparente.png"))
        build_seal(variant, ink, None, fonts, distressed=False).save(
            os.path.join(HERE, f"{stem}-{ink}-transparente-limpio.png"))

        if variant == "clasico":
            for px in (512, 384, 256, 128):
                tr.resize((px, px), Image.LANCZOS).save(
                    os.path.join(WEB, f"sello-{ink}-{px}.png"))
        print(f"✓ {variant:8s} tinta {ink:6s} fondo {bg}")

    # Portadas con el sello ya estampado (entrega final lista para usar)
    assets = os.path.dirname(HERE)
    covers = os.path.join(assets, "portadas-573x253")
    stamp_covers(covers, os.path.join(WEB, "sello-blanco-512.png"),
                 os.path.join(assets, "portadas-con-sello-blanco"))
    stamp_covers(covers, os.path.join(WEB, "sello-negro-512.png"),
                 os.path.join(assets, "portadas-con-sello-negro"))

    demo(covers, os.path.join(WEB, "sello-blanco-512.png"),
         os.path.join(HERE, "demo-portadas-blanco.jpg"))
    demo(covers, os.path.join(WEB, "sello-negro-512.png"),
         os.path.join(HERE, "demo-portadas-negro.jpg"))
    print("✓ demos generados")


if __name__ == "__main__":
    main()
