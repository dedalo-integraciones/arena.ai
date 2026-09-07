import numpy as np, wave, subprocess, imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe(); SR=44100; DUR=180.0
N=int(SR*DUR); L=np.zeros(N); R=np.zeros(N)
BPM=92.0; BEAT=60/BPM; BAR=4*BEAT
def hz(m): return 440.0*2**((m-69)/12)

def piano(f, dur, vel=1.0):
    n=int(SR*min(dur,6.0)); t=np.arange(n)/SR; y=np.zeros(n)
    for k in range(1,9):
        fk=f*k*(1+0.0004*k*k)
        if fk>16000: break
        tau=(1.9 if f<200 else 1.35)/(k**0.55)
        y+= (1.0/k**1.25)*np.exp(-t/tau)*np.sin(2*np.pi*fk*t+np.random.rand()*6.28)
    a=int(0.005*SR); y[:a]*=np.linspace(0,1,a)          # ataque
    nz=np.random.randn(int(0.012*SR))*np.exp(-np.arange(int(0.012*SR))/(0.002*SR))
    y[:len(nz)]+=nz*0.03
    r=int(0.03*SR); y[-r:]*=np.linspace(1,0,r)
    return y*vel*0.28

def kick(vel=1.0):
    n=int(0.30*SR); t=np.arange(n)/SR
    f=50+90*np.exp(-t/0.025)
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.10)
    return y*vel*0.5
def shaker(vel=1.0):
    n=int(0.07*SR); t=np.arange(n)/SR
    y=np.random.randn(n)*np.exp(-t/0.018)
    y=np.convolve(y,[1,-0.9],'same')                     # brillo
    return y*vel*0.10
def rim(vel=1.0):
    n=int(0.12*SR); t=np.arange(n)/SR
    y=(np.random.randn(n)*0.6+np.sin(2*np.pi*320*t))*np.exp(-t/0.03)
    return y*vel*0.12

def put(buf,y,t,pan=0.0):
    i=int(t*SR); m=min(len(y),len(buf[0])-i)
    if m<=0: return
    buf[0][i:i+m]+=y[:m]*np.sqrt((1-pan)/2+0.5); buf[1][i:i+m]+=y[:m]*np.sqrt((1+pan)/2+0.5)
B=[L,R]

# I - V - vi - IV  (Do mayor): progresion luminosa y estable
PROG=[dict(bass=36+12, top=[60,64,67,71]),   # C  maj7
      dict(bass=31+12, top=[59,62,67,71]),   # G
      dict(bass=33+12, top=[57,60,64,67]),   # Am7
      dict(bass=29+12, top=[57,60,65,69])]   # F  maj7
MEL=[[72,76,79,76],[74,79,curr:=78,74],[72,76,81,76],[72,77,81,77]]

nb=int(DUR/BAR)+1
CUT=148.0; BACK=150.0
for b in range(nb):
    t0=b*BAR
    if t0>=CUT and t0<BACK: continue
    ch=PROG[b%4]; sec = 0 if t0<15 else 1 if t0<55 else 2 if t0<95 else 3 if t0<CUT else 4
    if t0>=BACK: sec=4
    vol=[0.55,0.72,0.85,1.0,0.6][sec]
    # bajo
    put(B,piano(hz(ch['bass']),BAR*1.1,0.55*vol),t0,-0.15)
    if sec>=1: put(B,piano(hz(ch['bass']+7),BAR*0.9,0.30*vol),t0+2*BEAT,-0.2)
    # arpegio
    notes=ch['top']
    steps=[0,1,2,3] if sec==0 else [0,1,2,3,2,1,2,3]
    for j,s in enumerate(steps):
        st=t0+j*(BAR/len(steps))
        if st>=DUR or (CUT<=st<BACK): continue
        if st>=CUT and st<BACK: continue
        v=(0.42 if j%2==0 else 0.30)*vol
        put(B,piano(hz(notes[s]),BAR/len(steps)*3,v),st,0.12*np.sin(j))
    # melodia simple en secciones medias
    if 2<=sec<=3 and b%2==0:
        for j,m in enumerate(MEL[b%4]):
            st=t0+j*BEAT
            if st<DUR and not (CUT<=st<BACK): put(B,piano(hz(m),BEAT*2.2,0.22*vol),st,0.05)
    # percusion suave
    if sec>=2 and t0<CUT:
        for beat in range(4):
            st=t0+beat*BEAT
            if st>=CUT: break
            if beat in (0,2): put(B,kick(0.8 if beat==0 else 0.6),st)
            if sec>=3 and beat==2: put(B,rim(0.7),st)
            for h in (0,0.5):
                sh=st+h*BEAT
                if sh<CUT: put(B,shaker(0.9 if h==0 else 0.55),sh,0.25 if h else -0.25)

def comb(x,d,g):
    y=x.copy(); D=int(d*SR)
    for i in range(D,len(y),D):
        m=min(D,len(y)-i); y[i:i+m]+=g*y[i-D:i-D+m]
    return y
def reverb(x):
    w=sum(comb(x,d,g) for d,g in [(0.0297,0.78),(0.0371,0.75),(0.0411,0.72),(0.0437,0.70)])/4
    for d,g in [(0.005,0.7),(0.0017,0.7)]:
        D=int(d*SR); y=w.copy()
        for i in range(D,len(y),D):
            m=min(D,len(y)-i); y[i:i+m]+=-g*y[i-D:i-D+m]
        w=y
    return w
L=0.82*L+0.30*reverb(L); R=0.82*R+0.30*reverb(R)

def env_at(t): return np.interp(t,[0,2.5,14.5,15.5,CUT-0.05,CUT,BACK,BACK+2.0,176.0,180.0],
                                  [0,1.0,1.0,1.0,1.0,0.0,0.0,1.0,1.0,0.0])
t=np.arange(N)/SR; e=env_at(t)
L*=e; R*=e
st=np.stack([L,R]); st/=max(1e-9,np.abs(st).max()); st*=0.72
def save(p,x):
    w=wave.open(p,'wb'); w.setnchannels(x.shape[0]); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x.T,-1,1)*32767).astype('<i2').tobytes()); w.close()
save('build/bed.wav',st)
subprocess.run([FF,'-y','-loglevel','error','-i','build/bed.wav','-af','loudnorm=I=-20:TP=-3:LRA=11',
 '-codec:a','libmp3lame','-b:a','256k','-ar','44100',
 '-metadata','title=Depósito Bombal — cama musical reel','-metadata','artist=Música generada',
 'reel-musica-3min.mp3'],check=True)
print('ok  duracion %.2f s  pico %.2f'%(N/SR,np.abs(st).max()))
for a,b in [(0,15),(15,55),(55,95),(95,148),(148,150),(150,180)]:
    s=st[:,int(a*SR):int(b*SR)]; print('  %3d-%3ds  RMS %.4f'%(a,b,np.sqrt((s**2).mean())))
