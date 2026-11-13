# entrega v3 (bitacora 10)
# igual que la v2 (señales base + toques + lugar, radio 2.5 m / 18 frames) pero:
#  - entrena con metrica limpio + 3 tipos de ensuciado: suave (corrimiento + temblor, igual a la v2),
#    saltos (el tracker se confunde de objeto) y huecos extra en juego vivo
#  - costos del viterbi fijos en (25, 40): son los que mejor aguantan un ruido que el modelo no vio
#    (minimo entre el banco sucio y un banco de ruido mas fuerte y mezclado, ver bitacora 10)
# uso: python src/generar_v3.py   -> outputs/v3_segmentos.csv
import os, sys, gc, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'starter')); sys.path.insert(0, ROOT)
from sklearn.ensemble import HistGradientBoostingClassifier
import banco_metrica as bench, segmentos as seg

R_CONTROL, K_FRAMES = 2.5, 18
COSTOS = (25, 40)                                   # cambio H<->A, entrar/salir de D
LENTO = {1: 1.25, 2: 1.25, 3: 1.0}                  # de calibrar_ruido.py
VARIANTES = {
    'limpio': lambda g: {},
    'suave':  lambda g: {'lento': LENTO[g], 'temblor': 0.004},
    'saltos': lambda g: {'lento': LENTO[g], 'temblor': 0.004, 'saltos': (1 / 750, 4.0)},
    'huecos': lambda g: {'lento': LENTO[g], 'temblor': 0.004, 'huecos': 1 / 500},
}
LAB = {'H': 0, 'A': 1, 'D': 2}


def main():
    print('cargando metrica y armando las variantes...')
    Xs, ys = [], []
    for g in bench.games():
        y = np.array([LAB.get(c, -1) for c in g['gt']])
        for name, spec in VARIANTES.items():
            x = dict(g); x['B'] = seg.ruido(g['B'], spec(g['g']), seed=g['g'] * 10 + len(name))
            X = seg.features_v4(x, R_CONTROL, K_FRAMES)
            Xs.append(X[g['valid']][::3]); ys.append(y[g['valid']][::3])
        del g, x; gc.collect()
    X, y = seg.mirror_v4(np.vstack(Xs), np.concatenate(ys)); del Xs, ys
    print('entrenando...')
    m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31,
                                       random_state=0).fit(X, y)
    del X, y; gc.collect()
    print('aplicando a BAR-ATH...')
    import load_atd
    L, W = seg.L, seg.W
    ds = load_atd.load(); df = ds.to_df(engine='pandas'); h, a = ds.metadata.teams
    xy = lambda t: np.stack([np.stack([df[f'{p.player_id}_x'], df[f'{p.player_id}_y']], -1) for p in t.players], 1)
    B = dict(n=len(df), Ph=xy(h) * [L, W], Pa=xy(a) * [L, W], B=np.stack([df.ball_x, df.ball_y], -1) * [L, W])
    del ds, df
    lp = np.log(np.clip(m.predict_proba(seg.features_v4(B, R_CONTROL, K_FRAMES)), 1e-6, 1))
    lab = seg.viterbi(lp, *COSTOS)
    os.makedirs(os.path.join(ROOT, 'outputs'), exist_ok=True)
    out = os.path.join(ROOT, 'outputs', 'v3_segmentos.csv')
    pd.DataFrame({'frame': np.arange(len(lab)), 'label': lab}).to_csv(out, index=False)
    print('listo', out)


if __name__ == '__main__':
    main()
