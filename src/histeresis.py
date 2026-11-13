import numpy as np
import banco_metrica as bench
def hysteresis(G, r=2.0, k=8, dgap=25):
    """Dueno = equipo del jugador mas cercano si esta a < r m. Solo cambia de equipo si el otro
    controla k frames seguidos. D si el balon falta mas de dgap frames seguidos."""
    code,dh,da=bench.nearest(G); n=G['n']
    ctrl=np.full(n,-1,np.int8)
    ok=code>=0
    close=np.where(code==0,dh,da)
    ctrl[ok&(close<r)]=code[ok&(close<r)]
    # ball missing runs
    miss=np.isnan(G['B'][:,0]); run=np.zeros(n,int); i=0
    while i<n:
        if miss[i]:
            j=i
            while j<n and miss[j]: j+=1
            run[i:j]=j-i; i=j
        else: i+=1
    lab=np.full(n,'D',dtype='<U1'); cur=-1; cand=-1; cnt=0
    for f in range(n):
        if miss[f] and run[f]>dgap: cur=-1; lab[f]='D'; cnt=0; continue
        c=ctrl[f]
        if c>=0 and c!=cur:
            if c==cand: cnt+=1
            else: cand=c; cnt=1
            if cnt>=k or cur==-1: cur=c; cnt=0
        elif c==cur: cnt=0
        lab[f]='D' if cur==-1 else ('H' if cur==0 else 'A')
    return lab
