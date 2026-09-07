import wave, numpy as np
SR=24000
def load(p):
    w=wave.open(p,'rb'); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    return a
def mel_fb(nfft=512,n=26,sr=SR,lo=50,hi=8000):
    m=lambda f:2595*np.log10(1+f/700); mi=lambda x:700*(10**(x/2595)-1)
    pts=mi(np.linspace(m(lo),m(hi),n+2)); bins=np.floor((nfft+1)*pts/sr).astype(int)
    fb=np.zeros((n,nfft//2+1))
    for i in range(1,n+1):
        l,c,r=bins[i-1],bins[i],bins[i+1]
        for k in range(l,c): fb[i-1,k]=(k-l)/max(1,c-l)
        for k in range(c,r): fb[i-1,k]=(r-k)/max(1,r-c)
    return fb
FB=mel_fb()
def mfcc(a):
    fl,hop=int(0.025*SR),int(0.010*SR); win=np.hamming(fl)
    if len(a)<fl: return np.zeros((0,13)), np.zeros(0)
    idx=np.arange(0,len(a)-fl,hop)
    fr=np.stack([a[i:i+fl]*win for i in idx])
    S=np.abs(np.fft.rfft(fr,512))**2
    E=np.log(S@FB.T+1e-10)
    from numpy.fft import rfft
    C=np.zeros((E.shape[0],13))
    N=E.shape[1]; k=np.arange(N)
    for j in range(13):
        C[:,j]=(E*np.cos(np.pi*j*(2*k+1)/(2*N))).sum(1)
    en=np.log((fr**2).mean(1)+1e-10)
    return C,en
def prof(a):
    C,en=mfcc(a)
    if len(C)==0: return None
    th=np.percentile(en,60)          # solo frames con voz
    V=C[en>th]
    return np.concatenate([V.mean(0),V.std(0)])
def seg(a,t0,t1): return a[int(t0*SR):int(t1*SR)]

cur=load('current.wav')
REF=[(0.4,9.5),(15,26.8),(30,35.7),(45,48),(55,62.6),(70,73.6),(85,92),(95,104.2),(105,107.8),
     (115,121.9),(125,128.7),(135,138.9)]
ref=np.concatenate([seg(cur,a,b) for a,b in REF])
P=prof(ref)
# escala por dimension para normalizar la distancia
sub=[prof(seg(cur,a,b)) for a,b in REF]
sc=np.std(np.stack(sub),0)+1e-6
d=lambda p: float(np.sqrt((((p-P)/sc)**2).mean()))
base=[d(s) for s in sub]
print('REFERENCIA (escenas 1-5, aprobadas): distancia media %.2f  max %.2f'%(np.mean(base),np.max(base)))
print('umbral de alerta: %.2f\n'%(np.mean(base)+2.2*np.std(base)))
TAIL=[('2:28 Eso es control',148,149.7),('2:30 s6-1',150,158.8),('2:40 s6-2',160,165),('2:50 s6-3',170,176.9)]
for n,a,b in TAIL: print('  MP3 actual  %-22s %.2f'%(n,d(prof(seg(cur,a,b)))))
print()
for n in ['t1_a','t1_b','t1_c','t2_a','t2_b','t2_c']:
    print('  toma nueva  %-22s %.2f'%(n,d(prof(load(n+'.wav')))))
np.save('refprof.npy',np.stack([P,sc]))
