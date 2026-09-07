import wave, numpy as np
SR=24000
def load(p):
    w=wave.open(p,'rb'); return np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
def seg(a,t0,t1): return a[int(t0*SR):int(t1*SR)]
def fric_stats(a,label):
    fl,hop=int(0.025*SR),int(0.010*SR)
    if len(a)<fl: return None
    win=np.hamming(fl); idx=np.arange(0,len(a)-fl,hop)
    fr=np.stack([a[i:i+fl]*win for i in idx])
    S=np.abs(np.fft.rfft(fr,1024)); f=np.fft.rfftfreq(1024,1/SR)
    P=S**2; tot=P.sum(1)+1e-12
    cen=(P*f).sum(1)/tot
    hf=P[:,(f>=5000)].sum(1)/tot                 # energia >5 kHz
    lf=P[:,(f<1000)].sum(1)/tot
    rms=np.sqrt((fr**2).mean(1))
    zc=(np.diff(np.sign(fr),axis=1)!=0).mean(1)
    loud=rms>np.percentile(rms,45)
    # fricativa sorda: mucha energia alta, poca baja, alto cruce por cero
    m=loud&(hf>0.25)&(lf<0.25)&(zc>0.25)
    if m.sum()<6: return None
    c=cen[m]; h=hf[m]
    return dict(label=label,n=int(m.sum()),cen_med=float(np.median(c)),cen_p20=float(np.percentile(c,20)),
                hf_med=float(np.median(h)), pct_bajo=float((c<5200).mean()))
def show(d):
    if d is None: print('   (sin datos)'); return
    print('   %-26s n=%3d  centroide med=%5.0f Hz  p20=%5.0f Hz  HF>5k=%.2f  %%fric.graves=%.0f%%'
          %(d['label'],d['n'],d['cen_med'],d['cen_p20'],d['hf_med'],100*d['pct_bajo']))
cur=load('current.wav')
REF=[(0.4,9.5),(15,26.8),(30,35.7),(45,48),(55,62.6),(70,73.6),(85,92),(95,104.2),(105,107.8),(115,121.9),(125,128.7),(135,138.9)]
print('REFERENCIA aprobada (escenas 1-5):'); show(fric_stats(np.concatenate([seg(cur,a,b) for a,b in REF]),'escenas 1-5'))
print('\nTRAMO FINAL del MP3 actual:')
for n,a,b in [('2:28 Eso es control',148,149.8),('2:30 517 productos / 24 h / 365 dias',150,158.9),
              ('2:40 todo esto es tuyo',160,165.1),('2:50 quince minutos...',170,177)]:
    show(fric_stats(seg(cur,a,b),n))
print('\nTOMAS NUEVAS (voice-02):')
for n in ['t1_a','t1_b','t1_c','t2_a','t2_b','t2_c']: show(fric_stats(load(n+'.wav'),n))
