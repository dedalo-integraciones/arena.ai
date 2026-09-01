#!/usr/bin/env python3
"""Animación sobre flyer.jpg (sin rediseño):
  1) Mecha de la bomba (arriba a la derecha) encendida: llama parpadeante +
     resplandor + chispas en el chisporroteo (~760,512).
  2) Hombre-árbol: la figura intenta salir del suelo muy lento y con dificultad
     (ascenso diminuto con temblor, pujos y micro-repliegues).
Todo lo demás queda píxel-idéntico al original.
Salida: 404x720 (720 de alto, proporción original), 30 fps, 900 frames = 30.00 s.
"""
import sys
import numpy as np
from PIL import Image

SRC = "/home/user/arena.ai/flyer.jpg"
OUT = "/home/user/arena.ai/flyer_animado_30s.mp4"
FPS = 30
DUR = 30.0
N = int(FPS * DUR)          # 900 frames exactos
OUT_W, OUT_H = 404, 720

# ---- región del hombre-árbol (coords originales 899x1599) ----
RX0, RX1 = 0, 448
RY0, RY1 = 676, 1240
FE = 16.0                   # ancho de feather

# ---- centro del chisporroteo de la mecha ----
FX, FY = 760.0, 512.0
FR = 64                     # radio del parche de llama (deja volar chispas)

def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)

def right_boundary(y):
    r = np.where(y <= 1000.0, 448.0,
                 np.where(y >= 1040.0, 415.0,
                          448.0 + (415.0 - 448.0) * (y - 1000.0) / 40.0))
    return r

def build_weight():
    ys = np.arange(RY0, RY1, dtype=np.float32)
    xs = np.arange(RX0, RX1, dtype=np.float32)
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    wt = smooth((Y - RY0) / FE)
    wb = smooth((RY1 - Y) / FE)
    rb = right_boundary(Y)
    wr = smooth((rb - X) / FE)
    W = (wt * wb * wr).astype(np.float32)
    return W, ys, xs

# ---- curva de ascenso "con dificultad" (px originales) ----
def dy_dx(t):
    s = (t / DUR) ** 1.8                      # rampa lenta general
    A = 18.0
    trem = 1.1 * np.sin(2*np.pi*1.35*t + 1.3*np.sin(2*np.pi*0.21*t)) * (0.25 + 0.75*s)
    def bump(t, c, w):                        # pujo que sube y vuelve
        x = (t - c) / w
        return np.exp(-x*x)
    slips = -2.4*bump(t, 11.0, 1.6) - 1.8*bump(t, 21.0, 1.4)   # micro-repliegues
    lurch = 1.3*bump(t, 6.0, 1.1) + 1.5*bump(t, 16.0, 1.2) + 1.2*bump(t, 25.5, 1.3)
    dy = A*s + trem + slips + lurch
    dy = max(dy, 0.0)
    dx = 0.6 * np.sin(2*np.pi*0.55*t) * s
    return dy, dx

# ---- ruido suave determinista para la llama ----
def n1(t): return (np.sin(2*np.pi*7.3*t) + np.sin(2*np.pi*11.7*t+1.7) + np.sin(2*np.pi*3.1*t+0.5))/3
def n2(t): return (np.sin(2*np.pi*9.1*t+0.9) + np.sin(2*np.pi*5.3*t+2.1))/2

# ---- chispas deterministas ----
rng = np.random.RandomState(7)
NSP = 12
sp_period = rng.uniform(0.5, 0.95, NSP)
sp_phase  = rng.uniform(0, 1, NSP)
sp_ang    = rng.uniform(-0.15*np.pi, 1.15*np.pi, NSP)   # sesgo hacia arriba
sp_speed  = rng.uniform(30, 70, NSP)
sp_size   = rng.uniform(1.8, 3.2, NSP)

