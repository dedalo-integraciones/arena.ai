import wave, numpy as np, subprocess, imageio_ffmpeg, os
FF=imageio_ffmpeg.get_ffmpeg_exe(); SR=24000; TOTAL=180.0
def load(p):
    w=wave.open(p,'rb'); return np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
def save(p,x):
    w=wave.open(p,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.clip(x,-1,1).astype(np.float32).__mul__(32767).astype(np.int16).tobytes()); w.close()
def voiced_rms(x):
    fl=int(0.025*SR); r=np.sqrt(np.array([ (x[i:i+fl]**2).mean() for i in range(0,len(x)-fl,fl)]))
    return np.median(r[r>np.percentile(r,60)])
def trim(x,rel=0.02):
    fl=int(0.01*SR); r=np.array([np.sqrt((x[i:i+fl]**2).mean()) for i in range(0,len(x)-fl,fl)])
    th=r.max()*rel; nz=np.where(r>th)[0]
    return x[max(0,int((nz[0]*0.01-0.05)*SR)):int((nz[-1]*0.01+0.12)*SR)]
def fx(x, tempo=None):                      # misma cadena que el resto del mix
    save('_i.wav',x)
    af='highpass=f=80,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180'
    if tempo: af=f'atempo={tempo},'+af
    subprocess.run([FF,'-y','-loglevel','error','-i','_i.wav','-af',af,'-ar',str(SR),'-ac','1','_o.wav'],check=True)
    return load('_o.wav')
def fade(x,n=int(0.008*SR)):
    x=x.copy(); r=np.linspace(0,1,n); x[:n]*=r; x[-n:]*=r[::-1]; return x

cur=load('current.wav')
REF=[(0.4,9.5),(15,26.8),(30,35.7),(45,48),(55,62.6),(70,73.6),(85,92),(95,104.2),(105,107.8),(115,121.9),(125,128.7),(135,138.9)]
target=voiced_rms(np.concatenate([cur[int(a*SR):int(b*SR)] for a,b in REF]))

out=cur.copy()
out[int(149.90*SR):]=0.0                    # borro solo la escena 6 defectuosa; 2:28 "Eso es control" queda intacto
NEW=[('t2_a.wav',150.0,1.04),('t4_b.wav',160.0,None),('t2_c.wav',170.0,None)]
rep=[]
for f,cue,tp in NEW:
    s=fx(trim(load(f)),tp)
    s=fade(s*(target/voiced_rms(s)))
    o=int(cue*SR); n=min(len(s),len(out)-o); out[o:o+n]+=s[:n]
    rep.append((cue,cue+n/SR,f))
pk=np.abs(out).max(); out*= min(1.0, 0.92/pk)
save('mix2.wav',out)
dst='/home/user/arena.ai/deposito-bombal-narracion-3min.mp3'
subprocess.run([FF,'-y','-loglevel','error','-i','mix2.wav','-codec:a','libmp3lame','-b:a','192k','-ar','44100','-ac','1',
 '-metadata','title=Depósito Bombal — Demo (narración)','-metadata','artist=Narración IA',dst],check=True)
tc=lambda t:'%d:%05.2f'%(int(t//60),t%60)
for a,b,f in rep: print('%8s -> %8s  %s'%(tc(a),tc(b),f))
for t in ['_i.wav','_o.wav']:
    if os.path.exists(t): os.remove(t)
