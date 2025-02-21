# Kindergarten Vaccination Coverage and Exemptions

## Table Description
This table contains CDC data on vaccination coverage and exemptions among kindergarten students across different geographic regions and years. The data includes various vaccine types, coverage rates, and exemption information.

## Table Location
```sql
CDC_DATASET.PUBLIC.KINDERGARTEN_VACCINATION_COVERAGE
```

## Schema

| Column Name | Data Type | Description |
|------------|-----------|-------------|
| VACCINE_OR_EXEMPTION | VARCHAR | Type of vaccine (e.g., Polio, MMR) or exemption being reported |
| DOSE | VARCHAR | Specific dose information when applicable |
| GEOGRAPHY_TYPE | VARCHAR | Type of geographic region (currently only 'States') |
| GEOGRAPHY | VARCHAR | Name of the geographic region |
| SCHOOL_YEAR | VARCHAR | Academic year of the reported data |
| COVERAGE_ESTIMATE | FLOAT | Estimated vaccination coverage or exemption percentage |
| POPULATION_SIZE | INTEGER | Total kindergarten population in the geographic area |
| PERCENT_SURVEYED | FLOAT | Percentage of population included in the survey |
| FOOTNOTES | VARCHAR | Additional notes or clarifications about the data |
| EXEMPTION_COUNT | INTEGER | Number of exemptions granted |
| SURVEY_TYPE | VARCHAR | Type of survey methodology used |

## Example Queries

### 1. Get overall vaccination coverage by vaccine type for the most recent school year
```sql
SELECT 
    VACCINE_OR_EXEMPTION,
    AVG(COVERAGE_ESTIMATE) as avg_coverage,
    COUNT(DISTINCT GEOGRAPHY) as state_count
FROM CDC_DATASET.PUBLIC.KINDERGARTEN_VACCINATION_COVERAGE
WHERE 
    SCHOOL_YEAR = (SELECT MAX(SCHOOL_YEAR) FROM CDC_DATASET.PUBLIC.KINDERGARTEN_VACCINATION_COVERAGE)
    AND VACCINE_OR_EXEMPTION NOT LIKE 'Exemption%'
GROUP BY VACCINE_OR_EXEMPTION
ORDER BY avg_coverage DESC;
```

### 2. Track exemption trends over time
```sql
SELECT 
    SCHOOL_YEAR,
    AVG(COVERAGE_ESTIMATE) as avg_exemption_rate,
    SUM(EXEMPTION_COUNT) as total_exemptions
FROM CDC_DATASET.PUBLIC.KINDERGARTEN_VACCINATION_COVERAGE
WHERE VACCINE_OR_EXEMPTION = 'Exemption'
GROUP BY SCHOOL_YEAR
ORDER BY SCHOOL_YEAR;
```

### 3. Find states with lowest MMR vaccination rates
```sql
SELECT 
    GEOGRAPHY,
    SCHOOL_YEAR,
    COVERAGE_ESTIMATE as mmr_coverage,
    POPULATION_SIZE
FROM CDC_DATASET.PUBLIC.KINDERGARTEN_VACCINATION_COVERAGE
WHERE 
    VACCINE_OR_EXEMPTION = 'MMR'
    AND SCHOOL_YEAR = (SELECT MAX(SCHOOL_YEAR) FROM CDC_DATASET.PUBLIC.KINDERGARTEN_VACCINATION_COVERAGE)
ORDER BY COVERAGE_ESTIMATE ASC
LIMIT 10;
```

## Data Refresh
This is a static dataset containing historical vaccination coverage data from the CDC. Updates would be manual as new data becomes available from the CDC.