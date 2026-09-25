#!/bin/bash
#
# resize-500x450.sh
#
# Normaliza TODAS las imágenes .webp de la raíz del repo al tamaño exacto 500x450 px.
#
# Criterio:
#   1. Cada foto original es más ancha que la proporción 500:450 (5:4), por lo que
#      se recorta horizontalmente (nunca se deforma la imagen).
#   2. El desplazamiento horizontal del recorte (crop offset) se elige por imagen
#      según el sujeto principal, para no cortar el objeto/escena protagonista.
#   3. El recorte se reescala con filtro Lanczos a 500x450 exactos y se exporta
#      como WebP calidad 90, sin metadatos.
#
# Uso:  ./tools/resize-500x450.sh          (desde la raíz del repo)
#
# Requiere ImageMagick (convert/identify) y python3.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OUT_W=500
OUT_H=450
QUALITY=90

# Desplazamiento horizontal (px, sobre la imagen original) usado en cada foto.
# Los valores ya aplicados al set actual; si se reemplaza una foto, ajustar acá.
declare -A OFFSET=(
  # 1280x853 — 948 px de ancho de recorte
  [imgi_72_482226570_1245190180948958_4344029155388316551_n.webp]=140  # candelabro + sillas
  [imgi_72_482322863_1245189910948985_1957544056256773770_n.webp]=120  # carpa + alfombra roja
  [imgi_72_485299763_1255468446587798_2043865217343943293_n.webp]=120  # carpa + alfombra roja (dup)
  [imgi_72_485392061_1255468676587775_4326801045886413163_n.webp]=90   # mesa azul + candelabro
  [imgi_72_486413669_1255468309921145_8167059189227475125_n.webp]=55   # pista + mesa de dulces
  # 2048x1536 — 1707 px de ancho de recorte
  [imgi_72_484807778_9745365508815616_1517166788324366596_n.webp]=205  # buffet
  [imgi_72_485168292_9770885546263612_6908381330259453297_n.webp]=140  # salón violeta
  [imgi_72_485810420_9770885219596978_9217650192056871377_n.webp]=110  # candelabro azul
  # 2048x996 — 1107 px de ancho de recorte
  [imgi_72_488203908_1267967455337897_8583685222877607375_n.webp]=170  # pista + candy bar
  [imgi_72_488454696_1267967425337900_2057746017296472634_n.webp]=136  # mesa de dulces + torta
  [imgi_72_488790206_1267967068671269_5229811096366714189_n.webp]=170  # grupo + staff
)

for f in *.webp; do
  [ -e "$f" ] || continue
  W=$(identify -format "%w" "$f"); H=$(identify -format "%h" "$f")
  CW=$(python3 -c "print(int(round($H*$OUT_W/$OUT_H)))")   # ancho de recorte 5:4
  if [ "$CW" -le "$W" ]; then SPAN=$((W-CW)); else SPAN=0; CW=$W; fi
  X=${OFFSET[$f]:-$((SPAN/2))}
  [ "$X" -gt "$SPAN" ] && X=$SPAN

  tmp="$(mktemp --suffix=.webp)"
  convert "$f" -crop "${CW}x${H}+${X}+0" +repage \
      -filter Lanczos -resize "${OUT_W}x${OUT_H}!" \
      -strip -quality "$QUALITY" -define webp:method=6 "$tmp"
  mv "$tmp" "$f"

  printf "%-72s %sx%s recorte %sx%s +%s  ->  %sx%s\n" \
    "$f" "$W" "$H" "$CW" "$H" "$X" \
    "$(identify -format '%w' "$f")" "$(identify -format '%h' "$f")"
done

echo "Listo: todas las imágenes quedaron en ${OUT_W}x${OUT_H} px."
