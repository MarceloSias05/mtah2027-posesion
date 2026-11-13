# Fase 7 - cosas que probamos y NO funcionaron (13 nov)

Tambien hay que documentar lo que no jalo, el doc tecnico lo pide ("cuales descartaron").

## forma de los equipos

Idea: cuando no hay balon, el equipo que ataca se abre a lo ancho, se estira y avanza. Le metimos al modelo 10 señales de forma (`shape_features` en `src/segmentos.py`): que tan adelantado va cada equipo contra su posicion normal, ancho, largo, area y velocidad hacia adelante. La direccion de ataque la saca solo (en 2 minutos el equipo con el centroide mas a la izquierda ataca a la derecha).

Resultado fuera de muestra: **0.608**, peor que la v1 (0.623). Descartado.

Por que no ayudo: viendo los frames donde falta el balon pero el juego sigue vivo, el modelo casi siempre dice D ahi (acierta el equipo solo 11-24% de esas veces porque dice "muerto"). El problema en esos frames no es saber quien ataca, es que confunde vivo con muerto. La forma del equipo no arregla eso.

## afinar el viterbi

Probamos costos distintos para entrar y salir de balon muerto, y un sesgo para que diga mas o menos D. Lo mejor en el banco dio 0.624 contra 0.623 de la v1, nada. Y cuando la eleccion de esos costos se hace con prueba cruzada da 0.617, osea peor. Eso es sobreajuste al banco. Nos quedamos con la v1 como esta.

## conclusion

Con las señales que tenemos ya topamos alrededor de 0.62 en el banco. Para subir mas hace falta informacion NUEVA en los frames sin balon (el balon del video, el smart tagging), no darle mas vueltas a lo mismo.
