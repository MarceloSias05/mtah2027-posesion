# Fase 11 - cierre (14 nov)

Nos quedamos con la **v3** como entrega final.

Llegamos a intentar una v4 con los 7 partidos abiertos de la DFL (Bassek et al. 2025, CC-BY 4.0). Valian la pena porque su tracking oficial marca frame por frame si el balon esta vivo o muerto y quien lo tiene, que es como se arma el GT del reto. Pero no se podian bajar desde el entorno donde corriamos los experimentos y ya no daba el tiempo para bajarlos, armar el banco y probar con calma antes del 17. Preferimos no meter algo a la carrera. Queda como lo primero que hariamos con mas tiempo.

Por que la v3 y no otra:
- es la que mejor aguanta un ruido de tracking que no conoce (0.441 vs 0.387 de la v2), y no sabemos la forma exacta del error de BAR-ATH
- en el ruido que si conocemos pierde muy poco (0.529 vs 0.534)
- se reproduce identica byte por byte (md5 `6cb2046fe5924ae3878a475281a68c23`), probado desde una copia limpia

Las versiones v0, v1 y v2 se quedan en el repo como historial.
