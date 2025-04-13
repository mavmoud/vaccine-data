
## Team

| Name             | Student ID | GitHub ID       |
|------------------|------------|-----------------|
| Jad Hanna        | 40132590   | JX0X0           |
| Mahmoud Mohamed  | 40163777   | Mahmoud M.      |
| Baraa Chrit      | 40225403   | b-chrit         |
| Mostafa Mohamed  | 40201893   | Mustafa-M422    |


## Project Summary

This project revolves around the integration of real-world vaccine and worldwide COVID-19 data. The system fetches data from live APIs, stores it in a normalized relational schema (PostgreSQL), and then migrates the whole dataset to a graph database (Neo4j). The graph model allows us to explore complex relationships between countries, vaccines, ingredients, dosage details, and warnings.

Phase II is especially focused on the transition from relational to NoSQL, rendering the data fully accessible through graph-based queries and performance-tuned.

---

## Main Files

| File                   | Description                                              |
|------------------------|----------------------------------------------------------|
| `fetch_and_generate_sql.py` | Pulls and inserts data from APIs into PostgreSQL     |
| `export_tables.py`     | Exports tables from PostgreSQL as CSV                   |
| `import_neo4j.py`      | Imports CSV files into Neo4j and builds relationships   |
| `schema.sql`           | Relational schema for PostgreSQL                        |
| `queries.cypher`       | All Cypher queries required for Phase II                |
| `queries.py`           | Runs 23 SQL queries for testing the relational schema   |
| `README.md`            | Instructions and project overview                       |

---

## Graph Entities

- **Nodes**: `Country`, `DiseaseStats`, `Vaccine`, `Ingredient`, `DosageInfo`, `Warning`, `CountryVaccineUsage`
- **Relationships**:
  - `[:HAS_STATS]`
  - `[:HAS_INGREDIENT]`
  - `[:HAS_DOSAGE_INFO]`
  - `[:HAS_WARNING]`
  - `[:USES_VACCINE]`

---

## Queries Implemented

The project covers all required query types for Phase II:

- Basic search queries (e.g., find vaccines by manufacturer)
- Aggregate queries (e.g., count vaccines by route)
- Top-N queries (e.g., top 5 countries by COVID-19 cases)
- Group-by simulations using Cypher
- Indexing and performance comparison (using PROFILE)
- Full-text search with Neo4j fulltext indexes

---

## Phase II File Mapping & Requirements

| File Name                   | Description                                                                 | Phase II Requirement Fulfilled                          |
|----------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------|
| `schema.sql`               | Defines the full relational schema used in Phase I                         | Phase I design reference; used for data migration setup |
| `fetch_and_generate_sql.py`| Fetches live data from Disease.sh and OpenFDA, processes and inserts into PostgreSQL | Data migration, population of relational model          |
| `export_tables.py`         | Exports all PostgreSQL tables into `.csv` format for graph migration       | Required for data transfer to NoSQL                     |
| `import_neo4j.py`          | Reads the CSVs and imports them into Neo4j, creating nodes & relationships | Porting data to NoSQL, data modeling                    |
| `queries.py`               | Interface to run 23 SQL queries including joins, aggregates, subqueries    | SQL query implementation for Phase I review             |
| `queries.cypher`           | Neo4j Cypher queries: search, aggregate, top-N, group-by, indexes          | NoSQL query implementation, performance optimization    |
| `main.py` (optional)       | Script that runs everything sequentially                                   | Can be used for demo convenience                        |
| `phase-1-report.pdf`       | Previous phase documentation and schema breakdown                          | For ER model transition reference                       |
| `README.md`                | Full project instructions and overview                                     | Required for submission and clarity                     |



---

## Notes

- The Neo4j model simplifies some of the relational constraints (e.g., IS-A and weak entities).
- Country-vaccine mappings are partially inferred when not available directly in the data.
- Indexing is handled manually for performance comparison using `PROFILE`.
- All data was fetched in real-time to ensure variety and relevance in the dataset.

---

## How to Run 

Run the scripts in the following order:

- `fetch_and_generate_sql.py`  

  Fetches live data from Disease.sh and OpenFDA, then stores it in PostgreSQL.

- `export_tables.py`  

  Exports all PostgreSQL tables as `.csv` files.

- `import_neo4j.py`  

  Loads the CSV files into Neo4j as nodes and relationships.

4. Run queries:

- `queries.py` 
 lets you run and test all SQL queries.

- `queries.cypher` 
 open this file in Neo4j Browser to run Cypher queries.
 

