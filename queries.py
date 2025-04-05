import psycopg2

# --- Database Config ---
DB_CONFIG = {
    'dbname': 'soen363_project',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

# --- All Queries (Indexed by Number) ---
QUERIES = {

#-- INNER JOIN example: join Vaccine with DosageInfo on the vaccine_ndc field
    1: """SELECT v.ndc_code, v.brand_name, d.dosage_text
    FROM Vaccine v
    JOIN DosageInfo d ON v.ndc_code = d.vaccine_ndc;""",

#-- Cartesian product equivalent for INNER JOIN using WHERE clause
    2: """SELECT v.ndc_code, v.brand_name, d.dosage_text
    FROM Vaccine v, DosageInfo d
    WHERE v.ndc_code = d.vaccine_ndc;""",

#-- LEFT OUTER JOIN: return all vaccines and their ingredients (if any)
    3: """SELECT v.ndc_code, v.brand_name, i.substance_name
    FROM Vaccine v
    LEFT JOIN Ingredient i ON v.ndc_code = i.vaccine_ndc;""",

#-- RIGHT OUTER JOIN: return all ingredients and their associated vaccines (if any)
    4: """SELECT v.ndc_code, v.brand_name, i.substance_name
    FROM Vaccine v
    RIGHT JOIN Ingredient i ON v.ndc_code = i.vaccine_ndc;""",

#-- FULL OUTER JOIN: return all vaccines and ingredients even if there is no match
    5: """SELECT v.ndc_code, v.brand_name, i.substance_name
    FROM Vaccine v
    FULL OUTER JOIN Ingredient i ON v.ndc_code = i.vaccine_ndc;""",

#-- Query vaccines with no brand name (brand_name is NULL)
    6: """SELECT ndc_code, generic_name
    FROM Vaccine
    WHERE brand_name IS NULL;""",

#-- Query vaccines with a NULL route value
    7: """SELECT ndc_code, generic_name
    FROM Vaccine
    WHERE route IS NULL;""",

#-- Simple GROUP BY: count the number of vaccines used per country (CountryVaccineUsage)
    8: """SELECT c.name AS country_name, COUNT(cvu.vaccine_ndc) AS vaccine_count
    FROM CountryVaccineUsage cvu
    JOIN Country c ON cvu.country_id = c.id
    GROUP BY c.name;""",

#-- GROUP BY with WHERE and HAVING: only countries with non-null usage notes and more than one vaccine entry
    9: """SELECT c.name AS country_name, COUNT(cvu.vaccine_ndc) AS vaccine_count
    FROM CountryVaccineUsage cvu
    JOIN Country c ON cvu.country_id = c.id
    WHERE cvu.usage_notes IS NOT NULL
    GROUP BY c.name
    HAVING COUNT(cvu.vaccine_ndc) > 1;""",

#-- Join with nested sub-query: select countries with population above the average
    10: """SELECT c.name, ds.total_cases
    FROM Country c
    JOIN DiseaseStats ds ON c.id = ds.country_id
    WHERE c.population > (SELECT AVG(population) FROM Country);""",

#-- Correlated subquery: for each country, retrieve maximum total_cases from DiseaseStats
    11: """SELECT c.name,
    (SELECT MAX(ds.total_cases)
    FROM DiseaseStats ds
    WHERE ds.country_id = c.id) AS max_cases
    FROM Country c;""",

#-- Correlated subquery: for each vaccine, count how many active ingredients it has
    12: """SELECT v.ndc_code, v.generic_name,
    (SELECT COUNT(*)
    FROM Ingredient i
    WHERE i.vaccine_ndc = v.ndc_code AND i.is_active = TRUE) AS active_ingredient_count
    FROM Vaccine v;""",

#-- Set operation using INTERSECT: vaccines with non-null brand_name that also have a dosage entry
    13: """SELECT ndc_code FROM Vaccine WHERE brand_name IS NOT NULL
    INTERSECT
    SELECT vaccine_ndc FROM DosageInfo;""",

    #-- Equivalent without INTERSECT:
    14: """SELECT DISTINCT v.ndc_code
    FROM Vaccine v, DosageInfo d
    WHERE v.ndc_code = d.vaccine_ndc AND v.brand_name IS NOT NULL;""",

#-- Set operation using UNION: distinct vaccine codes from two manufacturers
    15: """SELECT ndc_code FROM Vaccine WHERE manufacturer = 'Sanofi Pasteur Inc.'
    UNION
    SELECT ndc_code FROM Vaccine WHERE manufacturer = 'Seqirus, Inc.';""",

    #-- Equivalent without UNION:
    16: """SELECT DISTINCT ndc_code
    FROM Vaccine
    WHERE manufacturer = 'Sanofi Pasteur Inc.' OR manufacturer = 'Seqirus, Inc.';""",

#-- Set operation using DIFFERENCE (EXCEPT): vaccines that do NOT have a dosage record
    17: """SELECT ndc_code FROM Vaccine
    EXCEPT
    SELECT vaccine_ndc FROM DosageInfo;""",

    #-- Equivalent without set difference:
    18: """SELECT ndc_code
    FROM Vaccine
    WHERE ndc_code NOT IN (SELECT vaccine_ndc FROM DosageInfo);""",

#-- View with hard-coded criteria: countries with population greater than 50,000,000
    19: """CREATE OR REPLACE VIEW HighPopulationCountry AS
    SELECT *
    FROM Country
    WHERE population > 50000000;

    SELECT * FROM HighPopulationCountry;""",

#-- Overlap constraint: vaccines that appear in both DosageInfo and Warning tables
    20: """SELECT v.ndc_code, v.generic_name
    FROM Vaccine v
    WHERE v.ndc_code IN (SELECT vaccine_ndc FROM DosageInfo)
        AND v.ndc_code IN (SELECT vaccine_ndc FROM Warning);""",

#-- Covering constraint: check whether every vaccine appears in at least one of DosageInfo or Warning
    21: """SELECT v.ndc_code, v.generic_name
    FROM Vaccine v
    WHERE v.ndc_code NOT IN (
        SELECT vaccine_ndc FROM DosageInfo
        UNION
        SELECT vaccine_ndc FROM Warning
    );""",

#-- Division operator using nested query with NOT IN: find vaccines used in every country
    22: """SELECT v.ndc_code, v.generic_name
    FROM Vaccine v
    WHERE NOT EXISTS (
        SELECT c.id FROM Country c
        WHERE c.id NOT IN (<user__selection></user__selection>
             SELECT cvu.country_id
             FROM CountryVaccineUsage cvu
             WHERE cvu.vaccine_ndc = v.ndc_code
    )
    );""",

#-- Division operator using correlated subquery with NOT EXISTS and EXCEPT: find vaccines used in every country
    23: """SELECT v.ndc_code, v.generic_name
    FROM Vaccine v
    WHERE NOT EXISTS (
        (SELECT c.id FROM Country)
        EXCEPT
        (SELECT cvu.country_id FROM CountryVaccineUsage cvu WHERE cvu.vaccine_ndc = v.ndc_code)
    );"""

}

def run_query(query_number):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = QUERIES[query_number]

        # Split query into individual statements if needed
        statements = [q.strip() for q in query.strip().split(';') if q.strip()]

        for stmt in statements:
            cursor.execute(stmt)
            if stmt.upper().startswith("SELECT"):
                rows = cursor.fetchall()
                if rows:
                    colnames = [desc[0] for desc in cursor.description]
                    print(" | ".join(colnames))
                    print("-" * 60)
                    for row in rows:
                        print(" | ".join(str(item) if item is not None else "NULL" for item in row))
                        print()
                else:
                    print("No results.")
            else:
                conn.commit()
                print("Query executed successfully (non-SELECT).")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error running query #{query_number}: {e}")

# def run_query(query_number):
#     try:
#         conn = psycopg2.connect(**DB_CONFIG)
#         cursor = conn.cursor()
#         query = QUERIES[query_number]
#
#         cursor.execute(query)
#
#         # If it's a SELECT, fetch and print
#         if query.strip().upper().startswith("SELECT"):
#             rows = cursor.fetchall()
#             if rows:
#                 colnames = [desc[0] for desc in cursor.description]
#                 print(" | ".join(colnames))
#                 print("-" * 60)
#                 for row in rows:
#                     print(" | ".join(str(item) if item is not None else "NULL" for item in row))
#                     print()
#             else:
#                 print("No results.")
#         else:
#             conn.commit()
#             print("Query executed successfully (non-SELECT).")
#
#         cursor.close()
#         conn.close()
#     except Exception as e:
#         print(f"Error running query #{query_number}: {e}")


if __name__ == "__main__":
    print("Choose a query number to run:")
    menu = (
        "1: INNER JOIN example\n"
        "2: Cartesian product equivalent for INNER JOIN\n"
        "3: LEFT OUTER JOIN example\n"
        "4: RIGHT OUTER JOIN example\n"
        "5: FULL OUTER JOIN example\n"
        "6: Vaccines with no brand name (NULL)\n"
        "7: Vaccines with NULL route\n"
        "8: Simple GROUP BY query\n"
        "9: GROUP BY with WHERE and HAVING clauses\n"
        "10: Join with nested sub-query\n"
        "11: Correlated subquery (max total_cases per country)\n"
        "12: Correlated subquery (count active ingredients per vaccine)\n"
        "13: Set operation (INTERSECT) and equivalent\n"
        "14: Set operation (INTERSECT) Equivalent without INTERSECT\n"
        "15: Set operation (UNION) and equivalent\n"
        "16: Set operation (UNION) Equivalent without UNION\n"
        "17: Set operation (DIFFERENCE/EXCEPT) and equivalent\n"
        "18: Set operation (DIFFERENCE/EXCEPT) Equivalent without set difference\n"
        "19: View with hard-coded criteria\n"
        "20: Overlap constraint query\n"
        "21: Covering constraint query\n"
        "22: Division operator using nested query (NOT IN)\n"
        "23: Division operator using correlated subquery (NOT EXISTS and EXCEPT)\n"
    )

    print(menu)

    try:
        qnum = int(input("Enter query number: "))
        if qnum in QUERIES:
            print(f"\n--- Running Query #{qnum} ---\n")
            run_query(qnum)
        else:
            print("Invalid query number.")
    except ValueError:
        print("Please enter a valid number.")
