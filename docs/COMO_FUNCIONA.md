# Como funciona y por que lo hicimos asi

> entrega actual: **v3** (seccion 10). las secciones 7, 8 y 9 describen versiones anteriores que siguen en el repo.

Esto es la explicacion completa para el equipo (y la base del documento tecnico, que va en ingles). La bitacora tiene el orden en que fuimos descubriendo las cosas, aqui esta ordenado por tema.

---

## 1. Entender bien que se califica

Lo primero fue leer `EVALUATION.md` con calma porque cambia todo.

El ranking es por **spellF1**. El scorer agarra nuestras etiquetas, las parte en "posesiones" (tramos seguidos del mismo equipo) y las empareja una a una con las del ground truth. Una posesion cuenta como acertada si se traslapa lo suficiente con la real (lo prueban con 5 niveles de traslape y promedian).

Que significa en la practica:
- **los bordes importan muchisimo.** si detectas un cambio de posesion un segundo tarde, esa posesion y la siguiente se traslapan menos con las reales
- **partir una posesion en dos es caro.** si en medio de una posesion del Barça pones 3 frames de Athletic, ahora tienes 3 posesiones donde habia 1, y dos de ellas no empatan con nada
- **la `X` dentro de una posesion es gratis**: el scorer la rellena con la etiqueta anterior. Entonces cuando no sabemos, conviene callarse y no inventar un cambio

Por eso el baseline sin suavizar saca 0.05 aunque por frames tenga 0.65: acierta muchos frames pero parte todo en pedacitos.

Otra cosa que leimos: el GT no lo hizo una persona viendo el partido. Sale mecanicamente del tracking **corregido** de Metrica (D donde ese tracking dice balon muerto, si no el equipo que marca como dueño). O sea en el fondo hay que parecerse a como Metrica decide dueño y balon muerto.

## 2. Las reglas y por que nos obligan a trabajar asi

El correo de aclaracion (11 nov) dice que no se puede entrenar, ajustar ni calibrar nada con el GT ni con el video del partido, y no se puede comparar el output contra el video. Si algo tiene parametros, se ajustan con datos externos.

Y no hay leaderboard. Entonces **no tenemos forma de saber si algo mejora** a menos que tengamos otro lugar donde medir. De ahi sale lo mas importante de todo el proyecto: el banco.

## 3. El banco de pruebas con Metrica (`src/banco_metrica.py`)

Metrica publica 3 partidos de muestra en github (`metrica-sports/sample-data`). Los 3 traen tracking de jugadores y balon + eventos (pases, recuperaciones, balones fuera, faltas, set pieces). El juego 3 viene en EPTS, el mismo formato del reto.

Con los eventos armamos un GT de posesion igual de formato que el del reto:
- el equipo que tiene la pelota = el equipo del ultimo pase / recuperacion / set piece / tiro / balon perdido
- D desde que el balon sale, hay falta o gol, hasta el siguiente set piece (el saque que reanuda)

Y lo calificamos con `evaluation/possession_metrics.py`, el mismo codigo del reto.

**Por que confiamos en el banco:** corrimos ahi el baseline oficial con sus 4 ventanas y sale el mismo orden que en BAR-ATH: la de 50 gana, la de 0 es pesima y la de 125 empeora. Los numeros son mas altos (el tracking de muestra es mas limpio) pero se comporta igual. Si algo sube en el banco es razonable pensar que sube en el reto.

**Limitacion:** nuestro GT del banco sale de eventos, no del tracking corregido como el del reto. Se parecen pero no son identicos, sobretodo en los bordes del balon muerto.

## 4. La regla de histeresis (`src/histeresis.py`)

**El problema del baseline:** por cada frame le da la pelota al equipo del jugador mas cercano al balon. Pero en futbol el rival pasa cerca del balon todo el tiempo (presion, un defensa que se cruza) sin que cambie la posesion. Cada vez que eso pasa el baseline parte la posesion. En Metrica predice ~470 posesiones cuando hay ~330.

**Lo que hace la regla:**
1. un jugador "controla" el balon solo si esta a menos de **r** metros (si el mas cercano esta a 5m nadie la controla, el balon va viajando)
2. el dueño se mantiene hasta que **el otro equipo controle k frames seguidos**. un rival que pasa cerca un instante no cambia nada
3. si el balon falta en el tracking mas de **dgap** frames seguidos, es D (el tracking pierde el balon casi siempre en balon muerto, ver seccion 5)

