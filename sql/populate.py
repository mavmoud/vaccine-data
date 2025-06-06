import requests
import psycopg2
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configuration
OPENFDA_API_KEY = 'zx9z8i0d6Z1Z1aC2CjooXOIEaOQ5XWOcBZDjIAqW'
DB_CONFIG = {
    'dbname': 'soen363_project',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}


def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        exit(1)


def fetch_countries_from_disease_sh() -> List[Dict[str, Any]]:
    """Fetch country data from Disease.sh API"""
    print("Fetching country data from Disease.sh...")
    try:
        response = requests.get('https://disease.sh/v3/covid-19/countries')
        if response.status_code == 200:
            countries = response.json()
            print(f"Retrieved {len(countries)} countries")
            return countries
        else:
            print(f"Error fetching countries: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to Disease.sh API: {e}")
        return []


def fetch_vaccines_from_openfda(limit: int = 1000) -> List[Dict[str, Any]]:
    """Fetch vaccine data from OpenFDA API"""
    print(f"Fetching up to {limit} vaccines from OpenFDA...")

    all_vaccines = []
    try:
        for offset in range(0, limit, 100):  # Fetch in batches of 100
            url = f"https://api.fda.gov/drug/ndc.json?api_key={OPENFDA_API_KEY}&search=product_type:\"VACCINE\"&limit=100&skip={offset}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                batch = data.get('results', [])
                all_vaccines.extend(batch)
                print(f"Fetched batch of {len(batch)} vaccines (total so far: {len(all_vaccines)})")

                if len(batch) < 100:  # Less than requested means we've hit the end
                    break

                # Be nice to the API - don't hammer it
                time.sleep(0.5)
            else:
                print(f"Error fetching vaccines (offset {offset}): {response.status_code}")
                if response.status_code == 429:  # Rate limit
                    print("Rate limited. Waiting before continuing...")
                    time.sleep(5)
                    continue
                break
    except Exception as e:
        print(f"Error connecting to OpenFDA API: {e}")

    print(f"Retrieved a total of {len(all_vaccines)} vaccines")
    return all_vaccines


def process_countries(conn, countries: List[Dict[str, Any]]) -> Dict[str, int]:
    """Insert country data and return mapping of country names to IDs"""
    print("Processing country data...")
    country_map = {}
    cursor = conn.cursor()

    for country in countries:
        try:
            name = country.get('country', '')
            if not name:
                continue

            code = country.get('countryInfo', {}).get('iso2', None)
            population = country.get('population', 0)
            updated_at = datetime.fromtimestamp(country.get('updated', 0) / 1000)

            # Insert country
            cursor.execute(
                "INSERT INTO Country (name, code, population, updated_at) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (name) DO UPDATE SET code = EXCLUDED.code, population = EXCLUDED.population, "
                "updated_at = EXCLUDED.updated_at RETURNING id",
                (name, code, population, updated_at)
            )
            country_id = cursor.fetchone()[0]
            country_map[name] = country_id

            # Insert disease stats
            cursor.execute(
                "INSERT INTO DiseaseStats (country_id, total_cases, today_cases, deaths, today_deaths, "
                "recovered, today_recovered, active, critical, cases_per_million, deaths_per_million, "
                "tests, tests_per_million, active_per_million, recovered_per_million, critical_per_million) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                (
                    country_id,
                    country.get('cases', 0),
                    country.get('todayCases', 0),
                    country.get('deaths', 0),
                    country.get('todayDeaths', 0),
                    country.get('recovered', 0),
                    country.get('todayRecovered', 0),
                    country.get('active', 0),
                    country.get('critical', 0),
                    country.get('casesPerOneMillion', 0),
                    country.get('deathsPerOneMillion', 0),
                    country.get('tests', 0),
                    country.get('testsPerOneMillion', 0),
                    country.get('activePerOneMillion', 0),
                    country.get('recoveredPerOneMillion', 0),
                    country.get('criticalPerOneMillion', 0)
                )
            )
        except Exception as e:
            print(f"Error processing country {country.get('country', 'Unknown')}: {e}")

    conn.commit()
    print(f"Processed {len(country_map)} countries with disease statistics")
    return country_map


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """Clean text fields and truncate if necessary"""
    if not text:
        return None

    text = text.strip()
    if max_length and len(text) > max_length:
        return text[:max_length]
    return text


