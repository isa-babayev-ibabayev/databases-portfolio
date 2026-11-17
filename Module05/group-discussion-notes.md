# Module 5 — Group Discussion Notes

## Example Group Discussion

**Isa:** I checked the functional dependencies. I found that one job belongs to one machine, and each machine has one site.

**Arshia:** That makes sense. When we worked on the ER diagrams, we separated the data into different tables.

**Asmin:** Yes, I think the normalized design is clearer because we don't need to repeat the same information many times.

**Rayan:** I worked on building the database and comparing the query performance. We used 200,000 rows for our tests.

**Isa:** In my part, I compared the update costs. I found that changing one machine's site affected only one row in the normalized database, but 4,000 rows in the denormalized table.

**Rayan:** That's a big difference. But what about the query speed?

**Isa:** The normalized query was actually faster in my test. I also tried removing an index, and the reporting query became faster.

**Arshia:** That's interesting. I thought an index would always make queries faster.

**Asmin:** So which design should we use?

**Isa:** I think we should keep the normalized database for daily work. We can also use a separate reporting table when needed.

## My Discussion Notes

- We compared our work and talked about the advantages of normalization.
- We looked at how the ER diagrams help organize the data.
- Rayan's benchmark work helped us compare query performance.
- My update test showed why repeated data can cause problems.
- We discussed why indexes do not always improve performance.
- Our main conclusion was that both designs can be useful, depending on the task.

## What I Learned From the Group

I learned that database design is not only about making tables. We also need to think about updates, storage, and speed. Our different tasks helped us understand the topic from different sides. I found the discussion useful because we could compare our results.

---

**Source note:** The reflection, discussion notes, group-member names, and role allocation were supplied by the student for publication. The section labeled “Example Group Discussion” is illustrative and is not represented as an independently verified word-for-word transcript. No date, location, or attendance record is inferred.