**De donde salen los numeros:** `src/calibrar_histeresis.py` prueba combinaciones de r, k y dgap **solo en Metrica** y hace prueba cruzada: calibra en 2 partidos y prueba en el que queda fuera, los 3 turnos. Si una combinacion solo sirviera por casualidad para un partido, ahi se veria.

| calibro en | pruebo en | histeresis | baseline |
|---|---|---|---|
| 2, 3 | 1 | 0.620 | 0.402 |
| 1, 3 | 2 | 0.558 | 0.390 |
| 1, 2 | 3 | 0.590 | 0.357 |

Promedio fuera de muestra 0.589 contra 0.383 del baseline.

Final: r = 1.0 m, k = 8 frames (un tercio de segundo), dgap = 25 frames (1 segundo). El 0.75m saca un poquito mas en datos limpios pero aguanta peor si el tracking trae ruido, por eso nos quedamos con 1.0 (detalle en bitacora 05).

Tiene sentido futbolero: 1 metro es "lo tiene en el pie", y un tercio de segundo es lo minimo para que un robo sea robo y no un roce.

## 5. Lo del balon muerto

En BAR-ATH el tracking ve el balon en 56.9% de los frames, que es casi lo que dura el balon en juego en un partido normal. Y cuando falta el balon los jugadores se mueven a la mitad de velocidad (0.9 vs 1.9 m/s). En Metrica lo confirmamos: el balon falta en 78-90% de los frames muertos y solo en 14-19% de los vivos.

**Pero** el baseline oficial ya usa esto (sin balon = nadie la tiene = D). Asi que no es ventaja nuestra por si sola. Lo que si podemos mejorar son los bordes: exactamente cuando se muere y cuando revive el balon. Para eso faltan señales como balon saliendo de la cancha y los set pieces del Smart Tagging.

## 6. El balon del video (`tools/ball_from_video.py`)

**Por que:** el tracking pierde el balon en 41% de los frames calificados. Si sabemos donde quedo el balon en esos huecos podemos saber donde y quien reanuda el juego.

**Como:** usamos el detector de balon de roboflow/sports (YOLOv8, codigo MIT, entrenado con videos de la Bundesliga, nunca vio este partido). El balon en la camara tactica mide 4-9 pixeles, entonces cada frame se corta en 8 tiles de 640px, se detecta en cada uno y se juntan. Con la homografia pasamos cada deteccion a coordenadas de cancha y tiramos lo que cae fuera. Guardamos hasta 5 candidatos por frame.

Solo corre en los 64,643 frames donde falta el balon + 1 de cada 25 donde si esta (para comparar). Tardo ~15 horas en una Mac M5.

**Que salio** (detalle en bitacora fase 3):
- cuando el tracking tiene balon, el detector cae a menos de 2m el 59% de las veces
- 48% de los candidatos son objetos fijos (puntos de penal, banda, porterias). los quitamos con una regla fisica: si algo aparece en el mismo metro cuadrado mas de un minuto no es el balon en juego
- despues de eso y de pedir que se mueva como balon de frame a frame: 63% de los huecos quedan con un candidato limpio, a ~0.8m del jugador mas cercano

**Ojo:** como los huecos son sobretodo balon muerto, este detector sirve mas para los reinicios que para seguir jugadas. Todavia no lo metemos a la entrega, primero hay que probar en el banco cuanto aporta.

El CSV que sale NO se sube al repo (las reglas no dejan publicar data derivada del video frame por frame). Lo entregariamos como archivo intermedio si los organizadores lo aceptan.

## 7. La entrega v0 (`src/generar_v0.py`)

Aplica la regla de histeresis con los parametros de Metrica tal cual a BAR-ATH. Pasa el validador oficial. 364 posesiones de ~12s, Barça ~60% de la posesion con balon vivo.

No la calificamos contra los 5 min publicos (no queremos tentarnos a ajustar con eso). Es nuestra red de seguridad: si todo lo demas falla, esto ya le gana al baseline en datos externos.

## 8. El modelo de segmentos (`src/segmentos.py`, `src/generar_v1.py`) - v1, version anterior

La histeresis es una regla a mano. El siguiente paso fue que un modelo aprenda de los partidos de Metrica que tan probable es H, A o D en cada frame, y que despues un **viterbi** escoja la secuencia completa de posesiones mas creible, cobrando cada cambio. Es como decir "prefiero pocas posesiones largas a muchas cortitas, a menos que la evidencia de un cambio sea fuerte". Eso es exactamente lo que premia el spellF1.

