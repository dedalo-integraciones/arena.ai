#!/usr/bin/env python3
"""Animación sobre flyer.jpg (sin rediseño):
  1) Mecha de la bomba (arriba a la derecha) encendida: llama parpadeante +
     resplandor + chispas en el chisporroteo (~760,512).
  2) Hombre-árbol: intenta salir de la tierra con intensidad: asciende,
     tiembla, pierde pie, y DOBLA LAS RODILLAS (el torso se agacha y la
     rodilla delantera empuja hacia afuera) en pujos repetidos.
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
RX0, RX1 = 0, 452
RY0, RY1 = 676, 1262        # borde inferior en fondo puro (raices mueren ~1245)
FE = 16.0                   # ancho de feather

# ---- centro del chisporroteo de la mecha ----
FX, FY = 760.0, 512.0
FR = 64                     # radio del parche de llama (deja volar chispas)

def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)

def right_boundary(y):
    return np.where(y <= 1000.0, float(RX1),
                    np.where(y >= 1040.0, 415.0,
                             float(RX1) + (415.0 - RX1) * (y - 1000.0) / 40.0))

def build_weight():
    ys = np.arange(RY0, RY1, dtype=np.float32)
    xs = np.arange(RX0, RX1, dtype=np.float32)
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    wt = smooth((Y - RY0) / FE)
    wb = smooth((RY1 - Y) / FE)
    wr = smooth((right_boundary(Y) - X) / FE)
    W = (wt * wb * wr).astype(np.float32)
    return W, ys, xs, Y, X

# ---- keyframes de esfuerzo: (t, ascenso R, agache C) en px originales ----
KEYS = [
    (0.0,  0.0, 2.0),
    (3.0,  2.0, 6.0),
    (6.0,  8.0, 16.0),  # se agacha juntando fuerza
    (7.5,  13.0, 6.0),  # empuja: sube y estira rodillas
    (11.0, 9.0, 11.0),  # pierde pie, se repliega
    (14.0, 17.0, 16.0),
    (16.5, 25.0, 6.0),
    (20.0, 22.0, 14.0),
    (23.0, 32.0, 19.0),
    (26.0, 40.0, 8.0),
    (29.0, 54.0, 14.0),
    (30.0, 58.0, 11.0),
]
KT = np.array([k[0] for k in KEYS])
KR = np.array([k[1] for k in KEYS])
KC = np.array([k[2] for k in KEYS])

def effort(t):
    R = float(np.interp(t, KT, KR))
    C = float(np.interp(t, KT, KC))
    s = (t / DUR) ** 1.6
    R += 3.0*np.sin(2*np.pi*1.5*t + 1.3*np.sin(2*np.pi*0.23*t)) * (0.2+0.8*s)
    C += 1.5*np.sin(2*np.pi*1.1*t + 0.7) * (0.2+0.8*s)
    C = max(C, 0.0)
    L = 0.6 * C          # torso se inclina adelante
    K = 0.8 * C          # rodilla delantera empuja afuera
    return R, C, L, K

# ---- perfil vertical del agache (1 arriba de la rodilla, 0 abajo) ----
def pc_of(ys):
    return smooth((950.0 - ys) / 100.0)

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
    R = FR
    yy, xx = np.mgrid[-R:R+1, -R:R+1].astype(np.float32)
    patch = np.zeros((2*R+1, 2*R+1, 3), np.float32)

    Rg = 33.0 + 5.0*n1(t)
    Ig = 0.42 + 0.16*n2(t)
    glow = np.exp(-(xx*xx + yy*yy) / (Rg*Rg)) * Ig
    patch[:, :, 0] += glow * 255*1.00
    patch[:, :, 1] += glow * 255*0.55
    patch[:, :, 2] += glow * 255*0.16

    cx = 2.4*n1(t+0.13)
    cy = -3.5 - 2.2*abs(n2(t+0.07))
    rf = 12.5 + 2.8*n2(t+0.21)
    ex, ey = 0.8*rf, 1.5*rf
    fl = np.exp(-(((xx-cx)/ex)**2 + ((yy-cy)/ey)**2))
    core = fl**2.0
    patch[:, :, 0] += fl*255*0.95 + core*255*0.20
    patch[:, :, 1] += fl*255*0.50 + core*255*0.50
    patch[:, :, 2] += fl*255*0.08 + core*255*0.60

    for i in range(NSP):
        age = (t + sp_phase[i]*sp_period[i]) % sp_period[i]
        k = age / sp_period[i]
        d = sp_speed[i]*age
        px = np.cos(sp_ang[i])*d
        py = -np.sin(sp_ang[i])*d + 0.5*55*age*age
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
    Wmap, ys, xs, Y, X = build_weight()
    pc = pc_of(ys)[:, None]                                # (Ylen,1)
    gk = np.exp(-(((X-375.0)/45.0)**2 + ((Y-920.0)/40.0)**2))   # rodilla delantera

    if preview:
        ts = [0.0, 6.0, 7.5, 14.0, 23.0, 29.9]
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
        R, C, L, K = effort(t)
        frame = base.copy()

        # campo de desplazamiento: sube R; torso agacha C; rodilla empuja K
        SY = (R - C*pc[:, 0])[:, None]                     # (Ylen,1)
        DX = -(L*pc + K*gk)                                # (Ylen,Xlen)
        srcy = Y + SY
        srcx = X + DX
        srcy = np.maximum(srcy, 673.0)   # nunca arrastrar el texto superior
        i0 = np.floor(srcy).astype(int); fy = (srcy - i0)[:, :, None]
        j0 = np.floor(srcx).astype(int); fx = (srcx - j0)[:, :, None]
        i0c = np.clip(i0, 0, H-1); i1c = np.clip(i0+1, 0, H-1)
        j0c = np.clip(j0, 0, W3-1); j1c = np.clip(j0+1, 0, W3-1)
        shifted = (base[i0c, j0c]*(1-fx) + base[i0c, j1c]*fx)*(1-fy) + \
                  (base[i1c, j0c]*(1-fx) + base[i1c, j1c]*fx)*fy
        Wm = Wmap[:, :, None]
        frame[RY0:RY1, RX0:RX1] = shifted*Wm + frame[RY0:RY1, RX0:RX1]*(1-Wm)

        # llama de la mecha (aditiva)
        p = flame_patch(t)
        Rr = FR
        y0, y1 = int(FY)-Rr, int(FY)+Rr+1
        x0, x1 = int(FX)-Rr, int(FX)+Rr+1
        sub = frame[y0:y1, x0:x1]
        frame[y0:y1, x0:x1] = np.clip(sub + p, 0, 255)

        img = Image.fromarray(frame.astype(np.uint8)).resize(
            (OUT_W, OUT_H), Image.LANCZOS)
        arr = np.asarray(img)
        if preview:
            if any(abs(t-v) < 0.5/FPS for v in ts):
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
