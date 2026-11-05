# Reflection 05 — Technical Evidence Outline

This is evidence for a future personal reflection, not a final reflection and
not a record of classroom participation.

## Supported technical learning

- The flat table repeated machine sites, technicians, and prices and therefore
  produced update, insert, and delete anomalies.
- 2NF moved part price away from the composite job-part key; 3NF moved site to
  the machine table.
- The generated workload contained 200,000 rows but only 10 parts because `k`
  ran from 1 through 10.
- The normalized and report dashboard queries produced the same 350 groups.
- Denormalization did not automatically improve the measured query. The indexed
  report was slower than the normalized join on the saved run.
- One site fact required one normalized update but 4,000 report-row updates.
- The report table used substantially more storage because it repeated data.
- Removing an index improved this broad aggregation on the recorded system.

## Personal information still needed

- Which result was most surprising or difficult for the student?
- Which experiment was performed or explained personally during class?
- Did any round gate occur with a nearest pod, and what genuine answer was
  received?
- Which prepared curiosity was actually shared, if any?
- Which AI suggestion required correction or extra verification?
