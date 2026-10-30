# Reflection 02 — Data Contracts and Reading Legacy Schemas

## Take-away

The biggest thing I learned is that a database can look okay and still give wrong answers. In the old maintenance data, job 1 had `P-1001,P-1002` in one field. A normal join could not match that text to one part number, so the job was missing from the result. Job 3 also pointed to `cnc-05`, even though that machine did not exist in the machine table. If I started again, I would check the real table definitions and try a few SQL queries before trusting the diagram. I also want to remember that keys and foreign keys are not just names. The database needs actual rules to protect its data.

## What was good?

I liked the small SQL examples because I could see what was wrong instead of only reading about it. The five queries in [our integrity audit](integrity-audit.sql) each show a different problem, and the [saved results](integrity-results.txt) make them easier to understand. The Machine–Sensor example was also helpful: it shows two sensors connected to one machine, and an invalid sensor reference gets rejected. The [contract tests](tests/test_contract.py) gave us another way to check the corrected design. The latest technical audit ran 11 tests and all passed. For my own study, I compared the queries with their saved results rather than claiming I personally ran every test.

## What was difficult?

At first, I mixed up entities, attributes and relationships. For example, I was not sure whether a maintenance job was just a connection between a machine and a technician. Now I understand why the job needs its own record, while its date is an attribute. I also found the 1:1 example confusing. A `UNIQUE` foreign key can stop two nameplates from pointing to the same machine, but it does not make every machine have a nameplate. Another confusing example was the price `9.90`. It looks like a number, but storing it as TEXT can make a price comparison behave differently. These examples helped me see that a diagram, a SQL table and the real business rule are not always the same thing.

## Exploration and show stoppers

The most interesting thing to explore was the difference between text and number comparisons in SQLite. The expression `'9.90' < '15'` gives a different answer from comparing the values as numbers. This was a good reminder to test a claim with a small example. I also looked at the optional EER material in the portfolio, where machine types can be stored in one table with a type column or in separate subtype tables. There was no major technical showstopper in the final audit, but there are still design questions. For example, should technician names really be `UNIQUE` when two people can have the same name? The audit also found that a job can accept a part number such as `P-ABC` even though the Part model rejects it. I would want to fix and test that in a later improvement.

## Interaction with peers and instructors

I worked with my Task Pod partner, Tunay Daldaban. On 15 October 2026, we had a 15-minute discussion about Module 2 because we had missed the class when the task was introduced. I also spent one hour studying the material myself. We reviewed each other's work on GitHub. Tunay looked at my ER models, integrity audit, and data contract, and I looked at his ER diagrams, SQL checks, and corrected schema. The reviews helped me think about whether my explanations were clear enough for another student to follow. We did not record a specific disagreement or a change requested by the other person, so I do not want to invent one. I later participated in a separate Module 3 query-plan discussion with students from another group, but that does not complete the missing Module 2 ER Task C activity. I do not have any individual instructor feedback to report for this module.

## How did you verify AI suggestions?

I used AI to get ideas about the hidden relationships in the old database and how to correct the comma-separated parts list. But I learned not to accept an explanation just because it sounds right. I looked at the SQL in [the integrity audit](integrity-audit.sql), compared it with [the recorded output](integrity-results.txt), and used the SQLite documentation to understand the results. One good example was the claim about prices stored as TEXT. Saying that text comparisons *always* fail is too general. In our example, `'9.90' < '15'` is false, while `CAST('9.90' AS NUMERIC) < 15` is true. The exact comparison matters. I also checked the explanation that a foreign key with `UNIQUE` means **at most one** nameplate, not automatically **exactly one**. The main lesson for me was to treat AI answers as suggestions and look for evidence before using them.

## Help and extra work

Tunay helped by reviewing my portfolio, and I gave something back by reviewing his work and commenting on the problems I understood, like duplicate part numbers and missing machine references. Our comments are available in [my review issue](https://github.com/isa-babayev-ibabayev/databases-portfolio/issues/2) and [Tunay's review issue](https://github.com/tunaydaldaban-beep/databases-portfolio/issues/2). Besides the main exercises, the portfolio includes extra material about EER inheritance and a [Mermaid diagram lab](mermaid-lab.md). I think those examples are useful because they show there can be more than one possible database design. The additional SQL results and tests also helped make the work easier to check. I still have things to improve, especially making the part-number rules consistent, but I now understand better why we should test a database model instead of trusting it only because the diagram looks correct.
