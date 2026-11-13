"""Baja los 7 partidos abiertos de la DFL (IDSSE, Bassek et al. 2025, CC-BY 4.0) y los guarda
comprimidos para el banco de pruebas.

Por que estos datos: el tracking oficial de la DFL trae por cada frame si el balon esta vivo o
muerto y que equipo lo tiene. Es la misma forma en que Metrica arma el ground truth del reto
(D donde su tracking corregido dice muerto, si no el equipo dueño). Con metrica teniamos que
sacarlo de los eventos.

Credito obligatorio (CC-BY 4.0): Deutsche Fussball Liga (DFL), y
Bassek, M., Rein, R., Weber, H., Memmert, D. (2025). An integrated dataset of spatiotemporal and
event data in elite soccer. Scientific Data, 12(1), 195. https://doi.org/10.1038/s41597-025-04505-y

Se corre donde haya internet (desde la nube del asistente figshare esta bloqueado):
    pip install kloppy==3.18.0 numpy pandas
    python tools/preparar_dfl.py
Sale data_externa/dfl/<match_id>.npz (unos 10-20 MB cada uno). Tarda varios minutos por partido
porque los XML de tracking son grandes.
"""
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data_externa', 'dfl')
IDS = ['J03WMX', 'J03WN1', 'J03WOH', 'J03WOY', 'J03WPF', 'J03WPY', 'J03WQF']
L, W = 105.0, 68.0


def preparar(match_id):
    from kloppy import sportec
    ds = sportec.load_open_tracking_data(match_id=match_id, coordinates='metrica', only_alive=False)
    df = ds.to_df(engine='pandas')
    home, away = ds.metadata.teams
    pitch = ds.metadata.pitch_dimensions
    xy = lambda t: np.stack([np.stack([df.get(f'{p.player_id}_x', np.nan * np.ones(len(df))),
                                       df.get(f'{p.player_id}_y', np.nan * np.ones(len(df)))], -1)
                             for p in t.players], 1)
    Ph = (xy(home) * [L, W]).astype(np.float16)
    Pa = (xy(away) * [L, W]).astype(np.float16)
    B = (np.stack([df.ball_x, df.ball_y], -1) * [L, W]).astype(np.float32)
    state = np.array([str(s).lower() for s in df.ball_state])
    owner = df.ball_owning_team_id.astype(str).values
    lab = np.full(len(df), 'D', dtype='<U1')
    alive = np.char.find(state, 'alive') >= 0
    lab[alive & (owner == str(home.team_id))] = 'H'
    lab[alive & (owner == str(away.team_id))] = 'A'
    period = df.period_id.values.astype(np.int8)
    frame = df.frame_id.values.astype(np.int64)
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(os.path.join(OUT, match_id + '.npz'), Ph=Ph, Pa=Pa, B=B, lab=lab,
                        period=period, frame=frame)
    vals, cnt = np.unique(lab, return_counts=True)
    print('  frames %d  jugadores %d/%d  balon visible %.3f  etiquetas %s  pitch %s' % (
        len(df), Ph.shape[1], Pa.shape[1], np.mean(~np.isnan(B[:, 0])),
        dict(zip(vals.tolist(), (cnt / cnt.sum()).round(3).tolist())), pitch), flush=True)


def main():
    ids = sys.argv[1:] or IDS
    for mid in ids:
        dst = os.path.join(OUT, mid + '.npz')
        if os.path.exists(dst):
            print(mid, 'ya estaba'); continue
        t0 = time.time(); print(mid, 'bajando y procesando...', flush=True)
        try:
            preparar(mid)
            print('  listo en %.0f s' % (time.time() - t0))
        except Exception as e:
            print('  ERROR con', mid, ':', repr(e))
    print('\nlisto. comprime la carpeta data_externa/dfl y pasala:')
    print('  cd', ROOT, '&& zip -r dfl.zip data_externa/dfl')


if __name__ == '__main__':
    main()
