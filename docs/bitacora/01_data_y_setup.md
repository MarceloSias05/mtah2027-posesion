# Fase 1 - bajar la data y ver que todo cuadre

La data venia en el drive del reto partida en varios zips. Se descomprimio en `data/` con los nombres originales. Los videos no se movieron de la compu porque pesan mucho (5.2 GB el tactico y 14 GB el broadcast).

Antes de hacer nada corrimos `starter/baseline.py` para regenerar los 4 baselines oficiales. Salieron identicos byte por byte a los que vienen en `evaluation/results/`, entonces la data esta completa y estamos leyendo los frames igual que ellos. Eso era lo primero que queriamos descartar porque un frame de desfase ya te tira el spellF1.

Cosas que vimos de la data:

| cosa | dato |
|---|---|
| frames del video tactico | 199,319 a 25fps |
| frames que califican | 158,857 (1er tiempo 11185-90651, 2do 110808-190197) |
| balon visible en el tracking | 56.9% de todos los frames |
| balon faltante en frames calificados | 64,643 frames, mas o menos el 41% |
| tracks | 46 slots, no son jugadores fijos, cambian de identidad |
| homografia tactico | valida en todos los frames |

Ojo con el indice: el ATD empieza en frame_id 1 y el video en 0, asi que `frame_video = frame_id - 1`. La homografia y la submission ya van en frames de video.

Tambien sacamos que tan grande se ve el balon en el video tactico proyectando 22cm con la homografia: entre 4 y 9 pixeles de ancho dependiendo de donde este en la cancha. Osea es muy chiquito, por eso en la fase 2 el detector va por tiles y no con la imagen completa.

Lo que nos dijo la doc de evaluacion y que cambia como pensamos el problema: el ranking es por **spellF1**, que cuenta posesiones completas y no frames. El baseline a vencer es 0.2433. Y la `X` el scorer la rellena con la ultima etiqueta que pusiste, osea que dentro de una posesion no cuesta nada quedarse callado cuando se pierde el balon pero en un cambio de posesion si cuesta caro.

Otra cosa importante: el GT no lo hizo una persona viendo el partido, sale mecanico del tracking corregido de Metrica (D donde marca balon muerto y si no el equipo que marca como dueño). Entonces en el fondo hay que parecerse a como Metrica decide "dueño" y "muerto".
