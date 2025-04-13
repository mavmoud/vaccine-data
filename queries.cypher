// ==============================================================================
// SOEN 363 Phase II - Neo4j Query Implementation
// ==============================================================================



// ==============================================================================
// 1. BASIC SEARCH QUERIES ON ATTRIBUTE VALUES
// ==============================================================================

// a) Find all vaccines where manufacturer contains 'Pfizer'
PROFILE MATCH (v:Vaccine)
WHERE v.manufacturer CONTAINS 'Pfizer'
RETURN v.ndc_code, v.brand_name, v.generic_name, v.manufacturer;


// b) Find all countries with population greater than 50 million
PROFILE MATCH (c:Country)
WHERE toInteger(c.population) > 50000000
RETURN c.name, c.code, c.population;


// c) Find all vaccines administered via Injection
PROFILE MATCH (v:Vaccine)
WHERE v.route = 'INJECTION'
RETURN v.ndc_code, v.brand_name, v.generic_name, v.route;



// ==============================================================================
// 2. AGGREGATE QUERIES (COUNT ENTITIES SATISFYING CRITERIA)
// ==============================================================================

// a) Count how many vaccines manufactured by Pfizer
PROFILE MATCH (v:Vaccine)
WHERE v.manufacturer CONTAINS 'Pfizer'
RETURN count(v) AS pfizer_vaccine_count;


// b) Count how many countries have population greater than 50 million
PROFILE MATCH (c:Country)
WHERE toInteger(c.population) > 50000000
RETURN count(c) AS high_population_country_count;



// ==============================================================================
// 3. TOP-N QUERIES (SORTED RESULTS)
// ==============================================================================

// a) Top 5 countries with highest total COVID cases
PROFILE MATCH (c:Country)-[:HAS_STATS]->(ds:DiseaseStats)
RETURN c.name, ds.total_cases
ORDER BY toInteger(ds.total_cases) DESC
LIMIT 5;


// b) Top 3 vaccines used in the most countries
PROFILE MATCH (v:Vaccine)<-[:USES_VACCINE]-(c:Country)
RETURN v.brand_name, count(c) AS usage_count
ORDER BY usage_count DESC
LIMIT 3;



// ==============================================================================
// 4. GROUP BY SIMULATION (AGGREGATE PER CATEGORY)
// ==============================================================================

// Count number of vaccines per route of administration
PROFILE MATCH (v:Vaccine)
WHERE v.route IS NOT NULL
RETURN v.route AS route_of_administration, count(v) AS vaccine_count
ORDER BY vaccine_count DESC;



// ==============================================================================
// 5. INDEX CREATION FOR OPTIMIZATION
// ==============================================================================

DROP INDEX vaccine_manufacturer_index IF EXISTS;
CREATE INDEX vaccine_manufacturer_index FOR (v:Vaccine) ON (v.manufacturer);

DROP INDEX country_population_index IF EXISTS;
CREATE INDEX country_population_index FOR (c:Country) ON (c.population);

DROP INDEX vaccine_route_index IF EXISTS;
CREATE INDEX vaccine_route_index FOR (v:Vaccine) ON (v.route);

DROP INDEX disease_stats_total_cases_index IF EXISTS;
CREATE INDEX disease_stats_total_cases_index FOR (ds:DiseaseStats) ON (ds.total_cases);



// ==============================================================================
// 6. QUERY USED FOR INDEX TESTING (BEFORE & AFTER REGULAR INDEX)
// ==============================================================================

// Find vaccines where manufacturer contains 'Pfizer'
// Used to compare performance before & after regular index
PROFILE MATCH (v:Vaccine)
WHERE v.manufacturer CONTAINS 'Pfizer'
RETURN v.ndc_code, v.brand_name, v.manufacturer;


/*
OBSERVATIONS:

BEFORE Index:
- Execution Time: ~92 ms
- Total DB Hits: 493
- Scan Type: NodeByLabelScan (Full Scan)

AFTER Regular Index:
- Execution Time: ~80 ms
- Total DB Hits: 181
- Scan Type: NodeIndexScan
- Observation: Regular index slightly improved but not enough due to CONTAINS operator.
RECOMMENDATION: Use Full-Text Index for better performance.
*/



// ==============================================================================
// 7. FULL-TEXT INDEX CREATION FOR MANUFACTURER ATTRIBUTE
// ==============================================================================

DROP INDEX vaccine_manufacturer_fulltext IF EXISTS;
CREATE FULLTEXT INDEX vaccine_manufacturer_fulltext FOR (v:Vaccine) ON EACH [v.manufacturer];



// ==============================================================================
// 8. FULL-TEXT SEARCH QUERY (OPTIMIZED PARTIAL MATCH)
// ==============================================================================

PROFILE CALL db.index.fulltext.queryNodes("vaccine_manufacturer_fulltext", "Pfizer")
YIELD node, score
RETURN node.ndc_code, node.brand_name, node.manufacturer;


/*
OBSERVATIONS:

AFTER Full-Text Index:

- Execution Time: ~1-5 ms
- Total DB Hits: ~10-50
- Scan Type: FullTextIndex

FINAL NOTE:
Full-Text Indexing provided the best performance for partial string matching.
Highly recommended in Neo4j for search scenarios.
*/
// ==============================================================================