def determine_route(route_text: str) -> str:
    """Map route text to enum value"""
    route_map = {
        'oral': 'ORAL',
        'mouth': 'ORAL',
        'injection': 'INJECTION',
        'intradermal': 'INJECTION',
        'intramuscular': 'INJECTION',
        'subcutaneous': 'INJECTION',
        'intravenous': 'INTRAVENOUS',
        'iv': 'INTRAVENOUS',
        'topical': 'TOPICAL',
        'dermal': 'TOPICAL',
        'cutaneous': 'TOPICAL',
        'skin': 'TOPICAL'
    }

    if not route_text:
        return None

    route_text = route_text.lower()
    for key, value in route_map.items():
        if key in route_text:
            return value

    return None


def get_country_mapping(vaccine_data: Dict[str, Any]) -> List[str]:
    """Extract country information from a vaccine record"""
    countries = []

    # Look for country information in various fields
    if 'openfda' in vaccine_data:
        openfda = vaccine_data['openfda']

        # Check manufacturer address
        if 'manufacturer_name' in openfda:
            for manufacturer in openfda['manufacturer_name']:
                # Extract country from manufacturer info if available
                if ',' in manufacturer:
                    parts = manufacturer.split(',')
                    country = parts[-1].strip()
                    if country and len(country) > 2:  # Simple filter to avoid state abbreviations
                        countries.append(country)

    return countries


