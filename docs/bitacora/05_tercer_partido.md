# Fase 5 - tercer partido de metrica y que tan robusta es la regla (13 nov)

## juego 3 al banco

El juego 3 de metrica viene en EPTS (igual que el reto) y los eventos en json, entonces le hicimos su propio cargador (`load_game3` en `src/metrica_datos.py`). Trae eventos CARRY que los otros no, los metimos tambien a la definicion de posesion.

El baseline se porta igual en los 3:

| ventana | juego 1 | juego 2 | juego 3 |
|---|---|---|---|
| 0 | 0.102 | 0.087 | 0.084 |
| 25 | 0.347 | 0.332 | 0.318 |
| **50** | **0.402** | **0.390** | **0.357** |
| 125 | 0.283 | 0.269 | 0.296 |

## prueba cruzada con 3 partidos

Ahora calibramos en 2 y probamos en el que queda fuera, los 3 turnos (`src/calibrar_histeresis.py`):

| calibro en | pruebo en | histeresis | baseline |
|---|---|---|---|
| 2, 3 | 1 | 0.620 | 0.402 |
| 1, 3 | 2 | 0.558 | 0.390 |
| 1, 2 | 3 | 0.590 | 0.357 |
| | **promedio** | **0.589** | **0.383** |

Se sostiene, ~54% arriba del baseline en partidos que la regla no vio.

## el ruido

Duda que nos salio: el tracking de BAR-ATH es automatico y el de metrica esta mas limpio. Si en BAR-ATH las posiciones vienen mas ruidosas, un radio de control muy chico (0.75m) podria fallar. Probamos ensuciando metrica con ruido a proposito:

| ruido | baseline | r0.75 k5 | r1.0 k8 | r1.5 k12 | r2.0 k12 |
|---|---|---|---|---|---|
| 0 | 0.383 | **0.603** | 0.596 | 0.587 | 0.573 |
| 0.3 m | 0.363 | **0.590** | 0.584 | 0.578 | 0.575 |
| 0.6 m | 0.329 | 0.527 | 0.532 | 0.529 | **0.552** |
| 1.0 m | 0.281 | 0.435 | 0.417 | 0.444 | **0.475** |

Osea con poco ruido gana el radio chico y con mucho ruido el grande. Entonces medimos que tanto "tiembla" el tracking de BAR-ATH de un frame a otro (segunda diferencia de la posicion, no necesita GT):

- jugadores: BAR-ATH 0.0014 m, metrica 0.0023-0.0029 m → BAR-ATH viene incluso mas suave (seguro ya viene filtrado)
- balon: BAR-ATH 0.011 m, metrica ~0.001 m → mas ruidoso pero muy lejos de lo que meteria un ruido de 0.3m (eso da ~0.86m)

Conclusion: el ruido frame a frame de BAR-ATH es bajo, el problema no es ese. Lo que no podemos medir es si tiene un error fijo (que el balon este corrido siempre un poco), eso no se ve con este truco.

Decidimos quedarnos con **r=1.0 m, k=8, dgap=25**: casi igual de bueno que 0.75 sin ruido (0.596 vs 0.603) y un poco mas aguantador si hay ruido. Es la misma que ya traia la v0, asi que la v0 no cambia.
