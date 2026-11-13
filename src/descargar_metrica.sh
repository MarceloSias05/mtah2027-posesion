#!/bin/bash
# baja los 3 partidos publicos de metrica (github.com/metrica-sports/sample-data)
# fijado a un commit exacto para que la entrega sea reproducible
# son los datos externos con los que calibramos y entrenamos todo. no se suben al repo
set -e
cd "$(dirname "$0")/.."
COMMIT=e706dd506b360d69d9d123d5b8026e7294b13996
mkdir -p data_externa
if [ ! -d data_externa/metrica/.git ]; then
  git clone https://github.com/metrica-sports/sample-data.git data_externa/metrica
fi
git -C data_externa/metrica checkout -q $COMMIT
echo "metrica sample data en data_externa/metrica @ $COMMIT"
