#!/bin/bash
# regenera la entrega desde cero: datos externos + modelo + archivo final + validacion
# requisitos: python 3.11+, git, y la data del reto en data/tactical/ (ver README)
# uso: bash reproducir.sh [nombre_equipo]
set -e
cd "$(dirname "$0")"
TEAM=${1:-submission}

for f in BAR-ATH_tactical_atd.xml BAR-ATH_tactical_atd.txt; do
  [ -f data/tactical/$f ] || { echo "falta data/tactical/$f (ver README, seccion Data)"; exit 1; }
done

if [ ! -d .venv-repro ]; then python3 -m venv .venv-repro; fi
source .venv-repro/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements-nuestro.txt

bash src/descargar_metrica.sh
python src/generar_v1.py
cp outputs/v1_segmentos.csv outputs/$TEAM.csv
python evaluation/validate_submission.py outputs/$TEAM.csv
echo
echo "md5 de la entrega:"
(md5sum outputs/$TEAM.csv 2>/dev/null || md5 outputs/$TEAM.csv)
