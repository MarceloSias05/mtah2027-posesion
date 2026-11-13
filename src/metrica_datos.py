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
