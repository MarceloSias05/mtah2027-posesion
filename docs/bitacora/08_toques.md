# Fase 8 - señales de toques y posicion del balon (13 nov)

Despues de topar en 0.62 probamos señales nuevas que si se pueden medir en el banco.

**Toques** (`touch_features`): para cada frame, cuanto tiempo paso desde la ultima vez que cada equipo controlo el balon (alguien a menos de r metros), y cuanto falta para la proxima. Mas la diferencia entre equipos. Tambien un detector de patadas (cambio brusco de velocidad del balon). Como el modelo ve todo el partido (no es en vivo), si puede usar "cuanto falta para el proximo toque".

Resultado fuera de muestra: **0.623 → 0.660**. El salto mas grande desde la histeresis.

**Lugar del balon** (`place_features`): distancia del balon (o de donde se vio por ultima vez) a la banda y a la linea de fondo, y en que parte del hueco sin balon va el frame (cuanto desde que se perdio, cuanto para que vuelva). Cerca de las lineas suelen venir saques.

Resultado: **0.660 → 0.671**.

Modelo mas grande (400 arboles, 63 hojas): 0.668, no ayuda. Nos quedamos con el normal.

Todo esto en el banco LIMPIO. Ver fase 9, que cambio bastante el panorama.
