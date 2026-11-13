# Fase 2 - buscar el balon en el video

El problema mas grande del tracking es que pierde el balon justo cuando importa (area llena, balones aereos, tapado por jugadores). Como el video si se puede usar como input mientras el modelo no se haya entrenado con el, decidimos correr un detector de balon sobre el video tactico para rellenar huecos.

Modelo que escogimos: el `football-ball-detection` de roboflow/sports. Por que ese:
- el codigo es MIT y los pesos son publicos, los organizadores lo pueden revisar y correr
- esta entrenado con videos de la Bundesliga (dataset DFL de kaggle), no con LaLiga y mucho menos con este partido
- ya trae una forma de usarlo pensada para balon chiquito (cortar la imagen en tiles de 640)

Probamos tambien pensar en YOLO normal de COCO (clase "sports ball") pero con un balon de 4-9px en una imagen 1920x1080 casi no lo iba a ver, asi que lo descartamos sin correrlo.

Como funciona `tools/ball_from_video.py`:

Corta cada frame en 8 tiles de 640 con 64px de traslape, corre el modelo en todos, junta las detecciones y si dos tiles vieron lo mismo se queda con la de mas confianza. Despues con la homografia pasa cada deteccion a coordenadas de cancha y tira las que caen fuera (gradas, anuncios). Guarda hasta 5 candidatos por frame con su conf, no elige uno todavia.

Solo corre en los 64,643 frames calificados donde el ATD no tiene balon, mas 3,763 frames (1 de cada 25) donde si lo tiene. Esos ultimos son solo para un check automatico de que tanto coincide con el tracking, no los usamos para escoger umbrales. Los settings son los mismos que trae roboflow/sports y el conf minimo esta bajo (0.05) a proposito, no se tuneo nada.

Un detalle que nos costo pensar: el script nunca hace seek en el video, siempre lee desde el frame 0. En mp4 el seek aveces cae unos frames despues y eso nos desalineaba todo sin darnos cuenta. Saltar frames con `grab()` tarda unos minutos nada mas.

Lo probamos con un video sintetico (un punto blanco donde la homografia dice que esta el centro de la cancha) y un detector falso. Los frames salen alineados y la ida y vuelta de la homografia da 0.500 / 0.500 como debe. Tambien probamos que si lo cortas y lo vuelves a correr sigue donde iba.

**Pendiente:** correrlo de verdad en la mac (M5, 24gb) con `--limit 300` primero para ver los fps y luego todo en la noche. Calculamos 2 a 5 horas pero no sabemos hasta ver los fps reales. El csv que sale (`outputs/ball_video.csv`) no se sube al repo porque es data derivada del video frame por frame y las reglas no dejan publicarla.

Para correrlo en la noche dejamos `tools/correr_balon_noche.sh`, arma el venv, baja los pesos, hace una prueba de 300 frames que imprime la velocidad y luego corre todo con caffeinate para que la mac no se duerma.
