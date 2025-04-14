from neo4j import GraphDatabase
import os
import csv
from dotenv import load_dotenv

load_dotenv()

CSV_DIR = "migration-csv-tables"

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def create_nodes(tx, label, csv_file):

    file_path = os.path.join(CSV_DIR, csv_file)
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            props = {k: row[k] for k in row if row[k] != ''}
            prop_str = ", ".join(f"{k}: ${k}" for k in props.keys())
            query = f"MERGE (n:{label} {{ {prop_str} }})"
            tx.run(query, **props)

def import_nodes():
    with driver.session(database="neo4j") as session:
        print("Importing nodes from CSV files...")
        session.execute_write(create_nodes, "Country", "country.csv")
        session.execute_write(create_nodes, "DiseaseStats", "disease_stats.csv")
        session.execute_write(create_nodes, "Vaccine", "vaccine.csv")
        session.execute_write(create_nodes, "Ingredient", "ingredient.csv")
        session.execute_write(create_nodes, "DosageInfo", "dosage_info.csv")
        session.execute_write(create_nodes, "Warning", "warning.csv")
        session.execute_write(create_nodes, "CountryVaccineUsage", "country_vaccine_usage.csv")
        session.execute_write(create_nodes, "VaccinePublicView", "vaccine_public_view.csv")
        session.execute_write(create_nodes, "VaccineFullView", "vaccine_full_view.csv")
        print("Nodes imported successfully!")

def create_relationship(tx, query):
    tx.run(query)

def import_relationships():
    with driver.session(database="neo4j") as session:
        print("Creating relationships...")

        query = """
        MATCH (c:Country), (ds:DiseaseStats)
        WHERE toString(ds.country_id) = toString(c.id)
        MERGE (c)-[:HAS_STATS]->(ds)
        """
        session.execute_write(create_relationship, query)

        query = """
        MATCH (v:Vaccine), (i:Ingredient)
        WHERE i.vaccine_ndc = v.ndc_code
        MERGE (v)-[:HAS_INGREDIENT]->(i)
        """
        session.execute_write(create_relationship, query)

        query = """
        MATCH (v:Vaccine), (d:DosageInfo)
        WHERE d.vaccine_ndc = v.ndc_code
        MERGE (v)-[:HAS_DOSAGE_INFO]->(d)
        """
        session.execute_write(create_relationship, query)

        query = """
        MATCH (v:Vaccine), (w:Warning)
        WHERE w.vaccine_ndc = v.ndc_code
        MERGE (v)-[:HAS_WARNING]->(w)
        """
        session.execute_write(create_relationship, query)

        query = """
        MATCH (c:Country), (cv:CountryVaccineUsage), (v:Vaccine)
        WHERE toString(cv.country_id) = toString(c.id)
          AND cv.vaccine_ndc = v.ndc_code
        MERGE (c)-[r:USES_VACCINE]->(v)
        SET r.usage_notes = cv.usage_notes
        """
        session.execute_write(create_relationship, query)

        print("Relationships created successfully!")

def import_data():
    import_nodes()
    import_relationships()

if __name__ == "__main__":
    import_data()
    driver.close()
    print("Neo4j import complete.")