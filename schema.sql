-- DOMAIN DEFINITIONS
CREATE DOMAIN dosage_text AS TEXT CHECK (length(VALUE) <= 1000);
CREATE DOMAIN warning_text AS TEXT;

-- TYPE DEFINITIONS
CREATE TYPE route_enum AS ENUM ('ORAL', 'INJECTION', 'INTRAVENOUS', 'TOPICAL', 'UNKNOWN');

-- BASE TABLE: COUNTRY (from Disease.sh)
CREATE TABLE Country (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code TEXT UNIQUE,
    population BIGINT,
    updated_at TIMESTAMP
);

-- TABLE: DISEASE_STATS (from Disease.sh)
CREATE TABLE DiseaseStats (
    id SERIAL PRIMARY KEY,
    country_id INT REFERENCES Country(id) ON DELETE CASCADE,
    total_cases BIGINT,
    today_cases BIGINT,
    deaths BIGINT,
    today_deaths BIGINT,
    recovered BIGINT,
    today_recovered BIGINT,
    active BIGINT,
    critical BIGINT,
    cases_per_million FLOAT,
    deaths_per_million FLOAT,
    tests BIGINT,
    tests_per_million FLOAT,
    active_per_million FLOAT,
    recovered_per_million FLOAT,
    critical_per_million FLOAT
);

-- TABLE: VACCINE (from OpenFDA)
CREATE TABLE Vaccine (
    ndc_code TEXT PRIMARY KEY,
    brand_name TEXT,
    generic_name TEXT,
    product_type TEXT,
    route route_enum,
    manufacturer TEXT,
    is_original_packager BOOLEAN,
    unii TEXT,
    upc TEXT
);

-- TABLE: INGREDIENT
CREATE TABLE Ingredient (
    id SERIAL PRIMARY KEY,
    vaccine_ndc TEXT REFERENCES Vaccine(ndc_code) ON DELETE CASCADE,
    substance_name TEXT,
    is_active BOOLEAN
);

-- TABLE: DOSAGE_INFO (IS-A example — has additional detail)
CREATE TABLE DosageInfo (
    vaccine_ndc TEXT PRIMARY KEY REFERENCES Vaccine(ndc_code),
    dosage_text dosage_text
);

-- TABLE: WARNING (weak entity — no unique PK without vaccine)
CREATE TABLE Warning (
    id SERIAL,
    vaccine_ndc TEXT REFERENCES Vaccine(ndc_code) ON DELETE CASCADE,
    warning warning_text,
    PRIMARY KEY (id, vaccine_ndc)
);

-- TABLE: USAGE_AGGREGATION (aggregation example)
CREATE TABLE CountryVaccineUsage (
    country_id INT REFERENCES Country(id),
    vaccine_ndc TEXT REFERENCES Vaccine(ndc_code),
    usage_notes TEXT,
    PRIMARY KEY (country_id, vaccine_ndc)
);

-- VIEW (filtered by privilege level)
CREATE VIEW VaccinePublicView AS
SELECT brand_name, generic_name, route
FROM Vaccine;

CREATE VIEW VaccineFullView AS
SELECT * FROM Vaccine;

-- ASSERTION/TRIGGER EXAMPLE PLACEHOLDER (to be implemented later as per schema needs)
-- Example: Ensure total_cases >= active + recovered + deaths

-- OPTIONAL: INDEXES for performance
CREATE INDEX idx_disease_country ON DiseaseStats(country_id);
CREATE INDEX idx_usage_country ON CountryVaccineUsage(country_id);
CREATE INDEX idx_usage_vaccine ON CountryVaccineUsage(vaccine_ndc);
