import wave, array, math, json
SR=24000
def load(f):
    w=wave.open(f,'rb'); a=array.array('h'); a.frombytes(w.readframes(w.getnframes())); return a
def silences(a, minlen=0.14, rel=0.02):
    fl=int(0.01*SR); env=[]
    for i in range(0,len(a)-fl,fl):
        s=a[i:i+fl]; env.append(math.sqrt(sum(x*x for x in s)/fl))
    peak=max(env); th=peak*rel; runs=[]; st=None
    for i,e in enumerate(env):
        if e<th:
            if st is None: st=i
        else:
            if st is not None: runs.append((st*0.01,i*0.01)); st=None
    if st is not None: runs.append((st*0.01,len(env)*0.01))
    return [r for r in runs if r[1]-r[0]>=minlen], len(a)/SR

SENT={
 's1':["¿Cuántos pedidos se te enfriaron porque el precio estaba en un cuaderno?","¿Cuántos clientes esperaron un WhatsApp con la lista que nunca llegó?"],
 's2':["Esta es tu vidriera digital: los destacados del mes, el catálogo completo filtrado por rubro y categoría, búsqueda por descripción, y los productos más pedidos.","Y lo mismo, en el bolsillo de tu cliente: abre, consulta, recorre.","Sin app, sin contraseñas: un link."],
 's3':["Y acá está el corazón del negocio: tu cliente aprieta presupuestar en cada producto y arma su propia lista.","Cuando está listo, pide el presupuesto en un clic:","el pedido te llega completo, con productos y cantidades, sin teléfono descompuesto y sin notas mal leídas."],
 's4':["Y cada uno tiene su puerta: productores y fabricantes, su propio canal para sumarse como aliados; tus clientes de siempre, el suyo para consultas.","Nadie queda perdido en una bandeja genérica."],
 's5':["Del otro lado, mandás vos: creás, editás y ordenás productos por categorías y rubros.","¿Un producto sin stock? Lo apagás sin borrarlo.","¿Cambió un precio? Lo editás y queda publicado en el acto."],
 's6':["Hoy, quinientos diecisiete productos viven en este catálogo, trabajando las veinticuatro horas, los trescientos sesenta y cinco días del año.","Y todo esto es tuyo: la plataforma, los datos, el dominio.","Agendamos quince minutos de llamada esta semana: te respondo todas las dudas, y si te gusta, lo ponemos en marcha."],
}
out={}
for f,sents in SENT.items():
    a=load(f+'.wav'); sil,dur=silences(a)
    lead = sil[0][1] if sil and sil[0][0]<0.05 else 0.0
    tail = sil[-1][0] if sil and sil[-1][1]>dur-0.05 else dur
    speech = tail-lead
    tot=sum(len(s) for s in sents); acc=0; targets=[]
    for s in sents[:-1]:
        acc+=len(s); targets.append(lead+speech*acc/tot)
    cand=[s for s in sil if s[0]>lead+0.2 and s[1]<tail-0.2]
    picks=[]
    for t in targets:
        # mejor silencio: cerca del objetivo y largo
        best=min(cand, key=lambda s: abs((s[0]+s[1])/2-t) - 3.0*(s[1]-s[0]))
        picks.append(round((best[0]+best[1])/2,2)); cand=[c for c in cand if c[0]>best[1]]
    out[f]={'dur':round(dur,2),'lead':round(lead,2),'tail':round(tail,2),'splits':picks,
            'targets':[round(t,2) for t in targets],
            'sil':[(round(s[0],2),round(s[1],2)) for s in sil]}
    print(f, out[f]['dur'], 'lead',out[f]['lead'],'tail',out[f]['tail'],'splits',picks,'esperados',out[f]['targets'])
    b=[lead]+picks+[tail]
    print('    chunks:', [round(b[i+1]-b[i],2) for i in range(len(b)-1)])
json.dump(out, open('splits.json','w'))
a=load('s5b.wav'); print('s5b', round(len(a)/SR,2))
