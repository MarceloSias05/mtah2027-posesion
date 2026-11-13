"""Banco de pruebas en los partidos publicos de Metrica: GT de posesion sacado de sus eventos,
el mismo scorer del reto. Aqui se calibra todo, nunca en BAR-ATH."""
import sys, numpy as np, pandas as pd
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(ROOT,'evaluation'))
import possession_metrics as pm
L,W=105.,68.
import metrica_datos as md

def gt_labels(e,n,dead,valid):
    lab=np.full(n,'X',dtype='<U1')
    keep=e[e.Type.isin(['PASS','RECOVERY','SET PIECE','SHOT','BALL LOST','BALL OUT'])].sort_values('Start Frame')
    cur=None; idx=0; ev=keep[['Start Frame','Team']].values
    team=np.full(n,'',dtype=object)
    j=0
    for f in range(n):
        while j<len(ev) and ev[j][0]-1<=f: cur=ev[j][1]; j+=1
        team[f]=cur
    lab[valid]=np.where(team[valid]=='Home','H','A')
    lab[dead&valid]='D'
    return lab

def score(gt,pred):
    g=pm.label_codes(gt); p=pm.label_codes(pred); runs=pm.valid_runs(g)
    filled=pm.fill_abstentions(p,runs)
    cm=pm.scored_confusion(pm.confusion(g,p))
    s=pm.spell_scores(g,filled,runs)
    return s['mean_f1'], pm.macro_f1(cm), s['n_gt'], s['n_pred']

def games():
    for g in (1,2):
        h,a,e=md.load(g); n=len(h)
        Ph=h[[c for c in h.columns if c.startswith('Player')]].values.reshape(n,-1,2)*[L,W]
        Pa=a[[c for c in a.columns if c.startswith('Player')]].values.reshape(n,-1,2)*[L,W]
        B=h[['Ball_x','Ball_y']].values*[L,W]
        P=np.concatenate([Ph,Pa],1)
        sp=np.nanmean(np.hypot(*np.moveaxis(np.diff(P,axis=0),2,0)),1)*25
        sp=pd.Series(np.r_[np.nan,sp]).rolling(25,center=True,min_periods=5).median().values
        valid=~np.isnan(sp)
        dead=md.dead_mask(e,n,None)
        yield dict(g=g,n=n,Ph=Ph,Pa=Pa,B=B,sp=sp,valid=valid,dead=dead,gt=gt_labels(e,n,dead,valid),e=e)

def nearest(G):
    dh=np.nanmin(np.hypot(*np.moveaxis(G['Ph']-G['B'][:,None],2,0)),1)
    da=np.nanmin(np.hypot(*np.moveaxis(G['Pa']-G['B'][:,None],2,0)),1)
    code=np.full(G['n'],-1,np.int8); ok=~np.isnan(G['B'][:,0])
    code[ok]=np.where(dh[ok]<=da[ok],0,1)
    return code,dh,da

def smooth(code,w):
    hc=np.r_[0,np.cumsum(code==0)]; ac=np.r_[0,np.cumsum(code==1)]
    i=np.arange(len(code)); lo=np.maximum(0,i-w); hi=np.minimum(len(code),i+w+1)
    h=hc[hi]-hc[lo]; a=ac[hi]-ac[lo]
    lab=np.full(len(code),'D',dtype='<U1'); s=(h+a)>0
    lab[s]=np.where(h[s]>=a[s],'H','A'); return lab
