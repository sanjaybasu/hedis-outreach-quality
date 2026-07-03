"""Gap-status volatility (open-gap span churn). Aggregate output only."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from hedis_outreach.spans import churn
DATA = os.environ.get("HEDIS_DATA_DIR", "data")
RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
s = pd.read_parquet(os.path.join(DATA, "spans.parquet"))
res = churn(s)
os.makedirs(RESULTS, exist_ok=True)
json.dump(res, open(os.path.join(RESULTS, "span_churn.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
