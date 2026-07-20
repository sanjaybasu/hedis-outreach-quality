"""Earlier-vs-later autoSMS activation: Callaway-Sant'Anna target-trial DiD on HEDIS
gap-closure. Not-yet-activated controls, WITHIN measure, cumulative-closure absorbing
outcome, cohort-weighted event-study aggregation. Member-clustered bootstrap CIs.

Identification gate is a MAGNITUDE criterion (matches the manuscript, which argues
against significance-testing pre-trends; Roth 2022): a measure is identified when
(1) largest pre-contact difference < 1.5 pp, (2) average post effect positive with
bootstrap CI excluding 0, (3) Honest-DiD relative-magnitude robustness M >= 3, and
(4) >= 30 dated closures. Pre-period CI coverage is reported for information only,
not used as a gate.

Also computes a BALANCED-COHORT event study (balance_e): restricts to contact-timing
cohorts observed at every event time in the window, so the dynamic path is not driven
by differential post-contact follow-up (administrative right-censoring) across cohorts.

Aggregate output only; no protected health information is written.
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
E_BAL = 4  # balanced-cohort horizon (months post-contact)

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

def es(g, Y, rows, gset=None, emax=EMAX):
    """event-time ATT dict for a subset of row indices (one measure).
    gset: restrict to these treatment cohorts (balanced-cohort event study).
    emax: maximum event time to include (balanced horizon)."""
    gv=g[rows]; Yv=Y[rows]
    from collections import defaultdict
    num=defaultdict(float); den=defaultdict(float)
    for gc in [c for c in np.unique(gv) if 1<=c<=12 and (gset is None or c in gset)]:
        base=gc-1; tr=gv==gc
        if tr.sum()<20: continue
        for t in range(13):
            e=t-gc
            if e<EMIN or e>emax: continue
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

def pooled_es(d, g, Y, rws, measures, gset=None, emax=EMAX):
    """cohort-weighted event-time ATTs pooled across measures (within-measure controls)."""
    from collections import defaultdict
    num=defaultdict(float); den=defaultdict(float)
    for m in measures:
        sub=rws[d.measure.values[rws]==m]
        pt=es(g,Y,sub,gset=gset,emax=emax); w=len(sub)
        for e,v in pt.items(): num[e]+=v*w; den[e]+=w
    return {e:num[e]/den[e] for e in num}

def summarize(d, g, Y, rows, measures, rng, gset=None, emax=EMAX):
    """point + member-clustered bootstrap for a pooled event study."""
    pt=pooled_es(d,g,Y,rows,measures,gset=gset,emax=emax)
    bs={e:[] for e in pt}
    for _ in range(B):
        tk=boot(d,Y,rows,rng); r=pooled_es(d,g,Y,tk,measures,gset=gset,emax=emax)
        for e in pt:
            if e in r: bs[e].append(r[e])
    post=[e for e in pt if e>=0]; pre=[e for e in pt if e<0]
    postbs=[np.mean([bs[e][i] for e in post if i<len(bs[e])]) for i in range(B)] if post else []
    avgpost=np.mean([pt[e] for e in post])*100 if post else float('nan')
    maxpre=max(abs(pt[e]) for e in pre)*100 if pre else float('nan')
    et_ci={str(e):(round(np.percentile(bs[e],2.5)*100,1),round(np.percentile(bs[e],97.5)*100,1)) for e in pt if bs[e]}
    return {"measures":list(measures),
        "event_time_pp":{str(e):round(pt[e]*100,1) for e in sorted(pt)},
        "event_time_ci":et_ci,
        "avg_post_ATT_pp":round(avgpost,1),
        "avg_post_ATT_ci":(round(np.percentile(postbs,2.5)*100,1),round(np.percentile(postbs,97.5)*100,1)) if postbs else None,
        "point_at_month4_pp":(round(pt[4]*100,1) if 4 in pt else None),
        "max_pretrend_pp":round(maxpre,1),
        "honest_did_M_breakdown":round(avgpost/maxpre,1) if maxpre>0 else None}

def main():
    d,Y=load(); g=d.g.values
    rng=np.random.default_rng(11)
    out={"by_measure":{}, "params":{"e_range":[EMIN,EMAX],"bootstrap":B,
        "gate":"magnitude: maxpre<1.5pp AND avg-post CI>0 AND M>=3 AND >=30 closures"}}
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
        maxpre=max(abs(pt[e]) for e in pre)*100 if pre else float('nan')
        pre_ok=all((ci[e][0]<=0<=ci[e][1]) for e in pre if e in ci) if pre else False
        postbs=[np.mean([bs[e][i] for e in post if i<len(bs[e])]) for i in range(B)] if post else []
        avgpost=np.mean([pt[e] for e in post])*100 if post else float('nan')
        postci=(round(np.percentile(postbs,2.5)*100,1),round(np.percentile(postbs,97.5)*100,1)) if postbs else None
        M=(avgpost/maxpre) if (maxpre and maxpre>0) else float('inf')
        effect_pos=bool(postci and postci[0]>0)
        # MAGNITUDE gate (matches manuscript; pre_ok reported but not gated)
        gate = (nclosed>=30) and (maxpre<1.5) and effect_pos and (M>=3)
        out["by_measure"][m]={"n_activated":len(rows),"n_closed":nclosed,
            "event_time_pp":{str(e):round(pt[e]*100,1) for e in sorted(pt)},
            "event_time_ci":{str(e):ci.get(e) for e in sorted(pt)},
            "max_pretrend_pp":round(maxpre,1),"pretrend_ci_covers_0":bool(pre_ok),
            "avg_post_ATT_pp":round(avgpost,1),"avg_post_ATT_ci":postci,
            "honest_did_M_breakdown":round(M,1) if np.isfinite(M) else None,
            "passes_gate":bool(gate)}
        if gate: passing.append(m)

    if passing:
        out["pooled_gatepassing"]=summarize(d,g,Y,
            np.where(d.measure.isin(passing).values)[0], passing, rng)
        # balanced-cohort event study: cohorts observed at every e in [EMIN, E_BAL]
        BAL=set(range(-EMIN, 12-E_BAL+1))  # e.g., {4,...,8} for EMIN=-4, E_BAL=4
        bal=summarize(d,g,Y, np.where(d.measure.isin(passing).values)[0], passing,
                      rng, gset=BAL, emax=E_BAL)
        bal["E_horizon"]=E_BAL; bal["balanced_cohorts"]=sorted(BAL)
        out["pooled_balanced_cohort"]=bal

    os.makedirs(RES,exist_ok=True); json.dump(out,open(f"{RES}/activation_did.json","w"),indent=2)
    print("PASSING GATE:",passing)
    print("UNBALANCED pooled:", json.dumps(out.get("pooled_gatepassing",{}),indent=1))
    print("BALANCED-COHORT pooled:", json.dumps(out.get("pooled_balanced_cohort",{}),indent=1))
    for m in sorted(out["by_measure"]):
        b=out["by_measure"][m]
        print(f"  {m:6} post {b['avg_post_ATT_pp']:+5} {b['avg_post_ATT_ci']} maxpre {b['max_pretrend_pp']} M {b['honest_did_M_breakdown']} gate={b['passes_gate']} (nclose {b['n_closed']})")

if __name__=="__main__": main()
