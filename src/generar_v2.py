# entrega v2 (bitacora 08 y 09)
#  - señales: base + toques (tiempo desde/hasta el ultimo control de cada equipo) + posicion del balon
#  - el tracking de BAR-ATH tiene el balon mas lejos de los jugadores y con mas temblor que metrica,
#    entonces entrenamos con metrica limpio + metrica "ensuciado" para parecerse a BAR-ATH
#    (niveles de ruido de calibrar_ruido.py, solo con el tracking de entrada)
#  - radio de control 2.5 m y 18 frames, elegidos en el banco sucio
#  - costos del viterbi elegidos con prueba cruzada en el banco sucio
# uso: python src/generar_v2.py   -> outputs/v2_segmentos.csv
import os, sys, itertools, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'starter')); sys.path.insert(0, ROOT)
from sklearn.ensemble import HistGradientBoostingClassifier
import banco_metrica as bench, segmentos as seg

R_CONTROL, K_FRAMES = 2.5, 18
RUIDO = {1: (1.25, 0.004), 2: (1.25, 0.004), 3: (1.0, 0.004)}   # de calibrar_ruido.py
LAB = {'H': 0, 'A': 1, 'D': 2}
GRID = list(itertools.product([5, 8, 12, 18, 25], [8, 12, 20, 40]))


def feats(g):
    return seg.features_v4(g, R_CONTROL, K_FRAMES)


def fit(games):
    X = np.vstack([g['X'][g['valid']][::3] for g in games])
    y = np.concatenate([g['y'][g['valid']][::3] for g in games])
    X, y = seg.mirror_v4(X, y)
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
                                          random_state=0).fit(X, y)


def logp(m, X):
    return np.log(np.clip(m.predict_proba(X), 1e-6, 1))


def main():
    print('cargando metrica (limpio + sucio)...')
    C = list(bench.games()); D = []
    for g in C:
        d = dict(g); d['B'] = seg.ensuciar_balon(g['B'], *RUIDO[g['g']], seed=g['g']); D.append(d)
    for g in C + D:
        g['X'] = feats(g); g['y'] = np.array([LAB.get(c, -1) for c in g['gt']])
    for g in C + D:   # ya no hacen falta las posiciones, solo las señales (ahorra memoria)
        for k in ('Ph', 'Pa', 'B', 'e', 'sp'): g.pop(k, None)

    print('eligiendo costos con prueba cruzada en el banco sucio...')
    oof = {}
    for i in range(len(C)):
        tr = [D[j] for j in range(len(C)) if j != i] + [C[j] for j in range(len(C)) if j != i]
        oof[i] = logp(fit(tr), D[i]['X'])

    def dec(g, lp, c):
        p = seg.viterbi(lp, *c); p[~g['valid']] = 'X'; return p
    S = {c: [bench.score(D[i]['gt'], dec(D[i], oof[i], c))[0] for i in range(len(C))] for c in GRID}
    best = max(GRID, key=lambda c: np.mean(S[c]))
    print('  costos', best, 'spellF1 fuera de muestra (sucio) por juego',
          ' '.join('%.3f' % s for s in S[best]), 'promedio %.3f' % np.mean(S[best]))

    print('entrenando con todo y aplicando a BAR-ATH...')
    m = fit(C + D)
    del C, D, oof
    import load_atd
    L, W = seg.L, seg.W
    ds = load_atd.load(); df = ds.to_df(engine='pandas'); h, a = ds.metadata.teams
    xy = lambda t: np.stack([np.stack([df[f'{p.player_id}_x'], df[f'{p.player_id}_y']], -1) for p in t.players], 1)
    B = dict(n=len(df), Ph=xy(h) * [L, W], Pa=xy(a) * [L, W], B=np.stack([df.ball_x, df.ball_y], -1) * [L, W])
    del ds, df
    lab = seg.viterbi(logp(m, feats(B)), *best)
    os.makedirs(os.path.join(ROOT, 'outputs'), exist_ok=True)
    out = os.path.join(ROOT, 'outputs', 'v2_segmentos.csv')
    pd.DataFrame({'frame': np.arange(len(lab)), 'label': lab}).to_csv(out, index=False)
    print('listo', out)


if __name__ == '__main__':
    main()
