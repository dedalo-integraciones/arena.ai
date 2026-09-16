# Sello redondo antiguo — "TU MARCA"

Sello tipo goma estampada, generado **vectorialmente** (no con IA), así que todas las
letras están perfectas. Salida en blanco y en negro, con y sin fondo.

## Los dos pedidos

| Pedido | Archivo |
|---|---|
| Sello **blanco con fondo negro** | `sello-blanco-fondo-negro.png` · `.jpg` |
| Sello **negro con fondo blanco** | `sello-negro-fondo-blanco.png` · `.jpg` |

## Todo lo demás

| Archivo | Para qué sirve |
|---|---|
| `sello-blanco-transparente.png` / `sello-negro-transparente.png` | Superponer sobre las fotos (PNG con alfa) |
| `sello-{blanco,negro}-transparente-limpio.png` | Igual pero **sin desgaste**: bordes nítidos, look vectorial |
| `sello-wordmark-{blanco,negro}-fondo-{negro,blanco}.png/.jpg` | Variante con "TU MARCA" grande al centro |
| `web/sello-{blanco,negro}-{128,256,384,512}.png` | Tamaños listos para web |
| `../portadas-con-sello-blanco/` y `../portadas-con-sello-negro/` | Las 5 portadas de rubro **con el sello ya incrustado** (573×253) |
| `demo-portadas-blanco.jpg` / `demo-portadas-negro.jpg` | Muestra de las 5 portadas con sello, en una sola imagen |
| `sello-variantes.jpg` | Las 4 variantes juntas con rótulos |
| `preview.html` | Vista previa: sellos sueltos + superposición en vivo sobre las portadas |

## Uso recomendado en la web

Sobreponer el PNG transparente es más liviano que incrustar el sello en cada foto:
una sola imagen (36 KB) sirve para todas las tarjetas.

```html
<div class="rubro">
  <img class="rubro__foto" src="/assets/portadas/pizzeria.jpg"
       width="573" height="253" loading="lazy"
       alt="Pizzería — pizza napolitana al horno de barro">
  <img class="rubro__sello" src="/assets/sello/sello-blanco-512.png" alt="" aria-hidden="true">
</div>
```

```css
.rubro{ position:relative; border-radius:12px; overflow:hidden; }
.rubro__foto{ display:block; width:100%; height:auto; }
.rubro__sello{ position:absolute; right:14px; bottom:10px; width:27%; height:auto;
               transform:rotate(-9deg); opacity:.92; pointer-events:none; }
```

En las fotos oscuras conviene el sello **blanco**; en las muy claras, el **negro**.

## Regenerar / personalizar

```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install Pillow numpy
/tmp/venv/bin/python generar-sello.py
```

El script se provisiona solo las tipografías (las baja de PyPI vía `matplotlib`,
porque trae STIX, una serif clásica tipo Times) y deja todo en esta carpeta.

### Cambiar el texto o el rubro

Todo está en `build_mask()` y en las constantes de arriba del archivo:

- `variant="clasico"` → nombre arriba en arco, claim abajo, estrella al centro.
- `variant="wordmark"` → nombre grande al centro, datos en los arcos.
- `INK` / `BG` → colores de tinta y fondo.
- `F_TOP`, `F_BOTTOM`, `R_BAND` → cuerpos de fuente y radio del texto en arco.
- `arc_text(..., max_span_deg=)` → cuánto arco puede ocupar cada línea: si el texto
  es más largo, el script avisa con un error en vez de superponer las letras.
- `apply_distress(..., wear=)` → 1.0 = bien gastado; 0.0 = impecable.

## Detalle técnico

- Lienzo 1200×1200 dibujado al triple (**supersampling ×3**) y reducido con Lanczos:
  bordes con antialias fino.
- Cada carácter del arco se rotula sobre la tangente del círculo y se estampa girado,
  así que el texto curvo queda con espaciado parejo y siempre derecho.
- El desgaste combina manchas suaves (comen los bordes de los trazos) con polvillo
  fino (grano de goma) y una variación suave de densidad de tinta, para que no se
  vea un círculo perfecto hecho por computadora.
