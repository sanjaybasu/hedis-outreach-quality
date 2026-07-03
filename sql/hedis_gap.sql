-- Member x measure-year HEDIS gaps with open/closed status and attribution flags.
-- Source schema is a Postgres HEDIS mart; adjust schema name to the local environment.
select *
from python_pipeline.hedis_gap;
