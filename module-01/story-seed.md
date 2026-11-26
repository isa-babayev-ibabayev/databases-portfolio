# Story Seed – Smart Industrial Machine Monitoring

Marta Weber is a maintenance engineer working at a small manufacturing company in Gütersloh, Germany. She is responsible for monitoring three CNC machines and preventing unexpected machine failures. However, the company has a limited budget and cannot justify expensive cloud infrastructure for its local monitoring system. Marta needs to decide which machine should receive maintenance priority based on its vibration measurements. The first question the database must answer is: **Which CNC machine recorded the highest vibration level during the last two days?** The data consists of temperature, vibration and spindle-load measurements collected every three seconds from three CNC machines. For the prototype, the data can be generated reproducibly using a Python script with a fixed random seed of 42, producing 172,800 records that are stored locally in SQLite. This matters to Marta because early detection of abnormal machine behaviour can help reduce unexpected downtime and maintenance costs. It also matters to me as an Industrial Engineering student because it connects database technology with industrial automation, predictive maintenance and data-driven decision-making.

## Initial Skills and Expectations

### My Background

I am an Industrial Engineering student at Hochschule Bielefeld. I am particularly interested in industrial digitalization, artificial intelligence, software development, automation and data-driven decision-making.

### Initial Skills

| Skill | Initial experience |
|---|---|
| Programming | Basic knowledge and experience with AI-assisted development |
| Python | Basic familiarity |
| SQL | Limited practical experience |
| Database systems | Basic theoretical understanding |
| SQLite | Limited previous experience |
| Command line and PowerShell | Basic experience |
| Git and GitHub | Basic familiarity |
| Web application development | Some experience with AI-assisted development |
| Database servers | Limited practical experience |
| Artificial intelligence tools | Experience using AI for learning, development and problem-solving |
| Industrial Engineering | Academic knowledge of industrial processes and engineering applications |

### My Expectations

At the beginning of this course, I wanted to:

- Understand how databases work and how they are structured.
- Develop practical SQL skills.
- Learn how to use Python with databases.
- Understand the differences between embedded and server-based databases.
- Improve my Git and GitHub skills.
- Learn how to verify AI-generated SQL and code.
- Understand how databases can support industrial monitoring, automation and predictive maintenance.
- Develop practical database applications that address real-world engineering problems.

## CBL/PBL and the Course Assessment Model

### Understanding the Course Philosophy and Assessment Model

#### Challenge-Based Learning (CBL)

Challenge-Based Learning focuses on investigating practical challenges and developing solutions through experimentation, research and collaboration.

In this module, the industrial machine telemetry exercise demonstrates this approach by using database technologies to investigate machine performance and identify abnormal vibration measurements.

#### Project-Based Learning (PBL)

Project-Based Learning focuses on developing practical knowledge through the implementation of meaningful projects.

Instead of only studying database theory, we develop solutions, measure performance, document results and reflect on engineering decisions.

#### Portfolio-Based Assessment

The course uses a GitHub portfolio and a final project instead of a traditional written examination.

The assessment consists of:

| Assessment component | Maximum points |
|---|---:|
| Modules 1–6 | 11 |
| Reflections and engineering decision log | 4 |
| Final project work | 3 |
| Project presentation and individual discussion | 2 |
| Total | 20 |

A minimum of 14 points is required to pass.

Module 1 is worth one point, while Modules 2–5 are worth two points each. Module 6 is taught as two studios, 6a and 6b, which together are worth two points.

The assessment focuses on demonstrating the learning goals through practical evidence rather than simply completing a checklist.

#### Task Pods and Continuous Feedback

Task Pods support collaboration, knowledge exchange, peer review and practical problem-solving.

Checkpoints provide feedback and help students identify missing evidence before the final assessment. The checkpoint itself is not a graded examination.

#### The Moving Bar

The course is continuously developing. Tasks and teaching materials may evolve based on student feedback, classroom discoveries and practical experience.

The learning goals remain the foundation of the course, while the methods used to demonstrate them can be adapted.

#### Responsible Use of Artificial Intelligence

AI tools can support SQL generation, debugging, documentation and learning. However, their outputs must be independently evaluated.

In Module 1, this principle is demonstrated through executing AI-generated SQL, examining the query plan, testing boundary conditions and documenting the limitations of the generated query.

### Official Course References

- [Course Syllabus](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/syllabus.md)
- [Module 1 Workbook](https://github.com/iotempire/iotempire-teaching/blob/main/full-classes/hsbi-databases-10d/modules/01-introduction-and-local-first.md)
