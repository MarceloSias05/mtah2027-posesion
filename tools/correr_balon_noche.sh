#!/bin/bash
# corre el detector de balon sobre el video tactico, pensado para dejarlo en la noche
# uso:  bash tools/correr_balon_noche.sh
# si se corta (o lo paras con ctrl+c) se vuelve a correr igual y sigue donde iba
set -e
cd "$(dirname "$0")/.."

if [ ! -f data/tactical/BAR-ATH_tactical.mp4 ]; then
  echo "no esta el video en data/tactical/BAR-ATH_tactical.mp4"; exit 1
fi

# entorno de python aparte para no ensuciar el del sistema
if [ ! -d .venv ]; then
  echo "creando .venv..."
  python3 -m venv .venv
fi
source .venv/bin/activate
echo "instalando dependencias (la primera vez tarda unos minutos)..."
pip install -q --upgrade pip
pip install -q -r tools/requirements-video.txt

if [ ! -f models/football-ball-detection.pt ]; then
  python tools/ball_from_video.py --download-weights
fi

mkdir -p outputs
echo
echo "== prueba corta, 300 frames =="
python -u tools/ball_from_video.py --limit 300 2>&1 | tee outputs/prueba.log
echo
echo "== ahora si todo. NO cierres la terminal ni la tapa, deja la mac conectada =="
# caffeinate evita que la mac se duerma mientras corre python
caffeinate -dimsu python -u tools/ball_from_video.py 2>&1 | tee -a outputs/balon.log
echo "termino. el archivo es outputs/ball_video.csv"
