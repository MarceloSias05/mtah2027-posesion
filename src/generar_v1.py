# entrega v1: modelo de segmentos
#  1. entrena el clasificador por frame con los 3 partidos de metrica (nada de BAR-ATH)
#  2. elige los costos del viterbi con prueba cruzada en metrica (cada partido predicho por un
#     modelo entrenado con los otros dos)
#  3. entrena con los 3 y aplica a BAR-ATH
# uso: python src/generar_v1.py   -> outputs/v1_segmentos.csv
import os, sys, itertools, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'starter')); sys.path.insert(0, ROOT)
from sklearn.ensemble import HistGradientBoostingClassifier
import banco_metrica as bench, segmentos as seg

LAB = {'H': 0, 'A': 1, 'D': 2}
GRID = list(itertools.product([2, 3, 5, 8, 12], [3, 5, 8, 12, 20, 40]))   # (cambio H<->A, entrar/salir de D)


def fit(games):
    X = np.vstack([g['X'][g['valid']][::3] for g in games])
    y = np.concatenate([g['y'][g['valid']][::3] for g in games])
    X, y = seg.mirror_full(X, y)
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
                                          random_state=0).fit(X, y)


def logp(m, X):
    return np.log(np.clip(m.predict_proba(X), 1e-6, 1))


def main():
    print('cargando metrica...')
    G = list(bench.games())
    for g in G:
        g['X'] = seg.features_con_histeresis(g)
        g['y'] = np.array([LAB.get(c, -1) for c in g['gt']])

    print('eligiendo costos con prueba cruzada...')
    oof = {}
    for i, g in enumerate(G):
        oof[i] = logp(fit([h for j, h in enumerate(G) if j != i]), g['X'])

    def dec(g, lp, c):
        p = seg.viterbi(lp, *c); p[~g['valid']] = 'X'; return p
    S = {c: [bench.score(g['gt'], dec(g, oof[i], c))[0] for i, g in enumerate(G)] for c in GRID}
    best = max(GRID, key=lambda c: np.mean(S[c]))
    print('  costos', best, 'spellF1 fuera de muestra por juego',
          ' '.join('%.3f' % s for s in S[best]), 'promedio %.3f' % np.mean(S[best]))

    print('entrenando con los 3 y aplicando a BAR-ATH...')
    m = fit(G)
    import load_atd
    L, W = seg.L, seg.W
    ds = load_atd.load(); df = ds.to_df(engine='pandas'); h, a = ds.metadata.teams
    xy = lambda t: np.stack([np.stack([df[f'{p.player_id}_x'], df[f'{p.player_id}_y']], -1) for p in t.players], 1)
    B = dict(n=len(df), Ph=xy(h) * [L, W], Pa=xy(a) * [L, W], B=np.stack([df.ball_x, df.ball_y], -1) * [L, W])
    lab = seg.viterbi(logp(m, seg.features_con_histeresis(B)), *best)
    os.makedirs(os.path.join(ROOT, 'outputs'), exist_ok=True)
    out = os.path.join(ROOT, 'outputs', 'v1_segmentos.csv')
    pd.DataFrame({'frame': np.arange(len(lab)), 'label': lab}).to_csv(out, index=False)
    print('listo', out)


if __name__ == '__main__':
    main()
