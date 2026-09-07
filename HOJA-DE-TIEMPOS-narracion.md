# Hoja de tiempos — `deposito-bombal-narracion-3min.mp3`

**Duración exacta:** 3:00.0 · Mono · MP3 256 kbps / 44.1 kHz · Loudness −16 LUFS (TP −1.5 dB)
**Voz:** femenina, cálida, español neutro rioplatense (segunda opción de la audición) · solo narración, sin música (mezclar el piano al 30-40 %)

| Escena | Ventana | Entra | Sale | Frase |
|---|---|---|---|---|
| 1 — Gancho | 0:00–0:15 | 0:00.4 | 0:04.4 | ¿Cuántos pedidos se te enfriaron…? |
| | | 0:05.5 | 0:09.4 | ¿Cuántos clientes esperaron un WhatsApp…? |
| 2 — La vidriera | 0:15–0:55 | 0:15.0 | 0:26.8 | Esta es tu vidriera digital… |
| | | 0:30.0 | 0:35.7 | Y lo mismo, en el bolsillo de tu cliente… |
| | | 0:45.0 | 0:48.0 | Sin app, sin contraseñas: un link. |
| 3 — El presupuesto | 0:55–1:35 | 0:55.0 | 1:02.6 | Y acá está el corazón del negocio… |
| | | 1:10.0 | 1:13.6 | Cuando está listo, pide el presupuesto en un clic: |
| | | 1:25.0 | 1:32.0 | …el pedido te llega completo, con productos y cantidades… |
| 4 — Cada uno su puerta | 1:35–1:55 | 1:35.0 | 1:44.2 | Y cada uno tiene su puerta… |
| | | 1:45.0 | 1:47.8 | Nadie queda perdido en una bandeja genérica. |
| 5 — Panel admin | 1:55–2:30 | 1:55.0 | 2:01.9 | Del otro lado, mandás vos… |
| | | 2:05.0 | 2:08.7 | ¿Un producto sin stock? Lo apagás sin borrarlo. |
| | | 2:15.0 | 2:18.9 | ¿Cambió un precio? …queda publicado en el acto. |
| | *silencio dramático* | 2:18.9 → 2:28.0 | — | corte seco de música en 2:28, según guion |
| | | 2:28.0 | 2:29.7 | **Eso es control.** (más lento, 0.90×) |
| 6 — Números y cierre | 2:30–3:00 | 2:30.0 | 2:38.7 | Hoy, 517 productos viven en este catálogo… |
| | | 2:40.0 | 2:45.2 | Y todo esto es tuyo. La plataforma, los datos, el dominio. |
| | | 2:50.0 | 2:57.2 | Agendamos 15 minutos de llamada esta semana… |

Cada frase entra exactamente en el timecode de su subtítulo rotativo: los subtítulos del guion
se pueden quemar tal cual, sin reajustes. Ninguna frase invade la ventana de la escena siguiente.

## Control de acento (escena 6 regrabada)

La primera versión de la escena 6 salió con ceceo peninsular en los números (*diecisiete,
trescientos, quince*). Se regrabó con la misma voz escribiendo las cifras en dígitos, y se
verificó midiendo el centroide espectral de las fricativas sordas:

| Tramo | Centroide | Fricativas graves ([θ]) | |
|---|---|---|---|
| Escenas 1-5 (referencia) | 8479 Hz | 0 % | patrón rioplatense |
| Escena 6 — versión vieja | 6220-6944 Hz | 12-21 % | ceceo, descartada |
| Escena 6 — versión actual | 7922-8335 Hz | 0-3 % | coincide con la referencia |

Todo el tramo 0:00–2:29.8 se conservó del máster aprobado (no se regrabó).

Reconstrucción del mix: `build/split.py` (detección de frases por silencio) + `build/assemble.py`
(montaje en el timeline de 180 s), sobre los WAV de narración originales.