def flame_patch(t):
    """Devolve parche aditivo (FR*2+1)^2 x3 float32 centrado en (FX,FY)."""
    R = FR
    yy, xx = np.mgrid[-R:R+1, -R:R+1].astype(np.float32)
    patch = np.zeros((2*R+1, 2*R+1, 3), np.float32)

    # resplandor cálido parpadeante
    Rg = 33.0 + 5.0*n1(t)
    Ig = 0.42 + 0.16*n2(t)
    glow = np.exp(-(xx*xx + yy*yy) / (Rg*Rg)) * Ig
    patch[:, :, 0] += glow * 255*1.00
    patch[:, :, 1] += glow * 255*0.55
    patch[:, :, 2] += glow * 255*0.16

    # cuerpo de llama (lágrima que tremola hacia arriba)
    cx = 2.4*n1(t+0.13)
    cy = -3.5 - 2.2*abs(n2(t+0.07))
    rf = 12.5 + 2.8*n2(t+0.21)
    ex, ey = 0.8*rf, 1.5*rf
    fl = np.exp(-(((xx-cx)/ex)**2 + ((yy-cy)/ey)**2))
    # núcleo blanco-amarillo + halo naranja
    core = fl**2.0
    patch[:, :, 0] += fl*255*0.95 + core*255*0.20
    patch[:, :, 1] += fl*255*0.50 + core*255*0.50
    patch[:, :, 2] += fl*255*0.08 + core*255*0.60

    # chispas
    for i in range(NSP):
        age = (t + sp_phase[i]*sp_period[i]) % sp_period[i]
        k = age / sp_period[i]
        d = sp_speed[i]*age
        px = FX + np.cos(sp_ang[i])*d - FX
        py = FY - np.sin(sp_ang[i])*d + 0.5*55*age*age - FY   # gravedad leve
        a = (1.0 - k)
        s = sp_size[i]*(1.0 - 0.5*k)
        g = np.exp(-(((xx-px)**2 + (yy-py)**2) / (s*s*2))) * a
        patch[:, :, 0] += g*255*1.0
        patch[:, :, 1] += g*255*0.72
        patch[:, :, 2] += g*255*0.25
    return patch

def main(preview=False):
    base = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
    H, W3, _ = base.shape
    Wmap, ys, xs = build_weight()
    patch = None  # la llama cambia por frame

    if preview:
        import imageio
        ts = [0.0, 4.0, 9.0, 14.0, 20.0, 26.0, 29.9]
        writer = None
        out_frames = []
    else:
        import imageio
        writer = imageio.get_writer(
            OUT, fps=FPS, codec="libx264", macro_block_size=1,
            output_params=["-pix_fmt", "yuv420p", "-crf", "18"])

    for f in range(N):
        t = f / FPS
        if preview and not any(abs(t-v) < 0.5/FPS for v in ts):
            continue
        dy, dx = dy_dx(t)
        frame = base.copy()

        # --- warp de la figura (contenido sube dy, se sacude dx) ---
        i0 = np.floor(ys + dy).astype(int)
        fy = (ys + dy) - i0
        i0c = np.clip(i0, 0, H-1)
        i1c = np.clip(i0+1, 0, H-1)
        j0 = np.floor(xs + dx).astype(int)
        fx = (xs + dx) - j0
        j0c = np.clip(j0, 0, W3-1)
        j1c = np.clip(j0+1, 0, W3-1)
        fy2 = fy[:, None, None]
        fx2 = fx[None, :, None]
        top = base[np.ix_(i0c, j0c)]*(1-fx2) + base[np.ix_(i0c, j1c)]*fx2
        bot = base[np.ix_(i1c, j0c)]*(1-fx2) + base[np.ix_(i1c, j1c)]*fx2
        shifted = top*(1-fy2) + bot*fy2
        Wm = Wmap[:, :, None]
        frame[RY0:RY1, RX0:RX1] = (shifted*Wm + frame[RY0:RY1, RX0:RX1]*(1-Wm))

        # --- llama de la mecha (aditiva) ---
        p = flame_patch(t)
        R = FR
        y0, y1 = int(FY)-R, int(FY)+R+1
        x0, x1 = int(FX)-R, int(FX)+R+1
        sub = frame[y0:y1, x0:x1]
        frame[y0:y1, x0:x1] = np.clip(sub + p, 0, 255)

        img = Image.fromarray(frame.astype(np.uint8)).resize(
            (OUT_W, OUT_H), Image.LANCZOS)
        arr = np.asarray(img)
        if preview:
            if t in ts or any(abs(t-v) < 0.5/FPS for v in ts):
                out_frames.append((t, arr))
        else:
            writer.append_data(arr)

    if preview:
        for t, arr in out_frames:
            Image.fromarray(arr).save(f"/home/user/crops/prev_{t:05.1f}.png")
            print("preview t=", t)
    else:
        writer.close()
        print("done", OUT)

if __name__ == "__main__":
    main(preview=(len(sys.argv) > 1 and sys.argv[1] == "preview"))
