import wave, array, subprocess, imageio_ffmpeg, os
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 24000
TOTAL = 180.0

def load(f):
    w = wave.open(f, 'rb'); a = array.array('h'); a.frombytes(w.readframes(w.getnframes())); return a

def cut(a, t0, t1):
    s = a[int(t0*SR):int(t1*SR)]
    n = int(0.006*SR)                      # micro fades anti-click
    for i in range(min(n, len(s))):
        s[i] = int(s[i]*i/n); s[-1-i] = int(s[-1-i]*i/n)
    return s

# (archivo, inicio, fin, cue en el timeline)  -- cues = timecodes del guion
PLAN = [
    ('s1.wav',  0.00,  9.07,   0.40),   # ESC1 0:00
    ('s2.wav',  0.00,  9.45,  15.00),   # ESC2 0:15
    ('s2.wav',  9.45, 13.60,  30.00),   #      0:30
    ('s2.wav', 13.60, 16.05,  45.00),   #      0:45
    ('s3.wav',  0.00,  6.10,  55.00),   # ESC3 0:55
    ('s3.wav',  6.10,  9.00,  70.00),   #      1:10
    ('s3.wav',  9.00, 16.65,  85.00),   #      1:25
    ('s4.wav',  0.00,  8.70,  95.00),   # ESC4 1:35
    ('s4.wav',  8.70, 11.85, 105.00),   #      1:45
    ('s5.wav',  0.00,  5.90, 115.00),   # ESC5 1:55
    ('s5.wav',  5.90,  8.78, 125.00),   #      2:05
    ('s5.wav',  8.78, 11.99, 135.00),   #      2:15
    ('s5b_slow.wav', 0.00, 99.0, 148.00), # pausa dramatica -> 2:28 "Eso es control."
    ('s6.wav',  0.55,  8.45, 150.00),   # ESC6 2:30
    ('s6.wav',  8.45, 12.88, 160.00),   #      2:40
    ('s6.wav', 12.88, 19.43, 170.00),   #      2:50
]

# "Eso es control." mas lento (nota de produccion: narracion mas lenta)
subprocess.run([FF, '-y', '-loglevel', 'error', '-i', 's5b.wav',
                '-filter:a', 'atempo=0.82', '-ar', str(SR), '-ac', '1', 's5b_slow.wav'], check=True)

buf = array.array('h', bytes(int(TOTAL*SR)*2))
cache = {}
report = []
for f, t0, t1, cue in PLAN:
    if f not in cache: cache[f] = load(f)
    a = cache[f]
    t1 = min(t1, len(a)/SR)
    seg = cut(a, t0, t1)
    off = int(cue*SR)
    for i, v in enumerate(seg):
        j = off+i
        if j < len(buf):
            m = buf[j]+v
            buf[j] = max(-32768, min(32767, m))
    report.append((cue, cue+len(seg)/SR, f))

peak = max(abs(x) for x in buf) or 1
g = int(32767*0.89)/peak
if g < 1.0:
    for i in range(len(buf)): buf[i] = int(buf[i]*g)

w = wave.open('mix.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(buf.tobytes()); w.close()

out = '/home/user/arena.ai/deposito-bombal-narracion-3min.mp3'
subprocess.run([FF, '-y', '-loglevel', 'error', '-i', 'mix.wav',
                '-af', 'highpass=f=80,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180,loudnorm=I=-16:TP=-1.5:LRA=11',
                '-codec:a', 'libmp3lame', '-b:a', '192k', '-ar', '44100', '-ac', '1',
                '-metadata', 'title=Depósito Bombal — Demo (narración)',
                '-metadata', 'artist=Narración IA', out], check=True)

def tc(t): return '%d:%05.2f' % (int(t//60), t % 60)
for a_, b_, f in report: print('%8s -> %8s  %s' % (tc(a_), tc(b_), f))
print('OK', out, os.path.getsize(out))
