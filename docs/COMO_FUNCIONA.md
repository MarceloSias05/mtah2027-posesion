# Como funciona y por que lo hicimos asi

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

Metrica publica 3 partidos de muestra en github (`metrica-sports/sample-data`). Los juegos 1 y 2 traen tracking de jugadores y balon + eventos (pases, recuperaciones, balones fuera, faltas, set pieces).

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

**De donde salen los numeros:** `src/calibrar_histeresis.py` prueba combinaciones de r, k y dgap **solo en Metrica** y hace prueba cruzada: calibra con el juego 1 y prueba en el juego 2, y al reves. Si una combinacion solo sirviera por casualidad para un partido, ahi se veria.

| calibro en | pruebo en | histeresis | baseline |
|---|---|---|---|
| juego 1 | juego 2 | 0.548 | 0.390 |
| juego 2 | juego 1 | 0.588 | 0.402 |

Final: r = 1.0 m, k = 8 frames (un tercio de segundo), dgap = 25 frames (1 segundo). spellF1 promedio 0.598 contra 0.396 del baseline.

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

## 8. Que sigue (por impacto)

1. meter el juego 3 de Metrica al banco (viene en el mismo formato EPTS que el reto)
2. modelo de segmentos en vez de la regla a mano: que elija la secuencia completa de posesiones mas creible usando cuanto suelen durar
3. leer la posesion en la forma de los equipos cuando no hay balon (el que ataca se abre y avanza)
4. balon del video + filtro del mecatronico en los huecos
5. bordes del balon muerto con balon fuera de la cancha y Smart Tagging

Cada cosa entra a la entrega **solo si sube en el banco**.

## 9. Lo que vamos a necesitar para el documento tecnico

- enfoque y por que (secciones 1, 3, 4)
- assets usados y descartados: tracking si, homografia si (para el video), video tactico si (detector), broadcast no por ahora, smart tagging pendiente
- datos de entrenamiento: ninguno etiquetado de este partido. Metrica sample data (publico, eventos hechos por Metrica) para calibrar; detector de roboflow entrenado con DFL Bundesliga (no lo entrenamos nosotros)
- reglas de posesion: seccion 4 + lo que escriba el analista
- limitaciones: GT del banco viene de eventos, solo 2-3 partidos para calibrar, el detector confunde objetos fijos
- como reproducir: README
- uso de IA: usamos Claude como asistente de desarrollo, la data se subio bajo la aclaracion del 11 nov que lo permite
