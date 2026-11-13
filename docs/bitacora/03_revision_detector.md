# Fase 3 - revision del detector de balon (13 nov)

Termino la corrida en la mac (M5, mps), 68,406 frames en ~15 horas reales con 1.2-1.5 fps. Salieron 5 warnings de "NMS time limit" en todo el log, no vale la pena reprocesar nada. El csv tiene exactamente los frames que tenia que tener, sin repetidos.

## que tanto coincide con el tracking

En los 3,763 frames "check" (donde el ATD si tiene balon) el mejor candidato del detector cae:

| distancia al balon del ATD | % de frames |
|---|---|
| < 1 m | 44% |
| < 2 m | 59% |
| < 5 m | 73% |

mediana 1.3 m. Cuando la confianza es >0.75 sube a 68% a menos de 2m, con conf <0.25 casi nunca le atina (8%). Esto es solo un check automatico, NO usamos estos numeros para escoger ningun umbral.

## falsos positivos fijos

Casi la mitad de los candidatos (48%) caen en puntos que no se mueven en coordenadas de cancha en todo el partido. Los mas fuertes: punto de penal izquierdo (11,34), un punto en la banda cerca del metro 95 (seguro balon de repuesto o algo asi), varios puntos en la banda de enfrente a media cancha (zona de bancas?), el centro, las porterias y banderines.

Regla que usamos para marcarlos, sin tocar el GT: una celda de 1m donde hay detecciones en 250+ frames distintos repartidos en mas de 60 segundos es un objeto fijo. El balon en juego no se queda 10 segundos en el mismo metro cuadrado repartido a lo largo de un minuto, eso es fisica no tuneo. (ojo: tambien puede borrar el balon real cuando esta en el punto de penal o en el centro para un saque, pero eso es balon muerto de todos modos)

## continuidad

Despues de quitar los fijos ligamos candidatos frame a frame si el salto es fisicamente posible: balon a max ~35 m/s = 1.4 m por frame a 25fps, mas 1.5m de ruido. Nos quedamos con tramos de 5+ frames seguidos.

Resultado: **63% de los frames donde el tracking perdio el balon tienen un candidato continuo y no fijo**. Y esos candidatos estan a una mediana de 0.8m del jugador mas cercano, osea pegados al pie de alguien, que es lo que esperarias del balon de verdad.

## lo que no esperabamos (importante)

Los huecos del balon en el tracking NO son cortitos. Son 150 huecos nomas, mediana de 10 segundos, y 44 de ellos duran mas de 20 segundos (el mas largo 3 min 41s). Casi no hay huecos de menos de 5s, parece que el ATD ya interpola esos.

Y en esos huecos los jugadores se mueven a la mitad de velocidad: ~0.9 m/s de promedio contra 1.9 m/s cuando el balon si se ve. Eso huele a balon muerto (faltas, cambios, lesiones, celebraciones). Tiene sentido porque en un partido normal el balon esta en juego mas o menos 55-60% del tiempo y aqui el tracking ve el balon en 56.9%.

Osea que **el tracking pierde el balon sobretodo cuando el juego esta parado**. Esto cambia el plan:
- "no hay balon + jugadores lentos" es una señal fuertisima de D. se la pasamos al de balon muerto
- el detector del video vale menos para seguir jugadas y mas para saber donde se reanuda el juego y quien saca
- hay que confirmar la relacion con datos externos (tiempo efectivo de juego de los partidos de metrica) antes de meter un umbral

## siguiente

- pasarle al mecatronico los candidatos ya marcados (fijo / tracklet) para el filtro
- medir en metrica cuanto cae el spellF1 si le quitamos el balon, para saber cuanto vale todo esto de verdad
