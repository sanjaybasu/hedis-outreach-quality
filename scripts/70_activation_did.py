"""Earlier-vs-later autoSMS activation: Callaway-Sant'Anna target-trial DiD on HEDIS
gap-closure. Not-yet-activated controls, WITHIN measure, cumulative-closure absorbing
outcome, cohort-weighted event-study aggregation. Member-clustered bootstrap CIs,
per-measure parallel-pre-trends gate, gate-passing pooled ATT, Honest-DiD relative-
magnitude sensitivity. Aggregate output only.
"""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hedis_outreach.outreach import is_rct

D = os.environ.get("HEDIS_DATA_DIR", "data")
RES = os.path.join(os.path.dirname(__file__), "..", "results")
MAP = {"aap":"AAP","bcs":"BCS-E","ccs":"CCS-E","eed":"EED","diabetes":"GSD","wcv":"WCV"}
mi = lambda ts:(ts.dt.year-2025)*12+ts.dt.month
EMIN, EMAX, B = -4, 5, 300

def load():
    a=pd.read_parquet(f"{D}/autosms_assigned.parquet")
    a=a[(~a.campaign.map(is_rct))&(a.messaged.astype(int)==1)].copy()
    def meas(s):
        for t in MAP:
            if t in s.lower(): return MAP[t]
    a["measure"]=a.campaign.map(meas); a["act"]=pd.to_datetime(a.start_date,errors="coerce")
    a=a.dropna(subset=["measure","act"])
    xw=pd.read_parquet(f"{D}/xw_cuid_way.parquet")
    a=a.merge(xw,left_on="member_ident",right_on="cuid",how="inner")
    act=a.groupby(["way","measure"]).act.min().reset_index(); act["g"]=mi(act.act)
    act=act[(act.g>=1)&(act.g<=12)]
    cd=pd.read_parquet(f"{D}/hedis_closed_dates.parquet")
    cd=cd[(cd.gap_closed_date>=pd.Timestamp("2025-01-01"))&(cd.gap_closed_date<=pd.Timestamp("2025-12-31"))]
    cd=cd.assign(cm=mi(cd.gap_closed_date))[["way","measure","cm"]]
    d=act.merge(cd,on=["way","measure"],how="left").reset_index(drop=True)
    Y=np.zeros((len(d),13)); cm=d.cm.values
    for t in range(13): Y[:,t]=np.where(~np.isnan(cm)&(cm<=t),1.0,0.0)
    return d, Y

def es(g, Y, rows):
    """event-time ATT dict for a subset of row indices (one measure)."""
    gv=g[rows]; Yv=Y[rows]
    from collections import defaultdict
    num=defaultdict(float); den=defaultdict(float)
    for gc in [c for c in np.unique(gv) if 1<=c<=12]:
        base=gc-1; tr=gv==gc
        if tr.sum()<20: continue
        for t in range(13):
            e=t-gc
            if e<EMIN or e>EMAX: continue
            ctrl=gv>t
            if ctrl.sum()<20: continue
            att=(Yv[tr,t]-Yv[tr,base]).mean()-(Yv[ctrl,t]-Yv[ctrl,base]).mean()
            num[e]+=att*tr.sum(); den[e]+=tr.sum()
    return {e:num[e]/den[e] for e in num if den[e]>0}

def boot(d, Y, rows, rng):
    ways=d.way.values[rows]; uniq=np.unique(ways)
    samp=rng.choice(uniq,len(uniq),replace=True)
    idxmap={w:np.where(ways==w)[0] for w in uniq}
    take=np.concatenate([rows[idxmap[w]] for w in samp])
    return take

