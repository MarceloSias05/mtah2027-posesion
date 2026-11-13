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


def features_con_histeresis(G, r=1.0, k=8):
    """señales + la salida de la regla de histeresis (one-hot H/A/D) como 3 columnas extra"""
    import histeresis as hyst
    h = hyst.hysteresis(G, r, k, 25)
    oh = np.stack([h == 'H', h == 'A', h == 'D'], 1).astype(np.float32)
    return np.hstack([features(G['Ph'], G['Pa'], G['B']), oh])


def mirror_full(X, y):
    nf = X.shape[1] - 3
    Xb, yb = mirror(X[:, :nf], y)
    return np.hstack([Xb, np.vstack([X[:, nf:], X[:, nf:][:, [1, 0, 2]]])]), yb


def shape_features(Ph, Pa):
    """forma de los equipos, sin balon. el que ataca se abre, se estira y avanza.
    la direccion de ataque se saca sola: en una ventana larga (2 min) el equipo con el
    centroide mas a la izquierda ataca hacia la derecha (cambia sola en el medio tiempo).
    columnas en pares (home, away) para poder voltearlas"""
    def stats(P):
        cx = np.nanmean(P[..., 0], 1); cy = np.nanmean(P[..., 1], 1)
        return cx, np.nanstd(P[..., 1], 1), np.nanstd(P[..., 0], 1)
    cxh, wh, lh = stats(Ph); cxa, wa, la = stats(Pa)
    long_ = lambda x: pd.Series(x).rolling(3000, center=True, min_periods=250).mean().values
    dirh = np.sign(long_(cxa) - long_(cxh)); dirh = np.where(np.isnan(dirh) | (dirh == 0), 1, dirh)
    advh = (cxh - long_(cxh)) * dirh            # que tan adelantado va home vs su posicion normal
    adva = (cxa - long_(cxa)) * -dirh
    vh = pd.Series(np.r_[0, np.diff(cxh)] * 25 * dirh).rolling(25, center=True, min_periods=1).mean().values
    va = pd.Series(np.r_[0, np.diff(cxa)] * 25 * -dirh).rolling(25, center=True, min_periods=1).mean().values
    sm = lambda x: pd.Series(x).rolling(25, center=True, min_periods=1).mean().values
    cols = [sm(advh), sm(adva), sm(wh), sm(wa), sm(lh), sm(la), vh, va,
            sm(wh * lh), sm(wa * la)]
    X = np.stack(cols, 1).astype(np.float32)
    return np.nan_to_num(X)


def features_v2(G):
    """[señales base | forma de equipos | histeresis one-hot]"""
    import histeresis as hyst
    h = hyst.hysteresis(G, 1.0, 8, 25)
    oh = np.stack([h == 'H', h == 'A', h == 'D'], 1).astype(np.float32)
    return np.hstack([features(G['Ph'], G['Pa'], G['B']), shape_features(G['Ph'], G['Pa']), oh])


def mirror_v2(X, y):
    nb = X.shape[1] - 3 - 10
    Xb, yb = mirror(X[:, :nb], y)
    S = X[:, nb:nb + 10]; Sm = S[:, [1, 0, 3, 2, 5, 4, 7, 6, 9, 8]]
    O = X[:, nb + 10:]; Om = O[:, [1, 0, 2]]
    return np.hstack([Xb, np.vstack([S, Sm]), np.vstack([O, Om])]), yb


def _since(mask):
    """frames desde la ultima vez que mask fue True (hacia atras) y hasta la proxima (hacia adelante)"""
    n = len(mask); idx = np.arange(n)
    last = np.where(mask, idx, -10**6); last = np.maximum.accumulate(last)
    nxt = np.where(mask, idx, 10**7); nxt = np.minimum.accumulate(nxt[::-1])[::-1]
    return np.minimum(idx - last, 3000), np.minimum(nxt - idx, 3000)


