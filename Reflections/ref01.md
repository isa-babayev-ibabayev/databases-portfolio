# Reflection 1 – Module 1: Introduction and Local-First Databases

## 1. What is your take-away, what do you want to remember, and what would be your advice?

The most important thing I learned in this module is that not every database application requires a dedicated server. SQLite is a lightweight and powerful solution that can handle a significant amount of data locally.

Another important takeaway is that AI-generated SQL should not automatically be considered correct. It is necessary to verify the results, understand the query execution plan, and test different conditions.

My advice would be to test every query, document the results properly, and make the work reproducible so that other people can understand and verify it.

## 2. What was good?

- Successfully setting up the Python environment using `uv`.
- Learning how to organize and document a project using GitHub and Markdown.
- Completing SQL Island and receiving the completion certificate.
- Generating and importing 172,800 industrial machine telemetry records into SQLite.
- Using SQL queries to analyze machine vibration, spindle load and alarm conditions.
- Understanding the differences between embedded and server-based databases.
- Verifying AI-generated SQL queries with actual database results.

As an Industrial Engineering student, I found the industrial machine telemetry exercise particularly relevant because it demonstrated how databases can support industrial monitoring and decision-making.

## 3. What was difficult, and where did you struggle?

Initially, working with the command line, PowerShell and SQLite shell was challenging. I also experienced some difficulties related to encoding and the technical environment.

Another challenge was understanding SQL execution plans and interpreting the difference between filtering by time of day and filtering by a specific timestamp.

These challenges helped me understand the importance of testing and understanding the logic behind SQL queries rather than simply executing them.

## 4. Was there any good or fun struggling or exploration? Any showstoppers?

The most interesting exploration was working with the industrial telemetry dataset and investigating the AI-generated SQL query.

I found it interesting that two apparently similar filtering approaches produced significantly different results: 43,194 records compared with 129,597 records.

This demonstrated how a small difference in SQL logic can significantly affect the results and potentially lead to incorrect industrial decisions.

There are still some documentation improvements I need to make, particularly preserving the exact SQL statements used for boundary testing.

## 5. How was your interaction with peers and instructors?

My Task Pod partner was Tunay. We used GitHub as a platform for sharing our portfolios and receiving feedback.

Tunay reviewed my work for Tasks 6 and 7 through GitHub Issue #1. His feedback helped me evaluate my SQL queries, telemetry analysis, execution plans and interpretation of time-filtering conditions.

This experience demonstrated the importance of peer review and constructive feedback in software and database development.

## 6. Help and extra work

### Who helped you, gave feedback, and was it valuable?

Tunay provided valuable and detailed feedback on my telemetry analysis and AI-generated SQL verification.

He particularly recommended documenting the exact boundary-test SQL statements to improve the reproducibility of my work.

His feedback is available here: [Module 1 – Task Pod Peer Review](https://github.com/isa-babayev-ibabayev/databases-portfolio/issues/1).

### Who did you help or give feedback to?

I reviewed Tunay's Module 1 SQL queries, AI verification report, query results and Python analysis in [his Module 1 peer-review issue](https://github.com/tunaydaldaban-beep/databases-portfolio/issues/1). I found the documented SQL, execution plan and 18:00 boundary verification consistent, while clearly stating that I had not rerun his full dataset.

### Did you present, implement, make a PR, or fix something crucial for the class?

My main technical contributions within my portfolio included implementing the industrial telemetry generator, developing the SQLite data ingestion process, analyzing machine readings, and verifying AI-generated SQL.

I also documented the results and technical findings in my GitHub portfolio to make the work understandable and reproducible for others.

## 7. What would you improve in the future?

In future modules, I would like to improve my SQL knowledge, command-line skills, documentation practices and collaboration with other students.

I would also like to become more independent in database development and improve my ability to identify errors in AI-generated code before using it in real-world applications.
