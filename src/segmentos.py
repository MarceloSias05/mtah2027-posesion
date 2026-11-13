"""modelo de segmentos: clasificador por frame (H/A/D) + viterbi que escoge la secuencia de
posesiones mas creible cobrando cada cambio.

el clasificador se entrena SOLO con los partidos de metrica. las señales son cosas que existen
igual en metrica y en BAR-ATH (posiciones de jugadores y balon), nada especifico de un partido.
"""
import numpy as np, pandas as pd

L, W = 105., 68.
CAP = 30.          # distancia maxima que nos importa (m), mas lejos da igual
WINS = (12, 25, 75)  # ventanas centradas de medio, 1 y 3 segundos


def _runlen(mask):
    """para cada frame, largo del tramo seguido de True en el que esta (0 si es False)"""
    n = len(mask); out = np.zeros(n, np.int32)
    if not mask.any(): return out
    d = np.diff(np.r_[0, mask.astype(np.int8), 0])
    st, en = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    for a, b in zip(st, en): out[a:b] = b - a
    return out


def _roll(x, w):
    """promedio centrado de +/- w frames ignorando nan"""
    s = pd.Series(x)
    return s.rolling(2 * w + 1, center=True, min_periods=1).mean().values


def features(Ph, Pa, B):
    """Ph, Pa: (n, jugadores, 2) en metros. B: (n, 2) en metros. regresa matriz (n, f)"""
    n = len(B)
    miss = np.isnan(B[:, 0])
    dh = np.nanmin(np.hypot(Ph[..., 0] - B[:, None, 0], Ph[..., 1] - B[:, None, 1]), 1)
    da = np.nanmin(np.hypot(Pa[..., 0] - B[:, None, 0], Pa[..., 1] - B[:, None, 1]), 1)
    dh = np.where(np.isnan(dh), CAP, np.minimum(dh, CAP))
    da = np.where(np.isnan(da), CAP, np.minimum(da, CAP))
    # velocidad del balon
    bv = np.r_[np.nan, np.hypot(*np.diff(B, axis=0).T)] * 25
    bv = np.where(np.isnan(bv), 0, np.minimum(bv, 40))
    # balon fuera de la cancha
    out = (~miss) & ((B[:, 0] < -0.5) | (B[:, 0] > L + 0.5) | (B[:, 1] < -0.5) | (B[:, 1] > W + 0.5))
    # velocidad media de los jugadores
    P = np.concatenate([Ph, Pa], 1)
    sp = np.nanmean(np.hypot(*np.moveaxis(np.diff(P, axis=0), 2, 0)), 1) * 25
    sp = pd.Series(np.r_[np.nan, sp]).rolling(25, center=True, min_periods=5).median().values
    sp = np.where(np.isnan(sp), 0, sp)
    run = _runlen(miss)
    closeh = ((dh < 1.5) & ~miss).astype(float); closea = ((da < 1.5) & ~miss).astype(float)
    homecloser = ((dh < da) & ~miss).astype(float); awaycloser = ((da < dh) & ~miss).astype(float)
    cols = [miss.astype(float), np.log1p(run), np.minimum(dh, CAP) * ~miss, np.minimum(da, CAP) * ~miss,
            (da - dh) * ~miss, bv, out.astype(float), sp]
    for w in WINS:
        cols += [_roll(miss.astype(float), w), _roll(closeh, w), _roll(closea, w),
                 _roll(homecloser, w), _roll(awaycloser, w), _roll(out.astype(float), w), _roll(bv, w)]
    return np.stack(cols, 1).astype(np.float32)


# indices de columnas que son "de un equipo", para el espejo home<->away
def _swap_index(nf):
    idx = list(range(nf))
    idx[2], idx[3] = 3, 2
    base = 8
    for k in range(len(WINS)):
        o = base + 7 * k
        idx[o + 1], idx[o + 2] = o + 2, o + 1
        idx[o + 3], idx[o + 4] = o + 4, o + 3
    return idx


def mirror(X, y):
    """aumenta los datos intercambiando home y away, asi el modelo no aprende 'el local la tiene mas'"""
    Xm = X[:, _swap_index(X.shape[1])].copy()
    Xm[:, 4] = -X[:, 4]
    ym = y.copy(); ym[y == 0] = 1; ym[y == 1] = 0
    return np.vstack([X, Xm]), np.r_[y, ym]


def viterbi(logp, c_switch, c_dead):
    """logp: (n, 3) log-prob de H, A, D. cambio H<->A cuesta c_switch, entrar/salir de D cuesta c_dead"""
    n = len(logp)
    T = np.array([[0, -c_switch, -c_dead], [-c_switch, 0, -c_dead], [-c_dead, -c_dead, 0]])
    score = logp[0].copy(); back = np.zeros((n, 3), np.int8)
    for t in range(1, n):
        cand = score[:, None] + T
        back[t] = cand.argmax(0)
        score = cand.max(0) + logp[t]
    path = np.zeros(n, np.int8); path[-1] = score.argmax()
    for t in range(n - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    return np.array(['H', 'A', 'D'])[path]


def features_con_histeresis(G):
    """señales + la salida de la regla de histeresis (one-hot H/A/D) como 3 columnas extra"""
    import histeresis as hyst
    h = hyst.hysteresis(G, 1.0, 8, 25)
    oh = np.stack([h == 'H', h == 'A', h == 'D'], 1).astype(np.float32)
    return np.hstack([features(G['Ph'], G['Pa'], G['B']), oh])


def mirror_full(X, y):
    nf = X.shape[1] - 3
    Xb, yb = mirror(X[:, :nf], y)
    return np.hstack([Xb, np.vstack([X[:, nf:], X[:, nf:][:, [1, 0, 2]]])]), yb
