# More than a Hack 2027 · reto de posesion

Nuestro repo para el Initial Challenge del More than a Hack 2027 (Metrica Sports + FC Barcelona + MWCapital).

**El reto:** para cada uno de los 199,319 frames del video tactico del Barça vs Athletic (LaLiga 24-25, J2) decir `H` si la tiene el Barça, `A` si la tiene el Athletic, `D` si el balon esta muerto o `X` si no sabemos. Se califica con **spellF1**, que cuenta posesiones completas bien cortadas (inicio y fin), no frames sueltos. El baseline oficial saca 0.2433. Entrega 17 nov.

La base (`games.py`, `evaluation/`, `starter/`) es del repo oficial de los organizadores (MIT). Lo nuestro esta en `src/`, `tools/` y `docs/`.

## La idea en corto

1. **No podemos tunear con este partido** (reglas). Entonces armamos un banco de pruebas con los 3 partidos publicos de Metrica, con posesion sacada de sus eventos y calificado con el mismo scorer del reto. Todo numero del codigo se calibra ahi.
2. **El baseline parte posesiones de mas** porque cambia de dueño cada que un rival queda mas cerca del balon aunque sea un frame. Nuestra regla de histeresis solo cambia de dueño cuando el otro equipo de verdad controla el balon un rato.
3. **Modelo de segmentos:** un clasificador entrenado en metrica da la probabilidad de H/A/D por frame y un viterbi escoge la secuencia de posesiones mas creible cobrando cada cambio. Es la entrega actual (v1).
4. **El tracking pierde el balon en 41% de los frames**, sobretodo en balon muerto. Para los huecos corrimos un detector de balon sobre el video (modelo publico entrenado con otros partidos).

Explicacion completa con el por que de cada cosa: **[docs/COMO_FUNCIONA.md](docs/COMO_FUNCIONA.md)**. El dia a dia de lo que fuimos probando: [docs/bitacora/](docs/bitacora/).

## Resultados hasta ahora (banco de Metrica, spellF1)

| metodo | juego 1 | juego 2 | juego 3 | promedio |
|---|---|---|---|---|
| baseline oficial (ventana 50) | 0.402 | 0.390 | 0.357 | 0.383 |
| histeresis, fuera de muestra* | 0.620 | 0.558 | 0.590 | 0.589 |
| **segmentos + histeresis, fuera de muestra*** | 0.636 | 0.614 | 0.620 | **0.623** |

\* calibrada en los otros 2 partidos y probada en el que queda. Histeresis: r=1.0m, k=8, dgap=25 (bitacora 05). Segmentos: bitacora 06. No sabemos el numero en BAR-ATH, no hay leaderboard.

## Como correr todo

```bash
# 0. data del reto en data/ (ver abajo) y python 3.9+
pip install -r requirements.txt -r requirements-starter.txt -r requirements-nuestro.txt

# 1. bajar los partidos publicos de metrica (datos externos para calibrar)
bash src/descargar_metrica.sh

# 2. calibrar la regla en metrica (imprime la prueba cruzada y los mejores parametros)
cd src && python calibrar_histeresis.py && cd ..

# 3. ENTREGA ACTUAL (v1): entrena en metrica, elige costos, aplica a BAR-ATH (~3.5 min)
python src/generar_v1.py                       # -> outputs/v1_segmentos.csv
python evaluation/validate_submission.py outputs/v1_segmentos.csv

# (red de seguridad) v0, solo la regla de histeresis
python src/generar_v0.py                       # -> outputs/v0_histeresis.csv

# (opcional, ~15 h en una mac M) detector de balon sobre el video
bash tools/correr_balon_noche.sh               # -> outputs/ball_video.csv
```

## Estructura

```
src/          banco de metrica, regla de histeresis, generar la entrega
tools/        detector de balon sobre el video (se corre aparte, es pesado)
docs/         COMO_FUNCIONA.md, bitacora/ por fases, reto_original/ (docs de los organizadores)
evaluation/   scorer oficial, sin cambios
starter/      cargadores oficiales, sin cambios
data/         data del reto, NO se sube (licencia)
data_externa/ partidos de metrica, se bajan con el script, NO se suben
outputs/      entregas y archivos intermedios, NO se suben
models/       pesos del detector, NO se suben
```

## Data

No esta en el repo porque no se puede redistribuir. Se baja del drive del reto y va asi:

```
data/tactical/BAR-ATH_tactical.mp4
data/tactical/BAR-ATH_tactical_atd.xml
data/tactical/BAR-ATH_tactical_atd.txt
data/tactical/BAR-ATH_tactical_homography.csv
data/tactical/BAR-ATH_tactical_smart_tagging.xml
data/broadcast/...   (opcional)
```

Check rapido de que esta bien: `python starter/baseline.py` tiene que regenerar identicos los 4 baselines de `evaluation/results/`.

## Reglas que seguimos

Las del correo de aclaracion del 11 nov (resumen en [docs/bitacora/00_reglas.md](docs/bitacora/00_reglas.md)): nada se entrena ni se ajusta con el GT ni con el video del partido, todo parametro sale de datos externos, y no comparamos nuestro output contra el video. Los 5 min de GT publico solo para checar formato.
