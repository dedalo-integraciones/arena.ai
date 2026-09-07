import numpy as np, wave, subprocess, imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe(); SR=44100
subprocess.run([FF,'-y','-loglevel','error','-i','deposito-bombal-narracion-3min.mp3','-ar',str(SR),'-ac','2','build/voz.wav'],check=True)
subprocess.run([FF,'-y','-loglevel','error','-i','reel-musica-3min.mp3','-ar',str(SR),'-ac','2','build/cama.wav'],check=True)
def load(p):
    w=wave.open(p,'rb'); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    return a.reshape(-1,w.getnchannels()).T
v=load('build/voz.wav'); m=load('build/cama.wav')
n=min(v.shape[1],m.shape[1]); v=v[:,:n]; m=m[:,:n]
# ducking: la musica baja 6 dB cuando hay voz
env=np.abs(v).max(0); win=int(0.05*SR)
env=np.convolve(env,np.ones(win)/win,'same')
gate=(env>0.02).astype(np.float32)
atk=np.ones(int(0.12*SR))/int(0.12*SR); gate=np.convolve(gate,atk,'same').clip(0,1)
duck=1.0-0.5*gate                      # -6 dB bajo la voz
mix=v*0.98 + m*0.34*duck               # cama al 34 %
pk=np.abs(mix).max(); mix*=min(1.0,0.95/pk)
w=wave.open('build/reelmix.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix.T,-1,1)*32767).astype('<i2').tobytes()); w.close()
subprocess.run([FF,'-y','-loglevel','error','-i','build/reelmix.wav','-af','loudnorm=I=-16:TP=-1.5:LRA=11',
 '-codec:a','libmp3lame','-b:a','256k','-ar','44100',
 '-metadata','title=Depósito Bombal — reel (voz + música)','-metadata','artist=Narración IA','deposito-bombal-reel-mezcla-3min.mp3'],check=True)
def db(x): return 20*np.log10(np.sqrt((x**2).mean())+1e-12)
print('duracion %.2f s  pico %.3f'%(n/SR,np.abs(mix).max()))
print('voz  %.1f dB | cama con voz %.1f dB | cama sola %.1f dB'%(db(v[:,int(20*SR):int(26*SR)]),
      db((m*0.34*duck)[:,int(20*SR):int(26*SR)]), db((m*0.34*duck)[:,int(10*SR):int(14*SR)])))
