-- Learning Goal 2: distinguish a covering index scan from a selective search.
-- Run safely with:
-- sqlite3 :memory: ".read module-03/covering-scan-demo.sql"

CREATE TABLE t(
    a INTEGER,
    b TEXT
);

CREATE INDEX i ON t(a);

INSERT INTO t(a, b)
VALUES (1, 'one'), (2, 'two'), (3, 'three');

EXPLAIN QUERY PLAN
SELECT a
FROM t INDEXED BY i;

SELECT a
FROM t INDEXED BY i;
