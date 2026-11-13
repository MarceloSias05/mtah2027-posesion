# Fase 6 - modelo de segmentos (13 nov)

La histeresis decide frame a frame con reglas fijas. La idea aqui es que un modelo aprenda que tan probable es H, A o D en cada frame y luego algo que vea **todo el partido de jalon** escoja la secuencia de posesiones mas creible.

## como funciona (`src/segmentos.py`)

**1. señales por frame** (todas existen igual en metrica y en BAR-ATH):
- si falta el balon y que tan largo es el hueco donde esta
- distancia del jugador mas cercano de cada equipo al balon
- velocidad del balon, si el balon esta fuera de la cancha, velocidad promedio de los jugadores
- promedios de todo eso en ventanas de medio, 1 y 3 segundos alrededor (quien estuvo cerca, cuanto falto el balon, etc)
- la salida de la regla de histeresis (H/A/D) como 3 columnas mas

**2. clasificador:** HistGradientBoosting de sklearn, entrenado SOLO con los 3 partidos de metrica. Le duplicamos los datos volteando local y visitante (y la etiqueta) para que no aprenda cosas como "el local la tiene mas", que no aplica a otro partido.

**3. viterbi:** con las probabilidades de cada frame busca la secuencia H/A/D que mas sentido tiene, pero cada cambio H↔A cuesta y cada entrada/salida de D cuesta. Eso evita partir posesiones por un frame raro, que es justo lo que castiga el spellF1.

## resultados (fuera de muestra, cada partido predicho por un modelo que no lo vio)

| | juego 1 | juego 2 | juego 3 | promedio |
|---|---|---|---|---|
| baseline | 0.402 | 0.390 | 0.357 | 0.383 |
| histeresis | 0.620 | 0.558 | 0.590 | 0.589 |
| segmentos sin histeresis como señal | 0.556 | 0.585 | 0.565 | 0.569 |
| **segmentos + histeresis** | **0.636** | **0.614** | **0.620** | **0.623** |

Sin la histeresis como señal salio PEOR que la histeresis sola (0.569). Juntaba posesiones de mas (predecia ~280 cuando habia ~330). Con la histeresis adentro y costos mas bajos ya le gana. Sin el viterbi, el puro clasificador frame a frame saca ~0.3, osea el viterbi es lo que hace todo el trabajo.

Costos elegidos con prueba cruzada en metrica: cambio H↔A = 8, entrar/salir de D = 20.

## v1

`python src/generar_v1.py` hace todo (cargar metrica, elegir costos, entrenar, aplicar a BAR-ATH) en ~3.5 min → `outputs/v1_segmentos.csv`. Pasa el validador: 464 posesiones de ~9 s.

**Reproducible:** lo corrimos 2 veces y sale identico byte por byte (mismo md5). Fijamos versiones en `requirements-nuestro.txt` porque con otra version de sklearn podria cambiar.

## dudas / pendiente

- en BAR-ATH predice 464 posesiones y la v0 364. No sabemos cual se acerca mas, no hay como saberlo sin el GT. En metrica el modelo predice MENOS posesiones que las reales, asi que mas no necesariamente es malo
- el balon del video todavia no entra
- la forma de los equipos tampoco
