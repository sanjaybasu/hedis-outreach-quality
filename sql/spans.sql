-- Attribution-validity spans per member with per-measure open-gap flags over time.
-- Used to reconstruct eligibility restatement (reattribution) rather than relying on
-- a point-in-time scored file.
select *
from python_pipeline.hedis_historical_spans;
