"""carga los partidos 1 y 2 de metrica y saca cuando esta muerto el balon a partir de sus eventos
(desde BALL OUT, falta o gol hasta el siguiente SET PIECE)"""
import os, sys
import numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L,W=105.,68.
def load(g):
    base=os.path.join(ROOT,'data_externa','metrica','data')+f'/Sample_Game_{g}/Sample_Game_{g}_'
    def trk(side):
        t=pd.read_csv(base+f'RawTrackingData_{side}_Team.csv',skiprows=2)
        cols=list(t.columns); new=[]
        for i,c in enumerate(cols):
            if c.startswith('Player') or c=='Ball': new.append(c+'_x')
            elif c.startswith('Unnamed'): new.append(new[-1][:-2]+'_y')
            else: new.append(c)
        t.columns=new; return t
    h,a=trk('Home'),trk('Away'); e=pd.read_csv(base+'RawEventsData.csv')
    return h,a,e
def dead_mask(e,n,period):
    dead=np.zeros(n+2,bool)
    e=e.sort_values('Start Frame').reset_index(drop=True)
    stop_types={'BALL OUT'}; 
    for i,r in e.iterrows():
        stop=None
        if r.Type=='BALL OUT': stop=r['End Frame'] if r['End Frame']>0 else r['Start Frame']
        elif r.Type=='FAULT RECEIVED': stop=r['Start Frame']
        elif r.Type=='SHOT' and isinstance(r.Subtype,str) and 'GOAL' in r.Subtype and 'OFF' not in r.Subtype: stop=r['End Frame']
        if stop is None: continue
        nxt=e[(e['Start Frame']>stop)&(e.Type=='SET PIECE')]
        if len(nxt)==0: continue
        dead[int(stop):int(nxt['Start Frame'].iloc[0])]=True
    return dead[1:n+1]


def load_game3():
    """juego 3 viene en otro formato: tracking EPTS (igual que el reto) + eventos en json.
    regresa (Ph, Pa, B, eventos) con eventos en las mismas columnas que los juegos 1 y 2"""
    import json
    from kloppy import metrica
    base = os.path.join(ROOT, 'data_externa', 'metrica', 'data', 'Sample_Game_3') + '/Sample_Game_3_'
    ds = metrica.load_tracking_epts(meta_data=base + 'metadata.xml', raw_data=base + 'tracking.txt')
    df = ds.to_df(engine='pandas')
    home, away = ds.metadata.teams
    xy = lambda t: np.stack([np.stack([df[f'{p.player_id}_x'], df[f'{p.player_id}_y']], -1) for p in t.players], 1)
    B = np.stack([df.ball_x, df.ball_y], -1)
    frames = df.frame_id.values
    ev = json.load(open(base + 'events.json'))['data']
    def sub(e):
        s = e.get('subtypes')
        if not s: return np.nan
        s = s if isinstance(s, list) else [s]
        return '-'.join(x['name'] for x in s)
    home_name = home.name
    rows = [dict(Team='Home' if e['team']['name'] == home_name else 'Away', Type=e['type']['name'],
                 Subtype=sub(e), Period=e['period'],
                 **{'Start Frame': e['start']['frame'], 'End Frame': e['end']['frame'] or 0}) for e in ev]
    return xy(home), xy(away), B, pd.DataFrame(rows), frames, home_name