def touch_features(Ph, Pa, B, r=1.0):
    """tiempo desde el ultimo control y hasta el proximo de cada equipo, y patadas (cambios bruscos
    de velocidad del balon). columnas en pares (home, away) salvo las ultimas 2"""
    miss = np.isnan(B[:, 0])
    dh = np.nanmin(np.hypot(Ph[..., 0] - B[:, None, 0], Ph[..., 1] - B[:, None, 1]), 1)
    da = np.nanmin(np.hypot(Pa[..., 0] - B[:, None, 0], Pa[..., 1] - B[:, None, 1]), 1)
    ch = (~miss) & (dh < r); ca = (~miss) & (da < r)
    bh, fh = _since(ch); ba, fa = _since(ca)
    v = np.r_[0, np.hypot(*np.diff(B, axis=0).T)] * 25
    acc = np.abs(np.r_[0, np.diff(np.nan_to_num(v))]); acc = np.where(miss, 0, np.minimum(acc, 30))
    kick = pd.Series(acc).rolling(13, center=True, min_periods=1).max().values
    lg = lambda x: np.log1p(x.astype(np.float32))
    X = np.stack([lg(bh), lg(ba), lg(fh), lg(fa), lg(bh) - lg(ba), lg(fh) - lg(fa), acc, kick], 1)
    return X.astype(np.float32)


def features_v3(G, r=1.0, k=8):
    """[señales base | toques | histeresis one-hot]"""
    import histeresis as hyst
    h = hyst.hysteresis(G, r, k, 25)
    oh = np.stack([h == 'H', h == 'A', h == 'D'], 1).astype(np.float32)
    return np.hstack([features(G['Ph'], G['Pa'], G['B']), touch_features(G['Ph'], G['Pa'], G['B'], r), oh])


def mirror_v3(X, y):
    nb = X.shape[1] - 3 - 8
    Xb, yb = mirror(X[:, :nb], y)
    T = X[:, nb:nb + 8]; Tm = T[:, [1, 0, 3, 2, 4, 5, 6, 7]].copy(); Tm[:, 4] = -T[:, 4]; Tm[:, 5] = -T[:, 5]
    O = X[:, nb + 8:]; Om = O[:, [1, 0, 2]]
    return np.hstack([Xb, np.vstack([T, Tm]), np.vstack([O, Om])]), yb


def place_features(B):
    """donde esta el balon respecto a las lineas, y en que parte del hueco sin balon va el frame.
    no dependen de que equipo es (no se voltean)"""
    miss = np.isnan(B[:, 0])
    # ultima posicion conocida del balon (para los frames sin balon)
    lastB = pd.DataFrame(B).ffill().bfill().values
    dside = np.minimum(lastB[:, 1], W - lastB[:, 1])
    dgoal = np.minimum(lastB[:, 0], L - lastB[:, 0])
    seen = ~miss
    bs, fs = _since(seen)
    lg = lambda x: np.log1p(np.maximum(x, 0).astype(np.float32))
    return np.stack([np.clip(dside, -5, 40), np.clip(dgoal, -5, 60), lg(bs), lg(fs)], 1).astype(np.float32)


def features_v4(G, r=1.0, k=8):
    return np.hstack([features_v3(G, r, k), place_features(G['B'])])


def mirror_v4(X, y):
    A = X[:, -4:]
    Xm, ym = mirror_v3(X[:, :-4], y)
    return np.hstack([Xm, np.vstack([A, A])]), ym


def ensuciar_balon(B, s_lento, s_temblor, seed=0):
    """le mete al balon dos tipos de error: uno lento (corrido unos metros, cambia en ~1 s) y uno
    rapido (temblor frame a frame). sirve para que metrica se parezca al tracking automatico."""
    rng = np.random.default_rng(seed)
    n = len(B)
    lento = rng.normal(0, 1, (n + 50, 2))
    for _ in range(4):   # 4 pasadas de promedio = curva suave, sin brincos frame a frame
        lento = pd.DataFrame(lento).rolling(50, center=True, min_periods=1).mean().values
    lento = lento[25:n + 25]
    lento = lento / lento.std(0) * s_lento
    return B + lento + rng.normal(0, s_temblor, (n, 2))


def stats_balon(Ph, Pa, B):
    """mediana de distancia balon-jugador mas cercano y mediana del 'temblor' (acc por frame)"""
    m = ~np.isnan(B[:, 0])
    dh = np.nanmin(np.hypot(Ph[..., 0] - B[:, None, 0], Ph[..., 1] - B[:, None, 1]), 1)
    da = np.nanmin(np.hypot(Pa[..., 0] - B[:, None, 0], Pa[..., 1] - B[:, None, 1]), 1)
    v = np.r_[0, np.hypot(*np.diff(B, axis=0).T)] * 25
    acc = np.abs(np.r_[0, np.diff(v)])
    return float(np.nanmedian(np.fmin(dh, da)[m])), float(np.nanmedian(acc))
