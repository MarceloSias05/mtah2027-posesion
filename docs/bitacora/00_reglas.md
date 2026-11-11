# Fase 0 - reglas (11 nov)

Nos llego un correo de los organizadores aclarando que se puede y que no en el Initial Challenge. Dice que esas reglas estan por encima de todo lo demas (docs del repo, correos anteriores, respuestas individuales) asi que trabajamos con eso.

**NO se puede:**
- comparar nuestro output contra el video
- etiquetas a mano o cualquier dato hecho por humanos sobre este partido
- entrenar, ajustar o calibrar con el ground truth de posesion o con el video

**SI se puede:**
- subir la data a servicios de IA
- correr checks automaticos usando solo la data que nos dieron
- ver la data y el video para entender que cuenta como posesion
- usar el video, el tracking automatico, el smart tagging etc como input mientras el algoritmo no se haya entrenado con el GT ni con ese video
- entregar archivos de pasos intermedios
- usar cualquier dataset que tengamos derecho de usar (checar licencias)

Y lo que mas nos pega: si algo necesita entrenarse o tiene parametros que tunear, eso se hace **solo con data externa**.

## Lo que decidimos por esto

El GT publico de 5 min (17 posesiones) lo usamos nomas para ver que el archivo este bien armado y alineado. No para elegir entre dos versiones. Igual el propio EVALUATION.md muestra que si eliges la ventana del baseline viendo esos 5 min escoges la peor, entonces ni conviene.

Cualquier numero que metamos en el codigo (distancias, cuantos frames, umbrales) tiene que tener de donde salio. Vamos a llevar eso anotado en las fases siguientes para que si alguien pregunta lo podamos enseñar.

Ver el video si se vale pero solo para entender la definicion (ej. que pasa con un rebote o un balon dividido). Nada de "en el minuto tal la tiene el Athletic" metido en el codigo.

Duda que queda abierta: si podemos correr el scorer contra el GT publico una vez al final solo para reportar el numero. Tecnicamente es "provided data" y un check automatico pero preferimos preguntar por correo antes.
