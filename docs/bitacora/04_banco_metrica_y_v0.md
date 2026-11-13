# Fase 4 - banco de pruebas con metrica y primera entrega (13 nov)

## el banco

Como no hay leaderboard y no podemos tunear con este partido, armamos un "mini reto" con los partidos publicos de Metrica (`src/descargar_metrica.sh`). Usamos los juegos 1 y 2 que traen tracking + eventos.

El GT lo sacamos de sus eventos: el equipo del ultimo pase/recuperacion/set piece/tiro es el que tiene la pelota, y es D desde un BALL OUT, falta o gol hasta el siguiente SET PIECE. No es identico a como Metrica saca el GT del reto (ellos usan su tracking corregido) pero se le parece bastante. Y lo calificamos con **el mismo scorer del reto** (`evaluation/possession_metrics.py`).

Primera prueba: correr el baseline ahi. Sale el mismo patron que en el reto:

| ventana | juego 1 | juego 2 | (BAR-ATH oficial) |
|---|---|---|---|
| 0 | 0.102 | 0.087 | 0.049 |
| 25 | 0.347 | 0.332 | 0.200 |
| **50** | **0.402** | **0.390** | **0.243** |
| 125 | 0.283 | 0.269 | 0.224 |

Los numeros son mas altos porque el tracking de los sample games es mas limpio, pero el orden es igual y la de 50 gana. Eso nos da confianza de que si algo sube aqui deberia subir alla tambien.

## lo de balon muerto

Confirmado en metrica que el balon desaparece del tracking sobretodo en balon muerto: falta en 78-90% de los frames muertos y solo 14-19% de los vivos. Los jugadores tambien bajan a ~1 m/s en balon muerto vs ~1.9 vivo.

PERO nos dimos cuenta que el baseline oficial ya hace eso (si no hay balon no le da la pelota a nadie y queda D). Osea no es ventaja nuestra por si sola, ya esta metido en el 0.24. Bajon pero bueno saberlo antes.

## regla de histeresis

Lo que si mueve el numero: el baseline cambia de dueño cada vez que alguien del otro equipo queda mas cerca del balon, aunque sea un frame. Eso parte las posesiones en pedacitos (en metrica predice ~470 posesiones cuando hay ~330).

`src/histeresis.py`:
- solo cuenta como "control" si el jugador mas cercano esta a menos de r metros
- el dueño solo cambia si el otro equipo controla k frames seguidos
- D si el balon falta mas de dgap frames seguidos

Calibrado en metrica (`src/calibrar_histeresis.py`), con prueba cruzada para no engañarnos:

| calibro en | pruebo en | histeresis | baseline |
|---|---|---|---|
| juego 1 | juego 2 | 0.548 | 0.390 |
| juego 2 | juego 1 | 0.588 | 0.402 |

Mejor combinacion en los dos juegos: **r=1.0 m, k=8 frames, dgap=25 frames** → spellF1 promedio 0.598 contra 0.396 del baseline. Osea ~50% mas, y sin tocar BAR-ATH para nada.

## v0

`src/generar_v0.py` aplica esa regla tal cual a BAR-ATH → `outputs/v0_histeresis.csv`. Pasa el validador. 364 posesiones de 11.9s promedio, Barça con ~60% de la posesion con balon vivo (suena a barça jaja).

NO la calificamos contra los 5 min publicos. No sabemos su numero real, solo que el metodo le gana al baseline en datos externos.

## siguiente

- meter el juego 3 de metrica (formato EPTS como el del reto) al banco, tres partidos > dos
- usar el balon del video y el filtro del mecatronico en los huecos
- balon muerto mas fino (balon fuera de la cancha, set pieces del smart tagging)
- modelo de segmentos en vez de la regla a mano
