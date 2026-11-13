# calcula cuanto hay que "ensuciar" el balon de cada partido de metrica para que se parezca al
# tracking automatico de BAR-ATH. solo usa el tracking de entrada (distancia tipica balon-jugador y
# temblor del balon), nunca el ground truth ni el video.
# uso: cd src && python calibrar_ruido.py   (los valores que salen estan fijos en generar_v2.py)
import os, sys, warnings
import numpy as np
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'starter')); sys.path.insert(0, ROOT)
import banco_metrica as bench, segmentos as seg, load_atd

ds = load_atd.load(); df = ds.to_df(engine='pandas'); h, a = ds.metadata.teams
xy = lambda t: np.stack([np.stack([df[f'{p.player_id}_x'], df[f'{p.player_id}_y']], -1) for p in t.players], 1)
g = np.zeros(len(df), bool); g[11185:90652] = True; g[110808:190198] = True
d0, a0 = seg.stats_balon(xy(h)[g] * [seg.L, seg.W], xy(a)[g] * [seg.L, seg.W],
                         np.stack([df.ball_x, df.ball_y], -1)[g] * [seg.L, seg.W])
del ds, df   # libera memoria antes de cargar metrica
print('BAR-ATH: distancia mediana balon-jugador %.3f m, temblor %.3f' % (d0, a0))
for x in bench.games():
    best = None
    for sl in [1.0, 1.1, 1.25, 1.4]:
        for st in [0.0, 0.002, 0.003, 0.004, 0.006]:
            d, ac = seg.stats_balon(x['Ph'], x['Pa'], seg.ensuciar_balon(x['B'], sl, st))
            err = abs(np.log(d / d0)) + abs(np.log(ac / a0))
            if best is None or err < best[0]: best = (err, sl, st, d, ac)
    print('juego %d: s_lento %.2f s_temblor %.3f -> distancia %.2f temblor %.3f' % ((x['g'],) + best[1:]))