def main():
    d,Y=load(); g=d.g.values
    rng=np.random.default_rng(11)
    out={"by_measure":{}, "params":{"e_range":[EMIN,EMAX],"bootstrap":B}}
    passing=[]
    for m in sorted(d.measure.unique()):
        rows=np.where((d.measure==m).values)[0]
        nclosed=int(d.iloc[rows].cm.notna().sum())
        pt=es(g,Y,rows)
        if not pt: continue
        bs={e:[] for e in pt}
        for _ in range(B):
            tk=boot(d,Y,rows,rng); r=es(g,Y,tk)
            for e in pt:
                if e in r: bs[e].append(r[e])
        ci={e:(round(np.percentile(bs[e],2.5)*100,1),round(np.percentile(bs[e],97.5)*100,1)) for e in pt if bs[e]}
        pre=[e for e in pt if e<0]; post=[e for e in pt if e>=0]
        maxpre=max(abs(pt[e]) for e in pre)*100 if pre else np.nan
        pre_ok=all((ci[e][0]<=0<=ci[e][1]) for e in pre if e in ci) if pre else False
        postbs=[np.mean([bs[e][i] for e in post if i<len(bs[e])]) for i in range(B)] if post else []
        avgpost=np.mean([pt[e] for e in post])*100 if post else np.nan
        postci=(round(np.percentile(postbs,2.5)*100,1),round(np.percentile(postbs,97.5)*100,1)) if postbs else None
        gate = (nclosed>=30) and pre_ok and (maxpre<1.5)
        out["by_measure"][m]={"n_activated":len(rows),"n_closed":nclosed,
            "event_time_pp":{str(e):round(pt[e]*100,1) for e in sorted(pt)},
            "event_time_ci":{str(e):ci.get(e) for e in sorted(pt)},
            "max_pretrend_pp":round(maxpre,1),"pretrend_ci_covers_0":bool(pre_ok),
            "avg_post_ATT_pp":round(avgpost,1),"avg_post_ATT_ci":postci,
            "passes_gate":bool(gate)}
        if gate: passing.append(m)
    # gate-passing pooled event study
    rows=np.where(d.measure.isin(passing).values)[0]
    # pool within-measure ATTs (already within-measure in es via cohorts; measures pooled by weight)
    def pooled(rws):
        from collections import defaultdict
        num=defaultdict(float); den=defaultdict(float)
        for m in passing:
            r=rws[np.isin(d.way.values[rws],d.way.values) & (d.measure.values[rws]==m)]
            sub=rws[d.measure.values[rws]==m]
            pt=es(g,Y,sub)
            w=len(sub)
            for e,v in pt.items(): num[e]+=v*w; den[e]+=w
        return {e:num[e]/den[e] for e in num}
    pt=pooled(rows); bs={e:[] for e in pt}
    for _ in range(B):
        tk=boot(d,Y,rows,rng); r=pooled(tk)
        for e in pt:
            if e in r: bs[e].append(r[e])
    post=[e for e in pt if e>=0]; pre=[e for e in pt if e<0]
    postbs=[np.mean([bs[e][i] for e in post if i<len(bs[e])]) for i in range(B)]
    avgpost=np.mean([pt[e] for e in post])*100
    maxpre=max(abs(pt[e]) for e in pre)*100
    out["pooled_gatepassing"]={"measures":passing,
        "event_time_pp":{str(e):round(pt[e]*100,1) for e in sorted(pt)},
        "avg_post_ATT_pp":round(avgpost,1),
        "avg_post_ATT_ci":(round(np.percentile(postbs,2.5)*100,1),round(np.percentile(postbs,97.5)*100,1)),
        "max_pretrend_pp":round(maxpre,1),
        "honest_did_M_breakdown":round(avgpost/maxpre,1) if maxpre>0 else None}
    os.makedirs(RES,exist_ok=True); json.dump(out,open(f"{RES}/activation_did.json","w"),indent=2)
    print("PASSING GATE:",passing)
    print(json.dumps(out["pooled_gatepassing"],indent=1))
    for m in sorted(out["by_measure"]):
        b=out["by_measure"][m]
        print(f"  {m:6} post {b['avg_post_ATT_pp']:+5.1f} {b['avg_post_ATT_ci']} maxpre {b['max_pretrend_pp']} gate={b['passes_gate']} (nclose {b['n_closed']})")

if __name__=="__main__": main()
