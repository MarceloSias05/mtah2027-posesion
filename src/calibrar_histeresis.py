# busca los parametros de la regla de histeresis SOLO en los partidos de metrica
# prueba cruzada: calibra en 2 partidos y prueba en el que queda fuera, los 3 turnos
# uso: cd src && python calibrar_histeresis.py
import itertools, warnings
import numpy as np
import banco_metrica as bench, histeresis as hyst
warnings.filterwarnings('ignore')
G = list(bench.games())
grid = list(itertools.product([0.75, 1.0, 1.5, 2.0, 2.5], [5, 8, 12, 18], [12, 25, 50]))
S = {}
for i, g in enumerate(G):
    for q in grid:
        p = hyst.hysteresis(g, *q); p[~g['valid']] = 'X'
        S[(i,) + q] = bench.score(g['gt'], p)[0]
base = []
for g in G:
    code, _, _ = bench.nearest(g); b = bench.smooth(code, 50); b[~g['valid']] = 'X'
    base.append(bench.score(g['gt'], b)[0])
print('prueba cruzada (deja un partido fuera):')
out = []
for te in range(len(G)):
    tr = [i for i in range(len(G)) if i != te]
    best = max(grid, key=lambda q: np.mean([S[(i,) + q] for i in tr]))
    out.append(S[(te,) + best])
    print('  calibro en %s %s -> juego %d: spellF1 %.3f (baseline %.3f)' % (
        [G[i]['g'] for i in tr], best, G[te]['g'], S[(te,) + best], base[te]))
print('  promedio fuera de muestra: %.3f  (baseline %.3f)' % (np.mean(out), np.mean(base)))
best = max(grid, key=lambda q: np.mean([S[(i,) + q] for i in range(len(G))]))
print('parametros finales (los 3 juegos):', best, 'spellF1 %.3f' % np.mean([S[(i,) + best] for i in range(len(G))]))
