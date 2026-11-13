# Fase 9 - el banco "sucio" y la v2 (13 nov)

## algo no cuadraba

Al aplicar la version con toques a BAR-ATH el reparto cambio mucho vs la v1. Antes de confiar revisamos si las señales se portan igual en BAR-ATH que en metrica (solo mirando el tracking de entrada, sin GT). Y no:

| | distancia mediana balon - jugador mas cercano | temblor del balon |
|---|---|---|
| metrica juego 1 | 0.28 m | 0.025 |
| metrica juego 2 | 0.28 m | 0.026 |
| metrica juego 3 | 1.27 m | 0.017 |
| **BAR-ATH** | **1.91 m** | **0.167** |

En los juegos 1 y 2 de metrica el balon viene casi pegado al que lo lleva. En BAR-ATH viene casi 2 metros lejos y tiembla como 7 veces mas. Osea la regla "a menos de 1 m = control" que calibramos en metrica casi nunca se cumple en BAR-ATH (solo 28% de los frames con balon vs 46-57% en metrica).

## ensuciar metrica

Hicimos que metrica se parezca a BAR-ATH: al balon le metemos un error lento (se corre unos metros, cambia suave en ~2 s) y un temblor frame a frame (`ensuciar_balon` en `src/segmentos.py`). Los niveles se eligen para que la distancia mediana y el temblor queden igual que en BAR-ATH (`src/calibrar_ruido.py`). Eso solo usa estadisticas del tracking de entrada, que las reglas permiten, nunca el GT ni el video.

| juego | error lento | temblor | distancia resultante | temblor resultante |
|---|---|---|---|---|
| 1 | 1.25 m | 0.004 | 1.96 m | 0.187 |
| 2 | 1.25 m | 0.004 | 1.90 m | 0.188 |
| 3 | 1.00 m | 0.004 | 1.89 m | 0.186 |
| BAR-ATH (objetivo) | | | 1.91 m | 0.167 |

## que paso en el banco sucio

El baseline en el banco sucio saca 0.323 (en el limpio 0.383). Su numero real en BAR-ATH es 0.243, asi que el banco sucio se parece mas a la realidad.

| metodo (fuera de muestra, banco sucio) | spellF1 |
|---|---|
| baseline | 0.323 |
| histeresis r=1.0 k=8 (v0) | 0.377 |
| histeresis r=2.5 k=18 | 0.443 |
| segmentos v1 (r=1.0) | 0.486 |
| segmentos + toques + lugar, r=1.0 | 0.507 |
| segmentos + toques + lugar, r=2.5 k=18 | 0.533 |
| **lo mismo, entrenando con metrica limpio + sucio (v2)** | **0.547** |

Lo importante: **la v0 y la v1 tenian el radio mal puesto para BAR-ATH**. Con el balon a 2 m, un radio de 1 m es demasiado fino. En el banco sucio el mejor es 2.5 m y 18 frames (0.72 s).

Entrenar con limpio + sucio junto gana en los dos bancos (sucio 0.547, limpio 0.612) contra entrenar solo con sucio (0.535 / 0.583). El modelo aprende a aguantar ruido sin olvidar el caso limpio.

## v2

`python src/generar_v2.py` → `outputs/v2_segmentos.csv`
- señales base + toques + lugar, radio 2.5 m / 18 frames
- entrena con los 3 partidos limpios + los 3 ensuciados
- costos del viterbi (cambio 18, balon muerto 12) elegidos con prueba cruzada en el banco sucio
- ~4 min, ~2-3 GB de RAM
- sale identico en cada corrida, md5 `5d3822b7e56bb6b604da90cd208bee40`
- 406 posesiones de 14 s, Barça ~58% de la posesion con balon vivo

**Esta es la entrega recomendada.**

## lo que no sabemos

- si el error del balon en BAR-ATH se parece a nuestro "ensuciado" en la forma, no solo en la mediana. Lo modelamos como corrimiento suave + temblor, puede ser otra cosa (ej. el balon en el aire proyectado al piso)
- el banco sucio sigue siendo mas facil que BAR-ATH real (baseline 0.323 vs 0.243)
