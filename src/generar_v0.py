# genera la entrega v0 para BAR-ATH con la regla de histeresis
# parametros calibrados en metrica (src/calibrar_histeresis.py), no en este partido
# uso: python src/generar_v0.py   -> outputs/v0_histeresis.csv
import os, sys
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'starter')); sys.path.insert(0, ROOT)
import load_atd, histeresis as hyst
R_CONTROL, K_FRAMES, DGAP = 1.0, 8, 25       # de metrica, mejor promedio en los 2 juegos
L, W = 105., 68.
ds = load_atd.load(); df = ds.to_df(engine='pandas'); h, a = ds.metadata.teams
xy = lambda team: np.stack([np.stack([df[f'{p.player_id}_x'], df[f'{p.player_id}_y']], -1) for p in team.players], 1)
G = dict(n=len(df), Ph=xy(h) * [L, W], Pa=xy(a) * [L, W], B=np.stack([df.ball_x, df.ball_y], -1) * [L, W])
lab = hyst.hysteresis(G, R_CONTROL, K_FRAMES, DGAP)
os.makedirs(os.path.join(ROOT, 'outputs'), exist_ok=True)
out = os.path.join(ROOT, 'outputs', 'v0_histeresis.csv')
pd.DataFrame({'frame': np.arange(len(lab)), 'label': lab}).to_csv(out, index=False)
print('listo', out)
