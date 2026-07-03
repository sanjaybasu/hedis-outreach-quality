-- Member x measure HEDIS numerator qualifying-event (closure) dates, all six measures.
-- Source: dbt_mgoldhirsh per-measure numerator tables (person_id = HEDIS "WAY" id).
-- Union across: br__hedis_aap_numerator, br__hedis_bcs_numerator, br__hedis_ccse_numerator,
--   hedis__eed_numerator, br__hedis_gsd_numerator, quality_measures__int_wcv_numerator.
select person_id as way, gap_closed_date, '<MEASURE>' as measure
from dbt_mgoldhirsh.<numerator_table>
where gap_closed_date is not null;
