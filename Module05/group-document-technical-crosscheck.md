# Module 5 Group Document — Technical Cross-check

## Source boundary

The student identified the original provenance document as the ten-page `discuss(1).pdf` and
supplied its membership, role allocation, page topics, and relevant technical values in the final
publication instructions. The PDF binary was not present in the accessible attachment directory
or user folders during publication, so this document does not claim a fresh visual inspection of
the pages. It cross-checks the student-supplied PDF-derived facts against the executable portfolio.
The original PDF is not modified or published here.

## Group-work provenance

The supplied group document identifies these Module 5 pod roles:

| Member | Supplied assignment role |
|---|---|
| Isa Babayev | Round 1 functional dependencies; Round 5 update/query/storage/index measurements; Round 6 recommendation |
| Rayan Slassi | Round 1 LLM FD comparison; Round 3 build; Round 4 race/database performance |
| Arshia Ziaee | Round 1 before/after ER sketches with Asmin |
| Asmin Metin | Round 1 before/after ER sketches with Arshia |

This division of the shared assignment is provenance information. It does not imply that all four
people co-authored every script or document in Isa's personal repository. The student states that
Tunay was absent for this Module 5 session and is not credited with these roles.

## Functional-dependency discrepancy

The supplied PDF description includes `job_id → part_id` (the implemented column is named
`part_no`). That is not a valid dependency for this job-part model because one job contains ten
different parts. The executable data demonstrates this directly:

```sql
SELECT job_id, COUNT(DISTINCT part_no)
FROM flat_jobpart
GROUP BY job_id;
```

Every generated job has ten distinct parts. The intended candidate key for one job-part fact is
the composite `(job_id, part_no)`. Valid job-level dependencies include `job_id → machine_id`,
`job_id → technician`, and `job_id → done_on`; `part_no → part_price` is a part-level dependency.
The published README and normalization notes retain the verified dependency model rather than
copying the conflicting PDF statement.

## ER-diagram difference

The supplied PDF description says the conceptual normalized sketch includes a separate `SITE`
entity and a `quantity` attribute. That can be a defensible alternative design, but it is not the
schema executed by this portfolio. The implemented exercise has four core normalized tables:

```text
machine(machine_id, site)
part(part_no, part_price)
job(job_id, machine_id, technician, done_on)
job_part(job_id, part_no)
```

The implemented `machine` table stores `site` as an attribute, and `job_part` has no `quantity`
column. Therefore the group sketch is documented as a conceptual proposal, not as an exact diagram
of `setup.sql`.

## Benchmark-run separation

Timing results must remain grouped by run. They cannot be mixed into a synthetic benchmark.

| Measurement | PDF pages 8–9 values supplied by student | Preserved portfolio run | 2026-11-17 audit rerun |
|---|---:|---:|---:|
| Normalized dashboard | 133.246 ms | 121.0052 ms | 105.2740 ms |
| Indexed report dashboard | 162.708 ms | 151.9686 ms | 122.0734 ms |
| Normalized update | 0.850 ms | 1.2915 ms | 1.4530 ms |
| Denormalized update | 13.896 ms | 22.6925 ms | 10.1288 ms |
| Indexed report experiment | 165.748 ms | 137.1854 ms | 120.9963 ms |
| Unindexed report experiment | 108.326 ms | 112.1664 ms | 88.5278 ms |

The student reports that the PDF memo on page 10 contains other timing values, but those exact
values were not included in the accessible publication source. They are not guessed here. The
portfolio recommendation continues to cite the internally consistent preserved run in
`evidence/benchmark-results.json`.

All three listed runs support the same narrow conclusions:

- the normalized dashboard was faster than the indexed reporting query on that run;
- removing `ix_report_machine` improved this broad reporting aggregation;
- a site update changed one normalized row but 4,000 reporting rows;
- timing differences across runs are expected and do not change the deterministic row counts.

The evidence does not prove that normalized designs always query faster or that indexes are
generally harmful.

## Discussion-gate boundary

The supplied discussion notes support real conversation about dependencies, ER design, the
200,000-row build, query performance, update amplification, index behavior, and the architecture
recommendation. They do not specifically document every workbook gate question. In particular,
the exact neighboring-pod answer, anomaly challenge, ten-part gate, cross-pod plan comparison,
prediction exercise, literal “what if” defense, and curiosity swap are not all recoverable from
the supplied notes. Those individual gates remain “not specifically documented” rather than
being marked complete by inference.
