import os
from dotenv import load_dotenv
import psycopg2
import csv

def export_to_csv(query, filename):
    cursor.execute(query)
    rows = cursor.fetchall()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([desc[0] for desc in cursor.description])
        writer.writerows(rows)
    print(f"Data exported to {filename}")

def main():
    load_dotenv()

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    global cursor
    cursor = conn.cursor()

    # ===========================
    # Export Country Table
    # ===========================
    # country_query = "SELECT * FROM Country;"
    # export_to_csv(country_query, 'migration-csv-tables/country.csv')

    # ===========================
    # Export DiseaseStats Table
    # ===========================
    disease_stats_query = "SELECT * FROM DiseaseStats;"
    export_to_csv(disease_stats_query, 'migration-csv-tables/disease_stats.csv')

    # ===========================
    # Export Vaccine Table
    # ===========================
    vaccine_query = "SELECT * FROM Vaccine;"
    export_to_csv(vaccine_query, 'migration-csv-tables/vaccine.csv')

    # ===========================
    # Export Ingredient Table
    # ===========================
    ingredient_query = "SELECT * FROM Ingredient;"
    export_to_csv(ingredient_query, 'migration-csv-tables/ingredient.csv')

    # ===========================
    # Export DosageInfo Table
    # ===========================
    dosage_info_query = "SELECT * FROM DosageInfo;"
    export_to_csv(dosage_info_query, 'migration-csv-tables/dosage_info.csv')

    # ===========================
    # Export Warning Table
    # ===========================
    warning_query = "SELECT * FROM Warning;"
    export_to_csv(warning_query, 'migration-csv-tables/warning.csv')

    # ===========================
    # Export CountryVaccineUsage Table
    # ===========================
    country_vaccine_usage_query = "SELECT * FROM CountryVaccineUsage;"
    export_to_csv(country_vaccine_usage_query, 'migration-csv-tables/country_vaccine_usage.csv')

    # ===========================
    # Export VaccinePublicView View
    # ===========================
    vaccine_public_query = "SELECT * FROM VaccinePublicView;"
    export_to_csv(vaccine_public_query, 'migration-csv-tables/vaccine_public_view.csv')

    # ===========================
    # Export VaccineFullView View
    # ===========================
    vaccine_full_query = "SELECT * FROM VaccineFullView;"
    export_to_csv(vaccine_full_query, 'migration-csv-tables/vaccine_full_view.csv')

    cursor.close()
    conn.close()

    print("All data exported successfully!")

if __name__ == "__main__":
    main()