# Fase 10 - v3: que aguante un ruido que no conocemos (13 nov)

## el problema

La v2 se entreno con un solo tipo de "ensuciado" (balon corrido suave + temblor) que le atina a la mediana de distancia y temblor de BAR-ATH. Pero el error real de BAR-ATH puede tener otra forma. Si el modelo solo aguanta el ruido que le enseñamos, en BAR-ATH puede fallar.

## como lo medimos

Armamos 3 tipos de ensuciado para entrenar:
- **suave**: el de la v2
- **saltos**: el tracker se confunde de objeto, tramos de 0.5-2 s con el balon corrido ~4 m (uno cada ~30 s)
- **huecos**: huecos extra de 0.5-3 s en juego vivo (uno cada ~20 s)

Y un ruido de **prueba** que nadie usa para entrenar: todo junto y mas fuerte (corrimiento x1.4, temblor x2, saltos de 6 m mas seguido, mas huecos).

Siempre fuera de muestra (calibro en 2 partidos, pruebo en el otro).

## que probamos

| que | limpio | sucio conocido | ruido de prueba |
|---|---|---|---|
| v2 tal cual (costos 18/12) | 0.611 | 0.534 | 0.387 |
| v2 con costos 25/40 | 0.603 | 0.542 | 0.417 |
| entrenar con los 3 ensuciados, costos 12/40 | 0.603 | 0.532 | 0.431 |
| **entrenar con los 3 ensuciados, costos 25/40 (v3)** | 0.587 | 0.529 | **0.441** |
| promedio de v2 y la de 3 ensuciados | | 0.539 | 0.426 |
| suavizar el balon antes (mediana ±3 frames) | 0.601 | 0.536 | 0.408 |
| suavizar el balon antes (mediana ±8 frames) | 0.588 | 0.518 | 0.376 |
| duracion minima de posesion 12 o 25 frames | | 0.535-0.542 | 0.361-0.418 |

(los numeros de la v2 aqui son con otra semilla de ruido que en la fase 9, por eso 0.534 y no 0.547)

Lo que aprendimos:
- **los costos de cambio altos aguantan mejor lo desconocido**. Los de la v2 (18/12) eran los peores en el ruido de prueba
- entrenar con mas tipos de ruido ayuda con lo desconocido y pierde poquito en lo conocido
- suavizar el balon empeora (borra patadas de verdad). Descartado
- la duracion minima no aporta nada que no hagan ya los costos. Descartado
- promediar modelos queda en medio. Descartado

## la eleccion

Elegimos la que tiene el **mejor peor caso** entre el banco sucio conocido y el ruido de prueba: entrenar con los 3 ensuciados y costos 25/40. Ojo: al usar el ruido de prueba para elegir entre estas opciones ya no es 100% "nunca visto", pero solo elegimos entre 4-5 candidatos, no tuneamos nada fino ahi.

Lo que cuesta: en el banco limpio baja de 0.611 a 0.587. Pero BAR-ATH no es limpio (fase 9), asi que es un costo que aceptamos.

## v3

`python src/generar_v3.py` → `outputs/v3_segmentos.csv`
- ~3.5 min, menos memoria que la v2 (ya no hace la prueba cruzada adentro, los costos son fijos)
- identico en cada corrida, md5 `6cb2046fe5924ae3878a475281a68c23`
- 333 posesiones de 16.8 s, Barça ~62% de la posesion con balon vivo

**Esta es la entrega recomendada ahora.** La v2 y la v1 siguen en el repo de respaldo.
