import wave, array, subprocess, json, os, math, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 24000; TOTAL = 180.0
S = json.load(open('splits.json'))

def load(p):
    w = wave.open(p,'rb'); a = array.array('h'); a.frombytes(w.readframes(w.getnframes())); return a
def save(p, a):
    w = wave.open(p,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes()); w.close()
def tempo(a, r):
    save('_t.wav', a)
    subprocess.run([FF,'-y','-loglevel','error','-i','_t.wav','-filter:a',f'atempo={r}','-ar',str(SR),'-ac','1','_o.wav'],check=True)
    return load('_o.wav')
def trim(a, rel=0.02):
    fl=int(0.01*SR); env=[math.sqrt(sum(x*x for x in a[i:i+fl])/fl) for i in range(0,len(a)-fl,fl)]
    th=max(env)*rel; i=0; j=len(env)-1
    while i<j and env[i]<th: i+=1
    while j>i and env[j]<th: j-=1
    return a[max(0,int((i*0.01-0.05)*SR)):int((j*0.01+0.12)*SR)]
def fades(a, n=int(0.006*SR)):
    for i in range(min(n,len(a))):
        a[i]=int(a[i]*i/n); a[-1-i]=int(a[-1-i]*i/n)
    return a

# frases -> cue exacto del guion (timecodes de los subtitulos rotativos)
CUES = {'s1':[0.40, 5.50], 's2':[15,30,45], 's3':[55,70,85], 's4':[95,105],
        's5':[115,125,135], 's6':[150,160,170]}
SPEED = {('s4',0):1.06}          # ajuste imperceptible para no invadir el cue 1:45
plan = []
for f, cues in CUES.items():
    a = load(f+'.wav'); d = S[f]
    bounds = [d['lead']] + d['splits'] + [d['tail']]
    assert len(cues) == len(bounds)-1, (f, len(cues), len(bounds)-1)
    for k, cue in enumerate(cues):
        seg = array.array('h', a[int(bounds[k]*SR):int(bounds[k+1]*SR)])
        r = SPEED.get((f,k))
        if r: seg = tempo(seg, r)
        plan.append((cue, fades(seg), f'{f}[{k+1}]'))

esо = trim(load('s5b.wav'))                     # "Eso es control." mas lento, a las 2:28
eso = tempo(esо, 0.90)
if len(eso)/SR > 1.85: eso = tempo(esо, 1.0)
plan.append((148.0, fades(eso), 's5b "Eso es control."'))

buf = array.array('h', bytes(int(TOTAL*SR)*2))
for cue, seg, name in sorted(plan):
    off = int(cue*SR)
    for i, v in enumerate(seg):
        j = off+i
        if j < len(buf): buf[j] = max(-32768, min(32767, buf[j]+v))
peak = max(abs(x) for x in buf) or 1
g = int(32767*0.89)/peak
if g < 1.0:
    for i in range(len(buf)): buf[i] = int(buf[i]*g)
save('mix.wav', buf)

out = '/home/user/arena.ai/deposito-bombal-narracion-3min.mp3'
subprocess.run([FF,'-y','-loglevel','error','-i','mix.wav','-af',
 'highpass=f=80,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180,loudnorm=I=-16:TP=-1.5:LRA=11',
 '-codec:a','libmp3lame','-b:a','192k','-ar','44100','-ac','1',
 '-metadata','title=Depósito Bombal — Demo (narración)','-metadata','artist=Narración IA', out], check=True)

def tc(t): return '%d:%05.2f'%(int(t//60), t%60)
prev_end = 0; ok = True
for cue, seg, name in sorted(plan):
    end = cue+len(seg)/SR
    if cue < prev_end - 0.01: ok = False; name += '  <-- SOLAPADO'
    prev_end = end
    print('%8s -> %8s  %s' % (tc(cue), tc(end), name))
print('sin solapamientos:', ok)
for t in ['_t.wav','_o.wav']:
    if os.path.exists(t): os.remove(t)
