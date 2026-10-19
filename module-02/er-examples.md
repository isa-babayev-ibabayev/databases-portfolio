# Four ER modeling exercises

Mermaid notation uses `||` for exactly one, `o|` for zero or one, and
`|{` for one or more.

## 1. One-to-one: machine and nameplate

```mermaid
erDiagram
    MACHINE ||--|| NAMEPLATE : has
    MACHINE {
        int machine_id PK
        string workshop_location
    }
    NAMEPLATE {
        int machine_id PK, FK
        string serial_no UK
        string manufacturer
    }
```

`Nameplate.machine_id` is both its primary key and a foreign key to Machine.
That makes each nameplate belong to only one machine and prevents two
nameplates for one machine. `serial_no UNIQUE NOT NULL` gives the natural
identifier its own guarantee. A separate entity is useful when nameplate data
has its own lifecycle, provenance, or more fields; if it is only two inseparable
values, embedding them in Machine is simpler.

The foreign key and uniqueness enforce *at most one* nameplate per machine.
They do not, by themselves, force every Machine row to have a Nameplate row.
“Exactly one” across both tables needs a transaction/workflow rule, a deferred
constraint in a database that supports it, or a single combined table.

## 2. One-to-many: machines and sensors

```mermaid
erDiagram
    MACHINE ||--|{ SENSOR : carries
    MACHINE {
        int machine_id PK
        string name UK
    }
    SENSOR {
        int sensor_id PK
        int machine_id FK
        string label
    }
```

```sql
CREATE TABLE machine (
  machine_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE sensor (
  sensor_id INTEGER PRIMARY KEY,
  machine_id INTEGER NOT NULL REFERENCES machine(machine_id),
  label TEXT NOT NULL
);
```

Machine is the parent; Sensor is the child and therefore carries the foreign
key. [The executable proof](sketch-proof.sql) inserts two sensors for machine 1,
counts 2, and rejects an orphan sensor for machine 999.

## 3. Many-to-many: work orders and parts

```mermaid
erDiagram
    WORK_ORDER ||--o{ WORK_ORDER_PART : contains
    PART ||--o{ WORK_ORDER_PART : appears_in
    WORK_ORDER {
        int order_id PK
        date opened_on
    }
    PART {
        string part_no PK
        string description
    }
    WORK_ORDER_PART {
        int order_id PK, FK
        string part_no PK, FK
        int quantity
    }
```

```sql
CREATE TABLE work_order_part (
  order_id INTEGER NOT NULL REFERENCES work_order(order_id),
  part_no TEXT NOT NULL REFERENCES part(part_no),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  PRIMARY KEY (order_id, part_no)
);
```

The junction row represents “this order uses this part.” Its composite primary
key rejects a second row with the same pair; quantity belongs on that one
relationship row if more than one physical unit is used.

## 4. Maintenance job as an entity

```mermaid
erDiagram
    MACHINE ||--o{ MAINTENANCE_JOB : receives
    TECHNICIAN ||--o{ MAINTENANCE_JOB : performs
    MACHINE {
        int machine_id PK
        string serial_no UK
    }
    TECHNICIAN {
        int technician_id PK
        string name
    }
    MAINTENANCE_JOB {
        int job_id PK
        int machine_id FK
        int technician_id FK
        date done_on
    }
```

MaintenanceJob connects a machine and a technician, but it should be an entity
because it has its own identity, date, and later relationships to parts,
documents, and costs. Machine and Technician use stable surrogate keys.
`done_on` is an attribute of the job. The two non-null foreign keys say each
job has exactly one machine and technician, while either parent may have zero
or many jobs.
