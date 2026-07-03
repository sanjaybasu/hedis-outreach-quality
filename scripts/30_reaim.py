"""RE-AIM reach/response/closure-among-reached funnel. Aggregate output only."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from hedis_outreach import io
from hedis_outreach.reaim import funnel
DATA = os.environ.get("HEDIS_DATA_DIR", "data")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
rr = pd.read_parquet(os.path.join(DATA, "autosms_reach_response.parquet"))
gap = io.load("gap")
am = pd.read_parquet(os.path.join(DATA, "autosms_members.parquet"))
res = funnel(rr, gap, am)
os.makedirs(RESULTS, exist_ok=True)
json.dump(res, open(os.path.join(RESULTS, "reaim_funnel.json"), "w"), indent=2)
print(json.dumps(res["_total"], indent=2))
