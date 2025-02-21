# Kindergartners Vaccination Coverage

This table contains data about vaccination coverage and exemption rates among kindergartners in the United States. The data includes information about different types of vaccines, coverage rates, and exemption types across various locations.

## Table Structure

- **VACCINE_OR_EXEMPTION** (VARCHAR(50)): Indicates if the record is for a vaccine or exemption
- **DOSE** (VARCHAR(50)): Specific dose information for exemptions
- **GEOGRAPHY_TYPE** (VARCHAR(50)): Type of geographic region (States, Local Areas, etc.)
- **GEOGRAPHY** (VARCHAR(100)): Name of the geographic location
- **SCHOOL_YEAR** (VARCHAR(10)): Academic year of the data
- **ESTIMATE_PERCENTAGE** (FLOAT): Estimated vaccination coverage or exemption percentage
- **POPULATION_SIZE** (NUMBER): Total population size
- **PERCENT_SURVEYED** (FLOAT): Percentage of population surveyed
- **FOOTNOTES** (VARCHAR(1000)): Additional notes about the data
- **NUMBER_OF_EXEMPTIONS** (NUMBER): Number of exemptions granted
- **SURVEY_TYPE** (VARCHAR(50)): Type of survey conducted

## Example Queries

1. Get average vaccination coverage by vaccine type for the most recent year:
```sql
SELECT 
    VACCINE_OR_EXEMPTION,
    SCHOOL_YEAR,
    AVG(ESTIMATE_PERCENTAGE) as AVG_COVERAGE,
    COUNT(DISTINCT GEOGRAPHY) as NUM_LOCATIONS,
    SUM(POPULATION_SIZE) as TOTAL_POPULATION
FROM KINDERGARTNERS_VACCINATION_COVERAGE
WHERE SCHOOL_YEAR = (
    SELECT MAX(SCHOOL_YEAR) 
    FROM KINDERGARTNERS_VACCINATION_COVERAGE
)
    AND VACCINE_OR_EXEMPTION != 'Exemption'
GROUP BY SCHOOL_YEAR, VACCINE_OR_EXEMPTION
ORDER BY AVG_COVERAGE DESC;
```

2. Compare exemption rates by state for the most recent year:
```sql
SELECT 
    GEOGRAPHY,
    DOSE as EXEMPTION_TYPE,
    ESTIMATE_PERCENTAGE as EXEMPTION_RATE,
    POPULATION_SIZE,
    NUMBER_OF_EXEMPTIONS
FROM KINDERGARTNERS_VACCINATION_COVERAGE
WHERE VACCINE_OR_EXEMPTION = 'Exemption'
    AND SCHOOL_YEAR = (
        SELECT MAX(SCHOOL_YEAR) 
        FROM KINDERGARTNERS_VACCINATION_COVERAGE
        WHERE VACCINE_OR_EXEMPTION = 'Exemption'
    )
    AND GEOGRAPHY_TYPE = 'States'
ORDER BY ESTIMATE_PERCENTAGE DESC;
```

3. Track vaccination coverage trends over time for a specific state:
```sql
SELECT 
    SCHOOL_YEAR,
    VACCINE_OR_EXEMPTION,
    ESTIMATE_PERCENTAGE as COVERAGE_RATE,
    POPULATION_SIZE,
    PERCENT_SURVEYED
FROM KINDERGARTNERS_VACCINATION_COVERAGE
WHERE GEOGRAPHY = 'California'
    AND VACCINE_OR_EXEMPTION != 'Exemption'
ORDER BY SCHOOL_YEAR, VACCINE_OR_EXEMPTION;
```

4. Compare survey participation rates across states:
```sql
SELECT 
    GEOGRAPHY,
    AVG(PERCENT_SURVEYED) as AVG_SURVEY_PARTICIPATION,
    COUNT(DISTINCT VACCINE_OR_EXEMPTION) as NUM_VACCINES_REPORTED,
    SUM(POPULATION_SIZE) as TOTAL_POPULATION,
    SURVEY_TYPE
FROM KINDERGARTNERS_VACCINATION_COVERAGE
WHERE SCHOOL_YEAR = (
    SELECT MAX(SCHOOL_YEAR) 
    FROM KINDERGARTNERS_VACCINATION_COVERAGE
)
    AND GEOGRAPHY_TYPE = 'States'
GROUP BY GEOGRAPHY, SURVEY_TYPE
ORDER BY AVG_SURVEY_PARTICIPATION DESC;
```