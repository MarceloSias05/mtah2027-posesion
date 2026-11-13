#!/bin/bash
# baja los 3 partidos publicos de metrica (github.com/metrica-sports/sample-data)
# son los datos externos con los que calibramos todo. no se suben al repo
cd "$(dirname "$0")/.."
mkdir -p data_externa
[ -d data_externa/metrica ] || git clone --depth 1 https://github.com/metrica-sports/sample-data.git data_externa/metrica
