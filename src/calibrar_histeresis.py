# busca los parametros de la regla de histeresis SOLO en los partidos de metrica
# y hace la prueba cruzada (calibra en uno, prueba en el otro)
# uso: python src/calibrar_histeresis.py
import itertools, warnings
import numpy as np
import banco_metrica as bench, histeresis as hyst
warnings.filterwarnings('ignore')
G = list(bench.games())
grid = list(itertools.product([0.75, 1.0, 1.5, 2.0, 2.5, 4.0], [5, 8, 12, 18, 25], [12, 25, 50]))
S = {}
for i, g in enumerate(G):
    for q in grid:
        p = hyst.hysteresis(g, *q); p[~g['valid']] = 'X'
        S[(i,) + q] = bench.score(g['gt'], p)[0]
for tr, te in [(0, 1), (1, 0)]:
    best = max(grid, key=lambda q: S[(tr,) + q])
    code, _, _ = bench.nearest(G[te]); b = bench.smooth(code, 50); b[~G[te]['valid']] = 'X'
    print('calibro en juego %d %s -> juego %d spellF1 %.3f (baseline %.3f)' % (
        tr + 1, best, te + 1, S[(te,) + best], bench.score(G[te]['gt'], b)[0]))
best = max(grid, key=lambda q: np.mean([S[(i,) + q] for i in range(len(G))]))
print('mejor en los dos juegos:', best, 'spellF1 promedio %.3f' % np.mean([S[(i,) + best] for i in range(len(G))]))