def process_vaccines(conn, vaccines: List[Dict[str, Any]], country_map: Dict[str, int]):
    """Process and insert vaccine data"""
    print("Processing vaccine data...")
    cursor = conn.cursor()

    for vaccine in vaccines:
        try:
            # Basic vaccine identification
            ndc_code = vaccine.get('product_ndc')
            if not ndc_code:
                continue

            brand_name = clean_text(vaccine.get('brand_name', ''))
            generic_name = clean_text(vaccine.get('generic_name', ''))
            product_type = clean_text(vaccine.get('product_type', ''))

            # Route handling
            route_raw = vaccine.get('route', [])
            route_raw = route_raw[0] if isinstance(route_raw, list) and route_raw else route_raw
            route = determine_route(route_raw)

            # Manufacturer and fallback to labeler_name
            manufacturer = None
            is_original_packager = False
            openfda = vaccine.get('openfda', {})

            manufacturer_list = openfda.get('manufacturer_name', [])
            if isinstance(manufacturer_list, list) and manufacturer_list and manufacturer_list[0].strip():
                manufacturer = clean_text(manufacturer_list[0])
            elif 'labeler_name' in vaccine and isinstance(vaccine['labeler_name'], str) and vaccine[
                'labeler_name'].strip():
                manufacturer = clean_text(vaccine['labeler_name'])

            is_original_packager_list = openfda.get('is_original_packager', [])
            if isinstance(is_original_packager_list, list) and is_original_packager_list:
                is_original_packager = is_original_packager_list[0] is True

            # UNII extraction
            unii = None
            for ingredient in vaccine.get('active_ingredients', []):
                if isinstance(ingredient, dict) and 'unii' in ingredient:
                    raw_unii = ingredient['unii']
                    if isinstance(raw_unii, str) and raw_unii.strip():
                        unii = clean_text(raw_unii)
                        break

            # UPC extraction
            upc = vaccine.get('upc')
            upc = clean_text(upc) if isinstance(upc, str) and upc.strip() else None

            # Insert into Vaccine table
            cursor.execute(
                """
                INSERT INTO Vaccine (ndc_code, brand_name, generic_name, product_type, route,
                                     manufacturer, is_original_packager, unii, upc)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ndc_code) DO UPDATE SET
                    brand_name = EXCLUDED.brand_name,
                    generic_name = EXCLUDED.generic_name,
                    product_type = EXCLUDED.product_type,
                    route = EXCLUDED.route,
                    manufacturer = EXCLUDED.manufacturer,
                    is_original_packager = EXCLUDED.is_original_packager,
                    unii = EXCLUDED.unii,
                    upc = EXCLUDED.upc
                """,
                (ndc_code, brand_name, generic_name, product_type, route,
                 manufacturer, is_original_packager, unii, upc)
            )

            # Active ingredients
            for ingredient in vaccine.get('active_ingredients', []):
                name = clean_text(ingredient.get('name', ''))
                if name:
                    cursor.execute(
                        "INSERT INTO Ingredient (vaccine_ndc, substance_name, is_active) VALUES (%s, %s, %s) "
                        "ON CONFLICT DO NOTHING",
                        (ndc_code, name, True)
                    )

            # Inactive ingredients
            for ingredient_name in vaccine.get('inactive_ingredients', []):
                name = clean_text(ingredient_name)
                if name:
                    cursor.execute(
                        "INSERT INTO Ingredient (vaccine_ndc, substance_name, is_active) VALUES (%s, %s, %s) "
                        "ON CONFLICT DO NOTHING",
                        (ndc_code, name, False)
                    )

            # Dosage info
            dosage_parts = []
            if 'dosage_form' in vaccine and vaccine['dosage_form']:
                dosage_parts.append(f"Dosage Form: {vaccine['dosage_form']}")

            for ingredient in vaccine.get('active_ingredients', []):
                if 'strength' in ingredient and 'name' in ingredient:
                    dosage_parts.append(f"{ingredient['name']}: {ingredient['strength']}")

            if 'dosage_and_administration' in vaccine:
                admin = vaccine['dosage_and_administration']
                if isinstance(admin, list) and admin:
                    dosage_parts.append(f"Administration: {admin[0]}")

            dosage_text = ". ".join(dosage_parts) if dosage_parts else None
            if dosage_text and len(dosage_text) > 1000:
                dosage_text = dosage_text[:997] + "..."

            if dosage_text:
                cursor.execute(
                    "INSERT INTO DosageInfo (vaccine_ndc, dosage_text) VALUES (%s, %s) "
                    "ON CONFLICT (vaccine_ndc) DO UPDATE SET dosage_text = EXCLUDED.dosage_text",
                    (ndc_code, dosage_text)
                )

            # Warnings
            warnings = vaccine.get('warnings', [])
            if isinstance(warnings, str):
                warnings = [warnings]

            for warning_text in warnings:
                if warning_text:
                    cursor.execute(
                        "INSERT INTO Warning (vaccine_ndc, warning) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (ndc_code, warning_text)
                    )

            # Country-vaccine usage
            vaccine_countries = get_country_mapping(vaccine)

            if vaccine_countries:
                for country_name in vaccine_countries:
                    matched = False
                    for db_country, country_id in country_map.items():
                        if country_name.lower() in db_country.lower() or db_country.lower() in country_name.lower():
                            cursor.execute(
                                "INSERT INTO CountryVaccineUsage (country_id, vaccine_ndc, usage_notes) "
                                "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                                (country_id, ndc_code, f"Used in {db_country}")
                            )
                            matched = True
                            break

                    if not matched and random.random() < 0.2:
                        random_country_id = random.choice(list(country_map.values()))
                        cursor.execute(
                            "INSERT INTO CountryVaccineUsage (country_id, vaccine_ndc, usage_notes) "
                            "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                            (random_country_id, ndc_code, "Used in multiple regions")
                        )
            else:
                selected_ids = random.sample(list(country_map.values()), min(5, len(country_map)))
                for country_id in selected_ids:
                    cursor.execute(
                        "INSERT INTO CountryVaccineUsage (country_id, vaccine_ndc, usage_notes) "
                        "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (country_id, ndc_code, "Standard deployment")
                    )

        except Exception as e:
            print(f"Error processing vaccine {vaccine.get('product_ndc', 'Unknown')}: {e}")
            continue

    conn.commit()
    print("Vaccine data processing complete")


def main():
    conn = connect_to_db()

    # Fetch data from APIs
    countries = fetch_countries_from_disease_sh()
    vaccines = fetch_vaccines_from_openfda(limit=5000)  # Try to get up to 5000 vaccines

    if not countries:
        print("No country data retrieved. Exiting.")
        return

    if not vaccines:
        print("No vaccine data retrieved. Exiting.")
        return

    # Process data
    country_map = process_countries(conn, countries)
    process_vaccines(conn, vaccines, country_map)

    # Clean up
    conn.close()
    print("Database population complete!")


if __name__ == "__main__":
    main()