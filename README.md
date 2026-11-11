# More than a Hack 2027 · Fase 1 posesion

Nuestro repo para el reto inicial del More than a Hack (Metrica Sports + FC Barcelona + MWCapital). El reto es decir frame por frame quien tiene el balon en el Barça vs Athletic (LaLiga 24-25, J2): `H` local, `A` visitante, `D` balon muerto, `X` no sabemos.

La base (games.py, evaluation/, starter/) viene del repo oficial de los organizadores, que es MIT. Lo nuestro esta en `src/`, `tools/` y `docs/bitacora/`. Los docs originales del reto los movimos a `docs/reto_original/` para no revolver.

## Como esta organizado

```
src/                  nuestro pipeline de posesion (en eso estamos)
tools/                cosas que se corren aparte, ej. detectar el balon en el video
docs/bitacora/        lo que fuimos haciendo y decidiendo, por fase
docs/reto_original/   README, reglas, evaluacion etc. de los organizadores
evaluation/ starter/  del repo oficial, sin cambios
data/                 aqui va la data del drive (NO se sube, esta en el gitignore)
outputs/ models/      resultados intermedios y pesos de modelos (tampoco se suben)
```

## Data

La data no esta aqui porque la licencia no deja redistribuirla. Hay que bajarla del drive que mandaron al inscribirse y descomprimirla en `data/` con los mismos nombres:

```
data/tactical/BAR-ATH_tactical.mp4
data/tactical/BAR-ATH_tactical_atd.xml
data/tactical/BAR-ATH_tactical_atd.txt
data/tactical/BAR-ATH_tactical_homography.csv
data/tactical/BAR-ATH_tactical_smart_tagging.xml
data/broadcast/...   (opcional)
```

Para checar que todo esta bien: `python starter/baseline.py` tiene que regenerar los 4 baselines identicos a los de `evaluation/results/`.

## Reglas que seguimos

Las que valen son las del correo de aclaracion (estan resumidas en `docs/bitacora/00_reglas.md`). Lo mas importante: nada se entrena ni se ajusta con el ground truth ni con el video del partido, todo parametro sale de datos externos, y no se compara el output contra el video.

## Requisitos

Python 3.9+. Para la evaluacion nomas numpy y pandas (`requirements.txt`). Para el detector de balon ver `tools/requirements-video.txt`.
