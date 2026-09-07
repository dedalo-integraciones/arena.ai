import numpy as np, wave, subprocess, imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe(); SR=44100; DUR=180.0
N=int(SR*DUR); BUF=np.zeros((2,N))
BPM=115.0; BEAT=60/BPM; BAR=4*BEAT; CUT=148.0; BACK=150.0
hz=lambda m:440.0*2**((m-69)/12)
rng=np.random.default_rng(7)

def put(y,t,pan=0.0,g=1.0):
    i=int(t*SR); m=min(len(y),N-i)
    if m<=0 or i<0: return
    BUF[0,i:i+m]+=y[:m]*g*np.cos((pan+1)*np.pi/4); BUF[1,i:i+m]+=y[:m]*g*np.sin((pan+1)*np.pi/4)
def adsr(n,a,d,s,r):
    e=np.ones(n); a,d,r=int(a*SR),int(d*SR),int(r*SR)
    if a: e[:a]=np.linspace(0,1,a)
    if d: e[a:a+d]=np.linspace(1,s,d)
    e[a+d:]=s
    if r: e[-r:]*=np.linspace(1,0,r)
    return e
def lp(x,fc):                      # 1 polo, simple y rapido
    a=np.exp(-2*np.pi*fc/SR); y=np.zeros_like(x); c=0.0
    b=1-a
    for i in range(0,len(x),4096):
        blk=x[i:i+4096]
        for j,v in enumerate(blk):
            c=a*c+b*v; y[i+j]=c
    return y

def pluck(f,dur,vel=1.0,bright=1.0):      # pluck brillante (saw filtrado, decay corto)
    n=int(SR*dur); t=np.arange(n)/SR
    y=np.zeros(n)
    for k in range(1,14):
        if f*k>14000: break
        y+=np.sin(2*np.pi*f*k*t)*(1.0/k**0.85)*np.exp(-t*(2.1+k*0.16/bright))
    y*=adsr(n,0.004,0.02,0.85,0.05)
    return y*vel*0.30
def marimba(f,dur,vel=1.0):
    n=int(SR*dur); t=np.arange(n)/SR
    y=(np.sin(2*np.pi*f*t)*np.exp(-t*5.0)+0.45*np.sin(2*np.pi*f*4*t)*np.exp(-t*11.0)
       +0.34*np.sin(2*np.pi*f*9.4*t)*np.exp(-t*15.0))
    y[:int(0.003*SR)]*=np.linspace(0,1,int(0.003*SR))
    return y*vel*0.36
def bell(f,dur,vel=1.0):
    n=int(SR*dur); t=np.arange(n)/SR
    y=sum(np.sin(2*np.pi*f*r*t)*np.exp(-t*(2.0+i*1.4))/(1+i) for i,r in enumerate([1,2.01,3.02,4.9]))
    return y*vel*0.24
def bass(f,dur,vel=1.0):
    n=int(SR*dur); t=np.arange(n)/SR
    y=np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*2*f*t)+0.12*np.sin(2*np.pi*3*f*t)
    return y*adsr(n,0.006,0.05,0.8,0.06)*vel*0.20
def kick(v=1.0):
    n=int(0.26*SR); t=np.arange(n)/SR
    f=52+150*np.exp(-t/0.018)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.085)
    y[:120]+=rng.standard_normal(120)*0.25*np.exp(-np.arange(120)/40)
    return y*v*0.40
def clap(v=1.0):
    n=int(0.22*SR); t=np.arange(n)/SR; y=np.zeros(n)
    for d in (0,0.010,0.021):
        i=int(d*SR); seg=rng.standard_normal(n-i)*np.exp(-np.arange(n-i)/(0.012*SR))
        y[i:]+=seg
    y+=rng.standard_normal(n)*np.exp(-t/0.055)*0.5
    y=np.convolve(y,[1,-0.7,0.3],'same')
    return y*v*0.22
def hat(v=1.0,op=False):
    d=0.16 if op else 0.045; n=int(d*SR); t=np.arange(n)/SR
    y=rng.standard_normal(n)*np.exp(-t/(d/3.2))
    y=np.convolve(y,[1,-0.92],'same')
    return y*v*(0.17 if not op else 0.14)
def riser(dur=1.8,v=1.0):
    n=int(dur*SR); t=np.arange(n)/SR
    y=rng.standard_normal(n)*np.linspace(0.05,1,n)**2
    y=np.convolve(y,[1,-0.9],'same')
    return y*v*0.10

# RE mayor: I - IV - V - IV  (sin acordes menores: siempre luminoso)
CH=[dict(r=50,notes=[62,66,69,76],b=38),   # D add9
    dict(r=55,notes=[62,67,71,74],b=43),   # G add9
    dict(r=57,notes=[61,64,69,73],b=45),   # A add9
    dict(r=55,notes=[62,67,71,78],b=43)]   # G add9
PENTA=[74,76,78,81,83,86]
MOTIF=[[0,2,3,2],[1,3,4,3],[2,4,5,4],[1,2,3,4]]

