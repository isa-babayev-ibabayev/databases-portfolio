# Reflection 05 — Normalization vs. Denormalization

## Take-away

I learned that normalization helps us avoid repeating the same data. Denormalization can make some queries easier, but it is not always faster. I think it is better to test both methods before choosing one.

## What was good?

I liked comparing the two database designs. The results showed that changing one value affected only one row in the normalized database, but 4,000 rows in the denormalized table. This example helped me understand normalization better.

## What was difficult?

At first, I thought the denormalized database would be faster because it uses fewer joins. But the results were different. It was a little difficult to understand why, especially when looking at query plans.

## Exploration and show stoppers

I found it interesting that removing an index made one query faster. I did not expect this result. It helped me understand that indexes do not always improve performance.

## Interaction with peers and instructors

I discussed Module 5 with my groupmates. We talked about normalization, denormalization, and database performance. It was useful to share ideas and discuss the results together.

## How did you verify AI suggestions?

I used AI to help me understand some SQL queries and database concepts. I checked the technical results using SQL tests and actual measurements. I learned that AI answers should always be checked because they may not be correct.

## Help and extra work

I also worked on additional tests and prepared results for the module. I checked the database tables, query performance, and SQL outputs. This extra work helped me understand the topic better.