Señales por frame: si falta el balon y que tan largo es el hueco, distancia del mas cercano de cada equipo, velocidad del balon, balon fuera de la cancha, velocidad de los jugadores, promedios en ventanas de 0.5/1/3 s, y la salida de la histeresis. Clasificador HistGradientBoosting entrenado solo en Metrica, con los datos volteados local/visitante para que no aprenda sesgos de un partido.

Fuera de muestra: **0.623** promedio (histeresis 0.589, baseline 0.383). Sin la histeresis como señal salio peor (0.569), y sin el viterbi el clasificador solo saca ~0.3: el viterbi es la pieza clave. Costos elegidos con prueba cruzada en Metrica (cambio 8, balon muerto 20). Sale identico byte por byte en cada corrida con las versiones de `requirements-nuestro.txt`.

## 9. Toques, el banco sucio y la v2 (`src/generar_v2.py`)

**Señales de toques.** Cuanto tiempo paso desde que cada equipo controlo el balon y cuanto falta para que lo vuelva a controlar, mas donde esta el balon respecto a las lineas. En el banco limpio subio de 0.623 a 0.671.

**Pero BAR-ATH no es como metrica.** Revisando solo el tracking de entrada vimos que en BAR-ATH el balon esta a 1.9 m del jugador mas cercano (mediana), contra 0.3 m en los juegos 1 y 2 de metrica, y tiembla 7 veces mas. Con eso la regla "a menos de 1 m = control" casi nunca se cumple en BAR-ATH.

**El banco sucio.** Le metimos a metrica un error lento (el balon se corre ~1 m y cambia suave) y un temblor, hasta que la distancia y el temblor quedan igual que en BAR-ATH (`src/calibrar_ruido.py`). Ahi el baseline baja a 0.323, mas cerca de su 0.243 real, osea se parece mas al reto. Y descubrimos que la v1 bajaba a 0.486 y la v0 a 0.377: tenian el radio mal puesto para BAR-ATH.

**La v2.** Radio de control 2.5 m y 18 frames (elegidos en el banco sucio), señales de toques y lugar, entrenada con metrica limpio + sucio juntos (aguanta los dos casos), costos del viterbi elegidos en el banco sucio. Fuera de muestra: **0.547 en el banco sucio** (v1 0.486, baseline 0.323) y 0.612 en el limpio. Reproducible byte por byte.

## 10. La v3: aguantar un ruido que no conocemos (`src/generar_v3.py`) - entrega actual

La v2 aprendio un solo tipo de error (balon corrido suave + temblor). Pero no sabemos que forma tiene el error real de BAR-ATH. Entonces armamos mas tipos: **saltos** (el tracker se confunde de objeto unos segundos) y **huecos** extra en juego vivo. Y un ruido de prueba mas fuerte y mezclado con el que nadie entrena, para ver quien aguanta lo desconocido.

Lo que salio: los costos de cambio que traia la v2 (18/12) eran los que peor aguantaban el ruido de prueba (0.387). Con costos mas altos (25/40) y entrenando con los 3 tipos de ruido sube a **0.441**, perdiendo poquito en el sucio conocido (0.529 vs 0.534) y algo en el limpio (0.587 vs 0.611). Como BAR-ATH no es limpio y no conocemos su error exacto, elegimos la que tiene el mejor peor caso.

Tambien probamos y descartamos: suavizar el balon antes (empeora, borra patadas), duracion minima de posesion (no aporta), promediar v2 con v3 (queda en medio). Detalle en bitacora 10.

## 11. Que sigue (por impacto)

1. leer la posesion en la forma de los equipos cuando no hay balon (el que ataca se abre y avanza)
2. balon del video + filtro del mecatronico en los huecos
3. bordes del balon muerto con balon fuera de la cancha y Smart Tagging

Cada cosa entra a la entrega **solo si sube en el banco**.

## 12. Lo que vamos a necesitar para el documento tecnico

- enfoque y por que (secciones 1, 3, 4)
- assets usados y descartados: tracking si, homografia si (para el video), video tactico si (detector), broadcast no por ahora, smart tagging pendiente
- datos de entrenamiento: ninguno etiquetado de este partido. Metrica sample data (publico, eventos hechos por Metrica) para calibrar; detector de roboflow entrenado con DFL Bundesliga (no lo entrenamos nosotros)
- reglas de posesion: seccion 4 + lo que escriba el analista
- limitaciones: GT del banco viene de eventos, solo 3 partidos para calibrar, el detector confunde objetos fijos
- como reproducir: README
- uso de IA: usamos Claude como asistente de desarrollo, la data se subio bajo la aclaracion del 11 nov que lo permite