nb=int(DUR/BAR)+2
for b in range(nb):
    t0=b*BAR
    if t0>=DUR: break
    if CUT<=t0<BACK: continue
    c=CH[b%4]
    sec = 0 if t0<6 else 1 if t0<55 else 2 if t0<95 else 3 if t0<CUT else 4
    if t0>=BACK: sec=4
    vol=[0.7,0.95,1.0,1.05,1.0][sec]
    beats=[t0+i*BEAT for i in range(4)]
    ok=lambda x: x<DUR and not (CUT<=x<BACK)
    # bajo con rebote de octava
    if sec>=1:
        for i,st in enumerate(beats):
            if ok(st): put(bass(hz(c['b']+(12 if i%2 else 0)),BEAT*0.9,0.95*vol),st,0.0)
    # plucks: patron de corcheas con sincopa alegre
    pat=[0,0.75,1.5,2,2.75,3.5] if sec>=1 else [0,1.5,2,3.5]
    for j,off in enumerate(pat):
        st=t0+off*BEAT
        if ok(st): put(pluck(hz(c['notes'][j%len(c['notes'])]),BEAT*1.1,(0.95 if j%2==0 else 0.7)*vol),st,0.35*np.sin(j*1.7))
    # marimba: contracanto en pentatonica
    if sec>=2:
        for j,d in enumerate(MOTIF[b%4]):
            st=t0+j*BEAT+BEAT*0.5
            if ok(st): put(marimba(hz(PENTA[d]),BEAT*1.4,0.85*vol),st,-0.3+0.2*j)
    # campana/lead en secciones altas
    if sec>=3 and b%2==0:
        for j,d in enumerate([2,4,5,4]):
            st=t0+j*BEAT
            if ok(st): put(bell(hz(PENTA[d]+12),BEAT*2.0,0.9*vol),st,0.1)
    # bateria
    if sec>=1:
        for i,st in enumerate(beats):
            if not ok(st): continue
            put(kick(1.0 if i%2==0 else 0.85),st)
            if i%2==1: put(clap(0.95*vol),st,0.05)
        for i in range(8):
            st=t0+i*BEAT/2
            if ok(st): put(hat(0.9 if i%2==0 else 0.55, op=(sec>=2 and i%4==3)),st,0.4 if i%2 else -0.4)
        if sec>=2:
            for i in range(16):
                st=t0+i*BEAT/4
                if ok(st) and i%4 in (1,3): put(hat(0.55),st,0.5 if i%2 else -0.5)
    # fills / risers antes de cada seccion nueva
    if abs(t0+BAR-55)<BAR/2 or abs(t0+BAR-95)<BAR/2 or abs(t0+BAR-BACK)<BAR/2:
        put(riser(1.8,1.0),max(0,t0+BAR-1.8),0.0)

# sidechain (pump): la musica respira con el bombo
t=np.arange(N)/SR
ph=np.mod(t,BEAT)/BEAT
pump=1-0.28*np.exp(-ph*7.5)
BUF*=pump
# delay corto para brillo + reverb chica
def delay(x,dt,fb,mix):
    D=int(dt*SR); y=x.copy()
    for i in range(D,len(y),D):
        m=min(D,len(y)-i); y[i:i+m]+=fb*y[i-D:i-D+m]
    return (1-mix)*x+mix*y
for ch in (0,1):
    BUF[ch]=delay(BUF[ch],BEAT/2*(1.0 if ch==0 else 1.02),0.24,0.16)
def comb(x,d,g):
    D=int(d*SR); y=x.copy()
    for i in range(D,len(y),D):
        m=min(D,len(y)-i); y[i:i+m]+=g*y[i-D:i-D+m]
    return y
rev=lambda x: sum(comb(x,d,g) for d,g in [(0.0231,0.62),(0.0277,0.60),(0.0313,0.58)])/3
BUF=0.90*BUF+0.16*np.stack([rev(BUF[0]),rev(BUF[1])])
# envolvente global: arranque directo (reel), corte 2:28, vuelta 2:30, salida limpia
env=np.interp(t,[0,0.8,CUT-0.03,CUT,BACK,BACK+0.6,177.5,180.0],[0,1,1,0,0,1,1,0])
BUF*=env
BUF=np.tanh(BUF*1.15)*0.93
BUF/=max(1e-9,np.abs(BUF).max()); BUF*=0.85
w=wave.open('build/bed2.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(BUF.T,-1,1)*32767).astype('<i2').tobytes()); w.close()
subprocess.run([FF,'-y','-loglevel','error','-i','build/bed2.wav','-af','highpass=f=55,equalizer=f=110:t=q:w=0.9:g=-3,equalizer=f=3200:t=q:w=1.2:g=4,treble=g=5:f=6000,loudnorm=I=-14:TP=-1.0:LRA=8',
 '-codec:a','libmp3lame','-b:a','256k','-ar','44100',
 '-metadata','title=Depósito Bombal — música reel (alegre)','-metadata','artist=Música generada',
 'reel-musica-alegre-3min.mp3'],check=True)
print('duracion %.2f s  pico %.2f'%(N/SR,np.abs(BUF).max()))
for a,b in [(0,6),(6,55),(55,95),(95,148),(148,150),(150,180)]:
    s=BUF[:,int(a*SR):int(b*SR)]; print('  %3d-%3ds RMS %.4f'%(a,b,np.sqrt((s**2).mean())))
