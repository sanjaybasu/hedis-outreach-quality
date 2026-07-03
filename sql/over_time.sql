-- Daily numerator/denominator by payer x measure x measurement year.
-- Basis for year-over-year closure trajectories and glide-path comparisons.
select *
from python_pipeline.hedis_over_time_df;
